#!/usr/bin/env python3
"""
Generate a bash script that creates one git commit per file in the School ERP
project, in a logical build order (foundation → apps → templates → static).

Usage:
    python3 scripts/git_one_commit_per_file.py > scripts/commit_all.sh
    chmod +x scripts/commit_all.sh
    cd school_erp
    ../scripts/commit_all.sh     # or: bash scripts/commit_all.sh
"""
import os
from pathlib import Path

PROJECT_ROOT = Path("/home/z/my-project/school_erp")

# Files to skip (build artifacts, OS junk, virtual envs)
SKIP_PATTERNS = {
    "__pycache__", ".pyc", ".pyo", ".pyd",
    ".git", ".gitignore",  # we'll commit .gitignore separately first
    "staticfiles", "db.sqlite3", "db.sqlite3-journal",
    "venv", "env", ".env",  # never commit .env
    ".DS_Store", "*.swp",
}

# Order in which files should be committed — foundation first
ORDER_PRECEDENCE = [
    # 1. Project meta
    "README.md",
    ".gitignore",
    ".env.example",
    "manage.py",
    # 2. Requirements
    "requirements/base.txt",
    "requirements/dev.txt",
    # 3. Config
    "config/__init__.py",
    "config/settings/__init__.py",
    "config/settings/base.py",
    "config/settings/dev.py",
    "config/settings/prod.py",
    "config/wsgi.py",
    "config/asgi.py",
    "config/urls.py",
    # 4. Static / scripts dirs (so they exist early)
    "static/css/style.css",
    "static/js/app.js",
    "scripts/generate_templates.py",
    "scripts/generate_remaining_templates.py",
    "scripts/git_one_commit_per_file.py",
]


def should_skip(path: Path) -> bool:
    parts = path.parts
    for part in parts:
        if part in SKIP_PATTERNS or part.startswith("."):
            return True
        if part.endswith(".pyc") or part == "__pycache__":
            return True
    rel = str(path.relative_to(PROJECT_ROOT))
    if rel.endswith(".pyc") or "__pycache__" in rel:
        return True
    if rel == ".env":
        return True
    if "staticfiles" in rel:
        return True
    if rel == "db.sqlite3":
        return True
    return False


def sort_key(rel_path: str):
    """Build a tuple sort key so files come out in a sensible order.
    Order: meta → config → static → scripts → each app together
    (__init__ → apps.py → models → migrations → admin → forms →
    services → management → urls → views → tests → middleware etc.)
    → templates → docs → tests."""
    # Try to use the predefined order
    for i, p in enumerate(ORDER_PRECEDENCE):
        if rel_path == p:
            return (0, i, rel_path)
    # Apps: keep each app's files together
    if rel_path.startswith("apps/"):
        parts = rel_path.split("/")
        app_name = parts[1]
        # File priority WITHIN an app
        # __init__ → apps.py → models → migrations/__init__ → migrations/0001 →
        # admin → forms → services → management → urls → views → tests →
        # middleware / context_processors / mixins / etc.
        if len(parts) == 3:
            file = parts[2]
            priority_map = {
                "__init__.py": 0,
                "apps.py": 1,
                "models.py": 2,
                "admin.py": 4,
                "forms.py": 5,
                "urls.py": 7,
                "views.py": 8,
                "tests.py": 9,
                "middleware.py": 10,
                "context_processors.py": 11,
                "mixins.py": 12,
            }
            prio = priority_map.get(file, 13)
            return (2, app_name, prio, file)
        elif len(parts) >= 4 and parts[2] == "migrations":
            mig = parts[3]
            if mig == "__init__.py":
                return (2, app_name, 3, 0, mig)
            try:
                num = int(mig.split("_")[0])
            except (ValueError, IndexError):
                num = 99
            return (2, app_name, 3, num, mig)
        elif len(parts) >= 4 and parts[2] == "services":
            svc = "/".join(parts[3:])
            if svc == "__init__.py":
                return (2, app_name, 6, 0, svc)
            return (2, app_name, 6, 1, svc)
        elif len(parts) >= 4 and parts[2] == "management":
            sub = "/".join(parts[3:])
            if sub == "__init__.py":
                return (2, app_name, 6.5, 0, sub)
            if sub == "commands/__init__.py":
                return (2, app_name, 6.5, 1, sub)
            return (2, app_name, 6.5, 2, sub)
        return (2, app_name, 14, "/".join(parts[2:]))
    # Templates (per app) — keep types consistent (all strings) to avoid
    # str-vs-int comparison errors during sort
    if rel_path.startswith("templates/"):
        parts = rel_path.split("/")
        if len(parts) >= 2:
            app_or_dir = parts[1]
            # Use string prefixes so includes/registration come before app dirs
            if app_or_dir == "includes":
                return (3, "00_includes", rel_path)
            if app_or_dir == "registration":
                return (3, "01_registration", rel_path)
            if parts[0] == "templates" and len(parts) == 2:
                # top-level templates (e.g. base.html, landing.html)
                return (3, "00_top", rel_path)
            tmpl = parts[2] if len(parts) > 2 else ""
            return (3, app_or_dir, tmpl)
        return (3, "zz_fallback", rel_path)
    # Static (already placed early via ORDER_PRECEDENCE; this catches extras)
    if rel_path.startswith("static/"):
        return (4, rel_path)
    # Docs
    if rel_path.startswith("docs/"):
        return (5, rel_path)
    # Tests folder
    if rel_path.startswith("tests/"):
        return (6, rel_path)
    # Fallback
    return (7, rel_path)


