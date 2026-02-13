# Django Serializers Guidelines

## Table of Contents
- [Overview](#overview)
- [Basic Serializers](#basic-serializers)
- [ModelSerializer](#modelserializer)
- [Field Types](#field-types)
- [Validation](#validation)
- [Nested Serializers](#nested-serializers)
- [SerializerMethodField](#serializermethodfield)
- [Performance Optimization](#performance-optimization)
- [Best Practices](#best-practices)

## Overview

Serializers in Django REST Framework convert complex data types (like Django models) to Python native datatypes that can be easily rendered into JSON, XML, or other content types, and vice versa.

## Basic Serializers

### Simple Serializer

```python
from rest_framework import serializers

class ArticleSerializer(serializers.Serializer):
    """Basic serializer for Article model"""
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(max_length=200)
    content = serializers.CharField()
    author = serializers.CharField(max_length=100)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    def create(self, validated_data):
        """Create and return a new Article instance"""
        return Article.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        """Update and return an existing Article instance"""
        instance.title = validated_data.get('title', instance.title)
        instance.content = validated_data.get('content', instance.content)
        instance.author = validated_data.get('author', instance.author)
        instance.save()
        return instance
```

## ModelSerializer

### Basic ModelSerializer

```python
from rest_framework import serializers
from .models import Article, Category, Tag

class ArticleSerializer(serializers.ModelSerializer):
    """ModelSerializer for Article model"""
    
    class Meta:
        model = Article
        fields = ['id', 'title', 'slug', 'content', 'author', 'created_at']
        # Or use '__all__' for all fields
        # fields = '__all__'
        
        # Exclude specific fields
        # exclude = ['internal_notes']
        
        # Read-only fields
        read_only_fields = ['id', 'created_at', 'updated_at', 'slug']
```

### Field-Level Control

```python
class ArticleSerializer(serializers.ModelSerializer):
    """Serializer with field-level control"""
    
    # Override field
    title = serializers.CharField(max_length=300, required=True)
    
    # Make field write-only (e.g., for passwords)
    password = serializers.CharField(write_only=True)
    
    # Make field read-only
    view_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Article
        fields = ['id', 'title', 'content', 'password', 'view_count']
        extra_kwargs = {
            'content': {
                'required': True,
                'allow_blank': False,
                'min_length': 100
            },
            'slug': {
                'required': False,
                'allow_blank': True
            }
        }
```

## Field Types

### Common Field Types

```python
class ExampleSerializer(serializers.Serializer):
    # String fields
    char_field = serializers.CharField(max_length=100)
    text_field = serializers.CharField(style={'base_template': 'textarea.html'})
    email_field = serializers.EmailField()
    regex_field = serializers.RegexField(regex=r'^[0-9]+$')
    slug_field = serializers.SlugField()
    url_field = serializers.URLField()
    
    # Numeric fields
    integer_field = serializers.IntegerField(min_value=0, max_value=100)
    float_field = serializers.FloatField()
    decimal_field = serializers.DecimalField(max_digits=10, decimal_places=2)
    
    # Boolean field
    boolean_field = serializers.BooleanField()
    
    # Date and time fields
    date_field = serializers.DateField()
    time_field = serializers.TimeField()
    datetime_field = serializers.DateTimeField()
    duration_field = serializers.DurationField()
    
    # Choice field
    CHOICES = [('draft', 'Draft'), ('published', 'Published')]
    choice_field = serializers.ChoiceField(choices=CHOICES)
    
    # File fields
    file_field = serializers.FileField()
    image_field = serializers.ImageField()
    
    # Composite fields
    list_field = serializers.ListField(child=serializers.CharField())
    dict_field = serializers.DictField()
    json_field = serializers.JSONField()
    
    # Relational fields
    primary_key_field = serializers.PrimaryKeyRelatedField(queryset=Article.objects.all())
    hyperlinked_field = serializers.HyperlinkedRelatedField(
        view_name='article-detail',
        queryset=Article.objects.all()
    )
    slug_related_field = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Article.objects.all()
    )
```

### Custom Fields

```python
class ColorField(serializers.Field):
    """Custom field for color values"""
    
    def to_representation(self, value):
        """Convert internal value to external representation"""
        return value.lower()
    
    def to_internal_value(self, data):
        """Convert external representation to internal value"""
        if not isinstance(data, str):
            raise serializers.ValidationError('String required')
        
        if not data.startswith('#'):
            raise serializers.ValidationError('Color must start with #')
        
        if len(data) != 7:
            raise serializers.ValidationError('Color must be in format #RRGGBB')
        
        return data.upper()

class ProductSerializer(serializers.ModelSerializer):
    color = ColorField()
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'color']
```

## Validation

### Field-Level Validation

```python
class ArticleSerializer(serializers.ModelSerializer):
    """Serializer with field-level validation"""
    
    def validate_title(self, value):
        """
        Validate title field.
        Method name must be validate_<field_name>
        """
        if len(value) < 5:
            raise serializers.ValidationError(
                'Title must be at least 5 characters long'
            )
        
        if Article.objects.filter(title=value).exists():
            raise serializers.ValidationError(
                'Article with this title already exists'
            )
        
        return value
    
    def validate_content(self, value):
        """Validate content field"""
        word_count = len(value.split())
        if word_count < 100:
            raise serializers.ValidationError(
                f'Content must be at least 100 words. Current: {word_count}'
            )
        return value
    
    class Meta:
        model = Article
        fields = ['id', 'title', 'content', 'author']
```

### Object-Level Validation

```python
class ArticleSerializer(serializers.ModelSerializer):
    """Serializer with object-level validation"""
    
    def validate(self, data):
        """
        Validate the entire object.
        This runs after all field-level validation.
        """
        # Cross-field validation
        if data.get('status') == 'published' and not data.get('published_date'):
            raise serializers.ValidationError({
                'published_date': 'Published date is required for published articles'
            })
        
        # Business logic validation
        if data.get('published_date'):
            from django.utils import timezone
            if data['published_date'] < timezone.now():
                raise serializers.ValidationError(
                    'Published date cannot be in the past'
                )
        
        return data
    
    class Meta:
        model = Article
        fields = ['id', 'title', 'status', 'published_date']
```

### Custom Validators

```python
def validate_word_count(value):
    """Validate minimum word count"""
    word_count = len(value.split())
    if word_count < 100:
        raise serializers.ValidationError(
            f'Must be at least 100 words. Current: {word_count}'
        )

class UniqueSlugValidator:
    """Custom validator class for unique slugs"""
    
    def __init__(self, queryset):
        self.queryset = queryset
    
    def __call__(self, value):
        if self.queryset.filter(slug=value).exists():
            raise serializers.ValidationError('Slug must be unique')

class ArticleSerializer(serializers.ModelSerializer):
    content = serializers.CharField(validators=[validate_word_count])
    slug = serializers.SlugField(
        validators=[UniqueSlugValidator(queryset=Article.objects.all())]
    )
    
    class Meta:
        model = Article
        fields = ['id', 'title', 'slug', 'content']
```

## Nested Serializers

### Basic Nesting

```python
class AuthorSerializer(serializers.ModelSerializer):
    """Serializer for Author"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category"""
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']

class ArticleSerializer(serializers.ModelSerializer):
    """Serializer with nested relationships"""
    author = AuthorSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    
    class Meta:
        model = Article
        fields = ['id', 'title', 'content', 'author', 'category']
```

### Writable Nested Serializers

```python
class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']

class ArticleSerializer(serializers.ModelSerializer):
    """Serializer with writable nested tags"""
    tags = TagSerializer(many=True)
    
    class Meta:
        model = Article
        fields = ['id', 'title', 'content', 'tags']
    
    def create(self, validated_data):
        """Handle nested tag creation"""
        tags_data = validated_data.pop('tags', [])
        article = Article.objects.create(**validated_data)
        
        for tag_data in tags_data:
            tag, created = Tag.objects.get_or_create(**tag_data)
            article.tags.add(tag)
        
        return article
    
    def update(self, instance, validated_data):
        """Handle nested tag updates"""
        tags_data = validated_data.pop('tags', None)
        
        # Update article fields
        instance.title = validated_data.get('title', instance.title)
        instance.content = validated_data.get('content', instance.content)
        instance.save()
        
        # Update tags if provided
        if tags_data is not None:
            instance.tags.clear()
            for tag_data in tags_data:
                tag, created = Tag.objects.get_or_create(**tag_data)
                instance.tags.add(tag)
        
        return instance
```

### Depth Option

```python
class ArticleSerializer(serializers.ModelSerializer):
    """Automatically nest related objects"""
    
    class Meta:
        model = Article
        fields = ['id', 'title', 'author', 'category', 'tags']
        depth = 1  # Automatically serialize one level of relationships
        # Warning: depth makes all nested fields read-only
```

## SerializerMethodField

### Basic Usage

```python
class ArticleSerializer(serializers.ModelSerializer):
    """Serializer with computed fields"""
    
    # Method field - computed from model instance
    reading_time = serializers.SerializerMethodField()
    author_name = serializers.SerializerMethodField()
    is_published = serializers.SerializerMethodField()
    tag_names = serializers.SerializerMethodField()
    
    class Meta:
        model = Article
        fields = [
            'id', 'title', 'content',
            'reading_time', 'author_name', 'is_published', 'tag_names'
        ]
    
    def get_reading_time(self, obj):
        """Calculate reading time in minutes"""
        word_count = len(obj.content.split())
        minutes = word_count // 200
        return max(1, minutes)
    
    def get_author_name(self, obj):
        """Get author's full name"""
        return f"{obj.author.first_name} {obj.author.last_name}"
    
    def get_is_published(self, obj):
        """Check if article is published"""
        from django.utils import timezone
        return obj.status == 'published' and obj.published_date <= timezone.now()
    
    def get_tag_names(self, obj):
        """Get list of tag names"""
        return [tag.name for tag in obj.tags.all()]
```

### Access Request Context

```python
class ArticleSerializer(serializers.ModelSerializer):
    """Serializer that uses request context"""
    
    is_author = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    absolute_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Article
        fields = ['id', 'title', 'is_author', 'can_edit', 'absolute_url']
    
    def get_is_author(self, obj):
        """Check if current user is the author"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.author == request.user
        return False
    
    def get_can_edit(self, obj):
        """Check if user can edit"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.author == request.user or request.user.is_staff
        return False
    
    def get_absolute_url(self, obj):
        """Get absolute URL"""
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.get_absolute_url())
        return obj.get_absolute_url()
```

## Performance Optimization

### Select Related and Prefetch Related

```python
# In your viewset or view
class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.select_related('author', 'category').prefetch_related('tags')
    serializer_class = ArticleSerializer
```

### Optimize SerializerMethodField

```python
class ArticleSerializer(serializers.ModelSerializer):
    """Optimized serializer"""
    comment_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Article
        fields = ['id', 'title', 'comment_count']
    
    def get_comment_count(self, obj):
        """
        Use annotated value if available,
        otherwise query the database
        """
        # If using annotation in queryset:
        # queryset.annotate(comment_count=Count('comments'))
        if hasattr(obj, 'comment_count'):
            return obj.comment_count
        
        # Fallback to querying
        return obj.comments.count()

# In view/viewset - annotate the queryset
from django.db.models import Count

class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.annotate(
        comment_count=Count('comments')
    )
    serializer_class = ArticleSerializer
```

### Use to_representation for Read-Only

```python
class ArticleSerializer(serializers.ModelSerializer):
    """Use to_representation for complex read-only logic"""
    
    class Meta:
        model = Article
        fields = ['id', 'title', 'author', 'tags']
    
    def to_representation(self, instance):
        """Customize the output representation"""
        representation = super().to_representation(instance)
        
        # Add computed fields
        representation['reading_time'] = len(instance.content.split()) // 200
        
        # Conditional fields based on permissions
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            representation['is_author'] = instance.author == request.user
        
        # Format dates
        representation['created_at'] = instance.created_at.strftime('%Y-%m-%d')
        
        return representation
```

## Best Practices

### 1. Use Appropriate Serializer Type

```python
# For simple CRUD: use ModelSerializer
class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = '__all__'

# For complex validation: use Serializer
class ArticleCreateSerializer(serializers.Serializer):
    # Define fields explicitly for full control
    pass

# For read-only: optimize with SerializerMethodField
class ArticleListSerializer(serializers.ModelSerializer):
    # Minimal fields for list view
    pass
```

### 2. Multiple Serializers for Different Contexts

```python
# List serializer - minimal fields
class ArticleListSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.username', read_only=True)
    
    class Meta:
        model = Article
        fields = ['id', 'title', 'author_name', 'created_at']

# Detail serializer - full fields
class ArticleDetailSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Article
        fields = ['id', 'title', 'content', 'author', 'tags', 'comments']

# Create/Update serializer - writable fields
class ArticleWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ['title', 'content', 'category', 'tags']

# In ViewSet
class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ArticleListSerializer
        elif self.action == 'retrieve':
            return ArticleDetailSerializer
        return ArticleWriteSerializer
```

### 3. Handle File Uploads

```python
class ArticleSerializer(serializers.ModelSerializer):
    """Serializer with file upload"""
    image = serializers.ImageField(required=False)
    document = serializers.FileField(required=False)
    
    class Meta:
        model = Article
        fields = ['id', 'title', 'image', 'document']
    
    def validate_image(self, value):
        """Validate image file"""
        # Check file size (5MB max)
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError('Image size must not exceed 5MB')
        
        # Check file type
        if not value.content_type.startswith('image/'):
            raise serializers.ValidationError('File must be an image')
        
        return value
```

### 4. Use Source Parameter

```python
class ArticleSerializer(serializers.ModelSerializer):
    """Use source to map field names"""
    
    # Map to different field name
    author_name = serializers.CharField(source='author.username')
    
    # Access nested attributes
    author_email = serializers.EmailField(source='author.email')
    
    # Use method
    author_full_name = serializers.CharField(source='author.get_full_name')
    
    class Meta:
        model = Article
        fields = ['id', 'title', 'author_name', 'author_email', 'author_full_name']
```

### 5. Conditional Fields

```python
class ArticleSerializer(serializers.ModelSerializer):
    """Serializer with conditional fields"""
    
    class Meta:
        model = Article
        fields = ['id', 'title', 'content', 'internal_notes']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Remove internal_notes for non-staff users
        request = self.context.get('request')
        if request and not request.user.is_staff:
            self.fields.pop('internal_notes', None)
```

### 6. DRY with Inheritance

```python
class BaseArticleSerializer(serializers.ModelSerializer):
    """Base serializer with common fields"""
    
    class Meta:
        model = Article
        fields = ['id', 'title', 'slug', 'created_at']
        read_only_fields = ['id', 'slug', 'created_at']

class ArticleListSerializer(BaseArticleSerializer):
    """Extends base with minimal fields"""
    author_name = serializers.CharField(source='author.username')
    
    class Meta(BaseArticleSerializer.Meta):
        fields = BaseArticleSerializer.Meta.fields + ['author_name']

class ArticleDetailSerializer(BaseArticleSerializer):
    """Extends base with full details"""
    author = AuthorSerializer(read_only=True)
    
    class Meta(BaseArticleSerializer.Meta):
        fields = BaseArticleSerializer.Meta.fields + ['content', 'author']
```

### 7. Pagination Awareness

```python
# In views, use pagination
from rest_framework.pagination import PageNumberPagination

class ArticlePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class ArticleViewSet(viewsets.ModelViewSet):
    pagination_class = ArticlePagination
    serializer_class = ArticleListSerializer
```

### 8. Validate Before Save

```python
class ArticleSerializer(serializers.ModelSerializer):
    
    def create(self, validated_data):
        # validated_data has already passed all validation
        # Safe to use directly
        return Article.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        # All validation has already passed
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
```

### 9. Handle Partial Updates

```python
class ArticleSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Article
        fields = ['id', 'title', 'content', 'status']
    
    def update(self, instance, validated_data):
        """Handle partial updates (PATCH)"""
        # Only update fields that are provided
        instance.title = validated_data.get('title', instance.title)
        instance.content = validated_data.get('content', instance.content)
        instance.status = validated_data.get('status', instance.status)
        instance.save()
        return instance

# In view, enable partial updates
class ArticleViewSet(viewsets.ModelViewSet):
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
```

### 10. Clear Error Messages

```python
class ArticleSerializer(serializers.ModelSerializer):
    
    def validate_title(self, value):
        if len(value) < 5:
            raise serializers.ValidationError(
                'Title must be at least 5 characters long. '
                f'Current length: {len(value)}'
            )
        return value
    
    def validate(self, data):
        if data.get('status') == 'published' and not data.get('category'):
            raise serializers.ValidationError({
                'category': 'A category is required for published articles.',
                'status': 'Cannot publish article without a category.'
            })
        return data
```

## Conclusion

Following these serializer guidelines will help you create efficient, maintainable, and robust Django REST Framework serializers. Remember to:

- Use the appropriate serializer type for your use case
- Implement proper validation at both field and object levels
- Optimize for performance with select_related and prefetch_related
- Use multiple serializers for different contexts
- Keep serializers focused and DRY
- Provide clear, helpful error messages
