# Django & DRF Best Practices — The Definitive Reference Guide

> A comprehensive, opinionated guide covering architecture decisions, code patterns, tooling, and a full checklist for building anything with Django and Django REST Framework.

---

## Table of Contents

1. [Project Structure & Architecture](#1-project-structure--architecture)
2. [Settings & Configuration](#2-settings--configuration)
3. [Models & Database](#3-models--database)
4. [Views & ViewSets](#4-views--viewsets)
5. [Serializers](#5-serializers)
6. [URLs & Routing](#6-urls--routing)
7. [Authentication & Permissions](#7-authentication--permissions)
8. [Filtering, Searching & Ordering](#8-filtering-searching--ordering)
9. [Pagination](#9-pagination)
10. [Caching](#10-caching)
11. [Celery & Async Tasks](#11-celery--async-tasks)
12. [File Handling & Storage](#12-file-handling--storage)
13. [Testing](#13-testing)
14. [API Versioning](#14-api-versioning)
15. [Error Handling](#15-error-handling)
16. [Security](#16-security)
17. [Performance & Optimization](#17-performance--optimization)
18. [Logging & Monitoring](#18-logging--monitoring)
19. [Documentation (drf-spectacular / Swagger)](#19-documentation-drf-spectacular--swagger)
20. [Deployment & DevOps](#20-deployment--devops)
21. [Essential Libraries Cheat Sheet](#21-essential-libraries-cheat-sheet)
22. [The Master Checklist](#22-the-master-checklist)

---

## 1. Project Structure & Architecture

### Recommended Layout

```
my_project/
├── config/                    # All configuration lives here
│   ├── __init__.py
│   ├── settings/
│   │   ├── base.py            # Shared settings
│   │   ├── development.py     # Dev overrides
│   │   ├── production.py      # Prod overrides
│   │   └── testing.py         # Test-specific settings
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/                      # All Django apps live here
│   ├── users/
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   ├── services.py        # Business logic (not in views/models)
│   │   ├── selectors.py       # Read queries (query layer)
│   │   ├── permissions.py
│   │   ├── filters.py
│   │   ├── tasks.py           # Celery tasks
│   │   ├── signals.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   └── tests/
│   │       ├── test_models.py
│   │       ├── test_views.py
│   │       └── test_services.py
│   └── orders/
│       └── ...
├── common/                    # Shared utilities (mixins, base classes, utils)
│   ├── models.py              # Abstract base models
│   ├── serializers.py
│   ├── permissions.py
│   ├── pagination.py
│   └── exceptions.py
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
├── docs/
├── .env.example
├── .env                       # Never commit this
├── manage.py
└── docker-compose.yml
```

### Architecture Pattern: Services + Selectors

The key insight is to **keep your views thin**. Business logic should not live in views or serializers.

- **Views/ViewSets**: Handle HTTP — authentication, parsing, validation delegation, response formatting. Nothing else.
- **Serializers**: Validate and transform data only. No database calls inside serializers beyond what DRF needs.
- **Services**: All write operations and business logic (`create_user()`, `place_order()`). They take plain Python values, not request objects.
- **Selectors**: All read/query logic (`get_user_by_email()`, `list_active_orders()`). Returns querysets or model instances.
- **Models**: Data structure and simple model-level methods only. No business logic that spans multiple models.

```python
# ✅ Good — thin view, logic in service
class OrderCreateView(generics.CreateAPIView):
    serializer_class = OrderCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        order = create_order(user=self.request.user, **serializer.validated_data)
        # Return the created order in response
        self.kwargs['created_order'] = order

# ✅ Good — service handles business logic
# apps/orders/services.py
def create_order(*, user, items, coupon_code=None):
    with transaction.atomic():
        order = Order.objects.create(user=user)
        for item in items:
            OrderItem.objects.create(order=order, **item)
        if coupon_code:
            apply_coupon(order=order, code=coupon_code)
        send_order_confirmation.delay(order.id)
        return order
```

---

## 2. Settings & Configuration

### Split Settings by Environment

```python
# config/settings/base.py
from pathlib import Path
import environ

env = environ.Env()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Read .env file
environ.Env.read_env(BASE_DIR / ".env")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    # Local
    "apps.users",
    "apps.orders",
]

# Always use a custom user model
AUTH_USER_MODEL = "users.User"
```

```python
# config/settings/production.py
from .base import *

DEBUG = False
SECRET_KEY = env("DJANGO_SECRET_KEY")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")

DATABASES = {
    "default": env.db("DATABASE_URL")  # Uses dj-database-url format
}

# Security headers
SECURE_HSTS_SECONDS = 31536000
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

### Use django-environ for All Secrets

Never hardcode credentials. Always pull from environment variables:

```python
# .env.example (commit this)
DJANGO_SECRET_KEY=your-secret-key-here
DATABASE_URL=postgres://user:password@localhost:5432/mydb
REDIS_URL=redis://localhost:6379/0
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
```

```python
# In settings
SECRET_KEY = env("DJANGO_SECRET_KEY")
DATABASES = {"default": env.db("DATABASE_URL")}
CACHES = {"default": env.cache("REDIS_URL")}
```

---

## 3. Models & Database

### Always Use a Custom User Model

Do this **before your first migration**. Changing it later is painful.

```python
# apps/users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    email = models.EmailField(unique=True)
    # Add your custom fields here from the start
    phone_number = models.CharField(max_length=20, blank=True)
    
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]
    
    class Meta:
        db_table = "users"

# config/settings/base.py
AUTH_USER_MODEL = "users.User"
```

### Use a Base Model for Common Fields

```python
# common/models.py
import uuid
from django.db import models

class TimeStampedModel(models.Model):
    """Abstract base giving every model created_at and updated_at."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class UUIDModel(models.Model):
    """Use UUID as primary key instead of auto-increment integer."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True

class BaseModel(UUIDModel, TimeStampedModel):
    """Combine UUID + timestamps. Use this as your default base."""
    class Meta:
        abstract = True
```

### Model Field Best Practices

```python
class Order(BaseModel):
    # ✅ Use TextChoices instead of plain strings or separate constants
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,       # ✅ PROTECT by default, not CASCADE
        related_name="orders",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,                  # ✅ Index fields you filter/order by
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,               # ✅ Always DecimalField for money, never FloatField
    )
    notes = models.TextField(blank=True, default="")  # ✅ blank=True for optional text

    class Meta:
        ordering = ["-created_at"]      # ✅ Default ordering
        indexes = [
            models.Index(fields=["user", "status"]),  # Composite index for common queries
        ]

    def __str__(self):
        return f"Order {self.id} — {self.user.email}"
```

### Migrations Best Practices

```bash
# ✅ Always name your migrations descriptively
python manage.py makemigrations --name add_phone_to_user

# ✅ Squash migrations periodically on long-lived projects
python manage.py squashmigrations users 0001 0020

# ✅ Check SQL before applying in production
python manage.py sqlmigrate users 0005
```

**Rules:**
- Never edit a migration that has already been applied in production.
- Avoid RunPython in large migrations on tables with millions of rows — do data migrations separately.
- Always add `db_index=True` on ForeignKey targets, status fields, and any field you filter on.

### Soft Delete Pattern

```python
# common/models.py
from django.db import models
from django.utils import timezone

class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

class SoftDeleteModel(models.Model):
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()  # Includes deleted records

    def delete(self, *args, **kwargs):
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])

    def hard_delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)

    class Meta:
        abstract = True
```

---

## 4. Views & ViewSets

### Choose the Right View Class

| Use Case | Class to Use |
|---|---|
| Full CRUD on a resource | `ModelViewSet` |
| Read-only resource | `ReadOnlyModelViewSet` |
| Single endpoint logic | `APIView` |
| Generic create/list | `generics.ListCreateAPIView` |
| Generic retrieve/update/delete | `generics.RetrieveUpdateDestroyAPIView` |

```python
# apps/orders/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Order
from .serializers import OrderSerializer, OrderCreateSerializer, OrderCancelSerializer
from .services import create_order, cancel_order
from .selectors import get_user_orders
from .permissions import IsOrderOwner

class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOrderOwner]
    
    def get_queryset(self):
        # ✅ Always scope queryset to the current user where appropriate
        return get_user_orders(user=self.request.user)

    def get_serializer_class(self):
        # ✅ Use different serializers for different actions
        if self.action == "create":
            return OrderCreateSerializer
        if self.action == "cancel":
            return OrderCancelSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        # ✅ Delegate to a service, don't put logic here
        create_order(user=self.request.user, **serializer.validated_data)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        """Custom action for cancelling an order."""
        order = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cancel_order(order=order, reason=serializer.validated_data.get("reason"))
        return Response({"detail": "Order cancelled."}, status=status.HTTP_200_OK)
```

### ViewSet Method Reference

```python
# HTTP Method → ViewSet Action → URL
# GET  /orders/        → list()         → router auto-generates
# POST /orders/        → create()
# GET  /orders/{id}/   → retrieve()
# PUT  /orders/{id}/   → update()
# PATCH /orders/{id}/  → partial_update()
# DELETE /orders/{id}/ → destroy()
# POST /orders/{id}/cancel/ → cancel() (custom @action)
```

---

## 5. Serializers

### Keep Serializers Focused

```python
# apps/orders/serializers.py
from rest_framework import serializers
from .models import Order, OrderItem

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["id", "product", "quantity", "unit_price"]

class OrderSerializer(serializers.ModelSerializer):
    """Read serializer — returns nested data."""
    items = OrderItemSerializer(many=True, read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "user_email", "status", "status_display",
            "total_amount", "items", "created_at"
        ]
        read_only_fields = ["id", "total_amount", "created_at"]

class OrderCreateSerializer(serializers.Serializer):
    """Write serializer — validates input for order creation."""
    items = OrderItemInputSerializer(many=True)
    coupon_code = serializers.CharField(required=False, allow_blank=True)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("At least one item is required.")
        return value

    def validate(self, attrs):
        # Cross-field validation goes in validate()
        return attrs
```

### Field-Level vs Object-Level Validation

```python
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    # Field-level: validate_<fieldname>
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered.")
        return value.lower()

    # Object-level: validate()
    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs
```

### Use SerializerMethodField Sparingly

`SerializerMethodField` is handy but can cause N+1 problems. Prefer annotating your queryset instead.

```python
# ❌ Bad — causes N+1 queries if listing many orders
class OrderSerializer(serializers.ModelSerializer):
    item_count = serializers.SerializerMethodField()
    
    def get_item_count(self, obj):
        return obj.items.count()  # Database query per object!

# ✅ Good — annotate once at the queryset level
from django.db.models import Count

class OrderSerializer(serializers.ModelSerializer):
    item_count = serializers.IntegerField(read_only=True)

# In your selector/view:
Order.objects.annotate(item_count=Count("items"))
```

---

## 6. URLs & Routing

```python
# apps/orders/urls.py
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"orders", views.OrderViewSet, basename="order")

urlpatterns = router.urls

# config/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.users.urls")),
    path("api/v1/", include("apps.orders.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
```

---

## 7. Authentication & Permissions

### Authentication Options

| Method | Library | When to Use |
|---|---|---|
| JWT (stateless) | `djangorestframework-simplejwt` | SPAs, mobile apps, microservices |
| Session | Built-in DRF | Browser-based Django apps with CSRF |
| Token (simple) | Built-in DRF | Simple APIs, admin tools |
| OAuth2 | `django-oauth-toolkit` | Third-party integrations |

### JWT Setup with SimpleJWT

```python
# settings/base.py
from datetime import timedelta

INSTALLED_APPS += ["rest_framework_simplejwt"]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",  # Secure by default!
    ],
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# apps/users/urls.py
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path("auth/login/", TokenObtainPairView.as_view(), name="token_obtain"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
```

### Custom Permissions

```python
# apps/orders/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOrderOwner(BasePermission):
    """Only the order's owner can access it."""
    
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class IsAdminOrReadOnly(BasePermission):
    """Read access to all, write access to admins only."""
    
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_staff
```

**Permission Hierarchy:**
- `has_permission(request, view)` — runs for every request to the view
- `has_object_permission(request, view, obj)` — only runs when `get_object()` is called (detail views)

---

## 8. Filtering, Searching & Ordering

### Use django-filter

```python
# settings
INSTALLED_APPS += ["django_filters"]
REST_FRAMEWORK = {
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
}

# apps/orders/filters.py
import django_filters
from .models import Order

class OrderFilter(django_filters.FilterSet):
    status = django_filters.MultipleChoiceFilter(choices=Order.Status.choices)
    created_after = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_before = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")
    min_amount = django_filters.NumberFilter(field_name="total_amount", lookup_expr="gte")
    max_amount = django_filters.NumberFilter(field_name="total_amount", lookup_expr="lte")

    class Meta:
        model = Order
        fields = ["status", "user"]

# apps/orders/views.py
class OrderViewSet(viewsets.ModelViewSet):
    filterset_class = OrderFilter
    search_fields = ["user__email", "notes"]     # Searched with ?search=
    ordering_fields = ["created_at", "total_amount"]  # Ordered with ?ordering=
    ordering = ["-created_at"]                    # Default ordering
```

---

## 9. Pagination

```python
# common/pagination.py
from rest_framework.pagination import PageNumberPagination, CursorPagination

class StandardPagination(PageNumberPagination):
    """Use for standard offset pagination. Good for most cases."""
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

class CursorBasedPagination(CursorPagination):
    """
    Use for large datasets or real-time feeds.
    More efficient than offset pagination on huge tables.
    Prevents duplicate/skipped items on rapidly changing data.
    """
    page_size = 20
    ordering = "-created_at"

# settings/base.py
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "common.pagination.StandardPagination",
    "PAGE_SIZE": 20,
}
```

**When to use which:**
- `PageNumberPagination`: Admin panels, standard lists, when users need to jump to page N.
- `LimitOffsetPagination`: When clients need flexible control (good for analytics dashboards).
- `CursorPagination`: News feeds, chat, large tables — prevents the "missing items" problem when data changes between pages.

---

## 10. Caching

### Cache Querysets with django-cacheops or Manual Caching

```python
# Option 1: Manual caching with Redis
from django.core.cache import cache
from django.utils.functional import cached_property

def get_active_categories():
    cache_key = "active_categories"
    result = cache.get(cache_key)
    if result is None:
        result = list(Category.objects.filter(is_active=True).values("id", "name"))
        cache.set(cache_key, result, timeout=60 * 15)  # 15 minutes
    return result

# Option 2: django-cacheops (automatic query caching)
# settings/base.py
CACHEOPS = {
    "orders.Order": {"ops": "all", "timeout": 60 * 5},
    "users.User": {"ops": "get", "timeout": 60 * 60},
}

# Option 3: Per-view caching
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

class CategoryListView(generics.ListAPIView):
    @method_decorator(cache_page(60 * 15))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
```

### Cache Invalidation Strategy

```python
# Use signals or call invalidation in your services
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache

@receiver(post_save, sender=Category)
def invalidate_category_cache(sender, instance, **kwargs):
    cache.delete("active_categories")
    cache.delete_pattern("category:*")  # If using django-redis
```

---

## 11. Celery & Async Tasks

### Setup

```python
# config/celery.py
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")
app = Celery("my_project")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# config/__init__.py
from .celery import app as celery_app
__all__ = ("celery_app",)

# settings/base.py
CELERY_BROKER_URL = env("REDIS_URL")
CELERY_RESULT_BACKEND = env("REDIS_URL")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
```

### Task Best Practices

```python
# apps/orders/tasks.py
from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

@shared_task(
    bind=True,                      # ✅ bind=True gives access to self (task instance)
    max_retries=3,
    default_retry_delay=60,         # Retry after 60 seconds
    autoretry_for=(Exception,),     # ✅ Auto-retry on any exception
    retry_backoff=True,             # ✅ Exponential backoff
    retry_jitter=True,              # ✅ Randomize retry delay to avoid thundering herd
)
def send_order_confirmation(self, order_id):
    """Send confirmation email for an order."""
    from apps.orders.models import Order  # ✅ Import inside task to avoid circular imports
    
    try:
        order = Order.objects.get(id=order_id)
        # ... send email
        logger.info(f"Confirmation sent for order {order_id}")
    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found, skipping.")
        return  # Don't retry if record doesn't exist

# In your service — call tasks with .delay() or .apply_async()
send_order_confirmation.delay(order.id)  # Fire and forget
send_order_confirmation.apply_async(
    args=[order.id],
    countdown=300,                  # Run after 5 minutes
    expires=3600,                   # Expire after 1 hour
)
```

### Celery Beat for Scheduled Tasks

```python
# settings/base.py
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "cleanup-expired-sessions": {
        "task": "apps.users.tasks.cleanup_expired_sessions",
        "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM UTC
    },
    "send-daily-digest": {
        "task": "apps.notifications.tasks.send_daily_digest",
        "schedule": crontab(hour=8, minute=0),
    },
}
```

---

## 12. File Handling & Storage

### Use django-storages with S3

```python
# settings/production.py
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
STATICFILES_STORAGE = "storages.backends.s3boto3.S3StaticStorage"

AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default="us-east-1")
AWS_S3_FILE_OVERWRITE = False       # ✅ Don't overwrite files with the same name
AWS_DEFAULT_ACL = None              # ✅ Use bucket default ACL
AWS_S3_OBJECT_PARAMETERS = {
    "CacheControl": "max-age=86400",
}
```

### Validate Uploads

```python
# common/validators.py
from django.core.exceptions import ValidationError

def validate_file_size(file, max_mb=10):
    limit = max_mb * 1024 * 1024
    if file.size > limit:
        raise ValidationError(f"File size cannot exceed {max_mb}MB.")

def validate_image_extension(file):
    import os
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
        raise ValidationError("Unsupported image format.")

# In your model
class UserProfile(BaseModel):
    avatar = models.ImageField(
        upload_to="avatars/%Y/%m/",
        validators=[validate_file_size, validate_image_extension],
        blank=True,
    )
```

---

## 13. Testing

### Testing Stack

- **pytest-django**: Better test runner than Django's built-in.
- **factory_boy**: For creating test fixtures programmatically.
- **faker**: Generating realistic fake data.
- **coverage**: Track test coverage.

### Setup

```python
# requirements/development.txt
pytest
pytest-django
pytest-cov
factory-boy
faker
freezegun       # Freeze time in tests
responses       # Mock HTTP requests

# pytest.ini or pyproject.toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings.testing"
python_files = "test_*.py"
addopts = "--cov=apps --cov-report=term-missing --reuse-db"
```

### Factories

```python
# apps/users/tests/factories.py
import factory
from factory.django import DjangoModelFactory
from faker import Faker
from apps.users.models import User

fake = Faker()

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    email = factory.LazyFunction(lambda: fake.unique.email())
    username = factory.LazyAttribute(lambda obj: obj.email.split("@")[0])
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    is_active = True

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        obj.set_password(extracted or "testpass123!")
        if create:
            obj.save()
```

### Writing Tests

```python
# apps/orders/tests/test_views.py
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from .factories import UserFactory, OrderFactory

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def authenticated_client(api_client):
    user = UserFactory()
    api_client.force_authenticate(user=user)
    return api_client, user

@pytest.mark.django_db
class TestOrderAPI:
    def test_list_orders_requires_auth(self, api_client):
        url = reverse("order-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_user_sees_only_their_orders(self, authenticated_client):
        client, user = authenticated_client
        other_user = UserFactory()
        own_order = OrderFactory(user=user)
        other_order = OrderFactory(user=other_user)
        
        url = reverse("order-list")
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        order_ids = [o["id"] for o in response.data["results"]]
        assert str(own_order.id) in order_ids
        assert str(other_order.id) not in order_ids

    def test_create_order_success(self, authenticated_client):
        client, user = authenticated_client
        payload = {"items": [{"product": 1, "quantity": 2}]}
        
        response = client.post(reverse("order-list"), data=payload, format="json")
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == "pending"
```

---

## 14. API Versioning

### URL Versioning (Recommended)

```python
# config/urls.py
urlpatterns = [
    path("api/v1/", include("apps.api_v1.urls")),
    path("api/v2/", include("apps.api_v2.urls")),
]

# settings/base.py
REST_FRAMEWORK = {
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.URLPathVersioning",
    "ALLOWED_VERSIONS": ["v1", "v2"],
    "DEFAULT_VERSION": "v1",
}
```

### Header Versioning (Alternative)

```python
REST_FRAMEWORK = {
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.AcceptHeaderVersioning",
}
# Client sends: Accept: application/json; version=v2
```

### Handling Versions in Views

```python
class OrderViewSet(viewsets.ModelViewSet):
    def get_serializer_class(self):
        if self.request.version == "v2":
            return OrderSerializerV2
        return OrderSerializer
```

---

## 15. Error Handling

### Global Exception Handler

```python
# common/exceptions.py
from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException
from rest_framework import status

class ServiceError(APIException):
    """Raise from service layer for known business logic errors."""
    status_code = status.HTTP_400_BAD_REQUEST

class NotFoundError(APIException):
    status_code = status.HTTP_404_NOT_FOUND

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    
    if response is not None:
        # Normalize error format across all errors
        response.data = {
            "error": {
                "code": response.status_code,
                "message": _extract_message(response.data),
                "details": response.data,
            }
        }
    
    return response

def _extract_message(data):
    if isinstance(data, dict):
        return data.get("detail", "An error occurred.")
    if isinstance(data, list):
        return data[0] if data else "An error occurred."
    return str(data)

# settings/base.py
REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "common.exceptions.custom_exception_handler",
}
```

---

## 16. Security

### Checklist

```python
# settings/production.py

# CORS — be specific, never use "*" in production
CORS_ALLOWED_ORIGINS = [
    "https://app.mysite.com",
]
CORS_ALLOW_CREDENTIALS = True

# Rate limiting with django-ratelimit or drf-throttling
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
    },
}

# Security headers (also set at Nginx/CDN level)
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
```

### Input Sanitization

```python
# ✅ DRF serializers handle input sanitization automatically
# ✅ Never pass request.data directly to a model — always validate through a serializer
# ✅ Use parameterized queries (Django ORM does this), never raw SQL with f-strings

# ❌ NEVER do this
User.objects.raw(f"SELECT * FROM users WHERE email = '{email}'")

# ✅ Safe raw SQL if you must
User.objects.raw("SELECT * FROM users WHERE email = %s", [email])
```

---

## 17. Performance & Optimization

### Avoid N+1 Queries

```python
# ❌ Bad — N+1: 1 query for orders + 1 per order for user
orders = Order.objects.all()
for order in orders:
    print(order.user.email)  # New query each iteration

# ✅ Good — select_related for FK/OneToOne (SQL JOIN)
orders = Order.objects.select_related("user").all()

# ✅ Good — prefetch_related for ManyToMany/reverse FK (separate query, then Python join)
orders = Order.objects.prefetch_related("items").all()

# ✅ Combine both
orders = Order.objects.select_related("user").prefetch_related("items").all()
```

### Use values() and only() to Reduce Data Transfer

```python
# ✅ Only fetch what you need
orders = Order.objects.values("id", "status", "total_amount")

# ✅ Load only specific fields into model instances
orders = Order.objects.only("id", "status").select_related("user")

# ✅ Use defer() to exclude heavy fields
orders = Order.objects.defer("notes", "internal_metadata")
```

### Annotate Instead of Computing in Python

```python
from django.db.models import Count, Sum, Avg, Q

# ✅ Let the database do the heavy lifting
stats = Order.objects.aggregate(
    total_orders=Count("id"),
    total_revenue=Sum("total_amount"),
    avg_order_value=Avg("total_amount"),
    pending_count=Count("id", filter=Q(status="pending")),
)
```

### Database Connection Pooling

```python
# Use PgBouncer externally, or pgpool-II
# Or use django-db-geventpool / psycogreen in production
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "CONN_MAX_AGE": 60,          # Keep connections alive for 60s
        "CONN_HEALTH_CHECKS": True,  # Django 4.1+
    }
}
```

### Use Django Debug Toolbar in Development

```python
# development.py
INSTALLED_APPS += ["debug_toolbar"]
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
INTERNAL_IPS = ["127.0.0.1"]

# Check the SQL panel — every N+1 shows up here
```

---

## 18. Logging & Monitoring

```python
# settings/base.py
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": env("DJANGO_LOG_LEVEL", default="INFO"),
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

# In your code — use named loggers, not the root logger
import logging
logger = logging.getLogger(__name__)

def create_order(...):
    logger.info("Creating order for user %s", user.id)
    try:
        ...
    except Exception as e:
        logger.exception("Failed to create order for user %s: %s", user.id, str(e))
        raise
```

### Monitoring Tools

- **Sentry**: Exception tracking and performance monitoring (`pip install sentry-sdk`).
- **Prometheus + Grafana**: Metrics via `django-prometheus`.
- **New Relic / Datadog**: APM for production.

```python
# Sentry setup
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

sentry_sdk.init(
    dsn=env("SENTRY_DSN"),
    integrations=[DjangoIntegration(), CeleryIntegration()],
    traces_sample_rate=0.1,  # 10% of transactions
    send_default_pii=False,  # Don't send user PII
)
```

---

## 19. Documentation (drf-spectacular / Swagger)

### Setup

```python
# pip install drf-spectacular

INSTALLED_APPS += ["drf_spectacular"]

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "My API",
    "DESCRIPTION": "API documentation for My Project",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# config/urls.py
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns += [
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
```

### Annotating Views

```python
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

class OrderViewSet(viewsets.ModelViewSet):
    @extend_schema(
        summary="List user's orders",
        description="Returns paginated list of the authenticated user's orders.",
        parameters=[
            OpenApiParameter("status", str, description="Filter by order status"),
        ],
        responses={200: OrderSerializer(many=True)},
        tags=["Orders"],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
```

---

## 20. Deployment & DevOps

### Docker Setup

```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/production.txt .
RUN pip install --no-cache-dir -r production.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
```

```yaml
# docker-compose.yml
version: "3.9"
services:
  web:
    build: .
    env_file: .env
    depends_on: [db, redis]
    ports:
      - "8000:8000"
  
  db:
    image: postgres:16
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}

  redis:
    image: redis:7-alpine

  celery:
    build: .
    command: celery -A config worker -l info -c 4
    env_file: .env
    depends_on: [db, redis]

  celery-beat:
    build: .
    command: celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    env_file: .env
    depends_on: [db, redis]

volumes:
  postgres_data:
```

### Production Checklist Items

```bash
# Run before every deploy
python manage.py check --deploy    # Django's built-in security check
python manage.py migrate           # Apply migrations
python manage.py collectstatic     # Gather static files
```

---

## 21. Essential Libraries Cheat Sheet

| Library | Purpose | Install |
|---|---|---|
| `djangorestframework` | REST API core | Always |
| `django-environ` | Environment variable config | Always |
| `psycopg2-binary` | PostgreSQL adapter | Always |
| `gunicorn` | WSGI server | Production |
| `whitenoise` | Serve static files | Production |
| `djangorestframework-simplejwt` | JWT authentication | When using JWT |
| `django-cors-headers` | CORS handling | When SPA frontend |
| `django-filter` | Queryset filtering | Almost always |
| `drf-spectacular` | OpenAPI/Swagger docs | Almost always |
| `celery` + `redis` | Async task queue | When async needed |
| `django-storages` + `boto3` | S3 file storage | Production file uploads |
| `factory-boy` | Test factories | Testing |
| `pytest-django` | Better test runner | Testing |
| `sentry-sdk` | Error tracking | Production |
| `django-debug-toolbar` | SQL query inspector | Development |
| `django-extensions` | Useful management commands | Development |
| `django-silk` | Request profiling | Development |
| `django-celery-beat` | DB-backed celery scheduling | When using celery beat |
| `django-redis` | Redis cache backend | When using Redis cache |

---

## 22. The Master Checklist

Use this checklist every time you build something new. Check each item before considering the work done.

---

### 📦 Starting a New Project

- [ ] Created custom User model **before** any migrations
- [ ] Settings split into `base.py`, `development.py`, `production.py`
- [ ] All secrets in `.env` via `django-environ`, never hardcoded
- [ ] `.env.example` committed, `.env` in `.gitignore`
- [ ] PostgreSQL configured (not SQLite for anything beyond local dev)
- [ ] Redis configured (for caching and Celery broker)
- [ ] Project structure follows apps + config + common layout
- [ ] `requirements/` split into base, dev, and prod files
- [ ] Docker and docker-compose configured
- [ ] CI/CD pipeline configured (GitHub Actions, GitLab CI, etc.)

---

### 🗄️ Building a Model

- [ ] Inherits from `BaseModel` (UUID primary key + timestamps)
- [ ] Used `TextChoices` for any enum-like fields
- [ ] Used `DecimalField` for any monetary amounts (not `FloatField`)
- [ ] `on_delete=models.PROTECT` on ForeignKeys (unless CASCADE is intentional)
- [ ] Added `db_index=True` on fields that will be filtered or ordered by
- [ ] Added composite `indexes` in `Meta` for common multi-field queries
- [ ] Added `__str__` method
- [ ] Added default `ordering` in `Meta`
- [ ] Migration is named descriptively (`--name add_status_to_order`)
- [ ] Checked `python manage.py sqlmigrate` output before applying
- [ ] No business logic in model methods (only simple property-like methods)
- [ ] If soft delete needed, inherits from `SoftDeleteModel`

---

### 🔌 Building a Serializer

- [ ] Separate serializers for read vs. write (don't reuse one serializer for everything)
- [ ] Sensitive fields marked `write_only=True` (passwords, tokens)
- [ ] Computed fields annotated in queryset, not using `SerializerMethodField` with DB calls
- [ ] Field-level validation in `validate_<fieldname>()` methods
- [ ] Cross-field validation in `validate()` method
- [ ] `read_only_fields` declared in `Meta` for fields the client shouldn't modify
- [ ] No database writes inside serializer `validate_*` methods

---

### 👁️ Building a View / ViewSet

- [ ] Using the right base class (see table in Section 4)
- [ ] `get_queryset()` scopes data to the current user where appropriate
- [ ] `get_serializer_class()` returns different serializers per action
- [ ] Permissions are explicit and tested
- [ ] `perform_create()` / `perform_update()` delegates to a service
- [ ] No business logic directly in the view method
- [ ] Custom actions use `@action` decorator with correct `methods` and `detail` settings
- [ ] Response status codes are correct (201 for create, 204 for delete, etc.)
- [ ] View is documented with `@extend_schema`

---

### 🛣️ Building URLs

- [ ] Using `DefaultRouter` for ViewSets
- [ ] URL patterns are under a version prefix (`/api/v1/`)
- [ ] URL names are consistent (`order-list`, `order-detail`)
- [ ] No logic in `urls.py`

---

### 🔐 Authentication & Permissions

- [ ] Default permission class is `IsAuthenticated` (secure by default)
- [ ] Public endpoints explicitly set `permission_classes = [AllowAny]`
- [ ] Custom permissions implement both `has_permission` and `has_object_permission` where needed
- [ ] JWT tokens have appropriate lifetimes (short access, longer refresh)
- [ ] Refresh token rotation and blacklisting enabled
- [ ] Throttling configured for auth endpoints

---

### ⚙️ Building a Service

- [ ] Service is a plain Python function in `services.py`
- [ ] Takes plain Python values as arguments (not `request` object)
- [ ] Wrapped in `transaction.atomic()` if it does multiple writes
- [ ] Raises `ServiceError` (or specific exception) for business logic failures
- [ ] Celery tasks are called with `.delay()` or `.apply_async()`, not run synchronously
- [ ] No HTTP logic, no serializer logic, no queryset building in services

---

### 📊 Building a Selector (Query Layer)

- [ ] Lives in `selectors.py`
- [ ] Returns querysets or model instances (not serialized data)
- [ ] Uses `select_related()` / `prefetch_related()` to avoid N+1 queries
- [ ] Uses `only()` or `values()` when full model instances aren't needed
- [ ] Uses `annotate()` for computed fields instead of Python-side computation
- [ ] Queryset is lazy (not evaluated until necessary)

---

### ⏱️ Building a Celery Task

- [ ] Task is idempotent (safe to run multiple times with the same input)
- [ ] Uses `bind=True` and handles retries with exponential backoff
- [ ] Imports done inside the task function to avoid circular imports
- [ ] Handles the case where the referenced DB record no longer exists
- [ ] Logs success and failure at appropriate levels
- [ ] Task is registered in `CELERY_BEAT_SCHEDULE` if it's a periodic task
- [ ] Task is tested with `@pytest.mark.django_db` and `task.apply()` for sync execution

---

### 🔍 Adding Filtering/Search/Ordering

- [ ] `FilterSet` defined in `filters.py` (not inline in the view)
- [ ] `filterset_class` set on the ViewSet
- [ ] `search_fields` and `ordering_fields` declared
- [ ] Filters are tested (invalid inputs return 400, not 500)

---

### 📄 Adding Pagination

- [ ] Correct pagination class chosen for the use case
- [ ] `page_size` and `max_page_size` set to sensible values
- [ ] Pagination response format is consistent

---

### 🧪 Writing Tests

- [ ] Factories exist for all models involved
- [ ] Tests cover the happy path
- [ ] Tests cover auth requirements (unauthenticated returns 401, wrong user returns 403/404)
- [ ] Tests cover validation errors (invalid input returns 400)
- [ ] Tests cover edge cases (empty lists, missing optional fields, etc.)
- [ ] No real HTTP calls in tests (external services mocked)
- [ ] Test coverage is above 80%
- [ ] `pytest --reuse-db` used for speed

---

### 🚀 Deploying a Feature

- [ ] `python manage.py check --deploy` passes with no issues
- [ ] All migrations created and reviewed
- [ ] Zero-downtime migration strategy used for large tables (add nullable, backfill, add constraint)
- [ ] Static files collected
- [ ] Environment variables updated in production
- [ ] Sentry error tracking verified
- [ ] Feature tested in staging before production deploy
- [ ] Rollback plan exists if migration fails

---

### 🌐 Building a REST API Service (Public API)

- [ ] Versioned from the start (`/api/v1/`)
- [ ] Swagger/OpenAPI documentation available and accurate
- [ ] All endpoints secured with appropriate authentication
- [ ] Rate limiting configured
- [ ] CORS configured to only allow known origins
- [ ] Error responses have a consistent format
- [ ] Pagination on all list endpoints
- [ ] Input size limits enforced (max file size, max list length, etc.)
- [ ] Sensitive data never returned in responses (passwords, internal IDs, etc.)
- [ ] Idempotent endpoints where appropriate (PUT, PATCH, DELETE)

---

### 🔔 Building a Notification Service

- [ ] Notifications sent asynchronously via Celery task
- [ ] Templates stored in `templates/email/` (never inline HTML strings)
- [ ] Unsubscribe mechanism in place for email
- [ ] Failed notifications are retried with backoff
- [ ] Notification preferences are user-configurable
- [ ] Test mode sends to a test address, not real users

---

### 🔎 Building a Search Feature

- [ ] Simple text search: use `SearchFilter` + `search_fields` in DRF
- [ ] Full-text search: use `django.contrib.postgres.search` (PostgreSQL) or Elasticsearch
- [ ] Consider `django-elasticsearch-dsl` for Elasticsearch integration
- [ ] Search queries are indexed (PostgreSQL `GinIndex` for full-text search)
- [ ] Results are paginated
- [ ] Search is debounced on the frontend to avoid excessive API calls

---

### 📊 Building a Reporting/Analytics Endpoint

- [ ] Uses `values()` + `annotate()` + `aggregate()` at the database level
- [ ] Results are cached with appropriate TTL (reports are expensive)
- [ ] Date range filters are enforced (no unbounded queries)
- [ ] Pagination or limit applied (don't return 100k rows)
- [ ] Consider background generation for large reports (Celery task + polling)

---

*Last updated: 2026. Always check the official Django and DRF documentation for the latest changes.*
