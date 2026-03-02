# Django i18n Technical Reference

Technical specification and implementation guide for Django internationalization (i18n).

---

## 1. Fundamentals

### 1.1 Overview

Django internationalization implements GNU gettext system. Process:

1. Mark translatable strings in code
2. Extract strings to `.po` files
3. Translators provide translations in `.po` files
4. Compile `.po` to `.mo` files (binary format)
5. Django loads translations at runtime

### 1.2 String Categories

| Category | Action | Example |
|----------|--------|---------|
| User-facing text | MUST translate | "Welcome to our site" |
| Debug/log messages | SHOULD NOT translate | "DEBUG: User 123 loaded" |
| User-generated data | NEVER translate | Article content from user |

### 1.3 Translation Timing

| Function | Timing | Use Case |
|----------|--------|----------|
| `gettext_lazy()` | Deferred (at use) | Models, forms, settings |
| `gettext()` | Immediate (at call) | Views, functions, tasks |

---

## 2. Configuration

### 2.1 settings.py Configuration

```python
LANGUAGE_CODE = 'en-us'

LANGUAGES = [
    ('en', _('English')),
    ('es', _('Spanish')),
    ('fr', _('French')),
]

I18N = True
USE_I18N = True
USE_L10N = True
USE_TZ = True
TIME_ZONE = 'UTC'

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]
```

**Required settings:**
- `I18N = True` - Enables translation system
- `USE_I18N = True` - Enables translation lookups
- `LOCALE_PATHS` - Where to find .po/.mo files

### 2.2 Middleware Configuration

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # After SessionMiddleware
    'django.middleware.common.CommonMiddleware',
    # ... other middleware
]
```

LocaleMiddleware detection order:
1. URL language code (if using i18n_patterns)
2. Session language preference
3. Accept-Language HTTP header
4. LANGUAGE_CODE setting

### 2.3 URL Configuration

```python
from django.conf.urls.i18n import i18n_patterns

urlpatterns = [
    path('api/', include('api.urls')),  # Non-translated
]

urlpatterns += i18n_patterns(
    path('articles/', include('articles.urls')),  # Translated
    prefix_default_language=True,
)
```

Effect: URLs become `/en/articles/`, `/es/articles/`, etc.

---

## 3. Models

### 3.1 Field Translation

```python
from django.db import models
from django.utils.translation import gettext_lazy as _

class Article(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name=_("Title"),
        help_text=_("Article title")
    )
    
    class Meta:
        verbose_name = _("Article")
        verbose_name_plural = _("Articles")
```

Translatable field attributes:
- `verbose_name` - Label in admin/forms
- `help_text` - Description in admin/forms
- `Meta.verbose_name` - Admin interface
- `Meta.verbose_name_plural` - Admin interface

### 3.2 Choice Fields

```python
class Article(models.Model):
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
```

Access patterns:
- `article.status` → 'draft' (value)
- `article.get_status_display()` → 'Borrador' (translated label)
- `Article.Status.DRAFT` → 'draft' (type-safe)
- `Article.Status.choices` → [('draft', 'Draft'), ...]

### 3.3 Dynamic Methods

```python
from django.utils.translation import pgettext, ngettext

class Article(models.Model):
    def get_status_label(self):
        labels = {
            self.Status.DRAFT: pgettext('status', 'Draft'),
            self.Status.PUBLISHED: pgettext('status', 'Published'),
        }
        return labels.get(self.status)
    
    def get_age_display(self):
        days = (timezone.now() - self.created_at).days
        return ngettext(
            '%(days)d day old',
            '%(days)d days old',
            days
        ) % {'days': days}
```

`pgettext(context, message)` - Provides context for translators
`ngettext(singular, plural, count)` - Selects correct plural form

---

## 4. Views

### 4.1 Function-Based Views

```python
from django.utils.translation import gettext as _
from django.contrib import messages

