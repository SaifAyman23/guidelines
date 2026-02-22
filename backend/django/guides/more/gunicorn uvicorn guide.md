# Gunicorn & Uvicorn for Django — The Complete Guide

> A complete, production-ready reference for running Django with Python's two dominant WSGI/ASGI servers. Understand the difference, configure them correctly, and deploy with confidence.

**Gunicorn:** https://gunicorn.org · https://github.com/benoitc/gunicorn
**Uvicorn:** https://www.uvicorn.org · https://github.com/encode/uvicorn
**WSGI spec:** PEP 3333 · **ASGI spec:** https://asgi.readthedocs.io

---

## Table of Contents

1. [Overview — WSGI vs ASGI](#1-overview--wsgi-vs-asgi)
2. [Gunicorn Deep Dive](#2-gunicorn-deep-dive)
   - [Installation & Quick Start](#installation--quick-start)
   - [Worker Types](#worker-types--the-critical-decision)
   - [How Many Workers?](#how-many-workers-the-formula)
   - [Full Configuration Reference](#full-configuration-reference)
3. [Uvicorn Deep Dive](#3-uvicorn-deep-dive)
   - [Installation & Quick Start](#installation--quick-start-1)
   - [Uvicorn + Gunicorn — The Production Pattern](#uvicorn--gunicorn--the-production-pattern)
   - [Full Configuration Reference](#full-configuration-reference-1)
   - [Logging Configuration](#uvicorn-logging-configuration)
4. [Side-by-Side Comparison](#4-side-by-side-comparison)
5. [Architecture Diagrams](#5-architecture-diagrams)
6. [Configuration Files](#6-configuration-files)
7. [Docker & Docker Compose](#7-docker--docker-compose)
8. [Nginx Reverse Proxy](#8-nginx-reverse-proxy)
9. [Which Should You Use?](#9-which-should-you-use)
10. [Production Hardening Checklist](#10-production-hardening-checklist)

---

## 1. Overview — WSGI vs ASGI

Before choosing a server, you need to understand the protocol your Django app speaks. This is the single most important decision that determines everything else.

### WSGI — Web Server Gateway Interface

WSGI is the traditional, synchronous Python web protocol. One request is handled at a time per worker. It is simple, battle-tested, and the right choice for most Django apps.

- One request at a time per worker
- Simple mental model — easy to reason about
- Battle-tested for 15+ years in production
- Django's original protocol (`wsgi.py`)
- Perfect for traditional HTTP APIs and server-rendered pages

### ASGI — Async Server Gateway Interface

ASGI is the modern protocol that supports concurrent connections, WebSockets, and async Python code.

- Handles WebSockets natively
- Supports `async def` Django views without a thread-per-request penalty
- Required for Django Channels
- Better for long-lived or high-concurrency connections
- Django has supported ASGI since version 3.0 (`asgi.py`)

> **Which protocol does Django use?**
> Django supports **both**. Every Django project has `wsgi.py` and `asgi.py`. Most traditional Django apps only need WSGI. Use ASGI if you have WebSockets, use `async def` views, or use Django Channels.

The server you run determines the protocol: **Gunicorn** speaks WSGI by default (and can speak ASGI via uvicorn workers). **Uvicorn** is a pure ASGI server. Understanding this distinction makes every configuration decision obvious.

---

## 2. Gunicorn Deep Dive

Gunicorn ("Green Unicorn") is a Python WSGI HTTP server and the industry standard for Django deployment since around 2010. It uses a pre-fork worker model: a master process manages a pool of worker processes that each handle requests independently.

### Installation & Quick Start

```bash
# Install
pip install gunicorn

# Add to requirements
pip freeze | grep gunicorn >> requirements.txt
# or just add: gunicorn>=21.0.0
```

```bash
# Minimal — development only
gunicorn myproject.wsgi:application

# With port and reload (dev)
gunicorn myproject.wsgi:application \
  --bind 0.0.0.0:8000 \
  --reload

# Production-ready command
gunicorn myproject.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --worker-class sync \
  --timeout 30 \
  --keep-alive 5 \
  --max-requests 1000 \
  --max-requests-jitter 100 \
  --log-level info \
  --access-logfile - \
  --error-logfile -
```

> **The wsgi:application path**
> The string `myproject.wsgi:application` tells Gunicorn: find the Python module `myproject/wsgi.py` and use the object named `application` inside it. Django auto-generates this file. Replace `myproject` with your actual project name (the folder that contains `settings.py`).

### Worker Types — The Critical Decision

Gunicorn supports several worker types, each with a completely different concurrency model.

| Worker Class | Concurrency Model | Install | Best For |
|---|---|---|---|
| `sync` | 1 request per worker at a time | built-in | CPU-bound, standard Django |
| `gevent` | Green threads (cooperative) | `pip install gevent` | Many concurrent I/O requests |
| `eventlet` | Green threads (cooperative) | `pip install eventlet` | Legacy — prefer gevent |
| `gthread` | OS threads per worker | built-in | Thread-safe I/O heavy apps |
| `uvicorn.workers.UvicornWorker` | Async event loop (ASGI) | `pip install uvicorn` | Async views, WebSockets |

```bash
# Default sync workers (most common, no extra dependencies)
gunicorn myproject.wsgi:application --worker-class sync

# Gevent workers — handles 1000s of concurrent connections per worker
pip install gevent
gunicorn myproject.wsgi:application --worker-class gevent --worker-connections 1000

# Thread workers — each worker runs multiple threads
gunicorn myproject.wsgi:application --worker-class gthread --threads 4

# Uvicorn workers — run ASGI apps via Gunicorn (best of both worlds)
pip install uvicorn
gunicorn myproject.asgi:application --worker-class uvicorn.workers.UvicornWorker
```

### How Many Workers? The Formula

Worker count has the largest single impact on performance. Too few means wasted CPU; too many causes memory pressure and context-switch overhead.

```python
# The classic Gunicorn docs formula:
workers = (2 × CPU_cores) + 1

# For a 2-core machine:   2*2+1 = 5 workers
# For a 4-core machine:   2*4+1 = 9 workers
# For an 8-core machine:  2*8+1 = 17 workers

# Get CPU count in Python:
# python -c "import multiprocessing; print(multiprocessing.cpu_count())"

# Dynamic workers in gunicorn.conf.py:
import multiprocessing
workers = multiprocessing.cpu_count() * 2 + 1
```

> **Memory warning:** Each Gunicorn worker is a full Python process. If your Django app uses 100 MB of RAM, 9 workers use ~900 MB. Monitor your memory usage in production and reduce workers if you are memory-constrained. Consider fewer workers + threads (`gthread`) on memory-limited servers.

### Full Configuration Reference

Gunicorn can be configured via command-line flags, environment variables, or a Python config file. A config file is strongly recommended for production.

```python
# gunicorn.conf.py — place this in your project root.
# Run with: gunicorn -c gunicorn.conf.py myproject.wsgi:application

import multiprocessing
import os

# ── Binding ───────────────────────────────────────────────────────────────────
# The socket to bind. For production, use a Unix socket for nginx integration.
bind = os.getenv("GUNICORN_BIND", "0.0.0.0:8000")
# Alternative: bind = "unix:/run/gunicorn/gunicorn.sock"
backlog = 2048  # pending connection queue size

# ── Workers ───────────────────────────────────────────────────────────────────
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = os.getenv("GUNICORN_WORKER_CLASS", "sync")
# Options: sync | gthread | gevent | eventlet | uvicorn.workers.UvicornWorker

threads = int(os.getenv("GUNICORN_THREADS", 1))
# Threads per worker (only for gthread). Total concurrency = workers × threads.

worker_connections = 1000
# Max simultaneous clients per worker (gevent/eventlet only).

# ── Timeouts ──────────────────────────────────────────────────────────────────
timeout = 30
# Worker silent for more than this many seconds is killed and restarted.
# Increase for views that do heavy computation or slow DB queries.

graceful_timeout = 30
# Seconds to wait for workers to finish in-flight requests on restart.

keepalive = 5
# Seconds to wait for next request on a keep-alive connection.
# Should match your nginx keepalive_timeout value.

# ── Worker Recycling ──────────────────────────────────────────────────────────
max_requests = 1000
# Restart workers after this many requests to prevent memory leaks.

max_requests_jitter = 100
# Randomise max_requests by ±jitter to prevent all workers restarting at once.

# ── Logging ───────────────────────────────────────────────────────────────────
accesslog = "-"     # "-" means stdout (good for Docker/systemd)
errorlog  = "-"     # "-" means stderr
loglevel  = os.getenv("LOG_LEVEL", "info")
# Options: debug | info | warning | error | critical

access_log_format = (
    '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)sµs'
)
# %(D)s = request duration in microseconds

# ── Process Naming ────────────────────────────────────────────────────────────
proc_name = "myproject-gunicorn"

# ── Security ──────────────────────────────────────────────────────────────────
limit_request_line   = 4096   # max HTTP request line size (bytes)
limit_request_fields = 100    # max number of HTTP headers
limit_request_field_size = 8190  # max size of each header

# ── Server Hooks ──────────────────────────────────────────────────────────────
def post_fork(server, worker):
    # Called after a worker is forked. Use this to set up per-worker state,
    # e.g., reconnect database connections.
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def worker_exit(server, worker):
    server.log.info("Worker exiting (pid: %s)", worker.pid)
```

```bash
# Gunicorn automatically finds gunicorn.conf.py in current directory, or:
gunicorn -c gunicorn.conf.py myproject.wsgi:application

# Config options can also be overridden via env vars:
# GUNICORN_WORKERS=4 GUNICORN_TIMEOUT=60 gunicorn myproject.wsgi:application
```

---

## 3. Uvicorn Deep Dive

Uvicorn is a lightning-fast ASGI server built on top of `uvloop` and `httptools`. It is the reference implementation server for ASGI and the recommended server for async Django apps, FastAPI, and Starlette.

> **Uvicorn is not a process manager.** Uvicorn alone runs a single process. In production, you need multiple processes for redundancy and to use multiple CPU cores. The recommended production pattern is **Gunicorn managing Uvicorn workers**, or a dedicated process manager like systemd or Docker.

### Installation & Quick Start

```bash
# Standard install
pip install uvicorn

# Install with "standard" extras — highly recommended for production.
# Includes uvloop (fast event loop) and httptools (fast HTTP parsing).
pip install "uvicorn[standard]"

# uvloop is Linux/macOS only. Windows uses the default asyncio event loop.
```

```bash
# Minimal
uvicorn myproject.asgi:application

# With hot reload (development only)
uvicorn myproject.asgi:application --reload --host 0.0.0.0 --port 8000

# Production — single process (use Gunicorn for multi-process)
uvicorn myproject.asgi:application \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --loop uvloop \
  --http httptools \
  --log-level info \
  --access-log \
  --no-server-header
```

> **asgi vs wsgi:** Notice we point Uvicorn at `myproject.asgi:application` (not `wsgi`). Every Django project has both. The `asgi.py` file lives in the same directory as `wsgi.py` and `settings.py`. Django's default ASGI entry point supports both sync and async views transparently.

### Uvicorn + Gunicorn — The Production Pattern

This is the most recommended production setup when you need ASGI. Gunicorn acts as the process manager (handling signals, worker restart, graceful shutdown) and spawns Uvicorn workers instead of its own sync workers.

**Why combine them?** Uvicorn's built-in `--workers` flag works, but lacks Gunicorn's robust process management: no graceful restart on config change, no automatic worker replacement on crash with backoff, no pre/post fork hooks. Gunicorn has solved these problems over 15 years of production use.

```bash
# Install both
pip install gunicorn "uvicorn[standard]"

# Run — point at asgi.py, use UvicornWorker
gunicorn myproject.asgi:application \
  --worker-class uvicorn.workers.UvicornWorker \
  --workers 4 \
  --bind 0.0.0.0:8000
```

```python
# gunicorn.conf.py — ASGI/uvicorn setup
import multiprocessing
import os

bind         = os.getenv("BIND", "0.0.0.0:8000")
workers      = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"

timeout          = 30
graceful_timeout = 30
keepalive        = 5

max_requests        = 1000
max_requests_jitter = 100

accesslog = "-"
errorlog  = "-"
loglevel  = os.getenv("LOG_LEVEL", "info")
```

```bash
# Run with config
gunicorn -c gunicorn.conf.py myproject.asgi:application
```

### Full Configuration Reference

```bash
uvicorn myproject.asgi:application \

  # ── Network ─────────────────────────────────────────────────────────────
  --host 0.0.0.0 \            # Interface to bind
  --port 8000 \               # Port to listen on
  --uds /tmp/uvicorn.sock \   # Unix socket (alternative to host/port)

  # ── Workers & Concurrency ────────────────────────────────────────────────
  --workers 4 \               # Number of worker processes
  --loop uvloop \             # Event loop: uvloop | asyncio
  --http httptools \          # HTTP protocol: h11 | httptools
  --ws websockets \           # WebSocket library: websockets | wsproto
  --lifespan on \             # ASGI lifespan events: on | off | auto
  --interface asgi3 \         # App interface: asgi3 | asgi2 | wsgi

  # ── Timeouts ─────────────────────────────────────────────────────────────
  --timeout-keep-alive 5 \    # Keep-alive seconds after last data
  --timeout-notify 30 \       # Worker restart notification seconds

  # ── TLS (use nginx instead in production) ────────────────────────────────
  --ssl-keyfile key.pem \
  --ssl-certfile cert.pem \

  # ── Logging ──────────────────────────────────────────────────────────────
  --log-level info \          # debug | info | warning | error | critical
  --access-log \              # Enable access logging
  --no-access-log \           # Disable access logging
  --use-colors \              # Force coloured output
  --log-config logging.json \ # Path to logging config file

  # ── Development ───────────────────────────────────────────────────────────
  --reload \                  # Auto-reload on file change
  --reload-dir . \            # Directory to watch for --reload

  # ── Security ──────────────────────────────────────────────────────────────
  --no-server-header \        # Don't send Server: uvicorn header
  --limit-concurrency 100 \   # Max concurrent connections before 503
  --limit-max-requests 1000   # Restart worker after N requests
```

### Uvicorn Logging Configuration

```json
{
  "version": 1,
  "disable_existing_loggers": false,
  "formatters": {
    "default": {
      "()": "uvicorn.logging.DefaultFormatter",
      "fmt": "%(asctime)s %(levelprefix)s %(message)s",
      "use_colors": false
    },
    "access": {
      "()": "uvicorn.logging.AccessFormatter",
      "fmt": "%(asctime)s %(levelprefix)s %(client_addr)s - \"%(request_line)s\" %(status_code)s"
    }
  },
  "handlers": {
    "default": { "class": "logging.StreamHandler", "stream": "ext://sys.stderr", "formatter": "default" },
    "access":  { "class": "logging.StreamHandler", "stream": "ext://sys.stdout", "formatter": "access"  }
  },
  "loggers": {
    "uvicorn":        { "handlers": ["default"], "level": "INFO" },
    "uvicorn.error":  { "level": "INFO" },
    "uvicorn.access": { "handlers": ["access"],  "level": "INFO", "propagate": false }
  }
}
```

---

## 4. Side-by-Side Comparison

| Feature | Gunicorn | Uvicorn |
|---|---|---|
| Protocol | WSGI (+ ASGI via uvicorn workers) | ASGI (+ WSGI compat mode) |
| Concurrency model | Pre-fork multiprocessing | Async event loop (asyncio/uvloop) |
| WebSocket support | No (need uvicorn worker) | Yes |
| HTTP/2 support | No | Via hypercorn |
| Process management | Excellent | Basic (`--workers`) |
| Graceful reload | Yes (USR2 signal) | Yes (--workers mode) |
| Worker recycling | Yes (`max-requests`) | Yes (`--limit-max-requests`) |
| Production maturity | 15+ years | ~5 years |
| Django Channels | No (needs ASGI) | Yes |
| async/await views | Sync-wrapped | Native |
| Memory per worker | Higher (full Python process) | Lower (fewer processes) |
| CPU-bound performance | Better (true parallelism) | GIL limits parallelism |
| I/O-bound performance | Good (gevent/gthread) | Excellent (native async) |
| Hot reload (dev) | Yes (`--reload`) | Yes (`--reload`) |
| Config file | Python (`.py`) | None (CLI only) |
| Default on Heroku/PaaS | Yes | Manual Procfile |

### Performance by Workload Type

Performance varies significantly by workload. These are relative figures to illustrate the tradeoffs — actual numbers depend on your app, database, and infrastructure.

**Sync I/O-heavy (ORM queries, external APIs):**
- Gunicorn sync: ~35% relative throughput
- Gunicorn gevent: ~72% relative throughput
- Uvicorn (async views): ~100% relative throughput

**CPU-heavy (image processing, report generation):**
- Gunicorn sync: ~100% relative throughput
- Gunicorn gevent: ~95% relative throughput
- Uvicorn (async views): ~65% relative throughput

**WebSockets / long-lived connections:**
- Gunicorn sync: ~10% relative throughput
- Gunicorn gevent: ~55% relative throughput
- Uvicorn (ASGI): ~100% relative throughput

---

## 5. Architecture Diagrams

### Pattern A — Gunicorn (WSGI, Traditional)

```
Client Browser / HTTP Client
        │
        ▼
      Nginx
  (reverse proxy, SSL, static files)
        │
        ▼
  Gunicorn Master Process
  (manages workers, handles signals)
        │
   ┌────┴────┬────────┐
   ▼         ▼        ▼
Worker 1  Worker 2  Worker N
(sync)    (sync)    (sync)
        │
        ▼
  Django Application
  (wsgi.py → URLconf → Views → ORM)
```

### Pattern B — Uvicorn (ASGI, Async)

```
Client Browser / WebSocket / HTTP Client
        │
        ▼
      Nginx
  (reverse proxy, WebSocket upgrade, static files)
        │
        ▼
  Uvicorn Process(es)
  (async event loop — handles 1000s of concurrent connections)
        │
        ▼
  Django Application
  (asgi.py → URLconf → Async Views → Async ORM)
```

### Pattern C — Gunicorn + Uvicorn Workers (Recommended for ASGI)

The best of both worlds: Gunicorn's process management + Uvicorn's async performance.

```
Client Browser / WebSocket / HTTP Client
        │
        ▼
      Nginx
        │
        ▼
  Gunicorn Master
  (process manager only — does not handle requests)
        │
   ┌────┴────────────┐
   ▼                 ▼
UvicornWorker 1  UvicornWorker N
(async loop)     (async loop)
        │
        ▼
  Django Application
  (asgi.py — sync and async views both work)
```

**How Pattern C works:** Gunicorn forks N child processes. Each child runs a Uvicorn event loop instead of a sync worker. The master process handles signals (SIGHUP for graceful reload, SIGTERM for shutdown), respawns crashed workers, and enforces timeouts. Each Uvicorn worker handles many concurrent requests via its async event loop.

---

## 6. Configuration Files

### Project File Layout

```
myproject/
├── manage.py
├── myproject/
│   ├── __init__.py
│   ├── settings/
│   ├── urls.py
│   ├── wsgi.py          ← for Gunicorn
│   └── asgi.py          ← for Uvicorn
├── gunicorn.conf.py     ← Gunicorn config
├── requirements.txt
└── Dockerfile
```

### wsgi.py

Django auto-generates this file. Do not change it unless you know why.

```python
# myproject/wsgi.py
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")

application = get_wsgi_application()
```

### asgi.py

```python
# myproject/asgi.py
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")

# Standard ASGI app — works with sync and async Django views.
application = get_asgi_application()

# If using Django Channels, it looks like this instead:
# from channels.routing import ProtocolTypeRouter, URLRouter
# from channels.auth import AuthMiddlewareStack
# from myapp.routing import websocket_urlpatterns
#
# application = ProtocolTypeRouter({
#     "http": get_asgi_application(),
#     "websocket": AuthMiddlewareStack(
#         URLRouter(websocket_urlpatterns)
#     ),
# })
```

### requirements.txt

```
# WSGI / Gunicorn only:
Django>=4.2
gunicorn>=21.2.0

# ASGI / Uvicorn only:
Django>=4.2
uvicorn[standard]>=0.27.0

# Gunicorn + Uvicorn workers (recommended ASGI setup):
Django>=4.2
gunicorn>=21.2.0
uvicorn[standard]>=0.27.0

# Optional — for gevent workers:
gevent>=23.0.0
```

---

## 7. Docker & Docker Compose

### Dockerfile — Gunicorn (WSGI)

```dockerfile
# ── Build stage ────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Runtime stage ──────────────────────────────────────────────────────────
FROM python:3.12-slim

# Non-root user for security
RUN groupadd -r django && useradd -r -g django django

WORKDIR /app
COPY --from=builder /install /usr/local
COPY --chown=django:django . .

ARG DJANGO_SETTINGS_MODULE=myproject.settings
ENV DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
RUN python manage.py collectstatic --noinput

USER django

EXPOSE 8000

# Gunicorn reads gunicorn.conf.py from current directory
CMD ["gunicorn", "-c", "gunicorn.conf.py", "myproject.wsgi:application"]
```

### Dockerfile — Uvicorn / Gunicorn + Uvicorn Workers (ASGI)

```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim
RUN groupadd -r django && useradd -r -g django django
WORKDIR /app
COPY --from=builder /install /usr/local
COPY --chown=django:django . .

ARG DJANGO_SETTINGS_MODULE=myproject.settings
ENV DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
RUN python manage.py collectstatic --noinput

USER django
EXPOSE 8000

# Gunicorn managing Uvicorn workers — point at asgi.py
CMD ["gunicorn", "-c", "gunicorn.conf.py", "myproject.asgi:application"]
```

### docker-compose.yml — Full Stack

```yaml
version: "3.9"

services:
  web:
    build:
      context: .
      dockerfile: Dockerfile
    restart: unless-stopped
    environment:
      - DJANGO_SETTINGS_MODULE=myproject.settings.production
      - DATABASE_URL=postgres://user:pass@db:5432/mydb
      - DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY}
      - GUNICORN_WORKERS=4
      - GUNICORN_WORKER_CLASS=sync  # or uvicorn.workers.UvicornWorker
      - LOG_LEVEL=info
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - static_files:/app/staticfiles
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s
      timeout: 10s
      retries: 3

  db:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      - POSTGRES_DB=mydb
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d mydb"]
      interval: 10s
      timeout: 5s
      retries: 5

  nginx:
    image: nginx:1.25-alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - static_files:/var/www/static:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - web

volumes:
  postgres_data:
  static_files:
```

> **Environment variable override pattern:** The same image can run as a WSGI app in one environment and ASGI in another by changing `GUNICORN_WORKER_CLASS` — without rebuilding. `gunicorn.conf.py` reads these with `os.getenv()`.

---

## 8. Nginx Reverse Proxy

In production, always place Nginx in front of Gunicorn or Uvicorn. Nginx handles SSL termination, serves static files, provides connection buffering, and protects your Python server from slow clients.

### Nginx Config — Gunicorn (WSGI)

```nginx
upstream django_gunicorn {
    # Unix socket is faster than TCP for local connections
    server unix:/run/gunicorn/gunicorn.sock fail_timeout=0;
    # Or use TCP: server 127.0.0.1:8000 fail_timeout=0;
    # For Docker:  server web:8000 fail_timeout=0;
}

server {
    listen 80;
    server_name example.com www.example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name example.com www.example.com;

    # SSL
    ssl_certificate     /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;
    ssl_session_cache   shared:SSL:10m;

    # Security headers
    add_header X-Frame-Options           DENY;
    add_header X-Content-Type-Options    nosniff;
    add_header X-XSS-Protection         "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

    # Static files — served directly by Nginx, never hits Django
    location /static/ {
        alias /var/www/static/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
        access_log off;
    }

    location /media/ {
        alias /var/www/media/;
        expires 7d;
        access_log off;
    }

    # Proxy to Gunicorn
    location / {
        proxy_pass         http://django_gunicorn;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;

        # Buffering — protects Gunicorn from slow clients
        proxy_buffering    on;
        proxy_buffer_size  128k;
        proxy_buffers      4 256k;

        # Timeouts — should exceed Gunicorn's timeout
        proxy_connect_timeout 75s;
        proxy_read_timeout    300s;

        proxy_redirect     off;
    }

    client_max_body_size 20M;

    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml;
    gzip_min_length 1024;
}
```

### Nginx Config — Uvicorn with WebSockets

```nginx
upstream django_uvicorn {
    server web:8000 fail_timeout=0;
}

server {
    listen 443 ssl http2;
    server_name example.com;

    ssl_certificate     /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;

    # Standard HTTP requests
    location / {
        proxy_pass         http://django_uvicorn;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_redirect     off;
        proxy_buffering    on;
        proxy_read_timeout 300s;
    }

    # WebSocket connections — must disable buffering and set upgrade headers
    location /ws/ {
        proxy_pass         http://django_uvicorn;
        proxy_http_version 1.1;

        # Required for WebSocket upgrade
        proxy_set_header   Upgrade    $http_upgrade;
        proxy_set_header   Connection "upgrade";

        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;

        # No buffering for WebSocket connections
        proxy_buffering    off;
        proxy_read_timeout 86400s;  # 24 hours for long-lived WS connections
    }

    location /static/ {
        alias /var/www/static/;
        expires 30d;
        access_log off;
    }

    client_max_body_size 20M;
}
```

### Django Settings — Proxy Trust

When running behind Nginx, configure Django to trust proxy headers:

```python
# settings.py
ALLOWED_HOSTS = ["example.com", "www.example.com"]

# Tell Django it's behind a proxy sending HTTPS via HTTP internally
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True
```

---

## 9. Which Should You Use?

| Situation | Gunicorn | Uvicorn | Gunicorn + Uvicorn |
|---|---|---|---|
| Traditional Django REST API | **Best choice** | Works, no benefit | Overkill |
| WebSockets / Django Channels | Won't work | Works (single process) | **Best choice** |
| `async def` views only | Works (sync wrapper) | **Best choice** | **Best choice** |
| Mixed sync + async views | OK for sync | Works (slow for sync) | **Best choice** |
| Heavy CPU processing | **Best choice** | Avoid (GIL) | OK |
| High I/O concurrency | OK (gevent) | **Best choice** | **Best choice** |
| Memory-constrained server | Many processes = RAM | Fewer processes needed | Fewer than pure Gunicorn |
| FastAPI or Starlette | Wrong tool | **Best choice** | **Best choice** |
| Heroku / Railway / Render | Native support | Manual Procfile | Manual Procfile |

### Decision Flowchart

```
Do you use WebSockets or Django Channels?
├── YES → Gunicorn + UvicornWorker (pointing at asgi.py)
└── NO  → Do you write async def views or need high concurrency?
          ├── YES → Gunicorn + UvicornWorker, or standalone Uvicorn
          └── NO  → Gunicorn (sync)
                    The default. Simple, battle-tested.
```

---

## 10. Production Hardening Checklist

### Django Settings

```python
# settings/production.py

# ── Security ──────────────────────────────────────────────────────────────────
DEBUG = False
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]  # Never hardcode this
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")

SECURE_SSL_REDIRECT              = True
SECURE_HSTS_SECONDS              = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS   = True
SECURE_HSTS_PRELOAD              = True
SECURE_BROWSER_XSS_FILTER        = True
SECURE_CONTENT_TYPE_NOSNIFF      = True
SESSION_COOKIE_SECURE            = True
CSRF_COOKIE_SECURE               = True
X_FRAME_OPTIONS                  = "DENY"
SECURE_PROXY_SSL_HEADER          = ("HTTP_X_FORWARDED_PROTO", "https")

# ── Static Files ──────────────────────────────────────────────────────────────
STATIC_ROOT = BASE_DIR / "staticfiles"
# Run: python manage.py collectstatic --noinput  (in Dockerfile)

# ── Database Connection Pooling ───────────────────────────────────────────────
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "CONN_MAX_AGE": 60,  # Reuse DB connections (seconds)
        # "CONN_HEALTH_CHECKS": True  # Django 4.1+ — validates before reuse
    }
}

# ── Logging ───────────────────────────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.getenv("LOG_LEVEL", "WARNING"),
            "propagate": False,
        },
    },
}
```

### Systemd Service Unit (non-Docker)

```ini
[Unit]
Description=Django via Gunicorn
After=network.target

[Service]
Type=notify
User=django
Group=django
WorkingDirectory=/srv/myproject
Environment="DJANGO_SETTINGS_MODULE=myproject.settings.production"
EnvironmentFile=/etc/myproject/env

ExecStart=/srv/myproject/venv/bin/gunicorn \
    -c /srv/myproject/gunicorn.conf.py \
    myproject.wsgi:application

ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl enable django
sudo systemctl start django

# View logs
sudo journalctl -u django -f

# Graceful reload (no downtime — sends SIGHUP to Gunicorn master)
sudo systemctl reload django
```

### Health Check Endpoint

Always add a lightweight health check endpoint for Nginx, Docker, and load balancers.

```python
# myapp/views.py
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    """Lightweight health check — verify app + DB are alive."""
    try:
        connection.ensure_connection()
        db_ok = True
    except Exception:
        db_ok = False

    status = 200 if db_ok else 503
    return JsonResponse({"status": "ok" if db_ok else "degraded", "db": db_ok}, status=status)
```

```python
# urls.py
from myapp.views import health_check

urlpatterns = [
    path("health/", health_check),
    # ... other urls
]
```

### Checklist

#### Server Setup

- [ ] Gunicorn or Uvicorn is pinned in `requirements.txt` with a minimum version
- [ ] `gunicorn.conf.py` exists and is committed to version control
- [ ] Server is started via a config file, not a long CLI string
- [ ] `accesslog` and `errorlog` are set to `"-"` (stdout/stderr for Docker/systemd)

#### Workers

- [ ] Worker count is tuned to `2 × CPU_cores + 1` and tested under load
- [ ] Worker type is appropriate for your app (sync for WSGI, UvicornWorker for ASGI)
- [ ] `max_requests` and `max_requests_jitter` are set to prevent memory leaks
- [ ] `timeout` is set and is less than Nginx's `proxy_read_timeout`
- [ ] `graceful_timeout` is set to allow in-flight requests to complete on restart

#### Django Settings

- [ ] `DEBUG = False` in production settings
- [ ] Secret key loaded from environment variable, not hardcoded
- [ ] `ALLOWED_HOSTS` locked down to your actual domain
- [ ] `STATIC_ROOT` configured and `collectstatic` run in Dockerfile
- [ ] `CONN_MAX_AGE` set in DATABASES to reuse database connections
- [ ] `SECURE_PROXY_SSL_HEADER` set since you are running behind Nginx

#### Nginx

- [ ] Nginx is in front of Gunicorn/Uvicorn
- [ ] SSL/TLS configured with modern cipher suites
- [ ] Nginx serves `/static/` and `/media/` directly (never through Django)
- [ ] `proxy_read_timeout` exceeds Gunicorn's `timeout`
- [ ] WebSocket `Upgrade` headers set if using Uvicorn/ASGI (`proxy_http_version 1.1`)

#### Operations

- [ ] Health check endpoint exists and Docker/Nginx is using it
- [ ] Process manager (systemd or Docker restart policy) set to auto-restart on failure
- [ ] Graceful reload tested: `kill -HUP <master_pid>` or `systemctl reload`
- [ ] Database password and Django secret key are in a secrets manager or env file — not in version control
- [ ] Log output is captured by Docker or systemd (stdout/stderr, not files)

---

*Gunicorn documentation: https://docs.gunicorn.org*
*Uvicorn documentation: https://www.uvicorn.org*
*Django deployment checklist: https://docs.djangoproject.com/en/stable/howto/deployment/checklist/*
*Django ASGI deployment: https://docs.djangoproject.com/en/stable/howto/deployment/asgi/*
