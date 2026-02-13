# Django Authentication Guidelines

## Table of Contents
- [Overview](#overview)
- [User Authentication](#user-authentication)
- [Custom User Model](#custom-user-model)
- [JWT Authentication](#jwt-authentication)
- [Permissions and Authorization](#permissions-and-authorization)
- [Session Authentication](#session-authentication)
- [Token Authentication](#token-authentication)
- [Social Authentication](#social-authentication)
- [Two-Factor Authentication](#two-factor-authentication)
- [Password Management](#password-management)
- [Best Practices](#best-practices)

## Overview

Django provides a robust authentication system out of the box. This guide covers custom user models, JWT authentication, permissions, and social authentication integration.

## User Authentication

### Basic Login and Logout

```python
# views.py
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages

def login_view(request):
    """Handle user login."""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            
            # Redirect to next parameter or default to home
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'accounts/login.html')


def logout_view(request):
    """Handle user logout."""
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('login')


@login_required
def profile_view(request):
    """Display user profile (requires login)."""
    return render(request, 'accounts/profile.html', {
        'user': request.user
    })
```

### User Registration

```python
# forms.py
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()


class UserRegistrationForm(UserCreationForm):
    """Form for user registration."""
    
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 
                  'password1', 'password2')
    
    def clean_email(self):
        """Ensure email is unique."""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email already exists.')
        return email
    
    def save(self, commit=True):
        """Save user with additional fields."""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
        return user
```

```python
# views.py
from .forms import UserRegistrationForm

def register_view(request):
    """Handle user registration."""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Log the user in
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('profile')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})
```

## Custom User Model

### Creating Custom User Model

```python
# users/models.py
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Custom user manager."""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user."""
        if not email:
            raise ValueError(_('The Email field must be set'))
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Custom user model with email as username."""
    
    username = None  # Remove username field
    email = models.EmailField(_('email address'), unique=True)
    bio = models.TextField(_('bio'), max_length=500, blank=True)
    avatar = models.ImageField(
        _('avatar'),
        upload_to='avatars/',
        blank=True,
        null=True
    )
    birth_date = models.DateField(_('birth date'), blank=True, null=True)
    phone_number = models.CharField(
        _('phone number'),
        max_length=15,
        blank=True
    )
    is_verified = models.BooleanField(_('verified'), default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """Return user's full name."""
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        """Return user's first name."""
        return self.first_name
```

```python
# settings.py
AUTH_USER_MODEL = 'users.User'
```

### User Profile Model

```python
# users/models.py
from django.db import models
from django.conf import settings


class UserProfile(models.Model):
    """Extended user profile information."""
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    website = models.URLField(blank=True)
    github = models.CharField(max_length=100, blank=True)
    twitter = models.CharField(max_length=100, blank=True)
    linkedin = models.CharField(max_length=100, blank=True)
    company = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=100, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    language = models.CharField(max_length=10, default='en')
    
    # Preferences
    email_notifications = models.BooleanField(default=True)
    marketing_emails = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.email}'s profile"


# Create profile automatically when user is created
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    """Create user profile when user is created."""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    """Save user profile when user is saved."""
    instance.profile.save()
```

## JWT Authentication

### Installing and Configuring JWT

```bash
pip install djangorestframework-simplejwt
```

```python
# settings.py
from datetime import timedelta

INSTALLED_APPS = [
    # ...
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
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
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    
    'JTI_CLAIM': 'jti',
    
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}
```

### JWT URL Configuration

```python
# urls.py
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

### Custom JWT Claims

```python
# serializers.py
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom token serializer with additional claims."""
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims
        token['email'] = user.email
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        token['is_staff'] = user.is_staff
        token['is_verified'] = user.is_verified
        
        return token


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom token view using custom serializer."""
    serializer_class = CustomTokenObtainPairSerializer
```

### JWT Registration and Login

```python
# serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ('email', 'password', 'password_confirm', 
                  'first_name', 'last_name')
    
    def validate(self, attrs):
        """Validate passwords match."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password': 'Passwords do not match.'
            })
        return attrs
    
    def create(self, validated_data):
        """Create user."""
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user data."""
    
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 
                  'bio', 'avatar', 'is_verified', 'created_at')
        read_only_fields = ('id', 'is_verified', 'created_at')
```

```python
# views.py
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken


class UserRegistrationView(generics.CreateAPIView):
    """Register a new user and return JWT tokens."""
    
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Retrieve and update user profile."""
    
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user
```

## Permissions and Authorization

### Built-in Permissions

```python
# views.py
from rest_framework import generics
from rest_framework.permissions import (
    IsAuthenticated,
    IsAdminUser,
    AllowAny,
    IsAuthenticatedOrReadOnly,
)


class ArticleListView(generics.ListCreateAPIView):
    """List articles (public) or create (authenticated)."""
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class AdminOnlyView(generics.ListAPIView):
    """Admin-only view."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
```

### Custom Permissions

```python
# permissions.py
from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner
        return obj.author == request.user


class IsOwner(permissions.BasePermission):
    """Permission to only allow owners of an object to access it."""
    
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user


class IsVerifiedUser(permissions.BasePermission):
    """Permission to only allow verified users."""
    
    message = 'You must verify your email address to perform this action.'
    
    def has_permission(self, request, view):
        return request.user.is_verified


class IsStaffOrReadOnly(permissions.BasePermission):
    """Allow staff to edit, others read-only."""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_staff


class HasSubscription(permissions.BasePermission):
    """Permission for users with active subscription."""
    
    message = 'You need an active subscription to access this resource.'
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return hasattr(request.user, 'subscription') and \
               request.user.subscription.is_active
```

### Using Custom Permissions

```python
# views.py
from rest_framework import generics
from .permissions import IsOwnerOrReadOnly, IsVerifiedUser


class ArticleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Article detail view with custom permissions."""
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly, IsVerifiedUser]


class ArticleCreateView(generics.CreateAPIView):
    """Create article - requires authentication and verification."""
    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated, IsVerifiedUser]
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
```

### Object-Level Permissions

```python
# permissions.py
class CanEditArticle(permissions.BasePermission):
    """
    Custom permission to check if user can edit article.
    - Owner can edit
    - Staff can edit
    - Editors in same category can edit
    """
    
    def has_object_permission(self, request, view, obj):
        # Owner can always edit
        if obj.author == request.user:
            return True
        
        # Staff can edit any article
        if request.user.is_staff:
            return True
        
        # Check if user is editor for this category
        if hasattr(request.user, 'editor_categories'):
            return obj.category in request.user.editor_categories.all()
        
        return False
```

### Role-Based Permissions

```python
# models.py
from django.db import models
from django.conf import settings


class Role(models.Model):
    """User role model."""
    
    ADMIN = 'admin'
    EDITOR = 'editor'
    AUTHOR = 'author'
    VIEWER = 'viewer'
    
    ROLE_CHOICES = [
        (ADMIN, 'Administrator'),
        (EDITOR, 'Editor'),
        (AUTHOR, 'Author'),
        (VIEWER, 'Viewer'),
    ]
    
    name = models.CharField(max_length=20, choices=ROLE_CHOICES, unique=True)
    permissions = models.JSONField(default=dict)
    
    def __str__(self):
        return self.get_name_display()


class UserRole(models.Model):
    """User-Role relationship."""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_roles'
    )
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    organization = models.ForeignKey(
        'Organization',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    
    class Meta:
        unique_together = ['user', 'role', 'organization']
```

```python
# permissions.py
class HasRole(permissions.BasePermission):
    """Check if user has specific role."""
    
    def __init__(self, required_role):
        self.required_role = required_role
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        return request.user.user_roles.filter(
            role__name=self.required_role
        ).exists()


class HasAnyRole(permissions.BasePermission):
    """Check if user has any of the specified roles."""
    
    def __init__(self, required_roles):
        self.required_roles = required_roles
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        return request.user.user_roles.filter(
            role__name__in=self.required_roles
        ).exists()
```

## Session Authentication

### Session Configuration

```python
# settings.py

# Session settings
SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # Database sessions
# SESSION_ENGINE = 'django.contrib.sessions.backends.cache'  # Cache sessions
# SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'  # Hybrid

SESSION_COOKIE_NAME = 'sessionid'
SESSION_COOKIE_AGE = 1209600  # 2 weeks in seconds
SESSION_COOKIE_SECURE = True  # HTTPS only (production)
SESSION_COOKIE_HTTPONLY = True  # No JavaScript access
SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
SESSION_SAVE_EVERY_REQUEST = False
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
```

### Session Management

```python
# views.py
from django.contrib.sessions.models import Session
from django.utils import timezone


def custom_login(request):
    """Login with custom session data."""
    user = authenticate(username=username, password=password)
    
    if user:
        login(request, user)
        
        # Store custom session data
        request.session['login_time'] = str(timezone.now())
        request.session['user_agent'] = request.META.get('HTTP_USER_AGENT', '')
        
        return redirect('home')


def get_user_sessions(user):
    """Get all active sessions for a user."""
    user_sessions = []
    sessions = Session.objects.filter(expire_date__gte=timezone.now())
    
    for session in sessions:
        data = session.get_decoded()
        if data.get('_auth_user_id') == str(user.id):
            user_sessions.append(session)
    
    return user_sessions


def logout_all_sessions(user):
    """Logout user from all devices."""
    sessions = get_user_sessions(user)
    for session in sessions:
        session.delete()
```

## Token Authentication

### DRF Token Authentication

```python
# settings.py
INSTALLED_APPS = [
    # ...
    'rest_framework.authtoken',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
}

# Run migrations to create token table
# python manage.py migrate
```

```python
# views.py
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response


class CustomObtainAuthToken(ObtainAuthToken):
    """Custom token authentication view."""
    
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        # Get or create token
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email,
        })


# Create token on user registration
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    """Create auth token when user is created."""
    if created:
        Token.objects.create(user=instance)
```

## Social Authentication

### django-allauth Setup

```bash
pip install django-allauth
```

```python
# settings.py
INSTALLED_APPS = [
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',  # Required for allauth
    
    # Third-party
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.github',
    'allauth.socialaccount.providers.facebook',
]

SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Allauth settings
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_SIGNUP_EMAIL_ENTER_TWICE = True
ACCOUNT_UNIQUE_EMAIL = True

# Social account settings
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_QUERY_EMAIL = True

# Provider specific settings
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    },
    'github': {
        'SCOPE': [
            'user',
            'repo',
            'read:org',
        ],
    },
    'facebook': {
        'METHOD': 'oauth2',
        'SCOPE': ['email', 'public_profile'],
        'AUTH_PARAMS': {'auth_type': 'reauthenticate'},
        'FIELDS': [
            'id',
            'email',
            'name',
            'first_name',
            'last_name',
            'verified',
        ],
    }
}
```

```python
# urls.py
from django.urls import path, include

urlpatterns = [
    # ...
    path('accounts/', include('allauth.urls')),
]
```

### Custom Social Authentication Adapter

```python
# adapters.py
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Custom social account adapter."""
    
    def pre_social_login(self, request, sociallogin):
        """
        Connect social account to existing user if email matches.
        """
        if sociallogin.is_existing:
            return
        
        try:
            email = sociallogin.account.extra_data.get('email')
            if email:
                user = User.objects.get(email=email)
                sociallogin.connect(request, user)
        except User.DoesNotExist:
            pass
    
    def populate_user(self, request, sociallogin, data):
        """Populate user instance with social account data."""
        user = super().populate_user(request, sociallogin, data)
        
        # Add custom logic
        if not user.first_name:
            user.first_name = data.get('first_name', '')
        if not user.last_name:
            user.last_name = data.get('last_name', '')
        
        return user


class CustomAccountAdapter(DefaultAccountAdapter):
    """Custom account adapter."""
    
    def save_user(self, request, user, form, commit=True):
        """Save user with additional data."""
        user = super().save_user(request, user, form, commit=False)
        
        # Add custom fields
        user.is_verified = False
        
        if commit:
            user.save()
        return user
```

```python
# settings.py
SOCIALACCOUNT_ADAPTER = 'myapp.adapters.CustomSocialAccountAdapter'
ACCOUNT_ADAPTER = 'myapp.adapters.CustomAccountAdapter'
```

## Two-Factor Authentication

### django-otp Setup

```bash
pip install django-otp qrcode
```

```python
# settings.py
INSTALLED_APPS = [
    # ...
    'django_otp',
    'django_otp.plugins.otp_totp',
    'django_otp.plugins.otp_static',
]

MIDDLEWARE = [
    # ...
    'django_otp.middleware.OTPMiddleware',
]
```

```python
# views.py
from django_otp.decorators import otp_required
from django_otp.plugins.otp_totp.models import TOTPDevice
from django.contrib.auth.decorators import login_required
import qrcode
from io import BytesIO
import base64


@login_required
def setup_2fa(request):
    """Set up two-factor authentication."""
    device, created = TOTPDevice.objects.get_or_create(
        user=request.user,
        name='default'
    )
    
    if created or not device.confirmed:
        # Generate QR code
        url = device.config_url
        qr = qrcode.make(url)
        buffer = BytesIO()
        qr.save(buffer, format='PNG')
        qr_code = base64.b64encode(buffer.getvalue()).decode()
        
        return render(request, 'accounts/setup_2fa.html', {
            'qr_code': qr_code,
            'secret': device.key,
        })
    
    return redirect('profile')


@login_required
def verify_2fa(request):
    """Verify 2FA token."""
    if request.method == 'POST':
        token = request.POST.get('token')
        device = TOTPDevice.objects.get(user=request.user, name='default')
        
        if device.verify_token(token):
            device.confirmed = True
            device.save()
            messages.success(request, '2FA enabled successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Invalid token.')
    
    return render(request, 'accounts/verify_2fa.html')


@otp_required
def protected_view(request):
    """View that requires 2FA."""
    return render(request, 'protected.html')
```

## Password Management

### Password Reset

```python
# urls.py
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset.html'
         ),
         name='password_reset'),
    
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html'
         ),
         name='password_reset_done'),
    
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html'
         ),
         name='password_reset_confirm'),
    
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html'
         ),
         name='password_reset_complete'),
]
```

### Password Change

```python
# views.py
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy


