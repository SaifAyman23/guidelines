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

---

## Overview

Serializers are one of the most important components in Django REST Framework. They sit at the boundary between your internal Python/Django world and the external JSON world your API clients interact with. They do three things in one class:

1. **Serialization** — Convert a Django model instance (or queryset) into a Python dictionary that can be rendered as JSON.
2. **Deserialization** — Parse incoming JSON from a client request back into validated Python data.
3. **Validation** — Enforce rules on that incoming data before it ever reaches your database.

Think of a serializer as a strict two-way gate: data coming in must pass all validation rules before entering, and data going out is shaped and filtered to exactly what the client should see.

**Serializer types at a glance:**

| Type | Use When |
|---|---|
| `serializers.Serializer` | Full manual control, complex logic, non-model data |
| `serializers.ModelSerializer` | Standard CRUD on a Django model — use this 90% of the time |
| `serializers.HyperlinkedModelSerializer` | Want URLs instead of PKs for related objects |

**Installation:**

```bash
pip install djangorestframework

# Add to settings.py INSTALLED_APPS:
# 'rest_framework'
```

---

## Basic Serializers

The base `serializers.Serializer` class gives you complete manual control over every field. You define each field explicitly and implement `create()` and `update()` yourself. Use this when you need maximum flexibility or when the data doesn't map directly to a single Django model.

### Simple Serializer

```python
from rest_framework import serializers

class ArticleSerializer(serializers.Serializer):
    """
    A basic serializer that defines every field manually.
    Unlike ModelSerializer, this has no awareness of your model — you
    control everything explicitly. This means more code, but also more
    flexibility for complex or non-model data structures.
    """
    id = serializers.IntegerField(read_only=True)        # Never writable by clients
    title = serializers.CharField(max_length=200)
    content = serializers.CharField()
    author = serializers.CharField(max_length=100)
    created_at = serializers.DateTimeField(read_only=True)  # Set by the system
    updated_at = serializers.DateTimeField(read_only=True)

    def create(self, validated_data):
        """
        Called by serializer.save() when no instance is passed.
        'validated_data' is guaranteed to have passed all field-level
        and object-level validation at this point — safe to use directly.
        """
        return Article.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Called by serializer.save() when an existing instance is passed.
        Use .get() with a fallback to the current value so that PATCH
        (partial update) requests only modify the fields that were sent.
        """
        instance.title = validated_data.get('title', instance.title)
        instance.content = validated_data.get('content', instance.content)
        instance.author = validated_data.get('author', instance.author)
        instance.save()
        return instance
```

**How serialization and deserialization work in practice:**

```python
# SERIALIZATION: model instance → Python dict → JSON
article = Article.objects.get(pk=1)
serializer = ArticleSerializer(article)
print(serializer.data)
# {'id': 1, 'title': 'Hello', 'content': '...', ...}

# DESERIALIZATION + VALIDATION: JSON → validated data → saved instance
data = {'title': 'New Article', 'content': 'Content here', 'author': 'Alice'}
serializer = ArticleSerializer(data=data)

if serializer.is_valid():
    article = serializer.save()  # Calls create() internally
else:
    print(serializer.errors)     # Dict of field-level error messages

# UPDATING an existing instance:
serializer = ArticleSerializer(article, data={'title': 'Updated'}, partial=True)
if serializer.is_valid():
    serializer.save()  # Calls update() internally
```

---

## ModelSerializer

`ModelSerializer` is a shortcut that automatically generates fields from your model's definition. It eliminates the need to manually define every field and implements default `create()` and `update()` methods. Use this for any standard CRUD operation on a Django model.

### Basic ModelSerializer

```python
from rest_framework import serializers
from .models import Article, Category, Tag

class ArticleSerializer(serializers.ModelSerializer):
    """
    ModelSerializer inspects the Article model and auto-generates
    fields based on the model's field definitions.

    The Meta class controls which fields are exposed and their behavior.
    """

    class Meta:
        model = Article
        fields = ['id', 'title', 'slug', 'content', 'author', 'created_at']

        # Alternatively, expose all model fields (use with caution —
        # this may expose internal fields you don't intend to share)
        # fields = '__all__'

        # Or define fields to exclude instead of include
        # exclude = ['internal_notes', 'deleted_at']

        # Fields listed here appear in responses but are rejected on input
        # Use for system-managed fields (timestamps, PKs, auto-generated slugs)
        read_only_fields = ['id', 'created_at', 'updated_at', 'slug']
```

