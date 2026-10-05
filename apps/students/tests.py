"""Tests for student registration number generation."""
from datetime import date
from django.conf import settings
from django.test import TestCase
from apps.students.models import Student, RegistrationNumberService


class RegistrationNumberTest(TestCase):
    def test_generates_unique_sequential_numbers(self):
        # Generate number, create a student with it, then generate another
        n1 = RegistrationNumberService.generate()
        Student.objects.create(
            registration_no=n1, full_name="Test A",
            date_of_birth=date(2010, 1, 1),
        )
        n2 = RegistrationNumberService.generate()
        Student.objects.create(
            registration_no=n2, full_name="Test B",
            date_of_birth=date(2010, 1, 1),
        )
        n3 = RegistrationNumberService.generate()
        self.assertNotEqual(n1, n2)
        self.assertNotEqual(n2, n3)
        prefix = settings.SCHOOL_REGISTRATION_PREFIX  # "APS" by default
        self.assertTrue(n1.startswith(f"{prefix}-"))

    def test_format(self):
        n = RegistrationNumberService.generate()
        # Format: APS-YYYY-NNNNNN (or whatever prefix is configured)
        parts = n.split("-")
        self.assertEqual(len(parts), 3)
        self.assertEqual(parts[0], settings.SCHOOL_REGISTRATION_PREFIX)
        self.assertEqual(len(parts[2]), 6)
