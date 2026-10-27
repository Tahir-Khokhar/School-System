"""
Base Django settings for School ERP.
Environment-specific overrides in dev.py / prod.py.
"""
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent.parent
APPS_DIR = BASE_DIR / "apps"


# ---------------------------------------------------------------------------
# Small env helpers — avoids repeating `.lower() == "true"` and prevents
# whitespace bugs when lists are comma-separated.
# FIX #12 — centralised, accepts 1/true/yes/on.
# ---------------------------------------------------------------------------
def env_bool(name, default=False):
    return os.environ.get(name, str(default)).lower() in ("1", "true", "yes", "on")


def env_int(name, default):
    try:
        return int(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        return default


def env_list(name, default=""):
    return [x.strip() for x in os.environ.get(name, default).split(",") if x.strip()]


# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------
# FIX #1 — never ship a usable SECRET_KEY default. If the env var is absent,
# raise on import so production can't start accidentally with a public key.
# `manage.py` (dev.py) can set a throwaway value explicitly.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    raise ImproperlyConfigured(
        "DJANGO_SECRET_KEY environment variable is required. "
        "Generate one with: python -c "
        "'from django.core.management.utils import get_random_secret_key; "
        "print(get_random_secret_key())'"
    )

# FIX #2 — DEBUG is an env-driven setting; prod.py forces it False and raises
# if it ends up True in production. Kept False as the safe default here.
DEBUG = env_bool("DJANGO_DEBUG", False)

# FIX #3 — ALLOWED_HOSTS must come from env; empty means "not configured" and
# prod.py raises. No implicit "*" anywhere in the codebase.
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS")


# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
]

THIRD_PARTY_APPS = [
    "crispy_forms",
    "crispy_bootstrap5",
    "django_otp",                       # 2FA core
    "django_otp.plugins.otp_totp",      # TOTP (Google Authenticator)
    "django_otp.plugins.otp_static",    # backup codes
    "two_factor",                       # full 2FA flow
    "csp",                              # Content Security Policy
]

LOCAL_APPS = [
    "apps.common",
    "apps.accounts",
    "apps.students",
    "apps.parents",
    "apps.teachers",
    "apps.admissions",
    "apps.attendance",
    "apps.diary",
    "apps.homework",
    "apps.syllabus",
    "apps.examinations",
    "apps.datesheets",
    "apps.fees",
    "apps.payroll",
    "apps.activities",
    "apps.announcements",
    "apps.notifications",
    "apps.school_calendar",
    "apps.reports",
    "apps.documents",
    "apps.audit_logs",
    "apps.dashboard",
    "apps.portal",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "csp.middleware.CSPMiddleware",                          # Content Security Policy
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",                  # 2FA
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.audit_logs.middleware.AuditLogMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.template.context_processors.media",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.common.context_processors.school_context",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# ---------------------------------------------------------------------------
# Database — SQLite by default; PostgreSQL optional via env vars.
# ---------------------------------------------------------------------------
# FIX #13 — check the engine against the exact string Django expects, and
# make the postgres branch fail loudly if required vars are missing rather
# than silently connecting with defaults.
if os.environ.get("DB_ENGINE") == "django.db.backends.postgresql":
    _required = ("DB_NAME", "DB_USER", "DB_PASSWORD", "DB_HOST")
    _missing = [k for k in _required if not os.environ.get(k)]
    if _missing:
        raise ImproperlyConfigured(
            f"PostgreSQL selected but missing env vars: {', '.join(_missing)}"
        )
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ["DB_NAME"],
            "USER": os.environ["DB_USER"],
            "PASSWORD": os.environ["DB_PASSWORD"],
            "HOST": os.environ["DB_HOST"],
            "PORT": os.environ.get("DB_PORT", "5432"),
            "CONN_MAX_AGE": env_int("DB_CONN_MAX_AGE", 60),
            "OPTIONS": {"connect_timeout": env_int("DB_CONNECT_TIMEOUT", 10)},
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": str(BASE_DIR / "db.sqlite3"),
        }
    }


# ---------------------------------------------------------------------------
# Auth + 2FA
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = "accounts.User"
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard:home"
LOGOUT_REDIRECT_URL = "login"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

OTP_TOTP_ISSUER = os.environ.get("OTP_ISSUER", "School ERP")
TWO_FACTOR_PATCH_LOGIN_REMEMBER = True
TWO_FACTOR_REMEMBER_COOKIE_AGE = 30 * 86400  # 30 days

# FIX #14 — validate forced roles against the real role enum (import lazily
# so settings remains importable without Django apps fully loaded — this is
# only a configuration list, so a plain set of strings is fine, but document
# where the canonical values live).
TWO_FACTOR_FORCE_ROLES = {"super_admin", "hr_payroll", "accountant"}


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = "default"
RATELIMIT_VIEW = "apps.accounts.views.rate_limit_exceeded"


