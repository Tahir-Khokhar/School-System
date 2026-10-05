"""
Export teachers / students / challans / payroll data to Excel (.xlsx) files.

Usage:
    python manage.py export_data teachers
    python manage.py export_data students
    python manage.py export_data challans
    python manage.py export_data payroll
    python manage.py export_data all     # exports all 4 to /tmp/

Output files go to the project root by default, or to a path you specify:
    python manage.py export_data teachers --out /tmp/teachers.xlsx
"""
import os
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from apps.teachers.models import Teacher
from apps.students.models import Student
from apps.fees.models import FeeChallan, FeePayment
from apps.payroll.models import Payroll


HEADER_FILL = PatternFill(start_color="1B5E20", end_color="1B5E20", fill_type="solid")
HEADER_FONT = Font(color="FFFFFF", bold=True, size=11)
TITLE_FONT = Font(bold=True, size=14, color="1B5E20")
THIN_BORDER = Border(
    left=Side(style="thin", color="DDDDDD"),
    right=Side(style="thin", color="DDDDDD"),
    top=Side(style="thin", color="DDDDDD"),
    bottom=Side(style="thin", color="DDDDDD"),
)


def style_sheet(ws, headers, title=None):
    """Apply consistent styling to a worksheet."""
    if title:
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(headers))
        cell = ws.cell(row=1, column=1, value=title)
        cell.font = TITLE_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[1].height = 24
        header_row = 2
    else:
        header_row = 1
    # Header row
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=header_row, column=col_num, value=header)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = THIN_BORDER
    # Auto-size columns
    for col_num in range(1, len(headers) + 1):
        max_len = max(
            (len(str(ws.cell(row=r, column=col_num).value or "")) for r in range(header_row, ws.max_row + 1)),
            default=10
        )
        ws.column_dimensions[get_column_letter(col_num)].width = min(max_len + 2, 50)


def export_teachers(out_path):
    wb = Workbook()
    ws = wb.active
    ws.title = "Teachers & Staff"

    headers = [
        "Emp ID", "Full Name", "Father Name", "Gender", "CNIC", "Phone", "Email",
        "Qualification", "Experience (yrs)", "Joining Date", "Designation",
        "Teaching Level", "Staff Category", "Subjects", "Classes", "Basic Salary",
        "Status",
    ]
    ws.append(headers)
    for t in Teacher.objects.select_related("user").order_by("employee_id"):
        ws.append([
            t.employee_id, t.full_name, t.father_name, t.gender, t.cnic, t.contact_phone, t.email,
            t.qualification, t.experience_years,
            t.joining_date.strftime("%Y-%m-%d") if t.joining_date else "",
            t.designation,
            t.get_teaching_level_display() if t.teaching_level else "—",
            t.get_staff_category_display(),
            ", ".join(s.name for s in t.subjects.all()) or "—",
            ", ".join(c.name for c in t.classes.all()) or "—",
            float(t.basic_salary) if t.basic_salary else 0,
            t.get_status_display(),
        ])
    style_sheet(ws, headers, title=f"{settings.SCHOOL_NAME} — Teaching & Administration Staff")
    wb.save(out_path)
    return Teacher.objects.count()


def export_students(out_path):
    wb = Workbook()
    ws = wb.active
    ws.title = "Students"

    headers = [
        "Registration #", "Full Name", "Father Name", "Mother Name",
        "Date of Birth", "Gender", "CNIC/B-Form", "Class", "Section",
        "Address", "Contact Phone", "Email", "Admission Date", "Status",
        "Parent Name", "Parent Phone", "Parent CNIC",
    ]
    ws.append(headers)
    for s in Student.objects.select_related(
        "current_class", "current_section", "parent"
    ).order_by("registration_no"):
        ws.append([
            s.registration_no, s.full_name, s.father_name, s.mother_name,
            s.date_of_birth.strftime("%Y-%m-%d") if s.date_of_birth else "",
            s.gender, s.cnic_or_bform,
            s.current_class.name if s.current_class else "—",
            s.current_section.name if s.current_section else "—",
            s.address, s.contact_phone, s.email,
            s.admission_date.strftime("%Y-%m-%d") if s.admission_date else "",
            s.get_status_display(),
            s.parent.full_name if s.parent else "—",
            s.parent.phone if s.parent else "—",
            s.parent.cnic if s.parent else "—",
        ])
    style_sheet(ws, headers, title=f"{settings.SCHOOL_NAME} — Student Directory")
    wb.save(out_path)
    return Student.objects.count()


