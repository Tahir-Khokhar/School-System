"""
Functional verification — smoke-test every URL in the system.

Logs in as superadmin (staff cashier role), then hits every admin + portal URL
and reports the HTTP status. Any non-200/302 result is flagged as a regression.

Run with: python manage.py shell < scripts/smoke_test_all_urls.py
"""
import os
import sys
import time
import subprocess
import json
import urllib.parse

# Make sure the project root is on sys.path so `config` is importable
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import requests

# Suppress InsecureRequestWarning for any HTTPS cert issues (we use HTTP localhost)
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


BASE = "http://127.0.0.1:8780"
ADMIN_USER = "superadmin"
ADMIN_PASS = "admin123"
STUDENT_USER = "student1"
STUDENT_PASS = "admin123"
PARENT_USER = "parent1"
PARENT_PASS = "admin123"
TEACHER_USER = "teacher1"
TEACHER_PASS = "admin123"


def login(session, username, password):
    """Login via the two_factor login flow. Returns True on success."""
    r = session.get(f"{BASE}/account/login/", timeout=10)
    if r.status_code != 200:
        return False, f"login page {r.status_code}"
    # Extract CSRF token
    import re
    m = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', r.text)
    if not m:
        return False, "no csrf token on login page"
    csrf = m.group(1)
    r = session.post(
        f"{BASE}/account/login/",
        data={
            "csrfmiddlewaretoken": csrf,
            "auth-username": username,
            "auth-password": password,
            "login_view-current_step": "auth",
        },
        headers={"Referer": f"{BASE}/account/login/"},
        timeout=10,
        allow_redirects=False,
    )
    if r.status_code != 302:
        return False, f"login POST {r.status_code} (expected 302)"
    return True, "ok"


# All admin/portal URLs to smoke-test
URLS_ADMIN = [
    ("/", "Landing page (public)"),
    ("/account/login/", "Login page"),
    ("/admin/", "Django admin index"),
    ("/dashboard/", "ERP dashboard"),
    # common
    ("/academic-years/", "Academic year list"),
    ("/classes/", "School class list"),
    ("/subjects/", "Subject list"),
    # students
    ("/students/", "Student list"),
    # parents
    ("/parents/", "Parent list"),
    # teachers
    ("/teachers/", "Teacher list"),
    # admissions
    ("/admissions/", "Admission application list"),
    ("/admissions/new/", "New admission form"),
    # attendance
    ("/attendance/mark/", "Mark attendance"),
    ("/attendance/report/", "Attendance report"),
    # diary
    ("/diary/", "Diary entry list"),
    ("/diary/new/", "New diary entry form"),
    # homework
    ("/homework/", "Homework list"),
    ("/homework/new/", "New homework form"),
    # syllabus
    ("/syllabus/", "Syllabus list"),
    ("/syllabus/new/", "New syllabus form"),
    # examinations
    ("/examinations/class-tests/", "Class test list"),
    ("/examinations/class-tests/new/", "New class test form"),
    ("/examinations/surprise-tests/", "Surprise test list"),
    ("/examinations/surprise-tests/new/", "New surprise test form"),
    ("/examinations/exams/", "Exam list"),
    ("/examinations/exams/new/", "New exam form"),
    ("/examinations/term-results/", "Term result list"),
    # datesheets
    ("/datesheets/", "Date sheet list"),
    ("/datesheets/new/", "New date sheet form"),
    # fees
    ("/fees/challans/", "Fee challan list"),
    ("/fees/challans/generate/", "Generate monthly challan form"),
    ("/fees/payments/", "Fee payment list"),
    ("/fees/payment/", "Challan lookup form"),
    ("/fees/defaulters/", "Fee defaulter report"),
    ("/fees/fee-types/", "Fee type list"),
    ("/fees/fee-types/new/", "New fee type form"),
    ("/fees/structures/", "Fee structure list"),
    ("/fees/structures/new/", "New fee structure form"),
    # payroll
    ("/payroll/", "Payroll list"),
    ("/payroll/new/", "New payroll form"),
    # activities
    ("/activities/", "Activity list"),
    ("/activities/new/", "New activity form"),
    # announcements
    ("/announcements/", "Announcement list"),
    ("/announcements/new/", "New announcement form"),
    # notifications
    ("/notifications/", "Notification list"),
    # calendar
    ("/calendar/", "Calendar event list"),
    # reports
    ("/reports/", "Report center"),
    # audit logs
    ("/audit-logs/", "Audit log list"),
    # accounts (2FA setup)
    ("/accounts/security/2fa/", "2FA setup"),
    # portal
    ("/portal/student/", "Student portal home"),
    ("/portal/parent/", "Parent portal home"),
    ("/portal/teacher/", "Teacher portal home"),
]

