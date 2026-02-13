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

## Overview

Well-designed APIs are crucial for modern applications. This guide covers RESTful principles, versioning strategies, pagination, filtering, error handling, and documentation using Django REST Framework.

## RESTful Principles

### Resource-Based URLs

```python
# ✅ GOOD: RESTful URL structure
urlpatterns = [
    # Collections
    path('api/articles/', ArticleListCreateView.as_view()),
    path('api/users/', UserListCreateView.as_view()),
    
    # Resources
    path('api/articles/<int:pk>/', ArticleDetailView.as_view()),
    path('api/users/<int:pk>/', UserDetailView.as_view()),
    
    # Nested resources
    path('api/articles/<int:article_pk>/comments/', CommentListCreateView.as_view()),
    path('api/articles/<int:article_pk>/comments/<int:pk>/', CommentDetailView.as_view()),
    
    # Actions
    path('api/articles/<int:pk>/publish/', ArticlePublishView.as_view()),
    path('api/articles/<int:pk>/like/', ArticleLikeView.as_view()),
]

# ❌ BAD: Non-RESTful URL structure
urlpatterns = [
    path('api/get-articles/', get_articles),
    path('api/create-article/', create_article),
    path('api/update-article/<int:id>/', update_article),
    path('api/delete-article/<int:id>/', delete_article),
]
```

### HTTP Methods

```python
# views.py
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view


class ArticleListCreateView(generics.ListCreateAPIView):
    """
    GET: List all articles
    POST: Create new article
    """
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    
    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = super().get_queryset()
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset


class ArticleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve article
    PUT/PATCH: Update article
    DELETE: Delete article
    """
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsOwnerOrReadOnly]


# Custom actions using @api_view decorator
@api_view(['POST'])
def article_publish(request, pk):
    """POST: Publish an article."""
    try:
        article = Article.objects.get(pk=pk)
    except Article.DoesNotExist:
        return Response(
            {'error': 'Article not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if article.author != request.user:
        return Response(
            {'error': 'Permission denied'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    article.status = 'published'
    article.published_at = timezone.now()
    article.save()
    
    return Response(
        ArticleSerializer(article).data,
        status=status.HTTP_200_OK
    )
```

### Status Codes

```python
from rest_framework import status

class ArticleViewSet(viewsets.ModelViewSet):
    """Article viewset with proper status codes."""
    
    def create(self, request, *args, **kwargs):
        """Create article - 201 Created."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )
    
    def update(self, request, *args, **kwargs):
        """Update article - 200 OK."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        """Delete article - 204 No Content."""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def retrieve(self, request, *args, **kwargs):
        """Get article - 200 OK or 404 Not Found."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
```

## API Versioning

### URL Path Versioning

```python
# urls.py (Project level)
from django.urls import path, include

urlpatterns = [
    path('api/v1/', include('api.v1.urls', namespace='api-v1')),
    path('api/v2/', include('api.v2.urls', namespace='api-v2')),
]
```

```python
# api/v1/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import viewsets

app_name = 'api-v1'

router = DefaultRouter()
router.register(r'articles', viewsets.ArticleViewSet, basename='article')
router.register(r'users', viewsets.UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
]
```

```python
# api/v2/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import viewsets

app_name = 'api-v2'

router = DefaultRouter()
router.register(r'articles', viewsets.ArticleV2ViewSet, basename='article')
router.register(r'users', viewsets.UserV2ViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
]
```

### Accept Header Versioning

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.AcceptHeaderVersioning',
    'DEFAULT_VERSION': 'v1',
    'ALLOWED_VERSIONS': ['v1', 'v2'],
}
```

```python
# views.py
from rest_framework import viewsets

class ArticleViewSet(viewsets.ModelViewSet):
    """Article viewset with version-specific behavior."""
    
    def get_serializer_class(self):
        """Return serializer based on API version."""
        if self.request.version == 'v2':
            return ArticleV2Serializer
        return ArticleV1Serializer
    
    def get_queryset(self):
        """Return queryset based on API version."""
        queryset = Article.objects.all()
        
        if self.request.version == 'v2':
            # v2 includes additional prefetch
            queryset = queryset.prefetch_related('tags', 'categories')
        
        return queryset
```

### Namespace Versioning

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
}
```

```python
# urls.py
urlpatterns = [
    path('v1/', include('api.urls', namespace='v1')),
    path('v2/', include('api.urls', namespace='v2')),
]
```

## Serialization

### Basic Serializers

