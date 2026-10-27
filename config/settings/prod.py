"""Production settings — read everything from environment."""
import os
from django.core.exceptions import ImproperlyConfigured
from .base import *  # noqa


def env_bool(name, default=False):
    return os.environ.get(name, str(default)).lower() in ("1", "true", "yes", "on")


def env_list(name, default=""):
    return [x.strip() for x in os.environ.get(name, default).split(",") if x.strip()]


DEBUG = env_bool("DJANGO_DEBUG", False)
if DEBUG and os.environ.get("ENV") == "production":
    raise ImproperlyConfigured("DEBUG must be False in production")

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS")
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured("ALLOWED_HOSTS must be set in production")

SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")  # only if proxy sets it

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")

SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", 31536000))  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = False  # enable only when actually submitted to preload list

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
