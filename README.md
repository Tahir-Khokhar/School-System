# School ERP & Management System

A complete, production-style Django-based School ERP & Management web application covering the entire yearly school lifecycle: Admissions → Students → Fees → Attendance → Tests → Exams → Reports → Promotion.

## Tech Stack

- **Backend**: Python 3.12, Django 4.2, Django ORM, Class-Based Views, Django Forms & Formsets
- **Database**: SQLite 3 (default — zero setup) / PostgreSQL 12+ (optional, for high-traffic deployments)
- **Auth & Security**: Django auth, Groups, Permissions, Custom User model, role-based access control, **Two-Factor Authentication** (TOTP), **rate limiting**, **Content Security Policy**
- **Payments**: Pluggable gateway abstraction (Stripe, JazzCash, Test) with **server-side webhook verification**
- **Frontend**: Bootstrap 5, Bootstrap Icons, Chart.js, Font Awesome, vanilla JS
- **PDF**: WeasyPrint (challans, receipts, salary slips, report cards, defaulter reports)
- **Architecture**: Modular multi-app + service layer + audit-logging middleware

## Project Structure

```
school_erp/
├── manage.py
├── config/                # project settings, URLs, ASGI/WSGI
│   └── settings/          # base / dev / prod
├── apps/
│   ├── accounts/          # Custom User + roles
│   ├── common/            # AcademicYear, Class, Section, Subject
│   ├── admissions/        # Full admission workflow + service
│   ├── students/          # Student + Enrollment
│   ├── parents/           # Parent
│   ├── teachers/          # Teacher + BankInfo (sensitive)
│   ├── fees/              # FeeType → Structure → Challan → Item → Payment → Receipt
│   ├── payroll/           # Teacher salary → Payroll → Bank payment
│   ├── attendance/        # Daily attendance + Teacher attendance
│   ├── diary/             # Daily diary entries
│   ├── homework/          # Homework + submissions
│   ├── syllabus/          # Syllabus + topics + lecture planning
│   ├── examinations/      # Class tests, surprise tests, term exams, results
│   ├── datesheets/        # Exam date sheets
│   ├── activities/        # Curricular/co/non-curricular
│   ├── announcements/     # School-wide announcements
│   ├── notifications/     # In-app notification center
│   ├── school_calendar/   # Yearly calendar of events
│   ├── reports/           # Report center + PDFs
│   ├── documents/         # Student documents + ID cards
│   ├── audit_logs/        # Audit log model + middleware
│   ├── dashboard/         # Premium admin dashboard
│   └── portal/            # Student / Teacher / Parent portals
├── templates/             # Base + per-app templates
├── static/                # CSS, JS, images
├── media/                 # User uploads
├── requirements/
├── scripts/               # Build/setup scripts
├── tests/                  # Project-wide tests
├── .env.example
├── .gitignore
└── README.md
```

## Quick Start (SQLite — zero setup)

> **Default database is SQLite 3** — no server to install, no credentials to set. The DB lives in a single file `db.sqlite3` at the project root. For a single-school deployment up to a few hundred students, SQLite is perfectly fine.

```bash
# 1. Create & activate virtualenv
python -m venv venv && source venv/bin/activate

# 2. Install dependencies
pip install -r requirements/dev.txt

# 3. Copy environment config (optional for SQLite — defaults work)
cp .env.example .env

# 4. Apply migrations (creates db.sqlite3 in project root)
python manage.py migrate

# 5. Create role groups (Super Admin, Principal, Coordinator, Teacher, Accountant, HR, Receptionist, Student, Parent)
python manage.py create_school_roles

# 6. Generate demo data
python manage.py generate_demo_data

# 7. Run server
python manage.py runserver
```

Open `http://localhost:8000/` and log in with one of these:

| Username     | Password  | Role                  |
|--------------|-----------|-----------------------|
| superadmin   | admin123  | Super Admin           |
| principal    | admin123  | Principal             |
| admin        | admin123  | School Administration |
| coordinator  | admin123  | Coordinator           |
| accountant   | admin123  | Accountant            |
| hr_payroll   | admin123  | HR / Payroll Officer  |
| receptionist | admin123  | Receptionist          |
| teacher1     | admin123  | Teacher               |

## Switching to PostgreSQL (optional, for production)

