# pytest & pytest-django — The Complete Guide

> A thorough, example-driven reference for installing, configuring, and mastering pytest with Django — covering everything from your first test to advanced patterns like factories, mocking, parametrize, fixtures, coverage, and CI integration.

**pytest version as of this writing:** 8.x  
**pytest-django version as of this writing:** 4.x  
**Official pytest docs:** https://docs.pytest.org/  
**Official pytest-django docs:** https://pytest-django.readthedocs.io/  
**Source:** https://github.com/pytest-dev/pytest-django  

---

## Table of Contents

- [1. Why pytest Instead of unittest](#1-why-pytest-instead-of-unittest)
- [2. How pytest Works — The Mental Model](#2-how-pytest-works--the-mental-model)
- [3. Installation](#3-installation)
- [4. Configuration — pytest.ini, pyproject.toml, setup.cfg](#4-configuration--pytestini-pyprojecttoml-setupcfg)
- [5. Your First Django Test](#5-your-first-django-test)
- [6. Fixtures — The Core of pytest](#6-fixtures--the-core-of-pytest)
- [7. Django-Specific Fixtures](#7-django-specific-fixtures)
- [8. The Database and Transactions](#8-the-database-and-transactions)
- [9. Testing Models](#9-testing-models)
- [10. Testing Views and URLs](#10-testing-views-and-urls)
- [11. Testing Forms](#11-testing-forms)
- [12. Testing the Django ORM — Queries and Managers](#12-testing-the-django-orm--queries-and-managers)
- [13. Testing Django REST Framework APIs](#13-testing-django-rest-framework-apis)
- [14. Parametrize — Running One Test With Many Inputs](#14-parametrize--running-one-test-with-many-inputs)
- [15. Factories with factory_boy](#15-factories-with-factory_boy)
- [16. Mocking — unittest.mock and pytest-mock](#16-mocking--unittestmock-and-pytest-mock)
- [17. Testing Signals](#17-testing-signals)
- [18. Testing Celery Tasks](#18-testing-celery-tasks)
- [19. Testing Email](#19-testing-email)
- [20. Testing File Uploads](#20-testing-file-uploads)
- [21. Testing Management Commands](#21-testing-management-commands)
- [22. Testing Middleware](#22-testing-middleware)
- [23. Testing Authentication and Permissions](#23-testing-authentication-and-permissions)
- [24. Markers — Categorizing and Controlling Tests](#24-markers--categorizing-and-controlling-tests)
- [25. Coverage with pytest-cov](#25-coverage-with-pytest-cov)
- [26. Performance — Speeding Up Your Test Suite](#26-performance--speeding-up-your-test-suite)
- [27. Running Tests in CI](#27-running-tests-in-ci)
- [28. Project Layout and Organization](#28-project-layout-and-organization)
- [29. Common Pitfalls & Troubleshooting](#29-common-pitfalls--troubleshooting)
- [30. Checklist](#30-checklist)

---

## 1. Why pytest Instead of unittest

Django ships with its own test runner built on top of Python's `unittest`. It works, but pytest is almost universally preferred in the Django community. Here is why.

**Less boilerplate.** With `unittest`, every test file starts with `import unittest` and every test class inherits from `TestCase`. With pytest, a test is just a function that starts with `test_`. Nothing to inherit.

```python
# unittest style — verbose
import unittest
from django.test import TestCase

class ArticleModelTest(TestCase):
    def test_str_representation(self):
        article = Article(title='Hello')
        self.assertEqual(str(article), 'Hello')

# pytest style — clean
def test_article_str_representation():
    article = Article(title='Hello')
    assert str(article) == 'Hello'
```

**Better assertion messages.** When a pytest assertion fails, pytest rewrites the expression and shows you exactly what the left side evaluated to and what the right side evaluated to. With `unittest`, you get a generic "AssertionError" unless you manually pass a `msg=` argument.

```
# pytest failure message
assert result == expected
  where result = Article.__str__(article)
  and expected = 'Hello World'
  but got      = 'hello world'
```

**Fixtures are composable and reusable.** pytest fixtures replace `setUp`/`tearDown` and `setUpTestData`. They are regular functions, can be shared across test files via `conftest.py`, can request other fixtures, and can be scoped to the test, class, module, or session.

**Parametrize.** Run the same test function with a list of different inputs in one declaration. No more copy-pasting test functions.

**Plugin ecosystem.** pytest-django, pytest-cov, pytest-mock, pytest-xdist (parallel test execution), pytest-factoryboy, and dozens of others add powerful capabilities with zero friction.

**You can still use Django's TestCase.** pytest-django is fully compatible with `django.test.TestCase`. You do not have to rewrite existing tests. You can adopt pytest incrementally.

---

## 2. How pytest Works — The Mental Model

Understanding pytest's mechanics makes everything else in this guide click.

**Test discovery.** When you run `pytest`, it searches for files matching `test_*.py` or `*_test.py` (configurable). Inside those files, it collects functions named `test_*` and methods named `test_*` inside classes named `Test*`.

**The fixture resolution chain.** When pytest sees a test function with parameters, it treats those parameter names as fixture requests. It looks up each name in a chain: local `conftest.py` → parent directory `conftest.py` → root `conftest.py` → built-in fixtures → installed plugin fixtures. The fixture function runs, and its return value is injected into the test.

```
pytest collects: test_create_article(db, article_data)
                              ↓
pytest sees parameters: 'db' and 'article_data'
                              ↓
pytest resolves 'db'           → built-in pytest-django fixture
pytest resolves 'article_data' → found in conftest.py
                              ↓
pytest calls fixtures in dependency order
                              ↓
pytest calls test_create_article(db=<database>, article_data={...})
```

**Fixture scope.** Fixtures have a scope that controls how often they run. `function` scope (default) runs once per test. `class` scope runs once per test class. `module` scope runs once per test file. `session` scope runs once per entire test session. Higher-scope fixtures are shared across many tests, which makes the suite faster.

**conftest.py.** This is a special file pytest recognizes automatically. Any fixtures defined in `conftest.py` are available to all tests in the same directory and all subdirectories, without any import. This is where you put shared fixtures.

**Marks.** You can annotate tests with `@pytest.mark.name` to control which tests run. Common uses: `@pytest.mark.slow`, `@pytest.mark.integration`, `@pytest.mark.skip`.

---

## 3. Installation

### Step 1: Install pytest and pytest-django

```bash
pip install pytest pytest-django

# or with uv
uv add pytest pytest-django --dev

# or with poetry
poetry add pytest pytest-django --group dev
```

### Step 2: Install commonly used companions

```bash
pip install pytest-cov          # coverage reporting
pip install pytest-mock         # cleaner mocking via the 'mocker' fixture
pip install factory-boy         # test data factories (highly recommended)
pip install pytest-factoryboy   # integrates factory-boy with pytest fixtures
pip install pytest-xdist        # run tests in parallel
pip install Faker               # generate realistic fake data (used by factory-boy)
```

### Step 3: Tell pytest which Django settings to use

pytest-django needs to know your Django settings module. You have two options.

**Option A (recommended): Set it in `pytest.ini` or `pyproject.toml`** (see Section 4).

**Option B: Set it via environment variable** before running pytest:

```bash
DJANGO_SETTINGS_MODULE=myproject.settings pytest
```

The configuration file approach is simpler and avoids forgetting to set the variable.

### Step 4: Verify the installation

```bash
pytest --version
# pytest 8.x.x

pytest --co -q    # collect tests without running them — useful to verify discovery
```

---

## 4. Configuration — pytest.ini, pyproject.toml, setup.cfg

pytest looks for configuration in several files. **`pyproject.toml` is the modern standard** for new projects. Use `pytest.ini` if your project doesn't use `pyproject.toml` yet.

### pyproject.toml (recommended)

```toml
[tool.pytest.ini_options]
# Tell pytest-django where your settings are
DJANGO_SETTINGS_MODULE = "myproject.settings"

# Where to look for tests (default is the current directory)
testpaths = ["tests"]

# Filename patterns pytest recognizes as test files
python_files = ["test_*.py", "*_test.py"]

# Function/method name patterns
python_functions = ["test_*"]

# Class name patterns
python_classes = ["Test*"]

# Register custom marks to avoid PytestUnknownMarkWarning
markers = [
    "slow: marks tests as slow (deselect with '-m not slow')",
    "integration: marks tests requiring external services",
    "unit: marks fast, isolated unit tests",
    "smoke: marks the minimal subset needed to verify basic functionality",
]

# Always show extra test summary info
addopts = "-v --tb=short"

# Fail immediately on first failure (optional, good for CI)
# addopts = "-v --tb=short -x"

# Show locals in tracebacks (helpful for debugging)
# addopts = "-v --tb=long --showlocals"
```

### pytest.ini (alternative)

```ini
[pytest]
DJANGO_SETTINGS_MODULE = myproject.settings
testpaths = tests
python_files = test_*.py *_test.py
python_functions = test_*
python_classes = Test*
addopts = -v --tb=short
markers =
    slow: marks tests as slow
    integration: marks integration tests
    unit: marks unit tests
```

### setup.cfg (legacy)

```ini
[tool:pytest]
DJANGO_SETTINGS_MODULE = myproject.settings
testpaths = tests
addopts = -v --tb=short
```

### Testing against multiple settings files

If you have separate settings for testing (e.g., using a faster password hasher or an in-memory cache), point to that file:

```toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "myproject.settings.test"
```

```python
# myproject/settings/test.py
from .base import *

# Use a faster password hasher — MD5 is 10x faster than bcrypt for tests
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

# Use an in-memory cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Disable celery during tests (tasks run synchronously)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Use a dedicated test database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'myproject_test',
        'USER': 'postgres',
        'PASSWORD': '',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}
```

### Running pytest

```bash
# Run all tests
pytest

# Run tests in a specific directory
pytest tests/

# Run a specific file
pytest tests/test_models.py

# Run a specific test function
pytest tests/test_models.py::test_article_str

# Run a specific test class
pytest tests/test_models.py::TestArticleModel

# Run a specific method in a class
pytest tests/test_models.py::TestArticleModel::test_str

# Run tests matching a keyword
pytest -k "article"              # runs any test with 'article' in its name
pytest -k "article and not slow" # combine expressions

# Run tests with a specific mark
pytest -m slow
pytest -m "not slow"
pytest -m "unit or integration"

# Run and stop on first failure
pytest -x

# Run and stop after N failures
pytest --maxfail=3

# Show stdout output (by default pytest captures it)
pytest -s

# Verbose output
pytest -v

# Extra verbose (shows fixture setup/teardown)
pytest -vv

# Re-run only the tests that failed last time
pytest --lf

# Run last failures first, then the rest
pytest --ff
```

---

## 5. Your First Django Test

Create a `tests/` directory at the root of your Django project (or inside your app). pytest-django requires no special imports — just write functions.

### Directory structure

```
myproject/
├── myapp/
│   ├── models.py
│   ├── views.py
│   └── urls.py
├── tests/
│   ├── conftest.py          ← shared fixtures
│   ├── test_models.py
│   ├── test_views.py
│   └── test_forms.py
├── pyproject.toml
└── manage.py
```

### A simple model test

```python
# tests/test_models.py
import pytest
from myapp.models import Article


def test_article_str_representation():
    """Article.__str__ should return the title."""
    article = Article(title='Hello World')
    assert str(article) == 'Hello World'


def test_article_is_published_by_default():
    """New articles should not be published by default."""
    article = Article(title='Draft')
    assert article.is_published is False


@pytest.mark.django_db
def test_article_save_and_retrieve():
    """Articles saved to the database can be retrieved."""
    Article.objects.create(title='Saved Article', body='Some content')
    retrieved = Article.objects.get(title='Saved Article')
    assert retrieved.body == 'Some content'


@pytest.mark.django_db
def test_article_slug_auto_generated():
    """Saving an article auto-generates a slug from the title."""
    article = Article.objects.create(title='My First Article')
    assert article.slug == 'my-first-article'
```

**Key point:** `@pytest.mark.django_db` is required for any test that touches the database. Without it, database access raises an error. This is intentional — it makes the boundary between pure tests and database-dependent tests explicit and keeps pure tests fast.

Tests that do not touch the database — like the first two above — run without the mark and execute much faster because they skip all database setup.

### The `db` fixture vs `@pytest.mark.django_db`

These two approaches are equivalent. The mark is more common for standalone functions; the fixture is required when composing with other fixtures.

```python
# Using the mark — most common
@pytest.mark.django_db
def test_something():
    ...

# Using the fixture — necessary when a fixture needs db access
@pytest.fixture
def article(db):
    return Article.objects.create(title='Test Article')

def test_with_fixture(article):   # db access granted transitively
    assert article.title == 'Test Article'
```

---

## 6. Fixtures — The Core of pytest

Fixtures are pytest's replacement for `setUp`/`tearDown`. They are regular functions decorated with `@pytest.fixture` that return a value. Tests declare which fixtures they need as function parameters.

### Basic fixture

```python
# tests/conftest.py
import pytest
from myapp.models import Article, Author


@pytest.fixture
def author():
    """A simple Author instance (not saved to database)."""
    return Author(name='Jane Doe', email='jane@example.com')


@pytest.fixture
def author_in_db(db):
    """An Author instance saved to the database."""
    return Author.objects.create(name='Jane Doe', email='jane@example.com')
```

```python
# tests/test_models.py
def test_author_str(author):
    assert str(author) == 'Jane Doe'


@pytest.mark.django_db
def test_author_can_be_saved(author):
    author.save()
    assert Author.objects.count() == 1


def test_author_in_db_exists(author_in_db):
    # db access is granted transitively because author_in_db requests 'db'
    assert author_in_db.pk is not None
```

### Fixture scope

```python
@pytest.fixture(scope='function')   # default — runs once per test
def fresh_object():
    return SomeModel()


@pytest.fixture(scope='class')      # runs once per test class
def class_level_data():
    return {'key': 'value'}


@pytest.fixture(scope='module')     # runs once per test file
def expensive_parse():
    return parse_large_file('fixtures/data.json')


@pytest.fixture(scope='session')    # runs once for the entire test run
def django_db_setup():              # useful for read-only reference data
    pass
```

**Rule:** Use `function` scope for anything that modifies the database. Use `session` or `module` scope only for read-only data — otherwise tests will affect each other.

### Fixtures with teardown using `yield`

```python
@pytest.fixture
def temp_upload_dir(tmp_path):
    """Create a temporary media directory and clean up after each test."""
    media_root = tmp_path / 'media'
    media_root.mkdir()
    
    # Everything before yield runs as setUp
    with override_settings(MEDIA_ROOT=str(media_root)):
        yield media_root
    
    # Everything after yield runs as tearDown
    # (The tmp_path fixture handles deletion automatically here,
    #  but you can add explicit cleanup if needed)


@pytest.fixture
def patched_stripe(mocker):
    """Patch the Stripe client before each test, restore after."""
    mock = mocker.patch('myapp.payments.stripe')
    mock.Charge.create.return_value = {'id': 'ch_test_123', 'status': 'succeeded'}
    yield mock
    # mocker handles restoration automatically
```

### Requesting fixtures from other fixtures

```python
@pytest.fixture
def user(db):
    from django.contrib.auth.models import User
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpassword123',
    )


@pytest.fixture
def article(db, user):
    """An article that belongs to a user."""
    return Article.objects.create(
        title='Test Article',
        author=user,
        body='Some content',
    )


def test_article_has_author(article):
    assert article.author.username == 'testuser'
```

### Parameterized fixtures

```python
@pytest.fixture(params=['postgresql', 'sqlite'])
def db_backend(request):
    """Run tests against multiple database backends."""
    return request.param


def test_query_works(db_backend):
    # This test runs twice: once with 'postgresql', once with 'sqlite'
    print(f'Running against {db_backend}')
```

### The `request` object inside fixtures

```python
@pytest.fixture
def user(db, request):
    """Create a user; allow customization via indirect parametrize."""
    params = getattr(request, 'param', {})
    from django.contrib.auth.models import User
    return User.objects.create_user(
        username=params.get('username', 'default'),
        email=params.get('email', 'default@example.com'),
        password='password',
        is_staff=params.get('is_staff', False),
    )
```

---

## 7. Django-Specific Fixtures

pytest-django provides several built-in fixtures for common Django testing needs. You do not need to import them — pytest finds them automatically.

### `db` — Grant database access

```python
def test_basic_query(db):
    count = Article.objects.count()
    assert count == 0
```

### `django_db_setup` — Control database creation

You rarely override this directly. It runs once per session and creates the test database.

### `client` — An unauthenticated Django test client

```python
def test_homepage_returns_200(client):
    response = client.get('/')
    assert response.status_code == 200
```

### `admin_client` — A client logged in as an admin

```python
def test_admin_dashboard_accessible(admin_client):
    response = admin_client.get('/admin/')
    assert response.status_code == 200
```

### `admin_user` — The admin User object

```python
def test_admin_user_is_superuser(admin_user):
    assert admin_user.is_superuser is True
```

### `rf` — The RequestFactory

```python
from myapp.views import ArticleListView

def test_article_list_view_with_request_factory(rf, db):
    request = rf.get('/articles/')
    response = ArticleListView.as_view()(request)
    assert response.status_code == 200
```

### `settings` — Live-override Django settings for one test

```python
def test_feature_flag_on(client, settings):
    settings.FEATURE_FLAG_NEW_UI = True
    response = client.get('/dashboard/')
    assert b'new-ui' in response.content


def test_debug_mode(settings):
    settings.DEBUG = True
    assert settings.DEBUG is True
    # DEBUG is restored to its original value after this test automatically
```

### `mailoutbox` — Capture outgoing emails

```python
def test_welcome_email_sent(db, mailoutbox):
    User.objects.create_user(username='new', email='new@example.com', password='pass')
    trigger_welcome_email('new@example.com')
    
    assert len(mailoutbox) == 1
    assert mailoutbox[0].subject == 'Welcome!'
    assert 'new@example.com' in mailoutbox[0].to
```

### `django_user_model` — The User model (respects AUTH_USER_MODEL)

```python
def test_create_user(db, django_user_model):
    user = django_user_model.objects.create_user(
        username='bob',
        password='securepassword',
    )
    assert user.username == 'bob'
```

### `django_username_field` — The username field name

```python
def test_username_field(django_username_field):
    assert django_username_field == 'username'
    # If using a custom user model with email as username, this returns 'email'
```

### `live_server` — A real HTTP server for integration tests

```python
def test_homepage_with_selenium(live_server, selenium):
    """Integration test with a real browser (requires selenium and a driver)."""
    selenium.get(f'{live_server.url}/')
    assert 'My Site' in selenium.title
```

---

## 8. The Database and Transactions

### Default behavior: rollback after each test

By default, `@pytest.mark.django_db` wraps each test in a transaction that is rolled back after the test completes. This means:

- Each test starts with a clean database state.
- Tests are completely isolated from each other.
- No cleanup code is needed.
- This is the same as Django's `TestCase`.

```python
@pytest.mark.django_db
def test_one():
    Article.objects.create(title='Test')
    assert Article.objects.count() == 1

@pytest.mark.django_db
def test_two():
    # Article from test_one is gone — transaction was rolled back
    assert Article.objects.count() == 0
```

### `transaction=True` — For tests that need real transactions

Some code uses `transaction.atomic()`, `select_for_update()`, `on_commit()` hooks, or tests that involve multiple database connections. These need real transaction commits.

```python
@pytest.mark.django_db(transaction=True)
def test_on_commit_hook():
    """Test that an on_commit callback fires after a real commit."""
    with transaction.atomic():
        article = Article.objects.create(title='Test')
    # on_commit hooks fire here, after the real COMMIT
    assert some_side_effect_happened()
```

**Tradeoff:** `transaction=True` tests are slower because the database must be reset between tests by truncating tables instead of rolling back. Use it only when needed.

### `databases` — Testing multi-database setups

```python
@pytest.mark.django_db(databases=['default', 'analytics'])
def test_cross_database_query():
    Article.objects.using('default').create(title='Test')
    assert AnalyticsEvent.objects.using('analytics').count() == 0
```

### `django_db_reset_sequences` — Reset auto-increment IDs

```python
@pytest.fixture
def reset_sequences(django_db_reset_sequences):
    """Ensure IDs start from 1 in each test (useful when tests depend on specific PKs)."""
    pass
```

### Using `setUpTestData` equivalent with session-scoped fixtures

For expensive read-only test data that is safe to share across tests:

```python
# conftest.py
@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """Load fixtures once per session."""
    with django_db_blocker.unblock():
        call_command('loaddata', 'test_data.json')
```

Or use `pytest.mark.django_db` with `scope='session'`:

```python
@pytest.fixture(scope='session')
def shared_article(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        return Article.objects.create(title='Shared', body='Read-only data')
```

---

## 9. Testing Models

### Testing model methods

```python
# myapp/models.py
class Article(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField()
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_published(self):
        return self.published_at is not None

    def word_count(self):
        return len(self.body.split())

    def __str__(self):
        return self.title
```

```python
# tests/test_models.py
import pytest
from django.utils import timezone
from myapp.models import Article


# Pure unit tests — no database needed
def test_article_str():
    article = Article(title='My Title')
    assert str(article) == 'My Title'


def test_unpublished_article_is_not_published():
    article = Article(published_at=None)
    assert article.is_published() is False


def test_published_article_is_published():
    article = Article(published_at=timezone.now())
    assert article.is_published() is True


def test_word_count():
    article = Article(body='one two three four five')
    assert article.word_count() == 5


def test_empty_body_word_count():
    article = Article(body='')
    assert article.word_count() == 0


# Database tests
@pytest.mark.django_db
def test_article_created_at_auto_populated():
    before = timezone.now()
    article = Article.objects.create(title='Test', body='')
    after = timezone.now()
    assert before <= article.created_at <= after


@pytest.mark.django_db
def test_article_ordering():
    Article.objects.create(title='Z Article', body='')
    Article.objects.create(title='A Article', body='')
    articles = list(Article.objects.order_by('title'))
    assert articles[0].title == 'A Article'
    assert articles[1].title == 'Z Article'
```

### Testing model validation

```python
import pytest
from django.core.exceptions import ValidationError
from myapp.models import Article


@pytest.mark.django_db
def test_title_max_length():
    article = Article(title='x' * 201, body='')
    with pytest.raises(ValidationError) as exc_info:
        article.full_clean()
    assert 'title' in exc_info.value.message_dict


@pytest.mark.django_db
def test_valid_article_passes_validation():
    article = Article(title='Valid Title', body='Some body text')
    article.full_clean()   # should not raise
```

### Testing model `save()` overrides

```python
# myapp/models.py
from django.utils.text import slugify

class Article(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


# tests/test_models.py
@pytest.mark.django_db
def test_slug_auto_generated_from_title():
    article = Article.objects.create(title='Hello World')
    assert article.slug == 'hello-world'


@pytest.mark.django_db
def test_existing_slug_not_overwritten():
    article = Article.objects.create(title='Hello World', slug='custom-slug')
    assert article.slug == 'custom-slug'


@pytest.mark.django_db
def test_slug_uniqueness_raises_integrity_error():
    from django.db import IntegrityError
    Article.objects.create(title='Hello')
    with pytest.raises(IntegrityError):
        Article.objects.create(title='Hello Again', slug='hello')
```

### Testing model managers and querysets

```python
# myapp/models.py
class PublishedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(published_at__isnull=False)

class Article(models.Model):
    title = models.CharField(max_length=200)
    published_at = models.DateTimeField(null=True, blank=True)

    objects = models.Manager()
    published = PublishedManager()


# tests/test_models.py
from django.utils import timezone

@pytest.mark.django_db
def test_published_manager_filters_correctly():
    Article.objects.create(title='Draft')
    Article.objects.create(title='Live', published_at=timezone.now())
    
    assert Article.objects.count() == 2
    assert Article.published.count() == 1
    assert Article.published.first().title == 'Live'
```

---

## 10. Testing Views and URLs

pytest-django provides `client` (unauthenticated) and `admin_client` (admin) fixtures. For testing views that require a specific logged-in user, create your own authenticated client fixture.

### Testing URL resolution

```python
# tests/test_urls.py
from django.urls import reverse, resolve
from myapp.views import ArticleListView, ArticleDetailView


def test_article_list_url():
    url = reverse('article-list')
    assert url == '/articles/'


def test_article_detail_url():
    url = reverse('article-detail', kwargs={'slug': 'hello-world'})
    assert url == '/articles/hello-world/'


def test_article_list_resolves_to_correct_view():
    resolver = resolve('/articles/')
    assert resolver.func.view_class is ArticleListView
```

### Testing function-based views

```python
@pytest.mark.django_db
def test_article_list_returns_200(client):
    response = client.get(reverse('article-list'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_article_list_contains_articles(client):
    Article.objects.create(title='First', body='Body', published_at=timezone.now())
    Article.objects.create(title='Second', body='Body', published_at=timezone.now())
    
    response = client.get(reverse('article-list'))
    assert b'First' in response.content
    assert b'Second' in response.content


@pytest.mark.django_db
def test_article_detail_404_for_nonexistent_slug(client):
    response = client.get(reverse('article-detail', kwargs={'slug': 'not-real'}))
    assert response.status_code == 404
```

### Testing views that require authentication

```python
# tests/conftest.py
import pytest
from django.contrib.auth.models import User


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpassword123',
    )


@pytest.fixture
def authenticated_client(client, user):
    client.login(username='testuser', password='testpassword123')
    return client


@pytest.fixture
def staff_user(db):
    return User.objects.create_user(
        username='staffuser',
        email='staff@example.com',
        password='testpassword123',
        is_staff=True,
    )


@pytest.fixture
def staff_client(client, staff_user):
    client.login(username='staffuser', password='testpassword123')
    return client
```

```python
# tests/test_views.py
def test_dashboard_requires_login(client):
    response = client.get(reverse('dashboard'))
    assert response.status_code == 302
    assert '/login/' in response['Location']


def test_dashboard_accessible_when_logged_in(authenticated_client):
    response = authenticated_client.get(reverse('dashboard'))
    assert response.status_code == 200


def test_admin_panel_requires_staff(authenticated_client):
    response = authenticated_client.get(reverse('admin-panel'))
    assert response.status_code == 403


def test_admin_panel_accessible_to_staff(staff_client):
    response = staff_client.get(reverse('admin-panel'))
    assert response.status_code == 200
```

### Testing POST requests

```python
@pytest.mark.django_db
def test_create_article_via_post(authenticated_client):
    response = authenticated_client.post(
        reverse('article-create'),
        data={
            'title': 'New Article',
            'body': 'Article body text',
        },
    )
    assert response.status_code == 302   # redirect after successful create
    assert Article.objects.filter(title='New Article').exists()


@pytest.mark.django_db
def test_create_article_invalid_data_returns_form_errors(authenticated_client):
    response = authenticated_client.post(
        reverse('article-create'),
        data={'title': ''},   # title is required
    )
    assert response.status_code == 200   # re-renders the form
    assert 'This field is required' in response.content.decode()
```

### Testing template context and template usage

```python
@pytest.mark.django_db
def test_article_detail_uses_correct_template(client):
    article = Article.objects.create(
        title='Test', body='Body', slug='test', published_at=timezone.now()
    )
    response = client.get(reverse('article-detail', kwargs={'slug': 'test'}))
    assert response.status_code == 200
    assert 'myapp/article_detail.html' in [t.name for t in response.templates]


@pytest.mark.django_db
def test_article_detail_passes_article_to_context(client):
    article = Article.objects.create(
        title='Context Test', body='Body', slug='context-test', published_at=timezone.now()
    )
    response = client.get(reverse('article-detail', kwargs={'slug': 'context-test'}))
    assert response.context['article'] == article
```

### Using `RequestFactory` for faster view tests

`RequestFactory` creates request objects without going through the URL resolver or middleware. This is faster for testing views in isolation.

```python
from django.test import RequestFactory
from myapp.views import ArticleListView, article_create

@pytest.fixture
def rf():
    return RequestFactory()


def test_article_list_view_with_rf(rf, db):
    request = rf.get('/articles/')
    response = ArticleListView.as_view()(request)
    assert response.status_code == 200


def test_article_create_requires_login_with_rf(rf, user):
    request = rf.post('/articles/create/', {'title': 'Test', 'body': 'Body'})
    request.user = user  # attach user manually — RF bypasses middleware
    response = article_create(request)
    assert response.status_code in (200, 302)
```

---

## 11. Testing Forms

```python
# myapp/forms.py
from django import forms
from myapp.models import Article

class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'body']

    def clean_title(self):
        title = self.cleaned_data['title']
        if title.lower() == 'test':
            raise forms.ValidationError("Please use a real title, not 'test'.")
        return title
```

```python
# tests/test_forms.py
import pytest
from myapp.forms import ArticleForm


def test_valid_form():
    form = ArticleForm(data={'title': 'My Article', 'body': 'Content here'})
    assert form.is_valid()


def test_empty_title_is_invalid():
    form = ArticleForm(data={'title': '', 'body': 'Content'})
    assert not form.is_valid()
    assert 'title' in form.errors


def test_empty_body_is_invalid():
    form = ArticleForm(data={'title': 'My Article', 'body': ''})
    assert not form.is_valid()
    assert 'body' in form.errors


def test_title_test_is_rejected_by_custom_validation():
    form = ArticleForm(data={'title': 'test', 'body': 'Content'})
    assert not form.is_valid()
    assert 'title' in form.errors
    assert "Please use a real title" in form.errors['title'][0]


def test_form_saves_to_database(db):
    form = ArticleForm(data={'title': 'Saved Article', 'body': 'Body text'})
    assert form.is_valid()
    article = form.save()
    assert article.pk is not None
    assert Article.objects.filter(title='Saved Article').exists()


@pytest.mark.django_db
def test_form_instance_edit():
    """Test editing an existing instance via a form."""
    article = Article.objects.create(title='Original Title', body='Body')
    form = ArticleForm(
        data={'title': 'Updated Title', 'body': 'Updated body'},
        instance=article,
    )
    assert form.is_valid()
    updated = form.save()
    assert updated.pk == article.pk
    assert updated.title == 'Updated Title'
```

---

## 12. Testing the Django ORM — Queries and Managers

### Counting queries with `django_assert_num_queries`

```python
def test_article_list_view_num_queries(client, django_assert_num_queries):
    Article.objects.bulk_create([
        Article(title=f'Article {i}', body='Body') for i in range(10)
    ])
    with django_assert_num_queries(1):
        response = client.get(reverse('article-list'))
    assert response.status_code == 200
```

### Using `assertNumQueries` from Django's TestCase (also works in pytest)

```python
from django.test import TestCase

class ArticleQueryTests(TestCase):
    def test_no_n_plus_one(self):
        """Listing articles with authors should use 2 queries: one for articles, one for authors."""
        Author.objects.bulk_create([Author(name=f'Author {i}') for i in range(5)])
        for i, author in enumerate(Author.objects.all()):
            Article.objects.create(title=f'Article {i}', author=author)

        with self.assertNumQueries(2):
            articles = list(Article.objects.select_related('author').all())
            for article in articles:
                _ = article.author.name
```

### Detecting N+1 queries

```python
@pytest.mark.django_db
def test_no_n_plus_one_in_article_list(client, django_assert_num_queries):
    """
    Without select_related, listing N articles generates N+1 queries
    (one for articles, then one per article to get its author).
    This test ensures we've fixed that with select_related.
    """
    for i in range(5):
        author = Author.objects.create(name=f'Author {i}')
        Article.objects.create(title=f'Article {i}', body='', author=author)

    # The view should use select_related('author'), resulting in exactly 2 queries
    with django_assert_num_queries(2):
        client.get(reverse('article-list'))
```

### Testing custom QuerySet methods

```python
# myapp/models.py
class ArticleQuerySet(models.QuerySet):
    def published(self):
        return self.filter(published_at__isnull=False)

    def by_author(self, author):
        return self.filter(author=author)

    def recent(self, days=7):
        cutoff = timezone.now() - timedelta(days=days)
        return self.filter(published_at__gte=cutoff)


# tests/test_models.py
@pytest.fixture
def article_set(db):
    """Create a mix of published and unpublished articles."""
    past = timezone.now() - timedelta(days=30)
    recent = timezone.now() - timedelta(days=2)
    author = Author.objects.create(name='Test Author')
    return {
        'draft': Article.objects.create(title='Draft', body=''),
        'old': Article.objects.create(title='Old', body='', published_at=past, author=author),
        'recent': Article.objects.create(title='Recent', body='', published_at=recent, author=author),
    }


def test_published_queryset(article_set):
    published = Article.objects.published()
    assert published.count() == 2
    assert article_set['draft'] not in published


def test_recent_queryset(article_set):
    recent = Article.objects.recent(days=7)
    assert recent.count() == 1
    assert article_set['recent'] in recent
    assert article_set['old'] not in recent


def test_by_author_queryset(article_set):
    author = article_set['old'].author
    by_author = Article.objects.by_author(author)
    assert by_author.count() == 2
```

---

## 13. Testing Django REST Framework APIs

Install DRF and add it to your project, then use the `APIClient` in tests.

```bash
pip install djangorestframework
```

```python
# tests/conftest.py
import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_api_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def admin_api_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client
```

```python
# tests/test_api.py
import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
def test_article_list_unauthenticated(api_client):
    response = api_client.get(reverse('api:article-list'))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_article_list_authenticated(authenticated_api_client):
    response = authenticated_api_client.get(reverse('api:article-list'))
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data['results'], list)


@pytest.mark.django_db
def test_create_article(authenticated_api_client):
    payload = {
        'title': 'New API Article',
        'body': 'Article body text',
    }
    response = authenticated_api_client.post(
        reverse('api:article-list'),
        data=payload,
        format='json',
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['title'] == 'New API Article'
    assert Article.objects.filter(title='New API Article').exists()


@pytest.mark.django_db
def test_update_article(authenticated_api_client, article):
    url = reverse('api:article-detail', kwargs={'pk': article.pk})
    payload = {'title': 'Updated Title', 'body': article.body}
    response = authenticated_api_client.put(url, data=payload, format='json')
    assert response.status_code == status.HTTP_200_OK
    article.refresh_from_db()
    assert article.title == 'Updated Title'


@pytest.mark.django_db
def test_delete_article_requires_permission(authenticated_api_client, article):
    url = reverse('api:article-detail', kwargs={'pk': article.pk})
    response = authenticated_api_client.delete(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_delete_article_as_admin(admin_api_client, article):
    url = reverse('api:article-detail', kwargs={'pk': article.pk})
    response = admin_api_client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Article.objects.filter(pk=article.pk).exists()


@pytest.mark.django_db
def test_article_list_pagination(authenticated_api_client):
    Article.objects.bulk_create([
        Article(title=f'Article {i}', body='') for i in range(25)
    ])
    response = authenticated_api_client.get(reverse('api:article-list'))
    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] == 25
    assert len(response.data['results']) == 20   # default page size


@pytest.mark.django_db
def test_api_returns_correct_json_structure(authenticated_api_client):
    article = Article.objects.create(title='Test', body='Content')
    response = authenticated_api_client.get(
        reverse('api:article-detail', kwargs={'pk': article.pk})
    )
    assert response.status_code == status.HTTP_200_OK
    assert set(response.data.keys()) == {'id', 'title', 'body', 'slug', 'published_at', 'created_at'}
```

### Testing serializers directly

```python
from myapp.serializers import ArticleSerializer


def test_serializer_valid_data():
    data = {'title': 'Test', 'body': 'Content'}
    serializer = ArticleSerializer(data=data)
    assert serializer.is_valid()


def test_serializer_missing_required_field():
    data = {'body': 'Content'}  # title is missing
    serializer = ArticleSerializer(data=data)
    assert not serializer.is_valid()
    assert 'title' in serializer.errors


def test_serializer_output_format(db):
    article = Article.objects.create(title='Hello', body='World', slug='hello')
    serializer = ArticleSerializer(article)
    assert serializer.data['title'] == 'Hello'
    assert serializer.data['slug'] == 'hello'
    assert 'created_at' in serializer.data
```

---

## 14. Parametrize — Running One Test With Many Inputs

`@pytest.mark.parametrize` runs a single test function multiple times with different arguments. This eliminates copy-pasted test functions and makes it easy to add new test cases.

### Basic usage

```python
import pytest
from myapp.utils import slugify_title


@pytest.mark.parametrize('title, expected_slug', [
    ('Hello World', 'hello-world'),
    ('Django Testing', 'django-testing'),
    ('  Leading Spaces  ', 'leading-spaces'),
    ('Special! @#$ Characters', 'special-characters'),
    ('UPPERCASE', 'uppercase'),
    ('already-a-slug', 'already-a-slug'),
])
def test_slugify_title(title, expected_slug):
    assert slugify_title(title) == expected_slug
```

pytest will run this test 6 times, once for each `(title, expected_slug)` pair, and report each separately in the output.

### Parametrize with expected exceptions

```python
@pytest.mark.parametrize('value, expected', [
    (True, True),
    ('true', True),
    ('on', True),
    ('yes', True),
    ('1', True),
    (False, False),
    ('false', False),
    ('off', False),
    ('no', False),
    ('0', False),
])
def test_parse_bool(value, expected):
    assert parse_bool(value) == expected


@pytest.mark.parametrize('invalid_value', ['maybe', 'yep', 2, None])
def test_parse_bool_raises_on_invalid(invalid_value):
    with pytest.raises(ValueError):
        parse_bool(invalid_value)
```

### Parametrize with IDs for readable output

```python
@pytest.mark.parametrize('email, is_valid', [
    pytest.param('good@example.com', True, id='valid-standard'),
    pytest.param('user+tag@example.co.uk', True, id='valid-plus-tag'),
    pytest.param('not-an-email', False, id='invalid-no-at'),
    pytest.param('@example.com', False, id='invalid-no-local'),
    pytest.param('', False, id='invalid-empty'),
], )
def test_email_validation(email, is_valid):
    assert validate_email_format(email) == is_valid
```

Output now shows descriptive IDs instead of just indices:

```
PASSED test_forms.py::test_email_validation[valid-standard]
PASSED test_forms.py::test_email_validation[valid-plus-tag]
FAILED test_forms.py::test_email_validation[invalid-no-at]
```

### Stacking parametrize (generates a matrix)

```python
@pytest.mark.parametrize('method', ['GET', 'POST', 'PUT', 'DELETE'])
@pytest.mark.parametrize('path', ['/articles/', '/articles/1/'])
def test_unauthenticated_requests_all_require_login(client, method, path):
    """Every method on every endpoint should redirect unauthenticated users."""
    response = getattr(client, method.lower())(path)
    assert response.status_code in (302, 401, 403)
```

This generates 4 × 2 = 8 test cases.

### Parametrize with database fixtures

```python
@pytest.mark.django_db
@pytest.mark.parametrize('status_code, path', [
    (200, '/'),
    (200, '/articles/'),
    (200, '/about/'),
    (404, '/does-not-exist/'),
])
def test_public_pages_return_expected_status(client, status_code, path):
    response = client.get(path)
    assert response.status_code == status_code
```

---

## 15. Factories with factory_boy

Hard-coding test data inside fixtures becomes brittle as your models grow. `factory_boy` lets you define a factory for each model that generates realistic test data with sensible defaults, with any field overridable per-test.

### Installation and basic setup

```bash
pip install factory-boy Faker
```

```python
# tests/factories.py
import factory
from factory.django import DjangoModelFactory
from django.utils import timezone
from myapp.models import Author, Article, Comment
from django.contrib.auth.models import User


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'user_{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'testpassword')
    is_active = True


class AuthorFactory(DjangoModelFactory):
    class Meta:
        model = Author

    name = factory.Faker('name')
    email = factory.Faker('email')
    bio = factory.Faker('paragraph')


class ArticleFactory(DjangoModelFactory):
    class Meta:
        model = Article

    title = factory.Faker('sentence', nb_words=5)
    body = factory.Faker('text', max_nb_chars=500)
    author = factory.SubFactory(AuthorFactory)
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))
    published_at = None   # draft by default


class PublishedArticleFactory(ArticleFactory):
    """An Article that is always published."""
    published_at = factory.LazyFunction(timezone.now)


class CommentFactory(DjangoModelFactory):
    class Meta:
        model = Comment

    article = factory.SubFactory(ArticleFactory)
    author = factory.SubFactory(UserFactory)
    body = factory.Faker('paragraph')
```

### Using factories in tests

```python
# tests/test_models.py
import pytest
from tests.factories import ArticleFactory, AuthorFactory, UserFactory


@pytest.mark.django_db
def test_article_factory_creates_valid_article():
    article = ArticleFactory()
    assert article.pk is not None
    assert article.title
    assert article.author is not None


@pytest.mark.django_db
def test_override_specific_fields():
    article = ArticleFactory(title='Custom Title', body='Custom body')
    assert article.title == 'Custom Title'


@pytest.mark.django_db
def test_published_article_factory():
    article = PublishedArticleFactory()
    assert article.is_published() is True


@pytest.mark.django_db
def test_create_many_articles():
    articles = ArticleFactory.create_batch(10)
    assert len(articles) == 10
    assert Article.objects.count() == 10


@pytest.mark.django_db
def test_build_does_not_save():
    """build() creates the instance in memory without touching the database."""
    article = ArticleFactory.build()
    assert article.pk is None
    assert Article.objects.count() == 0
```

### Using `pytest-factoryboy` to auto-register factories as fixtures

```bash
pip install pytest-factoryboy
```

```python
# tests/conftest.py
import pytest
from pytest_factoryboy import register
from tests.factories import UserFactory, AuthorFactory, ArticleFactory

register(UserFactory)       # creates 'user' fixture
register(AuthorFactory)     # creates 'author' fixture
register(ArticleFactory)    # creates 'article' fixture
```

```python
# tests/test_models.py — fixtures are now auto-registered
def test_article_has_title(article):
    assert article.title

def test_author_has_email(author):
    assert '@' in author.email

def test_article_belongs_to_author(article, author):
    article.author = author
    assert article.author == author
```

### Factories with Many-to-Many relationships

```python
class ArticleFactory(DjangoModelFactory):
    class Meta:
        model = Article

    title = factory.Faker('sentence', nb_words=4)

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for tag in extracted:
                self.tags.add(tag)


# Usage:
@pytest.mark.django_db
def test_article_with_tags():
    python_tag = Tag.objects.create(name='python')
    django_tag = Tag.objects.create(name='django')
    article = ArticleFactory(tags=[python_tag, django_tag])
    assert article.tags.count() == 2
```

---

## 16. Mocking — unittest.mock and pytest-mock

Mocking replaces real objects with controlled fakes during a test. Use it to avoid calling real external services (Stripe, Sendgrid, AWS S3), to control time, to force specific return values, and to verify that code called a function with the right arguments.

### `pytest-mock` — the `mocker` fixture

`pytest-mock` provides the `mocker` fixture, which wraps `unittest.mock` but automatically restores all patches after the test. No more `patcher.stop()` calls.

```bash
pip install pytest-mock
```

### Patching a function or method

```python
# myapp/services.py
import requests

def get_weather(city):
    response = requests.get(f'https://api.weather.com/v1/{city}')
    return response.json()['temperature']


# tests/test_services.py
def test_get_weather(mocker):
    mock_response = mocker.MagicMock()
    mock_response.json.return_value = {'temperature': 22}
    
    mocker.patch('myapp.services.requests.get', return_value=mock_response)
    
    result = get_weather('London')
    assert result == 22
```

**Important:** Always patch the name as it is used in the module under test (`myapp.services.requests.get`), not where it is defined (`requests.get`).

### Patching a class and its methods

```python
def test_stripe_charge(mocker):
    mock_stripe = mocker.patch('myapp.payments.stripe')
    mock_stripe.Charge.create.return_value = {
        'id': 'ch_test_123',
        'status': 'succeeded',
    }
    
    result = charge_customer(amount=1000, token='tok_test')
    
    assert result['status'] == 'succeeded'
    mock_stripe.Charge.create.assert_called_once_with(
        amount=1000,
        currency='usd',
        source='tok_test',
    )
```

### `mocker.spy` — call the real function but record calls

```python
def test_send_email_is_called(mocker):
    spy = mocker.spy(email_service, 'send_welcome_email')
    
    register_user('new@example.com')
    
    spy.assert_called_once_with('new@example.com')
    # The real send_welcome_email also ran
```

### Patching `timezone.now` for time-dependent tests

```python
from django.utils import timezone
from datetime import datetime

def test_article_published_at_is_set_correctly(mocker):
    frozen_time = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    mocker.patch('django.utils.timezone.now', return_value=frozen_time)
    
    article = publish_article(Article(title='Test'))
    
    assert article.published_at == frozen_time
```

### Using `pytest-freezegun` for comprehensive time control

```bash
pip install pytest-freezegun
```

```python
import pytest

@pytest.mark.freeze_time('2024-06-15 12:00:00')
def test_scheduled_task_runs_at_noon(db):
    result = run_daily_digest()
    assert result['scheduled_for'] == '2024-06-15 12:00:00'
```

### Patching Django settings

Prefer the `settings` fixture over `mocker.patch` for Django settings, since `settings` handles restoration correctly.

```python
def test_with_custom_setting(settings):
    settings.MAX_ARTICLES_PER_PAGE = 5
    # settings is restored after this test automatically
    assert get_page_size() == 5


def test_feature_disabled_by_default(settings):
    settings.ENABLE_BETA_FEATURES = False
    response = client.get('/beta/')
    assert response.status_code == 404
```

### Asserting mock call arguments

```python
def test_notification_sent_with_correct_args(mocker):
    mock_notify = mocker.patch('myapp.notifications.send_push_notification')
    
    create_order(user_id=42, total=99.99)
    
    # Check it was called exactly once
    mock_notify.assert_called_once()
    
    # Check specific arguments
    mock_notify.assert_called_once_with(
        user_id=42,
        message='Your order of $99.99 has been placed.',
    )
    
    # Inspect call arguments manually
    args, kwargs = mock_notify.call_args
    assert kwargs['user_id'] == 42
    
    # Check it was called multiple times
    create_order(user_id=43, total=50.00)
    assert mock_notify.call_count == 2
    
    # Check it was never called
    mock_notify.reset_mock()
    cancel_order(order_id=1)
    mock_notify.assert_not_called()
```

---

## 17. Testing Signals

### Checking that a signal fires

```python
# tests/test_signals.py
import pytest
from unittest.mock import MagicMock
from django.db.models.signals import post_save
from myapp.models import Article


@pytest.mark.django_db
def test_post_save_signal_fires_on_article_create(mocker):
    handler = MagicMock()
    post_save.connect(handler, sender=Article)
    
    try:
        Article.objects.create(title='Signal Test', body='Body')
        handler.assert_called_once()
        _, kwargs = handler.call_args
        assert kwargs['created'] is True
        assert kwargs['instance'].title == 'Signal Test'
    finally:
        post_save.disconnect(handler, sender=Article)
```

### Using `pytest-mock` with `mocker.patch` on signal handlers

```python
@pytest.mark.django_db
def test_welcome_email_sent_on_user_create(mocker):
    """The post_save signal on User should trigger a welcome email."""
    mock_send = mocker.patch('myapp.signals.send_welcome_email')
    
    User.objects.create_user(username='newuser', email='new@example.com', password='pass')
    
    mock_send.assert_called_once_with('new@example.com')
```

### Disconnecting signals during tests to avoid side effects

```python
@pytest.fixture(autouse=True)
def disable_signals(mocker):
    """
    Disconnect all custom signals during tests to avoid side effects like
    sending emails or making HTTP calls.
    """
    mocker.patch('myapp.signals.send_welcome_email')
    mocker.patch('myapp.signals.notify_slack_on_publish')
```

---

## 18. Testing Celery Tasks

### Synchronous execution with `CELERY_TASK_ALWAYS_EAGER`

The simplest approach: in your test settings, make Celery execute tasks synchronously in the same process.

```python
# settings/test.py
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True   # propagate exceptions from tasks
```

```python
# tests/test_tasks.py
import pytest
from myapp.tasks import generate_report


@pytest.mark.django_db
def test_generate_report_task():
    """With CELERY_TASK_ALWAYS_EAGER=True, the task runs synchronously."""
    result = generate_report.delay(user_id=1)
    assert result.successful()
    assert result.get() == {'status': 'completed', 'rows': 42}
```

### Using `@pytest.mark.celery` from pytest-celery

```bash
pip install pytest-celery
```

```python
import pytest

@pytest.mark.celery
def test_task_executes(celery_worker):
    from myapp.tasks import add
    result = add.delay(3, 4)
    assert result.get(timeout=10) == 7
```

### Testing task logic directly (without Celery infrastructure)

This is the most reliable approach for unit testing the business logic inside a task:

```python
# myapp/tasks.py
@app.task
def process_article(article_id):
    article = Article.objects.get(pk=article_id)
    article.word_count_cache = len(article.body.split())
    article.save()
    return article.word_count_cache


# tests/test_tasks.py
@pytest.mark.django_db
def test_process_article_computes_word_count():
    """Test the task's logic directly, without going through Celery."""
    article = Article.objects.create(title='Test', body='one two three four five')
    
    # Call the underlying function, not .delay() or .apply_async()
    result = process_article(article.pk)
    
    article.refresh_from_db()
    assert result == 5
    assert article.word_count_cache == 5
```

---

## 19. Testing Email

pytest-django's `mailoutbox` fixture captures all emails sent via Django's email backend and exposes them as a list.

```python
# tests/test_email.py
import pytest
from django.core import mail
from myapp.email import send_password_reset, send_order_confirmation


@pytest.mark.django_db
def test_password_reset_email_content(mailoutbox):
    send_password_reset(email='user@example.com', reset_link='https://example.com/reset/abc123')
    
    assert len(mailoutbox) == 1
    email = mailoutbox[0]
    assert email.subject == 'Reset your password'
    assert 'user@example.com' in email.to
    assert 'https://example.com/reset/abc123' in email.body


@pytest.mark.django_db
def test_order_confirmation_sends_html_email(mailoutbox):
    send_order_confirmation(order_id=42, email='buyer@example.com')
    
    assert len(mailoutbox) == 1
    email = mailoutbox[0]
    
    # Check both plain text and HTML parts
    assert len(email.alternatives) > 0
    html_content, content_type = email.alternatives[0]
    assert content_type == 'text/html'
    assert '<h1>Order Confirmed</h1>' in html_content


@pytest.mark.django_db
def test_no_email_sent_for_unverified_user(mailoutbox):
    user = User.objects.create_user(username='new', email_verified=False)
    send_weekly_digest(user)
    assert len(mailoutbox) == 0


@pytest.mark.django_db
def test_bulk_email_send(mailoutbox):
    users = User.objects.bulk_create([
        User(username=f'user{i}', email=f'user{i}@example.com') for i in range(5)
    ])
    send_newsletter_to_all()
    assert len(mailoutbox) == 5
```

---

## 20. Testing File Uploads

### Using `SimpleUploadedFile`

```python
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile


@pytest.mark.django_db
def test_profile_picture_upload(authenticated_client):
    image_content = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100   # minimal PNG header
    image = SimpleUploadedFile(
        name='profile.png',
        content=image_content,
        content_type='image/png',
    )
    response = authenticated_client.post(
        reverse('profile-upload'),
        data={'profile_picture': image},
        format='multipart',
    )
    assert response.status_code == 302


@pytest.mark.django_db
def test_file_type_validation(authenticated_client):
    """Non-image files should be rejected."""
    fake_file = SimpleUploadedFile(
        name='malware.exe',
        content=b'MZ\x90\x00',   # EXE header
        content_type='application/octet-stream',
    )
    response = authenticated_client.post(
        reverse('profile-upload'),
        data={'profile_picture': fake_file},
        format='multipart',
    )
    assert response.status_code == 200   # re-renders form
    assert 'Upload a valid image' in response.content.decode()
```

### Isolating file storage during tests

```python
# conftest.py
import pytest
from django.test import override_settings


@pytest.fixture(autouse=True)
def use_temp_media_dir(tmp_path, settings):
    """
    Redirect MEDIA_ROOT to a temp dir for each test so files don't accumulate
    and tests don't affect each other.
    """
    settings.MEDIA_ROOT = str(tmp_path / 'media')
    settings.DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
```

---

## 21. Testing Management Commands

```python
# tests/test_commands.py
import pytest
from io import StringIO
from django.core.management import call_command


@pytest.mark.django_db
def test_purge_old_articles_command():
    """The purge_old_articles command should delete articles older than 30 days."""
    from datetime import timedelta
    
    old_article = Article.objects.create(
        title='Old',
        body='',
        created_at=timezone.now() - timedelta(days=60),
    )
    new_article = Article.objects.create(title='New', body='')
    
    out = StringIO()
    call_command('purge_old_articles', days=30, stdout=out)
    
    assert not Article.objects.filter(pk=old_article.pk).exists()
    assert Article.objects.filter(pk=new_article.pk).exists()
    assert '1 article(s) deleted' in out.getvalue()


@pytest.mark.django_db
def test_import_articles_from_csv_command(tmp_path):
    """The import_articles command should create articles from a CSV file."""
    csv_file = tmp_path / 'articles.csv'
    csv_file.write_text('title,body\nImported Article,Imported body\n')
    
    call_command('import_articles', str(csv_file))
    
    assert Article.objects.filter(title='Imported Article').exists()


@pytest.mark.django_db
def test_command_with_no_data(capsys):
    """Commands should handle empty datasets gracefully."""
    call_command('purge_old_articles', days=30)
    captured = capsys.readouterr()
    assert '0 article(s) deleted' in captured.out
```

---

## 22. Testing Middleware

```python
# tests/test_middleware.py
import pytest
from django.test import RequestFactory
from myapp.middleware import MaintenanceModeMiddleware


def test_maintenance_mode_returns_503(settings, rf):
    settings.MAINTENANCE_MODE = True
    
    get_response = lambda req: HttpResponse('OK')
    middleware = MaintenanceModeMiddleware(get_response)
    
    request = rf.get('/')
    response = middleware(request)
    
    assert response.status_code == 503
    assert b'maintenance' in response.content.lower()


def test_maintenance_mode_disabled_passes_through(settings, rf):
    settings.MAINTENANCE_MODE = False
    
    get_response = lambda req: HttpResponse('OK', status=200)
    middleware = MaintenanceModeMiddleware(get_response)
    
    request = rf.get('/')
    response = middleware(request)
    
    assert response.status_code == 200


def test_maintenance_mode_allows_admin(settings, rf, admin_user):
    settings.MAINTENANCE_MODE = True
    
    get_response = lambda req: HttpResponse('OK')
    middleware = MaintenanceModeMiddleware(get_response)
    
    request = rf.get('/admin/')
    request.user = admin_user
    response = middleware(request)
    
    assert response.status_code == 200
```

---

## 23. Testing Authentication and Permissions

### Login and logout flows

```python
@pytest.mark.django_db
def test_login_with_valid_credentials(client, user):
    response = client.post(reverse('login'), {
        'username': 'testuser',
        'password': 'testpassword123',
    })
    assert response.status_code == 302
    assert response['Location'] == reverse('dashboard')


@pytest.mark.django_db
def test_login_with_invalid_credentials(client):
    response = client.post(reverse('login'), {
        'username': 'nobody',
        'password': 'wrongpassword',
    })
    assert response.status_code == 200
    assert 'Please enter a correct username and password' in response.content.decode()


@pytest.mark.django_db
def test_logout_clears_session(authenticated_client):
    response = authenticated_client.post(reverse('logout'))
    assert response.status_code == 302
    
    # After logout, accessing a protected page redirects to login
    response = authenticated_client.get(reverse('dashboard'))
    assert response.status_code == 302
    assert '/login/' in response['Location']
```

### Testing object-level permissions

```python
@pytest.mark.django_db
def test_user_can_edit_own_article(authenticated_client, user):
    article = Article.objects.create(title='Mine', body='', author=user)
    
    response = authenticated_client.post(
        reverse('article-edit', kwargs={'pk': article.pk}),
        data={'title': 'Updated', 'body': 'Updated body'},
    )
    assert response.status_code == 302


@pytest.mark.django_db
def test_user_cannot_edit_others_article(authenticated_client):
    other_user = User.objects.create_user(username='other', password='pass')
    article = Article.objects.create(title='Not Mine', body='', author=other_user)
    
    response = authenticated_client.post(
        reverse('article-edit', kwargs={'pk': article.pk}),
        data={'title': 'Hacked', 'body': 'Hacked'},
    )
    assert response.status_code == 403
```

### Using `force_login` for faster authentication in tests

```python
@pytest.fixture
def authenticated_client(client, user):
    """
    Use force_login instead of client.login() to skip password hashing.
    This is faster when using the real password hasher (not MD5PasswordHasher).
    """
    client.force_login(user)
    return client
```

---

## 24. Markers — Categorizing and Controlling Tests

### Built-in markers

```python
# Skip a test unconditionally
@pytest.mark.skip(reason='Not implemented yet')
def test_future_feature():
    pass


# Skip conditionally
import sys
@pytest.mark.skipif(sys.platform == 'win32', reason='Does not run on Windows')
def test_unix_only():
    pass


# Mark a test as expected to fail
@pytest.mark.xfail(reason='Known bug in upstream library, fixed in v2.0')
def test_known_broken_behavior():
    assert buggy_function() == 'correct'

# xfail with strict=True — test MUST fail; if it passes, it counts as a failure
@pytest.mark.xfail(strict=True, reason='This should always fail until fixed')
def test_expected_failure():
    assert False
```

### Custom markers

Register custom markers in `pyproject.toml` (see Section 4), then use them:

```python
@pytest.mark.slow
def test_expensive_computation():
    result = compute_large_dataset()
    assert result > 0


@pytest.mark.integration
def test_payment_gateway(live_server):
    response = requests.post(f'{live_server.url}/pay/', ...)
    assert response.status_code == 200


@pytest.mark.unit
def test_pure_function():
    assert add(1, 2) == 3
```

```bash
# Run only unit tests
pytest -m unit

# Exclude slow tests
pytest -m "not slow"

# Run everything except integration tests (for local dev)
pytest -m "not integration"
```

### The `autouse` fixture — run a fixture for all tests automatically

```python
# conftest.py

@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Clear the rate limiter cache before each test."""
    from myapp.rate_limiting import rate_limit_cache
    rate_limit_cache.clear()
    yield
    rate_limit_cache.clear()


@pytest.fixture(autouse=True, scope='session')
def configure_fake_smtp():
    """Set up a fake SMTP server for the entire session."""
    pass
```

---

## 25. Coverage with pytest-cov

Code coverage tells you which lines of your code were executed during tests. It does not tell you whether your tests are good, but it helps identify untested code paths.

### Installation and basic usage

```bash
pip install pytest-cov
```

```bash
# Run tests with coverage for a specific module
pytest --cov=myapp tests/

# Generate an HTML report
pytest --cov=myapp --cov-report=html tests/

# Generate a terminal report with missing lines
pytest --cov=myapp --cov-report=term-missing tests/

# Combine reports
pytest --cov=myapp --cov-report=term-missing --cov-report=html tests/

# Fail if coverage falls below a threshold
pytest --cov=myapp --cov-fail-under=80 tests/
```

### `.coveragerc` — coverage configuration

```ini
# .coveragerc
[run]
source = myapp
omit =
    */migrations/*
    */tests/*
    */settings/*
    manage.py
    */__init__.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
    if TYPE_CHECKING:

[html]
directory = htmlcov
```

### In `pyproject.toml`

```toml
[tool.coverage.run]
source = ["myapp"]
omit = ["*/migrations/*", "*/tests/*", "manage.py"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
]
fail_under = 80
```

### Excluding specific lines

```python
def debug_info(self):  # pragma: no cover
    """Only used when debugging — excluded from coverage."""
    return f'{self.__class__.__name__}({self.pk})'
```

---

## 26. Performance — Speeding Up Your Test Suite

### Use `pytest-xdist` to run tests in parallel

```bash
pip install pytest-xdist
```

```bash
# Use all available CPU cores
pytest -n auto

# Use a specific number of workers
pytest -n 4
```

**Note:** Parallel testing requires tests to be truly isolated. If tests share state (global variables, external services, specific database IDs), parallel execution will cause intermittent failures.

### Use the `--reuse-db` flag to skip database recreation

```bash
pip install pytest-django
```

```bash
# Create the test database on first run, reuse it on subsequent runs
pytest --reuse-db

# Force recreation (run after adding new migrations)
pytest --create-db
```

### Use a faster password hasher in test settings

```python
# settings/test.py
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]
```

bcrypt (Django's default) is intentionally slow. MD5 is much faster and fine for tests since you are not dealing with real passwords.

### Use `factory.build()` instead of `factory.create()` when possible

```python
# Slow — hits the database
article = ArticleFactory.create()

# Fast — creates the object in memory only
article = ArticleFactory.build()   # use when the test doesn't need the DB
```

### Profile slow tests with `--durations`

```bash
# Show the 10 slowest tests
pytest --durations=10

# Show all test durations
pytest --durations=0
```

### Avoid unnecessary database transactions

```python
# Slow — each call to Article.objects.create() is a separate INSERT
for i in range(100):
    Article.objects.create(title=f'Article {i}', body='')

# Fast — one INSERT
Article.objects.bulk_create([
    Article(title=f'Article {i}', body='') for i in range(100)
])
```

---

## 27. Running Tests in CI

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install -r requirements/test.txt

      - name: Run tests
        env:
          DJANGO_SETTINGS_MODULE: myproject.settings.test
          DATABASE_URL: postgres://postgres:postgres@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379/0
        run: |
          pytest --cov=myapp --cov-report=xml --cov-fail-under=80

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          file: coverage.xml
```

### GitLab CI

```yaml
# .gitlab-ci.yml
test:
  image: python:3.12
  services:
    - postgres:15
    - redis:7

  variables:
    POSTGRES_DB: test_db
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: postgres
    DJANGO_SETTINGS_MODULE: myproject.settings.test
    DATABASE_URL: postgres://postgres:postgres@postgres:5432/test_db

  script:
    - pip install -r requirements/test.txt
    - pytest --cov=myapp --cov-report=term-missing --cov-fail-under=80

  coverage: '/TOTAL.*\s+(\d+%)$/'

  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
```

---

## 28. Project Layout and Organization

### Recommended directory structure

```
myproject/
├── myapp/
│   ├── migrations/
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── serializers.py
│   ├── tasks.py
│   ├── signals.py
│   └── urls.py
├── tests/
│   ├── conftest.py           ← session/module-scoped fixtures, factories registration
│   ├── factories.py          ← all factory_boy factories
│   ├── test_models.py
│   ├── test_views.py
│   ├── test_forms.py
│   ├── test_serializers.py
│   ├── test_tasks.py
│   ├── test_signals.py
│   ├── test_commands.py
│   └── api/
│       ├── conftest.py       ← API-specific fixtures (api_client, etc.)
│       ├── test_articles.py
│       └── test_users.py
├── pyproject.toml
└── manage.py
```

### conftest.py hierarchy

pytest merges `conftest.py` files up the directory tree. Fixtures in a subdirectory's `conftest.py` are only available in that subdirectory.

```python
# tests/conftest.py — top-level, available everywhere
import pytest
from pytest_factoryboy import register
from tests.factories import UserFactory, ArticleFactory

register(UserFactory)
register(ArticleFactory)


@pytest.fixture
def user(db, django_user_model):
    return django_user_model.objects.create_user(
        username='testuser',
        password='testpassword123',
    )

@pytest.fixture
def authenticated_client(client, user):
    client.force_login(user)
    return client
```

```python
# tests/api/conftest.py — only available to tests in tests/api/
import pytest
from rest_framework.test import APIClient

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def authenticated_api_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client
```

### Naming conventions

Test names should describe the scenario being tested. The pattern `test_<thing>_<condition>_<expected_result>` is clear and readable:

```python
def test_article_str_returns_title():             # thing + result
def test_article_publish_sets_published_at():     # thing + condition + result
def test_article_create_without_title_fails():    # thing + condition + result
def test_dashboard_unauthenticated_redirects():   # thing + condition + result
def test_payment_stripe_error_raises_exception(): # thing + condition + result
```

---

## 29. Common Pitfalls & Troubleshooting

**Problem: `django.core.exceptions.ImproperlyConfigured: Requested setting DATABASES...` when running pytest**

Cause: pytest-django cannot find your Django settings module.

Fix: Add `DJANGO_SETTINGS_MODULE` to your `pytest.ini` or `pyproject.toml`:

```ini
[pytest]
DJANGO_SETTINGS_MODULE = myproject.settings
```

---

**Problem: `Failed: Database access not allowed, use the 'django_db' mark`**

Cause: Your test or a fixture it uses is accessing the database without requesting database access.

Fix: Add `@pytest.mark.django_db` to the test, or request the `db` fixture in the fixture that needs database access.

```python
# If the fixture accesses the DB, it must request 'db'
@pytest.fixture
def article(db):          # ← add 'db' here
    return Article.objects.create(title='Test')

# If using transaction features:
@pytest.fixture
def article(transactional_db):
    return Article.objects.create(title='Test')
```

---

**Problem: Tests pass in isolation but fail when run together**

Cause: Tests are not properly isolated. One test is creating or modifying database state that a later test depends on not existing.

Fix: Ensure all database-modifying tests use `@pytest.mark.django_db` (not `transaction=True` unless necessary). Check for `autouse` fixtures that might be sharing state. Avoid `scope='session'` for mutable data.

---

**Problem: `fixture 'db' not found` when using `scope='class'` or `scope='module'` fixtures**

Cause: The `db` fixture has `function` scope by default. Higher-scope fixtures cannot depend on lower-scope fixtures.

Fix: Use `django_db_setup` or `django_db_blocker` for session-scoped database access:

```python
@pytest.fixture(scope='module')
def shared_data(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        Article.objects.create(title='Shared')
        yield
        Article.objects.all().delete()
```

---

**Problem: `mocker.patch` is not restoring the original after the test**

Cause: You are using `unittest.mock.patch` directly instead of `mocker.patch`.

Fix: Always use `mocker.patch` from the `pytest-mock` `mocker` fixture. It registers all patches for automatic cleanup.

```python
# BAD — you must call patcher.stop() manually
patcher = patch('myapp.utils.requests.get')
mock_get = patcher.start()

# GOOD — mocker handles cleanup automatically
def test_something(mocker):
    mock_get = mocker.patch('myapp.utils.requests.get')
```

---

**Problem: `Live server tests fail with 'address already in use'`**

Cause: A previous test run left a port open.

Fix: Specify a port range: `pytest --live-server-url=http://localhost:8081`.

---

**Problem: Tests are very slow**

Diagnoses and fixes:

```bash
# Find the slowest tests
pytest --durations=10

# If most slowness is in DB setup, use --reuse-db
pytest --reuse-db

# If password hashing is slow, add to test settings:
# PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

# If you have many isolated tests hitting the DB, try parallel execution
pytest -n auto
```

---

**Problem: `factory_boy` raises `IntegrityError` on unique fields**

Cause: `factory.Sequence` or `factory.Faker` is generating duplicate values for a unique field.

Fix: Use `factory.Sequence` for unique fields:

```python
class UserFactory(DjangoModelFactory):
    username = factory.Sequence(lambda n: f'user_{n}')
    email = factory.Sequence(lambda n: f'user_{n}@example.com')
```

---

**Problem: Tests work locally but fail in CI with `ALLOWED_HOSTS` error**

Cause: `ALLOWED_HOSTS` does not include the test client's server name (`testserver` by default).

Fix: Add `testserver` to `ALLOWED_HOSTS` in your test settings:

```python
ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']
```

---

## 30. Checklist

Use this every time you add testing infrastructure to a Django project.

### Initial Setup

- [ ] `pytest`, `pytest-django`, `pytest-cov`, `pytest-mock`, `factory-boy` are installed
- [ ] `DJANGO_SETTINGS_MODULE` is set in `pyproject.toml` or `pytest.ini`
- [ ] A dedicated test settings file exists with a faster password hasher
- [ ] `conftest.py` is created at the project root with shared fixtures
- [ ] Custom markers are declared in `pyproject.toml` to avoid warnings

### Writing Tests

- [ ] Every test that touches the database uses `@pytest.mark.django_db` or the `db` fixture
- [ ] Tests that need real transactions use `@pytest.mark.django_db(transaction=True)`
- [ ] Test names follow the `test_<thing>_<condition>_<result>` convention
- [ ] Tests do not depend on each other or on execution order
- [ ] No hardcoded primary keys or database IDs in tests
- [ ] All password creation uses `create_user()` or `force_login()`; no hardcoded hash strings

### Fixtures

- [ ] Shared fixtures live in `conftest.py`, not imported between test files
- [ ] Fixtures that access the database request `db` or `transactional_db`
- [ ] `yield` is used for fixtures that need teardown
- [ ] `autouse=True` is used sparingly and only for truly universal setup

### Factories

- [ ] A `factories.py` file exists with a factory for every major model
- [ ] Unique fields use `factory.Sequence` to avoid `IntegrityError`
- [ ] `SubFactory` is used for FK relationships
- [ ] Factories use `build()` in tests that don't need the database

### Mocking

- [ ] `mocker.patch` (from `pytest-mock`) is used instead of `unittest.mock.patch` directly
- [ ] Patches target the name as used in the module under test, not where defined
- [ ] Time-dependent code uses the `settings` fixture or `mocker.patch` on `timezone.now`

### Coverage

- [ ] `pytest-cov` is configured to report coverage for the project source
- [ ] Migrations and test files are excluded from coverage
- [ ] A minimum coverage threshold (`--cov-fail-under`) is set in CI

### CI

- [ ] The CI workflow installs all test dependencies
- [ ] Database and Redis services are configured in CI
- [ ] The correct `DJANGO_SETTINGS_MODULE` is set in CI environment variables
- [ ] Coverage reports are generated and uploaded to a coverage service

---

*Official docs:*  
*pytest: https://docs.pytest.org/*  
*pytest-django: https://pytest-django.readthedocs.io/*  
*factory_boy: https://factoryboy.readthedocs.io/*  
*pytest-mock: https://pytest-mock.readthedocs.io/*
