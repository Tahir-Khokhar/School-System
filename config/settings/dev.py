"""Development settings — DEBUG=True, SQLite by default.

PostgreSQL is optional. To use it, set DB_ENGINE=django.db.backends.postgresql
in .env and run scripts/setup_postgres.sql once.
"""
from .base import *  # noqa


DEBUG = True

# Do NOT use "*" even in dev — it hides Host-header bugs that production
# will reject, and gets copy-pasted into prod by mistake.
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]

# Relax CSP in dev so inline debugging/Chart.js init is not blocked.
# In prod, use nonces via {{ request.csp_nonce }} instead.
CSP_REPORT_ONLY = True
CSP_SCRIPT_SRC = CSP_SCRIPT_SRC + ("'unsafe-inline'",)

# Password-reset emails print to the runserver console.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Payment gateway — default to test in dev (no real credentials).
ACTIVE_PAYMENT_GATEWAY = os.environ.get("ACTIVE_PAYMENT_GATEWAY", "test")
PAYMENT_GATEWAY_ENABLED = ACTIVE_PAYMENT_GATEWAY != "test"