```python
# serializers.py
from rest_framework import serializers
from .models import Article, Category, User


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model."""
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description']
        read_only_fields = ['id']


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class ArticleSerializer(serializers.ModelSerializer):
    """Serializer for Article model."""
    
    author = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
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
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']
    
    def validate_title(self, value):
        """Validate title is not empty and unique."""
        if not value.strip():
            raise serializers.ValidationError('Title cannot be empty.')
        
        # Check uniqueness (excluding current instance during update)
        queryset = Article.objects.filter(title=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise serializers.ValidationError('Article with this title already exists.')
        
        return value
```

### Nested Serializers

```python
# serializers.py
class CommentSerializer(serializers.ModelSerializer):
    """Serializer for Comment model."""
    
    author = UserSerializer(read_only=True)
    
    class Meta:
        model = Comment
        fields = ['id', 'article', 'author', 'content', 'created_at']
        read_only_fields = ['id', 'author', 'created_at']


class ArticleDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for Article with nested comments."""
    
    author = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    tags = serializers.StringRelatedField(many=True, read_only=True)
    
    # Computed fields
    comment_count = serializers.IntegerField(source='comments.count', read_only=True)
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
        """Calculate estimated read time."""
        words_per_minute = 200
        word_count = len(obj.content.split())
        minutes = max(1, round(word_count / words_per_minute))
        return minutes
```

### Different Serializers for Different Actions

```python
# views.py
class ArticleViewSet(viewsets.ModelViewSet):
    """Article viewset with different serializers per action."""
    
    queryset = Article.objects.all()
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'retrieve':
            return ArticleDetailSerializer
        elif self.action == 'list':
            return ArticleListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ArticleWriteSerializer
        return ArticleSerializer
    
    def get_queryset(self):
        """Optimize queryset based on action."""
        queryset = super().get_queryset()
        
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related(
                'comments__author',
                'tags',
                'category'
            ).select_related('author')
        elif self.action == 'list':
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

## Pagination

### Page Number Pagination

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}
```

```python
# pagination.py
from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination class."""
    
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'


class LargeResultsSetPagination(PageNumberPagination):
    """Pagination for large result sets."""
    
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000
```

```python
# views.py
class ArticleListView(generics.ListAPIView):
    """List articles with custom pagination."""
    
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    pagination_class = StandardResultsSetPagination
```

### Limit Offset Pagination

```python
# pagination.py
from rest_framework.pagination import LimitOffsetPagination


class CustomLimitOffsetPagination(LimitOffsetPagination):
    """Custom limit offset pagination."""
    
    default_limit = 20
    max_limit = 100
    limit_query_param = 'limit'
    offset_query_param = 'offset'
```

### Cursor Pagination

```python
# pagination.py
from rest_framework.pagination import CursorPagination


class ArticleCursorPagination(CursorPagination):
    """Cursor-based pagination for articles."""
    
    page_size = 20
    ordering = '-created_at'
    cursor_query_param = 'cursor'
```

### Custom Pagination Response

```python
# pagination.py
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomPagination(PageNumberPagination):
    """Custom pagination with enhanced response."""
    
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        """Return custom paginated response."""
        return Response({
            'pagination': {
                'count': self.page.paginator.count,
                'page': self.page.number,
                'page_size': self.page.paginator.per_page,
                'total_pages': self.page.paginator.num_pages,
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
            },
            'results': data
        })
```

## Filtering and Searching

### Basic Filtering

```python
# Install django-filter
# pip install django-filter

# settings.py
INSTALLED_APPS = [
    # ...
    'django_filters',
]

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}
```

```python
# views.py
from django_filters.rest_framework import DjangoFilterBackend


class ArticleListView(generics.ListAPIView):
    """List articles with filtering."""
    
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'category', 'author']

# Usage: GET /api/articles/?status=published&category=1
```

### Custom FilterSet

```python
# filters.py
import django_filters
from .models import Article


class ArticleFilter(django_filters.FilterSet):
    """Custom filter for Article model."""
    
    # Exact match filters
    status = django_filters.CharFilter(field_name='status')
    author = django_filters.NumberFilter(field_name='author__id')
    
    # Range filters
    min_date = django_filters.DateFilter(field_name='published_at', lookup_expr='gte')
    max_date = django_filters.DateFilter(field_name='published_at', lookup_expr='lte')
    
    # Contains filters
    title = django_filters.CharFilter(field_name='title', lookup_expr='icontains')
    content = django_filters.CharFilter(field_name='content', lookup_expr='icontains')
    
    # Choice filters
    category = django_filters.ModelChoiceFilter(queryset=Category.objects.all())
    
    # Multiple choice filters
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )
    
    # Boolean filters
    is_featured = django_filters.BooleanFilter(field_name='is_featured')
    
    # Custom method filters
    search = django_filters.CharFilter(method='filter_search')
    
    class Meta:
        model = Article
        fields = ['status', 'author', 'category', 'tags', 'is_featured']
    
    def filter_search(self, queryset, name, value):
        """Custom search across multiple fields."""
        return queryset.filter(
            Q(title__icontains=value) |
            Q(content__icontains=value) |
            Q(excerpt__icontains=value)
        )
```

