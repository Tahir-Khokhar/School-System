"""Audit log model + middleware."""
from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    class Action(models.TextChoices):
        CREATE = "create", "Create"
        UPDATE = "update", "Update"
        DELETE = "delete", "Delete"
        LOGIN = "login", "Login"
        LOGOUT = "logout", "Logout"
        WORKFLOW = "workflow", "Workflow Transition"
        PAYMENT = "payment", "Payment"
        PUBLISH = "publish", "Publish"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs")
    action = models.CharField(max_length=15, choices=Action.choices, db_index=True)
    object_repr = models.CharField(max_length=300)
    object_app = models.CharField(max_length=50, blank=True)
    object_model = models.CharField(max_length=50, blank=True)
    object_pk = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [models.Index(fields=["user", "action"])]

    def __str__(self):
        return f"{self.timestamp:%Y-%m-%d %H:%M} — {self.action} — {self.object_repr}"


class AuditLogService:
    """Service for writing audit logs from anywhere in the codebase."""

    @staticmethod
    def log(*, user=None, action="update", obj=None, description="", ip=None):
        if obj is not None:
            object_repr = str(obj)[:300]
            object_app = getattr(getattr(obj, "_meta", None), "app_label", "") if hasattr(obj, "_meta") else ""
            object_model = getattr(getattr(obj, "_meta", None), "model_name", "") if hasattr(obj, "_meta") else ""
            object_pk = str(getattr(obj, "pk", "") or "")
        else:
            object_repr = object_app = object_model = object_pk = ""
        return AuditLog.objects.create(
            user=user, action=action, object_repr=object_repr,
            object_app=object_app, object_model=object_model,
            object_pk=object_pk, description=description, ip_address=ip,
        )
