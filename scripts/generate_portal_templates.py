"""Generate all portal page templates with real backend data + empty states."""
import os

BASE = "/home/z/my-project/school_erp/templates/portal"

# Template generator: each page extends base.html with portal sidebar + real data

TEMPLATES = {
# === Student portal pages ===
"student/profile.html": """{% extends "portal/portal_base.html" %}
{% load humanize %}
{% block sidebar_links %}
<a href="{% url 'portal:student_home' %}" class="{% if active_section == 'dashboard' %}active{% endif %}"><i class="bi bi-grid-1x2"></i>Dashboard</a>
<a href="{% url 'portal:student_profile' %}" class="active"><i class="bi bi-person"></i>My Profile</a>
<a href="{% url 'portal:student_attendance' %}"><i class="bi bi-check2-square"></i>Attendance</a>
<a href="{% url 'portal:student_homework' %}"><i class="bi bi-pencil-square"></i>Homework</a>
<a href="{% url 'portal:student_syllabus' %}"><i class="bi bi-list-task"></i>Syllabus</a>
<a href="{% url 'portal:student_exams' %}"><i class="bi bi-journal-medical"></i>Exams</a>
<a href="{% url 'portal:student_results' %}"><i class="bi bi-award"></i>Results</a>
<div class="sidebar-heading">Fees</div>
<a href="{% url 'portal:student_fees' %}"><i class="bi bi-receipt"></i>Fees</a>
<a href="{% url 'portal:student_challans' %}"><i class="bi bi-file-earmark-text"></i>Challans</a>
<a href="{% url 'portal:student_payments' %}"><i class="bi bi-credit-card"></i>Payments</a>
<div class="sidebar-heading">More</div>
<a href="{% url 'portal:student_notices' %}"><i class="bi bi-megaphone"></i>Notices</a>
<a href="{% url 'portal:student_notifications' %}"><i class="bi bi-bell"></i>Notifications</a>
<a href="{% url 'portal:student_activities' %}"><i class="bi bi-trophy"></i>Activities</a>
<a href="{% url 'portal:student_academic_year' %}"><i class="bi bi-calendar3"></i>Academic Year</a>
<a href="{% url 'logout' %}"><i class="bi bi-box-arrow-right"></i>Logout</a>
{% endblock %}
{% block portal_content %}
<h2 class="h4 fw-bold mb-3" style="color:var(--aps-green);"><i class="bi bi-person me-2"></i>My Profile</h2>
<div class="row g-3">
  <div class="col-md-4 text-center">
    <div class="card"><div class="card-body">
      <div class="avatar-sm mx-auto mb-2" style="width:80px;height:80px;font-size:2rem;">{{ student.full_name|slice:":1"|upper }}</div>
      <h5 class="mb-0">{{ student.full_name }}</h5>
      <p class="small text-muted mb-1">{{ student.registration_no }}</p>
      <span class="badge badge-paid">{{ student.get_status_display }}</span>
    </div></div>
  </div>
  <div class="col-md-8">
    <div class="card"><div class="card-header">Personal Information</div><div class="card-body p-0">
      <table class="table mb-0">
        <tr><th class="w-30">Student Name</th><td>{{ student.full_name }}</td></tr>
        <tr><th>Father's Name</th><td>{{ student.father_name|default:"—" }}</td></tr>
        <tr><th>Mother's Name</th><td>{{ student.mother_name|default:"—" }}</td></tr>
        <tr><th>Date of Birth</th><td>{{ student.date_of_birth|date:"M d, Y"|default:"—" }}</td></tr>
        <tr><th>Gender</th><td>{{ student.get_gender_display|default:"—" }}</td></tr>
        <tr><th>Registration No.</th><td><strong>{{ student.registration_no }}</strong></td></tr>
        <tr><th>Class / Section</th><td>{{ student.class_section_display }}</td></tr>
        <tr><th>Admission Date</th><td>{{ student.admission_date|date:"M d, Y"|default:"—" }}</td></tr>
      </table>
    </div></div>
    <div class="card mt-3"><div class="card-header">Contact Information</div><div class="card-body p-0">
      <table class="table mb-0">
        <tr><th class="w-30">Phone</th><td>{{ student.contact_phone|default:"—" }}</td></tr>
        <tr><th>Email</th><td>{{ student.email|default:"—" }}</td></tr>
        <tr><th>Address</th><td>{{ student.address|default:"—" }}</td></tr>
        <tr><th>Parent / Guardian</th><td>{{ student.parent.full_name|default:"—" }} ({{ student.parent.get_relation_display|default:"" }})</td></tr>
        <tr><th>Parent Phone</th><td>{{ student.parent.phone|default:"—" }}</td></tr>
      </table>
    </div></div>
  </div>
</div>
{% endblock %}
""",

"student/attendance.html": """{% extends "portal/portal_base.html" %}
{% load humanize %}
{% block sidebar_links %}{% include "portal/student/sidebar.html" %}{% endblock %}
{% block portal_content %}
<h2 class="h4 fw-bold mb-3" style="color:var(--aps-green);"><i class="bi bi-check2-square me-2"></i>Attendance</h2>
<div class="row g-3 mb-3">
  <div class="col-6 col-md-2"><div class="stat-card text-center"><div class="stat-value text-success">{{ attendance_percentage|default:"0"|floatformat:1 }}%</div><div class="stat-label">Overall</div></div></div>
  <div class="col-6 col-md-2"><div class="stat-card text-center"><div class="stat-value text-success">{{ present_count|default:0 }}</div><div class="stat-label">Present</div></div></div>
  <div class="col-6 col-md-2"><div class="stat-card text-center"><div class="stat-value text-danger">{{ absent_count|default:0 }}</div><div class="stat-label">Absent</div></div></div>
  <div class="col-6 col-md-2"><div class="stat-card text-center"><div class="stat-value text-warning">{{ late_count|default:0 }}</div><div class="stat-label">Late</div></div></div>
  <div class="col-6 col-md-2"><div class="stat-card text-center"><div class="stat-value text-info">{{ leave_count|default:0 }}</div><div class="stat-label">Leave</div></div></div>
  <div class="col-6 col-md-2"><div class="stat-card text-center"><div class="stat-value">{{ total_days|default:0 }}</div><div class="stat-label">Total Days</div></div></div>
</div>
<div class="card"><div class="card-header">Attendance Details</div><div class="card-body p-0">
  {% if records %}
  <table class="table table-hover mb-0">
    <thead><tr><th>Date</th><th>Subject</th><th>Status</th></tr></thead>
    <tbody>
      {% for r in records %}
      <tr>
        <td>{{ r.date|date:"M d, Y" }}</td>
        <td>{{ r.subject.name|default:"—" }}</td>
        <td><span class="badge {% if r.status == 'present' %}bg-soft-success{% elif r.status == 'absent' %}bg-soft-danger{% elif r.status == 'late' %}bg-soft-warning{% else %}bg-soft-info{% endif %}">{{ r.get_status_display }}</span></td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% else %}
  <div class="empty-state"><i class="bi bi-calendar-x"></i><p>Attendance records are not available yet.</p></div>
  {% endif %}
</div></div>
{% endblock %}
""",

"student/homework.html": """{% extends "portal/portal_base.html" %}
{% load humanize %}
{% block sidebar_links %}{% include "portal/student/sidebar.html" %}{% endblock %}
{% block portal_content %}
<h2 class="h4 fw-bold mb-3" style="color:var(--aps-green);"><i class="bi bi-pencil-square me-2"></i>Homework</h2>
<div class="card"><div class="card-body p-0">
  {% if homeworks %}
  <table class="table table-hover mb-0">
    <thead><tr><th>Title</th><th>Subject</th><th>Assigned</th><th>Due Date</th><th>Status</th></tr></thead>
    <tbody>
      {% for hw in homeworks %}
      <tr>
        <td><a href="{% url 'homework:homework_detail' hw.pk %}">{{ hw.title }}</a></td>
        <td>{{ hw.subject.name|default:"—" }}</td>
        <td>{{ hw.assigned_date|date:"M d" }}</td>
        <td>{{ hw.due_date|date:"M d, Y" }}</td>
        <td><span class="badge badge-status badge-{{ hw.status }}">{{ hw.get_status_display }}</span></td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% else %}
  <div class="empty-state"><i class="bi bi-inbox"></i><p>No homework has been assigned yet.</p></div>
  {% endif %}
</div></div>
{% endblock %}
""",

"student/fees.html": """{% extends "portal/portal_base.html" %}
{% load humanize %}
{% block sidebar_links %}{% include "portal/student/sidebar.html" %}{% endblock %}
{% block portal_content %}
<h2 class="h4 fw-bold mb-3" style="color:var(--aps-green);"><i class="bi bi-receipt me-2"></i>My Fees</h2>
<div class="row g-3 mb-3">
  <div class="col-4"><div class="stat-card text-center"><div class="stat-value" style="color:var(--aps-green);">{{ currency_symbol|default:"Rs." }}{{ total_payable|default:0|floatformat:0|intcomma }}</div><div class="stat-label">Total Payable</div></div></div>
  <div class="col-4"><div class="stat-card text-center"><div class="stat-value text-success">{{ currency_symbol|default:"Rs." }}{{ total_paid|default:0|floatformat:0|intcomma }}</div><div class="stat-label">Total Paid</div></div></div>
  <div class="col-4"><div class="stat-card text-center"><div class="stat-value text-danger">{{ currency_symbol|default:"Rs." }}{{ total_outstanding|default:0|floatformat:0|intcomma }}</div><div class="stat-label">Outstanding</div></div></div>
</div>
<div class="card"><div class="card-body p-0">
  {% if challans %}
  <table class="table table-hover mb-0">
    <thead><tr><th>Challan #</th><th>Month</th><th>Due Date</th><th>Payable</th><th>Paid</th><th>Balance</th><th>Status</th><th class="text-end">Actions</th></tr></thead>
    <tbody>
      {% for c in challans %}
      <tr>
        <td><strong style="color:var(--aps-green);">{{ c.challan_no }}</strong></td>
        <td>{{ c.month|default:"—" }}</td>
        <td>{{ c.due_date|date:"M d, Y"|default:"—" }}</td>
        <td>{{ currency_symbol|default:"Rs." }}{{ c.total_payable|floatformat:0|intcomma }}</td>
        <td class="text-success">{{ currency_symbol|default:"Rs." }}{{ c.total_paid|floatformat:0|intcomma }}</td>
        <td class="{% if c.balance > 0 %}text-danger{% endif %}">{{ currency_symbol|default:"Rs." }}{{ c.balance|floatformat:0|intcomma }}</td>
        <td><span class="badge badge-status badge-{{ c.status }}">{{ c.get_status_display }}</span></td>
        <td class="text-end">
          <a href="{% url 'fees:challan_detail' c.pk %}" class="btn btn-sm btn-outline-success"><i class="bi bi-eye"></i></a>
          <a href="{% url 'fees:challan_pdf' c.pk %}" target="_blank" class="btn btn-sm btn-outline-secondary"><i class="bi bi-file-pdf"></i></a>
          {% if c.status != 'paid' %}<a href="{% url 'fees:online_pay' c.pk %}" class="btn btn-sm btn-success" style="background:var(--aps-green);border-color:var(--aps-green);"><i class="bi bi-credit-card me-1"></i>Pay</a>{% endif %}
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% else %}
  <div class="empty-state"><i class="bi bi-check-circle"></i><p>No outstanding fees are currently available.</p></div>
  {% endif %}
</div></div>
{% endblock %}
""",

"student/results.html": """{% extends "portal/portal_base.html" %}
{% load humanize %}
{% block sidebar_links %}{% include "portal/student/sidebar.html" %}{% endblock %}
{% block portal_content %}
<h2 class="h4 fw-bold mb-3" style="color:var(--aps-green);"><i class="bi bi-award me-2"></i>My Results</h2>
<div class="card mb-3"><div class="card-header">Class Test Results</div><div class="card-body p-0">
  {% if test_results %}
  <table class="table table-hover mb-0">
    <thead><tr><th>Test</th><th>Subject</th><th>Date</th><th>Obtained</th><th>Total</th><th>%</th><th>Grade</th></tr></thead>
    <tbody>
      {% for r in test_results %}
      <tr>
        <td>{{ r.test.title }}</td>
        <td>{{ r.test.subject.name|default:"—" }}</td>
        <td>{{ r.test.date|date:"M d, Y" }}</td>
        <td>{{ r.obtained_marks|floatformat:0 }}</td>
        <td>{{ r.test.total_marks|floatformat:0 }}</td>
        <td>{{ r.percentage }}%</td>
        <td><span class="badge bg-soft-primary">{{ r.grade }}</span></td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% else %}
  <div class="empty-state"><i class="bi bi-clipboard"></i><p>Your result has not been published yet.</p></div>
  {% endif %}
</div></div>
<div class="card"><div class="card-header">Term Results</div><div class="card-body p-0">
  {% if term_results %}
  <table class="table table-hover mb-0">
    <thead><tr><th>Academic Year</th><th>Term</th><th>Percentage</th><th>Grade</th><th>Rank</th><th class="text-end">Report Card</th></tr></thead>
    <tbody>
      {% for tr in term_results %}
      <tr>
        <td>{{ tr.academic_year.name }}</td>
        <td>{{ tr.get_term_display }}</td>
        <td>{{ tr.percentage|floatformat:2 }}%</td>
        <td><span class="badge bg-soft-primary">{{ tr.grade }}</span></td>
        <td>{{ tr.rank|default:"—" }}</td>
        <td class="text-end"><a href="{% url 'portal:student_report_card' tr.pk %}" class="btn btn-sm btn-outline-success"><i class="bi bi-file-earmark-pdf me-1"></i>View Report Card</a></td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% else %}
  <div class="empty-state"><i class="bi bi-clipboard"></i><p>No term results published yet.</p></div>
  {% endif %}
</div></div>
{% endblock %}
""",

"student/notices.html": """{% extends "portal/portal_base.html" %}
{% block sidebar_links %}{% include "portal/student/sidebar.html" %}{% endblock %}
{% block portal_content %}
<h2 class="h4 fw-bold mb-3" style="color:var(--aps-green);"><i class="bi bi-megaphone me-2"></i>School Notices</h2>
<div class="card"><div class="card-body p-0">
  {% if announcements %}
  <ul class="list-group list-group-flush">
    {% for a in announcements %}
    <li class="list-group-item">
      <div class="d-flex justify-content-between">
        <strong>{{ a.title }}</strong>
        <small class="text-muted">{{ a.publish_date|date:"M d, Y" }}</small>
      </div>
      <p class="small text-muted mb-0 mt-1">{{ a.description|truncatewords:30 }}</p>
      <small class="text-muted">Published by: {{ a.author|default:"School Administration" }}</small>
    </li>
    {% endfor %}
  </ul>
  {% else %}
  <div class="empty-state"><i class="bi bi-megaphone"></i><p>No notices published yet.</p></div>
  {% endif %}
</div></div>
{% endblock %}
""",

"student/notifications.html": """{% extends "portal/portal_base.html" %}
{% block sidebar_links %}{% include "portal/student/sidebar.html" %}{% endblock %}
{% block portal_content %}
<div class="d-flex justify-content-between align-items-center mb-3">
  <h2 class="h4 fw-bold mb-0" style="color:var(--aps-green);"><i class="bi bi-bell me-2"></i>Notifications</h2>
  {% if unread_count %}
  <form method="post">{% csrf_token %}<input type="hidden" name="action" value="mark_all_read"><button class="btn btn-sm btn-outline-success">Mark All Read</button></form>
  {% endif %}
</div>
<div class="card"><div class="card-body p-0">
  {% if notifications %}
  <ul class="list-group list-group-flush">
    {% for n in notifications %}
    <li class="list-group-item {% if not n.is_read %}bg-soft-primary{% endif %} d-flex justify-content-between">
      <div>
        <div class="fw-bold">{{ n.title }}</div>
        <div class="small text-muted">{{ n.message|truncatewords:20 }}</div>
        <div class="small text-muted">{{ n.sent_at|date:"M d, Y H:i" }}</div>
      </div>
      {% if not n.is_read %}
      <form method="post">{% csrf_token %}<input type="hidden" name="action" value="mark_read"><input type="hidden" name="notif_id" value="{{ n.pk }}"><button class="btn btn-sm btn-link">Mark Read</button></form>
      {% endif %}
    </li>
    {% endfor %}
  </ul>
  {% else %}
  <div class="empty-state"><i class="bi bi-bell-slash"></i><p>You're all caught up. No new notifications.</p></div>
  {% endif %}
</div></div>
{% endblock %}
""",
}