For high-traffic deployments (multiple schools, hundreds of concurrent fee payments), you can switch to PostgreSQL by setting env vars and running the setup script:

```bash
# 1. Install PostgreSQL (e.g. sudo apt install postgresql postgresql-contrib)
# 2. Edit password in scripts/setup_postgres.sql, then run as postgres user:
sudo -u postgres psql -f scripts/setup_postgres.sql

# 3. Set these in .env (uncomment the lines):
#    DB_ENGINE=django.db.backends.postgresql
#    DB_NAME=school_erp
#    DB_USER=school_erp_user
#    DB_PASSWORD=<password from step 2>
#    DB_HOST=localhost
#    DB_PORT=5432

# 4. Verify connection (optional)
python manage.py check_db

# 5. Migrate against PostgreSQL + load data
python manage.py migrate
python manage.py create_school_roles
python manage.py generate_demo_data
```

The setup script enables `pg_trgm`, `unaccent`, and `citext` extensions, sets the timezone, and sets a 30-second statement timeout to catch runaway queries.

## Management Commands

| Command                                | Description                                             |
|----------------------------------------|---------------------------------------------------------|
| `check_db`                             | Verify database connection (SQLite or PostgreSQL)       |
| `create_school_roles`                  | Create all role groups with appropriate permissions    |
| `generate_demo_data`                   | Seed comprehensive demo data + write `records.txt`     |
| `export_data teachers`                 | Export teachers/staff directory to Excel (.xlsx)        |
| `export_data students`                 | Export full student directory to Excel (.xlsx)         |
| `export_data challans`                 | Export all fee challans + payments to Excel (.xlsx)    |
| `export_data payroll`                  | Export teacher payroll records to Excel (.xlsx)         |
| `export_data all`                      | Export all 4 above at once to project root             |
| `import_students students.csv`          | Bulk import students from CSV (placeholder)            |
| `generate_monthly_challans`            | Generate monthly fee challans for active students       |
| `generate_monthly_fee_report`          | Generate monthly fee collection report                 |
| `generate_attendance_report`           | Generate attendance report                              |

> **Note on `records.txt`:** After running `generate_demo_data`, a file called `records.txt` will appear in the project root. It contains a complete human-readable dump of every demo account, student, teacher, parent, fee summary, payroll record, class/section breakdown, subject list, and financial statistics — perfect for quick reference while testing. The file is auto-regenerated each time you run the command.

> **Note on Excel exports:** `python manage.py export_data <kind>` produces a timestamped `.xlsx` file (e.g. `teachers_20261003_083414.xlsx`) in the project root. Use `--out /path/to/file.xlsx` to specify a custom path. The Excel files include styled headers (green APS theme), proper column widths, and one row per record.

## Major Workflows

### Admission Lifecycle
Draft → Submitted → Verified → Approved → Register Student → Generate Admission Challan → Payment → Completed → Active Student

### Fee Workflow
FeeStructure per (Academic Year, Class, Fee Type) → `FeeService.generate_monthly_challan(student, month)` → FeeChallan with multiple FeeChallanItem(s) → `FeeService.record_payment(challan, amount, method)` → Challan marked PAID (transaction-safe, prevents duplicates) → PDF receipt generated

### Challan Number Lookup (Cashier)
Accountant enters challan number → system fetches student + challan details automatically → confirm payment → receipt generated → challan shows PAID stamp.

### Teacher Payroll (separate from fee accounting)
Teacher → `PayrollService.generate_payroll(teacher, month)` → Draft → Approved → `PayrollService.record_bank_payment()` → Paid → Salary Slip PDF

## Security Notes

- All sensitive banking information (TeacherBankInfo) requires HR/Payroll role or superuser
- Online payments are designed for real payment-gateway integration — the system never marks a payment as successful based on a client-side message; verification must happen server-side
- CSRF protection, password hashing, secure sessions, ORM-only queries throughout
- Audit log middleware tracks key model changes (admissions, fees, results, payroll, announcements, users)

## Production-Grade Security Hardening

### 1. Two-Factor Authentication (TOTP)
Powered by `django-otp` + `django-two-factor-auth`.