### Field-Level Control

`extra_kwargs` lets you override field options (like `required`, `min_length`, `allow_blank`) without redefining the entire field. Use it for small tweaks; redefine the field explicitly for major changes.

```python
class ArticleSerializer(serializers.ModelSerializer):
    """
    Demonstrates different ways to control individual fields.
    """

    # Redefine a field to override its defaults (e.g., increase max_length)
    title = serializers.CharField(max_length=300, required=True)

    # write_only=True: the field is accepted on input but NEVER appears in output
    # Essential for passwords — you accept them but never return them
    password = serializers.CharField(write_only=True)

    # read_only=True: the field appears in output but is ignored on input
    # Good for system-managed counters or computed values
    view_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Article
        fields = ['id', 'title', 'content', 'password', 'view_count']
        extra_kwargs = {
            # Tweak content field without fully redefining it
            'content': {
                'required': True,
                'allow_blank': False,  # Rejects empty string ""
                'min_length': 100      # Minimum character count
            },
            'slug': {
                'required': False,     # Optional on input (auto-generated)
                'allow_blank': True
            }
        }
```

---

## Field Types

DRF provides a rich library of field types that map to Python and Django data types. Choosing the right field type gives you automatic type coercion and type-appropriate validation for free.

### Common Field Types

```python
class ExampleSerializer(serializers.Serializer):
    """
    Reference for the most commonly used DRF field types.
    Each field validates input and coerces it to the appropriate Python type.
    """

    # ── String fields ──────────────────────────────────────────────────
    char_field = serializers.CharField(max_length=100)
    # style={'base_template': 'textarea.html'} renders as textarea in the browsable API
    text_field = serializers.CharField(style={'base_template': 'textarea.html'})
    email_field = serializers.EmailField()          # Validates email format
    regex_field = serializers.RegexField(regex=r'^[0-9]+$')  # Must match regex
    slug_field = serializers.SlugField()            # Only a-z, 0-9, hyphens, underscores
    url_field = serializers.URLField()              # Validates URL format

    # ── Numeric fields ─────────────────────────────────────────────────
    integer_field = serializers.IntegerField(min_value=0, max_value=100)
    float_field = serializers.FloatField()
    # Always use DecimalField for money — FloatField has precision issues
    decimal_field = serializers.DecimalField(max_digits=10, decimal_places=2)

    # ── Boolean ────────────────────────────────────────────────────────
    boolean_field = serializers.BooleanField()

    # ── Date and time fields ───────────────────────────────────────────
    date_field = serializers.DateField()            # YYYY-MM-DD
    time_field = serializers.TimeField()            # HH:MM[:ss[.uuuuuu]]
    datetime_field = serializers.DateTimeField()    # ISO 8601 with timezone
    duration_field = serializers.DurationField()    # e.g., "3 days, 4:00:00"

    # ── Choice field ───────────────────────────────────────────────────
    # Validates that the input is one of the defined choices
    CHOICES = [('draft', 'Draft'), ('published', 'Published')]
    choice_field = serializers.ChoiceField(choices=CHOICES)

    # ── File fields ────────────────────────────────────────────────────
    # Requires multipart/form-data content type from the client
    file_field = serializers.FileField()
    image_field = serializers.ImageField()   # Like FileField but validates it's an image

    # ── Composite fields ───────────────────────────────────────────────
    # child defines the type of each item in the list
    list_field = serializers.ListField(child=serializers.CharField())
    dict_field = serializers.DictField()     # Arbitrary key-value pairs
    json_field = serializers.JSONField()     # Any valid JSON value

    # ── Relational fields ──────────────────────────────────────────────
    # Returns and accepts the related object's primary key (integer)
    primary_key_field = serializers.PrimaryKeyRelatedField(queryset=Article.objects.all())

    # Returns and accepts a URL pointing to the related object's endpoint
    hyperlinked_field = serializers.HyperlinkedRelatedField(
        view_name='article-detail',
        queryset=Article.objects.all()
    )

    # Returns and accepts a specific field from the related object (e.g., 'slug')
    slug_related_field = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Article.objects.all()
    )
```

### Custom Fields

