# django-split-settings — The Complete Guide

> A thorough, example-driven reference for installing, configuring, and mastering django-split-settings — the library that lets you organize Django settings into multiple files and directories, with wildcard support and optional file loading.

**Current version as of this writing:** 1.3.2+
**Official docs:** https://django-split-settings.readthedocs.io/
**Source:** https://github.com/wemake-services/django-split-settings
**PyPI:** https://pypi.org/project/django-split-settings/

---

## Table of Contents

1. [What is django-split-settings and Why Use It](#1-what-is-django-split-settings-and-why-use-it)
2. [How It Works Under the Hood](#2-how-it-works-under-the-hood)
3. [Installation](#3-installation)
4. [Your First Split Settings Structure](#4-your-first-split-settings-structure)
5. [The `include()` Function](#5-the-include-function)
6. [The `optional()` Wrapper](#6-the-optional-wrapper)
7. [Wildcards — Loading Files Dynamically](#7-wildcards--loading-files-dynamically)
8. [Environment-Based Settings Switching](#8-environment-based-settings-switching)
9. [Modifying Settings from Previous Files](#9-modifying-settings-from-previous-files)
10. [Fixing `BASE_DIR` After Converting to a Package](#10-fixing-base_dir-after-converting-to-a-package)
11. [Recommended Project Structures](#11-recommended-project-structures)
12. [Using django-split-settings with django-environ](#12-using-django-split-settings-with-django-environ)
13. [Running the Dev Server and Tests](#13-running-the-dev-server-and-tests)
14. [Common Pitfalls & Troubleshooting](#14-common-pitfalls--troubleshooting)
15. [Checklist](#15-checklist)

---

## 1. What is django-split-settings and Why Use It

Every Django project starts with a single `settings.py` file. For small projects, this works fine. For anything real, it becomes a problem.

A typical settings file for a medium project contains 200–400 lines covering: installed apps, database configuration, cache backends, email backends, logging, Celery, static/media files, security settings, third-party package configuration, and more. When you add multiple environments — local development, staging, production, CI — this single file becomes unmanageable. Developers resort to commenting out sections, maintaining multiple parallel files, and using fragile `try/except ImportError` tricks.

**django-split-settings** solves this with a clean, explicit approach: you replace your `settings.py` with a `settings/` package, and a single `__init__.py` file that uses `include()` to assemble the final settings from multiple component files. Each component file is a plain Python file. The local context passes from file to file in order, so later files can read and modify what earlier files set.

**What django-split-settings gives you:**

- Split settings into any number of files with a simple `include()` call
- Mark files as optional so they are silently skipped if missing (perfect for `.gitignore`d local overrides)
- Use glob wildcards to load all files in a directory (for plugin-style settings)
- Files are included in order, and each file shares the same namespace as all previous files — so any setting can be read and modified by a later file
- Compatible with Django's `runserver` auto-reloading
- No magic, no meta-classes, no custom configuration format — just Python files

**What django-split-settings does NOT do:**

- It does not read environment variables. That is the job of django-environ (covered in a separate guide).
- It does not encrypt or protect secrets.
- It does not provide any settings UI or validation beyond what Python gives you.

---

## 2. How It Works Under the Hood

The library is deliberately simple. The `include()` function:

1. Takes the calling scope's `globals()` dictionary (your `__init__.py`'s namespace)
2. Iterates over the file paths you provide
3. For each file, compiles and executes it, passing the same globals dictionary
4. The file's assignments (`DEBUG = True`, etc.) modify that shared globals dictionary directly

This is the same mechanism Python uses for `exec()` with a shared namespace. The result is that every included file sees all the settings defined by every file that came before it.

```
settings/__init__.py calls include('components/base.py', 'components/database.py', ...)

  components/base.py executes:         globals = {BASE_DIR, INSTALLED_APPS, ...}
  components/database.py executes:     globals = {BASE_DIR, INSTALLED_APPS, DATABASES, ...}
  components/email.py executes:        globals = {BASE_DIR, ..., DATABASES, EMAIL_BACKEND, ...}
  ...
  components/local.py executes:        globals = {all previous settings + any overrides}

Final result: Django's settings are the accumulated globals dictionary.
```

This design means there is no magic. Any Python you can write in `settings.py` you can write in a component file. Imports work. Conditionals work. Loops work.

---

## 3. Installation

### Step 1: Install the package

```bash
pip install django-split-settings

# or with uv
uv add django-split-settings

# or with poetry
poetry add django-split-settings
```

### Step 2: No changes to INSTALLED_APPS

django-split-settings does not go into `INSTALLED_APPS`. It is used only in your settings package.

### Step 3: Convert `settings.py` to a package

This is a one-time migration.

```bash
# Before:
myproject/
├── manage.py
├── myproject/
│   ├── __init__.py
│   ├── urls.py
│   └── settings.py       # single flat file

# After:
myproject/
├── manage.py
├── myproject/
│   ├── __init__.py
│   ├── urls.py
│   └── settings/         # new package
│       ├── __init__.py   # replaces settings.py — contains only the include() call
│       └── components/
│           ├── base.py
│           ├── database.py
│           └── ...
```

**Migration steps:**

```bash
# 1. Create the settings directory
mkdir myproject/settings
mkdir myproject/settings/components

# 2. Create the __init__.py (the entry point)
touch myproject/settings/__init__.py

# 3. Move the old settings.py content into component files
# (you will split it manually)

# 4. Delete the old settings.py
rm myproject/settings.py
```

No changes are needed to `manage.py`, `wsgi.py`, or `asgi.py`. Django discovers settings via the `DJANGO_SETTINGS_MODULE` environment variable, which already points to `myproject.settings`. Now that `settings` is a package, Python will find `settings/__init__.py` automatically.

---

## 4. Your First Split Settings Structure

Here is the simplest possible structure after migrating from a single `settings.py`.

### `settings/__init__.py`

This file contains **only** the `include()` call. All actual settings live in component files.

```python
# settings/__init__.py
from split_settings.tools import optional, include

include(
    'components/base.py',
    'components/database.py',
    'components/cache.py',
    'components/email.py',
    'components/logging.py',
    'components/security.py',
    optional('components/local.py'),   # developer overrides, not committed
)
```

### `settings/components/base.py`

```python
# settings/components/base.py
import os
from pathlib import Path

# BASE_DIR must point to the project root (see Section 10 for why we go up 3 levels)
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-only-insecure-key')
DEBUG = os.environ.get('DEBUG', 'on') == 'on'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # your apps
    'myapp',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'myproject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'myproject.wsgi.application'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

### `settings/components/database.py`

```python
# settings/components/database.py
import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'mydb'),
        'USER': os.environ.get('DB_USER', 'myuser'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'CONN_MAX_AGE': int(os.environ.get('CONN_MAX_AGE', '60')),
    }
}
```

### `settings/components/local.py` (not committed)

```python
# settings/components/local.py
# This file is in .gitignore. Each developer has their own copy.
# It overrides any settings from the files included before it.

DEBUG = True

INSTALLED_APPS += ['debug_toolbar']   # INSTALLED_APPS was set in base.py

MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Override the database to use a local SQLite file during development
DATABASES['default'] = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': BASE_DIR / 'db.sqlite3',
}
```

Add `settings/components/local.py` to your `.gitignore`:

```bash
# .gitignore
settings/components/local.py
# or if your settings package is inside the project package:
myproject/settings/components/local.py
```

---

## 5. The `include()` Function

`include()` is the core API of django-split-settings. It accepts any number of file path strings and executes them in order within the calling scope.

### Signature

```python
from split_settings.tools import optional, include

include(
    *args,          # one or more file paths (strings or optional() wrapped strings)
    scope=None,     # optional: explicitly pass globals() if needed
)
```

### How File Paths Are Resolved

File paths passed to `include()` are resolved **relative to the file that calls `include()`**. This is usually `settings/__init__.py`, so paths are relative to the `settings/` directory.

```python
# settings/__init__.py

include(
    'components/base.py',      # → settings/components/base.py
    'components/database.py',  # → settings/components/database.py
    '../other_settings.py',    # → relative paths work (but avoid them)
    '/absolute/path/to/file.py',  # absolute paths also work
)
```

### Shared Context

All included files share the same namespace. Variables set by earlier files are available in later files:

```python
# settings/components/base.py
INSTALLED_APPS = ['django.contrib.admin', 'django.contrib.auth']
DEBUG = False

# settings/components/local.py
# INSTALLED_APPS and DEBUG are available here without any import
DEBUG = True
INSTALLED_APPS += ['debug_toolbar']   # modifies the list from base.py
```

### Explicitly Passing Scope

In almost all cases, `include()` automatically captures the correct `globals()`. If you are calling `include()` from inside a function or a nested scope, you may need to pass `scope=globals()` explicitly:

```python
# settings/__init__.py

def load_settings():
    include(
        'components/base.py',
        scope=globals(),  # <-- required when calling from inside a function
    )

load_settings()
```

In practice, the automatic scope capture works correctly for the common case of calling `include()` at module level in `__init__.py`. Do not add `scope=globals()` unless you actually encounter a scope problem.

---

## 6. The `optional()` Wrapper

`optional()` marks a file path as optional. If the file does not exist, it is silently skipped. If the file exists and contains a Python error, that error is still raised normally.

```python
from split_settings.tools import optional, include

include(
    'components/base.py',        # required — raises OSError if missing
    optional('components/local.py'),  # optional — silently skipped if missing
)
```

### Common Uses for `optional()`

**Per-developer local overrides:**

```python
include(
    'components/base.py',
    'components/database.py',
    optional('components/local.py'),  # each developer has their own; not committed
)
```

**CI-specific overrides:**

```python
include(
    'components/base.py',
    optional('components/ci.py'),     # only exists in CI; absent in dev and production
)
```

**Machine-specific production overrides:**

```python
include(
    'components/base.py',
    'components/production.py',
    optional('/etc/myapp/local_settings.py'),   # absolute path on the server
)
```

**Feature flag testing:**

```python
include(
    'components/base.py',
    optional('components/feature_x.py'),   # toggle experimental feature
)
```

---

## 7. Wildcards — Loading Files Dynamically

`include()` passes all non-optional paths through Python's `glob.glob()`. This means you can use standard glob wildcards to include all files matching a pattern.

```python
include(
    'components/base.py',
    'components/*.py',             # load all .py files in components/
)
```

**Important:** Files matched by wildcards are loaded in the order that `glob.glob()` returns them. This is typically the same as `ls -U` (directory order), which is **not** alphabetical. If you need a specific order, include files explicitly by name rather than using wildcards.

### Plugin-Style Settings

Wildcards enable a plugin pattern where each installed third-party package gets its own settings file:

```
settings/
├── __init__.py
├── components/
│   ├── base.py
│   ├── database.py
│   └── third_party/
│       ├── celery.py
│       ├── redis.py
│       ├── sentry.py
│       └── stripe.py
```

```python
# settings/__init__.py
include(
    'components/base.py',
    'components/database.py',
    'components/third_party/*.py',    # load all third-party configs automatically
    optional('components/local.py'),
)
```

### Combining Explicit and Wildcard Includes

```python
include(
    'components/base.py',         # must be first — defines INSTALLED_APPS etc.
    'components/database.py',     # must be second — uses BASE_DIR from base.py
    'components/packages/*.py',   # order within this group doesn't matter
    'components/security.py',     # must come after packages (may use their settings)
    optional('components/local.py'),  # always last
)
```

---

## 8. Environment-Based Settings Switching

A common pattern is to switch between different settings files based on an environment variable. This lets you have explicit, separate files for development, staging, and production — rather than one file with many `if DEBUG:` branches.

### Pattern A: Override File Per Environment

The most common pattern. A shared base file applies everywhere, and an environment-specific file applies overrides on top.

```python
# settings/__init__.py
import os
from split_settings.tools import optional, include

ENVIRONMENT = os.environ.get('DJANGO_ENV', 'development')

include(
    'components/base.py',
    f'environments/{ENVIRONMENT}.py',     # load development.py or production.py
    optional('components/local.py'),       # developer local overrides on top
)
```

```
settings/
├── __init__.py
├── components/
│   └── base.py
└── environments/
    ├── development.py
    ├── staging.py
    └── production.py
```

```python
# settings/environments/development.py
DEBUG = True
INTERNAL_IPS = ['127.0.0.1']
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
```

```python
# settings/environments/production.py
DEBUG = False
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

Set the environment variable wherever your app runs:

```bash
# Local development (in your shell or .env file)
export DJANGO_ENV=development

# Production server (in systemd, Docker, or Heroku)
DJANGO_ENV=production

# CI
DJANGO_ENV=ci
```

### Pattern B: Entirely Separate Include Lists

A more explicit approach that makes each environment completely self-contained:

```python
# settings/__init__.py
import os
from split_settings.tools import optional, include

ENVIRONMENT = os.environ.get('DJANGO_ENV', 'development')

if ENVIRONMENT == 'production':
    include(
        'components/base.py',
        'components/database.py',
        'components/production_security.py',
        'components/production_logging.py',
    )
elif ENVIRONMENT == 'ci':
    include(
        'components/base.py',
        'components/ci_database.py',
        'components/ci_email.py',
    )
else:
    include(
        'components/base.py',
        'components/database.py',
        'components/development.py',
        optional('components/local.py'),
    )
```

### Pattern C: Feature Flags via Optional Files

```python
# settings/__init__.py
import os
from split_settings.tools import optional, include

include(
    'components/base.py',
    'components/database.py',
    optional('components/feature_payments.py'),  # exists only when payments are enabled
    optional('components/feature_ai.py'),         # exists only when AI is enabled
    optional('components/local.py'),
)
```

A developer enables a feature by creating the corresponding file. This keeps base settings clean and avoids sprawling feature-flag conditionals.

---

## 9. Modifying Settings from Previous Files

Because all files share the same namespace, modifying a setting set by an earlier file is straightforward. This is how you extend lists, dictionaries, and other mutable structures.

### Extending Lists

```python
# components/base.py
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    # ...
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # ...
]

# components/local.py — adds to the lists defined above
INSTALLED_APPS += [
    'debug_toolbar',
    'django_extensions',
]

MIDDLEWARE += [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]
```

### Modifying Nested Dictionaries

```python
# components/base.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'mydb',
        # ...
    }
}

# components/local.py — replace the default database for local development
DATABASES['default'] = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': BASE_DIR / 'db.sqlite3',
}

# Or update specific keys within the existing config:
DATABASES['default']['CONN_MAX_AGE'] = 0   # disable persistent connections locally
```

### Conditionally Adding to Settings

```python
# components/production.py
import os

if os.environ.get('USE_REDIS_CACHE', 'off') == 'on':
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': os.environ['CACHE_URL'],
        }
    }
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
```

### Using Settings from Earlier Files in Expressions

```python
# components/logging.py
import os

# BASE_DIR was set in base.py, it is available here
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': str(LOG_DIR / 'django.log'),
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'WARNING',
    },
}
```

---

## 10. Fixing `BASE_DIR` After Converting to a Package

This is the most common source of confusion when migrating to a split settings structure, and it trips up nearly every team.

### What Changes

When your settings lived in `settings.py`, the path was:

```
/home/user/myproject/myproject/settings.py
```

And `BASE_DIR` was calculated as:

```python
# settings.py
BASE_DIR = Path(__file__).resolve().parent.parent
# Path(__file__) = /home/user/myproject/myproject/settings.py
# .parent        = /home/user/myproject/myproject/   (the inner package)
# .parent        = /home/user/myproject/              (the project root)
```

Now your settings entry point is:

```
/home/user/myproject/myproject/settings/__init__.py
```

If you keep the same calculation in `settings/__init__.py`:

```python
# settings/__init__.py — WRONG
BASE_DIR = Path(__file__).resolve().parent.parent
# Path(__file__) = /home/user/myproject/myproject/settings/__init__.py
# .parent        = /home/user/myproject/myproject/settings/   (the settings package)
# .parent        = /home/user/myproject/myproject/             (the inner package, NOT the root!)
```

`BASE_DIR` now points to the wrong directory, and `STATIC_ROOT`, `MEDIA_ROOT`, and template directories will be wrong.

### The Fix

Add one more `.parent` wherever `BASE_DIR` is calculated. The number of `.parent` calls needed equals the number of directories between `__file__` and the project root.

```
File location:   /home/user/myproject/ myproject/ settings/ __init__.py
Levels to root:         3 up ↑             2 up ↑    1 up ↑    start
```

```python
# settings/__init__.py or settings/components/base.py — CORRECT
BASE_DIR = Path(__file__).resolve().parent.parent.parent
#                                   ^      ^      ^
#                              settings  myproject  project root
```

Or if your component files are inside `settings/components/`:

```
File location:   /home/user/myproject/ myproject/ settings/ components/ base.py
Levels to root:         4 up ↑             3 up ↑    2 up ↑    1 up ↑    start
```

```python
# settings/components/base.py — CORRECT
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
#                                   ^       ^      ^       ^
#                             components settings myproject root
```

### Verifying BASE_DIR

Add this temporarily to your settings to verify the path is correct:

```python
import sys
print(f"BASE_DIR = {BASE_DIR}", file=sys.stderr)
# Run: python manage.py check
# Should print: BASE_DIR = /home/user/myproject
```

---

## 11. Recommended Project Structures

Here are three real-world project structures for different sizes and complexity levels.

### Structure A: Simple (Small Projects)

Good for projects with one or two developers and straightforward environment needs.

```
myproject/
├── manage.py
├── requirements.txt
├── .env                          ← not committed
├── .env.example                  ← committed
├── .gitignore
└── config/                       ← or myproject/ — the Django project package
    ├── __init__.py
    ├── urls.py
    ├── wsgi.py
    └── settings/
        ├── __init__.py           ← include() call lives here
        ├── base.py               ← all shared settings
        └── local.py              ← developer overrides, not committed
```

```python
# config/settings/__init__.py
from split_settings.tools import optional, include

include(
    'base.py',
    optional('local.py'),
)
```

### Structure B: Standard (Medium Projects)

Good for teams of 3–10 developers with clear dev/staging/production environments.

```
myproject/
├── manage.py
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
├── .env
├── .env.example
└── config/
    ├── __init__.py
    ├── urls.py
    ├── wsgi.py
    └── settings/
        ├── __init__.py           ← environment switch + include()
        ├── components/
        │   ├── base.py           ← core Django settings
        │   ├── apps.py           ← INSTALLED_APPS only
        │   ├── database.py       ← DATABASES
        │   ├── cache.py          ← CACHES
        │   ├── email.py          ← email settings
        │   ├── logging.py        ← LOGGING
        │   ├── security.py       ← security headers, HSTS, etc.
        │   └── storage.py        ← static/media file storage
        ├── environments/
        │   ├── development.py    ← debug toolbar, console email
        │   ├── staging.py        ← production-like but with test data
        │   ├── production.py     ← hardened security settings
        │   └── ci.py             ← fast tests, in-memory cache
        └── local.py              ← per-developer overrides, not committed
```

```python
# config/settings/__init__.py
import os
from split_settings.tools import optional, include

ENVIRONMENT = os.environ.get('DJANGO_ENV', 'development')

include(
    'components/base.py',
    'components/apps.py',
    'components/database.py',
    'components/cache.py',
    'components/email.py',
    'components/logging.py',
    'components/security.py',
    'components/storage.py',
    f'environments/{ENVIRONMENT}.py',
    optional('local.py'),
)
```

### Structure C: Advanced (Large Projects / Microservices)

Good for large codebases where multiple Django services share some common settings.

```
myproject/
├── manage.py
├── shared_settings/              ← shared across multiple Django services
│   ├── __init__.py
│   ├── logging.py
│   └── security.py
└── services/
    ├── api/                      ← REST API service
    │   ├── config/
    │   │   └── settings/
    │   │       ├── __init__.py
    │   │       └── components/
    │   └── manage.py
    └── admin/                    ← Admin dashboard service
        ├── config/
        │   └── settings/
        │       ├── __init__.py
        │       └── components/
        └── manage.py
```

```python
# services/api/config/settings/__init__.py
from split_settings.tools import optional, include

include(
    'components/base.py',
    '../../../../shared_settings/logging.py',      # shared logging config
    '../../../../shared_settings/security.py',     # shared security config
    optional('components/local.py'),
)
```

---

## 12. Using django-split-settings with django-environ

These two libraries are designed to work together. django-split-settings handles the **structure** of your settings (multiple files), and django-environ handles reading **values** from environment variables. The combination gives you well-organized, 12-factor-compliant settings.

### The Standard Pattern

Initialize `environ.Env` in `base.py` (the first file loaded) and let it flow into all subsequent files via the shared namespace.

```python
# settings/components/base.py
import environ
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# Create the env object once — available to all subsequent component files
env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
)
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env('ALLOWED_HOSTS')

INSTALLED_APPS = [
    # ...
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
```

```python
# settings/components/database.py
# `env` is available here because it was set in base.py (shared namespace)
DATABASES = {
    'default': env.db(),  # reads DATABASE_URL
}
```

```python
# settings/components/cache.py
CACHES = {
    'default': env.cache('CACHE_URL', default='locmemcache://'),
}
```

```python
# settings/components/email.py
EMAIL_CONFIG = env.email('EMAIL_URL', default='consolemail://')
vars().update(EMAIL_CONFIG)
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@example.com')
```

```python
# settings/__init__.py
import os
from split_settings.tools import optional, include

ENVIRONMENT = os.environ.get('DJANGO_ENV', 'development')

include(
    'components/base.py',        # initializes `env`, sets core settings
    'components/database.py',    # uses `env` from base.py
    'components/cache.py',       # uses `env` from base.py
    'components/email.py',       # uses `env` from base.py
    'components/logging.py',
    'components/security.py',
    f'environments/{ENVIRONMENT}.py',
    optional('components/local.py'),
)
```

### Testing with a Specific `.env` File

During tests, you may want to use a test-specific `.env` file with an in-memory database and dummy email backend:

```python
# settings/environments/test.py
# Override DATABASE_URL for tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}
```

```bash
DJANGO_ENV=test python manage.py test
```

---

## 13. Running the Dev Server and Tests

Django identifies your settings module via the `DJANGO_SETTINGS_MODULE` environment variable. With split settings, this still points to `myproject.settings` (the package). Django finds `settings/__init__.py` automatically.

### `manage.py`

No changes are needed. Your `manage.py` should already have:

```python
# manage.py
import os
import sys

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    # ...
```

### Setting `DJANGO_ENV` for Development

```bash
# Option 1: Export in your shell (lasts for the session)
export DJANGO_ENV=development
python manage.py runserver

# Option 2: Inline (lasts for one command)
DJANGO_ENV=development python manage.py runserver

# Option 3: In your .env file (if using django-environ's read_env in __init__.py)
# DJANGO_ENV=development

# Option 4: In direnv (automatic on cd into the project)
# .envrc:
# export DJANGO_ENV=development
```

### pytest

Use `pytest-django` with the `DJANGO_SETTINGS_MODULE` pointing to your settings package:

```ini
# pytest.ini or setup.cfg
[pytest]
DJANGO_SETTINGS_MODULE = config.settings
```

Or set `DJANGO_ENV=ci` to switch to a faster test configuration:

```bash
DJANGO_ENV=ci pytest
```

### Auto-reloading

django-split-settings maintains compatibility with Django's `runserver` auto-reloader. When any of your component files change, the server restarts automatically — you do not need to do anything special to enable this.

---

## 14. Common Pitfalls & Troubleshooting

**Problem: `STATIC_ROOT`, `MEDIA_ROOT`, or template directories point to the wrong location**

Cause: `BASE_DIR` was not updated after converting `settings.py` to a package. It is pointing one level too shallow.

Fix: See Section 10. Count the directory levels between your `__file__` and the project root, and use the correct number of `.parent` calls.

---

**Problem: `OSError: No such file or directory: 'components/base.py'`**

Cause: The path passed to `include()` is wrong. Paths are relative to the file that calls `include()` (usually `settings/__init__.py`).

Fix: Verify the path. If your `__init__.py` is at `config/settings/__init__.py`, then `'components/base.py'` refers to `config/settings/components/base.py`. Print the working directory if you are unsure:

```python
import os
print("CWD:", os.getcwd())
print("__file__:", __file__)
```

---

**Problem: A variable from `base.py` is not available in `database.py`**

Cause: The files are not included in order, or there is a bug in one of the files that caused it to not execute fully.

Fix: Check the include order in `__init__.py`. `base.py` must come before any file that references its variables. Check for Python errors in `base.py` (run `python manage.py check` for a quick check).

---

**Problem: `INSTALLED_APPS += ['debug_toolbar']` fails with `NameError: name 'INSTALLED_APPS' is not defined`**

Cause: The `local.py` file is being loaded before `base.py`, or `base.py` was not included at all.

Fix: Verify `__init__.py` lists files in the correct order.

---

**Problem: Wildcard includes are loading files in the wrong order**

Cause: `glob.glob()` does not guarantee alphabetical order. It returns files in directory order.

Fix: If order matters, include files by explicit name rather than wildcard. If you must use wildcards, name your files with a numeric prefix to force a consistent order: `01_base.py`, `02_database.py`, etc.

---

**Problem: Changes to component files do not trigger `runserver` auto-reload**

This is rare but can happen with some file system setups. If it does, restart the server manually. In normal cases, auto-reloading should work.

---

**Problem: `ImproperlyConfigured: The SECRET_KEY setting must not be empty`**

Cause: `SECRET_KEY` is not set in any component file or in the environment.

Fix: Add `SECRET_KEY` to your `base.py` or read it from an environment variable. Never hardcode real secret keys — at minimum, use `os.environ.get('SECRET_KEY', 'dev-only-key-do-not-use-in-production')`.

---

**Problem: Tests pick up the wrong settings when running in CI**

Cause: `DJANGO_SETTINGS_MODULE` or `DJANGO_ENV` is not set correctly in the CI environment.

Fix: Set both in your CI configuration:

```yaml
# GitHub Actions example
env:
  DJANGO_SETTINGS_MODULE: config.settings
  DJANGO_ENV: ci
```

---

## 15. Checklist

Use this every time you add or configure django-split-settings in a project.

### Initial Setup

- [ ] `settings.py` has been renamed/moved to `settings/__init__.py`
- [ ] `settings/` is a proper Python package (has `__init__.py`)
- [ ] `settings/__init__.py` contains only the `include()` call, no actual settings
- [ ] `manage.py`, `wsgi.py`, and `asgi.py` still point to `yourproject.settings` — no changes needed
- [ ] `DJANGO_SETTINGS_MODULE` still works and resolves to the new package

### BASE_DIR

- [ ] `BASE_DIR` is calculated in the first included component file (usually `base.py`), not in `__init__.py`
- [ ] The number of `.parent` calls in `BASE_DIR` is correct for the new file location
- [ ] `STATIC_ROOT`, `MEDIA_ROOT`, and template directories resolve to the right paths

### File Structure

- [ ] Component files are logically named (base, database, cache, email, logging, security)
- [ ] Each component file contains one area of concern
- [ ] Environment-specific files are in an `environments/` directory
- [ ] The local override file (`local.py`) is in `.gitignore`
- [ ] A `.env.example` or `local.py.example` is committed to show what keys are needed

### `include()` Usage

- [ ] Required files are not wrapped in `optional()`
- [ ] Local/developer override files are wrapped in `optional()`
- [ ] File order in `include()` matches dependency order (base.py before files that use its variables)
- [ ] Environment switching uses `os.environ.get('DJANGO_ENV', 'development')` with a sensible default

### Modification of Existing Settings

- [ ] List extensions use `+= [...]` not `= [...]` (to avoid overwriting)
- [ ] Dictionary modifications use `['key'] = value` not replacing the entire dict (unless intended)
- [ ] Conditionals in component files handle the case where earlier-file variables might not exist

### Testing and CI

- [ ] Tests run with the correct `DJANGO_ENV` set
- [ ] CI pipeline sets both `DJANGO_SETTINGS_MODULE` and `DJANGO_ENV`
- [ ] A CI-specific environment file exists with fast test settings (in-memory db, dummy cache)
- [ ] `pytest.ini` or `setup.cfg` sets `DJANGO_SETTINGS_MODULE` for local test runs

---

*Official documentation: https://django-split-settings.readthedocs.io/ — always check for the latest options.*