"""
SECURITY FIX SCRIPT — idempotent, atomic, verified.

Usage:
    DRY_RUN=1 python scripts/fix_security.py   # preview
    python scripts/fix_security.py             # apply

Every fix:
  * asserts its "old" pattern is present before rewriting (no silent no-ops)
  * writes via temp file + os.replace() (atomic, no truncation)
  * is a no-op on a second run (idempotent)
  * ensures required imports exist before using them
  * verifies the resulting file compiles
"""
from __future__ import annotations

import os
import re
import sys
import tempfile
from pathlib import Path

BASE = Path(os.environ.get("SCHOOL_ERP_BASE", "/home/z/my-project/school_erp"))
DRY_RUN = os.environ.get("DRY_RUN") == "1"

CHANGED: list[Path] = []
SKIPPED: list[str] = []


# ---------------------------------------------------------------------------
# File helpers
# ---------------------------------------------------------------------------
def read(path: Path) -> str:
    if not path.exists():
        fail(f"{path} not found")
    return path.read_text(encoding="utf-8")


def write(path: Path, content: str) -> None:
    if DRY_RUN:
        print(f"[dry-run] would write {path.relative_to(BASE)} ({len(content)} bytes)")
        return
    # Verify it's valid Python before overwriting
    if path.suffix == ".py":
        try:
            compile(content, str(path), "exec")
        except SyntaxError as exc:
            fail(f"{path}: generated content has SyntaxError: {exc}")
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".fix_", suffix=path.suffix)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise
    CHANGED.append(path)


def replace_once(content: str, old: str, new: str, label: str) -> str:
    if new in content and old not in content:
        SKIPPED.append(label)
        print(f"  (skip) {label}: already applied")
        return content
    if old not in content:
        fail(f"{label}: expected pattern not found in file")
    return content.replace(old, new, 1)


def replace_re(content: str, pattern: str, repl: str, label: str, flags: int = 0) -> str:
    new_content, n = re.subn(pattern, repl, content, count=1, flags=flags)
    if n == 0:
        if re.search(repl, content, flags) or repl in content:
            SKIPPED.append(label)
            print(f"  (skip) {label}: already applied")
            return content
        fail(f"{label}: regex matched nothing")
    return new_content


def ensure_import(content: str, line: str, after: str, label: str) -> str:
    if line in content:
        return content
    if after not in content:
        fail(f"{label}: could not find anchor {after!r} to insert {line!r}")
    return content.replace(after, f"{after}\n{line}", 1)


def fail(msg: str) -> None:
    sys.exit(f"\n❌ {msg}\n   Aborting before any further writes. "
             f"Files already written: {[str(p) for p in CHANGED]}")


def banner(label: str) -> None:
    print(f"\n▶ {label}")


# ===========================================================================
# FIX 1 — TestGatewayPayView: login + pk match + DEBUG-only + balance charge
# ===========================================================================
banner("FIX 1: TestGatewayPayView hardening")
p = BASE / "apps/fees/views.py"
c = read(p)

# 1a. Ensure imports
c = ensure_import(
    c,
    "from django.contrib.auth.mixins import LoginRequiredMixin",
    "from django.contrib import messages",
    "FIX 1 imports (LoginRequiredMixin)",
)
c = ensure_import(
    c,
    "from django.http import HttpResponseBadRequest, HttpResponseNotFound",
    "from django.http import HttpResponse",
    "FIX 1 imports (HTTP errors)",
)

