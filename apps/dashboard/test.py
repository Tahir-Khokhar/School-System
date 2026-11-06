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


class MobileSidebarToggleTests(TestCase):
    """Guards against the phone-sidebar regression: the ☰ button toggled
    `.main-wrapper.sidebar-open`, but in base.html the `.sidebar` is a
    SIBLING of `.main-wrapper`, so the `.main-wrapper.sidebar-open .sidebar`
    descendant selector never matched and the drawer stayed hidden on phones.

    These tests lock in the fix: the toggle is on <body>, the CSS rule keys
    off body.sidebar-open, and the toggle/close buttons are present.
    """
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_superuser(
            username="adm", password="Adm1234!", email="adm@example.com"
        )

    def setUp(self):
        self.client.force_login(self.user)
        self.url = reverse("dashboard:home")

    def test_toggle_and_close_buttons_present(self):
        """Both #sidebarToggle and #sidebarCloseBtn must be in the page,
        otherwise the mobile drawer has no open/close control."""
        html = self.client.get(self.url).content.decode()
        self.assertIn("sidebarToggle", html)
        self.assertIn("sidebarCloseBtn", html)

    def test_app_js_toggles_body_not_main_wrapper(self):
        """app.js must toggle body.sidebar-open. Toggling a class on
        .main-wrapper is the regression — its descendant selector can
        never reach the sibling .sidebar."""
        import os
        from django.conf import settings
        app_js = open(
            os.path.join(settings.BASE_DIR, "static", "js", "app.js")
        ).read()
        self.assertIn("document.body.classList.toggle", app_js)
        # The old broken selector must not be present.
        self.assertNotIn("mainWrapper.classList.toggle", app_js)
        self.assertNotIn('main-wrapper").classList', app_js)

    def test_style_css_has_body_sidebar_open_rule(self):
        """style.css must define body.sidebar-open .sidebar — a class on
        .main-wrapper would not reach the sibling sidebar."""
        import os
        from django.conf import settings
        css = open(
            os.path.join(settings.BASE_DIR, "static", "css", "style.css")
        ).read()
        self.assertIn("body.sidebar-open .sidebar", css)
        # The old broken rule must be gone.
        self.assertNotIn(".main-wrapper.sidebar-open .sidebar", css)

    def test_sidebar_is_sibling_of_main_wrapper(self):
        """In base.html the .sidebar must come BEFORE .main-wrapper and
        must NOT be nested inside it — otherwise the descendant selector
        approach silently breaks (the original bug)."""
        html = self.client.get(self.url).content.decode()
        sidebar_pos = html.find('class="sidebar')
        wrapper_pos = html.find('class="main-wrapper"')
        self.assertGreater(sidebar_pos, 0, "sidebar element not found")
        self.assertGreater(wrapper_pos, 0, "main-wrapper element not found")
        self.assertLess(
            sidebar_pos, wrapper_pos,
            ".sidebar must appear before .main-wrapper (sibling), not inside it",
        )

