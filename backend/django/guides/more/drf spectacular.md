# drf-spectacular — The Complete Guide

> A thorough, example-driven reference for installing, configuring, and mastering drf-spectacular — the sane and flexible OpenAPI 3 schema generation library for Django REST Framework.

**Current version as of this writing:** 0.28+
**Official docs:** https://drf-spectacular.readthedocs.io/
**Source:** https://github.com/tfranzel/drf-spectacular
**PyPI:** https://pypi.org/project/drf-spectacular/
**Recommended by Django REST Framework** as the official schema generation solution

---

## Table of Contents

- [drf-spectacular — The Complete Guide](#drf-spectacular--the-complete-guide)
  - [Table of Contents](#table-of-contents)
  - [1. What is drf-spectacular and Why Use It](#1-what-is-drf-spectacular-and-why-use-it)
  - [2. How It Works Under the Hood](#2-how-it-works-under-the-hood)
  - [3. Installation](#3-installation)
    - [Step 1: Install the package](#step-1-install-the-package)
    - [Step 2: Add to `INSTALLED_APPS`](#step-2-add-to-installed_apps)
    - [Step 3: Tell DRF to use drf-spectacular's `AutoSchema`](#step-3-tell-drf-to-use-drf-spectaculars-autoschema)
    - [Step 4: Add minimal metadata](#step-4-add-minimal-metadata)
    - [Step 5: Run the check command to verify](#step-5-run-the-check-command-to-verify)
  - [4. The `SPECTACULAR_SETTINGS` Dictionary](#4-the-spectacular_settings-dictionary)
  - [5. Serving the Schema — URLs and Views](#5-serving-the-schema--urls-and-views)
    - [Restricting Schema Access](#restricting-schema-access)
    - [Pinning a Schema Version for a Specific URL](#pinning-a-schema-version-for-a-specific-url)
  - [6. Generating a Static Schema File](#6-generating-a-static-schema-file)
  - [7. How drf-spectacular Discovers Your API](#7-how-drf-spectacular-discovers-your-api)
    - [What is Discovered Automatically](#what-is-discovered-automatically)
    - [What Requires Manual Annotation](#what-requires-manual-annotation)
  - [8. The `@extend_schema` Decorator](#8-the-extend_schema-decorator)
    - [Full Reference](#full-reference)
    - [Common Patterns](#common-patterns)
  - [9. The `@extend_schema_view` Decorator](#9-the-extend_schema_view-decorator)
    - [Basic Usage](#basic-usage)
    - [Annotating Custom @action Methods](#annotating-custom-action-methods)
  - [10. Query and Path Parameters — `OpenApiParameter`](#10-query-and-path-parameters--openapiparameter)
    - [Full Reference](#full-reference-1)
    - [Common Location Values](#common-location-values)
    - [Path Parameters](#path-parameters)
    - [Using OpenApiTypes for Precise Type Control](#using-openapitypes-for-precise-type-control)
  - [11. Response Customization — `OpenApiResponse` and Status Codes](#11-response-customization--openapiresponse-and-status-codes)
    - [Per-Status-Code Responses](#per-status-code-responses)
    - [Documenting Empty Responses](#documenting-empty-responses)
    - [Documenting Binary File Responses](#documenting-binary-file-responses)
  - [12. Inline Serializers — `inline_serializer`](#12-inline-serializers--inline_serializer)
  - [13. Field-Level Schema — `@extend_schema_field` and `@extend_schema_serializer`](#13-field-level-schema--extend_schema_field-and-extend_schema_serializer)
    - [`@extend_schema_field`](#extend_schema_field)
    - [`@extend_schema_serializer`](#extend_schema_serializer)
  - [14. Adding Examples — `OpenApiExample`](#14-adding-examples--openapiexample)
    - [Attaching Examples to a View](#attaching-examples-to-a-view)
  - [15. Excluding Views and Operations](#15-excluding-views-and-operations)
    - [Exclude a Specific View](#exclude-a-specific-view)
    - [Exclude a Specific Method](#exclude-a-specific-method)
    - [Exclude Format-Suffix Patterns Globally](#exclude-format-suffix-patterns-globally)
    - [Exclude All Paths Matching a Prefix](#exclude-all-paths-matching-a-prefix)
  - [16. Tags — Organizing Operations](#16-tags--organizing-operations)
    - [Setting Tags on a ViewSet](#setting-tags-on-a-viewset)
    - [Setting Tags at the View Level (Applies to All Methods)](#setting-tags-at-the-view-level-applies-to-all-methods)
    - [Controlling Tag Order and Descriptions Globally](#controlling-tag-order-and-descriptions-globally)
  - [17. Authentication in the Schema](#17-authentication-in-the-schema)
    - [Automatically Detected Authentication Classes](#automatically-detected-authentication-classes)
    - [Manually Defining Authentication Schemes](#manually-defining-authentication-schemes)
    - [Marking an Endpoint as Public (No Auth Required)](#marking-an-endpoint-as-public-no-auth-required)
  - [18. Polymorphic Responses](#18-polymorphic-responses)
  - [19. Offline Serving with drf-spectacular-sidecar](#19-offline-serving-with-drf-spectacular-sidecar)
  - [20. Custom Extensions — Hooks and Postprocessors](#20-custom-extensions--hooks-and-postprocessors)
    - [Preprocessing Hooks](#preprocessing-hooks)
    - [Postprocessing Hooks](#postprocessing-hooks)
    - [View Replacement Extensions](#view-replacement-extensions)
  - [21. Schema Validation and Troubleshooting Warnings](#21-schema-validation-and-troubleshooting-warnings)
    - [Running Validation](#running-validation)
    - [Understanding Warning Messages](#understanding-warning-messages)
  - [22. Common Pitfalls \& Troubleshooting](#22-common-pitfalls--troubleshooting)
  - [23. Checklist](#23-checklist)
    - [Initial Setup](#initial-setup)
    - [Schema Generation](#schema-generation)
    - [Views and Serializers](#views-and-serializers)
    - [Organization](#organization)
    - [Responses](#responses)
    - [Authentication](#authentication)
    - [Documentation Quality](#documentation-quality)

---

## 1. What is drf-spectacular and Why Use It

Any API that other developers — or other services — must consume needs documentation. Without documentation, consumers must read your source code to understand what endpoints exist, what parameters they accept, what responses they return, and what authentication they require. This is slow and error-prone.

**OpenAPI 3** (formerly known as Swagger 3) is the industry-standard specification for describing REST APIs in a machine-readable format. From an OpenAPI schema you can generate interactive documentation, strongly-typed client SDKs in dozens of languages, automated test suites, and mock servers.

**drf-spectacular** generates OpenAPI 3 schemas automatically from your existing Django REST Framework views, serializers, and routers. It is the library that the DRF project itself recommends as the successor to the deprecated built-in schema generation.

**What drf-spectacular gives you out of the box:**

- Automatic OpenAPI 3 schema generation by introspecting your DRF views and serializers
- Swagger UI and ReDoc interactive documentation served from your running app
- A `manage.py spectacular` command to export a static YAML/JSON schema file
- Serializers rendered as reusable `components` in the schema (no duplication)
- Proper support for pagination, filtering (django-filter), nested serializers, and many authentication classes
- The `@extend_schema` decorator to override or augment anything the automatic discovery gets wrong
- Support for polymorphic responses (different serializers depending on a condition)
- Schema validation to catch errors before your consumers do

**What drf-spectacular does NOT do:**

- It does not create or manage your API. It only documents what you already have.
- It does not enforce that your API actually behaves like its documentation says — that is what consumer-driven contract testing is for.
- It does not support Swagger 2.0 / OpenAPI 2.0. For that, use `drf-yasg` (but note it is no longer actively developed).

---

## 2. How It Works Under the Hood

drf-spectacular works in two phases: **discovery** and **rendering**.

In the discovery phase, it scans your URL configuration, finds all registered DRF views, and inspects each one. It examines the view's `serializer_class`, `queryset`, `filter_backends`, `pagination_class`, and `permission_classes` to build an internal representation of each API operation. This introspection happens at schema generation time, not at request time, so it does not affect your API's performance.

In the rendering phase, it serializes that internal representation into an OpenAPI 3 YAML or JSON document.

```
URL conf (urlpatterns)
    ↓ discover registered views
DRF views (ViewSet, APIView, @api_view)
    ↓ introspect
serializer_class, queryset, filter_backends,
pagination_class, authentication_classes, permission_classes
    ↓ build internal schema
Operations, Components, Parameters, Responses
    ↓ @extend_schema decorators override/augment anything
    ↓ postprocessing hooks run last
OpenAPI 3 YAML/JSON document
    ↓ served via SpectacularAPIView or written to disk
Swagger UI / ReDoc / Client generators / Testing tools
```

The `@extend_schema` decorator is your escape hatch: wherever the automatic discovery gets something wrong or where you need to express something that cannot be inferred, you annotate the view directly.

---

## 3. Installation

### Step 1: Install the package

```bash
pip install drf-spectacular

# or with uv
uv add drf-spectacular

# or with poetry
poetry add drf-spectacular
```

### Step 2: Add to `INSTALLED_APPS`

```python
# settings.py
INSTALLED_APPS = [
    # ... your other apps
    'drf_spectacular',
]
```

### Step 3: Tell DRF to use drf-spectacular's `AutoSchema`

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    # ... your other DRF settings
}
```

This is the critical step. Without it, drf-spectacular's introspection does not run.

### Step 4: Add minimal metadata

```python
# settings.py
SPECTACULAR_SETTINGS = {
    'TITLE': 'My Project API',
    'DESCRIPTION': 'API documentation for My Project.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,   # hide the schema endpoint from the schema itself
}
```

### Step 5: Run the check command to verify

```bash
python manage.py spectacular --file schema.yaml --validate
```

This generates a schema file and validates it against the OpenAPI 3 specification. You should see no errors. Warnings are informational and often expected.

---

## 4. The `SPECTACULAR_SETTINGS` Dictionary

All configuration lives in a single `SPECTACULAR_SETTINGS` dictionary in `settings.py`. None of these settings are required — the schema generates with just the `AutoSchema` class set and no `SPECTACULAR_SETTINGS` at all.

```python
# settings.py
SPECTACULAR_SETTINGS = {

    # -------------------------------------------------------------------------
    # API metadata — appears in the schema's "info" object
    # -------------------------------------------------------------------------
    'TITLE': 'My Project API',
    'DESCRIPTION': """
        Complete documentation for the My Project API.

        ## Authentication
        All endpoints require a JWT token in the `Authorization` header.

        ## Versioning
        This is version 1.0. Breaking changes increment the major version.
    """,
    'VERSION': '1.0.0',
    'TERMS_OF_SERVICE': 'https://www.example.com/terms/',
    'CONTACT': {
        'name': 'API Support',
        'url': 'https://www.example.com/support/',
        'email': 'api@example.com',
    },
    'LICENSE': {
        'name': 'MIT',
        'url': 'https://opensource.org/licenses/MIT',
    },

    # -------------------------------------------------------------------------
    # Schema endpoint behavior
    # -------------------------------------------------------------------------
    # Prevent the schema endpoint itself from appearing in the schema
    'SERVE_INCLUDE_SCHEMA': False,

    # Allow anyone to access the schema endpoint (not just authenticated users)
    'SERVE_PUBLIC': True,

    # Only generate schema for specific URL prefixes
    # 'SERVE_URLCONF': 'myapp.urls',  # restrict to a specific URL conf

    # -------------------------------------------------------------------------
    # Component and operation naming
    # -------------------------------------------------------------------------
    # How to generate operation IDs. Options: 'auto', 'method_path'
    'OPERATION_ID_GENERATION': 'auto',

    # Prefix for component names (useful when merging multiple schemas)
    # 'COMPONENT_SPLIT_REQUEST': False,  # set True to split request/response schemas

    # -------------------------------------------------------------------------
    # Schema behavior
    # -------------------------------------------------------------------------
    # Set to True to add the schema URL to SPECTACULAR_SETTINGS instead of INSTALLED_APPS
    'SCHEMA_PATH_PREFIX': '/api/v[0-9]',  # helps strip version prefix from operation IDs

    # -------------------------------------------------------------------------
    # Enum handling
    # -------------------------------------------------------------------------
    # Consolidate all enum choices into reusable components
    'ENUM_GENERATE_CHOICE_DESCRIPTION': True,

    # -------------------------------------------------------------------------
    # Postprocessing hooks
    # -------------------------------------------------------------------------
    'POSTPROCESSING_HOOKS': [
        'drf_spectacular.hooks.postprocess_schema_enums',
    ],
    'PREPROCESSING_HOOKS': [
        # Removes format-suffix patterns (e.g., .json, .api) from the schema
        # 'drf_spectacular.hooks.preprocess_exclude_path_format',
    ],

    # -------------------------------------------------------------------------
    # Swagger UI configuration
    # -------------------------------------------------------------------------
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,           # enable deep linking for operations
        'persistAuthorization': True,  # keep auth token across page refreshes
        'displayOperationId': False,   # hide operation IDs in the UI
        'filter': True,                # enable search/filter bar
        'displayRequestDuration': True, # show how long requests take
        'docExpansion': 'list',        # 'list', 'full', or 'none'
    },
    'SWAGGER_UI_FAVICON_HREF': 'https://example.com/favicon.ico',

    # -------------------------------------------------------------------------
    # ReDoc configuration
    # -------------------------------------------------------------------------
    'REDOC_UI_SETTINGS': {
        'expandResponses': 'all',
        'pathInMiddlePanel': True,
    },

    # -------------------------------------------------------------------------
    # External documentation
    # -------------------------------------------------------------------------
    'EXTERNAL_DOCS': {
        'description': 'Find more info here',
        'url': 'https://example.com/docs/',
    },

    # -------------------------------------------------------------------------
    # Server list (overrides auto-detected servers)
    # -------------------------------------------------------------------------
    'SERVERS': [
        {'url': 'https://api.example.com', 'description': 'Production'},
        {'url': 'https://staging-api.example.com', 'description': 'Staging'},
        {'url': 'http://localhost:8000', 'description': 'Local development'},
    ],

    # -------------------------------------------------------------------------
    # Component handling
    # -------------------------------------------------------------------------
    # Force drf-spectacular to not mark read-only fields as required
    'COMPONENT_NO_READ_ONLY_REQUIRED': False,

    # Append extra schema components that are not discoverable automatically
    'APPEND_COMPONENTS': {
        'securitySchemes': {
            'bearerAuth': {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'JWT',
            }
        }
    },

    # Apply security globally to all operations
    'SECURITY': [
        {'bearerAuth': []},
    ],
}
```

---

## 5. Serving the Schema — URLs and Views

drf-spectacular provides three views for serving the schema:

- `SpectacularAPIView` — serves the raw schema as YAML or JSON
- `SpectacularSwaggerView` — serves an interactive Swagger UI
- `SpectacularRedocView` — serves an interactive ReDoc UI

```python
# urls.py
from django.urls import path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    # Your API URLs
    path('api/', include('myapp.urls')),

    # Schema endpoints
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
```

With this configuration:
- `GET /api/schema/` returns the OpenAPI 3 YAML document
- `GET /api/schema/?format=json` returns the OpenAPI 3 JSON document
- `GET /api/schema/swagger-ui/` shows the interactive Swagger UI
- `GET /api/schema/redoc/` shows the ReDoc documentation

### Restricting Schema Access

By default, `SpectacularAPIView` is public (any user can fetch it). To restrict access:

```python
from drf_spectacular.views import SpectacularAPIView
from rest_framework.permissions import IsAdminUser

urlpatterns = [
    path(
        'api/schema/',
        SpectacularAPIView.as_view(permission_classes=[IsAdminUser]),
        name='schema',
    ),
    path(
        'api/schema/swagger-ui/',
        SpectacularSwaggerView.as_view(url_name='schema', permission_classes=[IsAdminUser]),
        name='swagger-ui',
    ),
]
```

Or globally via `SPECTACULAR_SETTINGS`:

```python
SPECTACULAR_SETTINGS = {
    'SERVE_PUBLIC': False,  # requires authentication to access schema
}
```

### Pinning a Schema Version for a Specific URL

For versioned APIs, you can generate a different schema for each version:

```python
urlpatterns = [
    path('api/schema/v1/', SpectacularAPIView.as_view(api_version='v1'), name='schema-v1'),
    path('api/schema/v2/', SpectacularAPIView.as_view(api_version='v2'), name='schema-v2'),
]
```

---

## 6. Generating a Static Schema File

The management command generates a static schema file you can commit, publish, or use with client generators:

```bash
# Generate YAML (default)
python manage.py spectacular --file schema.yaml

# Generate JSON
python manage.py spectacular --file schema.json --format json

# Generate and validate in one step
python manage.py spectacular --file schema.yaml --validate

# Generate for a specific API version
python manage.py spectacular --file schema-v2.yaml --api-version v2

# Output to stdout (useful in pipelines)
python manage.py spectacular
```

**Integrating into CI:** Always generate and validate the schema in CI to catch regressions before they reach production.

```yaml
# GitHub Actions example
- name: Validate API Schema
  run: |
    python manage.py spectacular --file schema.yaml --validate
    git diff --exit-code schema.yaml  # fail if the schema changed unexpectedly
```

---

## 7. How drf-spectacular Discovers Your API

Understanding what drf-spectacular can and cannot discover automatically saves you a lot of annotation work.

### What is Discovered Automatically

- **ViewSets registered with a Router:** Full CRUD operations with correct HTTP methods and operation IDs
- **`serializer_class` attribute:** Used for both request body and response body
- **`queryset` attribute:** Model fields are inferred from it
- **`filter_backends`:** Query parameters are generated from filter class fields
- **`pagination_class`:** Response is wrapped in the pagination envelope
- **`authentication_classes` and `permission_classes`:** Security requirements are inferred
- **Docstrings:** Used as the operation description
- **`read_only_fields` and `required` on serializer fields:** Correctly reflected in schema

### What Requires Manual Annotation

- **`APIView` with no `serializer_class`:** drf-spectacular cannot infer request/response types
- **Custom `get_serializer_class()` that depends on request data:** The view must also have `swagger_fake_view` handling
- **`SerializerMethodField`:** Return type cannot be inferred automatically
- **Endpoints that return different schemas based on request parameters:** Requires `@extend_schema` with per-status-code responses
- **Custom serializer fields with complex representation:** Requires `@extend_schema_field`
- **Non-standard request content types (multipart, CSV):** Requires manual annotation

---

## 8. The `@extend_schema` Decorator

`@extend_schema` is the primary customization tool. It partially or completely overrides what drf-spectacular would generate for a view method. You only need to specify the arguments where the automatic discovery is wrong or incomplete.

### Full Reference

```python
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
from drf_spectacular.types import OpenApiTypes

@extend_schema(
    # Replace the auto-generated operation ID
    operation_id='my_custom_operation_id',

    # Replace the auto-generated description (docstring is used otherwise)
    description='Retrieve a specific album by its ID.',

    # Short one-line summary (first line of docstring if not set)
    summary='Get album',

    # Tags for grouping operations in Swagger UI and ReDoc
    tags=['Albums'],

    # Mark this operation as deprecated
    deprecated=False,

    # Override request body schema
    # Accepts: Serializer class/instance, OpenApiTypes, dict, None (no body)
    request=AlbumCreateSerializer,

    # Override response schema — can be a dict of {status_code: schema}
    responses={
        200: AlbumSerializer,
        404: OpenApiResponse(description='Album not found.'),
        422: OpenApiResponse(response=ErrorSerializer, description='Validation error.'),
    },

    # Additional query/path/header/cookie parameters
    parameters=[
        OpenApiParameter('include_hidden', bool, description='Include hidden albums.'),
    ],

    # Override authentication — use None to mark as public
    auth=None,

    # Provide request/response examples
    examples=[
        OpenApiExample(
            'Success',
            value={'id': 1, 'title': 'Dark Side of the Moon'},
            response_only=True,
            status_codes=['200'],
        ),
    ],

    # Scope this decorator to specific HTTP methods only (for class-based views)
    methods=['GET'],

    # Scope to specific API versions
    versions=['v2'],

    # Vendor extensions
    extensions={'x-badge': 'new'},

    # Completely exclude this operation from the schema
    exclude=False,

    # Manually provide the full operation dict (bypasses all auto-discovery)
    operation=None,
)
def my_view(request, pk):
    ...
```

### Common Patterns

**Override just the request serializer (when different from the response serializer):**

```python
@extend_schema(request=AlbumCreateSerializer, responses={201: AlbumDetailSerializer})
def create(self, request, *args, **kwargs):
    return super().create(request, *args, **kwargs)
```

**Add query parameters not from a filter backend:**

```python
@extend_schema(
    parameters=[
        OpenApiParameter('format', str, description='Response format: json or csv.', enum=['json', 'csv']),
        OpenApiParameter('page_size', int, description='Number of results per page.', default=20),
    ]
)
def list(self, request, *args, **kwargs):
    ...
```

**Document multiple response status codes:**

```python
@extend_schema(
    responses={
        200: UserSerializer,
        401: OpenApiResponse(description='Authentication credentials were not provided.'),
        403: OpenApiResponse(description='You do not have permission to perform this action.'),
        404: OpenApiResponse(description='User not found.'),
    }
)
def retrieve(self, request, *args, **kwargs):
    ...
```

**Mark an endpoint as not requiring authentication:**

```python
@extend_schema(auth=[])
@api_view(['GET'])
def public_health_check(request):
    return Response({'status': 'ok'})
```

**Apply to all methods on an APIView (without specifying `methods`):**

```python
@extend_schema(tags=['Health'])
class HealthCheckView(APIView):
    @extend_schema(description='Check if the API is alive.')
    def get(self, request):
        return Response({'status': 'ok'})
```

---

## 9. The `@extend_schema_view` Decorator

When your view inherits list/create/retrieve/update/destroy from a base class (like `ModelViewSet`), you have nothing to attach `@extend_schema` to for the default implementations. `@extend_schema_view` solves this by letting you annotate default methods from the outside.

### Basic Usage

```python
from drf_spectacular.utils import extend_schema, extend_schema_view

@extend_schema_view(
    list=extend_schema(
        summary='List all albums',
        description='Returns a paginated list of all albums in the catalog.',
        parameters=[
            OpenApiParameter('genre', str, description='Filter by genre.'),
        ],
    ),
    create=extend_schema(
        summary='Create an album',
        description='Creates a new album. Requires authentication.',
        request=AlbumCreateSerializer,
        responses={201: AlbumDetailSerializer},
    ),
    retrieve=extend_schema(
        summary='Get album details',
        description='Returns the full details of a specific album.',
    ),
    update=extend_schema(
        summary='Update an album',
        request=AlbumUpdateSerializer,
    ),
    partial_update=extend_schema(
        summary='Partially update an album',
        request=AlbumUpdateSerializer,
    ),
    destroy=extend_schema(
        summary='Delete an album',
        responses={204: None},
    ),
)
class AlbumViewSet(viewsets.ModelViewSet):
    queryset = Album.objects.all()
    serializer_class = AlbumSerializer
```

### Annotating Custom @action Methods

`@extend_schema_view` also supports annotating custom `@action` methods:

```python
@extend_schema_view(
    list=extend_schema(summary='List albums'),
    favorites=extend_schema(
        summary='Get user favorites',
        description='Returns the authenticated user\'s favorited albums.',
        responses={200: AlbumSerializer(many=True)},
    ),
)
class AlbumViewSet(viewsets.ModelViewSet):
    queryset = Album.objects.all()
    serializer_class = AlbumSerializer

    @action(detail=False, methods=['get'])
    def favorites(self, request):
        qs = Album.objects.filter(favorited_by=request.user)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)
```

---

## 10. Query and Path Parameters — `OpenApiParameter`

`OpenApiParameter` describes parameters that are not automatically discovered by the filter backend introspection.

### Full Reference

```python
from drf_spectacular.utils import OpenApiParameter
from drf_spectacular.types import OpenApiTypes

OpenApiParameter(
    name='search',                        # parameter name (as it appears in the URL)
    type=str,                             # Python type, OpenApiTypes enum, or Serializer
    location=OpenApiParameter.QUERY,      # QUERY, PATH, HEADER, or COOKIE
    required=False,                       # whether the parameter is mandatory
    description='Search by album title.', # description shown in documentation
    enum=['active', 'inactive', 'all'],   # restrict to a set of allowed values
    pattern=r'^[A-Z]{2}\d{4}$',          # regex pattern for string validation
    deprecated=False,                     # mark as deprecated
    default='active',                     # default value
    allow_blank=True,                     # whether empty string is accepted
    many=False,                           # True to accept multiple values (array)
    examples=[                            # example values
        OpenApiExample('Active only', value='active'),
        OpenApiExample('All', value='all'),
    ],
)
```

### Common Location Values

```python
OpenApiParameter.QUERY   # ?search=value in the URL
OpenApiParameter.PATH    # /albums/{album_id}/ — path variable
OpenApiParameter.HEADER  # HTTP header (e.g., X-Request-ID)
OpenApiParameter.COOKIE  # HTTP cookie
```

### Path Parameters

Path parameters in your URL pattern are usually discovered automatically from the URL regex. Only use `OpenApiParameter` for path parameters if you need to add extra documentation:

```python
@extend_schema(
    parameters=[
        OpenApiParameter(
            'album_id',
            int,
            location=OpenApiParameter.PATH,
            description='The unique identifier of the album.',
        ),
    ]
)
def retrieve(self, request, album_id):
    ...
```

### Using OpenApiTypes for Precise Type Control

```python
from drf_spectacular.types import OpenApiTypes

# Full list of available types:
# OpenApiTypes.STR     → string
# OpenApiTypes.INT     → integer
# OpenApiTypes.INT32   → integer (32-bit)
# OpenApiTypes.INT64   → integer (64-bit)
# OpenApiTypes.FLOAT   → number (float)
# OpenApiTypes.DOUBLE  → number (double)
# OpenApiTypes.BOOL    → boolean
# OpenApiTypes.BYTE    → string (base64 encoded)
# OpenApiTypes.DATE    → string (date, YYYY-MM-DD)
# OpenApiTypes.DATETIME → string (date-time, ISO 8601)
# OpenApiTypes.TIME    → string (time)
# OpenApiTypes.UUID    → string (UUID)
# OpenApiTypes.URI     → string (URI)
# OpenApiTypes.EMAIL   → string (email)
# OpenApiTypes.IP4     → string (IPv4)
# OpenApiTypes.IP6     → string (IPv6)
# OpenApiTypes.DECIMAL → string (decimal number)
# OpenApiTypes.OBJECT  → object (dict)
# OpenApiTypes.ANY     → any type

@extend_schema(
    parameters=[
        OpenApiParameter('release_date', OpenApiTypes.DATE, description='Filter by release date.'),
        OpenApiParameter('album_id', OpenApiTypes.UUID, location=OpenApiParameter.PATH),
    ]
)
def my_view(self, request):
    ...
```

---

## 11. Response Customization — `OpenApiResponse` and Status Codes

By default, drf-spectacular generates a single `200` (or `201` for create operations) response schema from the view's serializer. To document additional status codes or provide descriptions:

### Per-Status-Code Responses

```python
from drf_spectacular.utils import extend_schema, OpenApiResponse

@extend_schema(
    responses={
        200: AlbumSerializer,
        201: OpenApiResponse(
            response=AlbumSerializer,
            description='Album created successfully.',
        ),
        400: OpenApiResponse(
            response=ValidationErrorSerializer,
            description='The submitted data was invalid. Check the error messages.',
        ),
        401: OpenApiResponse(description='Authentication required. Include a Bearer token.'),
        403: OpenApiResponse(description='You do not have permission to create albums.'),
        404: OpenApiResponse(description='The specified album does not exist.'),
        409: OpenApiResponse(
            response=ConflictSerializer,
            description='An album with this title already exists.',
        ),
    }
)
def create(self, request, *args, **kwargs):
    ...
```

### Documenting Empty Responses

For `204 No Content` responses (successful deletions):

```python
@extend_schema(
    responses={204: None}
)
def destroy(self, request, pk):
    ...
```

### Documenting Binary File Responses

```python
@extend_schema(
    responses={
        200: OpenApiResponse(
            response=OpenApiTypes.BINARY,
            description='The album cover image as a JPEG file.',
        ),
    }
)
def cover_image(self, request, pk):
    album = get_object_or_404(Album, pk=pk)
    return FileResponse(album.cover_image.open(), content_type='image/jpeg')
```

---

## 12. Inline Serializers — `inline_serializer`

Sometimes you have a simple one-off response that does not justify writing a full serializer class. `inline_serializer` lets you define the schema inline in the decorator.

```python
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers

@extend_schema(
    request=inline_serializer(
        name='BulkDeleteRequest',
        fields={
            'ids': serializers.ListField(child=serializers.IntegerField()),
        }
    ),
    responses={
        200: inline_serializer(
            name='BulkDeleteResponse',
            fields={
                'deleted_count': serializers.IntegerField(),
                'message': serializers.CharField(),
            }
        ),
        400: OpenApiResponse(description='No IDs provided or IDs are invalid.'),
    },
)
@api_view(['POST'])
def bulk_delete(request):
    ids = request.data.get('ids', [])
    count = Album.objects.filter(pk__in=ids).delete()[0]
    return Response({'deleted_count': count, 'message': f'Deleted {count} albums.'})
```

**Note:** Each `inline_serializer` call requires a unique `name`. This name becomes the component name in the schema. Two inline serializers with the same name and different fields will conflict.

---

## 13. Field-Level Schema — `@extend_schema_field` and `@extend_schema_serializer`

### `@extend_schema_field`

Use this on a custom field class or a `SerializerMethodField` to tell drf-spectacular what type the field returns.

**On a custom field class:**

```python
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers
import base64

@extend_schema_field(OpenApiTypes.BYTE)   # documents as base64-encoded binary
class Base64Field(serializers.Field):
    def to_representation(self, value):
        return base64.b64encode(value).decode('utf-8')

    def to_internal_value(self, data):
        return base64.b64decode(data)
```

**On a `SerializerMethodField`:**

```python
class AlbumSerializer(serializers.ModelSerializer):
    cover_url = serializers.SerializerMethodField()
    track_count = serializers.SerializerMethodField()
    release_year = serializers.SerializerMethodField()

    @extend_schema_field(OpenApiTypes.URI)
    def get_cover_url(self, obj):
        return obj.cover_image.url if obj.cover_image else None

    @extend_schema_field(int)
    def get_track_count(self, obj):
        return obj.tracks.count()

    @extend_schema_field(OpenApiTypes.INT32)
    def get_release_year(self, obj):
        return obj.release_date.year if obj.release_date else None
```

**With a nested serializer:**

```python
class OrderSerializer(serializers.ModelSerializer):
    customer = serializers.SerializerMethodField()

    @extend_schema_field(CustomerSerializer)   # nested serializer
    def get_customer(self, obj):
        return CustomerSerializer(obj.user.customer_profile).data
```

**With an inline type dict (raw schema object):**

```python
@extend_schema_field({'type': 'array', 'items': {'type': 'string', 'format': 'uri'}})
def get_image_urls(self, obj):
    return [img.url for img in obj.images.all()]
```

### `@extend_schema_serializer`

Use this on a serializer class to affect how the entire serializer is represented in the schema.

```python
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample

@extend_schema_serializer(
    # Exclude specific fields from the schema representation
    exclude_fields=['internal_notes', 'admin_flag'],

    # Attach examples to this serializer wherever it appears in the schema
    examples=[
        OpenApiExample(
            'Create Album',
            description='Example payload for creating a new album.',
            value={
                'title': 'The Dark Side of the Moon',
                'artist': 'Pink Floyd',
                'release_date': '1973-03-01',
                'genre': 'progressive_rock',
            },
            request_only=True,
        ),
        OpenApiExample(
            'Album Response',
            description='Example response when retrieving an album.',
            value={
                'id': 1,
                'title': 'The Dark Side of the Moon',
                'artist': 'Pink Floyd',
                'release_date': '1973-03-01',
                'genre': 'progressive_rock',
                'created_at': '2024-01-15T10:30:00Z',
            },
            response_only=True,
        ),
    ],
)
class AlbumSerializer(serializers.ModelSerializer):
    class Meta:
        model = Album
        fields = '__all__'
```

---

## 14. Adding Examples — `OpenApiExample`

Examples appear in the Swagger UI and ReDoc documentation, giving consumers concrete data to understand the expected format.

```python
from drf_spectacular.utils import OpenApiExample

OpenApiExample(
    name='Example name',              # shown in the UI as the example title
    value={...},                      # the actual example data (dict, list, or scalar)
    summary='Short description',      # optional short summary
    description='Longer description', # optional detailed explanation
    request_only=True,                # only show in request context
    response_only=False,              # only show in response context
    status_codes=['200', '201'],      # restrict to specific response status codes
    media_type='application/json',    # restrict to a specific media type
)
```

### Attaching Examples to a View

```python
@extend_schema(
    examples=[
        OpenApiExample(
            'Successful creation',
            value={'id': 42, 'title': 'Rumours', 'artist': 'Fleetwood Mac'},
            response_only=True,
            status_codes=['201'],
        ),
        OpenApiExample(
            'Validation error',
            value={'title': ['This field may not be blank.']},
            response_only=True,
            status_codes=['400'],
        ),
        OpenApiExample(
            'Create request',
            value={'title': 'Rumours', 'artist': 'Fleetwood Mac', 'release_date': '1977-02-04'},
            request_only=True,
        ),
    ]
)
def create(self, request, *args, **kwargs):
    ...
```

---

## 15. Excluding Views and Operations

### Exclude a Specific View

```python
from drf_spectacular.utils import extend_schema

@extend_schema(exclude=True)
class InternalHealthCheckView(APIView):
    """Not public API — used by load balancer only."""
    def get(self, request):
        return Response({'status': 'ok'})
```

### Exclude a Specific Method

```python
class AlbumViewSet(viewsets.ModelViewSet):

    @extend_schema(exclude=True)
    def partial_update(self, request, *args, **kwargs):
        """PATCH is disabled for this resource. Use PUT instead."""
        return Response(status=405)
```

### Exclude Format-Suffix Patterns Globally

If your URL configuration uses `format_suffix_patterns` (adding `.json`, `.api` to URLs), those suffixed operations will appear in your schema by default. Remove them with the preprocessing hook:

```python
SPECTACULAR_SETTINGS = {
    'PREPROCESSING_HOOKS': [
        'drf_spectacular.hooks.preprocess_exclude_path_format',
    ],
}
```

### Exclude All Paths Matching a Prefix

```python
# settings.py
SPECTACULAR_SETTINGS = {
    'PREPROCESSING_HOOKS': ['myapp.schema.exclude_internal_paths'],
}

# myapp/schema.py
def exclude_internal_paths(endpoints):
    return [
        (path, path_regex, method, callback)
        for path, path_regex, method, callback in endpoints
        if not path.startswith('/internal/')
    ]
```

---

## 16. Tags — Organizing Operations

Tags group related operations together in Swagger UI and ReDoc. Without tags, operations are listed alphabetically by path. With tags, they are grouped visually into sections.

### Setting Tags on a ViewSet

```python
@extend_schema_view(
    list=extend_schema(tags=['Albums']),
    create=extend_schema(tags=['Albums']),
    retrieve=extend_schema(tags=['Albums']),
)
class AlbumViewSet(viewsets.ModelViewSet):
    ...
```

### Setting Tags at the View Level (Applies to All Methods)

```python
@extend_schema(tags=['Albums'])
class AlbumViewSet(viewsets.ModelViewSet):
    ...
```

### Controlling Tag Order and Descriptions Globally

```python
SPECTACULAR_SETTINGS = {
    'TAGS': [
        {'name': 'Albums', 'description': 'Operations related to music albums.'},
        {'name': 'Artists', 'description': 'Operations related to artists.'},
        {'name': 'Authentication', 'description': 'Login, logout, and token refresh.'},
        {'name': 'Admin', 'description': 'Administrative operations. Requires staff permissions.'},
    ],
}
```

Tags not listed in `SPECTACULAR_SETTINGS['TAGS']` still appear in the schema — they just appear after the listed ones without a description.

---

## 17. Authentication in the Schema

drf-spectacular automatically detects many common authentication classes and generates the appropriate security requirements.

### Automatically Detected Authentication Classes

| DRF authentication class | OpenAPI security scheme generated |
|---|---|
| `BasicAuthentication` | HTTP Basic |
| `SessionAuthentication` | Cookie-based |
| `TokenAuthentication` | API key in `Authorization` header |
| `JWTAuthentication` (Simple JWT) | Bearer token |
| `OAuth2Authentication` | OAuth 2.0 |

### Manually Defining Authentication Schemes

For custom authentication classes or fine-grained control:

```python
SPECTACULAR_SETTINGS = {
    'APPEND_COMPONENTS': {
        'securitySchemes': {
            'bearerAuth': {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'JWT',
                'description': 'Include your JWT token as: Authorization: Bearer <token>',
            },
            'apiKeyAuth': {
                'type': 'apiKey',
                'in': 'header',
                'name': 'X-API-Key',
            },
        }
    },
    # Apply security globally to all endpoints
    'SECURITY': [
        {'bearerAuth': []},
    ],
}
```

### Marking an Endpoint as Public (No Auth Required)

```python
@extend_schema(auth=[])  # empty list = no authentication required
@api_view(['GET'])
def public_endpoint(request):
    return Response({'message': 'This endpoint is public.'})
```

---

## 18. Polymorphic Responses

When an endpoint can return different shapes of data depending on a condition (for example, a base resource with several subtypes), use `PolymorphicProxySerializer`.

```python
from drf_spectacular.utils import PolymorphicProxySerializer, extend_schema

@extend_schema(
    responses=PolymorphicProxySerializer(
        component_name='Notification',
        serializers=[
            EmailNotificationSerializer,
            SMSNotificationSerializer,
            PushNotificationSerializer,
        ],
        resource_type_field_name='type',  # the field that discriminates between types
    ),
)
class NotificationListView(generics.ListAPIView):
    def get_serializer_class(self):
        # The actual logic for choosing the serializer at runtime
        ...
```

This tells drf-spectacular that the response can be any one of the listed serializers, and the `type` field identifies which one applies. The generated schema uses OpenAPI's `oneOf` (or `anyOf`) to express this.

---

## 19. Offline Serving with drf-spectacular-sidecar

By default, Swagger UI and ReDoc are served from CDNs. In environments without internet access, install the sidecar package:

```bash
pip install drf-spectacular-sidecar
```

```python
# settings.py
INSTALLED_APPS = [
    # ...
    'drf_spectacular',
    'drf_spectacular_sidecar',  # required for Django collectstatic to discover static files
]

SPECTACULAR_SETTINGS = {
    'SWAGGER_UI_DIST': 'SIDECAR',        # use locally bundled Swagger UI
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR', # use locally bundled favicon
    'REDOC_DIST': 'SIDECAR',             # use locally bundled ReDoc
    # ... other settings
}
```

Then run `python manage.py collectstatic` to copy the sidecar's static files to your static files directory.

---

## 20. Custom Extensions — Hooks and Postprocessors

For cases where decorators are not enough — for example, fixing schema issues in third-party packages you cannot modify, or making global schema transformations — drf-spectacular provides extension hooks.

### Preprocessing Hooks

Preprocessing hooks receive the list of discovered endpoints and can filter or transform them before schema generation.

```python
# myapp/schema_hooks.py

def remove_admin_endpoints(endpoints):
    """Remove all endpoints under /admin/ from the public schema."""
    return [
        (path, path_regex, method, callback)
        for path, path_regex, method, callback in endpoints
        if not path.startswith('/admin/')
    ]
```

```python
SPECTACULAR_SETTINGS = {
    'PREPROCESSING_HOOKS': [
        'myapp.schema_hooks.remove_admin_endpoints',
    ],
}
```

### Postprocessing Hooks

Postprocessing hooks run at the very end and receive the full assembled schema as a Python dict. You can make arbitrary modifications.

```python
# myapp/schema_hooks.py

def add_x_internal_flag(result, generator, request, public):
    """Add x-internal: true to all admin operations."""
    for path, path_item in result.get('paths', {}).items():
        if '/admin/' in path:
            for method, operation in path_item.items():
                if isinstance(operation, dict):
                    operation['x-internal'] = True
    return result
```

```python
SPECTACULAR_SETTINGS = {
    'POSTPROCESSING_HOOKS': [
        'drf_spectacular.hooks.postprocess_schema_enums',  # keep the default enum hook!
        'myapp.schema_hooks.add_x_internal_flag',
    ],
}
```

**Critical:** Setting `POSTPROCESSING_HOOKS` replaces the default list. Always include `'drf_spectacular.hooks.postprocess_schema_enums'` unless you specifically want to disable enum consolidation.

### View Replacement Extensions

For third-party views you cannot modify, use `OpenApiViewExtension`:

```python
# myapp/spectacular_extensions.py
from drf_spectacular.extensions import OpenApiViewExtension
from drf_spectacular.utils import extend_schema

class FixSomeThirdPartyView(OpenApiViewExtension):
    target_class = 'third_party.views.SomeView'

    def view_replacement(self):
        @extend_schema(responses={200: MyProperSerializer})
        class Fixed(self.target_class):
            pass
        return Fixed
```

The extension is automatically picked up by drf-spectacular if the module is imported. Add the import to your app's `AppConfig.ready()` method or to the app's `__init__.py`:

```python
# myapp/apps.py
class MyAppConfig(AppConfig):
    def ready(self):
        import myapp.spectacular_extensions  # noqa
```

---

## 21. Schema Validation and Troubleshooting Warnings

### Running Validation

```bash
# Validate your schema against the OpenAPI 3 specification
python manage.py spectacular --file schema.yaml --validate
```

### Understanding Warning Messages

drf-spectacular emits warnings during schema generation when it discovers issues. Most warnings are harmless, but some indicate a real problem in your schema.

**`Unable to guess serializer` (warning):**
Cause: A view (usually `APIView`) has no `serializer_class` or `get_serializer_class()`.
Fix: Add `serializer_class` to the view, or use `@extend_schema(responses={...})`.

**`Serializer field is not inspectable` (warning):**
Cause: A custom field class is not recognized by drf-spectacular.
Fix: Decorate the field class with `@extend_schema_field(OpenApiTypes.STR)` (or the appropriate type).

**`Error for operation {id}:` (warning):**
Cause: The view raises an exception during schema introspection. Common causes: `get_queryset()` or `get_serializer_class()` depends on `request.user` which is not available at schema time.
Fix: Add a guard for the schema generation context:

```python
def get_queryset(self):
    if getattr(self, 'swagger_fake_view', False):
        return MyModel.objects.none()
    # Normal logic that depends on request
    return MyModel.objects.filter(user=self.request.user)

def get_serializer_class(self):
    if getattr(self, 'swagger_fake_view', False):
        return MyDefaultSerializer
    # Normal logic
    return self.decide_serializer(self.request)
```

**`Duplicate operation id`:**
Cause: Two views generate the same `operationId`. This happens with generic views that override each other.
Fix: Use `@extend_schema(operation_id='unique_name')` to override the auto-generated ID.

---

## 22. Common Pitfalls & Troubleshooting

**Problem: My view does not appear in the schema at all.**

Cause: The view is not using DRF's `APIView` or `@api_view` decorator, or it is not reachable from the URL configuration.

Fix: Ensure your view inherits from a DRF class. Ensure the URL is included in the root `urlpatterns`. Run `python manage.py spectacular` and check for warnings.

---

**Problem: The schema shows the wrong serializer for my view.**

Cause: Your view's `get_serializer_class()` returns different serializers in different conditions, but drf-spectacular can only introspect the default case.

Fix: Use `@extend_schema(request=..., responses=...)` to explicitly specify the serializer for each condition.

---

**Problem: Query parameters from `django-filter` are not appearing in the schema.**

Cause: `drf_spectacular.contrib.django_filters.DjangoFilterExtension` needs to be active, which requires that `django-filter` is installed and `filterset_class` or `filterset_fields` is set on the view.

Fix: Ensure `django-filter` is in `INSTALLED_APPS` and that the view's `filter_backends` includes `DjangoFilterBackend`. drf-spectacular picks this up automatically.

---

**Problem: Pagination is not reflected in the schema — list endpoints show a plain array instead of the paginated envelope.**

Cause: The view does not have a `pagination_class` set, or the global `DEFAULT_PAGINATION_CLASS` is not set in `REST_FRAMEWORK`.

Fix: Add `pagination_class` to the view or set `DEFAULT_PAGINATION_CLASS` in `REST_FRAMEWORK` settings.

---

**Problem: My `SerializerMethodField` shows up as type `string` in the schema instead of its real type.**

Cause: drf-spectacular cannot infer the return type of a Python method.

Fix: Decorate `get_*` method with `@extend_schema_field`:

```python
@extend_schema_field(int)
def get_track_count(self, obj):
    return obj.tracks.count()
```

---

**Problem: Enum fields generate individual inline enums instead of reusable components.**

Cause: The postprocessing hook for enums is not running.

Fix: Ensure `POSTPROCESSING_HOOKS` includes `'drf_spectacular.hooks.postprocess_schema_enums'`. If you have customized `POSTPROCESSING_HOOKS`, the default list was replaced — you must add the enum hook back explicitly.

---

**Problem: The Swagger UI shows wrong server URLs.**

Cause: drf-spectacular auto-detects servers from the request context. In some proxy/load balancer setups this detects the wrong host.

Fix: Override the server list explicitly:

```python
SPECTACULAR_SETTINGS = {
    'SERVERS': [
        {'url': 'https://api.example.com', 'description': 'Production'},
        {'url': 'http://localhost:8000', 'description': 'Development'},
    ],
}
```

---

**Problem: `SERVE_INCLUDE_SCHEMA: False` is set but the schema endpoint still appears.**

Cause: This setting only applies when the schema endpoint is named `'schema'` in the URL configuration (using `name='schema'`). If your schema URL has a different name, the setting cannot identify it.

Fix: Name your schema URL `'schema'`:

```python
path('api/schema/', SpectacularAPIView.as_view(), name='schema'),  # name must be 'schema'
```

---

## 23. Checklist

Use this every time you add or configure drf-spectacular in a project.

### Initial Setup

- [ ] `'drf_spectacular'` is in `INSTALLED_APPS`
- [ ] `'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema'` is set in `REST_FRAMEWORK`
- [ ] `SPECTACULAR_SETTINGS` defines at least `TITLE`, `DESCRIPTION`, and `VERSION`
- [ ] `SERVE_INCLUDE_SCHEMA` is set to `False` so the schema endpoint does not document itself
- [ ] Schema URLs (`SpectacularAPIView`, `SpectacularSwaggerView`, `SpectacularRedocView`) are added to `urls.py`

### Schema Generation

- [ ] `python manage.py spectacular --validate` runs without errors (warnings may be acceptable)
- [ ] A static schema file is generated and committed to version control
- [ ] Schema generation is part of the CI pipeline
- [ ] CI fails if the schema changes unexpectedly (`git diff --exit-code schema.yaml`)

### Views and Serializers

- [ ] Every view that drf-spectacular cannot fully introspect has an `@extend_schema` annotation
- [ ] `APIView` subclasses without `serializer_class` have `@extend_schema(request=..., responses=...)`
- [ ] `SerializerMethodField` methods with non-obvious return types have `@extend_schema_field`
- [ ] Custom field classes have `@extend_schema_field`
- [ ] `get_queryset()` and `get_serializer_class()` handle `swagger_fake_view` if they depend on the request user

### Organization

- [ ] All operations have meaningful `summary` values (via `@extend_schema` or first docstring line)
- [ ] All operations are tagged with `tags=[...]`
- [ ] Tag descriptions are defined in `SPECTACULAR_SETTINGS['TAGS']`
- [ ] Internal/admin operations are excluded or marked with `x-internal`
- [ ] `@extend_schema_view` is used on ViewSets to annotate default methods cleanly

### Responses

- [ ] Multiple status codes (400, 401, 403, 404) are documented on views where they are possible
- [ ] Error response serializers are consistent and documented
- [ ] `204 No Content` responses on delete operations use `responses={204: None}`
- [ ] Create operations use `responses={201: Serializer}` not `{200: Serializer}`

### Authentication

- [ ] The authentication scheme is correctly represented (either via auto-detection or `APPEND_COMPONENTS`)
- [ ] `SECURITY` is set in `SPECTACULAR_SETTINGS` if authentication applies globally
- [ ] Public endpoints are marked with `@extend_schema(auth=[])`

### Documentation Quality

- [ ] All important endpoints have at least one `OpenApiExample` in the request and response
- [ ] Enum fields have descriptions explaining each allowed value
- [ ] The `DESCRIPTION` in `SPECTACULAR_SETTINGS` includes authentication instructions and versioning notes
- [ ] `SERVERS` is set to the actual API server URLs for each environment

---

*Official documentation: https://drf-spectacular.readthedocs.io/ — always check for the latest settings and decorator arguments, as drf-spectacular releases frequently.*