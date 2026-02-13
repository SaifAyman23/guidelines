# Django Backend Use Cases

A comprehensive guide with practical, actionable instructions for common Django development scenarios. Each use case provides step-by-step workflows, decision trees, and best practices to help you build robust Django applications.

## Table of Contents
- [Use Case 1: Starting a New Django Project](#use-case-1-starting-a-new-django-project)
- [Use Case 2: Building an API Endpoint](#use-case-2-building-an-api-endpoint)
- [Use Case 3: Adding Authentication](#use-case-3-adding-authentication)
- [Use Case 4: Optimizing Database Queries](#use-case-4-optimizing-database-queries)
- [Use Case 5: Deploying to Production](#use-case-5-deploying-to-production)

---

## Use Case 1: Starting a New Django Project

### 📋 Initial Setup Checklist

**Step 1: Environment Setup**

```bash
# Create project directory
mkdir myproject && cd myproject

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip
```

**Step 2: Install Django and Essential Packages**

```bash
# Install Django
pip install django

# Install Django REST Framework (if building APIs)
pip install djangorestframework

# Install additional essential packages
pip install python-decouple  # Environment variables
pip install psycopg2-binary  # PostgreSQL adapter
pip install django-cors-headers  # CORS handling
pip install djangorestframework-simplejwt  # JWT authentication
pip install django-filter  # Filtering support
pip install pillow  # Image handling
pip install celery  # Async task processing
pip install redis  # Caching
pip install django-debug-toolbar  # Development debugging
pip install pytest pytest-django  # Testing framework

# Create requirements.txt
pip freeze > requirements.txt
```

**Step 3: Create Django Project**

```bash
# Create project
django-admin startproject config .

# Create your first app
python manage.py startapp core

# Create additional apps as needed
python manage.py startapp users
python manage.py startapp api
```

### 🏗️ Project Structure Decisions

**Recommended Directory Structure:**

```
myproject/
├── venv/
├── config/
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── development.py
│   │   ├── production.py
│   │   └── testing.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── core/
│   ├── users/
│   └── api/
├── static/
├── media/
├── templates/
├── tests/
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
├── .env
├── .env.example
├── .gitignore
├── manage.py
└── README.md
```

**💡 Tip:** Split settings into multiple files for different environments to maintain cleaner configuration.

### ⚙️ Environment Configuration

**Create `.env` file:**

```bash
# .env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
REDIS_URL=redis://localhost:6379/0
```

**Create `.env.example` (for version control):**

```bash
# .env.example
SECRET_KEY=
DEBUG=False
ALLOWED_HOSTS=
DATABASE_URL=
REDIS_URL=
```

**Configure settings to use environment variables:**

```python
# config/settings/base.py
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    
    # Local apps
    'apps.core',
    'apps.users',
    'apps.api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # CORS
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

### 🗄️ Database Setup

**PostgreSQL Configuration:**

```python
# config/settings/base.py
import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL'),
        conn_max_age=600
    )
}
```

**Alternative: SQLite for Development:**

```python
# config/settings/development.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

### 📝 Initial Migrations

```bash
# Create initial migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### ✅ Verification Checklist

- [ ] Virtual environment created and activated
- [ ] Django and essential packages installed
- [ ] Project and apps created
- [ ] Settings split into environment-specific files
- [ ] Environment variables configured
- [ ] Database configured and migrations run
- [ ] Superuser created
- [ ] Development server running successfully
- [ ] `.gitignore` configured (exclude venv, .env, db.sqlite3, etc.)

---

## Use Case 2: Building an API Endpoint

### 📐 Step-by-Step Workflow

This use case demonstrates the **Model → Serializer → View → URL** pattern for creating a complete API endpoint.

### Step 1: Define the Model

```python
# apps/blog/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify

User = get_user_model()


class Post(models.Model):
    """Blog post model"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    content = models.TextField()
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='draft'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['slug']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
```

**Run migrations:**

```bash
python manage.py makemigrations blog
python manage.py migrate blog
```

### Step 2: Create Serializer

```python
# apps/blog/serializers.py
from rest_framework import serializers
from .models import Post


class PostSerializer(serializers.ModelSerializer):
    """Serializer for Post model"""
    
    author_name = serializers.CharField(source='author.username', read_only=True)
    author_email = serializers.EmailField(source='author.email', read_only=True)
    
    class Meta:
        model = Post
        fields = [
            'id',
            'title',
            'slug',
            'content',
            'author',
            'author_name',
            'author_email',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at']
    
    def validate_title(self, value):
        """Validate title is not empty and has minimum length"""
        if len(value.strip()) < 5:
            raise serializers.ValidationError(
                "Title must be at least 5 characters long"
            )
        return value
    
    def validate_content(self, value):
        """Validate content has minimum length"""
        if len(value.strip()) < 50:
            raise serializers.ValidationError(
                "Content must be at least 50 characters long"
            )
        return value


class PostListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing posts"""
    
    author_name = serializers.CharField(source='author.username', read_only=True)
    
    class Meta:
        model = Post
        fields = ['id', 'title', 'slug', 'author_name', 'status', 'created_at']
```

### Step 3: Create Views

**Option A: ViewSets (Recommended for full CRUD)**

```python
# apps/blog/views.py
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from .models import Post
from .serializers import PostSerializer, PostListSerializer
from .permissions import IsAuthorOrReadOnly


class PostViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Post model.
    
    Provides list, create, retrieve, update, and delete actions.
    """
    queryset = Post.objects.select_related('author').all()
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'author']
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'updated_at', 'title']
    
    def get_serializer_class(self):
        """Return appropriate serializer class"""
        if self.action == 'list':
            return PostListSerializer
        return PostSerializer
    
    def perform_create(self, serializer):
        """Set author to current user on creation"""
        serializer.save(author=self.request.user)
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """Custom action to publish a post"""
        post = self.get_object()
        post.status = 'published'
        post.save()
        serializer = self.get_serializer(post)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def published(self, request):
        """Custom action to list only published posts"""
        published_posts = self.queryset.filter(status='published')
        page = self.paginate_queryset(published_posts)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(published_posts, many=True)
        return Response(serializer.data)
```

**Option B: APIView (For custom logic)**

```python
# apps/blog/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Post
from .serializers import PostSerializer


class PostListCreateView(APIView):
    """
    List all posts or create a new post.
    """
    
    def get(self, request):
        """List all posts"""
        posts = Post.objects.select_related('author').all()
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """Create a new post"""
        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
```

### Step 4: Define URL Patterns

**With ViewSet (using router):**

```python
# apps/blog/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PostViewSet

router = DefaultRouter()
router.register(r'posts', PostViewSet, basename='post')

urlpatterns = [
    path('', include(router.urls)),
]
```

**With APIView:**

```python
# apps/blog/urls.py
from django.urls import path
from .views import PostListCreateView

urlpatterns = [
    path('posts/', PostListCreateView.as_view(), name='post-list-create'),
]
```

**Include in main urls.py:**

```python
# config/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('apps.blog.urls')),
]
```

### 🔒 Validation Approach

**Field-level validation:**

```python
def validate_field_name(self, value):
    if condition:
        raise serializers.ValidationError("Error message")
    return value
```

**Object-level validation:**

```python
def validate(self, attrs):
    if attrs['start_date'] > attrs['end_date']:
        raise serializers.ValidationError("End date must be after start date")
    return attrs
```

**Custom validators:**

```python
from rest_framework import serializers

def validate_file_size(value):
    limit = 2 * 1024 * 1024  # 2MB
    if value.size > limit:
        raise serializers.ValidationError('File too large. Max size is 2MB')

class DocumentSerializer(serializers.ModelSerializer):
    file = serializers.FileField(validators=[validate_file_size])
```

### ⚠️ Error Handling

**Create custom permission:**

```python
# apps/blog/permissions.py
from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow authors to edit their posts.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for the author
        return obj.author == request.user
```

**Custom exception handling:**

```python
# config/settings/base.py
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'apps.core.exceptions.custom_exception_handler',
}

# apps/core/exceptions.py
from rest_framework.views import exception_handler
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    """Custom exception handler"""
    response = exception_handler(exc, context)
    
    if response is not None:
        response.data['status_code'] = response.status_code
        
    return response
```

### 🧪 Testing the Endpoint

```python
# apps/blog/tests/test_api.py
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from apps.blog.models import Post

User = get_user_model()


class PostAPITestCase(APITestCase):
    """Test cases for Post API"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.post = Post.objects.create(
            title='Test Post',
            content='Test content for the post',
            author=self.user,
            status='published'
        )
    
    def test_list_posts(self):
        """Test listing all posts"""
        url = reverse('post-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_create_post_authenticated(self):
        """Test creating a post when authenticated"""
        self.client.force_authenticate(user=self.user)
        url = reverse('post-list')
        data = {
            'title': 'New Test Post',
            'content': 'New test content for the post that is long enough',
            'status': 'draft'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 2)
        self.assertEqual(response.data['author'], self.user.id)
    
    def test_create_post_unauthenticated(self):
        """Test creating a post when not authenticated"""
        url = reverse('post-list')
        data = {
            'title': 'New Test Post',
            'content': 'New test content',
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
```

**Run tests:**

```bash
python manage.py test apps.blog
# Or with pytest
pytest apps/blog/tests/
```

### 📊 API Documentation

Add API documentation using drf-spectacular:

```bash
pip install drf-spectacular
```

```python
# config/settings/base.py
INSTALLED_APPS = [
    # ...
    'drf_spectacular',
]

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Your Project API',
    'DESCRIPTION': 'API documentation',
    'VERSION': '1.0.0',
}

# config/urls.py
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
```

---

## Use Case 3: Adding Authentication

### 🌳 Decision Tree

```
Need Authentication?
│
├─ Simple Web App → Session-based (Django default)
│   └─ Pros: Built-in, secure, simple
│   └─ Cons: Not suitable for mobile/SPA
│
├─ API + Single Page App → JWT (JSON Web Tokens)
│   └─ Pros: Stateless, works across domains
│   └─ Cons: Token management complexity
│
└─ Third-party Login → OAuth 2.0 / Social Auth
    └─ Pros: User convenience, no password management
    └─ Cons: Dependency on external services
```

### 🔑 Option 1: JWT Authentication (Recommended for APIs)

**Installation:**

```bash
pip install djangorestframework-simplejwt
```

**Configuration:**

```python
# config/settings/base.py
from datetime import timedelta

INSTALLED_APPS = [
    # ...
    'rest_framework',
    'rest_framework_simplejwt',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}
```

**URL Configuration:**

```python
# config/urls.py
from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]
```

**Custom User Registration:**

```python
# apps/users/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


# apps/users/views.py
from rest_framework import generics, permissions
from .serializers import UserRegistrationSerializer


class RegisterView(generics.CreateAPIView):
    """User registration endpoint"""
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
```

### 🔐 Option 2: Session-based Authentication

**For web applications with traditional forms:**

```python
# apps/users/views.py
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'login.html', {
                'error': 'Invalid credentials'
            })
    
    return render(request, 'login.html')


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')
```

### 🌐 Option 3: OAuth 2.0 / Social Authentication

**Using django-allauth:**

```bash
pip install django-allauth
```

```python
# config/settings/base.py
INSTALLED_APPS = [
    # ...
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.github',
]

SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    }
}
```

### 🛡️ Permission Classes

**Built-in permissions:**

```python
from rest_framework import permissions

