"""
End-to-end functional verification script.
Creates real records for every workflow: academic year, classes, sections,
subjects, teachers, students, parents, fee structures, challans, payments,
payroll, attendance, diary, homework, datesheets, exams, etc.

Run with: python manage.py shell < scripts/seed_functional_test_data.py
"""
import os
import sys
from datetime import date, timedelta, time
from decimal import Decimal

import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction

from apps.common.models import AcademicYear, School, SchoolClass, Section, Subject
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
from apps.audit_logs.models import AuditLog

User = get_user_model()


@transaction.atomic
def seed():
    school, _ = School.objects.get_or_create(
        name="Army Public School Lahore",
        defaults={
            "tagline": "I shall rise and shine",
            "address": "Tufail Road, Lahore Cantt, Lahore, Pakistan",
            "phone": "+92 42 9920 2040",
            "email": "info@apslahore.edu.pk",
        },
    )

    year, _ = AcademicYear.objects.get_or_create(
        name="2026-2027",
        defaults={
            "start_date": date(2026, 4, 1),
            "end_date": date(2027, 3, 31),
            "is_active": True,
        },
    )

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

    math, _ = Subject.objects.get_or_create(name="Mathematics", defaults={"code": "MATH"})
    eng, _ = Subject.objects.get_or_create(name="English", defaults={"code": "ENG"})
    urdu, _ = Subject.objects.get_or_create(name="Urdu", defaults={"code": "URD"})
    sci, _ = Subject.objects.get_or_create(name="Science", defaults={"code": "SCI"})
    isl, _ = Subject.objects.get_or_create(name="Islamiat", defaults={"code": "ISL"})

    def mk_user(username, role, is_superuser=False):
        u, _ = User.objects.get_or_create(
            username=username,
            defaults={"role": role, "is_superuser": is_superuser, "is_staff": is_superuser}
        )
        if not u.check_password("admin123"):
            u.set_password("admin123")
            u.save()
        return u

    superadmin = mk_user("superadmin", "super_admin", is_superuser=True)
    admin = mk_user("admin", "admin")
    principal = mk_user("principal", "principal")
    coordinator = mk_user("coordinator", "coordinator")
    accountant = mk_user("accountant", "accountant")
    hr = mk_user("hr_payroll", "hr_payroll")
    receptionist = mk_user("receptionist", "receptionist")

    teacher_users = []
    teachers = []
    for i, name in enumerate([
        ("Mr. Ahmed Khan", "male", "Senior Teacher"),
        ("Ms. Ayesha Siddiqui", "female", "Mathematics Teacher"),
        ("Ms. Hira Akhtar", "female", "English Teacher"),
    ]):
        uname = f"teacher{i+1}"
        u = mk_user(uname, "teacher")
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

    parent_user = mk_user("parent1", "parent")
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

    student_user = mk_user("student1", "student")
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

    cta, _ = ClassTeacherAssignment.objects.get_or_create(
        academic_year=year, school_class=cls_grade8, section=sec8a,
        defaults={"teacher": teachers[0], "is_active": True},
    )

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

    challan = FeeChallan.objects.filter(student=student, month="October 2026").first()
    if not challan:
        challan = FeeChallan.objects.create(
            challan_no="CH-2026-000001",
            student=student, academic_year=year,
            month="October 2026",
            due_date=timezone.now().date() - timedelta(days=30),
            status=FeeChallan.Status.UNPAID,
        )
        FeeChallanItem.objects.create(challan=challan, fee_type=tuition_type, amount=Decimal("8000"))

    paid_challan = FeeChallan.objects.filter(student=student, month="September 2026").first()
    if not paid_challan:
        paid_challan = FeeChallan.objects.create(
            challan_no="CH-2026-000002",
            student=student, academic_year=year,
            month="September 2026",
            due_date=timezone.now().date() - timedelta(days=60),
            status=FeeChallan.Status.PAID,
            late_fee_charged=Decimal("500"),
        )
        FeeChallanItem.objects.create(challan=paid_challan, fee_type=tuition_type, amount=Decimal("8000"))
        FeePayment.objects.create(
            challan=paid_challan, amount=Decimal("8500"),
            method="cash", is_successful=True,
            payment_date=timezone.now().date() - timedelta(days=45),
            receipt_no="RC-2026-000001",
        )

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

    DiaryEntry.objects.get_or_create(
        academic_year=year, school_class=cls_grade8, section=sec8a, subject=math,
        date=timezone.now().date(),
        defaults={
            "topic": "Algebra — Linear Equations",
            "lecture_summary": "Solved linear equations and assigned homework.",
            "teacher": teacher_users[0],
        },
    )

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

    term_result, _ = TermResult.objects.get_or_create(
        student=student, academic_year=year, term="mid",
        defaults={
            "total_marks": Decimal("100"),
            "obtained_marks": Decimal("75"),
            "percentage": Decimal("75.00"),
            "grade": "B",
            "status": TermResult.Status.PUBLISHED,
        },
    )

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

    CalendarEvent.objects.get_or_create(
        title="Annual Sports Day",
        defaults={
            "academic_year": year,
            "start_date": timezone.now().date() + timedelta(days=14),
            "end_date": timezone.now().date() + timedelta(days=14),
            "description": "Inter-class athletic competition",
        },
    )

    from apps.audit_logs.models import AuditLogService
    AuditLogService.log(user=admin, action="create",
                        obj=student,
                        description="Seeded test data via script")

    print("Functional test data seeded.")
    print(f"  Users: {User.objects.count()}")
    print(f"  Students: {Student.objects.count()}")
    print(f"  Teachers: {Teacher.objects.count()}")
    print(f"  Parents: {Parent.objects.count()}")
    print(f"  Challans: {FeeChallan.objects.count()}")
    print(f"  Payments: {FeePayment.objects.count()}")
    print(f"  Payrolls: {Payroll.objects.count()}")
    print(f"  Class Tests: {ClassTest.objects.count()}")
    print(f"  Exams: {Exam.objects.count()}")
    print(f"  Term Results: {TermResult.objects.count()}")
    print(f"  Date Sheets: {DateSheet.objects.count()}")
    print(f"  Class Teacher Assignments: {ClassTeacherAssignment.objects.count()}")
    print(f"  Diary Entries: {DiaryEntry.objects.count()}")
    print(f"  Homework: {Homework.objects.count()}")
    print(f"  Syllabi: {Syllabus.objects.count()}")


if __name__ == "__main__":
    seed()
