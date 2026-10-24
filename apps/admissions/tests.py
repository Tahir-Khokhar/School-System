"""Tests for admission workflow state transitions."""
from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.common.models import AcademicYear, SchoolClass
from apps.admissions.models import Admission, ApplicationNumberService
from apps.admissions.services import AdmissionService, AdmissionWorkflowError

User = get_user_model()


class AdmissionWorkflowTest(TestCase):
    def setUp(self):
        self.year = AcademicYear.objects.create(
            name="2026-2027", start_date=date(2026, 4, 1), end_date=date(2027, 3, 31), is_active=True
        )
        self.cls = SchoolClass.objects.create(name="Grade 8", grade_level="middle", order=1)
        self.user = User.objects.create_user(username="admin", password="x", role="admin")
        self.admission = Admission.objects.create(
            application_no=ApplicationNumberService.generate(),
            full_name="Test Applicant",
            father_name="Father",
            applying_class=self.cls,
            academic_year=self.year,
            admission_date=date(2026, 4, 1),
            parent_name="Parent Name", parent_cnic="42101-1234567-1", parent_phone="+923001234567",
            status=Admission.Status.DRAFT,
        )

    def test_submit_workflow(self):
        AdmissionService.submit(self.admission, self.user)
        self.admission.refresh_from_db()
        self.assertEqual(self.admission.status, Admission.Status.SUBMITTED)

    def test_cannot_approve_from_draft(self):
        with self.assertRaises(AdmissionWorkflowError):
            AdmissionService.approve(self.admission, self.user)

    def test_full_workflow_to_registered(self):
        AdmissionService.submit(self.admission, self.user)
        AdmissionService.verify(self.admission, self.user)
        AdmissionService.approve(self.admission, self.user)
        student, _ = AdmissionService.register_student(self.admission, self.user)
        self.admission.refresh_from_db()
        self.assertEqual(self.admission.status, Admission.Status.REGISTERED)
        self.assertEqual(self.admission.student, student)
        self.assertTrue(student.registration_no.startswith("APS-"))  # APS Lahore prefix