# In your views
permission_classes = [permissions.IsAuthenticated]  # Must be logged in
permission_classes = [permissions.IsAdminUser]  # Must be staff
permission_classes = [permissions.AllowAny]  # No authentication required
permission_classes = [permissions.IsAuthenticatedOrReadOnly]  # Read for all, write for authenticated
```

**Custom permissions:**

```python
# apps/core/permissions.py
from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners to edit.
    """
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner == request.user


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Allow admin users to edit, others can only read.
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff
```

### 👤 User Model Customization

**Create custom user model:**

```python
# apps/users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model"""
    
    email = models.EmailField(unique=True)
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    USERNAME_FIELD = 'email'  # Use email for login
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return self.email
```

**Configure in settings:**

```python
# config/settings/base.py
AUTH_USER_MODEL = 'users.User'
```

**⚠️ Warning:** Must be done at project start before any migrations!

### 🔒 Security Best Practices

**1. Password Validation:**

```python
# config/settings/base.py
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8}
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
```

**2. HTTPS Only:**

```python
# config/settings/production.py
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
```

**3. CORS Configuration:**

```python
# config/settings/base.py
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# For production
CORS_ALLOW_CREDENTIALS = True
```

**4. Rate Limiting:**

```bash
pip install django-ratelimit
```

```python
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='5/m', method='POST')
def login_view(request):
    # Login logic
    pass
