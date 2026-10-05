"""Development settings — DEBUG=True, SQLite by default.

PostgreSQL is optional. To use it, set DB_ENGINE=django.db.backends.postgresql
in .env and run scripts/setup_postgres.sql once.
"""
from .base import *  # noqa

DEBUG = True
ALLOWED_HOSTS = ["*"]

# In dev: relax CSP so it doesn't block inline scripts during debugging
CSP_REPORT_ONLY = True

# In dev: payment gateway test mode by default (no real Stripe keys)
ACTIVE_PAYMENT_GATEWAY = os.environ.get("ACTIVE_PAYMENT_GATEWAY", "test")
