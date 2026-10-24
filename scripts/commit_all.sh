#!/usr/bin/env bash
# Auto-generated: one commit per file in the School ERP project.
# Run from the project root directory (school_erp/).
set -e

cd "$(dirname "$0")/.." 2>/dev/null || cd "$(pwd)"

# Initialize git if needed
if [ ! -d .git ]; then
    git init -q
    git branch -M main 2>/dev/null || true
fi

# Set committer identity if not set (override via env if you want)
git config user.email >/dev/null 2>&1 || git config user.email "dev@school-erp.local"
git config user.name  >/dev/null 2>&1 || git config user.name  "School ERP Dev"

# [1/357] README.md
git add -A -- "README.md"
git commit -q -m "docs: add project README with setup and usage instructions" --no-verify 2>/dev/null || true

# [2/357] manage.py
git add -A -- "manage.py"
git commit -q -m "chore: add Django manage.py entry point" --no-verify 2>/dev/null || true

# [3/357] requirements/base.txt
git add -A -- "requirements/base.txt"
git commit -q -m "build: pin base Python dependencies (Django, psycopg2, WeasyPrint)" --no-verify 2>/dev/null || true

# [4/357] requirements/dev.txt
git add -A -- "requirements/dev.txt"
git commit -q -m "build: pin dev dependencies (extends base.txt)" --no-verify 2>/dev/null || true

# [5/357] config/__init__.py
git add -A -- "config/__init__.py"
git commit -q -m "chore(config): add package init with default settings module" --no-verify 2>/dev/null || true

# [6/357] config/settings/__init__.py
git add -A -- "config/settings/__init__.py"
git commit -q -m "chore(config): add settings package init" --no-verify 2>/dev/null || true

# [7/357] config/settings/base.py
git add -A -- "config/settings/base.py"
git commit -q -m "feat(config): add base settings — INSTALLED_APPS, middleware, DB, auth, school config" --no-verify 2>/dev/null || true

# [8/357] config/settings/dev.py
git add -A -- "config/settings/dev.py"
git commit -q -m "feat(config): add dev settings — DEBUG=True, SQLite fallback" --no-verify 2>/dev/null || true

# [9/357] config/settings/prod.py
git add -A -- "config/settings/prod.py"
git commit -q -m "feat(config): add prod settings — security headers, HTTPS, env-driven" --no-verify 2>/dev/null || true

# [10/357] config/wsgi.py
git add -A -- "config/wsgi.py"
git commit -q -m "chore(config): add WSGI entry point" --no-verify 2>/dev/null || true

# [11/357] config/asgi.py
git add -A -- "config/asgi.py"
git commit -q -m "chore(config): add ASGI entry point" --no-verify 2>/dev/null || true

# [12/357] config/urls.py
git add -A -- "config/urls.py"
git commit -q -m "feat(config): wire up root URL configuration for all apps" --no-verify 2>/dev/null || true

# [13/357] static/css/style.css
git add -A -- "static/css/style.css"
git commit -q -m "style: add premium UI stylesheet (sidebar, topbar, stat cards, dark mode, PAID stamp)" --no-verify 2>/dev/null || true

# [14/357] static/js/app.js
git add -A -- "static/js/app.js"
git commit -q -m "feat(static): add app.js — theme toggle, sidebar, global search (Ctrl+K), toasts" --no-verify 2>/dev/null || true

# [15/357] scripts/generate_templates.py
git add -A -- "scripts/generate_templates.py"
git commit -q -m "chore(scripts): add generate_templates.py" --no-verify 2>/dev/null || true

# [16/357] scripts/generate_remaining_templates.py
git add -A -- "scripts/generate_remaining_templates.py"
git commit -q -m "chore(scripts): add generate_remaining_templates.py" --no-verify 2>/dev/null || true

# [17/357] scripts/git_one_commit_per_file.py
git add -A -- "scripts/git_one_commit_per_file.py"
git commit -q -m "chore(scripts): add git_one_commit_per_file.py" --no-verify 2>/dev/null || true

# [18/357] apps/accounts/__init__.py
git add -A -- "apps/accounts/__init__.py"
git commit -q -m "chore(accounts): add package __init__" --no-verify 2>/dev/null || true

# [19/357] apps/accounts/apps.py
git add -A -- "apps/accounts/apps.py"
git commit -q -m "feat(accounts): register AppConfig with proper label and name" --no-verify 2>/dev/null || true

# [20/357] apps/accounts/models.py
git add -A -- "apps/accounts/models.py"
git commit -q -m "feat(accounts): add models" --no-verify 2>/dev/null || true

# [21/357] apps/accounts/migrations/__init__.py
git add -A -- "apps/accounts/migrations/__init__.py"
git commit -q -m "chore(accounts): add migrations package init" --no-verify 2>/dev/null || true

# [22/357] apps/accounts/migrations/0001_initial.py
git add -A -- "apps/accounts/migrations/0001_initial.py"
git commit -q -m "feat(accounts): add migration 0001_initial.py" --no-verify 2>/dev/null || true

# [23/357] apps/accounts/admin.py
git add -A -- "apps/accounts/admin.py"
git commit -q -m "feat(accounts): register models with Django admin (list_display, filters, inlines)" --no-verify 2>/dev/null || true

# [24/357] apps/accounts/services/__init__.py
git add -A -- "apps/accounts/services/__init__.py"
git commit -q -m "chore(accounts): add services package init" --no-verify 2>/dev/null || true

# [25/357] apps/accounts/management/__init__.py
git add -A -- "apps/accounts/management/__init__.py"
git commit -q -m "chore(accounts): add management package init" --no-verify 2>/dev/null || true

# [26/357] apps/accounts/management/commands/__init__.py
git add -A -- "apps/accounts/management/commands/__init__.py"
git commit -q -m "chore(accounts): add management commands package init" --no-verify 2>/dev/null || true

# [27/357] apps/accounts/management/commands/create_school_roles.py
git add -A -- "apps/accounts/management/commands/create_school_roles.py"
git commit -q -m "feat(accounts): add management command 'create_school_roles'" --no-verify 2>/dev/null || true

# [28/357] apps/accounts/views.py
git add -A -- "apps/accounts/views.py"
git commit -q -m "feat(accounts): add class-based views (ListView, CreateView, etc.)" --no-verify 2>/dev/null || true

# [29/357] apps/accounts/tests.py
git add -A -- "apps/accounts/tests.py"
git commit -q -m "test(accounts): add unit tests" --no-verify 2>/dev/null || true

# [30/357] apps/accounts/mixins.py
git add -A -- "apps/accounts/mixins.py"
git commit -q -m "feat(accounts): add reusable view mixins" --no-verify 2>/dev/null || true

# [31/357] apps/activities/__init__.py
git add -A -- "apps/activities/__init__.py"
git commit -q -m "chore(activities): add package __init__" --no-verify 2>/dev/null || true

# [32/357] apps/activities/apps.py
git add -A -- "apps/activities/apps.py"
git commit -q -m "feat(activities): register AppConfig with proper label and name" --no-verify 2>/dev/null || true

# [33/357] apps/activities/models.py
git add -A -- "apps/activities/models.py"
git commit -q -m "feat(activities): add models" --no-verify 2>/dev/null || true

# [34/357] apps/activities/migrations/__init__.py
git add -A -- "apps/activities/migrations/__init__.py"
git commit -q -m "chore(activities): add migrations package init" --no-verify 2>/dev/null || true

# [35/357] apps/activities/migrations/0001_initial.py
git add -A -- "apps/activities/migrations/0001_initial.py"
git commit -q -m "feat(activities): add migration 0001_initial.py" --no-verify 2>/dev/null || true

# [36/357] apps/activities/admin.py
git add -A -- "apps/activities/admin.py"
git commit -q -m "feat(activities): register models with Django admin (list_display, filters, inlines)" --no-verify 2>/dev/null || true

# [37/357] apps/activities/forms.py
git add -A -- "apps/activities/forms.py"
git commit -q -m "feat(activities): add forms with crispy-forms helpers" --no-verify 2>/dev/null || true

# [38/357] apps/activities/services/__init__.py
git add -A -- "apps/activities/services/__init__.py"
git commit -q -m "chore(activities): add services package init" --no-verify 2>/dev/null || true

# [39/357] apps/activities/urls.py
git add -A -- "apps/activities/urls.py"
git commit -q -m "feat(activities): wire up app URL routing" --no-verify 2>/dev/null || true

# [40/357] apps/activities/views.py
git add -A -- "apps/activities/views.py"
git commit -q -m "feat(activities): add class-based views (ListView, CreateView, etc.)" --no-verify 2>/dev/null || true

# [41/357] apps/activities/tests.py
git add -A -- "apps/activities/tests.py"
git commit -q -m "test(activities): add unit tests" --no-verify 2>/dev/null || true

# [42/357] apps/admissions/__init__.py
git add -A -- "apps/admissions/__init__.py"
git commit -q -m "chore(admissions): add package __init__" --no-verify 2>/dev/null || true

# [43/357] apps/admissions/apps.py
git add -A -- "apps/admissions/apps.py"
git commit -q -m "feat(admissions): register AppConfig with proper label and name" --no-verify 2>/dev/null || true

