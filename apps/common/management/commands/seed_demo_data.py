"""
Seed demo data — a fast, idempotent demo dataset for end-to-end testing.

Creates: school, academic year, classes (Grade 8 + 9), sections, subjects,
12 demo user accounts (superadmin + 6 staff roles + 3 teachers + 1 parent + 1 student),
class-teacher assignment, fee structures, paid + unpaid challans, attendance, diary,
homework, syllabus, class test + result, exam + exam result, term result, datesheet,
payroll (draft + approved + paid), activity, announcement, calendar event, audit log.

Usage:
    python manage.py seed_demo_data

Safe to re-run — uses get_or_create everywhere so existing records aren't duplicated.

All demo accounts use the password: admin123
"""
import os
import sys
from datetime import date, timedelta, time
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction

from apps.common.models import (
    AcademicYear, School, SchoolClass, Section, Subject,
)
from apps.parents.models import Parent
from apps.teachers.models import Teacher, EmployeeIDService
from apps.students.models import Student, StudentEnrollment
from apps.fees.models import (
    FeeType, FeeStructure, FeeChallan, FeeChallanItem, FeePayment,
)
from apps.attendance.models import (
    Attendance, ClassTeacherAssignment,
)
from apps.diary.models import DiaryEntry
from apps.homework.models import Homework
from apps.syllabus.models import Syllabus, SyllabusTopic
from apps.examinations.models import (
    ClassTest, TestResult, Exam, ExamSubject, TermResult, ExamResult,
)
from apps.datesheets.models import DateSheet, DateSheetItem
from apps.payroll.models import Payroll, SalaryPayment
from apps.activities.models import Activity, StudentActivity
from apps.announcements.models import Announcement
from apps.school_calendar.models import CalendarEvent
from apps.audit_logs.models import AuditLogService

User = get_user_model()


def _mk_user(username, role, is_superuser=False):
    """Create or get a demo user. Always resets password to admin123."""
    u, _ = User.objects.get_or_create(
        username=username,
        defaults={"role": role, "is_superuser": is_superuser, "is_staff": is_superuser},
    )
    if not u.check_password("admin123"):
        u.set_password("admin123")
        u.save()
    return u