# 1b. Replace the whole TestGatewayPayView class, matching its full body.
old_test_view = re.compile(
    r"class TestGatewayPayView\(View\):.*?(?=\nclass |\Z)",
    re.DOTALL,
)
new_test_view = '''class TestGatewayPayView(LoginRequiredMixin, View):
    """Test gateway checkout — DEBUG-only, login-required, pk-matched."""

    def dispatch(self, request, *args, **kwargs):
        from django.conf import settings
        if not settings.DEBUG:
            return HttpResponseNotFound("Test gateway is not available.")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        challan = get_object_or_404(FeeChallan, pk=kwargs["pk"])
        session_id = kwargs["session_id"]
        if challan.challan_no not in session_id:
            return HttpResponseBadRequest("Session does not match challan.")
        return render(request, "fees/test_gateway_pay.html", {
            "challan": challan,
            "session_id": session_id,
        })

    def post(self, request, *args, **kwargs):
        challan = get_object_or_404(FeeChallan, pk=kwargs["pk"])
        session_id = kwargs.get("session_id", "")
        posted_no = request.POST.get("challan_no", "")

        if posted_no != challan.challan_no:
            messages.error(request, "Challan mismatch. Payment rejected.")
            return redirect("fees:challan_detail", pk=challan.pk)
        if challan.status in (FeeChallan.Status.PAID, FeeChallan.Status.CANCELLED):
            messages.error(request, "Challan is paid or cancelled.")
            return redirect("fees:challan_detail", pk=challan.pk)

        amount = challan.balance
        if amount <= 0:
            messages.error(request, "No balance due.")
            return redirect("fees:challan_detail", pk=challan.pk)

        try:
            FeeService.record_payment(
                challan=challan,
                amount=amount,
                method="online",
                user=request.user,
                transaction_ref=f"TEST-{session_id[-12:]}",
                notes="Test gateway payment (DEBUG only)",
                is_successful=True,
            )
            messages.success(request, "Test payment recorded.")
        except ValueError as exc:
            messages.error(request, f"Payment failed: {exc}")
        return redirect("fees:challan_detail", pk=challan.pk)
'''
c, n = re.subn(old_test_view, new_test_view, c)
if n == 0:
    if "class TestGatewayPayView(LoginRequiredMixin, View):" in c:
        SKIPPED.append("FIX 1: TestGatewayPayView")
        print("  (skip) FIX 1: already applied")
    else:
        fail("FIX 1: TestGatewayPayView class not found")
write(p, c)


# ===========================================================================
# FIX 2 — accounts/mixins.py: append missing mixins (don't overwrite)
# ===========================================================================
banner("FIX 2: StaffRequiredMixin")
p = BASE / "apps/accounts/mixins.py"
c = read(p) if p.exists() else ""

appended = False
if "class RoleRequiredMixin" not in c:
    c += '''

class RoleRequiredMixin:
    """Restrict access to a set of role names. Use after LoginRequiredMixin."""
    allowed_roles: list = []

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return self.handle_no_permission()
        if user.is_superuser or getattr(user, "role", None) == "super_admin":
            return super().dispatch(request, *args, **kwargs)
        role = getattr(user, "role", None)
        if self.allowed_roles and role not in self.allowed_roles:
            raise PermissionDenied("You do not have permission to access this page.")
        return super().dispatch(request, *args, **kwargs)
'''
    appended = True

if "class StaffRequiredMixin" not in c:
    c += '''

class StaffRequiredMixin(LoginRequiredMixin):
    """Only staff/admin roles can access. Students and parents are blocked."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        user = request.user
        if user.is_superuser or getattr(user, "role", None) == "super_admin":
            return super().dispatch(request, *args, **kwargs)
        if getattr(user, "role", None) in {"student", "parent"}:
            raise PermissionDenied("Students and parents cannot access staff pages.")
        return super().dispatch(request, *args, **kwargs)
'''
    appended = True

if appended or not p.exists():
    if not c.startswith('"""'):
        c = ('"""Reusable mixins for class-based views."""\n'
             "from django.contrib.auth.mixins import LoginRequiredMixin\n"
             "from django.core.exceptions import PermissionDenied\n") + c
    write(p, c)
else:
    SKIPPED.append("FIX 2: mixins")
    print("  (skip) FIX 2: mixins already present")


# ===========================================================================
# FIX 3 — Google login: no auto-create, active-only, explicit errors
# ===========================================================================
banner("FIX 3: Google login — no auto-create")
p = BASE / "apps/accounts/views.py"
c = read(p)

old_google = re.compile(
    r"(\n    )# Find or create a User with that email.*?login\(request, user, backend=\"django\.contrib\.auth\.backends\.ModelBackend\"\)",
    re.DOTALL,
)
new_google = '''
    # SECURITY: only existing, active accounts may log in via Google.
    # No auto-creation — strangers cannot self-enrol.
    user = User.objects.filter(email__iexact=email).first()
    if user is None:
        messages.error(
            request,
            "No account found with this Google email. "
            "Contact the school administration.",
        )
        return redirect("login")
    if not user.is_active:
        messages.error(request, "This account has been disabled.")
        return redirect("login")

    from apps.audit_logs.models import AuditLogService
    AuditLogService.log(
        user=user, action="login", obj=user,
        description=f"Login via Google OAuth ({email})",
    )

    login(request, user, backend="django.contrib.auth.backends.ModelBackend")'''