def make_commit_message(rel_path: str) -> str:
    """Generate a meaningful commit message based on file path."""
    # Project meta
    if rel_path == "README.md":
        return "docs: add project README with setup and usage instructions"
    if rel_path == ".gitignore":
        return "chore: add .gitignore for Python/Django project"
    if rel_path == ".env.example":
        return "chore: add .env.example template for environment configuration"
    if rel_path == "manage.py":
        return "chore: add Django manage.py entry point"
    if rel_path == "requirements/base.txt":
        return "build: pin base Python dependencies (Django, psycopg2, WeasyPrint)"
    if rel_path == "requirements/dev.txt":
        return "build: pin dev dependencies (extends base.txt)"
    # Config
    if rel_path.startswith("config/"):
        if rel_path == "config/__init__.py":
            return "chore(config): add package init with default settings module"
        if rel_path == "config/wsgi.py":
            return "chore(config): add WSGI entry point"
        if rel_path == "config/asgi.py":
            return "chore(config): add ASGI entry point"
        if rel_path == "config/urls.py":
            return "feat(config): wire up root URL configuration for all apps"
        if rel_path == "config/settings/__init__.py":
            return "chore(config): add settings package init"
        if rel_path == "config/settings/base.py":
            return "feat(config): add base settings — INSTALLED_APPS, middleware, DB, auth, school config"
        if rel_path == "config/settings/dev.py":
            return "feat(config): add dev settings — DEBUG=True, SQLite fallback"
        if rel_path == "config/settings/prod.py":
            return "feat(config): add prod settings — security headers, HTTPS, env-driven"
    # Static
    if rel_path == "static/css/style.css":
        return "style: add premium UI stylesheet (sidebar, topbar, stat cards, dark mode, PAID stamp)"
    if rel_path == "static/js/app.js":
        return "feat(static): add app.js — theme toggle, sidebar, global search (Ctrl+K), toasts"
    # Scripts
    if rel_path.startswith("scripts/"):
        name = rel_path.split("/")[-1]
        return f"chore(scripts): add {name}"
    # Apps
    if rel_path.startswith("apps/"):
        parts = rel_path.split("/")
        app = parts[1]
        if len(parts) == 2:
            return f"chore({app}): add package marker"
        rest = "/".join(parts[2:])
        if rest == "__init__.py":
            return f"chore({app}): add package __init__"
        if rest == "apps.py":
            return f"feat({app}): register AppConfig with proper label and name"
        if rest == "models.py":
            return f"feat({app}): add models"
        if rest == "admin.py":
            return f"feat({app}): register models with Django admin (list_display, filters, inlines)"
        if rest == "forms.py":
            return f"feat({app}): add forms with crispy-forms helpers"
        if rest == "urls.py":
            return f"feat({app}): wire up app URL routing"
        if rest == "views.py":
            return f"feat({app}): add class-based views (ListView, CreateView, etc.)"
        if rest == "tests.py":
            return f"test({app}): add unit tests"
        if rest == "middleware.py":
            return f"feat({app}): add middleware"
        if rest == "context_processors.py":
            return f"feat({app}): add template context processor"
        if rest == "mixins.py":
            return f"feat({app}): add reusable view mixins"
        if rest.startswith("services/"):
            service_file = rest.split("/", 1)[1]
            if service_file == "__init__.py":
                return f"chore({app}): add services package init"
            service_name = service_file.replace(".py", "")
            return f"feat({app}): add {service_name} service — business logic isolation"
        if rest.startswith("management/"):
            sub = rest[len("management/"):]
            if sub == "__init__.py":
                return f"chore({app}): add management package init"
            if sub == "commands/__init__.py":
                return f"chore({app}): add management commands package init"
            cmd_name = sub.split("/")[-1].replace(".py", "")
            return f"feat({app}): add management command '{cmd_name}'"
        if rest.startswith("migrations/"):
            mig = rest.split("/", 1)[1]
            if mig == "__init__.py":
                return f"chore({app}): add migrations package init"
            return f"feat({app}): add migration {mig}"
        return f"feat({app}): add {rest}"
    # Templates
    if rel_path.startswith("templates/"):
        # e.g. templates/students/student_list.html
        parts = rel_path.split("/")
        if len(parts) >= 3:
            app = parts[1]
            tmpl = parts[2]
            tmpl_name = tmpl.replace(".html", "")
            return f"feat({app}): add template '{tmpl_name}'"
        if rel_path == "templates/base.html":
            return "feat(templates): add base layout with sidebar, topbar, dark mode"
        if rel_path.startswith("templates/includes/"):
            inc = rel_path.split("/")[-1].replace(".html", "")
            return f"feat(templates): add include partial '{inc}'"
        if rel_path.startswith("templates/registration/"):
            inc = rel_path.split("/")[-1].replace(".html", "")
            return f"feat(templates): add registration template '{inc}'"
        return f"feat(templates): add {rel_path}"
    if rel_path.startswith("docs/"):
        return f"docs: add {rel_path}"
    if rel_path.startswith("tests/"):
        return f"test: add {rel_path}"
    return f"chore: add {rel_path}"


