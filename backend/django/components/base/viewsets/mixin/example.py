"""
Full example usage of BaseViewSet.

Imagine a simple blog API with:
  - Users can create Posts
  - Posts can have Comments
  - Posts can be published via a custom action
  - Comments can be deleted only by their author

Project structure assumed:
  blog/
    models.py       ← Post, Comment
    serializers.py  ← PostSerializer, CommentSerializer
    viewsets.py     ← PostViewSet, CommentViewSet   (this file)
    urls.py         ← router wiring
"""

# =============================================================================
# blog/models.py
# =============================================================================

from django.conf import settings
from django.db import models


class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    title = models.CharField(max_length=255)
    body = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    slug = models.SlugField(unique=True)

    def publish(self):
        if self.status == self.Status.PUBLISHED:
            raise ValueError("Post is already published.")
        self.status = self.Status.PUBLISHED
        self.save(update_fields=["status", "updated_at"])

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author} on {self.post}"


# =============================================================================
# blog/serializers.py
# =============================================================================

from rest_framework import serializers

# (models imported above in real code — kept flat here for single-file clarity)


class CommentSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source="author.username", read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "author_username", "body", "created_at"]
        read_only_fields = ["id", "author_username", "created_at"]


class PostSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source="author.username", read_only=True)
    comment_count = serializers.IntegerField(source="comments.count", read_only=True)
    comments = CommentSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = [
            "id",
            "author_username",
            "title",
            "slug",
            "body",
            "status",
            "comment_count",
            "comments",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "author_username", "status", "created_at", "updated_at"]


class PostPublishSerializer(serializers.Serializer):
    """Minimal serializer just to document the publish response."""
    id = serializers.IntegerField()
    title = serializers.CharField()
    status = serializers.CharField()


# =============================================================================
# blog/viewsets.py
# =============================================================================

import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.text import slugify

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError

# from .base_viewset import BaseViewSet        ← your real import
# from .models import Post, Comment
# from .serializers import PostSerializer, CommentSerializer, PostPublishSerializer

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Permission helpers
# ---------------------------------------------------------------------------