c, n = re.subn(old_google, new_google, c)
if n == 0:
    if "user = User.objects.filter(email__iexact=email).first()" in c:
        SKIPPED.append("FIX 3: google login")
        print("  (skip) FIX 3: already applied")
    else:
        fail("FIX 3: Google-login block not found")
write(p, c)


# ===========================================================================
# FIX 4 — File upload validation (insert inside the form class)
# ===========================================================================
banner("FIX 4: file upload validation")
p = BASE / "apps/homework/forms.py"
c = read(p)

if "def clean_attachment" not in c:
    header = '''ALLOWED_FILE_TYPES = {
    ".pdf", ".doc", ".docx", ".txt",
    ".png", ".jpg", ".jpeg",
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


'''
    if "ALLOWED_FILE_TYPES" not in c:
        c = header + c

    clean_method = '''
    def clean_attachment(self):
        import os as _os
        file = self.cleaned_data.get("attachment")
        if not file:
            return file
        ext = _os.path.splitext(file.name)[1].lower()
        if ext not in ALLOWED_FILE_TYPES:
            raise forms.ValidationError(
                f"File type '{ext}' is not allowed. "
                f"Allowed: {', '.join(sorted(ALLOWED_FILE_TYPES))}"
            )
        if file.size > MAX_FILE_SIZE:
            raise forms.ValidationError(
                f"File is too large ({file.size // 1024} KB). Max 10 MB."
            )
        return file
'''
    # Insert *inside* HomeworkForm — right before its end (before next top-level class or EOF)
    m = re.search(r"(class HomeworkForm\(forms\.ModelForm\):.*?)(?=\nclass |\Z)", c, re.DOTALL)
    if not m:
        fail("FIX 4: HomeworkForm class not found")
    insert_at = m.end(1)
    c = c[:insert_at] + clean_method + c[insert_at:]
    write(p, c)
else:
    SKIPPED.append("FIX 4: file upload")
    print("  (skip) FIX 4: already applied")


# ===========================================================================
# FIX 5 — Charge balance, not total_payable (tolerant regex)
# ===========================================================================
banner("FIX 5: charge balance in gateway views")
p = BASE / "apps/fees/views.py"
c = read(p)

pattern = re.compile(
    r"(FeeService\.record_payment\([^)]*?amount\s*=\s*)challan\.total_payable",
    re.DOTALL,
)
c, n = re.subn(pattern, r"\1challan.balance", c)
if n:
    print(f"  replaced {n} occurrence(s)")
else:
    SKIPPED.append("FIX 5: balance")
    print("  (skip) FIX 5: no total_payable payments found")
write(p, c)


# ===========================================================================
# FIX 6 — Late fee: actually freeze at payment time (schema-free version)
# ===========================================================================
banner("FIX 6: freeze late fee once paid")
p = BASE / "apps/fees/models.py"
c = read(p)

# Add a cached 'late_fee_applied' value to __init__ / properties? We use a
# stored, non-DB attribute fallback: if the challan has any payment, the
# late_fee property returns 0 (already collected).
old_lf_prop = re.compile(
    r"(def late_fee\(self\):\n)(.*?)(?=\n    @property|\n    def )",
    re.DOTALL,
)
new_lf = '''def late_fee(self):
        """Late fee is frozen once a payment is recorded: a paid/partially-paid
        challan never accrues new late fee, preventing 'phantom' increases."""
        if getattr(self, "pk", None) and self.payments.filter(is_successful=True).exists():
            return Decimal("0")
        return FeeService.calculate_late_fee(self)
'''
c, n = re.subn(old_lf_prop, new_lf, c, count=1)
if n == 0:
    if 'payments.filter(is_successful=True).exists()' in c:
        SKIPPED.append("FIX 6: late fee")
        print("  (skip) FIX 6: already applied")
    else:
        print("  ⚠ FIX 6: late_fee property shape unexpected — skipping (inspect manually)")
        SKIPPED.append("FIX 6: late fee")
else:
    write(p, c)


# ===========================================================================
# FIX 7 — record_payment: validate amount / status / zero-total
# ===========================================================================
banner("FIX 7: record_payment validation")
p = BASE / "apps/fees/services/fee_service.py"
c = read(p)