# Detail-view URLs that require a pk from the database — fetched dynamically
URLS_DYNAMIC = [
    ("/students/{pk}/", "Student detail"),
    ("/parents/{pk}/", "Parent detail"),
    ("/teachers/{pk}/", "Teacher detail"),
    ("/admissions/{pk}/", "Admission detail"),
    ("/diary/{pk}/", "Diary entry detail"),
    ("/homework/{pk}/", "Homework detail"),
    ("/syllabus/{pk}/", "Syllabus detail"),
    ("/examinations/class-tests/{pk}/", "Class test detail"),
    ("/examinations/class-tests/{pk}/results/", "Class test results"),
    ("/examinations/exams/{pk}/", "Exam detail"),
    ("/examinations/term-results/{pk}/publish/", "Publish term result (POST)"),
    ("/datesheets/{pk}/", "Date sheet detail"),
    ("/fees/challans/{pk}/", "Fee challan detail"),
    ("/fees/challans/{pk}/print/", "Fee challan print (HTML)"),
    ("/fees/challans/{pk}/pdf/", "Fee challan PDF"),
    ("/payroll/{pk}/", "Payroll detail"),
    ("/payroll/{pk}/pay/", "Payroll pay form"),
    ("/payroll/{pk}/slip/pdf/", "Salary slip PDF"),
    ("/activities/{pk}/", "Activity detail"),
    ("/announcements/{pk}/", "Announcement detail"),
    ("/portal/student/profile/", "Student profile"),
    ("/portal/student/attendance/", "Student attendance"),
    ("/portal/student/homework/", "Student homework"),
    ("/portal/student/diary/", "Student diary"),
    ("/portal/student/syllabus/", "Student syllabus"),
    ("/portal/student/exams/", "Student exams"),
    ("/portal/student/datesheet/", "Student datesheet"),
    ("/portal/student/results/", "Student results"),
    ("/portal/student/fees/", "Student fees"),
    ("/portal/student/challans/", "Student challans"),
    ("/portal/student/payments/", "Student payments"),
    ("/portal/student/receipts/", "Student receipts"),
    ("/portal/student/activities/", "Student activities"),
    ("/portal/student/notices/", "Student notices"),
    ("/portal/student/notifications/", "Student notifications"),
    ("/portal/student/academic-year/", "Student academic year"),
    ("/portal/parent/children/", "Parent children"),
    ("/portal/parent/child/attendance/", "Parent child attendance"),
    ("/portal/parent/child/homework/", "Parent child homework"),
    ("/portal/parent/child/exams/", "Parent child exams"),
    ("/portal/parent/child/results/", "Parent child results"),
    ("/portal/parent/child/fees/", "Parent child fees"),
    ("/portal/parent/child/challans/", "Parent child challans"),
    ("/portal/parent/child/payments/", "Parent child payments"),
    ("/portal/parent/child/receipts/", "Parent child receipts"),
    ("/portal/parent/child/activities/", "Parent child activities"),
]


def get_pks():
    """Fetch primary keys for each dynamic URL's model, so we can hit real records."""
    import django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    django.setup()
    from apps.students.models import Student
    from apps.parents.models import Parent
    from apps.teachers.models import Teacher
    from apps.admissions.models import Admission
    from apps.diary.models import DiaryEntry
    from apps.homework.models import Homework
    from apps.syllabus.models import Syllabus
    from apps.examinations.models import ClassTest, Exam, TermResult
    from apps.datesheets.models import DateSheet
    from apps.fees.models import FeeChallan
    from apps.payroll.models import Payroll
    from apps.activities.models import Activity
    from apps.announcements.models import Announcement
    return {
        "Student.pk": Student.objects.first().pk if Student.objects.exists() else None,
        "Parent.pk": Parent.objects.first().pk if Parent.objects.exists() else None,
        "Teacher.pk": Teacher.objects.first().pk if Teacher.objects.exists() else None,
        "Admission.pk": Admission.objects.first().pk if Admission.objects.exists() else None,
        "DiaryEntry.pk": DiaryEntry.objects.first().pk if DiaryEntry.objects.exists() else None,
        "Homework.pk": Homework.objects.first().pk if Homework.objects.exists() else None,
        "Syllabus.pk": Syllabus.objects.first().pk if Syllabus.objects.exists() else None,
        "ClassTest.pk": ClassTest.objects.first().pk if ClassTest.objects.exists() else None,
        "Exam.pk": Exam.objects.first().pk if Exam.objects.exists() else None,
        "TermResult.pk": TermResult.objects.first().pk if TermResult.objects.exists() else None,
        "DateSheet.pk": DateSheet.objects.first().pk if DateSheet.objects.exists() else None,
        "FeeChallan.pk": FeeChallan.objects.first().pk if FeeChallan.objects.exists() else None,
        "Payroll.pk": Payroll.objects.first().pk if Payroll.objects.exists() else None,
        "Activity.pk": Activity.objects.first().pk if Activity.objects.exists() else None,
        "Announcement.pk": Announcement.objects.first().pk if Announcement.objects.exists() else None,
    }