```

---

## Use Case 4: Optimizing Database Queries

### 🔍 Identifying N+1 Problems

**The Problem:**

```python
# BAD: N+1 query problem
posts = Post.objects.all()  # 1 query
for post in posts:
    print(post.author.username)  # N additional queries (one per post!)
```

**Enable Query Logging:**

```python
# config/settings/development.py
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

### 🚀 Using select_related and prefetch_related

**select_related (for ForeignKey and OneToOne):**

```python
# GOOD: Single query with JOIN
posts = Post.objects.select_related('author').all()
for post in posts:
    print(post.author.username)  # No additional queries!
```

**prefetch_related (for ManyToMany and reverse ForeignKey):**

```python
# GOOD: Two queries total (one for posts, one for tags)
posts = Post.objects.prefetch_related('tags').all()
for post in posts:
    for tag in post.tags.all():  # No additional queries!
        print(tag.name)
```

**Combining select_related and prefetch_related:**

```python
# Optimize complex queries
posts = Post.objects.select_related(
    'author',  # ForeignKey
    'category'  # ForeignKey
).prefetch_related(
    'tags',  # ManyToMany
    'comments__author'  # Nested prefetch
).all()
```

**Custom Prefetch:**

```python
from django.db.models import Prefetch

# Only prefetch published comments
published_comments = Comment.objects.filter(is_published=True)

posts = Post.objects.prefetch_related(
    Prefetch('comments', queryset=published_comments, to_attr='published_comments')
).all()

for post in posts:
    for comment in post.published_comments:  # Using custom attribute
        print(comment.text)
```