def publish_article(request, pk):
    article = get_object_or_404(Article, pk=pk)
    
    try:
        if article.author != request.user:
            raise PermissionError(
                _('No permission to publish.')
            )
        
        article.status = Article.Status.PUBLISHED
        article.save()
        
        messages.success(
            request,
            _('Article published successfully!')
        )
    
    except PermissionError as e:
        messages.error(request, str(e))
    
    return redirect('article-detail', pk=pk)
```

Pattern:
- Use eager `gettext()` (not lazy)
- Wrap error messages in `_()`
- Use Django messages framework for user feedback

### 4.2 Class-Based Views

```python
from django.views.generic import CreateView

class ArticleCreateView(LoginRequiredMixin, CreateView):
    model = Article
    fields = ['title', 'content']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Create Article')
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            _('Article created!')
        )
        return response
    
    def form_invalid(self, form):
        messages.error(
            self.request,
            _('Please correct errors.')
        )
        return super().form_invalid(form)
```

---

## 5. Forms

### 5.1 Field Definition

```python
from django import forms
from django.utils.translation import gettext_lazy as _

class ArticleForm(forms.ModelForm):
    title = forms.CharField(
        label=_('Article Title'),
        max_length=200,
        help_text=_('Brief title'),
        error_messages={
            'required': _('Title required'),
            'max_length': _('Too long'),
        }
    )
    
    class Meta:
        model = Article
        fields = ['title', 'content']
        labels = {
            'content': _('Article Content'),
        }
```

Translatable form components:
- Field `label`
- Field `help_text`
- Field `error_messages`
- Widget `attrs` (placeholder, etc.)
- Meta `labels`
- Meta `help_texts`

### 5.2 Validation

```python
class ArticleForm(forms.ModelForm):
    def clean_title(self):
        title = self.cleaned_data['title']
        if len(title) < 5:
            raise ValidationError(_('Too short'))
        return title
    
    def clean(self):
        cleaned = super().clean()
        if cleaned.get('status') == 'published' and not cleaned.get('summary'):
            raise ValidationError(
                _('Published articles need summary')
            )
        return cleaned
```

Validation hierarchy:
1. Field-level validation (`clean_<field>`)
2. Cross-field validation (`clean()`)
3. Model-level validation (model `clean()` method)

### 5.3 Custom Validators

```python
from django.core.exceptions import ValidationError
from django.utils.translation import ngettext_lazy

def validate_min_words(min_words):
    def validator(value):
        count = len(value.split())
        if count < min_words:
            raise ValidationError(
                ngettext_lazy(
                    'Min %(n)d word',
                    'Min %(n)d words',
                    min_words
                ) % {'n': min_words}
            )
    return validator
```

Usage:
```python
content = forms.CharField(validators=[validate_min_words(50)])
```

---

## 6. Templates

### 6.1 Translation Tags

| Tag | Use | Example |
|-----|-----|---------|
| `{% load i18n %}` | Required in template | Must be at top |
| `{% trans "text" %}` | Simple string | `{% trans "Welcome" %}` |
| `{% blocktrans %}` | Text with variables | `{% blocktrans %}Hello {{ name }}{% endblocktrans %}` |
| `{% pgettext "ctx" "text" %}` | Context translation | `{% pgettext "button" "Submit" %}` |

### 6.2 Basic Examples

```django
{% load i18n %}

<!-- Simple translation -->
<h1>{% trans "Articles" %}</h1>

<!-- With variables -->
<p>{% blocktrans with user=request.user %}
  Hello {{ user.name }}
{% endblocktrans %}</p>

<!-- Pluralization -->
{% blocktrans count counter=articles|length %}
  You have {{ counter }} article.
{% plural %}
  You have {{ counter }} articles.
{% endblocktrans %}

<!-- Model data (not translated) -->
<h2>{{ article.title }}</h2>

<!-- Choice display (auto-translated) -->
<span>{{ article.get_status_display }}</span>