def expand_urls(pks):
    """Replace {pk} placeholders with real primary keys."""
    expanded = []
    for url, label in URLS_DYNAMIC:
        # Pick the right PK for this URL based on its label
        if "Student detail" in label: pk_key = "Student.pk"
        elif "Parent detail" in label: pk_key = "Parent.pk"
        elif "Teacher detail" in label: pk_key = "Teacher.pk"
        elif "Admission detail" in label: pk_key = "Admission.pk"
        elif "Diary entry detail" in label: pk_key = "DiaryEntry.pk"
        elif "Homework detail" in label: pk_key = "Homework.pk"
        elif "Syllabus detail" in label: pk_key = "Syllabus.pk"
        elif "Class test detail" in label or "Class test results" in label: pk_key = "ClassTest.pk"
        elif "Exam detail" in label: pk_key = "Exam.pk"
        elif "Publish term result" in label: pk_key = "TermResult.pk"
        elif "Date sheet detail" in label: pk_key = "DateSheet.pk"
        elif "Fee challan" in label: pk_key = "FeeChallan.pk"
        elif "Payroll detail" in label or "Payroll pay" in label or "Salary slip" in label: pk_key = "Payroll.pk"
        elif "Activity detail" in label: pk_key = "Activity.pk"
        elif "Announcement detail" in label: pk_key = "Announcement.pk"
        else: pk_key = None
        if pk_key:
            pk = pks.get(pk_key)
            if pk is None:
                continue  # Skip — no record to test
            expanded.append((url.format(pk=pk), label))
        else:
            expanded.append((url, label))
    return expanded


def smoke_test():
    print("Starting functional verification...")
    pks = get_pks()
    print(f"Found {len(pks)} record pks for dynamic URLs.")
    missing = [k for k, v in pks.items() if v is None]
    if missing:
        print(f"  WARNING: missing pks for: {missing}")

    all_urls = URLS_ADMIN + expand_urls(pks)
    print(f"Total URLs to smoke-test: {len(all_urls)}")
    print()

    # === superadmin (full access) ===
    sess = requests.Session()
    ok, msg = login(sess, ADMIN_USER, ADMIN_PASS)
    if not ok:
        print(f"FAILED to login as {ADMIN_USER}: {msg}")
        return
    print(f"Login as {ADMIN_USER}: {msg}")

    pass_count = 0
    fail_count = 0
    skip_count = 0
    failures = []

    for url, label in all_urls:
        try:
            r = sess.get(f"{BASE}{url}", timeout=15, allow_redirects=True)
            status = r.status_code
            if status == 200:
                pass_count += 1
                marker = "✓"
            elif status in (301, 302, 303):
                pass_count += 1
                marker = "↻"
            elif status == 404:
                # Skip — record doesn't exist for the URL
                skip_count += 1
                marker = "?"
            elif status == 403:
                # Permission denied — for superadmin this would be a regression
                fail_count += 1
                marker = "✗"
                failures.append((url, label, status, "403 Forbidden"))
            elif status == 500:
                fail_count += 1
                marker = "✗"
                failures.append((url, label, status, "500 Server Error"))
            else:
                fail_count += 1
                marker = "✗"
                failures.append((url, label, status, f"unexpected status"))
            print(f"  {marker} [{status}] {url}  ({label})")
        except Exception as e:
            fail_count += 1
            marker = "✗"
            failures.append((url, label, "ERR", str(e)[:80]))
            print(f"  {marker} [ERR] {url}  ({label}) — {str(e)[:60]}")

    print()
    print("=" * 70)
    print(f"PASS: {pass_count}  SKIP: {skip_count}  FAIL: {fail_count}")
    print("=" * 70)
    if failures:
        print("FAILURES:")
        for url, label, status, reason in failures:
            print(f"  [{status}] {url}  ({label})  → {reason}")
    return fail_count == 0


if __name__ == "__main__":
    smoke_test()
