from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.generic import ListView, CreateView, DetailView, View, FormView

from .models import DateSheet, DateSheetItem
from .forms import DateSheetForm, DateSheetItemForm


class DateSheetListView(LoginRequiredMixin, ListView):
    model = DateSheet
    template_name = "datesheets/datesheet_list.html"
    context_object_name = "datesheets"
    paginate_by = 25

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumbs"] = [{"title": "Date Sheets"}]
        return ctx


class DateSheetDetailView(LoginRequiredMixin, DetailView):
    model = DateSheet
    template_name = "datesheets/datesheet_detail.html"
    context_object_name = "datesheet"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["items"] = self.object.items.select_related("subject")
        ctx["item_form"] = DateSheetItemForm()
        return ctx


class DateSheetCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = DateSheet
    form_class = DateSheetForm
    template_name = "datesheets/datesheet_form.html"
    permission_required = "datesheets.add_datesheet"

    def get_success_url(self):
        messages.success(self.request, "Date sheet created.")
        return reverse("datesheets:datesheet_detail", args=[self.object.pk])


class DateSheetItemCreateView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    template_name = "datesheets/datesheet_form.html"
    form_class = DateSheetItemForm
    permission_required = "datesheets.add_datesheet"

    def form_valid(self, form):
        ds = get_object_or_404(DateSheet, pk=self.kwargs["pk"])
        item = form.save(commit=False)
        item.datesheet = ds
        item.save()
        messages.success(self.request, "Item added.")
        return redirect("datesheets:datesheet_detail", pk=ds.pk)


class DateSheetPublishView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "datesheets.change_datesheet"

    def post(self, request, *args, **kwargs):
        ds = get_object_or_404(DateSheet, pk=kwargs["pk"])
        ds.status = DateSheet.Status.PUBLISHED
        ds.published_at = timezone.now()
        ds.published_by = request.user
        ds.save()
        messages.success(request, "Date sheet published.")
        return redirect("datesheets:datesheet_detail", pk=ds.pk)
