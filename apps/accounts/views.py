"""Account views — 2FA setup, rate-limit handler, Google OAuth."""
import json
import secrets
import urllib.parse
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, View
from django_otp.plugins.otp_totp.models import TOTPDevice

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


class Verify2FAView(LoginRequiredMixin, View):
    """Verify the user's first TOTP code, mark the device confirmed."""
    def post(self, request, *args, **kwargs):
        token = request.POST.get("token", "").strip()
        device = TOTPDevice.objects.filter(user=request.user, confirmed=False).first()
        if not device:
            messages.error(request, "No pending TOTP device. Start setup again.")
            return redirect("accounts:setup_2fa")
        if device.verify_token(token):
            device.confirmed = True
            device.save()
            messages.success(request, "Two-factor authentication enabled!")
            # Log audit entry
            from apps.audit_logs.models import AuditLogService
            AuditLogService.log(user=request.user, action="update",
                                obj=request.user, description="Enabled 2FA on account")
            return redirect("dashboard:home")
        messages.error(request, "Invalid token. Please make sure your authenticator app shows the current 6-digit code.")
        return redirect("accounts:setup_2fa")


class Disable2FAView(LoginRequiredMixin, View):
    """Disable 2FA — only allowed after re-entering the current password."""
    def post(self, request, *args, **kwargs):
        from django.contrib.auth import authenticate
        password = request.POST.get("password", "")
        user = authenticate(username=request.user.username, password=password)
        if not user:
            messages.error(request, "Incorrect password. 2FA was NOT disabled.")
            return redirect("accounts:setup_2fa")
        TOTPDevice.objects.filter(user=request.user).delete()
        messages.success(request, "Two-factor authentication disabled.")
        return redirect("dashboard:home")


# ============================================================================
# Google OAuth — minimal custom implementation
#
# To enable real Google login, set in .env:
#   GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
#   GOOGLE_CLIENT_SECRET=your-client-secret
#
# Configure OAuth consent screen + credentials at:
#   https://console.cloud.google.com/apis/credentials
#
# Add this authorized redirect URI:
#   http://localhost:8000/auth/google/callback/
# ============================================================================

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
GOOGLE_SCOPES = ["openid", "email", "profile"]


def google_login_start(request):
    """Step 1: redirect user to Google's OAuth consent screen."""
    client_id = getattr(settings, "GOOGLE_CLIENT_ID", "")
    if not client_id:
        messages.error(
            request,
            "Google login is not configured. "
            "Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env to enable. "
            "Get credentials at https://console.cloud.google.com/apis/credentials"
        )
        return redirect("login")

    # Generate a random state token to prevent CSRF
    state = secrets.token_urlsafe(32)
    request.session["google_oauth_state"] = state

    redirect_uri = request.build_absolute_uri(reverse("google_login_callback"))
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(GOOGLE_SCOPES),
        "state": state,
        "prompt": "select_account",
    }
    auth_url = f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"
    return HttpResponseRedirect(auth_url)


@csrf_exempt
def google_login_callback(request):
    """Step 2: Google redirects back with `code` param. Exchange for user info + login."""
    code = request.GET.get("code")
    state = request.GET.get("state")
    error = request.GET.get("error")

    if error:
        messages.error(request, f"Google login failed: {error}")
        return redirect("login")

    if not code or not state:
        return HttpResponseBadRequest("Missing code or state parameter")

    saved_state = request.session.get("google_oauth_state")
    if not saved_state or saved_state != state:
        return HttpResponseBadRequest("State mismatch — possible CSRF attack")

    # Exchange code for access token
    import urllib.request
    client_id = getattr(settings, "GOOGLE_CLIENT_ID", "")
    client_secret = getattr(settings, "GOOGLE_CLIENT_SECRET", "")
    redirect_uri = request.build_absolute_uri(reverse("google_login_callback"))

    token_data = urllib.parse.urlencode({
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }).encode("utf-8")

    req = urllib.request.Request(GOOGLE_TOKEN_URL, data=token_data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req) as response:
            token_response = json.loads(response.read())
    except Exception as e:
        messages.error(request, f"Google token exchange failed: {e}")
        return redirect("login")

    access_token = token_response.get("access_token")
    if not access_token:
        messages.error(request, "No access_token in Google response")
        return redirect("login")

    # Get user info from Google
    req = urllib.request.Request(GOOGLE_USERINFO_URL)
    req.add_header("Authorization", f"Bearer {access_token}")
    try:
        with urllib.request.urlopen(req) as response:
            user_info = json.loads(response.read())
    except Exception as e:
        messages.error(request, f"Failed to fetch Google user info: {e}")
        return redirect("login")

    email = user_info.get("email")
    if not email:
        messages.error(request, "Google did not return an email address")
        return redirect("login")

    # Find or create a User with that email
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            "username": email.split("@")[0],
            "first_name": user_info.get("given_name", ""),
            "last_name": user_info.get("family_name", ""),
            "role": User.Role.STUDENT,
            "is_active": True,
        },
    )
    if created:
        # Set a random unusable password (Google-only login)
        user.set_unusable_password()
        user.save()
        from apps.audit_logs.models import AuditLogService
        AuditLogService.log(
            user=user, action="create", obj=user,
            description=f"Account created via Google OAuth ({email})",
        )

    # Log the user in
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    # Clean up OAuth state
    request.session.pop("google_oauth_state", None)
    messages.success(request, f"Welcome, {user.get_full_name() or user.username}! Logged in via Google.")
    return redirect("dashboard:home")
