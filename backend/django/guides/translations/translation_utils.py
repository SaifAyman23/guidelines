"""
Django i18n Translation Utilities and Reusable Components

This module provides ready-to-use components for implementing translations
throughout your Django application. Use these as base classes and utilities
to ensure consistent i18n implementation.

Usage:
    from translation_utils import TranslatableModel, TranslationHelper, translate_in_language
    
    class Article(TranslatableModel):
        title = models.CharField(max_length=200)
"""

from django.db import models
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _lazy
from django.utils.translation import ngettext, ngettext_lazy
from django.utils.translation import pgettext, pgettext_lazy
from django.utils.translation import activate, get_language, override
from django.utils import timezone
from django.core.exceptions import ValidationError
from functools import wraps
from datetime import timedelta


# ============================================================================
# ABSTRACT BASE MODELS
# ============================================================================

class TranslatableModel(models.Model):
    """
    Abstract base model with translatable timestamp fields.
    
    Provides: created_at, updated_at with translated verbose names.
    
    Usage:
        class Article(TranslatableModel):
            title = models.CharField(max_length=200, verbose_name=_lazy("Title"))
    """
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_lazy("Created at")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_lazy("Updated at")
    )
    
    class Meta:
        abstract = True
        ordering = ['-created_at']


class PublishableModel(TranslatableModel):
    """
    Abstract base for publishable content with status and publication date.
    
    Provides: status, published_at with full i18n support.
    
    Includes methods: publish(), archive(), is_published()
    
    Usage:
        class Article(PublishableModel):
            title = models.CharField(max_length=200)
    """
    
    class Status(models.TextChoices):
        """Publication status choices."""
        DRAFT = 'draft', _lazy('Draft')
        REVIEW = 'review', _lazy('Under Review')
        PUBLISHED = 'published', _lazy('Published')
        ARCHIVED = 'archived', _lazy('Archived')
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name=_lazy("Status")
    )
    
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_lazy("Published at")
    )
    
    class Meta:
        abstract = True
    
    def publish(self):
        """
        Publish this item. Returns (success, message) tuple.
        
        Returns:
            tuple: (bool, str) - (success, translated_message)
        """
        if self.status != self.Status.DRAFT:
            return False, _('Only draft items can be published.')
        
        self.status = self.Status.PUBLISHED
        self.published_at = timezone.now()
        self.save()
        return True, _('Published successfully.')
    
    def archive(self):
        """Archive this item. Returns (success, message) tuple."""
        if self.status == self.Status.ARCHIVED:
            return False, _('Item is already archived.')
        
        self.status = self.Status.ARCHIVED
        self.save()
        return True, _('Archived successfully.')
    
    def is_published(self):
        """Check if item is published and not in the future."""
        return (self.status == self.Status.PUBLISHED and 
                self.published_at and 
                self.published_at <= timezone.now())


class SoftDeleteModel(models.Model):
    """
    Abstract base for soft-delete functionality with translation.
    
    Provides: is_deleted, deleted_at fields. Objects are never actually
    deleted from the database, just marked as deleted.
    
    Usage:
        class Article(SoftDeleteModel):
            title = models.CharField(max_length=200)
        
        article.soft_delete()  # Marks as deleted
        Article.objects.filter(is_deleted=False)  # Get active items
    """
    is_deleted = models.BooleanField(
        default=False,
        verbose_name=_lazy("Deleted")
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_lazy("Deleted at")
    )
    
    class Meta:
        abstract = True
    
    def soft_delete(self):
        """Mark as deleted without removing from database."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
        return True, _('Item deleted successfully.')
    
    def restore(self):
        """Restore a soft-deleted item."""
        if not self.is_deleted:
            return False, _('Item is not deleted.')
        
        self.is_deleted = False
        self.deleted_at = None
        self.save()
        return True, _('Item restored successfully.')


# ============================================================================
# DECORATORS
# ============================================================================

def translate_in_language(language_code):
    """
    Decorator to execute a function in a specific language context.
    
    Usage:
        @translate_in_language('es')
        def get_spanish_status():
            return str(Article.Status.DRAFT)
    
    Args:
        language_code (str): Language code (e.g., 'es', 'fr', 'de')
    
    Returns:
        function: Decorated function
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


