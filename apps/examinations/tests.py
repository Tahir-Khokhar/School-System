"""Tests for ResultService — grade calculation."""
from decimal import Decimal
from django.test import TestCase
from apps.examinations.services import ResultService


class ResultServiceTest(TestCase):
    def test_grade_a_plus(self):
        self.assertEqual(ResultService.grade_for_percentage(95), "A+")

    def test_grade_a(self):
        self.assertEqual(ResultService.grade_for_percentage(85), "A")

    def test_grade_f(self):
        self.assertEqual(ResultService.grade_for_percentage(30), "F")

    def test_grade_for_invalid_input(self):
        self.assertEqual(ResultService.grade_for_percentage(None), "—")
        self.assertEqual(ResultService.grade_for_percentage("invalid"), "—")

    def test_boundaries(self):
        self.assertEqual(ResultService.grade_for_percentage(90), "A+")
        self.assertEqual(ResultService.grade_for_percentage(89.9), "A")
        self.assertEqual(ResultService.grade_for_percentage(80), "A")
        self.assertEqual(ResultService.grade_for_percentage(79.9), "B")
