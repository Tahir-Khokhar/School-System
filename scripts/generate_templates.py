"""Generate remaining generic templates in batch."""
import os

BASE = "/home/z/my-project/school_erp/templates"

# Generic templates that just show a list of objects in a table
GENERIC_LIST_TEMPLATES = {
    "common/academic_year_list.html": (
        "Academic Years", "year", "years",
        [("name","Name"),("start_date","Start"),("end_date","End"),("is_active","Active?"),("","Actions")],
        [{"text": "year.name", "url": "common:academic_year_detail year.pk"},
         {"text": "year.start_date|date:'M d, Y'"},
         {"text": "year.end_date|date:'M d, Y'"},
         {"badge": "year.is_active", "true": "Active", "false": "Archived"},
         {"actions": ["common:academic_year_detail year.pk", "common:academic_year_activate year.pk", "Activate"]}],
    ),
    "common/class_list.html": (
        "Classes & Sections", "c", "classes",
        [("name","Class"),("grade_level","Level"),("order","Order"),("","Sections"),("","Actions")],
        [{"text": "c.name", "url": ""},
         {"text": "c.get_grade_level_display"},
         {"text": "c.order"},
         {"text": "c.sections.count"},
         {"actions": []}],
    ),
    "common/subject_list.html": (
        "Subjects", "s", "subjects",
        [("name","Name"),("code","Code"),("is_compulsory","Compulsory?"),("is_active","Active?")],
        [{"text": "s.name"}, {"text": "s.code"},
         {"badge_yes_no": "s.is_compulsory"},
         {"badge_yes_no": "s.is_active"}],
    ),
    "common/academic_year_form.html": (
        "New Academic Year", "Academic Year created.", "common:academic_year_list"
    ),
    "common/academic_year_detail.html": "year",
    "common/class_form.html": "New Class",
    "common/subject_form.html": "New Subject",
    "common/search_results.html": "search",
}

# Now write the simple form/detail templates
SIMPLE_FORM_TEMPLATES = [
    ("common/academic_year_form.html", "New Academic Year", "common:academic_year_list"),
    ("common/class_form.html", "New Class", "common:class_list"),
    ("common/subject_form.html", "New Subject", "common:subject_list"),
]

