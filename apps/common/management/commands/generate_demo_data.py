"""
Generate demo data — academic year, classes, subjects, teachers, students,
parents, fee structures, challans, payments, attendance, homework, etc.
Usage: python manage.py generate_demo_data

After running, also writes records.txt with all demo accounts, students,
teachers, parents, and key financial records.
"""
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
import random

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from django.conf import settings

BASE_DIR = Path(settings.BASE_DIR)

from apps.accounts.models import User
from apps.common.models import (
    AcademicYear, School, SchoolClass, Section, Subject,
)
from apps.parents.models import Parent
from apps.teachers.models import Teacher, EmployeeIDService, TeacherBankInfo
from apps.students.models import Student, RegistrationNumberService, StudentEnrollment
from apps.fees.models import (
    FeeType, FeeStructure, FeeChallan, FeeChallanItem, FeePayment,
)
from apps.fees.services import FeeService
from apps.attendance.models import Attendance, AttendanceService
from apps.diary.models import DiaryEntry
from apps.homework.models import Homework
from apps.syllabus.models import Syllabus, SyllabusTopic
from apps.examinations.models import ClassTest, TestResult, Exam, TermResult
from apps.datesheets.models import DateSheet, DateSheetItem
from apps.payroll.models import Payroll, PayrollService, SalaryPayment
from apps.activities.models import Activity, StudentActivity
from apps.announcements.models import Announcement
from apps.school_calendar.models import CalendarEvent


FIRST_NAMES = ["Muhammad","Ayesha","Fatima","Ahmed","Hassan","Sara","Bilal","Zainab","Hira","Omar",
               "Ayesha","Asma","Hamza","Iqra","Khadija","Rida","Yasir","Sadia","Imran","Nadia",
               "Tariq","Rubab","Junaid","Mahnoor","Sufyan","Anum","Faizan","Nida","Zeeshan","Hina"]
LAST_NAMES = ["Ahmed","Khan","Raza","Ali","Hussain","Noor","Malik","Siddiqui","Akhtar","Sheikh",
              "Ansari","Qureshi","Bilal","Rashid","Mahmood","Iqbal","Shah","Tariq","Jamal","Hassan"]

TEACHER_DESIGNATIONS = ["Senior Teacher","Mathematics Teacher","English Teacher",
                        "Science Teacher","Computer Teacher","Urdu Teacher","Islamiat Teacher"]


def make_password(): return "admin123"