class IsAuthorOrReadOnly(permissions.BasePermission):
    """Object-level permission: only the author can modify their own content."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user


# ---------------------------------------------------------------------------
# PostViewSet
# Demonstrates: get_create_kwargs, after_perform_create, before_perform_update,
#               get_queryset, custom @action with error_boundary
# ---------------------------------------------------------------------------

class PostViewSet(BaseViewSet, viewsets.ModelViewSet):
    """
    Standard CRUD for Post, with a custom /publish/ action.

    Endpoints:
        GET    /posts/                → list
        POST   /posts/                → create
        GET    /posts/{id}/           → retrieve
        PUT    /posts/{id}/           → update (full)
        PATCH  /posts/{id}/           → partial update
        DELETE /posts/{id}/           → destroy
        POST   /posts/{id}/publish/   → custom publish action
    """

    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    # Enable request/response debug logging for this viewset only.
    LOG_REQUESTS = True

    # ------------------------------------------------------------------
    # Queryset — only return published posts to anonymous users
    # ------------------------------------------------------------------

    def get_queryset(self):
        qs = Post.objects.select_related("author").prefetch_related("comments__author")

        user = self.request.user
        if not user.is_authenticated:
            qs = qs.filter(status=Post.Status.PUBLISHED)

        # Optional: filter by author query param  ?author=john
        author = self.request.query_params.get("author")
        if author:
            qs = qs.filter(author__username=author)

        return qs

    # ------------------------------------------------------------------
    # Create hooks — attach the current user + auto-generate slug
    # ------------------------------------------------------------------

    def get_create_kwargs(self, serializer) -> dict:
        """
        Attach the current user as author and auto-generate a slug from title.
        These are passed directly to serializer.save(), so the model fields
        must accept them (they do — author and slug are on the model).
        """
        title = serializer.validated_data.get("title", "")
        return {
            "author": self.request.user,
            "slug": slugify(title),
        }

    def before_perform_create(self, serializer):
        """
        Guard: a user cannot have two posts with the same title.
        Raise a DRF ValidationError here — it will be caught by handle_exception.
        """
        title = serializer.validated_data.get("title", "")
        if Post.objects.filter(author=self.request.user, title=title).exists():
            raise ValidationError({"title": "You already have a post with this title."})

    def after_perform_create(self, instance, serializer):
        """
        Fire side-effects after the post is saved.
        E.g. send a webhook, invalidate a cache, create a notification, etc.
        Any exception raised here is still caught by handle_exception.
        """
        logger.info("New post created: id=%s title=%r author=%s", instance.pk, instance.title, instance.author)
        # notify_followers.delay(instance.pk)  ← example Celery task

    # ------------------------------------------------------------------
    # Update hooks — prevent changing the slug after creation
    # ------------------------------------------------------------------

    def before_perform_update(self, serializer):
        """
        Block any attempt to change the slug after the post is created.
        The 'instance' is available on the serializer.
        """
        if "title" in serializer.validated_data:
            old_slug = serializer.instance.slug
            new_slug = slugify(serializer.validated_data["title"])
            if old_slug != new_slug:
                raise ValidationError({
                    "title": "Changing the title would alter the slug. Use a different approach to rename."
                })

    def after_perform_update(self, instance, serializer):
        logger.info("Post updated: id=%s", instance.pk)

    # ------------------------------------------------------------------
    # Destroy hooks — only draft posts can be deleted
    # ------------------------------------------------------------------

    def before_perform_destroy(self, instance):
        """
        Business rule: you cannot delete a published post.
        Returns 403 via PermissionDenied (DRF) → handle_exception.
        """
        if instance.status == Post.Status.PUBLISHED:
            raise PermissionDenied("Published posts cannot be deleted. Unpublish first.")

    def after_perform_destroy(self, instance):
        logger.info("Post deleted: id=%s title=%r", instance.pk, instance.title)

    # ------------------------------------------------------------------
    # List hooks — log how many results were returned
    # ------------------------------------------------------------------

    def before_perform_list(self, queryset):
        """Annotate or filter the queryset before the standard DRF filtering runs."""
        return queryset  # you could add .annotate(...) here

    def after_perform_list(self, queryset):
        logger.debug("Post list queryset count: %s", queryset.count())
        return queryset

    # ------------------------------------------------------------------
    # Retrieve hook — record a "view" event
    # ------------------------------------------------------------------

    def after_perform_retrieve(self, instance):
        logger.debug("Post retrieved: id=%s", instance.pk)
        # PostView.objects.create(post=instance, user=self.request.user)  ← example

    # ------------------------------------------------------------------
    # Custom action: POST /posts/{id}/publish/
    # ------------------------------------------------------------------

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def publish(self, request, pk=None):
        """
        Publish a draft post.

        Uses error_boundary() so any exception raised inside is routed
        through handle_exception() exactly like the standard CRUD actions.

        Example errors this naturally covers:
          - Post not found            → 404 (from get_object)
          - Already published         → 400 (from our ValidationError)
          - Not the author            → 403 (from IsAuthorOrReadOnly)
          - DB error during .save()   → 500 (from handle_exception)
        """
        with self.error_boundary():
            post = self.get_object()   # triggers check_object_permissions too

            if post.author != request.user:
                raise PermissionDenied("Only the author can publish this post.")

            try:
                post.publish()
            except ValueError as exc:
                # post.publish() raises ValueError if already published
                raise ValidationError({"detail": str(exc)}) from exc

            serializer = PostPublishSerializer(post)
            return self.success_response(
                data=serializer.data,
                message="Post published successfully.",
                status_code=status.HTTP_200_OK,
            )


# ---------------------------------------------------------------------------
# CommentViewSet
# Demonstrates: nested resource pattern, permission enforcement in destroy
# ---------------------------------------------------------------------------

class CommentViewSet(BaseViewSet, viewsets.ModelViewSet):
    """
    Comments nested under a post: /posts/{post_pk}/comments/

    Endpoints:
        GET    /posts/{post_pk}/comments/           → list comments on a post
        POST   /posts/{post_pk}/comments/           → add a comment
        GET    /posts/{post_pk}/comments/{id}/      → retrieve a comment
        DELETE /posts/{post_pk}/comments/{id}/      → delete (author only)

        PUT / PATCH are disabled via http_method_names.
    """

    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    http_method_names = ["get", "post", "delete", "head", "options"]

    # ------------------------------------------------------------------
    # Queryset — scoped to the parent post
    # ------------------------------------------------------------------

    def get_queryset(self):
        post_pk = self.kwargs.get("post_pk")
        return (
            Comment.objects
            .filter(post_id=post_pk)
            .select_related("author", "post")
            .order_by("created_at")
        )

    # ------------------------------------------------------------------
    # Create — attach the author + parent post
    # ------------------------------------------------------------------

    def get_create_kwargs(self, serializer) -> dict:
        post_pk = self.kwargs.get("post_pk")
        try:
            post = Post.objects.get(pk=post_pk)
        except Post.DoesNotExist:
            # ObjectDoesNotExist → handle_exception maps this to 404
            raise

        if post.status != Post.Status.PUBLISHED:
            raise PermissionDenied("You can only comment on published posts.")

        return {
            "author": self.request.user,
            "post": post,
        }

    # ------------------------------------------------------------------
    # Destroy — only the comment's author can delete it
    # ------------------------------------------------------------------

    def before_perform_destroy(self, instance):
        if instance.author != self.request.user:
            raise PermissionDenied("You can only delete your own comments.")

    def after_perform_destroy(self, instance):
        logger.info(
            "Comment deleted: id=%s post_id=%s by user=%s",
            instance.pk,
            instance.post_id,
            self.request.user,
        )


# =============================================================================
# blog/urls.py
# =============================================================================

from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers as nested_routers  # drf-nested-routers

# from .viewsets import PostViewSet, CommentViewSet

router = DefaultRouter()
router.register(r"posts", PostViewSet, basename="post")

posts_router = nested_routers.NestedDefaultRouter(router, r"posts", lookup="post")
posts_router.register(r"comments", CommentViewSet, basename="post-comments")

urlpatterns = [
    *router.urls,
    *posts_router.urls,
]


# =============================================================================
# Example HTTP interactions (what the API returns)
# =============================================================================

# ── POST /posts/ with a duplicate title ─────────────────────────────────────
#
# Request:
#   POST /api/posts/
#   { "title": "My First Post", "body": "Hello world" }
#
# Response 400:
#   {
#     "error": {
#       "code": "validation_error",
#       "message": "Invalid input.",
#       "details": { "title": ["You already have a post with this title."] }
#     }
#   }

# ── POST /posts/42/publish/ on an already-published post ────────────────────
#
# Response 400:
#   {
#     "error": {
#       "code": "validation_error",
#       "message": "Invalid input.",
#       "details": { "detail": ["Post is already published."] }
#     }
#   }

# ── DELETE /posts/42/ on a published post ───────────────────────────────────
#
# Response 403:
#   {
#     "error": {
#       "code": "permission_denied",
#       "message": "Published posts cannot be deleted. Unpublish first.",
#       "details": null
#     }
#   }

# ── DELETE /posts/42/comments/7/ by a non-author ────────────────────────────
#
# Response 403:
#   {
#     "error": {
#       "code": "permission_denied",
#       "message": "You can only delete your own comments.",
#       "details": null
#     }
#   }

# ── POST /posts/42/publish/ by an unauthenticated user ──────────────────────
#
# Response 401:
#   {
#     "error": {
#       "code": "authentication_error",
#       "message": "Authentication credentials were not provided.",
#       "details": null
#     }
#   }

# ── GET /posts/999/ (non-existent) ──────────────────────────────────────────
#
# Response 404:
#   {
#     "error": {
#       "code": "not_found",
#       "message": "Object not found.",
#       "details": null
#     }
#   }

# ── Successful publish ───────────────────────────────────────────────────────
#
# Response 200:
#   {
#     "message": "Post published successfully.",
#     "data": { "id": 42, "title": "My First Post", "status": "published" }
#   }
