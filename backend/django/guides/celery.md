# Celery in Django — Definitive Guide

> Celery is a distributed task queue system. It lets Django offload work to background worker processes — either immediately (async tasks) or on a schedule (periodic tasks). This guide covers every setup detail, every configuration option, every pattern, and every gotcha. Nothing is left to guessing.

---

## Table of Contents

1. [Architecture — How It Works](#architecture)
2. [Installation](#installation)
3. [Project Structure](#structure)
4. [Core Setup Files](#setup)
5. [Settings Reference](#settings)
6. [Writing Tasks](#writing-tasks)
7. [Calling Tasks](#calling-tasks)
8. [Task States & Results](#states)
9. [Retry Logic](#retries)
10. [Time Limits](#time-limits)
11. [Queues & Routing](#queues)
12. [Periodic Tasks — Celery Beat](#beat)
13. [Task Chaining, Groups & Chords](#chains)
14. [Django Integration & Signals](#signals)
15. [Running Workers](#running)
16. [Monitoring](#monitoring)
17. [Testing](#testing)
18. [Production Checklist](#production)
19. [Common Errors & Fixes](#errors)
20. [Quick Reference](#reference)

---

## 1. Architecture — How It Works {#architecture}

Understanding the architecture is essential before writing a single line of code.

```
Django App (Producer)
      │
      │  .delay() or .apply_async()
      ▼
  Message Broker ── Redis DB 0
  (stores queued tasks as messages)
      │
      │  Worker polls for new tasks
      ▼
  Celery Worker ── Separate OS process
  (executes the task function)
      │
      │  Writes outcome
      ▼
  Result Backend ── Django DB (via django-celery-results)
  (stores task state + return value)
      │
      │  Django code can query this
      ▼
  AsyncResult.state / .result
```

**Components and their roles:**

| Component | What It Is | Our Choice |
|---|---|---|
| **Producer** | Django code that enqueues tasks | Views, signals, services |
| **Broker** | Message queue holding pending tasks | Redis DB 0 |
| **Worker** | Separate OS process executing tasks | `celery -A myproject worker` |
| **Beat** | Scheduler that enqueues periodic tasks on a timer | `celery -A myproject beat` |
| **Result Backend** | Stores task state and return values | `django-celery-results` (Django DB) |

**Critical principle:** The Django web process and the Celery worker are **completely separate OS processes**. They share nothing in memory. They communicate only via the broker (Redis). A task cannot access the Django request context, the current user object, or any in-memory state from the web process. Always pass IDs, never objects.

---

## 2. Installation {#installation}

```bash
pip install celery redis django-celery-beat django-celery-results
```

**What each package does and why you need it:**

| Package | Min Version | Purpose |
|---|---|---|
| `celery` | `5.3+` | Core distributed task queue engine |
| `redis` | `4.0+` | Python client that connects to Redis for both broker and result backend |
| `django-celery-beat` | `2.5+` | Stores periodic task schedules in Django DB, editable via Admin — no redeploy needed to change a schedule |
| `django-celery-results` | `2.5+` | Stores task results (state, return value, traceback) in Django DB, queryable via ORM |

Add all four to `requirements.txt`. Pin minor versions in production to prevent breaking changes.

---

## 3. Project Structure {#structure}

```
myproject/
├── manage.py
├── myproject/
│   ├── __init__.py          ← MUST import celery app here (explained in setup)
│   ├── celery.py            ← Celery app definition — created manually
│   └── settings/
│       ├── base.py          ← shared settings including all CELERY_* config
│       ├── development.py   ← may override CELERY_TASK_ALWAYS_EAGER=True
│       └── production.py
├── apps/
│   ├── accounts/
│   │   ├── apps.py          ← registers signals in ready()
│   │   ├── models.py
│   │   ├── signals.py       ← dispatches tasks via transaction.on_commit
│   │   └── tasks.py         ← all account-related Celery tasks
│   ├── jobs/
│   │   ├── models.py
│   │   └── tasks.py
│   ├── notifications/
│   │   └── tasks.py
│   └── ai/
│       └── tasks.py
└── requirements.txt
```

**Rule:** Every Django app that owns background work gets its own `tasks.py`. Celery's `autodiscover_tasks()` finds them automatically as long as the app is listed in `INSTALLED_APPS`.

---

## 4. Core Setup Files {#setup}

### File 1: `myproject/celery.py`

Create this file manually — Django does not generate it.

```python
import os
from celery import Celery

# Tell Python which Django settings module to use before the Celery app is created.
# Without this, importing Django models inside tasks will fail.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings.base")

# Create the Celery application instance.
# The string "myproject" is the app name — it appears in task names and log output.
app = Celery("myproject")

# Pull Celery configuration from Django's settings.py.
# namespace="CELERY" means every setting in settings.py that starts with
# CELERY_ is treated as a Celery config key.
# Example: CELERY_BROKER_URL → broker_url internally.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Scan all apps in INSTALLED_APPS and auto-import their tasks.py files.
# Without this, you'd have to manually import every tasks.py.
app.autodiscover_tasks()
```

### File 2: `myproject/__init__.py`

Add these two lines to the existing `__init__.py` (create it if missing):

```python
# This forces the Celery app to be loaded whenever Django starts.
# Without this, @shared_task decorators on tasks may not register correctly
# because the Celery app hasn't been initialized before the worker
# starts consuming tasks.
from .celery import app as celery_app

__all__ = ("celery_app",)
```

**Why both files are required:** `celery.py` creates and configures the app. `__init__.py` ensures it's imported into Django's startup sequence. Skipping either one causes subtle, hard-to-debug failures in production.

---

## 5. Settings Reference {#settings}

All Celery settings live in `settings.py` (or `settings/base.py`) prefixed with `CELERY_`.

```python
# ─────────────────────────────────────────────────────────────────
# BROKER — where queued tasks are stored until a worker picks them up
# ─────────────────────────────────────────────────────────────────

# Redis DB 0 is dedicated to the Celery broker.
# Never share this DB with the Django cache — eviction policies conflict.
CELERY_BROKER_URL = "redis://localhost:6379/0"

# In production with password auth:
# CELERY_BROKER_URL = "redis://:your_password@redis-host:6379/0"

# In production with TLS:
# CELERY_BROKER_URL = "rediss://:your_password@redis-host:6380/0"

# Retry connecting to the broker on startup instead of crashing immediately.
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BROKER_CONNECTION_RETRY = True
CELERY_BROKER_CONNECTION_MAX_RETRIES = 10  # give up after 10 attempts

# ─────────────────────────────────────────────────────────────────
# RESULT BACKEND — where task outcomes are stored
# ─────────────────────────────────────────────────────────────────

# "django-db" stores results in a Django-managed table via django-celery-results.
# This lets you query task results using the Django ORM.
# Requires: django_celery_results in INSTALLED_APPS + python manage.py migrate
CELERY_RESULT_BACKEND = "django-db"

# Alternative: store in Redis (faster reads, but no ORM access, and results are lost on Redis restart unless persistence is on)
# CELERY_RESULT_BACKEND = "redis://localhost:6379/2"

# Delete stored results after this many seconds to prevent DB/Redis bloat.
# 86400 = 1 day. Adjust based on how long you need to query results.
CELERY_RESULT_EXPIRES = 86400

# ─────────────────────────────────────────────────────────────────
# SERIALIZATION — how task arguments and results are encoded
# ─────────────────────────────────────────────────────────────────

# ALWAYS use JSON. Never use pickle — pickle allows arbitrary code execution
# and is a critical security vulnerability if the broker is compromised.
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"

# ─────────────────────────────────────────────────────────────────
# TIMEZONE — all scheduled tasks use this timezone
# ─────────────────────────────────────────────────────────────────

CELERY_TIMEZONE = "UTC"
CELERY_ENABLE_UTC = True  # store all datetimes in UTC internally

# ─────────────────────────────────────────────────────────────────
# TASK BEHAVIOR
# ─────────────────────────────────────────────────────────────────

# Emit a STARTED event when a worker begins executing a task.
# Without this, a task goes from PENDING directly to SUCCESS/FAILURE —
# you can't tell whether it's running or just queued.
CELERY_TASK_TRACK_STARTED = True

# Hard time limit (seconds). After this, the worker PROCESS is killed with SIGKILL.
# The task is interrupted immediately — no cleanup is possible.
# Use soft_time_limit to handle cleanup before this fires.
CELERY_TASK_TIME_LIMIT = 30 * 60       # 30 minutes

# Soft time limit (seconds). Raises SoftTimeLimitExceeded inside the task.
# Use this to catch the exception, clean up, and exit gracefully
# before the hard kill arrives.
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes

# How many tasks each worker prefetches before processing.
# Default is 4 (CPU count). For long-running tasks, set to 1.
# With a high value, one slow task blocks the other prefetched tasks
# from being picked up by other workers.
CELERY_WORKER_PREFETCH_MULTIPLIER = 1

# Restart the worker child process after this many tasks.
# Prevents gradual memory leaks in workers that run continuously.
# 1000 is a reasonable default — tune based on your task memory usage.
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000

# ─────────────────────────────────────────────────────────────────
# BEAT SCHEDULER — for periodic tasks
# ─────────────────────────────────────────────────────────────────

# Use the database scheduler so schedules are stored in Django DB
# and editable via Django Admin without redeploying code.
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# ─────────────────────────────────────────────────────────────────
# INSTALLED APPS — required additions
# ─────────────────────────────────────────────────────────────────

INSTALLED_APPS = [
    # ... your existing apps ...
    "django_celery_beat",      # adds PeriodicTask, CrontabSchedule, etc. to admin
    "django_celery_results",   # adds TaskResult model to DB
]
```

### Run These Migrations After Editing INSTALLED_APPS

```bash
python manage.py migrate django_celery_beat
python manage.py migrate django_celery_results
```

---

## 6. Writing Tasks {#writing-tasks}

### Always Use `@shared_task`

```python
# apps/notifications/tasks.py
from celery import shared_task
```

Use `@shared_task` instead of `@app.task`. `@shared_task` doesn't require a direct import of the Celery app instance. This means:
- Tasks can be written without circular import issues
- The same task module can be used across different Celery apps (e.g. in tests)
- If the Celery app hasn't been created yet when the module loads, `@shared_task` will bind to the app when it is eventually created

### Always Import Models Inside Task Body

```python
# ❌ WRONG — causes AppRegistryNotReady error
from apps.accounts.models import User   # module-level import

@shared_task
def send_welcome_email(user_id: int):
    user = User.objects.get(id=user_id)

# ✅ CORRECT — import inside the function body
@shared_task
def send_welcome_email(user_id: int):
    from apps.accounts.models import User   # safe: Django is fully loaded by now
    user = User.objects.get(id=user_id)
```

**Why:** When Celery workers start, they import `tasks.py` files before Django's app registry is fully initialized. Module-level model imports fail at that point. Importing inside the function body defers the import until the task actually runs, at which point Django is fully ready.

### Always Pass IDs, Never Model Instances

```python
# ❌ WRONG — User instance is not JSON-serializable
send_welcome_email.delay(user=user_instance)

# ✅ CORRECT — pass the ID, fetch the model inside the task
send_welcome_email.delay(user_id=user.id)
```

**Why:** Task arguments are serialized to JSON and stored in the broker. Django model instances cannot be serialized to JSON. Even if they could, by the time the worker runs the task, the object's state may be stale. Always fetch fresh data inside the task.

### Minimal Task

```python
@shared_task
def send_welcome_email(user_id: int) -> str:
    from apps.accounts.models import User
    from apps.email.services import send_email

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        # Don't raise — raising marks the task as FAILURE and may trigger retries.
        # For non-critical tasks, log and return a descriptive value.
        import logging
        logging.getLogger(__name__).error(
            f"send_welcome_email: User {user_id} not found — skipping"
        )
        return f"skipped:user_not_found:{user_id}"

    send_email(
        to=user.email,
        subject="Welcome to Careerly",
        template="emails/welcome.html",
        context={"user": user},
    )
    return f"sent:{user.email}"
```

### Full Task with All Options

```python
@shared_task(
    # bind=True injects the task instance as the first argument (self).
    # Required for: self.retry(), self.request.id, self.request.retries
    bind=True,

    # Explicit task name. Default is "apps.notifications.tasks.send_welcome_email".
    # Use explicit names to avoid breakage if you rename files or move tasks.
    name="notifications.send_welcome_email",

    # Maximum number of retry attempts.
    # After max_retries, MaxRetriesExceededError is raised and the task is FAILURE.
    max_retries=3,

    # Default delay (seconds) between retries when using self.retry() without countdown.
    default_retry_delay=60,

    # Automatically call self.retry() if any of these exception types are raised.
    # Without this, you must call self.retry() manually in the except block.
    autoretry_for=(ConnectionError, TimeoutError),

    # Exponential backoff: each retry waits 2^n * base_delay seconds.
    # Retry 1: ~2s, Retry 2: ~4s, Retry 3: ~8s (with jitter applied on top)
    retry_backoff=True,

    # Maximum backoff delay in seconds. Prevents retries from waiting too long.
    retry_backoff_max=600,  # cap at 10 minutes

    # Add random jitter to backoff delays.
    # Prevents all retrying tasks from hammering the same external service simultaneously.
    retry_jitter=True,

    # Soft time limit in seconds. Raises SoftTimeLimitExceeded inside the task.
    # Gives the task a chance to clean up before the hard kill.
    soft_time_limit=120,

    # Don't store the return value in the result backend.
    # Use for fire-and-forget tasks to reduce DB/Redis writes.
    ignore_result=True,

    # Rate limit per worker process. "100/h" = max 100 executions per hour per worker.
    # Other formats: "10/m" (per minute), "1/s" (per second)
    rate_limit="100/h",

    # Default queue for this task. Can be overridden per-call with apply_async(queue=...).
    queue="notifications",
)
def send_welcome_email(self, user_id: int) -> str:
    from celery.exceptions import SoftTimeLimitExceeded
    from apps.accounts.models import User
    from apps.email.services import send_email
    import logging

    logger = logging.getLogger(__name__)

    try:
        user = User.objects.get(id=user_id)
        send_email(to=user.email, subject="Welcome", template="emails/welcome.html")
        return f"sent:{user.email}"

    except SoftTimeLimitExceeded:
        # This fires 120 seconds into execution.
        # Clean up any open resources (file handles, DB connections, HTTP sessions).
        # The hard kill (SIGKILL) is NOT coming unless you also have time_limit set.
        logger.warning(f"send_welcome_email soft timeout for user {user_id}")
        return f"timeout:user:{user_id}"

    except (ConnectionError, TimeoutError) as exc:
        # autoretry_for handles this automatically, but you can override behavior:
        raise self.retry(exc=exc, countdown=60)

    except User.DoesNotExist:
        # User doesn't exist — retrying will never fix this. Don't retry.
        logger.error(f"User {user_id} not found — task will not retry")
        return f"skipped:not_found:{user_id}"

    except Exception as exc:
        # Unexpected error — log with full context before retrying
        logger.exception(f"Unexpected error in send_welcome_email for user {user_id}")
        raise self.retry(exc=exc)
```

---

## 7. Calling Tasks {#calling-tasks}

### `.delay()` — Simplest Call

```python
# Enqueues the task with the given arguments.
# Returns an AsyncResult — the task's "receipt".
result = send_welcome_email.delay(user_id=user.id)
print(result.id)     # UUID string, e.g. "3ad2b7c4-1234-..."
print(result.state)  # "PENDING" — it just got queued
```

`.delay(*args, **kwargs)` is shorthand for `.apply_async(args=args, kwargs=kwargs)`.

### `.apply_async()` — Full Control

```python
from datetime import datetime, timezone, timedelta

result = send_welcome_email.apply_async(
    # Positional arguments to pass to the task function — must be a list
    args=[],

    # Keyword arguments — must be a dict
    kwargs={"user_id": user.id},

    # Run after this many seconds from now.
    # Use this OR eta — not both.
    countdown=30,

    # Run at this specific UTC datetime.
    eta=datetime(2025, 6, 1, 9, 0, tzinfo=timezone.utc),

    # Which queue to put this task in.
    # Overrides the task's default queue and CELERY_TASK_ROUTES.
    queue="high_priority",

    # Discard the task entirely if it hasn't started within this many seconds.
    # Useful for time-sensitive tasks that are useless if delayed.
    expires=3600,

    # Custom task ID. Must be globally unique.
    # Useful for deduplication — e.g. one email per user registration.
    task_id=f"welcome-{user.id}",

    # Task to run on SUCCESS of this task.
    # Receives this task's return value as its first argument.
    link=log_email_sent.s(user_id=user.id),

    # Task to run on FAILURE of this task.
    link_error=handle_email_failure.s(user_id=user.id),

    # Priority (0 = highest, 9 = lowest). Broker must support priority queues.
    priority=3,

    # Arbitrary metadata attached to the task message.
    # Accessible inside the task via self.request.headers.
    headers={"triggered_by": "registration_flow", "environment": "production"},
)
```

### Signature `.s()` — For Chains and Groups

A signature is a lazy, serializable representation of a task call. It doesn't execute the task — it describes one.

```python
# Create a signature (no execution yet)
sig = send_welcome_email.s(user_id=user.id)

# Execute it later
sig.delay()
sig.apply_async(countdown=10, queue="emails")

# Immutable signature — si() ignores any result passed in from a chain
sig_immutable = send_welcome_email.si(user_id=user.id)
```

### Synchronous Execution — Testing Only

```python
# Runs the task immediately in the current process.
# Blocks until the task finishes. Never use in production.
result = send_welcome_email.apply(kwargs={"user_id": user.id})
print(result.result)   # return value
print(result.state)    # "SUCCESS"
```

---

## 8. Task States & Results {#states}

### All States

| State | When It Occurs |
|---|---|
| `PENDING` | Task was enqueued. No worker has picked it up yet. Also the default state for unknown task IDs. |
| `RECEIVED` | Worker received the task from the broker. (Not always emitted — depends on config.) |
| `STARTED` | Worker began executing the task. Only emitted if `CELERY_TASK_TRACK_STARTED = True`. |
| `SUCCESS` | Task function returned normally. Return value is stored. |
| `FAILURE` | Task raised an unhandled exception. Exception and traceback are stored. |
| `RETRY` | Task raised an exception and `self.retry()` was called. A new attempt is scheduled. |
| `REVOKED` | Task was explicitly cancelled via `.revoke()` before or during execution. |

### Querying Task State

```python
from celery.result import AsyncResult

# Reconstruct from a previously stored task ID
result = AsyncResult("3ad2b7c4-1234-5678-abcd-ef0123456789")

# State string
print(result.state)         # "SUCCESS", "PENDING", "FAILURE", etc.

# Return value (only populated when state == "SUCCESS")
print(result.result)

# Exception (only populated when state == "FAILURE")
if result.state == "FAILURE":
    exc = result.result          # the exception instance
    tb = result.traceback        # full traceback as a string
    print(type(exc).__name__)    # e.g. "ConnectionError"

# Block until the task completes — raises TimeoutError if not done in time
value = result.get(timeout=30)

# Non-blocking check
if result.ready():           # True if SUCCESS or FAILURE
    if result.successful():  # True only if SUCCESS
        value = result.result
    elif result.failed():    # True only if FAILURE
        error = result.result

# Revoke a pending task (prevent it from running)
result.revoke()

# Revoke and kill if already running
result.revoke(terminate=True, signal="SIGKILL")

# Remove result from backend (frees storage)
result.forget()
```

### Querying via ORM (django-celery-results)

```python
from django_celery_results.models import TaskResult
from django.utils import timezone
from datetime import timedelta

# Fetch a specific result
tr = TaskResult.objects.get(task_id="3ad2b7c4-...")
tr.status         # "SUCCESS"
tr.result         # JSON string of return value — parse with json.loads(tr.result)
tr.date_created   # when it was first recorded
tr.date_done      # when it completed
tr.traceback      # None or traceback string
tr.task_name      # "notifications.send_welcome_email"
tr.task_args      # JSON string of positional args
tr.task_kwargs    # JSON string of keyword args
tr.worker         # which worker executed it, e.g. "celery@hostname"

# All failed tasks in the last 24 hours
failed = TaskResult.objects.filter(
    status="FAILURE",
    date_done__gte=timezone.now() - timedelta(hours=24)
).order_by("-date_done")

# Count by status
from django.db.models import Count
TaskResult.objects.values("status").annotate(count=Count("id"))
```

---

## 9. Retry Logic {#retries}

### Automatic Retries — `autoretry_for`

```python
@shared_task(
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError, requests.HTTPError),
    max_retries=5,
    retry_backoff=True,       # exponential: 2s, 4s, 8s, 16s, 32s (approximate)
    retry_backoff_max=300,    # cap at 5 minutes
    retry_jitter=True,        # randomize to avoid synchronized retries
)
def call_external_api(self, payload: dict) -> dict:
    import requests
    response = requests.post(
        "https://api.example.com/endpoint",
        json=payload,
        timeout=10  # always set a timeout on HTTP calls
    )
    response.raise_for_status()  # raises HTTPError for 4xx/5xx
    return response.json()
```

### Manual Retries — Full Control

```python
@shared_task(bind=True, max_retries=5)
def call_external_api(self, payload: dict) -> dict:
    import requests
    import logging
    logger = logging.getLogger(__name__)

    try:
        response = requests.post("https://api.example.com/endpoint", json=payload, timeout=10)
        response.raise_for_status()
        return response.json()

    except requests.Timeout as exc:
        # Network timeout — retry after 60 seconds
        logger.warning(f"Timeout on attempt {self.request.retries + 1} of {self.max_retries + 1}")
        raise self.retry(exc=exc, countdown=60)

    except requests.HTTPError as exc:
        status = exc.response.status_code
        if status == 429:
            # Rate limited. Retry after the Retry-After header value, or 5 minutes.
            retry_after = int(exc.response.headers.get("Retry-After", 300))
            raise self.retry(exc=exc, countdown=retry_after)
        elif status >= 500:
            # Server error — retry with exponential backoff
            countdown = (2 ** self.request.retries) * 30  # 30s, 60s, 120s, 240s, 480s
            raise self.retry(exc=exc, countdown=countdown)
        else:
            # 4xx client error — our fault, retrying won't fix it
            logger.error(f"Client error {status} — not retrying: {exc}")
            raise  # re-raise, task is marked FAILURE immediately

    except Exception as exc:
        if self.request.retries >= self.max_retries:
            # About to exhaust retries — log before giving up
            logger.error(
                f"call_external_api exhausted {self.max_retries} retries. "
                f"Payload: {payload}. Final error: {exc}"
            )
            raise  # raises MaxRetriesExceededError, task marked FAILURE
        raise self.retry(exc=exc, countdown=60)
```

### What Happens at Max Retries

When `self.retry()` is called and `self.request.retries >= max_retries`, Celery raises `MaxRetriesExceededError`. The task transitions to `FAILURE` state. The original exception (passed via `exc=`) is stored as the result. Monitor FAILURE tasks with Sentry or Flower.

---

## 10. Time Limits {#time-limits}

```python
from celery.exceptions import SoftTimeLimitExceeded

@shared_task(
    # Soft limit: raises SoftTimeLimitExceeded inside the task after N seconds.
    # The task keeps running after this exception unless you catch and return.
    soft_time_limit=25 * 60,   # 25 minutes

    # Hard limit: sends SIGKILL to the worker process after N seconds.
    # The task is terminated immediately — no further code runs.
    # Set this higher than soft_time_limit to allow time to clean up.
    time_limit=30 * 60,        # 30 minutes
)
def parse_resume(resume_id: int):
    from apps.resumes.models import Resume
    import logging
    logger = logging.getLogger(__name__)

    resume = Resume.objects.get(id=resume_id)
    resume.status = "PROCESSING"
    resume.save(update_fields=["status", "updated_at"])

    try:
        result = run_ai_parsing(resume.file.path)  # potentially long
        resume.parsed_data = result
        resume.status = "COMPLETE"
        resume.save(update_fields=["parsed_data", "status", "updated_at"])
        return f"complete:{resume_id}"

    except SoftTimeLimitExceeded:
        # We have up to (time_limit - soft_time_limit) = 5 minutes to clean up.
        resume.status = "TIMED_OUT"
        resume.save(update_fields=["status", "updated_at"])
        logger.error(f"parse_resume timed out for resume {resume_id}")
        return f"timed_out:{resume_id}"
```

**Important nuance:** The hard `time_limit` kills the **worker child process**, not just the task. With `CELERY_WORKER_MAX_TASKS_PER_CHILD=1`, each task gets a fresh child process, so a kill doesn't affect other running tasks. Without that setting, a hard kill could interrupt other tasks being handled by the same child.

---

## 11. Queues & Routing {#queues}

### Why Multiple Queues Matter

A single queue means a 10-minute AI task blocks 500 quick email tasks behind it in line. Routing tasks to dedicated queues lets you run specialized workers for each category.

### Queue Definitions in Settings

```python
from kombu import Queue

CELERY_TASK_QUEUES = (
    Queue("default"),        # catch-all for unrouted tasks
    Queue("high_priority"),  # time-sensitive: notifications, confirmations
    Queue("emails"),         # all outbound email tasks
    Queue("ai_tasks"),       # AI inference, resume parsing, scoring
    Queue("low_priority"),   # reports, exports, non-urgent processing
)

CELERY_TASK_DEFAULT_QUEUE = "default"

# Route tasks automatically based on module path patterns
CELERY_TASK_ROUTES = {
    # All tasks in any notifications tasks.py → high_priority
    "apps.notifications.tasks.*":          {"queue": "high_priority"},

    # All tasks in apps/ai/tasks.py → ai_tasks
    "apps.ai.tasks.*":                     {"queue": "ai_tasks"},

    # Specific named tasks → emails
    "apps.accounts.tasks.send_welcome_email":       {"queue": "emails"},
    "apps.accounts.tasks.send_password_reset_email": {"queue": "emails"},

    # All report tasks → low_priority
    "apps.reports.tasks.*":                {"queue": "low_priority"},
}
```

### Override Queue Per Call

```python
# Force a specific call to a specific queue regardless of routing config
send_welcome_email.apply_async(
    kwargs={"user_id": user.id},
    queue="high_priority"
)
```

### Start Workers Per Queue

```bash
# Default worker — 4 concurrent processes, handles default + high_priority
celery -A myproject worker -Q default,high_priority -c 4 -n default@%h --loglevel=info

# AI worker — 1 process (GPU-bound or high memory — no benefit to more processes)
celery -A myproject worker -Q ai_tasks -c 1 -n ai@%h --loglevel=info

# Email worker — 8 processes (I/O-bound: mostly waiting for SMTP)
celery -A myproject worker -Q emails -c 8 -n email@%h --loglevel=info

# Low priority worker — 2 processes (not urgent)
celery -A myproject worker -Q low_priority -c 2 -n reports@%h --loglevel=info
```

**Concurrency `-c` guidelines:**
- I/O-bound tasks (HTTP calls, email, DB writes): `num_cpu_cores × 4`
- CPU-bound tasks (compression, encoding, data processing): `num_cpu_cores`
- GPU/memory-heavy (AI inference): `1` per worker instance

---

## 12. Periodic Tasks — Celery Beat {#beat}

Beat is a **separate process** that reads a schedule and enqueues tasks at the right times. It does not execute tasks — it only enqueues them.

### Define Schedule in Settings (Static Schedule)

```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # Key is a unique identifier for this scheduled task
    "expire-old-job-postings": {
        "task": "apps.jobs.tasks.expire_old_postings",
        # crontab(hour=0, minute=0) = daily at midnight UTC
        "schedule": crontab(hour=0, minute=0),
        "args": (),           # positional args to pass to the task
        "kwargs": {},         # keyword args to pass to the task
        "options": {
            "queue": "low_priority",
            "expires": 3600,  # discard if not run within 1 hour (prevents backlog)
        },
    },

    "send-daily-digest-emails": {
        "task": "apps.notifications.tasks.send_daily_digest",
        "schedule": crontab(hour=8, minute=0),
    },

    "refresh-recommendation-scores": {
        "task": "apps.ai.tasks.refresh_all_scores",
        "schedule": crontab(minute="*/30"),  # every 30 minutes
    },

    "retry-failed-webhooks": {
        "task": "apps.payments.tasks.retry_failed_webhooks",
        "schedule": 60.0,   # float = run every N seconds
    },

    "weekly-employer-report": {
        "task": "apps.reports.tasks.send_employer_weekly_report",
        "schedule": crontab(hour=9, minute=0, day_of_week="monday"),
    },

    "monthly-cleanup": {
        "task": "apps.cleanup.tasks.purge_old_data",
        "schedule": crontab(hour=2, minute=0, day_of_month=1),  # 1st of each month at 2am
    },
}
```

### Crontab Reference

```python
from celery.schedules import crontab

crontab()                                        # every minute
crontab(minute="*/15")                           # every 15 minutes
crontab(minute=0, hour="*/2")                    # every 2 hours on the hour
crontab(minute=0, hour=0)                        # daily at midnight
crontab(minute=0, hour=8)                        # daily at 8am
crontab(minute=0, hour=0, day_of_week="monday")  # every monday at midnight
crontab(minute=0, hour=9, day_of_week="mon,wed,fri")
crontab(minute=0, hour=0, day_of_month=1)        # 1st of every month
crontab(minute=0, hour=0, day_of_month=1, month_of_year=1)  # Jan 1st each year
60.0                                             # every 60 seconds
timedelta(hours=2)                               # every 2 hours
```

### Dynamic Schedule via Django Admin

After migrating `django-celery-beat`, go to **Django Admin → Periodic Tasks**. Create, edit, enable, disable schedules without touching code. Changes take effect on the next Beat tick (usually within 5 seconds with the database scheduler).

### Starting Beat

```bash
# Beat MUST run as a separate process — never embed it in a worker
celery -A myproject beat \
  --loglevel=info \
  --scheduler django_celery_beat.schedulers:DatabaseScheduler \
  --logfile=/var/log/celery/beat.log \
  --pidfile=/var/run/celery/beat.pid
```

**Critical rule:** Run exactly **one Beat process** at all times. Two Beat processes will double-enqueue every task on every tick.

---

## 13. Task Chaining, Groups & Chords {#chains}

### Chain — Sequential Pipeline

Each task's return value is passed as the first argument to the next task.

```python
from celery import chain

# Step 1: parse_resume(resume_id=42) → returns parsed_data dict
# Step 2: score_resume(parsed_data) → returns score float
# Step 3: notify_employer(score, job_id=10) → sends notification
pipeline = chain(
    parse_resume.s(resume_id=42),
    score_resume.s(),                 # receives output of parse_resume as first arg
    notify_employer.s(job_id=10),     # receives output of score_resume as first arg
)
result = pipeline.delay()

# If you don't want to pass the previous result forward, use .si() (immutable):
chain(
    parse_resume.s(resume_id=42),
    notify_user.si(user_id=5, message="Resume parsed"),  # ignores parse output
)
```

### Group — Parallel Execution

All tasks run simultaneously. Waits for all to complete.

```python
from celery import group

# Send emails to 1000 users in parallel across all available workers
job = group(
    send_notification_email.s(user_id=uid)
    for uid in user_ids
)
result = job.delay()

# Get all results (blocks until all complete or timeout)
results = result.get(timeout=300)  # list of return values, in order
```

### Chord — Parallel Then Callback

A group of parallel tasks followed by a single callback that fires after all complete.

```python
from celery import chord, group

result = chord(
    # Header: these all run in parallel
    group(
        process_application.s(application_id=app_id)
        for app_id in application_ids
    ),
    # Body: callback runs after ALL header tasks complete
    # Receives list of all header return values as first argument
    compile_batch_report.s(batch_id=batch_id),
)()
```

**Warning:** Chords require the result backend to be configured and working. They will not work if `ignore_result=True` is set on any of the header tasks. The chord waits for results from every task in the header group.

---

## 14. Django Integration & Signals {#signals}

### The Most Important Pattern: `transaction.on_commit()`

**The problem without it:**

```python
# ❌ WRONG — race condition
def create_application(user, job):
    app = Application.objects.create(user=user, job=job)
    notify_employer.delay(app.id)
    # Django's ORM creates records inside a transaction.
    # That transaction may not have committed to the DB yet when .delay() fires.
    # The Celery worker starts immediately, calls Application.objects.get(id=app.id),
    # and gets DoesNotExist because the row isn't visible yet in the DB.
```

**The fix:**

```python
from django.db import transaction

# ✅ CORRECT — task runs after commit
def create_application(user, job):
    app = Application.objects.create(user=user, job=job)
    # on_commit() registers a callback that fires AFTER the outermost
    # transaction commits to the database.
    # If the transaction rolls back, the callback is NOT called.
    transaction.on_commit(lambda: notify_employer.delay(app.id))
    return app
```

### Dispatching from Django Signals

Signals also fire inside the model's save transaction. Use `on_commit` here too.

```python
# apps/accounts/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from .models import User

@receiver(post_save, sender=User)
def on_user_created(sender, instance, created, **kwargs):
    if created:
        # post_save fires inside User.save()'s transaction.
        # Using on_commit ensures the task runs after the commit.
        transaction.on_commit(
            lambda: send_welcome_email.delay(user_id=instance.id)
        )
```

```python
# apps/accounts/apps.py — register signals on startup
from django.apps import AppConfig

class AccountsConfig(AppConfig):
    name = "apps.accounts"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        # Import the signals module to register all @receiver decorators
        import apps.accounts.signals  # noqa: F401
```

```python
# apps/accounts/__init__.py
default_app_config = "apps.accounts.apps.AccountsConfig"
```

---

## 15. Running Workers {#running}

### Development Setup (4 Terminals)

```bash
# Terminal 1: Redis
redis-server

# Terminal 2: Celery worker (all queues, verbose logging)
celery -A myproject worker -l debug

# Terminal 3: Beat (only if you have periodic tasks)
celery -A myproject beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler

# Terminal 4: Flower monitoring UI (optional)
pip install flower
celery -A myproject flower --port=5555
# Visit http://localhost:5555
```

### All Worker CLI Options

```bash
celery -A myproject worker \
  --queues=default,emails \             # comma-separated queues to consume
  --concurrency=4 \                     # number of concurrent worker processes
  --hostname=worker1@%h \              # worker name (%h = hostname, %n = process)
  --loglevel=info \                     # debug | info | warning | error | critical
  --logfile=/var/log/celery/worker.log \
  --pidfile=/var/run/celery/worker.pid \
  --max-tasks-per-child=1000 \          # restart child process after N tasks
  --max-memory-per-child=200000 \       # restart if child exceeds N KB of memory
  --without-heartbeat \                 # disable heartbeat for low-traffic setups
  --without-gossip                      # disable worker-to-worker gossip
```

### Production: Supervisord Configuration

```ini
; /etc/supervisor/conf.d/celery.conf

[program:celery_default]
command=/home/app/venv/bin/celery -A myproject worker -Q default,high_priority -c 4 -n default@%%h --loglevel=info --logfile=/var/log/celery/default.log
directory=/home/app/myproject
user=appuser
numprocs=1
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=600       ; wait up to 600s for tasks to finish before killing
killasgroup=true
priority=998
stdout_logfile=/var/log/celery/default.out
stderr_logfile=/var/log/celery/default.err

[program:celery_ai]
command=/home/app/venv/bin/celery -A myproject worker -Q ai_tasks -c 1 -n ai@%%h --loglevel=info --logfile=/var/log/celery/ai.log
directory=/home/app/myproject
user=appuser
numprocs=1
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=600
killasgroup=true
priority=998
stdout_logfile=/var/log/celery/ai.out
stderr_logfile=/var/log/celery/ai.err

[program:celery_emails]
command=/home/app/venv/bin/celery -A myproject worker -Q emails -c 8 -n email@%%h --loglevel=info
directory=/home/app/myproject
user=appuser
numprocs=1
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=300
killasgroup=true
priority=998
stdout_logfile=/var/log/celery/emails.out
stderr_logfile=/var/log/celery/emails.err

[program:celery_beat]
; IMPORTANT: Only one Beat process — ever.
; Running two Beat processes doubles every scheduled task.
command=/home/app/venv/bin/celery -A myproject beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler --logfile=/var/log/celery/beat.log --pidfile=/var/run/celery/beat.pid
directory=/home/app/myproject
user=appuser
numprocs=1
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=60
killasgroup=true
priority=999           ; start Beat last
stdout_logfile=/var/log/celery/beat.out
stderr_logfile=/var/log/celery/beat.err

[group:celery]
programs=celery_default,celery_ai,celery_emails,celery_beat
```

```bash
# Apply supervisord config
sudo supervisorctl reread
sudo supervisorctl update

# Start all
sudo supervisorctl start celery:*

# Check status
sudo supervisorctl status

# Restart a specific worker (e.g. after code deploy)
sudo supervisorctl restart celery_default

# Graceful shutdown (waits for running tasks to finish)
sudo supervisorctl stop celery:*
```

---

## 16. Monitoring {#monitoring}

### Flower — Web UI

```bash
pip install flower

# Basic
celery -A myproject flower --port=5555

# With HTTP basic auth (recommended for production)
celery -A myproject flower --port=5555 --basic_auth=admin:strongpassword

# Persistent task history (stored in a local DB)
celery -A myproject flower --port=5555 --persistent=True --db=/var/lib/flower/flower.db
```

Flower shows:
- Active, queued, and completed tasks in real time
- Per-worker status and throughput
- Task failure rates and tracebacks
- Queue lengths per queue
- Task history with filtering

### CLI Commands

```bash
# List all currently executing tasks across all workers
celery -A myproject inspect active

# List tasks scheduled for future execution (ETA/countdown)
celery -A myproject inspect scheduled

# List tasks reserved (prefetched by a worker but not yet running)
celery -A myproject inspect reserved

# Show statistics for each worker (throughput, task counts, etc.)
celery -A myproject inspect stats

# List all task names registered on workers
celery -A myproject inspect registered

# Ping all workers — response means worker is alive
celery -A myproject inspect ping

# Revoke a specific task by ID
celery -A myproject control revoke <task-id>

# Revoke and kill if running
celery -A myproject control revoke <task-id> --terminate

# Discard all queued tasks (IRREVERSIBLE — never use in production without backup)
celery -A myproject purge
```

### Sentry Integration

```bash
pip install sentry-sdk
```

```python
# settings/base.py
import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.redis import RedisIntegration

sentry_sdk.init(
    dsn=env("SENTRY_DSN"),
    integrations=[
        DjangoIntegration(),
        CeleryIntegration(
            monitor_beat_tasks=True,    # track periodic task execution in Sentry Crons
            propagate_traces=True,      # link web request traces to task traces
        ),
        RedisIntegration(),
    ],
    traces_sample_rate=0.1,   # sample 10% of transactions for performance monitoring
    environment=env("ENVIRONMENT", default="production"),
)
```

With `CeleryIntegration`, every unhandled task exception is automatically captured in Sentry with full context including task name, arguments, retry count, and worker hostname.

---

## 17. Testing {#testing}

### Option A: Eager Mode (Synchronous Execution)

```python
# settings/test.py
CELERY_TASK_ALWAYS_EAGER = True
# Re-raise task exceptions instead of storing them
CELERY_TASK_EAGER_PROPAGATES = True
```

Tasks run synchronously in the test process. No worker or broker needed. Use this for most unit tests.

### Option B: Mock `.delay()` — Test That Tasks Are Enqueued

```python
from unittest.mock import patch, call
from django.test import TestCase

class UserRegistrationTest(TestCase):
    @patch("apps.notifications.tasks.send_welcome_email.delay")
    def test_welcome_email_is_enqueued_after_registration(self, mock_delay):
        response = self.client.post("/api/v1/auth/register/", {
            "email": "test@example.com",
            "password": "SecurePass123!",
        }, content_type="application/json")

        self.assertEqual(response.status_code, 201)
        user_id = response.data["id"]

        # Assert the task was enqueued exactly once with the correct argument
        mock_delay.assert_called_once_with(user_id=user_id)
```

### Option C: Test the Task Function Directly

```python
from django.test import TestCase
from apps.notifications.tasks import send_welcome_email

class SendWelcomeEmailTaskTest(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="pass"
        )

    def test_returns_sent_on_success(self):
        # Call the function directly — no .delay(), no worker
        result = send_welcome_email(user_id=self.user.id)
        self.assertEqual(result, f"sent:{self.user.email}")

    def test_returns_skipped_when_user_not_found(self):
        result = send_welcome_email(user_id=99999)
        self.assertIn("not_found", result)
```

### Option D: Test Chains and Groups

```python
from celery import chain
from unittest.mock import patch

class ResumeParsingPipelineTest(TestCase):
    @patch("apps.ai.tasks.score_resume.delay")
    @patch("apps.resumes.tasks.parse_resume.delay")
    def test_pipeline_tasks_enqueued(self, mock_parse, mock_score):
        trigger_resume_pipeline(resume_id=42)
        mock_parse.assert_called_once_with(resume_id=42)
```

---

## 18. Production Checklist {#production}

- [ ] `CELERY_TASK_SERIALIZER = "json"` — never pickle
- [ ] `CELERY_TASK_ALWAYS_EAGER = False` in production settings (explicitly set)
- [ ] Separate Redis DBs: broker on DB 0, cache on DB 1 — never shared
- [ ] `CELERY_RESULT_EXPIRES` configured to prevent DB/Redis bloat
- [ ] `CELERY_WORKER_PREFETCH_MULTIPLIER = 1` for any queue with long-running tasks
- [ ] `CELERY_WORKER_MAX_TASKS_PER_CHILD` set to prevent memory leaks
- [ ] All workers managed by supervisord or systemd — not started manually
- [ ] Exactly **one Beat process** — enforced by supervisord `numprocs=1`
- [ ] Every task dispatch inside a DB transaction wrapped in `transaction.on_commit()`
- [ ] All models imported inside task function body — never at module level
- [ ] All task arguments are JSON-serializable (IDs, strings, dicts of primitives)
- [ ] Critical tasks have `max_retries`, `autoretry_for`, and `retry_backoff` configured
- [ ] Long-running tasks have `soft_time_limit` and `time_limit` configured
- [ ] Queue routing configured — fast tasks are never blocked by slow tasks
- [ ] Sentry (or equivalent) integrated for worker error tracking
- [ ] Flower (or equivalent) running for operational visibility
- [ ] Worker logs are persistent and rotated (logfile + logrotate)
- [ ] `CELERY_BEAT_SCHEDULE` uses `expires` option on time-sensitive periodic tasks
- [ ] Tasks are idempotent — running a task twice produces the same outcome

---

## 19. Common Errors & Fixes {#errors}

| Error | Root Cause | Fix |
|---|---|---|
| `DoesNotExist` inside task | Task ran before DB transaction committed | Wrap dispatch in `transaction.on_commit()` |
| `AppRegistryNotReady` on worker start | Model imported at module level in tasks.py | Move all imports inside the task function body |
| `kombu.exceptions.EncodeError: Object of type X is not JSON serializable` | Passing a model instance or non-primitive as a task argument | Pass the ID only; fetch model inside the task |
| Task stuck in `PENDING` forever | Worker isn't running, or task was sent to a queue no worker is consuming | Start the correct worker; check `CELERY_TASK_ROUTES` |
| Periodic tasks not running | Two Beat processes running simultaneously | Kill one; `numprocs=1` in supervisord |
| Periodic tasks not running | Beat is running but static schedule wasn't loaded to DB | Run `python manage.py migrate django_celery_beat` |
| `MaxRetriesExceededError` | All retries failed | Log before max retries; investigate root cause in Sentry |
| Workers growing in RAM over hours | Memory leak in long-running tasks | Set `CELERY_WORKER_MAX_TASKS_PER_CHILD` |
| Same task processed twice | Multiple workers + non-idempotent task | Make tasks idempotent; use `task_id` + DB-level deduplication |
| `SoftTimeLimitExceeded` during normal operations | Task is slower than expected | Profile and optimize; increase `soft_time_limit`; or move heavy work to a dedicated queue |
| `chord` callback never fires | `ignore_result=True` on header tasks | Remove `ignore_result` from all tasks in a chord header |
| `celery beat` keeps creating duplicate PeriodicTask entries | `DatabaseScheduler` + static `CELERY_BEAT_SCHEDULE` conflict | Use one or the other — not both |

---

## 20. Quick Reference {#reference}

```bash
# Start worker (all queues)
celery -A myproject worker -l info

# Start worker (specific queues, specific concurrency)
celery -A myproject worker -Q default,emails -c 4 -l info

# Start beat
celery -A myproject beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler

# Monitor
celery -A myproject flower --port=5555

# Inspect
celery -A myproject inspect active
celery -A myproject inspect scheduled
celery -A myproject inspect ping
celery -A myproject inspect stats
```

```python
# Define a task
@shared_task(bind=True, max_retries=3, autoretry_for=(Exception,), retry_backoff=True)
def my_task(self, id: int) -> str:
    from apps.myapp.models import MyModel
    obj = MyModel.objects.get(id=id)
    # do work
    return f"done:{id}"

# Enqueue (fire and forget)
my_task.delay(id=42)

# Enqueue with options
my_task.apply_async(kwargs={"id": 42}, countdown=30, queue="emails")

# Always dispatch inside transactions via on_commit
transaction.on_commit(lambda: my_task.delay(id=obj.id))

# Check status
from celery.result import AsyncResult
r = AsyncResult(task_id)
r.state           # PENDING | STARTED | SUCCESS | FAILURE | RETRY | REVOKED
r.result          # return value (SUCCESS) or exception (FAILURE)
r.get(timeout=30) # block until done

# Retry manually
raise self.retry(exc=exc, countdown=60)
```
