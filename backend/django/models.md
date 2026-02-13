# Django Models Guidelines

## Table of Contents
- [Overview](#overview)
- [Model Structure](#model-structure)
- [Field Definitions](#field-definitions)
- [Relationships](#relationships)
- [Meta Options](#meta-options)
- [Model Methods](#model-methods)
- [Managers and QuerySets](#managers-and-querysets)
- [Validation](#validation)
- [Best Practices](#best-practices)

## Overview

Models are the single, definitive source of information about your data. They contain the essential fields and behaviors of the data you're storing.

## Model Structure

### Basic Structure

```python
from django.db import models
from django.utils.translation import gettext_lazy as _


class Article(models.Model):
    """
    Model representing a blog article.
    
    Attributes:
        title: The article title
        slug: URL-friendly version of the title
        content: The main article content
        author: ForeignKey to User model
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """
    title = models.CharField(
        max_length=200,
        verbose_name=_("Title"),
        help_text=_("Enter the article title")
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name=_("Slug")
    )
    content = models.TextField(verbose_name=_("Content"))
    author = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='articles',
        verbose_name=_("Author")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Article")
        verbose_name_plural = _("Articles")
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['slug']),
        ]
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('article-detail', kwargs={'slug': self.slug})
```

## Field Definitions

### Common Fields

```python
# CharField - for short strings
title = models.CharField(max_length=200)

# TextField - for long text
description = models.TextField(blank=True)

# IntegerField
views_count = models.IntegerField(default=0)

# DecimalField - for precise decimal numbers
price = models.DecimalField(max_digits=10, decimal_places=2)

# BooleanField
is_published = models.BooleanField(default=False)

# DateTimeField
created_at = models.DateTimeField(auto_now_add=True)
updated_at = models.DateTimeField(auto_now=True)

# EmailField
email = models.EmailField(unique=True)

# URLField
website = models.URLField(blank=True)

# FileField / ImageField
document = models.FileField(upload_to='documents/%Y/%m/%d/')
image = models.ImageField(upload_to='images/%Y/%m/%d/')

# JSONField (Django 3.1+)
metadata = models.JSONField(default=dict, blank=True)
```

### Field Options

```python
# Common field options
field = models.CharField(
    max_length=100,
    null=False,              # Database allows NULL
    blank=False,             # Forms allow empty
    default='default value', # Default value
    unique=True,             # Must be unique
    db_index=True,          # Create database index
    verbose_name="Field Name",
    help_text="Help text for this field",
    choices=[                # Predefined choices
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]
)
```

## Relationships

### ForeignKey (Many-to-One)

```python
class Comment(models.Model):
    article = models.ForeignKey(
        'Article',
        on_delete=models.CASCADE,  # Delete comments when article is deleted
        related_name='comments',    # Access via article.comments.all()
        related_query_name='comment' # For filtering: Article.objects.filter(comment__text=...)
    )
```

### on_delete Options

```python
# CASCADE - Delete related objects
author = models.ForeignKey(User, on_delete=models.CASCADE)

# PROTECT - Prevent deletion if related objects exist
category = models.ForeignKey(Category, on_delete=models.PROTECT)

# SET_NULL - Set to NULL (requires null=True)
editor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

# SET_DEFAULT - Set to default value
status = models.ForeignKey(Status, on_delete=models.SET_DEFAULT, default=1)

# DO_NOTHING - Do nothing (can cause database integrity errors)
legacy = models.ForeignKey(Legacy, on_delete=models.DO_NOTHING)
```

### ManyToManyField

```python
class Article(models.Model):
    tags = models.ManyToManyField(
        'Tag',
        related_name='articles',
        blank=True,
        through='ArticleTag'  # Custom intermediate table
    )

# Custom through model for additional fields
class ArticleTag(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    added_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [['article', 'tag']]
```

### OneToOneField

```python
class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True)
```

## Meta Options

### Common Meta Options

```python
class Article(models.Model):
    # ... fields ...
    
    class Meta:
        # Ordering
        ordering = ['-created_at', 'title']
        
        # Database table name
        db_table = 'blog_articles'
        
        # Verbose names
        verbose_name = "Article"
        verbose_name_plural = "Articles"
        
        # Unique together (deprecated in favor of constraints)
        unique_together = [['author', 'slug']]
        
        # Indexes
        indexes = [
            models.Index(fields=['created_at', 'author']),
            models.Index(fields=['-published_date']),
        ]
        
        # Constraints (Django 2.2+)
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'slug'],
                name='unique_author_slug'
            ),
            models.CheckConstraint(
                check=models.Q(views_count__gte=0),
                name='views_count_positive'
            ),
        ]
        
        # Permissions
        permissions = [
            ("can_publish", "Can publish articles"),
            ("can_feature", "Can feature articles"),
        ]
        
        # Abstract model
        abstract = False
        
        # Default manager name
        default_manager_name = 'objects'
```

## Model Methods

### Standard Methods

```python
class Article(models.Model):
    # ... fields ...
    
    def __str__(self):
        """String representation"""
        return self.title
    
    def __repr__(self):
        """Developer representation"""
        return f"<Article: {self.title}>"
    
    def get_absolute_url(self):
        """Canonical URL for the object"""
        from django.urls import reverse
        return reverse('article-detail', kwargs={'slug': self.slug})
    
    def save(self, *args, **kwargs):
        """Override save method"""
        # Auto-generate slug from title
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.title)
        
        # Call parent save
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Override delete method"""
        # Perform cleanup before deletion
        if self.image:
            self.image.delete()
        super().delete(*args, **kwargs)
```

### Custom Methods

```python
class Article(models.Model):
    # ... fields ...
    
    def is_published(self):
        """Check if article is published"""
        return self.status == 'published' and self.published_date <= timezone.now()
    
    def get_reading_time(self):
        """Calculate estimated reading time"""
        word_count = len(self.content.split())
        minutes = word_count // 200  # Assuming 200 words per minute
        return max(1, minutes)
    
    def increment_views(self):
        """Increment view count atomically"""
        from django.db.models import F
        Article.objects.filter(pk=self.pk).update(views_count=F('views_count') + 1)
        self.refresh_from_db()
    
    @property
    def summary(self):
        """Get article summary"""
        return self.content[:200] + '...' if len(self.content) > 200 else self.content
```

## Managers and QuerySets

### Custom Manager

```python
class PublishedManager(models.Manager):
    """Manager for published articles"""
    
    def get_queryset(self):
        return super().get_queryset().filter(
            status='published',
            published_date__lte=timezone.now()
        )

class Article(models.Model):
    # ... fields ...
    
    # Managers
    objects = models.Manager()  # Default manager
    published = PublishedManager()  # Custom manager
    
    # Usage:
    # Article.objects.all()  # All articles
    # Article.published.all()  # Only published articles
```

### Custom QuerySet

```python
class ArticleQuerySet(models.QuerySet):
    """Custom queryset for articles"""
    
    def published(self):
        return self.filter(
            status='published',
            published_date__lte=timezone.now()
        )
    
    def by_author(self, author):
        return self.filter(author=author)
    
    def recent(self, days=7):
        from django.utils import timezone
        from datetime import timedelta
        cutoff = timezone.now() - timedelta(days=days)
        return self.filter(created_at__gte=cutoff)

class ArticleManager(models.Manager):
    def get_queryset(self):
        return ArticleQuerySet(self.model, using=self._db)
    
    def published(self):
        return self.get_queryset().published()
    
    def by_author(self, author):
        return self.get_queryset().by_author(author)
    
    def recent(self, days=7):
        return self.get_queryset().recent(days)

class Article(models.Model):
    # ... fields ...
    objects = ArticleManager()
    
    # Usage:
    # Article.objects.published().recent(14)
```

## Validation

### Field-level Validation

```python
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator

class Article(models.Model):
    rating = models.IntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5)
        ]
    )
    
    def clean_fields(self, exclude=None):
        """Field-level validation"""
        super().clean_fields(exclude=exclude)
        
        if self.title and len(self.title) < 5:
            raise ValidationError({
                'title': 'Title must be at least 5 characters long.'
            })
```

### Model-level Validation

```python
class Article(models.Model):
    # ... fields ...
    
    def clean(self):
        """Model-level validation"""
        super().clean()
        
        # Cross-field validation
        if self.status == 'published' and not self.published_date:
            raise ValidationError({
                'published_date': 'Published date is required for published articles.'
            })
        
        # Business logic validation
        if self.published_date and self.published_date < self.created_at:
            raise ValidationError(
                'Published date cannot be before creation date.'
            )
```

### Custom Validators

```python
from django.core.exceptions import ValidationError

def validate_word_count(value):
    """Validate minimum word count"""
    word_count = len(value.split())
    if word_count < 100:
        raise ValidationError(
            f'Content must be at least 100 words. Current: {word_count}'
        )

class Article(models.Model):
    content = models.TextField(validators=[validate_word_count])
```

## Best Practices

### 1. Model Organization

```python
# Order of model inner classes and methods:
class Article(models.Model):
    # 1. Database fields
    title = models.CharField(max_length=200)
    
    # 2. Custom managers
    objects = ArticleManager()
    
    # 3. Meta class
    class Meta:
        ordering = ['-created_at']
    
    # 4. __str__ method
    def __str__(self):
        return self.title
    
    # 5. save/delete methods
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
    
    # 6. get_absolute_url
    def get_absolute_url(self):
        pass
    
    # 7. Other methods and properties
    def custom_method(self):
        pass
```

### 2. Use `blank` and `null` Correctly

```python
# For string fields: use blank=True, NOT null=True
title = models.CharField(max_length=200, blank=True)  # Good
title = models.CharField(max_length=200, null=True)   # Bad

# For non-string fields: use both if optional
age = models.IntegerField(null=True, blank=True)  # Good
```

### 3. Use Choices Properly

```python
class Article(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'
        ARCHIVED = 'archived', 'Archived'
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
```

### 4. Timestamp Fields

```python
# Always include timestamp fields
class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

# Use in other models
class Article(BaseModel):
    title = models.CharField(max_length=200)
```

### 5. Use Related Names

```python
# Always use descriptive related_name
author = models.ForeignKey(
    User,
    on_delete=models.CASCADE,
    related_name='articles'  # Good: user.articles.all()
)

# Avoid default related_name
author = models.ForeignKey(
    User,
    on_delete=models.CASCADE  # Bad: user.article_set.all()
)
```

### 6. Database Indexes

```python
class Article(models.Model):
    # ... fields ...
    
    class Meta:
        indexes = [
            # Index frequently queried fields
            models.Index(fields=['status', '-created_at']),
            # Index foreign keys (if not auto-indexed)
            models.Index(fields=['author']),
        ]
```

### 7. Abstract Base Models

```python
class TimeStampedModel(models.Model):
    """Abstract base model with timestamp fields"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class SoftDeleteModel(models.Model):
    """Abstract base model for soft deletion"""
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        abstract = True
    
    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

# Use them
class Article(TimeStampedModel, SoftDeleteModel):
    title = models.CharField(max_length=200)
```

### 8. Avoid N+1 Queries

```python
# Bad - causes N+1 queries
articles = Article.objects.all()
for article in articles:
    print(article.author.name)  # Query for each article

# Good - use select_related for ForeignKey
articles = Article.objects.select_related('author').all()
for article in articles:
    print(article.author.name)  # No additional queries

# Good - use prefetch_related for ManyToMany
articles = Article.objects.prefetch_related('tags').all()
for article in articles:
    print(article.tags.all())  # No additional queries
```

### 9. F() Expressions for Updates

```python
from django.db.models import F

# Bad - race condition
article = Article.objects.get(pk=1)
article.views_count += 1
article.save()

# Good - atomic operation
Article.objects.filter(pk=1).update(views_count=F('views_count') + 1)
```

### 10. Signals Usage

```python
# Use signals sparingly - prefer overriding save()
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Article)
def article_post_save(sender, instance, created, **kwargs):
    if created:
        # Send notification for new article
        send_notification(instance)
```

### 11. String Representation

```python
# Always provide meaningful __str__
def __str__(self):
    return f"{self.title} by {self.author.username}"  # Good

def __str__(self):
    return str(self.id)  # Bad
```

### 12. Use `get_or_create` and `update_or_create`

```python
# Get or create
article, created = Article.objects.get_or_create(
    slug='my-article',
    defaults={'title': 'My Article', 'author': user}
)

# Update or create
article, created = Article.objects.update_or_create(
    slug='my-article',
    defaults={'title': 'Updated Title', 'author': user}
)
```

## Conclusion

Following these guidelines will help you create robust, maintainable, and efficient Django models. Remember to:

- Keep models focused and single-purpose
- Use appropriate field types and options
- Implement proper validation
- Optimize database queries
- Follow Django conventions and best practices