class Command(BaseCommand):
    help = "Generate comprehensive demo data for School ERP."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Generating demo data...")

        # 1. School
        school, _ = School.objects.get_or_create(
            name="Army Public School Lahore",
            defaults={
                "tagline": "I shall rise and shine",
                "address": "Tufail Road, Lahore Cantt, Lahore, Pakistan",
                "phone": "+92 42 9920 2040",
                "email": "info@apslahore.edu.pk",
            },
        )

        # 2. Academic Year
        ay, _ = AcademicYear.objects.get_or_create(
            name="2026–2027",
            defaults={
                "start_date": date(2026, 4, 1),
                "end_date": date(2027, 3, 31),
                "is_active": True,
            },
        )
        # Ensure no other active year
        AcademicYear.objects.exclude(pk=ay.pk).update(is_active=False)

        # 3. Subjects — comprehensive set covering Primary (1-5), Middle (6-8), Secondary (9-10)
        subjects_data = [
            # Core subjects (taught at every grade)
            ("Mathematics", "MAT", True),
            ("English", "ENG", True),
            ("Urdu", "URD", True),
            ("Islamiat", "ISL", True),
            ("Computer Science", "CS", True),
            # Primary subjects (Grade 1-5)
            ("General Science", "GSC", True),
            ("Social Studies", "SST", True),
            ("General Knowledge", "GK", True),
            ("Art & Craft", "ART", False),
            ("Quran with Tajweed", "QUR", True),
            ("Handwriting", "HW", False),
            ("Physical Education", "PED", False),
            ("Nazra Quran", "NZQ", True),
            # Middle subjects (Grade 6-8)
            ("Physics", "PHY", True),
            ("Chemistry", "CHE", True),
            ("Biology", "BIO", True),
            ("Pakistan Studies", "PAK", True),
            ("History & Geography", "HIS", True),
            ("Arabic", "ARB", False),
            ("Punjabi", "PUN", False),
            # Secondary subjects (Grade 9-10)
            ("Computer Science (Elective)", "CSE", False),
            ("Biology (Elective)", "BIE", False),
            ("Additional Mathematics", "ADM", False),
            ("Civics", "CIV", False),
            ("Ethics", "ETH", False),
        ]
        subjects = []
        for name, code, compulsory in subjects_data:
            s, _ = Subject.objects.get_or_create(
                code=code, defaults={"name": name, "is_compulsory": compulsory, "is_active": True}
            )
            subjects.append(s)

        # 4. Classes (Grade 1-10) + 6 Sections per class
        # For Grade 9 and 10: sections A, B, C = Computer group; D, E, F = Biology group
        classes_data = [
            ("Grade 1",  "pre",      1),
            ("Grade 2",  "pre",      2),
            ("Grade 3",  "primary",  3),
            ("Grade 4",  "primary",  4),
            ("Grade 5",  "primary",  5),
            ("Grade 6",  "middle",   6),
            ("Grade 7",  "middle",   7),
            ("Grade 8",  "middle",   8),
            ("Grade 9",  "secondary", 9),
            ("Grade 10", "secondary", 10),
        ]
        SECTION_NAMES = ["A", "B", "C", "D", "E", "F"]
        school_classes = []
        for cname, level, order in classes_data:
            c, _ = SchoolClass.objects.get_or_create(
                name=cname, defaults={"grade_level": level, "order": order}
            )
            school_classes.append(c)
            for i, sec_name in enumerate(SECTION_NAMES):
                # For Grade 9 and 10: first 3 sections = Computer, last 3 = Bio
                if cname in ("Grade 9", "Grade 10"):
                    if i < 3:
                        group = Section.SubjectGroup.COMPUTER
                    else:
                        group = Section.SubjectGroup.BIO
                else:
                    group = Section.SubjectGroup.NONE
                Section.objects.get_or_create(
                    school_class=c, name=sec_name,
                    defaults={"capacity": 35, "subject_group": group}
                )

        # 5. Super admin + role users
        superadmin, _ = User.objects.get_or_create(
            username="superadmin",
            defaults={
                "email": "superadmin@apslahore.edu.pk",
                "first_name": "Super", "last_name": "Admin",
                "role": User.Role.SUPER_ADMIN, "is_staff": True, "is_superuser": True,
                "is_active": True,
            },
        )
        superadmin.set_password(make_password())
        superadmin.save()

        role_users = [
            ("principal", User.Role.PRINCIPAL, "Principal", "Raza"),
            ("admin", User.Role.ADMIN, "Admin", "Khan"),
            ("coordinator", User.Role.COORDINATOR, "Coordinator", "Noor"),
            ("accountant", User.Role.ACCOUNTANT, "Accountant", "Ali"),
            ("hr_payroll", User.Role.HR_PAYROLL, "HR", "Siddiqui"),
            ("receptionist", User.Role.RECEPTIONIST, "Reception", "Akhtar"),
        ]
        for uname, role, fn, ln in role_users:
            u, _ = User.objects.get_or_create(
                username=uname,
                defaults={
                    "email": f"{uname}@apslahore.edu.pk",
                    "first_name": fn, "last_name": ln,
                    "role": role, "is_staff": True, "is_active": True,
                },
            )
            u.set_password(make_password())
            u.save()

        # 6. Teachers (35+ teachers organized by level + gender + subject)
        # Real Pakistani names with male/female for each subject at each level
        TEACHERS_BY_LEVEL = [
            # (level, [(name, gender, subject, designation), ...])
            ("primary", [
                # Primary — class teachers (each handles multiple subjects in 1 section)
                ("Saima Tariq", "female", "English", "Primary Class Teacher"),
                ("Nadia Imran", "female", "English", "Primary Class Teacher"),
                ("Rubab Aslam", "female", "Mathematics", "Primary Class Teacher"),
                ("Ayesha Saleem", "female", "Mathematics", "Primary Class Teacher"),
                ("Imran Yousaf", "male", "Urdu", "Primary Class Teacher"),
                ("Hassan Javed", "male", "Islamiat", "Primary Class Teacher"),
                ("Fatima Sheikh", "female", "Science", "Primary Class Teacher"),
                ("Sana Akram", "female", "Social Studies", "Primary Class Teacher"),
                ("Bilal Raza", "male", "Computer Science", "Primary Computer Teacher"),
                ("Mahnoor Khan", "female", "English", "Primary Class Teacher"),
            ]),
            ("middle", [
                # Middle — subject specialists
                ("Ahmed Raza", "male", "Mathematics", "Mathematics Teacher"),
                ("Sara Iqbal", "female", "Mathematics", "Mathematics Teacher"),
                ("Tariq Mehmood", "male", "English", "English Teacher"),
                ("Hina Qureshi", "female", "English", "English Teacher"),
                ("Imran Siddiqui", "male", "Urdu", "Urdu Teacher"),
                ("Zainab Akhtar", "female", "Urdu", "Urdu Teacher"),
                ("Omar Farooq", "male", "Islamiat", "Islamiat Teacher"),
                ("Ayesha Noor", "female", "Islamiat", "Islamiat Teacher"),
                ("Hamza Khan", "male", "Computer Science", "Computer Teacher"),
                ("Fatima Bilal", "female", "Computer Science", "Computer Teacher"),
                ("Zeeshan Ali", "male", "Physics", "Science Teacher"),
                ("Saba Rashid", "female", "Chemistry", "Science Teacher"),
                ("Junaid Akbar", "male", "Biology", "Science Teacher"),
            ]),
            ("secondary", [
                # Secondary — senior subject specialists for Grade 9-10
                ("Khalid Mehmood", "male", "Mathematics", "Senior Mathematics Teacher"),
                ("Rabia Anwar", "female", "Mathematics", "Senior Mathematics Teacher"),
                ("Aslam Shah", "male", "Physics", "Senior Physics Teacher"),
                ("Nimra Tariq", "female", "Physics", "Senior Physics Teacher"),
                ("Tariq Aziz", "male", "Chemistry", "Senior Chemistry Teacher"),
                ("Samina Khalid", "female", "Chemistry", "Senior Chemistry Teacher"),
                ("Fahad Mahmood", "male", "Biology", "Senior Biology Teacher"),
                ("Mariam Yousaf", "female", "Biology", "Senior Biology Teacher"),
                ("Rizwan Akhtar", "male", "Computer Science", "Senior CS Teacher"),
                ("Amna Saleem", "female", "Computer Science", "Senior CS Teacher"),
                ("Sufyan Khan", "male", "English", "Senior English Teacher"),
                ("Khadija Aslam", "female", "English", "Senior English Teacher"),
                ("Adnan Malik", "male", "Pakistan Studies", "Pak Studies Teacher"),
                ("Rida Bashir", "female", "Pakistan Studies", "Pak Studies Teacher"),
            ]),
        ]

        # Administration staff (non-teaching)
        ADMIN_STAFF = [
            ("Tariq Hussain", "male", "Vice Principal"),
            ("Sadia Akram", "female", "Senior Mistress"),
            ("Imran Yousaf", "male", "Academic Coordinator"),
            ("Nadia Sheikh", "female", "Examination Incharge"),
            ("Asad Rauf", "male", "Discipline Incharge"),
            ("Hina Tariq", "female", "Activity Coordinator"),
        ]

        teachers = []
        teacher_counter = 0

        # Create teaching staff by level
        for level, teacher_specs in TEACHERS_BY_LEVEL:
            level_classes = [c for c in school_classes if (
                level == "primary" and c.order <= 5
                or level == "middle" and 6 <= c.order <= 8
                or level == "secondary" and c.order >= 9
            )]
            for full_name, gender, subject_name, designation in teacher_specs:
                teacher_counter += 1
                uname = f"teacher{teacher_counter}"
                # Convert full_name to first/last for the user model
                parts = full_name.split()
                fname, lname = parts[0], " ".join(parts[1:]) or parts[0]
                tuser, _ = User.objects.get_or_create(
                    username=uname,
                    defaults={
                        "email": f"{uname}@apslahore.edu.pk",
                        "first_name": fname, "last_name": lname,
                        "role": User.Role.TEACHER, "is_staff": True, "is_active": True,
                    },
                )
                tuser.set_password(make_password())
                tuser.save()

                # Salary based on level
                base = {"primary": 35000, "middle": 50000, "secondary": 70000}[level]
                t, _ = Teacher.objects.get_or_create(
                    employee_id=f"EMP-{teacher_counter:04d}",
                    defaults={
                        "user": tuser,
                        "full_name": full_name,
                        "father_name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
                        "cnic": f"35202-{random.randint(1000000,9999999)}-{random.randint(0,9)}",
                        "contact_phone": f"+923{random.randint(100000000,999999999)}",
                        "email": tuser.email,
                        "gender": gender,
                        "qualification": random.choice(["B.Ed", "M.Ed", "MSc", "MA", "MPhil"]),
                        "experience_years": random.randint(1, 25),
                        "joining_date": date(2015 + (teacher_counter % 9), (teacher_counter % 12) + 1, 15),
                        "designation": designation,
                        "basic_salary": Decimal(base + random.choice([0, 5000, 10000, 15000])),
                        "status": Teacher.Status.ACTIVE,
                        "teaching_level": level,
                        "staff_category": Teacher.StaffCategory.TEACHING,
                    },
                )
                # Assign classes within level + matching subject
                if level_classes:
                    t.classes.set(random.sample(level_classes, min(2, len(level_classes))))
                subject_obj = next((s for s in subjects if s.name == subject_name), subjects[0])
                t.subjects.set([subject_obj])
                # Sections from assigned classes
                sections_to_assign = list(Section.objects.filter(school_class__in=t.classes.all())[:2])
                if sections_to_assign:
                    t.sections.set(sections_to_assign)

                # Bank info
                TeacherBankInfo.objects.get_or_create(
                    teacher=t,
                    defaults={
                        "bank_name": random.choice(["HBL", "MCB", "UBL", "ABL", "Bank Al Falah"]),
                        "account_title": t.full_name,
                        "account_number": f"PK{random.randint(10**16, 10**17-1)}",
                        "iban": f"PK36SCBL0000{random.randint(10**12,10**13-1)}",
                    },
                )
                teachers.append(t)

        # Create administration staff (non-teaching, but stored as Teacher records
        # with staff_category=admin so they appear in the staff directory)
        for full_name, gender, designation in ADMIN_STAFF:
            teacher_counter += 1
            uname = f"admin_staff{teacher_counter}"
            parts = full_name.split()
            fname, lname = parts[0], " ".join(parts[1:]) or parts[0]
            tuser, _ = User.objects.get_or_create(
                username=uname,
                defaults={
                    "email": f"{uname}@apslahore.edu.pk",
                    "first_name": fname, "last_name": lname,
                    "role": User.Role.ADMIN, "is_staff": True, "is_active": True,
                },
            )
            tuser.set_password(make_password())
            tuser.save()

            t, _ = Teacher.objects.get_or_create(
                employee_id=f"EMP-{teacher_counter:04d}",
                defaults={
                    "user": tuser,
                    "full_name": full_name,
                    "father_name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
                    "cnic": f"35202-{random.randint(1000000,9999999)}-{random.randint(0,9)}",
                    "contact_phone": f"+923{random.randint(100000000,999999999)}",
                    "email": tuser.email,
                    "gender": gender,
                    "qualification": random.choice(["MBA", "MPA", "M.Ed"]),
                    "experience_years": random.randint(5, 25),
                    "joining_date": date(2015 + (teacher_counter % 9), (teacher_counter % 12) + 1, 15),
                    "designation": designation,
                    "basic_salary": Decimal(random.choice([60000, 75000, 90000, 120000])),
                    "status": Teacher.Status.ACTIVE,
                    "teaching_level": Teacher.TeachingLevel.ALL_LEVELS,
                    "staff_category": Teacher.StaffCategory.ADMIN,
                },
            )
            TeacherBankInfo.objects.get_or_create(
                teacher=t,
                defaults={
                    "bank_name": random.choice(["HBL", "MCB", "UBL", "ABL", "Bank Al Falah"]),
                    "account_title": t.full_name,
                    "account_number": f"PK{random.randint(10**16, 10**17-1)}",
                    "iban": f"PK36SCBL0000{random.randint(10**12,10**13-1)}",
                },
            )
            teachers.append(t)

        # 7. Parents (pool of 80 unique parents) + Students (30 per section)
        # Total: 10 classes × 6 sections × 30 students = 1800 students
        parents = []
        for i in range(80):
            fname = random.choice(FIRST_NAMES)
            lname = random.choice(LAST_NAMES)
            p, _ = Parent.objects.get_or_create(
                cnic=f"35202-{random.randint(10000000,99999999)}-{random.randint(0,9)}",
                defaults={
                    "full_name": f"{fname} {lname}",
                    "relation": Parent.Relation.FATHER,
                    "phone": f"+923{random.randint(100000000,999999999)}",
                    "email": f"parent{i+1}@apslahore.edu.pk",
                    "occupation": random.choice(["Army Officer","Engineer","Doctor","Businessman","Teacher","Banker","Govt Servant"]),
                    "address": f"House {random.randint(1,400)}, Block {chr(65+random.randint(0,25))}, Lahore Cantt",
                },
            )
            parents.append(p)

        students = []
        student_counter = 0
        # For each class, generate 30 students per section (180 per class)
        for cls in school_classes:
            # Year-of-birth based on grade level (approximate ages)
            base_year = 2026 - int(cls.name.replace("Grade ", "").strip()) - 5  # ~5yo + grade offset
            for section in cls.sections.all():
                for _ in range(30):
                    student_counter += 1
                    fname = random.choice(FIRST_NAMES)
                    lname = random.choice(LAST_NAMES)
                    p = random.choice(parents)
                    reg_no = RegistrationNumberService.generate()

                    s = Student.objects.create(
                        registration_no=reg_no,
                        full_name=f"{fname} {lname}",
                        father_name=p.full_name,
                        date_of_birth=date(
                            base_year + random.randint(0, 1),  # mostly same year, slight variance
                            random.randint(1, 12),
                            random.randint(1, 28),
                        ),
                        gender=random.choice([Student.Gender.MALE, Student.Gender.FEMALE]),
                        cnic_or_bform=f"B-Form-{random.randint(10**9,10**10-1)}",
                        address=p.address,
                        contact_phone=p.phone,
                        parent=p,
                        current_class=cls,
                        current_section=section,
                        admission_date=date(2026, 4, random.randint(1, 28)),
                        status=Student.Status.ACTIVE,
                    )
                    students.append(s)

                    StudentEnrollment.objects.create(
                        student=s, academic_year=ay, school_class=cls, section=section,
                        roll_no=f"{student_counter:04d}", is_current=True,
                    )

        # 7b. Create User accounts for ALL students + ALL parents
        # Username for student = registration_no (e.g. "APS-2026-000001")
        # Username for parent   = phone number digits (e.g. "3312345678")
        # Password for ALL accounts: admin123
        student_user_count = 0
        parent_user_count = 0
        self.stdout.write(f"  Creating user accounts for {len(students)} students + {len(parents)} parents...")

        for s in students:
            # Username = registration_no (e.g., "APS-2026-000001")
            uname = s.registration_no
            u, created = User.objects.get_or_create(
                username=uname,
                defaults={
                    "email": f"{uname.lower()}@apslahore.edu.pk",
                    "first_name": s.full_name.split()[0] if s.full_name else uname,
                    "last_name": " ".join(s.full_name.split()[1:]) or "",
                    "role": User.Role.STUDENT,
                    "is_active": True,
                },
            )
            if created:
                u.set_password("admin123")
                u.save()
                student_user_count += 1
            s.user = u
            s.save()

        for p in parents:
            # Username = phone number digits (e.g., "+923331234567" → "3331234567")
            phone_digits = "".join(c for c in (p.phone or "") if c.isdigit())
            # Strip the country code "92" prefix if present
            if phone_digits.startswith("92") and len(phone_digits) > 10:
                phone_digits = phone_digits[2:]
            uname = phone_digits or f"parent{p.id}"
            # Avoid duplicate usernames
            existing = User.objects.filter(username=uname).first()
            if existing:
                uname = f"{uname}_{p.id}"
            u, created = User.objects.get_or_create(
                username=uname,
                defaults={
                    "email": p.email or f"{uname}@apslahore.edu.pk",
                    "first_name": p.full_name.split()[0] if p.full_name else uname,
                    "last_name": " ".join(p.full_name.split()[1:]) or "",
                    "role": User.Role.PARENT,
                    "is_active": True,
                },
            )
            if created:
                u.set_password("admin123")
                u.save()
                parent_user_count += 1
            p.user = u
            p.save()

        # Also create a few "easy-to-remember" demo logins
        # student1..student5 → LINK to first 5 students (override the registration_no link
        # so the easy login actually has portal access via Student.user OneToOneField)
        easy_students = ["student1", "student2", "student3", "student4", "student5"]
        for i, uname in enumerate(easy_students):
            if i >= len(students):
                break
            s = students[i]
            u, _ = User.objects.get_or_create(
                username=uname,
                defaults={
                    "email": f"{uname}@apslahore.edu.pk",
                    "first_name": s.full_name.split()[0] if s.full_name else uname,
                    "last_name": " ".join(s.full_name.split()[1:]) or "",
                    "role": User.Role.STUDENT, "is_active": True,
                },
            )
            u.set_password("admin123")
            u.save()
            # LINK the easy user to this student (overrides the registration_no user link)
            s.user = u
            s.save()

        easy_parents = ["parent1", "parent2", "parent3"]
        for i, uname in enumerate(easy_parents):
            if i >= len(parents):
                break
            p = parents[i]
            u, _ = User.objects.get_or_create(
                username=uname,
                defaults={
                    "email": f"{uname}@apslahore.edu.pk",
                    "first_name": p.full_name.split()[0] if p.full_name else uname,
                    "last_name": " ".join(p.full_name.split()[1:]) or "",
                    "role": User.Role.PARENT, "is_active": True,
                },
            )
            u.set_password("admin123")
            u.save()
            # Link the easy parent account to this parent
            p.user = u
            p.save()

        self.stdout.write(f"  ✓ Created {student_user_count} student users + {parent_user_count} parent users (password: admin123)")

        # 8. Fee types + structures
        fee_types_data = [
            ("Tuition Fee","TUI","tuition",8000),
            ("Admission Fee","ADM","admission",5000),
            ("Annual Charges","ANN","annual",2000),
            ("Examination Fee","EXM","examination",1000),
            ("Computer Lab","LAB","computer",500),
            ("Library Fee","LIB","library",300),
            ("Sports Fee","SPO","sports",400),
            ("Transport","TRN","transport",1500),
        ]
        fee_types = []
        for name, code, ftype, default_amt in fee_types_data:
            ft, _ = FeeType.objects.get_or_create(
                code=code,
                defaults={"name": name, "fee_type": ftype, "default_amount": default_amt},
            )
            fee_types.append(ft)

        # Tuition fee structure per class
        for c in school_classes:
            for ft in fee_types[:1]:  # Only tuition monthly
                FeeStructure.objects.get_or_create(
                    academic_year=ay, school_class=c, fee_type=ft,
                    defaults={"amount": Decimal(8000 + (c.order * 500)), "applies_monthly": True},
                )

        # 9. Generate monthly challans for active students
        # With 1800 students, we generate 4 months of challans per student (7200 total)
        # to keep demo-data generation fast on SQLite:
        #   - April = paid
        #   - May = paid
        #   - June = partial
        #   - July = unpaid (defaulter, overdue)
        months = ["April 2026", "May 2026", "June 2026", "July 2026"]
        total_students = len(students)
        for i, s in enumerate(students, 1):
            if i % 200 == 0:
                self.stdout.write(f"  Generating challans for student {i}/{total_students}...")
            # April — paid
            try:
                ch = FeeService.generate_monthly_challan(s, months[0], ay, superadmin)
                if ch.status != FeeChallan.Status.PAID:
                    FeeService.record_payment(ch, ch.total_payable, "cash", superadmin,
                                               payment_date=date(2026, 4, 15))
            except Exception:
                continue
            # May — paid
            try:
                ch = FeeService.generate_monthly_challan(s, months[1], ay, superadmin)
                if ch.status != FeeChallan.Status.PAID:
                    FeeService.record_payment(ch, ch.total_payable, "cash", superadmin,
                                               payment_date=date(2026, 5, 15))
            except Exception:
                pass
            # June — partially paid
            try:
                ch = FeeService.generate_monthly_challan(s, months[2], ay, superadmin)
                FeeService.record_payment(ch, ch.total_payable / 2, "cash", superadmin,
                                           payment_date=date(2026, 6, 10))
            except Exception:
                pass
            # July — unpaid, overdue
            try:
                ch = FeeService.generate_monthly_challan(s, months[3], ay, superadmin)
                ch.due_date = date(2026, 7, 30)  # in the past → marked overdue
                ch.save()
                FeeService.update_challan_status(ch)
            except Exception:
                pass

        # 10. Payroll — generate last month's payroll + pay
        for t in teachers:
            payroll = PayrollService.generate_payroll(t, "September 2026", superadmin)
            payroll.status = Payroll.Status.APPROVED
            payroll.approved_by = superadmin
            payroll.save()
            PayrollService.record_bank_payment(
                payroll, superadmin, method="bank_transfer",
                transaction_ref=f"TXN-{random.randint(10000,99999)}",
            )
            # This month's — draft
            PayrollService.generate_payroll(t, "October 2026", superadmin)

        # 11. Attendance — today's marks for first class
        if students and school_classes:
            cls = school_classes[0]
            today = timezone.now().date()
            class_students = [s for s in students if s.current_class == cls][:5]
            records = [{"student_id": s.pk,
                        "status": random.choice(["present","present","present","absent","late"])}
                       for s in class_students]
            try:
                AttendanceService.mark_attendance(
                    school_class_id=cls.pk, section_id=cls.sections.first().pk,
                    date=today, subject_id=subjects[0].pk,
                    records=records, user=superadmin,
                )
            except Exception:
                pass

        # 12. Diary entries
        if school_classes and subjects and teachers:
            t = teachers[0].user if teachers else superadmin
            DiaryEntry.objects.create(
                academic_year=ay, date=timezone.now().date(),
                school_class=school_classes[0], section=school_classes[0].sections.first(),
                subject=subjects[0], topic="Linear Equations",
                lecture_summary="Solving one-variable linear equations",
                homework="Exercise 4.2 — Questions 1 to 10",
                important_instructions="Bring notebook tomorrow",
                teacher=t,
            )

        # 13. Homework
        if school_classes and subjects:
            Homework.objects.create(
                academic_year=ay, title="Math Worksheet 1",
                school_class=school_classes[0],
                section=school_classes[0].sections.first(),
                subject=subjects[0],
                description="Complete worksheet questions 1 to 5",
                assigned_date=timezone.now().date(),
                due_date=timezone.now().date() + timedelta(days=3),
                total_marks=10, teacher=teachers[0].user if teachers else superadmin,
                status=Homework.Status.ASSIGNED,
            )

        # 14. Comprehensive Syllabus + topics for every (class, subject) combo
        # Subject → list of chapter titles (real curriculum content per grade level)
        SYLLABUS_BY_SUBJECT = {
            "Mathematics": [
                "Chapter 1: Numbers and Number Sense",
                "Chapter 2: Whole Numbers and Operations",
                "Chapter 3: Fractions and Decimals",
                "Chapter 4: Geometry — Basic Shapes",
                "Chapter 5: Measurement (Length, Weight, Capacity)",
                "Chapter 6: Time and Money",
                "Chapter 7: Data Handling",
                "Chapter 8: Patterns and Symmetry",
            ],
            "English": [
                "Unit 1: My First Day at School",
                "Unit 2: The Honest Woodcutter",
                "Unit 3: Our Country Pakistan",
                "Unit 4: A Visit to the Zoo",
                "Unit 5: The Clever Fox",
                "Unit 6: Cleanliness is Next to Godliness",
                "Unit 7: Grammar — Nouns and Verbs",
                "Unit 8: Composition Writing",
            ],
            "Urdu": [
                "باب 1: ہمارا وطن",
                "باب 2: سچائی کی کمائی",
                "باب 3: محنت کا پھل",
                "باب 4: میرا اسکول",
                "باب 5: درخت کی اہمیت",
                "باب 6: گرامر — اسم اور فعل",
                "باب 7: خطوط نویسی",
                "باب 8: مشق",
            ],
            "Islamiat": [
                "Surah Al-Fatiha (Memorization + Translation)",
                "Surah Al-Ikhlas (Memorization + Translation)",
                "Five Pillars of Islam",
                "Belief in Prophets (Iman-e-Mursil)",
                "Life of Prophet Muhammad (PBUH) — Childhood",
                "Life of Prophet Muhammad (PBUH) — Prophethood",
                "Manners in Islam (Akhlaqiat)",
                "Stories of Prophets",
            ],
            "Computer Science": [
                "Unit 1: Introduction to Computers",
                "Unit 2: Hardware and Software",
                "Unit 3: Operating Systems",
                "Unit 4: Microsoft Word Basics",
                "Unit 5: Microsoft Excel Basics",
                "Unit 6: Introduction to Internet",
                "Unit 7: Cyber Safety and Ethics",
                "Unit 8: Basics of Programming (Scratch)",
            ],
            "General Science": [
                "Chapter 1: Living and Non-Living Things",
                "Chapter 2: Plants and Animals",
                "Chapter 3: Human Body — Organs and Senses",
                "Chapter 4: Food and Nutrition",
                "Chapter 5: Matter and Materials",
                "Chapter 6: Force and Energy",
                "Chapter 7: Earth and Universe",
                "Chapter 8: Environment and Conservation",
            ],
            "Social Studies": [
                "Chapter 1: Our Country — Pakistan",
                "Chapter 2: Provinces and Capitals",
                "Chapter 3: Our National Symbols",
                "Chapter 4: Famous Personalities of Pakistan",
                "Chapter 5: Means of Transport and Communication",
                "Chapter 6: Our Rights and Duties",
                "Chapter 7: Natural Resources",
                "Chapter 8: Festivals and National Days",
            ],
            "General Knowledge": [
                "Topic 1: My Family and Me",
                "Topic 2: Good Habits and Manners",
                "Topic 3: Safety Rules at Home and School",
                "Topic 4: Traffic Rules",
                "Topic 5: Famous Buildings and Monuments",
                "Topic 6: National Heroes",
            ],
            "Art & Craft": [
                "Project 1: Drawing with Pencil",
                "Project 2: Coloring with Crayons",
                "Project 3: Paper Folding (Origami)",
                "Project 4: Card Making",
                "Project 5: Clay Modeling",
                "Project 6: Painting with Watercolors",
            ],
            "Quran with Tajweed": [
                "Qaida — Lesson 1-10",
                "Surah Al-Fatiha with Tajweed",
                "Surah Al-Ikhlas with Tajweed",
                "Surah Al-Kawthar with Tajweed",
                "Surah Al-Asr with Tajweed",
                "Surah Al-Fil with Tajweed",
                "Namaz — Practical",
                "Daily Duas (Waking, Eating, Sleeping)",
            ],
            "Nazra Quran": [
                "Para 1 — Alif Lam Meem",
                "Para 2 — Sayaqool",
                "Para 3 — Tilkal Rusul",
                "Para 4 — Lan Talana",
                "Kalimahs and Iman-e-Mufassal",
                "Namaz — Practical Application",
            ],
            "Handwriting": [
                "Tracing Patterns",
                "English Cursive Letters (a-z)",
                "English Cursive Words",
                "English Cursive Sentences",
                "Urdu Letters (الف بے)",
                "Urdu Words and Sentences",
            ],
            "Physical Education": [
                "Warm-up and Stretching Exercises",
                "Ball Games (Cricket, Football, Throwball)",
                "Track and Field Events",
                "Drill and Marching",
                "Yoga and Meditation",
                "Sports Rules and Ethics",
            ],
            "Physics": [
                "Chapter 1: Measurements and Experimentation",
                "Chapter 2: Motion and Force",
                "Chapter 3: Scalars and Vectors",
                "Chapter 4: Work, Energy and Power",
                "Chapter 5: Properties of Matter",
                "Chapter 6: Heat and Temperature",
                "Chapter 7: Sound Waves",
                "Chapter 8: Light and Optics",
                "Chapter 9: Electricity — Basics",
                "Chapter 10: Magnetism",
            ],
            "Chemistry": [
                "Chapter 1: Introduction to Chemistry",
                "Chapter 2: Matter and its States",
                "Chapter 3: Atomic Structure",
                "Chapter 4: Periodic Table",
                "Chapter 5: Chemical Bonding",
                "Chapter 6: Chemical Reactions",
                "Chapter 7: Acids, Bases and Salts",
                "Chapter 8: Industrial Chemistry",
            ],
            "Biology": [
                "Chapter 1: Introduction to Biology",
                "Chapter 2: Cell Biology",
                "Chapter 3: Tissues and Organs",
                "Chapter 4: Plant Kingdom",
                "Chapter 5: Animal Kingdom",
                "Chapter 6: Human Physiology — Digestion",
                "Chapter 7: Human Physiology — Respiration",
                "Chapter 8: Human Physiology — Circulation",
                "Chapter 9: Ecosystem",
                "Chapter 10: Environmental Issues",
            ],
            "Pakistan Studies": [
                "Chapter 1: Ideology of Pakistan",
                "Chapter 2: Making of Pakistan (1857-1947)",
                "Chapter 3: Land and People of Pakistan",
                "Chapter 4: Steps Towards a Republic (1947-1958)",
                "Chapter 5: Era of Ayub Khan",
                "Chapter 6: Bangladesh Separation (1971)",
                "Chapter 7: Pakistan's Foreign Policy",
                "Chapter 8: Economy of Pakistan",
            ],
            "History & Geography": [
                "Chapter 1: Ancient Civilizations — Indus Valley",
                "Chapter 2: Muslim Rule in Subcontinent",
                "Chapter 3: Geography of Pakistan — Location",
                "Chapter 4: Climate and Weather",
                "Chapter 5: Agriculture and Industries",
                "Chapter 6: Population and Settlements",
                "Chapter 7: Continents and Oceans",
                "Chapter 8: Map Reading",
            ],
            "Arabic": [
                "Lesson 1: Arabic Alphabet",
                "Lesson 2: Vowels and Sukoon",
                "Lesson 3: Joining Letters",
                "Lesson 4: Basic Vocabulary",
                "Lesson 5: Short Sentences",
                "Lesson 6: Conversation — Greetings",
            ],
            "Punjabi": [
                "باب 1: پنجابی ورثہ",
                "باب 2: صوفی شاعری",
                "باب 3: وارث شاہ",
                "باب 4: بلھے شاہ",
                "باب 5: پنجابی زبان کی گرامر",
                "باب 6: پنجابی لوک گیت",
            ],
            "Computer Science (Elective)": [
                "Unit 1: Number Systems (Binary, Hexadecimal)",
                "Unit 2: Data Representation",
                "Unit 3: Programming in C/C++",
                "Unit 4: Control Structures",
                "Unit 5: Arrays and Strings",
                "Unit 6: Functions and Recursion",
                "Unit 7: File Handling",
                "Unit 8: Database Concepts (SQL)",
                "Unit 9: Web Development Basics (HTML/CSS)",
            ],
            "Biology (Elective)": [
                "Chapter 1: Cell Biology — Ultrastructure",
                "Chapter 2: Biochemistry",
                "Chapter 3: Bioenergetics",
                "Chapter 4: Cell Cycle and Reproduction",
                "Chapter 5: Variety of Life (Viruses, Bacteria)",
                "Chapter 6: Kingdom Protista and Fungi",
                "Chapter 7: Kingdom Plantae",
                "Chapter 8: Kingdom Animalia",
                "Chapter 9: Human Physiology — Nervous System",
                "Chapter 10: Human Physiology — Reproduction",
                "Chapter 11: Evolution",
                "Chapter 12: Ecology and Environment",
            ],
            "Additional Mathematics": [
                "Chapter 1: Functions and Their Graphs",
                "Chapter 2: Quadratic Functions",
                "Chapter 3: Sequences and Series",
                "Chapter 4: Trigonometric Identities",
                "Chapter 5: Vectors in 2D and 3D",
                "Chapter 6: Permutations and Combinations",
                "Chapter 7: Probability",
                "Chapter 8: Binomial Theorem",
            ],
            "Civics": [
                "Chapter 1: Introduction to Civics",
                "Chapter 2: Rights and Responsibilities",
                "Chapter 3: Forms of Government",
                "Chapter 4: Constitution of Pakistan",
                "Chapter 5: Federal and Provincial Governments",
                "Chapter 6: Local Government",
                "Chapter 7: Citizenship",
                "Chapter 8: Political Parties and Pressure Groups",
            ],
            "Ethics": [
                "Chapter 1: Definition and Scope of Ethics",
                "Chapter 2: Moral Theories",
                "Chapter 3: Ethical Decision Making",
                "Chapter 4: Personal and Social Ethics",
                "Chapter 5: Professional Ethics",
                "Chapter 6: Bioethics",
                "Chapter 7: Environmental Ethics",
                "Chapter 8: Ethics in Religion",
            ],
        }

        # For each class, choose appropriate subjects by level + create syllabus
        # Primary (1-5): General Science, Social Studies, GK, Quran, Nazra, Handwriting, Art, PE, plus core
        # Middle (6-8): Physics/Chemistry/Biology, Pak Studies, Hist/Geo, Arabic, Punjabi, plus core
        # Secondary (9-10): Pak Studies, plus electives (CSE/BIE/ADM/CIV/ETH)
        def subjects_for_class(cls):
            order = cls.order
            core = ["Mathematics", "English", "Urdu", "Islamiat", "Computer Science"]
            if order <= 5:
                # Primary
                primary = ["General Science", "Social Studies", "General Knowledge",
                           "Art & Craft", "Quran with Tajweed", "Handwriting",
                           "Physical Education", "Nazra Quran"]
                return core + primary
            elif 6 <= order <= 8:
                # Middle
                middle = ["Physics", "Chemistry", "Biology", "Pakistan Studies",
                          "History & Geography", "Arabic", "Punjabi"]
                return core + middle
            else:
                # Secondary (9-10)
                secondary = ["Pakistan Studies", "Computer Science (Elective)",
                             "Biology (Elective)", "Additional Mathematics",
                             "Civics", "Ethics"]
                return core + secondary

        # Build name→Subject map
        subject_by_name = {s.name: s for s in subjects}

        # Generate syllabus + topics for every (class, subject) combination
        from apps.syllabus.models import Syllabus, SyllabusTopic
        syl_count = 0
        topic_count = 0
        for cls in school_classes:
            sub_names = subjects_for_class(cls)
            for sub_name in sub_names:
                sub = subject_by_name.get(sub_name)
                if not sub:
                    continue
                syl, created = Syllabus.objects.get_or_create(
                    academic_year=ay, school_class=cls, subject=sub,
                    term=Syllabus.Term.FIRST,
                    defaults={"description": f"{sub.name} — First Term Syllabus for {cls.name}"},
                )
                if created:
                    syl_count += 1
                # Topics for this syllabus
                chapters = SYLLABUS_BY_SUBJECT.get(sub_name, [
                    f"Chapter 1: {sub_name}",
                    f"Chapter 2: {sub_name}",
                    f"Chapter 3: {sub_name}",
                    f"Chapter 4: {sub_name}",
                ])
                statuses_cycle = [
                    SyllabusTopic.Status.COMPLETED,
                    SyllabusTopic.Status.COMPLETED,
                    SyllabusTopic.Status.IN_PROGRESS,
                    SyllabusTopic.Status.NOT_STARTED,
                    SyllabusTopic.Status.DELAYED,
                ]
                for idx, ch in enumerate(chapters):
                    st = statuses_cycle[idx % len(statuses_cycle)]
                    t, created = SyllabusTopic.objects.get_or_create(
                        syllabus=syl, topic=ch,
                        defaults={
                            "chapter": ch.split(":")[0].strip(),
                            "description": ch,
                            "status": st,
                            "priority": random.randint(1, 5),
                            "expected_completion_date": date(2026, 9 + (idx % 3), (idx % 28) + 1) if idx >= 2 else None,
                        },
                    )
                    if created:
                        topic_count += 1
        self.stdout.write(f"  Syllabus created: {syl_count} syllabi, {topic_count} topics")

        # 15. Class test + results
        if school_classes and subjects and students:
            test = ClassTest.objects.create(
                academic_year=ay, school_class=school_classes[0],
                section=school_classes[0].sections.first(),
                subject=subjects[0], title="Surprise Test 1",
                date=timezone.now().date() - timedelta(days=2),
                total_marks=20, passing_marks=8,
                status="published", teacher=teachers[0].user if teachers else superadmin,
            )
            for s in students[:5]:
                if s.current_class == school_classes[0]:
                    TestResult.objects.get_or_create(
                        test=test, student=s,
                        defaults={"obtained_marks": random.randint(5, 20)},
                    )

        # 16. Exam
        if school_classes:
            exam = Exam.objects.create(
                academic_year=ay, name="First Term Examination 2026",
                term=Exam.Term.FIRST,
                start_date=date(2026, 11, 10), end_date=date(2026, 11, 20),
                is_published=False,
            )

        # 17. Date sheet
        if school_classes:
            ds = DateSheet.objects.create(
                academic_year=ay, title="First Term Date Sheet 2026",
                term="first", school_class=school_classes[0],
                status=DateSheet.Status.PUBLISHED,
                published_by=superadmin, published_at=timezone.now(),
            )
            for sub, day in zip(subjects[:4], [10,12,14,16]):
                DateSheetItem.objects.create(
                    datesheet=ds, subject=sub, date=date(2026, 11, day),
                    start_time="09:00", end_time="12:00", room="Examination Hall",
                )

        # 18. Activities
        if school_classes:
            act = Activity.objects.create(
                academic_year=ay, title="Inter-School Science Exhibition",
                category=Activity.Category.CO_CURRICULAR, date=date(2026, 9, 12),
                description="Annual science exhibition for all classes",
                location="School Auditorium", teacher_incharge=superadmin,
                result="Three students achieved 1st position",
            )
            for s in students[:3]:
                StudentActivity.objects.create(
                    activity=act, student=s, position="1st",
                    award="Gold Medal", certificate_no=f"CER-{random.randint(1000,9999)}",
                )

        # 19. Announcement
        Announcement.objects.create(
            academic_year=ay, title="Welcome to Academic Year 2026-2027",
            description="Welcome to a new academic year. Classes commence on April 1, 2026. Please ensure all dues are cleared before the start of classes.",
            audience=Announcement.Audience.EVERYONE,
            publish_date=timezone.now(), author=superadmin,
            is_published=True,
        )

        # 19b. Sample admission applications in different workflow states
        from apps.admissions.models import Admission, ApplicationNumberService
        from apps.admissions.services import AdmissionService
        app1, _ = Admission.objects.get_or_create(
            full_name="Imran Qureshi",
            defaults={
                "application_no": ApplicationNumberService.generate(),
                "father_name": "Tariq Qureshi",
                "date_of_birth": date(2013, 5, 12),
                "gender": "male",
                "cnic_bform": "B-Form-9876543210",
                "address": "House 25, Block B, Karachi",
                "contact_phone": "+923331234567",
                "previous_school": "City School",
                "previous_class": "Grade 5",
                "applying_class": school_classes[0],
                "applying_section": school_classes[0].sections.first(),
                "academic_year": ay,
                "admission_date": date(2026, 4, 1),
                "parent_name": "Tariq Qureshi",
                "parent_cnic": "42101-1234567-8",
                "parent_phone": "+923331234567",
                "parent_occupation": "Engineer",
                "status": Admission.Status.DRAFT,
            },
        )
        try:
            AdmissionService.submit(app1, superadmin)
            AdmissionService.verify(app1, superadmin)
        except Exception:
            pass
        app2, _ = Admission.objects.get_or_create(
            full_name="Ayesha Siddiqui",
            defaults={
                "application_no": ApplicationNumberService.generate(),
                "father_name": "Hamid Siddiqui",
                "date_of_birth": date(2012, 8, 22),
                "gender": "female",
                "address": "House 88, Block C, Karachi",
                "contact_phone": "+923339876543",
                "applying_class": school_classes[1],
                "applying_section": school_classes[1].sections.first(),
                "academic_year": ay,
                "admission_date": date(2026, 4, 1),
                "parent_name": "Hamid Siddiqui",
                "parent_cnic": "42101-9876543-2",
                "parent_phone": "+923339876543",
                "status": Admission.Status.DRAFT,
            },
        )
        try:
            AdmissionService.submit(app2, superadmin)
        except Exception:
            pass

        # 20. Calendar events
        events = [
            ("First Day of School", "event", date(2026, 4, 1)),
            ("Summer Break", "holiday", date(2026, 6, 15)),
            ("Parent-Teacher Meeting", "parent_meeting", date(2026, 9, 25)),
            ("Sports Day", "sports_day", date(2026, 11, 5)),
            ("Annual Function", "annual_function", date(2026, 12, 20)),
        ]
        for title, cat, dt in events:
            CalendarEvent.objects.get_or_create(
                title=title, start_date=dt,
                defaults={"category": cat, "academic_year": ay, "is_public": True},
            )

        self.stdout.write(self.style.SUCCESS(
            "✓ Demo data generated:\n"
            f"  - {User.objects.count()} users\n"
            f"  - {Teacher.objects.count()} teachers\n"
            f"  - {Parent.objects.count()} parents\n"
            f"  - {Student.objects.count()} students\n"
            f"  - {SchoolClass.objects.count()} classes\n"
            f"  - {Section.objects.count()} sections\n"
            f"  - {Subject.objects.count()} subjects\n"
            f"  - {FeeChallan.objects.count()} fee challans\n"
            f"  - {FeePayment.objects.count()} fee payments\n"
            f"  - {Payroll.objects.count()} payroll records\n"
            f"  - {Attendance.objects.count()} attendance records\n"
            f"  - {Activity.objects.count()} activities\n"
            f"  - {Announcement.objects.count()} announcements\n"
            f"  - {CalendarEvent.objects.count()} calendar events\n"
        ))
        self.stdout.write(self.style.SUCCESS(
            "\nLogin: superadmin / admin123 (also: principal, admin, coordinator, accountant, hr_payroll, receptionist, teacher1)"
        ))

        # -----------------------------------------------------------------
        # Write records.txt — full demo data dump for reference
        # -----------------------------------------------------------------
        records_path = BASE_DIR / "records.txt"
        with open(records_path, "w", encoding="utf-8") as f:
            w = f.write
            w("=" * 80 + "\n")
            w(f"  SCHOOL ERP — DEMO DATA RECORDS\n")
            w(f"  Generated: {timezone.now():%Y-%m-%d %H:%M:%S}\n")
            w("=" * 80 + "\n\n")

            w("This file lists every demo account, student, teacher, parent, and key\n")
            w("financial record created by `python manage.py generate_demo_data`.\n")
            w("You can use these credentials to log in (password is admin123 for all).\n\n")

            # ----- Users / Login credentials -----
            w("=" * 80 + "\n")
            w("  1. USER ACCOUNTS  (log in with username + password 'admin123')\n")
            w("=" * 80 + "\n\n")
            w(f"{'Username':<15} {'Role':<22} {'Email':<40} {'Name'}\n")
            w("-" * 95 + "\n")
            for u in User.objects.order_by("id"):
                full = u.get_full_name() or "—"
                w(f"{u.username:<15} {u.get_role_display():<22} {u.email:<40} {full}\n")
            w("\nPassword for ALL accounts: admin123\n\n")

            # ----- Teachers -----
            w("=" * 80 + "\n")
            w("  2. TEACHERS & STAFF\n")
            w("=" * 80 + "\n\n")
            w(f"{'Emp ID':<10} {'Name':<26} {'Gender':<8} {'Category':<12} {'Level':<12} {'Designation':<26} {'Subject':<18} {'Classes'}\n")
            w("-" * 140 + "\n")
            for t in Teacher.objects.select_related("user").order_by("employee_id"):
                subs = ", ".join(s.name for s in t.subjects.all()[:2]) or "—"
                cls = ", ".join(c.name for c in t.classes.all()[:3]) or "—"
                w(f"{t.employee_id:<10} {t.full_name[:26]:<26} {t.gender:<8} {t.get_staff_category_display().split(' ')[0]:<12} {t.get_teaching_level_display().split(' ')[0] if t.teaching_level else '—':<12} {t.designation[:26]:<26} {subs[:18]:<18} {cls}\n")
            w("\n")
            # Summary: teachers by level + category
            w("Staff summary:\n")
            for level_key, level_label in Teacher.TeachingLevel.choices:
                count = Teacher.objects.filter(teaching_level=level_key, staff_category="teaching").count()
                w(f"  {level_label:<28}: {count} teachers\n")
            w(f"  Administration Staff         : {Teacher.objects.filter(staff_category='admin').count()}\n")
            w(f"  TOTAL                         : {Teacher.objects.count()}\n")
            # Gender breakdown
            male = Teacher.objects.filter(gender="male").count()
            female = Teacher.objects.filter(gender="female").count()
            w(f"\nGender breakdown: {male} male · {female} female\n")
            w("\n")

            # ----- Parents -----
            w("=" * 80 + "\n")
            w("  3. PARENTS  (Username = phone digits, password = admin123)\n")
            w("=" * 80 + "\n\n")
            w(f"{'Username':<22} {'Name':<26} {'Relation':<10} {'CNIC':<20} {'Phone':<18} {'Occupation'}\n")
            w("-" * 115 + "\n")
            for p in Parent.objects.select_related("user").order_by("id"):
                uname = p.user.username if p.user else "—"
                w(f"{uname:<22} {p.full_name[:26]:<26} {p.get_relation_display():<10} {p.cnic:<20} {p.phone:<18} {p.occupation or '—'}\n")
            w("\n")

            # ----- Students -----
            w("=" * 80 + "\n")
            w("  4. STUDENTS  (Username = registration no, password = admin123)\n")
            w("=" * 80 + "\n\n")
            w(f"{'Username (Reg No)':<22} {'Name':<28} {'Class':<10} {'Father':<28} {'Status':<10} {'Admission'}\n")
            w("-" * 115 + "\n")
            for s in Student.objects.select_related("current_class", "current_section", "user").order_by("registration_no"):
                cls = s.class_section_display
                w(f"{s.registration_no:<22} {s.full_name[:28]:<28} {cls:<10} {s.father_name[:28]:<28} {s.get_status_display():<10} {s.admission_date:%Y-%m-%d}\n")
            w("\n")
            # Note about easy logins
            w("EASY DEMO LOGINS (password admin123 for all):\n")
            w("  student1, student2, student3, student4, student5  → first 5 students\n")
            w("  parent1, parent2, parent3                          → first 3 parents\n")
            w("  teacher1 through teacher37                         → 37 teachers (Primary/Middle/Secondary)\n")
            w("  superadmin, principal, admin, coordinator, accountant, hr_payroll, receptionist\n")
            w("\n")

            # ----- Fee summary per student -----
            w("=" * 80 + "\n")
            w("  5. FEE SUMMARY PER STUDENT\n")
            w("=" * 80 + "\n\n")
            w(f"{'Reg No':<20} {'Name':<28} {'Challans':<10} {'Paid':<10} {'Pending':<10} {'Defaulted'}\n")
            w("-" * 95 + "\n")
            for s in Student.objects.order_by("registration_no"):
                challans = s.fee_challans.all()
                total = challans.count()
                paid = challans.filter(status=FeeChallan.Status.PAID).count()
                pending = challans.filter(status__in=[FeeChallan.Status.UNPAID, FeeChallan.Status.PARTIAL]).count()
                defaulted = challans.filter(status=FeeChallan.Status.OVERDUE).count()
                w(f"{s.registration_no:<20} {s.full_name[:28]:<28} {total:<10} {paid:<10} {pending:<10} {defaulted}\n")
            w("\n")

            # ----- Payroll summary -----
            w("=" * 80 + "\n")
            w("  6. TEACHER PAYROLL\n")
            w("=" * 80 + "\n\n")
            w(f"{'Emp ID':<10} {'Teacher':<28} {'Month':<18} {'Net Salary':<15} {'Status'}\n")
            w("-" * 85 + "\n")
            for p in Payroll.objects.select_related("teacher").order_by("-month", "teacher__employee_id"):
                w(f"{p.teacher.employee_id:<10} {p.teacher.full_name[:28]:<28} {p.month:<18} Rs.{p.net_salary:>10,.0f}    {p.get_status_display()}\n")
            w("\n")

            # ----- Classes & Sections -----
            w("=" * 80 + "\n")
            w("  7. CLASSES & SECTIONS (BIG SCHOOL LAYOUT)\n")
            w("=" * 80 + "\n\n")
            w(f"{'Grade':<10} {'Level':<12} {'Section':<10} {'Group':<22} {'Students'}\n")
            w("-" * 70 + "\n")
            for c in SchoolClass.objects.order_by("order"):
                for sec in c.sections.all().order_by("name"):
                    student_count = Student.objects.filter(current_class=c, current_section=sec).count()
                    group_label = sec.get_subject_group_display() if sec.subject_group else "—"
                    w(f"{c.name:<10} {c.get_grade_level_display():<12} {sec.name:<10} {group_label:<22} {student_count}\n")
                w("\n")
            # Subject-group summary for Grade 9-10
            w("Subject-group summary (Grade 9-10):\n")
            for grade_name in ["Grade 9", "Grade 10"]:
                cls = SchoolClass.objects.filter(name=grade_name).first()
                if cls:
                    comp_count = cls.sections.filter(subject_group="computer").count()
                    bio_count = cls.sections.filter(subject_group="bio").count()
                    w(f"  {grade_name}: {comp_count} Computer sections + {bio_count} Biology sections\n")
            w("\n")

            # ----- Subjects -----
            w("=" * 80 + "\n")
            w("  8. SUBJECTS\n")
            w("=" * 80 + "\n\n")
            w(f"{'Code':<8} {'Name':<35} {'Compulsory':<12} {'Active'}\n")
            w("-" * 70 + "\n")
            for s in Subject.objects.order_by("code"):
                w(f"{s.code:<8} {s.name[:35]:<35} {'Yes' if s.is_compulsory else 'No':<12} {'Yes' if s.is_active else 'No'}\n")
            w("\n")
            # Subject count + syllabus coverage summary
            from apps.syllabus.models import Syllabus, SyllabusTopic
            w(f"Total subjects: {Subject.objects.count()}\n")
            w(f"Total syllabi created: {Syllabus.objects.count()}\n")
            w(f"Total syllabus topics: {SyllabusTopic.objects.count()}\n")
            # Per-grade subject count
            for cls in SchoolClass.objects.order_by("order"):
                count = Syllabus.objects.filter(school_class=cls).count()
                topics = SyllabusTopic.objects.filter(syllabus__school_class=cls).count()
                w(f"  {cls.name:<10}: {count} subjects, {topics} topics in syllabus\n")
            w("\n")

            # ----- Stats summary -----
            w("=" * 80 + "\n")
            w("  9. SUMMARY STATISTICS\n")
            w("=" * 80 + "\n\n")
            total_collected = sum(p.amount for p in FeePayment.objects.filter(is_successful=True))
            total_outstanding = sum(c.balance for c in FeeChallan.objects.exclude(status=FeeChallan.Status.PAID))
            w(f"Total users:           {User.objects.count()}\n")
            w(f"Total teachers:        {Teacher.objects.count()}\n")
            w(f"Total parents:         {Parent.objects.count()}\n")
            w(f"Total students:        {Student.objects.count()}\n")
            w(f"Total fee challans:    {FeeChallan.objects.count()}\n")
            w(f"Total fee payments:    {FeePayment.objects.count()}\n")
            w(f"Total collected:       Rs. {total_collected:,.2f}\n")
            w(f"Total outstanding:      Rs. {total_outstanding:,.2f}\n")
            w(f"Total payroll records: {Payroll.objects.count()}\n")
            w(f"Active academic year:  {ay.name}\n")
            w("\n")

            # ----- Login URLs -----
            w("=" * 80 + "\n")
            w("  10. QUICK LOGIN URLs\n")
            w("=" * 80 + "\n\n")
            w("Login page:   http://localhost:8000/account/login/\n")
            w("Dashboard:    http://localhost:8000/dashboard/  (after login)\n")
            w("Django admin: http://localhost:8000/admin/      (superadmin only)\n")
            w("2FA setup:    http://localhost:8000/accounts/security/2fa/\n")
            w("Records file: /home/z/my-project/school_erp/records.txt (this file)\n\n")
            w("=" * 80 + "\n")
            w("  END OF RECORDS\n")
            w("=" * 80 + "\n")

        self.stdout.write(self.style.SUCCESS(
            f"\n✓ Demo data records saved to: {records_path}\n"
            f"  Open this file to see every demo account, student, teacher, parent, and fee record.\n"
        ))