<!-- Localized date -->
{{ article.created_at|date:"DATE_FORMAT" }}

<!-- Localized number -->
{{ article.views_count|localize }}
```

### 6.3 Form Rendering

```django
{% load i18n %}

{% if form.errors %}
  <div class="errors">
    <h4>{% trans "Please correct errors:" %}</h4>
    {% for field, errors in form.errors.items %}
      <ul>
        {% for error in errors %}
          <li>{{ error }}</li>
        {% endfor %}
      </ul>
    {% endfor %}
  </div>
{% endif %}

{% for field in form %}
  {{ field.label_tag }}
  {{ field }}
  {% if field.help_text %}
    <p>{{ field.help_text|safe }}</p>
  {% endif %}
  {% if field.errors %}
    <ul>
      {% for error in field.errors %}
        <li>{{ error }}</li>
      {% endfor %}
    </ul>
  {% endif %}
{% endfor %}
```

### 6.4 Language Selector

```django
{% load i18n %}

<form method="post" action="{% url 'set_language' %}">
  {% csrf_token %}
  <select name="language" onchange="this.form.submit()">
    {% get_available_languages as languages %}
    {% for code, name in languages %}
      <option value="{{ code }}" 
              {% if code == LANGUAGE_CODE %}selected{% endif %}>
        {{ name }}
      </option>
    {% endfor %}
  </select>
</form>

<!-- In urls.py: path('i18n/', include('django.conf.urls.i18n')) -->
```

---

## 7. Management Commands

### 7.1 Translation Commands

| Command | Action | Example |
|---------|--------|---------|
| `makemessages` | Extract strings to .po | `makemessages -a` |
| `compilemessages` | Compile .po to .mo | `compilemessages` |

```bash
# Extract all languages
python manage.py makemessages -a

# Extract specific languages
python manage.py makemessages -l es -l fr

# Include JavaScript
python manage.py makemessages -a -d djangojs

# Compile
python manage.py compilemessages
```

### 7.2 Custom Command with Translation

```python
from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _
from django.utils.translation import activate

class Command(BaseCommand):
    help = _('Do something useful')
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--language',
            default='en',
            help=_('Language for output')
        )
    
    def handle(self, *args, **options):
        activate(options['language'])
        
        try:
            # Do work
            self.stdout.write(
                self.style.SUCCESS(_('Success!'))
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    _('Error: %(error)s') % {'error': str(e)}
                )
            )
```

---

## 8. Asynchronous Tasks

### 8.1 Celery Task Translation

```python
from celery import shared_task
from django.utils.translation import gettext as _
from django.utils.translation import activate

@shared_task
def send_notification(user_id, language='en'):
    """Send email in user's language."""
    activate(language)
    
    user = User.objects.get(id=user_id)
    subject = _('Welcome!')  # Translated in user's language
    send_mail(subject, ...)
```

Pattern:
- Accept `language` parameter
- Call `activate(language)` at task start
- Use `gettext()` for messages

### 8.2 Triggering Task with Language

```python
from django.utils.translation import get_language

def publish_article(request, pk):
    article = get_object_or_404(Article, pk=pk)
    article.status = Article.Status.PUBLISHED
    article.save()
    
    # Queue task with current language
    send_notification.delay(
        user_id=article.author.id,
        language=get_language()
    )
    
    return redirect('article-detail', pk=pk)
```

---

## 9. Pluralization

### 9.1 ngettext Function

```python
from django.utils.translation import ngettext

# Singular vs Plural
count = 5
message = ngettext(
    '%(count)d item',
    '%(count)d items',
    count
) % {'count': count}
```

Syntax: `ngettext(singular, plural, count)`

Django selects correct form based on language plural rules.

### 9.2 ngettext_lazy

```python
from django.utils.translation import ngettext_lazy

