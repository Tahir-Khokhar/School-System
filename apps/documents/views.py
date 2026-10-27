"""Document Center — secure upload + list + download for student documents.

Permissions:
    - Staff with `documents.add_studentdocument` can upload.
    - Staff with `documents.view_studentdocument` can list + view.
    - Students can see ONLY their own documents (via the portal — those
      views are in apps/portal/, not here).
    - Parents see ONLY their linked children's documents (same portal rule).
"""
import os
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import FileResponse, Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import ListView, CreateView, DetailView, View

from apps.accounts.mixins import StaffRequiredMixin
from apps.students.models import Student
from .models import StudentDocument
from .forms import StudentDocumentForm


class StudentDocumentListView(StaffRequiredMixin, PermissionRequiredMixin, ListView):
    """List all uploaded student documents. Staff-only."""
    model = StudentDocument
    template_name = "documents/list.html"
    context_object_name = "documents"
    paginate_by = 25
    permission_required = "documents.view_studentdocument"

    def get_queryset(self):
        qs = StudentDocument.objects.select_related("student", "uploaded_by")
        student_q = self.request.GET.get("q")
        if student_q:
            qs = qs.filter(student__full_name__icontains=student_q) | \
                 qs.filter(student__registration_no__icontains=student_q)
        return qs.distinct()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumbs"] = [{"title": "Documents"}]
        return ctx


class StudentDocumentCreateView(StaffRequiredMixin, PermissionRequiredMixin, CreateView):
    """Upload a document for a specific student. Validates that the student
    exists before showing the form (uses ?student=<pk> query string)."""
    model = StudentDocument
    form_class = StudentDocumentForm
    template_name = "documents/form.html"
    permission_required = "documents.add_studentdocument"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumbs"] = [
            {"title": "Documents", "url": reverse("documents:list")},
            {"title": "New"},
        ]
        student_id = self.request.GET.get("student") or self.kwargs.get("student_pk")
        if student_id:
            ctx["student"] = get_object_or_404(Student, pk=student_id)
        return ctx

    def form_valid(self, form):
        # The form's student field is set by the user; verified server-side
        # by the form's clean() — but we double-check the FK is valid here.
        student = form.cleaned_data.get("student")
        if not student:
            messages.error(self.request, "You must select a student for this document.")
            return self.form_invalid(form)
        form.instance.uploaded_by = self.request.user
        messages.success(self.request, f"Document '{form.instance.name}' uploaded for {student.full_name}.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("documents:detail", args=[self.object.pk])


class StudentDocumentDetailView(StaffRequiredMixin, PermissionRequiredMixin, DetailView):
    """Show document metadata (NOT the file contents — that's a separate
    download view with stricter access control)."""
    model = StudentDocument
    template_name = "documents/detail.html"
    context_object_name = "document"
    permission_required = "documents.view_studentdocument"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["breadcrumbs"] = [
            {"title": "Documents", "url": reverse("documents:list")},
            {"title": self.object.name},
        ]
        return ctx


class StudentDocumentDownloadView(StaffRequiredMixin, PermissionRequiredMixin, View):
    """Download the actual file. Serves the file via Django (NOT via static
    file serving) so that:
      - File access goes through Django's auth + permission checks.
      - Files in /media/ are NEVER directly served (would be a PII leak).
      - We can audit downloads if needed.

    In production, use X-Acceliof-Redirect (nginx) or similar to offload
    the actual file streaming to the web server.
    """
    permission_required = "documents.view_studentdocument"

    def get(self, request, *args, **kwargs):
        document = get_object_or_404(StudentDocument, pk=kwargs["pk"])
        # Defence in depth: even with permission, re-verify the file exists.
        if not document.file or not document.file.name:
            raise Http404("Document file is missing.")
        # Open the file from MEDIA_ROOT. Django's FileField wraps it.
        try:
            document.file.open("rb")
            file_handle = document.file.file
        except (IOError, OSError, FileNotFoundError):
            raise Http404("Document file could not be opened.")
        # Build a safe filename for the Content-Disposition header.
        original_name = os.path.basename(document.file.name)
        response = FileResponse(file_handle, content_type="application/octet-stream")
        response["Content-Disposition"] = f'attachment; filename="{original_name}"'
        # Audit the download (sensitive: a parent's CNIC scan, a student's
        # medical certificate, etc.).
        from apps.audit_logs.models import AuditLogService
        AuditLogService.log(
            user=request.user, action="download",
            obj=document,
            description=f"Downloaded document '{document.name}' for student {document.student.full_name}",
        )
        return response


class StudentDocumentDeleteView(StaffRequiredMixin, PermissionRequiredMixin, View):
    """Delete a document. Hard-delete is intentional (Django file storage
    doesn't support soft-delete natively); the audit log preserves the
    record of deletion so the security trail survives.
    """
    permission_required = "documents.delete_studentdocument"

    def post(self, request, *args, **kwargs):
        document = get_object_or_404(StudentDocument, pk=kwargs["pk"])
        student_name = document.student.full_name
        document_name = document.name
        # Delete the underlying file too.
        if document.file:
            try:
                document.file.delete(save=False)
            except Exception:
                pass  # File already gone — fine.
        document.delete()
        from apps.audit_logs.models import AuditLogService
        AuditLogService.log(
            user=request.user, action="delete",
            obj=None,
            description=f"Deleted document '{document_name}' for student {student_name}",
        )
        messages.success(request, f"Document '{document_name}' deleted.")
        return redirect("documents:list")
