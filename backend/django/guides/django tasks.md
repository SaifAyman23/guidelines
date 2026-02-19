# Django Tasks — Definitive Guide

> Django Tasks (via the `django-tasks` package or Django 5.x built-in) provides lightweight background task execution without requiring a message broker. This guide covers everything — installation, configuration, writing tasks, calling tasks, error handling, testing, and production deployment — with no assumptions.

---

## Table of Contents

1. [What Django Tasks Is and When to Use It](#what)
2. [How It Works Under the Hood](#architecture)
3. [Installation](#installation)
4. [Backends — Which One to Use When](#backends)
5. [Configuration](#configuration)
6. [Migrations](#migrations)
7. [Writing Tasks](#writing-tasks)
8. [Calling Tasks](#calling-tasks)
9. [Safe Dispatch — `transaction.on_commit()`](#on-commit)
10. [Task States & Results](#states)
11. [Error Handling](#errors)
12. [Running the Worker](#worker)
13. [Django Admin Integration](#admin)
14. [Testing](#testing)
15. [Organizing Tasks Across Apps](#organizing)
16. [Production Deployment](#production)
17. [Limitations — What Django Tasks Cannot Do](#limitations)
18. [Comparison with Celery](#comparison)
19. [Common Errors & Fixes](#common-errors)
20. [Quick Reference](#reference)

---

## 1. What Django Tasks Is and When to Use It {#what}

Django Tasks is a background task runner built on top of Django's database. It lets you defer work outside the request-response cycle without setting up Redis, a message broker, or a dedicated queue server.

### Use Django Tasks When

- The task is **triggered by a single user action** (registration, form submit, status change)
- The task completes in **under 2 seconds** (single email, one DB write, one push notification)
- **No retry logic is required** — if it fails, logging the error is acceptable
- **No schedule is required** — the task is reactive, not proactive
- You want **minimal infrastructure** — no Redis broker, no Celery workers, just the Django DB

### Do NOT Use Django Tasks When

- The task takes more than 2 seconds (use Celery)
- The task calls an external API that can fail and needs retries (use Celery)
- The task needs to run on a schedule (use Celery Beat)
- The task fans out to many sub-tasks (use Celery group)
- Losing the task on a server restart is unacceptable for business reasons (use Celery — stored in Redis broker)
- You need a monitoring UI for task history (use Celery + Flower)

---

## 2. How It Works Under the Hood {#architecture}

```
Django View (or Signal)
      │
      │  my_task.enqueue(arg)
      ▼
  Django Database ── task_results table
  (task is stored as a row with status=NEW)
      │
      │  Worker polls the table every N seconds
      ▼
  db_worker process
  (SELECT task WHERE status=NEW FOR UPDATE SKIP LOCKED)
  (sets status=RUNNING, executes function, sets status=COMPLETE or FAILED)
      │
      │
  task_results table updated with outcome
```

**Key behaviors:**

- Tasks are stored in the Django database as rows — not in Redis or an external broker.
- The worker uses `SELECT ... FOR UPDATE SKIP LOCKED` — a PostgreSQL and SQLite-compatible pattern that allows multiple worker threads to pull different tasks from the same queue without race conditions.
- There is no broker dependency. The DB is the broker.
- Tasks persist across server restarts (the DB row survives).
- No retry logic is built in. A FAILED task stays FAILED unless your code handles it.

---

## 3. Installation {#installation}

### Django 5.x (built-in, no package needed)

Django 5.x includes background task support natively via `django.tasks`. No package needed — just configure it in settings.

### Django 4.2+ (use `django-tasks` backport)

```bash
pip install django-tasks
```

Add to `requirements.txt`:
```
django-tasks>=0.6
```

Add to `INSTALLED_APPS`:
```python
INSTALLED_APPS = [
    # ... your apps ...
    "django_tasks",
]
```

---

## 4. Backends — Which One to Use When {#backends}

Django Tasks supports three backends. Choosing the wrong one is the most common mistake.

### `DatabaseBackend` — Use in Development and Production

```python
TASKS = {
    "default": {
        "BACKEND": "django_tasks.backends.database.DatabaseBackend",
    }
}
```

**How it works:** Tasks are stored as rows in the `django_tasks_taskresult` table. The worker polls this table with `SELECT ... FOR UPDATE SKIP LOCKED` to pull tasks atomically. Tasks survive server restarts.

**Use this in:** all real environments (development, staging, production).

---

### `ImmediateBackend` — Use in Tests

```python
TASKS = {
    "default": {
        "BACKEND": "django_tasks.backends.immediate.ImmediateBackend",
    }
}
```

**How it works:** When `my_task.enqueue(arg)` is called, the task function is executed **immediately in the same thread**, synchronously, before `enqueue()` returns. No worker process is needed.

**Use this in:** test settings (`settings/test.py`). It makes tests simple — you don't need to start a worker, and tasks run predictably in order.

**Do not use in production.** It executes tasks synchronously in your web workers, which defeats the purpose of background tasks and will slow down responses.

---

### `DummyBackend` — Use in CI or When You Don't Care About Tasks

```python
TASKS = {
    "default": {
        "BACKEND": "django_tasks.backends.dummy.DummyBackend",
    }
}
```

**How it works:** All tasks are silently discarded. `my_task.enqueue(arg)` returns a `TaskResult` object but the function is never called.

**Use this in:** CI pipelines where you're testing code that enqueues tasks, but you only care that the enqueue call happened — not what the task does.

---

## 5. Configuration {#configuration}

### Minimal Configuration (Single Queue)

```python
# settings/base.py
TASKS = {
    "default": {
        "BACKEND": "django_tasks.backends.database.DatabaseBackend",
    }
}
```

### Full Configuration with Multiple Queues

```python
# settings/base.py
TASKS = {
    "default": {
        "BACKEND": "django_tasks.backends.database.DatabaseBackend",
        # Optional: list the queue names this backend handles.
        # If not specified, the backend handles all queues.
        "QUEUES": ["default"],
    },
    "emails": {
        "BACKEND": "django_tasks.backends.database.DatabaseBackend",
        "QUEUES": ["emails"],
    },
    "notifications": {
        "BACKEND": "django_tasks.backends.database.DatabaseBackend",
        "QUEUES": ["notifications"],
    },
}
```

### Test Settings Override

```python
# settings/test.py
from .base import *

TASKS = {
    "default": {
        "BACKEND": "django_tasks.backends.immediate.ImmediateBackend",
    },
    "emails": {
        "BACKEND": "django_tasks.backends.immediate.ImmediateBackend",
    },
    "notifications": {
        "BACKEND": "django_tasks.backends.immediate.ImmediateBackend",
    },
}
```

---

## 6. Migrations {#migrations}

After installing `django-tasks` and adding it to `INSTALLED_APPS`, create the task results table:

```bash
python manage.py migrate django_tasks
```

This creates the `django_tasks_taskresult` table which stores all task records.

**Verify it worked:**

```bash
python manage.py dbshell
```

```sql
\dt django_tasks*
-- Should show: django_tasks_taskresult
```

---

## 7. Writing Tasks {#writing-tasks}

### The `@task()` Decorator

```python
from django_tasks import task
```

`@task()` registers a function as a Django Task. It does not execute the function — it wraps it and makes `.enqueue()` available on the wrapped function.

### Always Import Models Inside the Task Body

```python
# ❌ WRONG — module-level import
from apps.accounts.models import User

@task()
def send_welcome_email(user_id: int):
    user = User.objects.get(id=user_id)

# ✅ CORRECT — import inside the function
@task()
def send_welcome_email(user_id: int):
    from apps.accounts.models import User  # safe: Django is fully loaded when task runs
    user = User.objects.get(id=user_id)
```

**Why:** `tasks.py` files are imported at Django startup. At import time, the app registry may not be fully initialized. Model imports at module level fail with `AppRegistryNotReady`. Importing inside the function body defers the import until the task actually executes — at which point Django is fully loaded.

### Always Pass IDs, Never Model Instances

```python
# ❌ WRONG — model instances are not JSON serializable
send_welcome_email.enqueue(user=user_instance)

# ✅ CORRECT — pass the primary key
send_welcome_email.enqueue(user_id=user.id)
```

**Why:** Task arguments are serialized to JSON and stored in the DB. Django model instances cannot be serialized to JSON. Always pass IDs (integers, UUIDs as strings) and fetch the model inside the task.

### Minimal Task

```python
# apps/accounts/tasks.py
from django_tasks import task

@task()
def send_welcome_email(user_id: int) -> str:
    """
    Send a welcome email to a newly registered user.
    Called after registration — quick, non-critical, no retry needed.
    """
    from apps.accounts.models import User
    from apps.email.services import send_transactional_email
    import logging

    logger = logging.getLogger(__name__)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        # User was deleted before the task ran. Log and move on.
        # Do NOT raise — raising marks the task FAILED.
        logger.warning(f"send_welcome_email: User {user_id} not found — skipping")
        return f"skipped:user_not_found:{user_id}"

    try:
        send_transactional_email(
            to_email=user.email,
            subject="Welcome to Careerly!",
            template="emails/accounts/welcome.html",
            context={
                "user_name": user.get_full_name(),
                "login_url": "https://careerly.com/login",
            },
        )
        logger.info(f"Welcome email sent to user {user_id} ({user.email})")
        return f"sent:{user.email}"

    except Exception as e:
        # Log the error. The task will be marked FAILED.
        # The user can trigger a resend from their account settings.
        logger.error(f"Failed to send welcome email to user {user_id}: {e}", exc_info=True)
        raise  # re-raise so the task is marked FAILED (visible in admin)
```

### Task with Queue Assignment

```python
@task(queue_name="emails")
def send_welcome_email(user_id: int) -> str:
    ...

@task(queue_name="notifications")
def create_in_app_notification(user_id: int, message: str, url: str) -> str:
    ...
```

Workers can be started per queue (covered in [Running the Worker](#worker) section).

### Task Return Values

The return value of the task function is stored in the `TaskResult.result` field as a JSON string. Return simple, JSON-serializable values (strings, dicts, numbers, lists). Do not return model instances.

```python
@task()
def write_audit_log(user_id: int, action: str, metadata: dict) -> dict:
    from apps.audit.models import AuditLog
    log = AuditLog.objects.create(
        user_id=user_id,
        action=action,
        metadata=metadata,
    )
    return {"id": log.id, "created_at": log.created_at.isoformat()}
```

---

## 8. Calling Tasks {#calling-tasks}

### `.enqueue()` — Standard Call

```python
# Enqueue a task — returns a TaskResult immediately
result = send_welcome_email.enqueue(user_id=user.id)

print(result.id)      # UUID of the task record
print(result.status)  # TaskResultStatus.NEW
```

### `.enqueue()` with Delay

```python
from datetime import timedelta, datetime, timezone

# Run after 5 minutes
result = send_welcome_email.enqueue(
    user_id=user.id,
    run_after=timedelta(minutes=5)
)

# Run at a specific datetime (must be timezone-aware)
result = send_welcome_email.enqueue(
    user_id=user.id,
    run_after=datetime(2025, 6, 1, 9, 0, tzinfo=timezone.utc)
)
```

`run_after` sets the earliest time the task will run. The worker won't pick it up before that time.

### `.using()` — Override Queue

```python
# Override the task's default queue for this specific call
result = send_welcome_email.using(queue_name="emails").enqueue(user_id=user.id)
```

`.using()` returns a new task object with the specified options applied. It does not modify the original task — you can call it multiple times with different queues.

### `.enqueue()` Options Reference

```python
result = my_task.enqueue(
    # Task function arguments — pass as keyword arguments
    user_id=user.id,
    extra_data={"key": "value"},

    # Earliest time the worker should pick this task up.
    # Type: timedelta (relative to now) or datetime (absolute, must be UTC-aware)
    run_after=timedelta(seconds=30),
)
```

---

## 9. Safe Dispatch — `transaction.on_commit()` {#on-commit}

This is the most important pattern when using Django Tasks from views, signals, or services that write to the database.

### The Problem

```python
# ❌ WRONG — race condition
def register_user(email: str, password: str):
    user = User.objects.create_user(email=email, password=password)
    # At this point, the User record MAY NOT be committed to the DB yet.
    # Django wraps requests in a transaction (ATOMIC_REQUESTS=True by default).
    # The commit happens AFTER the view returns a response.
    # If the worker picks up this task before the commit, it gets DoesNotExist.
    send_welcome_email.enqueue(user_id=user.id)
    return user
```

### The Fix

```python
from django.db import transaction

# ✅ CORRECT
def register_user(email: str, password: str):
    user = User.objects.create_user(email=email, password=password)
    # on_commit registers a callback that fires AFTER the transaction commits.
    # If the transaction rolls back (e.g. due to an exception), this callback
    # is NOT called — so no orphan tasks are enqueued for users that don't exist.
    transaction.on_commit(
        lambda: send_welcome_email.enqueue(user_id=user.id)
    )
    return user
```

### In Django Signals

Signals also fire inside the save transaction. Always use `on_commit` here too.

```python
# apps/accounts/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import User

@receiver(post_save, sender=User)
def user_created(sender, instance, created, **kwargs):
    if created:
        transaction.on_commit(
            lambda: send_welcome_email.enqueue(user_id=instance.id)
        )
```

### When NOT to Use `on_commit`

If you're calling `my_task.enqueue()` from code that is NOT inside a database transaction (e.g. a management command, a Celery task, a standalone script), `on_commit` is unnecessary. The DB write has already committed by the time your code runs.

```python
# Management command — no active transaction, on_commit is not needed
class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        for user in User.objects.filter(welcome_email_sent=False):
            send_welcome_email.enqueue(user_id=user.id)  # fine without on_commit
```

---

## 10. Task States & Results {#states}

### All States

| State | Value | Meaning |
|---|---|---|
| `NEW` | `"NEW"` | Task was enqueued. No worker has picked it up yet. |
| `RUNNING` | `"RUNNING"` | Worker is currently executing the task function. |
| `COMPLETE` | `"COMPLETE"` | Task function returned without raising an exception. |
| `FAILED` | `"FAILED"` | Task function raised an exception. |

### TaskResult Object

`.enqueue()` returns a `TaskResult` object immediately. This object represents the DB row.

```python
result = send_welcome_email.enqueue(user_id=user.id)

result.id            # UUID string — unique identifier for this task
result.status        # TaskResultStatus.NEW | RUNNING | COMPLETE | FAILED
result.task_name     # "apps.accounts.tasks.send_welcome_email"
result.task_kwargs   # {"user_id": 42}
result.created_at    # datetime when enqueued
result.finished_at   # datetime when completed or failed (None until done)
result.result        # return value as JSON string (None until COMPLETE)
result.exception_class  # exception class name as string (None unless FAILED)
result.traceback     # full traceback string (None unless FAILED)
```

### Refreshing a Result

The `TaskResult` object is a snapshot at the time of enqueue. To get the current state, you must refresh it from the DB:

```python
# Enqueue and get initial result
result = send_welcome_email.enqueue(user_id=user.id)
print(result.status)  # NEW

# Later, after some time...
from django_tasks.backends.database.models import DBTaskResult

# Fetch the current state from DB
current = DBTaskR
