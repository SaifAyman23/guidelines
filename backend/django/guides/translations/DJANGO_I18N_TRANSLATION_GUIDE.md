# Django i18n Translation Guide: Complete Implementation with gettext_lazy

A comprehensive guide to implementing internationalization (i18n) in Django applications, covering everything from models to views to error messages.

---

## Table of Contents

1. [Getting Started with gettext_lazy](#getting-started)
2. [Project Setup](#project-setup)
3. [Models and Choices](#models-and-choices)
4. [Views and Error Messages](#views-and-error-messages)
5. [Forms and Validation](#forms-and-validation)
6. [Templates](#templates)
7. [Management Commands](#management-commands)
8. [Celery Tasks and Async Work](#celery-tasks)
9. [Best Practices](#best-practices)
10. [Quick Reference](#quick-reference)
11. [Reusable Components](#reusable-components)

---

## Getting Started with gettext_lazy {#getting-started}

### What is gettext_lazy?

`gettext_lazy` (imported as `_lazy` or `_`) is Django's lazy translation function. Unlike regular `gettext`, it **delays translation until the string is actually used**. This is critical for module-level code like model definitions.

**Why is this important?**

- **Regular gettext**: Translates immediately at import time. At this point, Django isn't fully initialized, and the language context might not be set correctly.
- **gettext_lazy**: Returns a "lazy" object that translates only when converted to a string. Perfect for definitions.

### The Key Rule

```
Use gettext_lazy for:
- Model field definitions
- Form field definitions
- Settings and configuration
- Choice labels
- Any module-level strings

Use gettext (eager) for:
- View messages (at request time)
- Exception messages in functions
- Management command output
- Celery task messages
```

---

## Project Setup {#project-setup}

### Step 1: Configure settings.py

```python
# settings.py
import os
from django.utils.translation import gettext_lazy as _

# Define supported languages
LANGUAGE_CODE = 'en-us'

LANGUAGES = [
    ('en', _('English')),
    ('es', _('Spanish')),
    ('fr', _('French')),
    ('de', _('German')),
    ('ja', _('Japanese')),
    ('pt-br', _('Portuguese (Brazil)')),
    ('zh-hans', _('Simplified Chinese')),
]

# Enable internationalization
I18N = True
USE_I18N = True
USE_L10N = True  # Localized formatting (numbers, dates, etc.)

# Add locale middleware for language detection
MIDDLEWARE = [
    'django.middleware.locale.LocaleMiddleware',  # After SessionMiddleware
    # ... other middleware
]

# Where translation files live
LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
    os.path.join(BASE_DIR, 'apps', 'accounts', 'locale'),
]

# Time zone
TIME_ZONE = 'UTC'
USE_TZ = True
```

### Step 2: Configure urls.py

```python
# urls.py
from django.conf.urls.i18n import i18n_patterns
from django.urls import path, include

urlpatterns = [
    # Non-translated URLs (admin, API, etc.)
    path('api/', include('api.urls')),
]

# Translated URLs
urlpatterns += i18n_patterns(
    path('articles/', include('articles.urls')),
    path('accounts/', include('accounts.urls')),
    # ... other translated patterns
    prefix_default_language=True,  # Include language prefix for default language
)
```

### Step 3: Essential Imports

Create a habit of using these imports:

```python
# Models, forms, settings (module-level code)
from django.utils.translation import gettext_lazy as _

# Views, functions, commands (runtime code)
from django.utils.translation import gettext as _

# Pluralization
from django.utils.translation import ngettext, ngettext_lazy

# Context-aware translation (same word, different meanings)
from django.utils.translation import pgettext, pgettext_lazy

# Language control
from django.utils.translation import activate, override, get_language
```

---

## Models and Choices {#models-and-choices}

### Basic Model with Translatable Fields

```python
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class Article(models.Model):
    """
    Blog article model with full i18n support.
    
    All user-facing text uses gettext_lazy to ensure translation.
    """
    
    # Use gettext_lazy for all verbose_name and help_text
    title = models.CharField(
        max_length=200,
        verbose_name=_("Title"),  # Admin, forms will show translated label
        help_text=_("Enter a concise article title")
    )
    
    slug = models.SlugField(
        unique=True,
        verbose_name=_("Slug"),
        help_text=_("URL-friendly version of the title")
    )
    
    content = models.TextField(
        verbose_name=_("Content"),
        help_text=_("Main article body. Supports Markdown.")
    )
    
    summary = models.TextField(
        blank=True,
        verbose_name=_("Summary"),
        help_text=_("Brief overview shown in listings")
    )
    
    author = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='articles',
        verbose_name=_("Author")
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created at")
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated at")
    )
    
    is_published = models.BooleanField(
        default=False,
        verbose_name=_("Published")
    )
    
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Published at")
    )
    
    # Meta class with translations
    class Meta:
        verbose_name = _("Article")
        verbose_name_plural = _("Articles")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['slug']),
        ]
    
    def __str__(self):
        """User-facing string representation."""
        return self.title
```

### TextChoices for Status Fields (Recommended)

Django 3.0+ provides `TextChoices` and `IntegerChoices` for cleaner, translatable choices:

```python
class Article(models.Model):
    """Article with translatable status and priority."""
    
    # Option 1: TextChoices (for string values)
    class Status(models.TextChoices):
        """Publication status choices."""
        DRAFT = 'draft', _('Draft')
        REVIEW = 'review', _('Under Review')
        PUBLISHED = 'published', _('Published')
        ARCHIVED = 'archived', _('Archived')
    
    # Option 2: IntegerChoices (for integer values)
    class Priority(models.IntegerChoices):
        """Priority levels."""
        LOW = 1, _('Low Priority')
        MEDIUM = 2, _('Medium Priority')
        HIGH = 3, _('High Priority')
        URGENT = 4, _('Urgent')
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name=_("Publication Status")
    )
    
    priority = models.IntegerField(
        choices=Priority.choices,
        default=Priority.MEDIUM,
        verbose_name=_("Priority")
    )
    
    class Meta:
        verbose_name = _("Article")
        verbose_name_plural = _("Articles")
    
    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
```

**How to use choices:**

```python
# In templates - automatically translated
{{ article.get_status_display }}  # Returns "Draft", "Borrador" (Spanish), etc.

# In Python - get the value vs display
article.status  # Returns 'draft' (the value)
article.get_status_display()  # Returns translated label

# Access choices
Article.Status.DRAFT  # Returns 'draft'
Article.Status.choices  # Returns [('draft', 'Draft'), ...]
Article.Status.values  # Returns ['draft', 'review', ...]
Article.Status.labels  # Returns ['Draft', 'Under Review', ...]
```

### Translating Dynamic Model Methods

Sometimes you need to return translated text from model methods:

```python
from django.utils.translation import pgettext, ngettext

class Article(models.Model):
    # ... fields ...
    
    def get_status_badge(self):
        """
        Return translated status label with context.
        
        Using pgettext allows translators to provide context-specific translations.
        Example: "Submit" can mean different things as a button label vs. status.
        """
        status_labels = {
            self.Status.DRAFT: pgettext('article status', 'Draft'),
            self.Status.REVIEW: pgettext('article status', 'In Review'),
            self.Status.PUBLISHED: pgettext('article status', 'Published'),
            self.Status.ARCHIVED: pgettext('article status', 'Archived'),
        }
        return status_labels.get(self.status, self.status)
    
    def get_age_display(self):
        """
        Display article age with proper pluralization.
        
        ngettext handles singular/plural forms in different languages.
        """
        from datetime import timedelta
        
        age = timezone.now() - self.created_at
        days = age.days
        
        # ngettext(singular, plural, count)
        return ngettext(
            '%(days)d day old',
            '%(days)d days old',
            days
        ) % {'days': days}
    
    def is_recent(self):
        """Check if article was created within the last week."""
        cutoff = timezone.now() - timedelta(days=7)
        return self.created_at >= cutoff
```

---

## Views and Error Messages {#views-and-error-messages}

### Function-Based Views

```python
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils.translation import gettext as _  # Use eager gettext in views
from django.views.decorators.http import require_http_methods

@require_http_methods(["GET", "POST"])
def article_detail(request, slug):
    """Display article detail page."""
    article = get_object_or_404(Article, slug=slug)
    
    try:
        # Increment views (atomic operation)
        from django.db.models import F
        Article.objects.filter(pk=article.pk).update(
            views_count=F('views_count') + 1
        )
        article.refresh_from_db()
        
    except Exception as e:
        # Log error but don't fail
        messages.warning(
            request,
            _('Could not update view count.')
        )
    
    return render(request, 'articles/detail.html', {
        'article': article,
        'page_title': _('Article Details'),
    })


def publish_article(request, pk):
    """
    Handle article publication with comprehensive error handling.
    
    Demonstrates translating error messages in try/except blocks.
    """
    article = get_object_or_404(Article, pk=pk)
    
    try:
        # Permission check
        if article.author != request.user:
            raise PermissionError(
                _('You do not have permission to publish this article.')
            )
        
        # Validation
        if article.status != Article.Status.DRAFT:
            raise ValueError(
                _('Only draft articles can be published.')
            )
        
        if not article.content.strip():
            raise ValueError(
                _('Article content cannot be empty.')
            )
        
        # Perform action
        article.status = Article.Status.PUBLISHED
        article.published_at = timezone.now()
        article.save()
        
        # Success message with context
        messages.success(
            request,
            _('Article "%(title)s" published successfully!') % {
                'title': article.title
            }
        )
        
    except PermissionError as e:
        messages.error(request, str(e))
        return redirect('login')
    
    except ValueError as e:
        messages.error(request, str(e))
    
    except Exception as e:
        # Generic error handling
        messages.error(
            request,
            _('An unexpected error occurred: %(error)s') % {
                'error': str(e)
            }
        )
    
    return redirect('article-detail', slug=article.slug)
```

### Class-Based Views

```python
from django.views.generic import CreateView, UpdateView, DeleteView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages

class ArticleCreateView(LoginRequiredMixin, CreateView):
    """Create a new article."""
    model = Article
    fields = ['title', 'content', 'summary']
    template_name = 'articles/form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Create Article')
        return context
    
    def form_valid(self, form):
        """Handle valid form submission."""
        form.instance.author = self.request.user
        response = super().form_valid(form)
        
        # Use eager gettext for user messages
        messages.success(
            self.request,
            _('Article "%(title)s" created successfully!') % {
                'title': form.instance.title
            }
        )
        return response
    
    def form_invalid(self, form):
        """Handle invalid form submission."""
        messages.error(
            self.request,
            _('Please correct the errors below.')
        )
        return super().form_invalid(form)


class ArticleDeleteView(LoginRequiredMixin, DeleteView):
    """Delete an article."""
    model = Article
    template_name = 'articles/confirm_delete.html'
    success_url = '/articles/'
    
    def delete(self, request, *args, **kwargs):
        """Delete the article and show message."""
        article = self.get_object()
        title = article.title
        response = super().delete(request, *args, **kwargs)
        
        messages.success(
            request,
            _('Article "%(title)s" deleted successfully.') % {
                'title': title
            }
        )
        return response
```

### Service Classes for Complex Logic

```python
from django.core.exceptions import ValidationError

class ArticleService:
    """
    Business logic service with translated error messages.
    
    Keeps translation concerns in one place, making it easy to update messages.
    """
    
    @staticmethod
    def validate_title(title):
        """Validate article title."""
        if not title or len(title) < 5:
            raise ValidationError(
                _('Title must be at least 5 characters long.')
            )
        
        if len(title) > 200:
            raise ValidationError(
                _('Title cannot exceed 200 characters.')
            )
    
    @staticmethod
    def validate_content(content):
        """Validate article content."""
        word_count = len(content.split())
        
        if word_count < 50:
            raise ValidationError(
                ngettext(
                    'Content must be at least 50 words. You have %(count)d.',
                    'Content must be at least 50 words. You have %(count)d.',
                    word_count
                ) % {'count': word_count}
            )
    
    @staticmethod
    def publish(article):
        """
        Publish an article with validation.
        
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            if article.status != Article.Status.DRAFT:
                raise ValidationError(
                    _('Only draft articles can be published.')
                )
            
            ArticleService.validate_content(article.content)
            
            article.status = Article.Status.PUBLISHED
            article.published_at = timezone.now()
            article.save()
            
            return True, _('Article published successfully.')
        
        except ValidationError as e:
            return False, str(e.message)
        except Exception as e:
            return False, _('Unexpected error: %(error)s') % {'error': str(e)}
    
    @staticmethod
    def archive(article):
        """Archive an article."""
        try:
            article.status = Article.Status.ARCHIVED
            article.save()
            return True, _('Article archived successfully.')
        except Exception as e:
            return False, _('Error archiving article: %(error)s') % {'error': str(e)}
```

---

## Forms and Validation {#forms-and-validation}

### Model Forms

```python
from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext
from django.core.exceptions import ValidationError

class ArticleForm(forms.ModelForm):
    """Form for creating/editing articles."""
    
    # Override fields to add translation
    title = forms.CharField(
        label=_('Article Title'),
        max_length=200,
        widget=forms.TextInput(attrs={
            'placeholder': _('Enter your article title'),
            'class': 'form-control',
        }),
        help_text=_('Keep it concise and descriptive'),
        error_messages={
            'required': _('Title is required.'),
            'max_length': _('Title is too long (max 200 characters).'),
        }
    )
    
    content = forms.CharField(
        label=_('Content'),
        widget=forms.Textarea(attrs={
            'placeholder': _('Write your article here...'),
            'class': 'form-control',
            'rows': 10,
        }),
        help_text=_('Markdown is supported'),
        error_messages={
            'required': _('Content is required.'),
        }
    )
    
    summary = forms.CharField(
        label=_('Summary'),
        required=False,
        widget=forms.Textarea(attrs={
            'placeholder': _('Brief overview of the article'),
            'class': 'form-control',
            'rows': 3,
        }),
        help_text=_('Optional. Used in listings.')
    )
    
    class Meta:
        model = Article
        fields = ['title', 'content', 'summary', 'status']
        labels = {
            'status': _('Publication Status'),
        }
    
    def clean_title(self):
        """Field-level validation for title."""
        title = self.cleaned_data.get('title', '').strip()
        
        if len(title) < 5:
            raise ValidationError(
                _('Title must be at least 5 characters long.')
            )
        
        # Check for duplicates (if editing, exclude current)
        queryset = Article.objects.filter(title=title)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise ValidationError(
                _('An article with this title already exists.')
            )
        
        return title
    
    def clean_content(self):
        """Field-level validation for content with pluralization."""
        content = self.cleaned_data.get('content', '').strip()
        word_count = len(content.split())
        
        if word_count < 50:
            raise ValidationError(
                ngettext(
                    'Content must be at least 50 words. You have %(count)d word.',
                    'Content must be at least 50 words. You have %(count)d words.',
                    word_count
                ) % {'count': word_count}
            )
        
        return content
    
    def clean(self):
        """Cross-field validation."""
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        summary = cleaned_data.get('summary')
        
        # Require summary for published articles
        if status == Article.Status.PUBLISHED and not summary:
            raise ValidationError(
                _('Published articles must include a summary.')
            )
        
        return cleaned_data
```

### Custom Validators

```python
def validate_no_profanity(value):
    """
    Custom validator to check for inappropriate language.
    Can be reused across multiple fields.
    """
    banned_words = ['badword1', 'badword2', 'inappropriate']
    
    if any(word.lower() in value.lower() for word in banned_words):
        raise ValidationError(
            _('Your content contains inappropriate language.')
        )


def validate_minimum_words(min_words):
    """
    Factory function for creating word count validators.
    
    Usage: validators=[validate_minimum_words(100)]
    """
    def validator(value):
        word_count = len(value.split())
        if word_count < min_words:
            raise ValidationError(
                ngettext(
                    'Content must be at least %(min)d word.',
                    'Content must be at least %(min)d words.',
                    min_words
                ) % {'min': min_words}
            )
    return validator


class ArticleForm(forms.ModelForm):
    """Form with custom validators."""
    
    content = forms.CharField(
        validators=[
            validate_no_profanity,
            validate_minimum_words(50),
        ],
        error_messages={
            'required': _('Content is required.'),
        }
    )
    
    class Meta:
        model = Article
        fields = ['title', 'content']
```

---

## Templates {#templates}

### Basic Translation Tags

```django
{% load i18n %}

<!-- Simple string translation -->
<h1>{% trans "Welcome to Our Blog" %}</h1>

<!-- With lazy loading (recommended) -->
{% trans "Welcome to Our Blog" as page_title %}
<h1>{{ page_title }}</h1>

<!-- With variables -->
<p>{% blocktrans %}Hello {{ username }}, welcome back!{% endblocktrans %}</p>

<!-- With multiple variables and block -->
{% blocktrans with author_name=article.author.get_full_name %}
  This article was written by {{ author_name }}
{% endblocktrans %}

<!-- Pluralization -->
{% blocktrans count counter=articles|length %}
  There is {{ counter }} article.
{% plural %}
  There are {{ counter }} articles.
{% endblocktrans %}

<!-- Context-aware translation -->
<button>{% pgettext "button label" "Submit" %}</button>

<!-- Model choice display (automatically translated) -->
<span class="badge">{{ article.get_status_display }}</span>

<!-- Localized date/time -->
<p>Published: {{ article.published_at|date:"SHORT_DATE_FORMAT" }}</p>

<!-- Localized number -->
<p>Views: {{ article.views_count|localize }}</p>
```

### Common Template Patterns

```django
{% load i18n %}

<!-- Conditional with translations -->
<div class="status-section">
  {% if article.status == article.Status.DRAFT %}
    <span class="badge badge-warning">{% trans "Draft" %}</span>
  {% elif article.status == article.Status.PUBLISHED %}
    <span class="badge badge-success">{% trans "Published" %}</span>
  {% elif article.status == article.Status.ARCHIVED %}
    <span class="badge badge-secondary">{% trans "Archived" %}</span>
  {% endif %}
</div>

<!-- Display form errors -->
{% if form.errors %}
  <div class="alert alert-danger" role="alert">
    <h4 class="alert-heading">{% trans "Please correct the following errors:" %}</h4>
    <ul>
      {% for field, errors in form.errors.items %}
        <li>
          <strong>{{ form|lookup:field|label }}:</strong>
          {% for error in errors %}
            <div>{{ error }}</div>
          {% endfor %}
        </li>
      {% endfor %}
    </ul>
  </div>
{% endif %}

<!-- Messages -->
{% if messages %}
  <div class="messages">
    {% for message in messages %}
      <div class="alert alert-{{ message.tags }}">
        {{ message }}
      </div>
    {% endfor %}
  </div>
{% endif %}

<!-- Language selector -->
<form action="{% url 'set_language' %}" method="post">
  {% csrf_token %}
  <select name="language" onchange="this.form.submit()">
    {% get_available_languages as languages %}
    {% for code, name in languages %}
      <option value="{{ code }}" {% if code == LANGUAGE_CODE %}selected{% endif %}>
        {{ name }}
      </option>
    {% endfor %}
  </select>
</form>

<!-- Date formatting respects locale -->
<p>{% trans "Article published:" %} {{ article.published_at|date:"DATE_FORMAT" }}</p>

<!-- Complex block translation -->
{% blocktrans with views=article.views_count %}
  This article has been viewed {{ views }} times.
{% endblocktrans %}
```

### Language Switcher Dropdown

```django
{% load i18n %}

<div class="language-switcher">
  <form method="post" action="{% url 'set_language' %}">
    {% csrf_token %}
    <select name="language" onchange="this.form.submit()" class="form-control">
      {% get_available_languages as available_languages %}
      {% for code, name in available_languages %}
        <option value="{{ code }}" {% if code == LANGUAGE_CODE %}selected{% endif %}>
          {{ name }}
        </option>
      {% endfor %}
    </select>
  </form>
</div>
```

---

## Management Commands {#management-commands}

### Custom Commands with Translation

```python
# apps/articles/management/commands/publish_scheduled.py

from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _
from django.utils import timezone
from articles.models import Article

class Command(BaseCommand):
    """
    Custom management command that publishes scheduled articles.
    
    Usage:
        python manage.py publish_scheduled
        python manage.py publish_scheduled --dry-run
    """
    
    help = _('Publish articles scheduled for publication')
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help=_('Show what would be published without making changes')
        )
        
        parser.add_argument(
            '--language',
            type=str,
            default='en',
            help=_('Language for output messages')
        )
    
    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        language = options.get('language', 'en')
        
        # Set language for output
        from django.utils.translation import activate
        activate(language)
        
        try:
            # Find articles ready to publish
            articles = Article.objects.filter(
                status=Article.Status.DRAFT,
                published_at__lte=timezone.now()
            )
            
            if not articles.exists():
                self.stdout.write(
                    self.style.WARNING(
                        _('No articles found to publish.')
                    )
                )
                return
            
            # Process each article
            published_count = 0
            for article in articles:
                if not dry_run:
                    article.status = Article.Status.PUBLISHED
                    article.save()
                    published_count += 1
                
                self.stdout.write(
                    self.style.SUCCESS(
                        _('Published: %(title)s') % {'title': article.title}
                    )
                )
            
            # Summary message
            if dry_run:
                self.stdout.write(
                    self.style.HTTP_INFO(
                        _('[DRY RUN] Would have published %(count)d article(s).') % {
                            'count': articles.count()
                        }
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        _('Successfully published %(count)d article(s).') % {
                            'count': published_count
                        }
                    )
                )
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    _('Error: %(error)s') % {'error': str(e)}
                )
            )
            raise
```

### Django Translation Management Commands

```bash
# Extract translatable strings from all files
python manage.py makemessages -a

# Extract for specific languages
python manage.py makemessages -l es -l fr -l de

# Extract from JavaScript files too
python manage.py makemessages -a -d djangojs

# Compile .po files to .mo (binary format)
python manage.py compilemessages

# Verify translations (check for untranslated strings)
python manage.py makemessages --check-changes

# Verbose output to see what's being extracted
python manage.py makemessages -a --verbosity 2

# Create initial .pot template
python manage.py makemessages -a --no-wrap
```

---

## Celery Tasks and Async Work {#celery-tasks}

### Basic Translated Tasks

```python
# apps/articles/tasks.py

from celery import shared_task
from django.utils.translation import gettext as _
from django.utils.translation import activate, get_language
from django.core.mail import send_mail
from django.conf import settings
from articles.models import Article

@shared_task
def send_publication_notification(article_id, user_id, language='en'):
    """
    Send notification email when article is published.
    
    Language context is lost in async tasks, so we must explicitly set it.
    """
    from django.contrib.auth.models import User
    
    try:
        # Activate the user's preferred language
        activate(language)
        
        # Fetch objects
        article = Article.objects.get(id=article_id)
        user = User.objects.get(id=user_id)
        
        # Compose translated message
        subject = _('Article Published: %(title)s') % {
            'title': article.title
        }
        
        message = _(
            'Your article "%(title)s" has been published and is now live!'
        ) % {'title': article.title}
        
        # Send email
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        
        return _('Notification sent to %(email)s') % {'email': user.email}
    
    except Article.DoesNotExist:
        return _('Article not found')
    except User.DoesNotExist:
        return _('User not found')
    except Exception as e:
        return _('Error: %(error)s') % {'error': str(e)}


@shared_task(bind=True)
def process_article_batch(self, article_ids, language_code='en'):
    """
    Process multiple articles with progress tracking.
    
    `bind=True` gives us access to `self` for updating progress.
    """
    activate(language_code)
    
    results = []
    total = len(article_ids)
    
    for idx, article_id in enumerate(article_ids, 1):
        try:
            article = Article.objects.get(id=article_id)
            
            # Do work (example: generate summary)
            # article.generate_summary()
            # article.save()
            
            result = _('Processed %(idx)d/%(total)d: %(title)s') % {
                'idx': idx,
                'total': total,
                'title': article.title
            }
            results.append(result)
            
            # Update task progress
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': idx,
                    'total': total,
                    'status': result
                }
            )
        
        except Article.DoesNotExist:
            results.append(
                _('Article %(id)d not found') % {'id': article_id}
            )
        except Exception as e:
            results.append(
                _('Error processing %(idx)d: %(error)s') % {
                    'idx': idx,
                    'error': str(e)
                }
            )
    
    return {
        'status': _('Batch processing complete'),
        'results': results
    }
```

### Scheduling Tasks with Language Context

```python
# views.py - triggering task with language info

from celery import current_app
from articles.tasks import send_publication_notification

def publish_article(request, pk):
    """Publish article and queue notification task."""
    article = get_object_or_404(Article, pk=pk)
    
    # Get current language
    current_language = get_language()
    
    # Update article
    article.status = Article.Status.PUBLISHED
    article.published_at = timezone.now()
    article.save()
    
    # Queue task with language context
    send_publication_notification.delay(
        article_id=article.id,
        user_id=article.author.id,
        language=current_language  # Pass language to task
    )
    
    messages.success(request, _('Article published!'))
    return redirect('article-detail', pk=pk)
```

---

## Best Practices {#best-practices}

### 1. Consistency in Usage

```python
# ✅ GOOD: Consistent use of lazy translation at module level
from django.utils.translation import gettext_lazy as _

class Article(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name=_("Title")
    )

# ❌ BAD: Mixing eager and lazy
class Article(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name=gettext("Title")  # Wrong! Translates at import time
    )
```

### 2. Always Translate Choice Labels

```python
# ✅ GOOD: Choice labels are translatable
class Status(models.TextChoices):
    DRAFT = 'draft', _('Draft')
    PUBLISHED = 'published', _('Published')

# ❌ BAD: Hard-coded choice labels
STATUS_CHOICES = [
    ('draft', 'Draft'),  # Won't be translated!
    ('published', 'Published'),
]
```

### 3. Provide Context When Ambiguous

```python
# ✅ GOOD: Using pgettext to disambiguate
submit_button = pgettext('button label', 'Submit')
submitted_status = pgettext('status', 'Submitted')

# ❌ BAD: Same word, but translators don't know context
submit = _('Submit')  # Is this a button? Status? Action?
```

### 4. Use Format Strings for Variables

```python
# ✅ GOOD: Format strings allow word reordering in translations
message = _('Article "%(title)s" by %(author)s') % {
    'title': article.title,
    'author': article.author.name
}

# ❌ BAD: F-strings break translations (concatenation)
message = f'Article "{article.title}" by {article.author.name}'

# ❌ BAD: String concatenation loses context
message = _('Article "') + article.title + _('") by ') + article.author.name
```

### 5. Pluralization When Needed

```python
# ✅ GOOD: Handle singular/plural forms
count = 5
message = ngettext(
    '%(count)d item in cart',
    '%(count)d items in cart',
    count
) % {'count': count}

# ❌ BAD: Force plural (wrong in singular languages)
message = _('%(count)d items in cart') % {'count': 1}  # "1 items"
```

### 6. Handle Language Context in Async Tasks

```python
# ✅ GOOD: Explicitly set language in tasks
@shared_task
def send_email(user_id, language='en'):
    from django.utils.translation import activate
    activate(language)
    
    user = User.objects.get(id=user_id)
    subject = _('Welcome!')  # Translated in user's language
    send_mail(subject, ...)

# ❌ BAD: Assume language context exists in task
@shared_task
def send_email(user_id):
    user = User.objects.get(id=user_id)
    subject = _('Welcome!')  # Unknown language!
```

### 7. Testing Translations

```python
# tests/test_translations.py

from django.test import TestCase
from django.utils.translation import activate, override, gettext as _
from django.conf import settings
from articles.models import Article

class TranslationTestCase(TestCase):
    """Test translation functionality."""
    
    def setUp(self):
        self.article = Article.objects.create(
            title='Test Article',
            content='Test content' * 20
        )
    
    def test_verbose_names_are_translatable(self):
        """Verify model verbose names are translatable."""
        with override('es'):
            verbose_name = str(Article._meta.verbose_name)
            # Should be translated to Spanish
            self.assertIsInstance(verbose_name, str)
    
    def test_choice_labels_are_translated(self):
        """Verify choice labels are translated."""
        self.article.status = Article.Status.DRAFT
        
        with override('es'):
            display = self.article.get_status_display()
            # Should show Spanish translation
            self.assertNotEqual(display, 'Draft')
    
    def test_all_languages_have_translations(self):
        """Verify all configured languages work."""
        for code, name in settings.LANGUAGES:
            with override(code):
                translated = str(_('Welcome'))
                self.assertIsInstance(translated, str)
```

### 8. Error Message Formatting

```python
# ✅ GOOD: Translatable error messages with context
try:
    validate_article(article)
except ValidationError as e:
    messages.error(
        request,
        _('Validation failed: %(reason)s') % {'reason': str(e.message)}
    )

# ❌ BAD: Error text concatenated at runtime
try:
    validate_article(article)
except ValidationError as e:
    messages.error(request, 'Error: ' + str(e))  # 'Error' not translatable
```

---

## Quick Reference {#quick-reference}

### When to Use What

| Situation | Function | Example |
|-----------|----------|---------|
| Model field `verbose_name` | `gettext_lazy as _` | `verbose_name=_("Title")` |
| Model field `help_text` | `gettext_lazy as _` | `help_text=_("Brief description")` |
| Choice labels | `gettext_lazy as _` in TextChoices | `DRAFT = 'draft', _('Draft')` |
| Form field `label` | `gettext_lazy as _` | `label=_("Email Address")` |
| Form field `help_text` | `gettext_lazy as _` | `help_text=_("We'll never share")` |
| Settings/config | `gettext_lazy as _` | `LANGUAGES = [('en', _('English'))]` |
| View messages | `gettext as _` | `messages.success(r, _('Saved!'))` |
| Exception messages | `gettext as _` | `raise ValueError(_('Invalid'))` |
| Form validation | `gettext as _` | `raise ValidationError(_('Error'))` |
| Pluralization | `ngettext` / `ngettext_lazy` | `ngettext('%d item', '%d items', count)` |
| Context translation | `pgettext` / `pgettext_lazy` | `pgettext('button', 'Submit')` |
| Templates | `{% trans %}` / `{% blocktrans %}` | `{% trans "Welcome" %}` |
| Celery tasks | `gettext as _` + `activate()` | `activate(lang); msg = _('...')` |
| Management commands | `gettext as _` + `activate()` | `activate(lang); self.stdout.write(_('...'))` |

### Key Import Patterns

```python
# Models, forms, settings (module-level)
from django.utils.translation import gettext_lazy as _

# Views, functions, commands (runtime)
from django.utils.translation import gettext as _

# Both when you need both
from django.utils.translation import gettext_lazy, gettext

# Pluralization
from django.utils.translation import ngettext, ngettext_lazy

# Context
from django.utils.translation import pgettext, pgettext_lazy

# Language control
from django.utils.translation import activate, override, get_language
```

### Common Patterns

```python
# Format with variables (NOT f-strings!)
_('Welcome %(name)s') % {'name': user.name}

# Pluralization
ngettext('%d item', '%d items', count) % count

# With variables and plural
ngettext(
    'You have %(count)d message',
    'You have %(count)d messages',
    count
) % {'count': count}

# Context-aware
pgettext('button label', 'Submit')

# In templates
{% trans "Welcome" %}
{% blocktrans with name=user.name %}Hello {{ name }}{% endblocktrans %}
{% blocktrans count counter=items|length %}1 item{% plural %}{{ counter }} items{% endblocktrans %}
```

---

## Reusable Components {#reusable-components}

### Abstract Base Models

```python
# core/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class TranslatableModel(models.Model):
    """
    Abstract base model with translatable timestamp fields.
    
    Usage:
        class Article(TranslatableModel):
            title = models.CharField(max_length=200)
    """
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created at")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated at")
    )
    
    class Meta:
        abstract = True
        ordering = ['-created_at']


class PublishableModel(TranslatableModel):
    """
    Abstract base for publishable content.
    
    Usage:
        class Article(PublishableModel):
            title = models.CharField(max_length=200)
    """
    
    class Status(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        PUBLISHED = 'published', _('Published')
        ARCHIVED = 'archived', _('Archived')
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name=_("Status")
    )
    
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Published at")
    )
    
    class Meta:
        abstract = True
    
    def publish(self):
        """Publish this item."""
        if self.status == self.Status.DRAFT:
            self.status = self.Status.PUBLISHED
            self.published_at = timezone.now()
            self.save()
            return True, _('Published successfully.')
        return False, _('Only draft items can be published.')


class SoftDeleteModel(models.Model):
    """
    Abstract base for soft-delete functionality.
    
    Usage:
        class Article(SoftDeleteModel):
            title = models.CharField(max_length=200)
    """
    
    is_deleted = models.BooleanField(
        default=False,
        verbose_name=_("Deleted")
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Deleted at")
    )
    
    class Meta:
        abstract = True
    
    def soft_delete(self):
        """Mark as deleted."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
        return True, _('Item deleted successfully.')
```

### Translation Helper Utilities

```python
# utils/translation.py

from django.utils.translation import gettext as _
from django.utils.translation import activate, override, get_language
from django.conf import settings
from functools import wraps

def translate_in_language(language_code):
    """
    Decorator to execute function in specific language.
    
    Usage:
        @translate_in_language('es')
        def get_spanish_message():
            return str(_('Welcome'))
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_language = get_language()
            try:
                activate(language_code)
                return func(*args, **kwargs)
            finally:
                activate(current_language)
        return wrapper
    return decorator


class TranslationHelper:
    """Utility methods for common translation tasks."""
    
    @staticmethod
    def get_choice_display(model, field_name, value, language='en'):
        """
        Get translated display value for a choice field.
        
        Usage:
            display = TranslationHelper.get_choice_display(
                Article, 'status', 'published', 'es'
            )
        """
        with override(language):
            field = model._meta.get_field(field_name)
            for choice_value, choice_label in field.choices:
                if choice_value == value:
                    return str(choice_label)
            return str(value)
    
    @staticmethod
    def get_all_languages_display(text):
        """
        Get text translated in all configured languages.
        
        Usage:
            translations = TranslationHelper.get_all_languages_display(
                _('Welcome')
            )
            # Returns {'en': 'Welcome', 'es': 'Bienvenido', ...}
        """
        translations = {}
        for code, name in settings.LANGUAGES:
            with override(code):
                translations[code] = str(text)
        return translations
```

### Reusable Form Mixins

```python
# forms/mixins.py

from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

class TranslatableFormMixin:
    """
    Mixin to add common translated error messages to forms.
    
    Usage:
        class ArticleForm(TranslatableFormMixin, forms.ModelForm):
            class Meta:
                model = Article
                fields = ['title']
    """
    
    # Override in subclass to customize
    default_error_messages = {
        'required': _('This field is required.'),
        'invalid': _('Enter a valid value.'),
        'max_length': _('Ensure this value has at most %(limit_value)d characters.'),
        'min_length': _('Ensure this value has at least %(limit_value)d characters.'),
    }
    
    def __init__(self, *args, **kwargs):
        """Apply translated error messages to all fields."""
        super().__init__(*args, **kwargs)
        
        for field in self.fields.values():
            if not hasattr(field, 'error_messages'):
                continue
            
            # Merge translated messages with field-specific ones
            field_messages = field.error_messages.copy()
            field_messages.update(self.default_error_messages)
            field.error_messages = field_messages


class ValidatedModelFormMixin:
    """
    Mixin for model forms with enhanced validation.
    
    Ensures clean() and full_clean() properly handle ValidationError.
    
    Usage:
        class ArticleForm(ValidatedModelFormMixin, forms.ModelForm):
            class Meta:
                model = Article
                fields = ['title', 'content']
    """
    
    def full_clean(self):
        """
        Override to catch and format validation errors.
        """
        try:
            super().full_clean()
        except ValidationError as e:
            # Ensure error messages are translatable
            self.add_error(None, _('Please correct the errors below.'))
```

---

## Translation Workflow

### Step-by-Step Process

1. **Write translatable code** (already done by following this guide)

2. **Extract translatable strings**
   ```bash
   python manage.py makemessages -a
   ```
   Creates/updates `locale/[language]/LC_MESSAGES/django.po` files

3. **Review and translate .po files**
   - Use Poedit (desktop), Weblate (web), or any text editor
   - Each `msgid` (original) gets a `msgstr` (translation)

4. **Compile translations**
   ```bash
   python manage.py compilemessages
   ```
   Creates `.mo` files used by Django at runtime

5. **Test in different languages**
   ```bash
   LANGUAGE_CODE=es python manage.py runserver
   ```

6. **Deploy**
   - Include compiled `.mo` files in deployment
   - Set `LANGUAGE_CODE` based on user preference

### .po File Example

```
# locale/es/LC_MESSAGES/django.po

#: apps/articles/models.py:25
msgid "Article"
msgstr "Artículo"

#: apps/articles/models.py:30
msgid "Title"
msgstr "Título"

#: apps/articles/models.py:32
msgid "Content"
msgstr "Contenido"

#: apps/articles/models.py:45
msgid "Status"
msgstr "Estado"

#: apps/articles/models.py:Status
msgid "Draft"
msgstr "Borrador"

msgid "Published"
msgstr "Publicado"
```

---

## Common Mistakes and Solutions

| Mistake | Problem | Solution |
|---------|---------|----------|
| Using `gettext()` in models | Translates at import time, before Django is ready | Use `gettext_lazy()` |
| Not translating choice labels | Choice options show in English only | Wrap with `_()` in TextChoices |
| Forgetting about exception messages | Error messages aren't translatable | Always use `_()` in exceptions |
| String concatenation | Breaks translation context | Use format strings: `_("Text %(var)s") % {'var': value}` |
| No language context in tasks | Task output in default language | Call `activate(language)` in task |
| Missing parentheses in translate | Import doesn't work | `gettext_lazy as _` not `gettext_lazy _` |
| Using f-strings | Variables can't be reordered for translation | Use: `_("%(name)s") % {'name': value}` |
| Pluralization hardcoded | Wrong in non-English languages | Use `ngettext()` |

---

## Resources

- [Django i18n Documentation](https://docs.djangoproject.com/en/stable/topics/i18n/)
- [gettext_lazy vs gettext](https://docs.djangoproject.com/en/stable/topics/i18n/translation/#lazy-translations)
- [Translation Framework Reference](https://docs.djangoproject.com/en/stable/ref/utils/#module-django.utils.translation)
- [Translators Guide](https://docs.djangoproject.com/en/stable/topics/i18n/translation/#localization-how-to-create-language-files)

---

## Checklist for Complete i18n Implementation

- [ ] Configure `LANGUAGE_CODE`, `LANGUAGES`, `I18N`, `LOCALE_PATHS` in settings
- [ ] Add `LocaleMiddleware` to middleware stack
- [ ] Import `gettext_lazy` in all model files
- [ ] Wrap all model field `verbose_name` and `help_text` with `_()`
- [ ] Use `TextChoices` with `_()` for all status/choice fields
- [ ] Wrap all form field labels with `_()`
- [ ] Wrap all form error messages with `_()`
- [ ] Use `gettext` in views for user messages
- [ ] Use `gettext` for exception messages
- [ ] Add translation tags to templates: `{% load i18n %}`
- [ ] Wrap template strings with `{% trans %}` or `{% blocktrans %}`
- [ ] Use `ngettext` for pluralization
- [ ] Use `pgettext` for context-aware translations
- [ ] Handle language context in Celery tasks with `activate()`
- [ ] Translate management command output
- [ ] Run `python manage.py makemessages -a` regularly
- [ ] Coordinate with translators to update `.po` files
- [ ] Run `python manage.py compilemessages` before deployment
- [ ] Test with multiple languages using Django test client
- [ ] Set up translation workflow (Weblate, Crowdin, etc.) for teams

---

## Final Tips

1. **Be consistent** - Always use the same import pattern in each file
2. **Translate early** - Add translations during development, not at the end
3. **Use context** - Provide context when the same word has multiple meanings
4. **Test regularly** - Test with multiple languages during development
5. **Plan workflow** - Decide how translators will work (Weblate, Poedit, etc.)
6. **Document strings** - Use translator comments for non-obvious strings
7. **Keep it simple** - Complex logic is harder to translate correctly

---

**Last Updated:** 2024
**Django Version:** 3.2+
