# Django i18n Translation Guide: Comprehensive Edition

Complete guide to implementing internationalization (i18n) in Django applications with extensive explanations and best practices for every topic.

---

## Table of Contents

1. [Fundamentals of Translation in Django](#fundamentals)
2. [gettext_lazy vs gettext: Understanding the Difference](#gettext-comparison)
3. [Project Configuration](#project-configuration)
4. [Models and Database](#models-and-database)
5. [Views and User-Facing Messages](#views-and-messages)
6. [Forms and User Input Validation](#forms-and-validation)
7. [Templates and Frontend](#templates)
8. [Management Commands](#management-commands)
9. [Asynchronous Tasks and Background Jobs](#async-tasks)
10. [Translation Workflow and Tools](#translation-workflow)
11. [Testing and Quality Assurance](#testing)
12. [Performance Considerations](#performance)
13. [Common Pitfalls and Solutions](#pitfalls)
14. [Enterprise Implementation](#enterprise)

---

## Fundamentals of Translation in Django {#fundamentals}

### Why Internationalization (i18n) Matters

Internationalization is the process of designing software to support multiple languages and locales. This goes beyond simple translation—it includes:

- **Language Support**: Display content in different languages
- **Locale Awareness**: Format dates, numbers, and currency according to regional preferences
- **Right-to-Left Support**: Handle languages like Arabic and Hebrew that read right-to-left
- **User Preferences**: Let users choose their preferred language
- **Context-Aware Translation**: Handle words with multiple meanings in different contexts

### How Django Handles Translations

Django uses the GNU gettext system, which is the industry standard for i18n. Here's how it works:

1. **Mark strings as translatable** in your code using `_()` or `_lazy()`
2. **Extract marked strings** into `.po` files (human-readable translation files)
3. **Translators edit .po files** with translations for each language
4. **Compile translations** into `.mo` files (binary, optimized for runtime)
5. **Django loads appropriate translations** based on the user's language preference at runtime

This separation of concerns means:
- Developers mark strings, translators translate
- No code changes needed to add new languages
- Translations can be updated independently of code releases

### The Three Types of Strings

Not all strings need translation. Django recognizes three categories:

**1. Hard-coded user-facing strings** (MUST translate)
```
"Welcome to our site"
"Please enter a valid email"
"Article published successfully"
```

**2. Technical/debug strings** (should NOT translate)
```
"DEBUG: User ID 123 loaded"
"WARNING: Cache miss on key X"
"ERROR: Database connection failed"
```

**3. Data strings** (user input, not translatable)
```
User's name: "John Smith"
Article content written by users
Comments from users
```

The challenge: Developer must distinguish between these, especially since database content (user-generated) should never be marked for translation.

---

## gettext_lazy vs gettext: Understanding the Difference {#gettext-comparison}

### Why This Matters

This is THE most critical concept in Django i18n. Getting this wrong is the #1 cause of broken translations.

### The Problem: Module-Level Code

When Python imports a module, it executes all module-level code immediately:

```python
# models.py
from django.utils.translation import gettext as _  # WRONG!

class Article(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name=_("Title")  # Translation happens NOW, at import time
    )
```

When this code runs:
1. Python imports models.py
2. It executes `_("Title")` immediately
3. At this moment, Django's translation system may not be initialized
4. The language context is undefined
5. The translation uses whatever the default language was set to

**Result**: The label is translated once and cached. If the user later switches languages, the admin will still show the original translation.

### The Solution: Lazy Translation

```python
from django.utils.translation import gettext_lazy as _  # CORRECT!

class Article(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name=_("Title")  # Translation is DEFERRED
    )
```

When `gettext_lazy()` is called, it doesn't translate immediately. Instead, it returns a "lazy" object that remembers what string needs translation. The actual translation happens later when the string is used:

1. Admin page is rendered
2. Django needs to display the field label
3. The lazy object is converted to a string
4. At this moment, Django knows the current language
5. Translation happens using the correct language
6. Result: Correct translation based on current language preference

### Side-by-Side Comparison

```python
# ❌ WRONG: Eager translation at import time
from django.utils.translation import gettext as _

class Article(models.Model):
    title = models.CharField(verbose_name=_("Title"))
    content = models.TextField(verbose_name=_("Content"))

# Result in Spanish admin: Always shows English "Title" and "Content"
```

```python
# ✅ CORRECT: Lazy translation at use time
from django.utils.translation import gettext_lazy as _

class Article(models.Model):
    title = models.CharField(verbose_name=_("Title"))
    content = models.TextField(verbose_name=_("Content"))

# Result in Spanish admin: Shows Spanish "Título" and "Contenido"
```

### When to Use Each

**Use gettext_lazy (`_lazy` or `_`) for:**
- Model field definitions (always module-level)
- Form field definitions (always module-level)
- Settings and configuration (module-level)
- Choice labels in TextChoices (module-level)
- Menu items, navigation labels (often defined at module-level)
- Any string defined once and used multiple times

**Use gettext (eager `_`) for:**
- View functions processing a request (runtime context exists)
- Exception and error messages raised in functions
- Form validation error messages (called at form time)
- Management command output (called at execution time)
- Celery task messages (called at task execution time)
- Messages in try/except blocks
- Any string that depends on request/task context

### The Memory Aid

Think of it this way:
- **Lazy**: "I don't know what language you want yet, so I'll wait to translate when you actually ask for the string"
- **Eager**: "You're asking for the translation right now, so translate immediately based on current context"

---

## Project Configuration {#project-configuration}

### Why Configuration Matters

Proper configuration is the foundation of a working i18n system. Missing or incorrect settings will cause:
- Translations to not be found
- Language switching to fail
- Incorrect date/number formatting
- Broken locale detection

### Complete settings.py Configuration

```python
# settings.py
import os
from django.utils.translation import gettext_lazy as _

# ============================================================================
# LANGUAGE AND LOCALE SETTINGS
# ============================================================================

# Default language when user hasn't chosen one
LANGUAGE_CODE = 'en-us'

# All supported languages in your application
# Format: (language_code, user-friendly_name)
LANGUAGES = [
    ('en', _('English')),
    ('es', _('Spanish')),
    ('fr', _('French')),
    ('de', _('German')),
    ('ja', _('Japanese')),
    ('pt-br', _('Portuguese (Brazil)')),
    ('zh-hans', _('Simplified Chinese')),
    ('ar', _('Arabic')),
]

# Enable internationalization system
I18N = True

# Enable translation lookups
USE_I18N = True

# Format numbers, dates, times according to user's locale
# Example: 1000 → "1,000" in English, "1.000" in German
USE_L10N = True

# Use timezone-aware datetimes
USE_TZ = True

# Default timezone for all datetimes
TIME_ZONE = 'UTC'

# ============================================================================
# LOCALE PATHS
# ============================================================================

# Where Django looks for translation files (.po and .mo files)
# Create locale/ directory in project root and in each app
LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),  # Project-wide translations
    os.path.join(BASE_DIR, 'apps', 'accounts', 'locale'),  # App-specific
    os.path.join(BASE_DIR, 'apps', 'articles', 'locale'),
]

# ============================================================================
# MIDDLEWARE CONFIGURATION
# ============================================================================

# LocaleMiddleware MUST come after SessionMiddleware
# It uses session to store user's language preference
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    # LocaleMiddleware detects and sets language for each request
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

# ============================================================================
# TEMPLATE SETTINGS
# ============================================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # Makes LANGUAGES available in all templates
                'django.template.context_processors.i18n',
            ],
        },
    },
]
```

### Why These Settings Matter

**LANGUAGE_CODE**: The fallback language if a translation isn't available. Set this to your primary development language.

**LANGUAGES**: Defines which languages your application supports. Adding a language here doesn't automatically translate your app—it just enables Django's i18n for that language.

**I18N = True**: Without this, Django ignores all translation work. Forgetting this setting means hours of debugging wondering why translations don't work.

**LocaleMiddleware**: This is what detects the user's language preference. It checks, in order:
1. Language code in URL path (if using i18n_patterns)
2. Language preference in session (if user has set it)
3. Language from Accept-Language HTTP header (browser setting)
4. Default LANGUAGE_CODE

Placement matters: It must come after SessionMiddleware because it stores language preference in the session.

**LOCALE_PATHS**: Django won't find your translation files without this. It searches these directories for `.po` and `.mo` files.

### URL Configuration for i18n

```python
# urls.py
from django.conf.urls.i18n import i18n_patterns
from django.urls import path, include
from django.conf import settings

urlpatterns = [
    # Non-translated URLs (shouldn't change with language)
    path('api/', include('api.urls')),
    path('admin/', admin.site.urls),
]

# Translated URLs - users see /en/articles/, /es/articles/, etc.
urlpatterns += i18n_patterns(
    path('articles/', include('articles.urls')),
    path('accounts/', include('accounts.urls')),
    # ... other user-facing patterns
    prefix_default_language=True,  # Include /en/ even for default language
)

# In non-i18n_patterns URLs, language detection still works
# via LocaleMiddleware, but URLs don't change
```

Why use `i18n_patterns`?

**Pros:**
- SEO-friendly: Google sees `/en/articles/` and `/es/articles/` as separate pages
- Explicit language in URL: User always knows which language they're viewing
- Consistent: URL clearly indicates language

**Cons:**
- More URLs to manage
- All URLs must be nested in i18n_patterns

Alternative (without i18n_patterns):
- Language detection only via Accept-Language header and session
- URLs stay the same regardless of language
- Simpler URL structure

Choose based on your needs.

---

## Models and Database {#models-and-database}

### Why Model Translation Matters

Models are where data structure is defined. Translatable parts of models include:

1. **Field metadata** (verbose_name, help_text) - User sees in admin, forms
2. **Choice labels** (Status, Priority fields) - Shown in dropdowns, templates
3. **Model metadata** (verbose_name, verbose_name_plural) - Shown in admin

Database content (user-generated data) is NOT translated—it's user input.

### Translatable Field Definitions

```python
from django.db import models
from django.utils.translation import gettext_lazy as _

class Article(models.Model):
    """
    Article model with complete i18n support.
    
    All user-facing metadata is translatable. Data stored in fields
    (title, content) are user-generated and not marked for translation.
    """
    
    # String fields - use blank=True, never null=True
    title = models.CharField(
        max_length=200,
        verbose_name=_("Title"),  # Label shown in admin form
        help_text=_("Enter a concise, descriptive title"),  # Admin form help
        # Database stores user's title in their original language
    )
    
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name=_("URL Slug"),
        help_text=_("Auto-generated from title, used in URLs")
    )
    
    content = models.TextField(
        verbose_name=_("Article Content"),
        help_text=_("Markdown formatting is supported")
    )
    
    # ForeignKey with translatable metadata
    author = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='articles',  # Access via user.articles.all()
        verbose_name=_("Author"),  # "Author" label shown in admin
        help_text=_("Select the article's author")
    )
    
    # DateTime fields
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
        help_text=_("Automatically set when article is created")
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Last Updated"),
        help_text=_("Automatically updated when article changes")
    )
    
    # Boolean field
    is_published = models.BooleanField(
        default=False,
        verbose_name=_("Published"),
        help_text=_("Check to make this article visible to users")
    )
    
    # DateTime field that can be null
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Published At"),
        help_text=_("When the article was published")
    )
    
    class Meta:
        # These appear in admin interface
        verbose_name = _("Article")
        verbose_name_plural = _("Articles")
        ordering = ['-created_at']  # Newest first
        
        # Optimize database queries
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['slug']),
        ]
    
    def __str__(self):
        return self.title
```

**Important Pattern Explanation:**

Notice how verbose_name and help_text are translatable, but the data stored in fields is NOT. This is correct because:

- `verbose_name=_("Title")` → Shows as "Título" in Spanish admin, but doesn't affect stored data
- The actual title text stored in database is whatever the user typed (could be in any language)
- When article is displayed, its title is shown as-is, unchanged

If a user writes an article in Spanish, the `title` field contains Spanish text. The `verbose_name` being translatable only affects the admin interface labels.

### TextChoices for Status Fields

```python
class Article(models.Model):
    """
    Article with translatable status choices.
    
    TextChoices makes choices translatable and type-safe.
    """
    
    class Status(models.TextChoices):
        """Status options for articles."""
        DRAFT = 'draft', _('Draft')
        REVIEW = 'review', _('Under Review')
        PUBLISHED = 'published', _('Published')
        ARCHIVED = 'archived', _('Archived')
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name=_("Publication Status"),
        help_text=_("Current publication state of the article")
    )
    
    class Meta:
        verbose_name = _("Article")
        verbose_name_plural = _("Articles")
```

**Why TextChoices?**

Before TextChoices (pre-Django 3.0), choices were defined as tuples:

```python
# ❌ Old way - error-prone
STATUS_CHOICES = [
    ('draft', _('Draft')),
    ('published', _('Published')),
]

status = models.CharField(choices=STATUS_CHOICES)

# Problems:
# - Magic strings: status='draft' (what if you typo 'draft'?)
# - Can't discover options with IDE autocomplete
# - Choices duplicated if used in multiple models
```

With TextChoices:

```python
# ✅ New way - safe and discoverable
class Status(models.TextChoices):
    DRAFT = 'draft', _('Draft')
    PUBLISHED = 'published', _('Published')

status = models.CharField(choices=Status.choices)

# Benefits:
# - Use Status.DRAFT instead of 'draft' (type-safe)
# - IDE autocomplete works: Status.<TAB>
# - Translatable by default
# - Defined once, reused everywhere
```

### Translating Dynamic Model Methods

Some translations need to happen at runtime based on data:

```python
from django.utils.translation import pgettext, ngettext
from datetime import timedelta
from django.utils import timezone

class Article(models.Model):
    # ... fields ...
    
    def get_status_display_with_context(self):
        """
        Return translated status with additional context.
        
        pgettext allows translators to provide context-specific translations.
        Without context, the word 'Draft' might be confusing in some languages.
        """
        status_labels = {
            self.Status.DRAFT: pgettext('article status', 'Draft'),
            self.Status.REVIEW: pgettext('article status', 'Under Review'),
            self.Status.PUBLISHED: pgettext('article status', 'Published'),
            self.Status.ARCHIVED: pgettext('article status', 'Archived'),
        }
        return status_labels.get(self.status, self.status)
    
    def get_age_display(self):
        """
        Display article age with proper pluralization.
        
        ngettext handles singular/plural forms, which vary by language.
        In English: "1 day old" vs "2 days old"
        In Polish: 1 day, 2-4 days, 5+ days use different forms
        In Russian: similar complexity
        
        ngettext automatically selects correct form based on count.
        """
        age = timezone.now() - self.created_at
        days = age.days
        
        return ngettext(
            '%(days)d day old',
            '%(days)d days old',
            days
        ) % {'days': days}
    
    def get_age_description(self):
        """
        Human-readable age description with smart pluralization.
        """
        age = timezone.now() - self.created_at
        
        if age.days == 0:
            return _('Published today')
        elif age.days == 1:
            return _('Published yesterday')
        elif age.days < 7:
            return ngettext(
                'Published %(days)d day ago',
                'Published %(days)d days ago',
                age.days
            ) % {'days': age.days}
        else:
            weeks = age.days // 7
            return ngettext(
                'Published %(weeks)d week ago',
                'Published %(weeks)d weeks ago',
                weeks
            ) % {'weeks': weeks}
    
    def is_recent(self):
        """Check if article was created within the last week."""
        cutoff = timezone.now() - timedelta(days=7)
        return self.created_at >= cutoff
```

**Understanding ngettext:**

Different languages handle plurals differently:

- **English**: Singular (1) vs. Plural (0, 2+)
  - "1 item" vs "0 items", "2 items"
- **Polish**: 1, 2-4, 5+ have different forms
  - "1 artykuł", "2 artykuły", "5 artykułów"
- **Russian**: Similar complexity to Polish
- **Chinese**: No plural forms, same form for all counts

`ngettext(singular, plural, count)` automatically:
1. Counts the items
2. Looks up language rules
3. Selects correct form
4. Translates to user's language

---

## Views and User-Facing Messages {#views-and-messages}

### Why View Translation is Different

Views run at request time, when language context is known. Unlike models (evaluated at import time), views can use eager translation because:

1. Request has just arrived
2. Django knows which language user requested
3. LocaleMiddleware has set the language
4. Translation will be correct immediately

### Function-Based Views with Error Handling

```python
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods
from django.db.models import F

@require_http_methods(["GET", "POST"])
def article_detail(request, slug):
    """
    Display article details and track views.
    
    Demonstrates proper error handling with translatable messages.
    """
    # Get article or show 404 (Django handles i18n automatically)
    article = get_object_or_404(Article, slug=slug)
    
    try:
        # Increment views atomically (prevents race conditions)
        # F() expression updates in database, not in Python
        Article.objects.filter(pk=article.pk).update(
            views_count=F('views_count') + 1
        )
        # Refresh from DB to get updated value
        article.refresh_from_db()
        
    except Exception as e:
        # Log error but don't fail view - graceful degradation
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to increment view count: {e}")
        
        # Show translated warning (but don't prevent page load)
        messages.warning(
            request,
            _('Could not update view count.')
        )
    
    return render(request, 'articles/detail.html', {
        'article': article,
        'page_title': _('Article Details'),
    })


def publish_article_view(request, pk):
    """
    Publish an article with comprehensive error handling.
    
    Shows best practices for:
    - Permission checks with translated errors
    - Validation with translated errors
    - Success messages with context
    - Different error types with appropriate responses
    """
    article = get_object_or_404(Article, pk=pk)
    
    try:
        # PERMISSION CHECK
        if article.author != request.user:
            # Don't reveal whether article exists
            raise PermissionError(
                _('You do not have permission to publish this article.')
            )
        
        # VALIDATION CHECKS
        if article.status != Article.Status.DRAFT:
            raise ValueError(
                _('Only draft articles can be published. '
                  'This article is %(status)s.') % {
                    'status': article.get_status_display()
                }
            )
        
        if not article.content.strip():
            raise ValueError(
                _('Article content cannot be empty.')
            )
        
        if not article.title.strip():
            raise ValueError(
                _('Article must have a title.')
            )
        
        # PERFORM ACTION
        article.status = Article.Status.PUBLISHED
        article.published_at = timezone.now()
        article.save()
        
        # SUCCESS MESSAGE
        messages.success(
            request,
            _('Article "%(title)s" published successfully!') % {
                'title': article.title
            }
        )
        
        return redirect('article-detail', slug=article.slug)
        
    except PermissionError as e:
        # Authorization failure - redirect to login
        messages.error(request, str(e))
        return redirect('login')
    
    except ValueError as e:
        # Validation failure - stay on page with error
        messages.error(request, str(e))
        return redirect('article-edit', pk=pk)
    
    except Exception as e:
        # Unexpected error - log and show generic message
        import logging
        logger = logging.getLogger(__name__)
        logger.exception(f"Unexpected error publishing article {pk}")
        
        messages.error(
            request,
            _('An unexpected error occurred. Please try again later.')
        )
        return redirect('article-detail', pk=pk)
```

**Key Principles:**

1. **Eager translation in views**: Use `gettext()` (not lazy) because request context exists
2. **User-friendly error messages**: Each error type has appropriate message and redirect
3. **Message context**: Include relevant data in messages (article title, etc.)
4. **Logging untranslated details**: Log full technical details for debugging, show friendly message to user
5. **Proper error handling**: Different exceptions get different treatment

### Class-Based Views

```python
from django.views.generic import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils.translation import gettext as _

class ArticleCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new article.
    
    LoginRequiredMixin ensures only authenticated users can access.
    """
    model = Article
    fields = ['title', 'content', 'summary']
    template_name = 'articles/form.html'
    
    def get_context_data(self, **kwargs):
        """Add translatable page title to template context."""
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Create New Article')
        return context
    
    def form_valid(self, form):
        """Handle successful form submission."""
        # Set author before saving
        form.instance.author = self.request.user
        
        # Save and get response
        response = super().form_valid(form)
        
        # Show success message with article title
        messages.success(
            self.request,
            _('Article "%(title)s" created successfully!') % {
                'title': form.instance.title
            }
        )
        return response
    
    def form_invalid(self, form):
        """Handle form validation failure."""
        # Show generic error message
        messages.error(
            self.request,
            _('Please correct the errors below.')
        )
        return super().form_invalid(form)


class ArticleUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing article."""
    model = Article
    fields = ['title', 'content', 'summary', 'status']
    template_name = 'articles/form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Edit Article')
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            _('Article "%(title)s" updated successfully.') % {
                'title': form.instance.title
            }
        )
        return response
    
    def form_invalid(self, form):
        messages.error(
            self.request,
            _('Please correct the errors below.')
        )
        return super().form_invalid(form)


class ArticleDeleteView(LoginRequiredMixin, DeleteView):
    """Delete an article (with confirmation)."""
    model = Article
    template_name = 'articles/confirm_delete.html'
    success_url = '/articles/'
    
    def delete(self, request, *args, **kwargs):
        """Delete article and show confirmation message."""
        article = self.get_object()
        article_title = article.title  # Save before deletion
        
        response = super().delete(request, *args, **kwargs)
        
        messages.success(
            request,
            _('Article "%(title)s" has been permanently deleted.') % {
                'title': article_title
            }
        )
        return response
```

### Service Classes for Complex Business Logic

```python
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

class ArticleService:
    """
    Business logic service with translated error handling.
    
    Keeps translation logic centralized, making it easier to:
    - Update messages consistently
    - Test validation logic
    - Reuse across views, API, commands, etc.
    """
    
    @staticmethod
    def validate_title(title):
        """
        Validate article title with translatable errors.
        
        Args:
            title: Title string to validate
        
        Raises:
            ValidationError: If title is invalid
        """
        if not title or len(title.strip()) == 0:
            raise ValidationError(
                _('Title is required.')
            )
        
        if len(title) < 5:
            raise ValidationError(
                _('Title must be at least 5 characters long.')
            )
        
        if len(title) > 200:
            raise ValidationError(
                _('Title cannot exceed 200 characters.')
            )
    
    @staticmethod
    def validate_content(content):
        """
        Validate article content with pluralization.
        
        Uses ngettext for proper plural forms in translations.
        """
        word_count = len(content.split())
        
        if word_count < 50:
            from django.utils.translation import ngettext
            raise ValidationError(
                ngettext(
                    'Content must be at least 50 words. You have %(count)d word.',
                    'Content must be at least 50 words. You have %(count)d words.',
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
            # Validate state
            if article.status != Article.Status.DRAFT:
                return False, _('Only draft articles can be published.')
            
            # Validate content
            ArticleService.validate_content(article.content)
            ArticleService.validate_title(article.title)
            
            # Perform action
            article.status = Article.Status.PUBLISHED
            article.published_at = timezone.now()
            article.save()
            
            return True, _('Article published successfully.')
        
        except ValidationError as e:
            return False, str(e.message)
        
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception("Error publishing article")
            return False, _('Unexpected error. Please try again later.')
```

---

## Forms and User Input Validation {#forms-and-validation}

### Why Form Translation Matters

Forms are where users interact with your application and where validation errors occur. Every piece of form text must be translatable:

1. **Field labels** - What the user sees above input boxes
2. **Help text** - Explanatory text below fields
3. **Error messages** - Validation failure feedback
4. **Placeholder text** - Suggested input format

### Complete Model Form with Translation

```python
from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext
from django.core.exceptions import ValidationError

class ArticleForm(forms.ModelForm):
    """
    Form for creating and editing articles.
    
    Every piece of text users see is translatable.
    """
    
    # Override default CharField to customize label, help, errors
    title = forms.CharField(
        label=_('Article Title'),
        max_length=200,
        widget=forms.TextInput(attrs={
            'placeholder': _('Enter your article title'),
            'class': 'form-control',
            'autocomplete': 'off',
        }),
        help_text=_('Keep it concise and descriptive'),
        error_messages={
            'required': _('Title is required.'),
            'max_length': _('Title cannot exceed 200 characters.'),
        }
    )
    
    content = forms.CharField(
        label=_('Article Content'),
        widget=forms.Textarea(attrs={
            'placeholder': _('Write your article here...'),
            'class': 'form-control',
            'rows': 10,
        }),
        help_text=_('Markdown formatting is supported'),
        error_messages={
            'required': _('Content is required.'),
        }
    )
    
    summary = forms.CharField(
        label=_('Summary'),
        required=False,  # Optional field
        widget=forms.Textarea(attrs={
            'placeholder': _('Brief overview shown in listings'),
            'class': 'form-control',
            'rows': 3,
        }),
        help_text=_('Optional. Shown in article listings.')
    )
    
    class Meta:
        model = Article
        fields = ['title', 'content', 'summary', 'status']
        labels = {
            'status': _('Publication Status'),
        }
        help_texts = {
            'status': _('Choose whether this article is draft or published'),
        }
    
    # FIELD-LEVEL VALIDATION
    # Called after individual field is validated
    
    def clean_title(self):
        """
        Validate article title.
        
        This method is called after CharField validation but before
        full form clean(). It's where you put field-specific logic.
        """
        title = self.cleaned_data.get('title', '').strip()
        
        # Check minimum length
        if len(title) < 5:
            raise ValidationError(
                _('Title must be at least 5 characters long.')
            )
        
        # Check for duplicates (excluding current article if editing)
        queryset = Article.objects.filter(title__iexact=title)
        
        # In update view, exclude current instance
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        # If duplicate exists, error
        if queryset.exists():
            raise ValidationError(
                _('An article with this title already exists.')
            )
        
        return title
    
    def clean_content(self):
        """
        Validate article content with pluralization.
        
        Uses ngettext so translation accounts for language-specific
        plural rules.
        """
        content = self.cleaned_data.get('content', '').strip()
        word_count = len(content.split())
        
        # Minimum word count
        if word_count < 50:
            raise ValidationError(
                ngettext(
                    'Content must be at least 50 words. '
                    'You have %(count)d word.',
                    'Content must be at least 50 words. '
                    'You have %(count)d words.',
                    word_count
                ) % {'count': word_count}
            )
        
        # Maximum word count (optional)
        max_words = 10000
        if word_count > max_words:
            raise ValidationError(
                ngettext(
                    'Content cannot exceed %(max)d word.',
                    'Content cannot exceed %(max)d words.',
                    max_words
                ) % {'max': max_words}
            )
        
        return content
    
    # CROSS-FIELD VALIDATION
    # Called after all individual field validation
    
    def clean(self):
        """
        Validate across multiple fields.
        
        This is called after all field validation. Use it for checks
        that span multiple fields or for complex logic.
        """
        cleaned_data = super().clean()
        
        status = cleaned_data.get('status')
        summary = cleaned_data.get('summary')
        
        # Published articles must have summary
        if status == Article.Status.PUBLISHED and not summary:
            raise ValidationError(
                _('Published articles must include a summary.')
            )
        
        return cleaned_data
```

**Validation Hierarchy Explanation:**

1. **Field-level validation**
   - CharField checks max_length
   - IntegerField checks it's an integer
   - Called for each field independently
   - If field fails, that field's error shows

2. **Form-level clean_<field> methods**
   - Called after field validation
   - Can access self.cleaned_data
   - Can check database for duplicates
   - Field-specific complex logic

3. **Form-level clean() method**
   - Called after all field clean methods
   - Can access all cleaned_data
   - Can validate relationships between fields
   - Can raise ValidationError on specific fields or general error

### Custom Validators for Reusability

```python
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy

def validate_no_profanity(value):
    """
    Reusable validator to check for inappropriate language.
    
    Can be applied to multiple form fields or model fields.
    
    Usage:
        content = forms.CharField(validators=[validate_no_profanity])
    """
    # List of banned words (in production, might be database/service)
    banned_words = ['badword1', 'badword2', 'inappropriate']
    
    # Check if any banned word appears (case-insensitive)
    for word in banned_words:
        if word.lower() in value.lower():
            raise ValidationError(
                _('Your content contains inappropriate language.')
            )


def validate_minimum_words(min_words):
    """
    Validator factory - creates validators with specific word count.
    
    This is a function that returns a validator function, allowing
    reuse with different parameters.
    
    Usage:
        content = forms.CharField(validators=[validate_minimum_words(100)])
    """
    def validator(value):
        word_count = len(value.split())
        if word_count < min_words:
            raise ValidationError(
                ngettext_lazy(
                    'Content must be at least %(min)d word.',
                    'Content must be at least %(min)d words.',
                    min_words
                ) % {'min': min_words}
            )
    
    validator.__name__ = f'validate_minimum_{min_words}_words'
    return validator


def validate_unique_slug(value, exclude_id=None):
    """
    Validate slug uniqueness.
    
    Can be used in forms where you can't rely on model's unique constraint.
    """
    queryset = Article.objects.filter(slug=value)
    if exclude_id:
        queryset = queryset.exclude(pk=exclude_id)
    
    if queryset.exists():
        raise ValidationError(
            _('An article with this URL already exists.')
        )


# Using validators in forms
class ArticleForm(forms.ModelForm):
    content = forms.CharField(
        validators=[
            validate_no_profanity,  # Check content
            validate_minimum_words(50),  # At least 50 words
        ]
    )
    
    class Meta:
        model = Article
        fields = ['title', 'content']
```

---

## Templates {#templates}

### Why Template Translation is Critical

Templates generate the HTML users see. Every visible text must be translatable:

1. **Navigation**: Menu items, labels
2. **Page content**: Headings, descriptions
3. **Form labels and help text**: Already handled if using forms
4. **Messages and feedback**: Errors, confirmations
5. **Model data**: Dates, numbers (formatted per locale)

### Loading i18n in Templates

```django
{% load i18n %}
```

This must be at the top of any template using translation tags.

### Basic Translation Tags

```django
{% load i18n %}

<!-- SIMPLE TRANSLATION -->
<!-- Wraps static text for translation -->
<h1>{% trans "Welcome to Our Blog" %}</h1>

<!-- VARIABLES -->
<!-- Use blocktrans for text with variables -->
<p>
  {% blocktrans with name=user.get_full_name %}
    Hello {{ name }}, welcome back!
  {% endblocktrans %}
</p>

<!-- PLURALIZATION -->
<!-- Different text based on count, handles language plural rules -->
{% blocktrans count counter=articles|length %}
  There is {{ counter }} article.
{% plural %}
  There are {{ counter }} articles.
{% endblocktrans %}

<!-- CONTEXT FOR DISAMBIGUATION -->
<!-- Tells translators the context/meaning of word -->
<button>
  {% pgettext "button label" "Submit" %}
</button>
```

**Why use blocktrans instead of trans with variables?**

```django
<!-- ❌ DON'T DO THIS -->
<p>{% trans "Hello " %}{{ username }}{% trans ", welcome back!" %}</p>

<!-- Problems:
     - Broken into 3 separate sentences
     - Translator can't see full context
     - Some languages have different word order
     - Can't reorder words for grammar
-->

<!-- ✅ DO THIS INSTEAD -->
<p>
  {% blocktrans with name=username %}
    Hello {{ name }}, welcome back!
  {% endblocktrans %}
</p>

<!-- Benefits:
     - Translator sees full sentence
     - Can reorder words if needed
     - Grammatically correct in each language
-->
```

### Translating Model Display

```django
{% load i18n %}

<!-- Display article with automatic translation -->
<div class="article">
    <!-- Field values (user-generated data) are not translated -->
    <h1>{{ article.title }}</h1>
    
    <!-- Field metadata (verbose_name) is automatically translated -->
    <p class="published">
        {{ article.get_published_at_display }}
    </p>
    
    <!-- Choice labels are automatically translated to user's language -->
    <span class="badge">
        {{ article.get_status_display }}
    </span>
    
    <!-- Dates are formatted according to locale -->
    <time datetime="{{ article.created_at|date:'c' }}">
        {% blocktrans with date=article.created_at|date:"DATE_FORMAT" %}
            Published on {{ date }}
        {% endblocktrans %}
    </time>
    
    <!-- Numbers are formatted per locale -->
    <p>
        {% blocktrans with views=article.views_count|localize %}
            This article has been viewed {{ views }} times.
        {% endblocktrans %}
    </p>
</div>
```

**Important:** Article title and content are NOT translated. They're user data. Only metadata (when it was published, view count) is localized.

### Form Error Display

```django
{% load i18n %}

<!-- Display all form errors -->
{% if form.errors %}
    <div class="alert alert-danger" role="alert">
        <h4 class="alert-heading">
            {% trans "Please correct the following errors:" %}
        </h4>
        <ul>
            {% for field, errors in form.errors.items %}
                <li>
                    <!-- Field label is automatically translated -->
                    <strong>{{ form|lookup:field|label }}:</strong>
                    
                    <!-- Error messages are automatically translated -->
                    {% for error in errors %}
                        <div class="error">{{ error }}</div>
                    {% endfor %}
                </li>
            {% endfor %}
        </ul>
    </div>
{% endif %}

<!-- Display field-specific errors -->
<form>
    {% for field in form %}
        <div class="form-group">
            <!-- Field label (from model verbose_name or form label=) -->
            {{ field.label_tag }}
            {{ field }}
            
            <!-- Field help text (from model or form) -->
            {% if field.help_text %}
                <small class="form-text text-muted">
                    {{ field.help_text|safe }}
                </small>
            {% endif %}
            
            <!-- Field errors (ValidationError messages) -->
            {% if field.errors %}
                <ul class="errorlist">
                    {% for error in field.errors %}
                        <li>{{ error }}</li>
                    {% endfor %}
                </ul>
            {% endif %}
        </div>
    {% endfor %}
</form>
```

### Language Selector

```django
{% load i18n %}

<!-- Dropdown to switch languages -->
<div class="language-selector">
    <form method="post" action="{% url 'set_language' %}">
        {% csrf_token %}
        
        <label for="id_language">
            {% trans "Language" %}:
        </label>
        
        <select name="language" id="id_language" 
                onchange="this.form.submit()" class="form-control">
            
            <!-- Get available languages from settings -->
            {% get_available_languages as available_languages %}
            
            {% for code, name in available_languages %}
                <!-- name is already translated (from settings LANGUAGES) -->
                <option value="{{ code }}"
                        {% if code == LANGUAGE_CODE %}selected{% endif %}>
                    {{ name }}
                </option>
            {% endfor %}
        </select>
    </form>
</div>

<!-- URL view needed for set_language to work -->
<!-- Add to urls.py: path('i18n/', include('django.conf.urls.i18n')), -->
```

---

## Management Commands {#management-commands}

### Why Command Translation Matters

Management commands are often used for:
- Batch processing
- Automated tasks
- Admin utilities
- Deployment scripts

Output should be localized when running in different language contexts.

### Complete Translated Management Command

```python
# apps/articles/management/commands/publish_scheduled.py

from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import gettext as _
from django.utils.translation import activate, ngettext
from django.utils import timezone
from articles.models import Article
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    """
    Publish articles scheduled for publication.
    
    This command finds articles with published_at in the past
    and changes their status to PUBLISHED.
    
    Usage:
        python manage.py publish_scheduled
        python manage.py publish_scheduled --dry-run
        python manage.py publish_scheduled --language es
    """
    
    # Description shown in help
    help = _('Publish articles scheduled for publication')
    
    def add_arguments(self, parser):
        """Define command-line arguments."""
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            help=_('Show what would be published without making changes')
        )
        
        parser.add_argument(
            '--language',
            type=str,
            default='en',
            dest='language',
            help=_('Language for output messages (default: en)')
        )
        
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            dest='batch_size',
            help=_('Number of articles to process per batch (default: 100)')
        )
    
    def handle(self, *args, **options):
        """Main command logic."""
        
        # Get options
        dry_run = options['dry_run']
        language = options['language']
        batch_size = options['batch_size']
        
        # Set language for all output messages
        activate(language)
        
        try:
            # Find candidates for publication
            articles = Article.objects.filter(
                status=Article.Status.DRAFT,
                published_at__lte=timezone.now()
            ).order_by('published_at')
            
            # No articles to publish
            if not articles.exists():
                self.stdout.write(
                    self.style.WARNING(
                        _('No articles scheduled for publication.')
                    )
                )
                return
            
            # Get count
            total_count = articles.count()
            
            # Process in batches (memory efficient)
            published_count = 0
            for idx, article in enumerate(articles, 1):
                try:
                    # Show progress
                    self.stdout.write(
                        _('Processing %(current)d/%(total)d: %(title)s') % {
                            'current': idx,
                            'total': total_count,
                            'title': article.title
                        }
                    )
                    
                    # Actually publish if not dry-run
                    if not dry_run:
                        article.status = Article.Status.PUBLISHED
                        article.save()
                        published_count += 1
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            _('✓ Published: %(title)s') % {
                                'title': article.title
                            }
                        )
                    )
                
                except Exception as e:
                    logger.exception(f"Error publishing article {article.id}")
                    self.stdout.write(
                        self.style.ERROR(
                            _('✗ Error publishing %(title)s: %(error)s') % {
                                'title': article.title,
                                'error': str(e)
                            }
                        )
                    )
            
            # Summary message
            if dry_run:
                self.stdout.write(
                    self.style.HTTP_INFO(
                        ngettext(
                            '[DRY RUN] Would have published %(count)d article.',
                            '[DRY RUN] Would have published %(count)d articles.',
                            total_count
                        ) % {'count': total_count}
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        ngettext(
                            'Successfully published %(count)d article.',
                            'Successfully published %(count)d articles.',
                            published_count
                        ) % {'count': published_count}
                    )
                )
        
        except Exception as e:
            logger.exception("Error in publish_scheduled command")
            raise CommandError(
                _('Error: %(error)s') % {'error': str(e)}
            )
```

**Key Command Translation Points:**

1. **activate(language)** - Sets language for this command's execution
2. **self.style.SUCCESS/ERROR/WARNING** - Color-coded output
3. **ngettext for pluralization** - Correct forms in user's language
4. **CommandError for failures** - Proper exit codes and messages
5. **Logging technical details** - Separate from user-facing messages

---

## Asynchronous Tasks and Background Jobs {#async-tasks}

### Why Async Task Translation Differs

Celery tasks run in separate processes. Unlike views (which have request context), tasks don't automatically know the user's language.

**Problem:** When a task sends an email or notification, which language should it use?

**Solution:** Pass language context to the task explicitly.

### Complete Translated Celery Task

```python
# apps/articles/tasks.py

from celery import shared_task, Task
from django.utils.translation import gettext as _
from django.utils.translation import activate, get_language, override
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from articles.models import Article
from users.models import User
import logging

logger = logging.getLogger(__name__)

class TranslatedTask(Task):
    """
    Base class for tasks that need translation support.
    
    Subclass this instead of Task to get language context automatically.
    """
    
    def __call__(self, *args, **kwargs):
        """Ensure language is set before task runs."""
        language = kwargs.pop('language', None) or settings.LANGUAGE_CODE
        with override(language):
            return self.run(*args, **kwargs)


@shared_task(bind=True, base=TranslatedTask)
def send_publication_notification(
    self,
    article_id,
    user_id,
    language='en'
):
    """
    Send email notification when article is published.
    
    Args:
        article_id: ID of published article
        user_id: ID of article author
        language: Language code for email (user's preference)
    
    This task demonstrates:
    - Explicit language passing
    - Translated email subject and body
    - Error handling and retries
    """
    
    try:
        # Activate user's language for this task
        activate(language)
        
        # Fetch objects
        article = Article.objects.get(id=article_id)
        user = User.objects.get(id=user_id)
        
        # Compose translated email
        subject = _('Article Published: %(title)s') % {
            'title': article.title
        }
        
        message = _(
            'Your article "%(title)s" has been published '
            'and is now live on our site!'
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
        logger.error(f"Article {article_id} not found")
        return _('Article not found')
    
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return _('User not found')
    
    except Exception as e:
        logger.exception("Error sending publication notification")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60)


@shared_task(bind=True)
def process_article_batch(
    self,
    article_ids,
    operation='summarize',
    language='en'
):
    """
    Process multiple articles with progress tracking.
    
    Args:
        article_ids: List of article IDs to process
        operation: Type of operation (summarize, analyze, etc.)
        language: Language for any messages
    
    Demonstrates:
    - Batch processing with progress updates
    - Language context for messages
    - Task state updates for progress bar
    """
    
    activate(language)
    
    results = []
    total = len(article_ids)
    
    for idx, article_id in enumerate(article_ids, 1):
        try:
            article = Article.objects.get(id=article_id)
            
            # Simulate work
            if operation == 'summarize':
                article.generate_summary()
                article.save()
            
            result = _('Processed %(idx)d/%(total)d: %(title)s') % {
                'idx': idx,
                'total': total,
                'title': article.title
            }
            results.append(result)
            
            # Update task progress for frontend
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
            logger.exception(f"Error processing article {article_id}")
            results.append(
                _('Error processing %(idx)d: %(error)s') % {
                    'idx': idx,
                    'error': str(e)
                }
            )
    
    return {
        'status': _('Batch processing complete'),
        'results': results,
        'total': total
    }
```

### Triggering Tasks from Views

```python
# views.py - How to queue tasks with language context

from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import get_language
from articles.tasks import send_publication_notification

def publish_article_view(request, pk):
    """Publish article and queue notification task."""
    
    article = get_object_or_404(Article, pk=pk)
    
    # Get current user's language
    current_language = get_language()
    
    # Update article
    article.status = Article.Status.PUBLISHED
    article.published_at = timezone.now()
    article.save()
    
    # Queue task with language context
    # Task will send email in user's language
    send_publication_notification.delay(
        article_id=article.id,
        user_id=article.author.id,
        language=current_language  # Pass user's language
    )
    
    messages.success(
        request,
        _('Article published! Author will be notified.')
    )
    return redirect('article-detail', pk=pk)
```

---

## Translation Workflow and Tools {#translation-workflow}

### The Complete Translation Process

Translation is a workflow with multiple stages:

**Stage 1: Mark strings** (Developer)
- Add `_()` around all user-facing text
- Already covered in previous sections

**Stage 2: Extract strings**
```bash
python manage.py makemessages -a
```
Creates/updates `.po` files with all marked strings

**Stage 3: Translate** (Translator)
- Edit `.po` files in Poedit, Weblate, or text editor
- Add `msgstr` values for each `msgid`

**Stage 4: Compile**
```bash
python manage.py compilemessages
```
Converts `.po` files to `.mo` (binary, fast lookup)

**Stage 5: Deploy**
- Include `.mo` files in deployment
- Django uses these at runtime

### Understanding .po Files

```
# locale/es/LC_MESSAGES/django.po
# Spanish translations for My Blog

#: apps/articles/models.py:15
msgid "Article"
msgstr "Artículo"

#: apps/articles/models.py:25
msgid "Title"
msgstr "Título"

#: apps/articles/models.py:30
msgid "Content"
msgstr "Contenido"

#: apps/articles/models.py:50
#, python-format
msgid "Published %(count)d days ago"
msgstr "Publicado hace %(count)d días"

# Plural forms example
#: apps/articles/models.py:75
msgid "You have %(count)d article"
msgid_plural "You have %(count)d articles"
msgstr[0] "Tienes %(count)d artículo"
msgstr[1] "Tienes %(count)d artículos"
```

**Fields:**
- `#:` - Location in source code
- `msgid` - Original English text
- `msgstr` - Translated text
- `#,` comment - Flags like `python-format` for strings with variables

### Translation Tools and Services

**Poedit (Desktop)**
- Download from poedit.net
- GUI for editing .po files
- Integrates with version control
- Free and paid versions

**Weblate (Web-based)**
- Self-hosted or SaaS
- Team collaboration
- Git integration
- Automatic merging back to repo

**Crowdin (SaaS)**
- Professional translation platform
- Translation memory
- Pricing per word

**LocalizationKit (SaaS)**
- Simpler than Crowdin
- Good for small teams

**Command-line workflow:**

```bash
# 1. Extract all translatable strings
python manage.py makemessages -a

# 2. Merge with existing translations (if updating)
msgmerge -U locale/es/LC_MESSAGES/django.po locale/django.pot

# 3. Edit .po file (your editor or Poedit)
poedit locale/es/LC_MESSAGES/django.po

# 4. Compile to binary .mo format
python manage.py compilemessages

# 5. Test
LANGUAGE_CODE=es python manage.py runserver

# 6. Commit and deploy
git add locale/
git commit -m "Update Spanish translations"
```

---

## Testing and Quality Assurance {#testing}

### Why Test Translations

Translations can fail silently:
- Missing .mo files (Django falls back to English)
- Untranslated strings (show English instead)
- Broken placeholders (Python errors)
- Wrong plural forms (shows English)

Tests prevent these issues from reaching production.

### Test Suite for Translations

```python
# tests/test_translations.py

from django.test import TestCase, override_settings
from django.utils.translation import (
    activate, override, gettext as _, 
    gettext_lazy, ngettext
)
from django.conf import settings
from articles.models import Article

class ModelTranslationTestCase(TestCase):
    """Test that models have complete translation coverage."""
    
    def test_article_verbose_name_translatable(self):
        """Article verbose name should be translatable."""
        # Verbose names are lazy, so convert to string in different languages
        with override('es'):
            spanish = str(Article._meta.verbose_name)
        
        with override('fr'):
            french = str(Article._meta.verbose_name)
        
        # All should be strings (not lazy objects anymore)
        self.assertIsInstance(spanish, str)
        self.assertIsInstance(french, str)
        
        # Should be translated (not same as English)
        self.assertNotEqual(spanish, 'Article')
        self.assertNotEqual(french, 'Article')
    
    def test_field_verbose_names_are_lazy(self):
        """All field verbose_names should use lazy translation."""
        for field in Article._meta.get_fields():
            if hasattr(field, 'verbose_name'):
                # Check if it's a lazy translation object
                self.assertTrue(
                    hasattr(field.verbose_name, '_proxy____args') or
                    isinstance(field.verbose_name, str),
                    f"Field {field.name} verbose_name not lazy: "
                    f"{field.verbose_name}"
                )
    
    def test_choice_labels_translated(self):
        """Status choice labels should be translated."""
        with override('es'):
            choices = dict(Article.Status.choices)
            draft = str(choices[Article.Status.DRAFT])
            published = str(choices[Article.Status.PUBLISHED])
        
        # Should be Spanish words, not English
        self.assertNotEqual(draft, 'Draft')
        self.assertNotEqual(published, 'Published')


class ViewTranslationTestCase(TestCase):
    """Test that views show translated content."""
    
    def setUp(self):
        self.article = Article.objects.create(
            title='Test Article',
            content='Content' * 20,
            status=Article.Status.DRAFT
        )
    
    def test_admin_field_labels_translated(self):
        """Admin form should show translated field labels."""
        # This requires AdminSite to be set up with translation
        # Usually tested through admin tests
        pass
    
    def test_form_labels_translated(self):
        """Form labels should be translatable."""
        from articles.forms import ArticleForm
        
        with override('es'):
            form = ArticleForm()
            # Labels are lazy, convert to string
            title_label = str(form.fields['title'].label)
        
        # Should be Spanish
        self.assertNotEqual(title_label, 'Article Title')


class TemplateTranslationTestCase(TestCase):
    """Test that templates properly translate content."""
    
    def setUp(self):
        self.article = Article.objects.create(
            title='Test Article',
            content='Content' * 20
        )
    
    def test_template_status_display_translated(self):
        """Template should show translated status."""
        self.client.get('/')  # Just to load Django
        
        with override('es'):
            display = self.article.get_status_display()
        
        # Should be Spanish for Draft
        self.assertNotEqual(display, 'Draft')
    
    def test_all_languages_supported(self):
        """Template rendering should work in all languages."""
        for code, name in settings.LANGUAGES:
            with override(code):
                # Should not raise any errors
                display = self.article.get_status_display()
                self.assertIsInstance(display, str)


class PluralFormTestCase(TestCase):
    """Test that plural forms work correctly."""
    
    def test_ngettext_singular(self):
        """Single item should use singular form."""
        with override('es'):
            result = ngettext(
                '%(count)d item',
                '%(count)d items',
                1
            ) % {'count': 1}
        
        # Should match singular translation
        self.assertIn('1', result)
    
    def test_ngettext_plural(self):
        """Multiple items should use plural form."""
        with override('es'):
            result = ngettext(
                '%(count)d item',
                '%(count)d items',
                5
            ) % {'count': 5}
        
        # Should match plural translation
        self.assertIn('5', result)


class TranslationCompletenessTestCase(TestCase):
    """Test that all strings are properly marked for translation."""
    
    def test_no_hardcoded_user_strings(self):
        """User-facing strings shouldn't be hardcoded."""
        # This would require code inspection or linting
        # Usually done with tools like gettext-lint or custom linters
        pass
```

### Testing in Different Languages

```python
# Django test runner with language override

from django.test import TestCase
from django.utils.translation import override

class SpanishTranslationTestCase(TestCase):
    """Run all tests with Spanish language."""
    
    def setUp(self):
        self.language_override = override('es')
        self.language_override.__enter__()
    
    def tearDown(self):
        self.language_override.__exit__(None, None, None)
```

---

## Performance Considerations {#performance}

### Translation Performance Matters

Each translation lookup has a tiny cost. With thousands of page views, it adds up.

**Sources of overhead:**
1. Lazy object creation - minimal
2. String lookup in .mo files - very fast (binary search)
3. Memory for translations - can be significant in RAM

### Performance Best Practices

**1. Use .mo files (binary)**
```bash
# Always compile translations
python manage.py compilemessages
```

Binary .mo files are 10-100x faster than .po files.

**2. Minimize lazy objects**
- Don't create unnecessary lazy objects
- Use gettext_lazy only where needed

**3. Cache translations at high level**
```python
# ❌ DON'T: Query translation in loop
for article in articles:
    message = _('Article: %(title)s') % {'title': article.title}
```

```python
# ✅ DO: Cache translated template
article_template = _('Article: %(title)s')
for article in articles:
    message = article_template % {'title': article.title}
```

**4. Use select_related/prefetch_related**
- Reduce database queries
- Translation performance is moot if database is slow

**5. Monitor translation file size**
```bash
# Check .mo file size
ls -lh locale/*/LC_MESSAGES/django.mo

# If >1MB, consider splitting into multiple apps
```

---

## Common Pitfalls and Solutions {#pitfalls}

### Pitfall 1: Using gettext() in Models

**Problem:**
```python
from django.utils.translation import gettext as _

class Article(models.Model):
    title = models.CharField(verbose_name=_("Title"))
    # Translates at import time, wrong language!
```

**Solution:**
```python
from django.utils.translation import gettext_lazy as _

class Article(models.Model):
    title = models.CharField(verbose_name=_("Title"))
    # Translates when needed, correct language!
```

### Pitfall 2: Forgetting Choice Label Translation

**Problem:**
```python
class Article(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),  # Won't be translated!
        ('published', 'Published'),
    ]
    status = models.CharField(choices=STATUS_CHOICES)
```

**Solution:**
```python
class Article(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        PUBLISHED = 'published', _('Published')
    
    status = models.CharField(choices=Status.choices)
```

### Pitfall 3: String Concatenation

**Problem:**
```python
# ❌ Breaks translation
message = _('Welcome') + ' ' + user.name + _('!')

# Also breaks with f-strings
message = f"{_('Welcome')} {user.name}{_('!')}"
```

**Solution:**
```python
# ✅ Use format strings
message = _('Welcome %(name)s!') % {'name': user.name}
```

### Pitfall 4: No Language Context in Tasks

**Problem:**
```python
@shared_task
def send_email(user_id):
    user = User.objects.get(id=user_id)
    subject = _('Welcome!')  # Unknown language!
    send_mail(subject, ...)
```

**Solution:**
```python
@shared_task
def send_email(user_id, language='en'):
    from django.utils.translation import activate
    activate(language)
    
    user = User.objects.get(id=user_id)
    subject = _('Welcome!')  # Known language!
    send_mail(subject, ...)
```

### Pitfall 5: Mixing Lazy and Eager

**Problem:**
```python
# Inconsistent - confusing which is which
result = _lazy('Welcome') + gettext('to our site')
```

**Solution:**
```python
# Consistent - clear what's what
welcome = _('Welcome to our site')  # Use one or the other

# Or be explicit about why they differ
label = _('Article')  # Lazy - shown in admin
message = _('Article created')  # Eager - shown to user
```

---

## Enterprise Implementation {#enterprise}

### Large-Scale Translation Strategy

For applications with many languages or many developers:

**Structure:**
```
project/
├── locale/                     # Project-wide translations
│   ├── es/LC_MESSAGES/
│   ├── fr/LC_MESSAGES/
│   └── ...
├── apps/
│   ├── articles/
│   │   ├── locale/            # App-specific translations
│   │   │   ├── es/LC_MESSAGES/
│   │   │   └── fr/LC_MESSAGES/
│   │   ├── models.py
│   │   ├── views.py
│   │   └── ...
│   └── accounts/
│       ├── locale/
│       └── ...
```

This separation allows:
- Distributed translation (each app translated independently)
- Reusable apps with built-in translations
- Easier to manage large codebases

**settings.py:**
```python
LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
    os.path.join(BASE_DIR, 'apps', 'articles', 'locale'),
    os.path.join(BASE_DIR, 'apps', 'accounts', 'locale'),
]
```

### Translation Management Workflow

**Use Weblate or Crowdin for:**
- Collaborative translation
- Translation memory
- Context for translators
- Automatic Git integration
- Translation progress tracking

**Workflow:**
1. Developers mark strings, commit to Git
2. Weblate detects new strings via Git integration
3. Translators work in Weblate UI
4. Weblate commits translations back to Git
5. CI/CD automatically compiles .mo files
6. Deployment includes latest translations

### Quality Assurance for Translations

**Code review checklist:**
- [ ] All user-visible strings use `_()` or `_lazy()`
- [ ] Models use `gettext_lazy`
- [ ] Views use `gettext`
- [ ] No string concatenation (use format strings)
- [ ] Pluralization uses `ngettext`
- [ ] `.po` files are up-to-date
- [ ] `.mo` files are compiled
- [ ] Tests cover multiple languages
- [ ] Admin interface tested in multiple languages

**Translator notes:**
```python
# Use translator comments for context
# Translators: This "Submit" is on a button, not a form status
submit_button = pgettext('button label', 'Submit')
```

Translators see these comments in their translation tools.

---

## Summary

This guide covers translation at every layer of Django applications:

- **Models**: Translatable fields, choices, dynamic methods
- **Views**: User messages, error handling, service classes
- **Forms**: Field labels, validation messages, error display
- **Templates**: Trans tags, model data display, language selection
- **Commands**: Output messages, language context
- **Tasks**: Async email, language passing, progress updates
- **Testing**: Verify translations complete and working
- **Deployment**: Translation workflow, tools, quality

Key principles throughout:
1. Mark all user-visible strings
2. Use `gettext_lazy` at module level
3. Use `gettext` at runtime
4. Pass language context explicitly in async work
5. Test in multiple languages
6. Use format strings, not concatenation
7. Include translator context when ambiguous

---