When none of the built-in fields match your data type, subclass `serializers.Field` and implement two methods: `to_representation()` (for output/serialization) and `to_internal_value()` (for input/deserialization).

```python
class ColorField(serializers.Field):
    """
    Custom field for hex color values (e.g., #FF5733).
    - to_representation: called when serializing (model → JSON output)
    - to_internal_value: called when deserializing (JSON input → Python value)
    Raise serializers.ValidationError in to_internal_value to reject invalid input.
    """

    def to_representation(self, value):
        """
        Convert the stored value (from the database) to output format.
        Here we lowercase for consistent display in API responses.
        """
        return value.lower()

    def to_internal_value(self, data):
        """
        Validate and convert the incoming value (from the client request).
        Any exception raised here results in a 400 Bad Request.
        """
        if not isinstance(data, str):
            raise serializers.ValidationError('A string is required.')

        if not data.startswith('#'):
            raise serializers.ValidationError('Color must start with #.')

        if len(data) != 7:
            raise serializers.ValidationError('Color must be in #RRGGBB format (7 characters).')

        # Return the normalized value to be stored
        return data.upper()


class ProductSerializer(serializers.ModelSerializer):
    """Uses the custom ColorField for the product's color attribute."""
    color = ColorField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'color']
```

---

## Validation

Validation is one of the most critical parts of a serializer. DRF runs validation in layers, from field-level to object-level. All validation runs before `create()` or `update()` is ever called, so your database logic is always working with clean data.

**Validation order:**
1. Field type validation (built-in — e.g., is it a valid integer?)
2. Field-level validators (your `validate_<field_name>` methods)
3. Custom validators attached to fields
4. Object-level validation (your `validate()` method)

### Field-Level Validation

Field-level validators run on a single field's value in isolation. The method must be named `validate_<field_name>` and must either return the (possibly modified) value or raise a `ValidationError`.

```python
class ArticleSerializer(serializers.ModelSerializer):
    """
    Demonstrates field-level validation.
    Each validate_<field_name> method receives the field's already
    type-coerced value (e.g., a string, not raw bytes).
    """

    def validate_title(self, value):
        """
        Validate the 'title' field.
        - 'value' is the cleaned string value from the request
        - Return the value to accept it, raise ValidationError to reject it
        - You can also transform the value before returning (e.g., .strip())
        """
        if len(value) < 5:
            raise serializers.ValidationError(
                'Title must be at least 5 characters long.'
            )

        # Check uniqueness — exclude the current instance when updating
        # so you can save an article without changing its title
        queryset = Article.objects.filter(title=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                'An article with this title already exists.'
            )

        return value.strip()  # Normalize: remove leading/trailing whitespace

    def validate_content(self, value):
        """
        Validate that content meets the minimum word count requirement.
        Providing the actual count in the error message helps the client
        understand how far off they are.
        """
        word_count = len(value.split())
        if word_count < 100:
            raise serializers.ValidationError(
                f'Content must be at least 100 words. You have {word_count}.'
            )
        return value

    class Meta:
        model = Article
        fields = ['id', 'title', 'content', 'author']
```

### Object-Level Validation

Object-level validation (`validate()`) receives all fields together in a single dictionary. Use this for cross-field rules that involve two or more fields — for example, requiring a `published_date` when `status` is `'published'`.

```python
class ArticleSerializer(serializers.ModelSerializer):
    """
    Object-level validation runs after ALL field-level validators have passed.
    'data' is a dict containing all successfully validated field values.
    """

    def validate(self, data):
        """
        Validate the complete object with all fields available.
        You can raise a single error string or a dict of field-specific errors.
        """
        # Cross-field rule: published articles must have a published_date
        if data.get('status') == 'published' and not data.get('published_date'):
            # Raising a dict targets specific fields in the error response
            raise serializers.ValidationError({
                'published_date': 'A published date is required for published articles.'
            })

        # Business logic: published_date must be in the future
        if data.get('published_date'):
            from django.utils import timezone
            if data['published_date'] < timezone.now():
                raise serializers.ValidationError(
                    'Published date cannot be in the past.'
                )

        return data  # Always return the validated data dict

    class Meta:
        model = Article
        fields = ['id', 'title', 'status', 'published_date']
```

### Custom Validators

Reusable validators can be defined as standalone functions or classes and attached to fields. This keeps validation logic DRY — define it once, use it on any serializer.