class Command(BaseCommand):
    help = "Seed a fast, idempotent demo dataset for end-to-end testing. All users use password 'admin123'."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset", action="store_true",
            help="Delete existing demo data before seeding (DANGEROUS — wipes everything).",
        )
        parser.add_argument(
            "--no-input", action="store_true",
            help="Don't prompt for confirmation when --reset is used.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options.get("reset"):
            if not options.get("no_input"):
                answer = input("This will DELETE ALL data in the database. Type 'yes' to continue: ")
                if answer.lower() != "yes":
                    self.stdout.write("Aborted.")
                    return
            self.stdout.write("Wiping existing data...")
            # Delete in dependency order to avoid FK constraint violations
            for model in [
                CalendarEvent, Announcement, StudentActivity, Activity,
                SalaryPayment, Payroll,
                DateSheetItem, DateSheet,
                ExamResult, ExamSubject, Exam, TermResult, TestResult, ClassTest,
                SyllabusTopic, Syllabus,
                Homework, DiaryEntry, Attendance, ClassTeacherAssignment,
                FeePayment, FeeChallanItem, FeeChallan, FeeStructure, FeeType,
                StudentEnrollment, Student, Parent, Teacher,
                Subject, Section, SchoolClass, AcademicYear, School,
                User,
            ]:
                qs = model.objects.all()
                count = qs.count()
                if count:
                    qs.delete()
                    self.stdout.write(f"  Deleted {count} {model.__name__}")

        # === School ===
        school, _ = School.objects.get_or_create(
            name="Your School Name",
            defaults={
                "tagline": "Excellence in Education",
                "address": "123 Education Street, Your City, Your Country",
                "phone": "+1 (555) 123-4567",
                "email": "info@yourschool.edu",
            },
        )

        # === Academic year ===
        year, _ = AcademicYear.objects.get_or_create(
            name="2026-2027",
            defaults={
                "start_date": date(2026, 4, 1),
                "end_date": date(2027, 3, 31),
                "is_active": True,
            },
        )

        # === Classes + sections ===
        cls_grade8, _ = SchoolClass.objects.get_or_create(
            name="Grade 8", defaults={"grade_level": "middle", "order": 80}
        )
        cls_grade9, _ = SchoolClass.objects.get_or_create(
            name="Grade 9", defaults={"grade_level": "secondary", "order": 90}
        )
        sec8a, _ = Section.objects.get_or_create(
            school_class=cls_grade8, name="A",
            defaults={"capacity": 40, "subject_group": Section.SubjectGroup.GENERAL},
        )
        sec9a, _ = Section.objects.get_or_create(
            school_class=cls_grade9, name="A",
            defaults={"capacity": 40, "subject_group": Section.SubjectGroup.COMPUTER},
        )

        # === Subjects ===
        math, _ = Subject.objects.get_or_create(name="Mathematics", defaults={"code": "MATH"})
        eng, _ = Subject.objects.get_or_create(name="English", defaults={"code": "ENG"})
        urdu, _ = Subject.objects.get_or_create(name="Urdu", defaults={"code": "URD"})
        sci, _ = Subject.objects.get_or_create(name="Science", defaults={"code": "SCI"})

        # === Demo users (12 accounts) ===
        superadmin = _mk_user("superadmin", "super_admin", is_superuser=True)
        admin = _mk_user("admin", "admin")
        principal = _mk_user("principal", "principal")
        coordinator = _mk_user("coordinator", "coordinator")
        accountant = _mk_user("accountant", "accountant")
        hr = _mk_user("hr_payroll", "hr_payroll")
        receptionist = _mk_user("receptionist", "receptionist")

        # === Teachers (3, each linked to a User) ===
        teacher_users = []
        teachers = []
        for i, name in enumerate([
            ("Mr. Ahmed Khan", "male", "Senior Teacher"),
            ("Ms. Ayesha Siddiqui", "female", "Mathematics Teacher"),
            ("Ms. Hira Akhtar", "female", "English Teacher"),
        ]):
            u = _mk_user(f"teacher{i+1}", "teacher")
            teacher_users.append(u)
            t = Teacher.objects.filter(user=u).first()
            if not t:
                t = Teacher.objects.create(
                    user=u, employee_id=EmployeeIDService.generate(),
                    full_name=name[0], gender=name[1],
                    designation=name[2],
                    joining_date=date(2015, 8, 1),
                    basic_salary=Decimal("45000"),
                    teaching_level=Teacher.TeachingLevel.MIDDLE,
                    staff_category=Teacher.StaffCategory.TEACHING,
                )
            t.classes.add(cls_grade8, cls_grade9)
            t.sections.add(sec8a, sec9a)
            t.subjects.add(math, eng, urdu, sci)
            teachers.append(t)

        # === Parent + Student (linked together) ===
        parent_user = _mk_user("parent1", "parent")
        parent, _ = Parent.objects.get_or_create(
            cnic="35202-1234567-1",
            defaults={
                "full_name": "Mr. Muhammad Raza",
                "relation": Parent.Relation.FATHER,
                "phone": "0300-1234567",
                "occupation": "Engineer",
                "address": "House 12, Street 5, Lahore Cantt",
                "user": parent_user,
            },
        )
        parent_user.parent_profile = parent
        parent_user.save()

        student_user = _mk_user("student1", "student")
        student, _ = Student.objects.get_or_create(
            registration_no="APS-2026-000001",
            defaults={
                "full_name": "Bilal Raza",
                "father_name": "Muhammad Raza",
                "date_of_birth": date(2010, 5, 15),
                "gender": Student.Gender.MALE,
                "cnic_or_bform": "12345-6789012-3",
                "address": "House 12, Street 5, Lahore Cantt",
                "contact_phone": "0300-1234567",
                "parent": parent,
                "current_class": cls_grade8,
                "current_section": sec8a,
                "admission_date": date(2026, 4, 1),
                "user": student_user,
            },
        )
        StudentEnrollment.objects.get_or_create(
            student=student, academic_year=year,
            defaults={
                "school_class": cls_grade8,
                "section": sec8a,
                "roll_no": "8A-01",
                "is_current": True,
            },
        )

        # === Class teacher assignment (so attendance can be marked) ===
        ClassTeacherAssignment.objects.get_or_create(
            academic_year=year, school_class=cls_grade8, section=sec8a,
            defaults={"teacher": teachers[0], "is_active": True},
        )

        # === Fee structures + types ===
        tuition_type, _ = FeeType.objects.get_or_create(
            code="TUI", defaults={"name": "Tuition Fee", "fee_type": "tuition", "default_amount": Decimal("8000")}
        )
        admission_type, _ = FeeType.objects.get_or_create(
            code="ADM", defaults={"name": "Admission Fee", "fee_type": "admission", "default_amount": Decimal("5000")}
        )
        annual_type, _ = FeeType.objects.get_or_create(
            code="ANN", defaults={"name": "Annual Charges", "fee_type": "annual", "default_amount": Decimal("3000")}
        )
        for ft in [tuition_type, annual_type]:
            FeeStructure.objects.get_or_create(
                academic_year=year, school_class=cls_grade8, fee_type=ft,
                defaults={"amount": ft.default_amount, "applies_monthly": (ft.fee_type == "tuition"), "is_active": True},
            )

        # === Monthly fee challan (overdue → late fee applies) ===
        challan, _ = FeeChallan.objects.get_or_create(
            challan_no="CH-2026-000001",
            defaults={
                "student": student, "academic_year": year,
                "month": "October 2026",
                "due_date": timezone.now().date() - timedelta(days=30),
                "status": FeeChallan.Status.UNPAID,
            },
        )
        FeeChallanItem.objects.get_or_create(
            challan=challan, fee_type=tuition_type,
            defaults={"amount": Decimal("8000")},
        )

        # === Paid challan (already paid, demonstrates late-fee freeze) ===
        paid_challan, _ = FeeChallan.objects.get_or_create(
            challan_no="CH-2026-000002",
            defaults={
                "student": student, "academic_year": year,
                "month": "September 2026",
                "due_date": timezone.now().date() - timedelta(days=60),
                "status": FeeChallan.Status.PAID,
                "late_fee_charged": Decimal("500"),
            },
        )
        FeeChallanItem.objects.get_or_create(
            challan=paid_challan, fee_type=tuition_type,
            defaults={"amount": Decimal("8000")},
        )
        FeePayment.objects.get_or_create(
            receipt_no="RC-2026-000001",
            defaults={
                "challan": paid_challan, "amount": Decimal("8500"),
                "method": "cash", "is_successful": True,
                "payment_date": timezone.now().date() - timedelta(days=45),
            },
        )

        # === Attendance record ===
        Attendance.objects.get_or_create(
            student=student, date=timezone.now().date() - timedelta(days=1),
            subject=None,
            defaults={
                "academic_year": year,
                "school_class": cls_grade8,
                "section": sec8a,
                "status": Attendance.Status.PRESENT,
                "marked_by": teacher_users[0],
            },
        )

        # === Diary entry ===
        DiaryEntry.objects.get_or_create(
            academic_year=year, school_class=cls_grade8, section=sec8a, subject=math,
            date=timezone.now().date(),
            defaults={
                "topic": "Algebra — Linear Equations",
                "lecture_summary": "Solved linear equations and assigned homework.",
                "teacher": teacher_users[0],
            },
        )

        # === Homework ===
        Homework.objects.get_or_create(
            academic_year=year, school_class=cls_grade8, section=sec8a,
            subject=math, title="Algebra Practice",
            defaults={
                "description": "Solve exercise 5.1 in textbook.",
                "assigned_date": timezone.now().date(),
                "due_date": timezone.now().date() + timedelta(days=3),
                "total_marks": Decimal("20"),
                "teacher": teacher_users[0],
                "status": Homework.Status.ASSIGNED,
            },
        )

        # === Syllabus + topic ===
        syl, _ = Syllabus.objects.get_or_create(
            academic_year=year, school_class=cls_grade8, subject=math, term=Syllabus.Term.MID,
            defaults={"description": "Mathematics Syllabus 2026-2027 (Mid-Term)"},
        )
        SyllabusTopic.objects.get_or_create(
            syllabus=syl, topic="Linear Equations", chapter="Algebra",
            defaults={
                "priority": 1,
                "expected_completion_date": timezone.now().date() + timedelta(days=30),
                "status": SyllabusTopic.Status.NOT_STARTED,
            },
        )

        # === Class test + result ===
        ct, _ = ClassTest.objects.get_or_create(
            academic_year=year, school_class=cls_grade8, section=sec8a, subject=math,
            title="Algebra Quiz",
            defaults={
                "date": timezone.now().date() - timedelta(days=2),
                "total_marks": Decimal("20"),
                "passing_marks": Decimal("8"),
                "status": "published",
                "teacher": teacher_users[0],
            },
        )
        TestResult.objects.get_or_create(
            test=ct, student=student,
            defaults={"obtained_marks": Decimal("16"), "remarks": "Good work"},
        )

        # === Term exam + result ===
        exam, _ = Exam.objects.get_or_create(
            academic_year=year, term=Exam.Term.MID, name="Mid-Term Examination 2026",
            defaults={
                "start_date": timezone.now().date() - timedelta(days=10),
                "end_date": timezone.now().date() - timedelta(days=5),
                "is_published": True,
            },
        )
        es, _ = ExamSubject.objects.get_or_create(
            exam=exam, subject=math, school_class=cls_grade8,
            defaults={
                "total_marks": Decimal("100"),
                "passing_marks": Decimal("40"),
                "date": timezone.now().date() - timedelta(days=8),
            },
        )
        ExamResult.objects.get_or_create(
            exam_subject=es, student=student,
            defaults={"obtained_marks": Decimal("75")},
        )

        # === Term result ===
        TermResult.objects.get_or_create(
            student=student, academic_year=year, term="mid",
            defaults={
                "total_marks": Decimal("100"),
                "obtained_marks": Decimal("75"),
                "percentage": Decimal("75.00"),
                "grade": "B",
                "status": TermResult.Status.PUBLISHED,
            },
        )

        # === Date sheet + item ===
        ds, _ = DateSheet.objects.get_or_create(
            academic_year=year, title="Mid-Term Date Sheet 2026", school_class=cls_grade8,
            defaults={
                "term": "mid",
                "status": DateSheet.Status.PUBLISHED,
                "published_at": timezone.now(),
                "published_by": admin,
            },
        )
        DateSheetItem.objects.get_or_create(
            datesheet=ds, subject=math, date=date(2026, 11, 1),
            defaults={
                "start_time": time(9, 0),
                "end_time": time(11, 0),
                "room": "101",
                "instructions": "Bring calculators",
            },
        )

        # === Payroll (3 records: DRAFT, APPROVED, PAID) ===
        payroll_draft, _ = Payroll.objects.get_or_create(
            teacher=teachers[0], month="October 2026",
            defaults={
                "basic_salary": teachers[0].basic_salary,
                "allowances": Decimal("5000"),
                "deductions": Decimal("0"),
                "bonus": Decimal("0"),
                "leave_deductions": Decimal("0"),
                "net_salary": teachers[0].basic_salary + Decimal("5000"),
                "status": Payroll.Status.DRAFT,
            },
        )
        payroll_approved, _ = Payroll.objects.get_or_create(
            teacher=teachers[1], month="October 2026",
            defaults={
                "basic_salary": teachers[1].basic_salary,
                "allowances": Decimal("3000"),
                "deductions": Decimal("0"),
                "bonus": Decimal("1000"),
                "leave_deductions": Decimal("0"),
                "net_salary": teachers[1].basic_salary + Decimal("4000"),
                "status": Payroll.Status.APPROVED,
                "approved_by": hr,
            },
        )
        payroll_paid, _ = Payroll.objects.get_or_create(
            teacher=teachers[2], month="October 2026",
            defaults={
                "basic_salary": teachers[2].basic_salary,
                "allowances": Decimal("2000"),
                "deductions": Decimal("0"),
                "bonus": Decimal("0"),
                "leave_deductions": Decimal("0"),
                "net_salary": teachers[2].basic_salary + Decimal("2000"),
                "status": Payroll.Status.PAID,
                "approved_by": hr,
            },
        )
        SalaryPayment.objects.get_or_create(
            payroll=payroll_paid,
            defaults={
                "amount": payroll_paid.net_salary,
                "method": "bank_transfer",
                "transaction_ref": "BNK-OCT2026-001",
                "is_successful": True,
                "recorded_by": hr,
            },
        )

        # === Activity ===
        act, _ = Activity.objects.get_or_create(
            title="Annual Sports Day",
            defaults={
                "academic_year": year,
                "category": Activity.Category.CO_CURRICULAR,
                "date": timezone.now().date() + timedelta(days=14),
                "description": "Inter-class athletic competition",
                "location": "School Playground",
            },
        )
        act.classes.add(cls_grade8)
        StudentActivity.objects.get_or_create(
            activity=act, student=student,
            defaults={"position": "Participant", "remarks": "Participated in 100m race"},
        )

        # === Announcement ===
        Announcement.objects.get_or_create(
            title="Mid-Term Examination Schedule",
            defaults={
                "description": "Mid-term examinations begin Nov 1. Good luck to all students!",
                "academic_year": year,
                "audience": Announcement.Audience.EVERYONE,
                "is_published": True,
                "publish_date": timezone.now(),
                "author": admin,
            },
        )

        # === Calendar event ===
        CalendarEvent.objects.get_or_create(
            title="Annual Sports Day",
            defaults={
                "academic_year": year,
                "start_date": timezone.now().date() + timedelta(days=14),
                "end_date": timezone.now().date() + timedelta(days=14),
                "description": "Inter-class athletic competition",
            },
        )

        # === Audit log ===
        AuditLogService.log(
            user=admin, action="create",
            obj=student,
            description="Seeded demo data via management command",
        )

        # === Summary ===
        self.stdout.write(self.style.SUCCESS("✓ Demo data seeded successfully."))
        self.stdout.write("")
        self.stdout.write("Demo login accounts (password for all: admin123):")
        for username, role_label in [
            ("superadmin", "Super Admin (full access)"),
            ("admin", "School Administration"),
            ("principal", "Principal"),
            ("coordinator", "Coordinator"),
            ("accountant", "Accountant (fees only)"),
            ("hr_payroll", "HR/Payroll Officer (payroll only)"),
            ("receptionist", "Receptionist"),
            ("teacher1", "Teacher (Grade 8-A class teacher)"),
            ("teacher2", "Teacher (not a class teacher)"),
            ("parent1", "Parent (1 child linked)"),
            ("student1", "Student"),
        ]:
            self.stdout.write(f"  - {username:14} → {role_label}")

        self.stdout.write("")
        self.stdout.write("Records created:")
        self.stdout.write(f"  Users:              {User.objects.count()}")
        self.stdout.write(f"  Students:           {Student.objects.count()}")
        self.stdout.write(f"  Teachers:           {Teacher.objects.count()}")
        self.stdout.write(f"  Parents:            {Parent.objects.count()}")
        self.stdout.write(f"  Fee challans:       {FeeChallan.objects.count()}")
        self.stdout.write(f"  Fee payments:       {FeePayment.objects.count()}")
        self.stdout.write(f"  Payrolls:           {Payroll.objects.count()}")
        self.stdout.write(f"  Class tests:       {ClassTest.objects.count()}")
        self.stdout.write(f"  Exams:              {Exam.objects.count()}")
        self.stdout.write(f"  Term results:      {TermResult.objects.count()}")
        self.stdout.write(f"  Date sheets:       {DateSheet.objects.count()}")
        self.stdout.write(f"  Class-teacher assigns: {ClassTeacherAssignment.objects.count()}")
        self.stdout.write(f"  Diary entries:     {DiaryEntry.objects.count()}")
        self.stdout.write(f"  Homework:          {Homework.objects.count()}")
        self.stdout.write(f"  Syllabi:           {Syllabus.objects.count()}")
        self.stdout.write("")
        self.stdout.write("Open http://127.0.0.1:8000/ and log in.")
