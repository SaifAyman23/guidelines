# django-prometheus — The Complete Guide

> A thorough, production-focused reference for instrumenting Django applications with Prometheus, understanding metric types, writing PromQL, building Grafana dashboards, and handling multi-process deployments correctly.

**Package:** `django-prometheus` (v2.4.1 as of this writing)
**GitHub:** https://github.com/django-commons/django-prometheus
**Underlying client:** `prometheus_client` (Python Prometheus client, installed automatically)

---

## Table of Contents

1. [The Big Picture — What Is Prometheus and How Does It Work](#1-the-big-picture--what-is-prometheus-and-how-does-it-work)
2. [Installation](#2-installation)
3. [Settings and Middleware](#3-settings-and-middleware)
4. [The /metrics Endpoint](#4-the-metrics-endpoint)
5. [What Metrics django-prometheus Gives You for Free](#5-what-metrics-django-prometheus-gives-you-for-free)
6. [Monitoring Your Database](#6-monitoring-your-database)
7. [Monitoring Your Cache](#7-monitoring-your-cache)
8. [Monitoring Your Models](#8-monitoring-your-models)
9. [The Four Prometheus Metric Types](#9-the-four-prometheus-metric-types)
10. [Writing Custom Metrics](#10-writing-custom-metrics)
11. [Labels — Dimensions on Your Metrics](#11-labels--dimensions-on-your-metrics)
12. [The Multi-Process Problem and How to Solve It](#12-the-multi-process-problem-and-how-to-solve-it)
13. [Securing the /metrics Endpoint](#13-securing-the-metrics-endpoint)
14. [Prometheus Server Configuration](#14-prometheus-server-configuration)
15. [PromQL — Querying Your Metrics](#15-promql--querying-your-metrics)
16. [Alerting Rules](#16-alerting-rules)
17. [Grafana Dashboard Setup](#17-grafana-dashboard-setup)
18. [Custom Middleware Labels](#18-custom-middleware-labels)
19. [Docker and Kubernetes Setup](#19-docker-and-kubernetes-setup)
20. [Naming Conventions and Best Practices](#20-naming-conventions-and-best-practices)
21. [Checklist](#21-checklist)

---

## 1. The Big Picture — What Is Prometheus and How Does It Work

Before touching any code, you need to understand the architecture, because it is fundamentally different from logging or traditional monitoring.

### The Pull Model

Most monitoring systems work by pushing data: your app sends metrics to a central server. Prometheus inverts this. Prometheus **pulls** — it periodically sends an HTTP GET request to a `/metrics` endpoint on your application, reads the current values of all metrics, and stores them in its time-series database.

```
Your Django app                Prometheus server               Grafana
┌──────────────┐               ┌────────────────┐             ┌──────────┐
│              │   GET /metrics│                │  PromQL     │          │
│  /metrics    │ <─────────────│   Scrapes every│ <──────────│Dashboard │
│  endpoint    │ ─────────────>│   15s by default│            │          │
│              │   metrics data│                │             └──────────┘
└──────────────┘               └────────────────┘
```

This means:
- Your app does not need to know where Prometheus is. It just exposes `/metrics`.
- Prometheus decides how often to scrape. The default is every 15 seconds.
- If Prometheus goes down, your app keeps running. When Prometheus comes back, it resumes scraping.
- You can have multiple Prometheus servers scraping the same app.

### What the /metrics Endpoint Returns

When Prometheus scrapes your app, it gets a plain-text response that looks like this:

```
# HELP django_http_requests_total_by_method_total Number of requests by method
# TYPE django_http_requests_total_by_method_total counter
django_http_requests_total_by_method_total{method="GET"} 4521.0
django_http_requests_total_by_method_total{method="POST"} 832.0

# HELP django_http_responses_total_by_status_total Responses by status code
# TYPE django_http_responses_total_by_status_total counter
django_http_responses_total_by_status_total{status="200"} 4200.0
django_http_responses_total_by_status_total{status="404"} 102.0
django_http_responses_total_by_status_total{status="500"} 21.0

# HELP django_db_execute_total Total number of DB execute calls
# TYPE django_db_execute_total counter
django_db_execute_total{alias="default",vendor="postgresql"} 89432.0
```

Each line is a metric name, a set of labels in `{}`, and a current value. The `# HELP` comment is the description. The `# TYPE` comment tells Prometheus what kind of metric it is.

### The Three-Layer Stack

A complete production monitoring setup has three layers:

```
Layer 1 — Instrumentation:  Your Django app exposing /metrics
Layer 2 — Collection:       Prometheus server scraping and storing metrics
Layer 3 — Visualization:    Grafana reading from Prometheus and displaying dashboards
```

`django-prometheus` only handles Layer 1. You still need to run Prometheus and Grafana separately. This guide covers all three layers.

---

## 2. Installation

```bash
pip install django-prometheus

# or with uv
uv add django-prometheus

# or with poetry
poetry add django-prometheus
```

This automatically installs `prometheus_client` (the official Python Prometheus client library) as a dependency. You will use both packages — `django_prometheus` for the Django-specific instrumentation, and `prometheus_client` directly for your own custom metrics.

---

## 3. Settings and Middleware

### INSTALLED_APPS

```python
# settings/base.py
INSTALLED_APPS = [
    ...
    "django_prometheus",
    ...
]
```

### Middleware — Position Matters

The two Prometheus middlewares must be the outermost pair in your middleware stack. `PrometheusBeforeMiddleware` must be first and `PrometheusAfterMiddleware` must be last. Every middleware that runs between them is timed, and the request and response are measured correctly regardless of which middleware in between raises an exception.

```python
MIDDLEWARE = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",  # FIRST
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",   # LAST
]
```

If you place these middlewares anywhere other than the absolute first and last positions, request latency measurements will be wrong — you will miss the time spent in middlewares outside the pair.

### Optional Settings

```python
# settings/base.py

# Custom namespace prefix for all auto-generated metrics.
# Default: no prefix. With this set, all metrics become:
# myproject_django_http_requests_total_by_method_total etc.
PROMETHEUS_METRIC_NAMESPACE = "myproject"

# Latency buckets for the request duration histogram.
# These are the upper bounds of each bucket, in seconds.
# More buckets = more accuracy but more storage and scrape cost.
# Default buckets are listed below — tune for your app's expected latency.
PROMETHEUS_LATENCY_BUCKETS = (
    0.01,   # 10ms
    0.025,  # 25ms
    0.05,   # 50ms
    0.075,  # 75ms
    0.1,    # 100ms
    0.25,   # 250ms
    0.5,    # 500ms
    0.75,   # 750ms
    1.0,    # 1s
    2.5,    # 2.5s
    5.0,    # 5s
    7.5,    # 7.5s
    10.0,   # 10s
    25.0,   # 25s
    50.0,   # 50s
    75.0,   # 75s
    float("inf"),  # anything above the last bucket
)

# Disable auto-export of migration metrics (applied/unapplied counts)
# Useful if you handle migrations outside the running app process
PROMETHEUS_EXPORT_MIGRATIONS = True  # default: True
```

---

## 4. The /metrics Endpoint

### Basic Setup

```python
# config/urls.py
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.api.urls")),

    # This adds /metrics — the path Prometheus will scrape
    path("", include("django_prometheus.urls")),
]
```

The above exposes `/metrics` at the root of your URL conf. If you want it at a different path:

```python
# Expose at /monitoring/metrics instead of /metrics
path("monitoring/", include("django_prometheus.urls")),
```

If you use a prefix, you must tell Prometheus the path in your scrape config (covered in Section 14).

### What the Endpoint Looks Like

Visit `http://localhost:8000/metrics` in your browser or with curl after setting up the middleware:

```bash
curl http://localhost:8000/metrics
```

You will see hundreds of lines of text metrics. This is normal. It includes Python runtime metrics, Django-specific metrics, and any custom metrics you define.

---

## 5. What Metrics django-prometheus Gives You for Free

Once the middleware and `INSTALLED_APPS` entry are in place, you automatically get the following metrics without writing a single line of code.

### HTTP Request Metrics

| Metric Name | Type | Description |
|---|---|---|
| `django_http_requests_total_by_method` | Counter | Request count broken down by HTTP method (GET, POST, etc.) |
| `django_http_requests_total_by_transport` | Counter | HTTP vs HTTPS |
| `django_http_requests_total_by_view_transport_method` | Counter | Per view name, transport, and method |
| `django_http_requests_unknown_latency` | Counter | Requests where latency could not be measured |
| `django_http_requests_before_middlewares_total` | Counter | All requests hitting the Before middleware |
| `django_http_responses_total_by_status` | Counter | Response count broken down by HTTP status code |
| `django_http_responses_total_by_status_view_method` | Counter | Per status code, view name, and method |
| `django_http_responses_body_total_bytes` | Counter | Total bytes sent in response bodies |
| `django_http_requests_latency_including_middlewares_seconds` | Histogram | End-to-end request latency (includes all middleware time) |
| `django_http_requests_latency_seconds_by_view_method` | Histogram | Latency broken down by view name and HTTP method |

### Migration Metrics

| Metric Name | Type | Description |
|---|---|---|
| `django_migrations_applied_by_connection` | Gauge | Number of applied migrations per database alias |
| `django_migrations_unapplied_by_connection` | Gauge | Number of pending (unapplied) migrations |

The migration metrics are particularly useful: you can alert on `django_migrations_unapplied_by_connection > 0` to catch cases where a deployment forgot to run migrations.

### Python Runtime Metrics

The underlying `prometheus_client` also automatically exports Python process metrics:

| Metric Name | Type | Description |
|---|---|---|
| `python_gc_objects_collected_total` | Counter | GC objects collected per generation |
| `python_gc_objects_uncollectable_total` | Counter | Uncollectable GC objects |
| `python_gc_collections_total` | Counter | GC collection cycles per generation |
| `python_info` | Gauge | Python version info |
| `process_virtual_memory_bytes` | Gauge | Virtual memory usage |
| `process_resident_memory_bytes` | Gauge | Resident memory (RSS) |
| `process_cpu_seconds_total` | Counter | CPU time used |
| `process_open_fds` | Gauge | Open file descriptors |

---

## 6. Monitoring Your Database

By default, Django's database backend does not emit metrics. To enable database monitoring, swap Django's backend with django-prometheus's instrumented version.

### PostgreSQL

```python
# settings/base.py
DATABASES = {
    "default": {
        # Change django.db.backends.postgresql
        # to   django_prometheus.db.backends.postgresql
        "ENGINE": "django_prometheus.db.backends.postgresql",
        "NAME": env("POSTGRES_DB"),
        "USER": env("POSTGRES_USER"),
        "PASSWORD": env("POSTGRES_PASSWORD"),
        "HOST": env("POSTGRES_HOST", default="localhost"),
        "PORT": env("POSTGRES_PORT", default="5432"),
        "CONN_MAX_AGE": 60,
    }
}
```

### MySQL

```python
"ENGINE": "django_prometheus.db.backends.mysql",
```

### SQLite (Development)

```python
"ENGINE": "django_prometheus.db.backends.sqlite3",
```

### Database Metrics You Get

| Metric Name | Type | Description |
|---|---|---|
| `django_db_query_duration_seconds` | Histogram | Query execution time per database alias and vendor |
| `django_db_execute_total` | Counter | Total `execute()` calls |
| `django_db_execute_many_total` | Counter | Total `executemany()` calls |
| `django_db_errors_total` | Counter | Database errors by type |

These let you answer questions like: "Which database alias is generating the most queries?" and "Are query times increasing?"

---

## 7. Monitoring Your Cache

Similar to databases, swap the cache backend with django-prometheus's instrumented version:

```python
# settings/base.py

# Redis cache
CACHES = {
    "default": {
        # Change: django.core.cache.backends.redis.RedisCache
        # To:     django_prometheus.cache.backends.redis.RedisCache
        "BACKEND": "django_prometheus.cache.backends.redis.RedisCache",
        "LOCATION": env("REDIS_URL"),
    }
}

# Memcached
CACHES = {
    "default": {
        "BACKEND": "django_prometheus.cache.backends.memcached.PyMemcacheCache",
        "LOCATION": "127.0.0.1:11211",
    }
}

# File-based cache (development)
CACHES = {
    "default": {
        "BACKEND": "django_prometheus.cache.backends.filebased.FileBasedCache",
        "LOCATION": "/var/tmp/django_cache",
    }
}
```

### Cache Metrics You Get

| Metric Name | Type | Description |
|---|---|---|
| `django_cache_get_total` | Counter | Total cache GET operations |
| `django_cache_get_hits_total` | Counter | Cache hits (value was found) |
| `django_cache_get_misses_total` | Counter | Cache misses (value not found) |
| `django_cache_hits_total` | Counter | Alias for hits |
| `django_cache_misses_total` | Counter | Alias for misses |
| `django_cache_set_total` | Counter | Total cache SET operations |
| `django_cache_delete_total` | Counter | Total cache DELETE operations |

A critical metric derived from these is your **cache hit rate**:
```
django_cache_get_hits_total / django_cache_get_total
```
A dropping hit rate means your cache is not working as expected — keys are expiring too fast, memory is full, or your code changed and keys are no longer being hit.

---

## 8. Monitoring Your Models

You can track creation, update, and deletion rates for individual models by adding a mixin. This requires **no database migration** — the mixin only hooks into Django's model signals.

```python
# apps/orders/models.py
from django.db import models
from django_prometheus.models import ExportModelOperationsMixin

# Usage: ExportModelOperationsMixin('name_used_in_metric_label')
# The name becomes the value of the "model" label in the exported metrics.
# Keep it lowercase, no spaces, descriptive but short.

class Order(ExportModelOperationsMixin("order"), models.Model):
    status = models.CharField(max_length=20)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

class OrderItem(ExportModelOperationsMixin("order_item"), models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

class Product(ExportModelOperationsMixin("product"), models.Model):
    name = models.CharField(max_length=200)
    stock = models.PositiveIntegerField(default=0)
```

This exports three metrics per instrumented model:

```
django_model_inserts_total{model="order"} 1204.0
django_model_updates_total{model="order"} 982.0
django_model_deletes_total{model="order"} 11.0

django_model_inserts_total{model="order_item"} 3891.0
...
```

**Important:** these are counters of operations that happened in the current process, not counts of how many records exist in the database. To know how many orders exist, use a Gauge that queries the database (covered in the custom metrics section).

---

## 9. The Four Prometheus Metric Types

This is the most important conceptual section. Using the wrong metric type leads to incorrect data and misleading dashboards. There are exactly four types.

### Counter

A Counter is a number that only ever increases. It resets to zero when the process restarts. You never decrement a counter.

**When to use it:** counting events — requests served, emails sent, errors raised, jobs completed, payments processed.

**Never use it for:** anything that can go down — queue depth, active connections, memory usage.

**PromQL:** Because counters reset on restart, you never use the raw value. You always use `rate()` or `increase()` to compute how fast the counter is growing.

```python
from prometheus_client import Counter

# Define at module level (not inside a function or class)
orders_created = Counter(
    "myapp_orders_created_total",   # Name — must end in _total for counters
    "Total number of orders created",
)
payments_failed = Counter(
    "myapp_payments_failed_total",
    "Total number of failed payment attempts",
    ["payment_provider"],           # Labels (see Section 11)
)

# Usage
orders_created.inc()                        # Increment by 1
orders_created.inc(5)                       # Increment by 5
payments_failed.labels(payment_provider="stripe").inc()
```

### Gauge

A Gauge is a number that can go up and down. It represents a current state.

**When to use it:** measuring current quantities — active sessions, items in a queue, memory usage, number of open connections, temperature readings, cache size.

**Never use it for:** cumulative event counts (use Counter for that).

```python
from prometheus_client import Gauge

active_sessions = Gauge(
    "myapp_active_sessions",
    "Number of currently active user sessions",
)
queue_depth = Gauge(
    "myapp_task_queue_depth",
    "Number of tasks waiting in the Celery queue",
    ["queue_name"],
)

# Usage
active_sessions.set(42)           # Set to an absolute value
active_sessions.inc()             # Increment by 1
active_sessions.dec()             # Decrement by 1
queue_depth.labels(queue_name="default").set(current_depth)

# Context manager — automatically inc on enter, dec on exit
with active_sessions.track_inprogress():
    # Code that runs while the "session" is active
    process_request()
```

### Histogram

A Histogram tracks the distribution of values by sorting observations into pre-defined buckets. It is used for things that have a range of possible values, like response times, file sizes, or payment amounts.

A single Histogram metric automatically exports three things to Prometheus:
- `metric_bucket{le="0.1"}` — how many observations were ≤ 0.1 seconds (one per bucket)
- `metric_sum` — the sum of all observations
- `metric_count` — the total number of observations

**When to use it:** response latency, request size, queue wait time, file upload size.

**Key decision: bucket configuration.** You must choose bucket boundaries that make sense for what you are measuring. If your API typically responds in 50-200ms, your buckets should have granularity in that range. The default buckets in Prometheus are designed for general HTTP latency.

```python
from prometheus_client import Histogram

request_latency = Histogram(
    "myapp_request_duration_seconds",
    "Time spent processing a request",
    ["endpoint", "method"],
    # Buckets in seconds. Think about your app's expected latency profile.
    # Fine granularity at the low end where most requests land.
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, float("inf"))
)

payment_amount = Histogram(
    "myapp_payment_amount_dollars",
    "Distribution of payment amounts in dollars",
    # Buckets tuned for dollar amounts
    buckets=(5, 10, 25, 50, 100, 250, 500, 1000, 5000, float("inf"))
)

# Usage: manually
import time
start = time.time()
process_order()
request_latency.labels(endpoint="/api/orders/", method="POST").observe(time.time() - start)

# Usage: as a context manager (cleaner)
with request_latency.labels(endpoint="/api/orders/", method="POST").time():
    process_order()

# Usage: as a decorator
@request_latency.labels(endpoint="/api/products/", method="GET").time()
def list_products():
    ...
```

### Summary

A Summary also tracks distributions, like Histogram, but it pre-computes quantiles on the client side (inside your Django process) rather than letting Prometheus compute them later from buckets.

**When to use it:** when you need precise quantile accuracy within a single process and do not need to aggregate across multiple instances.

**When NOT to use it:** in multi-process environments (like Django + Gunicorn with multiple workers), summaries cannot be aggregated across workers. Histograms can. This makes **Histogram the better choice in virtually all Django production setups.**

```python
from prometheus_client import Summary

# Summary pre-computes these quantiles (0.5 = median, 0.9 = 90th percentile)
request_summary = Summary(
    "myapp_request_processing_seconds",
    "Summary of request processing time",
)

# Usage
with request_summary.time():
    process_request()
```

### Choosing the Right Type — Quick Decision Guide

```
Is the value always increasing (never decreases)?
    Yes → Counter

Can the value go up and down?
    Yes → Gauge

Do you need to measure the distribution/spread of values (like latency)?
    Yes → Histogram (preferred for multi-process apps like Django + Gunicorn)
          Summary only if single-process and you need client-side quantile precision
```

---

## 10. Writing Custom Metrics

Custom metrics are where django-prometheus becomes truly powerful. The built-in metrics tell you how Django is performing; custom metrics tell you what your business is doing.

### Where to Define Metrics

Define metrics at the **module level**, not inside functions or class methods. Prometheus metrics are global singletons — instantiating them inside a function creates duplicate registration errors.

```python
# apps/orders/metrics.py
# Create a dedicated file for your metrics. Import from here everywhere.

from prometheus_client import Counter, Gauge, Histogram

# ---- Order business metrics ----

orders_created = Counter(
    "myapp_orders_created_total",
    "Total orders created",
    ["payment_provider", "user_type"],  # labels: dimensions you can filter/group by
)

order_processing_duration = Histogram(
    "myapp_order_processing_duration_seconds",
    "Time taken to process an order from creation to confirmation",
    ["order_type"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, float("inf")),
)

orders_pending = Gauge(
    "myapp_orders_pending",
    "Number of orders currently in pending status",
)

payments_failed = Counter(
    "myapp_payments_failed_total",
    "Total failed payment attempts",
    ["payment_provider", "failure_reason"],
)

# ---- User metrics ----

user_logins = Counter(
    "myapp_user_logins_total",
    "Total successful user logins",
    ["auth_method"],  # e.g., password, oauth, sso
)

user_login_failures = Counter(
    "myapp_user_login_failures_total",
    "Total failed login attempts",
    ["failure_reason"],  # e.g., wrong_password, account_locked, user_not_found
)

active_users = Gauge(
    "myapp_active_users",
    "Number of users with an active session",
)
```

### Using Metrics in Your Services

```python
# apps/orders/services.py
from django.db import transaction
from .metrics import (
    orders_created,
    order_processing_duration,
    orders_pending,
    payments_failed,
)

def create_order(*, user, items, payment_provider):
    with order_processing_duration.labels(order_type="standard").time():
        with transaction.atomic():
            order = Order.objects.create(user=user)
            for item in items:
                OrderItem.objects.create(order=order, **item)

        # Determine user type for label
        user_type = "premium" if user.is_premium else "standard"

        # Increment the counter with label values
        orders_created.labels(
            payment_provider=payment_provider,
            user_type=user_type,
        ).inc()

        # Update the pending gauge
        orders_pending.inc()

    return order


def process_payment(order, payment_provider):
    try:
        charge_card(order)
        orders_pending.dec()  # Order is no longer pending
    except PaymentDeclined as e:
        payments_failed.labels(
            payment_provider=payment_provider,
            failure_reason="card_declined",
        ).inc()
        raise
    except InsufficientFunds as e:
        payments_failed.labels(
            payment_provider=payment_provider,
            failure_reason="insufficient_funds",
        ).inc()
        raise
```

### Periodic Gauge Updates

Some gauges represent database counts or other values you need to query periodically. The best place to update these is a Celery periodic task:

```python
# apps/orders/tasks.py
from celery import shared_task
from .models import Order
from .metrics import orders_pending

@shared_task
def update_order_metrics():
    """Sync gauge metrics with actual database state. Run every minute."""
    pending_count = Order.objects.filter(status="pending").count()
    orders_pending.set(pending_count)
```

```python
# settings/base.py
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "update-order-metrics": {
        "task": "apps.orders.tasks.update_order_metrics",
        "schedule": 60.0,  # Every 60 seconds
    },
}
```

### Timing Code Blocks with a Context Manager

```python
from apps.orders.metrics import order_processing_duration

def process_bulk_import(file):
    with order_processing_duration.labels(order_type="bulk_import").time():
        # Everything inside this block is timed
        rows = parse_csv(file)
        for row in rows:
            create_order(**row)
```

### Timing with a Decorator

```python
from apps.orders.metrics import order_processing_duration

@order_processing_duration.labels(order_type="api").time()
def create_order_from_api(data):
    ...
```

---

## 11. Labels — Dimensions on Your Metrics

Labels are key-value pairs attached to a metric that let you slice and group data when querying. They are the most powerful feature of Prometheus and the most common source of mistakes.

### Good Label Usage

```python
# A counter with useful labels
http_errors = Counter(
    "myapp_http_errors_total",
    "HTTP errors by status and view",
    ["status_code", "view_name"],
)

# Now you can query:
# - Total 500 errors: myapp_http_errors_total{status_code="500"}
# - Errors on /api/orders/: myapp_http_errors_total{view_name="order-list"}
# - Both: myapp_http_errors_total{status_code="500", view_name="order-list"}
```

### The High-Cardinality Problem

Every unique combination of label values creates a separate **time series** in Prometheus. Prometheus stores all time series in memory. If a label has many possible values, your memory usage explodes and Prometheus slows down.

```python
# NEVER do this — user_id can be millions of distinct values
# This creates millions of time series, one per user
request_count = Counter(
    "myapp_requests_total",
    "Requests by user",
    ["user_id"],  # BAD: high cardinality label
)

# NEVER do this — full URL paths can be unbounded
request_count = Counter(
    "myapp_requests_total",
    "Requests by path",
    ["path"],    # BAD: /api/orders/123, /api/orders/456 — creates one series per order ID
)

# GOOD: use view name (bounded set) instead of full path
request_count = Counter(
    "myapp_requests_total",
    "Requests by view",
    ["view_name"],  # GOOD: small bounded set of view names
)

# GOOD: use bucketed categories instead of raw values
payment_amount = Histogram(
    "myapp_payment_dollars",
    "Payment amounts",
    # No user_id label. The histogram buckets handle distribution.
    buckets=(10, 50, 100, 500, 1000, float("inf")),
)
```

**Rules for labels:**

- Labels should have a small, bounded set of possible values (typically under 100 distinct values per label).
- Never use user IDs, request IDs, session IDs, IP addresses, or raw URL paths as label values.
- Good label candidates: HTTP method, status code, view name, endpoint group, environment, payment provider, queue name, model name, error type.

### Label Naming

Label names follow the same rules as metric names: lowercase, underscores, no special characters. The `le` and `quantile` labels are reserved by Prometheus.

---

## 12. The Multi-Process Problem and How to Solve It

This is the most commonly misunderstood aspect of running Prometheus in Python. If you skip this section and run multiple Gunicorn workers, your metrics will be incorrect.

### The Problem

The Python Prometheus client stores metric values in memory, inside each Python process. When you run Gunicorn with 4 workers, you have 4 separate Python processes, each with their own copy of every metric in memory.

When Prometheus scrapes `/metrics`, it hits one of the 4 workers at random. That worker responds with only the metrics it has seen. The result is that different scrapes return different values, and the data is inconsistent and incomplete.

```
Worker 1: orders_created = 200
Worker 2: orders_created = 150
Worker 3: orders_created = 175
Worker 4: orders_created = 143

Prometheus scrapes randomly:
  Scrape 1: hits Worker 3 → sees 175
  Scrape 2: hits Worker 1 → sees 200
  Scrape 3: hits Worker 2 → sees 150

Result: Prometheus thinks the counter went DOWN (200 → 150), which is wrong.
```

### The Solution: PROMETHEUS_MULTIPROC_DIR

The Python Prometheus client has a multiprocess mode where each worker writes its metrics to files in a shared directory. When any worker handles a `/metrics` request, it reads and aggregates all files from the shared directory, giving a complete view of all workers.

**Step 1: Create the directory**

```bash
mkdir -p /tmp/prometheus_multiproc
# In production, use a directory on a tmpfs filesystem for speed:
# /run/prometheus_multiproc or /dev/shm/prometheus_multiproc
```

**Step 2: Set the environment variable BEFORE Django starts**

This is critical: the variable must be set in the shell environment, not from Python code. If set from Python, child processes may not inherit it correctly.

```bash
# In your start script, Docker entrypoint, or systemd service file:
export PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc

# Then start your server:
gunicorn config.wsgi:application --workers 4
```

```dockerfile
# In your Dockerfile
ENV PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc
RUN mkdir -p /tmp/prometheus_multiproc
```

**Step 3: Configure Gunicorn to clean up dead worker files**

When a Gunicorn worker exits, its metrics files should be marked as dead. Add a `gunicorn.conf.py`:

```python
# gunicorn.conf.py
from prometheus_client import multiprocess

def child_exit(server, worker):
    """Called by Gunicorn when a worker exits."""
    multiprocess.mark_process_dead(worker.pid)
```

```bash
# Start Gunicorn with the config file:
gunicorn config.wsgi:application \
    --workers 4 \
    --config gunicorn.conf.py
```

**Step 4: Clear the directory on startup**

Stale files from a previous run will corrupt your metrics. Clear the directory before each startup:

```bash
# Docker entrypoint script (entrypoint.sh)
#!/bin/bash
set -e

# Clear stale multiprocess files from any previous run
rm -rf /tmp/prometheus_multiproc/*

# Run migrations
python manage.py migrate

# Start the server
exec gunicorn config.wsgi:application \
    --workers 4 \
    --config gunicorn.conf.py \
    --bind 0.0.0.0:8000
```

**Step 5: Disable app preloading in Gunicorn**

With multiprocess mode, each worker must initialize the Prometheus client independently. Gunicorn's `--preload` flag loads the app in the master process before forking, which breaks multiprocess mode.

```bash
# If using preload, disable it:
gunicorn config.wsgi:application --workers 4 --no-preload
# Or in gunicorn.conf.py:
preload_app = False
```

### Gauge Mode in Multiprocess

Counters and Histograms aggregate naturally across processes (they are summed). Gauges are trickier because "current active sessions" in worker 1 and "current active sessions" in worker 2 should be summed, not each reported separately.

You control this with `multiprocess_mode`:

```python
from prometheus_client import Gauge

# Sum across all workers — use for quantities that each worker tracks independently
active_requests = Gauge(
    "myapp_active_requests",
    "Requests currently being processed",
    multiprocess_mode="livesum",  # Sum all live workers
)

# Most recent value across all workers — use for gauges set once (like config values)
app_version = Gauge(
    "myapp_version_info",
    "Application version",
    multiprocess_mode="mostrecent",
)

# Available modes:
# "all"        — (default) one time series per process, labeled by pid
# "livesum"    — sum of all LIVE processes only
# "liveall"    — all time series, but only for LIVE processes
# "min"        — minimum value across all processes
# "max"        — maximum value across all processes
# "sum"        — sum of all processes (alive and dead)
# "mostrecent" — most recently set value across all processes
```

---

## 13. Securing the /metrics Endpoint

The `/metrics` endpoint exposes detailed internal information about your application. In production, it should not be publicly accessible.

### Option 1: Network-Level Restriction (Recommended)

Restrict access to `/metrics` at the nginx or load balancer level, allowing only your Prometheus server's IP:

```nginx
# nginx.conf
server {
    listen 80;
    server_name api.mysite.com;

    # Block /metrics from the public internet
    location /metrics {
        # Only allow your Prometheus server's IP
        allow 10.0.1.50;   # Prometheus server internal IP
        deny all;
        proxy_pass http://django:8000;
    }

    location / {
        proxy_pass http://django:8000;
    }
}
```

### Option 2: Token-Based Authentication

If network-level restriction is not possible, add a simple token check:

```python
# config/urls.py
from django.urls import path, include
from django.http import HttpResponse
from django.views.decorators.http import require_GET

@require_GET
def metrics_view(request):
    """Prometheus metrics endpoint, protected by token."""
    token = request.headers.get("Authorization", "")
    expected = f"Bearer {settings.PROMETHEUS_TOKEN}"

    if token != expected:
        return HttpResponse(status=403)

    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    return HttpResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST)

urlpatterns = [
    # Replace the default django_prometheus.urls with your protected view
    path("metrics", metrics_view, name="prometheus-metrics"),
]
```

Then configure Prometheus to send the token in its scrape config:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: "django"
    authorization:
      credentials: "your-secret-token-here"
    static_configs:
      - targets: ["api.mysite.com:80"]
    metrics_path: "/metrics"
```

### Option 3: Separate Internal Port (Advanced)

Run a separate HTTP server on an internal port just for metrics, not exposed publicly:

```python
# settings/base.py
PROMETHEUS_METRICS_EXPORT_PORT = 9090       # Internal port for metrics only
PROMETHEUS_METRICS_EXPORT_ADDRESS = ""       # Listen on all interfaces

# Prometheus then scrapes internal port 9090, not the public app port
```

Note: this approach has limitations with Gunicorn and requires careful handling. The network-level restriction at nginx is simpler and more reliable.

---

## 14. Prometheus Server Configuration

This section covers how to run and configure the Prometheus server itself.

### Docker Setup

```yaml
# docker-compose.yml
version: "3.9"

services:
  web:
    build: .
    environment:
      PROMETHEUS_MULTIPROC_DIR: /tmp/prometheus_multiproc
    ports:
      - "8000:8000"

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./provisioning/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
      - "--storage.tsdb.retention.time=15d"   # Keep 15 days of data
      - "--storage.tsdb.path=/prometheus"

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    environment:
      GF_SECURITY_ADMIN_PASSWORD: your-grafana-password

volumes:
  prometheus_data:
  grafana_data:
```

### prometheus.yml Configuration

```yaml
# provisioning/prometheus/prometheus.yml

global:
  scrape_interval: 15s       # How often Prometheus scrapes targets
  evaluation_interval: 15s   # How often alerting rules are evaluated

# Alertmanager configuration (optional, for sending alerts)
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - "alertmanager:9093"

# Alerting rules files (optional)
rule_files:
  - "alerts.yml"

# Scrape configurations
scrape_configs:
  # Your Django application
  - job_name: "django"
    scrape_interval: 15s
    static_configs:
      - targets:
          - "web:8000"          # Docker service name and port
    metrics_path: "/metrics"   # Only needed if you used a custom prefix

  # If you used path("monitoring/", ...) in urls.py:
  # metrics_path: "/monitoring/metrics"

  # Scrape Prometheus itself (useful for debugging)
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]
```

### Kubernetes Configuration

In Kubernetes, you typically use the Prometheus Operator with `ServiceMonitor` resources rather than static scrape configs:

```yaml
# servicemonitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: django-app
  labels:
    app: django
spec:
  selector:
    matchLabels:
      app: django
  endpoints:
    - port: http
      path: /metrics
      interval: 15s
```

---

## 15. PromQL — Querying Your Metrics

PromQL (Prometheus Query Language) is what you use in Grafana panels and alerting rules. You do not need to be an expert, but you need to understand the essential functions.

### Instant Vector vs Range Vector

Every PromQL query returns one of two types:

An **instant vector** is the current value of a metric right now:
```
django_http_responses_total_by_status_total{status="200"}
# Returns: 48291 (current counter value)
```

A **range vector** is the values of a metric over a time window, used with functions like `rate()`. Written with a `[duration]` selector:
```
django_http_responses_total_by_status_total{status="200"}[5m]
# Returns: all values scraped over the last 5 minutes
```

### The Essential Functions

**rate() — How fast is a counter increasing?**

`rate()` computes the per-second rate of increase of a counter over a time window. This is the most used function in Prometheus. Always use `rate()` on counters, never the raw counter value.

```
# Requests per second over the last 5 minutes
rate(django_http_requests_total_by_method_total[5m])

# 500 errors per second
rate(django_http_responses_total_by_status_total{status="500"}[5m])

# DB queries per second
rate(django_db_execute_total{alias="default"}[5m])
```

**increase() — How much did a counter grow?**

`increase()` is like `rate()` but returns the total increase over the time window rather than the per-second rate.

```
# Total requests in the last 1 hour
increase(django_http_requests_total_by_method_total[1h])

# Orders created in the last 24 hours
increase(myapp_orders_created_total[24h])
```

**sum() — Aggregate across labels**

```
# Total requests per second across all methods
sum(rate(django_http_requests_total_by_method_total[5m]))

# Requests per second grouped by HTTP method
sum by (method) (rate(django_http_requests_total_by_method_total[5m]))

# Total 5xx errors per second across all status codes
sum(rate(django_http_responses_total_by_status_total{status=~"5.."}[5m]))
```

**histogram_quantile() — Percentile latency from a histogram**

```
# 95th percentile request latency over the last 5 minutes
histogram_quantile(0.95, rate(django_http_requests_latency_including_middlewares_seconds_bucket[5m]))

# 99th percentile latency per view
histogram_quantile(0.99,
  sum by (view, le) (
    rate(django_http_requests_latency_seconds_by_view_method_bucket[5m])
  )
)

# Median (50th percentile) latency
histogram_quantile(0.50, rate(django_http_requests_latency_including_middlewares_seconds_bucket[5m]))
```

**avg_over_time() — Average of a gauge over time**

```
# Average number of pending orders over the last hour
avg_over_time(myapp_orders_pending[1h])

# Max queue depth in the last 15 minutes
max_over_time(myapp_task_queue_depth[15m])
```

### Practical PromQL Examples

```
# ---- HTTP Performance ----

# Overall request rate (requests per second)
sum(rate(django_http_requests_total_by_method_total[5m]))

# Error rate (percentage of responses that are 5xx)
sum(rate(django_http_responses_total_by_status_total{status=~"5.."}[5m]))
  /
sum(rate(django_http_requests_total_by_method_total[5m]))
* 100

# 95th percentile latency in milliseconds
histogram_quantile(0.95, rate(django_http_requests_latency_including_middlewares_seconds_bucket[5m])) * 1000

# Apdex score — ratio of requests that are "satisfying" (< 0.5s)
(
  sum(rate(django_http_requests_latency_including_middlewares_seconds_bucket{le="0.5"}[5m]))
)
/
sum(rate(django_http_requests_latency_including_middlewares_seconds_count[5m]))


# ---- Database ----

# DB query rate
rate(django_db_execute_total{alias="default"}[5m])

# DB error rate
rate(django_db_errors_total[5m])

# Average DB query duration
rate(django_db_query_duration_seconds_sum[5m])
  /
rate(django_db_query_duration_seconds_count[5m])


# ---- Cache ----

# Cache hit rate (0 to 1, higher is better)
rate(django_cache_get_hits_total[5m])
  /
rate(django_cache_get_total[5m])


# ---- Business Metrics ----

# Orders created per minute
sum(increase(myapp_orders_created_total[1m]))

# Payment failure rate
rate(myapp_payments_failed_total[5m])
  /
(rate(myapp_payments_failed_total[5m]) + rate(myapp_orders_created_total[5m]))
* 100

# Current pending orders
myapp_orders_pending

# ---- Migrations ----
# Alert if there are unapplied migrations
django_migrations_unapplied_by_connection > 0
```

---

## 16. Alerting Rules

Alerting rules are written in YAML and evaluated by Prometheus. When a rule's condition is true for longer than `for:` duration, Prometheus sends an alert to Alertmanager, which routes it to Slack, PagerDuty, email, etc.

```yaml
# provisioning/prometheus/alerts.yml

groups:
  - name: django_application
    interval: 60s  # How often to evaluate these rules

    rules:
      # High error rate — more than 1% of responses are 5xx
      - alert: HighErrorRate
        expr: |
          sum(rate(django_http_responses_total_by_status_total{status=~"5.."}[5m]))
          /
          sum(rate(django_http_requests_total_by_method_total[5m]))
          > 0.01
        for: 2m   # Must be true for 2 minutes before firing
        labels:
          severity: critical
        annotations:
          summary: "High HTTP error rate on {{ $labels.instance }}"
          description: "{{ $value | humanizePercentage }} of requests are returning 5xx errors."

      # High latency — 95th percentile above 2 seconds
      - alert: HighLatency
        expr: |
          histogram_quantile(0.95,
            rate(django_http_requests_latency_including_middlewares_seconds_bucket[5m])
          ) > 2.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High request latency"
          description: "95th percentile latency is {{ $value }}s"

      # Unapplied migrations
      - alert: UnappliedMigrations
        expr: django_migrations_unapplied_by_connection > 0
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Unapplied database migrations detected"
          description: "{{ $value }} migration(s) have not been applied on {{ $labels.connection }}."

      # DB error rate spike
      - alert: DatabaseErrors
        expr: rate(django_db_errors_total[5m]) > 0.1
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Database errors occurring"
          description: "{{ $value }} DB errors per second"

      # Cache hit rate drop
      - alert: LowCacheHitRate
        expr: |
          rate(django_cache_get_hits_total[10m])
          /
          rate(django_cache_get_total[10m])
          < 0.5
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Cache hit rate below 50%"
          description: "Cache hit rate is {{ $value | humanizePercentage }}. Check cache configuration."

      # Payment failures
      - alert: PaymentFailureSpike
        expr: rate(myapp_payments_failed_total[5m]) > 0.5
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Payment failures spiking"
          description: "{{ $value }} payment failures per second"
```

---

## 17. Grafana Dashboard Setup

Grafana connects to Prometheus as a data source and lets you build dashboards using PromQL queries.

### Connect Grafana to Prometheus

1. Open Grafana at `http://localhost:3000` (default credentials: admin / admin)
2. Go to **Connections** → **Data Sources** → **Add data source**
3. Select **Prometheus**
4. Set the URL to `http://prometheus:9090` (or your Prometheus address)
5. Click **Save & Test**

### Key Panels for a Django Dashboard

Here are the essential panels to create, with the PromQL queries and recommended visualization type for each.

**Request Rate — Time Series**
```
sum(rate(django_http_requests_total_by_method_total[5m]))
```

**Error Rate (%) — Gauge or Time Series**
```
sum(rate(django_http_responses_total_by_status_total{status=~"5.."}[5m]))
  /
sum(rate(django_http_requests_total_by_method_total[5m]))
* 100
```

**95th Percentile Latency (ms) — Time Series**
```
histogram_quantile(0.95, rate(django_http_requests_latency_including_middlewares_seconds_bucket[5m])) * 1000
```

**DB Query Rate — Time Series**
```
rate(django_db_execute_total{alias="default"}[5m])
```

**Cache Hit Rate (%) — Gauge**
```
rate(django_cache_get_hits_total[5m])
  /
rate(django_cache_get_total[5m])
* 100
```

**Memory Usage (MB) — Time Series**
```
process_resident_memory_bytes{job="django"} / 1024 / 1024
```

**Requests by Status Code — Time Series (stacked)**
```
sum by (status) (rate(django_http_responses_total_by_status_total[5m]))
```

**Unapplied Migrations — Stat panel**
```
django_migrations_unapplied_by_connection
```
Set a threshold: green at 0, red above 0.

**Pending Orders — Stat panel**
```
myapp_orders_pending
```

### Pre-built Grafana Dashboard

The Grafana community maintains dashboards you can import directly. Search for "django prometheus" at https://grafana.com/grafana/dashboards/ to find ready-made templates. Import by dashboard ID in the Grafana UI (Dashboards → Import).

---

## 18. Custom Middleware Labels

django-prometheus lets you attach your own labels to the auto-generated middleware metrics. This lets you slice HTTP metrics by dimensions your app knows about, like `tenant`, `api_version`, or `user_type`.

```python
# myapp/prometheus_middleware.py
from django_prometheus.middleware import (
    Metrics,
    PrometheusBeforeMiddleware,
    PrometheusAfterMiddleware,
)

class CustomMetrics(Metrics):
    """Extended Metrics class that adds application-specific labels."""

    def register_metric(self, metric_cls, name, documentation, labelnames=(), **kwargs):
        # Add your custom label names to every request/response metric
        return super().register_metric(
            metric_cls,
            name,
            documentation,
            labelnames=list(labelnames) + ["api_version", "user_type"],
            **kwargs,
        )


class CustomPrometheusBeforeMiddleware(PrometheusBeforeMiddleware):
    metrics_cls = CustomMetrics


class CustomPrometheusAfterMiddleware(PrometheusAfterMiddleware):
    metrics_cls = CustomMetrics

    def label_metric(self, metric, request, response=None, **labels):
        # Extract custom label values from the request
        api_version = getattr(request, "version", "v1") or "v1"
        user_type = "authenticated" if request.user.is_authenticated else "anonymous"

        return super().label_metric(
            metric,
            request,
            response,
            api_version=api_version,
            user_type=user_type,
            **labels,
        )
```

```python
# settings/base.py — use your custom middleware classes instead of the defaults
MIDDLEWARE = [
    "myapp.prometheus_middleware.CustomPrometheusBeforeMiddleware",   # Custom
    "django.middleware.security.SecurityMiddleware",
    # ... other middlewares ...
    "myapp.prometheus_middleware.CustomPrometheusAfterMiddleware",    # Custom
]
```

---

## 19. Docker and Kubernetes Setup

### Full Docker Compose Stack

```yaml
# docker-compose.yml
version: "3.9"

x-django-env: &django-env
  DJANGO_SETTINGS_MODULE: config.settings.production
  DATABASE_URL: postgres://user:password@db:5432/mydb
  REDIS_URL: redis://redis:6379/0
  PROMETHEUS_MULTIPROC_DIR: /tmp/prometheus_multiproc

services:
  web:
    build: .
    environment:
      <<: *django-env
    volumes:
      - prometheus_multiproc:/tmp/prometheus_multiproc
    ports:
      - "8000:8000"
    depends_on: [db, redis]
    command: >
      sh -c "rm -rf /tmp/prometheus_multiproc/* &&
             python manage.py migrate &&
             gunicorn config.wsgi:application
               --workers 4
               --config gunicorn.conf.py
               --bind 0.0.0.0:8000"

  celery:
    build: .
    environment:
      <<: *django-env
    volumes:
      - prometheus_multiproc:/tmp/prometheus_multiproc
    command: celery -A config worker -l info

  db:
    image: postgres:16
    environment:
      POSTGRES_DB: mydb
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data/

  redis:
    image: redis:7-alpine

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./provisioning/prometheus:/etc/prometheus
      - prometheus_data:/prometheus
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
      - "--storage.tsdb.retention.time=15d"

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./provisioning/grafana:/etc/grafana/provisioning
    environment:
      GF_SECURITY_ADMIN_PASSWORD: changeme
    depends_on: [prometheus]

volumes:
  postgres_data:
  prometheus_data:
  grafana_data:
  prometheus_multiproc:
```

### gunicorn.conf.py

```python
# gunicorn.conf.py
import os
from prometheus_client import multiprocess

bind = "0.0.0.0:8000"
workers = 4
worker_class = "sync"
preload_app = False     # IMPORTANT: must be False for multiprocess mode
timeout = 30
keepalive = 2

def child_exit(server, worker):
    """Clean up prometheus multiprocess files when a worker exits."""
    multiprocess.mark_process_dead(worker.pid)
```

### Kubernetes Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: django-app
spec:
  replicas: 3
  template:
    spec:
      initContainers:
        # Clear stale multiproc files on startup
        - name: clear-prometheus-multiproc
          image: busybox
          command: ["sh", "-c", "rm -rf /tmp/prometheus_multiproc/*"]
          volumeMounts:
            - name: prometheus-multiproc
              mountPath: /tmp/prometheus_multiproc

      containers:
        - name: django
          image: mycompany/django-app:latest
          env:
            - name: PROMETHEUS_MULTIPROC_DIR
              value: /tmp/prometheus_multiproc
          ports:
            - containerPort: 8000
          volumeMounts:
            - name: prometheus-multiproc
              mountPath: /tmp/prometheus_multiproc

      volumes:
        - name: prometheus-multiproc
          emptyDir:
            medium: Memory   # Use tmpfs for speed
```

---

## 20. Naming Conventions and Best Practices

### Metric Naming

Follow Prometheus's official naming conventions to keep your metrics consistent with the wider ecosystem:

```
<namespace>_<subsystem>_<name>_<unit>_total (for counters)
<namespace>_<subsystem>_<name>_<unit>      (for gauges, histograms, summaries)
```

- Use lowercase and underscores only.
- Include the unit in the metric name: `_seconds`, `_bytes`, `_total`, `_ratio`.
- Counter names must end in `_total`.
- Do not include label names in the metric name.
- Do not use the word "metric" in a metric name — everything is a metric.

```python
# Good names
"myapp_http_requests_total"
"myapp_order_processing_duration_seconds"
"myapp_cache_size_bytes"
"myapp_active_connections"
"myapp_payment_amount_dollars"

# Bad names
"myapp_requests"              # Missing _total for a counter
"myapp_requestDurationMs"     # Camel case, unit not in base units
"myapp_metric_count"          # "metric" in name
"myapp_http_requests_by_user" # Label value in name
```

### The RED Method

When deciding what custom metrics to add to a service endpoint, use the RED method as a checklist:

- **R — Rate:** How many requests per second is this endpoint handling?
- **E — Errors:** What fraction of those requests are failing?
- **D — Duration:** How long does each request take?

Every important endpoint and background task in your system should have these three metrics.

### The USE Method

For resources like databases, caches, queues, and workers, use the USE method:

- **U — Utilization:** What fraction of capacity is being used? (e.g., DB connection pool usage)
- **S — Saturation:** How much demand is queued up waiting? (e.g., Celery queue depth)
- **E — Errors:** Are errors occurring? (e.g., DB errors, cache misses treated as errors)

### Cardinality Budget

As a rule of thumb, keep the total number of unique time series in Prometheus under 1 million for a typical single-node setup. Each label combination creates a time series. Calculate your cardinality:

```
Total time series per metric = number of label value combinations
                             = value_count(label_1) × value_count(label_2) × ...

Example:
  http_errors with labels [status_code (5 values), view_name (50 values), method (5 values)]
  = 5 × 50 × 5 = 1,250 time series for this one metric

  That is fine. Cardinality only becomes a problem with high-cardinality labels
  (thousands or millions of unique values).
```

---

## 21. Checklist

Use this every time you add Prometheus monitoring to a new Django project or feature.

### Initial Setup

- [ ] `django_prometheus` is in `INSTALLED_APPS`
- [ ] `PrometheusBeforeMiddleware` is the very first middleware
- [ ] `PrometheusAfterMiddleware` is the very last middleware
- [ ] `django_prometheus.urls` is included in `urls.py`
- [ ] The `/metrics` endpoint returns data when visited locally
- [ ] `PROMETHEUS_METRIC_NAMESPACE` is set to your project name (prevents collisions)

### Database Monitoring

- [ ] Database ENGINE is set to `django_prometheus.db.backends.postgresql` (or mysql/sqlite3)
- [ ] DB metrics appear in `/metrics` after making a request

### Cache Monitoring

- [ ] Cache BACKEND is set to the django_prometheus equivalent
- [ ] Cache metrics appear in `/metrics`

### Model Monitoring

- [ ] `ExportModelOperationsMixin` is added to all key models
- [ ] Model metric label names are lowercase and concise
- [ ] `ExportModelOperationsMixin` uses a short, descriptive string argument for the label

### Multi-Process (Gunicorn)

- [ ] `PROMETHEUS_MULTIPROC_DIR` is set in the environment (not Python code)
- [ ] The directory is created before startup
- [ ] The directory is cleared before every startup (especially in Docker)
- [ ] `gunicorn.conf.py` has the `child_exit` hook calling `multiprocess.mark_process_dead`
- [ ] `preload_app = False` in gunicorn.conf.py
- [ ] Gauge metrics use the appropriate `multiprocess_mode` (livesum, liveall, etc.)

### Custom Metrics

- [ ] All custom metrics are defined at module level in `metrics.py` files
- [ ] Counter names end in `_total`
- [ ] Metric names are lowercase with underscores, include unit in name
- [ ] No high-cardinality labels (no user IDs, request IDs, raw URLs)
- [ ] Each important endpoint/task has Rate, Error, Duration metrics (RED method)
- [ ] Business-critical resources have Utilization, Saturation, Error metrics (USE method)

### Security

- [ ] `/metrics` is not publicly accessible in production
- [ ] Either nginx restricts access by IP, or token authentication is implemented
- [ ] The metrics endpoint is not listed in robots.txt or public documentation

### Prometheus Server

- [ ] `prometheus.yml` has the correct `targets` pointing to your Django app
- [ ] `metrics_path` is set if you used a URL prefix other than the root
- [ ] `scrape_interval` is set appropriately (15s is a good default)
- [ ] Storage retention is configured (`--storage.tsdb.retention.time`)
- [ ] Alerting rules file is included and loaded

### Alerting

- [ ] Alert fires when 5xx error rate exceeds threshold
- [ ] Alert fires when p95 latency exceeds threshold
- [ ] Alert fires when `django_migrations_unapplied_by_connection > 0`
- [ ] Alert fires when DB error rate spikes
- [ ] Alert fires when cache hit rate drops below threshold
- [ ] Alerts have meaningful `summary` and `description` annotations
- [ ] Alerts have `for:` duration set (avoids alerting on transient spikes)

### Grafana

- [ ] Prometheus is added as a data source and verified with "Save & Test"
- [ ] Dashboard has panels for: request rate, error rate, p95 latency, DB query rate, cache hit rate
- [ ] Business metric panels exist for key models and workflows
- [ ] Memory and CPU panels exist
- [ ] Unapplied migrations stat panel exists with a red threshold at 1

---

*Official repository: https://github.com/django-commons/django-prometheus*
*Prometheus documentation: https://prometheus.io/docs/*
*Python Prometheus client: https://github.com/prometheus/client_python*
