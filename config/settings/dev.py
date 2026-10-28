"""Development settings — DEBUG=True, SQLite by default.

PostgreSQL is optional. To use it, set DB_ENGINE=django.db.backends.postgresql
in .env and run scripts/setup_postgres.sql once.
"""
from .base import *  # noqa

DEBUG = True
ALLOWED_HOSTS = ["*"]

# In dev: relax CSP so inline scripts (Chart.js init, CSRF ajax) work.
# Production inherits strict CSP from base.py for script-src
# (style-src already allows 'unsafe-inline' in base since 52 templates
# use inline styles — styles are low-risk for XSS).
CSP_REPORT_ONLY = True
CSP_SCRIPT_SRC = tuple(CSP_SCRIPT_SRC) + ("'unsafe-inline'",)

# In dev: payment gateway test mode by default (no real Stripe keys).
# This is the ONLY setting module where the "test" gateway is allowed —
# prod.py explicitly rejects ACTIVE_PAYMENT_GATEWAY=test.
ACTIVE_PAYMENT_GATEWAY = os.environ.get("ACTIVE_PAYMENT_GATEWAY", "test")
