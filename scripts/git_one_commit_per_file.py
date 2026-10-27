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
import shlex
from pathlib import Path

PROJECT_ROOT = Path("/home/z/my-project/school_erp")

# Files/dirs to skip (build artifacts, OS junk, virtual envs)
SKIP_DIRS = {
    "__pycache__", ".git", "staticfiles", "venv", "env",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", "node_modules",
    "htmlcov", ".tox", ".idea", ".vscode",
}
SKIP_FILES = {
    "db.sqlite3", "db.sqlite3-journal", ".env", ".DS_Store",
}
SKIP_EXTS = {".pyc", ".pyo", ".pyd", ".swp", ".sqlite3"}

# Explicit files we DO want even though they start with a dot
ALLOW_DOTFILES = {".gitignore", ".env.example", ".editorconfig", ".flake8"}

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

# Within an app directory, prioritize files in this order
APP_FILE_PRIORITY = {
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


def should_skip(path: Path) -> bool:
    rel = path.relative_to(PROJECT_ROOT)
    parts = rel.parts

    # Allow explicit dotfiles
    if parts and parts[-1] in ALLOW_DOTFILES:
        return False

    for part in parts:
        if part in SKIP_DIRS:
            return True
        # Skip hidden files/dirs, but NOT explicit allow-list
        if part.startswith(".") and part not in ALLOW_DOTFILES:
            return True

    if parts and parts[-1] in SKIP_FILES:
        return True
    if path.suffix in SKIP_EXTS:
        return True
    return False


def sort_key(rel_path: str):
    """Return a sort tuple. Every position must be the same TYPE across all
    returns to avoid `TypeError: '<' not supported between instances of
    'int' and 'str'` when Python compares tuples element-by-element.

    Strategy: pad every return to a 6-tuple:
        (group, subgroup, priority_int, name_str, sub_int, extra_str)

    group     : int  — top-level bucket (0=meta, 1=config, 2=apps,
                       3=templates, 4=static, 5=docs, 6=tests, 7=fallback)
    subgroup  : str  — app name / "00_top" / etc.
    priority  : int  — file-type priority within the bucket
    name      : str  — file/migration name for stable ordering
    sub       : int  — secondary int for migration numbers
    extra     : str  — tiebreaker
    """
    # Fixed precedence list
    for i, p in enumerate(ORDER_PRECEDENCE):
        if rel_path == p:
            return (0, "", i, rel_path, 0, "")

    # Apps
    if rel_path.startswith("apps/"):
        parts = rel_path.split("/")
        app = parts[1] if len(parts) > 1 else ""
        if len(parts) == 2:  # apps/<app>/__init__.py handled below; this is bare dir
            return (2, app, 0, "", 0, "")
        rest = parts[2:]
        if len(rest) == 1:
            file = rest[0]
            prio = APP_FILE_PRIORITY.get(file, 13)
            return (2, app, prio, file, 0, "")
        if rest[0] == "migrations":
            if len(rest) == 2 and rest[1] == "__init__.py":
                return (2, app, 3, "0000_init", 0, "")
            mig = rest[-1]
            try:
                num = int(mig.split("_")[0])
            except (ValueError, IndexError):
                num = 9999
            return (2, app, 3, mig, num, "")
        if rest[0] == "services":
            svc = "/".join(rest[1:])
            return (2, app, 6, svc, 0, "")
        if rest[0] == "management":
            sub = "/".join(rest[1:])
            return (2, app, 7, sub, 0, "")
        return (2, app, 14, "/".join(rest), 0, "")

    # Templates
    if rel_path.startswith("templates/"):
        parts = rel_path.split("/")
        if len(parts) == 2:
            # e.g. templates/base.html, templates/landing.html
            return (3, "00_top", 0, parts[1], 0, "")
        sub = parts[1]
        if sub == "includes":
            return (3, "00_includes", 0, "/".join(parts[2:]), 0, "")
        if sub == "registration":
            return (3, "01_registration", 0, "/".join(parts[2:]), 0, "")
        return (3, sub, 0, "/".join(parts[2:]), 0, "")

    if rel_path.startswith("static/"):
        return (4, "", 0, rel_path, 0, "")
    if rel_path.startswith("docs/"):
        return (5, "", 0, rel_path, 0, "")
    if rel_path.startswith("tests/"):
        return (6, "", 0, rel_path, 0, "")
    return (7, "", 0, rel_path, 0, "")


def make_commit_message(rel_path: str) -> str:
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

    if rel_path.startswith("config/"):
        mapping = {
            "config/__init__.py": "chore(config): add package init with default settings module",
            "config/wsgi.py": "chore(config): add WSGI entry point",
            "config/asgi.py": "chore(config): add ASGI entry point",
            "config/urls.py": "feat(config): wire up root URL configuration for all apps",
            "config/settings/__init__.py": "chore(config): add settings package init",
            "config/settings/base.py": "feat(config): add base settings — INSTALLED_APPS, middleware, DB, auth, school config",
            "config/settings/dev.py": "feat(config): add dev settings — DEBUG=True, SQLite fallback",
            "config/settings/prod.py": "feat(config): add prod settings — security headers, HTTPS, env-driven",
        }
        if rel_path in mapping:
            return mapping[rel_path]

    if rel_path == "static/css/style.css":
        return "style: add premium UI stylesheet (sidebar, topbar, stat cards, dark mode, PAID stamp)"
    if rel_path == "static/js/app.js":
        return "feat(static): add app.js — theme toggle, sidebar, global search (Ctrl+K), toasts"
    if rel_path.startswith("scripts/"):
        return f"chore(scripts): add {rel_path.split('/')[-1]}"

    if rel_path.startswith("apps/"):
        parts = rel_path.split("/")
        app = parts[1]
        if len(parts) == 2:
            return f"chore({app}): add package marker"
        rest = "/".join(parts[2:])
        exact = {
            "__init__.py": f"chore({app}): add package __init__",
            "apps.py": f"feat({app}): register AppConfig with proper label and name",
            "models.py": f"feat({app}): add models",
            "admin.py": f"feat({app}): register models with Django admin (list_display, filters, inlines)",
            "forms.py": f"feat({app}): add forms with crispy-forms helpers",
            "urls.py": f"feat({app}): wire up app URL routing",
            "views.py": f"feat({app}): add class-based views (ListView, CreateView, etc.)",
            "tests.py": f"test({app}): add unit tests",
            "middleware.py": f"feat({app}): add middleware",
            "context_processors.py": f"feat({app}): add template context processor",
            "mixins.py": f"feat({app}): add reusable view mixins",
        }
        if rest in exact:
            return exact[rest]
        if rest.startswith("services/"):
            sf = rest.split("/", 1)[1]
            if sf == "__init__.py":
                return f"chore({app}): add services package init"
            return f"feat({app}): add {sf.replace('.py', '')} service — business logic isolation"
        if rest.startswith("management/"):
            sub = rest[len("management/"):]
            if sub == "__init__.py":
                return f"chore({app}): add management package init"
            if sub == "commands/__init__.py":
                return f"chore({app}): add management commands package init"
            cmd = sub.split("/")[-1].replace(".py", "")
            return f"feat({app}): add management command '{cmd}'"
        if rest.startswith("migrations/"):
            mig = rest.split("/", 1)[1]
            if mig == "__init__.py":
                return f"chore({app}): add migrations package init"
            return f"feat({app}): add migration {mig}"
        return f"feat({app}): add {rest}"

    if rel_path.startswith("templates/"):
        parts = rel_path.split("/")
        if len(parts) == 2:
            name = parts[1].replace(".html", "")
            if name == "base":
                return "feat(templates): add base layout with sidebar, topbar, dark mode"
            return f"feat(templates): add top-level template '{name}'"
        app = parts[1]
        tmpl = "/".join(parts[2:]).replace(".html", "")
        if app == "includes":
            return f"feat(templates): add include partial '{tmpl}'"
        if app == "registration":
            return f"feat(templates): add registration template '{tmpl}'"
        return f"feat({app}): add template '{tmpl}'"

    if rel_path.startswith("docs/"):
        return f"docs: add {rel_path}"
    if rel_path.startswith("tests/"):
        return f"test: add {rel_path}"
    return f"chore: add {rel_path}"


def bash_quote(s: str) -> str:
    """Safely quote a string for embedding in a bash script."""
    return shlex.quote(s)


def main():
    files = []
    for root, dirs, fs in os.walk(PROJECT_ROOT):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith("."))
        for f in sorted(fs):
            full = Path(root) / f
            if should_skip(full):
                continue
            files.append(str(full.relative_to(PROJECT_ROOT)))

    files.sort(key=sort_key)

    print("#!/usr/bin/env bash")
    print("# Auto-generated: one commit per file in the School ERP project.")
    print("# Run from the project root directory (school_erp/).")
    print("set -euo pipefail")
    print("")
    print('cd "$(dirname "$0")/.." 2>/dev/null || cd "$(pwd)"')
    print("")
    print("if [ ! -d .git ]; then")
    print("    git init -q")
    print("    git branch -M main 2>/dev/null || true")
    print("fi")
    print("")
    print('# Set committer identity if not set (override via env if you want)')
    print('git config user.email >/dev/null 2>&1 || git config user.email "dev@school-erp.local"')
    print('git config user.name  >/dev/null 2>&1 || git config user.name  "School ERP Dev"')
    print("")
    total = len(files)
    for i, rel in enumerate(files, 1):
        msg = make_commit_message(rel)
        qrel = bash_quote(rel)
        qmsg = bash_quote(msg)
        print(f"# [{i}/{total}] {rel}")
        print(f"git add -- {qrel}")
        print(f"git commit -q -m {qmsg} --no-verify")
        print("")
    print(f'echo "✓ Created {total} commits"')
    print('echo "Latest commit:"')
    print('git log --oneline -1')
    print('echo ""')
    print('echo "Total commits:"')
    print('git rev-list --count HEAD')


if __name__ == "__main__":
    main()