### 🔧 Query Profiling with Django Debug Toolbar

**Installation:**

```bash
pip install django-debug-toolbar
```

**Configuration:**

```python
# config/settings/development.py
INSTALLED_APPS = [
    # ...
    'debug_toolbar',
]

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    # ... other middleware
]

INTERNAL_IPS = [
    '127.0.0.1',
]

# config/urls.py
from django.conf import settings

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
```

**💡 Tip:** The SQL panel shows all queries, duplicates, and query time!

### 📊 Indexing Strategies

**Add indexes to frequently queried fields:**

```python
class Post(models.Model):
    title = models.CharField(max_length=200, db_index=True)  # Simple index
    slug = models.SlugField(unique=True)  # Unique constraint creates index
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['-created_at']),  # Descending index
            models.Index(fields=['status', 'published_at']),  # Composite index
            models.Index(fields=['author', '-created_at']),  # Multi-field index
        ]
```

**When to add indexes:**

- ✅ Fields used in WHERE clauses
- ✅ Fields used in ORDER BY
- ✅ Foreign keys (Django creates these automatically)
- ✅ Fields used in JOINs
- ❌ Fields that are frequently updated
- ❌ Fields with low cardinality (few unique values)
- ❌ Small tables

### 💾 Caching Approaches

**1. Per-View Caching:**

```python
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)  # Cache for 15 minutes
def my_view(request):
    # View logic
    pass
```

**2. Template Fragment Caching:**

```django
{% load cache %}
{% cache 500 sidebar request.user.username %}
    .. sidebar for logged in user ..
{% endcache %}
```

**3. Low-Level Cache API:**

```python
from django.core.cache import cache

# Set cache
cache.set('my_key', 'my_value', 60 * 15)  # 15 minutes

# Get cache
value = cache.get('my_key')

# Get or set
value = cache.get_or_set('my_key', compute_expensive_value, 60 * 15)

# Delete cache
cache.delete('my_key')
```

**4. QuerySet Caching:**

```python
# apps/blog/managers.py
from django.core.cache import cache


class PostManager(models.Manager):
    def get_published_posts(self):
        cache_key = 'published_posts'
        posts = cache.get(cache_key)
        
        if posts is None:
            posts = list(self.filter(status='published').select_related('author'))
            cache.set(cache_key, posts, 60 * 15)  # 15 minutes
        
        return posts
```

**Redis Configuration:**

```python
# config/settings/base.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'myproject',
        'TIMEOUT': 300,
    }
}
```

