# Django Views Guidelines

## Table of Contents
- [Overview](#overview)
- [Function-Based Views (FBVs)](#function-based-views-fbvs)
- [Class-Based Views (CBVs)](#class-based-views-cbvs)
- [Generic Views](#generic-views)
- [API Views (DRF)](#api-views-drf)
- [Mixins](#mixins)
- [Permissions and Authentication](#permissions-and-authentication)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)

## Overview

Views are the bridge between your models and templates. They handle HTTP requests and return HTTP responses.

## Function-Based Views (FBVs)

### Basic FBV

```python
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from .models import Article
from .forms import ArticleForm

def article_list(request):
    """Display list of articles"""
    articles = Article.objects.filter(status='published')
    context = {
        'articles': articles,
        'title': 'Articles'
    }
    return render(request, 'articles/list.html', context)

def article_detail(request, slug):
    """Display single article"""
    article = get_object_or_404(Article, slug=slug, status='published')
    return render(request, 'articles/detail.html', {'article': article})
```

### FBV with Form Handling

```python
from django.contrib import messages

def article_create(request):
    """Create new article"""
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.save()
            form.save_m2m()  # Save many-to-many relationships
            messages.success(request, 'Article created successfully!')
            return redirect('article-detail', slug=article.slug)
    else:
        form = ArticleForm()
    
    return render(request, 'articles/form.html', {'form': form})

def article_update(request, slug):
    """Update existing article"""
    article = get_object_or_404(Article, slug=slug)
    
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            form.save()
            messages.success(request, 'Article updated successfully!')
            return redirect('article-detail', slug=article.slug)
    else:
        form = ArticleForm(instance=article)
    
    return render(request, 'articles/form.html', {
        'form': form,
        'article': article
    })

def article_delete(request, slug):
    """Delete article"""
    article = get_object_or_404(Article, slug=slug)
    
    if request.method == 'POST':
        article.delete()
        messages.success(request, 'Article deleted successfully!')
        return redirect('article-list')
    
    return render(request, 'articles/confirm_delete.html', {
        'article': article
    })
```

### FBV with Decorators

```python
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.cache import cache_page

@login_required
@require_http_methods(["GET", "POST"])
def article_create(request):
    """Create article - requires authentication"""
    # ... view logic

@permission_required('articles.can_publish', raise_exception=True)
def article_publish(request, slug):
    """Publish article - requires permission"""
    article = get_object_or_404(Article, slug=slug)
    article.status = 'published'
    article.save()
    return redirect('article-detail', slug=slug)

@cache_page(60 * 15)  # Cache for 15 minutes
def article_list(request):
    """Cached article list"""
    articles = Article.objects.filter(status='published')
    return render(request, 'articles/list.html', {'articles': articles})

@require_POST
def article_like(request, slug):
    """Like article - POST only"""
    article = get_object_or_404(Article, slug=slug)
    article.likes += 1
    article.save()
    return JsonResponse({'likes': article.likes})
```

## Class-Based Views (CBVs)

### Basic CBV

```python
from django.views import View
from django.views.generic import TemplateView

class ArticleListView(View):
    """Basic class-based view"""
    
    def get(self, request):
        articles = Article.objects.filter(status='published')
        return render(request, 'articles/list.html', {
            'articles': articles
        })
    
    def post(self, request):
        # Handle POST request
        pass

class AboutView(TemplateView):
    """Simple template view"""
    template_name = 'about.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team_size'] = 10
        return context
```

### CBV with Mixins

```python
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy

class ArticleCreateView(LoginRequiredMixin, CreateView):
    """Create article view"""
    model = Article
    form_class = ArticleForm
    template_name = 'articles/form.html'
    success_url = reverse_lazy('article-list')
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, 'Article created successfully!')
        return super().form_valid(form)

class ArticleUpdateView(LoginRequiredMixin, UpdateView):
    """Update article view"""
    model = Article
    form_class = ArticleForm
    template_name = 'articles/form.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        # Only allow users to edit their own articles
        return Article.objects.filter(author=self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('article-detail', kwargs={'slug': self.object.slug})

class ArticleDeleteView(LoginRequiredMixin, DeleteView):
    """Delete article view"""
    model = Article
    template_name = 'articles/confirm_delete.html'
    success_url = reverse_lazy('article-list')
    
    def get_queryset(self):
        return Article.objects.filter(author=self.request.user)
```

## Generic Views

### ListView

```python
from django.views.generic import ListView
from django.db.models import Q

class ArticleListView(ListView):
    """Display list of articles"""
    model = Article
    template_name = 'articles/list.html'
    context_object_name = 'articles'
    paginate_by = 10
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(status='published')
        
        # Search functionality
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(content__icontains=query)
            )
        
        # Filter by category
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['search_query'] = self.request.GET.get('q', '')
        return context
```

### DetailView

```python
from django.views.generic import DetailView

class ArticleDetailView(DetailView):
    """Display article detail"""
    model = Article
    template_name = 'articles/detail.html'
    context_object_name = 'article'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        # Only show published articles to non-authors
        queryset = super().get_queryset()
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(status='published')
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add related articles
        context['related_articles'] = Article.objects.filter(
            category=self.object.category
        ).exclude(pk=self.object.pk)[:5]
        return context
    
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        # Increment view count
        self.object.increment_views()
        return response
```

### CreateView

```python
from django.views.generic.edit import CreateView

class ArticleCreateView(LoginRequiredMixin, CreateView):
    """Create new article"""
    model = Article
    form_class = ArticleForm
    template_name = 'articles/form.html'
    
    def form_valid(self, form):
        """Set the author before saving"""
        form.instance.author = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, 'Article created successfully!')
        return response
    
    def get_success_url(self):
        return reverse_lazy('article-detail', kwargs={'slug': self.object.slug})
    
    def get_initial(self):
        """Set initial form values"""
        initial = super().get_initial()
        initial['status'] = 'draft'
        return initial
```

### UpdateView

```python
from django.views.generic.edit import UpdateView
from django.core.exceptions import PermissionDenied

class ArticleUpdateView(LoginRequiredMixin, UpdateView):
    """Update article"""
    model = Article
    form_class = ArticleForm
    template_name = 'articles/form.html'
    
    def get_object(self, queryset=None):
        """Ensure user can only edit their own articles"""
        obj = super().get_object(queryset)
        if obj.author != self.request.user and not self.request.user.is_staff:
            raise PermissionDenied
        return obj
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Article updated successfully!')
        return response
    
    def get_success_url(self):
        return reverse_lazy('article-detail', kwargs={'slug': self.object.slug})
```

## API Views (DRF)

### APIView

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ArticleSerializer

class ArticleListAPIView(APIView):
    """List and create articles"""
    
    def get(self, request):
        """Get list of articles"""
        articles = Article.objects.filter(status='published')
        serializer = ArticleSerializer(articles, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """Create new article"""
        serializer = ArticleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ArticleDetailAPIView(APIView):
    """Retrieve, update, delete article"""
    
    def get_object(self, slug):
        """Get article by slug"""
        try:
            return Article.objects.get(slug=slug)
        except Article.DoesNotExist:
            return None
    
    def get(self, request, slug):
        """Get article detail"""
        article = self.get_object(slug)
        if article is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = ArticleSerializer(article)
        return Response(serializer.data)
    
    def put(self, request, slug):
        """Update article"""
        article = self.get_object(slug)
        if article is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        serializer = ArticleSerializer(article, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, slug):
        """Delete article"""
        article = self.get_object(slug)
        if article is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        article.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
```

### Generic API Views

```python
from rest_framework import generics
from rest_framework.permissions import IsAuthenticatedOrReadOnly

class ArticleListCreateAPIView(generics.ListCreateAPIView):
    """List and create articles"""
    queryset = Article.objects.filter(status='published')
    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_fields = ['category', 'author']
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'title']
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class ArticleRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, delete article"""
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    lookup_field = 'slug'
    
    def perform_update(self, serializer):
        serializer.save()
```

### ViewSets

```python
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

class ArticleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for article operations.
    Provides list, create, retrieve, update, destroy actions.
    """
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    lookup_field = 'slug'
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        """Filter queryset based on user"""
        queryset = super().get_queryset()
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(status='published')
        return queryset
    
    def perform_create(self, serializer):
        """Set author on creation"""
        serializer.save(author=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def publish(self, request, slug=None):
        """Custom action to publish article"""
        article = self.get_object()
        article.status = 'published'
        article.save()
        serializer = self.get_serializer(article)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def like(self, request, slug=None):
        """Custom action to like article"""
        article = self.get_object()
        article.likes += 1
        article.save()
        return Response({'likes': article.likes})
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Custom action to get recent articles"""
        recent_articles = self.get_queryset().order_by('-created_at')[:10]
        serializer = self.get_serializer(recent_articles, many=True)
        return Response(serializer.data)
```

## Mixins

### Custom Mixins

```python
class FormValidMessageMixin:
    """Add success message on form validation"""
    success_message = ''
    
    def form_valid(self, form):
        response = super().form_valid(form)
        success_message = self.get_success_message(form.cleaned_data)
        if success_message:
            messages.success(self.request, success_message)
        return response
    
    def get_success_message(self, cleaned_data):
        return self.success_message % cleaned_data

class AuthorRequiredMixin:
    """Ensure user is the author of the object"""
    
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.author != request.user and not request.user.is_staff:
            raise PermissionDenied("You don't have permission to access this.")
        return super().dispatch(request, *args, **kwargs)

class AjaxableResponseMixin:
    """Mixin to add AJAX support to a form"""
    
    def form_invalid(self, form):
        response = super().form_invalid(form)
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(form.errors, status=400)
        return response
    
    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            data = {
                'message': 'Success!',
                'object_id': self.object.pk
            }
            return JsonResponse(data)
        return response

# Usage
class ArticleCreateView(
    LoginRequiredMixin,
    FormValidMessageMixin,
    AjaxableResponseMixin,
    CreateView
):
    model = Article
    form_class = ArticleForm
    success_message = 'Article "%(title)s" created successfully!'
```

## Permissions and Authentication

### Custom Permissions

```python
from rest_framework import permissions

class IsAuthorOrReadOnly(permissions.BasePermission):
    """Custom permission to only allow authors to edit their articles"""
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only to author
        return obj.author == request.user

class IsPublishedOrAuthor(permissions.BasePermission):
    """Allow access to published articles or article author"""
    
    def has_object_permission(self, request, view, obj):
        # Published articles are visible to everyone
        if obj.status == 'published':
            return True
        
        # Unpublished articles only visible to author
        return obj.author == request.user

# Usage
class ArticleViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthorOrReadOnly]
```

### Authentication in Views

```python
from django.contrib.auth.mixins import UserPassesTestMixin

class StaffRequiredMixin(UserPassesTestMixin):
    """Require user to be staff"""
    
    def test_func(self):
        return self.request.user.is_staff

class ArticlePublishView(StaffRequiredMixin, UpdateView):
    """Only staff can publish articles"""
    model = Article
    fields = ['status']
```

## Error Handling

### Custom Error Views

```python
from django.shortcuts import render

def handler404(request, exception):
    """Custom 404 error handler"""
    return render(request, 'errors/404.html', status=404)

def handler500(request):
    """Custom 500 error handler"""
    return render(request, 'errors/500.html', status=500)

def handler403(request, exception):
    """Custom 403 error handler"""
    return render(request, 'errors/403.html', status=403)
```

### Try-Except in Views

```python
from django.core.exceptions import ValidationError
from django.db import IntegrityError

def article_create(request):
    if request.method == 'POST':
        form = ArticleForm(request.POST)
        try:
            if form.is_valid():
                article = form.save(commit=False)
                article.author = request.user
                article.save()
                return redirect('article-detail', slug=article.slug)
        except IntegrityError:
            messages.error(request, 'An article with this slug already exists.')
        except ValidationError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, 'An unexpected error occurred.')
            # Log the error
            logger.error(f'Error creating article: {str(e)}')
    else:
        form = ArticleForm()
    
    return render(request, 'articles/form.html', {'form': form})
```

## Best Practices

### 1. Use Appropriate View Type

```python
# Use FBVs for simple, one-off views
def simple_view(request):
    return render(request, 'simple.html')

# Use CBVs for CRUD operations
class ArticleListView(ListView):
    model = Article

# Use ViewSets for APIs
class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
```

### 2. Keep Views Thin

```python
# Bad - too much logic in view
def article_create(request):
    if request.method == 'POST':
        # Lots of business logic here
        # Data processing
        # Multiple database queries
        # Email sending
        pass

# Good - move logic to models, managers, or services
def article_create(request):
    if request.method == 'POST':
        form = ArticleForm(request.POST)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.publish()  # Business logic in model method
            return redirect('article-detail', slug=article.slug)
```

### 3. Use get_object_or_404

```python
# Bad
try:
    article = Article.objects.get(slug=slug)
except Article.DoesNotExist:
    return HttpResponseNotFound()

# Good
article = get_object_or_404(Article, slug=slug)
```

### 4. Optimize Queries

```python
class ArticleListView(ListView):
    def get_queryset(self):
        return Article.objects.select_related(
            'author', 'category'
        ).prefetch_related(
            'tags'
        ).filter(status='published')
```

### 5. Use Proper HTTP Methods

```python
# Use GET for reading
# Use POST for creating
# Use PUT/PATCH for updating
# Use DELETE for deleting

class ArticleViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']  # Exclude 'put'
```

### 6. Return Appropriate Status Codes

```python
from rest_framework import status

def api_view(request):
    # 200 OK - Success
    # 201 Created - Resource created
    # 204 No Content - Success with no response body
    # 400 Bad Request - Invalid input
    # 401 Unauthorized - Authentication required
    # 403 Forbidden - No permission
    # 404 Not Found - Resource not found
    # 500 Internal Server Error - Server error
    
    return Response(data, status=status.HTTP_200_OK)
```

### 7. Use Context Processors for Common Data

```python
# context_processors.py
def site_settings(request):
    return {
        'SITE_NAME': 'My Site',
        'CURRENT_YEAR': datetime.now().year,
    }

# settings.py
TEMPLATES = [{
    'OPTIONS': {
        'context_processors': [
            'myapp.context_processors.site_settings',
        ],
    },
}]
```

### 8. Validate User Input

```python
def article_create(request):
    if request.method == 'POST':
        form = ArticleForm(request.POST)
        # Always validate form data
        if form.is_valid():
            # Process valid data
            pass
        else:
            # Handle validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
```

### 9. Use Reverse URLs

```python
# Bad
return redirect('/articles/')

# Good
from django.urls import reverse
return redirect(reverse('article-list'))

# Or with reverse_lazy for class-based views
from django.urls import reverse_lazy
success_url = reverse_lazy('article-list')
```

### 10. Log Important Events

```python
import logging

logger = logging.getLogger(__name__)

def article_create(request):
    try:
        # ... logic
        logger.info(f'Article created: {article.slug} by {request.user}')
    except Exception as e:
        logger.error(f'Error creating article: {str(e)}', exc_info=True)
```

## Conclusion

Following these view guidelines will help you create maintainable, secure, and efficient Django views. Remember to:

- Choose the right view type for your use case
- Keep views thin and focused
- Handle errors gracefully
- Optimize database queries
- Follow REST principles for APIs
- Use appropriate permissions and authentication