# For module-level (model, form)
message = ngettext_lazy(
    '%(count)d day',
    '%(count)d days',
    days
)
```

### 9.3 Template Pluralization

```django
{% load i18n %}

{% blocktrans count counter=items %}
  You have {{ counter }} item.
{% plural %}
  You have {{ counter }} items.
{% endblocktrans %}
```

---

## 10. Context-Aware Translation

### 10.1 pgettext Function

```python
from django.utils.translation import pgettext

# Same word, different contexts
submit_button = pgettext('button label', 'Submit')
submitted_status = pgettext('status', 'Submitted')
```

Provides context to translators for disambiguation.

### 10.2 pgettext_lazy

```python
from django.utils.translation import pgettext_lazy

# For module-level
label = pgettext_lazy('menu', 'File')
```

---

## 11. .po and .mo Files

### 11.1 .po File Structure

```
# locale/es/LC_MESSAGES/django.po

#: models.py:15
msgid "Article"
msgstr "Artículo"

#: models.py:25
#, python-format
msgid "Published %(date)s"
msgstr "Publicado %(date)s"

#: models.py:35
msgid "You have %(count)d article."
msgid_plural "You have %(count)d articles."
msgstr[0] "Tienes %(count)d artículo."
msgstr[1] "Tienes %(count)d artículos."
```

Fields:
- `#:` - Source location
- `msgid` - Source string
- `msgstr` - Translation
- `#,` - Flags (python-format, etc.)
- `msgid_plural/msgstr[n]` - Plural forms

### 11.2 .mo File

Binary compiled version of .po. Generated by:
```bash
python manage.py compilemessages
```

Format: Indexed for O(1) lookup performance.

---

## 12. Testing

### 12.1 Test Translation

```python
from django.test import TestCase, override_settings
from django.utils.translation import override, gettext as _
from django.conf import settings

class TranslationTest(TestCase):
    def test_string_translatable(self):
        with override('es'):
            spanish = str(_('Article'))
        
        self.assertNotEqual(spanish, 'Article')
    
    def test_all_languages(self):
        for code, name in settings.LANGUAGES:
            with override(code):
                result = str(_('Welcome'))
                self.assertIsInstance(result, str)
```

### 12.2 Override Translation

```python
from django.utils.translation import override

# Temporary language switch
with override('es'):
    spanish_text = str(_('Welcome'))

# Language reverts automatically
english_text = str(_('Welcome'))
```

---

## 13. Workflow

### 13.1 Development to Production

1. **Mark strings** - Use `_()` in code
2. **Extract** - `python manage.py makemessages -a`
3. **Translate** - Edit .po files (Poedit, Weblate, etc.)
4. **Compile** - `python manage.py compilemessages`
5. **Test** - Test with multiple languages
6. **Deploy** - Include .mo files in deployment

### 13.2 Updating Translations

```bash
# Extract new/modified strings
python manage.py makemessages -a

# Merge with existing (if needed)
msgmerge -U locale/es/LC_MESSAGES/django.po locale/django.pot

# Compile
python manage.py compilemessages
```

### 13.3 Translation Tools

| Tool | Type | Notes |
|------|------|-------|
| Poedit | Desktop | GUI editor |
| Weblate | Web | Team collaboration |
| Crowdin | SaaS | Professional translation |
| vim/nano | CLI | Text editor |

---

## 14. Import Patterns

### 14.1 Module-Level Code

```python
# models.py, forms.py, settings.py
from django.utils.translation import gettext_lazy as _

class Article(models.Model):
    title = models.CharField(verbose_name=_("Title"))
```

### 14.2 Runtime Code

```python
# views.py, functions, commands, tasks
from django.utils.translation import gettext as _

def publish(request):
    messages.success(request, _('Published!'))
```

### 14.3 Special Cases

```python
# Pluralization
from django.utils.translation import ngettext, ngettext_lazy

# Context
from django.utils.translation import pgettext, pgettext_lazy

# Language control
from django.utils.translation import activate, override, get_language
```

