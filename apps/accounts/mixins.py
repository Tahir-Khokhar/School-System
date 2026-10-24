"""Reusable mixins for class-based views."""
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied


class RoleRequiredMixin:
    """Restrict access to a set of role names. Use after LoginRequiredMixin."""
    allowed_roles = []

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return self.handle_no_permission()
        if user.is_superuser or user.role == "super_admin":
            return super().dispatch(request, *args, **kwargs)
        if self.allowed_roles and user.role not in self.allowed_roles:
            raise PermissionDenied("You do not have permission to access this page.")
        return super().dispatch(request, *args, **kwargs)


class StaffRequiredMixin(LoginRequiredMixin):
    """Only staff/admin roles can access. Students and parents are blocked."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        user = request.user
        if user.is_superuser or user.role == "super_admin":
            return super().dispatch(request, *args, **kwargs)
        if user.role in {"student", "parent"}:
            raise PermissionDenied("Students and parents cannot access staff pages.")
        return super().dispatch(request, *args, **kwargs)


class BreadcrumbMixin:
    breadcrumbs = []
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumbs"] = self.breadcrumbs
        return ctx