# [44/357] apps/admissions/models.py
git add -A -- "apps/admissions/models.py"
git commit -q -m "feat(admissions): add models" --no-verify 2>/dev/null || true

# [45/357] apps/admissions/migrations/__init__.py
git add -A -- "apps/admissions/migrations/__init__.py"
git commit -q -m "chore(admissions): add migrations package init" --no-verify 2>/dev/null || true

# [46/357] apps/admissions/migrations/0001_initial.py
git add -A -- "apps/admissions/migrations/0001_initial.py"
git commit -q -m "feat(admissions): add migration 0001_initial.py" --no-verify 2>/dev/null || true

# [47/357] apps/admissions/admin.py
git add -A -- "apps/admissions/admin.py"
git commit -q -m "feat(admissions): register models with Django admin (list_display, filters, inlines)" --no-verify 2>/dev/null || true

# [48/357] apps/admissions/forms.py
git add -A -- "apps/admissions/forms.py"
git commit -q -m "feat(admissions): add forms with crispy-forms helpers" --no-verify 2>/dev/null || true

# [49/357] apps/admissions/services/__init__.py
git add -A -- "apps/admissions/services/__init__.py"
git commit -q -m "chore(admissions): add services package init" --no-verify 2>/dev/null || true

# [50/357] apps/admissions/services/admission_service.py
git add -A -- "apps/admissions/services/admission_service.py"
git commit -q -m "feat(admissions): add admission_service service — business logic isolation" --no-verify 2>/dev/null || true

# [51/357] apps/admissions/urls.py
git add -A -- "apps/admissions/urls.py"
git commit -q -m "feat(admissions): wire up app URL routing" --no-verify 2>/dev/null || true

# [52/357] apps/admissions/views.py
git add -A -- "apps/admissions/views.py"
git commit -q -m "feat(admissions): add class-based views (ListView, CreateView, etc.)" --no-verify 2>/dev/null || true

# [53/357] apps/admissions/tests.py
git add -A -- "apps/admissions/tests.py"
git commit -q -m "test(admissions): add unit tests" --no-verify 2>/dev/null || true

# [54/357] apps/announcements/__init__.py
git add -A -- "apps/announcements/__init__.py"
git commit -q -m "chore(announcements): add package __init__" --no-verify 2>/dev/null || true

# [55/357] apps/announcements/apps.py
git add -A -- "apps/announcements/apps.py"
git commit -q -m "feat(announcements): register AppConfig with proper label and name" --no-verify 2>/dev/null || true

# [56/357] apps/announcements/models.py
git add -A -- "apps/announcements/models.py"
git commit -q -m "feat(announcements): add models" --no-verify 2>/dev/null || true

# [57/357] apps/announcements/migrations/__init__.py
git add -A -- "apps/announcements/migrations/__init__.py"
git commit -q -m "chore(announcements): add migrations package init" --no-verify 2>/dev/null || true

# [58/357] apps/announcements/migrations/0001_initial.py
git add -A -- "apps/announcements/migrations/0001_initial.py"
git commit -q -m "feat(announcements): add migration 0001_initial.py" --no-verify 2>/dev/null || true

# [59/357] apps/announcements/admin.py
git add -A -- "apps/announcements/admin.py"
git commit -q -m "feat(announcements): register models with Django admin (list_display, filters, inlines)" --no-verify 2>/dev/null || true

# [60/357] apps/announcements/forms.py
git add -A -- "apps/announcements/forms.py"
git commit -q -m "feat(announcements): add forms with crispy-forms helpers" --no-verify 2>/dev/null || true

# [61/357] apps/announcements/services/__init__.py
git add -A -- "apps/announcements/services/__init__.py"
git commit -q -m "chore(announcements): add services package init" --no-verify 2>/dev/null || true

# [62/357] apps/announcements/urls.py
git add -A -- "apps/announcements/urls.py"
git commit -q -m "feat(announcements): wire up app URL routing" --no-verify 2>/dev/null || true

# [63/357] apps/announcements/views.py
git add -A -- "apps/announcements/views.py"
git commit -q -m "feat(announcements): add class-based views (ListView, CreateView, etc.)" --no-verify 2>/dev/null || true

# [64/357] apps/announcements/tests.py
git add -A -- "apps/announcements/tests.py"
git commit -q -m "test(announcements): add unit tests" --no-verify 2>/dev/null || true

# [65/357] apps/attendance/__init__.py
git add -A -- "apps/attendance/__init__.py"
git commit -q -m "chore(attendance): add package __init__" --no-verify 2>/dev/null || true

# [66/357] apps/attendance/apps.py
git add -A -- "apps/attendance/apps.py"
git commit -q -m "feat(attendance): register AppConfig with proper label and name" --no-verify 2>/dev/null || true

# [67/357] apps/attendance/models.py
git add -A -- "apps/attendance/models.py"
git commit -q -m "feat(attendance): add models" --no-verify 2>/dev/null || true

# [68/357] apps/attendance/migrations/__init__.py
git add -A -- "apps/attendance/migrations/__init__.py"
git commit -q -m "chore(attendance): add migrations package init" --no-verify 2>/dev/null || true

# [69/357] apps/attendance/migrations/0001_initial.py
git add -A -- "apps/attendance/migrations/0001_initial.py"
git commit -q -m "feat(attendance): add migration 0001_initial.py" --no-verify 2>/dev/null || true

# [70/357] apps/attendance/admin.py
git add -A -- "apps/attendance/admin.py"
git commit -q -m "feat(attendance): register models with Django admin (list_display, filters, inlines)" --no-verify 2>/dev/null || true

# [71/357] apps/attendance/forms.py
git add -A -- "apps/attendance/forms.py"
git commit -q -m "feat(attendance): add forms with crispy-forms helpers" --no-verify 2>/dev/null || true

# [72/357] apps/attendance/services/__init__.py
git add -A -- "apps/attendance/services/__init__.py"
git commit -q -m "chore(attendance): add services package init" --no-verify 2>/dev/null || true

# [73/357] apps/attendance/urls.py
git add -A -- "apps/attendance/urls.py"
git commit -q -m "feat(attendance): wire up app URL routing" --no-verify 2>/dev/null || true

# [74/357] apps/attendance/views.py
git add -A -- "apps/attendance/views.py"
git commit -q -m "feat(attendance): add class-based views (ListView, CreateView, etc.)" --no-verify 2>/dev/null || true

# [75/357] apps/attendance/tests.py
git add -A -- "apps/attendance/tests.py"
git commit -q -m "test(attendance): add unit tests" --no-verify 2>/dev/null || true

# [76/357] apps/audit_logs/__init__.py
git add -A -- "apps/audit_logs/__init__.py"
git commit -q -m "chore(audit_logs): add package __init__" --no-verify 2>/dev/null || true

# [77/357] apps/audit_logs/apps.py
git add -A -- "apps/audit_logs/apps.py"
git commit -q -m "feat(audit_logs): register AppConfig with proper label and name" --no-verify 2>/dev/null || true

# [78/357] apps/audit_logs/models.py
git add -A -- "apps/audit_logs/models.py"
git commit -q -m "feat(audit_logs): add models" --no-verify 2>/dev/null || true

# [79/357] apps/audit_logs/migrations/__init__.py
git add -A -- "apps/audit_logs/migrations/__init__.py"
git commit -q -m "chore(audit_logs): add migrations package init" --no-verify 2>/dev/null || true

# [80/357] apps/audit_logs/migrations/0001_initial.py
git add -A -- "apps/audit_logs/migrations/0001_initial.py"
git commit -q -m "feat(audit_logs): add migration 0001_initial.py" --no-verify 2>/dev/null || true

# [81/357] apps/audit_logs/admin.py
git add -A -- "apps/audit_logs/admin.py"
git commit -q -m "feat(audit_logs): register models with Django admin (list_display, filters, inlines)" --no-verify 2>/dev/null || true

# [82/357] apps/audit_logs/services/__init__.py
git add -A -- "apps/audit_logs/services/__init__.py"
git commit -q -m "chore(audit_logs): add services package init" --no-verify 2>/dev/null || true

# [83/357] apps/audit_logs/urls.py
git add -A -- "apps/audit_logs/urls.py"
git commit -q -m "feat(audit_logs): wire up app URL routing" --no-verify 2>/dev/null || true

# [84/357] apps/audit_logs/views.py
git add -A -- "apps/audit_logs/views.py"
git commit -q -m "feat(audit_logs): add class-based views (ListView, CreateView, etc.)" --no-verify 2>/dev/null || true

# [85/357] apps/audit_logs/tests.py
git add -A -- "apps/audit_logs/tests.py"
git commit -q -m "test(audit_logs): add unit tests" --no-verify 2>/dev/null || true

# [86/357] apps/audit_logs/middleware.py
git add -A -- "apps/audit_logs/middleware.py"
git commit -q -m "feat(audit_logs): add middleware" --no-verify 2>/dev/null || true

# [87/357] apps/common/__init__.py
git add -A -- "apps/common/__init__.py"
git commit -q -m "chore(common): add package __init__" --no-verify 2>/dev/null || true