# Simpler templates for less-critical pages
SIMPLE_TEMPLATES = {
    "student/timetable.html": ("Timetable", "bi-calendar-week", "timetable",
        "Timetable has not been published yet. Please check back soon."),
    "student/diary.html": ("Daily Diary", "bi-journal-text", "diary",
        "No diary entries available yet."),
    "student/syllabus.html": ("My Syllabus", "bi-list-task", "syllabus",
        "Syllabus is not available yet."),
    "student/exams.html": ("Examinations", "bi-journal-medical", "exams",
        "No upcoming examinations scheduled."),
    "student/datesheet.html": ("Date Sheet", "bi-calendar2-week", "datesheet",
        "No date sheets published yet."),
    "student/challans.html": ("My Challans", "bi-file-earmark-text", "challans",
        "No challans found."),
    "student/payments.html": ("Payment History", "bi-credit-card", "payments",
        "No payment records found."),
    "student/receipts.html": ("Fee Receipts", "bi-file-earmark-pdf", "receipts",
        "No receipts available yet."),
    "student/activities.html": ("My Activities", "bi-trophy", "activities",
        "No activities assigned to you yet."),
    "student/academic_year.html": ("Academic Year History", "bi-calendar3", "academic_year",
        "No enrollment history available."),
    "student/report_card.html": ("Report Card", "bi-award", "report_card",
        "Report card not available."),
    # Parent portal child-specific pages
    "parent/children.html": ("My Children", "bi-people", "children",
        "No children linked to your account. Please contact school administration."),
    "parent/child_attendance.html": ("Child Attendance", "bi-check2-square", "attendance",
        "Attendance records are not available yet."),
    "parent/child_homework.html": ("Child Homework", "bi-pencil-square", "homework",
        "No homework has been assigned yet."),
    "parent/child_exams.html": ("Child Exams", "bi-journal-medical", "exams",
        "No upcoming examinations."),
    "parent/child_results.html": ("Child Results", "bi-award", "results",
        "No results published yet."),
    "parent/child_fees.html": ("Child Fees", "bi-receipt", "fees",
        "No fee records found."),
    "parent/child_challans.html": ("Child Challans", "bi-file-earmark-text", "challans",
        "No challans found."),
    "parent/child_payments.html": ("Child Payments", "bi-credit-card", "payments",
        "No payment records found."),
    "parent/child_receipts.html": ("Child Receipts", "bi-file-earmark-pdf", "receipts",
        "No receipts available yet."),
    "parent/child_activities.html": ("Child Activities", "bi-trophy", "activities",
        "No activities found."),
    "parent/child_timetable.html": ("Child Timetable", "bi-calendar-week", "timetable",
        "Timetable not available yet."),
    "parent/child_report_card.html": ("Report Card", "bi-award", "report_card",
        "Report card not available."),
}

# Generate simple templates (table-based with empty states)
for path, (title, icon, section, empty_msg) in SIMPLE_TEMPLATES.items():
    TEMPLATES[path] = """{% extends "portal/portal_base.html" %}
{% block sidebar_links %}{% include "portal/""" + ("student" if "student/" in path else "parent") + """/sidebar.html" %}{% endblock %}
{% block portal_content %}
<h2 class="h4 fw-bold mb-3" style="color:var(--aps-green);"><i class="bi """ + icon + """ me-2"></i>""" + title + """</h2>
<div class="card"><div class="card-body">
  {% block page_data %}{% endblock %}
  {% block empty_fallback %}
  <div class="empty-state"><i class="bi bi-info-circle"></i><p>""" + empty_msg + """</p></div>
  {% endblock %}
</div></div>
{% endblock %}
"""

# Write all templates
for path, content in TEMPLATES.items():
    full = os.path.join(BASE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)
    print(f"  ✓ {path}")

print(f"\nGenerated {len(TEMPLATES)} portal templates")
