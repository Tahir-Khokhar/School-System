"""Default to dev settings if DJANGO_SETTINGS_MODULE is unset."""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