### 📈 Query Optimization Checklist

- [ ] Use `select_related()` for ForeignKey/OneToOne
- [ ] Use `prefetch_related()` for ManyToMany/reverse ForeignKey
- [ ] Add database indexes on frequently queried fields
- [ ] Use `only()` and `defer()` to select specific fields
- [ ] Use `values()` and `values_list()` for simple data
- [ ] Aggregate in the database, not in Python
- [ ] Use `exists()` instead of `count()` for boolean checks
- [ ] Use `iterator()` for large querysets
- [ ] Cache expensive queries
- [ ] Use Django Debug Toolbar to profile queries

---

## Use Case 5: Deploying to Production

### 📋 Production Checklist

**Pre-Deployment:**

```bash
# 1. Run security check
python manage.py check --deploy

# 2. Collect static files
python manage.py collectstatic --noinput

# 3. Run migrations
python manage.py migrate

# 4. Run tests
python manage.py test
# or
pytest

# 5. Check for missing migrations
python manage.py makemigrations --check --dry-run
```

### 🔐 Environment Variables

**Production .env file:**

```bash
# .env.production
SECRET_KEY=your-very-secure-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DATABASE_URL=postgresql://user:password@db-host:5432/dbname

# Redis
REDIS_URL=redis://redis-host:6379/0

# AWS S3 (for static/media files)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1

# Email
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key
EMAIL_USE_TLS=True

# Sentry (Error tracking)
SENTRY_DSN=your-sentry-dsn
```

### 📦 Static Files Configuration

**Option 1: Using WhiteNoise (Simple)**

```bash
pip install whitenoise
```

```python
# config/settings/production.py
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add this
    # ... other middleware
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

STATIC_ROOT = BASE_DIR / 'staticfiles'
STATIC_URL = '/static/'
```

**Option 2: Using AWS S3 (Scalable)**

```bash
pip install django-storages boto3
```

```python
# config/settings/production.py
INSTALLED_APPS = [
    # ...
    'storages',
]

# AWS S3 Settings
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='us-east-1')
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
AWS_DEFAULT_ACL = 'public-read'
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}

# Static files
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'

# Media files
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
```

### 🗄️ Database Migrations Strategy

**Safe Migration Practices:**

```python
# 1. Always backup database before migrations
# 2. Test migrations on staging first
# 3. Use migration squashing for many migrations

# Squash migrations
python manage.py squashmigrations app_name 0001 0005

# Show migration plan
python manage.py showmigrations

# Show SQL for a migration
python manage.py sqlmigrate app_name 0001
```

**Zero-Downtime Migrations:**

```python
# Step 1: Add new field as nullable
class Migration(migrations.Migration):
    operations = [
        migrations.AddField(
            model_name='mymodel',
            name='new_field',
            field=models.CharField(max_length=100, null=True),
        ),
    ]

# Step 2: Deploy code that populates new field

# Step 3: Make field non-nullable
class Migration(migrations.Migration):
    operations = [
        migrations.AlterField(
            model_name='mymodel',
            name='new_field',
            field=models.CharField(max_length=100),
        ),
    ]
```

### 📝 Logging and Monitoring

**Logging Configuration:**

```python
# config/settings/production.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django/django.log',
            'maxBytes': 1024 * 1024 * 15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

**Sentry Integration:**

```bash
pip install sentry-sdk
```

```python
# config/settings/production.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=config('SENTRY_DSN'),
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,
    send_default_pii=True,
    environment='production',
)
```

### 🚀 CI/CD Pipeline Setup

**GitHub Actions Example:**

```yaml
# .github/workflows/django.yml
name: Django CI/CD

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run migrations
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
      run: python manage.py migrate
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
      run: pytest
    
    - name: Run linting
      run: |
        pip install flake8
        flake8 .
  
  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Deploy to production
      run: |
        # Your deployment script here
        echo "Deploying to production..."
```

**Docker Deployment:**

```dockerfile
# Dockerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Collect static files
RUN python manage.py collectstatic --noinput

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "config.wsgi:application"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:14
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: myproject
      POSTGRES_USER: myuser
      POSTGRES_PASSWORD: mypassword
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  web:
    build: .
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - .:/app
      - static_volume:/app/staticfiles
    ports:
      - "8000:8000"
    env_file:
      - .env.production
    depends_on:
      - db
      - redis
  
  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - static_volume:/app/staticfiles
    ports:
      - "80:80"
    depends_on:
      - web

