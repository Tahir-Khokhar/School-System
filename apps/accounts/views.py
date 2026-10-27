"""Account views — 2FA setup, rate-limit handler."""
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, View
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_ratelimit.decorators import ratelimit

User = get_user_model()


def rate_limit_exceeded(request, exception=None, *args, **kwargs):
    """Custom view shown when a rate limit is hit."""
    if request.headers.get("x-requested-with") == "XMLHttpRequest" or request.content_type == "application/json":
        return HttpResponse(
            '{"error": "Too many attempts. Please slow down and try again later."}',
            content_type="application/json",
            status=429,
        )
    return render(
        request,
        "accounts/rate_limit.html",
        {"retry_after": getattr(exception, "expected_delay", "60")},
        status=429,
    )


class TwoFactorRequiredMixin:
    """Mixin that redirects to 2FA setup if user has a sensitive role but no TOTP device."""
    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return self.handle_no_permission()
        force_roles = getattr(settings, "TWO_FACTOR_FORCE_ROLES", set())
        if (user.role in force_roles or user.is_superuser):
            has_totp = TOTPDevice.objects.filter(user=user, confirmed=True).exists()
            if not has_totp:
                messages.warning(
                    request,
                    "Your role requires 2FA. Please set up an authenticator app first."
                )
                return redirect("accounts:setup_2fa")
        return super().dispatch(request, *args, **kwargs)


class Setup2FAView(LoginRequiredMixin, TemplateView):
    """Display QR code for the user's TOTP device."""
    template_name = "accounts/setup_2fa.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        # Get or create an unconfirmed TOTP device
        device = TOTPDevice.objects.filter(user=user, confirmed=False).first()
        if not device:
            device = TOTPDevice.objects.create(user=user, name="default", confirmed=False)
        ctx["device"] = device
        # Generate the QR code SVG using qrcode library
        import qrcode
        import qrcode.image.svg
        factory = qrcode.image.svg.SvgPathImage
        url = device.config_url
        img = qrcode.make(url, image_factory=factory, box_size=10, border=2)
        from io import BytesIO
        buf = BytesIO()
        img.save(buf)
        ctx["qr_svg"] = buf.getvalue().decode("utf-8")
        ctx["otp_url"] = url
        ctx["breadcrumbs"] = [{"title": "Security"}, {"title": "Set up 2FA"}]
        return ctx


@method_decorator(ratelimit(key="user", rate="10/m", method="POST", block=True), name="post")
class Verify2FAView(LoginRequiredMixin, View):
    """Verify the user's first TOTP code, mark the device confirmed.

    Rate-limited: 10 verification attempts/minute/user. A 6-digit TOTP code
    has only 1,000,000 possibilities — without rate limiting, an attacker
    with the user's password could brute-force it in ~17 minutes at 1k req/s.
    10/min bounds the attack to ~7 days minimum, by which time the code has
    rotated ~10,080 times.
    """
    def post(self, request, *args, **kwargs):
        if getattr(request, "limited", False):
            return rate_limit_exceeded(request)

        token = request.POST.get("token", "").strip()
        device = TOTPDevice.objects.filter(user=request.user, confirmed=False).first()
        if not device:
            messages.error(request, "No pending TOTP device. Start setup again.")
            return redirect("accounts:setup_2fa")
        if device.verify_token(token):
            device.confirmed = True
            device.save()
            messages.success(request, "Two-factor authentication enabled!")
            # Audit log entry — 2FA enablement is a security-relevant event.
            from apps.audit_logs.models import AuditLogService
            AuditLogService.log(
                user=request.user, action="update",
                obj=request.user,
                description="Enabled 2FA on account",
            )
            return redirect("dashboard:home")
        messages.error(request, "Invalid token. Please make sure your authenticator app shows the current 6-digit code.")
        return redirect("accounts:setup_2fa")


@method_decorator(ratelimit(key="user", rate="3/m", method="POST", block=True), name="post")
class Disable2FAView(LoginRequiredMixin, View):
    """Disable 2FA — only allowed after re-entering the current password.

    Rate-limited: 3 attempts/minute (tighter than verify — disabling 2FA is
    more dangerous). Audit-logged so the security trail survives.

    NOTE: deliberately NOT protected by TwoFactorRequiredMixin (it's the
    disable endpoint itself). Password re-entry is the security gate here.
    """
    def post(self, request, *args, **kwargs):
        if getattr(request, "limited", False):
            return rate_limit_exceeded(request)

        from django.contrib.auth import authenticate
        password = request.POST.get("password", "")
        user = authenticate(username=request.user.username, password=password)
        if not user:
            messages.error(request, "Incorrect password. 2FA was NOT disabled.")
            return redirect("accounts:setup_2fa")
        TOTPDevice.objects.filter(user=request.user).delete()
        messages.success(request, "Two-factor authentication disabled.")
        # Audit log entry — 2FA disablement is a high-severity security event.
        from apps.audit_logs.models import AuditLogService
        AuditLogService.log(
            user=request.user, action="update",
            obj=request.user,
            description="Disabled 2FA on account",
        )
        return redirect("dashboard:home")
