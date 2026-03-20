# Django Channels — Definitive Guide

> Django Channels extends Django to handle WebSockets, HTTP/2, and other async protocols. It lets Django maintain persistent, bidirectional connections with clients — real-time chat, live notifications, collaborative editing, dashboard updates. This guide covers every setup detail, every configuration option, every pattern, and every gotcha. Nothing is left to guessing.

---

## Table of Contents

1. [Architecture — How It Works](#architecture)
2. [Installation](#installation)
3. [Project Structure](#structure)
4. [Core Setup Files](#setup)
5. [Settings Reference](#settings)
6. [ASGI Configuration](#asgi)
7. [Routing — URLs for WebSockets](#routing)
8. [Writing Consumers](#consumers)
9. [Authentication & Middleware](#authentication)
10. [Channel Layers — Cross-Consumer Communication](#channel-layers)
11. [Groups — Broadcasting to Multiple Clients](#groups)
12. [Database Access in Async Consumers](#database)
13. [Testing WebSockets](#testing)
14. [Deployment — Daphne & Nginx](#deployment)
15. [Performance & Scaling](#performance)
16. [Security Checklist](#security)
17. [Common Patterns](#patterns)
18. [Debugging & Monitoring](#debugging)
19. [Common Errors & Fixes](#errors)
20. [Quick Reference](#reference)

---

## 1. Architecture — How It Works {#architecture}

Understanding the architecture is essential before writing a single line of code.

```
Client Browser
      │
      │  WebSocket connection: ws://example.com/ws/chat/
      ▼
  ASGI Server (Daphne/Uvicorn)
  - Handles async protocols (WebSocket, HTTP/2)
  - One process per server instance
      │
      │  Routes to appropriate Consumer
      ▼
  WebSocket Consumer
  - Async Python class handling connection lifecycle
  - connect() → accept/reject
  - receive() → handle incoming messages
  - disconnect() → cleanup
      │
      │  Cross-consumer messaging via Channel Layer
      ▼
  Channel Layer (Redis)
  - Message broker for server-to-server communication
  - Enables broadcasting to groups
  - NOT for client messages (those go directly to consumer)
      │
      │  Consumers can query Django ORM
      ▼
  Django Database
  - Accessed via database_sync_to_async() wrapper
  - Same models, same ORM as traditional Django
```

**Components and their roles:**

| Component | What It Is | Our Choice |
|---|---|---|
| **ASGI Server** | Async-capable web server that handles WebSocket protocol | Daphne (official Channels server) |
| **Consumer** | Python class handling WebSocket lifecycle (connect/receive/disconnect) | `AsyncWebsocketConsumer` or `WebsocketConsumer` |
| **Routing** | Maps WebSocket URLs to Consumers | `websocket_urlpatterns` in `routing.py` |
| **Channel Layer** | Message broker for cross-consumer/cross-server communication | Redis via `channels_redis` |
| **Middleware** | Auth, session handling, custom logic before consumer | `AuthMiddlewareStack`, custom middleware |

**Critical principles:**

1. **ASGI vs WSGI:** Django's traditional WSGI server (Gunicorn, uWSGI) cannot handle WebSockets. You **must** use an ASGI server (Daphne, Uvicorn) for Channels.

2. **Async by default:** Channels consumers run in async mode. Blocking calls (ORM queries, file I/O, HTTP requests) must be wrapped in `sync_to_async()` or `database_sync_to_async()`.

3. **Channel Layer is optional:** You can build simple WebSocket apps without a channel layer. You need it only when:
   - Broadcasting to multiple clients (chat rooms, notifications)
   - Sending messages from Django views to WebSocket consumers
   - Running multiple ASGI server instances

4. **Separate processes:** The ASGI server handling WebSockets is a separate OS process from your traditional WSGI server handling HTTP requests. They communicate via the database or channel layer — never shared memory.

---

## 2. Installation {#installation}

```bash
pip install channels daphne channels-redis
```

**What each package does and why you need it:**

| Package | Min Version | Purpose |
|---|---|---|
| `channels` | `4.0+` | Core WebSocket/async protocol framework for Django |
| `daphne` | `4.0+` | Official ASGI server — runs your WebSocket application |
| `channels-redis` | `4.1+` | Redis-backed channel layer for broadcasting and cross-server messaging |

Optional but recommended:

```bash
pip install msgpack  # Faster serialization for channel layer messages
```

Add all to `requirements.txt`. Pin minor versions in production.

---

## 3. Project Structure {#structure}

```
myproject/
├── manage.py
├── myproject/
│   ├── __init__.py
│   ├── asgi.py              ← ASGI application definition (replaces wsgi.py for Channels)
│   ├── wsgi.py              ← Keep this for traditional HTTP traffic via Gunicorn
│   ├── routing.py           ← WebSocket URL routing (like urls.py but for WS)
│   └── settings/
│       ├── base.py          ← INSTALLED_APPS includes 'channels'
│       ├── development.py
│       └── production.py
├── apps/
│   ├── chat/
│   │   ├── models.py        ← ChatRoom, Message models
│   │   ├── consumers.py     ← WebSocket consumers (like views.py for WS)
│   │   ├── routing.py       ← App-specific WebSocket routes
│   │   └── tests.py
│   ├── notifications/
│   │   ├── consumers.py
│   │   ├── routing.py
│   │   └── signals.py       ← Can trigger WebSocket messages from Django signals
│   └── live_updates/
│       ├── consumers.py
│       └── routing.py
└── requirements.txt
```

**Rule:** Every Django app that handles WebSockets gets its own `consumers.py` and `routing.py`. The project-level `routing.py` imports and combines them all.

---

## 4. Core Setup Files {#setup}

### File 1: Add Channels to `INSTALLED_APPS`

```python
# settings/base.py

INSTALLED_APPS = [
    # Channels MUST come before django.contrib.staticfiles
    # to override the staticfiles handler for development server
    "daphne",  # Add this at the very top
    
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    
    # Your apps
    "apps.chat",
    "apps.notifications",
    
    # Channels framework
    "channels",
]

# Tell Django to use Channels' ASGI application
ASGI_APPLICATION = "myproject.asgi.application"
```

**Critical:** `daphne` must be at the **top** of `INSTALLED_APPS`. This ensures Channels takes over from Django's default `runserver` command.

### File 2: `myproject/asgi.py`

This is the ASGI equivalent of `wsgi.py`. Create it manually if it doesn't exist.

```python
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

# Set Django settings module before importing anything Django-related
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings.base")

# Initialize Django ASGI application early to ensure AppRegistry is populated
# before importing routing which may import models
django_asgi_app = get_asgi_application()

# Import routing AFTER get_asgi_application() to avoid AppRegistryNotReady
from myproject.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    # Django's ASGI application handles traditional HTTP requests
    "http": django_asgi_app,
    
    # WebSocket connections routed through our custom URL patterns
    # AuthMiddlewareStack populates scope with user from session
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
```

**Order matters:** Call `get_asgi_application()` **before** importing any code that touches Django models. Otherwise you'll get `AppRegistryNotReady` errors.

### File 3: `myproject/routing.py`

Project-level WebSocket routing. Like `urls.py` but for WebSocket paths.

```python
from django.urls import path
from channels.routing import URLRouter

# Import app-specific WebSocket routes
from apps.chat.routing import websocket_urlpatterns as chat_ws_urls
from apps.notifications.routing import websocket_urlpatterns as notification_ws_urls

# Combine all WebSocket URL patterns
websocket_urlpatterns = [
    # URLRouter allows us to organize routes by app
    path("ws/chat/", URLRouter(chat_ws_urls)),
    path("ws/notifications/", URLRouter(notification_ws_urls)),
]
```

### File 4: App-Level Routing — `apps/chat/routing.py`

```python
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    # ws://example.com/ws/chat/room/42/
    path("room/<int:room_id>/", consumers.ChatConsumer.as_asgi()),
    
    # ws://example.com/ws/chat/private/<str:username>/
    path("private/<str:username>/", consumers.PrivateChatConsumer.as_asgi()),
]
```

**URL parameters:** Just like Django's HTTP `path()`, you can capture parameters (`<int:room_id>`) which are passed to the consumer in `self.scope["url_route"]["kwargs"]`.

---

## 5. Settings Reference {#settings}

All Channels-specific settings live in `settings.py`.

```python
# ─────────────────────────────────────────────────────────────────
# CORE CHANNELS SETTINGS
# ─────────────────────────────────────────────────────────────────

# Tell Django which ASGI application to use
ASGI_APPLICATION = "myproject.asgi.application"

# ─────────────────────────────────────────────────────────────────
# CHANNEL LAYER — for broadcasting and cross-server messaging
# ─────────────────────────────────────────────────────────────────

# Production: Redis-backed channel layer
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
            
            # Or with password:
            # "hosts": [("redis://:<password>@<host>:6379/1")],
            
            # Use a different Redis DB than Celery broker (avoid conflicts)
            # Redis DB 1 for channel layer, DB 0 for Celery broker
            
            # Connection pool settings
            "capacity": 1500,  # max messages per channel before dropping old ones
            "expiry": 10,      # message expiry in seconds (prevents stale messages)
            
            # Symmetric encryption key for message security (optional but recommended)
            "symmetric_encryption_keys": [
                os.environ.get("CHANNEL_LAYER_ENCRYPTION_KEY", "")
            ],
        },
    },
}

# Development: In-memory channel layer (no Redis required, single-server only)
# CHANNEL_LAYERS = {
#     "default": {
#         "BACKEND": "channels.layers.InMemoryChannelLayer"
#     }
# }

# Testing: No channel layer (fastest for unit tests that don't need broadcasting)
# Set this in settings/test.py:
# CHANNEL_LAYERS = {}

# ─────────────────────────────────────────────────────────────────
# WEBSOCKET SETTINGS
# ─────────────────────────────────────────────────────────────────

# Maximum time (seconds) to wait for a WebSocket handshake to complete
# Increase if clients have slow connections
WEBSOCKET_CONNECT_TIMEOUT = 5

# Maximum size (bytes) of a WebSocket message frame
# Prevent clients from sending huge messages that could exhaust memory
# 1MB = 1048576 bytes
WEBSOCKET_MESSAGE_SIZE_LIMIT = 1048576

# ─────────────────────────────────────────────────────────────────
# ALLOWED_HOSTS — required for WebSocket connections
# ─────────────────────────────────────────────────────────────────

# WebSocket connections check Host header just like HTTP
ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "example.com",
    "www.example.com",
]

# In production with load balancer, you may need to trust X-Forwarded-Host
# USE_X_FORWARDED_HOST = True
```

### Channel Layer Backends Comparison

| Backend | Use Case | Pros | Cons |
|---|---|---|---|
| `channels_redis.core.RedisChannelLayer` | Production (multi-server) | Fast, persistent across restarts, supports multiple servers | Requires Redis |
| `channels.layers.InMemoryChannelLayer` | Development (single-server) | No external dependencies, fast | Lost on restart, single-server only |
| No channel layer (`{}`) | Testing, simple apps | Fastest, no setup | No broadcasting, no cross-server messaging |

---

## 6. ASGI Configuration {#asgi}

### Full `asgi.py` with All Options

```python
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings.production")

# Initialize Django before importing models
django_asgi_app = get_asgi_application()

from myproject.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    # Traditional HTTP requests
    "http": django_asgi_app,
    
    # WebSocket connections
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
```

**Middleware layers (inside to outside):**

1. **`URLRouter`** — Routes WebSocket connections to the correct consumer based on URL path
2. **`AuthMiddlewareStack`** — Populates `scope["user"]` with the Django user from the session cookie
3. **`AllowedHostsOriginValidator`** — Validates the `Origin` header against `ALLOWED_HOSTS` (CSRF protection for WebSockets)

### Custom Middleware

Create middleware to add custom logic before consumers run.

```python
# myproject/middleware.py
from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

@database_sync_to_async
def get_user_from_token(token_string):
    """Extract user from JWT token."""
    try:
        token = UntypedToken(token_string)
        user_id = token.payload.get("user_id")
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return User.objects.get(id=user_id)
    except (InvalidToken, TokenError, User.DoesNotExist):
        return AnonymousUser()

class JWTAuthMiddleware:
    """
    Custom middleware to authenticate WebSocket connections via JWT token
    passed in query string: ws://example.com/ws/chat/?token=<jwt>
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # Parse query string
        query_string = parse_qs(scope["query_string"].decode())
        token = query_string.get("token")
        
        if token:
            # Authenticate user from JWT token
            scope["user"] = await get_user_from_token(token[0])
        else:
            scope["user"] = AnonymousUser()
        
        return await self.app(scope, receive, send)
```

Apply in `asgi.py`:

```python
from myproject.middleware import JWTAuthMiddleware

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTAuthMiddleware(  # Custom middleware
        AllowedHostsOriginValidator(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
```

---

## 7. Routing — URLs for WebSockets {#routing}

### Basic Routing

```python
# apps/chat/routing.py
from django.urls import path, re_path
from . import consumers

websocket_urlpatterns = [
    # Static path
    path("ws/notifications/", consumers.NotificationConsumer.as_asgi()),
    
    # Path with integer parameter
    path("ws/chat/room/<int:room_id>/", consumers.ChatRoomConsumer.as_asgi()),
    
    # Path with string parameter
    path("ws/chat/user/<str:username>/", consumers.PrivateChatConsumer.as_asgi()),
    
    # Regex path (for complex patterns)
    re_path(r"ws/live/(?P<stream_id>[0-9a-f-]+)/$", consumers.LiveStreamConsumer.as_asgi()),
]
```

### Accessing Route Parameters in Consumer

```python
class ChatRoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Access captured URL parameters
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"chat_{self.room_id}"
        
        # Access query string parameters
        # ws://example.com/ws/chat/room/42/?page=1
        query_string = parse_qs(self.scope["query_string"].decode())
        page = query_string.get("page", ["1"])[0]
        
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
```

---

## 8. Writing Consumers {#consumers}

Consumers are the WebSocket equivalent of Django views. They handle the connection lifecycle.

### Consumer Types

| Type | When to Use | Sync/Async | Database Access |
|---|---|---|---|
| `AsyncWebsocketConsumer` | **Default choice** — fastest, handles async naturally | Async | Wrap ORM in `database_sync_to_async()` |
| `WebsocketConsumer` | Legacy code, heavy sync operations | Sync | Direct ORM access (blocking) |
| `AsyncJsonWebsocketConsumer` | Auto JSON encode/decode | Async | Wrap ORM in `database_sync_to_async()` |
| `JsonWebsocketConsumer` | Auto JSON encode/decode | Sync | Direct ORM access (blocking) |

**Always prefer `AsyncWebsocketConsumer`** unless you have a specific reason not to.

### Minimal Consumer

```python
# apps/chat/consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import json

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """
        Called when WebSocket handshake is complete.
        Accept or reject the connection here.
        """
        # Accept the connection
        await self.accept()
        
        # Or reject:
        # await self.close()
    
    async def disconnect(self, close_code):
        """
        Called when WebSocket connection is closed.
        Cleanup happens here.
        """
        pass
    
    async def receive(self, text_data):
        """
        Called when we receive a message from the WebSocket.
        text_data is a string (for text frames).
        For binary frames, use receive(self, bytes_data).
        """
        # Parse JSON
        data = json.loads(text_data)
        message = data.get("message", "")
        
        # Echo it back
        await self.send(text_data=json.dumps({
            "message": message
        }))
```

### Full Consumer with All Lifecycle Methods

```python
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import json
import logging

logger = logging.getLogger(__name__)

class ChatRoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """
        WebSocket handshake complete. Decide whether to accept or reject.
        """
        # Extract URL parameter
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"chat_{self.room_id}"
        
        # Get authenticated user (populated by AuthMiddlewareStack)
        self.user = self.scope["user"]
        
        # Reject if not authenticated
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Check user has access to this room
        has_access = await self.check_room_access()
        if not has_access:
            await self.close()
            return
        
        # Join room group (for broadcasting)
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name  # unique name for this consumer instance
        )
        
        # Accept connection
        await self.accept()
        
        # Send initial data
        await self.send(text_data=json.dumps({
            "type": "connection_established",
            "message": f"Welcome to room {self.room_id}"
        }))
        
        # Notify other users in the room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_joined",
                "username": self.user.username,
            }
        )
    
    async def disconnect(self, close_code):
        """
        WebSocket connection closed. Cleanup here.
        close_code: integer (1000 = normal, 1006 = abnormal, etc.)
        """
        logger.info(f"User {self.user.username} disconnected from room {self.room_id} (code: {close_code})")
        
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Notify others that user left
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_left",
                "username": self.user.username,
            }
        )
    
    async def receive(self, text_data):
        """
        Received a message from WebSocket client.
        """
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": "Invalid JSON"
            }))
            return
        
        message_type = data.get("type")
        
        if message_type == "chat_message":
            # Save to database
            message = await self.save_message(data.get("message", ""))
            
            # Broadcast to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",  # calls self.chat_message() on all consumers in group
                    "message": message.content,
                    "username": self.user.username,
                    "timestamp": message.created_at.isoformat(),
                }
            )
        
        elif message_type == "typing":
            # Broadcast typing indicator (no DB save)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "typing_indicator",
                    "username": self.user.username,
                    "is_typing": data.get("is_typing", False),
                }
            )
    
    # ─────────────────────────────────────────────────────────────
    # Group message handlers (called by channel_layer.group_send)
    # ─────────────────────────────────────────────────────────────
    
    async def chat_message(self, event):
        """
        Called when a 'chat_message' is sent to the group.
        Send it to this consumer's WebSocket client.
        """
        await self.send(text_data=json.dumps({
            "type": "chat_message",
            "message": event["message"],
            "username": event["username"],
            "timestamp": event["timestamp"],
        }))
    
    async def user_joined(self, event):
        """Called when a user joins the room."""
        await self.send(text_data=json.dumps({
            "type": "user_joined",
            "username": event["username"],
        }))
    
    async def user_left(self, event):
        """Called when a user leaves the room."""
        await self.send(text_data=json.dumps({
            "type": "user_left",
            "username": event["username"],
        }))
    
    async def typing_indicator(self, event):
        """Called when someone is typing."""
        # Don't send typing indicator back to the person who's typing
        if event["username"] != self.user.username:
            await self.send(text_data=json.dumps({
                "type": "typing",
                "username": event["username"],
                "is_typing": event["is_typing"],
            }))
    
    # ─────────────────────────────────────────────────────────────
    # Database operations (wrapped in database_sync_to_async)
    # ─────────────────────────────────────────────────────────────
    
    @database_sync_to_async
    def check_room_access(self):
        """Check if user has permission to access this room."""
        from apps.chat.models import ChatRoom
        try:
            room = ChatRoom.objects.get(id=self.room_id)
            return room.members.filter(id=self.user.id).exists()
        except ChatRoom.DoesNotExist:
            return False
    
    @database_sync_to_async
    def save_message(self, content):
        """Save message to database."""
        from apps.chat.models import Message
        return Message.objects.create(
            room_id=self.room_id,
            user=self.user,
            content=content
        )
```

### AsyncJsonWebsocketConsumer — Auto JSON Handling

```python
from channels.generic.websocket import AsyncJsonWebsocketConsumer

class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.accept()
    
    async def disconnect(self, close_code):
        pass
    
    async def receive_json(self, content):
        """
        Called when we receive a message.
        content is already parsed into a Python dict — no json.loads() needed.
        """
        message = content.get("message", "")
        
        # Send response
        # send_json() automatically calls json.dumps()
        await self.send_json({
            "type": "message",
            "content": message,
        })
```

---

## 9. Authentication & Middleware {#authentication}

### Session-Based Auth (Default)

`AuthMiddlewareStack` reads the Django session cookie and populates `scope["user"]`.

```python
# asgi.py
from channels.auth import AuthMiddlewareStack

application = ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
```

**Client-side:** Browser automatically sends session cookie with WebSocket handshake (same origin).

**Consumer access:**

```python
async def connect(self):
    self.user = self.scope["user"]
    if not self.user.is_authenticated:
        await self.close()
```

### Token-Based Auth (JWT)

For mobile apps, SPAs, or cross-origin WebSockets.

**Custom middleware:**

```python
# myproject/middleware.py
from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

@database_sync_to_async
def get_user_from_jwt(token_string):
    try:
        token = UntypedToken(token_string)
        user_id = token.payload.get("user_id")
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return User.objects.get(id=user_id)
    except (InvalidToken, TokenError, User.DoesNotExist):
        return AnonymousUser()

class JWTAuthMiddleware:
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        # Get token from query string or headers
        query_string = parse_qs(scope["query_string"].decode())
        token = query_string.get("token")
        
        if token:
            scope["user"] = await get_user_from_jwt(token[0])
        else:
            # Try to get from Sec-WebSocket-Protocol header (more secure)
            headers = dict(scope["headers"])
            protocol_header = headers.get(b"sec-websocket-protocol", b"").decode()
            if protocol_header:
                # Client sends: Sec-WebSocket-Protocol: token, <jwt>
                protocols = [p.strip() for p in protocol_header.split(",")]
                if len(protocols) == 2 and protocols[0] == "token":
                    scope["user"] = await get_user_from_jwt(protocols[1])
                else:
                    scope["user"] = AnonymousUser()
            else:
                scope["user"] = AnonymousUser()
        
        return await self.app(scope, receive, send)
```

**Apply in `asgi.py`:**

```python
from myproject.middleware import JWTAuthMiddleware

application = ProtocolTypeRouter({
    "websocket": JWTAuthMiddleware(
        URLRouter(websocket_urlpatterns)
    ),
})
```

**Client-side (JavaScript):**

```javascript
// Option 1: Query string (least secure — token visible in logs)
const ws = new WebSocket(`ws://example.com/ws/chat/?token=${jwtToken}`);

// Option 2: Sec-WebSocket-Protocol header (more secure)
const ws = new WebSocket('ws://example.com/ws/chat/', ['token', jwtToken]);
```

**Security note:** Query string tokens are visible in server logs. Use `Sec-WebSocket-Protocol` header method in production.

### Custom Permission Checks

```python
async def connect(self):
    self.user = self.scope["user"]
    
    # Reject unauthenticated users
    if not self.user.is_authenticated:
        await self.close()
        return
    
    # Reject users without permission
    if not await self.has_permission():
        await self.close()
        return
    
    await self.accept()

@database_sync_to_async
def has_permission(self):
    """Check user has specific permission."""
    return self.user.has_perm("chat.can_access_premium_rooms")
```

---

## 10. Channel Layers — Cross-Consumer Communication {#channel-layers}

A **channel layer** is a message broker that lets consumers send messages to each other — even across different server instances.

### When You Need a Channel Layer

✅ **Use channel layer when:**
- Broadcasting to multiple WebSocket clients (chat rooms, notifications)
- Sending messages from Django views/signals to WebSocket consumers
- Running multiple ASGI server instances (production scaling)

❌ **Don't need channel layer when:**
- Simple request/response WebSockets (one client talks to one consumer)
- Single-server development setup with no broadcasting

### Sending Messages Between Consumers

```python
# Consumer A sends to Consumer B
await self.channel_layer.send(
    "specific-channel-name",  # unique channel name of target consumer
    {
        "type": "chat.message",  # maps to chat_message() method
        "text": "Hello from another consumer",
    }
)

# Consumer B receives it
async def chat_message(self, event):
    message = event["text"]
    await self.send(text_data=json.dumps({"message": message}))
```

### Sending from Django Views to Consumers

```python
# apps/chat/views.py
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def send_notification(request):
    """
    Traditional Django view that sends a message to WebSocket consumers.
    """
    channel_layer = get_channel_layer()
    
    # Send to a specific group
    async_to_sync(channel_layer.group_send)(
        "notifications",  # group name
        {
            "type": "notification_message",
            "message": "New notification from Django view",
        }
    )
    
    return JsonResponse({"status": "sent"})
```

**Critical:** Wrap `channel_layer.group_send()` in `async_to_sync()` when calling from synchronous code (views, Celery tasks, signals).

### Sending from Celery Tasks

```python
# apps/notifications/tasks.py
from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@shared_task
def send_daily_digest():
    """
    Celery task that sends WebSocket message to all connected users.
    """
    channel_layer = get_channel_layer()
    
    async_to_sync(channel_layer.group_send)(
        "user_notifications",
        {
            "type": "daily_digest",
            "data": {"unread_count": 42},
        }
    )
```

---

## 11. Groups — Broadcasting to Multiple Clients {#groups}

Groups let you broadcast a single message to many consumers at once.

### How Groups Work

1. Each consumer joins a group by name during `connect()`
2. Any consumer can send a message to the group
3. The channel layer delivers the message to **all** consumers in that group
4. Each consumer's handler method is called

**Group names** are arbitrary strings. Common patterns:
- `chat_room_{room_id}` — one group per chat room
- `user_{user_id}` — private channel for one user across devices
- `notifications` — global broadcast group

### Join/Leave Groups

```python
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"chat_room_{self.room_id}"
        
        # Join group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name  # unique identifier for this consumer instance
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
```

### Broadcast to Group

```python
async def receive(self, text_data):
    data = json.loads(text_data)
    
    # Broadcast to all consumers in the group (including self)
    await self.channel_layer.group_send(
        self.room_group_name,
        {
            "type": "chat_message",  # method name (dots become underscores)
            "message": data["message"],
            "username": self.scope["user"].username,
        }
    )

# Handler called on each consumer in the group
async def chat_message(self, event):
    """
    Called when channel_layer.group_send() delivers a message.
    event dict contains the data we sent.
    """
    await self.send(text_data=json.dumps({
        "message": event["message"],
        "username": event["username"],
    }))
```

**Key insight:** `type: "chat_message"` maps to the method `chat_message()`. Dots in type are converted to underscores. So `type: "user.joined"` would call `user_joined()`.

### Per-User Groups (Multi-Device Support)

```python
class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Each user gets a personal group
        # All their devices join the same group
        self.user_group_name = f"user_{self.user.id}"
        
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.user_group_name,
            self.channel_name
        )
```

**Send notification to a specific user from Django view:**

```python
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def send_notification_to_user(user_id, message):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{user_id}",
        {
            "type": "notification",
            "message": message,
        }
    )
```

---

## 12. Database Access in Async Consumers {#database}

Django's ORM is **synchronous** — it blocks. In async consumers, blocking the event loop kills performance.

### The Problem

```python
# ❌ WRONG — blocks the event loop
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # This blocks ALL other WebSocket connections handled by this worker
        user = User.objects.get(id=1)  # BLOCKING CALL
        await self.accept()
```

### The Solution: `database_sync_to_async`

```python
from channels.db import database_sync_to_async

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Run blocking ORM call in a thread pool
        user = await self.get_user(user_id=1)
        await self.accept()
    
    @database_sync_to_async
    def get_user(self, user_id):
        """
        Decorated function runs in a thread pool.
        Returns the result to the async caller.
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return User.objects.get(id=user_id)
```

### Inline Usage

```python
async def receive(self, text_data):
    data = json.loads(text_data)
    
    # Inline database_sync_to_async for one-off queries
    from apps.chat.models import Message
    message = await database_sync_to_async(Message.objects.create)(
        room_id=self.room_id,
        user=self.scope["user"],
        content=data["message"]
    )
```

### QuerySet Operations

```python
@database_sync_to_async
def get_recent_messages(self, room_id, limit=50):
    """Fetch recent messages."""
    from apps.chat.models import Message
    return list(
        Message.objects
        .filter(room_id=room_id)
        .select_related("user")
        .order_by("-created_at")[:limit]
    )

async def connect(self):
    # ...
    messages = await self.get_recent_messages(self.room_id)
    await self.send(text_data=json.dumps({
        "type": "history",
        "messages": [
            {"user": m.user.username, "text": m.content}
            for m in messages
        ]
    }))
```

**Critical rule:** Always **return a list** from QuerySet operations. QuerySets are lazy and not thread-safe across async boundaries. Use `list(queryset)` to force evaluation inside the sync context.

### Atomic Transactions

```python
from django.db import transaction

@database_sync_to_async
def create_message_atomic(self, room_id, content):
    """
    Create message and update room's last_message in a transaction.
    """
    from apps.chat.models import Message, ChatRoom
    
    with transaction.atomic():
        message = Message.objects.create(
            room_id=room_id,
            user=self.user,
            content=content
        )
        ChatRoom.objects.filter(id=room_id).update(
            last_message=message,
            updated_at=timezone.now()
        )
        return message
```

---

## 13. Testing WebSockets {#testing}

### Channels Test Utilities

```bash
pip install pytest pytest-asyncio pytest-django
```

```python
# tests/test_consumers.py
import pytest
from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter
from django.urls import path
from apps.chat.consumers import ChatConsumer

@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_chat_consumer_connect():
    """Test WebSocket connection."""
    application = URLRouter([
        path("ws/chat/<int:room_id>/", ChatConsumer.as_asgi()),
    ])
    
    communicator = WebsocketCommunicator(application, "/ws/chat/1/")
    connected, subprotocol = await communicator.connect()
    
    assert connected is True
    
    await communicator.disconnect()

@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_chat_consumer_send_receive():
    """Test sending and receiving messages."""
    application = URLRouter([
        path("ws/chat/<int:room_id>/", ChatConsumer.as_asgi()),
    ])
    
    communicator = WebsocketCommunicator(application, "/ws/chat/1/")
    await communicator.connect()
    
    # Send a message
    await communicator.send_json_to({
        "type": "chat_message",
        "message": "Hello, world!"
    })
    
    # Receive the response
    response = await communicator.receive_json_from()
    
    assert response["type"] == "chat_message"
    assert response["message"] == "Hello, world!"
    
    await communicator.disconnect()
```

### Testing with Authentication

```python
from channels.testing import WebsocketCommunicator
from channels.auth import AuthMiddlewareStack
from django.contrib.auth import get_user_model

@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_authenticated_consumer():
    """Test WebSocket with authenticated user."""
    User = get_user_model()
    user = await database_sync_to_async(User.objects.create)(username="testuser")
    
    application = AuthMiddlewareStack(
        URLRouter([
            path("ws/notifications/", NotificationConsumer.as_asgi()),
        ])
    )
    
    communicator = WebsocketCommunicator(application, "/ws/notifications/")
    
    # Add user to scope
    communicator.scope["user"] = user
    
    connected, _ = await communicator.connect()
    assert connected is True
    
    await communicator.disconnect()
```

### Testing Group Broadcasting

```python
@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_group_broadcast():
    """Test message broadcast to group."""
    from channels.layers import get_channel_layer
    from channels.testing import WebsocketCommunicator
    
    channel_layer = get_channel_layer()
    
    # Create two communicators (two clients in same room)
    comm1 = WebsocketCommunicator(application, "/ws/chat/1/")
    comm2 = WebsocketCommunicator(application, "/ws/chat/1/")
    
    await comm1.connect()
    await comm2.connect()
    
    # Send message from client 1
    await comm1.send_json_to({"type": "chat_message", "message": "Hello"})
    
    # Both clients should receive it
    response1 = await comm1.receive_json_from()
    response2 = await comm2.receive_json_from()
    
    assert response1["message"] == "Hello"
    assert response2["message"] == "Hello"
    
    await comm1.disconnect()
    await comm2.disconnect()
```

---

## 14. Deployment — Daphne & Nginx {#deployment}

### Running Daphne in Production

```bash
# Install
pip install daphne

# Run manually (testing)
daphne -b 0.0.0.0 -p 8001 myproject.asgi:application

# With workers (production)
daphne -b 127.0.0.1 -p 8001 \
  --websocket-timeout 86400 \
  --access-log /var/log/daphne/access.log \
  --proxy-headers \
  myproject.asgi:application
```

### Supervisor Configuration

```ini
; /etc/supervisor/conf.d/daphne.conf

[program:daphne]
command=/home/app/venv/bin/daphne -u /tmp/daphne.sock --proxy-headers myproject.asgi:application
directory=/home/app/myproject
user=appuser
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/daphne/daphne.log
environment=DJANGO_SETTINGS_MODULE="myproject.settings.production"
```

### Nginx Configuration

```nginx
# /etc/nginx/sites-available/myproject

upstream django_http {
    server 127.0.0.1:8000;  # Gunicorn for HTTP
}

upstream django_ws {
    server 127.0.0.1:8001;  # Daphne for WebSockets
}

server {
    listen 80;
    server_name example.com;
    
    # Static files
    location /static/ {
        alias /home/app/myproject/staticfiles/;
    }
    
    # WebSocket connections
    location /ws/ {
        proxy_pass http://django_ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Prevent timeout on idle connections
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }
    
    # Regular HTTP requests
    location / {
        proxy_pass http://django_http;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Key directives:**
- `proxy_http_version 1.1` — required for WebSockets
- `Upgrade` and `Connection "upgrade"` — WebSocket handshake headers
- `proxy_read_timeout 86400s` — prevent nginx from killing idle WebSocket connections (24 hours)

### SSL/TLS (wss://)

```nginx
server {
    listen 443 ssl http2;
    server_name example.com;
    
    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
    
    # WebSocket over TLS
    location /ws/ {
        proxy_pass http://django_ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto https;
        proxy_read_timeout 86400s;
    }
    
    # ... rest of config
}
```

**Client-side:**

```javascript
// Production: secure WebSocket
const ws = new WebSocket('wss://example.com/ws/chat/');

// Development: unsecure WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/chat/');
```

---

## 15. Performance & Scaling {#performance}

### Scaling Horizontally (Multiple Servers)

With a Redis channel layer, you can run multiple Daphne instances across multiple servers.

```
Client 1 → Server A (Daphne)
Client 2 → Server B (Daphne)
                ↓ ↓
            Redis Channel Layer
                ↓ ↓
         Broadcasts to both servers
```

**Load balancer:** Nginx, HAProxy, or AWS ALB. Ensure session affinity is **not required** — any server can handle any client.

### Connection Limits

Each Daphne worker can handle **thousands** of concurrent WebSocket connections. Limits:
- OS file descriptor limit (use `ulimit -n 65536`)
- Memory (each connection uses ~5-10KB)
- Database connection pool

**Estimate:**
- 1GB RAM = ~50,000 idle WebSocket connections
- Active connections (frequent messaging) = ~10,000 per GB

### Database Connection Pooling

```bash
pip install django-db-geventpool
```

```python
# settings/production.py
DATABASES = {
    'default': {
        'ENGINE': 'django_db_geventpool.backends.postgresql_psycopg2',
        'NAME': 'mydb',
        'CONN_MAX_AGE': 0,
        'OPTIONS': {
            'MAX_CONNS': 100,  # max connections in pool
            'REUSE_CONNS': 10,  # reuse connection for N queries before recycling
        }
    }
}
```

### Redis Optimization

```python
# settings/production.py
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [
                {
                    "address": ("redis-host", 6379),
                    "db": 1,
                    # Connection pool settings
                    "max_connections": 50,
                    "socket_timeout": 5,
                    "socket_connect_timeout": 5,
                }
            ],
            "capacity": 1500,
            "expiry": 10,
        },
    },
}
```

### Monitoring Connection Count

```python
# apps/monitoring/management/commands/ws_stats.py
from django.core.management.base import BaseCommand
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class Command(BaseCommand):
    def handle(self, *args, **options):
        channel_layer = get_channel_layer()
        
        # This requires redis-py >= 4.2
        info = async_to_sync(channel_layer.connection)().info()
        
        print(f"Connected clients: {info.get('connected_clients')}")
        print(f"Used memory: {info.get('used_memory_human')}")
```

---

## 16. Security Checklist {#security}

### ✅ Essential Security Measures

- [ ] **HTTPS only in production** — Use `wss://` not `ws://`
- [ ] **Origin validation** — Use `AllowedHostsOriginValidator` in ASGI config
- [ ] **ALLOWED_HOSTS** — Set correctly for WebSocket handshake validation
- [ ] **Authentication required** — Reject unauthenticated connections unless truly public
- [ ] **Rate limiting** — Prevent spam/DoS on message reception
- [ ] **Input validation** — Never trust client data, validate all incoming messages
- [ ] **Message size limits** — Set `WEBSOCKET_MESSAGE_SIZE_LIMIT` to prevent memory exhaustion
- [ ] **Token security** — Use `Sec-WebSocket-Protocol` header for JWT, not query string
- [ ] **Channel layer encryption** — Enable `symmetric_encryption_keys` in production
- [ ] **CSRF protection** — `AllowedHostsOriginValidator` provides basic protection
- [ ] **Connection timeout** — Set reasonable `WEBSOCKET_CONNECT_TIMEOUT`
- [ ] **Permission checks** — Validate user permissions in `connect()` before accepting
- [ ] **SQL injection** — Use ORM parameterized queries, never raw SQL with user input
- [ ] **XSS protection** — Sanitize HTML in messages if rendering in browser
- [ ] **Logging** — Log all connection attempts, failures, and suspicious activity

### Rate Limiting Example

```python
from django.core.cache import cache
from django.utils import timezone

class ChatConsumer(AsyncWebsocketConsumer):
    async def receive(self, text_data):
        # Rate limit: max 10 messages per minute per user
        cache_key = f"ws_rate_limit:{self.user.id}"
        message_count = cache.get(cache_key, 0)
        
        if message_count >= 10:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": "Rate limit exceeded. Please slow down."
            }))
            return
        
        # Increment counter
        cache.set(cache_key, message_count + 1, 60)  # 60 seconds TTL
        
        # Process message normally
        # ...
```

### Input Validation Example

```python
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

async def receive(self, text_data):
    try:
        data = json.loads(text_data)
    except json.JSONDecodeError:
        await self.send(text_data=json.dumps({
            "type": "error",
            "message": "Invalid JSON"
        }))
        return
    
    # Validate message type
    allowed_types = ["chat_message", "typing", "read_receipt"]
    if data.get("type") not in allowed_types:
        await self.send(text_data=json.dumps({
            "type": "error",
            "message": "Invalid message type"
        }))
        return
    
    # Validate message content
    message = data.get("message", "")
    if len(message) > 5000:
        await self.send(text_data=json.dumps({
            "type": "error",
            "message": "Message too long (max 5000 characters)"
        }))
        return
    
    # Strip dangerous HTML
    import bleach
    message = bleach.clean(message, tags=[], strip=True)
    
    # Process validated message
    # ...
```

---

## 17. Common Patterns {#patterns}

### Pattern 1: Presence Tracking (Online/Offline Status)

```python
class PresenceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Mark user as online
        await self.update_user_status("online")
        
        # Join presence group
        await self.channel_layer.group_add("presence", self.channel_name)
        
        # Broadcast to others
        await self.channel_layer.group_send(
            "presence",
            {
                "type": "user_status_change",
                "user_id": self.user.id,
                "status": "online",
            }
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Mark user as offline
        await self.update_user_status("offline")
        
        # Broadcast to others
        await self.channel_layer.group_send(
            "presence",
            {
                "type": "user_status_change",
                "user_id": self.user.id,
                "status": "offline",
            }
        )
        
        await self.channel_layer.group_discard("presence", self.channel_name)
    
    @database_sync_to_async
    def update_user_status(self, status):
        from apps.accounts.models import UserProfile
        UserProfile.objects.filter(user=self.user).update(
            status=status,
            last_seen=timezone.now()
        )
    
    async def user_status_change(self, event):
        await self.send(text_data=json.dumps({
            "type": "status_change",
            "user_id": event["user_id"],
            "status": event["status"],
        }))
```

### Pattern 2: Heartbeat/Ping-Pong (Keep-Alive)

```python
import asyncio

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        
        # Start heartbeat task
        self.heartbeat_task = asyncio.create_task(self.send_heartbeat())
    
    async def disconnect(self, close_code):
        # Cancel heartbeat task
        if hasattr(self, 'heartbeat_task'):
            self.heartbeat_task.cancel()
    
    async def send_heartbeat(self):
        """Send ping every 30 seconds to keep connection alive."""
        try:
            while True:
                await asyncio.sleep(30)
                await self.send(text_data=json.dumps({
                    "type": "ping",
                    "timestamp": timezone.now().isoformat()
                }))
        except asyncio.CancelledError:
            pass
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        
        # Client responds to ping with pong
        if data.get("type") == "pong":
            # Connection is alive
            return
        
        # Handle other messages
        # ...
```

### Pattern 3: Reconnection with Message Queue

```python
class ReliableConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.session_id = self.scope["url_route"]["kwargs"]["session_id"]
        
        await self.accept()
        
        # Send queued messages from previous session
        await self.send_queued_messages()
    
    async def disconnect(self, close_code):
        # Don't delete queued messages yet — client might reconnect
        pass
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        
        if data.get("type") == "ack":
            # Client acknowledged receipt of a message
            message_id = data.get("message_id")
            await self.remove_from_queue(message_id)
        else:
            # Handle normal message
            # ...
    
    @database_sync_to_async
    def send_queued_messages(self):
        from apps.chat.models import QueuedMessage
        messages = QueuedMessage.objects.filter(
            user=self.user,
            session_id=self.session_id,
            delivered=False
        ).order_by("created_at")
        
        for msg in messages:
            asyncio.create_task(
                self.send(text_data=json.dumps({
                    "type": "queued_message",
                    "message_id": str(msg.id),
                    "content": msg.content,
                }))
            )
    
    @database_sync_to_async
    def remove_from_queue(self, message_id):
        from apps.chat.models import QueuedMessage
        QueuedMessage.objects.filter(id=message_id).update(delivered=True)
```

### Pattern 4: Private Messaging Between Users

```python
class PrivateMessageConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Personal group for this user (all their devices)
        self.user_group = f"user_{self.user.id}"
        
        await self.channel_layer.group_add(self.user_group, self.channel_name)
        await self.accept()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.user_group, self.channel_name)
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        
        if data.get("type") == "private_message":
            recipient_id = data.get("recipient_id")
            message = data.get("message")
            
            # Save to database
            msg = await self.save_private_message(recipient_id, message)
            
            # Send to recipient's group (all their devices)
            await self.channel_layer.group_send(
                f"user_{recipient_id}",
                {
                    "type": "private_message_received",
                    "sender_id": self.user.id,
                    "sender_username": self.user.username,
                    "message": message,
                    "message_id": msg.id,
                    "timestamp": msg.created_at.isoformat(),
                }
            )
            
            # Confirm to sender
            await self.send(text_data=json.dumps({
                "type": "message_sent",
                "message_id": msg.id,
            }))
    
    async def private_message_received(self, event):
        """Handler for incoming private messages."""
        await self.send(text_data=json.dumps({
            "type": "private_message",
            "sender_id": event["sender_id"],
            "sender_username": event["sender_username"],
            "message": event["message"],
            "message_id": event["message_id"],
            "timestamp": event["timestamp"],
        }))
    
    @database_sync_to_async
    def save_private_message(self, recipient_id, content):
        from apps.chat.models import PrivateMessage
        return PrivateMessage.objects.create(
            sender=self.user,
            recipient_id=recipient_id,
            content=content
        )
```

### Pattern 5: File Upload via WebSocket (Base64)

```python
import base64
from django.core.files.base import ContentFile

class FileUploadConsumer(AsyncWebsocketConsumer):
    async def receive(self, text_data):
        data = json.loads(text_data)
        
        if data.get("type") == "file_upload":
            filename = data.get("filename")
            file_data = data.get("file_data")  # base64 encoded
            file_type = data.get("file_type")
            
            # Validate file size (base64 is ~33% larger than original)
            if len(file_data) > 5 * 1024 * 1024:  # 5MB limit
                await self.send(text_data=json.dumps({
                    "type": "error",
                    "message": "File too large (max 5MB)"
                }))
                return
            
            # Decode base64
            try:
                file_content = base64.b64decode(file_data)
            except Exception:
                await self.send(text_data=json.dumps({
                    "type": "error",
                    "message": "Invalid file data"
                }))
                return
            
            # Save file
            file_obj = await self.save_file(filename, file_content, file_type)
            
            # Broadcast to room
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "file_uploaded",
                    "filename": filename,
                    "file_url": file_obj.file.url,
                    "uploaded_by": self.user.username,
                }
            )
    
    @database_sync_to_async
    def save_file(self, filename, content, file_type):
        from apps.chat.models import UploadedFile
        return UploadedFile.objects.create(
            user=self.user,
            room_id=self.room_id,
            file=ContentFile(content, name=filename),
            file_type=file_type
        )
    
    async def file_uploaded(self, event):
        await self.send(text_data=json.dumps({
            "type": "file_uploaded",
            "filename": event["filename"],
            "file_url": event["file_url"],
            "uploaded_by": event["uploaded_by"],
        }))
```

---

## 18. Debugging & Monitoring {#debugging}

### Logging Configuration

```python
# settings/base.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django/channels.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'channels': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'apps.chat.consumers': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
        },
    },
}
```

### Debug Logging in Consumers

```python
import logging

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        logger.info(
            f"WebSocket connect attempt: user={self.scope['user']}, "
            f"path={self.scope['path']}, "
            f"headers={dict(self.scope['headers'])}"
        )
        
        try:
            # Connection logic
            await self.accept()
            logger.info(f"WebSocket connected: user={self.scope['user']}")
        except Exception as e:
            logger.error(f"WebSocket connect failed: {e}", exc_info=True)
            await self.close()
    
    async def receive(self, text_data):
        logger.debug(f"Received message: user={self.user.username}, data={text_data[:100]}")
        
        try:
            # Message handling
            pass
        except Exception as e:
            logger.error(
                f"Message handling failed: user={self.user.username}, error={e}",
                exc_info=True
            )
```

### Connection Tracking

```python
# Track active connections in Redis
class MonitoredConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        from django.core.cache import cache
        
        # Increment connection count
        cache.incr("ws_connections_total", 1)
        cache.incr(f"ws_connections_room_{self.room_id}", 1)
        
        await self.accept()
    
    async def disconnect(self, close_code):
        from django.core.cache import cache
        
        # Decrement connection count
        cache.decr("ws_connections_total", 1)
        cache.decr(f"ws_connections_room_{self.room_id}", 1)
```

### Monitoring Dashboard Command

```python
# apps/monitoring/management/commands/ws_monitor.py
from django.core.management.base import BaseCommand
from django.core.cache import cache
import time

class Command(BaseCommand):
    help = 'Monitor WebSocket connections in real-time'
    
    def handle(self, *args, **options):
        while True:
            total = cache.get("ws_connections_total", 0)
            
            self.stdout.write(
                self.style.SUCCESS(f"Active WebSocket connections: {total}")
            )
            
            # Show per-room breakdown
            # ... (iterate through rooms)
            
            time.sleep(5)  # Update every 5 seconds
```

### Sentry Integration

```python
# settings/production.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=env("SENTRY_DSN"),
    integrations=[
        DjangoIntegration(),
    ],
    traces_sample_rate=0.1,
    environment=env("ENVIRONMENT", default="production"),
)
```

Sentry automatically captures exceptions in consumers and provides full stack traces.

---

## 19. Common Errors & Fixes {#errors}

| Error | Root Cause | Fix |
|---|---|---|
| `AppRegistryNotReady` on Daphne start | Importing models before Django initialized | Call `get_asgi_application()` before importing routing |
| `AttributeError: 'NoneType' object has no attribute 'group_add'` | Channel layer not configured | Add `CHANNEL_LAYERS` to settings; check Redis connection |
| `WebSocket connection failed` in browser | Wrong URL or Daphne not running | Verify Daphne is running; check URL starts with `ws://` or `wss://` |
| `Origin header does not match allowed origins` | CORS/origin validation failure | Add domain to `ALLOWED_HOSTS`; use `AllowedHostsOriginValidator` |
| Consumer never receives messages | Not in group or wrong group name | Verify `group_add()` called; check group name matches `group_send()` |
| Database query blocks all connections | Using sync ORM in async consumer | Wrap queries in `database_sync_to_async()` |
| `RuntimeError: This event loop is already running` | Mixing sync/async incorrectly | Use `async_to_sync()` when calling async from sync; use `database_sync_to_async()` for ORM |
| Messages not persisting across reconnects | No session/reconnection logic | Implement message queue pattern; save messages to DB |
| High memory usage over time | Connections not cleaned up | Implement proper `disconnect()` cleanup; monitor with `ulimit` |
| `TypeError: Object of type X is not JSON serializable` | Sending non-serializable data | Convert to primitives; use `.isoformat()` for datetimes |
| Connection drops after 60 seconds | Nginx/proxy timeout | Increase `proxy_read_timeout` in Nginx config |
| Auth fails on WebSocket | Session cookie not sent | Check same-origin; use JWT for cross-origin |
| `channel_layer.group_send()` silently fails | Redis connection lost | Check Redis status; verify connection settings |

---

## 20. Quick Reference {#reference}

### Development Commands

```bash
# Start Daphne development server
python manage.py runserver  # Channels takes over if daphne is in INSTALLED_APPS

# Or run Daphne directly
daphne -b 0.0.0.0 -p 8000 myproject.asgi:application

# Check configuration
python manage.py check

# Run migrations
python manage.py migrate

# Test WebSocket connection
wscat -c ws://localhost:8000/ws/chat/1/
```

### Consumer Quick Reference

```python
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import json

class MyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Accept or reject connection
        await self.accept()
        # await self.close()  # reject
    
    async def disconnect(self, close_code):
        # Cleanup
        pass
    
    async def receive(self, text_data):
        # Handle incoming message
        data = json.loads(text_data)
        await self.send(text_data=json.dumps({"response": "ok"}))
    
    # Group operations
    async def join_group(self, group_name):
        await self.channel_layer.group_add(group_name, self.channel_name)
    
    async def leave_group(self, group_name):
        await self.channel_layer.group_discard(group_name, self.channel_name)
    
    async def broadcast_to_group(self, group_name, message):
        await self.channel_layer.group_send(
            group_name,
            {
                "type": "group_message",  # calls self.group_message()
                "text": message,
            }
        )
    
    async def group_message(self, event):
        # Handler for group messages
        await self.send(text_data=json.dumps({"message": event["text"]}))
    
    # Database access
    @database_sync_to_async
    def get_data(self):
        from apps.myapp.models import MyModel
        return list(MyModel.objects.all())
```

### Client-Side JavaScript

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/chat/1/');

// Connection opened
ws.onopen = (event) => {
    console.log('WebSocket connected');
    ws.send(JSON.stringify({
        type: 'chat_message',
        message: 'Hello, server!'
    }));
};

// Receive message
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Message from server:', data);
};

// Connection closed
ws.onclose = (event) => {
    console.log('WebSocket closed:', event.code, event.reason);
};

// Error
ws.onerror = (error) => {
    console.error('WebSocket error:', error);
};

// Send message
function sendMessage(message) {
    ws.send(JSON.stringify({
        type: 'chat_message',
        message: message
    }));
}

// Close connection
ws.close();
```

### Production Checklist

- [ ] `daphne` at top of `INSTALLED_APPS`
- [ ] `ASGI_APPLICATION` configured in settings
- [ ] `ALLOWED_HOSTS` includes production domain
- [ ] Channel layer configured with Redis
- [ ] `AllowedHostsOriginValidator` in ASGI middleware stack
- [ ] Authentication middleware configured (session or JWT)
- [ ] Database connection pooling enabled
- [ ] Nginx/proxy configured with WebSocket support
- [ ] SSL/TLS enabled (`wss://` in production)
- [ ] Rate limiting implemented on message reception
- [ ] Input validation on all incoming messages
- [ ] Logging configured and monitored
- [ ] Sentry (or equivalent) integrated
- [ ] Connection limits tested and tuned
- [ ] Redis persistence enabled if needed
- [ ] Backup Redis channel layer configured
- [ ] Health check endpoint implemented
- [ ] Load testing performed
- [ ] Graceful shutdown handled in deployment

---

**That's everything.** You now have every detail needed to build production-grade WebSocket applications with Django Channels. No guessing. No missing pieces. Just the complete picture.