# [88/357] apps/common/apps.py
git add -A -- "apps/common/apps.py"
git commit -q -m "feat(common): register AppConfig with proper label and name" --no-verify 2>/dev/null || true

# [89/357] apps/common/models.py
git add -A -- "apps/common/models.py"
git commit -q -m "feat(common): add models" --no-verify 2>/dev/null || true

# [90/357] apps/common/migrations/__init__.py
git add -A -- "apps/common/migrations/__init__.py"
git commit -q -m "chore(common): add migrations package init" --no-verify 2>/dev/null || true

# [91/357] apps/common/migrations/0001_initial.py
git add -A -- "apps/common/migrations/0001_initial.py"
git commit -q -m "feat(common): add migration 0001_initial.py" --no-verify 2>/dev/null || true

# [92/357] apps/common/admin.py
git add -A -- "apps/common/admin.py"
git commit -q -m "feat(common): register models with Django admin (list_display, filters, inlines)" --no-verify 2>/dev/null || true

# [93/357] apps/common/forms.py
git add -A -- "apps/common/forms.py"
git commit -q -m "feat(common): add forms with crispy-forms helpers" --no-verify 2>/dev/null || true

# [94/357] apps/common/services/__init__.py
git add -A -- "apps/common/services/__init__.py"
git commit -q -m "chore(common): add services package init" --no-verify 2>/dev/null || true

# [95/357] apps/common/management/__init__.py
git add -A -- "apps/common/management/__init__.py"
git commit -q -m "chore(common): add management package init" --no-verify 2>/dev/null || true

# [96/357] apps/common/management/commands/__init__.py
git add -A -- "apps/common/management/commands/__init__.py"
git commit -q -m "chore(common): add management commands package init" --no-verify 2>/dev/null || true

# [97/357] apps/common/management/commands/generate_demo_data.py
git add -A -- "apps/common/management/commands/generate_demo_data.py"
git commit -q -m "feat(common): add management command 'generate_demo_data'" --no-verify 2>/dev/null || true

# [98/357] apps/common/urls.py
git add -A -- "apps/common/urls.py"
git commit -q -m "feat(common): wire up app URL routing" --no-verify 2>/dev/null || true

# [99/357] apps/common/views.py
git add -A -- "apps/common/views.py"
git commit -q -m "feat(common): add class-based views (ListView, CreateView, etc.)" --no-verify 2>/dev/null || true

# [100/357] apps/common/tests.py
git add -A -- "apps/common/tests.py"
git commit -q -m "test(common): add unit tests" --no-verify 2>/dev/null || true

# [101/357] apps/common/context_processors.py
git add -A -- "apps/common/context_processors.py"
git commit -q -m "feat(common): add template context processor" --no-verify 2>/dev/null || true

# [102/357] apps/dashboard/__init__.py
git add -A -- "apps/dashboard/__init__.py"
git commit -q -m "chore(dashboard): add package __init__" --no-verify 2>/dev/null || true

# [103/357] apps/dashboard/apps.py
git add -A -- "apps/dashboard/apps.py"
git commit -q -m "feat(dashboard): register AppConfig with proper label and name" --no-verify 2>/dev/null || true

# [104/357] apps/dashboard/urls.py
git add -A -- "apps/dashboard/urls.py"
git commit -q -m "feat(dashboard): wire up app URL routing" --no-verify 2>/dev/null || true

# [105/357] apps/dashboard/views.py
git add -A -- "apps/dashboard/views.py"
git commit -q -m "feat(dashboard): add class-based views (ListView, CreateView, etc.)" --no-verify 2>/dev/null || true

# [106/357] apps/datesheets/__init__.py
git add -A -- "apps/datesheets/__init__.py"
git commit -q -m "chore(datesheets): add package __init__" --no-verify 2>/dev/null || true

# [107/357] apps/datesheets/apps.py
git add -A -- "apps/datesheets/apps.py"
git commit -q -m "feat(datesheets): register AppConfig with proper label and name" --no-verify 2>/dev/null || true

# [108/357] apps/datesheets/models.py
git add -A -- "apps/datesheets/models.py"
git commit -q -m "feat(datesheets): add models" --no-verify 2>/dev/null || true

# [109/357] apps/datesheets/migrations/__init__.py
git add -A -- "apps/datesheets/migrations/__init__.py"
git commit -q -m "chore(datesheets): add migrations package init" --no-verify 2>/dev/null || true

# [110/357] apps/datesheets/migrations/0001_initial.py
git add -A -- "apps/datesheets/migrations/0001_initial.py"
git commit -q -m "feat(datesheets): add migration 0001_initial.py" --no-verify 2>/dev/null || true

# [111/357] apps/datesheets/admin.py
git add -A -- "apps/datesheets/admin.py"
git commit -q -m "feat(datesheets): register models with Django admin (list_display, filters, inlines)" --no-verify 2>/dev/null || true

# [112/357] apps/datesheets/forms.py
git add -A -- "apps/datesheets/forms.py"
git commit -q -m "feat(datesheets): add forms with crispy-forms helpers" --no-verify 2>/dev/null || true

# [113/357] apps/datesheets/services/__init__.py
git add -A -- "apps/datesheets/services/__init__.py"
git commit -q -m "chore(datesheets): add services package init" --no-verify 2>/dev/null || true

# [114/357] apps/datesheets/urls.py
git add -A -- "apps/datesheets/urls.py"
git commit -q -m "feat(datesheets): wire up app URL routing" --no-verify 2>/dev/null || true

# [115/357] apps/datesheets/views.py
git add -A -- "apps/datesheets/views.py"
git commit -q -m "feat(datesheets): add class-based views (ListView, CreateView, etc.)" --no-verify 2>/dev/null || true

# [116/357] apps/datesheets/tests.py
git add -A -- "apps/datesheets/tests.py"
git commit -q -m "test(datesheets): add unit tests" --no-verify 2>/dev/null || true

# [117/357] apps/diary/__init__.py
git add -A -- "apps/diary/__init__.py"
git commit -q -m "chore(diary): add package __init__" --no-verify 2>/dev/null || true

# [118/357] apps/diary/apps.py
git add -A -- "apps/diary/apps.py"
git commit -q -m "feat(diary): register AppConfig with proper label and name" --no-verify 2>/dev/null || true

# [119/357] apps/diary/models.py
git add -A -- "apps/diary/models.py"
git commit -q -m "feat(diary): add models" --no-verify 2>/dev/null || true

# [120/357] apps/diary/migrations/__init__.py
git add -A -- "apps/diary/migrations/__init__.py"
git commit -q -m "chore(diary): add migrations package init" --no-verify 2>/dev/null || true

# [121/357] apps/diary/migrations/0001_initial.py
git add -A -- "apps/diary/migrations/0001_initial.py"
git commit -q -m "feat(diary): add migration 0001_initial.py" --no-verify 2>/dev/null || true

# [122/357] apps/diary/admin.py
git add -A -- "apps/diary/admin.py"
git commit -q -m "feat(diary): register models with Django admin (list_display, filters, inlines)" --no-verify 2>/dev/null || true

# [123/357] apps/diary/forms.py
git add -A -- "apps/diary/forms.py"
git commit -q -m "feat(diary): add forms with crispy-forms helpers" --no-verify 2>/dev/null || true

# [124/357] apps/diary/services/__init__.py
git add -A -- "apps/diary/services/__init__.py"
git commit -q -m "chore(diary): add services package init" --no-verify 2>/dev/null || true

# [125/357] apps/diary/urls.py
git add -A -- "apps/diary/urls.py"
git commit -q -m "feat(diary): wire up app URL routing" --no-verify 2>/dev/null || true

# [126/357] apps/diary/views.py
git add -A -- "apps/diary/views.py"
git commit -q -m "feat(diary): add class-based views (ListView, CreateView, etc.)" --no-verify 2>/dev/null || true

# [127/357] apps/diary/tests.py
git add -A -- "apps/diary/tests.py"
git commit -q -m "test(diary): add unit tests" --no-verify 2>/dev/null || true

# [128/357] apps/documents/__init__.py
git add -A -- "apps/documents/__init__.py"
git commit -q -m "chore(documents): add package __init__" --no-verify 2>/dev/null || true

# [129/357] apps/documents/apps.py
git add -A -- "apps/documents/apps.py"
git commit -q -m "feat(documents): register AppConfig with proper label and name" --no-verify 2>/dev/null || true

# [130/357] apps/documents/models.py
git add -A -- "apps/documents/models.py"
git commit -q -m "feat(documents): add models" --no-verify 2>/dev/null || true

# [131/357] apps/documents/migrations/__init__.py
git add -A -- "apps/documents/migrations/__init__.py"
git commit -q -m "chore(documents): add migrations package init" --no-verify 2>/dev/null || true

# [132/357] apps/documents/migrations/0001_initial.py
git add -A -- "apps/documents/migrations/0001_initial.py"
git commit -q -m "feat(documents): add migration 0001_initial.py" --no-verify 2>/dev/null || true

