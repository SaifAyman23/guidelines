# django-environ — The Complete Guide

> A thorough, example-driven reference for installing, configuring, and mastering django-environ — the library that lets you configure Django using environment variables and `.env` files, following the Twelve-Factor App methodology.

**Current version as of this writing:** 0.12+
**Official docs:** https://django-environ.readthedocs.io/
**Source:** https://github.com/joke2k/django-environ
**PyPI:** https://pypi.org/project/django-environ/

---

## Table of Contents

- [django-environ — The Complete Guide](#django-environ--the-complete-guide)
  - [Table of Contents](#table-of-contents)
  - [1. What is django-environ and Why Use It](#1-what-is-django-environ-and-why-use-it)
  - [2. How It Works Under the Hood](#2-how-it-works-under-the-hood)
  - [3. Installation](#3-installation)
    - [Step 1: Install the package](#step-1-install-the-package)
    - [Step 2: No changes to INSTALLED\_APPS](#step-2-no-changes-to-installed_apps)
    - [Step 3: Add `.env` to `.gitignore`](#step-3-add-env-to-gitignore)
  - [4. Your First `.env` File](#4-your-first-env-file)
  - [5. The `environ.Env` Object](#5-the-environenv-object)
    - [Basic Setup](#basic-setup)
    - [Declaring Defaults in the Constructor vs. at Read Time](#declaring-defaults-in-the-constructor-vs-at-read-time)
  - [6. Type Casting — Reading Values with the Right Type](#6-type-casting--reading-values-with-the-right-type)
    - [All Available Typed Readers](#all-available-typed-readers)
    - [Reading Nested Lists — ADMINS and MANAGERS](#reading-nested-lists--admins-and-managers)
    - [Reading Dictionaries](#reading-dictionaries)
  - [7. URL Parsers — Databases, Caches, and Email in One Line](#7-url-parsers--databases-caches-and-email-in-one-line)
    - [Database URLs](#database-urls)
    - [Cache URLs](#cache-urls)
    - [Email URLs](#email-urls)
  - [8. The `Path` Helper](#8-the-path-helper)
  - [9. Docker and Kubernetes — `FileAwareEnv`](#9-docker-and-kubernetes--fileawareenv)
  - [10. Prefixing Environment Variables](#10-prefixing-environment-variables)
  - [11. Smart Casting and Its Pitfalls](#11-smart-casting-and-its-pitfalls)
    - [Comment Parsing](#comment-parsing)
  - [12. Multiple `.env` Files](#12-multiple-env-files)
  - [13. A Full Production `settings.py` Example](#13-a-full-production-settingspy-example)
  - [14. Using django-environ with Split Settings](#14-using-django-environ-with-split-settings)
  - [15. Common Pitfalls \& Troubleshooting](#15-common-pitfalls--troubleshooting)
  - [16. Checklist](#16-checklist)
    - [Initial Setup](#initial-setup)
    - [Variable Declarations](#variable-declarations)
    - [URL Parsers](#url-parsers)
    - [Docker / Kubernetes](#docker--kubernetes)
    - [Environment-Specific](#environment-specific)

---

## 1. What is django-environ and Why Use It

Every non-trivial Django project needs at least two configurations: one for local development and one for production. The naive approach is to keep multiple `settings_local.py`, `settings_production.py` files and flip between them manually. This approach creates several problems. Secrets leak into version control. Developers overwrite each other's local settings. Deployment gets complicated.

**The Twelve-Factor App** methodology (https://12factor.net/config) defines the correct solution: store configuration in the **environment**, not in the code. Your `settings.py` should read values from environment variables, and the values themselves should live outside your repository entirely.

**django-environ** makes this painless. It provides a clean API to read environment variables from a `.env` file or from the real OS environment, parse them into typed Python values, and configure Django's settings with them — all in a few lines of code.

**What django-environ gives you:**

- A single `Env` object that reads from environment variables with type-safe parsing
- Automatic loading of a `.env` file into the environment
- URL string parsers for databases, caches, and email that turn a single connection string into Django's nested settings dictionaries
- A `Path` helper for building filesystem paths robustly
- `FileAwareEnv` for Docker and Kubernetes secrets mounted as files
- Support for defaults, so missing variables fail loudly instead of silently

**What django-environ does NOT do:**

- It does not manage multiple settings files. That is the job of django-split-settings (covered in a separate guide).
- It does not encrypt your secrets. It only reads them from outside your codebase.
- It does not set variables for you. You or your deployment system must provide them.

**The mental model:** Your `.env` file is a development convenience that simulates what a production environment would inject. In production, your environment variables come from your server, Docker container, Heroku config, or Kubernetes secret — not from any file.

---

## 2. How It Works Under the Hood

When you call `environ.Env.read_env(path_to_env_file)`, the library reads the file line by line and calls `os.environ.setdefault()` for each key-value pair. The critical word is **setdefault**: it only sets the value if that key is not already present in the real environment. This means real OS environment variables always win over `.env` file values. You can override any `.env` setting from the outside without touching the file.

```
Your .env file:
  DEBUG=on
  DATABASE_URL=psql://user:pass@localhost/mydb

     ↓  environ.Env.read_env()
     ↓  calls os.environ.setdefault() for each line

os.environ (after read_env):
  DEBUG=on             ← from .env file
  DATABASE_URL=...     ← from .env file
  SECRET_KEY=...       ← already existed from real environment, unchanged

     ↓  env('DEBUG') / env.bool('DEBUG') / env.db()
     ↓  reads from os.environ and casts to the right Python type

settings.py values:
  DEBUG = True         ← cast from string 'on' → Python bool True
  DATABASES = {...}    ← parsed from URL string into Django's dict format
  SECRET_KEY = '...'   ← read directly from real environment
```

This flow means you never hardcode secrets. Your `.env` file contains development-only values and is added to `.gitignore`. Production values come from wherever your deployment platform injects them.

---

## 3. Installation

### Step 1: Install the package

```bash
pip install django-environ

# or with uv
uv add django-environ

# or with poetry
poetry add django-environ
```

### Step 2: No changes to INSTALLED_APPS

Unlike many Django packages, django-environ does **not** go into `INSTALLED_APPS`. It is a plain Python utility you import in `settings.py`.

### Step 3: Add `.env` to `.gitignore`

This step is mandatory. Your `.env` file will contain real secrets and must never be committed.

```bash
# .gitignore
.env
.env.*
!.env.example
```

Create a `.env.example` file that contains all the keys but with placeholder values. Commit this file. New developers copy it to `.env` and fill in real values.

```bash
# .env.example
DEBUG=on
SECRET_KEY=replace-this-with-a-real-secret-key
DATABASE_URL=psql://user:password@127.0.0.1:5432/dbname
CACHE_URL=redis://127.0.0.1:6379/0
EMAIL_URL=consolemail://
ALLOWED_HOSTS=localhost,127.0.0.1
```

---

## 4. Your First `.env` File

The `.env` file uses a simple `KEY=value` syntax. Here are the important rules:

```bash
# .env

# Comments start with #
# Inline comments are NOT stripped by default (see Section 11 on parse_comments)

# Strings — no quotes needed for simple values
DEBUG=on
SITE_NAME=My Django App

# Strings with spaces — use quotes
SITE_TAGLINE="The best Django app around"

# Numbers — stored as strings, cast by your code
MAX_UPLOAD_MB=25
TIMEOUT_SECONDS=30

# Booleans — these all evaluate to True:
# true, on, ok, y, yes, 1
DEBUG=on
FEATURE_FLAG=True
SEND_EMAIL=yes

# Booleans — these all evaluate to False:
# false, off, no, n, 0
MAINTENANCE_MODE=off

# Lists — comma-separated
ALLOWED_HOSTS=mysite.com,www.mysite.com,localhost

# Admins — see Section 6 for parsing this format
DJANGO_ADMINS=Alice <alice@example.com>, Bob <bob@example.com>

# Multi-line values — use a backslash to continue on the next line
LONG_VALUE=this is a very \
    long value split \
    across lines

# Secrets — treat these exactly like any other variable
SECRET_KEY=50-character-random-string-here
DATABASE_URL=psql://myuser:mypassword@127.0.0.1:5432/mydb
```

**Unsafe characters in passwords:** If your password contains `#`, `@`, `:`, `/`, or other URL-special characters, you must URL-encode them when they appear inside connection URLs. Use Python's `urllib.parse.quote()` to encode the value first, then put the encoded string in your `.env` file.

```python
# One-time helper to encode a password
from urllib.parse import quote
print(quote("p@ssw#rd!"))
# Output: p%40ssw%23rd%21

# Then in .env:
# DATABASE_URL=psql://user:p%40ssw%23rd%21@127.0.0.1:5432/mydb
```

---

## 5. The `environ.Env` Object

Everything starts with creating an `Env` instance. You do this at the top of `settings.py`, before reading any values.

### Basic Setup

```python
# settings.py
import environ
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Create the Env object.
# You can declare types and defaults here to validate on startup.
env = environ.Env(
    # Declare expected types and default values.
    # Format: VARIABLE_NAME=(type, default_value)
    # Variables without defaults are REQUIRED — missing them raises ImproperlyConfigured.
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
)

# Read the .env file.
# os.path.join(BASE_DIR, '.env') locates the file relative to your project root.
# The second argument (overwrite=False by default) prevents .env from overriding
# real environment variables already set.
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# Now read settings from the environment.
DEBUG = env('DEBUG')                          # bool, defaults to False if not set
SECRET_KEY = env('SECRET_KEY')                # str, REQUIRED — raises error if missing
ALLOWED_HOSTS = env('ALLOWED_HOSTS')          # list, defaults to []
```

### Declaring Defaults in the Constructor vs. at Read Time

You have two places to declare defaults: in the `Env()` constructor, or as an argument to each `env()` call. Both work; use whichever keeps your settings.py readable.

```python
# Option A: declare defaults in the constructor
env = environ.Env(
    DEBUG=(bool, False),
    PORT=(int, 8000),
)
DEBUG = env('DEBUG')     # returns False if not in environment
PORT = env('PORT')       # returns 8000 if not in environment

# Option B: declare defaults at read time
env = environ.Env()
DEBUG = env.bool('DEBUG', default=False)
PORT = env.int('PORT', default=8000)

# Option C: require a variable (no default means it's mandatory)
env = environ.Env()
SECRET_KEY = env('SECRET_KEY')  # raises ImproperlyConfigured if missing
```

---

## 6. Type Casting — Reading Values with the Right Type

All environment variables are strings in the OS. django-environ provides typed reader methods that cast the string to the appropriate Python type.

### All Available Typed Readers

```python
env = environ.Env()

# --- Strings ---
name = env.str('SITE_NAME')
name = env('SITE_NAME')             # str() is the default when no type is given

# --- Booleans ---
# Truthy: 'true', 'on', 'ok', 'y', 'yes', '1'
# Falsy:  'false', 'off', 'no', 'n', '', '0'
debug = env.bool('DEBUG')
debug = env.bool('DEBUG', default=False)

# --- Integers ---
port = env.int('PORT')
port = env.int('PORT', default=8000)

# --- Floats ---
rate = env.float('TAX_RATE')
rate = env.float('TAX_RATE', default=0.0)

# --- Decimal ---
from decimal import Decimal
price = env.decimal('MIN_PRICE', default=Decimal('0.00'))

# --- Lists (comma-separated) ---
# 'localhost,mysite.com,www.mysite.com' → ['localhost', 'mysite.com', 'www.mysite.com']
hosts = env.list('ALLOWED_HOSTS')
hosts = env.list('ALLOWED_HOSTS', default=[])

# --- Tuples ---
# Same as list but returns a tuple
coords = env.tuple('COORDINATES')

# --- JSON ---
# Parses arbitrary JSON from an env var
config = env.json('MY_JSON_CONFIG')
# MY_JSON_CONFIG='{"key": "val", "numbers": [1, 2, 3]}'
# → {'key': 'val', 'numbers': [1, 2, 3]}

# --- Bytes ---
key_bytes = env.bytes('ENCRYPTION_KEY')

# --- Datetime ---
dt = env.datetime('EVENT_DATETIME')
# Accepts ISO 8601 format: 2024-06-15T14:30:00

# --- Date ---
d = env.date('START_DATE')
# Accepts: 2024-06-15

# --- Time ---
t = env.time('DAILY_RUN_AT')
# Accepts: 14:30:00

# --- Timedelta ---
delta = env.timedelta('SESSION_AGE')
# Accepts seconds as integer: 86400 → datetime.timedelta(seconds=86400)

# --- Paths (see Section 8) ---
media_root = env.path('MEDIA_ROOT')
```

### Reading Nested Lists — ADMINS and MANAGERS

Django's `ADMINS` and `MANAGERS` settings are lists of `(name, email)` tuples. Environment variables are flat strings, so you have to parse them yourself:

```python
from email.utils import getaddresses

# In .env:
# DJANGO_ADMINS=Alice Judge <alice@example.com>, Bob <bob@example.com>

ADMINS = getaddresses([env('DJANGO_ADMINS', default='')])
# → [('Alice Judge', 'alice@example.com'), ('Bob', 'bob@example.com')]
```

### Reading Dictionaries

```python
# In .env:
# MY_DICT=key=val,foo=bar
config = env.parse_value('key=val,foo=bar', dict)
# → {'key': 'val', 'foo': 'bar'}

# With typed values in the dict:
# MY_DICT=key=val;foo=1.1;baz=True
config = env.parse_value('key=val;foo=1.1;baz=True', dict(value=str, cast=dict(foo=float, baz=bool)))
# → {'key': 'val', 'foo': 1.1, 'baz': True}
```

---

## 7. URL Parsers — Databases, Caches, and Email in One Line

The most powerful feature of django-environ is its URL parsers. Instead of writing Django's verbose nested dictionaries for databases, caches, and email, you express the connection as a single URL string in your `.env` file and let django-environ expand it into the correct format.

### Database URLs

The `env.db()` method reads `DATABASE_URL` (by default) and returns a dictionary that Django's `DATABASES` setting expects.

```python
# settings.py
DATABASES = {
    'default': env.db(),             # reads os.environ['DATABASE_URL']
    'replica': env.db('REPLICA_URL', default='sqlite:////tmp/replica.db'),
}
```

**Supported database URL schemes:**

| URL scheme | Django backend |
|---|---|
| `postgres://` or `postgresql://` or `psql://` or `pgsql://` | `django.db.backends.postgresql` |
| `postgis://` | `django.contrib.gis.db.backends.postgis` |
| `mysql://` or `mysql2://` | `django.db.backends.mysql` |
| `sqlite:///` | `django.db.backends.sqlite3` |
| `sqlite://:memory:` | SQLite in-memory database |
| `oracle://` | `django.db.backends.oracle` |
| `cockroachdb://` | `django_cockroachdb` |
| `mssql://` | SQL Server via `mssql-django` |

**Examples:**

```bash
# .env examples for common databases

# PostgreSQL on localhost
DATABASE_URL=psql://myuser:mypassword@127.0.0.1:5432/mydb

# PostgreSQL on Heroku (the full URL is provided as-is)
DATABASE_URL=postgres://abc:xyz@ec2-123.compute.amazonaws.com:5432/d6abcd

# PostgreSQL via UNIX socket
DATABASE_URL=postgres://myuser:mypassword@%2Fvar%2Frun%2Fpostgresql/mydb

# MySQL
DATABASE_URL=mysql://myuser:mypassword@127.0.0.1:3306/mydb

# SQLite — four slashes for absolute path
DATABASE_URL=sqlite:////home/user/project/db.sqlite3

# SQLite — three slashes for relative path (relative to where Django is run from)
DATABASE_URL=sqlite:///db.sqlite3

# SQLite in-memory (useful for testing)
DATABASE_URL=sqlite://:memory:
```

**Adding extra options to a database URL:**

```bash
# Pass CONN_MAX_AGE and ssl options as query parameters
DATABASE_URL=psql://user:pass@host:5432/db?conn_max_age=60&sslmode=require
```

```python
# Or pass OPTIONS explicitly in Python after parsing
import environ
env = environ.Env()
DATABASES = {
    'default': {
        **env.db(),
        'CONN_MAX_AGE': env.int('CONN_MAX_AGE', default=60),
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}
```

### Cache URLs

The `env.cache()` method reads `CACHE_URL` (by default) and returns a dictionary for Django's `CACHES` setting.

```python
# settings.py
CACHES = {
    'default': env.cache(),           # reads os.environ['CACHE_URL']
    'sessions': env.cache_url('SESSION_CACHE_URL', default='locmemcache://'),
}
```

**Supported cache URL schemes:**

| URL scheme | Django cache backend |
|---|---|
| `memcache://` | `django.core.cache.backends.memcached.PyMemcacheCache` |
| `pymemcache://` | `django.core.cache.backends.memcached.PyMemcacheCache` |
| `pylibmc://` | `django.core.cache.backends.memcached.PyLibMCCache` |
| `redis://` or `rediscache://` | Django's Redis cache |
| `rediss://` | Redis over TLS |
| `locmemcache://` | `django.core.cache.backends.locmem.LocMemCache` (local memory, dev only) |
| `dummycache://` | `django.core.cache.backends.dummy.DummyCache` |
| `filecache:///path/` | `django.core.cache.backends.filebased.FileBasedCache` |

```bash
# .env examples for caches

# Redis (standard)
CACHE_URL=redis://127.0.0.1:6379/0

# Redis with auth
CACHE_URL=redis://:mypassword@127.0.0.1:6379/0

# Redis with TLS
CACHE_URL=rediss://user:password@redis.example.com:6379/0

# Memcached
CACHE_URL=memcache://127.0.0.1:11211

# Multiple Memcached nodes (comma-separated in the netloc)
CACHE_URL=memcache://127.0.0.1:11211,127.0.0.1:11212,127.0.0.1:11213

# Multiple Redis replicas (for redis-py cluster mode)
CACHE_URL=rediscache://master:6379,slave1:6379,slave2:6379/1

# Local memory cache — for development only
CACHE_URL=locmemcache://

# Dummy cache — swallows all writes, always returns None. For testing.
CACHE_URL=dummycache://
```

### Email URLs

The `env.email()` method reads `EMAIL_URL` (by default) and returns a dictionary of individual email settings. The trick is to use `vars().update()` to inject them all into the settings module's namespace at once.

```python
# settings.py
EMAIL_CONFIG = env.email(
    'EMAIL_URL',
    default='consolemail://',    # prints to console in development
)
vars().update(EMAIL_CONFIG)

# This sets all of these settings at once:
# EMAIL_BACKEND
# EMAIL_HOST
# EMAIL_PORT
# EMAIL_USE_TLS
# EMAIL_USE_SSL
# EMAIL_HOST_USER
# EMAIL_HOST_PASSWORD
```

**Supported email URL schemes:**

| URL scheme | Django email backend |
|---|---|
| `smtp://` | `django.core.mail.backends.smtp.EmailBackend` |
| `smtps://` | SMTP with TLS |
| `smtp+tls://` | SMTP with TLS (explicit) |
| `smtp+ssl://` | SMTP with SSL |
| `consolemail://` | `django.core.mail.backends.console.EmailBackend` |
| `filemail://` | `django.core.mail.backends.filebased.EmailBackend` |
| `memorymail://` | `django.core.mail.backends.locmem.EmailBackend` |
| `dummymail://` | `django.core.mail.backends.dummy.EmailBackend` |

```bash
# .env examples for email

# Console (development — prints emails to terminal)
EMAIL_URL=consolemail://

# SMTP with TLS (common for production via SendGrid, Mailgun, etc.)
EMAIL_URL=smtp+tls://myuser@example.com:mypassword@smtp.sendgrid.net:587

# SMTP with SSL (port 465)
EMAIL_URL=smtp+ssl://myuser@example.com:mypassword@smtp.gmail.com:465

# File-based (writes emails to disk — useful for staging)
EMAIL_URL=filemail:///var/mail/django-emails/

# Dummy (swallows all emails silently)
EMAIL_URL=dummymail://
```

---

## 8. The `Path` Helper

django-environ provides a `Path` class that simplifies building filesystem paths in settings. It supports Python's `/` operator for path joining, which is readable and cross-platform.

```python
import environ

env = environ.Env()
environ.Env.read_env()

# Create a Path object from an environment variable
# MEDIA_ROOT must be an absolute path in the .env file
MEDIA_ROOT = env.path('MEDIA_ROOT')

# Or create from a hard-coded base and build sub-paths from it
ROOT = environ.Path(__file__) - 2   # go up 2 levels from settings.py
# If settings.py is at /home/user/myproject/config/settings.py
# ROOT is now /home/user/myproject

STATIC_ROOT = ROOT.path('staticfiles')()
# → '/home/user/myproject/staticfiles'

MEDIA_ROOT = ROOT.path('media')()
# → '/home/user/myproject/media'

TEMPLATES_DIR = ROOT.path('templates')()
# → '/home/user/myproject/templates'

# Path supports the / operator (same as .path())
LOGS_DIR = str(ROOT / 'logs')
# → '/home/user/myproject/logs'

# The Path object itself is not a string; call it to get the string value
root_str = ROOT()             # '/home/user/myproject'
media_path = MEDIA_ROOT()     # '/home/user/myproject/media'
```

**Important note:** When settings is inside a package (common when using django-split-settings), `__file__` refers to the package directory, not the project root. Adjust the number of levels accordingly.

---

## 9. Docker and Kubernetes — `FileAwareEnv`

Docker Swarm and Kubernetes both have a convention for sharing secrets with containers: they mount secret values as **files** inside the container, typically under `/run/secrets/`. A corresponding environment variable with a `_FILE` suffix points to the file path.

For example, instead of setting `SECRET_KEY=mysecretvalue`, the deployment sets `SECRET_KEY_FILE=/run/secrets/secret_key`, and the file at that path contains the secret value.

`environ.FileAwareEnv` is a drop-in replacement for `environ.Env` that automatically handles this pattern. When you call `env('SECRET_KEY')`, it first checks for `SECRET_KEY_FILE`. If that exists, it reads and returns the file's contents. If not, it falls back to looking for `SECRET_KEY` normally.

```python
# settings.py — use FileAwareEnv instead of Env for Docker/Kubernetes compatibility
import environ

env = environ.FileAwareEnv(
    DEBUG=(bool, False),
)
environ.FileAwareEnv.read_env()

# These calls now automatically check SECRET_KEY_FILE first,
# then fall back to SECRET_KEY
SECRET_KEY = env('SECRET_KEY')
DATABASE_URL = env('DATABASE_URL')
```

**Docker Compose example:**

```yaml
# docker-compose.yml
version: '3.8'
secrets:
  secret_key:
    file: ./secrets/secret_key.txt

services:
  web:
    image: myapp
    secrets:
      - secret_key
    environment:
      # Point to the mounted secret file
      - SECRET_KEY_FILE=/run/secrets/secret_key
      # Regular env vars still work normally
      - DEBUG=off
      - DATABASE_URL=psql://user:pass@db:5432/mydb
```

**Kubernetes Secret example:**

```yaml
# kubernetes/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: django-secrets
type: Opaque
stringData:
  secret_key: "your-very-long-secret-key-here"

---
# kubernetes/deployment.yaml
spec:
  containers:
    - name: web
      env:
        - name: SECRET_KEY_FILE
          value: /run/secrets/secret_key
      volumeMounts:
        - name: secrets
          mountPath: /run/secrets
          readOnly: true
  volumes:
    - name: secrets
      secret:
        secretName: django-secrets
```

---

## 10. Prefixing Environment Variables

In shared environments or when multiple Django services run on the same host, you may want to namespace your environment variables to avoid collisions. django-environ supports a `prefix` argument:

```python
import environ

env = environ.Env(prefix='MYAPP_')

# Now env('DEBUG') reads MYAPP_DEBUG from the environment
# env('SECRET_KEY') reads MYAPP_SECRET_KEY
# etc.

DEBUG = env.bool('DEBUG', default=False)   # reads MYAPP_DEBUG
SECRET_KEY = env('SECRET_KEY')             # reads MYAPP_SECRET_KEY
```

```bash
# .env
MYAPP_DEBUG=on
MYAPP_SECRET_KEY=supersecretvalue
MYAPP_DATABASE_URL=psql://user:pass@localhost/mydb
```

---

## 11. Smart Casting and Its Pitfalls

By default, django-environ enables **smart casting**: if you call `env('SOME_VAR')` without specifying a type, and there is a default value declared in the constructor, it infers the type from the default and casts automatically.

```python
env = environ.Env(
    DEBUG=(bool, False),   # default is a bool, so env('DEBUG') will cast to bool
    PORT=(int, 8000),      # default is an int, so env('PORT') will cast to int
)

DEBUG = env('DEBUG')   # smartcast: returns bool, not string
PORT = env('PORT')     # smartcast: returns int, not string
```

**The pitfall:** Smart casting can cause unexpected behavior if your value looks like a type it wasn't meant to be.

```python
# .env
MY_STRING=123

env = environ.Env(MY_STRING=(str, ''))
value = env('MY_STRING')  # returns '123' as a string — correct

# But if the default was accidentally an int:
env = environ.Env(MY_STRING=(int, 0))   # oops, wrong default type
value = env('MY_STRING')  # returns 123 as an int — maybe not what you wanted
```

**To disable smart casting entirely** (and always use explicit typed readers):

```python
env = environ.Env()
env.smart_cast = False   # disable smart casting globally

# Now you must always use typed methods:
DEBUG = env.bool('DEBUG', default=False)
PORT = env.int('PORT', default=8000)
```

The library's next major version will disable smart casting by default. It is good practice to disable it now and use explicit typed methods throughout.

### Comment Parsing

By default, django-environ does **not** strip inline comments from `.env` values:

```bash
# .env
MY_VAR=hello  # this comment becomes part of the value!
```

To strip inline comments, pass `parse_comments=True` to `read_env()`:

```python
environ.Env.read_env(os.path.join(BASE_DIR, '.env'), parse_comments=True)

# Now 'hello  # this comment becomes part of the value!' becomes just 'hello'
```

Note: `parse_comments=True` changes how the `#` character in values is handled. If your values legitimately contain `#` (for example in some passwords), URL-encode them instead of using `parse_comments`.

---

## 12. Multiple `.env` Files

You can read multiple `.env` files by calling `read_env()` more than once. The second call's values will only set variables not already in the environment, because `setdefault()` does not overwrite.

```python
import environ
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()

# Read a shared base .env first
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# Then read an environment-specific override.
# Values from .env.local only apply if not already set by .env
environ_name = os.environ.get('DJANGO_ENV', 'local')
environ.Env.read_env(os.path.join(BASE_DIR, f'.env.{environ_name}'), overwrite=True)
```

**Using `overwrite=True`:** Pass `overwrite=True` to `read_env()` to make the second file's values override the first file's values. This is useful for environment-specific overrides.

```python
# First pass — shared base config
environ.Env.read_env(os.path.join(BASE_DIR, '.env.base'))

# Second pass — local developer overrides, which should win
environ.Env.read_env(os.path.join(BASE_DIR, '.env.local'), overwrite=True)
```

A common project structure for multiple environment files:

```
myproject/
├── .env.base        ← shared defaults, safe to commit (no secrets)
├── .env.example     ← template with all keys, empty values, committed
├── .env             ← developer's local overrides, NEVER committed
├── .env.test        ← test-specific values, often committed
└── .env.production  ← production values, NEVER committed (use real secrets management)
```

---

## 13. A Full Production `settings.py` Example

This is a complete, real-world `settings.py` using django-environ. It handles all of Django's core settings, uses URL parsers for the database/cache/email, and fails loudly if required variables are missing.

```python
# settings.py
import environ
import os
from pathlib import Path
from email.utils import getaddresses

# ---------------------------------------------------------------------------
# Environment setup
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
    CORS_ALLOWED_ORIGINS=(list, []),
    INTERNAL_IPS=(list, ['127.0.0.1']),
    USE_SSL=(bool, False),
    SESSION_COOKIE_AGE=(int, 1209600),   # 2 weeks in seconds
)

# Read .env file — this is a no-op if the file does not exist
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# ---------------------------------------------------------------------------
# Core settings
# ---------------------------------------------------------------------------

SECRET_KEY = env('SECRET_KEY')      # required — no default
DEBUG = env('DEBUG')                # bool, defaults to False

ALLOWED_HOSTS = env('ALLOWED_HOSTS')

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # your apps here
]

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

DATABASES = {
    'default': env.db(),
    # Uncomment for a read replica:
    # 'replica': env.db('REPLICA_URL'),
}
DATABASES['default']['CONN_MAX_AGE'] = env.int('CONN_MAX_AGE', default=60)

# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

CACHES = {
    'default': env.cache('CACHE_URL', default='locmemcache://'),
}

# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------

EMAIL_CONFIG = env.email('EMAIL_URL', default='consolemail://')
vars().update(EMAIL_CONFIG)
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@example.com')
SERVER_EMAIL = env('SERVER_EMAIL', default='errors@example.com')

# ---------------------------------------------------------------------------
# People who get error notifications
# ---------------------------------------------------------------------------

ADMINS = getaddresses([env('DJANGO_ADMINS', default='')])
MANAGERS = ADMINS

# ---------------------------------------------------------------------------
# Static and media files
# ---------------------------------------------------------------------------

STATIC_URL = env('STATIC_URL', default='/static/')
STATIC_ROOT = env.path('STATIC_ROOT', default=str(BASE_DIR / 'staticfiles'))()
MEDIA_URL = env('MEDIA_URL', default='/media/')
MEDIA_ROOT = env.path('MEDIA_ROOT', default=str(BASE_DIR / 'media'))()

# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------

SESSION_COOKIE_AGE = env('SESSION_COOKIE_AGE')

if not DEBUG:
    SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=31536000)  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_SSL_REDIRECT = env.bool('USE_SSL', default=True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    X_FRAME_OPTIONS = 'DENY'

# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------

LANGUAGE_CODE = env('LANGUAGE_CODE', default='en-us')
TIME_ZONE = env('TIME_ZONE', default='UTC')
USE_I18N = True
USE_TZ = True
```

**Corresponding `.env` file for the above:**

```bash
# .env (development)
DEBUG=on
SECRET_KEY=dev-only-insecure-key-replace-for-production
DATABASE_URL=psql://myuser:mypassword@127.0.0.1:5432/mydb
CACHE_URL=redis://127.0.0.1:6379/0
EMAIL_URL=consolemail://
ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_ADMINS=Alice <alice@example.com>
STATIC_URL=/static/
MEDIA_URL=/media/
TIME_ZONE=America/New_York
```

---

## 14. Using django-environ with Split Settings

django-environ pairs naturally with django-split-settings (covered in its own guide). The typical pattern is to initialize the `env` object in a `base.py` settings file and import it in environment-specific files.

```python
# config/settings/base.py
import environ
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env('SECRET_KEY')
INSTALLED_APPS = [...]
DATABASES = {'default': env.db()}
# ... all shared settings
```

```python
# config/settings/local.py
from .base import *  # noqa

DEBUG = True
INSTALLED_APPS += ['debug_toolbar']
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

```python
# config/settings/production.py
from .base import *  # noqa

DEBUG = False
SECURE_SSL_REDIRECT = True
```

---

## 15. Common Pitfalls & Troubleshooting

**Problem: `ImproperlyConfigured: Set the SECRET_KEY environment variable`**

This means the variable is not in your OS environment and not in your `.env` file (or `read_env()` was called before `environ.Env.read_env()`).

Fix: Ensure `.env` exists in the directory you pass to `read_env()`. Print `os.path.join(BASE_DIR, '.env')` to verify the path is correct. Check the file actually contains the variable.

---

**Problem: Boolean environment variables aren't being cast — `DEBUG` stays as the string `'on'`**

Cause: You are calling `env('DEBUG')` without declaring a type, and smart casting is off or no default was declared.

Fix: Use the explicit typed reader: `env.bool('DEBUG', default=False)`. Or declare it in the constructor: `env = environ.Env(DEBUG=(bool, False))` and call `env('DEBUG')`.

---

**Problem: Database password with special characters causes a URL parse error**

Cause: Characters like `@`, `#`, `:`, `/` have special meaning in URLs and break the parser when they appear in the password segment unencoded.

Fix: URL-encode the password before putting it in the `.env` file.

```python
from urllib.parse import quote
print(quote("p@ss#word"))
# Output: p%40ss%23word
```

Then in `.env`: `DATABASE_URL=psql://user:p%40ss%23word@host:5432/db`

---

**Problem: Inline comments in `.env` are being included in the value**

Cause: By default, django-environ does not strip inline comments.

Fix: Pass `parse_comments=True` to `read_env()`:

```python
environ.Env.read_env(os.path.join(BASE_DIR, '.env'), parse_comments=True)
```

---

**Problem: `.env` values are not overriding real environment variables**

Cause: `read_env()` uses `setdefault()` by default, meaning real OS environment variables win.

Fix: This is intentional and correct behavior. If you genuinely need `.env` to override real environment variables (unusual), pass `overwrite=True` to `read_env()`.

---

**Problem: `BASE_DIR` is pointing to the wrong directory after converting to a settings package**

Cause: When `settings.py` becomes `settings/__init__.py` or `settings/base.py`, `Path(__file__)` now points inside the settings directory.

Fix: Add one more `.parent` to walk up the extra level:

```python
# Was: BASE_DIR = Path(__file__).resolve().parent.parent
# Now (settings is a package one level deeper):
BASE_DIR = Path(__file__).resolve().parent.parent.parent
```

---

**Problem: `read_env()` silently does nothing — no variables are being set**

Cause: `read_env()` does not raise an error if the file doesn't exist. It silently returns.

Fix: Check that the file path is correct by printing it during startup, or explicitly verify the file exists:

```python
env_file = os.path.join(BASE_DIR, '.env')
if not os.path.exists(env_file):
    print(f"WARNING: .env file not found at {env_file}")
environ.Env.read_env(env_file)
```

---

## 16. Checklist

Use this every time you add or configure django-environ in a project.

### Initial Setup

- [ ] `.env` is listed in `.gitignore`
- [ ] `.env.example` exists with all keys and placeholder values, and IS committed
- [ ] `environ.Env.read_env()` is called before any `env(...)` calls in `settings.py`
- [ ] The path passed to `read_env()` is correct (verify `BASE_DIR` points to the project root)
- [ ] No secrets are hardcoded anywhere in `settings.py`

### Variable Declarations

- [ ] All required variables (no defaults) are intentionally left without defaults — they will raise `ImproperlyConfigured` if missing
- [ ] Optional variables have sensible defaults
- [ ] `DEBUG` defaults to `False` so missing it in production is safe
- [ ] Smart casting is disabled (`env.smart_cast = False`) if you prefer explicit types
- [ ] All boolean variables use `env.bool()` or declare `(bool, default)` in the constructor

### URL Parsers

- [ ] `DATABASE_URL` is used for databases, not individual `DB_NAME`, `DB_USER`, etc. settings
- [ ] `CACHE_URL` is used for caches
- [ ] `EMAIL_URL` is used for email configuration
- [ ] Passwords in URL strings are URL-encoded if they contain special characters
- [ ] `env.db()` result is assigned to `DATABASES['default']`
- [ ] `env.email()` result is injected with `vars().update()`

### Docker / Kubernetes

- [ ] `FileAwareEnv` is used instead of `Env` in containerized environments
- [ ] Secrets are mounted as files and referenced via `*_FILE` environment variables
- [ ] The `.env` file is NOT baked into the Docker image

### Environment-Specific

- [ ] Development `.env` uses `DEBUG=on` and `consolemail://` for email
- [ ] Production deployment does not use a `.env` file — secrets are injected via the environment
- [ ] Production `SECRET_KEY` is at least 50 characters of random data
- [ ] `ALLOWED_HOSTS` contains real hostnames in production

---

*Official documentation: https://django-environ.readthedocs.io/ — always check for the latest options as the library releases regularly.*