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

## Overview

Testing is essential for maintaining code quality and preventing regressions. Django provides a comprehensive testing framework built on Python's unittest.

## Test Structure

### Directory Structure

```
myapp/
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_views.py
│   ├── test_serializers.py
│   ├── test_forms.py
│   ├── test_api.py
│   ├── test_utils.py
│   ├── factories.py
│   └── fixtures/
│       ├── users.json
│       └── articles.json
├── models.py
├── views.py
└── serializers.py
```

### Basic Test Class

```python
from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class BasicTestCase(TestCase):
    """Basic test case example."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def tearDown(self):
        """Clean up after tests."""
        pass
    
    def test_user_creation(self):
        """Test user was created successfully."""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertTrue(self.user.check_password('testpass123'))
```

## Unit Tests

### Model Tests

```python
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from myapp.models import Article, Category

class ArticleModelTest(TestCase):
    """Test Article model."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up data for the whole TestCase."""
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
        """Set up data for each test method."""
        self.article = Article.objects.create(
            title='Test Article',
            slug='test-article',
            content='Test content',
            author=self.user,
            category=self.category
        )
    
    def test_article_creation(self):
        """Test article is created correctly."""
        self.assertEqual(self.article.title, 'Test Article')
        self.assertEqual(self.article.slug, 'test-article')
        self.assertEqual(self.article.author, self.user)
        self.assertIsInstance(self.article.created_at, timezone.datetime)
    
    def test_article_str_representation(self):
        """Test article string representation."""
        self.assertEqual(str(self.article), 'Test Article')
    
    def test_article_absolute_url(self):
        """Test article get_absolute_url method."""
        expected_url = f'/articles/{self.article.slug}/'
        self.assertEqual(self.article.get_absolute_url(), expected_url)
    
    def test_article_slug_unique(self):
        """Test article slug must be unique."""
        with self.assertRaises(ValidationError):
            duplicate = Article(
                title='Another Article',
                slug='test-article',  # Duplicate slug
                content='Content',
                author=self.user,
                category=self.category
            )
            duplicate.full_clean()
    
    def test_article_ordering(self):
        """Test articles are ordered by created_at descending."""
        article2 = Article.objects.create(
            title='Second Article',
            slug='second-article',
            content='Content',
            author=self.user,
            category=self.category
        )
        articles = Article.objects.all()
        self.assertEqual(articles[0], article2)
        self.assertEqual(articles[1], self.article)
    
    def test_article_published_manager(self):
        """Test published manager returns only published articles."""
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

```python
from django.test import TestCase
from myapp.models import Article