# [133/357] apps/documents/admin.py
git add -A -- "apps/documents/admin.py"
git commit -q -m "feat(documents): register models with Django admin (list_display, filters, inlines)" --no-verify 2>/dev/null || true

# [134/357] apps/documents/services/__init__.py
git add -A -- "apps/documents/services/__init__.py"
git commit -q -m "chore(documents): add services package init" --no-verify 2>/dev/null || true

# [135/357] apps/documents/views.py
git add -A -- "apps/documents/views.py"
git commit -q -m "feat(documents): add class-based views (ListView, CreateView, etc.)" --no-verify 2>/dev/null || true

# [136/357] apps/documents/tests.py
git add -A -- "apps/documents/tests.py"
git commit -q -m "test(documents): add unit tests" --no-verify 2>/dev/null || true

# [137/357] apps/examinations/__init__.py
git add -A -- "apps/examinations/__init__.py"
git commit -q -m "chore(examinations): add package __init__" --no-verify 2>/dev/null || true

# [138/357] apps/examinations/apps.py
git add -A -- "apps/examinations/apps.py"
git commit -q -m "feat(examinations): register AppConfig with proper label and name" --no-verify 2>/dev/null || true

# [139/357] apps/examinations/models.py
git add -A -- "apps/examinations/models.py"
git commit -q -m "feat(examinations): add models" --no-verify 2>/dev/null || true

# [140/357] apps/examinations/migrations/__init__.py
git add -A -- "apps/examinations/migrations/__init__.py"
git commit -q -m "chore(examinations): add migrations package init" --no-verify 2>/dev/null || true

# [141/357] apps/examinations/migrations/0001_initial.py
git add -A -- "apps/examinations/migrations/0001_initial.py"
git commit -q -m "feat(examinations): add migration 0001_initial.py" --no-verify 2>/dev/null || true

# [142/357] apps/examinations/admin.py
git add -A -- "apps/examinations/admin.py"
git commit -q -m "feat(examinations): register models with Django admin (list_display, filters, inlines)" --no-verify 2>/dev/null || true

# [143/357] apps/examinations/forms.py
git add -A -- "apps/examinations/forms.py"
git commit -q -m "feat(examinations): add forms with crispy-forms helpers" --no-verify 2>/dev/null || true

# [144/357] apps/examinations/services/__init__.py
git add -A -- "apps/examinations/services/__init__.py"
git commit -q -m "chore(examinations): add services package init" --no-verify 2>/dev/null || true

# [145/357] apps/examinations/services/result_service.py
git add -A -- "apps/examinations/services/result_service.py"
git commit -q -m "feat(examinations): add result_service service — business logic isolation" --no-verify 2>/dev/null || true

# [146/357] apps/examinations/urls.py
git add -A -- "apps/examinations/urls.py"
git commit -q -m "feat(examinations): wire up app URL routing" --no-verify 2>/dev/null || true

# [147/357] apps/examinations/views.py
git add -A -- "apps/examinations/views.py"
git commit -q -m "feat(examinations): add class-based views (ListView, CreateView, etc.)" --no-verify 2>/dev/null || true

# [148/357] apps/examinations/tests.py
git add -A -- "apps/examinations/tests.py"
git commit -q -m "test(examinations): add unit tests" --no-verify 2>/dev/null || true

# [149/357] apps/fees/__init__.py
git add -A -- "apps/fees/__init__.py"
git commit -q -m "chore(fees): add package __init__" --no-verify 2>/dev/null || true

# [150/357] apps/fees/apps.py
git add -A -- "apps/fees/apps.py"
git commit -q -m "feat(fees): register AppConfig with proper label and name" --no-verify 2>/dev/null || true

# [151/357] apps/fees/models.py
git add -A -- "apps/fees/models.py"
git commit -q -m "feat(fees): add models" --no-verify 2>/dev/null || true

# [152/357] apps/fees/migrations/__init__.py
git add -A -- "apps/fees/migrations/__init__.py"
git commit -q -m "chore(fees): add migrations package init" --no-verify 2>/dev/null || true

# [153/357] apps/fees/migrations/0001_initial.py
git add -A -- "apps/fees/migrations/0001_initial.py"
git commit -q -m "feat(fees): add migration 0001_initial.py" --no-verify 2>/dev/null || true

# [154/357] apps/fees/admin.py
git add -A -- "apps/fees/admin.py"
git commit -q -m "feat(fees): register models with Django admin (list_display, filters, inlines)" --no-verify 2>/dev/null || true

# [155/357] apps/fees/forms.py
git add -A -- "apps/fees/forms.py"
git commit -q -m "feat(fees): add forms with crispy-forms helpers" --no-verify 2>/dev/null || true

# [156/357] apps/fees/services/__init__.py
git add -A -- "apps/fees/services/__init__.py"
git commit -q -m "chore(fees): add services package init" --no-verify 2>/dev/null || true

# [157/357] apps/fees/services/fee_service.py
git add -A -- "apps/fees/services/fee_service.py"
git commit -q -m "feat(fees): add fee_service service — business logic isolation" --no-verify 2>/dev/null || true

# [158/357] apps/fees/urls.py
git add -A -- "apps/fees/urls.py"
git commit -q -m "feat(fees): wire up app URL routing" --no-verify 2>/dev/null || true

# [159/357] apps/fees/views.py
git add -A -- "apps/fees/views.py"
git commit -q -m "feat(fees): add class-based views (ListView, CreateView, etc.)" --no-verify 2>/dev/null || true

# [160/357] apps/fees/tests.py
git add -A -- "apps/fees/tests.py"
git commit -q -m "test(fees): add unit tests" --no-verify 2>/dev/null || true

# [161/357] apps/homework/__init__.py
git add -A -- "apps/homework/__init__.py"
git commit -q -m "chore(homework): add package __init__" --no-verify 2>/dev/null || true

# [162/357] apps/homework/apps.py
git add -A -- "apps/homework/apps.py"
git commit -q -m "feat(homework): register AppConfig with proper label and name" --no-verify 2>/dev/null || true

# [163/357] apps/homework/models.py
git add -A -- "apps/homework/models.py"
git commit -q -m "feat(homework): add models" --no-verify 2>/dev/null || true

# [164/357] apps/homework/migrations/__init__.py
git add -A -- "apps/homework/migrations/__init__.py"
git commit -q -m "chore(homework): add migrations package init" --no-verify 2>/dev/null || true

# [165/357] apps/homework/migrations/0001_initial.py
git add -A -- "apps/homework/migrations/0001_initial.py"
git commit -q -m "feat(homework): add migration 0001_initial.py" --no-verify 2>/dev/null || true

# [166/357] apps/homework/admin.py
git add -A -- "apps/homework/admin.py"
git commit -q -m "feat(homework): register models with Django admin (list_display, filters, inlines)" --no-verify 2>/dev/null || true

# [167/357] apps/homework/forms.py
git add -A -- "apps/homework/forms.py"
git commit -q -m "feat(homework): add forms with crispy-forms helpers" --no-verify 2>/dev/null || true

# [168/357] apps/homework/services/__init__.py
git add -A -- "apps/homework/services/__init__.py"
git commit -q -m "chore(homework): add services package init" --no-verify 2>/dev/null || true

# [169/357] apps/homework/urls.py
git add -A -- "apps/homework/urls.py"
git commit -q -m "feat(homework): wire up app URL routing" --no-verify 2>/dev/null || true

# [170/357] apps/homework/views.py
git add -A -- "apps/homework/views.py"
git commit -q -m "feat(homework): add class-based views (ListView, CreateView, etc.)" --no-verify 2>/dev/null || true

# [171/357] apps/homework/tests.py
git add -A -- "apps/homework/tests.py"
git commit -q -m "test(homework): add unit tests" --no-verify 2>/dev/null || true

# [172/357] apps/notifications/__init__.py
git add -A -- "apps/notifications/__init__.py"
git commit -q -m "chore(notifications): add package __init__" --no-verify 2>/dev/null || true

# [173/357] apps/notifications/apps.py
git add -A -- "apps/notifications/apps.py"
git commit -q -m "feat(notifications): register AppConfig with proper label and name" --no-verify 2>/dev/null || true

# [174/357] apps/notifications/models.py
git add -A -- "apps/notifications/models.py"
git commit -q -m "feat(notifications): add models" --no-verify 2>/dev/null || true

# [175/357] apps/notifications/migrations/__init__.py
git add -A -- "apps/notifications/migrations/__init__.py"
git commit -q -m "chore(notifications): add migrations package init" --no-verify 2>/dev/null || true

# [176/357] apps/notifications/migrations/0001_initial.py
git add -A -- "apps/notifications/migrations/0001_initial.py"
git commit -q -m "feat(notifications): add migration 0001_initial.py" --no-verify 2>/dev/null || true

# [177/357] apps/notifications/admin.py
git add -A -- "apps/notifications/admin.py"
git commit -q -m "feat(notifications): register models with Django admin (list_display, filters, inlines)" --no-verify 2>/dev/null || true

# [178/357] apps/notifications/services/__init__.py
git add -A -- "apps/notifications/services/__init__.py"
git commit -q -m "chore(notifications): add services package init" --no-verify 2>/dev/null || true

