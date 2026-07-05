# OAuth in Django — Definitive Guide

> OAuth shows up in Django projects in two directions. **Django as client**: your app lets users "Sign in with Google/GitHub/Microsoft," using `django-allauth`. **Django as provider**: your app issues OAuth2 access tokens so *other* apps (a mobile app, a partner's server, a public API) can access your API on a user's behalf, using `django-oauth-toolkit`. This guide covers both, end to end, with current package versions as of mid-2026.

---

## Table of Contents

1. [OAuth2 Concepts — How It Actually Works](#concepts)
2. [Which Direction Do You Need?](#direction)
3. [Part A: Django as OAuth Client (Social Login)](#part-a)
   - [A1. Installation](#a1)
   - [A2. Settings Reference](#a2)
   - [A3. Provider Configuration (Google, GitHub, Microsoft)](#a3)
   - [A4. URLs & Templates](#a4)
   - [A5. Custom Adapters](#a5)
   - [A6. Headless / API Mode (SPA, mobile)](#a6)
   - [A7. Getting Data Out — Signals & Models](#a7)
4. [Part B: Django as OAuth Provider (Issuing Tokens)](#part-b)
   - [B1. Installation](#b1)
   - [B2. Settings Reference](#b2)
   - [B3. Registering an Application](#b3)
   - [B4. Protecting Views/APIs](#b4)
   - [B5. Scopes — Endpoint-Level and Per-Object](#b5)
   - [B6. The Grant Flows](#b6)
   - [B7. Stateless Tokens with OIDC/JWT (for scaling)](#b7)
5. [Scaling to Production](#scaling)
6. [Security Checklist (Both Directions)](#security)
7. [Testing](#testing)
8. [Common Errors & Fixes](#errors)
9. [Quick Reference](#reference)

---

## 1. OAuth2 Concepts — How It Actually Works {#concepts}

```
SOCIAL LOGIN (Django is the CLIENT)
────────────────────────────────────
  Browser            Your Django App           Google
     │                      │                     │
     │  clicks "Login       │                     │
     │  with Google"        │                     │
     ├─────────────────────>│                     │
     │                      │  redirect to Google's
     │                      │  authorize URL, with
     │                      │  client_id + redirect_uri
     │                      │  + state + PKCE challenge
     │<─────────────────────┤                     │
     │  redirected to Google                       │
     ├──────────────────────────────────────────>│
     │         user logs in & consents             │
     │<──────────────────────────────────────────┤
     │  redirected back to your                    │
     │  redirect_uri with ?code=...&state=...      │
     ├─────────────────────>│                     │
     │                      │  exchange code for   │
     │                      │  access_token (server-│
     │                      │  to-server, with      │
     │                      │  client_secret)       │
     │                      ├────────────────────>│
     │                      │<────────────────────┤
     │                      │  fetch user's profile │
     │                      │  (email, name, sub id)│
     │                      ├────────────────────>│
     │                      │<────────────────────┤
     │  logged in, session  │                     │
     │  cookie set          │                     │
     │<─────────────────────┤                     │


API PROVIDER (Django is the SERVER / provider)
────────────────────────────────────
  Third-party App      Your Django App (as provider)
        │                       │
        │  redirect user to     │
        │  your /o/authorize/   │
        ├──────────────────────>│
        │  user logs in on YOUR │
        │  site, approves scopes│
        │<──────────────────────┤
        │  redirected back to   │
        │  their redirect_uri   │
        │  with ?code=...       │
        │                       │
        │  POST /o/token/       │
        │  (code, client_id,    │
        │  client_secret)       │
        ├──────────────────────>│
        │<──────────────────────┤
        │  access_token +       │
        │  refresh_token        │
        │                       │
        │  GET /api/me/         │
        │  Authorization:       │
        │  Bearer <token>       │
        ├──────────────────────>│
        │<──────────────────────┤
```

**Key vocabulary:**

| Term | Meaning |
|---|---|
| **Resource Owner** | The end user who owns the data |
| **Client** | The app requesting access (your Django app in Part A; the third-party app in Part B) |
| **Authorization Server** | Issues tokens after the user consents (Google/GitHub in Part A; your Django app in Part B) |
| **Resource Server** | Hosts the protected data behind the access token (Google's API in Part A; your Django API in Part B) |
| **Authorization Code** | Short-lived, single-use code exchanged for a token — never usable on its own |
| **Access Token** | Credential used to call the API. Short-lived (minutes to hours) |
| **Refresh Token** | Long-lived credential used to get a new access token without re-prompting the user |
| **Scope** | A permission string limiting what the token can do (`read:profile`, `email`, etc.) |
| **State** | A random value your app generates, sent to the authorization server, and checked on return — prevents CSRF |
| **PKCE** | Proof Key for Code Exchange — a one-time code challenge/verifier pair that stops a stolen authorization code from being redeemed by anyone but the app that started the flow. Mandatory for public clients (mobile, SPA) and now recommended for all clients |

**Critical principle:** The `client_secret` must never reach the browser or a mobile binary. Any flow where the secret would be embedded client-side (mobile apps, SPAs) uses PKCE instead of, or in addition to, a secret.

---

## 2. Which Direction Do You Need? {#direction}

| You want to... | Use | Package |
|---|---|---|
| Let users log in with Google/GitHub/Microsoft/Apple | Django as **client** | `django-allauth` |
| Let users log in with username/email + password too, alongside social | Django as **client** | `django-allauth` |
| Let a mobile app or SPA you also control call your Django API | Either session auth (allauth headless) or your own token auth (DRF) — full OAuth provider is usually overkill | `django-allauth` (headless) |
| Let **third-party developers** integrate with your API (public API, "Sign in with YourApp") | Django as **provider** | `django-oauth-toolkit` |
| Both — your app logs users in via Google AND exposes its own OAuth API to partners | Both, simultaneously — they don't conflict | Both |

Most Django projects only need Part A. Part B is for when your product itself becomes an OAuth provider for others.

---

# Part A: Django as OAuth Client (Social Login) {#part-a}

`django-allauth` (current stable: **65.18.0**, May 2026) is the de facto standard. It handles local accounts, social accounts, email verification, MFA, and a headless JSON API in one integrated package, so login state doesn't fork into two separate systems depending on how the user signed up.

## A1. Installation {#a1}

```bash
pip install django-allauth
```

Requires Python 3.10+ (3.8/3.9 support was dropped) and supports Django 4.2 through 6.0.

```python
# settings.py
INSTALLED_APPS = [
    # ...
    "django.contrib.auth",
    "django.contrib.sites",   # required by allauth

    "allauth",
    "allauth.account",
    "allauth.socialaccount",

    # one line per provider you want:
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.github",
    "allauth.socialaccount.providers.microsoft",
]

SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",          # local username/password login
    "allauth.account.auth_backends.AuthenticationBackend", # allauth login
]

MIDDLEWARE = [
    # ...
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",  # required since allauth 0.62+
]

TEMPLATES = [
    {
        # ...
        "OPTIONS": {
            "context_processors": [
                # ...
                "django.template.context_processors.request",  # required by allauth
            ],
        },
    },
]
```

```bash
python manage.py migrate
```

## A2. Settings Reference {#a2}

```python
# ─────────────────────────────────────────────────────────────────
# LOGIN METHOD — how local (non-social) users log in
# ─────────────────────────────────────────────────────────────────

# Replaces the old ACCOUNT_AUTHENTICATION_METHOD (deprecated).
# A set: {"username"}, {"email"}, or {"username", "email"}
ACCOUNT_LOGIN_METHODS = {"email"}

# Replaces the old ACCOUNT_EMAIL_REQUIRED / ACCOUNT_USERNAME_REQUIRED /
# ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE settings (all deprecated as of 65.5+).
# '*' marks a field required. Order controls the field order on the form.
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]

# "mandatory" | "optional" | "none"
# mandatory: user cannot log in until they click the emailed confirmation link
ACCOUNT_EMAIL_VERIFICATION = "mandatory"

# Send a 6-8 char numeric/dashed code instead of a link — better for mobile deep-linking issues
ACCOUNT_EMAIL_VERIFICATION_BY_CODE_ENABLED = True

# Prevent user enumeration: password reset / signup responses look identical
# whether or not the email exists, so attackers can't probe for valid accounts
ACCOUNT_PREVENT_ENUMERATION = True

# Where to send users after login/logout
LOGIN_REDIRECT_URL = "/dashboard/"
ACCOUNT_LOGOUT_REDIRECT_URL = "/"

# Rate limiting on login attempts, password resets, etc.
# Format: "attempts/period" e.g. "5/5m" = 5 attempts per 5 minutes
ACCOUNT_RATE_LIMITS = {
    "login_failed": "5/5m",
}

# ─────────────────────────────────────────────────────────────────
# SOCIAL ACCOUNT BEHAVIOR
# ─────────────────────────────────────────────────────────────────

# Auto-create a local account on first social login without a separate
# "complete your signup" step, PROVIDED the provider gives a verified email.
SOCIALACCOUNT_AUTO_SIGNUP = True

# If a user signs up locally with an email, and later logs in via Google
# using that same (verified) email, connect the accounts instead of erroring.
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True

# Only trust an email address from the provider if the provider marked it verified.
SOCIALACCOUNT_STORE_TOKENS = True   # keep provider access/refresh tokens for later API calls

# ─────────────────────────────────────────────────────────────────
# SECURITY — session & cookies
# ─────────────────────────────────────────────────────────────────

SESSION_COOKIE_SECURE = True     # HTTPS only, production
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True

# ─────────────────────────────────────────────────────────────────
# MFA (optional, built into allauth)
# ─────────────────────────────────────────────────────────────────

INSTALLED_APPS += ["allauth.mfa"]
MFA_SUPPORTED_TYPES = ["totp", "webauthn", "recovery_codes"]
```

## A3. Provider Configuration (Google, GitHub, Microsoft) {#a3}

Each provider needs a "social app" registered — either in `settings.py` (simpler, static) or via Django Admin at `/admin/socialaccount/socialapp/` (dynamic, no redeploy to rotate secrets).

```python
# settings.py
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},  # "offline" if you need a refresh token from Google
        "OAUTH_PKCE_ENABLED": True,
        "APP": {
            "client_id": env("GOOGLE_OAUTH_CLIENT_ID"),
            "secret": env("GOOGLE_OAUTH_CLIENT_SECRET"),
        },
    },
    "github": {
        "SCOPE": ["user:email"],
        "APP": {
            "client_id": env("GITHUB_OAUTH_CLIENT_ID"),
            "secret": env("GITHUB_OAUTH_CLIENT_SECRET"),
        },
    },
    "microsoft": {
        "APP": {
            "client_id": env("MICROSOFT_OAUTH_CLIENT_ID"),
            "secret": env("MICROSOFT_OAUTH_CLIENT_SECRET"),
        },
        # Restrict to a specific Azure AD tenant, or "common" for any Microsoft account
        "TENANT": env("MICROSOFT_TENANT_ID", default="common"),
    },
}
```

**Where to get client IDs/secrets:**

| Provider | Console | Redirect URI to register there |
|---|---|---|
| Google | console.cloud.google.com → APIs & Services → Credentials | `https://yourdomain.com/accounts/google/login/callback/` |
| GitHub | github.com/settings/developers → OAuth Apps | `https://yourdomain.com/accounts/github/login/callback/` |
| Microsoft | portal.azure.com → App registrations | `https://yourdomain.com/accounts/microsoft/login/callback/` |

**Never commit client secrets.** Load them from environment variables (`django-environ`, `python-decouple`) or a secrets manager — never hardcode them in `settings.py`.

## A4. URLs & Templates {#a4}

```python
# urls.py
urlpatterns = [
    # ...
    path("accounts/", include("allauth.urls")),
]
```

That single include wires up `/accounts/login/`, `/accounts/signup/`, `/accounts/logout/`, `/accounts/google/login/`, `/accounts/github/login/`, password reset, email verification, MFA setup — the full set.

Minimal login template with a social button:

```html
{% load allauth %}
<form method="post" action="{% url 'account_login' %}">
  {% csrf_token %}
  {{ form.as_p }}
  <button type="submit">Log in</button>
</form>

{% get_providers as socialaccount_providers %}
{% for provider in socialaccount_providers %}
  <a href="{% provider_login_url provider.id %}">
    Continue with {{ provider.name }}
  </a>
{% endfor %}
```

## A5. Custom Adapters {#a5}

Adapters are the primary extension point — override methods instead of monkey-patching views.

```python
# accounts/adapters.py
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class AccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        # e.g. invite-only during a private beta
        return True

    def get_login_redirect_url(self, request):
        return f"/u/{request.user.username}/"


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        # Pull extra provider-specific fields into your user model
        if sociallogin.account.provider == "google":
            user.avatar_url = data.get("picture", "")
        return user

    def pre_social_login(self, request, sociallogin):
        # Called after the user authenticates with the provider but before
        # the local User is created/logged in. Good place for custom
        # account-linking logic beyond the built-in email auto-connect.
        pass
```

```python
# settings.py
ACCOUNT_ADAPTER = "accounts.adapters.AccountAdapter"
SOCIALACCOUNT_ADAPTER = "accounts.adapters.SocialAccountAdapter"
```

## A6. Headless / API Mode (SPA, mobile) {#a6}

If your frontend is React/Vue/a mobile app rather than server-rendered Django templates, use allauth's **headless** mode: the same auth logic, exposed as a JSON API instead of HTML forms.

```python
INSTALLED_APPS += ["allauth.headless"]

HEADLESS_ONLY = False   # True if you have NO server-rendered templates at all
HEADLESS_FRONTEND_URLS = {
    "account_confirm_email": "https://app.example.com/verify-email/{key}",
    "account_reset_password": "https://app.example.com/reset-password",
    "socialaccount_login_error": "https://app.example.com/login/error",
}
```

```python
# urls.py
urlpatterns = [
    path("_allauth/", include("allauth.headless.urls")),
]
```

This exposes endpoints like `POST /_allauth/browser/v1/auth/login`, `POST /_allauth/browser/v1/auth/provider/redirect`, and `GET /_allauth/browser/v1/auth/session`, documented via an auto-generated OpenAPI spec at `/_allauth/openapi.html` when `HEADLESS_SERVE_SPECIFICATION = True`. Token-based (JWT) auth for native mobile apps is supported via `HEADLESS_TOKEN_STRATEGY`.

## A7. Getting Data Out — Signals & Models {#a7}

```python
from allauth.socialaccount.models import SocialAccount
from allauth.account.models import EmailAddress

# All social accounts linked to a user
SocialAccount.objects.filter(user=user)

# The raw profile data the provider returned at login time
social_account = SocialAccount.objects.get(user=user, provider="google")
social_account.extra_data["picture"]

# Provider access/refresh tokens (only present if SOCIALACCOUNT_STORE_TOKENS = True)
# Use these to call the provider's API later (e.g. list the user's Google Calendar events)
token = social_account.socialtoken_set.first()
token.token           # access token
token.token_secret     # refresh token, for providers that issue one

# Verified email addresses
EmailAddress.objects.filter(user=user, verified=True)
```

```python
from allauth.account.signals import user_signed_up
from allauth.socialaccount.signals import social_account_added
from django.dispatch import receiver


@receiver(user_signed_up)
def on_signup(request, user, **kwargs):
    # e.g. enqueue a Celery welcome-email task, exactly as in the Celery guide:
    # transaction.on_commit(lambda: send_welcome_email.delay(user_id=user.id))
    pass
```

---

# Part B: Django as OAuth Provider (Issuing Tokens) {#part-b}

`django-oauth-toolkit` (current stable: **3.3.0**, May 2026) turns your Django app into a spec-compliant OAuth2 authorization server, built on `oauthlib`.

## B1. Installation {#b1}

```bash
pip install django-oauth-toolkit
```

```python
# settings.py
INSTALLED_APPS = [
    # ...
    "oauth2_provider",
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "oauth2_provider.backends.OAuth2Backend",
]

MIDDLEWARE = [
    # ...
    "oauth2_provider.middleware.OAuth2TokenMiddleware",  # populates request.user from a bearer token
]
```

```python
# urls.py
from django.urls import include, path

urlpatterns = [
    path("o/", include("oauth2_provider.urls", namespace="oauth2_provider")),
]
```

```bash
python manage.py migrate oauth2_provider
```

## B2. Settings Reference {#b2}

```python
OAUTH2_PROVIDER = {
    # Access tokens expire after this many seconds. Keep this short —
    # clients use the refresh token to get a new one silently.
    "ACCESS_TOKEN_EXPIRE_SECONDS": 3600,   # 1 hour

    # Refresh tokens expire after this many seconds. Long-lived by design.
    "REFRESH_TOKEN_EXPIRE_SECONDS": 30 * 24 * 3600,   # 30 days

    # Rotate the refresh token every time it's used — a stolen refresh
    # token that gets reused (by both attacker and legitimate client)
    # can then be detected and the whole token family revoked.
    "ROTATE_REFRESH_TOKEN": True,

    # All scopes your API exposes, with human-readable descriptions
    # shown to the user on the consent screen.
    "SCOPES": {
        "read": "Read access to your data",
        "write": "Write access to your data",
        "profile": "Access to your basic profile info",
    },

    # Default scopes granted if a client doesn't request specific ones
    "DEFAULT_SCOPES": ["read"],

    # PKCE is required for "public" clients (mobile, SPA — anything that
    # can't keep a client_secret confidential). Recommended for all clients.
    "PKCE_REQUIRED": True,

    # Only allow HTTPS redirect URIs in production (allow http://localhost for dev)
    "ALLOWED_REDIRECT_URI_SCHEMES": ["https"],

    # How long an authorization code is valid before it must be exchanged
    "AUTHORIZATION_CODE_EXPIRE_SECONDS": 600,   # 10 minutes

    # Custom model if you need extra fields on Application/AccessToken
    # "APPLICATION_MODEL": "myapp.Application",
}

LOGIN_URL = "/accounts/login/"   # where /o/authorize/ redirects unauthenticated users
```

## B3. Registering an Application {#b3}

A "client" (the third-party app that wants to integrate) registers via `/o/applications/` or Django Admin.

| Field | Meaning |
|---|---|
| `name` | Human-readable name shown on the consent screen |
| `client_type` | `confidential` (has a server that can keep the secret, e.g. another backend) or `public` (mobile app, SPA — no secret storage) |
| `authorization_grant_type` | `authorization-code` (the standard, most secure flow), `client-credentials` (machine-to-machine, no user), `password` (legacy, avoid), `openid-hybrid-code` |
| `redirect_uris` | Exact allow-listed callback URL(s) — the authorization server refuses to redirect anywhere else |
| `client_id` / `client_secret` | Generated automatically. `client_secret` is only shown once and hashed at rest from DOT 2.x onward |

```python
from oauth2_provider.models import Application

app = Application.objects.create(
    name="Partner Mobile App",
    client_type=Application.CLIENT_PUBLIC,
    authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
    redirect_uris="com.partner.app://callback",
    user=None,          # None = not tied to a specific Django user (typical for real apps)
)
```

## B4. Protecting Views/APIs {#b4}

### Plain Django views

```python
from oauth2_provider.decorators import protected_resource

@protected_resource(scopes=["read"])
def api_profile(request):
    return JsonResponse({"username": request.user.username})
```

### Django REST Framework

```bash
pip install djangorestframework
```

```python
# settings.py
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "oauth2_provider.contrib.rest_framework.OAuth2Authentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}
```

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from oauth2_provider.contrib.rest_framework import TokenHasScope


class ProfileView(APIView):
    permission_classes = [TokenHasScope]
    required_scopes = ["profile"]

    def get(self, request):
        return Response({"username": request.user.username})
```

## B5. Scopes — Endpoint-Level and Per-Object {#b5}

Scope enforcement happens at **three layers**. Most guides only show the first — the other two are what you actually need for a real multi-tenant or per-resource API.

### Layer 1 — Declare the scopes that exist

```python
OAUTH2_PROVIDER = {
    "SCOPES": {
        "read": "Read access to your data",
        "write": "Write access to your data",
        "jobs:read": "Read job postings",
        "jobs:write": "Create and edit job postings",
        "applications:read": "Read applications submitted to your jobs",
    },
    "DEFAULT_SCOPES": ["read"],
}
```

Use a `resource:action` naming convention (`jobs:read`, `jobs:write`) once you have more than a handful of scopes — a flat `read`/`write` pair doesn't scale past a toy API.

### Layer 2 — Restrict a whole endpoint to a scope

This is what most tutorials stop at. It answers "can this token touch the `/jobs/` endpoint at all," not "can this token touch *this specific* job."

```python
from rest_framework.views import APIView
from oauth2_provider.contrib.rest_framework import TokenHasScope

class JobListView(APIView):
    permission_classes = [TokenHasScope]
    required_scopes = ["jobs:read"]
```

`TokenHasReadWriteScope` is a built-in variant that auto-picks `read`/`write` based on HTTP method (`GET`/`HEAD`/`OPTIONS` need `read`, everything else needs `write`) — useful if your scope names match that pattern.

### Layer 3 — Restrict access to a *specific object* the token is allowed to touch

Scope alone can never express "this token may only read Job #42, not all jobs." That's an authorization decision that has to happen inside the view, using **who the token belongs to** (`request.user`) plus, if you need finer granularity than "the whole user account," **which application/client issued the token** (`request.auth.application`).

```python
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import RetrieveAPIView
from oauth2_provider.contrib.rest_framework import TokenHasScope

class JobDetailView(RetrieveAPIView):
    permission_classes = [TokenHasScope]
    required_scopes = ["jobs:read"]
    queryset = Job.objects.all()

    def get_object(self):
        job = super().get_object()
        # Scope said "this token can read jobs" — this check says
        # "...but only jobs belonging to the token's own user."
        if job.employer_id != self.request.user.id:
            raise PermissionDenied("This token cannot access this job.")
        return job
```

For consent-driven, resource-specific delegation (e.g. a partner app should only ever see the *one* job listing the user picked during the OAuth consent screen, not all of them), store that grant explicitly rather than trying to encode it in scope names:

```python
# models.py
class DelegatedResourceGrant(models.Model):
    access_token = models.ForeignKey(
        "oauth2_provider.AccessToken", on_delete=models.CASCADE
    )
    job = models.ForeignKey("jobs.Job", on_delete=models.CASCADE)

# view
def get_object(self):
    job = super().get_object()
    token = self.request.auth
    if not DelegatedResourceGrant.objects.filter(access_token=token, job=job).exists():
        raise PermissionDenied("Token was not granted access to this job.")
    return job
```

### Dynamic scopes (computed, not static)

If the *set of available scopes itself* needs to depend on runtime data (e.g. a per-plan feature flag: some customers' tokens can request a `billing:write` scope, others can't), implement a custom scopes backend instead of hardcoding everything in settings:

```python
OAUTH2_PROVIDER = {
    "SCOPES_BACKEND_CLASS": "myapp.oauth.CustomScopesBackend",
}
```

```python
# myapp/oauth.py
from oauth2_provider.scopes import BaseScopes

class CustomScopesBackend(BaseScopes):
    def get_all_scopes(self):
        return {"read": "Read access", "write": "Write access", "billing:write": "Manage billing"}

    def get_available_scopes(self, application=None, request=None, *args, **kwargs):
        scopes = ["read", "write"]
        if application and application.organization.plan == "enterprise":
            scopes.append("billing:write")
        return scopes

    def get_default_scopes(self, application=None, request=None, *args, **kwargs):
        return ["read"]
```

## B6. The Grant Flows {#b6}

| Flow | When to use | Needs a client_secret? |
|---|---|---|
| **Authorization Code + PKCE** | Standard for anything with a user — web apps, mobile apps, SPAs. Always prefer this. | Confidential clients: yes. Public clients: no — PKCE replaces it. |
| **Client Credentials** | Machine-to-machine — no human user in the loop (e.g. a partner's server syncing data on a schedule) | Yes |
| **Refresh Token** | Not a standalone flow — used to get a new access token once the first one expires, without re-prompting the user | Depends on client type |
| **Password (Resource Owner Password Credentials)** | Legacy only — the client collects the user's password directly. Deprecated by the OAuth2 spec itself; avoid for new integrations. | Yes |

```bash
# Authorization Code flow — step 1: redirect user here
GET /o/authorize/?response_type=code&client_id=<id>&redirect_uri=<uri>&scope=read+profile&state=<random>&code_challenge=<challenge>&code_challenge_method=S256

# Step 2: exchange the code for a token (server-to-server)
curl -X POST https://yourdomain.com/o/token/ \
  -d "grant_type=authorization_code" \
  -d "code=<code>" \
  -d "redirect_uri=<uri>" \
  -d "client_id=<id>" \
  -d "code_verifier=<verifier>"

# Refresh
curl -X POST https://yourdomain.com/o/token/ \
  -d "grant_type=refresh_token" \
  -d "refresh_token=<token>" \
  -d "client_id=<id>" \
  -d "client_secret=<secret>"

# Client Credentials (no user)
curl -X POST https://yourdomain.com/o/token/ \
  -d "grant_type=client_credentials" \
  -d "client_id=<id>" \
  -d "client_secret=<secret>" \
  -d "scope=read"

# Revoke a token
curl -X POST https://yourdomain.com/o/revoke_token/ \
  -d "token=<token>" \
  -d "client_id=<id>" \
  -d "client_secret=<secret>"
```

## B7. Stateless Tokens with OIDC/JWT (for scaling) {#b7}

By default, every access token DOT issues is an opaque string — validating it means a database (or cache) lookup on **every single API request**. That's fine at moderate traffic, but it becomes a bottleneck once you're running many app servers or splitting your product into microservices that all need to verify the same tokens independently.

The fix is to make tokens self-verifying JWTs signed with an RSA key (RS256), via DOT's built-in OpenID Connect support. Any service holding the public key can verify a token's signature and expiry **without calling back to your auth server or database at all**.

```bash
# Generate a 4096-bit RSA key pair for signing (do this once, keep the private key secret)
openssl genrsa -out oidc.key 4096
```

```python
# settings.py
OAUTH2_PROVIDER = {
    "OIDC_ENABLED": True,
    # Load from a secrets manager / env var — never commit this file or its contents.
    "OIDC_RSA_PRIVATE_KEY": env("OIDC_RSA_PRIVATE_KEY"),
    # Old keys, kept here (unused for signing) so already-issued tokens still verify
    # during a rotation window. Remove only after ID_TOKEN_EXPIRE_SECONDS has elapsed.
    "OIDC_RSA_PRIVATE_KEYS_INACTIVE": [
        env("OIDC_RSA_PRIVATE_KEY_PREVIOUS", default=None),
    ],
    "SCOPES": {
        "openid": "OpenID Connect scope",
        "read": "Read access to your data",
        "write": "Write access to your data",
    },
}
```

Create the `Application` with grant type **Authorization Code** and signing algorithm **RS256** (RS256 is strongly preferred over HS256 — HS256 signs with the `client_secret` itself, which means any service that needs to *verify* a token also needs the secret, defeating the point of a public/private key split; it's also required for public clients since they can't hold a secret at all). Requesting the `openid` scope on the authorization request returns an ID token JWT alongside the access token.

Other services then verify tokens locally:

```python
import jwt
import requests
from functools import lru_cache

@lru_cache(maxsize=1)
def get_jwks():
    # Fetch once, cache — this endpoint is designed to be cached aggressively
    # (see OIDC_JWKS_MAX_AGE_SECONDS in settings)
    return requests.get("https://yourdomain.com/o/.well-known/jwks.json").json()

def verify_token(token: str) -> dict:
    jwks = get_jwks()
    signing_key = jwt.PyJWKClient("https://yourdomain.com/o/.well-known/jwks.json").get_signing_key_from_jwt(token)
    return jwt.decode(token, signing_key.key, algorithms=["RS256"], audience="your-client-id")
```

This is the single biggest lever for scaling an OAuth-protected API horizontally: it turns "every request round-trips to the auth DB" into "every request does a local signature check," and it's the same mechanism identity providers like Auth0/Okta use under the hood.

---

## 5. Scaling to Production {#scaling}

The code from Parts A and B is correct at any scale, but a handful of infrastructure decisions determine whether it stays fast and reliable as traffic grows.

### Sessions and the client direction (allauth)

`django-allauth` logs users in via Django's normal session framework, so **all** of Django's usual session-scaling rules apply:

- Use a shared, fast session backend across all app servers — `django-redis` or `django.contrib.sessions.backends.cache` backed by Redis/Memcached, not the default database-backed sessions, once you have more than one app server.
- Sticky sessions at the load balancer are *not* required if your session backend is shared — prefer a shared backend over sticky sessions, since sticky sessions turn a server restart or deploy into a wave of logged-out users.
- Put `SocialToken`/`SocialAccount` reads behind `select_related`/`prefetch_related` if you're checking linked accounts on every request (e.g. in middleware) — this is an easy N+1 to introduce.

### Tokens and the provider direction (DOT)

- **Prefer JWT/OIDC (B7 above)** once you have more than one app server or any microservice that needs to check tokens — it removes the DB round-trip from the hot path entirely.
- If you stick with opaque tokens, put `AccessToken` lookups behind your normal DB read-replica routing — token validation is a read on every request, and it's one of the highest-QPS queries in the system.
- Run `python manage.py cleartokens` on a schedule (a Celery Beat periodic task, using the pattern from a Celery/Django task-queue guide, is the natural place for this) — expired tokens otherwise accumulate forever and bloat the token table, which slows down the very lookups you're trying to keep fast.
- Set `REFRESH_TOKEN_EXPIRE_SECONDS` and `ROTATE_REFRESH_TOKEN` deliberately rather than leaving defaults — token churn has a direct storage and query-load cost at scale.

### General

- Terminate TLS at the load balancer, but make sure `SECURE_PROXY_SSL_HEADER` is set so Django knows the original request was HTTPS — OAuth redirect URIs and cookie `Secure` flags depend on Django believing the request is on HTTPS, even though the app server itself only sees plain HTTP from the balancer.
- Put your provider's `/.well-known/openid-configuration` and `/.well-known/jwks.json` responses behind a CDN or long cache — they're public, static-ish, and hit by every client that verifies a token.
- Rate limit the `/o/token/` and `/accounts/login/` endpoints at the edge (in addition to `ACCOUNT_RATE_LIMITS`) — these are the endpoints credential-stuffing and token-grinding attacks target first, and app-level rate limiting alone won't survive a real attempt at scale.

---

## 6. Security Checklist (Both Directions) {#security}

- [ ] `client_secret` values are only ever in environment variables or a secrets manager — never in version control
- [ ] Redirect/callback URIs are exact-match allow-listed, no wildcards, no open redirects
- [ ] All OAuth traffic is HTTPS in production — `ALLOWED_REDIRECT_URI_SCHEMES = ["https"]`
- [ ] `state` parameter is validated on every callback (allauth and DOT both do this by default — don't disable it)
- [ ] PKCE is enabled for any public client (mobile, SPA) — `OAUTH_PKCE_ENABLED` / `PKCE_REQUIRED`
- [ ] Access tokens are short-lived; refresh tokens rotate on use (`ROTATE_REFRESH_TOKEN = True`)
- [ ] Provider emails are only trusted when the provider marks them verified — don't auto-link accounts on an unverified email
- [ ] Rate limiting is on for login, signup, and token endpoints
- [ ] `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, and `SESSION_COOKIE_HTTPONLY` are all `True` in production
- [ ] Stored provider tokens (`SocialToken`) are treated as sensitive — encrypted at rest if your compliance requirements call for it
- [ ] Dependencies are kept current — both packages have shipped real CVE fixes (e.g. an open-redirect fix in allauth's SAML IdP-initiated SSO, and identifier-spoofing fixes for OIDC providers using mutable claims); pin versions and update on a schedule rather than never touching them

---

## 7. Testing {#testing}

### Mocking social login (allauth)

```python
from django.test import TestCase
from allauth.socialaccount.models import SocialAccount, SocialApp
from django.contrib.sites.models import Site


class SocialLoginTest(TestCase):
    def setUp(self):
        self.site = Site.objects.get_current()
        self.app = SocialApp.objects.create(
            provider="google", name="Google", client_id="test", secret="test"
        )
        self.app.sites.add(self.site)

    def test_social_account_created(self):
        # Prefer allauth's test helpers (allauth.socialaccount.test) which
        # simulate the full provider callback rather than hand-building
        # SocialAccount rows, so adapter hooks actually run.
        pass
```

### Testing protected API endpoints (django-oauth-toolkit)

```python
from django.test import TestCase
from oauth2_provider.models import Application, AccessToken
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta


class ProtectedAPITest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="alice", password="pass")
        self.application = Application.objects.create(
            name="Test App",
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_CLIENT_CREDENTIALS,
        )
        self.token = AccessToken.objects.create(
            user=self.user,
            application=self.application,
            token="test-token-123",
            expires=timezone.now() + timedelta(hours=1),
            scope="read profile",
        )

    def test_authenticated_request(self):
        response = self.client.get(
            "/api/profile/",
            HTTP_AUTHORIZATION=f"Bearer {self.token.token}",
        )
        self.assertEqual(response.status_code, 200)

    def test_missing_token_rejected(self):
        response = self.client.get("/api/profile/")
        self.assertEqual(response.status_code, 401)
```

---

## 8. Common Errors & Fixes {#errors}

| Error | Root Cause | Fix |
|---|---|---|
| `redirect_uri_mismatch` from provider | The URI you send doesn't byte-for-byte match what's registered in the provider console | Copy exactly, including trailing slash and scheme; check `http` vs `https` |
| `SocialApp matching query does not exist` | No `SocialApp` created for that provider on the current `Site` | Add it in Admin, or via settings `SOCIALACCOUNT_PROVIDERS[...]["APP"]`, and confirm `SITE_ID` matches |
| User created twice for the same person (one local, one social) | Provider email wasn't verified, so allauth couldn't safely auto-connect | Enable `SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT`; only auto-link on verified emails |
| `invalid_grant` on token exchange | Authorization code expired, already used, or `redirect_uri` on the token request doesn't match the one used in the authorize request | Codes are single-use and short-lived — restart the flow; double-check `redirect_uri` consistency |
| `invalid_client` on token exchange | Wrong `client_id`/`client_secret`, or a public client incorrectly sending a secret | Public clients should use PKCE instead of a secret |
| 401 on every API call despite a fresh token | `OAuth2TokenMiddleware` missing, or `DEFAULT_AUTHENTICATION_CLASSES` not set for DRF | Add the middleware; set DRF's authentication class |
| Consent screen shows the wrong scopes | `OAUTH2_PROVIDER["SCOPES"]` dict not updated after adding a new API capability | Add the scope to settings and to the specific view's `required_scopes` |
| `MissingSchema` / CSRF errors mixing headless API and template-based views | `HEADLESS_ONLY` misconfigured, or the request context processor missing | Set `HEADLESS_ONLY` correctly for your architecture; ensure `django.template.context_processors.request` is present |
| allauth `AccountMiddleware` missing error | Introduced as required in allauth 0.62+, easy to miss on upgrades from older versions | Add `"allauth.account.middleware.AccountMiddleware"` to `MIDDLEWARE` |

---

## 9. Quick Reference {#reference}

```bash
# Install both directions
pip install django-allauth django-oauth-toolkit

# Migrate
python manage.py migrate
```

```python
# urls.py — both directions can coexist
urlpatterns = [
    path("accounts/", include("allauth.urls")),          # social login (client)
    path("o/", include("oauth2_provider.urls", namespace="oauth2_provider")),  # your API (provider)
]
```

```python
# Client direction — check a user's linked social accounts
from allauth.socialaccount.models import SocialAccount
SocialAccount.objects.filter(user=user)

# Provider direction — protect a DRF view
from oauth2_provider.contrib.rest_framework import TokenHasScope
class MyView(APIView):
    permission_classes = [TokenHasScope]
    required_scopes = ["read"]
```

```python
# Core settings to always set explicitly, not leave at defaults
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
OAUTH2_PROVIDER = {"PKCE_REQUIRED": True, "ROTATE_REFRESH_TOKEN": True}
```