def requires_i18n(func):
    """
    Decorator to ensure i18n is properly initialized before function execution.
    
    Useful for management commands and tasks that rely on translations.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not timezone.is_aware(timezone.now()):
            raise RuntimeError(_('Django i18n not properly initialized.'))
        return func(*args, **kwargs)
    return wrapper


# ============================================================================
# TRANSLATION HELPERS
# ============================================================================

class TranslationHelper:
    """
    Utility class with common translation helper methods.
    
    Usage:
        helper = TranslationHelper()
        display = helper.get_choice_display(Article, 'status', 'published', 'es')
    """
    
    @staticmethod
    def get_choice_display(model, field_name, value, language='en'):
        """
        Get translated display value for a model choice field.
        
        Args:
            model: Django model class
            field_name (str): Name of the field with choices
            value: Choice value to translate
            language (str): Language code (default: 'en')
        
        Returns:
            str: Translated choice label
        
        Example:
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
        Get a text translated in all configured languages.
        
        Args:
            text (str): Text to translate (should be already translated with _())
        
        Returns:
            dict: {language_code: translated_text}
        
        Example:
            translations = TranslationHelper.get_all_languages_display(_('Welcome'))
            # Returns {'en': 'Welcome', 'es': 'Bienvenido', ...}
        """
        from django.conf import settings
        translations = {}
        for code, name in settings.LANGUAGES:
            with override(code):
                translations[code] = str(text)
        return translations
    
    @staticmethod
    def get_verbose_name(model, language='en'):
        """Get translated model name."""
        with override(language):
            return str(model._meta.verbose_name)
    
    @staticmethod
    def get_verbose_name_plural(model, language='en'):
        """Get translated plural model name."""
        with override(language):
            return str(model._meta.verbose_name_plural)


# ============================================================================
# CONTEXT MANAGERS
# ============================================================================

class TranslationContext:
    """
    Context manager for temporary language switching.
    
    Usage:
        with TranslationContext('es'):
            message = str(_('Welcome'))  # Spanish
        # Automatically reverts to previous language
    """
    
    def __init__(self, language_code):
        self.language_code = language_code
        self.previous_language = None
    
    def __enter__(self):
        self.previous_language = get_language()
        activate(self.language_code)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        activate(self.previous_language)
        return False


# ============================================================================
# DECORATORS
# ============================================================================

def translate_in_language(language_code):
    """
    Decorator to execute function in specific language context.
    
    Usage:
        @translate_in_language('es')
        def get_spanish_status():
            return str(Article.Status.DRAFT)
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