# [179/357] apps/notifications/urls.py
git add -A -- "apps/notifications/urls.py"
git commit -q -m "feat(notifications): wire up app URL routing" --no-verify 2>/dev/null || true

# [180/357] apps/notifications/views.py
git add -A -- "apps/notifications/views.py"
git commit -q -m "feat(notifications): add class-based views (ListView, CreateView, etc.)" --no-verify 2>/dev/null || true

# [181/357] apps/notifications/tests.py
git add -A -- "apps/notifications/tests.py"
git commit -q -m "test(notifications): add unit tests" --no-verify 2>/dev/null || true

# [182/357] apps/parents/__init__.py
git add -A -- "apps/parents/__init__.py"
git commit -q -m "chore(parents): add package __init__" --no-verify 2>/dev/null || true

# [183/357] apps/parents/apps.py
git add -A -- "apps/parents/apps.py"
git commit -q -m "feat(parents): register AppConfig with proper label and name" --no-verify 2>/dev/null || true

# [184/357] apps/parents/models.py
git add -A -- "apps/parents/models.py"
git commit -q -m "feat(parents): add models" --no-verify 2>/dev/null || true

# [185/357] apps/parents/migrations/__init__.py
git add -A -- "apps/parents/migrations/__init__.py"
git commit -q -m "chore(parents): add migrations package init" --no-verify 2>/dev/null || true

# [186/357] apps/parents/migrations/0001_initial.py
git add -A -- "apps/parents/migrations/0001_initial.py"
git commit -q -m "feat(parents): add migration 0001_initial.py" --no-verify 2>/dev/null || true

# [187/357] apps/parents/admin.py
git add -A -- "apps/parents/admin.py"
git commit -q -m "feat(parents): register models with Django admin (list_display, filters, inlines)" --no-verify 2>/dev/null || true

# [188/357] apps/parents/forms.py
git add -A -- "apps/parents/forms.py"
git commit -q -m "feat(parents): add forms with crispy-forms helpers" --no-verify 2>/dev/null || true

# [189/357] apps/parents/services/__init__.py
git add -A -- "apps/parents/services/__init__.py"
git commit -q -m "chore(parents): add services package init" --no-verify 2>/dev/null || true

# [190/357] apps/parents/urls.py
git add -A -- "apps/parents/urls.py"
git commit -q -m "feat(parents): wire up app URL routing" --no-verify 2>/dev/null || true

# [191/357] apps/parents/views.py
git add -A -- "apps/parents/views.py"
git commit -q -m "feat(parents): add class-based views (ListView, CreateView, etc.)" --no-verify 2>/dev/null || true

# [192/357] apps/parents/tests.py
git add -A -- "apps/parents/tests.py"
git commit -q -m "test(parents): add unit tests" --no-verify 2>/dev/null || true

# [193/357] apps/payroll/__init__.py
git add -A -- "apps/payroll/__init__.py"
git commit -q -m "chore(payroll): add package __init__" --no-verify 2>/dev/null || true

# [194/357] apps/payroll/apps.py
git add -A -- "apps/payroll/apps.py"
git commit -q -m "feat(payroll): register AppConfig with proper label and name" --no-verify 2>/dev/null || true

# [195/357] apps/payroll/models.py
git add -A -- "apps/payroll/models.py"
git commit -q -m "feat(payroll): add models" --no-verify 2>/dev/null || true

# [196/357] apps/payroll/migrations/__init__.py
git add -A -- "apps/payroll/migrations/__init__.py"
git commit -q -m "chore(payroll): add migrations package init" --no-verify 2>/dev/null || true

# [197/357] apps/payroll/migrations/0001_initial.py
git add -A -- "apps/payroll/migrations/0001_initial.py"
git commit -q -m "feat(payroll): add migration 0001_initial.py" --no-verify 2>/dev/null || true

# [198/357] apps/payroll/admin.py
git add -A -- "apps/payroll/admin.py"
git commit -q -m "feat(payroll): register models with Django admin (list_display, filters, inlines)" --no-verify 2>/dev/null || true

# [199/357] apps/payroll/forms.py
git add -A -- "apps/payroll/forms.py"
git commit -q -m "feat(payroll): add forms with crispy-forms helpers" --no-verify 2>/dev/null || true

# [200/357] apps/payroll/services/__init__.py
git add -A -- "apps/payroll/services/__init__.py"
git commit -q -m "chore(payroll): add services package init" --no-verify 2>/dev/null || true

# [201/357] apps/payroll/urls.py
git add -A -- "apps/payroll/urls.py"
git commit -q -m "feat(payroll): wire up app URL routing" --no-verify 2>/dev/null || true

# [202/357] apps/payroll/views.py
git add -A -- "apps/payroll/views.py"
git commit -q -m "feat(payroll): add class-based views (ListView, CreateView, etc.)" --no-verify 2>/dev/null || true

# [203/357] apps/payroll/tests.py
git add -A -- "apps/payroll/tests.py"
git commit -q -m "test(payroll): add unit tests" --no-verify 2>/dev/null || true

# [204/357] apps/portal/__init__.py
git add -A -- "apps/portal/__init__.py"
git commit -q -m "chore(portal): add package __init__" --no-verify 2>/dev/null || true

# [205/357] apps/portal/apps.py
git add -A -- "apps/portal/apps.py"
git commit -q -m "feat(portal): register AppConfig with proper label and name" --no-verify 2>/dev/null || true

# [206/357] apps/portal/urls.py
git add -A -- "apps/portal/urls.py"
git commit -q -m "feat(portal): wire up app URL routing" --no-verify 2>/dev/null || true

# [207/357] apps/portal/views.py
git add -A -- "apps/portal/views.py"
git commit -q -m "feat(portal): add class-based views (ListView, CreateView, etc.)" --no-verify 2>/dev/null || true

# [208/357] apps/reports/__init__.py
git add -A -- "apps/reports/__init__.py"
git commit -q -m "chore(reports): add package __init__" --no-verify 2>/dev/null || true

# [209/357] apps/reports/apps.py
git add -A -- "apps/reports/apps.py"
git commit -q -m "feat(reports): register AppConfig with proper label and name" --no-verify 2>/dev/null || true

# [210/357] apps/reports/models.py
git add -A -- "apps/reports/models.py"
git commit -q -m "feat(reports): add models" --no-verify 2>/dev/null || true

# [211/357] apps/reports/migrations/__init__.py
git add -A -- "apps/reports/migrations/__init__.py"
git commit -q -m "chore(reports): add migrations package init" --no-verify 2>/dev/null || true

# [212/357] apps/reports/admin.py
git add -A -- "apps/reports/admin.py"
git commit -q -m "feat(reports): register models with Django admin (list_display, filters, inlines)" --no-verify 2>/dev/null || true

# [213/357] apps/reports/services/__init__.py
git add -A -- "apps/reports/services/__init__.py"
git commit -q -m "chore(reports): add services package init" --no-verify 2>/dev/null || true

# [214/357] apps/reports/urls.py
git add -A -- "apps/reports/urls.py"
git commit -q -m "feat(reports): wire up app URL routing" --no-verify 2>/dev/null || true

# [215/357] apps/reports/views.py
git add -A -- "apps/reports/views.py"
git commit -q -m "feat(reports): add class-based views (ListView, CreateView, etc.)" --no-verify 2>/dev/null || true

# [216/357] apps/reports/tests.py
git add -A -- "apps/reports/tests.py"
git commit -q -m "test(reports): add unit tests" --no-verify 2>/dev/null || true

# [217/357] apps/school_calendar/__init__.py
git add -A -- "apps/school_calendar/__init__.py"
git commit -q -m "chore(school_calendar): add package __init__" --no-verify 2>/dev/null || true

# [218/357] apps/school_calendar/apps.py
git add -A -- "apps/school_calendar/apps.py"
git commit -q -m "feat(school_calendar): register AppConfig with proper label and name" --no-verify 2>/dev/null || true

# [219/357] apps/school_calendar/models.py
git add -A -- "apps/school_calendar/models.py"
git commit -q -m "feat(school_calendar): add models" --no-verify 2>/dev/null || true

# [220/357] apps/school_calendar/migrations/__init__.py
git add -A -- "apps/school_calendar/migrations/__init__.py"
git commit -q -m "chore(school_calendar): add migrations package init" --no-verify 2>/dev/null || true

# [221/357] apps/school_calendar/migrations/0001_initial.py
git add -A -- "apps/school_calendar/migrations/0001_initial.py"
git commit -q -m "feat(school_calendar): add migration 0001_initial.py" --no-verify 2>/dev/null || true

# [222/357] apps/school_calendar/admin.py
git add -A -- "apps/school_calendar/admin.py"
git commit -q -m "feat(school_calendar): register models with Django admin (list_display, filters, inlines)" --no-verify 2>/dev/null || true

# [223/357] apps/school_calendar/forms.py
git add -A -- "apps/school_calendar/forms.py"
git commit -q -m "feat(school_calendar): add forms with crispy-forms helpers" --no-verify 2>/dev/null || true

