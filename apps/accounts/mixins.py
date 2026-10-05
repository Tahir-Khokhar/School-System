"""Common reusable mixins for class-based views."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.views.generic import TemplateView


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


class BreadcrumbMixin:
    breadcrumbs = []

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumbs"] = self.breadcrumbs
        return ctx


class HomeView(LoginRequiredMixin, TemplateView):
    """Default dashboard router; subclass with role-based logic."""
    template_name = "dashboard/home.html"
