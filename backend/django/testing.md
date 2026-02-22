# Django Testing Guidelines

## Table of Contents
- [Overview](#overview)
- [Test Structure](#test-structure)
- [Unit Tests](#unit-tests)
- [Integration Tests](#integration-tests)
- [Test-Driven Development (TDD)](#test-driven-development-tdd)
- [Fixtures and Factories](#fixtures-and-factories)
- [Mocking](#mocking)
- [API Testing](#api-testing)
- [Test Coverage](#test-coverage)
- [Performance Testing](#performance-testing)
- [Best Practices](#best-practices)

---

## Overview

Testing is not optional — it is the backbone of any production-ready Django application. A well-tested codebase gives you confidence to refactor, add features, and deploy without fear of silent regressions. Django provides a comprehensive testing framework built directly on Python's built-in `unittest` library, extended with database helpers, a test client for simulating HTTP requests, and seamless integration with Django REST Framework.

**Why tests matter:**
- They act as living documentation of expected behavior.
- They catch bugs before they reach production.
- They make refactoring safe by verifying that nothing breaks.
- They enforce clean, modular code — tightly coupled code is hard to test.

**Types of tests in Django:**

| Type | Purpose | Speed |
|---|---|---|
| Unit | Test a single class or function in isolation | Very fast |
| Integration | Test multiple components working together | Moderate |
| API / Functional | Test HTTP endpoints end-to-end | Slower |
| Performance | Measure response time and query counts | Slow |

**Running your tests:**

```bash
# Run all tests across the entire project
python manage.py test

# Run tests for a specific app
python manage.py test myapp

# Run a specific test module
python manage.py test myapp.tests.test_models

# Run a specific test class
python manage.py test myapp.tests.test_models.ArticleModelTest

# Run a single test method
python manage.py test myapp.tests.test_models.ArticleModelTest.test_article_creation

# Run tests with verbose output (shows each test name as it runs)
python manage.py test --verbosity=2

# Run tests in parallel to speed up large test suites
python manage.py test --parallel

# Stop on first failure (useful during debugging)
python manage.py test --failfast

# Keep the test database between runs (speeds up subsequent runs)
python manage.py test --keepdb
```

---

## Test Structure

### Directory Structure

Organizing tests into a dedicated `tests/` package (rather than a single `tests.py` file) is strongly recommended for any non-trivial app. This makes it easy to find relevant tests and keeps individual files focused and manageable.

```
myapp/
├── tests/
│   ├── __init__.py          # Makes the folder a Python package
│   ├── test_models.py       # Unit tests for models and managers
│   ├── test_views.py        # Tests for Django HTML views
│   ├── test_serializers.py  # Tests for DRF serializers
│   ├── test_forms.py        # Tests for Django forms
│   ├── test_api.py          # Tests for REST API endpoints
│   ├── test_utils.py        # Tests for utility functions
│   ├── factories.py         # Factory Boy factory definitions
│   └── fixtures/
│       ├── users.json       # JSON fixture for user data
│       └── articles.json    # JSON fixture for article data
├── models.py
├── views.py
└── serializers.py
```

> **Tip:** Keep one test file per source file. If `models.py` has 3 models, `test_models.py` should have a test class for each.

### Choosing the Right Test Base Class

Django provides several base classes depending on what you need to test:

| Base Class | Use When |
|---|---|
| `TestCase` | Most tests — wraps each test in a transaction that rolls back automatically |
| `TransactionTestCase` | Testing transaction behavior, signals, or multi-db scenarios |
| `SimpleTestCase` | No database access needed (pure logic, forms) |
| `LiveServerTestCase` | Selenium/browser-based tests |
| `APITestCase` (DRF) | Testing REST API endpoints |

### Basic Test Class

The `setUp` method runs before every single test method. Use it to create the objects each test will need. The `tearDown` method runs after each test — usually you don't need it since `TestCase` rolls back the database automatically.

```python
from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class BasicTestCase(TestCase):
    """
    A basic test case demonstrating setUp, tearDown, and a simple assertion.
    Inheriting from django.test.TestCase ensures each test runs inside a
    database transaction that is rolled back afterwards, so tests are isolated.
    """

    def setUp(self):
        """
        Called before each test method in this class.
        Use this to create objects your tests will work with.
        Avoid putting data here that tests won't modify — use setUpTestData instead.
        """
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def tearDown(self):
        """
        Called after each test method. Since TestCase wraps tests in transactions,
        you rarely need to clean up manually. Override only for non-database resources
        like temporary files or patched settings.
        """
        pass

    def test_user_creation(self):
        """Test that the user was created with the correct attributes."""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        # check_password hashes the password internally — never compare raw strings
        self.assertTrue(self.user.check_password('testpass123'))
```

---

## Unit Tests

Unit tests verify the smallest possible pieces of your code in isolation — a single model method, a form field, a utility function. They should be fast (no network, minimal DB), independent, and highly specific.

### Model Tests

Model tests verify field behavior, custom methods, `__str__` representations, ordering, and custom managers. Use `setUpTestData` (a classmethod) for data that is shared across all tests in the class and won't be modified — it's created once and is significantly faster than `setUp`.

```python
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from myapp.models import Article, Category

class ArticleModelTest(TestCase):
    """
    Tests for the Article model.

    Uses setUpTestData for shared read-only objects (user, category) and
    setUp for the article itself since some tests will modify it.
    """

    @classmethod
    def setUpTestData(cls):
        """
        Create data once for the entire TestCase class.
        This runs once before any test in the class, wrapped in a transaction.
        Data created here is shared (read-only) across all test methods.
        Use for objects that tests will never modify.
        """
        cls.category = Category.objects.create(
            name='Technology',
            slug='technology'
        )
        cls.user = User.objects.create_user(
            username='author',
            email='author@example.com',
            password='password123'
        )

    def setUp(self):
        """
        Create a fresh Article for each test method.
        We create the article here (not in setUpTestData) because some tests
        will modify or delete it, and we need a clean copy each time.
        """
        self.article = Article.objects.create(
            title='Test Article',
            slug='test-article',
            content='Test content',
            author=self.user,
            category=self.category
        )

    def test_article_creation(self):
        """Test that an article is persisted with all the correct field values."""
        self.assertEqual(self.article.title, 'Test Article')
        self.assertEqual(self.article.slug, 'test-article')
        self.assertEqual(self.article.author, self.user)
        # Verify the auto-generated timestamp is a proper datetime
        self.assertIsInstance(self.article.created_at, timezone.datetime)

    def test_article_str_representation(self):
        """Test that the __str__ method returns the article title."""
        self.assertEqual(str(self.article), 'Test Article')

    def test_article_absolute_url(self):
        """
        Test get_absolute_url returns the correct path.
        This is important for templates and sitemaps.
        """
        expected_url = f'/articles/{self.article.slug}/'
        self.assertEqual(self.article.get_absolute_url(), expected_url)

    def test_article_slug_unique(self):
        """
        Test that the unique constraint on slug is enforced.
        We call full_clean() because Django's unique validation runs at the
        model validation level, not always at the database level in tests.
        """
        with self.assertRaises(ValidationError):
            duplicate = Article(
                title='Another Article',
                slug='test-article',  # Same slug as the article in setUp
                content='Content',
                author=self.user,
                category=self.category
            )
            duplicate.full_clean()  # Triggers model-level validators

    def test_article_ordering(self):
        """
        Test that articles are returned newest-first (descending by created_at).
        This validates the Meta.ordering setting on the model.
        """
        article2 = Article.objects.create(
            title='Second Article',
            slug='second-article',
            content='Content',
            author=self.user,
            category=self.category
        )
        articles = Article.objects.all()
        # The most recently created article should appear first
        self.assertEqual(articles[0], article2)
        self.assertEqual(articles[1], self.article)

    def test_article_published_manager(self):
        """
        Test that a custom Published manager returns only articles with
        status='published', filtering out drafts and archived articles.
        """
        self.article.status = 'draft'
        self.article.save()

        published = Article.objects.create(
            title='Published Article',
            slug='published-article',
            content='Content',
            author=self.user,
            category=self.category,
            status='published'
        )

        published_articles = Article.published.all()
        self.assertEqual(published_articles.count(), 1)
        self.assertEqual(published_articles[0], published)
```

### Manager and QuerySet Tests

Custom managers and QuerySet methods deserve their own test class. These are often the most query-heavy part of your app.

```python
from django.test import TestCase
from myapp.models import Article

class ArticleManagerTest(TestCase):
    """
    Tests for Article's custom manager methods.
    Separating manager tests from general model tests keeps files focused.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='password123'
        )
        # Create one published and one draft to test filtering
        self.published = Article.objects.create(
            title='Published',
            slug='published',
            content='Content',
            author=self.user,
            status='published'
        )
        self.draft = Article.objects.create(
            title='Draft',
            slug='draft',
            content='Content',
            author=self.user,
            status='draft'
        )

    def test_published_manager(self):
        """Test that Article.published only returns status='published' articles."""
        published_articles = Article.published.all()
        self.assertEqual(published_articles.count(), 1)
        self.assertEqual(published_articles[0], self.published)
        # Confirm draft is excluded
        self.assertNotIn(self.draft, published_articles)

    def test_by_author_method(self):
        """Test the by_author() queryset method returns all articles by the given user."""
        articles = Article.objects.by_author(self.user)
        self.assertEqual(articles.count(), 2)

    def test_search_method(self):
        """
        Test the search() method performs a case-insensitive title/content search
        and returns only matching results.
        """
        articles = Article.objects.search('Published')
        self.assertEqual(articles.count(), 1)
        self.assertEqual(articles[0], self.published)
```

### Form Tests

Form tests verify validation logic, custom clean methods, and that forms save data correctly.

```python
from django.test import TestCase
from myapp.forms import ArticleForm

class ArticleFormTest(TestCase):
    """
    Tests for ArticleForm.
    Form tests do not hit the database unless the form's save() method is called.
    """

    def test_valid_form(self):
        """Test that a form with all required fields is valid."""
        form_data = {
            'title': 'Test Article',
            'slug': 'test-article',
            'content': 'Test content',
            'status': 'draft',
        }
        form = ArticleForm(data=form_data)
        self.assertTrue(form.is_valid(), msg=form.errors)

    def test_invalid_form_missing_title(self):
        """
        Test that omitting the required 'title' field makes the form invalid
        and adds an error specifically on the 'title' field.
        """
        form_data = {
            'slug': 'test-article',
            'content': 'Test content',
            # 'title' is intentionally missing
        }
        form = ArticleForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_form_slug_validation(self):
        """
        Test that a slug with special characters (spaces, punctuation) is rejected.
        Slugs must match URL-safe patterns: lowercase letters, numbers, and hyphens only.
        """
        form_data = {
            'title': 'Test Article',
            'slug': 'invalid slug!',  # Contains a space and exclamation mark
            'content': 'Test content',
        }
        form = ArticleForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('slug', form.errors)

    def test_form_save(self):
        """
        Test that form.save() persists data to the database correctly.
        We use commit=False so we can attach a required author before saving.
        """
        form_data = {
            'title': 'Test Article',
            'slug': 'test-article',
            'content': 'Test content',
            'status': 'draft',
        }
        form = ArticleForm(data=form_data)
        self.assertTrue(form.is_valid())

        # commit=False gives us the unsaved instance so we can add required FK fields
        article = form.save(commit=False)
        article.author = User.objects.create_user(
            username='testuser',
            password='password123'
        )
        article.save()

        self.assertEqual(Article.objects.count(), 1)
        self.assertEqual(article.title, 'Test Article')
```

### View Tests

View tests verify that each URL returns the right status code, the right template, and the right context data. Django's built-in test `Client` simulates HTTP requests without a real server.

```python
from django.test import TestCase, Client
from django.urls import reverse
from myapp.models import Article

class ArticleViewTest(TestCase):
    """
    Tests for Article HTML views using Django's test Client.
    The test Client lets you simulate GET and POST requests and inspect
    the response's status code, template, and context.
    """

    def setUp(self):
        # Use Django's built-in test Client — no server needed
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='password123'
        )
        self.article = Article.objects.create(
            title='Test Article',
            slug='test-article',
            content='Test content',
            author=self.user,
            status='published'
        )

    def test_article_list_view(self):
        """
        GET /articles/ should return 200, render the list template,
        and display the article title in the response HTML.
        """
        url = reverse('article-list')  # Always use reverse() — never hardcode URLs
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Article')  # Checks HTML body
        self.assertTemplateUsed(response, 'articles/list.html')

    def test_article_detail_view(self):
        """
        GET /articles/<slug>/ should return 200, display the article's
        title and content, and pass the article object in context.
        """
        url = reverse('article-detail', kwargs={'slug': self.article.slug})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.article.title)
        self.assertContains(response, self.article.content)
        # Verify the correct article object is in the template context
        self.assertEqual(response.context['article'], self.article)

    def test_article_create_view_requires_login(self):
        """
        Unauthenticated users should be redirected away from the create view.
        Django's LoginRequiredMixin returns a 302 redirect to the login page.
        """
        url = reverse('article-create')
        response = self.client.get(url)

        # 302 = redirect (to login page)
        self.assertEqual(response.status_code, 302)
        # Optionally assert the redirect goes to the login URL
        self.assertRedirects(response, f'/accounts/login/?next={url}')

    def test_article_create_view_logged_in(self):
        """Authenticated users should be able to access the create form."""
        self.client.login(username='testuser', password='password123')
        url = reverse('article-create')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'articles/form.html')

    def test_article_create_post(self):
        """
        A valid POST to the create view should create a new Article in the database
        and assign the logged-in user as its author.
        """
        self.client.login(username='testuser', password='password123')
        url = reverse('article-create')
        data = {
            'title': 'New Article',
            'slug': 'new-article',
            'content': 'New content',
            'status': 'draft',
        }
        response = self.client.post(url, data)

        # Confirm new article exists in the database
        self.assertEqual(Article.objects.count(), 2)
        new_article = Article.objects.get(slug='new-article')
        self.assertEqual(new_article.title, 'New Article')
        # Confirm the author is automatically set to the logged-in user
        self.assertEqual(new_article.author, self.user)

    def test_article_update_view(self):
        """
        A valid POST to the update view should change the article's title.
        We use refresh_from_db() to reload the object from the database
        to confirm the change was persisted.
        """
        self.client.login(username='testuser', password='password123')
        url = reverse('article-update', kwargs={'slug': self.article.slug})
        data = {
            'title': 'Updated Title',
            'slug': self.article.slug,
            'content': self.article.content,
            'status': self.article.status,
        }
        response = self.client.post(url, data)

        # Reload the article from the database to see the saved changes
        self.article.refresh_from_db()
        self.assertEqual(self.article.title, 'Updated Title')

    def test_article_delete_view(self):
        """
        A POST to the delete view should remove the article and redirect
        the user back to the article list.
        """
        self.client.login(username='testuser', password='password123')
        url = reverse('article-delete', kwargs={'slug': self.article.slug})
        response = self.client.post(url)

        self.assertEqual(Article.objects.count(), 0)
        self.assertRedirects(response, reverse('article-list'))
```

---

## Integration Tests

Integration tests verify that multiple components — models, views, signals, tasks — work correctly together. They are broader than unit tests and are particularly valuable for testing workflows.

### TransactionTestCase

Use `TransactionTestCase` instead of `TestCase` when you need to test actual database transactions, signals that depend on commits, or Celery tasks that hit the DB. It's slower because it truncates the database between tests (rather than rolling back).

```python
from django.test import TransactionTestCase
from myapp.models import Article
from myapp.tasks import process_article

class ArticleIntegrationTest(TransactionTestCase):
    """
    Integration tests for the article processing workflow.
    TransactionTestCase is used here because process_article() uses
    database transactions internally that TestCase would interfere with.
    """

    def test_article_processing_workflow(self):
        """
        Test the complete lifecycle: create a draft article, run the processing
        task, and confirm the article is published with correct metadata.
        """
        user = User.objects.create_user(
            username='testuser',
            password='password123'
        )

        # Start with a draft article
        article = Article.objects.create(
            title='Test Article',
            slug='test-article',
            content='Test content',
            author=user,
            status='draft'
        )

        # Simulate the processing workflow (e.g., content moderation + auto-publish)
        result = process_article(article.id)

        # Reload from DB and verify the article was updated
        article.refresh_from_db()
        self.assertEqual(article.status, 'published')
        self.assertTrue(result['success'])
```

### Database Integration Tests

Use `CaptureQueriesContext` to assert the exact number of queries a code path makes. This is the most reliable way to catch N+1 query regressions.

```python
from django.test import TestCase
from django.db import connection
from django.test.utils import CaptureQueriesContext

class DatabaseIntegrationTest(TestCase):
    """
    Tests that verify database query behavior.
    Query count tests prevent N+1 regressions from creeping into querysets.
    """

    def test_query_optimization(self):
        """
        Verify that fetching 10 articles with their authors uses select_related
        and does NOT generate an extra query per article (N+1 problem).
        Without select_related, 10 articles = 11 queries (1 + 10 author lookups).
        With select_related, it should be just 1-2 queries total.
        """
        user = User.objects.create_user(
            username='testuser',
            password='password123'
        )
        for i in range(10):
            Article.objects.create(
                title=f'Article {i}',
                slug=f'article-{i}',
                content='Content',
                author=user
            )

        # CaptureQueriesContext records every SQL query made inside the block
        with CaptureQueriesContext(connection) as context:
            # select_related('author') JOINs the author table in a single query
            articles = list(Article.objects.select_related('author').all())

        # If select_related is working, this should be 1 query, definitely under 3
        self.assertLess(
            len(context.captured_queries),
            3,
            msg=f"Expected < 3 queries, got {len(context.captured_queries)}"
        )
```

---

## Test-Driven Development (TDD)

TDD is a discipline where you write a failing test before writing any application code. It forces you to think about the interface and expected behavior before implementation, and it guarantees 100% test coverage of the feature you're building.

**The TDD cycle — Red, Green, Refactor:**

1. **Red** — Write a test for the new feature. Run it. It should fail because the code doesn't exist yet.
2. **Green** — Write the minimum amount of code to make the test pass.
3. **Refactor** — Clean up the implementation without breaking the tests.

### TDD Example: Article Like Feature

```python
# ─────────────────────────────────────────────
# STEP 1: RED — Write the test first
# Running these tests now will raise AttributeError because Article has no like() method.
# ─────────────────────────────────────────────

class ArticleLikeFeatureTest(TestCase):
    """
    TDD example: tests for the article "like" feature.
    These tests are written before the feature exists.
    They define the expected interface and behavior.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='password123'
        )
        self.article = Article.objects.create(
            title='Test Article',
            slug='test-article',
            content='Content',
            author=self.user
        )

    def test_user_can_like_article(self):
        """A user should be able to like an article, adding them to article.likes."""
        self.article.like(self.user)  # This method doesn't exist yet — test will fail (RED)
        self.assertEqual(self.article.likes.count(), 1)
        self.assertIn(self.user, self.article.likes.all())

    def test_user_cannot_like_article_twice(self):
        """Liking an article twice should be idempotent — still only 1 like."""
        self.article.like(self.user)
        self.article.like(self.user)  # Second like — should be ignored
        self.assertEqual(self.article.likes.count(), 1)

    def test_user_can_unlike_article(self):
        """A user should be able to remove their like."""
        self.article.like(self.user)
        self.article.unlike(self.user)
        self.assertEqual(self.article.likes.count(), 0)


# ─────────────────────────────────────────────
# STEP 2: GREEN — Add the minimum implementation to make the tests pass
# Add this to models.py
# ─────────────────────────────────────────────

class Article(models.Model):
    # ... existing fields ...
    likes = models.ManyToManyField(
        User,
        related_name='liked_articles',
        blank=True
    )

    def like(self, user):
        """Add the given user to the article's likes. ManyToMany .add() is idempotent."""
        self.likes.add(user)  # add() won't create duplicates — safe to call multiple times

    def unlike(self, user):
        """Remove the given user from the article's likes."""
        self.likes.remove(user)

    def is_liked_by(self, user):
        """Return True if the given user has liked this article."""
        return self.likes.filter(id=user.id).exists()

# Run: python manage.py test myapp.tests.test_models.ArticleLikeFeatureTest
# All 3 tests should now pass (GREEN).


# ─────────────────────────────────────────────
# STEP 3: REFACTOR — Clean up without breaking tests
# No logic changes — just clarity improvements. Re-run tests to confirm still GREEN.
# ─────────────────────────────────────────────
```

### Red-Green-Refactor: Read Time Feature

```python
# ─────── RED ───────
def test_article_read_time(self):
    """
    Test that read_time returns the estimated reading time in minutes,
    based on an average speed of 200 words per minute.
    300 words / 200 wpm = 1.5 minutes, rounded to 2.
    """
    article = Article.objects.create(
        title='Test',
        slug='test',
        content='word ' * 300,  # 300 words
        author=self.user
    )
    self.assertEqual(article.read_time, 2)  # Fails — property doesn't exist yet


# ─────── GREEN ───────
# Add to models.py — minimum code to pass the test
class Article(models.Model):
    @property
    def read_time(self):
        """Estimated reading time in minutes (minimum 1)."""
        word_count = len(self.content.split())
        minutes = word_count / 200
        return max(1, round(minutes))


# ─────── REFACTOR ───────
# Improve clarity: extract the constant and add a companion property
class Article(models.Model):
    WORDS_PER_MINUTE = 200  # Industry-standard average reading speed

    @property
    def word_count(self):
        """Total number of words in the article's content."""
        return len(self.content.split())

    @property
    def read_time(self):
        """
        Estimated reading time in whole minutes.
        Minimum value is 1 minute even for very short articles.
        """
        minutes = self.word_count / self.WORDS_PER_MINUTE
        return max(1, round(minutes))
```

---

## Fixtures and Factories

Fixtures and factories are two different approaches to seeding test data. Fixtures are static JSON/YAML files; factories are dynamic Python objects that generate data programmatically.

### JSON Fixtures

Fixtures are a quick way to load fixed, predefined data into the test database. They are best for small, stable datasets (e.g., a handful of predefined categories).

```json
// tests/fixtures/users.json
// Load this in a test with: fixtures = ['users.json']
[
    {
        "model": "auth.user",
        "pk": 1,
        "fields": {
            "username": "testuser",
            "email": "test@example.com",
            "is_staff": false,
            "is_active": true,
            "password": "pbkdf2_sha256$..."  // Use a hashed password
        }
    }
]
```

```bash
# Create a fixture from existing data in your development database
python manage.py dumpdata myapp.article --indent 2 > myapp/tests/fixtures/articles.json

# Load a fixture manually (usually done automatically via the fixtures attribute)
python manage.py loaddata myapp/tests/fixtures/articles.json
```

```python
class ArticleWithFixturesTest(TestCase):
    """
    Test class that loads JSON fixtures before each test.
    Fixtures are loaded after the database is set up and before setUp() runs.
    All fixture data is automatically cleaned up between tests.
    """
    fixtures = ['users.json', 'articles.json']

    def test_fixture_data(self):
        """Verify that fixture data was loaded correctly."""
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Article.objects.count(), 5)
```

> **When to use fixtures vs. factories:** Fixtures are simple but brittle — if your model changes, you must update the JSON manually. Factories (below) are more flexible and self-maintaining.

### Factory Boy

Factory Boy is the preferred approach for generating dynamic test data. It respects model relationships, supports sequences for unique values, and makes creating variations of objects trivial.

```bash
# Install Factory Boy
pip install factory-boy
```

```python
# tests/factories.py
# Define factories here and import them in any test file.

import factory
from factory.django import DjangoModelFactory
from myapp.models import Article, Category

class UserFactory(DjangoModelFactory):
    """
    Factory for the User model.
    Calling UserFactory() creates a new user with a unique username and email.
    factory.Sequence guarantees uniqueness across all instances in a test run.
    """
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'user{n}')  # user0, user1, user2, ...
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    first_name = factory.Faker('first_name')   # Uses the Faker library for realistic data
    last_name = factory.Faker('last_name')
    is_active = True

class CategoryFactory(DjangoModelFactory):
    """Factory for Category model."""
    class Meta:
        model = Category

    name = factory.Sequence(lambda n: f'Category {n}')
    # LazyAttribute computes the value from other fields on the same object
    slug = factory.LazyAttribute(lambda obj: obj.name.lower().replace(' ', '-'))

class ArticleFactory(DjangoModelFactory):
    """
    Factory for Article model.
    SubFactory automatically creates a related object if one is not provided.
    """
    class Meta:
        model = Article

    title = factory.Sequence(lambda n: f'Article {n}')
    slug = factory.LazyAttribute(lambda obj: obj.title.lower().replace(' ', '-'))
    content = factory.Faker('text', max_nb_chars=1000)  # Generates realistic lorem ipsum
    author = factory.SubFactory(UserFactory)       # Creates a User automatically
    category = factory.SubFactory(CategoryFactory) # Creates a Category automatically
    status = 'published'

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        """
        post_generation hooks run after the object is created.
        This allows passing tags as a list: ArticleFactory(tags=[tag1, tag2])
        If no tags are provided, this does nothing.
        """
        if not create:
            return  # Do nothing in build (non-DB) mode
        if extracted:
            for tag in extracted:
                self.tags.add(tag)
```

```python
# Using factories in tests
from myapp.tests.factories import ArticleFactory, UserFactory

class ArticleFactoryTest(TestCase):
    """
    Demonstrates common factory usage patterns.
    Factories replace manual Article.objects.create() calls and handle
    all required related objects automatically.
    """

    def test_create_article_with_factory(self):
        """
        ArticleFactory() creates a fully valid article with an author and category.
        No need to manually create a User or Category first.
        """
        article = ArticleFactory()
        self.assertIsNotNone(article.id)       # Was saved to the DB
        self.assertIsNotNone(article.author)   # Author was auto-created
        self.assertEqual(article.status, 'published')

    def test_create_multiple_articles(self):
        """
        create_batch(n) creates n articles in a single call.
        Useful for testing pagination, filtering, and ordering.
        """
        articles = ArticleFactory.create_batch(5)
        self.assertEqual(len(articles), 5)
        self.assertEqual(Article.objects.count(), 5)

    def test_override_factory_attributes(self):
        """
        Pass keyword arguments to override any factory default.
        This lets you test specific scenarios without rewriting the factory.
        """
        user = UserFactory(username='specificuser')
        article = ArticleFactory(
            title='Specific Title',
            author=user,
            status='draft'   # Override the default 'published' status
        )
        self.assertEqual(article.title, 'Specific Title')
        self.assertEqual(article.author.username, 'specificuser')
        self.assertEqual(article.status, 'draft')
```

---

## Mocking

Mocking replaces real dependencies (external APIs, email services, Celery tasks, time functions) with controlled fakes during tests. This makes tests faster, more reliable, and independent of external services.

Python's built-in `unittest.mock` module provides everything you need.

### Mocking External Services

Use `@patch` to replace a real function or object with a `Mock` for the duration of the test. The mock is automatically restored after the test ends.

```python
from unittest.mock import patch, Mock
from django.test import TestCase
from myapp.services import ArticleService

class ArticleServiceTest(TestCase):
    """
    Tests for ArticleService using mocks to avoid real HTTP calls.
    Without mocking, tests would be slow, flaky (network-dependent), and would
    consume real API quotas.
    """

    @patch('myapp.services.requests.get')
    def test_fetch_external_data(self, mock_get):
        """
        Patch requests.get so no real HTTP request is made.
        The mock is injected as the first argument after self.
        """
        # Define what the fake response should look like
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'title': 'External Article',
            'content': 'External content'
        }
        mock_get.return_value = mock_response  # requests.get() now returns this mock

        service = ArticleService()
        result = service.fetch_external_article(123)

        self.assertEqual(result['title'], 'External Article')
        # Verify that requests.get was called with the correct URL
        mock_get.assert_called_once_with('https://api.example.com/articles/123')

    @patch('myapp.services.send_mail')
    def test_send_notification(self, mock_send_mail):
        """
        Patch Django's send_mail so no real email is sent during tests.
        We just verify our code called it with the right arguments.
        """
        article = ArticleFactory()

        service = ArticleService()
        service.send_publication_notification(article)

        # Assert send_mail was called exactly once
        mock_send_mail.assert_called_once()
        # Unpack the call arguments to verify content
        args, kwargs = mock_send_mail.call_args
        # args[1] is the email body — it should mention the article title
        self.assertIn(article.title, args[1])
```

### Mocking Time

Freeze time to test timestamp-dependent behavior without relying on the real clock.

```python
from unittest.mock import patch
from django.test import TestCase
from django.utils import timezone

class ArticleTimestampTest(TestCase):
    """
    Tests that verify timestamp behavior by freezing time.
    Without mocking timezone.now(), you can't reliably assert exact datetime values.
    """

    @patch('django.utils.timezone.now')
    def test_article_creation_timestamp(self, mock_now):
        """
        Patch timezone.now() to return a fixed datetime.
        This lets us assert the exact created_at value without flakiness.
        """
        fake_time = timezone.datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_now.return_value = fake_time

        article = ArticleFactory()

        self.assertEqual(article.created_at, fake_time)
```

### Mocking Celery Tasks

In most tests, you don't want Celery to actually run tasks asynchronously — you want to verify they were called, or run them synchronously to test their logic.

```python
from unittest.mock import patch
from django.test import TestCase
from myapp.tasks import process_article_task

class CeleryTaskTest(TestCase):
    """
    Two strategies for testing Celery tasks:
    1. Mock .delay() to verify the task is *triggered* without actually running it.
    2. Call the task function directly (synchronously) to test its *logic*.
    """

    @patch('myapp.tasks.process_article_task.delay')
    def test_task_is_triggered(self, mock_task):
        """
        Verify that publishing an article triggers the Celery task.
        We mock .delay() so the task doesn't actually run — we just confirm
        it was called with the correct argument.
        """
        article = ArticleFactory()

        # This action (e.g., in a signal or view) should call the task
        article.publish()

        # Confirm the task was dispatched with the correct article ID
        mock_task.assert_called_once_with(article.id)

    def test_task_logic(self):
        """
        Test the actual task function by calling it directly (synchronously).
        This skips the Celery broker entirely and tests the function's logic.
        """
        article = ArticleFactory(status='draft')

        # Call the task function directly — no broker, no async
        result = process_article_task(article.id)

        article.refresh_from_db()
        self.assertEqual(article.status, 'published')
        self.assertTrue(result['success'])
```

---

## API Testing

DRF provides `APITestCase` and `APIClient`, which extend Django's test client with JSON-aware request/response handling and convenient authentication helpers.

### DRF API Test Case

```python
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse

class ArticleAPITest(APITestCase):
    """
    Tests for the Article REST API.
    APITestCase sets self.client to an APIClient automatically.
    APIClient is like Django's test Client but with JSON support built in.
    """

    def setUp(self):
        # APIClient is already available as self.client via APITestCase
        self.user = UserFactory()
        self.article = ArticleFactory(author=self.user)

    def test_article_list(self):
        """
        GET /api/articles/ should return 200 and a paginated list.
        No authentication required for listing public articles.
        """
        url = reverse('api:article-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # For paginated responses, results are nested under 'results'
        self.assertEqual(len(response.data['results']), 1)

    def test_article_detail(self):
        """GET /api/articles/<pk>/ should return the article's data."""
        url = reverse('api:article-detail', kwargs={'pk': self.article.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.article.title)

    def test_create_article_unauthenticated(self):
        """
        Unauthenticated POST requests should be rejected with 401.
        This confirms the endpoint is properly protected.
        """
        url = reverse('api:article-list')
        data = {'title': 'New Article', 'content': 'New content'}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_article_authenticated(self):
        """
        Authenticated POST with valid data should create an article (201).
        force_authenticate() bypasses password checking — faster than login().
        Use format='json' to send data as a JSON body rather than form-encoded.
        """
        self.client.force_authenticate(user=self.user)
        url = reverse('api:article-list')
        data = {
            'title': 'New Article',
            'slug': 'new-article',
            'content': 'New content',
            'status': 'draft',
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Article.objects.count(), 2)
        self.assertEqual(response.data['title'], 'New Article')

    def test_update_article(self):
        """
        Authenticated PUT should update all fields and return 200.
        PUT requires all required fields; use PATCH for partial updates.
        """
        self.client.force_authenticate(user=self.user)
        url = reverse('api:article-detail', kwargs={'pk': self.article.pk})
        data = {
            'title': 'Updated Title',
            'slug': self.article.slug,
            'content': self.article.content,
            'status': self.article.status,
        }
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Reload from DB to confirm the update was persisted
        self.article.refresh_from_db()
        self.assertEqual(self.article.title, 'Updated Title')

    def test_delete_article(self):
        """Authenticated DELETE should remove the article and return 204 No Content."""
        self.client.force_authenticate(user=self.user)
        url = reverse('api:article-detail', kwargs={'pk': self.article.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Article.objects.count(), 0)

    def test_pagination(self):
        """
        Verify that the list endpoint paginates results.
        Create enough articles to exceed one page, then check page 1 has the right count.
        """
        ArticleFactory.create_batch(25)  # 25 new + 1 from setUp = 26 total
        url = reverse('api:article-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)   # Paginated response has 'results' key
        self.assertIn('count', response.data)     # And a total 'count'
        self.assertEqual(len(response.data['results']), 20)  # Default page size

    def test_filtering(self):
        """
        Verify that ?status=published filters articles by status.
        Only published articles should appear in the results.
        """
        ArticleFactory(status='draft')
        published = ArticleFactory(status='published')

        url = reverse('api:article-list')
        response = self.client.get(url, {'status': 'published'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], published.id)
```

### Testing API Permissions

Permission tests are among the most important API tests — they verify your security model.

```python
from rest_framework.test import APITestCase

class ArticlePermissionTest(APITestCase):
    """
    Tests for object-level permissions.
    These verify that only authorized users can modify specific articles.
    """

    def setUp(self):
        self.owner = UserFactory()
        self.other_user = UserFactory()            # Another regular user
        self.staff_user = UserFactory(is_staff=True)  # Admin/staff user
        self.article = ArticleFactory(author=self.owner)

    def test_owner_can_update(self):
        """The article's author should be able to edit their own article."""
        self.client.force_authenticate(user=self.owner)
        url = reverse('api:article-detail', kwargs={'pk': self.article.pk})
        response = self.client.patch(url, {'title': 'Updated'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_non_owner_cannot_update(self):
        """A different authenticated user should be forbidden from editing another's article."""
        self.client.force_authenticate(user=self.other_user)
        url = reverse('api:article-detail', kwargs={'pk': self.article.pk})
        response = self.client.patch(url, {'title': 'Hacked'})

        # 403 Forbidden — authenticated but not authorized
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_can_update(self):
        """Staff users should have elevated permissions to edit any article."""
        self.client.force_authenticate(user=self.staff_user)
        url = reverse('api:article-detail', kwargs={'pk': self.article.pk})
        response = self.client.patch(url, {'title': 'Staff Edit'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
```

---

## Test Coverage

Coverage measures what percentage of your source code is exercised by tests. Aim for 90%+ on critical business logic, though 100% is not always practical or meaningful.

### Installing and Running Coverage

```bash
# Install coverage
pip install coverage

# Run your test suite while tracking which lines are executed
coverage run --source='.' manage.py test

# Print a summary report in the terminal
coverage report

# Generate a full HTML report (open htmlcov/index.html in your browser)
coverage html
open htmlcov/index.html   # macOS
xdg-open htmlcov/index.html  # Linux

# Show which specific lines are NOT covered (the most useful flag)
coverage report --show-missing

# Fail the command if coverage drops below a threshold (useful in CI)
coverage report --fail-under=90
```

### Coverage Configuration

Create a `.coveragerc` file in your project root to exclude files that don't need coverage (migrations, test files themselves, settings).

```ini
# .coveragerc
[run]
source = .
# Skip files and directories that shouldn't be measured
omit =
    */migrations/*           # Auto-generated migration files
    */tests/*                # Test files themselves
    */venv/*                 # Virtual environment
    */virtualenv/*
    manage.py
    */settings/*             # Settings modules
    */wsgi.py
    */asgi.py

[report]
# Exclude specific lines or patterns from coverage counting
exclude_lines =
    pragma: no cover         # Mark individual lines to skip with # pragma: no cover
    def __repr__             # repr methods aren't usually worth testing
    raise AssertionError     # Defensive assertions
    raise NotImplementedError
    if __name__ == .__main__.:
    if settings.DEBUG        # Debug-only code
    if TYPE_CHECKING:        # Type annotation imports
```

```python
# Marking lines to skip in coverage reports
class Article(models.Model):
    def __repr__(self):  # pragma: no cover
        return f'<Article: {self.title}>'

    def legacy_method(self):  # pragma: no cover
        """Old method kept for backward compatibility — do not test."""
        pass
```

### Ensuring Critical Paths Are Tested

```python
class CoverageTest(TestCase):
    """Ensure every custom model method is exercised at least once."""

    def test_all_article_state_transitions(self):
        """
        Walk through all model methods that change state.
        This ensures no method is accidentally left untested.
        """
        article = ArticleFactory(status='draft')

        article.publish()
        self.assertEqual(article.status, 'published')
        self.assertTrue(article.is_published())

        article.unpublish()
        self.assertEqual(article.status, 'draft')

        article.archive()
        self.assertEqual(article.status, 'archived')

        # Test utility methods
        self.assertIsNotNone(article.get_related_articles())
```

---

## Performance Testing

Performance tests measure response time and query efficiency. They should not be your primary test focus, but they are invaluable for catching regressions in critical paths.

### Response Time Tests

```python
from django.test import TestCase
import time

class PerformanceTest(TestCase):
    """
    Performance tests verify that key views respond within acceptable time limits.
    These are rough benchmarks — not a replacement for proper load testing tools
    like Locust or k6, but useful for catching obvious regressions in CI.
    """

    def test_article_list_performance(self):
        """
        The article list view should respond in under 1 second
        even with 100 articles in the database.
        """
        ArticleFactory.create_batch(100)

        start_time = time.time()
        response = self.client.get(reverse('article-list'))
        elapsed = time.time() - start_time

        self.assertEqual(response.status_code, 200)
        self.assertLess(
            elapsed,
            1.0,
            msg=f"Article list took {elapsed:.2f}s — expected < 1.0s"
        )

    def test_query_count(self):
        """
        Use assertNumQueries to assert an exact query count.
        This is the best way to guard against N+1 regressions.
        If a new ForeignKey is added and select_related isn't updated,
        this test will fail immediately.
        """
        ArticleFactory.create_batch(10)

        # assertNumQueries fails if the block generates a different number of queries
        with self.assertNumQueries(2):  # 1 for articles, 1 for prefetched tags
            articles = list(
                Article.objects.select_related('author')
                .prefetch_related('tags')
                .all()
            )
```

### Profiling Tests

```python
import cProfile
import pstats
from django.test import TestCase

class ProfilingTest(TestCase):
    """
    Use Python's cProfile to identify slow functions in your code.
    Not run in normal CI — use for local investigation of slow tests.
    """

    def test_with_profiling(self):
        """Profile a specific operation to find bottlenecks."""
        profiler = cProfile.Profile()
        profiler.enable()

        # Code you want to profile
        ArticleFactory.create_batch(100)
        articles = list(Article.objects.all())

        profiler.disable()

        # Print the top 10 slowest calls, sorted by cumulative time
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')
        stats.print_stats(10)
```

---

## Best Practices

### Test Organization

Organize tests into separate classes, one per concern. A single `ArticleTest` class that tests models, views, API, and forms together becomes impossible to navigate.

```python
# GOOD: One class per concern — focused and easy to navigate
class ArticleModelTest(TestCase):
    """Tests for Article model fields, methods, and constraints."""
    pass

class ArticleManagerTest(TestCase):
    """Tests for Article's custom manager and QuerySet methods."""
    pass

class ArticleViewTest(TestCase):
    """Tests for Django HTML views (not API)."""
    pass

class ArticleAPITest(APITestCase):
    """Tests for REST API endpoints."""
    pass


# BAD: Everything lumped into one class
class ArticleTest(TestCase):
    """Tests for... everything? Hard to navigate, easy to miss things."""
    pass
```

### Test Naming

Test method names should read like a sentence describing the expected behavior. You should be able to understand what failed just from the test name.

```python
# GOOD: Reads like a specification
def test_user_cannot_delete_another_users_article(self):
    pass

def test_article_slug_is_auto_generated_from_title(self):
    pass

def test_published_articles_appear_in_homepage_feed(self):
    pass


# BAD: Vague — tells you nothing about what failed or what was expected
def test_article(self):
    pass

def test_delete(self):
    pass

def test_slug(self):
    pass
```

### Test Independence

Every test must be able to run in any order and produce the same result. Tests that depend on each other are fragile and hard to debug.

```python
# GOOD: Each test creates its own data in setUp — fully independent
class ArticleTest(TestCase):
    def setUp(self):
        """Fresh article for every test method."""
        self.article = ArticleFactory()

    def test_publish(self):
        self.article.publish()
        self.assertEqual(self.article.status, 'published')

    def test_unpublish(self):
        # This works even if test_publish hasn't run yet
        self.article.publish()
        self.article.unpublish()
        self.assertEqual(self.article.status, 'draft')


# BAD: test_2 depends on test_1 having run first
# Django does not guarantee test execution order across methods
class ArticleTest(TestCase):
    def test_1_create(self):
        Article.article = ArticleFactory()  # Sets instance on class — fragile

    def test_2_publish(self):
        Article.article.publish()  # Will fail if test_1 didn't run first
```

### Assertion Messages

Provide a helpful message on assertions — when they fail in CI, the message is often all you have.

```python
# GOOD: Failure message explains what went wrong and what was expected
self.assertEqual(
    article.status,
    'published',
    'Article should be published after calling publish()'
)
self.assertTrue(
    article.is_visible,
    f'Article {article.id} should be visible, but is_visible={article.is_visible}'
)

# GOOD: Use the most specific assertion available
self.assertIn(user, article.likes.all())       # Better than assertTrue(user in ...)
self.assertIsNone(article.published_at)        # Better than assertEqual(None, ...)
self.assertGreater(article.view_count, 0)      # Better than assertTrue(count > 0)
self.assertContains(response, 'Login')         # Checks response body
self.assertRedirects(response, '/login/')      # Checks redirect URL and status
```

### Test Data Management

Use `setUpTestData` for large, shared, read-only datasets. Use `setUp` for objects that individual tests will mutate.

```python
class ArticleReadOnlyTest(TestCase):
    """
    Read-only tests share data created in setUpTestData.
    This is significantly faster than creating the same objects in setUp()
    for every single test method.
    """
    @classmethod
    def setUpTestData(cls):
        """Create once for the whole class — much faster than setUp() for each test."""
        cls.user = UserFactory()
        cls.category = CategoryFactory()
        cls.articles = ArticleFactory.create_batch(10, category=cls.category)

    def test_count(self):
        self.assertEqual(Article.objects.count(), 10)

    def test_all_articles_have_category(self):
        for article in self.articles:
            self.assertEqual(article.category, self.category)


class ArticleMutationTest(TestCase):
    """
    Tests that modify objects must use setUp() to get a fresh copy per test.
    If setUpTestData were used here, one test's changes would affect others.
    """
    def setUp(self):
        """Fresh article for each test — safe to modify."""
        self.article = ArticleFactory()

    def test_publish(self):
        self.article.publish()
        self.assertEqual(self.article.status, 'published')

    def test_archive(self):
        # This test is unaffected by test_publish because setUp() gives a fresh article
        self.article.archive()
        self.assertEqual(self.article.status, 'archived')
```

### Testing Edge Cases

Always test the boundaries and error conditions — these are where bugs hide.

```python
class ArticleEdgeCaseTest(TestCase):
    """
    Edge case tests verify behavior at the boundaries of expected input.
    These are often the most valuable tests because they catch bugs that
    normal happy-path tests miss.
    """

    def test_empty_content(self):
        """An article with no content should have 0 words and a minimum read time of 1 min."""
        article = ArticleFactory(content='')
        self.assertEqual(article.word_count, 0)
        self.assertEqual(article.read_time, 1)  # Never return 0 minutes

    def test_very_long_title(self):
        """Test that the model accepts a title at the maximum allowed length."""
        long_title = 'A' * 200  # Assumes max_length=200
        article = ArticleFactory(title=long_title)
        self.assertEqual(len(article.title), 200)

    def test_special_characters_in_slug(self):
        """
        Auto-generated slugs should only contain lowercase letters, numbers, and hyphens.
        Special characters from the title must be stripped or converted.
        """
        article = ArticleFactory(title='Test!@#$%^&*()')
        # Regex: only a-z, 0-9, and hyphens allowed in a valid slug
        self.assertRegex(article.slug, r'^[a-z0-9-]+$')

    def test_duplicate_slug_raises_validation_error(self):
        """
        Attempting to create a second article with the same slug should
        raise a ValidationError at the model level.
        We call full_clean() explicitly because unique constraint validation
        doesn't always run automatically before save().
        """
        ArticleFactory(slug='test-article')
        with self.assertRaises(ValidationError):
            article = Article(
                title='Test',
                slug='test-article',  # Duplicate slug
                content='Content',
                author=UserFactory()
            )
            article.full_clean()  # Trigger model-level validation
```
