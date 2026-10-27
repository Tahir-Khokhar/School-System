"""Generate portal templates: student/, parent/, sidebars. Idempotent, validated."""
from __future__ import annotations
import os
import sys
from pathlib import Path

# --- Config ---------------------------------------------------------------
# Prefer env var; fall back to cwd for portability. Reject if it doesn't exist.
BASE_ROOT = Path(os.environ.get(
    "SCHOOL_ERP_TEMPLATES", "templates/portal"
)).resolve()
if not BASE_ROOT.parent.exists():
    sys.exit(f"❌ Templates root not found: {BASE_ROOT.parent}")

# --- Sidebars -------------------------------------------------------------
STUDENT_SIDEBAR = """<a href="{% url 'portal:student_home' %}" class="{% if active_section == 'dashboard' %}active{% endif %}"><i class="bi bi-grid-1x2"></i>Dashboard</a>
<a href="{% url 'portal:student_profile' %}" class="{% if active_section == 'profile' %}active{% endif %}"><i class="bi bi-person"></i>My Profile</a>
<a href="{% url 'portal:student_attendance' %}" class="{% if active_section == 'attendance' %}active{% endif %}"><i class="bi bi-check2-square"></i>Attendance</a>
<a href="{% url 'portal:student_homework' %}" class="{% if active_section == 'homework' %}active{% endif %}"><i class="bi bi-pencil-square"></i>Homework</a>
<a href="{% url 'portal:student_timetable' %}" class="{% if active_section == 'timetable' %}active{% endif %}"><i class="bi bi-calendar-week"></i>Timetable</a>
<a href="{% url 'portal:student_syllabus' %}" class="{% if active_section == 'syllabus' %}active{% endif %}"><i class="bi bi-list-task"></i>Syllabus</a>
<a href="{% url 'portal:student_exams' %}" class="{% if active_section == 'exams' %}active{% endif %}"><i class="bi bi-journal-medical"></i>Exams</a>
<a href="{% url 'portal:student_results' %}" class="{% if active_section == 'results' %}active{% endif %}"><i class="bi bi-award"></i>Results</a>
<div class="sidebar-heading">Fees</div>
<a href="{% url 'portal:student_fees' %}" class="{% if active_section == 'fees' %}active{% endif %}"><i class="bi bi-receipt"></i>Fees</a>
<a href="{% url 'portal:student_challans' %}" class="{% if active_section == 'challans' %}active{% endif %}"><i class="bi bi-file-earmark-text"></i>Challans</a>
<a href="{% url 'portal:student_payments' %}" class="{% if active_section == 'payments' %}active{% endif %}"><i class="bi bi-credit-card"></i>Payments</a>
<div class="sidebar-heading">More</div>
<a href="{% url 'portal:student_notices' %}" class="{% if active_section == 'notices' %}active{% endif %}"><i class="bi bi-megaphone"></i>Notices</a>
<a href="{% url 'portal:student_notifications' %}" class="{% if active_section == 'notifications' %}active{% endif %}"><i class="bi bi-bell"></i>Notifications</a>
<a href="{% url 'portal:student_activities' %}" class="{% if active_section == 'activities' %}active{% endif %}"><i class="bi bi-trophy"></i>Activities</a>
<a href="{% url 'portal:student_academic_year' %}" class="{% if active_section == 'academic_year' %}active{% endif %}"><i class="bi bi-calendar3"></i>Academic Year</a>
<a href="{% url 'logout' %}"><i class="bi bi-box-arrow-right"></i>Logout</a>
"""