```python
# views.py
class ArticleListView(generics.ListAPIView):
    """List articles with custom filtering."""
    
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    filterset_class = ArticleFilter

# Usage:
# GET /api/articles/?status=published
# GET /api/articles/?min_date=2024-01-01&max_date=2024-12-31
# GET /api/articles/?title=django
# GET /api/articles/?tags=python,django
# GET /api/articles/?search=tutorial
```

### Search Filter

```python
# views.py
from rest_framework.filters import SearchFilter


class ArticleListView(generics.ListAPIView):
    """List articles with search."""
    
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    filter_backends = [SearchFilter]
    search_fields = ['title', 'content', 'author__username', 'category__name']

# Usage:
# GET /api/articles/?search=django
# Searches in title, content, author username, and category name
```

## Sorting and Ordering

### Ordering Filter

```python
# views.py
from rest_framework.filters import OrderingFilter


class ArticleListView(generics.ListAPIView):
    """List articles with ordering."""
    
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ['created_at', 'updated_at', 'published_at', 'title']
    ordering = ['-created_at']  # Default ordering

# Usage:
# GET /api/articles/?ordering=created_at
# GET /api/articles/?ordering=-created_at
# GET /api/articles/?ordering=title,-created_at
```

### Custom Ordering

```python
# views.py
class ArticleListView(generics.ListAPIView):
    """List articles with custom ordering logic."""
    
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    
    def get_queryset(self):
        """Apply custom ordering based on query parameters."""
        queryset = super().get_queryset()
        ordering = self.request.query_params.get('ordering', '-created_at')
        
        # Map custom ordering to actual fields
        ordering_map = {
            'popular': '-view_count',
            'trending': '-like_count',
            'newest': '-created_at',
            'oldest': 'created_at',
            'alphabetical': 'title',
        }
        
        if ordering in ordering_map:
            ordering = ordering_map[ordering]
        
        return queryset.order_by(ordering)

# Usage:
# GET /api/articles/?ordering=popular
# GET /api/articles/?ordering=trending
```

## Error Handling

### Custom Exception Handler

```python
# exceptions.py
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """Custom exception handler for DRF."""
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Customize error response format
        custom_response = {
            'error': {
                'status_code': response.status_code,
                'message': 'An error occurred',
                'details': response.data
            }
        }
        
        # Add specific messages for common errors
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
# settings.py
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'myapp.exceptions.custom_exception_handler',
}
```

### Custom Exceptions

```python
# exceptions.py
from rest_framework.exceptions import APIException
from rest_framework import status


class ServiceUnavailable(APIException):
    """Custom exception for service unavailable."""
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'Service temporarily unavailable, please try again later.'
    default_code = 'service_unavailable'


class ResourceConflict(APIException):
    """Custom exception for resource conflicts."""
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'Resource conflict.'
    default_code = 'resource_conflict'


class ValidationError(APIException):
    """Custom validation error."""
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = 'Validation error.'
    default_code = 'validation_error'
```

### Error Response Format

```python
# views.py
from rest_framework.response import Response
from rest_framework import status


class ArticleViewSet(viewsets.ModelViewSet):
    """Article viewset with consistent error responses."""
    
    def create(self, request, *args, **kwargs):
        """Create article with error handling."""
        serializer = self.get_serializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            return Response({
                'success': True,
                'data': serializer.data,
                'message': 'Article created successfully'
            }, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Validation failed',
                    'details': e.detail
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'An unexpected error occurred',
                    'details': str(e) if settings.DEBUG else None
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

## Rate Limiting

### DRF Throttling

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day',
    }
}
```

### Custom Throttle Classes

```python
# throttles.py
from rest_framework.throttling import UserRateThrottle


class BurstRateThrottle(UserRateThrottle):
    """Throttle for burst requests."""
    scope = 'burst'


class SustainedRateThrottle(UserRateThrottle):
    """Throttle for sustained requests."""
    scope = 'sustained'


class UploadRateThrottle(UserRateThrottle):
    """Throttle for upload endpoints."""
    scope = 'upload'
```

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day',
        'burst': '60/min',
        'sustained': '1000/day',
        'upload': '20/hour',
    }
}
```

```python
# views.py
class ArticleCreateView(generics.CreateAPIView):
    """Create article with rate limiting."""
    
    serializer_class = ArticleSerializer
    throttle_classes = [BurstRateThrottle, SustainedRateThrottle]