def ensure_i18n(func):
    """
    Decorator to ensure i18n is properly initialized.
    
    Raises RuntimeError if Django i18n is not ready.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            current = get_language()
            if not current:
                raise RuntimeError(_('Django i18n not properly initialized.'))
        except Exception as e:
            raise RuntimeError(
                _('i18n initialization error: %(error)s') % {'error': str(e)}
            )
        return func(*args, **kwargs)
    return wrapper


# ============================================================================
# VALIDATORS FOR TRANSLATIONS
# ============================================================================

def validate_translation_completeness(model_class):
    """
    Validate that a model has all required translated fields.
    
    Usage:
        errors = validate_translation_completeness(Article)
        if errors:
            print("Missing translations:", errors)
    
    Returns:
        list: List of error messages
    """
    errors = []
    
    # Check verbose names
    if not model_class._meta.verbose_name:
        errors.append(f"{model_class.__name__}: Missing verbose_name")
    
    # Check field verbose names
    for field in model_class._meta.get_fields():
        if hasattr(field, 'verbose_name') and not field.verbose_name:
            errors.append(
                f"{model_class.__name__}.{field.name}: Missing verbose_name"
            )
    
    # Check choices
    for field in model_class._meta.get_fields():
        if hasattr(field, 'choices') and field.choices:
            for value, label in field.choices:
                # Check if label is translatable (lazy)
                if isinstance(label, str) and not hasattr(label, '_proxy____args'):
                    errors.append(
                        f"{model_class.__name__}.{field.name}: "
                        f'Choice "{value}" not wrapped with _()'
                    )
    
    return errors


# ============================================================================
# FORM MIXINS
# ============================================================================

class TranslatableFormMixin:
    """
    Mixin to add consistent translated error messages to forms.
    
    Usage:
        class ArticleForm(TranslatableFormMixin, forms.ModelForm):
            class Meta:
                model = Article
                fields = ['title', 'content']
    """
    
    default_error_messages = {
        'required': _('This field is required.'),
        'invalid': _('Enter a valid value.'),
        'null': _('This field cannot be null.'),
        'blank': _('This field cannot be blank.'),
    }
    
    def __init__(self, *args, **kwargs):
        """Apply translated error messages to all fields."""
        super().__init__(*args, **kwargs)
        
        for field in self.fields.values():
            if not hasattr(field, 'error_messages'):
                continue
            
            # Merge default translated messages with field-specific ones
            messages_dict = self.default_error_messages.copy()
            messages_dict.update(field.error_messages)
            field.error_messages = messages_dict


class ValidatedFormMixin:
    """
    Mixin for enhanced form validation with better error handling.
    
    Usage:
        class ArticleForm(ValidatedFormMixin, forms.ModelForm):
            class Meta:
                model = Article
                fields = ['title']
    """
    
    def full_clean(self):
        """Override to catch validation errors."""
        try:
            super().full_clean()
        except ValidationError as e:
            # Wrap validation errors with friendly message
            if self.non_field_errors():
                pass  # Non-field errors already added
            else:
                self.add_error(None, _('Please correct the errors below.'))
    
    def get_field_error_messages(self):
        """Get all field error messages as translatable strings."""
        errors = {}
        for field_name, error_list in self.errors.items():
            if field_name != '__all__':
                errors[field_name] = ' '.join(str(e) for e in error_list)
        return errors


# ============================================================================
# QUERY HELPERS
# ============================================================================

class TranslationQueryHelper:
    """
    Helper methods for querying models with translated fields.
    
    Usage:
        articles = TranslationQueryHelper.get_published(Article)
    """
    
    @staticmethod
    def get_published(model_class):
        """
        Get published instances (assumes Status.PUBLISHED field).
        """
        if not hasattr(model_class, 'Status'):
            raise AttributeError(
                f'{model_class.__name__} does not have Status choices'
            )
        
        return model_class.objects.filter(
            status=model_class.Status.PUBLISHED
        )
    
    @staticmethod
    def get_by_status(model_class, status_value):
        """
        Get instances by status value.
        
        Usage:
            drafts = TranslationQueryHelper.get_by_status(Article, 'draft')
        """
        return model_class.objects.filter(status=status_value)
    
    @staticmethod
    def get_recent(model_class, days=7):
        """
        Get recently created instances.
        
        Usage:
            recent = TranslationQueryHelper.get_recent(Article, 7)
        """
        cutoff = timezone.now() - timedelta(days=days)
        return model_class.objects.filter(created_at__gte=cutoff)


# ============================================================================
# EMAIL AND NOTIFICATION HELPERS
# ============================================================================

class TranslatedEmailHelper:
    """
    Helper for sending translated emails.
    
    Usage:
        helper = TranslatedEmailHelper()
        helper.send_welcome_email(user, language='es')
    """
    
    @staticmethod
    def send_email(
        subject,
        message,
        recipient_list,
        language='en',
        from_email=None,
        fail_silently=False
    ):
        """
        Send email with translated subject and body.
        
        Args:
            subject: Translatable subject string
            message: Translatable message string
            recipient_list: List of email addresses
            language: Language code
            from_email: Sender email
            fail_silently: Suppress exceptions
        """
        from django.core.mail import send_mail
        from django.conf import settings
        
        from_email = from_email or settings.DEFAULT_FROM_EMAIL
        
        with override(language):
            translated_subject = str(subject)
            translated_message = str(message)
        
        return send_mail(
            translated_subject,
            translated_message,
            from_email,
            recipient_list,
            fail_silently=fail_silently
        )
    
    @staticmethod
    def send_multi_language_email(
        subject,
        message,
        user_language_map,
        from_email=None,
        fail_silently=False
    ):
        """
        Send same email to multiple users in their preferred languages.
        
        Args:
            subject: Translatable subject
            message: Translatable message
            user_language_map: Dict of {email: language_code}
            from_email: Sender email
            fail_silently: Suppress exceptions
        
        Usage:
            map = {'user1@example.com': 'es', 'user2@example.com': 'en'}
            TranslatedEmailHelper.send_multi_language_email(
                _('Welcome!'),
                _('Thanks for joining'),
                map
            )
        """
        from django.core.mail import send_mail
        from django.conf import settings
        
        from_email = from_email or settings.DEFAULT_FROM_EMAIL
        
        for email, language_code in user_language_map.items():
            with override(language_code):
                translated_subject = str(subject)
                translated_message = str(message)
            
            send_mail(
                translated_subject,
                translated_message,
                from_email,
                [email],
                fail_silently=fail_silently
            )


# ============================================================================
# TESTING HELPERS
# ============================================================================

class TranslationTestHelper:
    """
    Helper methods for testing translations.
    
    Usage:
        helper = TranslationTestHelper()
        helper.assert_all_fields_translatable(Article)
    """
    
    @staticmethod
    def assert_translatable_in_all_languages(text, testcase):
        """
        Assert that a translatable string works in all configured languages.
        
        Usage:
            helper.assert_translatable_in_all_languages(_('Welcome'), self)
        """
        from django.conf import settings
        
        for code, name in settings.LANGUAGES:
            with override(code):
                translated = str(text)
                testcase.assertIsInstance(
                    translated, str,
                    f"Translation failed for language {code}"
                )
                testcase.assertGreater(
                    len(translated), 0,
                    f"Empty translation for language {code}"
                )
    
    @staticmethod
    def assert_all_model_fields_translatable(model_class, testcase):
        """
        Assert that all model fields have translatable verbose names.
        
        Usage:
            helper.assert_all_model_fields_translatable(Article, self)
        """
        for field in model_class._meta.get_fields():
            if hasattr(field, 'verbose_name'):
                testcase.assertTrue(
                    hasattr(field.verbose_name, '_proxy____args') or
                    isinstance(field.verbose_name, str),
                    f"Field {field.name} verbose_name not translatable"
                )
    
    @staticmethod
    def assert_choice_labels_translatable(model_class, testcase):
        """
        Assert that all choice labels are translatable.
        
        Usage:
            helper.assert_choice_labels_translatable(Article, self)
        """
        for field in model_class._meta.get_fields():
            if hasattr(field, 'choices') and field.choices:
                for value, label in field.choices:
                    testcase.assertTrue(
                        hasattr(label, '_proxy____args') or 
                        callable(label) or
                        isinstance(label, str),
                        f"Choice label '{label}' for {field.name} not translatable"
                    )


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

"""
EXAMPLE: Using these utilities in your Django project

# models.py
from translation_utils import PublishableModel, TranslatableModel

class Article(PublishableModel):
    '''Article with translation support.'''
    title = models.CharField(max_length=200, verbose_name=_("Title"))
    content = models.TextField(verbose_name=_("Content"))

# forms.py
from translation_utils import TranslatableFormMixin, ValidatedFormMixin

class ArticleForm(TranslatableFormMixin, ValidatedFormMixin, forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'content']

# views.py
from translation_utils import translate_in_language, TranslationHelper

class ArticleListView(ListView):
    model = Article
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['languages'] = TranslationHelper.get_all_languages_display(
            _('Articles')
        )
        return context

# tasks.py
from translation_utils import TranslationContext

@shared_task
def send_notification(user_id, language='en'):
    with TranslationContext(language):
        user = User.objects.get(id=user_id)
        subject = _('Welcome to our site')
        send_mail(subject, ...)

# tests.py
from translation_utils import TranslationTestHelper

class ArticleTranslationTests(TestCase):
    def test_translations_complete(self):
        helper = TranslationTestHelper()
        helper.assert_all_model_fields_translatable(Article, self)
        helper.assert_choice_labels_translatable(Article, self)
"""
