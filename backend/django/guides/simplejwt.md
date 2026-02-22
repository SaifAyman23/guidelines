# Comprehensive Guide to djangorestframework-simplejwt

## Table of Contents
1. [Introduction](#introduction)
2. [Installation & Setup](#installation--setup)
3. [Core Concepts](#core-concepts)
4. [Basic Configuration](#basic-configuration)
5. [Built-in Views & Endpoints](#built-in-views--endpoints)
6. [Token Types & Lifecycle](#token-types--lifecycle)
7. [Customizing Token Claims](#customizing-token-claims)
8. [Custom Token Serializers](#custom-token-serializers)
9. [Protecting Views](#protecting-views)
10. [Token Blacklisting](#token-blacklisting)
11. [Rotating Refresh Tokens](#rotating-refresh-tokens)
12. [Custom Authentication Backend](#custom-authentication-backend)
13. [Settings Reference](#settings-reference)
14. [Working with the Frontend](#working-with-the-frontend)
15. [Security Best Practices](#security-best-practices)
16. [Testing JWT Authentication](#testing-jwt-authentication)
17. [Common Errors & Troubleshooting](#common-errors--troubleshooting)

---

## Introduction

`djangorestframework-simplejwt` is the most widely used JWT (JSON Web Token) authentication library for Django REST Framework. It provides stateless, scalable authentication without requiring server-side session storage.

**Why JWT?**
- Stateless — the server does not store session data
- Scalable — works across distributed systems and microservices
- Self-contained — tokens carry their own claims (user ID, expiry, roles, etc.)
- Standard — follows RFC 7519

**simplejwt vs. other options:**

| Feature | simplejwt | djoser | djangorestframework-jwt (deprecated) |
|---|---|---|---|
| Maintained | ✅ Yes | ✅ Yes | ❌ No |
| Blacklisting | ✅ Yes | ✅ Yes | ❌ No |
| Token Rotation | ✅ Yes | ✅ Yes | ❌ No |
| Minimal footprint | ✅ Yes | ❌ (more opinionated) | — |

---

## Installation & Setup

### 1. Install the package

```bash
pip install djangorestframework-simplejwt
```

Optionally, install with cryptographic signing support (RSA/EC keys):

```bash
pip install djangorestframework-simplejwt[crypto]
```

### 2. Add to INSTALLED_APPS

```python
# settings.py
INSTALLED_APPS = [
    ...
    'rest_framework',
    'rest_framework_simplejwt',
    # Required only if using token blacklisting:
    'rest_framework_simplejwt.token_blacklist',
]
```

### 3. Set the default authentication class

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}
```

### 4. Run migrations (if using blacklisting)

```bash
python manage.py migrate
```

---

## Core Concepts

### Access Token
A short-lived token (default: 5 minutes) sent with every API request in the `Authorization` header. When it expires, the client must use the refresh token to get a new one.

### Refresh Token
A long-lived token (default: 1 day) used exclusively to obtain new access tokens. It should be stored securely and never sent to arbitrary endpoints.

### Token Structure
Every JWT has three base64url-encoded parts separated by dots:

```
header.payload.signature

eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9   ← header (alg + typ)
.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwidXNlcl9pZCI6MX0  ← payload (claims)
.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c       ← signature
```

Claims in the payload include:
- `token_type` — "access" or "refresh"
- `exp` — expiration timestamp
- `iat` — issued-at timestamp
- `jti` — unique token ID (used for blacklisting)
- `user_id` — the authenticated user's PK

---

## Basic Configuration

```python
# settings.py
from datetime import timedelta

SIMPLE_JWT = {
    # Token lifetimes
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=5),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),

    # Rotation & blacklisting
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,

    # Signing
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,       # use SECRET_KEY or a separate strong key
    'VERIFYING_KEY': None,           # for asymmetric algos (RS256, ES256)

    # Header config
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',

    # User identification
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',

    # Token classes
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',

    # JTI (unique token ID)
    'JTI_CLAIM': 'jti',

    # Sliding tokens (optional alternative to access/refresh pair)
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),

    # Serializers
    'TOKEN_OBTAIN_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenObtainPairSerializer',
    'TOKEN_REFRESH_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenRefreshSerializer',
    'TOKEN_VERIFY_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenVerifySerializer',
    'TOKEN_BLACKLIST_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenBlacklistSerializer',
}
```

---

## Built-in Views & Endpoints

simplejwt ships with ready-to-use views. Wire them up in `urls.py`:

```python
# urls.py
from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
    TokenBlacklistView,
)

urlpatterns = [
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('api/token/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),
]
```

### `POST /api/token/` — Obtain Tokens

**Request:**
```json
{
    "username": "john",
    "password": "secret123"
}
```

**Response:**
```json
{
    "access": "eyJ0eXAiOiJKV1Qi...",
    "refresh": "eyJ0eXAiOiJKV1Qi..."
}
```

### `POST /api/token/refresh/` — Refresh Access Token

**Request:**
```json
{
    "refresh": "eyJ0eXAiOiJKV1Qi..."
}
```

**Response:**
```json
{
    "access": "eyJ0eXAiOiJKV1Qi..."
}
```

If `ROTATE_REFRESH_TOKENS` is `True`, a new `refresh` token is also returned.

### `POST /api/token/verify/` — Verify a Token

**Request:**
```json
{
    "token": "eyJ0eXAiOiJKV1Qi..."
}
```

**Response:** `200 OK` with `{}` if valid, `401` if invalid/expired.

### `POST /api/token/blacklist/` — Blacklist a Refresh Token

```json
{
    "refresh": "eyJ0eXAiOiJKV1Qi..."
}
```

Requires `rest_framework_simplejwt.token_blacklist` in `INSTALLED_APPS`.

---

## Token Types & Lifecycle

### Standard Flow (Access + Refresh)

```
Client                              Server
  |                                    |
  |-- POST /api/token/ (credentials) ->|
  |<-- {access, refresh} -------------|
  |                                    |
  |-- GET /api/resource/ (access) ---> |
  |<-- 200 OK --------------------------|
  |                                    |
  | [access token expires]             |
  |                                    |
  |-- POST /api/token/refresh/ ------> |
  |<-- {access (new)} ----------------|
  |                                    |
  | [user logs out]                    |
  |-- POST /api/token/blacklist/ ----> |
  |<-- 200 OK --------------------------|
```

### Sliding Tokens (Alternative)

Sliding tokens are a single token that auto-extends its lifetime when used, up to a `refresh_exp` limit. They simplify the flow but are harder to revoke.

```python
# urls.py
from rest_framework_simplejwt.views import (
    TokenObtainSlidingView,
    TokenRefreshSlidingView,
)

urlpatterns = [
    path('api/token/', TokenObtainSlidingView.as_view(), name='token_obtain_sliding'),
    path('api/token/refresh/', TokenRefreshSlidingView.as_view(), name='token_refresh_sliding'),
]
```

---

## Customizing Token Claims

By default, the token payload includes only `user_id`. You can add any data (roles, email, full name, etc.) by subclassing the serializer.

### Step 1: Create a custom serializer

```python
# myapp/serializers.py
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['username'] = user.username
        token['email'] = user.email
        token['is_staff'] = user.is_staff
        token['roles'] = list(user.groups.values_list('name', flat=True))

        return token
```

### Step 2: Create a custom view

```python
# myapp/views.py
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import MyTokenObtainPairSerializer

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
```

### Step 3: Wire the custom view

```python
# urls.py
from myapp.views import MyTokenObtainPairView

urlpatterns = [
    path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    ...
]
```

Alternatively, point to the custom serializer via settings:

```python
SIMPLE_JWT = {
    'TOKEN_OBTAIN_SERIALIZER': 'myapp.serializers.MyTokenObtainPairSerializer',
}
```

---

## Custom Token Serializers

### Adding extra response fields

If you want to return additional data (not in the token) alongside the tokens (e.g., user profile):

```python
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        # Add extra response data (NOT encoded in the token)
        data['user_id'] = self.user.id
        data['username'] = self.user.username
        data['email'] = self.user.email
        data['is_staff'] = self.user.is_staff

        return data
```

### Validating with email instead of username

```python
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

class EmailTokenObtainSerializer(TokenObtainPairSerializer):
    username_field = User.EMAIL_FIELD  # switches to email field

    def validate(self, attrs):
        # The username_field swap handles most of it
        return super().validate(attrs)
```

---

## Protecting Views

### Class-based views

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

class SecretDataView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'message': f'Hello, {request.user.username}!'})
```

### Function-based views

```python
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def my_view(request):
    return Response({'user': request.user.username})
```

### Sending the token from the client

Every protected request must include the token in the `Authorization` header:

```
Authorization: Bearer eyJ0eXAiOiJKV1Qi...
```

Example with `curl`:

```bash
curl -H "Authorization: Bearer eyJ0eXAiOiJKV1Qi..." http://localhost:8000/api/secret/
```

Example with JavaScript `fetch`:

```javascript
const response = await fetch('/api/secret/', {
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json',
  }
});
```

---

## Token Blacklisting

Blacklisting lets you invalidate tokens before they expire — useful for logout, forced sign-out on password change, or revoking compromised tokens.

### Setup

```python
INSTALLED_APPS = [
    ...
    'rest_framework_simplejwt.token_blacklist',
]
```

```bash
python manage.py migrate
```

### How it works

Each refresh token has a unique `jti` (JWT ID). When blacklisted, this JTI is stored in the database. Any subsequent request using that refresh token (or its derived access tokens, if configured) will be rejected.

### Logout endpoint example

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

class LogoutView(APIView):
    def post(self, request):
        try:
            refresh_token = request.data['refresh']
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'detail': 'Logout successful.'}, status=status.HTTP_205_RESET_CONTENT)
        except KeyError:
            return Response({'error': 'Refresh token required.'}, status=status.HTTP_400_BAD_REQUEST)
        except TokenError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
```

### Blacklist on password change

```python
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

def blacklist_all_user_tokens(user):
    tokens = OutstandingToken.objects.filter(user=user)
    for token in tokens:
        BlacklistedToken.objects.get_or_create(token=token)
```

### Flushing expired tokens

Outstanding tokens accumulate in the DB. Periodically flush expired ones:

```bash
python manage.py flushexpiredtokens
```

Automate with cron or Celery:

```python
# celery task example
from celery import shared_task
from django.core.management import call_command

@shared_task
def flush_expired_tokens():
    call_command('flushexpiredtokens')
```

---

## Rotating Refresh Tokens

Token rotation improves security by issuing a new refresh token every time one is used. The old refresh token is immediately blacklisted.

```python
SIMPLE_JWT = {
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,  # blacklist old refresh tokens
}
```

With rotation enabled, a refresh response includes both tokens:

```json
{
    "access": "eyJ0eXAiOiJKV1Qi...",
    "refresh": "eyJ0eXAiOiJKV1Qi..."  ← new refresh token
}
```

**Important:** The client must always store and use the latest refresh token, discarding the old one immediately.

---

## Custom Authentication Backend

You can create a fully custom token model by subclassing `Token`:

```python
from rest_framework_simplejwt.tokens import Token

class MyCustomToken(Token):
    token_type = 'custom'
    lifetime = timedelta(hours=2)

# Generate a token manually:
token = MyCustomToken.for_user(user)
print(str(token))  # the encoded JWT string
```

### Manually creating tokens (useful for testing or special flows)

```python
from rest_framework_simplejwt.tokens import RefreshToken

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }
```

### Using RSA/EC asymmetric keys (RS256)

Asymmetric signing allows public-key verification without sharing the secret:

```python
SIMPLE_JWT = {
    'ALGORITHM': 'RS256',
    'SIGNING_KEY': open('private.pem').read(),
    'VERIFYING_KEY': open('public.pem').read(),
}
```

Generate keys:

```bash
openssl genrsa -out private.pem 2048
openssl rsa -in private.pem -pubout -out public.pem
```

---

## Settings Reference

| Setting | Default | Description |
|---|---|---|
| `ACCESS_TOKEN_LIFETIME` | `timedelta(minutes=5)` | Access token expiry |
| `REFRESH_TOKEN_LIFETIME` | `timedelta(days=1)` | Refresh token expiry |
| `ROTATE_REFRESH_TOKENS` | `False` | Issue new refresh token on each refresh |
| `BLACKLIST_AFTER_ROTATION` | `False` | Blacklist old refresh after rotation |
| `UPDATE_LAST_LOGIN` | `False` | Update `last_login` on token obtain |
| `ALGORITHM` | `'HS256'` | Signing algorithm |
| `SIGNING_KEY` | `settings.SECRET_KEY` | Key for signing tokens |
| `VERIFYING_KEY` | `None` | Public key for asymmetric verification |
| `AUDIENCE` | `None` | JWT `aud` claim |
| `ISSUER` | `None` | JWT `iss` claim |
| `AUTH_HEADER_TYPES` | `('Bearer',)` | Accepted auth header prefixes |
| `AUTH_HEADER_NAME` | `'HTTP_AUTHORIZATION'` | Header name |
| `USER_ID_FIELD` | `'id'` | User model field to embed in token |
| `USER_ID_CLAIM` | `'user_id'` | Token claim name for user ID |
| `AUTH_TOKEN_CLASSES` | `('...AccessToken',)` | Token classes to authenticate with |
| `TOKEN_TYPE_CLAIM` | `'token_type'` | Claim for token type |
| `JTI_CLAIM` | `'jti'` | Claim for unique token ID |
| `TOKEN_OBTAIN_SERIALIZER` | `'...TokenObtainPairSerializer'` | Serializer for token obtain |
| `TOKEN_REFRESH_SERIALIZER` | `'...TokenRefreshSerializer'` | Serializer for token refresh |
| `TOKEN_VERIFY_SERIALIZER` | `'...TokenVerifySerializer'` | Serializer for token verify |
| `TOKEN_BLACKLIST_SERIALIZER` | `'...TokenBlacklistSerializer'` | Serializer for blacklist |

---

## Working with the Frontend

### Storing tokens

| Storage | Security | Notes |
|---|---|---|
| `localStorage` | ⚠️ Vulnerable to XSS | Easy but insecure for sensitive apps |
| `sessionStorage` | ⚠️ Same as localStorage | Cleared on tab close |
| **HttpOnly Cookie** | ✅ Recommended | Cannot be read by JS — immune to XSS |
| In-memory (JS variable) | ✅ Best | Lost on refresh; combine with cookie for refresh |

### Cookie-based approach (Django side)

```python
# views.py
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import RefreshToken

class CookieTokenObtainView(APIView):
    def post(self, request):
        # authenticate user...
        user = authenticate(request, **request.data)
        if not user:
            return Response({'error': 'Invalid credentials'}, status=401)

        refresh = RefreshToken.for_user(user)
        response = JsonResponse({'access': str(refresh.access_token)})
        response.set_cookie(
            key='refresh_token',
            value=str(refresh),
            httponly=True,
            secure=True,          # HTTPS only
            samesite='Strict',    # CSRF protection
            max_age=86400,        # 1 day in seconds
        )
        return response
```

### Axios interceptor — auto-refresh on 401

```javascript
import axios from 'axios';

let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    error ? prom.reject(error) : prom.resolve(token);
  });
  failedQueue = [];
};

axios.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then(token => {
          originalRequest.headers['Authorization'] = `Bearer ${token}`;
          return axios(originalRequest);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const { data } = await axios.post('/api/token/refresh/', {
          refresh: localStorage.getItem('refresh'),
        });
        localStorage.setItem('access', data.access);
        axios.defaults.headers.common['Authorization'] = `Bearer ${data.access}`;
        processQueue(null, data.access);
        return axios(originalRequest);
      } catch (err) {
        processQueue(err, null);
        // redirect to login
        window.location.href = '/login';
        return Promise.reject(err);
      } finally {
        isRefreshing = false;
      }
    }
    return Promise.reject(error);
  }
);
```

---

## Security Best Practices

**1. Use short access token lifetimes.** 5 minutes is the default and a good starting point. For highly sensitive APIs, use 1–2 minutes.

**2. Use HTTPS everywhere.** Tokens in transit must be encrypted. Never run JWT authentication over plain HTTP in production.

**3. Rotate refresh tokens.** Enable `ROTATE_REFRESH_TOKENS` and `BLACKLIST_AFTER_ROTATION` so stolen refresh tokens can only be used once.

**4. Use HttpOnly cookies for refresh tokens.** This prevents JavaScript from reading the refresh token, protecting against XSS attacks.

**5. Set a strong `SIGNING_KEY`.** Never use the default `SECRET_KEY` in production for JWT signing — use a separate, randomly generated 256-bit key:

```python
import secrets
print(secrets.token_hex(32))  # generate once, store in env variable
```

**6. Consider asymmetric keys (RS256) in microservices.** If multiple services verify tokens, RS256 lets them verify without sharing the signing secret.

**7. Include only necessary claims.** Do not put sensitive data (passwords, credit card info, PII) in the token payload — it is base64-encoded, not encrypted.

**8. Flush expired tokens regularly.** Run `flushexpiredtokens` as a scheduled task to keep the blacklist table lean.

**9. Validate audience and issuer.** Use `AUDIENCE` and `ISSUER` settings in multi-tenant or multi-service environments:

```python
SIMPLE_JWT = {
    'AUDIENCE': 'my-api',
    'ISSUER': 'https://auth.example.com',
}
```

**10. Blacklist tokens on sensitive events.** Password change, account deactivation, and role changes should immediately blacklist all outstanding tokens for the affected user.

---

## Testing JWT Authentication

### Using `APIClient` in tests

```python
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class JWTAuthTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def get_tokens(self, user=None):
        user = user or self.user
        refresh = RefreshToken.for_user(user)
        return {'access': str(refresh.access_token), 'refresh': str(refresh)}

    def authenticate(self, user=None):
        tokens = self.get_tokens(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        return tokens

    def test_obtain_token(self):
        response = self.client.post('/api/token/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_protected_endpoint_without_token(self):
        response = self.client.get('/api/protected/')
        self.assertEqual(response.status_code, 401)

    def test_protected_endpoint_with_token(self):
        self.authenticate()
        response = self.client.get('/api/protected/')
        self.assertEqual(response.status_code, 200)

    def test_token_refresh(self):
        tokens = self.get_tokens()
        response = self.client.post('/api/token/refresh/', {
            'refresh': tokens['refresh']
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)

    def test_blacklist_token(self):
        tokens = self.get_tokens()
        response = self.client.post('/api/token/blacklist/', {
            'refresh': tokens['refresh']
        })
        self.assertEqual(response.status_code, 200)

        # The old refresh token should now fail
        response = self.client.post('/api/token/refresh/', {
            'refresh': tokens['refresh']
        })
        self.assertEqual(response.status_code, 401)
```

### Mocking token expiry in tests

```python
from unittest.mock import patch
from datetime import timedelta
from django.utils import timezone

def test_expired_access_token(self):
    with patch('rest_framework_simplejwt.tokens.AccessToken.lifetime',
               new_callable=lambda: property(lambda self: timedelta(seconds=-1))):
        tokens = self.get_tokens()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        response = self.client.get('/api/protected/')
        self.assertEqual(response.status_code, 401)
```

---

## Common Errors & Troubleshooting

### `401 Unauthorized` — "No active account found with the given credentials"
- The username/password is wrong, or the user does not exist.
- Make sure `is_active=True` on the user account.
- If using a custom user model, confirm `USERNAME_FIELD` is correct.

### `401 Unauthorized` — "Token is invalid or expired"
- The access token has expired. The client should refresh it.
- Check that `ACCESS_TOKEN_LIFETIME` is not too short.
- Ensure the server clock is synchronized (NTP).

### `401 Unauthorized` — "Token is blacklisted"
- The refresh token was already used with rotation enabled, or explicitly blacklisted.
- The user needs to log in again.

### `500 Internal Server Error` — "No module named 'rest_framework_simplejwt'"
- Run `pip install djangorestframework-simplejwt` and ensure the virtualenv is active.

### Clock skew issues
If tokens are rejected as expired immediately, your server clock may be out of sync. On Linux:

```bash
sudo timedatectl set-ntp true
```

### `django.db.utils.ProgrammingError` — "token_blacklist_outstandingtoken does not exist"
- You added `token_blacklist` to `INSTALLED_APPS` but forgot to migrate.
- Run `python manage.py migrate`.

### Custom claims not appearing in refresh response
- Custom claims added in `get_token()` are baked into the token at creation.
- The refresh endpoint generates a new access token from the existing refresh token — it does not re-query the database for updated claims unless you override `TokenRefreshSerializer`.

To always fetch fresh claims on refresh:

```python
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

class FreshClaimsTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        # Re-fetch user and add fresh claims
        refresh = RefreshToken(attrs['refresh'])
        user_id = refresh['user_id']
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(pk=user_id)
        new_refresh = RefreshToken.for_user(user)
        data['access'] = str(new_refresh.access_token)
        return data
```

---

## Quick Reference Cheatsheet

```python
# Generate tokens manually
from rest_framework_simplejwt.tokens import RefreshToken

refresh = RefreshToken.for_user(user)
access = str(refresh.access_token)
refresh_str = str(refresh)

# Add custom claims
refresh['my_claim'] = 'my_value'

# Decode a token (read claims)
from rest_framework_simplejwt.tokens import AccessToken
token = AccessToken(token_string)
print(token['user_id'])
print(token['exp'])

# Blacklist a refresh token
from rest_framework_simplejwt.tokens import RefreshToken
token = RefreshToken(refresh_string)
token.blacklist()

# Use in APIClient (tests)
client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
```