# [224/357] apps/school_calendar/services/__init__.py
git add -A -- "apps/school_calendar/services/__init__.py"
git commit -q -m "chore(school_calendar): add services package init" --no-verify 2>/dev/null || true

# [225/357] apps/school_calendar/urls.py
git add -A -- "apps/school_calendar/urls.py"
git commit -q -m "feat(school_calendar): wire up app URL routing" --no-verify 2>/dev/null || true

# [226/357] apps/school_calendar/views.py
git add -A -- "apps/school_calendar/views.py"
git commit -q -m "feat(school_calendar): add class-based views (ListView, CreateView, etc.)" --no-verify 2>/dev/null || true

# [227/357] apps/school_calendar/tests.py
git add -A -- "apps/school_calendar/tests.py"
git commit -q -m "test(school_calendar): add unit tests" --no-verify 2>/dev/null || true

# [228/357] apps/students/__init__.py
git add -A -- "apps/students/__init__.py"
git commit -q -m "chore(students): add package __init__" --no-verify 2>/dev/null || true

# [229/357] apps/students/apps.py
git add -A -- "apps/students/apps.py"
git commit -q -m "feat(students): register AppConfig with proper label and name" --no-verify 2>/dev/null || true

# [230/357] apps/students/models.py
git add -A -- "apps/students/models.py"
git commit -q -m "feat(students): add models" --no-verify 2>/dev/null || true

# [231/357] apps/students/migrations/__init__.py
git add -A -- "apps/students/migrations/__init__.py"
git commit -q -m "chore(students): add migrations package init" --no-verify 2>/dev/null || true

# [232/357] apps/students/migrations/0001_initial.py
git add -A -- "apps/students/migrations/0001_initial.py"
git commit -q -m "feat(students): add migration 0001_initial.py" --no-verify 2>/dev/null || true

# [233/357] apps/students/admin.py
git add -A -- "apps/students/admin.py"
git commit -q -m "feat(students): register models with Django admin (list_display, filters, inlines)" --no-verify 2>/dev/null || true

# [234/357] apps/students/forms.py
git add -A -- "apps/students/forms.py"
git commit -q -m "feat(students): add forms with crispy-forms helpers" --no-verify 2>/dev/null || true

# [235/357] apps/students/services/__init__.py
git add -A -- "apps/students/services/__init__.py"
git commit -q -m "chore(students): add services package init" --no-verify 2>/dev/null || true

# [236/357] apps/students/urls.py
git add -A -- "apps/students/urls.py"
git commit -q -m "feat(students): wire up app URL routing" --no-verify 2>/dev/null || true

# [237/357] apps/students/views.py
git add -A -- "apps/students/views.py"
git commit -q -m "feat(students): add class-based views (ListView, CreateView, etc.)" --no-verify 2>/dev/null || true

# [238/357] apps/students/tests.py
git add -A -- "apps/students/tests.py"
git commit -q -m "test(students): add unit tests" --no-verify 2>/dev/null || true

# [239/357] apps/syllabus/__init__.py
git add -A -- "apps/syllabus/__init__.py"
git commit -q -m "chore(syllabus): add package __init__" --no-verify 2>/dev/null || true

# [240/357] apps/syllabus/apps.py
git add -A -- "apps/syllabus/apps.py"
git commit -q -m "feat(syllabus): register AppConfig with proper label and name" --no-verify 2>/dev/null || true

# [241/357] apps/syllabus/models.py
git add -A -- "apps/syllabus/models.py"
git commit -q -m "feat(syllabus): add models" --no-verify 2>/dev/null || true

# [242/357] apps/syllabus/migrations/__init__.py
git add -A -- "apps/syllabus/migrations/__init__.py"
git commit -q -m "chore(syllabus): add migrations package init" --no-verify 2>/dev/null || true

# [243/357] apps/syllabus/migrations/0001_initial.py
git add -A -- "apps/syllabus/migrations/0001_initial.py"
git commit -q -m "feat(syllabus): add migration 0001_initial.py" --no-verify 2>/dev/null || true

# [244/357] apps/syllabus/admin.py
git add -A -- "apps/syllabus/admin.py"
git commit -q -m "feat(syllabus): register models with Django admin (list_display, filters, inlines)" --no-verify 2>/dev/null || true

# [245/357] apps/syllabus/forms.py
git add -A -- "apps/syllabus/forms.py"
git commit -q -m "feat(syllabus): add forms with crispy-forms helpers" --no-verify 2>/dev/null || true

# [246/357] apps/syllabus/services/__init__.py
git add -A -- "apps/syllabus/services/__init__.py"
git commit -q -m "chore(syllabus): add services package init" --no-verify 2>/dev/null || true

# [247/357] apps/syllabus/urls.py
git add -A -- "apps/syllabus/urls.py"
git commit -q -m "feat(syllabus): wire up app URL routing" --no-verify 2>/dev/null || true

# [248/357] apps/syllabus/views.py
git add -A -- "apps/syllabus/views.py"
git commit -q -m "feat(syllabus): add class-based views (ListView, CreateView, etc.)" --no-verify 2>/dev/null || true

# [249/357] apps/syllabus/tests.py
git add -A -- "apps/syllabus/tests.py"
git commit -q -m "test(syllabus): add unit tests" --no-verify 2>/dev/null || true

# [250/357] apps/teachers/__init__.py
git add -A -- "apps/teachers/__init__.py"
git commit -q -m "chore(teachers): add package __init__" --no-verify 2>/dev/null || true

# [251/357] apps/teachers/apps.py
git add -A -- "apps/teachers/apps.py"
git commit -q -m "feat(teachers): register AppConfig with proper label and name" --no-verify 2>/dev/null || true

# [252/357] apps/teachers/models.py
git add -A -- "apps/teachers/models.py"
git commit -q -m "feat(teachers): add models" --no-verify 2>/dev/null || true

# [253/357] apps/teachers/migrations/__init__.py
git add -A -- "apps/teachers/migrations/__init__.py"
git commit -q -m "chore(teachers): add migrations package init" --no-verify 2>/dev/null || true

# [254/357] apps/teachers/migrations/0001_initial.py
git add -A -- "apps/teachers/migrations/0001_initial.py"
git commit -q -m "feat(teachers): add migration 0001_initial.py" --no-verify 2>/dev/null || true

# [255/357] apps/teachers/admin.py
git add -A -- "apps/teachers/admin.py"
git commit -q -m "feat(teachers): register models with Django admin (list_display, filters, inlines)" --no-verify 2>/dev/null || true

# [256/357] apps/teachers/forms.py
git add -A -- "apps/teachers/forms.py"
git commit -q -m "feat(teachers): add forms with crispy-forms helpers" --no-verify 2>/dev/null || true

# [257/357] apps/teachers/services/__init__.py
git add -A -- "apps/teachers/services/__init__.py"
git commit -q -m "chore(teachers): add services package init" --no-verify 2>/dev/null || true

# [258/357] apps/teachers/urls.py
git add -A -- "apps/teachers/urls.py"
git commit -q -m "feat(teachers): wire up app URL routing" --no-verify 2>/dev/null || true

# [259/357] apps/teachers/views.py
git add -A -- "apps/teachers/views.py"
git commit -q -m "feat(teachers): add class-based views (ListView, CreateView, etc.)" --no-verify 2>/dev/null || true

# [260/357] apps/teachers/tests.py
git add -A -- "apps/teachers/tests.py"
git commit -q -m "test(teachers): add unit tests" --no-verify 2>/dev/null || true

# [261/357] templates/includes/breadcrumbs.html
git add -A -- "templates/includes/breadcrumbs.html"
git commit -q -m "feat(includes): add template 'breadcrumbs'" --no-verify 2>/dev/null || true

# [262/357] templates/includes/messages.html
git add -A -- "templates/includes/messages.html"
git commit -q -m "feat(includes): add template 'messages'" --no-verify 2>/dev/null || true

# [263/357] templates/includes/navbar.html
git add -A -- "templates/includes/navbar.html"
git commit -q -m "feat(includes): add template 'navbar'" --no-verify 2>/dev/null || true

# [264/357] templates/includes/sidebar.html
git add -A -- "templates/includes/sidebar.html"
git commit -q -m "feat(includes): add template 'sidebar'" --no-verify 2>/dev/null || true

# [265/357] templates/base.html
git add -A -- "templates/base.html"
git commit -q -m "feat(templates): add base layout with sidebar, topbar, dark mode" --no-verify 2>/dev/null || true

# [266/357] templates/landing.html
git add -A -- "templates/landing.html"
git commit -q -m "feat(templates): add templates/landing.html" --no-verify 2>/dev/null || true

# [267/357] templates/registration/login.html
git add -A -- "templates/registration/login.html"
git commit -q -m "feat(registration): add template 'login'" --no-verify 2>/dev/null || true

# [268/357] templates/registration/password_change.html
git add -A -- "templates/registration/password_change.html"
git commit -q -m "feat(registration): add template 'password_change'" --no-verify 2>/dev/null || true

# [269/357] templates/registration/password_change_done.html
git add -A -- "templates/registration/password_change_done.html"
git commit -q -m "feat(registration): add template 'password_change_done'" --no-verify 2>/dev/null || true

