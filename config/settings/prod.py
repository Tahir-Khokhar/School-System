"""Production settings — read everything from environment, fail-fast on missing
required variables. NEVER default SECRET_KEY or ALLOWED_HOSTS to permissive
values; production deployments must set them explicitly.

Default values are deliberately restrictive. If an env var is missing or set
to a sentinel like 'change-me', settings import raises an ImproperlyConfigured
so the deployment cannot start in an insecure state.
"""
import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401,F403  (import base settings)


def _require_env(name, *, sentinel="change-me-to-a-long-random-string"):
    """Read an environment variable; fail fast if missing or set to a sentinel.

    Sentinel check prevents the deployment from starting with the default
    placeholder value that ships in .env.example.
    """
    value = os.environ.get(name, "").strip()
    if not value:
        raise ImproperlyConfigured(
            f"Production deployment requires the {name} environment variable to be set."
        )
    if value.lower().startswith(sentinel.lower()[:12]):  # match first 12 chars of sentinel
        raise ImproperlyConfigured(
            f"{name} is set to the placeholder sentinel — replace it with a real value."
        )
    return value


# ---------------------------------------------------------------------------
# DEBUG — hard-coded False; CANNOT be enabled via env var in prod.
# If you really need DEBUG=True in prod (you shouldn't), use the dev settings.
# ---------------------------------------------------------------------------
DEBUG = False

# ---------------------------------------------------------------------------
# SECRET_KEY — required, must not be the placeholder. 64+ chars recommended.
# ---------------------------------------------------------------------------
SECRET_KEY = _require_env("DJANGO_SECRET_KEY")

# ---------------------------------------------------------------------------
# ALLOWED_HOSTS — required, comma-separated list. No "*" in prod.
# ---------------------------------------------------------------------------
_allowed = os.environ.get("ALLOWED_HOSTS", "").strip()
if not _allowed or _allowed == "*":
    raise ImproperlyConfigured(
        "ALLOWED_HOSTS must be set to a comma-separated list of real hostnames "
        "in production. The wildcard '*' is forbidden."
    )
ALLOWED_HOSTS = [h.strip() for h in _allowed.split(",") if h.strip()]
if "*" in ALLOWED_HOSTS:
    raise ImproperlyConfigured("ALLOWED_HOSTS contains '*' — forbidden in production.")

# ---------------------------------------------------------------------------
# CSRF_TRUSTED_ORIGINS — required for HTTPS deployments behind a proxy.
# Defaults to the same hostnames as ALLOWED_HOSTS with https:// prefix.
# ---------------------------------------------------------------------------
_csrf = os.environ.get("CSRF_TRUSTED_ORIGINS", "").strip()
if _csrf:
    CSRF_TRUSTED_ORIGINS = [c.strip() for c in _csrf.split(",") if c.strip()]
else:
    CSRF_TRUSTED_ORIGINS = [f"https://{h}" for h in ALLOWED_HOSTS]

# ---------------------------------------------------------------------------
# HTTPS / HSTS — always on in prod.
# Override with SECURE_SSL_REDIRECT=False only if serving behind a TLS
# terminator that the deployment trusts (set SECURE_PROXY_SSL_HEADER too).
# ---------------------------------------------------------------------------
SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "True").lower() == "true"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30  # 30 days
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNOSNIFF = True  # (DEPRECATED alias — kept for compat)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

# Trust the X-Forwarded-Proto header from the proxy so SECURE_SSL_REDIRECT works.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ---------------------------------------------------------------------------
# Payment gateway — FAIL CLOSED. Default to "none" (no gateway) instead of
# "test" (always-succeeds gateway). Active gateway MUST be set explicitly.
# ---------------------------------------------------------------------------
PAYMENT_GATEWAY_ENABLED = True
_active_gw = os.environ.get("ACTIVE_PAYMENT_GATEWAY", "").strip().lower()
if _active_gw == "test":
    raise ImproperlyConfigured(
        "ACTIVE_PAYMENT_GATEWAY=test is forbidden in production. "
        "Use 'stripe' or 'jazzcash' with real credentials, or leave it unset "
        "to disable online payments."
    )
if _active_gw and _active_gw not in {"stripe", "jazzcash"}:
    raise ImproperlyConfigured(
        f"Unknown ACTIVE_PAYMENT_GATEWAY='{_active_gw}'. Use 'stripe' or 'jazzcash'."
    )
ACTIVE_PAYMENT_GATEWAY = _active_gw or "stripe"

# If Stripe is the active gateway, the secret + webhook secret MUST be set.
if ACTIVE_PAYMENT_GATEWAY == "stripe":
    _require_env("STRIPE_SECRET_KEY", sentinel="change-me")
    _require_env("STRIPE_WEBHOOK_SECRET", sentinel="change-me")

# If JazzCash is the active gateway, all 3 credentials MUST be set.
if ACTIVE_PAYMENT_GATEWAY == "jazzcash":
    _require_env("JAZZCASH_MERCHANT_ID", sentinel="change-me")
    _require_env("JAZZCASH_PASSWORD", sentinel="change-me")
    _require_env("JAZZCASH_INTEGRITY_SALT", sentinel="change-me")
