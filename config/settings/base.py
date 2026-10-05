"""
Base Django settings for School ERP.
Environment-specific overrides in dev.py / prod.py.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
APPS_DIR = BASE_DIR / "apps"

# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-change-me-in-production-please-use-a-long-random-string",
)
DEBUG = False
ALLOWED_HOSTS = ["*"]

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
    "django_otp.plugins.otp_static",     # backup codes
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
    "django_otp.middleware.OTPMiddleware",                  # 2FA: marks request.user.is_verified()
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
# For dev/demo/low-traffic single-school deployments, SQLite is perfectly fine.
# To switch to PostgreSQL, set DB_ENGINE=django.db.backends.postgresql in .env
# and run scripts/setup_postgres.sql once.
# ---------------------------------------------------------------------------
if os.environ.get("DB_ENGINE") == "django.db.backends.postgresql":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("DB_NAME", "school_erp"),
            "USER": os.environ.get("DB_USER", "school_erp_user"),
            "PASSWORD": os.environ.get("DB_PASSWORD", ""),
            "HOST": os.environ.get("DB_HOST", "localhost"),
            "PORT": os.environ.get("DB_PORT", "5432"),
            "CONN_MAX_AGE": int(os.environ.get("DB_CONN_MAX_AGE", "60")),
            "OPTIONS": {
                "connect_timeout": int(os.environ.get("DB_CONNECT_TIMEOUT", "10")),
            },
        }
    }
else:
    # Default: SQLite (single-file DB, no server, no setup)
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
LOGIN_URL = "login"          # two_factor.urls exposes 'login' name (no namespace)
LOGIN_REDIRECT_URL = "dashboard:home"
LOGOUT_REDIRECT_URL = "login"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# django-otp / two_factor
OTP_TOTP_ISSUER = os.environ.get("OTP_ISSUER", "School ERP")
TWO_FACTOR_PATCH_LOGIN_REMEMBER = True
TWO_FACTOR_REMEMBER_COOKIE_AGE = 30 * 86400  # 30 days

# Force 2FA for sensitive roles (HR, superuser, accountant)
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
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = (
    "'self'",
    "'unsafe-inline'",  # required for inline Chart.js init + CSRF ajax
    "https://cdn.jsdelivr.net",
    "https://code.jquery.com",
)
CSP_STYLE_SRC = (
    "'self'",
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

# JazzCash (Pakistan) — placeholder credentials; fill from .env
JAZZCASH_MERCHANT_ID = os.environ.get("JAZZCASH_MERCHANT_ID", "")
JAZZCASH_PASSWORD = os.environ.get("JAZZCASH_PASSWORD", "")
JAZZCASH_INTEGRITY_SALT = os.environ.get("JAZZCASH_INTEGRITY_SALT", "")
JAZZCASH_RETURN_URL = os.environ.get("JAZZCASH_RETURN_URL", "http://localhost:8000/fees/payment/jazzcash/return/")
JAZZCASH_API_URL = os.environ.get("JAZZCASH_API_URL", "https://sandbox.jazzcash.com.pk/ApplicationAPI/API/2.0/Payment/DoPayment")

# Active gateway: "stripe" | "jazzcash" | "test"
ACTIVE_PAYMENT_GATEWAY = os.environ.get("ACTIVE_PAYMENT_GATEWAY", "test")

# ---------------------------------------------------------------------------
# Email backend — for "Forgot password" reset emails
# In dev: print emails to console (you'll see them in the runserver terminal)
# In prod: configure SMTP via env vars (e.g., SendGrid, AWS SES, Gmail)
# ---------------------------------------------------------------------------
EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True").lower() == "true"
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@apslahore.edu.pk")

# ---------------------------------------------------------------------------
# Google OAuth — for "Login with Google" button
# Get credentials at https://console.cloud.google.com/apis/credentials
# Add authorized redirect URI: http://localhost:8000/auth/google/callback/
# ---------------------------------------------------------------------------
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")

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
SCHOOL_LATE_FEE_DAYS = 7
SCHOOL_LATE_FEE_AMOUNT = 500
SCHOOL_REGISTRATION_PREFIX = "APS"        # was SCH — now uses APS-2026-000001
SCHOOL_CHALLAN_PREFIX = "CH"
SCHOOL_RECEIPT_PREFIX = "RC"
SCHOOL_EMPLOYEE_PREFIX = "EMP"

PAYMENT_GATEWAY_ENABLED = False

AUDIT_LOG_MODELS = [
    "students.student", "admissions.admission", "fees.feechallan",
    "fees.feepayment", "examinations.termresult", "payroll.payroll",
    "announcements.announcement", "accounts.user",
]

# ---------------------------------------------------------------------------
# Custom error handlers — friendly messages, no raw tracebacks shown to users
# ---------------------------------------------------------------------------
handler404 = "config.urls.handler404_page"
handler500 = "config.urls.handler500_page"
handler403 = "config.urls.handler403_page"
