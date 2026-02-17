"""
BaseViewSet — Central error handling + perform_* hooks for Django REST Framework.

Usage:
    from .base_viewset import BaseViewSet

    class MyModelViewSet(BaseViewSet, viewsets.ModelViewSet):
        queryset = MyModel.objects.all()
        serializer_class = MyModelSerializer
"""

import logging
from contextlib import contextmanager

from django.core.exceptions import (
    ObjectDoesNotExist,
    MultipleObjectsReturned,
    PermissionDenied,
    ValidationError as DjangoValidationError,
    FieldDoesNotExist,
    SuspiciousOperation,
    DisallowedHost,
    ImproperlyConfigured,
)
from django.db import (
    IntegrityError,
    OperationalError,
    ProgrammingError,
    DataError,
    DatabaseError,
)
from django.db.models.deletion import ProtectedError, RestrictedError
from django.http import Http404

from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    NotAuthenticated,
    PermissionDenied as DRFPermissionDenied,
    NotFound,
    MethodNotAllowed,
    NotAcceptable,
    UnsupportedMediaType,
    Throttled,
    ValidationError as DRFValidationError,
    ParseError,
)
from rest_framework.response import Response
from rest_framework.viewsets import ViewSetMixin

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _error_response(
    message: str,
    code: str,
    status_code: int,
    errors: dict | list | None = None,
    extra: dict | None = None,
) -> Response:
    """
    Unified error response shape:

    {
        "error": {
            "code":    "validation_error",
            "message": "Human-readable summary.",
            "details": { ... } | [ ... ] | null
        }
    }
    """
    payload: dict = {
        "error": {
            "code": code,
            "message": message,
            "details": errors,
        }
    }
    if extra:
        payload["error"].update(extra)
    return Response(payload, status=status_code)


# ---------------------------------------------------------------------------
# BaseViewSet
# ---------------------------------------------------------------------------

