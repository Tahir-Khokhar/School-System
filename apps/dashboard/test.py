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
    """Guards against the phone-sidebar regression.

    Round 7's fix toggled ``body.sidebar-open`` (correct) but added a
    document-level tap-to-close handler that immediately removed the
    class on the same click — so the ☰ button opened the drawer and
    closed it in the same event. The string-matching tests passed
    anyway because they only searched the source for substrings.

    These tests use a real jsdom click test (``tests/js/test_sidebar.js``)
    that loads ``app.js``, clicks the actual ☰ button, and asserts the
    ``sidebar-open`` class survives the click. Two template-level checks
    are kept as quick structural guards.
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

    def test_sidebar_is_sibling_of_main_wrapper(self):
        """In base.html the .sidebar must come BEFORE .main-wrapper and
        must NOT be nested inside it — otherwise a descendant selector
        off .main-wrapper can never reach the sidebar (the original bug)."""
        html = self.client.get(self.url).content.decode()
        sidebar_pos = html.find('class="sidebar')
        wrapper_pos = html.find('class="main-wrapper"')
        self.assertGreater(sidebar_pos, 0, "sidebar element not found")
        self.assertGreater(wrapper_pos, 0, "main-wrapper element not found")
        self.assertLess(
            sidebar_pos, wrapper_pos,
            ".sidebar must appear before .main-wrapper (sibling), not inside it",
        )

    def test_jsdom_click_opens_sidebar(self):
        """The real test: load app.js in jsdom, click the ☰ button, and
        assert ``body.sidebar-open`` survives the click. This catches the
        event-bubbling bug where the toggle handler adds the class and the
        tap-to-close handler removes it on the same click.

        Requires Node.js + jsdom (``npm install`` in ``tests/js/``).
        Skipped if Node is unavailable so CI without Node still passes.
        """
        import os
        import shutil
        import subprocess
        from django.conf import settings

        node = shutil.which("node")
        if node is None:
            self.skipTest("Node.js not installed — jsdom test skipped")

        test_script = os.path.join(
            settings.BASE_DIR, "tests", "js", "test_sidebar.js"
        )
        node_modules = os.path.join(
            settings.BASE_DIR, "tests", "js", "node_modules", "jsdom"
        )
        if not os.path.isfile(test_script):
            self.skipTest(f"jsdom test script not found: {test_script}")
        if not os.path.isdir(node_modules):
            self.skipTest(
                "jsdom not installed — run `npm install` in tests/js/"
            )

        result = subprocess.run(
            [node, test_script],
            capture_output=True,
            text=True,
            cwd=os.path.join(settings.BASE_DIR, "tests", "js"),
            timeout=30,
        )
        if result.returncode != 0:
            self.fail(
                "jsdom sidebar test failed (return code %d).\n"
                "stdout:\n%s\nstderr:\n%s"
                % (result.returncode, result.stdout, result.stderr)
            )