def export_challans(out_path):
    wb = Workbook()
    ws = wb.active
    ws.title = "Fee Challans"

    headers = [
        "Challan #", "Student Name", "Registration #", "Class", "Section",
        "Academic Year", "Month", "Issue Date", "Due Date",
        "Total Payable", "Total Paid", "Balance", "Status",
    ]
    ws.append(headers)
    for c in FeeChallan.objects.select_related(
        "student", "academic_year", "student__current_class", "student__current_section"
    ).order_by("-issue_date"):
        ws.append([
            c.challan_no, c.student.full_name, c.student.registration_no,
            c.student.current_class.name if c.student.current_class else "—",
            c.student.current_section.name if c.student.current_section else "—",
            c.academic_year.name, c.month or "—",
            c.issue_date.strftime("%Y-%m-%d") if c.issue_date else "",
            c.due_date.strftime("%Y-%m-%d") if c.due_date else "",
            float(c.total_payable), float(c.total_paid), float(c.balance),
            c.get_status_display(),
        ])
    style_sheet(ws, headers, title=f"{settings.SCHOOL_NAME} — Fee Challans")
    wb.save(out_path)
    return FeeChallan.objects.count()


def export_payroll(out_path):
    wb = Workbook()
    ws = wb.active
    ws.title = "Payroll"

    headers = [
        "Emp ID", "Teacher Name", "Month", "Basic Salary", "Allowances",
        "Deductions", "Bonus", "Leave Deductions", "Net Salary", "Status",
        "Approved By", "Payment Date", "Payment Method",
    ]
    ws.append(headers)
    for p in Payroll.objects.select_related("teacher", "approved_by").order_by("-month"):
        payment = getattr(p, "payment", None)
        ws.append([
            p.teacher.employee_id, p.teacher.full_name, p.month,
            float(p.basic_salary), float(p.allowances), float(p.deductions),
            float(p.bonus), float(p.leave_deductions), float(p.net_salary),
            p.get_status_display(),
            p.approved_by.get_full_name() if p.approved_by else "—",
            payment.payment_date.strftime("%Y-%m-%d") if payment and payment.payment_date else "",
            payment.get_method_display() if payment else "—",
        ])
    style_sheet(ws, headers, title=f"{settings.SCHOOL_NAME} — Teacher Payroll")
    wb.save(out_path)
    return Payroll.objects.count()


class Command(BaseCommand):
    help = "Export teachers / students / challans / payroll to Excel (.xlsx)"

    def add_arguments(self, parser):
        parser.add_argument(
            "kind",
            choices=["teachers", "students", "challans", "payroll", "all"],
            help="What to export",
        )
        parser.add_argument(
            "--out", "-o",
            default="",
            help="Output path (default: project root, named <kind>_<timestamp>.xlsx)",
        )

    def handle(self, *args, **options):
        kind = options["kind"]
        out_arg = options["out"]
        base_dir = Path(settings.BASE_DIR)

        # Generate timestamped filename if not provided
        from datetime import datetime
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        exports = {
            "teachers": ("teachers", export_teachers),
            "students": ("students", export_students),
            "challans": ("challans", export_challans),
            "payroll":  ("payroll",  export_payroll),
        }
        if kind == "all":
            kinds_to_run = list(exports.keys())
        else:
            kinds_to_run = [kind]

        for k in kinds_to_run:
            label, func = exports[k]
            out_path = Path(out_arg) if out_arg else base_dir / f"{label}_{ts}.xlsx"
            count = func(out_path)
            self.stdout.write(self.style.SUCCESS(
                f"✓ Exported {count} {label} records to {out_path}"
            ))