---

## 15. Common Patterns

### 15.1 Error with Context

```python
# Format with variables
error = _('Article "%(title)s" by %(author)s') % {
    'title': article.title,
    'author': article.author.name
}

# NOT:
error = f'Article "{article.title}" by {article.author.name}'
```

### 15.2 Conditional Message

```python
if article.status == Article.Status.DRAFT:
    message = _('Article is a draft')
else:
    message = _('Article is published')
```

### 15.3 List of Options

```python
statuses = {
    Article.Status.DRAFT: _('Draft'),
    Article.Status.PUBLISHED: _('Published'),
}

display = statuses.get(article.status)
```

---

## 16. Troubleshooting

### 16.1 Translations Not Showing

| Issue | Cause | Solution |
|-------|-------|----------|
| Strings in English | .mo files not compiled | Run `compilemessages` |
| Strings disappear | I18N=False | Set I18N=True in settings |
| No LOCALE_PATHS | Files not found | Add LOCALE_PATHS to settings |
| Wrong language | LocaleMiddleware missing | Add to MIDDLEWARE |

### 16.2 Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| No modules named translations | Missing makemessages | Run `makemessages` |
| Empty translations | Translators didn't translate | Have translators complete .po files |
| Placeholder errors | Variable name mismatch | Use matching names in `%` operator |

---

## 17. Performance

### 17.1 Optimization

- Use .mo files (binary, faster than .po)
- Minimize lazy object creation
- Cache frequently accessed translations
- Use select_related/prefetch_related for database queries

### 17.2 File Size

Typical .mo file sizes:
- Small app: <100KB
- Medium app: 100KB-1MB
- Large app: >1MB (consider splitting)

---

## 18. Architecture

### 18.1 Directory Structure

```
project/
├── locale/                      # Project-wide
│   ├── es/LC_MESSAGES/
│   ├── fr/LC_MESSAGES/
│   └── django.pot               # Translation template
├── apps/
│   ├── articles/
│   │   ├── locale/             # App-specific
│   │   │   ├── es/LC_MESSAGES/
│   │   │   └── fr/LC_MESSAGES/
│   │   ├── models.py
│   │   └── views.py
```

### 18.2 File Types

| Extension | Type | Purpose |
|-----------|------|---------|
| .po | Text | Human-editable translations |
| .mo | Binary | Runtime translations (fast lookup) |
| .pot | Text | Translation template (generated) |

---

## 19. Django Version Support

| Feature | Version | Notes |
|---------|---------|-------|
| gettext_lazy | 1.0+ | Standard |
| TextChoices | 3.0+ | Recommended for choices |
| i18n_patterns | 1.0+ | URL localization |
| LocaleMiddleware | 1.0+ | Language detection |

---

## 20. Settings Reference

```python
# Core i18n settings
I18N = True                     # Enable translation system
USE_I18N = True                 # Enable translation lookups
USE_L10N = True                 # Localize format (dates, numbers)
USE_TZ = True                   # Use timezone-aware datetimes

# Language configuration
LANGUAGE_CODE = 'en-us'         # Default language
LANGUAGES = [                   # Supported languages
    ('en', _('English')),
]

# File locations
LOCALE_PATHS = [                # Where translation files live
    os.path.join(BASE_DIR, 'locale'),
]

# Time/date formatting
TIME_ZONE = 'UTC'               # Server timezone
DATE_FORMAT = 'N j, Y'          # How to format dates
TIME_FORMAT = 'P'               # How to format times
```

---

## 21. Function Reference

### 21.1 Translation Functions