class BaseViewSet(ViewSetMixin):
    """
    Drop-in mixin that provides:

    • Centralised error handling via handle_exception()
    • perform_create / perform_update / perform_destroy with before/after hooks
    • perform_list / perform_retrieve hooks
    • Safe get_queryset / get_object wrappers
    • Optional request/response logging (set LOG_REQUESTS = True)

    Inherit **before** the concrete viewset class so MRO works correctly:

        class ArticleViewSet(BaseViewSet, viewsets.ModelViewSet): ...
    """

    LOG_REQUESTS: bool = False          # flip to True for debug logging
    SAFE_DB_ERRORS: bool = True         # convert DB errors → 500 (not leaking SQL)

    # ------------------------------------------------------------------
    # Error handling
    # ------------------------------------------------------------------

    def handle_exception(self, exc: Exception) -> Response:  # noqa: C901 (complexity accepted)
        """
        Single entry-point for all exceptions raised anywhere in the viewset.
        Maps Django + DRF exceptions → consistent JSON error responses.
        """
        request = getattr(self, "request", None)

        # ── DRF native exceptions ──────────────────────────────────────

        if isinstance(exc, DRFValidationError):
            logger.debug("Validation error: %s", exc.detail)
            return _error_response(
                message="Invalid input.",
                code="validation_error",
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=exc.detail,
            )

        if isinstance(exc, ParseError):
            logger.debug("Parse error: %s", exc.detail)
            return _error_response(
                message="Malformed request body.",
                code="parse_error",
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=exc.detail,
            )

        if isinstance(exc, (NotAuthenticated, AuthenticationFailed)):
            logger.debug("Auth error (%s): %s", type(exc).__name__, exc.detail)
            return _error_response(
                message=str(exc.detail),
                code="authentication_error",
                status_code=exc.status_code,
            )

        if isinstance(exc, (DRFPermissionDenied,)):
            logger.warning("Permission denied: %s", exc.detail)
            return _error_response(
                message=str(exc.detail),
                code="permission_denied",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        if isinstance(exc, NotFound):
            logger.debug("Not found: %s", exc.detail)
            return _error_response(
                message=str(exc.detail),
                code="not_found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if isinstance(exc, MethodNotAllowed):
            return _error_response(
                message=str(exc.detail),
                code="method_not_allowed",
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            )

        if isinstance(exc, NotAcceptable):
            return _error_response(
                message=str(exc.detail),
                code="not_acceptable",
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
            )

        if isinstance(exc, UnsupportedMediaType):
            return _error_response(
                message=str(exc.detail),
                code="unsupported_media_type",
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            )

        if isinstance(exc, Throttled):
            extra = {}
            if exc.wait is not None:
                extra["retry_after"] = exc.wait
            return _error_response(
                message="Request throttled. Try again later.",
                code="throttled",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                extra=extra,
            )

        if isinstance(exc, APIException):
            # Catch-all for any custom DRF APIException subclasses.
            logger.warning("Unhandled APIException (%s): %s", type(exc).__name__, exc.detail)
            return _error_response(
                message=str(exc.detail),
                code=getattr(exc, "default_code", "api_error"),
                status_code=exc.status_code,
            )

        # ── Django core exceptions ─────────────────────────────────────

        if isinstance(exc, Http404):
            logger.debug("Http404: %s", exc)
            return _error_response(
                message="The requested resource was not found.",
                code="not_found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if isinstance(exc, ObjectDoesNotExist):
            logger.debug("ObjectDoesNotExist: %s", exc)
            return _error_response(
                message="The requested object does not exist.",
                code="not_found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if isinstance(exc, MultipleObjectsReturned):
            logger.error("MultipleObjectsReturned: %s", exc)
            return _error_response(
                message="Multiple objects found where only one was expected.",
                code="multiple_objects",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if isinstance(exc, PermissionDenied):
            logger.warning("Django PermissionDenied: %s", exc)
            return _error_response(
                message="You do not have permission to perform this action.",
                code="permission_denied",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        if isinstance(exc, DjangoValidationError):
            # Django's (non-DRF) ValidationError — normalise message_dict or messages.
            logger.debug("Django ValidationError: %s", exc)
            errors = (
                exc.message_dict
                if hasattr(exc, "message_dict")
                else {"non_field_errors": exc.messages}
            )
            return _error_response(
                message="Invalid input.",
                code="validation_error",
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=errors,
            )

        if isinstance(exc, (SuspiciousOperation, DisallowedHost)):
            logger.warning("Suspicious operation (%s): %s", type(exc).__name__, exc)
            return _error_response(
                message="Bad request.",
                code="bad_request",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if isinstance(exc, FieldDoesNotExist):
            logger.error("FieldDoesNotExist: %s", exc)
            return _error_response(
                message="A referenced field does not exist.",
                code="field_does_not_exist",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # ── Database exceptions ────────────────────────────────────────

        if isinstance(exc, (ProtectedError, RestrictedError)):
            dependents = [str(obj) for obj in exc.protected_objects] if hasattr(exc, "protected_objects") else []
            logger.warning("Delete blocked by related objects: %s", exc)
            return _error_response(
                message="Cannot delete this object because it is referenced by other records.",
                code="protected_object",
                status_code=status.HTTP_409_CONFLICT,
                errors={"dependents": dependents[:10]},   # cap for safety
            )

        if isinstance(exc, IntegrityError):
            logger.error("IntegrityError: %s", exc)
            msg = "A database integrity constraint was violated." if self.SAFE_DB_ERRORS else str(exc)
            return _error_response(
                message=msg,
                code="integrity_error",
                status_code=status.HTTP_409_CONFLICT,
            )

        if isinstance(exc, DataError):
            logger.error("DataError: %s", exc)
            msg = "The provided data is invalid for the database schema." if self.SAFE_DB_ERRORS else str(exc)
            return _error_response(
                message=msg,
                code="data_error",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if isinstance(exc, OperationalError):
            logger.critical("DB OperationalError: %s", exc, exc_info=True)
            return _error_response(
                message="A database operational error occurred. Please try again later.",
                code="db_operational_error",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if isinstance(exc, (ProgrammingError, DatabaseError)):
            logger.critical("DB error (%s): %s", type(exc).__name__, exc, exc_info=True)
            return _error_response(
                message="An unexpected database error occurred.",
                code="db_error",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # ── Catch-all ─────────────────────────────────────────────────

        logger.exception(
            "Unhandled exception in %s [%s %s]: %s",
            self.__class__.__name__,
            getattr(request, "method", "?"),
            getattr(request, "path", "?"),
            exc,
        )
        return _error_response(
            message="An unexpected internal error occurred.",
            code="internal_server_error",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    def initial(self, request, *args, **kwargs):
        if self.LOG_REQUESTS:
            logger.debug(
                "→ %s %s | user=%s | data=%s",
                request.method,
                request.path,
                getattr(request.user, "pk", "anon"),
                request.data,
            )
        super().initial(request, *args, **kwargs)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        if self.LOG_REQUESTS:
            logger.debug(
                "← %s %s | status=%s",
                request.method,
                request.path,
                response.status_code,
            )
        return response

    # ------------------------------------------------------------------
    # Context manager for ad-hoc error boundaries inside actions
    # ------------------------------------------------------------------

    @contextmanager
    def error_boundary(self):
        """
        Use inside custom @action methods to re-use the same error handling:

            @action(detail=True, methods=["post"])
            def publish(self, request, pk=None):
                with self.error_boundary():
                    obj = self.get_object()
                    obj.publish()
                    return Response({"status": "published"})
        """
        try:
            yield
        except Exception as exc:
            raise exc   # bubbles up to handle_exception via dispatch()

    # ------------------------------------------------------------------
    # get_queryset / get_object — safe wrappers
    # ------------------------------------------------------------------

    def get_queryset(self):
        """
        Wraps the parent get_queryset, converting raw Django exceptions to DRF ones
        before they escape to handle_exception (so you get a 404 not a 500).
        """
        try:
            return super().get_queryset()
        except ObjectDoesNotExist as exc:
            raise NotFound(detail=str(exc)) from exc

    def get_object(self):
        """
        Wraps the parent get_object with the same safety net.
        """
        try:
            return super().get_object()
        except Http404 as exc:
            raise NotFound(detail="Object not found.") from exc
        except ObjectDoesNotExist as exc:
            raise NotFound(detail=str(exc)) from exc

    # ------------------------------------------------------------------
    # perform_* hooks — override any of these in your subclass
    # ------------------------------------------------------------------

    # ── Create ────────────────────────────────────────────────────────

    def before_perform_create(self, serializer):
        """Called before the object is saved during a create action."""

    def perform_create(self, serializer):
        self.before_perform_create(serializer)
        instance = serializer.save(**self.get_create_kwargs(serializer))
        self.after_perform_create(instance, serializer)
        return instance

    def after_perform_create(self, instance, serializer):
        """Called after the object has been saved during a create action."""

    def get_create_kwargs(self, serializer) -> dict:
        """
        Extra kwargs passed to serializer.save() on create.
        Common use: attach the current user.

            def get_create_kwargs(self, serializer):
                return {"owner": self.request.user}
        """
        return {}

    # ── Update ────────────────────────────────────────────────────────

    def before_perform_update(self, serializer):
        """Called before the object is saved during an update action."""

    def perform_update(self, serializer):
        self.before_perform_update(serializer)
        instance = serializer.save(**self.get_update_kwargs(serializer))
        self.after_perform_update(instance, serializer)
        return instance

    def after_perform_update(self, instance, serializer):
        """Called after the object has been saved during an update action."""

    def get_update_kwargs(self, serializer) -> dict:
        """Extra kwargs passed to serializer.save() on update."""
        return {}

    # ── Destroy ───────────────────────────────────────────────────────

    def before_perform_destroy(self, instance):
        """Called before the object is deleted."""

    def perform_destroy(self, instance):
        self.before_perform_destroy(instance)
        instance.delete()
        self.after_perform_destroy(instance)

    def after_perform_destroy(self, instance):
        """Called after the object has been deleted."""

    # ── List ──────────────────────────────────────────────────────────

    def before_perform_list(self, queryset):
        """Called before the queryset is filtered/paginated for list."""
        return queryset

    def after_perform_list(self, queryset):
        """Called after the queryset is ready, before serialisation."""
        return queryset

    def filter_queryset(self, queryset):
        queryset = self.before_perform_list(queryset)
        queryset = super().filter_queryset(queryset)
        queryset = self.after_perform_list(queryset)
        return queryset

    # ── Retrieve ──────────────────────────────────────────────────────

    def before_perform_retrieve(self, instance):
        """Called just after get_object() on a retrieve action."""

    def after_perform_retrieve(self, instance):
        """Called after retrieve, before the response is returned."""

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        self.before_perform_retrieve(instance)
        serializer = self.get_serializer(instance)
        self.after_perform_retrieve(instance)
        return Response(serializer.data)

    # ------------------------------------------------------------------
    # Success response helper  (optional — use in custom @action methods)
    # ------------------------------------------------------------------

    def success_response(
        self,
        data=None,
        message: str = "Success.",
        status_code: int = status.HTTP_200_OK,
    ) -> Response:
        """
        Standardised success envelope, mirroring the error envelope.

        {
            "message": "Success.",
            "data": { ... }
        }
        """
        return Response(
            {"message": message, "data": data},
            status=status_code,
        )
