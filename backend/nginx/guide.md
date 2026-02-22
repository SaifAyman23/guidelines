# NGINX — The Complete Deployment Guide for Django + React

> A production-focused reference for deploying a Django backend and React frontend using NGINX, covering configuration, SSL, security, performance, reverse proxying, static files, WebSockets, and monitoring integration.

---

## Table of Contents

1. [The Big Picture — How NGINX Fits In](#1-the-big-picture--how-nginx-fits-in)
2. [Installation](#2-installation)
3. [NGINX Configuration Structure](#3-nginx-configuration-structure)
4. [Core Concepts: Directives, Blocks, and Context](#4-core-concepts-directives-blocks-and-context)
5. [Serving the React Frontend](#5-serving-the-react-frontend)
6. [Reverse Proxying to Django (Gunicorn)](#6-reverse-proxying-to-django-gunicorn)
7. [Static and Media Files](#7-static-and-media-files)
8. [SSL/TLS with Let's Encrypt](#8-ssltls-with-lets-encrypt)
9. [Security Hardening](#9-security-hardening)
10. [Performance Tuning](#10-performance-tuning)
11. [Gzip and Brotli Compression](#11-gzip-and-brotli-compression)
12. [Caching](#12-caching)
13. [WebSocket Support](#13-websocket-support)
14. [Rate Limiting](#14-rate-limiting)
15. [Protecting the /metrics Endpoint](#15-protecting-the-metrics-endpoint)
16. [Logging](#16-logging)
17. [Health Checks](#17-health-checks)
18. [Docker Compose Full Stack](#18-docker-compose-full-stack)
19. [Kubernetes Ingress with NGINX](#19-kubernetes-ingress-with-nginx)
20. [Multiple Environments](#20-multiple-environments)
21. [Common Errors and How to Fix Them](#21-common-errors-and-how-to-fix-them)
22. [Full Production Configuration Reference](#22-full-production-configuration-reference)
23. [Checklist](#23-checklist)

---

## 1. The Big Picture — How NGINX Fits In

NGINX sits in front of everything. It is the single entry point for all traffic to your application. Every HTTP and HTTPS request goes through NGINX first, and NGINX decides where to route it.

```
Internet
    │
    ▼
┌─────────────────────────────────────────────┐
│                  NGINX                       │
│                                             │
│  /           → Serve React build (static)   │
│  /api/       → Proxy to Django (Gunicorn)   │
│  /admin/     → Proxy to Django (Gunicorn)   │
│  /ws/        → Proxy to Django (Channels)   │
│  /media/     → Serve Django uploaded files  │
│  /metrics    → Restricted to Prometheus IP  │
└──────────────────┬───────────┬──────────────┘
                   │           │
          ┌────────▼──┐  ┌─────▼──────────┐
          │ Gunicorn  │  │  React Build   │
          │ Django    │  │  /var/www/app  │
          │ :8000     │  │  (static HTML) │
          └────────────┘  └───────────────┘
```

### Why NGINX and not just Gunicorn?

Gunicorn is a Python application server. It is excellent at running Python code but not designed for:

- Serving thousands of static files efficiently
- Handling SSL/TLS termination
- Connection buffering (slow clients would tie up Gunicorn workers)
- Gzip compression
- Rate limiting and DDoS mitigation
- Routing between multiple services

NGINX handles all of the above in C, orders of magnitude faster than Python, freeing Gunicorn workers to focus entirely on running your Django application.

---

## 2. Installation

### Ubuntu / Debian

```bash
sudo apt update
sudo apt install nginx

# Start and enable on boot
sudo systemctl start nginx
sudo systemctl enable nginx

# Verify it is running
sudo systemctl status nginx
curl http://localhost
```

### CentOS / RHEL / Rocky Linux

```bash
sudo dnf install nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

### Docker

```dockerfile
FROM nginx:1.25-alpine
COPY nginx.conf /etc/nginx/nginx.conf
COPY sites-enabled/ /etc/nginx/conf.d/
```

### Check the Version

```bash
nginx -v
# nginx version: nginx/1.25.3

# Full version and build options (useful for checking module support)
nginx -V
```

---

## 3. NGINX Configuration Structure

After installation, NGINX's configuration lives in `/etc/nginx/`. Understanding the layout is essential before editing anything.

```
/etc/nginx/
├── nginx.conf                  ← Main configuration file
├── conf.d/                     ← Additional config files (auto-included)
│   └── default.conf
├── sites-available/            ← Virtual host configs (Ubuntu/Debian convention)
│   ├── myapp.conf
│   └── default
├── sites-enabled/              ← Symlinks to sites-available that are active
│   └── myapp.conf -> ../sites-available/myapp.conf
├── snippets/                   ← Reusable config fragments
│   ├── fastcgi-php.conf
│   └── snakeoil.conf
├── mime.types                  ← Maps file extensions to MIME types
└── modules-enabled/            ← Dynamically loaded modules
```

### The Enable/Disable Pattern (Ubuntu/Debian)

On Ubuntu/Debian, the convention is to write configs in `sites-available/` and create symlinks in `sites-enabled/` to activate them. This lets you disable a site without deleting its config.

```bash
# Create a new site config
sudo nano /etc/nginx/sites-available/myapp.conf

# Enable it by creating a symlink
sudo ln -s /etc/nginx/sites-available/myapp.conf /etc/nginx/sites-enabled/myapp.conf

# Disable it without deleting
sudo rm /etc/nginx/sites-enabled/myapp.conf

# Test config for syntax errors before reloading
sudo nginx -t

# Reload NGINX (zero-downtime, applies new config)
sudo systemctl reload nginx

# Full restart (brief downtime, use only when reload is not enough)
sudo systemctl restart nginx
```

> **Always run `sudo nginx -t` before reloading.** A config syntax error with an immediate reload will kill NGINX and take down your site.

---

## 4. Core Concepts: Directives, Blocks, and Context

NGINX configuration is made up of **directives** grouped into **blocks** (also called **contexts**).

```nginx
# A directive is a key-value pair ending in a semicolon
worker_processes auto;

# A block is a group of directives inside braces
events {
    worker_connections 1024;
}

# Blocks can nest
http {
    # Directives that apply to all HTTP traffic
    sendfile on;

    server {
        # Directives for one virtual host
        listen 80;
        server_name example.com;

        location / {
            # Directives for a specific URL path
            root /var/www/html;
        }
    }
}
```

### The Four Essential Blocks

**`events {}`** — Configures NGINX's connection handling at the OS level. Rarely needs to be changed from defaults.

**`http {}`** — Contains all HTTP configuration. Everything related to web serving lives here.

**`server {}`** — Defines a virtual host — one server block per domain or port. You can have many server blocks.

**`location {}`** — Matches URL paths and defines how to handle requests for those paths. Lives inside a `server` block.

### Location Block Matching — Priority Order

NGINX matches location blocks in a specific order. Getting this wrong causes requests to hit the wrong handler.

```nginx
server {
    # 1. Exact match — highest priority, checked first
    location = /favicon.ico {
        log_not_found off;
        access_log off;
    }

    # 2. Preferential prefix match (^~) — if this matches, stop looking
    #    Use for static file directories to prevent regex matching
    location ^~ /static/ {
        root /var/www/myapp;
    }

    # 3. Case-sensitive regex (~)
    location ~ \.php$ {
        # Handle PHP files
    }

    # 4. Case-insensitive regex (~*)
    location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
        expires 30d;
    }

    # 5. Prefix match — lowest priority, the catch-all
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

---

## 5. Serving the React Frontend

A React app built with `npm run build` (or `vite build`) produces a directory of static files — HTML, JavaScript, CSS, and assets. NGINX serves these directly from disk, with no Python involved.

### Build Your React App

```bash
# In your React project directory
npm run build

# This creates a build/ or dist/ directory:
# build/
# ├── index.html
# ├── static/
# │   ├── js/main.abc123.js
# │   └── css/main.def456.css
# └── assets/
```

### Copy the Build to the Server

```bash
# Copy to the web root on your server
sudo mkdir -p /var/www/myapp
sudo cp -r build/* /var/www/myapp/
sudo chown -R www-data:www-data /var/www/myapp
```

### NGINX Configuration for React (SPA)

The critical configuration for a Single Page Application is `try_files $uri $uri/ /index.html`. This tells NGINX:
1. Try to find the file at the exact URI (`$uri`)
2. Try to find a directory at the URI (`$uri/`)
3. If neither exists, serve `index.html` and let React Router handle routing

Without this, navigating directly to `/dashboard` returns a 404 because there is no `/dashboard` file on disk. React Router only works when `index.html` is always returned.

```nginx
server {
    listen 80;
    server_name myapp.com www.myapp.com;

    root /var/www/myapp;
    index index.html;

    # React SPA — all routes serve index.html and React Router takes over
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Static assets with hashed filenames can be cached aggressively.
    # React's build tool adds a content hash to filenames (main.abc123.js)
    # so a new deploy generates a new filename, invalidating the cache automatically.
    location /static/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
}
```

---

## 6. Reverse Proxying to Django (Gunicorn)

Django runs inside Gunicorn (the Python WSGI application server) on port 8000. NGINX proxies specific URL paths to Gunicorn. Gunicorn never faces the internet directly.

### Start Gunicorn

```bash
# Basic Gunicorn start (run from your Django project directory)
gunicorn config.wsgi:application --workers 4 --bind 127.0.0.1:8000

# Or with a Unix socket (faster than TCP for local communication)
gunicorn config.wsgi:application --workers 4 --bind unix:/run/gunicorn/gunicorn.sock
```

Using a Unix socket instead of TCP (`127.0.0.1:8000`) reduces latency for the NGINX-to-Gunicorn hop because it avoids the TCP stack entirely. Both work fine; sockets are marginally faster.

### NGINX Reverse Proxy Configuration

```nginx
# Define the upstream server (Gunicorn)
# Defined once in the http {} block and referenced by name in server blocks
upstream django_backend {
    # TCP connection to Gunicorn
    server 127.0.0.1:8000;

    # Or a Unix socket (uncomment if using socket, comment out the line above)
    # server unix:/run/gunicorn/gunicorn.sock;

    # Multiple Gunicorn instances for load balancing (optional)
    # server 127.0.0.1:8001;
    # server 127.0.0.1:8002;
}

server {
    listen 80;
    server_name myapp.com;

    # --- Django API and Admin ---
    location /api/ {
        proxy_pass http://django_backend;

        # Essential proxy headers — Django reads these for request info
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout    60s;
        proxy_read_timeout    60s;

        # Buffer settings — NGINX buffers the response from Gunicorn
        # before sending to the client. This frees up Gunicorn workers faster.
        proxy_buffering on;
        proxy_buffer_size 8k;
        proxy_buffers 8 8k;
    }

    location /admin/ {
        proxy_pass http://django_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # --- React Frontend ---
    location / {
        root /var/www/myapp;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
}
```

### Tell Django to Trust the Proxy Headers

In your `settings.py`, you must configure Django to trust the `X-Forwarded-For` and `X-Forwarded-Proto` headers that NGINX sets. Without this, `request.is_secure()` and `request.META['REMOTE_ADDR']` will be wrong.

```python
# settings/production.py

# Trust the proxy headers from NGINX
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

ALLOWED_HOSTS = ["myapp.com", "www.myapp.com"]
```

### Reusing Proxy Headers with a Snippet

Rather than repeating the same proxy headers in every location block, extract them into a reusable snippet:

```nginx
# /etc/nginx/snippets/proxy-headers.conf
proxy_set_header Host              $host;
proxy_set_header X-Real-IP         $remote_addr;
proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_connect_timeout              60s;
proxy_send_timeout                 60s;
proxy_read_timeout                 60s;
```

```nginx
# In your server block
location /api/ {
    proxy_pass http://django_backend;
    include snippets/proxy-headers.conf;
}

location /admin/ {
    proxy_pass http://django_backend;
    include snippets/proxy-headers.conf;
}
```

---

## 7. Static and Media Files

### Django Static Files

Django's `collectstatic` command gathers all static files (from your apps and `STATICFILES_DIRS`) into a single directory. NGINX serves this directory directly, bypassing Django entirely for every static file request.

```python
# settings/production.py
STATIC_URL  = "/django-static/"
STATIC_ROOT = "/var/www/myapp-static/"   # Where collectstatic puts files

MEDIA_URL  = "/media/"
MEDIA_ROOT = "/var/www/myapp-media/"     # Where user uploads are stored
```

```bash
# Run before each deployment
python manage.py collectstatic --noinput
```

```nginx
server {
    # Django's collected static files (CSS, JS, images for admin, etc.)
    location /django-static/ {
        alias /var/www/myapp-static/;
        expires 30d;
        add_header Cache-Control "public";
        access_log off;

        # Security: only serve files, never execute them
        location ~* \.(py|pyc|conf)$ {
            deny all;
        }
    }

    # User-uploaded media files
    location /media/ {
        alias /var/www/myapp-media/;
        expires 7d;
        add_header Cache-Control "public";

        # Security: prevent uploaded files from being executed as scripts
        location ~* \.(php|py|pl|sh|cgi)$ {
            deny all;
        }
    }
}
```

> **Note:** Serving user-uploaded files directly from NGINX is fine for most apps, but if you need access control on media files (e.g., only authenticated users can view uploads), you must serve them through Django using `X-Accel-Redirect`. Django checks auth, then tells NGINX to serve the file without the response passing back through Django.

### X-Accel-Redirect for Protected Media

```python
# views.py — Protected file download
from django.http import HttpResponse

def serve_protected_file(request, filename):
    if not request.user.is_authenticated:
        return HttpResponse(status=403)

    response = HttpResponse()
    response["X-Accel-Redirect"] = f"/protected-media/{filename}"
    response["Content-Type"] = ""   # Let NGINX set the content type
    return response
```

```nginx
# Internal location — NGINX serves it, but it is not publicly accessible
location /protected-media/ {
    internal;                           # Only accessible via X-Accel-Redirect
    alias /var/www/myapp-media/;
}

location /media/ {
    # Public URL routes through Django first for auth check
    proxy_pass http://django_backend;
    include snippets/proxy-headers.conf;
}
```

---

## 8. SSL/TLS with Let's Encrypt

All production traffic must use HTTPS. Let's Encrypt provides free, automatically-renewing SSL certificates.

### Install Certbot

```bash
sudo apt install certbot python3-certbot-nginx
```

### Obtain a Certificate

```bash
# Certbot automatically edits your NGINX config to add SSL
sudo certbot --nginx -d myapp.com -d www.myapp.com

# Certbot sets up a cron job for auto-renewal. Test it:
sudo certbot renew --dry-run
```

### Manual SSL Configuration (what Certbot produces, annotated)

```nginx
server {
    listen 80;
    server_name myapp.com www.myapp.com;

    # Redirect all HTTP traffic to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    http2 on;                          # Enable HTTP/2 for multiplexing and performance
    server_name myapp.com www.myapp.com;

    # --- SSL Certificate ---
    ssl_certificate     /etc/letsencrypt/live/myapp.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/myapp.com/privkey.pem;

    # --- SSL Protocol and Cipher Configuration ---
    # Modern config — supports TLS 1.2 and 1.3 only
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;     # Let client pick (better for TLS 1.3)

    # --- SSL Session Caching ---
    # Caches SSL session parameters to avoid full TLS handshake on every request
    ssl_session_cache   shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_session_tickets off;           # Disable for forward secrecy

    # --- OCSP Stapling ---
    # NGINX fetches and caches the certificate revocation status,
    # attaching it to the TLS handshake. Faster for clients.
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/letsencrypt/live/myapp.com/chain.pem;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;

    # Your location blocks go here...
}
```

### HSTS — Force HTTPS in Browsers

Once you are confident HTTPS is working, add HTTP Strict Transport Security. This tells browsers to never make HTTP requests to your domain, even if a user types `http://`.

```nginx
# Add to the SSL server block
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
```

> **Warning:** Start with a short `max-age` (e.g., `max-age=300`) while testing, then increase to `31536000` (1 year) once you are sure SSL works. HSTS with a long max-age is very hard to undo if you make a mistake.

---

## 9. Security Hardening

### Hide the NGINX Version

```nginx
# In http {} block
server_tokens off;   # Prevents NGINX from showing its version in error pages and headers
```

### Security Headers

```nginx
# In the server {} block (SSL server)

# Prevents clickjacking attacks (your site won't load inside an iframe on other domains)
add_header X-Frame-Options "SAMEORIGIN" always;

# Prevents MIME-type sniffing (browsers trust the Content-Type header)
add_header X-Content-Type-Options "nosniff" always;

# Controls how much referrer information is sent
add_header Referrer-Policy "strict-origin-when-cross-origin" always;

# Controls what browser features are available (camera, microphone, etc.)
add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;

# Content Security Policy — prevents XSS by whitelisting sources of content
# Tune this for your app's actual needs
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self';" always;

# HSTS (only on HTTPS server block)
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

### Block Common Attack Patterns

```nginx
server {
    # Block requests with no Host header (common in scan traffic)
    if ($host = "") {
        return 444;   # 444 = close the connection without a response
    }

    # Block common vulnerability scanners looking for WordPress, PHP, etc.
    location ~* \.(php|asp|aspx|jsp|cgi)$ {
        deny all;
    }

    # Block hidden files (.git, .env, .htaccess)
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }

    # Block access to Python/Django internals
    location ~* (settings\.py|wsgi\.py|manage\.py) {
        deny all;
    }

    # Block common backup/config file extensions
    location ~* \.(bak|config|sql|fla|psd|ini|log|sh|inc|swp|dist)$ {
        deny all;
    }
}
```

### Limit Request Size

```nginx
# In http {} or server {} block
# Prevents large file uploads or request body attacks
client_max_body_size 10M;   # Adjust to your app's largest expected upload

# For an API with no file uploads, set this small
# client_max_body_size 1M;
```

---

## 10. Performance Tuning

### Worker Processes and Connections

```nginx
# nginx.conf — top level

# Set to number of CPU cores on the server (auto detects automatically)
worker_processes auto;

events {
    # Maximum simultaneous connections per worker process
    # Total connections = worker_processes × worker_connections
    worker_connections 1024;

    # Accept multiple connections at once (improves performance under load)
    multi_accept on;
}
```

### Connection Optimizations

```nginx
http {
    # Sends file contents directly from OS kernel without copying to userspace.
    # Significantly faster for serving static files.
    sendfile on;

    # Optimizes sendfile by sending headers and file data in one packet
    tcp_nopush on;

    # Reduces latency for small packets
    tcp_nodelay on;

    # How long to keep an idle keep-alive connection open
    keepalive_timeout 65;

    # Maximum number of requests per keep-alive connection
    keepalive_requests 100;

    # How long to wait for the client to send the request headers
    client_header_timeout 10;
    client_body_timeout 10;

    # How long to wait for the client to receive the response
    send_timeout 10;
}
```

### Upstream Keep-Alive

Keep connections open between NGINX and Gunicorn to avoid reconnecting on every request:

```nginx
upstream django_backend {
    server 127.0.0.1:8000;

    # Keep up to 32 idle connections to the upstream server
    keepalive 32;
}

# In the location block that proxies to Django:
location /api/ {
    proxy_pass http://django_backend;
    proxy_http_version 1.1;                    # Required for keep-alive
    proxy_set_header Connection "";            # Clear Connection header for keep-alive
    include snippets/proxy-headers.conf;
}
```

---

## 11. Gzip and Brotli Compression

Compression dramatically reduces the size of text responses (HTML, CSS, JS, JSON, XML) sent to clients.

### Gzip (Built-in)

```nginx
http {
    gzip on;

    # Minimum response size to compress (don't compress tiny responses)
    gzip_min_length 1024;

    # Compression level: 1 (fastest) to 9 (most compressed). 4-6 is a good balance.
    gzip_comp_level 5;

    # Compress these MIME types (text/html is always compressed)
    gzip_types
        text/plain
        text/css
        text/javascript
        application/javascript
        application/json
        application/xml
        application/rss+xml
        image/svg+xml
        font/woff
        font/woff2;

    # Add Vary: Accept-Encoding so CDNs cache compressed and uncompressed separately
    gzip_vary on;

    # Compress responses from proxied upstream servers (Django)
    gzip_proxied any;

    # Disable gzip for old IE browsers that don't support it correctly
    gzip_disable "msie6";
}
```

### Brotli (Better Compression, Requires Module)

Brotli compresses 15-25% better than gzip for text content. It requires the `ngx_brotli` module, which is not compiled into standard NGINX.

```bash
# On Ubuntu, install from the nginx-extras package which includes the module
sudo apt install nginx-extras
```

```nginx
http {
    brotli on;
    brotli_comp_level 6;
    brotli_types
        text/plain
        text/css
        application/json
        application/javascript
        text/javascript
        image/svg+xml
        font/woff
        font/woff2;
}
```

---

## 12. Caching

### Browser Caching — Cache-Control Headers

Different resources should have different cache lifetimes:

```nginx
server {
    # React build static files (hashed filenames — safe to cache forever)
    location /static/ {
        root /var/www/myapp;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # index.html — must never be cached so users always get the latest shell
    location = / {
        root /var/www/myapp;
        try_files /index.html =404;
        expires -1;
        add_header Cache-Control "no-store, no-cache, must-revalidate";
    }

    # Media files (user uploads)
    location /media/ {
        alias /var/www/myapp-media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # API responses — don't cache (let Django control its own Cache-Control headers)
    location /api/ {
        proxy_pass http://django_backend;
        include snippets/proxy-headers.conf;
    }
}
```

### NGINX Proxy Cache — Cache Django Responses in NGINX

For API endpoints that return the same data for many users (e.g., product listings), NGINX can cache the Django response and serve subsequent requests from cache, entirely skipping Gunicorn.

```nginx
http {
    # Define where NGINX stores the cached responses
    # levels=1:2 — two-level directory structure for file distribution
    # keys_zone=django_cache:10m — 10MB of memory for cache keys
    # max_size=1g — max disk space for cached content
    # inactive=60m — remove items not accessed in 60 minutes
    proxy_cache_path /var/cache/nginx/django
        levels=1:2
        keys_zone=django_cache:10m
        max_size=1g
        inactive=60m
        use_temp_path=off;
}

server {
    location /api/products/ {
        proxy_pass http://django_backend;
        include snippets/proxy-headers.conf;

        # Enable caching for this location
        proxy_cache django_cache;

        # Cache key — unique per method, host, and URI
        proxy_cache_key "$request_method$host$request_uri";

        # Cache 200 responses for 5 minutes, 404 for 1 minute
        proxy_cache_valid 200 5m;
        proxy_cache_valid 404 1m;

        # Serve stale cache while revalidating in background
        proxy_cache_background_update on;
        proxy_cache_lock on;

        # Header showing if response came from cache (HIT, MISS, BYPASS)
        add_header X-Cache-Status $upstream_cache_status;
    }
}
```

---

## 13. WebSocket Support

Django Channels enables WebSockets in Django. WebSockets require a different NGINX configuration because they use a persistent connection with protocol upgrade.

### Django Channels Setup

Django Channels runs with Daphne or Uvicorn as the ASGI server, often on a different port from Gunicorn.

```bash
# Run Daphne for WebSocket support on port 8001
daphne -b 127.0.0.1 -p 8001 config.asgi:application
```

### NGINX WebSocket Proxy

```nginx
upstream django_asgi {
    server 127.0.0.1:8001;   # Daphne or Uvicorn
}

server {
    # WebSocket connections at /ws/
    location /ws/ {
        proxy_pass http://django_asgi;

        # Required for WebSocket protocol upgrade
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Standard proxy headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket connections are long-lived — increase timeouts
        proxy_read_timeout  3600s;   # 1 hour
        proxy_send_timeout  3600s;
    }

    # Regular HTTP requests go to Gunicorn as usual
    location /api/ {
        proxy_pass http://django_backend;
        include snippets/proxy-headers.conf;
    }
}
```

### Combined ASGI Setup (Uvicorn handles both HTTP and WebSocket)

If you run Django with Uvicorn instead of Gunicorn, a single upstream handles both HTTP and WebSocket:

```nginx
upstream django_asgi {
    server 127.0.0.1:8000;   # Uvicorn handles HTTP + WS
}

server {
    # HTTP API
    location /api/ {
        proxy_pass http://django_asgi;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        include snippets/proxy-headers.conf;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://django_asgi;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        include snippets/proxy-headers.conf;
        proxy_read_timeout 3600s;
    }
}
```

---

## 14. Rate Limiting

Rate limiting protects your backend from abuse, brute-force attacks, and accidental flooding.

```nginx
http {
    # Define rate limit zones in the http {} block
    # $binary_remote_addr — the client's IP address in binary format
    # zone=name:10m — store rate limit state in 10MB of shared memory
    # rate=10r/s — allow maximum 10 requests per second per IP

    # General API rate limit
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

    # Stricter limit for auth endpoints (login, password reset)
    limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=5r/m;

    # Limit for admin area
    limit_req_zone $binary_remote_addr zone=admin_limit:10m rate=20r/m;
}

server {
    location /api/ {
        # burst=20 — allow a burst of 20 requests above the rate
        # nodelay — don't add artificial delay within the burst
        limit_req zone=api_limit burst=20 nodelay;
        limit_req_status 429;   # Return 429 Too Many Requests when rate exceeded

        proxy_pass http://django_backend;
        include snippets/proxy-headers.conf;
    }

    location /api/auth/ {
        # Strict limit on auth endpoints — 5 requests per minute
        limit_req zone=auth_limit burst=5 nodelay;
        limit_req_status 429;

        proxy_pass http://django_backend;
        include snippets/proxy-headers.conf;
    }

    location /admin/ {
        limit_req zone=admin_limit burst=10 nodelay;
        limit_req_status 429;

        proxy_pass http://django_backend;
        include snippets/proxy-headers.conf;
    }
}
```

### Returning a JSON Error for Rate-Limiting

By default, NGINX returns an HTML error page for 429 responses. If your frontend expects JSON:

```nginx
server {
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;
        limit_req_status 429;

        error_page 429 = @rate_limit_json;

        proxy_pass http://django_backend;
        include snippets/proxy-headers.conf;
    }

    location @rate_limit_json {
        default_type application/json;
        return 429 '{"error": "Rate limit exceeded. Please try again later."}';
    }
}
```

---

## 15. Protecting the /metrics Endpoint

The `/metrics` endpoint exposes detailed internal information about your application and must not be publicly accessible. NGINX is the ideal place to enforce this restriction.

### Restrict by IP (Recommended)

```nginx
server {
    # Prometheus /metrics endpoint — restricted to internal network only
    location /metrics {
        # Allow your Prometheus server's internal IP
        allow 10.0.1.50;         # Prometheus server
        allow 10.0.0.0/8;        # Entire internal network (if needed)
        allow 172.16.0.0/12;     # Docker default network
        allow 127.0.0.1;         # Localhost

        # Deny everyone else — returns 403 Forbidden
        deny all;

        proxy_pass http://django_backend;
        include snippets/proxy-headers.conf;
    }
}
```

### Using Bearer Token Authentication

```nginx
server {
    location /metrics {
        if ($http_authorization != "Bearer your-secret-metrics-token-here") {
            return 403;
        }

        proxy_pass http://django_backend;
        include snippets/proxy-headers.conf;
    }
}
```

### Combine Both for Defense in Depth

```nginx
server {
    location /metrics {
        allow 10.0.1.50;
        deny all;

        if ($http_authorization != "Bearer your-secret-metrics-token-here") {
            return 403;
        }

        proxy_pass http://django_backend;
        include snippets/proxy-headers.conf;
    }
}
```

---

## 16. Logging

### Log Formats

```nginx
http {
    # Default combined log format
    log_format combined '$remote_addr - $remote_user [$time_local] '
                        '"$request" $status $body_bytes_sent '
                        '"$http_referer" "$http_user_agent"';

    # JSON format — easier to parse with log aggregators (Datadog, Loki, ELK)
    log_format json_access escape=json
        '{"time":"$time_iso8601",'
        '"remote_addr":"$remote_addr",'
        '"method":"$request_method",'
        '"uri":"$request_uri",'
        '"status":$status,'
        '"bytes_sent":$bytes_sent,'
        '"request_time":$request_time,'
        '"upstream_response_time":"$upstream_response_time",'
        '"http_referrer":"$http_referer",'
        '"http_user_agent":"$http_user_agent"}';

    access_log /var/log/nginx/access.log json_access;
    error_log  /var/log/nginx/error.log warn;
}
```

### Per-Server Logging

```nginx
server {
    server_name myapp.com;

    access_log /var/log/nginx/myapp-access.log json_access;
    error_log  /var/log/nginx/myapp-error.log warn;

    # Suppress logs for noisy but unimportant requests
    location = /favicon.ico {
        access_log off;
        log_not_found off;
    }

    location /static/ {
        access_log off;   # Static files — don't log to save disk space
    }
}
```

### Log Rotation

NGINX does not rotate logs itself. Use `logrotate` (installed by default on most Linux distros):

```
# /etc/logrotate.d/nginx
/var/log/nginx/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    sharedscripts
    postrotate
        # Reopen log files after rotation
        if [ -f /var/run/nginx.pid ]; then
            kill -USR1 `cat /var/run/nginx.pid`
        fi
    endscript
}
```

---

## 17. Health Checks

NGINX can expose a health check endpoint used by load balancers, Kubernetes probes, and monitoring systems:

```nginx
server {
    # Simple health check — returns 200 OK without hitting the backend
    location = /nginx-health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }

    # Full app health check — proxies to Django's health endpoint
    location = /health/ {
        proxy_pass http://django_backend;
        include snippets/proxy-headers.conf;
        access_log off;
        add_header Cache-Control "no-cache";
    }
}
```

### Django Health Check View

```python
# apps/core/views.py
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    """Simple health check — verifies DB is reachable."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        db_status = "ok"
    except Exception as e:
        db_status = str(e)

    status = 200 if db_status == "ok" else 503
    return JsonResponse({"status": "ok", "db": db_status}, status=status)
```

```python
# urls.py
from apps.core.views import health_check
urlpatterns = [
    path("health/", health_check, name="health-check"),
    ...
]
```

---

## 18. Docker Compose Full Stack

Here is a complete, production-ready Docker Compose configuration tying NGINX, Django, React, PostgreSQL, Redis, and Prometheus together.

### Project Structure

```
myproject/
├── docker-compose.yml
├── docker-compose.override.yml      ← Development overrides
├── nginx/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── conf.d/
│       └── myapp.conf
├── backend/                         ← Django project
│   ├── Dockerfile
│   ├── gunicorn.conf.py
│   └── ...
├── frontend/                        ← React project
│   ├── Dockerfile
│   └── ...
└── provisioning/
    └── prometheus/
        └── prometheus.yml
```

### nginx/Dockerfile

```dockerfile
FROM nginx:1.25-alpine

# Remove default config
RUN rm /etc/nginx/conf.d/default.conf

# Copy our config
COPY nginx.conf /etc/nginx/nginx.conf
COPY conf.d/ /etc/nginx/conf.d/

RUN mkdir -p /var/cache/nginx /var/log/nginx

EXPOSE 80 443
```

### nginx/nginx.conf

```nginx
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    server_tokens off;

    gzip on;
    gzip_min_length 1024;
    gzip_comp_level 5;
    gzip_types text/plain text/css application/json application/javascript text/javascript image/svg+xml;
    gzip_vary on;
    gzip_proxied any;

    log_format json_access escape=json
        '{"time":"$time_iso8601","remote_addr":"$remote_addr","method":"$request_method",'
        '"uri":"$request_uri","status":$status,"bytes_sent":$bytes_sent,'
        '"request_time":$request_time,"upstream_time":"$upstream_response_time"}';

    access_log /var/log/nginx/access.log json_access;

    include /etc/nginx/conf.d/*.conf;
}
```

### nginx/conf.d/myapp.conf

```nginx
upstream django_backend {
    server backend:8000;
    keepalive 32;
}

limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=5r/m;

server {
    listen 80;
    server_name _;

    client_max_body_size 20M;

    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Health check
    location = /health/ {
        proxy_pass http://django_backend;
        access_log off;
    }

    # Prometheus metrics — restrict to Docker internal network
    location /metrics {
        allow 172.16.0.0/12;
        allow 10.0.0.0/8;
        allow 127.0.0.1;
        deny all;
        proxy_pass http://django_backend;
    }

    # Django API
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;
        limit_req_status 429;

        proxy_pass http://django_backend;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Auth endpoints — stricter rate limit
    location /api/auth/ {
        limit_req zone=auth_limit burst=5 nodelay;
        limit_req_status 429;

        proxy_pass http://django_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Django Admin
    location /admin/ {
        proxy_pass http://django_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Django collected static files
    location /django-static/ {
        alias /var/www/django-static/;
        expires 30d;
        add_header Cache-Control "public";
        access_log off;
    }

    # Media files
    location /media/ {
        alias /var/www/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # React hashed static assets — cache forever
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        root /var/www/frontend;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # React frontend (SPA catch-all)
    location / {
        root /var/www/frontend;
        index index.html;
        try_files $uri $uri/ /index.html;

        location = /index.html {
            expires -1;
            add_header Cache-Control "no-store, no-cache, must-revalidate";
        }
    }
}
```

### docker-compose.yml

```yaml
version: "3.9"

x-django-env: &django-env
  DJANGO_SETTINGS_MODULE: config.settings.production
  DATABASE_URL: postgres://myuser:mypassword@db:5432/mydb
  REDIS_URL: redis://redis:6379/0
  PROMETHEUS_MULTIPROC_DIR: /tmp/prometheus_multiproc
  SECRET_KEY: ${DJANGO_SECRET_KEY}

services:

  # --- NGINX ---
  nginx:
    build: ./nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - django_static:/var/www/django-static:ro
      - media_files:/var/www/media:ro
      - frontend_build:/var/www/frontend:ro
    depends_on:
      - backend
    restart: unless-stopped

  # --- Django Backend ---
  backend:
    build: ./backend
    environment:
      <<: *django-env
    volumes:
      - django_static:/app/staticfiles
      - media_files:/app/media
      - prometheus_multiproc:/tmp/prometheus_multiproc
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    command: >
      sh -c "rm -rf /tmp/prometheus_multiproc/* &&
             python manage.py migrate --noinput &&
             python manage.py collectstatic --noinput &&
             gunicorn config.wsgi:application
               --workers 4
               --config gunicorn.conf.py
               --bind 0.0.0.0:8000"
    restart: unless-stopped

  # --- Celery Worker ---
  celery:
    build: ./backend
    environment:
      <<: *django-env
    volumes:
      - media_files:/app/media
      - prometheus_multiproc:/tmp/prometheus_multiproc
    command: celery -A config worker -l info -c 2
    depends_on:
      - db
      - redis
    restart: unless-stopped

  # --- Celery Beat ---
  celery-beat:
    build: ./backend
    environment:
      <<: *django-env
    command: celery -A config beat -l info
    depends_on:
      - db
      - redis
    restart: unless-stopped

  # --- React Frontend Build ---
  # Builds and exits; NGINX serves the output via a shared volume
  frontend:
    build:
      context: ./frontend
      target: builder
    volumes:
      - frontend_build:/app/build

  # --- PostgreSQL ---
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: mydb
      POSTGRES_USER: myuser
      POSTGRES_PASSWORD: mypassword
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U myuser -d mydb"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  # --- Redis ---
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

  # --- Prometheus ---
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./provisioning/prometheus:/etc/prometheus:ro
      - prometheus_data:/prometheus
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
      - "--storage.tsdb.retention.time=15d"
    restart: unless-stopped

  # --- Grafana ---
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD:-changeme}
    depends_on:
      - prometheus
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  django_static:
  media_files:
  frontend_build:
  prometheus_multiproc:
  prometheus_data:
  grafana_data:
```

### backend/Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /tmp/prometheus_multiproc

EXPOSE 8000
```

### backend/gunicorn.conf.py

```python
# gunicorn.conf.py
import os
from prometheus_client import multiprocess

bind = "0.0.0.0:8000"
workers = 4
worker_class = "sync"
preload_app = False     # IMPORTANT: must be False for prometheus multiprocess mode
timeout = 30
keepalive = 2

def child_exit(server, worker):
    """Clean up prometheus multiprocess files when a worker exits."""
    multiprocess.mark_process_dead(worker.pid)
```

### frontend/Dockerfile

```dockerfile
# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Stage 2: Export build artifacts to a Docker volume
# NGINX mounts this volume and serves files from it
FROM scratch AS artifacts
COPY --from=builder /app/build /
```

---

## 19. Kubernetes Ingress with NGINX

In Kubernetes, NGINX runs as an **Ingress Controller** — a cluster-wide resource that routes traffic to your pods.

### Install the NGINX Ingress Controller

```bash
# Using Helm
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace
```

### Ingress Resource for Django + React

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp-ingress
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/use-regex: "true"
    nginx.ingress.kubernetes.io/limit-rps: "10"
    nginx.ingress.kubernetes.io/limit-connections: "20"
    nginx.ingress.kubernetes.io/proxy-body-size: "20m"
    nginx.ingress.kubernetes.io/enable-cors: "true"
    nginx.ingress.kubernetes.io/cors-allow-origin: "https://myapp.com"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"

spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - myapp.com
        - www.myapp.com
      secretName: myapp-tls
  rules:
    - host: myapp.com
      http:
        paths:
          # Django API
          - path: /api/
            pathType: Prefix
            backend:
              service:
                name: django-service
                port:
                  number: 8000
          # Django Admin
          - path: /admin/
            pathType: Prefix
            backend:
              service:
                name: django-service
                port:
                  number: 8000
          # Django static files
          - path: /django-static/
            pathType: Prefix
            backend:
              service:
                name: django-service
                port:
                  number: 8000
          # React Frontend (catch-all)
          - path: /
            pathType: Prefix
            backend:
              service:
                name: frontend-service
                port:
                  number: 80
```

### ConfigMap for Global NGINX Settings

```yaml
# nginx-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ingress-nginx-controller
  namespace: ingress-nginx
data:
  use-gzip: "true"
  gzip-level: "5"
  keep-alive: "65"
  keep-alive-requests: "100"
  proxy-connect-timeout: "60"
  proxy-read-timeout: "60"
  proxy-send-timeout: "60"
  log-format-upstream: '{"time":"$time_iso8601","addr":"$remote_addr","method":"$request_method","uri":"$request_uri","status":$status,"duration":$request_time}'
```

### Kubernetes Deployment with Prometheus Multiprocess

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
        # Clear stale multiproc files on every startup
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

## 20. Multiple Environments

### Development Override

```yaml
# docker-compose.override.yml — automatically loaded in development
services:
  nginx:
    volumes:
      - ./frontend/build:/var/www/frontend:ro
    ports:
      - "80:80"   # No HTTPS in dev

  backend:
    volumes:
      - ./backend:/app   # Mount source code for live reload
    command: >
      sh -c "python manage.py migrate &&
             python manage.py runserver 0.0.0.0:8000"
    environment:
      DJANGO_SETTINGS_MODULE: config.settings.development
      DEBUG: "True"
```

### Makefile for Common Tasks

```makefile
# Makefile
.PHONY: dev prod build deploy

dev:
	docker compose up

prod:
	docker compose -f docker-compose.yml up -d

build:
	docker compose build

deploy:
	docker compose pull
	docker compose up -d --no-deps --build backend frontend nginx

logs:
	docker compose logs -f nginx backend

nginx-test:
	docker compose exec nginx nginx -t

nginx-reload:
	docker compose exec nginx nginx -s reload
```

---

## 21. Common Errors and How to Fix Them

### 502 Bad Gateway

NGINX cannot reach Gunicorn. Possible causes:

```bash
# Check if Gunicorn is running
ps aux | grep gunicorn

# Check if it's listening on the right address
ss -tlnp | grep 8000

# Check NGINX error log
tail -f /var/log/nginx/error.log

# Check Gunicorn log
journalctl -u gunicorn -f
```

**Fix:** Ensure Gunicorn is running and the `proxy_pass` address in NGINX exactly matches what Gunicorn is listening on.

### 413 Request Entity Too Large

The request body exceeded `client_max_body_size`.

```nginx
server {
    client_max_body_size 50M;   # Allow up to 50MB uploads
}
```

### 504 Gateway Timeout

Gunicorn took too long to respond. Either the Django view is slow, or timeouts are too short.

```nginx
location /api/ {
    proxy_read_timeout 120s;   # Increase from default 60s
    proxy_send_timeout 120s;
}
```

### React Router Returns 404 on Direct URL Access

Missing `try_files` in the React location block.

```nginx
location / {
    root /var/www/myapp;
    try_files $uri $uri/ /index.html;   # This line is essential for SPA routing
}
```

### Mixed Content Warning (HTTP resources on HTTPS page)

Django is generating URLs with `http://` instead of `https://`. The proxy headers are not being trusted.

```python
# settings/production.py
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
```

### CORS Errors from the Frontend

Add `django-cors-headers` to Django if the frontend and backend are on different origins:

```python
# settings/production.py
INSTALLED_APPS += ["corsheaders"]
MIDDLEWARE.insert(0, "corsheaders.middleware.CorsMiddleware")

CORS_ALLOWED_ORIGINS = [
    "https://myapp.com",
    "https://www.myapp.com",
]
CORS_ALLOW_CREDENTIALS = True
```

### `nginx -t` Fails: "unknown directive"

A module required for a directive is not compiled into your NGINX build. Check with `nginx -V` which modules are included. Brotli, for example, requires a separate module not present in the default build.

### Static Files Return 403 Forbidden

The NGINX worker process (`www-data` or `nginx` user) does not have permission to read the files.

```bash
# Fix permissions
sudo chown -R www-data:www-data /var/www/myapp
sudo chmod -R 755 /var/www/myapp
```

---

## 22. Full Production Configuration Reference

This is a complete, annotated NGINX configuration for a production Django + React deployment with SSL, security, rate limiting, compression, and metrics protection.

```nginx
# /etc/nginx/nginx.conf

user www-data;
worker_processes auto;
pid /run/nginx.pid;

worker_rlimit_nofile 65535;

events {
    worker_connections 4096;
    multi_accept on;
    use epoll;                  # Linux-specific, fastest event model
}

http {
    # --- Basic Settings ---
    include      /etc/nginx/mime.types;
    default_type application/octet-stream;
    charset      utf-8;

    sendfile    on;
    tcp_nopush  on;
    tcp_nodelay on;
    server_tokens off;

    keepalive_timeout     65;
    keepalive_requests    100;
    client_max_body_size  20M;

    # --- Timeouts ---
    client_body_timeout   12;
    client_header_timeout 12;
    send_timeout          10;

    # --- Gzip ---
    gzip              on;
    gzip_vary         on;
    gzip_proxied      any;
    gzip_comp_level   5;
    gzip_min_length   1024;
    gzip_types
        text/plain text/css text/javascript text/xml
        application/json application/javascript application/xml
        application/rss+xml image/svg+xml font/woff font/woff2;

    # --- Proxy Cache ---
    proxy_cache_path /var/cache/nginx levels=1:2
        keys_zone=api_cache:10m max_size=500m inactive=30m use_temp_path=off;

    # --- Rate Limiting Zones ---
    limit_req_zone $binary_remote_addr zone=api:10m      rate=10r/s;
    limit_req_zone $binary_remote_addr zone=auth:10m     rate=5r/m;
    limit_req_zone $binary_remote_addr zone=admin:10m    rate=20r/m;

    # --- Logging ---
    log_format json_combined escape=json
        '{"time":"$time_iso8601","remote_addr":"$remote_addr",'
        '"method":"$request_method","uri":"$request_uri","status":$status,'
        '"bytes_sent":$bytes_sent,"duration":$request_time,'
        '"upstream_time":"$upstream_response_time",'
        '"user_agent":"$http_user_agent"}';

    access_log /var/log/nginx/access.log json_combined;
    error_log  /var/log/nginx/error.log  warn;

    # --- Upstream ---
    upstream django_backend {
        server 127.0.0.1:8000;
        keepalive 32;
    }

    # --- HTTP → HTTPS Redirect ---
    server {
        listen 80 default_server;
        listen [::]:80 default_server;
        server_name _;
        return 301 https://$host$request_uri;
    }

    # --- Main HTTPS Server ---
    server {
        listen 443 ssl;
        http2 on;
        server_name myapp.com www.myapp.com;

        # --- SSL ---
        ssl_certificate     /etc/letsencrypt/live/myapp.com/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/myapp.com/privkey.pem;
        ssl_protocols       TLSv1.2 TLSv1.3;
        ssl_ciphers         ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305;
        ssl_prefer_server_ciphers off;
        ssl_session_cache   shared:SSL:10m;
        ssl_session_timeout 1d;
        ssl_session_tickets off;
        ssl_stapling        on;
        ssl_stapling_verify on;
        ssl_trusted_certificate /etc/letsencrypt/live/myapp.com/chain.pem;
        resolver 8.8.8.8 8.8.4.4 valid=300s;

        # --- Security Headers ---
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;
        add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;
        add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' wss:;" always;

        # --- Block Bad Actors ---
        location ~ /\. { deny all; }
        location ~* \.(php|asp|aspx|jsp)$ { deny all; }
        location ~* \.(bak|config|sql|log|sh|swp)$ { deny all; }

        # --- Health Check ---
        location = /health/ {
            proxy_pass http://django_backend;
            access_log off;
        }

        # --- Prometheus Metrics (internal only) ---
        location /metrics {
            allow 10.0.0.0/8;
            allow 172.16.0.0/12;
            allow 127.0.0.1;
            deny all;
            proxy_pass http://django_backend;
        }

        # --- Django Admin ---
        location /admin/ {
            limit_req zone=admin burst=10 nodelay;
            limit_req_status 429;

            proxy_pass         http://django_backend;
            proxy_http_version 1.1;
            proxy_set_header   Connection "";
            proxy_set_header   Host              $host;
            proxy_set_header   X-Real-IP         $remote_addr;
            proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
            proxy_set_header   X-Forwarded-Proto $scheme;
        }

        # --- Auth API ---
        location /api/auth/ {
            limit_req zone=auth burst=5 nodelay;
            limit_req_status 429;

            proxy_pass         http://django_backend;
            proxy_http_version 1.1;
            proxy_set_header   Connection "";
            proxy_set_header   Host              $host;
            proxy_set_header   X-Real-IP         $remote_addr;
            proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
            proxy_set_header   X-Forwarded-Proto $scheme;
            proxy_read_timeout 30s;
        }

        # --- Django API ---
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            limit_req_status 429;

            proxy_pass         http://django_backend;
            proxy_http_version 1.1;
            proxy_set_header   Connection "";
            proxy_set_header   Host              $host;
            proxy_set_header   X-Real-IP         $remote_addr;
            proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
            proxy_set_header   X-Forwarded-Proto $scheme;
            proxy_connect_timeout 60s;
            proxy_read_timeout    60s;
            proxy_send_timeout    60s;
            proxy_buffering    on;
            proxy_buffer_size  8k;
            proxy_buffers      8 8k;
        }

        # --- Django Static Files ---
        location /django-static/ {
            alias /var/www/django-static/;
            expires 30d;
            add_header Cache-Control "public";
            access_log off;
        }

        # --- Media Files ---
        location /media/ {
            alias /var/www/media/;
            expires 7d;
            add_header Cache-Control "public";
        }

        # --- Favicon ---
        location = /favicon.ico {
            root /var/www/myapp;
            access_log off;
            log_not_found off;
        }

        # --- React Hashed Static Assets ---
        location ~* \.(js|css|woff|woff2|ttf|eot|ico)$ {
            root /var/www/myapp;
            expires 1y;
            add_header Cache-Control "public, immutable";
            access_log off;
        }

        # --- React Frontend (SPA catch-all) ---
        location / {
            root /var/www/myapp;
            index index.html;
            try_files $uri $uri/ /index.html;

            location = /index.html {
                expires -1;
                add_header Cache-Control "no-store, no-cache, must-revalidate";
            }
        }
    }
}
```

---

## 23. Checklist

Use this checklist when deploying or reviewing an NGINX setup for Django + React.

### Initial Setup

- [ ] NGINX installed and running (`systemctl status nginx`)
- [ ] Default site disabled or replaced
- [ ] `nginx -t` passes without errors before every reload
- [ ] Config split into logical files in `conf.d/` or `sites-available/`

### React Frontend

- [ ] React app built with `npm run build`
- [ ] Build output copied to web root (`/var/www/myapp`)
- [ ] `try_files $uri $uri/ /index.html` is present (required for React Router)
- [ ] `index.html` is not cached (`Cache-Control: no-store`)
- [ ] Hashed static assets are cached aggressively (`Cache-Control: public, immutable, max-age=31536000`)

### Django Backend

- [ ] Gunicorn is running and bound to `127.0.0.1:8000` or a Unix socket
- [ ] `proxy_pass` in NGINX matches the Gunicorn address exactly
- [ ] All required proxy headers are set (`Host`, `X-Real-IP`, `X-Forwarded-For`, `X-Forwarded-Proto`)
- [ ] Django has `SECURE_PROXY_SSL_HEADER` and `USE_X_FORWARDED_HOST` configured
- [ ] `proxy_buffering on` is set (frees Gunicorn workers faster)
- [ ] Upstream `keepalive` is configured (avoids reconnecting per request)

### Static and Media Files

- [ ] `python manage.py collectstatic` is run before deployment
- [ ] `/django-static/` location serves from `STATIC_ROOT` via `alias`
- [ ] `/media/` location serves from `MEDIA_ROOT` via `alias`
- [ ] Static file directories have correct permissions (`www-data` user)
- [ ] Executable file types (`.php`, `.py`) are blocked in static/media directories

### SSL/TLS

- [ ] Certificate obtained (Let's Encrypt via `certbot --nginx`)
- [ ] HTTP (port 80) redirects to HTTPS with `301`
- [ ] HTTP/2 is enabled (`http2 on`)
- [ ] TLS 1.0 and 1.1 are disabled (only 1.2 and 1.3 allowed)
- [ ] OCSP stapling is enabled
- [ ] SSL session caching is configured
- [ ] Certbot auto-renewal is set up (`certbot renew --dry-run` passes)

### Security Headers

- [ ] `server_tokens off` hides NGINX version
- [ ] `Strict-Transport-Security` header is set (HSTS)
- [ ] `X-Frame-Options` header is set
- [ ] `X-Content-Type-Options: nosniff` is set
- [ ] `Referrer-Policy` is set
- [ ] `Content-Security-Policy` is configured for your app's actual sources
- [ ] Hidden files (`/.*`) are blocked
- [ ] Script extensions (`.php`, `.asp`, etc.) are blocked

### Rate Limiting

- [ ] `limit_req_zone` defined in `http {}` block
- [ ] `/api/` has a rate limit
- [ ] Auth endpoints (`/api/auth/`) have a stricter rate limit
- [ ] Admin has a rate limit
- [ ] `limit_req_status 429` is set

### Performance

- [ ] `sendfile`, `tcp_nopush`, `tcp_nodelay` are enabled
- [ ] Gzip compression is enabled for text content types
- [ ] `client_max_body_size` is appropriate for your app's uploads
- [ ] `keepalive_timeout` is set
- [ ] `worker_processes auto` is set

### Monitoring Integration

- [ ] `/metrics` endpoint is restricted by IP to Prometheus server only
- [ ] Health check endpoint (`/health/`) is accessible without auth
- [ ] NGINX access logs include request duration (`$request_time`)
- [ ] Log format is JSON for easy ingestion by log aggregators

### WebSockets (if applicable)

- [ ] `Upgrade` and `Connection` headers are set in the WebSocket location
- [ ] `proxy_read_timeout` is increased for long-lived WebSocket connections
- [ ] WebSocket path (`/ws/`) routes to the correct ASGI server (Daphne/Uvicorn)

### Docker / Kubernetes

- [ ] `PROMETHEUS_MULTIPROC_DIR` is set and the directory is cleared on startup
- [ ] Gunicorn `child_exit` hook is configured (`multiprocess.mark_process_dead`)
- [ ] `preload_app = False` in gunicorn.conf.py
- [ ] Static files are shared between backend and NGINX containers via a named volume
- [ ] NGINX container mounts static/media volumes as read-only (`:ro`)

---

*NGINX official documentation: https://nginx.org/en/docs/*
*NGINX configuration pitfalls: https://www.nginx.com/resources/wiki/start/topics/tutorials/config_pitfalls/*
*SSL configuration generator: https://ssl-config.mozilla.org/*
*Let's Encrypt: https://letsencrypt.org/docs/*