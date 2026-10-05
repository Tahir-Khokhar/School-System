from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View

from apps.common.models import AcademicYear
from .models import Admission
from .forms import AdmissionForm, AdmissionStatusForm
from .services import AdmissionService, AdmissionWorkflowError


class AdmissionApplicationListView(LoginRequiredMixin, ListView):
    model = Admission
    template_name = "admissions/application_list.html"
    context_object_name = "admissions"
    paginate_by = 25

    def get_queryset(self):
        qs = Admission.objects.select_related("applying_class", "academic_year", "student")
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(full_name__icontains=q) | qs.filter(application_no__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status_choices"] = Admission.Status.choices
        ctx["breadcrumbs"] = [{"title": "Admissions"}]
        return ctx


class AdmissionApplicationCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Admission
    form_class = AdmissionForm
    template_name = "admissions/application_form.html"
    permission_required = "admissions.add_admission"

    def get_initial(self):
        initial = super().get_initial()
        active_year = AcademicYear.objects.get_active()
        if active_year:
            initial["academic_year"] = active_year
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumbs"] = [
            {"title": "Admissions", "url": reverse("admissions:application_list")},
            {"title": "New Application"},
        ]
        return ctx

    def form_valid(self, form):
        form.instance.application_no = Admission.objects.none() and None  # let service set it
        # We'll set the application_no on submit; for now create as draft
        response = super().form_valid(form)
        # Force generate application_no so it's never empty
        if not self.object.application_no:
            from .models import ApplicationNumberService
            self.object.application_no = ApplicationNumberService.generate()
            self.object.save()
        messages.success(self.request, f"Application saved as {self.object.application_no} (Draft).")
        return response

    def get_success_url(self):
        return reverse("admissions:application_detail", args=[self.object.pk])


class AdmissionApplicationDetailView(LoginRequiredMixin, DetailView):
    model = Admission
    template_name = "admissions/application_detail.html"
    context_object_name = "admission"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumbs"] = [
            {"title": "Admissions", "url": reverse("admissions:application_list")},
            {"title": self.object.application_no},
        ]
        ctx["workflow_steps"] = [
            ("Draft", Admission.Status.DRAFT),
            ("Submitted", Admission.Status.SUBMITTED),
            ("Verified", Admission.Status.VERIFIED),
            ("Approved", Admission.Status.APPROVED),
            ("Registered", Admission.Status.REGISTERED),
            ("Completed", Admission.Status.COMPLETED),
        ]
        return ctx


class AdmissionApplicationUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Admission
    form_class = AdmissionForm
    template_name = "admissions/application_form.html"
    permission_required = "admissions.change_admission"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumbs"] = [
            {"title": "Admissions", "url": reverse("admissions:application_list")},
            {"title": self.object.application_no, "url": reverse("admissions:application_detail", args=[self.object.pk])},
            {"title": "Edit"},
        ]
        return ctx

    def get_success_url(self):
        messages.success(self.request, "Application updated.")
        return reverse("admissions:application_detail", args=[self.object.pk])


class WorkflowActionView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Base view for any workflow transition action."""
    action_method = None
    action_label = ""
    permission_required = "admissions.change_admission"

    def post(self, request, *args, **kwargs):
        admission = Admission.objects.get(pk=kwargs["pk"])
        try:
            self.action_method(admission, request.user)
            messages.success(request, f"Admission {self.action_label}: {admission.application_no}")
        except AdmissionWorkflowError as e:
            messages.error(request, str(e))
        return HttpResponseRedirect(reverse("admissions:application_detail", args=[admission.pk]))


class AdmissionSubmitView(WorkflowActionView):
    action_method = AdmissionService.submit
    action_label = "submitted"


class AdmissionVerifyView(WorkflowActionView):
    action_method = AdmissionService.verify
    action_label = "verified"
    permission_required = "admissions.change_admission"


class AdmissionApproveView(WorkflowActionView):
    action_method = AdmissionService.approve
    action_label = "approved"
    permission_required = "admissions.change_admission"


class AdmissionRejectView(WorkflowActionView):
    action_method = AdmissionService.reject
    action_label = "rejected"


class AdmissionRegisterStudentView(WorkflowActionView):
    action_method = AdmissionService.register_student
    action_label = "student registered"
    permission_required = "admissions.change_admission"


class AdmissionGenerateChallanView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "fees.add_feechallan"

    def post(self, request, *args, **kwargs):
        admission = Admission.objects.get(pk=kwargs["pk"])
        try:
            challan = AdmissionService.generate_admission_challan(admission, request.user)
            messages.success(request, f"Admission challan {challan.challan_no} generated.")
        except AdmissionWorkflowError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f"Error generating challan: {e}")
        return HttpResponseRedirect(reverse("admissions:application_detail", args=[admission.pk]))