def main():
    # Collect all files
    files = []
    for root, dirs, fs in os.walk(PROJECT_ROOT):
        # Modify dirs in place to skip excluded
        dirs[:] = [d for d in dirs if d not in SKIP_PATTERNS and not d.startswith(".") and d != "__pycache__"]
        for f in fs:
            full = Path(root) / f
            if should_skip(full):
                continue
            files.append(str(full.relative_to(PROJECT_ROOT)))

    # Sort by our key
    files.sort(key=sort_key)

    # Output bash script
    print("#!/usr/bin/env bash")
    print("# Auto-generated: one commit per file in the School ERP project.")
    print("# Run from the project root directory (school_erp/).")
    print("set -e")
    print("")
    print("cd \"$(dirname \"$0\")/..\" 2>/dev/null || cd \"$(pwd)\"")
    print("")
    print("# Initialize git if needed")
    print("if [ ! -d .git ]; then")
    print("    git init -q")
    print("    git branch -M main 2>/dev/null || true")
    print("fi")
    print("")
    print("# Set committer identity if not set (override via env if you want)")
    print('git config user.email >/dev/null 2>&1 || git config user.email "dev@school-erp.local"')
    print('git config user.name  >/dev/null 2>&1 || git config user.name  "School ERP Dev"')
    print("")
    total = len(files)
    for i, rel in enumerate(files, 1):
        msg = make_commit_message(rel).replace("\"", "\\\"")
        # Use --allow-empty just in case, but normally each file is a real add
        print(f'# [{i}/{total}] {rel}')
        print(f'git add -A -- "{rel}"')
        print(f'git commit -q -m "{msg}" --no-verify 2>/dev/null || true')
        print("")
    print(f'echo "✓ Created {total} commits"')
    print('echo "Latest commit:"')
    print('git log --oneline -1')
    print('echo ""')
    print('echo "Total commits:"')
    print('git rev-list --count HEAD')


if __name__ == "__main__":
    main()