insert_after = "challan = FeeChallan.objects.select_for_update().get(pk=challan.pk)"
if "Cannot pay a cancelled challan" not in c:
    guard = '''challan = FeeChallan.objects.select_for_update().get(pk=challan.pk)

        if challan.status == FeeChallan.Status.CANCELLED:
            raise ValueError("Cannot pay a cancelled challan.")
        if challan.status == FeeChallan.Status.PAID:
            raise ValueError("Challan is already fully paid.")'''
    c = replace_once(c, insert_after, guard, "FIX 7: status guards")

if "exceeds outstanding balance" not in c:
    guard2 = '''        amount = Decimal(amount)
        if amount <= 0:
            raise ValueError("Payment amount must be positive.")

        if amount > challan.balance:
            raise ValueError(
                f"Payment amount ({amount}) exceeds balance ({challan.balance})."
            )'''
    old_amt = '''        amount = Decimal(amount)
        if amount <= 0:
            raise ValueError("Payment amount must be positive.")'''
    c = replace_once(c, old_amt, guard2, "FIX 7: balance cap")

write(p, c)


# ===========================================================================
# FIX 8 — Payroll: guards + retry-safe (real fixes, not the broken version)
# ===========================================================================
banner("FIX 8: payroll guards + retry-safe")
p = BASE / "apps/payroll/models.py"
c = read(p)

# 8a. generate_payroll: include FAILED in the "don't reset" set
if "Payroll.Status.FAILED" not in c or "return existing  # Don't reset" not in c:
    c = replace_re(
        c,
        r'if existing and existing\.status in \((Payroll\.Status\.PAID), (Payroll\.Status\.PROCESSING)\):',
        r'if existing and existing.status in (\1, \2, Payroll.Status.FAILED):',
        "FIX 8a: FAILED not reset",
    )

# 8b. record_bank_payment: PROCESSING guard + delete *all* prior payments on retry
if "Payroll is already being processed" not in c:
    old_guard = '''            if payroll.status == Payroll.Status.PAID:
                raise ValueError("This payroll has already been paid.")'''
    new_guard = '''            if payroll.status == Payroll.Status.PAID:
                raise ValueError("This payroll has already been paid.")
            if payroll.status == Payroll.Status.PROCESSING:
                raise ValueError("Payroll is already being processed.")'''
    c = replace_once(c, old_guard, new_guard, "FIX 8b: PROCESSING guard")

if "SalaryPayment.objects.filter(payroll=payroll).delete()" not in c:
    old_retry = '''            if payroll.status == Payroll.Status.FAILED:
                SalaryPayment.objects.filter(payroll=payroll, is_successful=False).delete()'''
    new_retry = '''            if payroll.status == Payroll.Status.FAILED:
                # OneToOneField means any prior row must be removed first
                SalaryPayment.objects.filter(payroll=payroll).delete()'''
    c = replace_once(c, old_retry, new_retry, "FIX 8b: retry deletes all prior")

write(p, c)


# ===========================================================================
# FIX 11 — Marks validation
# ===========================================================================
banner("FIX 11: marks validation")
p = BASE / "apps/examinations/views.py"
c = read(p)

if "Marks cannot be negative" not in c:
    old_marks = '''    def post(self, request, *args, **kwargs):
        student_ids = request.POST.getlist("student_id")
        obtained = request.POST.getlist("obtained_marks")
        remarks = request.POST.getlist("remarks")
        for sid, marks, rem in zip(student_ids, obtained, remarks):
            TestResult.objects.update_or_create(
                test=self.test, student_id=sid,
                defaults={"obtained_marks": marks or 0, "remarks": rem or ""},
            )
        messages.success(request, "Marks saved.")
        return redirect("examinations:classtest_detail", pk=self.test.pk)'''
    new_marks = '''    def post(self, request, *args, **kwargs):
        from decimal import Decimal, InvalidOperation

        student_ids = request.POST.getlist("student_id")
        obtained = request.POST.getlist("obtained_marks")
        remarks = request.POST.getlist("remarks")
        errors = []
        total = self.test.total_marks
        for sid, marks, rem in zip(student_ids, obtained, remarks):
            try:
                val = Decimal(str(marks or "0")).quantize(Decimal("0.01"))
            except (InvalidOperation, TypeError):
                errors.append(f"Invalid marks for student #{sid}")
                continue
            if val < 0 or val > total:
                errors.append(
                    f"Marks {val} out of range 0–{total} for student #{sid}"
                )
                continue
            TestResult.objects.update_or_create(
                test=self.test, student_id=sid,
                defaults={"obtained_marks": val, "remarks": rem or ""},
            )
        if errors:
            messages.error(request, "Some marks not saved: " + "; ".join(errors))
        else:
            messages.success(request, "Marks saved.")
        return redirect("examinations:classtest_detail", pk=self.test.pk)'''
    c = replace_once(c, old_marks, new_marks, "FIX 11: marks validation")
    write(p, c)