volumes:
  postgres_data:
  static_volume:
```

**Nginx Configuration (`nginx.conf`):**

```nginx
events {
    worker_connections 1024;
}

http {
    upstream django {
        server web:8000;
    }
    
    server {
        listen 80;
        server_name yourdomain.com www.yourdomain.com;
        
        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        
        # Static files
        location /static/ {
            alias /app/staticfiles/;
            expires 30d;
            add_header Cache-Control "public, immutable";
        }
        
        # Media files
        location /media/ {
            alias /app/media/;
            expires 7d;
        }
        
        # Django application
        location / {
            proxy_pass http://django;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket support (if using channels)
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }
        
        # Health check endpoint
        location /health/ {
            access_log off;
            proxy_pass http://django;
        }
        
        # Deny access to sensitive files
        location ~ /\. {
            deny all;
        }
    }
}
```

**Production Dockerfile (Multi-stage build):**

```dockerfile
# Dockerfile.prod
# Stage 1: Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 django && \
    mkdir -p /app /app/staticfiles /app/media && \
    chown -R django:django /app

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder --chown=django:django /root/.local /home/django/.local

# Copy application code
COPY --chown=django:django . .

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PATH=/home/django/.local/bin:$PATH

# Switch to non-root user
USER django

# Collect static files
RUN python manage.py collectstatic --noinput

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health/')"

# Expose port
EXPOSE 8000

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--worker-class", "gthread", \
     "--threads", "2", \
     "--timeout", "60", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "config.wsgi:application"]
```

**Docker Commands Reference:**

```bash
# Build and start services
docker-compose up -d --build

# View logs
docker-compose logs -f web

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Run tests
docker-compose exec web python manage.py test

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Rebuild specific service
docker-compose up -d --build web

# Scale web service
docker-compose up -d --scale web=3

# Execute Django shell
docker-compose exec web python manage.py shell

# Database backup
docker-compose exec db pg_dump -U myuser myproject > backup.sql

# Database restore
docker-compose exec -T db psql -U myuser myproject < backup.sql
```

**.dockerignore:**

```
# Git
.git
.gitignore

# Python
__pycache__
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
.venv

# Django
*.log
db.sqlite3
media/
staticfiles/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Testing
.coverage
htmlcov/
.pytest_cache/

# Environment
.env
.env.*

# OS
.DS_Store
Thumbs.db

# Documentation
README.md
docs/
```

### 🔒 Production Security Settings

```python
# config/settings/production.py

# Security
DEBUG = False
SECRET_KEY = config('SECRET_KEY')
ALLOWED_HOSTS = config('ALLOWED_HOSTS').split(',')

# HTTPS
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Security headers
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# CORS
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    'https://yourdomain.com',
    'https://www.yourdomain.com',
]
```

### ✅ Deployment Verification

```bash
# 1. Check that the site is accessible
curl https://yourdomain.com

# 2. Check admin panel
curl https://yourdomain.com/admin/

# 3. Check API endpoints
curl https://yourdomain.com/api/v1/

# 4. Monitor logs
tail -f /var/log/django/django.log

# 5. Check Sentry for errors
# Visit Sentry dashboard

# 6. Monitor server resources
htop
```

---

## 📚 Additional Resources

- [Django Official Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Two Scoops of Django](https://www.feldroy.com/books/two-scoops-of-django-3-x)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [Django Best Practices](https://django-best-practices.readthedocs.io/)

---

## 🎯 Quick Reference

| Task | Command |
|------|---------|
| Start new project | `django-admin startproject config .` |
| Create app | `python manage.py startapp app_name` |
| Make migrations | `python manage.py makemigrations` |
| Apply migrations | `python manage.py migrate` |
| Create superuser | `python manage.py createsuperuser` |
| Run server | `python manage.py runserver` |
| Run tests | `python manage.py test` or `pytest` |
| Collect static | `python manage.py collectstatic` |
| Django shell | `python manage.py shell` |
| Database shell | `python manage.py dbshell` |

---

**Remember:** These use cases are guidelines. Adapt them to your specific project needs and requirements.