class CustomPasswordChangeView(PasswordChangeView):
    """Custom password change view."""
    template_name = 'accounts/password_change.html'
    success_url = reverse_lazy('profile')
    
    def form_valid(self, form):
        messages.success(self.request, 'Password changed successfully!')
        return super().form_valid(form)
```

### Password Validation

```python
# settings.py
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        'OPTIONS': {
            'user_attributes': ('username', 'email', 'first_name', 'last_name'),
            'max_similarity': 0.7,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
```

## Best Practices

### Security Best Practices

```python
# ✅ GOOD: Use environment variables for secrets
# settings.py
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']

# Social auth credentials
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': os.environ['GOOGLE_CLIENT_ID'],
            'secret': os.environ['GOOGLE_CLIENT_SECRET'],
        }
    }
}

# ❌ BAD: Hardcode secrets
SECRET_KEY = 'hardcoded-secret-key-123'
```

### Token Storage

```python
# ✅ GOOD: Store JWT in httpOnly cookie (for web)
from rest_framework_simplejwt.authentication import JWTAuthentication

class CookieJWTAuthentication(JWTAuthentication):
    """Custom JWT authentication using cookies."""
    
    def authenticate(self, request):
        cookie_name = getattr(settings, 'JWT_AUTH_COOKIE', 'access_token')
        raw_token = request.COOKIES.get(cookie_name)
        
        if raw_token is None:
            return None
        
        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token

# ❌ BAD: Store JWT in localStorage (XSS vulnerable)
```

### Permission Checks

```python
# ✅ GOOD: Explicit permission checks
class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

# ❌ BAD: No permission checks
class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
```

### Rate Limiting

```python
# Install: pip install django-ratelimit

from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='5/m', method='POST')
def login_view(request):
    """Login with rate limiting."""
    # ... login logic
```

### Audit Logging

```python
# models.py
class AuditLog(models.Model):
    """Model for tracking authentication events."""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    action = models.CharField(max_length=50)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user} - {self.action} - {self.timestamp}"


# utils.py
def log_auth_event(user, action, request, success=True):
    """Log authentication event."""
    AuditLog.objects.create(
        user=user,
        action=action,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        success=success
    )


def get_client_ip(request):
    """Get client IP address."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
```
