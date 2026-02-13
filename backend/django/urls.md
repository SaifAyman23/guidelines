# Django URL Configuration Guidelines

## Table of Contents
- [Overview](#overview)
- [URL Patterns](#url-patterns)
- [Path Converters](#path-converters)
- [URL Naming](#url-naming)
- [URL Namespaces](#url-namespaces)
- [Including URLconfs](#including-urlconfs)
- [Advanced Patterns](#advanced-patterns)
- [URL Reversing](#url-reversing)
- [Best Practices](#best-practices)

## Overview

URL configuration (URLconf) is Django's routing mechanism that maps URL patterns to views. A clean URLconf is essential for maintainable applications and good API design.

## URL Patterns

### Basic URL Patterns

```python
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
]
```

### Using path() vs re_path()

```python
from django.urls import path, re_path
from . import views

urlpatterns = [
    # path() - Modern, cleaner syntax (preferred)
    path('articles/<int:year>/', views.year_archive, name='article-year'),
    path('articles/<int:year>/<int:month>/', views.month_archive, name='article-month'),
    path('articles/<slug:slug>/', views.article_detail, name='article-detail'),
    
    # re_path() - Use only when regex is necessary
    re_path(r'^articles/(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/$', 
            views.month_archive, 
            name='article-month-regex'),
    re_path(r'^articles/(?P<slug>[\w-]+)/$', 
            views.article_detail, 
            name='article-detail-regex'),
]
```

### Path with Multiple Parameters

```python
from django.urls import path
from . import views

urlpatterns = [
    # Blog article with year, month, and slug
    path('blog/<int:year>/<int:month>/<slug:slug>/', 
         views.article_detail, 
         name='article-detail'),
    
    # User profile with username
    path('users/<str:username>/', 
         views.user_profile, 
         name='user-profile'),
    
    # Product with category and product slug
    path('shop/<slug:category>/<slug:product>/', 
         views.product_detail, 
         name='product-detail'),
]
```

## Path Converters

### Built-in Path Converters

```python
from django.urls import path
from . import views

urlpatterns = [
    # str - Matches any non-empty string (excluding '/')
    path('articles/<str:title>/', views.article_by_title),
    
    # int - Matches zero or any positive integer
    path('articles/<int:id>/', views.article_by_id),
    
    # slug - Matches slug strings (letters, numbers, hyphens, underscores)
    path('articles/<slug:slug>/', views.article_detail),
    
    # uuid - Matches a UUID
    path('objects/<uuid:uuid>/', views.object_detail),
    
    # path - Matches any non-empty string (including '/')
    path('files/<path:filepath>/', views.file_view),
]
```

### Custom Path Converters

```python
# converters.py
class FourDigitYearConverter:
    """Custom converter for 4-digit years."""
    regex = '[0-9]{4}'
    
    def to_python(self, value):
        return int(value)
    
    def to_url(self, value):
        return '%04d' % value


class MonthConverter:
    """Custom converter for months (01-12)."""
    regex = '0[1-9]|1[0-2]'
    
    def to_python(self, value):
        return int(value)
    
    def to_url(self, value):
        return '%02d' % value


class UsernameConverter:
    """Custom converter for usernames (alphanumeric and underscore)."""
    regex = '[a-zA-Z0-9_]+'
    
    def to_python(self, value):
        return value.lower()
    
    def to_url(self, value):
        return str(value)
```

### Registering Custom Converters

```python
# urls.py
from django.urls import path, register_converter
from . import views, converters

# Register custom converters
register_converter(converters.FourDigitYearConverter, 'yyyy')
register_converter(converters.MonthConverter, 'mm')
register_converter(converters.UsernameConverter, 'username')

urlpatterns = [
    # Use custom converters
    path('articles/<yyyy:year>/', views.year_archive, name='year-archive'),
    path('articles/<yyyy:year>/<mm:month>/', views.month_archive, name='month-archive'),
    path('users/<username:username>/', views.user_profile, name='user-profile'),
]
```

## URL Naming

### Naming Conventions

```python
from django.urls import path
from . import views

urlpatterns = [
    # List views: model-list
    path('articles/', views.ArticleListView.as_view(), name='article-list'),
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    
    # Detail views: model-detail
    path('articles/<slug:slug>/', views.ArticleDetailView.as_view(), name='article-detail'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    
    # Create views: model-create
    path('articles/new/', views.ArticleCreateView.as_view(), name='article-create'),
    
    # Update views: model-update
    path('articles/<slug:slug>/edit/', views.ArticleUpdateView.as_view(), name='article-update'),
    
    # Delete views: model-delete
    path('articles/<slug:slug>/delete/', views.ArticleDeleteView.as_view(), name='article-delete'),
    
    # Custom action views: model-action
    path('articles/<slug:slug>/publish/', views.article_publish, name='article-publish'),
    path('articles/<slug:slug>/archive/', views.article_archive, name='article-archive'),
]
```

### API URL Naming

```python
from django.urls import path
from . import api_views

urlpatterns = [
    # API endpoints should include 'api' prefix in name
    path('api/articles/', api_views.ArticleListCreateAPIView.as_view(), name='api-article-list'),
    path('api/articles/<int:pk>/', api_views.ArticleDetailAPIView.as_view(), name='api-article-detail'),
    
    # Nested resources
    path('api/articles/<int:article_pk>/comments/', 
         api_views.CommentListCreateAPIView.as_view(), 
         name='api-article-comment-list'),
    path('api/articles/<int:article_pk>/comments/<int:pk>/', 
         api_views.CommentDetailAPIView.as_view(), 
         name='api-article-comment-detail'),
]
```

## URL Namespaces

### Application Namespaces

```python
# articles/urls.py
from django.urls import path
from . import views

app_name = 'articles'

urlpatterns = [
    path('', views.ArticleListView.as_view(), name='list'),
    path('<slug:slug>/', views.ArticleDetailView.as_view(), name='detail'),
    path('create/', views.ArticleCreateView.as_view(), name='create'),
    path('<slug:slug>/edit/', views.ArticleUpdateView.as_view(), name='update'),
    path('<slug:slug>/delete/', views.ArticleDeleteView.as_view(), name='delete'),
]
```

```python
# project/urls.py
from django.urls import path, include

urlpatterns = [
    path('articles/', include('articles.urls')),
    # URLs are now accessible as 'articles:list', 'articles:detail', etc.
]
```

### Instance Namespaces

```python
# project/urls.py
from django.urls import path, include

urlpatterns = [
    # Different instances of the same URLconf
    path('blog/', include('articles.urls', namespace='blog')),
    path('news/', include('articles.urls', namespace='news')),
    path('tutorials/', include('articles.urls', namespace='tutorials')),
]
```

### Nested Namespaces

```python
# project/urls.py
from django.urls import path, include

urlpatterns = [
    path('api/v1/', include('api.v1.urls', namespace='api-v1')),
    path('api/v2/', include('api.v2.urls', namespace='api-v2')),
]
```

```python
# api/v1/urls.py
from django.urls import path, include

app_name = 'api-v1'

urlpatterns = [
    path('articles/', include('api.v1.articles.urls', namespace='articles')),
    path('users/', include('api.v1.users.urls', namespace='users')),
]
# URLs accessible as 'api-v1:articles:list', 'api-v1:users:detail', etc.
```

## Including URLconfs

### Basic Include

```python
# project/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('articles/', include('articles.urls')),
    path('users/', include('users.urls')),
    path('api/', include('api.urls')),
]
```

### Include with Namespace

```python
from django.urls import path, include

urlpatterns = [
    path('blog/', include('articles.urls', namespace='blog')),
    path('api/v1/', include('api.v1.urls', namespace='api-v1')),
]
```

### Include Multiple Patterns

```python
from django.urls import path, include
from articles import views as article_views

# Define extra patterns
extra_patterns = [
    path('reports/', article_views.reports, name='article-reports'),
    path('stats/', article_views.stats, name='article-stats'),
]

urlpatterns = [
    path('articles/', include([
        path('', include('articles.urls')),
        path('', include(extra_patterns)),
    ])),
]
```

### Conditional Includes

```python
from django.conf import settings
from django.urls import path, include

urlpatterns = [
    path('api/', include('api.urls')),
]

# Include debug toolbar only in DEBUG mode
if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]

# Include silk profiler if installed
if 'silk' in settings.INSTALLED_APPS:
    urlpatterns += [
        path('silk/', include('silk.urls', namespace='silk')),
    ]
```

## Advanced Patterns

### Optional Parameters

```python
from django.urls import path, re_path
from . import views

urlpatterns = [
    # Using re_path for optional page parameter
    re_path(r'^articles/(?:page/(?P<page>\d+)/)?$', 
            views.article_list, 
            name='article-list'),
    
    # Optional format parameter
    re_path(r'^api/articles/(?P<pk>\d+)(?:\.(?P<format>json|xml))?/$',
            views.article_api_detail,
            name='api-article-detail'),
]
```

### Multiple URL Patterns for Same View

```python
from django.urls import path
from . import views

urlpatterns = [
    # Different URLs pointing to same view
    path('articles/', views.article_list, name='article-list'),
    path('posts/', views.article_list, name='post-list'),  # Alias
    
    # Same view with different default parameters
    path('articles/published/', 
         views.article_list, 
         {'filter': 'published'}, 
         name='published-articles'),
    path('articles/draft/', 
         views.article_list, 
         {'filter': 'draft'}, 
         name='draft-articles'),
]
```

### Passing Extra Options to Views

```python
from django.urls import path
from . import views

urlpatterns = [
    path('articles/', 
         views.article_list, 
         {'filter': 'all', 'page_size': 10},
         name='article-list'),
    
    path('articles/featured/', 
         views.article_list, 
         {'filter': 'featured', 'page_size': 5},
         name='featured-articles'),
    
    path('articles/<slug:slug>/', 
         views.article_detail,
         {'show_comments': True},
         name='article-detail'),
]
```

### Class-Based View URLs

```python
from django.urls import path
from . import views

urlpatterns = [
    # Basic CBV
    path('articles/', views.ArticleListView.as_view(), name='article-list'),
    
    # CBV with kwargs
    path('articles/featured/', 
         views.ArticleListView.as_view(filter='featured'),
         name='featured-articles'),
    
    # CBV with custom template
    path('articles/archive/', 
         views.ArticleListView.as_view(
             template_name='articles/archive.html',
             paginate_by=20
         ),
         name='article-archive'),
]
```

### DRF Router URLs

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import viewsets

# Create router
router = DefaultRouter()
router.register(r'articles', viewsets.ArticleViewSet, basename='article')
router.register(r'categories', viewsets.CategoryViewSet, basename='category')
router.register(r'tags', viewsets.TagViewSet, basename='tag')

urlpatterns = [
    path('api/', include(router.urls)),
]

# Generates URLs:
# /api/articles/ - list, create
# /api/articles/{pk}/ - retrieve, update, delete
# /api/categories/ - list, create
# /api/categories/{pk}/ - retrieve, update, delete
```

### Nested Routers

```python
from rest_framework_nested import routers
from . import viewsets

# Main router
router = routers.DefaultRouter()
router.register(r'articles', viewsets.ArticleViewSet, basename='article')

# Nested router for comments
articles_router = routers.NestedDefaultRouter(
    router, 
    r'articles', 
    lookup='article'
)
articles_router.register(
    r'comments', 
    viewsets.CommentViewSet, 
    basename='article-comments'
)

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/', include(articles_router.urls)),
]

# Generates URLs:
# /api/articles/{article_pk}/comments/ - list, create
# /api/articles/{article_pk}/comments/{pk}/ - retrieve, update, delete
```

## URL Reversing

### Basic URL Reversing

```python
from django.urls import reverse
from django.shortcuts import redirect

# In views
def my_view(request):
    # Reverse URL by name
    url = reverse('article-list')
    
    # Reverse with arguments
    url = reverse('article-detail', kwargs={'slug': 'my-article'})
    url = reverse('article-detail', args=['my-article'])
    
    # Redirect to reversed URL
    return redirect('article-detail', slug='my-article')
```

### Reversing with Namespaces

```python
from django.urls import reverse

# Reverse with app namespace
url = reverse('articles:list')
url = reverse('articles:detail', kwargs={'slug': 'my-article'})

# Reverse with instance namespace
url = reverse('blog:articles:list')
url = reverse('api-v1:articles:detail', kwargs={'pk': 1})
```

### Reversing in Templates

```django
{% load static %}

<!-- Basic reverse -->
<a href="{% url 'article-list' %}">Articles</a>

<!-- With arguments -->
<a href="{% url 'article-detail' slug=article.slug %}">{{ article.title }}</a>

<!-- With namespaces -->
<a href="{% url 'articles:list' %}">All Articles</a>
<a href="{% url 'blog:articles:detail' slug=article.slug %}">Read More</a>

<!-- With query parameters (manual) -->
<a href="{% url 'article-list' %}?page=2&filter=published">Page 2</a>
```

### Reversing in Models

```python
from django.db import models
from django.urls import reverse

class Article(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    
    def get_absolute_url(self):
        """Return canonical URL for this article."""
        return reverse('articles:detail', kwargs={'slug': self.slug})
    
    def get_edit_url(self):
        """Return edit URL for this article."""
        return reverse('articles:update', kwargs={'slug': self.slug})
    
    def get_delete_url(self):
        """Return delete URL for this article."""
        return reverse('articles:delete', kwargs={'slug': self.slug})
```

### Reverse URL with Current Request

```python
from django.urls import reverse

def my_view(request):
    # Build absolute URL
    absolute_url = request.build_absolute_uri(
        reverse('article-detail', kwargs={'slug': 'my-article'})
    )
    # Returns: http://example.com/articles/my-article/
    
    # Get current URL name
    from django.urls import resolve
    current_url_name = resolve(request.path_info).url_name
```

## Best Practices

### URL Structure Best Practices

```python
from django.urls import path, include
from . import views

# ✅ GOOD: Clear, RESTful URL structure
urlpatterns = [
    # Collection URLs
    path('articles/', views.ArticleListView.as_view(), name='article-list'),
    path('articles/create/', views.ArticleCreateView.as_view(), name='article-create'),
    
    # Resource URLs
    path('articles/<slug:slug>/', views.ArticleDetailView.as_view(), name='article-detail'),
    path('articles/<slug:slug>/edit/', views.ArticleUpdateView.as_view(), name='article-update'),
    path('articles/<slug:slug>/delete/', views.ArticleDeleteView.as_view(), name='article-delete'),
    
    # Action URLs
    path('articles/<slug:slug>/publish/', views.article_publish, name='article-publish'),
    path('articles/<slug:slug>/unpublish/', views.article_unpublish, name='article-unpublish'),
]

# ❌ BAD: Inconsistent, unclear structure
urlpatterns = [
    path('article-list/', views.article_list),
    path('new-article/', views.article_create),
    path('article/<int:id>/', views.article_view),
    path('edit/<int:id>/', views.article_edit),
    path('delete-article/<int:id>/', views.article_delete),
]
```

### Trailing Slashes

```python
from django.urls import path
from . import views

# ✅ GOOD: Consistent use of trailing slashes
urlpatterns = [
    path('articles/', views.article_list, name='article-list'),
    path('articles/<slug:slug>/', views.article_detail, name='article-detail'),
    path('about/', views.about, name='about'),
]

# Set in settings.py
APPEND_SLASH = True  # Redirects /articles to /articles/

# For APIs, consider no trailing slash
# api/urls.py
urlpatterns = [
    path('articles', views.article_list, name='api-article-list'),
    path('articles/<int:pk>', views.article_detail, name='api-article-detail'),
]
```

### API Versioning

```python
# ✅ GOOD: URL-based versioning
# project/urls.py
from django.urls import path, include

urlpatterns = [
    path('api/v1/', include('api.v1.urls', namespace='api-v1')),
    path('api/v2/', include('api.v2.urls', namespace='api-v2')),
]

# api/v1/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import viewsets

router = DefaultRouter()
router.register(r'articles', viewsets.ArticleViewSet)
router.register(r'users', viewsets.UserViewSet)

app_name = 'api-v1'
urlpatterns = [
    path('', include(router.urls)),
]
```

### URL Organization

```python
# ✅ GOOD: Organized by feature/app
# project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Apps
    path('', include('core.urls')),
    path('articles/', include('articles.urls')),
    path('users/', include('users.urls')),
    
    # API
    path('api/v1/', include('api.v1.urls')),
    
    # Third-party
    path('accounts/', include('allauth.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
```

### Security Considerations

```python
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
from . import views

urlpatterns = [
    # ✅ GOOD: CSRF protection enabled by default
    path('articles/create/', views.ArticleCreateView.as_view(), name='article-create'),
    
    # ⚠️ Use csrf_exempt only when absolutely necessary (e.g., webhooks)
    path('webhooks/stripe/', 
         csrf_exempt(views.stripe_webhook), 
         name='stripe-webhook'),
    
    # ✅ GOOD: Never cache sensitive pages
    path('dashboard/', 
         never_cache(views.DashboardView.as_view()), 
         name='dashboard'),
]
```

### Internationalization (i18n)

```python
# settings.py
USE_I18N = True
LANGUAGES = [
    ('en', 'English'),
    ('es', 'Spanish'),
    ('fr', 'French'),
]

# urls.py
from django.conf.urls.i18n import i18n_patterns
from django.urls import path, include

urlpatterns = [
    path('api/', include('api.urls')),  # Not translated
]

# Add language prefix to these URLs
urlpatterns += i18n_patterns(
    path('', include('core.urls')),
    path('articles/', include('articles.urls')),
    path('about/', views.about, name='about'),
)

# Generates URLs like:
# /en/articles/
# /es/articles/
# /fr/articles/
```

### Custom Error Pages

```python
# project/urls.py
from django.urls import path
from . import views

handler404 = 'myapp.views.custom_404'
handler500 = 'myapp.views.custom_500'
handler403 = 'myapp.views.custom_403'
handler400 = 'myapp.views.custom_400'

urlpatterns = [
    # Your URL patterns here
]
```

```python
# views.py
from django.shortcuts import render

def custom_404(request, exception):
    return render(request, 'errors/404.html', status=404)

def custom_500(request):
    return render(request, 'errors/500.html', status=500)

def custom_403(request, exception):
    return render(request, 'errors/403.html', status=403)

def custom_400(request, exception):
    return render(request, 'errors/400.html', status=400)
```

### Performance Optimization

```python
from django.urls import path
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from . import views

urlpatterns = [
    # Cache static pages
    path('about/', 
         cache_page(60 * 60)(views.AboutView.as_view()), 
         name='about'),
    
    # Cache with vary on cookie for authenticated users
    path('dashboard/', 
         vary_on_cookie(cache_page(60 * 5)(views.DashboardView.as_view())),
         name='dashboard'),
    
    # Don't cache dynamic content
    path('articles/', views.ArticleListView.as_view(), name='article-list'),
]
```

### Testing URLs

```python
from django.test import TestCase
from django.urls import reverse, resolve

class URLTests(TestCase):
    """Test URL configuration."""
    
    def test_article_list_url(self):
        """Test article list URL resolves correctly."""
        url = reverse('articles:list')
        self.assertEqual(url, '/articles/')
        self.assertEqual(resolve(url).view_name, 'articles:list')
    
    def test_article_detail_url(self):
        """Test article detail URL with slug."""
        url = reverse('articles:detail', kwargs={'slug': 'test-article'})
        self.assertEqual(url, '/articles/test-article/')
    
    def test_api_url_versioning(self):
        """Test API versioning in URLs."""
        url_v1 = reverse('api-v1:articles:list')
        url_v2 = reverse('api-v2:articles:list')
        self.assertEqual(url_v1, '/api/v1/articles/')
        self.assertEqual(url_v2, '/api/v2/articles/')
    
    def test_url_parameters(self):
        """Test URL with multiple parameters."""
        url = reverse('blog:article-by-date', kwargs={
            'year': 2024,
            'month': 1,
            'slug': 'my-article'
        })
        self.assertEqual(url, '/blog/2024/1/my-article/')
```

### Documentation

```python
"""
URL Configuration for Articles App

Available URLs:
- articles:list - List all articles
- articles:detail - Article detail page (requires slug)
- articles:create - Create new article (login required)
- articles:update - Update article (requires slug, login required)
- articles:delete - Delete article (requires slug, login required)
- articles:publish - Publish article (requires slug, staff only)
- articles:archive - Archive article (requires slug, staff only)

API URLs:
- api-articles:list - API list/create articles
- api-articles:detail - API retrieve/update/delete article (requires pk)
"""

from django.urls import path
from . import views

app_name = 'articles'

urlpatterns = [
    path('', views.ArticleListView.as_view(), name='list'),
    path('create/', views.ArticleCreateView.as_view(), name='create'),
    path('<slug:slug>/', views.ArticleDetailView.as_view(), name='detail'),
    path('<slug:slug>/edit/', views.ArticleUpdateView.as_view(), name='update'),
    path('<slug:slug>/delete/', views.ArticleDeleteView.as_view(), name='delete'),
    path('<slug:slug>/publish/', views.article_publish, name='publish'),
    path('<slug:slug>/archive/', views.article_archive, name='archive'),
]
```