for tmpl_path, title, cancel_url in SIMPLE_FORM_TEMPLATES:
    full_path = os.path.join(BASE, tmpl_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write("""{% extends "base.html" %}
{% load crispy_forms_tags %}
{% block content %}
<h1 class="h3 fw-bold mb-3">""" + title + """</h1>
<div class="card"><div class="card-body">
<form method="post">{% csrf_token %}{{ form|crispy }}
<div class="mt-3">
<button class="btn btn-primary"><i class="bi bi-check-lg me-1"></i>Save</button>
<a href="{% url '""" + cancel_url + """' %}" class="btn btn-outline-secondary">Cancel</a>
</div></form>
</div></div>
{% endblock %}
""")

# Academic year detail template
with open(os.path.join(BASE, "common/academic_year_detail.html"), "w") as f:
    f.write("""{% extends "base.html" %}
{% block content %}
<h1 class="h3 fw-bold mb-3">{{ year.name }} {% if year.is_active %}<span class="badge bg-soft-success">Active</span>{% else %}<span class="badge badge-draft">Archived</span>{% endif %}</h1>
<div class="card"><div class="card-body p-0">
<table class="table mb-0">
<tr><th class="w-25">Name</th><td>{{ year.name }}</td></tr>
<tr><th>Start Date</th><td>{{ year.start_date|date:"M d, Y" }}</td></tr>
<tr><th>End Date</th><td>{{ year.end_date|date:"M d, Y" }}</td></tr>
<tr><th>Status</th><td>{% if year.is_active %}<span class="badge bg-soft-success">Active</span>{% else %}<span class="badge badge-draft">Archived</span>{% endif %}</td></tr>
</table>
</div></div>
<div class="mt-3">
{% if not year.is_active %}
<form method="post" action="{% url 'common:academic_year_activate' year.pk %}">{% csrf_token %}<button class="btn btn-primary"><i class="bi bi-check-circle me-1"></i>Make Active</button></form>
{% endif %}
<a href="{% url 'common:academic_year_list' %}" class="btn btn-outline-secondary">Back</a>
</div>
{% endblock %}
""")

# Academic year list
with open(os.path.join(BASE, "common/academic_year_list.html"), "w") as f:
    f.write("""{% extends "base.html" %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3">
<h1 class="h3 fw-bold mb-0">Academic Years</h1>
{% if perms.common.add_academicyear %}
<a href="{% url 'common:academic_year_create' %}" class="btn btn-primary"><i class="bi bi-plus me-1"></i>New Academic Year</a>
{% endif %}
</div>
<div class="card"><div class="card-body p-0">
{% if years %}
<table class="table table-hover mb-0">
<thead><tr><th>Name</th><th>Start</th><th>End</th><th>Status</th><th class="text-end">Actions</th></tr></thead>
<tbody>
{% for y in years %}
<tr>
<td><strong>{{ y.name }}</strong></td>
<td>{{ y.start_date|date:"M d, Y" }}</td>
<td>{{ y.end_date|date:"M d, Y" }}</td>
<td>{% if y.is_active %}<span class="badge bg-soft-success">Active</span>{% elif y.is_archived %}<span class="badge badge-draft">Archived</span>{% else %}<span class="badge badge-draft">Inactive</span>{% endif %}</td>
<td class="text-end">
<a href="{% url 'common:academic_year_detail' y.pk %}" class="btn btn-sm btn-outline-primary"><i class="bi bi-eye"></i></a>
{% if not y.is_active and perms.common.change_academicyear %}
<form method="post" action="{% url 'common:academic_year_activate' y.pk %}" class="d-inline">{% csrf_token %}<button class="btn btn-sm btn-outline-success" data-confirm="Make this the active year?"><i class="bi bi-check-circle"></i></button></form>
{% endif %}
</td>
</tr>
{% endfor %}
</tbody>
</table>
{% else %}
<div class="empty-state"><i class="bi bi-calendar"></i><p>No academic years yet.</p></div>
{% endif %}
</div></div>
{% endblock %}
""")

# Class list
with open(os.path.join(BASE, "common/class_list.html"), "w") as f:
    f.write("""{% extends "base.html" %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3">
<h1 class="h3 fw-bold mb-0">Classes & Sections</h1>
{% if perms.common.add_schoolclass %}
<a href="{% url 'common:class_create' %}" class="btn btn-primary"><i class="bi bi-plus me-1"></i>New Class</a>
{% endif %}
</div>
<div class="card"><div class="card-body">
<form method="get" class="mb-3"><div class="input-group"><input type="text" name="q" class="form-control" placeholder="Search" value="{{ request.GET.q }}"><button class="btn btn-outline-primary">Search</button></div></form>
</div></div>
<div class="card mt-3"><div class="card-body p-0">
{% if classes %}
<table class="table table-hover mb-0">
<thead><tr><th>Name</th><th>Level</th><th>Order</th><th>Sections</th><th>Active?</th></tr></thead>
<tbody>
{% for c in classes %}
<tr><td><strong>{{ c.name }}</strong></td><td>{{ c.get_grade_level_display }}</td><td>{{ c.order }}</td><td>{{ c.sections.count }}</td><td>{% if c.is_active %}<i class="bi bi-check-circle text-success"></i>{% else %}<i class="bi bi-x-circle text-danger"></i>{% endif %}</td></tr>
{% endfor %}
</tbody>
</table>
{% else %}
<div class="empty-state"><i class="bi bi-easel"></i></div>
{% endif %}
</div></div>
{% endblock %}
""")

# Subject list
with open(os.path.join(BASE, "common/subject_list.html"), "w") as f:
    f.write("""{% extends "base.html" %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3">
<h1 class="h3 fw-bold mb-0">Subjects</h1>
{% if perms.common.add_subject %}
<a href="{% url 'common:subject_create' %}" class="btn btn-primary"><i class="bi bi-plus me-1"></i>New Subject</a>
{% endif %}
</div>
<div class="card"><div class="card-body p-0">
{% if subjects %}
<table class="table table-hover mb-0">
<thead><tr><th>Name</th><th>Code</th><th>Compulsory</th><th>Active</th></tr></thead>
<tbody>
{% for s in subjects %}
<tr><td><strong>{{ s.name }}</strong></td><td>{{ s.code }}</td><td>{% if s.is_compulsory %}<i class="bi bi-check-circle text-success"></i>{% else %}<i class="bi bi-x-circle text-danger"></i>{% endif %}</td><td>{% if s.is_active %}<i class="bi bi-check-circle text-success"></i>{% else %}<i class="bi bi-x-circle text-danger"></i>{% endif %}</td></tr>
{% endfor %}
</tbody>
</table>
{% else %}
<div class="empty-state"><i class="bi bi-journal-bookmark"></i></div>
{% endif %}
</div></div>
{% endblock %}
""")

# Global search results
with open(os.path.join(BASE, "common/search_results.html"), "w") as f:
    f.write("""{% extends "base.html" %}
{% block content %}
<h1 class="h3 fw-bold mb-3"><i class="bi bi-search me-2"></i>Search Results</h1>
<p class="text-muted-2">Searching for: <strong>{{ q }}</strong></p>
<div class="row g-3">
{% if students %}
<div class="col-md-6"><div class="card"><div class="card-header">Students</div><div class="card-body p-0"><ul class="list-group list-group-flush">{% for s in students %}<li class="list-group-item"><a href="{% url 'students:student_detail' s.pk %}">{{ s.full_name }}</a><br><small class="text-muted-2">{{ s.registration_no }} · {{ s.class_section_display }}</small></li>{% endfor %}</ul></div></div></div>
{% endif %}
{% if teachers %}
<div class="col-md-6"><div class="card"><div class="card-header">Teachers</div><div class="card-body p-0"><ul class="list-group list-group-flush">{% for t in teachers %}<li class="list-group-item"><a href="{% url 'teachers:teacher_detail' t.pk %}">{{ t.full_name }}</a><br><small class="text-muted-2">{{ t.employee_id }}</small></li>{% endfor %}</ul></div></div></div>
{% endif %}
{% if parents %}
<div class="col-md-6"><div class="card"><div class="card-header">Parents</div><div class="card-body p-0"><ul class="list-group list-group-flush">{% for p in parents %}<li class="list-group-item"><a href="{% url 'parents:parent_detail' p.pk %}">{{ p.full_name }}</a><br><small class="text-muted-2">{{ p.cnic }}</small></li>{% endfor %}</ul></div></div></div>
{% endif %}
{% if challans %}
<div class="col-md-6"><div class="card"><div class="card-header">Fee Challans</div><div class="card-body p-0"><ul class="list-group list-group-flush">{% for c in challans %}<li class="list-group-item"><a href="{% url 'fees:challan_detail' c.pk %}">{{ c.challan_no }}</a><br><small class="text-muted-2">{{ c.student.full_name }} · {{ c.month|default:"" }}</small></li>{% endfor %}</ul></div></div></div>
{% endif %}
{% if tests %}
<div class="col-md-6"><div class="card"><div class="card-header">Class Tests</div><div class="card-body p-0"><ul class="list-group list-group-flush">{% for t in tests %}<li class="list-group-item"><a href="{% url 'examinations:classtest_detail' t.pk %}">{{ t.title }}</a><br><small class="text-muted-2">{{ t.school_class.name }} · {{ t.date }}</small></li>{% endfor %}</ul></div></div></div>
{% endif %}
{% if not students and not teachers and not parents and not challans and not tests %}
<div class="empty-state"><i class="bi bi-search"></i><p>No results found. Try a different query.</p></div>
{% endif %}
</div>
{% endblock %}
""")

print("All common templates created")
