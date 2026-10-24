"""
Audit log middleware — records login/logout + key model changes.
We piggyback on Django's signals for create/update/delete.
"""
import json
from .models import AuditLog, AuditLogService


class AuditLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Could log requests here
        pass


def log_audit_from_signal(sender, instance, action, user=None, **kwargs):
    """Helper to call from signal handlers."""
    AuditLogService.log(user=user, action=action, obj=instance)