```python
def validate_word_count(value):
    """
    Standalone validator function — can be reused on any CharField.
    Functions are best for simple, stateless rules.
    Raise serializers.ValidationError to reject the value.
    """
    word_count = len(value.split())
    if word_count < 100:
        raise serializers.ValidationError(
            f'Must be at least 100 words. Current count: {word_count}.'
        )
    # No return needed — function validators don't transform the value


class UniqueSlugValidator:
    """
    Validator class — better when the rule requires configuration (like a queryset).
    DRF calls instances of this class with __call__(value).
    """

    def __init__(self, queryset):
        self.queryset = queryset

    def __call__(self, value):
        """Called by DRF during validation with the field's value."""
        if self.queryset.filter(slug=value).exists():
            raise serializers.ValidationError(
                'This slug is already in use. Slugs must be unique.'
            )


class ArticleSerializer(serializers.ModelSerializer):
    # Attach the standalone function validator to the content field
    content = serializers.CharField(validators=[validate_word_count])

    # Attach the class validator — instantiated with the queryset it needs
    slug = serializers.SlugField(
        validators=[UniqueSlugValidator(queryset=Article.objects.all())]
    )

    class Meta:
        model = Article
        fields = ['id', 'title', 'slug', 'content']
```

---

## Nested Serializers

Nested serializers let you include related objects inline in your response — returning a full author object instead of just an author ID, for example. This saves clients from making additional requests to look up related data.

**Trade-off:** Nesting is convenient but can trigger N+1 query problems. Always pair nested serializers with `select_related()` or `prefetch_related()` in your queryset.

### Basic Nesting (Read-Only)

```python
class AuthorSerializer(serializers.ModelSerializer):
    """Minimal public profile for a user — used when embedding authors in articles."""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']


class ArticleSerializer(serializers.ModelSerializer):
    """
    Article serializer with nested (read-only) related objects.
    'read_only=True' means these fields appear in GET responses
    but are completely ignored on POST/PUT/PATCH input.

    To allow clients to set the author and category, add separate
    write-only PrimaryKeyRelatedFields (author_id, category_id).
    """
    author = AuthorSerializer(read_only=True)
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Article
        fields = ['id', 'title', 'content', 'author', 'category']

# IMPORTANT: To avoid N+1 queries, the view's queryset must use:
# Article.objects.select_related('author', 'category')
```

### Writable Nested Serializers

Writable nested serializers let clients create or update related objects in a single request. They require manually implementing `create()` and `update()` because DRF doesn't know how to handle nested writes automatically.

```python
class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']


class ArticleSerializer(serializers.ModelSerializer):
    """
    Article serializer where tags can be created/updated in the same request.
    The client sends tags as a list of objects: [{"name": "django"}, {"name": "python"}]
    """
    # many=True means the field accepts and returns a list of tag objects
    tags = TagSerializer(many=True)

    class Meta:
        model = Article
        fields = ['id', 'title', 'content', 'tags']

    def create(self, validated_data):
        """
        Handle nested tag creation when creating a new article.
        We must manually extract 'tags' before creating the article
        because Article.objects.create() doesn't know about nested data.
        """
        # Pop tags out before creating the article
        # (Article.objects.create won't accept nested dicts)
        tags_data = validated_data.pop('tags', [])
        article = Article.objects.create(**validated_data)

        for tag_data in tags_data:
            # get_or_create prevents duplicate tags
            tag, created = Tag.objects.get_or_create(**tag_data)
            article.tags.add(tag)

        return article

    def update(self, instance, validated_data):
        """
        Handle nested tag updates when updating an existing article.
        If 'tags' is not in the request, leave existing tags unchanged.
        If 'tags' is an empty list [], clear all tags.
        If 'tags' contains items, replace the existing tags entirely.
        """
        tags_data = validated_data.pop('tags', None)  # None = not provided

        # Update simple fields on the article
        instance.title = validated_data.get('title', instance.title)
        instance.content = validated_data.get('content', instance.content)
        instance.save()

        # Only update tags if the client included them in the request
        if tags_data is not None:
            instance.tags.clear()  # Remove all existing tags first
            for tag_data in tags_data:
                tag, created = Tag.objects.get_or_create(**tag_data)
                instance.tags.add(tag)

        return instance
```

### The `depth` Option