PARENT_SIDEBAR = """<a href="{% url 'portal:parent_home' %}" class="{% if active_section == 'dashboard' %}active{% endif %}"><i class="bi bi-grid-1x2"></i>Dashboard</a>
<a href="{% url 'portal:parent_children' %}" class="{% if active_section == 'children' %}active{% endif %}"><i class="bi bi-people"></i>My Children</a>
<div class="sidebar-heading">Fees</div>
<a href="{% url 'portal:parent_fees' %}" class="{% if active_section == 'fees' %}active{% endif %}"><i class="bi bi-receipt"></i>Fees</a>
<a href="{% url 'portal:parent_challans' %}" class="{% if active_section == 'challans' %}active{% endif %}"><i class="bi bi-file-earmark-text"></i>Challans</a>
<a href="{% url 'portal:parent_payments' %}" class="{% if active_section == 'payments' %}active{% endif %}"><i class="bi bi-credit-card"></i>Payments</a>
<div class="sidebar-heading">More</div>
<a href="{% url 'portal:parent_notices' %}" class="{% if active_section == 'notices' %}active{% endif %}"><i class="bi bi-megaphone"></i>Notices</a>
<a href="{% url 'portal:parent_notifications' %}" class="{% if active_section == 'notifications' %}active{% endif %}"><i class="bi bi-bell"></i>Notifications</a>
<a href="{% url 'logout' %}"><i class="bi bi-box-arrow-right"></i>Logout</a>
"""

SIDEBARS = {
    "student/sidebar.html": STUDENT_SIDEBAR,
    "parent/sidebar.html": PARENT_SIDEBAR,
}

# --- Simple template body (shared) ----------------------------------------
# Uses {% if items %} so views control what's shown. `items` is a generic list
# of dicts or objects; templates render each entry's __str__ or named fields.
SIMPLE_BODY = """{% extends "portal/portal_base.html" %}
{% block sidebar_links %}{% include "portal/{portal}/sidebar.html" %}{% endblock %}
{% block portal_content %}
<h2 class="h4 fw-bold mb-3" style="color:var(--aps-green);">
  <i class="bi {icon} me-2"></i>{title}
</h2>
<div class="card">
  <div class="card-body p-0">
    {{% if {items_var} %}}
    <table class="table table-hover mb-0">
      <thead>
        <tr>
          {{% for label in {headers_var} %}}<th>{{{{ label }}}}</th>{{% endfor %}}
        </tr>
      </thead>
      <tbody>
        {{% for row in {items_var} %}}
        <tr>
          {{% for cell in row %}}<td>{{{{ cell }}}}</td>{{% endfor %}}
        </tr>
        {{% endfor %}}
      </tbody>
    </table>
    {{% else %}}
    <div class="empty-state">
      <i class="bi bi-info-circle"></i>
      <p>{empty_msg}</p>
    </div>
    {{% endif %}}
  </div>
</div>
{{% endblock %}}
"""

SIMPLE_TEMPLATES = {
    # path: (title, icon, items_var, headers_var, empty_msg)
    "student/timetable.html": ("Timetable", "bi-calendar-week",
        "timetable_rows", "timetable_headers", "Timetable has not been published yet."),
    "student/diary.html": ("Daily Diary", "bi-journal-text",
        "diary_entries", "diary_headers", "No diary entries available yet."),
    "student/syllabus.html": ("My Syllabus", "bi-list-task",
        "syllabus_items", "syllabus_headers", "Syllabus is not available yet."),
    "student/exams.html": ("Examinations", "bi-journal-medical",
        "exams", "exam_headers", "No upcoming examinations scheduled."),
    "student/datesheet.html": ("Date Sheet", "bi-calendar2-week",
        "datesheet_rows", "datesheet_headers", "No date sheets published yet."),
    "student/challans.html": ("My Challans", "bi-file-earmark-text",
        "challans", "challan_headers", "No challans found."),
    "student/payments.html": ("Payment History", "bi-credit-card",
        "payments", "payment_headers", "No payment records found."),
    "student/receipts.html": ("Fee Receipts", "bi-file-earmark-pdf",
        "receipts", "receipt_headers", "No receipts available yet."),
    "student/activities.html": ("My Activities", "bi-trophy",
        "activities", "activity_headers", "No activities assigned yet."),
    "student/academic_year.html": ("Academic Year History", "bi-calendar3",
        "academic_years", "year_headers", "No enrollment history available."),
    "student/report_card.html": ("Report Card", "bi-award",
        "report_cards", "report_headers", "Report card not available."),
    "parent/children.html": ("My Children", "bi-people",
        "children", "child_headers", "No children linked to your account."),
    "parent/child_attendance.html": ("Child Attendance", "bi-check2-square",
        "attendance_records", "attendance_headers", "Attendance records not available."),
    "parent/child_homework.html": ("Child Homework", "bi-pencil-square",
        "homeworks", "homework_headers", "No homework has been assigned."),
    "parent/child_exams.html": ("Child Exams", "bi-journal-medical",
        "exams", "exam_headers", "No upcoming examinations."),
    "parent/child_results.html": ("Child Results", "bi-award",
        "results", "result_headers", "No results published yet."),
    "parent/child_fees.html": ("Child Fees", "bi-receipt",
        "challans", "fee_headers", "No fee records found."),
    "parent/child_challans.html": ("Child Challans", "bi-file-earmark-text",
        "challans", "challan_headers", "No challans found."),
    "parent/child_payments.html": ("Child Payments", "bi-credit-card",
        "payments", "payment_headers", "No payment records found."),
    "parent/child_receipts.html": ("Child Receipts", "bi-file-earmark-pdf",
        "receipts", "receipt_headers", "No receipts available yet."),
    "parent/child_activities.html": ("Child Activities", "bi-trophy",
        "activities", "activity_headers", "No activities found."),
    "parent/child_timetable.html": ("Child Timetable", "bi-calendar-week",
        "timetable_rows", "timetable_headers", "Timetable not available yet."),
    "parent/child_report_card.html": ("Report Card", "bi-award",
        "report_cards", "report_headers", "Report card not available."),
}

