"""Parent views — list, detail, create, update."""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q
from django.urls import reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from apps.accounts.mixins import StaffRequiredMixin
from .models import Parent
from .forms import ParentForm


class ParentListView(StaffRequiredMixin, ListView):
    model = Parent
    template_name = "parents/parent_list.html"
    context_object_name = "parents"
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset()
        q = (self.request.GET.get("q") or "").strip()[:100]
        if q:
            # Q() instead of `qs.filter(...) | qs.filter(...)` — the `|`
            # operator loses ordering/select_related and can duplicate rows.
            qs = qs.filter(
                Q(full_name__icontains=q) | Q(cnic__icontains=q)
            )
        return qs


class ParentDetailView(StaffRequiredMixin, DetailView):
    model = Parent
    template_name = "parents/parent_detail.html"
    context_object_name = "parent"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["children"] = self.object.children.select_related("current_class")
        return ctx


class ParentCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Parent
    form_class = ParentForm
    template_name = "parents/parent_form.html"
    permission_required = "parents.add_parent"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumbs"] = [
            {"title": "Parents", "url": reverse("parents:parent_list")},
            {"title": "New"},
        ]
        return ctx

    def form_valid(self, form):
        # Messages belong in form_valid, not get_success_url.
        # get_success_url can be called multiple times (e.g. by test client
        # resolve()), causing duplicate flash messages.
        response = super().form_valid(form)
        messages.success(self.request, "Parent added.")
        return response

    def get_success_url(self):
        return reverse("parents:parent_detail", args=[self.object.pk])


class ParentUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Parent
    form_class = ParentForm
    template_name = "parents/parent_form.html"
    permission_required = "parents.change_parent"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumbs"] = [
            {"title": "Parents", "url": reverse("parents:parent_list")},
            {"title": str(self.object)},
            {"title": "Edit"},
        ]
        return ctx

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Parent updated.")
        return response

    def get_success_url(self):
        return reverse("parents:parent_detail", args=[self.object.pk])