`depth` is a quick way to auto-serialize one level (or more) of relationships. It's useful for prototyping but has a major limitation: all nested fields become read-only.

```python
class ArticleSerializer(serializers.ModelSerializer):
    """
    depth = 1 automatically expands all related ForeignKey and ManyToMany fields
    by one level — no need to define nested serializers manually.

    LIMITATION: All auto-expanded nested fields are read-only.
    You can't write to them. For writable nesting, define explicit
    nested serializers as shown above.
    Also, depth gives you no control over which fields of the related
    object are included — it uses all of them.
    """
    class Meta:
        model = Article
        fields = ['id', 'title', 'author', 'category', 'tags']
        depth = 1  # Expand relationships by one level
```

---

## SerializerMethodField

`SerializerMethodField` is a read-only field whose value is computed by a method on the serializer. Use it for derived, formatted, or context-dependent data that doesn't exist as a simple model attribute.

### Basic Usage

```python
class ArticleSerializer(serializers.ModelSerializer):
    """
    Demonstrates SerializerMethodField for computed values.
    The method name must follow the pattern: get_<field_name>.
    DRF calls this method automatically, passing the model instance as 'obj'.
    """

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
        """
        Calculate estimated reading time.
        Uses integer division (//) to get whole minutes, minimum 1.
        'obj' is the Article instance being serialized.
        """
        word_count = len(obj.content.split())
        minutes = word_count // 200
        return max(1, minutes)

    def get_author_name(self, obj):
        """
        Build the author's full name from their first and last name.
        This traverses the FK — make sure 'author' is in select_related().
        """
        return f"{obj.author.first_name} {obj.author.last_name}"

    def get_is_published(self, obj):
        """
        A derived boolean: true only if status is 'published' AND the
        published_date is not in the future.
        """
        from django.utils import timezone
        return obj.status == 'published' and obj.published_date <= timezone.now()

    def get_tag_names(self, obj):
        """
        Return a flat list of tag name strings instead of nested tag objects.
        Make sure 'tags' is in prefetch_related() in the view's queryset.
        """
        return [tag.name for tag in obj.tags.all()]
```

### Accessing Request Context

The request is available inside serializer methods via `self.context.get('request')`. DRF passes the request as context automatically when the serializer is instantiated from a view. Use this for user-specific flags, building absolute URLs, or permission checks.

```python
class ArticleSerializer(serializers.ModelSerializer):
    """
    Serializer that uses the request context for user-specific fields.
    self.context['request'] is set automatically by DRF views.
    Always use .get() to avoid KeyError — context may be absent in tests.
    """

    is_author = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    absolute_url = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = ['id', 'title', 'is_author', 'can_edit', 'absolute_url']

    def get_is_author(self, obj):
        """
        True if the currently authenticated user is the article's author.
        Returns False for unauthenticated users rather than raising an error.
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.author == request.user
        return False

    def get_can_edit(self, obj):
        """
        True if the user is either the author or a staff member.
        Staff can edit any article regardless of authorship.
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.author == request.user or request.user.is_staff
        return False

    def get_absolute_url(self, obj):
        """
        Build a full URL (including scheme and domain) for this article.
        request.build_absolute_uri() uses the request's host to build the URL.
        Falls back to a relative URL if no request is available.
        """
        request = self.context.get('request')
        if request:
            # Returns e.g. "https://example.com/articles/my-article/"
            return request.build_absolute_uri(obj.get_absolute_url())
        # Fallback: relative URL like "/articles/my-article/"
        return obj.get_absolute_url()
```

---

## Performance Optimization

Serializers that access related objects can silently generate N+1 database queries — one query to fetch the main objects, then one additional query per object to fetch its related data. For a list of 100 articles, that's 101 queries instead of 2. The solutions are `select_related`, `prefetch_related`, and annotations.

### select_related and prefetch_related

Always optimize the queryset in the *view*, not the serializer. The serializer just reads data — the view controls how it's fetched.

```python
# views.py
class ArticleViewSet(viewsets.ModelViewSet):
    """
    Optimize the queryset to avoid N+1 queries.

    select_related('author', 'category'):
      - For ForeignKey and OneToOne relationships
      - Performs a SQL JOIN — fetches author and category in the SAME query
      - Use for relationships where you always need the related object

    prefetch_related('tags'):
      - For ManyToMany and reverse ForeignKey relationships
      - Performs a SEPARATE query for tags, then joins in Python
      - Use for relationships where you may have many related objects
    """
    queryset = (
        Article.objects
        .select_related('author', 'category')   # Joins: no extra queries for author/category
        .prefetch_related('tags')               # Separate query, but only ONE for all articles
    )
    serializer_class = ArticleSerializer
```

