# Webhooks in Django — Definitive Guide

> Webhooks are HTTP callbacks that enable real-time communication between systems. In a Django project, you both receive webhooks from external services (Stripe, GitHub, Twilio) and send webhooks to external consumers who subscribe to events in your system. This guide covers every aspect with full detail — no assumptions, no gaps.

---

## Table of Contents

1. [What Webhooks Are and How They Work](#architecture)
2. [Installation](#installation)
3. [Receiving Webhooks — Full Reference](#receiving)
4. [Webhook Security — Signature Verification](#security)
5. [Processing Webhook Events](#processing)
6. [Idempotency — Preventing Duplicate Processing](#idempotency)
7. [Sending Webhooks — Full Reference](#sending)
8. [Webhook Retry Logic](#retry)
9. [Webhook Event Models](#models)
10. [Rate Limiting Webhook Endpoints](#rate-limiting)
11. [Monitoring & Logging](#monitoring)
12. [Testing Webhooks Locally](#testing)
13. [Testing in Code](#testing-code)
14. [Production Configuration](#production)
15. [Common Webhook Providers](#providers)
16. [Common Errors & Fixes](#errors)
17. [Quick Reference](#reference)

---

## 1. What Webhooks Are and How They Work {#architecture}

A webhook is an HTTP POST request sent from one system to another when an event occurs. Instead of polling an API repeatedly ("Did anything happen yet?"), webhooks push data to you in real-time when events happen.

**Two Perspectives:**

### Receiving Webhooks (You are the consumer)

External services (Stripe, GitHub, Shopify) send HTTP POST requests to your endpoints when events occur in their systems.

```
[Stripe] --POST--> [Your Django App: /webhooks/stripe/]
Event: payment succeeded
Payload: { "type": "payment_intent.succeeded", "data": {...} }
```

**Your responsibilities:**
- Expose an HTTP endpoint that accepts POST requests
- Verify the request is authentic (signature verification)
- Return 200 OK immediately (within 5-10 seconds)
- Process the event asynchronously (Celery task)
- Handle duplicate events (idempotency)
- Log all events for debugging

### Sending Webhooks (You are the provider)

Your Django app sends HTTP POST requests to external consumers when events occur in your system.

```
[Your Django App] --POST--> [Customer's Server: https://customer.com/webhook]
Event: order.completed
Payload: { "event": "order.completed", "data": {...} }
```

**Your responsibilities:**
- Allow customers to register webhook URLs
- Send HTTP POST with event data when events occur
- Implement retry logic for failed deliveries
- Sign requests so customers can verify authenticity
- Provide a delivery log/dashboard for customers
- Rate limit to avoid overwhelming customer servers

---

## 2. Installation {#installation}

```bash
pip install celery redis requests cryptography
```

| Package | Min Version | Purpose |
|---|---|---|
| `celery` | `5.0+` | Asynchronous task processing for webhook events |
| `redis` | `4.0+` | Celery broker and idempotency key storage |
| `requests` | `2.28+` | HTTP client for sending webhooks to external URLs |
| `cryptography` | `41.0+` | HMAC signature generation and verification |

**Why async processing is required:** Webhook providers (Stripe, GitHub, etc.) expect a 200 response within 5-10 seconds. If processing takes longer, they mark the delivery as failed and retry. You must return 200 immediately, then process in the background.

---

## 3. Receiving Webhooks — Full Reference {#receiving}

### Basic Webhook Receiver View

```python
# apps/webhooks/views.py
import json
import logging
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .tasks import process_stripe_webhook

logger = logging.getLogger(__name__)


@csrf_exempt  # Webhooks come from external servers — no CSRF token
@require_POST  # Only accept POST requests
def stripe_webhook(request):
    """
    Endpoint for receiving Stripe webhooks.
    Stripe sends events like payment_intent.succeeded, customer.created, etc.
    """
    try:
        # 1. Extract the raw body — needed for signature verification
        payload = request.body

        # 2. Get the Stripe signature header
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
        if not sig_header:
            logger.warning("Stripe webhook: missing signature header")
            return HttpResponse("Missing signature", status=400)

        # 3. Verify the signature (see Security section below)
        # This confirms the request actually came from Stripe
        if not verify_stripe_signature(payload, sig_header):
            logger.warning("Stripe webhook: invalid signature")
            return HttpResponse("Invalid signature", status=400)

        # 4. Parse the JSON payload
        event = json.loads(payload)
        event_type = event.get("type")
        event_id = event.get("id")

        logger.info(f"Stripe webhook received: {event_type} ({event_id})")

        # 5. Queue the event for async processing
        # Do NOT process it here — return 200 immediately
        process_stripe_webhook.delay(event)

        # 6. Return 200 OK immediately
        # Stripe will retry if we return anything other than 2xx
        return HttpResponse("Webhook received", status=200)

    except json.JSONDecodeError:
        logger.error("Stripe webhook: invalid JSON")
        return HttpResponse("Invalid JSON", status=400)

    except Exception as e:
        logger.exception("Stripe webhook: unexpected error")
        # Still return 200 to prevent retries for unrecoverable errors
        # Log the error for manual investigation
        return HttpResponse("Error", status=500)
```

### URL Configuration

```python
# urls.py
from django.urls import path
from apps.webhooks.views import stripe_webhook, github_webhook, shopify_webhook

urlpatterns = [
    # Webhook endpoints — no trailing slash to match provider defaults
    path("webhooks/stripe", stripe_webhook, name="webhook_stripe"),
    path("webhooks/github", github_webhook, name="webhook_github"),
    path("webhooks/shopify", shopify_webhook, name="webhook_shopify"),
]
```

**Important: No trailing slash.** Most webhook providers send to the exact URL you provide. If you register `https://yourapp.com/webhooks/stripe` but your URL pattern requires a trailing slash, Django will 301 redirect, which causes most webhook providers to fail.

### Class-Based View Alternative

```python
# apps/webhooks/views.py
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(View):
    def post(self, request):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

        if not verify_stripe_signature(payload, sig_header):
            return HttpResponse("Invalid signature", status=400)

        event = json.loads(payload)
        process_stripe_webhook.delay(event)
        return HttpResponse("Webhook received", status=200)

    def get(self, request):
        # Some providers send GET requests to verify the endpoint exists
        return HttpResponse("Webhook endpoint active", status=200)
```

---

## 4. Webhook Security — Signature Verification {#security}

### Why Signature Verification Is Critical

Anyone can send a POST request to your webhook endpoint. Without verification, an attacker could:
- Trigger fake payment success events
- Create bogus user accounts
- Manipulate your data

Signature verification proves the request came from the legitimate provider.

### How HMAC Signatures Work

1. The provider generates a signature using HMAC-SHA256 with a secret key
2. The signature is computed from the raw request body
3. The signature is sent in a header (e.g. `X-Hub-Signature-256`)
4. You compute the same signature using the same secret and body
5. If the signatures match, the request is authentic

### Stripe Signature Verification

```python
# apps/webhooks/security.py
import hmac
import hashlib
import time
from django.conf import settings


def verify_stripe_signature(payload: bytes, sig_header: str) -> bool:
    """
    Verify a Stripe webhook signature.
    
    Stripe sends: Stripe-Signature: t=1234567890,v1=signature_hash
    
    Args:
        payload: Raw request body (bytes)
        sig_header: Value of Stripe-Signature header
    
    Returns:
        True if signature is valid, False otherwise
    """
    # Get the webhook secret from settings
    # This is provided by Stripe when you create a webhook endpoint
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    # Parse the signature header
    # Format: t=timestamp,v1=signature
    try:
        elements = sig_header.split(",")
        timestamp = None
        signatures = []

        for element in elements:
            key, value = element.split("=", 1)
            if key == "t":
                timestamp = int(value)
            elif key.startswith("v"):
                signatures.append(value)

        if not timestamp or not signatures:
            return False

    except (ValueError, AttributeError):
        return False

    # Check timestamp is recent (within 5 minutes)
    # Prevents replay attacks
    current_time = int(time.time())
    if abs(current_time - timestamp) > 300:  # 5 minutes
        return False

    # Compute the expected signature
    signed_payload = f"{timestamp}.".encode() + payload
    expected_sig = hmac.new(
        webhook_secret.encode(),
        signed_payload,
        hashlib.sha256
    ).hexdigest()

    # Compare with provided signatures (constant-time comparison)
    # Stripe may send multiple signature versions
    for signature in signatures:
        if hmac.compare_digest(expected_sig, signature):
            return True

    return False
```

### GitHub Signature Verification

```python
def verify_github_signature(payload: bytes, sig_header: str) -> bool:
    """
    Verify a GitHub webhook signature.
    
    GitHub sends: X-Hub-Signature-256: sha256=signature_hash
    
    Args:
        payload: Raw request body (bytes)
        sig_header: Value of X-Hub-Signature-256 header
    
    Returns:
        True if signature is valid, False otherwise
    """
    webhook_secret = settings.GITHUB_WEBHOOK_SECRET

    if not sig_header or not sig_header.startswith("sha256="):
        return False

    # Extract the signature (everything after "sha256=")
    provided_signature = sig_header[7:]  # skip "sha256="

    # Compute expected signature
    expected_signature = hmac.new(
        webhook_secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    # Constant-time comparison to prevent timing attacks
    return hmac.compare_digest(expected_signature, provided_signature)
```

### Shopify Signature Verification

```python
import base64


def verify_shopify_signature(payload: bytes, sig_header: str) -> bool:
    """
    Verify a Shopify webhook signature.
    
    Shopify sends: X-Shopify-Hmac-SHA256: base64_signature
    
    Args:
        payload: Raw request body (bytes)
        sig_header: Value of X-Shopify-Hmac-SHA256 header
    
    Returns:
        True if signature is valid, False otherwise
    """
    webhook_secret = settings.SHOPIFY_WEBHOOK_SECRET

    # Compute the expected signature
    expected_signature = base64.b64encode(
        hmac.new(
            webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).digest()
    ).decode()

    # Compare with provided signature
    return hmac.compare_digest(expected_signature, sig_header)
```

### Settings Configuration

```python
# settings/base.py

# Webhook secrets — NEVER commit these to git
# Get them from environment variables
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET")
GITHUB_WEBHOOK_SECRET = env("GITHUB_WEBHOOK_SECRET")
SHOPIFY_WEBHOOK_SECRET = env("SHOPIFY_WEBHOOK_SECRET")
```

```bash
# .env
STRIPE_WEBHOOK_SECRET=whsec_abcd1234...
GITHUB_WEBHOOK_SECRET=your_github_secret
SHOPIFY_WEBHOOK_SECRET=your_shopify_secret
```

---

## 5. Processing Webhook Events {#processing}

### Celery Task for Async Processing

```python
# apps/webhooks/tasks.py
from celery import shared_task
from celery.utils.log import get_task_logger
from django.db import transaction
from apps.payments.models import Payment
from apps.webhooks.models import WebhookEvent

logger = get_task_logger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_stripe_webhook(self, event_data: dict):
    """
    Process a Stripe webhook event asynchronously.
    
    Args:
        event_data: The complete event object from Stripe
    """
    event_type = event_data.get("type")
    event_id = event_data.get("id")

    try:
        # Log the event to the database for audit trail
        webhook_event = WebhookEvent.objects.create(
            provider="stripe",
            event_type=event_type,
            event_id=event_id,
            payload=event_data,
            status="processing",
        )

        # Route to the appropriate handler based on event type
        handlers = {
            "payment_intent.succeeded": handle_payment_succeeded,
            "payment_intent.payment_failed": handle_payment_failed,
            "customer.subscription.created": handle_subscription_created,
            "customer.subscription.deleted": handle_subscription_deleted,
            "invoice.payment_succeeded": handle_invoice_paid,
            "charge.refunded": handle_charge_refunded,
        }

        handler = handlers.get(event_type)
        if handler:
            handler(event_data)
            webhook_event.status = "processed"
            webhook_event.save(update_fields=["status", "processed_at"])
            logger.info(f"Processed Stripe event: {event_type} ({event_id})")
        else:
            # Unknown event type — log but don't fail
            webhook_event.status = "ignored"
            webhook_event.save(update_fields=["status"])
            logger.info(f"Ignored Stripe event: {event_type} ({event_id})")

    except Exception as exc:
        logger.exception(f"Error processing Stripe event: {event_type} ({event_id})")
        webhook_event.status = "failed"
        webhook_event.error_message = str(exc)
        webhook_event.save(update_fields=["status", "error_message"])

        # Retry the task up to 3 times
        raise self.retry(exc=exc)


def handle_payment_succeeded(event_data: dict):
    """Handle a successful payment from Stripe."""
    payment_intent = event_data["data"]["object"]
    payment_intent_id = payment_intent["id"]
    amount = payment_intent["amount"]  # in cents
    currency = payment_intent["currency"]

    # Update your Payment model
    with transaction.atomic():
        payment = Payment.objects.select_for_update().get(
            stripe_payment_intent_id=payment_intent_id
        )
        payment.status = "succeeded"
        payment.paid_at = timezone.now()
        payment.save(update_fields=["status", "paid_at", "updated_at"])

        # Trigger downstream actions
        # e.g. send receipt email, provision service, etc.
        from apps.orders.tasks import fulfill_order
        fulfill_order.delay(payment.order_id)


def handle_payment_failed(event_data: dict):
    """Handle a failed payment from Stripe."""
    payment_intent = event_data["data"]["object"]
    payment_intent_id = payment_intent["id"]
    failure_message = payment_intent.get("last_payment_error", {}).get("message", "")

    with transaction.atomic():
        payment = Payment.objects.select_for_update().get(
            stripe_payment_intent_id=payment_intent_id
        )
        payment.status = "failed"
        payment.failure_reason = failure_message
        payment.save(update_fields=["status", "failure_reason", "updated_at"])

        # Notify the user
        from apps.notifications.tasks import send_payment_failed_email
        send_payment_failed_email.delay(payment.user_id, payment.id)


def handle_subscription_created(event_data: dict):
    """Handle a new subscription from Stripe."""
    subscription = event_data["data"]["object"]
    customer_id = subscription["customer"]
    subscription_id = subscription["id"]
    status = subscription["status"]

    # Create or update subscription in your database
    from apps.subscriptions.models import Subscription
    Subscription.objects.update_or_create(
        stripe_subscription_id=subscription_id,
        defaults={
            "stripe_customer_id": customer_id,
            "status": status,
            "current_period_start": timezone.datetime.fromtimestamp(
                subscription["current_period_start"], tz=timezone.utc
            ),
            "current_period_end": timezone.datetime.fromtimestamp(
                subscription["current_period_end"], tz=timezone.utc
            ),
        },
    )


def handle_subscription_deleted(event_data: dict):
    """Handle subscription cancellation from Stripe."""
    subscription = event_data["data"]["object"]
    subscription_id = subscription["id"]

    from apps.subscriptions.models import Subscription
    with transaction.atomic():
        sub = Subscription.objects.select_for_update().get(
            stripe_subscription_id=subscription_id
        )
        sub.status = "canceled"
        sub.canceled_at = timezone.now()
        sub.save(update_fields=["status", "canceled_at", "updated_at"])


def handle_invoice_paid(event_data: dict):
    """Handle invoice payment from Stripe."""
    invoice = event_data["data"]["object"]
    subscription_id = invoice.get("subscription")

    if subscription_id:
        # Extend subscription period
        from apps.subscriptions.models import Subscription
        sub = Subscription.objects.get(stripe_subscription_id=subscription_id)
        sub.last_invoice_paid_at = timezone.now()
        sub.save(update_fields=["last_invoice_paid_at", "updated_at"])


def handle_charge_refunded(event_data: dict):
    """Handle charge refund from Stripe."""
    charge = event_data["data"]["object"]
    charge_id = charge["id"]
    refunds = charge.get("refunds", {}).get("data", [])

    # Update payment status
    payment = Payment.objects.get(stripe_charge_id=charge_id)
    payment.status = "refunded"
    payment.refunded_at = timezone.now()
    payment.refund_amount = sum(r["amount"] for r in refunds)
    payment.save(update_fields=["status", "refunded_at", "refund_amount", "updated_at"])
```

### Event Handler Pattern (Alternative)

```python
# apps/webhooks/handlers.py
from typing import Callable, Dict


class WebhookEventHandler:
    """Registry for webhook event handlers."""

    def __init__(self):
        self._handlers: Dict[str, Callable] = {}

    def register(self, event_type: str):
        """Decorator to register a handler for an event type."""
        def decorator(func: Callable):
            self._handlers[event_type] = func
            return func
        return decorator

    def handle(self, event_type: str, event_data: dict):
        """Route an event to its handler."""
        handler = self._handlers.get(event_type)
        if handler:
            handler(event_data)
        else:
            logger.info(f"No handler for event type: {event_type}")


# Create a global handler registry
stripe_handler = WebhookEventHandler()


# Register handlers using decorators
@stripe_handler.register("payment_intent.succeeded")
def handle_payment_succeeded(event_data: dict):
    # ... processing logic


@stripe_handler.register("payment_intent.payment_failed")
def handle_payment_failed(event_data: dict):
    # ... processing logic


# In the Celery task:
@shared_task
def process_stripe_webhook(event_data: dict):
    event_type = event_data.get("type")
    stripe_handler.handle(event_type, event_data)
```

---

## 6. Idempotency — Preventing Duplicate Processing {#idempotency}

Webhook providers retry failed deliveries. This means your endpoint might receive the same event multiple times. You must ensure each event is processed exactly once.

### Why Idempotency Matters

```
Stripe sends: payment_intent.succeeded (id: evt_123)
Your server: 200 OK, but network timeout before Stripe receives response
Stripe retries: payment_intent.succeeded (id: evt_123) — same event
Your server: 200 OK

Without idempotency: payment is credited twice ❌
With idempotency: second event is ignored ✅
```

### Implementation: Idempotency Keys in Redis

```python
# apps/webhooks/idempotency.py
from django_redis import get_redis_connection


def is_duplicate_webhook(provider: str, event_id: str, ttl: int = 86400) -> bool:
    """
    Check if a webhook event has already been processed.
    
    Args:
        provider: Webhook provider name (e.g. "stripe", "github")
        event_id: Unique event ID from the provider
        ttl: How long to remember this event (seconds)
    
    Returns:
        True if this is a duplicate (already processed)
        False if this is the first time seeing this event
    """
    redis = get_redis_connection("default")
    key = f"webhook:idempotency:{provider}:{event_id}"

    # Try to set the key — returns True only if key didn't exist
    is_new = redis.set(key, "1", nx=True, ex=ttl)

    # If is_new is True → this is the first time → NOT a duplicate
    # If is_new is False → key already existed → IS a duplicate
    return not is_new
```

### Usage in Webhook Receiver

```python
# apps/webhooks/views.py
from .idempotency import is_duplicate_webhook


@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

    if not verify_stripe_signature(payload, sig_header):
        return HttpResponse("Invalid signature", status=400)

    event = json.loads(payload)
    event_id = event.get("id")

    # Check for duplicate before queuing the task
    if is_duplicate_webhook("stripe", event_id):
        logger.info(f"Duplicate Stripe webhook ignored: {event_id}")
        # Still return 200 — this is normal behavior
        return HttpResponse("Duplicate webhook", status=200)

    # Queue for processing
    process_stripe_webhook.delay(event)
    return HttpResponse("Webhook received", status=200)
```

### Database-Based Idempotency (Alternative)

```python
# apps/webhooks/models.py
from django.db import models


class WebhookEvent(models.Model):
    """
    Audit log for all received webhook events.
    Also serves as idempotency check via unique constraint.
    """
    provider = models.CharField(max_length=50, db_index=True)
    event_id = models.CharField(max_length=255)
    event_type = models.CharField(max_length=100, db_index=True)
    payload = models.JSONField()
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("processing", "Processing"),
            ("processed", "Processed"),
            ("failed", "Failed"),
            ("ignored", "Ignored"),
        ],
        default="pending",
        db_index=True,
    )
    error_message = models.TextField(blank=True, null=True)
    received_at = models.DateTimeField(auto_now_add=True, db_index=True)
    processed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        # Prevent duplicate events from the same provider
        unique_together = [("provider", "event_id")]
        indexes = [
            models.Index(fields=["provider", "event_type", "received_at"]),
            models.Index(fields=["status", "received_at"]),
        ]
        ordering = ["-received_at"]

    def __str__(self):
        return f"{self.provider}: {self.event_type} ({self.event_id})"
```

```python
# apps/webhooks/views.py
from django.db import IntegrityError
from .models import WebhookEvent


@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

    if not verify_stripe_signature(payload, sig_header):
        return HttpResponse("Invalid signature", status=400)

    event = json.loads(payload)
    event_id = event.get("id")
    event_type = event.get("type")

    try:
        # Try to create the event record
        # Fails if (provider, event_id) already exists
        webhook_event = WebhookEvent.objects.create(
            provider="stripe",
            event_id=event_id,
            event_type=event_type,
            payload=event,
            status="pending",
        )

        # Queue for processing
        process_stripe_webhook.delay(event)
        return HttpResponse("Webhook received", status=200)

    except IntegrityError:
        # Duplicate event — already in database
        logger.info(f"Duplicate Stripe webhook ignored: {event_id}")
        return HttpResponse("Duplicate webhook", status=200)
```

---

## 7. Sending Webhooks — Full Reference {#sending}

### Webhook Subscription Model

```python
# apps/webhooks/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class WebhookSubscription(models.Model):
    """
    Stores customer webhook subscriptions.
    Each customer can register URLs to receive events.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="webhook_subscriptions")
    url = models.URLField(max_length=500)
    secret = models.CharField(max_length=64, unique=True)  # Used for signature generation
    events = models.JSONField(default=list)  # List of event types to receive
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Delivery stats
    total_deliveries = models.IntegerField(default=0)
    successful_deliveries = models.IntegerField(default=0)
    failed_deliveries = models.IntegerField(default=0)
    last_delivery_at = models.DateTimeField(blank=True, null=True)
    last_success_at = models.DateTimeField(blank=True, null=True)
    last_failure_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "is_active"]),
        ]

    def __str__(self):
        return f"{self.user.email}: {self.url}"

    def save(self, *args, **kwargs):
        # Generate a secret if this is a new subscription
        if not self.secret:
            import secrets
            self.secret = secrets.token_hex(32)  # 64-character hex string
        super().save(*args, **kwargs)
```

### Webhook Delivery Log Model

```python
class WebhookDelivery(models.Model):
    """
    Audit log for all webhook deliveries sent to customers.
    """
    subscription = models.ForeignKey(
        WebhookSubscription,
        on_delete=models.CASCADE,
        related_name="deliveries"
    )
    event_type = models.CharField(max_length=100, db_index=True)
    payload = models.JSONField()
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("success", "Success"),
            ("failed", "Failed"),
            ("retrying", "Retrying"),
        ],
        default="pending",
        db_index=True,
    )
    http_status = models.IntegerField(blank=True, null=True)
    response_body = models.TextField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    attempts = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    next_retry_at = models.DateTimeField(blank=True, null=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["subscription", "created_at"]),
            models.Index(fields=["status", "next_retry_at"]),
            models.Index(fields=["event_type", "created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.event_type} to {self.subscription.url} ({self.status})"
```

### Sending Webhook Events

```python
# apps/webhooks/services.py
import hmac
import hashlib
import json
import requests
from django.utils import timezone
from .models import WebhookSubscription, WebhookDelivery


def trigger_webhook_event(event_type: str, event_data: dict, user_id: int = None):
    """
    Trigger a webhook event to all active subscriptions.
    
    Args:
        event_type: The event type (e.g. "order.completed", "user.updated")
        event_data: The event payload to send
        user_id: Optional user ID to filter subscriptions
    """
    # Get all active subscriptions for this event type
    subscriptions = WebhookSubscription.objects.filter(is_active=True)

    if user_id:
        subscriptions = subscriptions.filter(user_id=user_id)

    for subscription in subscriptions:
        # Check if subscription wants this event type
        # Empty events list means "subscribe to all events"
        if subscription.events and event_type not in subscription.events:
            continue

        # Queue the delivery as a Celery task
        from .tasks import send_webhook
        send_webhook.delay(
            subscription_id=subscription.id,
            event_type=event_type,
            event_data=event_data,
        )


def generate_webhook_signature(payload: bytes, secret: str) -> str:
    """
    Generate HMAC signature for webhook payload.
    
    Args:
        payload: JSON-encoded payload as bytes
        secret: The subscription's secret key
    
    Returns:
        Hex-encoded HMAC-SHA256 signature
    """
    return hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()


def send_webhook_request(
    url: str,
    payload: dict,
    secret: str,
    timeout: int = 10
) -> tuple[bool, int, str]:
    """
    Send an HTTP POST request to a webhook URL.
    
    Args:
        url: Destination URL
        payload: Event data to send
        secret: Secret for signature generation
        timeout: Request timeout in seconds
    
    Returns:
        (success: bool, status_code: int, response_body: str)
    """
    # Serialize payload to JSON
    payload_json = json.dumps(payload, separators=(",", ":"))
    payload_bytes = payload_json.encode("utf-8")

    # Generate signature
    signature = generate_webhook_signature(payload_bytes, secret)

    # Prepare headers
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "YourApp-Webhooks/1.0",
        "X-Webhook-Signature": signature,
        "X-Webhook-Signature-Algorithm": "sha256",
    }

    try:
        response = requests.post(
            url,
            data=payload_bytes,
            headers=headers,
            timeout=timeout,
            allow_redirects=False,  # Don't follow redirects
        )

        success = 200 <= response.status_code < 300
        return success, response.status_code, response.text[:1000]  # Limit response body

    except requests.exceptions.Timeout:
        return False, 0, "Request timeout"

    except requests.exceptions.ConnectionError as e:
        return False, 0, f"Connection error: {str(e)}"

    except requests.exceptions.RequestException as e:
        return False, 0, f"Request error: {str(e)}"
```

### Celery Task for Sending Webhooks

```python
# apps/webhooks/tasks.py
from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone
from .models import WebhookSubscription, WebhookDelivery
from .services import send_webhook_request

logger = get_task_logger(__name__)


@shared_task(bind=True, max_retries=5)
def send_webhook(self, subscription_id: int, event_type: str, event_data: dict):
    """
    Send a webhook event to a customer's endpoint.
    Implements exponential backoff retry logic.
    """
    try:
        subscription = WebhookSubscription.objects.get(id=subscription_id)
    except WebhookSubscription.DoesNotExist:
        logger.error(f"Webhook subscription not found: {subscription_id}")
        return

    # Check if subscription is still active
    if not subscription.is_active:
        logger.info(f"Webhook subscription inactive: {subscription_id}")
        return

    # Create or get the delivery record
    delivery, created = WebhookDelivery.objects.get_or_create(
        subscription=subscription,
        event_type=event_type,
        payload=event_data,
        defaults={"status": "pending"}
    )

    delivery.attempts += 1
    delivery.status = "retrying" if delivery.attempts > 1 else "pending"
    delivery.save(update_fields=["attempts", "status"])

    # Build the payload
    payload = {
        "event": event_type,
        "data": event_data,
        "timestamp": timezone.now().isoformat(),
        "webhook_id": str(delivery.id),
    }

    # Send the webhook
    success, status_code, response_body = send_webhook_request(
        url=subscription.url,
        payload=payload,
        secret=subscription.secret,
    )

    # Update delivery record
    delivery.http_status = status_code
    delivery.response_body = response_body

    if success:
        delivery.status = "success"
        delivery.delivered_at = timezone.now()

        # Update subscription stats
        subscription.total_deliveries += 1
        subscription.successful_deliveries += 1
        subscription.last_delivery_at = timezone.now()
        subscription.last_success_at = timezone.now()
        subscription.save(update_fields=[
            "total_deliveries",
            "successful_deliveries",
            "last_delivery_at",
            "last_success_at",
        ])

        logger.info(f"Webhook delivered: {event_type} to {subscription.url}")

    else:
        delivery.status = "failed"
        delivery.error_message = f"HTTP {status_code}: {response_body}"

        # Update subscription stats
        subscription.total_deliveries += 1
        subscription.failed_deliveries += 1
        subscription.last_delivery_at = timezone.now()
        subscription.last_failure_at = timezone.now()
        subscription.save(update_fields=[
            "total_deliveries",
            "failed_deliveries",
            "last_delivery_at",
            "last_failure_at",
        ])

        logger.warning(f"Webhook delivery failed: {event_type} to {subscription.url} (attempt {delivery.attempts})")

        # Retry with exponential backoff
        # Attempt 1: retry in 1 minute
        # Attempt 2: retry in 5 minutes
        # Attempt 3: retry in 15 minutes
        # Attempt 4: retry in 1 hour
        # Attempt 5: retry in 6 hours
        if self.request.retries < self.max_retries:
            retry_delays = [60, 300, 900, 3600, 21600]
            countdown = retry_delays[self.request.retries]
            delivery.next_retry_at = timezone.now() + timezone.timedelta(seconds=countdown)
            delivery.save(update_fields=["next_retry_at"])

            raise self.retry(countdown=countdown)

    delivery.save()
```

### Triggering Webhooks from Django Signals

```python
# apps/orders/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order
from apps.webhooks.services import trigger_webhook_event


@receiver(post_save, sender=Order)
def order_updated_webhook(sender, instance, created, **kwargs):
    """
    Send webhook when an order is created or updated.
    """
    if created:
        event_type = "order.created"
    else:
        event_type = "order.updated"

    event_data = {
        "id": instance.id,
        "status": instance.status,
        "total": str(instance.total),
        "customer_email": instance.customer.email,
        "created_at": instance.created_at.isoformat(),
        "updated_at": instance.updated_at.isoformat(),
    }

    trigger_webhook_event(
        event_type=event_type,
        event_data=event_data,
        user_id=instance.customer_id,
    )


@receiver(post_save, sender=Order)
def order_completed_webhook(sender, instance, **kwargs):
    """
    Send webhook when an order is completed.
    Only triggers when status changes to 'completed'.
    """
    if instance.status == "completed" and instance.tracker.has_changed("status"):
        event_data = {
            "id": instance.id,
            "total": str(instance.total),
            "completed_at": timezone.now().isoformat(),
        }

        trigger_webhook_event(
            event_type="order.completed",
            event_data=event_data,
            user_id=instance.customer_id,
        )
```

---

## 8. Webhook Retry Logic {#retry}

### Exponential Backoff Strategy

When a webhook delivery fails, retry with increasing delays:

| Attempt | Delay | Total Elapsed |
|---|---|---|
| 1 (initial) | 0 | 0 |
| 2 | 1 minute | 1 min |
| 3 | 5 minutes | 6 min |
| 4 | 15 minutes | 21 min |
| 5 | 1 hour | 1h 21min |
| 6 | 6 hours | 7h 21min |

After 6 attempts, mark the delivery as permanently failed.

### Retry Queue Worker

```python
# apps/webhooks/management/commands/retry_failed_webhooks.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.webhooks.models import WebhookDelivery
from apps.webhooks.tasks import send_webhook


class Command(BaseCommand):
    help = "Retry failed webhook deliveries that are due for retry"

    def handle(self, *args, **options):
        # Find all deliveries that:
        # 1. Failed or are retrying
        # 2. Are due for retry (next_retry_at <= now)
        # 3. Haven't exceeded max attempts
        now = timezone.now()
        deliveries = WebhookDelivery.objects.filter(
            status__in=["failed", "retrying"],
            next_retry_at__lte=now,
            attempts__lt=6,
        )

        count = 0
        for delivery in deliveries:
            send_webhook.delay(
                subscription_id=delivery.subscription_id,
                event_type=delivery.event_type,
                event_data=delivery.payload,
            )
            count += 1

        self.stdout.write(f"Queued {count} webhook deliveries for retry")
```

```bash
# Run this command via cron every 5 minutes
*/5 * * * * cd /app && python manage.py retry_failed_webhooks
```

### Celery Beat Alternative

```python
# settings/base.py
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "retry-failed-webhooks": {
        "task": "apps.webhooks.tasks.retry_failed_webhooks",
        "schedule": crontab(minute="*/5"),  # Every 5 minutes
    },
}
```

```python
# apps/webhooks/tasks.py
@shared_task
def retry_failed_webhooks():
    """Periodic task to retry failed webhook deliveries."""
    from django.utils import timezone
    from .models import WebhookDelivery

    now = timezone.now()
    deliveries = WebhookDelivery.objects.filter(
        status__in=["failed", "retrying"],
        next_retry_at__lte=now,
        attempts__lt=6,
    )

    for delivery in deliveries:
        send_webhook.delay(
            subscription_id=delivery.subscription_id,
            event_type=delivery.event_type,
            event_data=delivery.payload,
        )
```

---

## 9. Webhook Event Models {#models}

Complete model definitions for webhook management:

```python
# apps/webhooks/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class WebhookEvent(models.Model):
    """
    Audit log for all incoming webhook events (received from external providers).
    """
    provider = models.CharField(max_length=50, db_index=True)
    event_id = models.CharField(max_length=255)
    event_type = models.CharField(max_length=100, db_index=True)
    payload = models.JSONField()
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("processing", "Processing"),
            ("processed", "Processed"),
            ("failed", "Failed"),
            ("ignored", "Ignored"),
        ],
        default="pending",
        db_index=True,
    )
    error_message = models.TextField(blank=True, null=True)
    received_at = models.DateTimeField(auto_now_add=True, db_index=True)
    processed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = [("provider", "event_id")]
        indexes = [
            models.Index(fields=["provider", "event_type", "received_at"]),
            models.Index(fields=["status", "received_at"]),
        ]
        ordering = ["-received_at"]

    def __str__(self):
        return f"{self.provider}: {self.event_type} ({self.event_id})"


class WebhookSubscription(models.Model):
    """
    Customer webhook subscriptions (outgoing webhooks to customer endpoints).
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="webhook_subscriptions")
    url = models.URLField(max_length=500)
    secret = models.CharField(max_length=64, unique=True)
    events = models.JSONField(default=list, help_text="List of event types to receive. Empty = all events.")
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Delivery stats
    total_deliveries = models.IntegerField(default=0)
    successful_deliveries = models.IntegerField(default=0)
    failed_deliveries = models.IntegerField(default=0)
    last_delivery_at = models.DateTimeField(blank=True, null=True)
    last_success_at = models.DateTimeField(blank=True, null=True)
    last_failure_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "is_active"]),
        ]

    def __str__(self):
        return f"{self.user.email}: {self.url}"

    def save(self, *args, **kwargs):
        if not self.secret:
            import secrets
            self.secret = secrets.token_hex(32)
        super().save(*args, **kwargs)

    @property
    def success_rate(self) -> float:
        if self.total_deliveries == 0:
            return 0.0
        return (self.successful_deliveries / self.total_deliveries) * 100


class WebhookDelivery(models.Model):
    """
    Audit log for all outgoing webhook deliveries to customers.
    """
    subscription = models.ForeignKey(
        WebhookSubscription,
        on_delete=models.CASCADE,
        related_name="deliveries"
    )
    event_type = models.CharField(max_length=100, db_index=True)
    payload = models.JSONField()
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("success", "Success"),
            ("failed", "Failed"),
            ("retrying", "Retrying"),
        ],
        default="pending",
        db_index=True,
    )
    http_status = models.IntegerField(blank=True, null=True)
    response_body = models.TextField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    attempts = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    next_retry_at = models.DateTimeField(blank=True, null=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["subscription", "created_at"]),
            models.Index(fields=["status", "next_retry_at"]),
            models.Index(fields=["event_type", "created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.event_type} to {self.subscription.url} ({self.status})"
```

---

## 10. Rate Limiting Webhook Endpoints {#rate-limiting}

Protect your webhook endpoints from abuse or accidental flooding:

```python
# apps/webhooks/middleware.py
from django.core.cache import cache
from django.http import HttpResponse


class WebhookRateLimitMiddleware:
    """
    Rate limit webhook endpoints to prevent abuse.
    Applies per-IP address.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/webhooks/"):
            ip = self.get_client_ip(request)
            key = f"webhook_rate_limit:{ip}"

            # Allow 100 requests per minute per IP
            count = cache.get(key, 0)
            if count >= 100:
                return HttpResponse("Rate limit exceeded", status=429)

            cache.set(key, count + 1, timeout=60)

        return self.get_response(request)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")
```

```python
# settings/base.py
MIDDLEWARE = [
    ...
    "apps.webhooks.middleware.WebhookRateLimitMiddleware",
    ...
]
```

---

## 11. Monitoring & Logging {#monitoring}

### Logging Configuration

```python
# settings/base.py
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "webhook_file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/var/log/django/webhooks.log",
            "maxBytes": 10 * 1024 * 1024,  # 10 MB
            "backupCount": 10,
            "formatter": "verbose",
        },
    },
    "loggers": {
        "apps.webhooks": {
            "handlers": ["webhook_file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
```

### Monitoring Dashboard

```python
# apps/webhooks/admin.py
from django.contrib import admin
from .models import WebhookEvent, WebhookSubscription, WebhookDelivery


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ["id", "provider", "event_type", "status", "received_at"]
    list_filter = ["provider", "status", "event_type", "received_at"]
    search_fields = ["event_id", "event_type"]
    readonly_fields = ["received_at", "processed_at"]
    date_hierarchy = "received_at"


@admin.register(WebhookSubscription)
class WebhookSubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "url",
        "is_active",
        "success_rate_display",
        "last_delivery_at",
    ]
    list_filter = ["is_active", "created_at"]
    search_fields = ["user__email", "url"]
    readonly_fields = [
        "secret",
        "total_deliveries",
        "successful_deliveries",
        "failed_deliveries",
        "last_delivery_at",
        "last_success_at",
        "last_failure_at",
    ]

    def success_rate_display(self, obj):
        return f"{obj.success_rate:.1f}%"
    success_rate_display.short_description = "Success Rate"


@admin.register(WebhookDelivery)
class WebhookDeliveryAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "subscription",
        "event_type",
        "status",
        "http_status",
        "attempts",
        "created_at",
    ]
    list_filter = ["status", "event_type", "created_at"]
    search_fields = ["subscription__url", "event_type"]
    readonly_fields = ["created_at", "delivered_at"]
    date_hierarchy = "created_at"
```

### Health Check Endpoint

```python
# apps/webhooks/views.py
from django.http import JsonResponse
from .models import WebhookEvent, WebhookDelivery


def webhook_health(request):
    """
    Health check endpoint for monitoring.
    Returns stats about recent webhook activity.
    """
    from django.utils import timezone
    from datetime import timedelta

    now = timezone.now()
    last_hour = now - timedelta(hours=1)

    # Incoming webhook stats
    incoming_total = WebhookEvent.objects.filter(received_at__gte=last_hour).count()
    incoming_failed = WebhookEvent.objects.filter(
        received_at__gte=last_hour,
        status="failed"
    ).count()

    # Outgoing webhook stats
    outgoing_total = WebhookDelivery.objects.filter(created_at__gte=last_hour).count()
    outgoing_failed = WebhookDelivery.objects.filter(
        created_at__gte=last_hour,
        status="failed"
    ).count()

    return JsonResponse({
        "status": "ok",
        "last_hour": {
            "incoming": {
                "total": incoming_total,
                "failed": incoming_failed,
            },
            "outgoing": {
                "total": outgoing_total,
                "failed": outgoing_failed,
            },
        },
    })
```

---

## 12. Testing Webhooks Locally {#testing}

### ngrok for Local Testing

Webhook providers need a public URL to send events to. Use ngrok to expose your local dev server:

```bash
# Install ngrok
brew install ngrok  # macOS
# or download from https://ngrok.com

# Start your Django dev server
python manage.py runserver

# In another terminal, start ngrok
ngrok http 8000

# ngrok will output a public URL like:
# https://abc123.ngrok.io -> http://localhost:8000
```

Register the ngrok URL with the webhook provider:
```
https://abc123.ngrok.io/webhooks/stripe
```

### Webhook Testing Tools

#### 1. webhook.site

Visit https://webhook.site — you get a unique URL. Configure the provider to send to that URL, then inspect the requests in the browser.

#### 2. Stripe CLI

```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe

# Login
stripe login

# Forward webhook events to your local server
stripe listen --forward-to localhost:8000/webhooks/stripe

# Trigger test events
stripe trigger payment_intent.succeeded
stripe trigger customer.subscription.created
```

#### 3. Postman

Create a POST request to your webhook endpoint:

```
POST http://localhost:8000/webhooks/stripe
Headers:
  Stripe-Signature: (generated signature)
Body:
  {
    "id": "evt_test_123",
    "type": "payment_intent.succeeded",
    "data": { ... }
  }
```

---

## 13. Testing in Code {#testing-code}

### Unit Tests for Signature Verification

```python
# apps/webhooks/tests/test_security.py
import hmac
import hashlib
import json
from django.test import TestCase
from apps.webhooks.security import verify_stripe_signature, verify_github_signature


class SignatureVerificationTest(TestCase):
    def test_stripe_signature_valid(self):
        payload = b'{"type": "payment_intent.succeeded"}'
        secret = "whsec_test123"
        timestamp = 1234567890

        # Generate valid signature
        signed_payload = f"{timestamp}.".encode() + payload
        signature = hmac.new(
            secret.encode(),
            signed_payload,
            hashlib.sha256
        ).hexdigest()

        sig_header = f"t={timestamp},v1={signature}"

        # Should return True
        self.assertTrue(verify_stripe_signature(payload, sig_header, secret))

    def test_stripe_signature_invalid(self):
        payload = b'{"type": "payment_intent.succeeded"}'
        sig_header = "t=1234567890,v1=invalid_signature"
        secret = "whsec_test123"

        # Should return False
        self.assertFalse(verify_stripe_signature(payload, sig_header, secret))

    def test_github_signature_valid(self):
        payload = b'{"action": "opened"}'
        secret = "github_secret_123"

        signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        sig_header = f"sha256={signature}"

        self.assertTrue(verify_github_signature(payload, sig_header, secret))
```

### Integration Tests for Webhook Receivers

```python
# apps/webhooks/tests/test_views.py
import json
from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch


class StripeWebhookTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("webhook_stripe")

    @patch("apps.webhooks.views.verify_stripe_signature")
    @patch("apps.webhooks.tasks.process_stripe_webhook.delay")
    def test_webhook_valid_signature(self, mock_task, mock_verify):
        mock_verify.return_value = True

        payload = {
            "id": "evt_test_123",
            "type": "payment_intent.succeeded",
            "data": {"object": {"id": "pi_123"}},
        }

        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="valid_signature",
        )

        self.assertEqual(response.status_code, 200)
        mock_verify.assert_called_once()
        mock_task.assert_called_once_with(payload)

    @patch("apps.webhooks.views.verify_stripe_signature")
    def test_webhook_invalid_signature(self, mock_verify):
        mock_verify.return_value = False

        payload = {"id": "evt_test_123", "type": "payment_intent.succeeded"}

        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="invalid_signature",
        )

        self.assertEqual(response.status_code, 400)

    def test_webhook_missing_signature(self):
        payload = {"id": "evt_test_123", "type": "payment_intent.succeeded"}

        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

    @patch("apps.webhooks.views.verify_stripe_signature")
    @patch("apps.webhooks.views.is_duplicate_webhook")
    def test_webhook_duplicate(self, mock_duplicate, mock_verify):
        mock_verify.return_value = True
        mock_duplicate.return_value = True

        payload = {"id": "evt_test_123", "type": "payment_intent.succeeded"}

        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="valid_signature",
        )

        self.assertEqual(response.status_code, 200)
        # Task should not be called for duplicate
```

### Tests for Sending Webhooks

```python
# apps/webhooks/tests/test_sending.py
from django.test import TestCase
from unittest.mock import patch, Mock
from apps.webhooks.models import WebhookSubscription
from apps.webhooks.services import trigger_webhook_event, send_webhook_request
from django.contrib.auth import get_user_model

User = get_user_model()


class SendWebhookTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com"
        )
        self.subscription = WebhookSubscription.objects.create(
            user=self.user,
            url="https://customer.com/webhook",
            events=["order.created", "order.completed"],
        )

    @patch("apps.webhooks.tasks.send_webhook.delay")
    def test_trigger_webhook_event(self, mock_task):
        event_data = {"order_id": 123, "status": "completed"}

        trigger_webhook_event(
            event_type="order.completed",
            event_data=event_data,
            user_id=self.user.id,
        )

        mock_task.assert_called_once()

    @patch("requests.post")
    def test_send_webhook_success(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        mock_post.return_value = mock_response

        success, status, body = send_webhook_request(
            url="https://customer.com/webhook",
            payload={"event": "test"},
            secret="secret123",
        )

        self.assertTrue(success)
        self.assertEqual(status, 200)
        self.assertEqual(body, "OK")

    @patch("requests.post")
    def test_send_webhook_failure(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        success, status, body = send_webhook_request(
            url="https://customer.com/webhook",
            payload={"event": "test"},
            secret="secret123",
        )

        self.assertFalse(success)
        self.assertEqual(status, 500)
```

---

## 14. Production Configuration {#production}

### Security Checklist

- [ ] All webhook endpoints use HTTPS (never HTTP)
- [ ] Signature verification is enabled for all providers
- [ ] Webhook secrets are stored in environment variables, not code
- [ ] Rate limiting is enabled on webhook endpoints
- [ ] Request body size limit is enforced (prevent memory attacks)
- [ ] Celery workers are properly configured for async processing
- [ ] Failed webhook deliveries are retried with exponential backoff
- [ ] Webhook logs are retained for at least 30 days
- [ ] Monitoring alerts are configured for high failure rates

### Django Settings

```python
# settings/production.py

# Webhook secrets
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET")
GITHUB_WEBHOOK_SECRET = env("GITHUB_WEBHOOK_SECRET")
SHOPIFY_WEBHOOK_SECRET = env("SHOPIFY_WEBHOOK_SECRET")

# Request body size limit (10 MB)
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

# Celery configuration
CELERY_BROKER_URL = env("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND")
CELERY_TASK_ALWAYS_EAGER = False  # Must be False in production
CELERY_TASK_ACKS_LATE = True      # Tasks acknowledged after completion
CELERY_WORKER_PREFETCH_MULTIPLIER = 1  # One task at a time per worker

# Celery Beat schedule for retrying failed webhooks
from celery.schedules import crontab
CELERY_BEAT_SCHEDULE = {
    "retry-failed-webhooks": {
        "task": "apps.webhooks.tasks.retry_failed_webhooks",
        "schedule": crontab(minute="*/5"),
    },
}
```

### nginx Configuration

```nginx
# /etc/nginx/sites-available/yourapp

server {
    listen 443 ssl;
    server_name yourapp.com;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/yourapp.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourapp.com/privkey.pem;

    # Webhook-specific settings
    location /webhooks/ {
        # Increase timeout for slow webhook providers
        proxy_read_timeout 30s;
        proxy_connect_timeout 10s;

        # Preserve original IP for rate limiting
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Real-IP $remote_addr;

        # Request body size limit
        client_max_body_size 10M;

        proxy_pass http://127.0.0.1:8000;
    }
}
```

### Monitoring with Sentry

```python
# settings/production.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

sentry_sdk.init(
    dsn=env("SENTRY_DSN"),
    integrations=[
        DjangoIntegration(),
        CeleryIntegration(),
    ],
    traces_sample_rate=0.1,
    environment="production",
)
```

---

## 15. Common Webhook Providers {#providers}

### Stripe

**Event Types:**
- `payment_intent.succeeded`
- `payment_intent.payment_failed`
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.payment_succeeded`
- `invoice.payment_failed`
- `charge.refunded`

**Documentation:** https://stripe.com/docs/webhooks

**Signature Header:** `Stripe-Signature`

### GitHub

**Event Types:**
- `push`
- `pull_request`
- `issues`
- `release`
- `workflow_run`

**Documentation:** https://docs.github.com/en/webhooks

**Signature Header:** `X-Hub-Signature-256`

### Shopify

**Event Types:**
- `orders/create`
- `orders/updated`
- `orders/paid`
- `customers/create`
- `products/create`

**Documentation:** https://shopify.dev/docs/api/webhooks

**Signature Header:** `X-Shopify-Hmac-SHA256`

### Twilio

**Event Types:**
- `message.status`
- `call.status`

**Documentation:** https://www.twilio.com/docs/usage/webhooks

**Signature Header:** `X-Twilio-Signature`

### PayPal

**Event Types:**
- `PAYMENT.CAPTURE.COMPLETED`
- `PAYMENT.CAPTURE.DENIED`
- `BILLING.SUBSCRIPTION.ACTIVATED`

**Documentation:** https://developer.paypal.com/docs/api-basics/notifications/webhooks/

**Signature Headers:** `PAYPAL-TRANSMISSION-ID`, `PAYPAL-TRANSMISSION-SIG`

---

## 16. Common Errors & Fixes {#errors}

| Error | Root Cause | Fix |
|---|---|---|
| `403 Forbidden` on webhook endpoint | CSRF protection is enabled | Add `@csrf_exempt` decorator to view |
| `Invalid signature` errors | Wrong secret or signature algorithm | Verify you're using the correct webhook secret from the provider dashboard |
| `Duplicate key value violates unique constraint` | Same event processed twice | Implement idempotency check before database insert |
| Webhook delivery times out | Processing takes >10 seconds | Return 200 immediately, process in Celery task |
| Provider marks webhooks as failed | Endpoint returns non-2xx status | Always return 2xx, even for errors; log errors for investigation |
| `ConnectionRefusedError` when sending webhooks | Customer's server is down | Implement retry logic with exponential backoff |
| Webhook events arrive out of order | Network latency | Use event timestamps to order events, not arrival time |
| Memory errors on large payloads | No size limit configured | Set `DATA_UPLOAD_MAX_MEMORY_SIZE` in Django settings |
| `Task has been replaced: {...}` in Celery logs | Task with same ID retried before first completed | Use `task.apply_async(task_id=unique_id)` for idempotent task IDs |
| Signature verification fails locally | Using ngrok, which modifies headers | Check if ngrok adds/removes headers; test with raw POST requests |

---

## 17. Quick Reference {#reference}

### Receiving Webhooks Checklist

```python
# 1. Create view
@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig = request.META.get("HTTP_STRIPE_SIGNATURE")
    
    if not verify_signature(payload, sig):
        return HttpResponse("Invalid signature", status=400)
    
    event = json.loads(payload)
    
    if is_duplicate_webhook("stripe", event["id"]):
        return HttpResponse("Duplicate", status=200)
    
    process_webhook.delay(event)
    return HttpResponse("OK", status=200)

# 2. Process async
@shared_task
def process_webhook(event):
    # Handle event
    pass

# 3. Add URL
path("webhooks/stripe", stripe_webhook)
```

### Sending Webhooks Checklist

```python
# 1. Create subscription model
class WebhookSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    url = models.URLField()
    secret = models.CharField(max_length=64)
    events = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)

# 2. Trigger event
def trigger_event(event_type, data):
    for sub in WebhookSubscription.objects.filter(is_active=True):
        if not sub.events or event_type in sub.events:
            send_webhook.delay(sub.id, event_type, data)

# 3. Send webhook
@shared_task
def send_webhook(subscription_id, event_type, data):
    sub = WebhookSubscription.objects.get(id=subscription_id)
    payload = json.dumps({"event": event_type, "data": data})
    signature = generate_signature(payload, sub.secret)
    
    response = requests.post(
        sub.url,
        data=payload,
        headers={"X-Webhook-Signature": signature},
        timeout=10,
    )
    # Log delivery result
```

### Signature Verification

```python
import hmac
import hashlib

# Stripe
def verify_stripe(payload, sig_header, secret):
    elements = sig_header.split(",")
    timestamp = int(elements[0].split("=")[1])
    signature = elements[1].split("=")[1]
    
    signed_payload = f"{timestamp}.".encode() + payload
    expected = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)

# GitHub
def verify_github(payload, sig_header, secret):
    signature = sig_header.replace("sha256=", "")
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
```

### Testing Commands

```bash
# Start ngrok
ngrok http 8000

# Stripe CLI
stripe listen --forward-to localhost:8000/webhooks/stripe
stripe trigger payment_intent.succeeded

# cURL test
curl -X POST http://localhost:8000/webhooks/test \
  -H "Content-Type: application/json" \
  -d '{"event": "test", "data": {"id": 123}}'
```

### Monitoring Queries

```python
# Recent failures
WebhookEvent.objects.filter(
    status="failed",
    received_at__gte=timezone.now() - timedelta(hours=24)
)

# Delivery success rate
subscription.success_rate  # Uses property from model

# Events to retry
WebhookDelivery.objects.filter(
    status__in=["failed", "retrying"],
    next_retry_at__lte=timezone.now(),
    attempts__lt=6,
)
```
