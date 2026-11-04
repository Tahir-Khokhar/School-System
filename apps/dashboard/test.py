"""Routing tests for the role-aware dashboard.

Covers the three regressions flagged in the last code review:
  * anonymous visit → redirect to login (was 500 AttributeError).
  * superuser created via createsuperuser → 200 (was 302 to student portal,
    because role defaulted to STUDENT and was checked before is_superuser).
  * each portal role → its own portal home (student / parent / teacher).
  * chart data passed to the template is a JSON array, not a double-encoded
    string ("[]") — guards against the json.dumps + json_script bug.
"""
from django.test import TestCase, RequestFactory
from django.urls import reverse

from apps.accounts.models import User


class DashboardRoutingTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.url = reverse("dashboard:home")

    # ---- anonymous ----
    def test_anonymous_redirected_to_login(self):
        """Anonymous user → 302 to the login page, NOT a 500."""
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/account/login", resp.url)

    # ---- superuser ----
    def test_createsuperuser_lands_on_dashboard(self):
        """A user created via the manager's create_superuser (mirrors
        `manage.py createsuperuser`) must get 200 on /dashboard/ — even
        though the role field default is STUDENT.
        """
        user = User.objects.create_superuser(
            username="root", password="Root1234!", email="root@example.com"
        )
        self.assertEqual(user.role, User.Role.SUPER_ADMIN)
        self.client.force_login(user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    # ---- portal roles ----
    def _make_user(self, role):
        return User.objects.create_user(
            username=role, password="Pass1234!", role=role
        )

    def test_student_redirected_to_student_portal(self):
        self.client.force_login(self._make_user(User.Role.STUDENT))
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse("portal:student_home"))

    def test_parent_redirected_to_parent_portal(self):
        self.client.force_login(self._make_user(User.Role.PARENT))
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse("portal:parent_home"))

    def test_teacher_redirected_to_teacher_portal(self):
        self.client.force_login(self._make_user(User.Role.TEACHER))
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse("portal:teacher_home"))


class DashboardChartContextTests(TestCase):
    """The chart data passed to the template must be a Python list,
    not a JSON-encoded string — otherwise json_script double-encodes it
    and JSON.parse returns a string, breaking the chart.
    """

    def setUp(self):
        self.user = User.objects.create_superuser(
            username="fin", password="Fin1234!", email="fin@example.com"
        )
        self.client.force_login(self.user)
        self.url = reverse("dashboard:home")

    def test_collection_labels_is_a_list(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        labels = resp.context["collection_labels"]
        values = resp.context["collection_values"]
        enrollment = resp.context["enrollment_data"]
        self.assertIsInstance(labels, list)
        self.assertIsInstance(values, list)
        self.assertIsInstance(enrollment, list)
        # No json.dumps artifacts: each item is a plain str / int / dict,
        # never a serialized string.
        for item in labels:
            self.assertIsInstance(item, str)
        for item in enrollment:
            self.assertIsInstance(item, dict)
            self.assertIn("name", item)
            self.assertIn("count", item)
