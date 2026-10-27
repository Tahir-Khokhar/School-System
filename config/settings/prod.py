"""Production settings — everything comes from environment.

Required env vars (missing ones cause ImproperlyConfigured at import):
    DJANGO_SECRET_KEY        — long random string, never committed
    ALLOWED_HOSTS            — comma-separated hostnames (e.g. "school.example.pk,www.school.example.pk")
    CSRF_TRUSTED_ORIGINS     — comma-separated origins (e.g. "https://school.example.pk")

Optional:
    SECURE_SSL_REDIRECT      — default: true
    SECURE_HSTS_SECONDS      — default: 31536000 (1 year)
    SECURE_HSTS_PRELOAD      — default: false (set true only after submitting to preload list)
"""
from django.core.exceptions import ImproperlyConfigured
from .base import *  # noqa  — also brings in env_bool / env_int / env_list


# ---------------------------------------------------------------------------
# Guards
# ---------------------------------------------------------------------------
DEBUG = False
if env_bool("DJANGO_DEBUG", False):
    raise ImproperlyConfigured(
        "DJANGO_DEBUG must not be set in production settings."
    )

if not ALLOWED_HOSTS:
    raise ImproperlyConfigured(
        "ALLOWED_HOSTS must be set in production (comma-separated hostnames)."
    )

CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")
if not CSRF_TRUSTED_ORIGINS:
    raise ImproperlyConfigured(
        "CSRF_TRUSTED_ORIGINS must be set in production "
        "(comma-separated, e.g. 'https://school.example.pk')."
    )


# ---------------------------------------------------------------------------
# Cookies
# ---------------------------------------------------------------------------
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False  # JS must read this cookie for AJAX CSRF header


# ---------------------------------------------------------------------------
# HTTPS / HSTS
# ---------------------------------------------------------------------------
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)

# Only correct if your reverse proxy sets X-Forwarded-Proto faithfully.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SECURE_HSTS_SECONDS = env_int("SECURE_HSTS_SECONDS", 31536000)  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", False)


# ---------------------------------------------------------------------------
# Misc hardening
# ---------------------------------------------------------------------------
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
# SECURE_BROWSER_XSS_FILTER: removed in Django 4.0 — do not set it.