### Optimize SerializerMethodField with Annotations

`SerializerMethodField` methods that call `.count()` or aggregate functions generate an extra query *per object*. The fix is to pre-compute the value in the queryset using `annotate()`.

```python
# serializers.py
class ArticleSerializer(serializers.ModelSerializer):
    """
    Optimized serializer that uses annotated values when available.
    The get_comment_count method first checks for a pre-computed annotation,
    falling back to a live query only if the annotation isn't present.
    This pattern allows the same serializer to work correctly in both
    optimized and non-optimized contexts.
    """
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = ['id', 'title', 'comment_count']

    def get_comment_count(self, obj):
        """
        Use the annotated value if it exists (fast — no extra query).
        Fall back to a fresh DB query if the annotation wasn't applied.
        The annotation is named 'comment_count' in the queryset below.
        """
        if hasattr(obj, 'comment_count'):
            return obj.comment_count          # Pre-computed — zero extra queries
        return obj.comments.count()           # Live query — one extra per article


# views.py — annotate the queryset before it reaches the serializer
from django.db.models import Count

class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.annotate(
        comment_count=Count('comments')  # Computed in SQL, not Python
    )
    serializer_class = ArticleSerializer
    # Result: fetching 100 articles = 1 query (including comment counts)
    # Without annotation: fetching 100 articles = 101 queries
```

### Use `to_representation` for Read-Only Customization

Override `to_representation()` to modify the output of a serializer after all fields have been processed. This is the right place for output-only formatting and conditional fields that don't need to be separate `SerializerMethodField` instances.

```python
class ArticleSerializer(serializers.ModelSerializer):
    """
    Use to_representation() to add or modify fields in the output
    without defining them as separate serializer fields.
    This approach is cleaner for output-only transformations.
    """

    class Meta:
        model = Article
        fields = ['id', 'title', 'author', 'tags']

    def to_representation(self, instance):
        """
        Called automatically by DRF when converting an instance to a dict.
        We call super() first to get the standard representation, then
        add or modify fields on the resulting dict.
        """
        representation = super().to_representation(instance)

        # Add a computed field not defined in 'fields'
        representation['reading_time'] = len(instance.content.split()) // 200

        # Add a conditional field based on user permissions
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            representation['is_author'] = (instance.author == request.user)

        # Reformat a date field for consistent output
        representation['created_at'] = instance.created_at.strftime('%Y-%m-%d')

        return representation
```

---

## Best Practices

### 1. Use the Right Serializer Type

Choosing the right base class saves time and keeps code focused.

```python
# For standard model CRUD — ModelSerializer is almost always correct
class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = '__all__'

# For complex validation or non-model data — base Serializer gives full control
class ArticleImportSerializer(serializers.Serializer):
    """Used for importing articles from a CSV — not tied to a single model."""
    csv_data = serializers.CharField()
    overwrite_existing = serializers.BooleanField(default=False)

# For lightweight list views — keep it minimal to reduce payload and DB load
class ArticleListSerializer(serializers.ModelSerializer):
    """Only the fields needed to render a list item — no nested objects."""
    class Meta:
        model = Article
        fields = ['id', 'title', 'slug', 'created_at']
```

### 2. Use Multiple Serializers for Different Contexts

A single serializer trying to handle list, detail, create, and update in one class ends up with too many compromises. Instead, define a serializer per context and switch between them in the viewset.

