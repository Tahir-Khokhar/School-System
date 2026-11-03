
"""
Document Center — secure upload, listing, detail, download, and deletion.

Permissions:
    - Staff with documents.add_studentdocument can upload.
    - Staff with documents.view_studentdocument can list and view.
    - Staff with documents.delete_studentdocument can delete.
    - Students access only their own documents through portal views.
    - Parents access only their linked children's documents through portal views.

Security:
    - All staff views require authentication and staff authorization.
    - Model permissions are checked independently.
    - Downloads are served through Django, not direct media URLs.
    - Document downloads and deletions are audited.
"""

import logging
import os

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db import transaction
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView, View

from apps.accounts.mixins import StaffRequiredMixin
from apps.students.models import Student

from .forms import StudentDocumentForm
from .models import StudentDocument


logger = logging.getLogger(__name__)


# ==========================================================
# DOCUMENT LIST
# ==========================================================

class StudentDocumentListView(
    StaffRequiredMixin,
    PermissionRequiredMixin,
    ListView,
):
    """
    Display student documents.

    Only authorized staff with view permission can access
    the complete document listing.
    """

    model = StudentDocument
    template_name = "documents/list.html"
    context_object_name = "documents"
    paginate_by = 25

    permission_required = "documents.view_studentdocument"

    def get_queryset(self):
        """Retrieve documents and efficiently load related records."""

        queryset = StudentDocument.objects.select_related(
            "student",
            "uploaded_by",
        )

        # Search by student name or registration number.
        search_query = self.request.GET.get("q", "").strip()

        if search_query:
            queryset = queryset.filter(
                Q(student__full_name__icontains=search_query)
                | Q(student__registration_no__icontains=search_query)
            )

        return queryset.order_by("-created_at").distinct()

    def get_context_data(self, **kwargs):
        """Add breadcrumb information to the template."""

        context = super().get_context_data(**kwargs)

        context["breadcrumbs"] = [
            {"title": "Documents"},
        ]

        return context


# ==========================================================
# DOCUMENT CREATE / UPLOAD
# ==========================================================

class StudentDocumentCreateView(
    StaffRequiredMixin,
    PermissionRequiredMixin,
    CreateView,
):
    """
    Upload a document for a student.

    Supports:
        - ?student=<student_pk>
        - URL containing student_pk

    The selected student is verified server-side.
    """

    model = StudentDocument
    form_class = StudentDocumentForm
    template_name = "documents/form.html"

    permission_required = "documents.add_studentdocument"

    def get_preselected_student(self):
        """Retrieve and cache the student selected in the URL."""

        if not hasattr(self, "_preselected_student"):

            student_id = (
                self.request.GET.get("student")
                or self.kwargs.get("student_pk")
            )

            self._preselected_student = (
                get_object_or_404(Student, pk=student_id)
                if student_id
                else None
            )

        return self._preselected_student

    def get_initial(self):
        """Preselect the student in the upload form when provided."""

        initial = super().get_initial()

        student = self.get_preselected_student()

        if student:
            initial["student"] = student

        return initial

    def get_context_data(self, **kwargs):
        """Add breadcrumbs and selected student to the template."""

        context = super().get_context_data(**kwargs)

        context["breadcrumbs"] = [
            {
                "title": "Documents",
                "url": reverse("documents:list"),
            },
            {"title": "New"},
        ]

        context["student"] = self.get_preselected_student()

        return context

    def form_valid(self, form):
        """Validate ownership fields and save the uploaded document."""

        selected_student = self.get_preselected_student()

        student = (
            selected_student
            or form.cleaned_data.get("student")
        )

        if not student:
            messages.error(
                self.request,
                "You must select a student for this document.",
            )
            return self.form_invalid(form)

        # Always assign the verified student.
        form.instance.student = student

        # Record the authenticated uploader.
        form.instance.uploaded_by = self.request.user

        response = super().form_valid(form)

        messages.success(
            self.request,
            f"Document '{self.object.name}' uploaded successfully "
            f"for {student.full_name}.",
        )

        return response

    def get_success_url(self):
        """Redirect to the uploaded document's detail page."""

        return reverse(
            "documents:detail",
            args=[self.object.pk],
        )


# ==========================================================
# DOCUMENT DETAIL
# ==========================================================