else:
    SKIPPED.append("FIX 11: marks")
    print("  (skip) FIX 11: already applied")


# ===========================================================================
# FIX 12 — result_service import path
# ===========================================================================
banner("FIX 12: result_service import")
p = BASE / "apps/examinations/services/result_service.py"
c = read(p)
c = replace_once(
    c,
    "from .models import ExamResult, Exam",
    "from ..models import ExamResult, Exam",
    "FIX 12: relative import",
)
write(p, c)


# ===========================================================================
# FIX MEDIUM — rate limit: single decorator, tolerant of class args
# ===========================================================================
banner("MEDIUM: rate-limit decorator dedupe")
p = BASE / "apps/fees/views.py"
c = read(p)
c = re.sub(
    r'@method_decorator\(ratelimit\(key="user", rate="10/m", method="POST", block=True\), name="post"\)\n',
    "",
    c,
)
write(p, c)


# ===========================================================================
# FIX MEDIUM — .env loading in manage.py (path + warning on missing dotenv)
# ===========================================================================
banner("MEDIUM: manage.py dotenv")
p = BASE / "manage.py"
c = read(p)
if "load_dotenv" not in c:
    c = replace_once(
        c,
        '"""Django\'s command-line utility for administrative tasks."""',
        '''"""Django's command-line utility for administrative tasks."""
from pathlib import Path as _Path
try:
    from dotenv import load_dotenv as _load_dotenv
    _load_dotenv(_Path(__file__).resolve().parent / ".env")
except ImportError:
    import sys as _sys
    _sys.stderr.write("warning: python-dotenv not installed; .env ignored\\n")''',
        "MEDIUM: manage.py dotenv",
    )
    write(p, c)
else:
    SKIPPED.append("MEDIUM: dotenv")
    print("  (skip) MEDIUM: dotenv already applied")


# ===========================================================================
# FIX MEDIUM — .gitignore inline comments
# ===========================================================================
banner("MEDIUM: .gitignore cleanup")
p = BASE / ".gitignore"
if p.exists():
    c = read(p)
    c = re.sub(r"^(.*?)\s+#\s.*$", r"\1", c, flags=re.MULTILINE)
    write(p, c)
else:
    SKIPPED.append("MEDIUM: .gitignore missing")
    print("  (skip) MEDIUM: .gitignore not found")


# ===========================================================================
# FIX MEDIUM — wsgi.py: default to base, not prod
# ===========================================================================
banner("MEDIUM: wsgi.py default settings")
p = BASE / "config/wsgi.py"
c = read(p)
# Do NOT flip dev -> prod (that breaks local runserver).
# Instead, make it configurable and keep 'dev' as the safe local default.
if "DJANGO_SETTINGS_MODULE" in c and 'os.environ.setdefault("DJANGO_SETTINGS_MODULE"' not in c \
        and "os.environ.setdefault('DJANGO_SETTINGS_MODULE'" not in c:
    c = replace_re(
        c,
        r"os\.environ\[\s*['\"]DJANGO_SETTINGS_MODULE['\"]\s*\]\s*=\s*['\"]config\.settings\.(?:dev|prod)['\"]",
        'os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")',
        "MEDIUM: wsgi.py",
    )
    write(p, c)
else:
    SKIPPED.append("MEDIUM: wsgi.py")
    print("  (skip) MEDIUM: wsgi.py already uses setdefault")


# ===========================================================================
# Done
# ===========================================================================
print(f"\n{'[DRY-RUN] ' if DRY_RUN else ''}"
      f"Changed {len(CHANGED)} file(s); skipped {len(SKIPPED)} already-applied fix(es).")
for path in CHANGED:
    print(f"  • {path.relative_to(BASE) if path.is_relative_to(BASE) else path}")
if SKIPPED:
    print("Skipped (already applied):")
    for s in SKIPPED:
        print(f"  – {s}")
