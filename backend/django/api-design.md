# Django API Design Guidelines

## Table of Contents
- [Overview](#overview)
- [RESTful Principles](#restful-principles)
- [API Versioning](#api-versioning)
- [Serialization](#serialization)
- [Pagination](#pagination)
- [Filtering and Searching](#filtering-and-searching)
- [Sorting and Ordering](#sorting-and-ordering)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [API Documentation](#api-documentation)
- [Best Practices](#best-practices)

---

## Overview

Well-designed APIs are the foundation of any modern application. A clean, consistent API is easier to consume, easier to maintain, and much easier to reason about — whether you're the one building it or a frontend developer integrating against it six months later.

This guide covers the key pillars of professional Django REST Framework API design:

| Topic | Why It Matters |
|---|---|
| RESTful Principles | Makes APIs predictable and self-documenting |
| Versioning | Allows evolution without breaking existing clients |
| Serialization | Controls the shape and validation of your data |
| Pagination | Prevents overloading clients and databases |
| Filtering & Searching | Lets clients ask for exactly the data they need |
| Error Handling | Makes debugging fast and integration reliable |
| Rate Limiting | Protects your server from abuse |
| Documentation | Makes your API usable without reverse-engineering |

**Installation and Setup:**

```bash
# Install Django REST Framework
pip install djangorestframework

# Install commonly needed companions
pip install django-filter          # For advanced filtering
pip install drf-spectacular        # For OpenAPI 3 documentation
pip install djangorestframework-simplejwt  # For JWT authentication

# Add to INSTALLED_APPS in settings.py
# 'rest_framework'
# 'django_filters'
# 'drf_spectacular'
```

```python
# settings.py — baseline DRF configuration
REST_FRAMEWORK = {
    # Who is allowed to make requests
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    # What authenticated/unauthenticated users can do
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    # How results are formatted
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    # Pagination defaults
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}
```

---

## RESTful Principles

REST (Representational State Transfer) is an architectural style, not a strict standard. The key idea is that your API is organized around **resources** (nouns like articles, users, comments) — not actions (verbs like getArticle, deleteUser). HTTP methods (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`) express the action.

Following REST conventions means developers can guess how your API works before reading any documentation.

### Resource-Based URLs

URLs should identify *what* you're acting on, not *what you're doing*. The HTTP method already expresses the action.

```python
# urls.py

# GOOD: RESTful URL structure
# URLs are nouns. HTTP methods are the verbs.
urlpatterns = [
    # Collections — represent a list of resources
    path('api/articles/', ArticleListCreateView.as_view()),
    path('api/users/', UserListCreateView.as_view()),

    # Individual resources — identified by their primary key
    path('api/articles/<int:pk>/', ArticleDetailView.as_view()),
    path('api/users/<int:pk>/', UserDetailView.as_view()),

    # Nested resources — comments belong to an article
    path('api/articles/<int:article_pk>/comments/', CommentListCreateView.as_view()),
    path('api/articles/<int:article_pk>/comments/<int:pk>/', CommentDetailView.as_view()),

    # Non-CRUD actions — use a descriptive sub-resource name
    # These are acceptable when an action doesn't map cleanly to CRUD
    path('api/articles/<int:pk>/publish/', ArticlePublishView.as_view()),
    path('api/articles/<int:pk>/like/', ArticleLikeView.as_view()),
]

# BAD: Verb-based URLs — these encode the action in the URL, not the resource
urlpatterns = [
    path('api/get-articles/', get_articles),       # GET is already implied
    path('api/create-article/', create_article),   # POST to a collection creates
    path('api/update-article/<int:id>/', update_article),  # PUT/PATCH handles updates
    path('api/delete-article/<int:id>/', delete_article),  # DELETE handles deletion
]
```

### HTTP Methods

Each HTTP method has a specific, universally understood meaning. Using them correctly makes your API self-documenting and compatible with HTTP infrastructure (caches, proxies, etc.).

| Method | Action | Idempotent? | Response |
|---|---|---|---|
| `GET` | Read | Yes | 200 OK |
| `POST` | Create | No | 201 Created |
| `PUT` | Full update | Yes | 200 OK |
| `PATCH` | Partial update | Yes | 200 OK |
| `DELETE` | Delete | Yes | 204 No Content |

```python
# views.py
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view


class ArticleListCreateView(generics.ListCreateAPIView):
    """
    Handles two HTTP methods on the /api/articles/ endpoint:
      GET  → returns a paginated list of articles
      POST → creates a new article

    Using DRF's generic views means we get list/create behavior for free.
    Override get_queryset() to add filtering logic.
    """
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer

    def get_queryset(self):
        """
        Filter the queryset based on query parameters.
        Called automatically by DRF before serializing the response.
        """
        queryset = super().get_queryset()
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset


class ArticleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Handles multiple HTTP methods on /api/articles/<pk>/:
      GET    → retrieve a single article
      PUT    → fully replace the article (all fields required)
      PATCH  → partially update the article (only send changed fields)
      DELETE → permanently remove the article

    IsOwnerOrReadOnly means anyone can read, but only the author can modify.
    """
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsOwnerOrReadOnly]


@api_view(['POST'])
def article_publish(request, pk):
    """
    POST /api/articles/<pk>/publish/
    Publishes an article. This is a custom action because 'publish' is a
    domain concept that doesn't map cleanly to a standard CRUD operation.

    @api_view(['POST']) restricts this to POST requests only.
    Other HTTP methods will automatically receive a 405 Method Not Allowed.
    """
    try:
        article = Article.objects.get(pk=pk)
    except Article.DoesNotExist:
        return Response(
            {'error': 'Article not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Only the article's author can publish it
    if article.author != request.user:
        return Response(
            {'error': 'Permission denied'},
            status=status.HTTP_403_FORBIDDEN
        )

    article.status = 'published'
    article.published_at = timezone.now()
    article.save()

    # Return the updated article data so the client doesn't need to re-fetch
    return Response(
        ArticleSerializer(article).data,
        status=status.HTTP_200_OK
    )
```

### HTTP Status Codes

Always return semantically correct status codes. Returning `200 OK` for a failed request, or `200 OK` for a new resource creation (instead of `201 Created`), confuses clients and breaks HTTP-aware tooling.

```python
# views.py
from rest_framework import status

class ArticleViewSet(viewsets.ModelViewSet):
    """
    ViewSet demonstrating correct status code usage for each operation.
    DRF's built-in generic views handle most of this automatically,
    but it's important to understand what each code means.
    """

    def create(self, request, *args, **kwargs):
        """
        201 Created — used when a new resource is successfully created.
        Include a Location header pointing to the new resource if possible.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)  # Raises 400 automatically on failure
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers  # Includes Location: /api/articles/<new_pk>/
        )

    def update(self, request, *args, **kwargs):
        """
        200 OK — returned when an existing resource is successfully updated.
        The response body contains the updated resource.
        """
        partial = kwargs.pop('partial', False)  # True for PATCH, False for PUT
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """
        204 No Content — used when deletion succeeds.
        No response body is returned because the resource no longer exists.
        """
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def retrieve(self, request, *args, **kwargs):
        """
        200 OK — returned when a resource is found and returned.
        404 Not Found is raised automatically by get_object() if pk doesn't exist.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
```

---

## API Versioning

API versioning lets you evolve your API — adding fields, changing behavior, deprecating endpoints — without breaking existing clients. It is much easier to add versioning from the start than to retrofit it later.

**Choosing a versioning strategy:**

| Strategy | How | Example | Best For |
|---|---|---|---|
| URL Path | Version in the URL | `/api/v1/articles/` | Most common; easy to test in browser |
| Accept Header | Version in request header | `Accept: application/json; version=v2` | Cleaner URLs; harder to test |
| Namespace | URL namespace-based | `/v1/` and `/v2/` namespaces | Large projects with separate teams |

### URL Path Versioning (Recommended)

This is the most widely used approach. The version is part of the URL, making it immediately visible and easy to test with a browser or curl.

```python
# Project-level urls.py
from django.urls import path, include

urlpatterns = [
    # Each version gets its own URL prefix and URL namespace
    path('api/v1/', include('api.v1.urls', namespace='api-v1')),
    path('api/v2/', include('api.v2.urls', namespace='api-v2')),
]
# Result: /api/v1/articles/ and /api/v2/articles/ are independent
```

```python
# api/v1/urls.py — version 1 routes
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import viewsets

app_name = 'api-v1'

router = DefaultRouter()
# Registers GET /articles/, POST /articles/, GET /articles/<pk>/, etc. automatically
router.register(r'articles', viewsets.ArticleViewSet, basename='article')
router.register(r'users', viewsets.UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
]
```

```python
# api/v2/urls.py — version 2 routes (may use different viewsets with new behavior)
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import viewsets

app_name = 'api-v2'

router = DefaultRouter()
# V2 ViewSets may have different serializers, fields, or behavior
router.register(r'articles', viewsets.ArticleV2ViewSet, basename='article')
router.register(r'users', viewsets.UserV2ViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
]
```

### Accept Header Versioning

The client specifies the version in the `Accept` header rather than the URL. This keeps URLs clean but makes API exploration in a browser harder.

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.AcceptHeaderVersioning',
    'DEFAULT_VERSION': 'v1',           # Used if client doesn't specify a version
    'ALLOWED_VERSIONS': ['v1', 'v2'],  # Requests for other versions get a 404
}
```

```python
# views.py
class ArticleViewSet(viewsets.ModelViewSet):
    """
    Single ViewSet that serves different behavior based on the requested version.
    The client sends: Accept: application/json; version=v2
    DRF parses this and exposes it as request.version.
    """

    def get_serializer_class(self):
        """
        Return different serializers per version.
        V2 might include additional fields (tags, read_time) not in V1.
        """
        if self.request.version == 'v2':
            return ArticleV2Serializer
        return ArticleV1Serializer  # Default to v1

    def get_queryset(self):
        """
        Optimize the queryset based on the version's serializer needs.
        If V2 serializer exposes tags and categories, we must prefetch them.
        """
        queryset = Article.objects.all()

        if self.request.version == 'v2':
            # V2 serializer exposes tags and categories, so prefetch to avoid N+1
            queryset = queryset.prefetch_related('tags', 'categories')

        return queryset
```

### Namespace Versioning

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
}

# urls.py
# The namespace of the matched URL is used as the version
urlpatterns = [
    path('v1/', include('api.urls', namespace='v1')),
    path('v2/', include('api.urls', namespace='v2')),
]
# DRF reads request.version from the URL namespace automatically
```

---

## Serialization

Serializers are the heart of DRF. They do three things: convert model instances to JSON (serialization), convert incoming JSON to validated Python data (deserialization), and validate that data against rules you define.

Think of a serializer like a two-way adapter between your database model and the JSON representation you expose to clients. A good serializer exposes only what the client needs, hides internal implementation details, and enforces input rules.

### Basic Serializers

```python
# serializers.py
from rest_framework import serializers
from .models import Article, Category, User


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for the Category model.
    ModelSerializer auto-generates fields from the model's field definitions.
    read_only_fields prevents clients from setting the ID directly.
    """
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description']
        read_only_fields = ['id']  # ID is auto-assigned by the database


class UserSerializer(serializers.ModelSerializer):
    """
    Public-facing User serializer.
    Note: 'password' is NOT in fields — never expose sensitive data.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class ArticleSerializer(serializers.ModelSerializer):
    """
    Article serializer demonstrating a common pattern:
    - Nested read serializers for related objects (author, category)
    - A write-only PrimaryKeyRelatedField for setting the category on create/update
    - Custom field-level validation
    """

    # Read: expand category into full object for GET responses
    author = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)

    # Write: accept a category ID on POST/PUT/PATCH
    # write_only=True means this field appears in input but NOT in the output
    # source='category' means it writes to the same 'category' FK on the model
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True
    )

    class Meta:
        model = Article
        fields = [
            'id', 'title', 'slug', 'content', 'excerpt',
            'author', 'category', 'category_id',
            'status', 'published_at', 'created_at', 'updated_at'
        ]
        # These fields are set by the system, never by the client
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']

    def validate_title(self, value):
        """
        Field-level validator for 'title'.
        Method name must follow the pattern: validate_<field_name>.
        DRF calls this automatically during .is_valid().
        Raise serializers.ValidationError to reject the value.
        """
        if not value.strip():
            raise serializers.ValidationError('Title cannot be empty.')

        # Check uniqueness, but exclude the current article when updating
        # (so you can save without changing the title)
        queryset = Article.objects.filter(title=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError('An article with this title already exists.')

        return value
```

### Nested Serializers

Nesting serializers allows you to return rich, related data in a single API response — avoiding the need for multiple round-trips. Be careful though: deeply nested serializers can create N+1 query problems if `select_related` and `prefetch_related` aren't used.

```python
# serializers.py
class CommentSerializer(serializers.ModelSerializer):
    """Serializer for comments, including the comment author's public profile."""
    author = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'article', 'author', 'content', 'created_at']
        read_only_fields = ['id', 'author', 'created_at']


class ArticleDetailSerializer(serializers.ModelSerializer):
    """
    Rich, detailed serializer for the article detail view.
    Includes nested comments, tags, and computed fields.
    Only use this for single-article retrieval — too heavy for list views.
    """
    author = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)     # All nested comments
    tags = serializers.StringRelatedField(many=True, read_only=True)  # Tag names as strings

    # A computed field sourced from a model method/property
    comment_count = serializers.IntegerField(source='comments.count', read_only=True)

    # SerializerMethodField calls get_<field_name>() to compute the value
    read_time = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = [
            'id', 'title', 'slug', 'content', 'excerpt',
            'author', 'category', 'tags', 'comments',
            'comment_count', 'read_time',
            'status', 'published_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_read_time(self, obj):
        """
        Called automatically by DRF for the 'read_time' SerializerMethodField.
        Returns estimated reading time in whole minutes (minimum 1).
        """
        words_per_minute = 200
        word_count = len(obj.content.split())
        minutes = max(1, round(word_count / words_per_minute))
        return minutes
```

### Using Different Serializers per Action

A common and powerful pattern is to use a lightweight serializer for list views (fewer fields, faster) and a rich serializer for detail views. Write views may also need a separate serializer that exposes writable fields hidden in read serializers.

```python
# views.py
class ArticleViewSet(viewsets.ModelViewSet):
    """
    Demonstrates using different serializers per action.
    This optimizes both data transfer (lighter list payloads) and
    database queries (different prefetching per action).
    """
    queryset = Article.objects.all()

    def get_serializer_class(self):
        """
        Return the appropriate serializer based on the current action.
        self.action is set by the router and matches method names like
        'list', 'retrieve', 'create', 'update', 'partial_update', 'destroy'.
        """
        if self.action == 'retrieve':
            # Detail view: full nested serializer with comments and tags
            return ArticleDetailSerializer
        elif self.action == 'list':
            # List view: lightweight serializer with just summary fields
            return ArticleListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            # Write operations: separate serializer with writable fields
            return ArticleWriteSerializer
        return ArticleSerializer  # Fallback

    def get_queryset(self):
        """
        Optimize the database query based on what the serializer needs.
        Never prefetch data you won't use — it wastes memory and DB time.
        """
        queryset = super().get_queryset()

        if self.action == 'retrieve':
            # Detail view needs comments with authors, tags, and category
            queryset = queryset.prefetch_related(
                'comments__author',
                'tags',
                'category'
            ).select_related('author')

        elif self.action == 'list':
            # List view only needs a subset of fields — use .only() to avoid SELECT *
            queryset = queryset.select_related(
                'author',
                'category'
            ).only(
                'id', 'title', 'slug', 'excerpt',
                'author__username', 'category__name',
                'published_at', 'created_at'
            )

        return queryset
```

---

## Pagination

Pagination is non-negotiable for any endpoint that returns lists. Without it, a single request could return tens of thousands of records, crashing clients and overloading your database.

DRF ships with three pagination styles. Choose based on your use case:

| Style | How It Works | Best For |
|---|---|---|
| `PageNumberPagination` | `?page=2&page_size=20` | General use, simple UIs |
| `LimitOffsetPagination` | `?limit=20&offset=40` | Flexible APIs, power users |
| `CursorPagination` | `?cursor=abc123` | Real-time feeds, high-volume data |

### Page Number Pagination

The most common and intuitive style. Clients navigate by page number.

```python
# settings.py — set a global default
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,  # Returned if client doesn't specify page_size
}
```

```python
# pagination.py
from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination for most list endpoints.
    - page_size: default number of results per page
    - page_size_query_param: allows client to request a different page size (?page_size=50)
    - max_page_size: hard ceiling — clients can never exceed this, preventing abuse
    - page_query_param: the query parameter name for the page number
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100          # ?page_size=9999 will be capped at 100
    page_query_param = 'page'   # Usage: ?page=3


class LargeResultsSetPagination(PageNumberPagination):
    """
    For endpoints that need to return more data at once (e.g., exports, admin views).
    Only use this where the larger payload is genuinely necessary.
    """
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000
```

```python
# views.py — attach pagination class per view or set globally in settings
class ArticleListView(generics.ListAPIView):
    """
    List articles using standard pagination.
    Response includes: count, next, previous, results.
    """
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    pagination_class = StandardResultsSetPagination
    # Usage: GET /api/articles/?page=2&page_size=10
```

### Limit Offset Pagination

Lets clients say "give me 20 items starting from item 40." More flexible than page-number pagination, particularly useful for dashboards and data tables.

```python
# pagination.py
from rest_framework.pagination import LimitOffsetPagination


class CustomLimitOffsetPagination(LimitOffsetPagination):
    """
    Limit/offset pagination.
    - default_limit: results returned if client doesn't specify ?limit
    - max_limit: hard ceiling to prevent abuse
    Usage: GET /api/articles/?limit=20&offset=40
    (returns items 41–60)
    """
    default_limit = 20
    max_limit = 100
    limit_query_param = 'limit'
    offset_query_param = 'offset'
```

### Cursor Pagination

Cursor-based pagination is the most robust approach for high-volume, real-time data (like a news feed or activity stream). It uses an opaque cursor token instead of page numbers, which means it handles concurrent inserts correctly and prevents the "page drift" problem (where inserting a new item pushes old items to a different page).

```python
# pagination.py
from rest_framework.pagination import CursorPagination


class ArticleCursorPagination(CursorPagination):
    """
    Cursor-based pagination for article feeds.
    - ordering must be a stable, indexed field (usually a timestamp)
    - The cursor encodes the current position, not a page number
    - Clients cannot jump to arbitrary pages — only forward/backward
    Usage: GET /api/articles/?cursor=cD0yMDI0...
    """
    page_size = 20
    ordering = '-created_at'       # Must match an indexed field
    cursor_query_param = 'cursor'
```

### Custom Pagination Response

By default, DRF's pagination returns `count`, `next`, `previous`, `results`. Override `get_paginated_response()` to add extra metadata your clients need.

```python
# pagination.py
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomPagination(PageNumberPagination):
    """
    Enhanced pagination that returns richer metadata.
    Clients get the current page number and total pages, which is useful
    for building page-number UI controls.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        """
        Override to return a richer response structure.
        The 'pagination' object groups all navigation metadata together.
        """
        return Response({
            'pagination': {
                'count': self.page.paginator.count,          # Total items
                'page': self.page.number,                    # Current page
                'page_size': self.page.paginator.per_page,  # Items per page
                'total_pages': self.page.paginator.num_pages,
                'next': self.get_next_link(),                # URL for next page (or null)
                'previous': self.get_previous_link(),        # URL for prev page (or null)
            },
            'results': data                                  # The actual items
        })
```

---

## Filtering and Searching

Filtering lets clients narrow down list results without fetching everything. A well-designed filtering system reduces bandwidth, speeds up responses, and makes your API dramatically more useful.

**Install the dependency first:**

```bash
pip install django-filter
```

```python
# settings.py
INSTALLED_APPS = [
    # ...
    'django_filters',
]

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',  # ?status=published
        'rest_framework.filters.SearchFilter',                # ?search=keyword
        'rest_framework.filters.OrderingFilter',              # ?ordering=-created_at
    ],
}
```

### Basic Filtering

For simple cases, `filterset_fields` is all you need. DRF and django-filter handle everything else.

```python
# views.py
from django_filters.rest_framework import DjangoFilterBackend


class ArticleListView(generics.ListAPIView):
    """
    Automatically generates filters for the specified fields.
    Each field gets an exact-match filter based on its type.
    """
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'category', 'author']
    # Usage examples:
    # GET /api/articles/?status=published
    # GET /api/articles/?category=1
    # GET /api/articles/?status=published&category=1  ← multiple filters are ANDed
```

### Custom FilterSet

For more sophisticated filtering — ranges, partial matches, multi-value filters, custom logic — define a `FilterSet` class.

```python
# filters.py
import django_filters
from django.db.models import Q
from .models import Article


class ArticleFilter(django_filters.FilterSet):
    """
    Custom FilterSet for the Article model.
    Each filter maps to a query parameter clients can use.
    """

    # Exact match — ?status=published
    status = django_filters.CharFilter(field_name='status')

    # Filter by author's ID — ?author=5
    author = django_filters.NumberFilter(field_name='author__id')

    # Date range filters — ?min_date=2024-01-01&max_date=2024-12-31
    # 'gte' = greater than or equal to, 'lte' = less than or equal to
    min_date = django_filters.DateFilter(field_name='published_at', lookup_expr='gte')
    max_date = django_filters.DateFilter(field_name='published_at', lookup_expr='lte')

    # Case-insensitive partial match — ?title=django
    title = django_filters.CharFilter(field_name='title', lookup_expr='icontains')
    content = django_filters.CharFilter(field_name='content', lookup_expr='icontains')

    # Related model filter — ?category=1 (by Category ID)
    category = django_filters.ModelChoiceFilter(queryset=Category.objects.all())

    # Multiple values filter — ?tags=python&tags=django (OR logic)
    # field_name='tags__slug' traverses the ManyToMany to filter by tag slug
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )

    # Boolean filter — ?is_featured=true
    is_featured = django_filters.BooleanFilter(field_name='is_featured')

    # Custom method filter — ?search=keyword
    # 'method' points to a method on this FilterSet class
    search = django_filters.CharFilter(method='filter_search')

    class Meta:
        model = Article
        fields = ['status', 'author', 'category', 'tags', 'is_featured']

    def filter_search(self, queryset, name, value):
        """
        Custom search that checks across multiple text fields simultaneously.
        Uses OR logic (|) so any matching field qualifies the article.
        Q objects are Django's way of building complex OR/AND conditions.
        """
        return queryset.filter(
            Q(title__icontains=value) |
            Q(content__icontains=value) |
            Q(excerpt__icontains=value)
        )
```

```python
# views.py — wire the FilterSet to the view
class ArticleListView(generics.ListAPIView):
    """
    Full-featured list view with custom filtering.
    """
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    filterset_class = ArticleFilter  # Points to the FilterSet above

    # Usage examples:
    # GET /api/articles/?status=published
    # GET /api/articles/?min_date=2024-01-01&max_date=2024-12-31
    # GET /api/articles/?title=django
    # GET /api/articles/?tags=python&tags=django
    # GET /api/articles/?search=tutorial
```

### Search Filter

DRF's built-in `SearchFilter` provides simple keyword search across multiple fields. Unlike the custom `filter_search` above, it uses a single `?search=` parameter and automatically handles the field traversal.

```python
# views.py
from rest_framework.filters import SearchFilter


class ArticleListView(generics.ListAPIView):
    """
    Keyword search across multiple fields using DRF's SearchFilter.
    Prefix field names with ^ for starts-with, = for exact, @ for full-text search.
    No prefix = contains (icontains).
    """
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    filter_backends = [SearchFilter]
    search_fields = [
        'title',            # Contains search in title
        'content',          # Contains search in content
        'author__username', # Traverses FK to search author's username
        'category__name',   # Traverses FK to search category name
    ]
    # Usage: GET /api/articles/?search=django
    # Finds articles where title, content, author username, or category name
    # contains "django" (case-insensitive)
```

---

## Sorting and Ordering

Ordering lets clients control the sort order of results. Always define a sensible default so results are consistent when no ordering is specified.

### Ordering Filter

```python
# views.py
from rest_framework.filters import OrderingFilter


class ArticleListView(generics.ListAPIView):
    """
    Allow clients to sort results by specifying ?ordering=<field>.
    Prefix with '-' for descending (newest first).
    """
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ['created_at', 'updated_at', 'published_at', 'title']
    ordering = ['-created_at']  # Default: newest articles first

    # Usage examples:
    # GET /api/articles/?ordering=created_at        ← oldest first
    # GET /api/articles/?ordering=-created_at       ← newest first (same as default)
    # GET /api/articles/?ordering=title             ← alphabetical A-Z
    # GET /api/articles/?ordering=title,-created_at ← alphabetical, then newest first
```

### Custom Ordering

Sometimes you want to expose friendly ordering aliases (like `popular` or `trending`) that map to complex database expressions clients shouldn't know about.

```python
# views.py
class ArticleListView(generics.ListAPIView):
    """
    Custom ordering with human-friendly aliases.
    Clients use simple words; the view maps them to real database fields.
    """
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer

    def get_queryset(self):
        """
        Intercept ?ordering= before it reaches the database.
        Map friendly names to real field names or database expressions.
        Falls back to '-created_at' (newest first) if no ordering specified.
        """
        queryset = super().get_queryset()
        ordering = self.request.query_params.get('ordering', '-created_at')

        # Map client-facing aliases to real DB fields
        ordering_map = {
            'popular':      '-view_count',   # Most viewed first
            'trending':     '-like_count',   # Most liked first
            'newest':       '-created_at',
            'oldest':       'created_at',
            'alphabetical': 'title',
        }

        # Use the mapped field if it's a known alias, otherwise use as-is
        ordering = ordering_map.get(ordering, ordering)

        return queryset.order_by(ordering)

    # Usage examples:
    # GET /api/articles/?ordering=popular
    # GET /api/articles/?ordering=trending
    # GET /api/articles/?ordering=oldest
```

---

## Error Handling

Consistent, informative error responses are as important as correct success responses. A well-designed error response tells the client exactly what went wrong, where, and how to fix it — without revealing sensitive internal details.

**Anatomy of a good error response:**

```json
{
  "error": {
    "status_code": 400,
    "message": "Validation failed",
    "details": {
      "title": ["An article with this title already exists."],
      "category_id": ["This field is required."]
    }
  }
}
```

### Custom Exception Handler

DRF's default exception handler returns raw validation errors without any wrapping structure. A custom handler lets you standardize the format across your entire API.

```python
# exceptions.py
from rest_framework.views import exception_handler
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    """
    Global exception handler for Django REST Framework.
    Wraps all DRF error responses in a consistent structure.

    DRF calls this automatically for any exception raised in a view.
    It's only called for exceptions DRF knows about (APIException subclasses).
    For unhandled exceptions (500s), Django's standard error handling applies.
    """
    # First, let DRF process the exception with its default handler.
    # This handles authentication errors, permission errors, validation errors, etc.
    response = exception_handler(exc, context)

    if response is not None:
        # Wrap the default response in a structured envelope
        custom_response = {
            'error': {
                'status_code': response.status_code,
                'message': 'An error occurred',
                'details': response.data   # Original DRF error data
            }
        }

        # Override the generic message with something more specific per status code
        if response.status_code == 404:
            custom_response['error']['message'] = 'Resource not found'
        elif response.status_code == 400:
            custom_response['error']['message'] = 'Bad request'
        elif response.status_code == 401:
            custom_response['error']['message'] = 'Authentication required'
        elif response.status_code == 403:
            custom_response['error']['message'] = 'Permission denied'
        elif response.status_code == 500:
            custom_response['error']['message'] = 'Internal server error'

        response.data = custom_response

    return response
```

```python
# settings.py — register your custom exception handler
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'myapp.exceptions.custom_exception_handler',
}
```

### Custom Exceptions

Define your own exception classes for domain-specific error conditions that don't map cleanly to standard HTTP status codes. This also documents the possible error states in your codebase.

```python
# exceptions.py
from rest_framework.exceptions import APIException
from rest_framework import status


class ServiceUnavailable(APIException):
    """
    Raised when a required external service (e.g., payment processor, email provider)
    is temporarily unavailable. Returns 503 Service Unavailable.
    The client should retry after a short delay.
    """
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'Service temporarily unavailable, please try again later.'
    default_code = 'service_unavailable'


class ResourceConflict(APIException):
    """
    Raised when a request conflicts with the current state of a resource.
    Example: trying to publish an article that is already published.
    Returns 409 Conflict.
    """
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'Resource conflict.'
    default_code = 'resource_conflict'


class ValidationError(APIException):
    """
    More semantically precise than 400 Bad Request for input validation failures.
    Returns 422 Unprocessable Entity — the request was well-formed but contained
    invalid data (e.g., a date in the past when a future date is required).
    """
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = 'Validation error.'
    default_code = 'validation_error'
```

### Error Response Format in Views

Use try/except in views to catch specific exception types and return consistent, structured error responses.

```python
# views.py
from rest_framework.response import Response
from rest_framework import status


class ArticleViewSet(viewsets.ModelViewSet):
    """
    Article viewset with structured, consistent error handling.
    Every response — success or failure — follows the same envelope format.
    """

    def create(self, request, *args, **kwargs):
        """
        Create an article with detailed error handling.
        - ValidationError from serializer → 400 with field-level details
        - Unexpected exceptions → 500 (details hidden in production)
        """
        serializer = self.get_serializer(data=request.data)

        try:
            # raise_exception=True causes DRF to raise ValidationError automatically
            # if is_valid() returns False — no need to check the return value
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)

            return Response({
                'success': True,
                'data': serializer.data,
                'message': 'Article created successfully'
            }, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            # Field-level validation errors — safe to expose to the client
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Validation failed',
                    'details': e.detail  # Contains field-by-field error messages
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            # Unexpected errors — never expose internal details in production
            # settings.DEBUG=True in development will show the actual error
            return Response({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'An unexpected error occurred',
                    'details': str(e) if settings.DEBUG else None
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

---

## Rate Limiting

Rate limiting (called "throttling" in DRF) protects your API from abuse — both malicious (denial-of-service attacks) and accidental (a client with a bug making thousands of requests per second). It is especially important for unauthenticated endpoints.

DRF throttling works by tracking requests in the cache (usually Redis or Memcached) and rejecting requests that exceed a defined threshold.

### DRF Throttling

```python
# settings.py — global throttle configuration
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        # Throttle unauthenticated requests by IP address
        'rest_framework.throttling.AnonRateThrottle',
        # Throttle authenticated requests by user
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',    # Unauthenticated: 100 requests per day
        'user': '1000/day',   # Authenticated: 1000 requests per day
    }
}
# Clients that exceed the limit receive: 429 Too Many Requests
# The response includes a Retry-After header telling the client when to retry
```

### Custom Throttle Classes

Define multiple throttles with different scopes for fine-grained control. For example, you might allow 60 requests per minute in bursts, but cap the daily total.

```python
# throttles.py
from rest_framework.throttling import UserRateThrottle


class BurstRateThrottle(UserRateThrottle):
    """
    Short-window throttle — limits rapid-fire requests.
    Prevents a client from making 60 requests in a single second.
    Applied alongside SustainedRateThrottle for two-tier limiting.
    """
    scope = 'burst'


class SustainedRateThrottle(UserRateThrottle):
    """
    Long-window throttle — limits total daily usage.
    Works together with BurstRateThrottle: clients can burst up to 60/min,
    but are still capped at 1000/day overall.
    """
    scope = 'sustained'


class UploadRateThrottle(UserRateThrottle):
    """
    Separate throttle for file upload endpoints.
    Uploads are expensive (storage, processing) so they get a stricter limit.
    """
    scope = 'upload'
```

```python
# settings.py — define rates for each scope
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_RATES': {
        'anon':      '100/day',
        'user':      '1000/day',
        'burst':     '60/min',     # 60 requests per minute max
        'sustained': '1000/day',   # 1000 requests per day max
        'upload':    '20/hour',    # 20 uploads per hour max
    }
}
```

```python
# views.py — apply throttles per view rather than globally
class ArticleCreateView(generics.CreateAPIView):
    """
    Create view with two-tier rate limiting.
    Both throttles apply simultaneously — the request must pass both.
    """
    serializer_class = ArticleSerializer
    throttle_classes = [BurstRateThrottle, SustainedRateThrottle]
    # Usage: If user hits 60 req/min → 429. If user hits 1000 req/day → 429.
```

---

## API Documentation

Good API documentation is as important as the API itself. Without documentation, even a well-designed API is frustrating to use. `drf-spectacular` generates OpenAPI 3.0 schemas automatically from your code and serves them through interactive UIs.

### Setup drf-spectacular

```bash
pip install drf-spectacular
```

```python
# settings.py
INSTALLED_APPS = [
    # ...
    'drf_spectacular',
]

REST_FRAMEWORK = {
    # Tell DRF to use drf-spectacular's schema generator
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'My API',
    'DESCRIPTION': 'API documentation for My Project',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,  # Don't include the schema endpoint in the schema itself
    'COMPONENT_SPLIT_REQUEST': True,  # Use separate schemas for requests vs responses
}
```

```python
# urls.py — add documentation endpoints
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView
)

urlpatterns = [
    # Raw OpenAPI schema (JSON/YAML) — used by tools and other UIs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),

    # Swagger UI — interactive, try-it-out API explorer
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # ReDoc — clean, read-only reference documentation
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
```

```bash
# Generate a static schema file (useful for CI, type generation, contract testing)
python manage.py spectacular --color --file schema.yml
```

### Documenting Endpoints with @extend_schema

`drf-spectacular` infers a lot automatically, but you should add `@extend_schema` for clarity — especially for parameters, multiple response types, and examples.

```python
# views.py
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes


class ArticleViewSet(viewsets.ModelViewSet):
    """ViewSet for managing articles."""

    queryset = Article.objects.all()
    serializer_class = ArticleSerializer

    @extend_schema(
        summary='List articles',                          # Short title in the UI
        description="""
            Retrieve a paginated list of articles.
            Results can be filtered by status, category, and author.
            Use the search parameter to find articles by keyword.
        """,
        parameters=[
            OpenApiParameter(
                name='status',
                type=OpenApiTypes.STR,
                description='Filter articles by publication status.',
                enum=['draft', 'published', 'archived'],  # Documents valid choices
                required=False,
            ),
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                description='Search across title, content, and author username.',
                required=False,
            ),
        ],
        responses={200: ArticleSerializer(many=True)},   # Documents the response schema
        tags=['Articles']                                 # Groups endpoint in the UI
    )
    def list(self, request, *args, **kwargs):
        """List all articles."""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary='Create article',
        description='Create a new article. The author is automatically set to the logged-in user.',
        request=ArticleWriteSerializer,     # Input schema (may differ from output schema)
        responses={
            201: ArticleSerializer,         # Success response
            400: OpenApiTypes.OBJECT,       # Validation error response
        },
        examples=[
            OpenApiExample(
                'Article Example',
                summary='Basic article creation',
                description='A minimal example for creating a draft article.',
                value={
                    'title': 'My Article',
                    'content': 'Article content here...',
                    'status': 'draft',
                    'category_id': 1
                },
                request_only=True   # Show only in the request schema, not the response
            )
        ],
        tags=['Articles']
    )
    def create(self, request, *args, **kwargs):
        """Create a new article."""
        return super().create(request, *args, **kwargs)
```

---

## Best Practices

### Consistent Response Format

Consistency is king. Every response — success or error — should follow the same envelope structure. This makes client-side parsing predictable and reduces integration bugs.

```python
# utils.py
from rest_framework.response import Response


def success_response(data=None, message='Success', status=200):
    """
    Wrap successful data in a standard envelope.
    'success': True signals to clients they can safely read 'data'.
    """
    return Response({
        'success': True,
        'message': message,
        'data': data
    }, status=status)


def error_response(message='Error', errors=None, status=400):
    """
    Wrap error information in a standard envelope.
    'success': False signals to clients they should read 'errors' instead of 'data'.
    """
    return Response({
        'success': False,
        'message': message,
        'errors': errors
    }, status=status)

# Usage in views:
# return success_response(data=serializer.data, message='Article created', status=201)
# return error_response(message='Invalid data', errors=serializer.errors)
```

### API Naming Conventions

Follow consistent, plural, lowercase, hyphenated URL patterns. Inconsistency forces developers to memorize exceptions instead of inferring the pattern.

```python
# GOOD: Consistent, predictable patterns
urlpatterns = [
    # Plural nouns, lowercase, no verbs, versioned
    path('api/v1/articles/', ArticleListCreateView.as_view()),
    path('api/v1/articles/<int:pk>/', ArticleDetailView.as_view()),
    path('api/v1/users/', UserListCreateView.as_view()),
    path('api/v1/users/<int:pk>/', UserDetailView.as_view()),
]

# BAD: Inconsistent — forces developers to memorize rather than infer
urlpatterns = [
    path('api/article/', get_articles),                     # Singular, not plural
    path('api/getArticle/<int:id>/', get_article),          # Verb in URL, camelCase
    path('api/user_list/', list_users),                     # Underscore, verb suffix
]
```

### HATEOAS — Hypermedia Links

HATEOAS (Hypermedia As The Engine Of Application State) means your API responses include links to related resources. Clients can navigate the API by following links rather than hardcoding URLs. It's the ideal, though not always practical to implement fully.

```python
# serializers.py
class ArticleSerializer(serializers.ModelSerializer):
    """
    Article serializer with hypermedia links.
    HyperlinkedIdentityField generates the full URL to this resource.
    HyperlinkedRelatedField generates the full URL to a related resource.
    Clients can follow these links without knowing URL structure.
    """

    # Self-link: the URL of this specific article
    url = serializers.HyperlinkedIdentityField(
        view_name='api:article-detail',
        lookup_field='pk'
    )

    # Related link: the URL of the author's user profile
    author_url = serializers.HyperlinkedRelatedField(
        source='author',
        view_name='api:user-detail',
        read_only=True
    )

    class Meta:
        model = Article
        fields = ['id', 'url', 'title', 'content', 'author_url', 'created_at']
        # Response: {"id": 1, "url": "/api/v1/articles/1/", "author_url": "/api/v1/users/5/", ...}
```

### Field Selection

Allow clients to request only the fields they need. This reduces payload size and speeds up responses — especially valuable for mobile clients or dashboards that only need summary data.

```python
# views.py
class DynamicFieldsViewSet(viewsets.ModelViewSet):
    """
    ViewSet that supports sparse fieldsets via ?fields= query parameter.
    Clients specify which fields they want; unused fields are removed
    before serialization happens.
    """

    def get_serializer(self, *args, **kwargs):
        """
        Intercept the serializer creation and remove fields not requested.
        This happens before serialization, so excluded fields are never
        accessed — avoiding unnecessary database queries.
        """
        serializer = super().get_serializer(*args, **kwargs)

        fields = self.request.query_params.get('fields')
        if fields:
            allowed = set(fields.split(','))      # Client-requested fields
            existing = set(serializer.fields.keys())  # All available fields
            # Remove any field the client didn't request
            for field_name in existing - allowed:
                serializer.fields.pop(field_name)

        return serializer

    # Usage:
    # GET /api/articles/?fields=id,title,created_at
    # Response only contains id, title, and created_at — nothing else
```

### Caching

Cache expensive list endpoints to dramatically reduce database load. Use `cache_page` for public data and `vary_on_cookie` for per-user content to ensure cached responses aren't shared between different users.

```python
# views.py
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie


class ArticleListView(generics.ListAPIView):
    """
    Public article list — cached for 15 minutes.
    All users get the same cached response since it's public data.
    Cache is invalidated automatically after 15 minutes.
    """
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer

    @method_decorator(cache_page(60 * 15))  # 60 seconds × 15 = 15 minutes
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class UserArticleListView(generics.ListAPIView):
    """
    User-specific article list — cached per user (via cookie).
    vary_on_cookie ensures each user gets their own cache entry.
    Without this, User A might get User B's cached articles.
    """

    @method_decorator(vary_on_cookie)          # Separate cache per user session
    @method_decorator(cache_page(60 * 5))      # Cache for 5 minutes per user
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
```

### Performance Optimization

Database queries are almost always the bottleneck in Django APIs. `select_related` and `prefetch_related` are the two most important tools for keeping query counts low.

```python
# views.py
class ArticleViewSet(viewsets.ModelViewSet):
    """
    Optimized ViewSet that tailors database queries to each action.
    The key principle: only fetch what you'll actually use.
    """

    def get_queryset(self):
        """
        Different actions need different data — optimize each independently.
        """
        queryset = Article.objects.all()

        if self.action == 'list':
            # List view: lightweight — only the fields the list serializer uses
            # select_related('author', 'category') = one JOIN query (no N+1)
            # .only() = SELECT only named columns (avoids SELECT *)
            queryset = queryset.select_related(
                'author',
                'category'
            ).only(
                'id', 'title', 'slug', 'excerpt',
                'author__username',
                'category__name',
                'published_at'
            )

        elif self.action == 'retrieve':
            # Detail view: rich — includes nested comments, tags, and full author data
            # prefetch_related = efficient batch queries for ManyToMany and reverse FKs
            # 'comments__author' = prefetch comments AND their authors in 2 extra queries
            queryset = queryset.select_related(
                'author',
                'category'
            ).prefetch_related(
                'tags',
                'comments__author'
            )

        return queryset
```

### API Security Configuration

Security should be configured explicitly, not left to defaults. The settings below represent a secure baseline for a production API.

```python
# settings.py — secure production API configuration
REST_FRAMEWORK = {
    # JWT-based authentication — stateless, scalable
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],

    # Deny access to unauthenticated users by default
    # Override per-view for public endpoints (e.g., AllowAny on login)
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],

    # Rate limiting — protects against abuse and accidental hammering
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',  # By IP
        'rest_framework.throttling.UserRateThrottle',  # By user
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day',
    },

    # Return JSON only — disables the browsable HTML API in production
    # In development, you may want to include BrowsableAPIRenderer for debugging
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}
```