```python
# List view — minimal, fast, no nested objects
class ArticleListSerializer(serializers.ModelSerializer):
    """
    Used for GET /api/articles/ — returns just enough to render a list.
    No nested serializers means no extra queries.
    source='author.username' reads the author's username without nesting.
    """
    author_name = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = Article
        fields = ['id', 'title', 'author_name', 'created_at']


# Detail view — rich, with nested objects and all fields
class ArticleDetailSerializer(serializers.ModelSerializer):
    """Used for GET /api/articles/<pk>/ — full details including nested data."""
    author = AuthorSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)

    class Meta:
        model = Article
        fields = ['id', 'title', 'content', 'author', 'tags', 'comments']


# Write serializer — only the fields clients are allowed to set
class ArticleWriteSerializer(serializers.ModelSerializer):
    """Used for POST, PUT, PATCH — exposes only writable fields."""
    class Meta:
        model = Article
        fields = ['title', 'content', 'category', 'tags']
        # Note: no 'author', 'id', or timestamps — set automatically by the view


# ViewSet that selects the right serializer per action
class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()

    def get_serializer_class(self):
        """Return the appropriate serializer for the current action."""
        if self.action == 'list':
            return ArticleListSerializer
        elif self.action == 'retrieve':
            return ArticleDetailSerializer
        # create, update, partial_update all use the write serializer
        return ArticleWriteSerializer
```

### 3. Handle File Uploads

```python
class ArticleSerializer(serializers.ModelSerializer):
    """
    File upload fields require the client to send multipart/form-data
    instead of application/json. DRF handles this automatically.
    Always validate file size and type to prevent abuse.
    """
    image = serializers.ImageField(required=False)
    document = serializers.FileField(required=False)

    class Meta:
        model = Article
        fields = ['id', 'title', 'image', 'document']

    def validate_image(self, value):
        """
        Validate image before saving.
        value.size is in bytes; 5MB = 5 * 1024 * 1024 bytes.
        value.content_type is set by the browser from the file's MIME type.
        """
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError('Image file size must not exceed 5MB.')

        if not value.content_type.startswith('image/'):
            raise serializers.ValidationError('Uploaded file must be an image.')

        return value
```

### 4. Use the `source` Parameter

`source` maps a serializer field name to a different attribute on the model — including dotted paths for traversing relationships and calling methods.

```python
class ArticleSerializer(serializers.ModelSerializer):
    """
    The 'source' parameter maps field names without creating a nested serializer.
    Perfect for exposing a single attribute from a related object.
    """

    # source='author.username' reads article.author.username (traverses FK)
    author_name = serializers.CharField(source='author.username')

    # source='author.email' reads article.author.email
    author_email = serializers.EmailField(source='author.email')

    # source='author.get_full_name' calls the method article.author.get_full_name()
    # Note: no parentheses — DRF calls the method for you
    author_full_name = serializers.CharField(source='author.get_full_name')

    class Meta:
        model = Article
        fields = ['id', 'title', 'author_name', 'author_email', 'author_full_name']
    # Queryset in the view must include: .select_related('author')
    # to avoid an extra query per article.
```

### 5. Conditional Fields

Remove fields from the serializer at initialization time based on the requesting user's role. This is more efficient than including the field in the output and hiding it — the value is never computed or transmitted.

```python
class ArticleSerializer(serializers.ModelSerializer):
    """
    Removes sensitive fields for non-staff users at serializer initialization.
    This happens before any data is processed, so there's no performance cost.
    """

    class Meta:
        model = Article
        fields = ['id', 'title', 'content', 'internal_notes']

    def __init__(self, *args, **kwargs):
        """
        __init__ is called when the serializer is instantiated.
        self.context is available here because kwargs are processed by super().__init__().
        We remove 'internal_notes' entirely for non-staff users — it won't appear
        in the response at all, not even as null.
        """
        super().__init__(*args, **kwargs)

        request = self.context.get('request')
        if request and not request.user.is_staff:
            # pop() removes the field safely (no error if it doesn't exist)
            self.fields.pop('internal_notes', None)
```

### 6. Keep Serializers DRY with Inheritance

When multiple serializers share a common set of fields and configuration, extract the shared parts into a base class.

```python
class BaseArticleSerializer(serializers.ModelSerializer):
    """
    Base class with fields shared by all article serializers.
    Subclasses inherit the Meta class and extend its 'fields' list.
    """

    class Meta:
        model = Article
        fields = ['id', 'title', 'slug', 'created_at']
        read_only_fields = ['id', 'slug', 'created_at']


class ArticleListSerializer(BaseArticleSerializer):
    """Extends the base with the author name for list displays."""
    author_name = serializers.CharField(source='author.username')

    class Meta(BaseArticleSerializer.Meta):
        # Inherit model and read_only_fields from base, extend fields
        fields = BaseArticleSerializer.Meta.fields + ['author_name']


class ArticleDetailSerializer(BaseArticleSerializer):
    """Extends the base with full content and nested author object."""
    author = AuthorSerializer(read_only=True)

    class Meta(BaseArticleSerializer.Meta):
        fields = BaseArticleSerializer.Meta.fields + ['content', 'author']
```