| Function | Module | Returns | Use |
|----------|--------|---------|-----|
| `gettext(msg)` | django.utils.translation | str | Runtime translation |
| `gettext_lazy(msg)` | django.utils.translation | lazy | Module-level translation |
| `ngettext(sing, plur, n)` | django.utils.translation | str | Runtime pluralization |
| `ngettext_lazy(sing, plur, n)` | django.utils.translation | lazy | Module-level pluralization |
| `pgettext(ctx, msg)` | django.utils.translation | str | Runtime with context |
| `pgettext_lazy(ctx, msg)` | django.utils.translation | lazy | Module-level with context |

### 21.2 Language Functions

| Function | Purpose | Returns |
|----------|---------|---------|
| `activate(language)` | Set current language | None |
| `get_language()` | Get current language | str (code) |
| `override(language)` | Temporary language switch | context manager |

### 21.3 Template Tags

| Tag | Module | Purpose |
|-----|--------|---------|
| `{% load i18n %}` | django.templatetags.i18n | Load i18n tags |
| `{% trans %}` | django.templatetags.i18n | Translate string |
| `{% blocktrans %}` | django.templatetags.i18n | Translate block with vars |
| `{% pgettext %}` | django.templatetags.i18n | Context translation |
| `{% get_available_languages %}` | django.templatetags.i18n | Get LANGUAGES list |
| `{% get_current_language %}` | django.templatetags.i18n | Get current language |

---

## 22. Abbreviations and Terminology

| Term | Meaning |
|------|---------|
| i18n | Internationalization (18 letters removed from "internationalization") |
| l10n | Localization (10 letters removed from "localization") |
| .po | Portable Object (human-readable translation file) |
| .mo | Machine Object (compiled binary translation file) |
| .pot | Portable Object Template (translation template) |
| gettext | GNU translation system |
| msgid | Message ID (original string) |
| msgstr | Message string (translation) |

---

## 23. Exit Codes

Management commands:

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |

---

## 24. Locale Code Format

RFC 5646 language tags:

```
[language]-[SCRIPT]-[REGION]-[variant]

Examples:
en          English
en-US       English (United States)
en-GB       English (Great Britain)
zh-Hans     Chinese (Simplified)
zh-Hant     Chinese (Traditional)
pt-BR       Portuguese (Brazil)
pt-PT       Portuguese (Portugal)
```

Django format (simplified):
```
en          Language only
en-us       Language-Region
en_US       Alternative format (Django accepts both)
```

---

## 25. Default Django Locale Formats

When `USE_L10N = True`:

```python
DATE_FORMAT = 'N j, Y'           # Nov. 10, 2023
TIME_FORMAT = 'P'                # 10:30 p.m.
DATETIME_FORMAT = 'N j, Y, P'    # Nov. 10, 2023, 10:30 p.m.
YEAR_MONTH_FORMAT = 'F Y'        # November 2023
MONTH_DAY_FORMAT = 'F j'         # November 10
SHORT_DATE_FORMAT = 'm/d/Y'      # 11/10/2023
SHORT_DATETIME_FORMAT = 'm/d/Y P' # 11/10/2023 10:30 p.m.
FIRST_DAY_OF_WEEK = 0            # Sunday (0-6, Monday=1)
DECIMAL_SEPARATOR = '.'          # Thousands separator
THOUSAND_SEPARATOR = ','         # Decimal separator
```

Overrides per-locale if `USE_L10N = True`.

---

## 26. Command-Line Reference

```bash
# Extract all languages
python manage.py makemessages -a

# Extract specific language
python manage.py makemessages -l es

# Extract multiple languages
python manage.py makemessages -l es -l fr -l de

# Extract JavaScript only
python manage.py makemessages -d djangojs -a

# Verbose output
python manage.py makemessages -a --verbosity 2

# Compile translations
python manage.py compilemessages

# Compile verbose
python manage.py compilemessages --verbosity 2

# Set language for current shell
export LANGUAGE=es
```

---

## 27. Django Admin Integration

Admin automatically:
- Translates field labels (uses verbose_name)
- Translates field help text
- Translates choice labels (uses get_X_display)
- Localizes dates/numbers

No additional setup required.

---