- Login flow is now a 2-step wizard: password → TOTP token (only for users who enabled 2FA)
- Visit **`/accounts/security/2fa/`** to see the QR code, scan with Google Authenticator / Authy
- Force-2FA for sensitive roles via `TWO_FACTOR_FORCE_ROLES = {"super_admin", "hr_payroll", "accountant"}` in settings
- Backup tokens supported
- 30-day "Remember this device" cookie

### 2. Rate Limiting
Powered by `django-ratelimit`. Decorated endpoints:

| Endpoint | Limit | Why |
|----------|-------|-----|
| `POST /fees/payment/` (lookup) | 10/min per user | Prevent challan-number enumeration |
| `POST /fees/payment/<pk>/` (cash payment) | 5/min per user | Prevent fast-click payment attacks |
| `POST /fees/challans/<pk>/pay/` (online checkout) | 6/min per user | Prevent checkout-spam attacks |
| `POST /fees/payment/jazzcash/return/` | 10/min per IP | Limit forged-return attacks |

When exceeded, the user sees the custom `accounts/rate_limit.html` page (or JSON `429` for AJAX).

### 3. Content Security Policy (CSP)
Powered by `django-csp`. Configured allowlists for:

- `script-src`: jsdelivr (Bootstrap/Chart.js), jquery.com
- `style-src`: jsdelivr, fonts.googleapis.com
- `font-src`: jsdelivr, fonts.gstatic.com
- `img-src`: self + data: (for QR codes)
- `frame-src`: js.stripe.com (Stripe Checkout iframe)
- `form-action`: self + api.stripe.com
- `object-src`: 'none' (no Flash/Java)
- CSP report endpoint at `/csp-report/`

In dev: `CSP_REPORT_ONLY = True` (log violations, don't block). In prod: violations are blocked.

### 4. Real Payment Gateway Integration

Pluggable architecture in `apps/fees/payment_gateway/`:

```python
class PaymentGateway(abc.ABC):
    @abc.abstractmethod
    def create_checkout(self, challan, request) -> dict: ...
    @abc.abstractmethod
    def verify_payment(self, request) -> tuple[bool, dict]: ...
```

Three concrete gateways:

- **`TestGateway`** — always succeeds; used in dev (no API keys needed)
- **`StripeGateway`** — Stripe Checkout (international cards) with webhook signature verification
- **`JazzCashGateway`** — Pakistan's JazzCash with MD5 secure-hash verification (signed return URL)

Switch with one env var:
```env
ACTIVE_PAYMENT_GATEWAY=test      # or "stripe" or "jazzcash"
```

### Security flow (NEVER trust client-side success)

```
Student clicks "Pay Online"
        ↓
Server creates checkout at gateway (with metadata: challan_no, amount)
        ↓
Redirect to gateway-hosted payment page
        ↓
Student enters card / mobile number
        ↓
Gateway processes payment
        ↓
Gateway calls our webhook / redirect URL with signed payload
        ↓
Server verifies signature using shared secret
        ↓
Only if valid → FeeService.record_payment() (transaction-safe, idempotent)
        ↓
Challan marked PAID, receipt generated, accountant notified
```

**Endpoints:**

| Method | URL | Purpose |
|--------|-----|---------|
| POST | `/fees/challans/<pk>/pay/` | Start online checkout |
| POST | `/fees/webhook/stripe/` | Stripe webhook (CSRF-exempt, signature-verified) |
| POST | `/fees/payment/stripe/return/` | User redirected here after Stripe Checkout (display only) |
| POST | `/fees/payment/jazzcash/return/` | JazzCash signed-return URL |
| GET | `/fees/payment/test/<pk>/<session_id>/` | Test gateway dev-only "checkout" |

## Customization

Most school-specific settings live in `config/settings/base.py`:

```python
SCHOOL_NAME = "Army Public School Lahore"
SCHOOL_CURRENCY_SYMBOL = "Rs."
SCHOOL_LATE_FEE_DAYS = 7
SCHOOL_LATE_FEE_AMOUNT = 500
SCHOOL_REGISTRATION_PREFIX = "SCH"   # → SCH-2026-000123
SCHOOL_CHALLAN_PREFIX = "CH"        # → CH-2026-000145
SCHOOL_RECEIPT_PREFIX = "RC"        # → RC-2026-00145
SCHOOL_EMPLOYEE_PREFIX = "EMP"      # → EMP-0001
```

Or set via environment variables in `.env`.

## License

This is a demonstration project — adapt and use as needed for your institution.