class StudentDocumentDetailView(
    StaffRequiredMixin,
    PermissionRequiredMixin,
    DetailView,
):
    """
    Display document metadata.

    The actual file content is served separately through
    StudentDocumentDownloadView.
    """

    model = StudentDocument
    template_name = "documents/detail.html"
    context_object_name = "document"

    permission_required = "documents.view_studentdocument"

    def get_queryset(self):
        """Load related student and uploader information efficiently."""

        return super().get_queryset().select_related(
            "student",
            "uploaded_by",
        )

    def get_context_data(self, **kwargs):
        """Add document breadcrumbs."""

        context = super().get_context_data(**kwargs)

        context["breadcrumbs"] = [
            {
                "title": "Documents",
                "url": reverse("documents:list"),
            },
            {
                "title": self.object.name,
            },
        ]

        return context


# ==========================================================
# DOCUMENT DOWNLOAD
# ==========================================================

class StudentDocumentDownloadView(
    StaffRequiredMixin,
    PermissionRequiredMixin,
    View,
):
    """
    Securely download student documents.

    File access passes through Django authentication and
    permission checks.

    Production deployment should prevent direct public
    access to the underlying media storage.
    """

    permission_required = "documents.view_studentdocument"

    def get(self, request, *args, **kwargs):
        """Open and securely stream the requested document."""

        document = get_object_or_404(
            StudentDocument.objects.select_related("student"),
            pk=kwargs["pk"],
        )

        # Verify that a file is associated with the document.
        if not document.file or not document.file.name:
            raise Http404("Document file is missing.")

        # Generate a safe download filename.
        original_name = os.path.basename(
            document.file.name.replace("\\", "/")
        )

        if not original_name:
            raise Http404("Invalid document filename.")

        # Open the file through Django's storage backend.
        try:
            document.file.open("rb")
            file_handle = document.file.file

        except (OSError, ValueError) as error:
            raise Http404(
                "Document file could not be opened."
            ) from error

        # Audit the successful file access.
        try:
            from apps.audit_logs.models import AuditLogService

            AuditLogService.log(
                user=request.user,
                action="download",
                obj=document,
                description=(
                    f"Downloaded student document "
                    f"'{document.name}' (document ID: {document.pk})."
                ),
            )

        except Exception:
            # Close the opened file if audit logging fails.
            file_handle.close()
            raise

        # Use FileResponse to safely construct Content-Disposition.
        response = FileResponse(
            file_handle,
            as_attachment=True,
            filename=original_name,
            content_type="application/octet-stream",
        )

        # Security headers for downloaded documents.
        response["X-Content-Type-Options"] = "nosniff"
        response["Cache-Control"] = "private, no-store"

        return response


# ==========================================================
# DOCUMENT DELETE
# ==========================================================

class StudentDocumentDeleteView(
    StaffRequiredMixin,
    PermissionRequiredMixin,
    View,
):
    """
    Delete a student document.

    Deletion is POST-only.

    The audit record and database deletion are performed
    within a database transaction. The stored file is
    removed after the database transaction commits.
    """

    permission_required = "documents.delete_studentdocument"

    def post(self, request, *args, **kwargs):
        """Delete the document and record the action."""

        document = get_object_or_404(
            StudentDocument.objects.select_related("student"),
            pk=kwargs["pk"],
        )

        document_name = document.name
        document_id = document.pk
        student_name = document.student.full_name

        # Retain the storage reference before deleting the DB record.
        file_name = (
            document.file.name
            if document.file
            else None
        )

        storage = (
            document.file.storage
            if file_name
            else None
        )

        # Import locally to avoid unnecessary module-level coupling.
        from apps.audit_logs.models import AuditLogService

        # Record the audit event and delete the database record
        # atomically. Preserve the document reference in the audit log.
        with transaction.atomic():

            AuditLogService.log(
                user=request.user,
                action="delete",
                obj=document,
                description=(
                    f"Deleted document '{document_name}' "
                    f"(document ID: {document_id}) "
                    f"for student {student_name}."
                ),
            )

            document.delete()

        # Delete the physical file after the database transaction.
        # If storage deletion fails, retain an administrator warning.
        if file_name and storage:

            try:
                storage.delete(file_name)

            except Exception:
                logger.exception(
                    "Failed to delete stored document file. "
                    "Document ID: %s",
                    document_id,
                )

                messages.warning(
                    request,
                    "The document record was deleted, but its stored "
                    "file could not be removed. Please contact the "
                    "system administrator for storage cleanup.",
                )

            else:
                messages.success(
                    request,
                    f"Document '{document_name}' deleted successfully.",
                )

        else:
            messages.success(
                request,
                f"Document '{document_name}' deleted successfully.",
            )

        return redirect("documents:list")