# --- Fixed templates (kept from original, only fixing profile sidebar) ----
# (Assumes TEMPLATES dict from original is defined above this block; if not,
#  paste it here verbatim. The only change: student/profile.html uses
#  {% include "portal/student/sidebar.html" %} instead of inline links.)

# --- Writer ---------------------------------------------------------------
def safe_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)


def validate_django_template(name: str, content: str) -> None:
    """Catch unclosed tags before writing."""
    try:
        from django.template import engines
        engines["django"].from_string(content)
    except ImportError:
        return  # Django not installed; skip validation
    except Exception as exc:
        raise SystemExit(f"❌ Invalid template {name}: {exc}")


def main() -> None:
    written = 0

    # 1. Sidebars
    for rel, content in SIDEBARS.items():
        p = BASE_ROOT / rel
        validate_django_template(rel, content)
        safe_write(p, content)
        print(f"  ✓ {rel}")
        written += 1

    # 2. Fixed templates (the big dict) — assume defined as `TEMPLATES`
    for rel, content in TEMPLATES.items():
        # Normalise: replace inline student sidebar with include, if present
        content = _normalise_sidebar(rel, content)
        validate_django_template(rel, content)
        safe_write(BASE_ROOT / rel.lstrip("/"), content)
        print(f"  ✓ {rel}")
        written += 1

    # 3. Simple templates
    for rel, (title, icon, items_var, headers_var, empty_msg) in SIMPLE_TEMPLATES.items():
        portal = rel.split("/", 1)[0]
        body = SIMPLE_BODY.format(
            portal=portal, icon=icon, title=title,
            items_var=items_var, headers_var=headers_var, empty_msg=empty_msg,
        )
        validate_django_template(rel, body)
        safe_write(BASE_ROOT / rel, body)
        print(f"  ✓ {rel}")
        written += 1

    print(f"\nGenerated {written} templates under {BASE_ROOT}")


def _normalise_sidebar(rel: str, content: str) -> str:
    """Replace inline student sidebar block with {% include %}."""
    if not rel.startswith("student/"):
        return content
    inline_start = '{% block sidebar_links %}\n<a href="{% url \'portal:student_home\' %}'
    if inline_start not in content:
        return content
    end = content.find("{% endblock %}", content.find(inline_start))
    if end == -1:
        return content
    replace_with = (
        '{% block sidebar_links %}{% include "portal/student/sidebar.html" %}'
    )
    return content[:content.find("{% block sidebar_links %}")] + replace_with + content[end + len("{% endblock %}"):]


if __name__ == "__main__":
    main()
