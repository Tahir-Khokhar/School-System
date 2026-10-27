"""
Audit log middleware — records login/logout events + key model changes.

We piggyback on Django's built-in user_logged_in / user_logged_out signals to
record auth events. (The middleware itself is intentionally minimal — the
heavy lifting is done by the signal handlers connected in apps.py.)
"""
import json
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from .models import AuditLog, AuditLogService


class AuditLogMiddleware:
    """Pass-through middleware. The login/logout audit hooks live below as
    @receiver-decorated signal handlers, which is the idiomatic Django way.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        pass


# ---------------------------------------------------------------------------
# Signal handlers — wire up login/logout auditing.
# These MUST be imported at app-ready time. apps.py's ready() method imports
# this module so the receivers get registered.
# ---------------------------------------------------------------------------
@receiver(user_logged_in)
def _audit_user_logged_in(sender, request, user, **kwargs):
    """Record every successful login."""
    ip = ""
    if request is not None:
        xff = request.META.get("HTTP_X_FORWARDED_PROTO", "")
        ip = (xff.split(",")[0].strip() if xff else request.META.get("REMOTE_ADDR", ""))
    AuditLogService.log(
        user=user,
        action="login",
        obj=user,
        description=f"User logged in from IP {ip}",
    )


@receiver(user_logged_out)
def _audit_user_logged_out(sender, request, user, **kwargs):
    """Record every logout."""
    ip = ""
    if request is not None:
        xff = request.META.get("HTTP_X_FORWARDED_PROTO", "")
        ip = (xff.split(",")[0].strip() if xff else request.META.get("REMOTE_ADDR", ""))
    AuditLogService.log(
        user=user,
        action="logout",
        obj=user,
        description=f"User logged out from IP {ip}",
    )


def log_audit_from_signal(sender, instance, action, user=None, **kwargs):
    """Helper to call from signal handlers."""
    AuditLogService.log(user=user, action=action, obj=instance)
