# Redis in Django — Definitive Guide

> Redis is an in-memory data structure store. In a Django project it serves as the Celery broker, the cache layer, the session store, the rate limiter, the pub/sub layer for WebSockets, and the distributed lock manager. This guide covers every use case with full detail — no assumptions, no gaps.

---

## Table of Contents

1. [What Redis Is and How It Works](#architecture)
2. [Installation](#installation)
3. [Redis DB Allocation Convention](#db-allocation)
4. [Connection Setup](#connection)
5. [Caching — Full Reference](#caching)
6. [Caching Patterns](#patterns)
7. [Cache Invalidation](#invalidation)
8. [Sessions](#sessions)
9. [Rate Limiting](#rate-limiting)
10. [Distributed Locks](#locks)
11. [Pub/Sub — Django Channels](#pubsub)
12. [Raw Redis Data Structures](#data-structures)
13. [Key Naming Convention](#key-naming)
14. [Health Check](#health)
15. [Production Configuration](#production)
16. [Common Errors & Fixes](#errors)
17. [Quick Reference](#reference)

---

## 1. What Redis Is and How It Works {#architecture}

Redis stores data in memory. This makes reads and writes orders of magnitude faster than PostgreSQL. It is not a replacement for your relational database — it is a complement for data that needs to be accessed very frequently, data that is temporary (TTLs), or data that needs fast atomic operations.

**Redis serves multiple roles in a Django project:**

| Role | What It Does | Redis DB |
|---|---|---|
| **Celery Broker** | Stores queued tasks until workers consume them | DB 0 |
| **Django Cache** | Stores cached query results, computed values | DB 1 |
| **Session Store** | Stores user session data | DB 2 (or combined with cache) |
| **Rate Limiter** | Atomic counters with TTL for per-user limits | DB 3 |
| **Channels Layer** | WebSocket group messaging pub/sub | DB 4 |

**How data is stored:** Key-value pairs where keys are strings and values can be strings, lists, sets, sorted sets, hashes, or bitmaps. Every key can have a TTL (expiry time) after which Redis deletes it automatically.

**Key property: atomic operations.** Redis is single-threaded internally. This means operations like `INCR` (increment a counter) are guaranteed to be atomic — no race condition is possible even with thousands of concurrent requests hitting the same key.

---

## 2. Installation {#installation}

```bash
pip install redis django-redis
```

| Package | Min Version | Purpose |
|---|---|---|
| `redis` | `4.0+` | Python client for communicating with Redis server |
| `django-redis` | `5.0+` | Django cache backend that uses the redis package under the hood; adds Django-specific features like `delete_pattern` and raw client access |

**Install and start Redis server:**

```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Docker (for local development)
docker run -d --name redis -p 6379:6379 redis:7-alpine

# Verify Redis is running
redis-cli ping   # should return: PONG
```

---

## 3. Redis DB Allocation Convention {#db-allocation}

Redis ships with 16 logical databases (0–15) on a single server instance. They share the same memory but their keys are completely isolated. Never mix unrelated data in the same DB — eviction policies and flush commands are DB-wide.

| DB Index | Purpose | Who Writes | Who Reads |
|---|---|---|---|
| `0` | Celery broker (task queue) | Django producers | Celery workers |
| `1` | Django cache | Django cache API | Django cache API |
| `2` | Django sessions | Session middleware | Session middleware |
| `3` | Rate limiting counters | Custom middleware/views | Custom middleware/views |
| `4` | Django Channels layer (WebSockets) | Channels consumers | Channels consumers |
| `5+` | Reserved / custom use | — | — |

---

## 4. Connection Setup {#connection}

### `settings/base.py`

```python
# ─────────────────────────────────────────────────────────────────
# REDIS — base connection string
# ─────────────────────────────────────────────────────────────────

# Local development
REDIS_HOST = "localhost"
REDIS_PORT = 6379

# Production with auth
# REDIS_URL = "redis://:your_password@your-redis-host:6379"

# Production with TLS (note: rediss:// with double s)
# REDIS_URL = "rediss://:your_password@your-redis-host:6380"

# ─────────────────────────────────────────────────────────────────
# DJANGO CACHE — uses Redis DB 1
# ─────────────────────────────────────────────────────────────────

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",

        # DB 1 for cache — separate from Celery broker (DB 0)
        "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}/1",

        "OPTIONS": {
            # django-redis client class
            "CLIENT_CLASS": "django_redis.client.DefaultClient",

            # How many seconds to wait for a connection to be established.
            # After this, a ConnectionError is raised.
            "SOCKET_CONNECT_TIMEOUT": 5,

            # How many seconds to wait for a response from Redis.
            "SOCKET_TIMEOUT": 5,

            # If a Redis operation times out, retry it once automatically.
            "RETRY_ON_TIMEOUT": True,

            # Maximum number of connections in the connection pool.
            # Each Django worker process has its own pool.
            # For gunicorn with 4 workers: each worker uses up to 1000 connections.
            "MAX_CONNECTIONS": 1000,

            # Compress values larger than this threshold (bytes) using zlib.
            # Reduces Redis memory usage at the cost of slightly more CPU.
            # Recommended for large cached objects (>1KB).
            "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",

            # Optional: ignore Redis exceptions instead of crashing.
            # With this, cache misses are returned instead of errors.
            # Use with caution — it can mask Redis outages.
            # "IGNORE_EXCEPTIONS": True,
        },

        # All cache keys for this project are prefixed with this string.
        # Prevents key collisions if multiple projects share the same Redis instance.
        "KEY_PREFIX": "careerly",

        # Default TTL in seconds for all cache.set() calls that don't specify timeout.
        # 300 = 5 minutes.
        "TIMEOUT": 300,
    }
}

# ─────────────────────────────────────────────────────────────────
# DJANGO SESSIONS — stored in Redis (DB 2 or combined with cache)
# ─────────────────────────────────────────────────────────────────

# Store sessions in the cache backend (Redis DB 1 in our config)
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# How long a session lasts (seconds)
SESSION_COOKIE_AGE = 86400 * 30       # 30 days

# Only save session if data changed — reduces write overhead
SESSION_SAVE_EVERY_REQUEST = False

# ─────────────────────────────────────────────────────────────────
# CELERY BROKER — Redis DB 0 (defined here for reference)
# ─────────────────────────────────────────────────────────────────

CELERY_BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

# ─────────────────────────────────────────────────────────────────
# CHANNELS LAYER — Redis DB 4 for WebSockets
# ─────────────────────────────────────────────────────────────────

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(REDIS_HOST, REDIS_PORT)],
            "prefix": "careerly:channels",  # namespace for channel keys
            "capacity": 1500,               # max queued messages per channel
            "expiry": 10,                   # seconds before unread messages expire
        },
    },
}
```

---

## 5. Caching — Full Reference {#caching}

### Import

```python
from django.core.cache import cache
```

The `cache` object is a thread-safe interface to the configured Redis backend. All operations go through this — never instantiate a Redis client directly for caching.

### Basic Operations

```python
# ─── SET ────────────────────────────────────────────────────────

# Store a value with a TTL of 600 seconds (10 minutes).
# If timeout=None, the key never expires — use with extreme caution.
# If timeout=0, the key is deleted immediately (same as not setting it).
cache.set("user:42:profile", profile_data, timeout=600)

# ─── GET ────────────────────────────────────────────────────────

# Retrieve a value. Returns None if the key doesn't exist or has expired.
data = cache.get("user:42:profile")

if data is None:
    # Cache miss — fetch from DB and repopulate
    data = UserProfile.objects.get(user_id=42)
    cache.set("user:42:profile", data, timeout=600)

# Retrieve with a default value instead of None on miss
data = cache.get("user:42:profile", default={})

# ─── DELETE ─────────────────────────────────────────────────────

cache.delete("user:42:profile")

# ─── ADD ────────────────────────────────────────────────────────

# Set a value ONLY if the key does NOT already exist. Atomic operation.
# Returns True if set, False if key already existed.
# Useful for distributed locks or "first write wins" scenarios.
was_set = cache.add("lock:job:99", True, timeout=30)

# ─── GET OR SET ─────────────────────────────────────────────────

# Atomic: get the value, or set it if it doesn't exist, in one operation.
# Accepts a callable for lazy evaluation — the DB query only runs on cache miss.
data = cache.get_or_set(
    "featured_jobs",
    lambda: list(Job.objects.filter(featured=True).values()),
    timeout=600,
)

# ─── INCR / DECR ────────────────────────────────────────────────

# Atomically increment a counter. Creates the key with value 1 if it doesn't exist.
# Returns the new value.
cache.set("views:job:42", 0, timeout=86400)
new_count = cache.incr("views:job:42")        # returns 1
new_count = cache.incr("views:job:42", 5)     # increment by 5, returns 6
cache.decr("views:job:42")                    # decrement by 1

# ─── HAS KEY ────────────────────────────────────────────────────

if cache.has_key("user:42:profile"):
    # Key exists and hasn't expired
    pass

# ─── BULK OPERATIONS ────────────────────────────────────────────

# Set multiple keys in a single Redis round-trip
cache.set_many({
    "user:42:profile": profile_data,
    "user:42:jobs":    jobs_data,
    "user:42:alerts":  alerts_data,
}, timeout=300)

# Get multiple keys in a single Redis round-trip
# Returns a dict with only the keys that existed
values = cache.get_many(["user:42:profile", "user:42:jobs", "user:42:alerts"])
# values = {"user:42:profile": ..., "user:42:jobs": ...}  (missing keys omitted)

# Delete multiple keys in a single call
cache.delete_many(["user:42:profile", "user:42:jobs"])

# ─── CLEAR ──────────────────────────────────────────────────────

# Delete ALL keys in the cache.
# Never call this in production unless you know exactly what you're doing.
# It clears the entire Redis DB, including session data if using the same backend.
cache.clear()

# ─── DELETE BY PATTERN (django-redis only) ──────────────────────

# Delete all keys matching a wildcard pattern.
# More surgical than cache.clear() — affects only the matched keys.
# Uses Redis SCAN internally — safe to use on large datasets.
cache.delete_pattern("user:42:*")         # all keys for user 42
cache.delete_pattern("jobs:featured:*")   # all featured job variants
```

### Versioning

```python
# Set a versioned key — useful when the shape of cached data changes
cache.set("jobs_list", data, version=2)
cache.get("jobs_list", version=2)          # returns data
cache.get("jobs_list", version=1)          # returns None — different version

# Bump version — all reads of the old version become cache misses
cache.incr_version("jobs_list")            # version 2 → 3

# Explicitly delete a specific version
cache.delete("jobs_list", version=2)
```

---

## 6. Caching Patterns {#patterns}

### Pattern 1: Cache-Aside (Most Common)

The application checks the cache first. On miss, fetches from DB and populates cache.

```python
# services/jobs.py
from django.core.cache import cache
from apps.jobs.models import Job

def get_job(job_id: int) -> dict:
    cache_key = f"job:{job_id}:detail"

    # 1. Try cache
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    # 2. Cache miss — fetch from DB
    try:
        job = Job.objects.select_related("employer", "category").get(id=job_id)
    except Job.DoesNotExist:
        return None

    # Serialize to a dict for safe JSON storage in Redis
    data = {
        "id": job.id,
        "title": job.title,
        "employer": {"id": job.employer.id, "name": job.employer.name},
        "location": job.location,
        "salary_min": str(job.salary_min),  # Decimal → str to avoid JSON issues
        "salary_max": str(job.salary_max),
        "posted_at": job.posted_at.isoformat(),
    }

    # 3. Populate cache with 10-minute TTL
    cache.set(cache_key, data, timeout=600)
    return data
```

**Why serialize to dict:** Django model instances are not JSON-serializable. If `django-redis` tries to serialize a model instance to Redis, it will use pickle (a security risk) or fail. Always convert to primitive types before caching.

### Pattern 2: `get_or_set` — Shorthand for Cache-Aside

```python
def get_featured_jobs() -> list:
    return cache.get_or_set(
        key="jobs:featured",
        default=lambda: list(
            Job.objects.filter(featured=True, status="ACTIVE")
            .values("id", "title", "employer__name", "location")
            .order_by("-featured_at")[:20]
        ),
        timeout=600,
    )
```

The lambda is only evaluated on a cache miss — the DB query only runs when the cache is empty or expired.

### Pattern 3: View-Level Caching

```python
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator

# Cache the entire HTTP response for 15 minutes
# For function-based views:
@cache_page(60 * 15)
def job_list_view(request):
    ...

# For class-based views — decorate dispatch to cache all HTTP methods:
@method_decorator(cache_page(60 * 15), name="dispatch")
class JobListView(ListView):
    ...

# For class-based views — only cache GET requests:
@method_decorator(cache_page(60 * 15), name="get")
class JobListView(ListView):
    ...
```

**Limitation:** `cache_page` uses the full URL (including query params) as the cache key. Two users hitting `/jobs/?page=1` share the same cached response. This means user-specific data (personalized results, auth-dependent content) must NOT use `cache_page`. Use low-level `cache.get/set` instead for per-user caching.

### Pattern 4: Vary-By-User Caching

```python
def get_user_feed(user_id: int, page: int) -> list:
    cache_key = f"feed:user:{user_id}:page:{page}"
    cached = cache.get(cache_key)

    if cached is not None:
        return cached

    feed = compute_personalized_feed(user_id=user_id, page=page)
    cache.set(cache_key, feed, timeout=120)  # 2 min TTL — feeds change often
    return feed
```

### Pattern 5: Raw Redis Client

```python
from django_redis import get_redis_connection

# Get the underlying redis-py client
# "default" refers to the cache alias in CACHES dict
redis = get_redis_connection("default")

# Use Redis data structures not exposed by Django's cache API
# Example: maintain a list of recent searches
def add_recent_search(user_id: int, query: str):
    key = f"careerly:recent_searches:{user_id}"
    redis.lpush(key, query)        # add to front of list
    redis.ltrim(key, 0, 9)         # keep only last 10 items
    redis.expire(key, 86400 * 7)   # expire after 7 days

def get_recent_searches(user_id: int) -> list:
    key = f"careerly:recent_searches:{user_id}"
    return [s.decode("utf-8") for s in redis.lrange(key, 0, -1)]
```

---

## 7. Cache Invalidation {#invalidation}

Cache invalidation is the process of deleting or updating cached data when the source data changes. There are two strategies:

### Strategy 1: Invalidate on Save (Django Signals)

```python
# apps/jobs/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Job

@receiver(post_save, sender=Job)
def invalidate_job_cache(sender, instance, **kwargs):
    # Delete the specific job's detail cache
    cache.delete(f"job:{instance.id}:detail")

    # Delete list caches that might contain this job
    cache.delete_pattern("jobs:featured:*")
    cache.delete_pattern("jobs:list:*")
    cache.delete_pattern(f"employer:{instance.employer_id}:jobs:*")

@receiver(post_delete, sender=Job)
def invalidate_job_cache_on_delete(sender, instance, **kwargs):
    cache.delete(f"job:{instance.id}:detail")
    cache.delete_pattern("jobs:featured:*")
    cache.delete_pattern("jobs:list:*")
```

### Strategy 2: Short TTL + Natural Expiry

For data that can tolerate slight staleness (e.g. job count stats, leaderboards), set a short TTL and let the cache expire naturally. No explicit invalidation needed.

```python
# This data is at most 60 seconds stale — acceptable for a counter
cache.set("stats:total_jobs", total, timeout=60)
```

### Strategy 3: Cache Versioning for Bulk Invalidation

When many keys need to be invalidated at once (e.g. all caches for a user), use versioning instead of pattern deletion.

```python
def get_user_cache_version(user_id: int) -> int:
    return cache.get(f"version:user:{user_id}", default=1)

def invalidate_all_user_caches(user_id: int):
    # Bump the version — all old caches become stale misses
    cache.incr(f"version:user:{user_id}")

def get_user_profile(user_id: int) -> dict:
    version = get_user_cache_version(user_id)
    return cache.get_or_set(
        key=f"profile:user:{user_id}",
        default=lambda: fetch_from_db(user_id),
        timeout=600,
        version=version,
    )
```

---

## 8. Sessions {#sessions}

### Configuration

```python
# settings/base.py

# Store sessions in the Django cache backend (Redis DB 1 in our setup)
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"   # refers to the "default" entry in CACHES

# Cookie lifetime — how long the browser keeps the session cookie
SESSION_COOKIE_AGE = 86400 * 30   # 30 days

# Cookie security settings
SESSION_COOKIE_SECURE = True       # only send over HTTPS (required in production)
SESSION_COOKIE_HTTPONLY = True     # prevent JavaScript access to cookie
SESSION_COOKIE_SAMESITE = "Lax"   # CSRF protection

# Only write session to Redis if data changed — reduces write overhead
SESSION_SAVE_EVERY_REQUEST = False
```

### Usage in Views

The session API is identical to file-based or DB-backed sessions — Redis is transparent.

```python
# Set session data
def login_view(request):
    user = authenticate(request, ...)
    request.session["user_id"] = user.id
    request.session["user_role"] = user.role
    request.session["last_login"] = timezone.now().isoformat()

# Read session data
def profile_view(request):
    role = request.session.get("user_role", "job_seeker")
    user_id = request.session.get("user_id")

# Delete a specific session key
def update_role(request):
    del request.session["user_role"]

# Flush the entire session (logout)
def logout_view(request):
    request.session.flush()   # deletes the session from Redis and clears the cookie

# Regenerate session key (security: call after privilege escalation)
def login_view(request):
    ...
    request.session.cycle_key()   # new key, same data — prevents session fixation
```

### Session TTL

Session keys in Redis have TTL = `SESSION_COOKIE_AGE`. When a user is active and `SESSION_SAVE_EVERY_REQUEST = True`, the TTL is refreshed on every request. With `False` (default), the TTL is only refreshed when session data changes.

---

## 9. Rate Limiting {#rate-limiting}

### How Redis Rate Limiting Works

Redis `INCR` is atomic. The pattern is:
1. `INCR rate_limit:{identifier}` → get the new count
2. If count == 1, set `EXPIRE rate_limit:{identifier} {window_seconds}` → start the window
3. If count > limit → reject the request

Because step 1 is atomic, two simultaneous requests can never both see count == 0.

### Custom Middleware Implementation

```python
# apps/core/rate_limiting.py
from django_redis import get_redis_connection
from django.http import JsonResponse

def check_rate_limit(identifier: str, limit: int, window_seconds: int) -> tuple[bool, int]:
    """
    Returns (allowed: bool, current_count: int).
    allowed = True if the request is within the rate limit.
    allowed = False if the limit has been exceeded.
    """
    redis = get_redis_connection("default")
    key = f"careerly:rate_limit:{identifier}"

    # Atomic pipeline: INCR then EXPIRE in a single round-trip
    pipe = redis.pipeline(transaction=True)
    pipe.incr(key)
    pipe.ttl(key)
    count, ttl = pipe.execute()

    if ttl == -1:
        # Key exists but has no expiry (edge case: INCR succeeded but EXPIRE failed)
        # Set the expiry now
        redis.expire(key, window_seconds)
    elif count == 1:
        # First request in this window — set the window expiry
        redis.expire(key, window_seconds)

    allowed = count <= limit
    return allowed, count


class RateLimitMiddleware:
    """
    Apply per-user rate limiting to API endpoints.
    Unauthenticated requests are limited by IP address.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/api/"):
            if request.user.is_authenticated:
                identifier = f"user:{request.user.id}"
                limit = 1000
            else:
                identifier = f"ip:{self.get_client_ip(request)}"
                limit = 100

            allowed, count = check_rate_limit(
                identifier=identifier,
                limit=limit,
                window_seconds=3600,  # 1 hour window
            )

            if not allowed:
                return JsonResponse(
                    {"error": "Rate limit exceeded. Try again later."},
                    status=429,
                    headers={"Retry-After": "3600"},
                )

        return self.get_response(request)

    def get_client_ip(self, request) -> str:
        # Handle proxied requests (nginx, load balancers)
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")
```

### Per-Endpoint Rate Limiting (Decorator)

```python
# apps/core/decorators.py
import functools
from django.http import JsonResponse
from .rate_limiting import check_rate_limit

def rate_limit(limit: int, window_seconds: int, key_prefix: str = "endpoint"):
    """
    Decorator for per-endpoint rate limiting.
    Usage: @rate_limit(limit=10, window_seconds=3600)
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated:
                identifier = f"{key_prefix}:{request.user.id}"
            else:
                identifier = f"{key_prefix}:ip:{request.META.get('REMOTE_ADDR')}"

            allowed, count = check_rate_limit(identifier, limit, window_seconds)
            if not allowed:
                return JsonResponse({"error": "Too many requests"}, status=429)

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

# Usage:
from apps.core.decorators import rate_limit

@rate_limit(limit=5, window_seconds=3600, key_prefix="job_apply")
def apply_for_job(request, job_id):
    ...
```

### Using `django-ratelimit` Package

```bash
pip install django-ratelimit
```

```python
from ratelimit.decorators import ratelimit

# rate="5/h" = 5 requests per hour per user
# key="user" = rate-limit key is the authenticated user
# method="POST" = only apply to POST requests
# block=True = return 403 instead of letting the view decide
@ratelimit(key="user", rate="5/h", method="POST", block=True)
def apply_for_job(request, job_id):
    ...

# For class-based views:
from ratelimit.mixins import RatelimitMixin

class ApplyForJobView(RatelimitMixin, CreateAPIView):
    ratelimit_key = "user"
    ratelimit_rate = "5/h"
    ratelimit_method = "POST"
    ratelimit_block = True
```

---

## 10. Distributed Locks {#locks}

### Why You Need Distributed Locks

In a multi-worker environment (multiple gunicorn processes, multiple Celery workers, multiple pods in Kubernetes), two workers can attempt to process the same resource simultaneously. Distributed locks prevent this.

### Implementation

```python
# apps/core/locks.py
import uuid
import time
from contextlib import contextmanager
from django_redis import get_redis_connection
from django.core.exceptions import ValidationError

class RedisLock:
    """
    A distributed lock backed by Redis.
    Uses SET NX EX — atomic set-if-not-exists with expiry.
    """
    def __init__(self, lock_name: str, timeout: int = 30):
        """
        lock_name: unique name for the lock (e.g. "payout:17")
        timeout: seconds before the lock automatically expires (prevents deadlocks)
        """
        self.redis = get_redis_connection("default")
        self.key = f"careerly:lock:{lock_name}"
        self.timeout = timeout
        self.token = str(uuid.uuid4())  # unique token per lock instance

    def acquire(self, blocking: bool = True, retry_interval: float = 0.1) -> bool:
        """
        Try to acquire the lock.
        blocking=True: keep retrying until the lock is acquired or timeout expires.
        blocking=False: return immediately.
        Returns True if lock was acquired, False otherwise.
        """
        deadline = time.time() + self.timeout

        while True:
            # SET key token NX EX timeout
            # NX = only set if key does NOT exist (atomic)
            # EX = set expiry in seconds
            acquired = self.redis.set(
                self.key,
                self.token,
                nx=True,
                ex=self.timeout,
            )
            if acquired:
                return True
            if not blocking or time.time() >= deadline:
                return False
            time.sleep(retry_interval)

    def release(self):
        """
        Release the lock — only if it's still ours (not expired and re-acquired by someone else).
        Uses a Lua script for atomic check-and-delete.
        """
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        self.redis.eval(lua_script, 1, self.key, self.token)


@contextmanager
def distributed_lock(lock_name: str, timeout: int = 30, blocking: bool = True):
    """
    Context manager for distributed locking.

    Usage:
        with distributed_lock("process_payout:17"):
            # only one worker runs this at a time
            process_payout(17)

    Raises RuntimeError if blocking=False and lock cannot be acquired.
    """
    lock = RedisLock(lock_name=lock_name, timeout=timeout)
    acquired = lock.acquire(blocking=blocking)

    if not acquired:
        raise RuntimeError(f"Could not acquire lock: {lock_name}")

    try:
        yield lock
    finally:
        lock.release()
```

### Usage in Celery Tasks

```python
# apps/payments/tasks.py
from celery import shared_task
from apps.core.locks import distributed_lock

@shared_task(bind=True, max_retries=3)
def process_payout(self, payout_id: int):
    from apps.payments.models import Payout

    # Ensure only one worker processes this payout at a time
    try:
        with distributed_lock(f"payout:{payout_id}", timeout=60, blocking=False):
            payout = Payout.objects.get(id=payout_id)
            if payout.status != "PENDING":
                return f"skipped:already_processed:{payout_id}"

            # do payment processing
            payout.status = "COMPLETE"
            payout.save(update_fields=["status", "updated_at"])
            return f"complete:{payout_id}"

    except RuntimeError:
        # Lock was held by another worker — retry after 10 seconds
        raise self.retry(countdown=10)
```

---

## 11. Pub/Sub — Django Channels {#pubsub}

Django Channels adds WebSocket support to Django. Redis acts as the channel layer — the message bus between channel consumers running in different processes.

### Installation

```bash
pip install channels channels-redis
```

### Settings

```python
# settings/base.py
INSTALLED_APPS = [
    ...
    "channels",
]

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("localhost", 6379)],
            "prefix": "careerly:channels",
            "capacity": 1500,    # max messages queued per channel group
            "expiry": 10,        # seconds before unread messages expire
        },
    },
}

# ASGI — required for Channels
ASGI_APPLICATION = "myproject.asgi.application"
```

### ASGI Configuration

```python
# myproject/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from apps.notifications.routing import websocket_urlpatterns

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings.base")

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
```

### WebSocket Consumer

```python
# apps/notifications/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if not user.is_authenticated:
            await self.close()
            return

        # Join a group named after the user ID
        # All messages sent to "user_{id}" group are delivered to this consumer
        self.group_name = f"user_{user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # This method is called when the group receives a "notification.new" type message
    async def notification_new(self, event):
        await self.send(text_data=json.dumps({
            "type": "notification",
            "data": event["data"],
        }))
```

### Sending Messages from Django Code (e.g. Celery Task)

```python
# apps/notifications/services.py
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def send_realtime_notification(user_id: int, notification_data: dict):
    """
    Push a notification to a connected WebSocket client.
    Can be called from anywhere: views, Celery tasks, signals.
    """
    channel_layer = get_channel_layer()

    # async_to_sync wraps the async group_send so it can be called from sync code
    async_to_sync(channel_layer.group_send)(
        f"user_{user_id}",           # group name
        {
            "type": "notification.new",    # maps to notification_new() method on consumer
            "data": notification_data,
        }
    )
```

### Routing

```python
# apps/notifications/routing.py
from django.urls import re_path
from .consumers import NotificationConsumer

websocket_urlpatterns = [
    re_path(r"ws/notifications/$", NotificationConsumer.as_asgi()),
]
```

---

## 12. Raw Redis Data Structures {#data-structures}

Access Redis data structures directly via the raw client for use cases beyond simple key-value caching.

```python
from django_redis import get_redis_connection
redis = get_redis_connection("default")
```

### Lists — Ordered, Allows Duplicates

```python
# Recent activity feed (newest first)
key = "careerly:activity:user:42"
redis.lpush(key, json.dumps({"action": "applied", "job_id": 10}))   # add to front
redis.ltrim(key, 0, 49)           # keep only last 50 items
redis.expire(key, 86400 * 30)     # expire after 30 days

items = redis.lrange(key, 0, -1)  # get all items
items = redis.lrange(key, 0, 9)   # get latest 10 items
count = redis.llen(key)           # count items
```

### Sets — Unordered, No Duplicates

```python
# Track which users viewed a job posting
key = "careerly:viewers:job:99"
redis.sadd(key, user_id)          # add user to set (no-op if already present)
redis.expire(key, 86400 * 7)

count = redis.scard(key)          # count unique viewers
is_viewed = redis.sismember(key, user_id)  # check if user already viewed
all_viewers = redis.smembers(key)          # get all viewer IDs
```

### Sorted Sets — Ordered by Score

```python
# Employer leaderboard ordered by number of applications received
key = "careerly:leaderboard:employers"
redis.zadd(key, {"acme_corp": 95.5, "techco": 88.0})
redis.zincrby(key, 1.0, "acme_corp")                    # add 1 to score

top_10 = redis.zrevrange(key, 0, 9, withscores=True)    # top 10 highest scores
# Returns: [("acme_corp", 96.5), ("techco", 88.0), ...]

bottom_10 = redis.zrange(key, 0, 9, withscores=True)    # bottom 10
rank = redis.zrevrank(key, "acme_corp")                  # 0-indexed rank (0 = #1)
```

### HyperLogLog — Approximate Unique Count

HyperLogLog uses ~12KB of memory to count up to billions of unique items with ~0.81% error margin. Perfect for analytics where approximate counts are acceptable.

```python
# Count unique job viewers without storing every user ID
key = "careerly:unique_views:job:99"
redis.pfadd(key, user_id)            # add a user — no duplicates tracked
redis.expire(key, 86400 * 30)

approx_count = redis.pfcount(key)    # estimated unique viewers
# Merge multiple HyperLogLogs:
redis.pfmerge("careerly:total_unique_views", "careerly:unique_views:job:99", "careerly:unique_views:job:100")
```

### Hashes — Field-Value Maps

```python
# Store multiple attributes for an entity without separate cache keys
key = "careerly:employer:42"
redis.hset(key, mapping={
    "name": "Acme Corp",
    "plan": "premium",
    "active_jobs": "5",
})
redis.expire(key, 3600)

name = redis.hget(key, "name").decode()         # get one field
all_data = redis.hgetall(key)                   # get all fields as dict
redis.hincrby(key, "active_jobs", 1)            # atomic increment on a hash field
redis.hdel(key, "plan")                         # delete a field
```

---

## 13. Key Naming Convention {#key-naming}

All Redis keys must follow a consistent naming convention to:
- Avoid collisions between apps and environments
- Enable pattern-based deletion (`delete_pattern`)
- Make debugging easier in Redis CLI

**Format:** `{project}:{entity}:{id}:{attribute}`

```
careerly:user:42:profile
careerly:user:42:feed:page:1
careerly:job:99:detail
careerly:job:99:applications:count
careerly:jobs:featured
careerly:jobs:list:page:3:sort:recent
careerly:employer:7:jobs:active
careerly:rate_limit:apply:user:42
careerly:rate_limit:ip:192.168.1.1
careerly:lock:payout:17
careerly:lock:resume_parse:88
careerly:leaderboard:employers
careerly:unique_views:job:99
careerly:activity:user:42
careerly:recent_searches:user:42
```

**Rules:**
- Always start with project prefix (`careerly:`) — enables safe `delete_pattern("careerly:*")` in scripts
- Use `:` as separator — never `/`, `-`, or spaces
- IDs go after the entity name
- Always lowercase
- Never store secrets, PII, or sensitive data as part of the key — keys are visible in Redis CLI and logs

---

## 14. Health Check {#health}

```python
# apps/core/health.py
from django.core.cache import cache
from django.http import JsonResponse

def redis_health_check(request):
    """
    Simple endpoint to verify Redis is reachable and responding.
    Returns 200 if healthy, 503 if Redis is down.
    """
    try:
        cache.set("health:ping", "pong", timeout=5)
        value = cache.get("health:ping")
        if value != "pong":
            raise ValueError("Redis returned unexpected value")
        return JsonResponse({"status": "ok", "redis": "connected"})
    except Exception as e:
        return JsonResponse(
            {"status": "error", "redis": "unreachable", "detail": str(e)},
            status=503
        )
```

```python
# urls.py
from apps.core.health import redis_health_check

urlpatterns = [
    path("health/redis/", redis_health_check),
]
```

---

## 15. Production Configuration {#production}

### Redis Server Configuration (`/etc/redis/redis.conf`)

```conf
# Maximum memory Redis can use.
# When this limit is reached, Redis applies the eviction policy.
maxmemory 2gb

# Eviction policy — what to do when memory is full.
# allkeys-lru: evict the least recently used key among all keys.
# Best choice for a pure cache.
maxmemory-policy allkeys-lru

# Enable persistence with Append-Only File.
# Every write is appended to the AOF file — allows full recovery on restart.
# Set to "yes" if cached data is important enough to survive restarts.
# Set to "no" if the cache is truly ephemeral (can be rebuilt from DB).
appendonly no

# Save snapshots to disk (RDB).
# "save 900 1" = save every 15 minutes if at least 1 key changed.
# Remove all save directives if Redis is cache-only and persistence is not needed.
save ""

# Require authentication
requirepass your_strong_password_here

# Bind to specific interface — never expose Redis to 0.0.0.0 in production
bind 127.0.0.1

# Disable dangerous commands
rename-command FLUSHALL ""
rename-command FLUSHDB ""
rename-command CONFIG ""
rename-command DEBUG ""
```

### Eviction Policy Reference

| Policy | Behavior | Use When |
|---|---|---|
| `noeviction` | Return error when memory is full — writes rejected | Never: this crashes your app |
| `allkeys-lru` | Evict least recently used across ALL keys | Cache-only Redis — recommended |
| `volatile-lru` | Evict LRU keys that have a TTL set | Mixed cache + persistent data |
| `allkeys-random` | Evict random keys | Not recommended |
| `volatile-ttl` | Evict keys with the shortest remaining TTL | Not recommended |

### Django Settings for Production

```python
# settings/production.py

REDIS_URL = env("REDIS_URL")  # e.g. redis://:password@redis-host:6379

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"{REDIS_URL}/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
            "RETRY_ON_TIMEOUT": True,
            "MAX_CONNECTIONS": 1000,
            "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
            "CONNECTION_POOL_KWARGS": {
                "max_connections": 100,
                "retry_on_timeout": True,
            },
        },
        "KEY_PREFIX": "careerly",
        "TIMEOUT": 300,
    }
}

CELERY_BROKER_URL = f"{REDIS_URL}/0"
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
```

### Security Checklist

- [ ] Redis is not exposed to the public internet (`bind 127.0.0.1` or private network only)
- [ ] `requirepass` is set with a strong password (32+ random characters)
- [ ] `FLUSHALL` and `FLUSHDB` commands are renamed or disabled
- [ ] TLS is used if Redis is on a different host (`rediss://`)
- [ ] Separate Redis DBs for broker (0), cache (1), sessions (2), rate limit (3)
- [ ] `maxmemory` and `maxmemory-policy` are configured
- [ ] `appendonly` is configured based on whether you need persistence

---

## 16. Common Errors & Fixes {#errors}

| Error | Root Cause | Fix |
|---|---|---|
| `ConnectionRefusedError: [Errno 111]` | Redis server is not running | Start Redis: `redis-server` or `sudo systemctl start redis` |
| `redis.exceptions.AuthenticationError` | Wrong or missing password | Set `requirepass` in redis.conf and update `REDIS_URL` with password |
| `django.core.cache.backends.base.CacheKeyWarning: Cache key contains characters...` | Key has spaces or special characters | Use only alphanumeric, `:`, `.`, `-` in keys; follow naming convention |
| `cache.delete_pattern(...)` raises `AttributeError` | Using `LocMemCache` or another backend that doesn't support `delete_pattern` | Switch to `django_redis.cache.RedisCache` backend |
| `redis.exceptions.ResponseError: OOM command not allowed` | Redis hit `maxmemory` with `noeviction` policy | Change eviction policy to `allkeys-lru` and increase `maxmemory` |
| Sessions lost on Redis restart | No persistence configured | Enable `appendonly yes` in redis.conf OR store sessions in Django DB |
| `channels.exceptions.ChannelFull` | WebSocket message queue is full | Increase `capacity` in `CHANNEL_LAYERS` config or process messages faster |
| Keys not expiring | Set with `timeout=None` | Always set a timeout; audit code for `cache.set` without `timeout=` |
| Cache returning stale data | Invalidation not set up | Add `post_save` signal to delete/update cache on model changes |

---

## 17. Quick Reference {#reference}

```bash
# Connect to CLI
redis-cli

# With password
redis-cli -a your_password

# Select DB
redis-cli -n 1

# Check server is alive
redis-cli ping       # returns PONG

# Monitor all commands in real time (dev only — high overhead)
redis-cli monitor

# Scan keys with pattern (use SCAN instead of KEYS in production)
redis-cli --scan --pattern "careerly:job:*"

# Get a value
redis-cli get careerly:job:42:detail

# Check TTL in seconds (-1 = no expiry, -2 = key doesn't exist)
redis-cli ttl careerly:job:42:detail

# Delete by pattern
redis-cli --scan --pattern "careerly:user:42:*" | xargs redis-cli del

# Memory info
redis-cli info memory

# All connected clients
redis-cli client list

# Flush a specific DB (careful — deletes ALL keys in that DB)
redis-cli -n 1 flushdb
```

```python
from django.core.cache import cache
from django_redis import get_redis_connection

# Basic get/set
cache.set("key", value, timeout=300)
value = cache.get("key")
value = cache.get("key", default="fallback")
cache.delete("key")
cache.delete_pattern("prefix:*")

# Atomic shorthand
value = cache.get_or_set("key", lambda: expensive_query(), timeout=300)
cache.add("key", value, timeout=30)  # only sets if not exists
cache.incr("counter")
cache.decr("counter")

# Bulk
cache.set_many({"k1": v1, "k2": v2}, timeout=300)
cache.get_many(["k1", "k2"])
cache.delete_many(["k1", "k2"])

# Raw client
redis = get_redis_connection("default")
redis.lpush("list_key", item)
redis.zadd("leaderboard", {"user": score})
redis.sadd("set_key", member)
redis.pfadd("hll_key", item)
```