# ---------------------------------------------------------------------------
# Content Security Policy (CSP)
# ---------------------------------------------------------------------------
# FIX #4 — `'unsafe-inline'` on script-src effectively disables script
# restrictions. If inline scripts are needed (Chart.js init, CSRF AJAX),
# use nonces via django-csp's `CSP_SCRIPT_SRC` + `{{ request.csp_nonce }}`
# in templates. In dev you may relax this, but production must not allow it.
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = (
    "'self'",
    "https://cdn.jsdelivr.net",
    "https://code.jquery.com",
    # Add "'unsafe-inline'" ONLY in dev.py if you need it during development.
)
CSP_STYLE_SRC = (
    "'self'",
    # FIX #4b — style-src unsafe-inline is still a hole (data exfil via CSS),
    # but is far less severe than script-src. Prefer nonces where possible.
    "'unsafe-inline'",
    "https://cdn.jsdelivr.net",
    "https://fonts.googleapis.com",
)
CSP_FONT_SRC = (
    "'self'",
    "https://cdn.jsdelivr.net",
    "https://fonts.gstatic.com",
)
CSP_IMG_SRC = (
    "'self'",
    "data:",
    "https://cdn.jsdelivr.net",
    "https://chartjs.org",
)
CSP_CONNECT_SRC = ("'self'",)
CSP_FRAME_SRC = ("'self'", "https://js.stripe.com")
CSP_OBJECT_SRC = ("'none'",)
CSP_BASE_URI = ("'self'",)
CSP_FORM_ACTION = ("'self'", "https://api.stripe.com")
CSP_REPORT_URI = "/csp-report/"
CSP_EXCLUDE_URL_PREFIXES = ("/admin/", "/media/")


# ---------------------------------------------------------------------------
# Payment gateway
# ---------------------------------------------------------------------------
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

JAZZCASH_MERCHANT_ID = os.environ.get("JAZZCASH_MERCHANT_ID", "")
JAZZCASH_PASSWORD = os.environ.get("JAZZCASH_PASSWORD", "")
JAZZCASH_INTEGRITY_SALT = os.environ.get("JAZZCASH_INTEGRITY_SALT", "")
JAZZCASH_RETURN_URL = os.environ.get(
    "JAZZCASH_RETURN_URL",
    "http://localhost:8000/fees/payment/jazzcash/return/",
)
JAZZCASH_API_URL = os.environ.get(
    "JAZZCASH_API_URL",
    "https://sandbox.jazzcash.com.pk/ApplicationAPI/API/2.0/Payment/DoPayment",
)

# FIX #5 — one source of truth for the active gateway. `PAYMENT_GATEWAY_ENABLED`
# below is derived; previously it was a separate hardcoded False that
# contradicted ACTIVE_PAYMENT_GATEWAY="test".
ACTIVE_PAYMENT_GATEWAY = os.environ.get("ACTIVE_PAYMENT_GATEWAY", "test")
if ACTIVE_PAYMENT_GATEWAY not in ("stripe", "jazzcash", "test"):
    raise ImproperlyConfigured(
        f"ACTIVE_PAYMENT_GATEWAY must be one of stripe/jazzcash/test, "
        f"got {ACTIVE_PAYMENT_GATEWAY!r}"
    )
PAYMENT_GATEWAY_ENABLED = ACTIVE_PAYMENT_GATEWAY != "test"


# ---------------------------------------------------------------------------
# Email backend
# ---------------------------------------------------------------------------
EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = env_int("EMAIL_PORT", 587)
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@apslahore.edu.pk")

# FIX #15 — if a real SMTP backend is configured, refuse to boot without
# credentials so password-reset emails don't silently go to nowhere.
if EMAIL_BACKEND.endswith("smtp.EmailBackend"):
    if not EMAIL_HOST_USER or not EMAIL_HOST_PASSWORD:
        raise ImproperlyConfigured(
            "SMTP email backend selected but EMAIL_HOST_USER/PASSWORD are empty."
        )


# ---------------------------------------------------------------------------
# i18n
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Karachi"
USE_I18N = True
USE_TZ = True


# ---------------------------------------------------------------------------
# Static / Media
# ---------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ---------------------------------------------------------------------------
# Crispy
# ---------------------------------------------------------------------------
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"


# ---------------------------------------------------------------------------
# School config
# ---------------------------------------------------------------------------
SCHOOL_NAME = os.environ.get("SCHOOL_NAME", "Army Public School Lahore")
SCHOOL_TAGLINE = os.environ.get("SCHOOL_TAGLINE", "I shall rise and shine")
SCHOOL_ADDRESS = os.environ.get(
    "SCHOOL_ADDRESS",
    "Army Public School Lahore, Tufail Road, Lahore Cantt, Lahore, Pakistan",
)
SCHOOL_PHONE = os.environ.get("SCHOOL_PHONE", "+92 42 9920 2040")
SCHOOL_EMAIL = os.environ.get("SCHOOL_EMAIL", "info@apslahore.edu.pk")
SCHOOL_CURRENCY = "PKR"
SCHOOL_CURRENCY_SYMBOL = "Rs."
SCHOOL_LATE_FEE_DAYS = env_int("SCHOOL_LATE_FEE_DAYS", 7)
SCHOOL_LATE_FEE_AMOUNT = env_int("SCHOOL_LATE_FEE_AMOUNT", 500)

# FIX #6 — the inline comment said "was SCH — now uses APS-2026-000001" but
# the value was still "APS". Keep APS (which is what the comment implies) and
# make the numbering hint explicit in the comment.
SCHOOL_REGISTRATION_PREFIX = "APS"      # e.g. APS-2026-000001
SCHOOL_CHALLAN_PREFIX = "CH"
SCHOOL_RECEIPT_PREFIX = "RC"
SCHOOL_EMPLOYEE_PREFIX = "EMP"

AUDIT_LOG_MODELS = [
    "students.student", "admissions.admission", "fees.feechallan",
    "fees.feepayment", "examinations.termresult", "payroll.payroll",
    "announcements.announcement", "accounts.user",
]


# ---------------------------------------------------------------------------
# Custom error handlers
# ---------------------------------------------------------------------------
handler404 = "config.urls.handler404_page"
handler500 = "config.urls.handler500_page"
handler403 = "config.urls.handler403_page"