# [270/357] templates/activities/activity_detail.html
git add -A -- "templates/activities/activity_detail.html"
git commit -q -m "feat(activities): add template 'activity_detail'" --no-verify 2>/dev/null || true

# [271/357] templates/activities/activity_form.html
git add -A -- "templates/activities/activity_form.html"
git commit -q -m "feat(activities): add template 'activity_form'" --no-verify 2>/dev/null || true

# [272/357] templates/activities/activity_list.html
git add -A -- "templates/activities/activity_list.html"
git commit -q -m "feat(activities): add template 'activity_list'" --no-verify 2>/dev/null || true

# [273/357] templates/admissions/application_detail.html
git add -A -- "templates/admissions/application_detail.html"
git commit -q -m "feat(admissions): add template 'application_detail'" --no-verify 2>/dev/null || true

# [274/357] templates/admissions/application_form.html
git add -A -- "templates/admissions/application_form.html"
git commit -q -m "feat(admissions): add template 'application_form'" --no-verify 2>/dev/null || true

# [275/357] templates/admissions/application_list.html
git add -A -- "templates/admissions/application_list.html"
git commit -q -m "feat(admissions): add template 'application_list'" --no-verify 2>/dev/null || true

# [276/357] templates/announcements/detail.html
git add -A -- "templates/announcements/detail.html"
git commit -q -m "feat(announcements): add template 'detail'" --no-verify 2>/dev/null || true

# [277/357] templates/announcements/form.html
git add -A -- "templates/announcements/form.html"
git commit -q -m "feat(announcements): add template 'form'" --no-verify 2>/dev/null || true

# [278/357] templates/announcements/list.html
git add -A -- "templates/announcements/list.html"
git commit -q -m "feat(announcements): add template 'list'" --no-verify 2>/dev/null || true

# [279/357] templates/attendance/mark.html
git add -A -- "templates/attendance/mark.html"
git commit -q -m "feat(attendance): add template 'mark'" --no-verify 2>/dev/null || true

# [280/357] templates/attendance/report.html
git add -A -- "templates/attendance/report.html"
git commit -q -m "feat(attendance): add template 'report'" --no-verify 2>/dev/null || true

# [281/357] templates/audit_logs/log_list.html
git add -A -- "templates/audit_logs/log_list.html"
git commit -q -m "feat(audit_logs): add template 'log_list'" --no-verify 2>/dev/null || true

# [282/357] templates/common/academic_year_detail.html
git add -A -- "templates/common/academic_year_detail.html"
git commit -q -m "feat(common): add template 'academic_year_detail'" --no-verify 2>/dev/null || true

# [283/357] templates/common/academic_year_form.html
git add -A -- "templates/common/academic_year_form.html"
git commit -q -m "feat(common): add template 'academic_year_form'" --no-verify 2>/dev/null || true

# [284/357] templates/common/academic_year_list.html
git add -A -- "templates/common/academic_year_list.html"
git commit -q -m "feat(common): add template 'academic_year_list'" --no-verify 2>/dev/null || true

# [285/357] templates/common/class_form.html
git add -A -- "templates/common/class_form.html"
git commit -q -m "feat(common): add template 'class_form'" --no-verify 2>/dev/null || true

# [286/357] templates/common/class_list.html
git add -A -- "templates/common/class_list.html"
git commit -q -m "feat(common): add template 'class_list'" --no-verify 2>/dev/null || true

# [287/357] templates/common/search_results.html
git add -A -- "templates/common/search_results.html"
git commit -q -m "feat(common): add template 'search_results'" --no-verify 2>/dev/null || true

# [288/357] templates/common/subject_form.html
git add -A -- "templates/common/subject_form.html"
git commit -q -m "feat(common): add template 'subject_form'" --no-verify 2>/dev/null || true

# [289/357] templates/common/subject_list.html
git add -A -- "templates/common/subject_list.html"
git commit -q -m "feat(common): add template 'subject_list'" --no-verify 2>/dev/null || true

# [290/357] templates/dashboard/home.html
git add -A -- "templates/dashboard/home.html"
git commit -q -m "feat(dashboard): add template 'home'" --no-verify 2>/dev/null || true

# [291/357] templates/datesheets/datesheet_detail.html
git add -A -- "templates/datesheets/datesheet_detail.html"
git commit -q -m "feat(datesheets): add template 'datesheet_detail'" --no-verify 2>/dev/null || true

# [292/357] templates/datesheets/datesheet_form.html
git add -A -- "templates/datesheets/datesheet_form.html"
git commit -q -m "feat(datesheets): add template 'datesheet_form'" --no-verify 2>/dev/null || true

# [293/357] templates/datesheets/datesheet_list.html
git add -A -- "templates/datesheets/datesheet_list.html"
git commit -q -m "feat(datesheets): add template 'datesheet_list'" --no-verify 2>/dev/null || true

# [294/357] templates/diary/entry_detail.html
git add -A -- "templates/diary/entry_detail.html"
git commit -q -m "feat(diary): add template 'entry_detail'" --no-verify 2>/dev/null || true

# [295/357] templates/diary/entry_form.html
git add -A -- "templates/diary/entry_form.html"
git commit -q -m "feat(diary): add template 'entry_form'" --no-verify 2>/dev/null || true

# [296/357] templates/diary/entry_list.html
git add -A -- "templates/diary/entry_list.html"
git commit -q -m "feat(diary): add template 'entry_list'" --no-verify 2>/dev/null || true

# [297/357] templates/examinations/classtest_detail.html
git add -A -- "templates/examinations/classtest_detail.html"
git commit -q -m "feat(examinations): add template 'classtest_detail'" --no-verify 2>/dev/null || true

# [298/357] templates/examinations/classtest_form.html
git add -A -- "templates/examinations/classtest_form.html"
git commit -q -m "feat(examinations): add template 'classtest_form'" --no-verify 2>/dev/null || true

# [299/357] templates/examinations/classtest_list.html
git add -A -- "templates/examinations/classtest_list.html"
git commit -q -m "feat(examinations): add template 'classtest_list'" --no-verify 2>/dev/null || true

# [300/357] templates/examinations/classtest_results.html
git add -A -- "templates/examinations/classtest_results.html"
git commit -q -m "feat(examinations): add template 'classtest_results'" --no-verify 2>/dev/null || true

# [301/357] templates/examinations/exam_detail.html
git add -A -- "templates/examinations/exam_detail.html"
git commit -q -m "feat(examinations): add template 'exam_detail'" --no-verify 2>/dev/null || true

# [302/357] templates/examinations/exam_form.html
git add -A -- "templates/examinations/exam_form.html"
git commit -q -m "feat(examinations): add template 'exam_form'" --no-verify 2>/dev/null || true

# [303/357] templates/examinations/exam_list.html
git add -A -- "templates/examinations/exam_list.html"
git commit -q -m "feat(examinations): add template 'exam_list'" --no-verify 2>/dev/null || true

# [304/357] templates/examinations/report_card.html
git add -A -- "templates/examinations/report_card.html"
git commit -q -m "feat(examinations): add template 'report_card'" --no-verify 2>/dev/null || true

# [305/357] templates/examinations/surprisetest_form.html
git add -A -- "templates/examinations/surprisetest_form.html"
git commit -q -m "feat(examinations): add template 'surprisetest_form'" --no-verify 2>/dev/null || true

# [306/357] templates/examinations/surprisetest_list.html
git add -A -- "templates/examinations/surprisetest_list.html"
git commit -q -m "feat(examinations): add template 'surprisetest_list'" --no-verify 2>/dev/null || true

# [307/357] templates/examinations/termresult_list.html
git add -A -- "templates/examinations/termresult_list.html"
git commit -q -m "feat(examinations): add template 'termresult_list'" --no-verify 2>/dev/null || true

# [308/357] templates/fees/challan_detail.html
git add -A -- "templates/fees/challan_detail.html"
git commit -q -m "feat(fees): add template 'challan_detail'" --no-verify 2>/dev/null || true

# [309/357] templates/fees/challan_generate.html
git add -A -- "templates/fees/challan_generate.html"
git commit -q -m "feat(fees): add template 'challan_generate'" --no-verify 2>/dev/null || true

# [310/357] templates/fees/challan_list.html
git add -A -- "templates/fees/challan_list.html"
git commit -q -m "feat(fees): add template 'challan_list'" --no-verify 2>/dev/null || true

# [311/357] templates/fees/challan_print.html
git add -A -- "templates/fees/challan_print.html"
git commit -q -m "feat(fees): add template 'challan_print'" --no-verify 2>/dev/null || true

# [312/357] templates/fees/defaulter_report.html
git add -A -- "templates/fees/defaulter_report.html"
git commit -q -m "feat(fees): add template 'defaulter_report'" --no-verify 2>/dev/null || true

# [313/357] templates/fees/fee_type_form.html
git add -A -- "templates/fees/fee_type_form.html"
git commit -q -m "feat(fees): add template 'fee_type_form'" --no-verify 2>/dev/null || true

# [314/357] templates/fees/fee_type_list.html
git add -A -- "templates/fees/fee_type_list.html"
git commit -q -m "feat(fees): add template 'fee_type_list'" --no-verify 2>/dev/null || true