class ArticleManagerTest(TestCase):
    """Test Article custom manager."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='password123'
        )
        
        # Create articles with different statuses
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
        """Test published manager filters correctly."""
        published_articles = Article.published.all()
        self.assertEqual(published_articles.count(), 1)
        self.assertEqual(published_articles[0], self.published)
    
    def test_by_author_method(self):
        """Test by_author queryset method."""
        articles = Article.objects.by_author(self.user)
        self.assertEqual(articles.count(), 2)
    
    def test_search_method(self):
        """Test search queryset method."""
        articles = Article.objects.search('Published')
        self.assertEqual(articles.count(), 1)
        self.assertEqual(articles[0], self.published)
```

### Form Tests

```python
from django.test import TestCase
from myapp.forms import ArticleForm

class ArticleFormTest(TestCase):
    """Test ArticleForm."""
    
    def test_valid_form(self):
        """Test form with valid data."""
        form_data = {
            'title': 'Test Article',
            'slug': 'test-article',
            'content': 'Test content',
            'status': 'draft',
        }
        form = ArticleForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_invalid_form_missing_title(self):
        """Test form is invalid without title."""
        form_data = {
            'slug': 'test-article',
            'content': 'Test content',
        }
        form = ArticleForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)
    
    def test_form_slug_validation(self):
        """Test form validates slug format."""
        form_data = {
            'title': 'Test Article',
            'slug': 'invalid slug!',  # Invalid characters
            'content': 'Test content',
        }
        form = ArticleForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('slug', form.errors)
    
    def test_form_save(self):
        """Test form saves data correctly."""
        form_data = {
            'title': 'Test Article',
            'slug': 'test-article',
            'content': 'Test content',
            'status': 'draft',
        }
        form = ArticleForm(data=form_data)
        self.assertTrue(form.is_valid())
        
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

```python
from django.test import TestCase, Client
from django.urls import reverse
from myapp.models import Article

class ArticleViewTest(TestCase):
    """Test Article views."""
    
    def setUp(self):
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
        """Test article list view."""
        url = reverse('article-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Article')
        self.assertTemplateUsed(response, 'articles/list.html')
    
    def test_article_detail_view(self):
        """Test article detail view."""
        url = reverse('article-detail', kwargs={'slug': self.article.slug})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.article.title)
        self.assertContains(response, self.article.content)
        self.assertEqual(response.context['article'], self.article)
    
    def test_article_create_view_requires_login(self):
        """Test create view requires authentication."""
        url = reverse('article-create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_article_create_view_logged_in(self):
        """Test create view when logged in."""
        self.client.login(username='testuser', password='password123')
        url = reverse('article-create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'articles/form.html')
    
    def test_article_create_post(self):
        """Test creating article via POST."""
        self.client.login(username='testuser', password='password123')
        url = reverse('article-create')
        data = {
            'title': 'New Article',
            'slug': 'new-article',
            'content': 'New content',
            'status': 'draft',
        }
        response = self.client.post(url, data)
        
        self.assertEqual(Article.objects.count(), 2)
        new_article = Article.objects.get(slug='new-article')
        self.assertEqual(new_article.title, 'New Article')
        self.assertEqual(new_article.author, self.user)
    
    def test_article_update_view(self):
        """Test updating article."""
        self.client.login(username='testuser', password='password123')
        url = reverse('article-update', kwargs={'slug': self.article.slug})
        data = {
            'title': 'Updated Title',
            'slug': self.article.slug,
            'content': self.article.content,
            'status': self.article.status,
        }
        response = self.client.post(url, data)
        
        self.article.refresh_from_db()
        self.assertEqual(self.article.title, 'Updated Title')
    
    def test_article_delete_view(self):
        """Test deleting article."""
        self.client.login(username='testuser', password='password123')
        url = reverse('article-delete', kwargs={'slug': self.article.slug})
        response = self.client.post(url)
        
        self.assertEqual(Article.objects.count(), 0)
        self.assertRedirects(response, reverse('article-list'))
```

## Integration Tests

### Transaction Test Case

```python
from django.test import TransactionTestCase
from myapp.models import Article
from myapp.tasks import process_article

class ArticleIntegrationTest(TransactionTestCase):
    """Integration tests for article processing."""
    
    def test_article_processing_workflow(self):
        """Test complete article processing workflow."""
        user = User.objects.create_user(
            username='testuser',
            password='password123'
        )
        
        # Create article
        article = Article.objects.create(
            title='Test Article',
            slug='test-article',
            content='Test content',
            author=user,
            status='draft'
        )
        
        # Process article (assuming this triggers various operations)
        result = process_article(article.id)
        
        # Verify processing
        article.refresh_from_db()
        self.assertEqual(article.status, 'published')
        self.assertTrue(result['success'])
```

### Database Integration Tests

```python
from django.test import TestCase
from django.db import connection
from django.test.utils import CaptureQueriesContext

class DatabaseIntegrationTest(TestCase):
    """Test database interactions."""
    
    def test_query_optimization(self):
        """Test that queries are optimized."""
        # Create test data
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
        
        # Test query count
        with CaptureQueriesContext(connection) as context:
            articles = list(Article.objects.select_related('author').all())
            
        # Should use select_related to reduce queries
        self.assertLess(len(context.captured_queries), 3)
```

## Test-Driven Development (TDD)

### TDD Example: Creating a Feature

```python
# Step 1: Write failing test
class ArticleLikeFeatureTest(TestCase):
    """Test article like feature (TDD)."""
    
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
        """Test user can like an article."""
        # This will fail initially
        self.article.like(self.user)
        self.assertEqual(self.article.likes.count(), 1)
        self.assertIn(self.user, self.article.likes.all())
    
    def test_user_cannot_like_article_twice(self):
        """Test user cannot like article multiple times."""
        self.article.like(self.user)
        self.article.like(self.user)  # Second like
        self.assertEqual(self.article.likes.count(), 1)
    
    def test_user_can_unlike_article(self):
        """Test user can unlike an article."""
        self.article.like(self.user)
        self.article.unlike(self.user)
        self.assertEqual(self.article.likes.count(), 0)

# Step 2: Implement feature to make tests pass
# models.py
class Article(models.Model):
    # ... existing fields ...
    likes = models.ManyToManyField(User, related_name='liked_articles', blank=True)
    
    def like(self, user):
        """Add user to likes."""
        self.likes.add(user)
    
    def unlike(self, user):
        """Remove user from likes."""
        self.likes.remove(user)
    
    def is_liked_by(self, user):
        """Check if user has liked this article."""
        return self.likes.filter(id=user.id).exists()

# Step 3: Run tests - they should pass now
```

### Red-Green-Refactor Cycle

```python
# RED: Write failing test
def test_article_read_time(self):
    """Test article calculates read time correctly."""
    article = Article.objects.create(
        title='Test',
        slug='test',
        content='word ' * 300,  # 300 words
        author=self.user
    )
    # Assuming average reading speed of 200 words/minute
    self.assertEqual(article.read_time, 2)  # Will fail

# GREEN: Make it pass
class Article(models.Model):
    # ... fields ...
    
    @property
    def read_time(self):
        """Calculate estimated read time in minutes."""
        word_count = len(self.content.split())
        minutes = word_count / 200  # 200 words per minute
        return max(1, round(minutes))

# REFACTOR: Improve implementation
class Article(models.Model):
    # ... fields ...
    
    WORDS_PER_MINUTE = 200
    
    @property
    def read_time(self):
        """Calculate estimated read time in minutes."""
        word_count = len(self.content.split())
        minutes = word_count / self.WORDS_PER_MINUTE
        return max(1, round(minutes))
    
    @property
    def word_count(self):
        """Get word count of article content."""
        return len(self.content.split())
```

## Fixtures and Factories

### JSON Fixtures

```python
# tests/fixtures/users.json
[
    {
        "model": "auth.user",
        "pk": 1,
        "fields": {
            "username": "testuser",
            "email": "test@example.com",
            "is_staff": false,
            "is_active": true
        }
    }
]
```

```python
# Using fixtures in tests
class ArticleWithFixturesTest(TestCase):
    """Test with JSON fixtures."""
    
    fixtures = ['users.json', 'articles.json']
    
    def test_fixture_data(self):
        """Test that fixture data is loaded."""
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Article.objects.count(), 5)
```

### Factory Boy

```python
# Install: pip install factory-boy

# tests/factories.py
import factory
from factory.django import DjangoModelFactory
from myapp.models import Article, Category

class UserFactory(DjangoModelFactory):
    """Factory for User model."""
    
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True


class CategoryFactory(DjangoModelFactory):
    """Factory for Category model."""
    
    class Meta:
        model = Category
    
    name = factory.Sequence(lambda n: f'Category {n}')
    slug = factory.LazyAttribute(lambda obj: obj.name.lower().replace(' ', '-'))


class ArticleFactory(DjangoModelFactory):
    """Factory for Article model."""
    
    class Meta:
        model = Article
    
    title = factory.Sequence(lambda n: f'Article {n}')
    slug = factory.LazyAttribute(lambda obj: obj.title.lower().replace(' ', '-'))
    content = factory.Faker('text', max_nb_chars=1000)
    author = factory.SubFactory(UserFactory)
    category = factory.SubFactory(CategoryFactory)
    status = 'published'
    
    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        """Add tags after article creation."""
        if not create:
            return
        
        if extracted:
            for tag in extracted:
                self.tags.add(tag)
```

```python
# Using factories in tests
from myapp.tests.factories import ArticleFactory, UserFactory

class ArticleFactoryTest(TestCase):
    """Test using factories."""
    
    def test_create_article_with_factory(self):
        """Test creating article with factory."""
        article = ArticleFactory()
        self.assertIsNotNone(article.id)
        self.assertIsNotNone(article.author)
        self.assertEqual(article.status, 'published')
    
    def test_create_multiple_articles(self):
        """Test creating multiple articles."""
        articles = ArticleFactory.create_batch(5)
        self.assertEqual(len(articles), 5)
        self.assertEqual(Article.objects.count(), 5)
    
    def test_override_factory_attributes(self):
        """Test overriding factory attributes."""
        user = UserFactory(username='specificuser')
        article = ArticleFactory(
            title='Specific Title',
            author=user,
            status='draft'
        )
        self.assertEqual(article.title, 'Specific Title')
        self.assertEqual(article.author.username, 'specificuser')
        self.assertEqual(article.status, 'draft')
```

## Mocking

### Mocking External Services

```python
from unittest.mock import patch, Mock
from django.test import TestCase
from myapp.services import ArticleService

class ArticleServiceTest(TestCase):
    """Test ArticleService with mocking."""
    
    @patch('myapp.services.requests.get')
    def test_fetch_external_data(self, mock_get):
        """Test fetching data from external API."""
        # Mock the response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'title': 'External Article',
            'content': 'External content'
        }
        mock_get.return_value = mock_response
        
        # Call service
        service = ArticleService()
        result = service.fetch_external_article(123)
        
        # Assertions
        self.assertEqual(result['title'], 'External Article')
        mock_get.assert_called_once_with('https://api.example.com/articles/123')
    
    @patch('myapp.services.send_mail')
    def test_send_notification(self, mock_send_mail):
        """Test sending email notification."""
        article = ArticleFactory()
        
        service = ArticleService()
        service.send_publication_notification(article)
        
        # Verify email was sent
        mock_send_mail.assert_called_once()
        args, kwargs = mock_send_mail.call_args
        self.assertIn(article.title, args[1])  # Subject contains title
```

### Mocking Django Methods

```python
from unittest.mock import patch
from django.test import TestCase
from django.utils import timezone

class ArticleTimestampTest(TestCase):
    """Test article timestamps with mocking."""
    
    @patch('django.utils.timezone.now')
    def test_article_creation_timestamp(self, mock_now):
        """Test article created_at timestamp."""
        fake_time = timezone.datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_now.return_value = fake_time
        
        article = ArticleFactory()
        
        self.assertEqual(article.created_at, fake_time)
```

### Mocking Celery Tasks

```python
from unittest.mock import patch
from django.test import TestCase
from myapp.tasks import process_article_task

class CeleryTaskTest(TestCase):
    """Test Celery tasks."""
    
    @patch('myapp.tasks.process_article_task.delay')
    def test_task_called(self, mock_task):
        """Test that Celery task is called."""
        article = ArticleFactory()
        
        # Trigger action that should call task
        article.publish()
        
        # Verify task was called
        mock_task.assert_called_once_with(article.id)
    
    def test_task_execution(self):
        """Test actual task execution."""
        article = ArticleFactory(status='draft')
        
        # Execute task synchronously
        result = process_article_task(article.id)
        
        # Verify results
        article.refresh_from_db()
        self.assertEqual(article.status, 'published')
        self.assertTrue(result['success'])
```

## API Testing

### DRF API Test Case

```python
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse

class ArticleAPITest(APITestCase):
    """Test Article API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.article = ArticleFactory(author=self.user)
    
    def test_article_list(self):
        """Test listing articles."""
        url = reverse('api:article-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_article_detail(self):
        """Test retrieving article detail."""
        url = reverse('api:article-detail', kwargs={'pk': self.article.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.article.title)
    
    def test_create_article_unauthenticated(self):
        """Test creating article without authentication."""
        url = reverse('api:article-list')
        data = {
            'title': 'New Article',
            'content': 'New content',
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_article_authenticated(self):
        """Test creating article with authentication."""
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
        """Test updating article."""
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
        self.article.refresh_from_db()
        self.assertEqual(self.article.title, 'Updated Title')
    
    def test_delete_article(self):
        """Test deleting article."""
        self.client.force_authenticate(user=self.user)
        url = reverse('api:article-detail', kwargs={'pk': self.article.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Article.objects.count(), 0)
    
    def test_pagination(self):
        """Test API pagination."""
        ArticleFactory.create_batch(25)
        url = reverse('api:article-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(len(response.data['results']), 20)  # Default page size
    
    def test_filtering(self):
        """Test API filtering."""
        draft = ArticleFactory(status='draft')
        published = ArticleFactory(status='published')
        
        url = reverse('api:article-list')
        response = self.client.get(url, {'status': 'published'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], published.id)
```

### Testing API Permissions

```python
from rest_framework.test import APITestCase

class ArticlePermissionTest(APITestCase):
    """Test article API permissions."""
    
    def setUp(self):
        self.owner = UserFactory()
        self.other_user = UserFactory()
        self.staff_user = UserFactory(is_staff=True)
        self.article = ArticleFactory(author=self.owner)
    
    def test_owner_can_update(self):
        """Test article owner can update."""
        self.client.force_authenticate(user=self.owner)
        url = reverse('api:article-detail', kwargs={'pk': self.article.pk})
        data = {'title': 'Updated'}
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_non_owner_cannot_update(self):
        """Test non-owner cannot update."""
        self.client.force_authenticate(user=self.other_user)
        url = reverse('api:article-detail', kwargs={'pk': self.article.pk})
        data = {'title': 'Updated'}
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_staff_can_update(self):
        """Test staff user can update any article."""
        self.client.force_authenticate(user=self.staff_user)
        url = reverse('api:article-detail', kwargs={'pk': self.article.pk})
        data = {'title': 'Updated'}
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
```

## Test Coverage

### Measuring Coverage

```bash
# Install coverage
pip install coverage

# Run tests with coverage
coverage run --source='.' manage.py test

# Generate report
coverage report

# Generate HTML report
coverage html

# View HTML report
open htmlcov/index.html
```

### Coverage Configuration

```ini
# .coveragerc
[run]
source = .
omit =
    */migrations/*
    */tests/*
    */venv/*
    */virtualenv/*
    manage.py
    */settings/*
    */wsgi.py
    */asgi.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if settings.DEBUG
    if TYPE_CHECKING:
```

### Coverage in Tests

```python
class CoverageTest(TestCase):
    """Ensure critical code paths are tested."""
    
    def test_all_model_methods(self):
        """Test all custom model methods."""
        article = ArticleFactory()
        
        # Test each custom method
        article.publish()
        article.unpublish()
        article.archive()
        self.assertTrue(article.is_published())
        self.assertIsNotNone(article.get_related_articles())
```

## Performance Testing

### Load Testing

```python
from django.test import TestCase
from django.test.utils import override_settings
import time

class PerformanceTest(TestCase):
    """Test application performance."""
    
    def test_article_list_performance(self):
        """Test article list view performance."""
        # Create test data
        ArticleFactory.create_batch(100)
        
        # Measure response time
        start_time = time.time()
        response = self.client.get(reverse('article-list'))
        end_time = time.time()
        
        # Assert response time is acceptable
        response_time = end_time - start_time
        self.assertLess(response_time, 1.0)  # Less than 1 second
        self.assertEqual(response.status_code, 200)
    
    def test_query_count(self):
        """Test number of database queries."""
        ArticleFactory.create_batch(10)
        
        with self.assertNumQueries(2):  # Should use select_related/prefetch_related
            articles = list(
                Article.objects.select_related('author')
                .prefetch_related('tags')
                .all()
            )
```

### Profiling Tests

```python
from django.test import TestCase
import cProfile
import pstats

class ProfilingTest(TestCase):
    """Profile code performance."""
    
    def test_with_profiling(self):
        """Test with profiling enabled."""
        profiler = cProfile.Profile()
        profiler.enable()
        
        # Code to profile
        ArticleFactory.create_batch(100)
        articles = Article.objects.all()
        list(articles)
        
        profiler.disable()
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')
        stats.print_stats(10)  # Print top 10
```

## Best Practices

### Test Organization

```python
# ✅ GOOD: Clear test organization
class ArticleModelTest(TestCase):
    """Test Article model functionality."""
    
    def test_article_creation(self):
        """Test article is created with correct attributes."""
        pass
    
    def test_article_validation(self):
        """Test article field validation."""
        pass


class ArticleManagerTest(TestCase):
    """Test Article custom manager."""
    
    def test_published_queryset(self):
        """Test published() queryset method."""
        pass


class ArticleAPITest(APITestCase):
    """Test Article API endpoints."""
    
    def test_list_endpoint(self):
        """Test GET /api/articles/."""
        pass

# ❌ BAD: Mixed concerns in single test class
class ArticleTest(TestCase):
    """Test everything about articles."""
    # Tests models, views, API, forms all mixed together
```

### Test Naming

```python
# ✅ GOOD: Descriptive test names
def test_user_cannot_delete_other_users_article(self):
    """Test that users can only delete their own articles."""
    pass

def test_article_slug_generated_from_title(self):
    """Test slug is auto-generated from title if not provided."""
    pass

# ❌ BAD: Vague test names
def test_article(self):
    pass

def test_delete(self):
    pass
```

### Test Independence

```python
# ✅ GOOD: Each test is independent
class ArticleTest(TestCase):
    def setUp(self):
        """Create fresh data for each test."""
        self.article = ArticleFactory()
    
    def test_publish(self):
        """Test publishing article."""
        self.article.publish()
        self.assertEqual(self.article.status, 'published')
    
    def test_unpublish(self):
        """Test unpublishing article."""
        self.article.publish()
        self.article.unpublish()
        self.assertEqual(self.article.status, 'draft')

# ❌ BAD: Tests depend on each other
class ArticleTest(TestCase):
    def test_1_create(self):
        self.article = ArticleFactory()
    
    def test_2_publish(self):
        # Depends on test_1
        self.article.publish()
```

### Assertion Messages

```python
# ✅ GOOD: Helpful assertion messages
self.assertEqual(
    article.status,
    'published',
    'Article should be published after calling publish()'
)

self.assertTrue(
    article.is_visible,
    f'Article {article.id} should be visible but is hidden'
)

# ✅ GOOD: Use specific assertions
self.assertIn(user, article.likes.all())
self.assertIsNone(article.published_at)
self.assertGreater(article.view_count, 0)
```

### Test Data Management

```python
# ✅ GOOD: Use setUpTestData for shared read-only data
class ArticleReadOnlyTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        """Create data once for all tests in this class."""
        cls.user = UserFactory()
        cls.category = CategoryFactory()
        cls.articles = ArticleFactory.create_batch(10)
    
    def test_count(self):
        """Test article count."""
        self.assertEqual(Article.objects.count(), 10)
    
    def test_category(self):
        """Test articles have category."""
        for article in self.articles:
            self.assertIsNotNone(article.category)

# ✅ GOOD: Use setUp for data that tests might modify
class ArticleModifyTest(TestCase):
    def setUp(self):
        """Create fresh data for each test."""
        self.article = ArticleFactory()
    
    def test_update(self):
        """Test updating article."""
        self.article.title = 'New Title'
        self.article.save()
```

### Testing Edge Cases

```python
class ArticleEdgeCaseTest(TestCase):
    """Test edge cases and error conditions."""
    
    def test_empty_content(self):
        """Test article with empty content."""
        article = ArticleFactory(content='')
        self.assertEqual(article.word_count, 0)
        self.assertEqual(article.read_time, 1)  # Minimum 1 minute
    
    def test_very_long_title(self):
        """Test article with maximum length title."""
        long_title = 'A' * 200
        article = ArticleFactory(title=long_title)
        self.assertEqual(len(article.title), 200)
    
    def test_special_characters_in_slug(self):
        """Test slug generation with special characters."""
        article = ArticleFactory(title='Test!@#$%^&*()')
        self.assertRegex(article.slug, r'^[a-z0-9-]+$')
    
    def test_duplicate_slug_handling(self):
        """Test handling of duplicate slugs."""
        ArticleFactory(slug='test-article')
        with self.assertRaises(ValidationError):
            article = Article(
                title='Test',
                slug='test-article',
                content='Content',
                author=UserFactory()
            )
            article.full_clean()
```