### 7. Use Pagination in Views

Serializers handle individual objects — pagination is a view-level concern. Always paginate list endpoints to prevent unbounded responses.

```python
# pagination.py
from rest_framework.pagination import PageNumberPagination

class ArticlePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'  # Client can override with ?page_size=25
    max_page_size = 100                  # Hard ceiling — prevents abuse


# views.py
class ArticleViewSet(viewsets.ModelViewSet):
    pagination_class = ArticlePagination
    serializer_class = ArticleListSerializer
    # Response: {"count": 150, "next": "...", "previous": "...", "results": [...]}
```

### 8. Trust `validated_data` in create() and update()

By the time `create()` or `update()` is called, all validation has already passed. `validated_data` is clean — never re-validate inside these methods.

```python
class ArticleSerializer(serializers.ModelSerializer):

    def create(self, validated_data):
        """
        validated_data contains only fields that passed all validation.
        It's safe to pass directly to .create() — no further checking needed.
        The ** unpacking maps each key in validated_data to a model field.
        """
        return Article.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Use setattr() to update each field dynamically.
        This is cleaner than listing every field manually and automatically
        handles any new fields you add to the serializer in the future.
        """
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
```

### 9. Handle Partial Updates (PATCH)

`PATCH` allows clients to send only the fields they want to change. The serializer's `partial=True` flag makes all fields optional for that request.

```python
class ArticleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Article
        fields = ['id', 'title', 'content', 'status']

    def update(self, instance, validated_data):
        """
        Handle both full (PUT) and partial (PATCH) updates.
        .get(field, current_value) means: use the new value if provided,
        otherwise keep the existing value unchanged.
        This is exactly what PATCH semantics require.
        """
        instance.title = validated_data.get('title', instance.title)
        instance.content = validated_data.get('content', instance.content)
        instance.status = validated_data.get('status', instance.status)
        instance.save()
        return instance


# In the ViewSet — pass partial=True for PATCH requests
class ArticleViewSet(viewsets.ModelViewSet):
    def partial_update(self, request, *args, **kwargs):
        """
        Override partial_update to explicitly set partial=True.
        This tells the serializer to treat all fields as optional
        for this specific request, even if they're normally required.
        """
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
```

### 10. Write Clear, Actionable Error Messages

Error messages are part of your API's contract with clients. A message like "Invalid value" is useless. A message like "Title must be at least 5 characters. Current length: 3." tells the developer exactly what to fix.

```python
class ArticleSerializer(serializers.ModelSerializer):
    """
    Error messages should tell the client:
    1. What the rule is
    2. What value was provided (when safe to echo back)
    3. How to fix it
    """

    def validate_title(self, value):
        if len(value) < 5:
            raise serializers.ValidationError(
                f'Title must be at least 5 characters long. '
                f'Current length: {len(value)}.'
            )
        return value

    def validate(self, data):
        """
        For cross-field errors, raise a dict to target specific fields.
        This tells clients exactly which fields are problematic and why.
        """
        if data.get('status') == 'published' and not data.get('category'):
            raise serializers.ValidationError({
                'category': 'A category is required before publishing.',
                'status': 'Cannot set to "published" without a category.'
            })
        return data
```

---

## Conclusion

Well-designed serializers are the foundation of a clean, reliable Django REST API. To summarize the key principles:

- **Choose the right type.** Use `ModelSerializer` for 90% of cases. Drop down to `Serializer` only when you need full manual control.
- **Validate at the right level.** Field-level validators for single-field rules, `validate()` for cross-field rules, standalone validators for reusable logic.
- **Use multiple serializers.** Don't force one serializer to serve list, detail, read, and write contexts — use one per context and switch in the viewset.
- **Optimize aggressively.** Pair nested serializers with `select_related()` and `prefetch_related()`. Use annotations for aggregated data.
- **Keep error messages actionable.** Tell clients what failed, what value was sent, and how to fix it.
- **Trust `validated_data`.** By the time `create()` or `update()` runs, validation is complete. Don't re-validate.
- **Inherit for DRY code.** Extract shared fields to a base serializer and extend it.