# [315/357] templates/fees/payment_confirm.html
git add -A -- "templates/fees/payment_confirm.html"
git commit -q -m "feat(fees): add template 'payment_confirm'" --no-verify 2>/dev/null || true

# [316/357] templates/fees/payment_list.html
git add -A -- "templates/fees/payment_list.html"
git commit -q -m "feat(fees): add template 'payment_list'" --no-verify 2>/dev/null || true

# [317/357] templates/fees/payment_lookup.html
git add -A -- "templates/fees/payment_lookup.html"
git commit -q -m "feat(fees): add template 'payment_lookup'" --no-verify 2>/dev/null || true

# [318/357] templates/fees/receipt_print.html
git add -A -- "templates/fees/receipt_print.html"
git commit -q -m "feat(fees): add template 'receipt_print'" --no-verify 2>/dev/null || true

# [319/357] templates/fees/structure_form.html
git add -A -- "templates/fees/structure_form.html"
git commit -q -m "feat(fees): add template 'structure_form'" --no-verify 2>/dev/null || true

# [320/357] templates/fees/structure_list.html
git add -A -- "templates/fees/structure_list.html"
git commit -q -m "feat(fees): add template 'structure_list'" --no-verify 2>/dev/null || true

# [321/357] templates/homework/homework_detail.html
git add -A -- "templates/homework/homework_detail.html"
git commit -q -m "feat(homework): add template 'homework_detail'" --no-verify 2>/dev/null || true

# [322/357] templates/homework/homework_form.html
git add -A -- "templates/homework/homework_form.html"
git commit -q -m "feat(homework): add template 'homework_form'" --no-verify 2>/dev/null || true

# [323/357] templates/homework/homework_list.html
git add -A -- "templates/homework/homework_list.html"
git commit -q -m "feat(homework): add template 'homework_list'" --no-verify 2>/dev/null || true

# [324/357] templates/notifications/list.html
git add -A -- "templates/notifications/list.html"
git commit -q -m "feat(notifications): add template 'list'" --no-verify 2>/dev/null || true

# [325/357] templates/parents/parent_detail.html
git add -A -- "templates/parents/parent_detail.html"
git commit -q -m "feat(parents): add template 'parent_detail'" --no-verify 2>/dev/null || true

# [326/357] templates/parents/parent_form.html
git add -A -- "templates/parents/parent_form.html"
git commit -q -m "feat(parents): add template 'parent_form'" --no-verify 2>/dev/null || true

# [327/357] templates/parents/parent_list.html
git add -A -- "templates/parents/parent_list.html"
git commit -q -m "feat(parents): add template 'parent_list'" --no-verify 2>/dev/null || true

# [328/357] templates/payroll/payroll_detail.html
git add -A -- "templates/payroll/payroll_detail.html"
git commit -q -m "feat(payroll): add template 'payroll_detail'" --no-verify 2>/dev/null || true

# [329/357] templates/payroll/payroll_form.html
git add -A -- "templates/payroll/payroll_form.html"
git commit -q -m "feat(payroll): add template 'payroll_form'" --no-verify 2>/dev/null || true

# [330/357] templates/payroll/payroll_list.html
git add -A -- "templates/payroll/payroll_list.html"
git commit -q -m "feat(payroll): add template 'payroll_list'" --no-verify 2>/dev/null || true

# [331/357] templates/payroll/payroll_pay.html
git add -A -- "templates/payroll/payroll_pay.html"
git commit -q -m "feat(payroll): add template 'payroll_pay'" --no-verify 2>/dev/null || true

# [332/357] templates/payroll/salary_slip.html
git add -A -- "templates/payroll/salary_slip.html"
git commit -q -m "feat(payroll): add template 'salary_slip'" --no-verify 2>/dev/null || true

# [333/357] templates/portal/parent_home.html
git add -A -- "templates/portal/parent_home.html"
git commit -q -m "feat(portal): add template 'parent_home'" --no-verify 2>/dev/null || true

# [334/357] templates/portal/student_home.html
git add -A -- "templates/portal/student_home.html"
git commit -q -m "feat(portal): add template 'student_home'" --no-verify 2>/dev/null || true

# [335/357] templates/portal/teacher_home.html
git add -A -- "templates/portal/teacher_home.html"
git commit -q -m "feat(portal): add template 'teacher_home'" --no-verify 2>/dev/null || true

# [336/357] templates/reports/attendance_report.html
git add -A -- "templates/reports/attendance_report.html"
git commit -q -m "feat(reports): add template 'attendance_report'" --no-verify 2>/dev/null || true

# [337/357] templates/reports/defaulter_pdf.html
git add -A -- "templates/reports/defaulter_pdf.html"
git commit -q -m "feat(reports): add template 'defaulter_pdf'" --no-verify 2>/dev/null || true

# [338/357] templates/reports/fee_report.html
git add -A -- "templates/reports/fee_report.html"
git commit -q -m "feat(reports): add template 'fee_report'" --no-verify 2>/dev/null || true

# [339/357] templates/reports/index.html
git add -A -- "templates/reports/index.html"
git commit -q -m "feat(reports): add template 'index'" --no-verify 2>/dev/null || true

# [340/357] templates/reports/payroll_report.html
git add -A -- "templates/reports/payroll_report.html"
git commit -q -m "feat(reports): add template 'payroll_report'" --no-verify 2>/dev/null || true

# [341/357] templates/reports/student_report.html
git add -A -- "templates/reports/student_report.html"
git commit -q -m "feat(reports): add template 'student_report'" --no-verify 2>/dev/null || true

# [342/357] templates/school_calendar/event_form.html
git add -A -- "templates/school_calendar/event_form.html"
git commit -q -m "feat(school_calendar): add template 'event_form'" --no-verify 2>/dev/null || true

# [343/357] templates/school_calendar/event_list.html
git add -A -- "templates/school_calendar/event_list.html"
git commit -q -m "feat(school_calendar): add template 'event_list'" --no-verify 2>/dev/null || true

# [344/357] templates/students/student_detail.html
git add -A -- "templates/students/student_detail.html"
git commit -q -m "feat(students): add template 'student_detail'" --no-verify 2>/dev/null || true

# [345/357] templates/students/student_form.html
git add -A -- "templates/students/student_form.html"
git commit -q -m "feat(students): add template 'student_form'" --no-verify 2>/dev/null || true

# [346/357] templates/students/student_list.html
git add -A -- "templates/students/student_list.html"
git commit -q -m "feat(students): add template 'student_list'" --no-verify 2>/dev/null || true

# [347/357] templates/syllabus/lecture_form.html
git add -A -- "templates/syllabus/lecture_form.html"
git commit -q -m "feat(syllabus): add template 'lecture_form'" --no-verify 2>/dev/null || true

# [348/357] templates/syllabus/lecture_list.html
git add -A -- "templates/syllabus/lecture_list.html"
git commit -q -m "feat(syllabus): add template 'lecture_list'" --no-verify 2>/dev/null || true

# [349/357] templates/syllabus/syllabus_detail.html
git add -A -- "templates/syllabus/syllabus_detail.html"
git commit -q -m "feat(syllabus): add template 'syllabus_detail'" --no-verify 2>/dev/null || true

# [350/357] templates/syllabus/syllabus_form.html
git add -A -- "templates/syllabus/syllabus_form.html"
git commit -q -m "feat(syllabus): add template 'syllabus_form'" --no-verify 2>/dev/null || true

# [351/357] templates/syllabus/syllabus_list.html
git add -A -- "templates/syllabus/syllabus_list.html"
git commit -q -m "feat(syllabus): add template 'syllabus_list'" --no-verify 2>/dev/null || true

# [352/357] templates/syllabus/topic_form.html
git add -A -- "templates/syllabus/topic_form.html"
git commit -q -m "feat(syllabus): add template 'topic_form'" --no-verify 2>/dev/null || true

# [353/357] templates/teachers/teacher_bank_info.html
git add -A -- "templates/teachers/teacher_bank_info.html"
git commit -q -m "feat(teachers): add template 'teacher_bank_info'" --no-verify 2>/dev/null || true

# [354/357] templates/teachers/teacher_detail.html
git add -A -- "templates/teachers/teacher_detail.html"
git commit -q -m "feat(teachers): add template 'teacher_detail'" --no-verify 2>/dev/null || true

# [355/357] templates/teachers/teacher_form.html
git add -A -- "templates/teachers/teacher_form.html"
git commit -q -m "feat(teachers): add template 'teacher_form'" --no-verify 2>/dev/null || true

# [356/357] templates/teachers/teacher_list.html
git add -A -- "templates/teachers/teacher_list.html"
git commit -q -m "feat(teachers): add template 'teacher_list'" --no-verify 2>/dev/null || true

# [357/357] scripts/commit_all.sh
git add -A -- "scripts/commit_all.sh"
git commit -q -m "chore(scripts): add commit_all.sh" --no-verify 2>/dev/null || true

echo "✓ Created 357 commits"
echo "Latest commit:"
git log --oneline -1
echo ""
echo "Total commits:"
git rev-list --count HEAD
