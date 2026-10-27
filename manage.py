#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

# Load .env BEFORE settings are imported, so env vars like DJANGO_SECRET_KEY,
# ALLOWED_HOSTS, and DB_* exist when config.settings.<env> is evaluated.
# In production, real env vars are set by the OS/container — dotenv is a no-op.
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except ImportError:
    pass


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and available "
            "on your PYTHONPATH environment variable? Did you forget to activate "
            "a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