```

## API Documentation

### drf-spectacular (OpenAPI 3)

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
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'My API',
    'DESCRIPTION': 'API documentation for My Project',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
}
```

```python
# urls.py
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView
)

urlpatterns = [
    # Schema
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    
    # Swagger UI
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # ReDoc UI
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
```

### Documenting Endpoints

```python
# views.py
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes


class ArticleViewSet(viewsets.ModelViewSet):
    """ViewSet for managing articles."""
    
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    
    @extend_schema(
        summary='List articles',
        description='Retrieve a paginated list of articles with filtering and search.',
        parameters=[
            OpenApiParameter(
                name='status',
                type=OpenApiTypes.STR,
                description='Filter by status',
                enum=['draft', 'published', 'archived']
            ),
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                description='Search in title and content'
            ),
        ],
        responses={200: ArticleSerializer(many=True)},
        tags=['Articles']
    )
    def list(self, request, *args, **kwargs):
        """List all articles."""
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        summary='Create article',
        description='Create a new article.',
        request=ArticleWriteSerializer,
        responses={
            201: ArticleSerializer,
            400: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                'Article Example',
                value={
                    'title': 'My Article',
                    'content': 'Article content here...',
                    'status': 'draft',
                    'category_id': 1
                },
                request_only=True
            )
        ],
        tags=['Articles']
    )
    def create(self, request, *args, **kwargs):
        """Create a new article."""
        return super().create(request, *args, **kwargs)
```

## Best Practices

### Consistent Response Format

```python
# utils.py
from rest_framework.response import Response


def success_response(data=None, message='Success', status=200):
    """Standard success response."""
    return Response({
        'success': True,
        'message': message,
        'data': data
    }, status=status)


def error_response(message='Error', errors=None, status=400):
    """Standard error response."""
    return Response({
        'success': False,
        'message': message,
        'errors': errors
    }, status=status)
```

### API Naming Conventions

```python
# ✅ GOOD: Consistent naming
urlpatterns = [
    path('api/v1/articles/', ArticleListCreateView.as_view()),
    path('api/v1/articles/<int:pk>/', ArticleDetailView.as_view()),
    path('api/v1/users/', UserListCreateView.as_view()),
    path('api/v1/users/<int:pk>/', UserDetailView.as_view()),
]

# ❌ BAD: Inconsistent naming
urlpatterns = [
    path('api/article/', get_articles),
    path('api/getArticle/<int:id>/', get_article),
    path('api/user_list/', list_users),
]
```

### HATEOAS (Hypermedia)

```python
# serializers.py
class ArticleSerializer(serializers.ModelSerializer):
    """Article serializer with hypermedia links."""
    
    url = serializers.HyperlinkedIdentityField(
        view_name='api:article-detail',
        lookup_field='pk'
    )
    author_url = serializers.HyperlinkedRelatedField(
        source='author',
        view_name='api:user-detail',
        read_only=True
    )
    
    class Meta:
        model = Article
        fields = ['id', 'url', 'title', 'content', 'author_url', 'created_at']
```

### Field Selection

```python
# views.py
class DynamicFieldsViewSet(viewsets.ModelViewSet):
    """ViewSet with dynamic field selection."""
    
    def get_serializer(self, *args, **kwargs):
        """Allow dynamic field selection via query params."""
        serializer = super().get_serializer(*args, **kwargs)
        
        fields = self.request.query_params.get('fields')
        if fields:
            allowed = set(fields.split(','))
            existing = set(serializer.fields.keys())
            for field in existing - allowed:
                serializer.fields.pop(field)
        
        return serializer

# Usage: GET /api/articles/?fields=id,title,created_at
```

### Caching

```python
# views.py
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie


class ArticleListView(generics.ListAPIView):
    """List articles with caching."""
    
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    
    @method_decorator(cache_page(60 * 15))  # Cache for 15 minutes
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class UserArticleListView(generics.ListAPIView):
    """List user's articles with per-user caching."""
    
    @method_decorator(vary_on_cookie)
    @method_decorator(cache_page(60 * 5))
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
```

### Performance Optimization

```python
# views.py
class ArticleViewSet(viewsets.ModelViewSet):
    """Optimized article viewset."""
    
    def get_queryset(self):
        """Optimize queryset with select_related and prefetch_related."""
        queryset = Article.objects.all()
        
        if self.action == 'list':
            # Optimize list view
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
            # Optimize detail view
            queryset = queryset.select_related(
                'author',
                'category'
            ).prefetch_related(
                'tags',
                'comments__author'
            )
        
        return queryset
```

### API Security

```python
# ✅ GOOD: Secure API configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day',
    },
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}
```
