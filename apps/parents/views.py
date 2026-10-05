from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from .models import Parent
from .forms import ParentForm


class ParentListView(LoginRequiredMixin, ListView):
    model = Parent
    template_name = "parents/parent_list.html"
    context_object_name = "parents"
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(full_name__icontains=q) | qs.filter(cnic__icontains=q)
        return qs


class ParentDetailView(LoginRequiredMixin, DetailView):
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
        ctx["breadcrumbs"] = [{"title": "Parents", "url": reverse("parents:parent_list")}, {"title": "New"}]
        return ctx

    def get_success_url(self):
        from django.contrib import messages
        messages.success(self.request, "Parent added.")
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

    def get_success_url(self):
        from django.contrib import messages
        messages.success(self.request, "Parent updated.")
        return reverse("parents:parent_detail", args=[self.object.pk])
