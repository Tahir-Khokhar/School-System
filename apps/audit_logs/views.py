from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView
from .models import AuditLog


class AuditLogListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = AuditLog
    template_name = "audit_logs/log_list.html"
    context_object_name = "logs"
    paginate_by = 50
    permission_required = "audit_logs.view_auditlog"

    def get_queryset(self):
        qs = AuditLog.objects.select_related("user")
        action = self.request.GET.get("action")
        if action:
            qs = qs.filter(action=action)
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(object_repr__icontains=q) | qs.filter(description__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["action_choices"] = AuditLog.Action.choices
        ctx["breadcrumbs"] = [{"title": "Audit Logs"}]
        return ctx
