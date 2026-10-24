"""
School ERP — accounts app.
Custom user model with role, groups, and helper role-check properties.
"""
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.urls import reverse


class User(AbstractUser):
    """Custom user with role and explicit role helper methods."""

    class Role(models.TextChoices):
        SUPER_ADMIN = "super_admin", "Super Admin"
        ADMIN = "admin", "School Administration"
        PRINCIPAL = "principal", "Principal"
        COORDINATOR = "coordinator", "Coordinator"
        TEACHER = "teacher", "Teacher"
        ACCOUNTANT = "accountant", "Accountant"
        HR_PAYROLL = "hr_payroll", "HR / Payroll Officer"
        RECEPTIONIST = "receptionist", "Receptionist"
        STUDENT = "student", "Student"
        PARENT = "parent", "Parent"

    role = models.CharField(
        max_length=20, choices=Role.choices,
        default=Role.STUDENT, db_index=True,
    )
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    force_password_change = models.BooleanField(default=False)
    last_activity_ip = models.GenericIPAddressField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date_joined"]
        indexes = [models.Index(fields=["role"])]

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    # ---- role helpers used in templates / views ----
    @property
    def is_student(self):
        return self.role == self.Role.STUDENT

    @property
    def is_teacher(self):
        return self.role == self.Role.TEACHER

    @property
    def is_parent(self):
        return self.role == self.Role.PARENT

    @property
    def is_admin_staff(self):
        return self.role in {
            self.Role.SUPER_ADMIN, self.Role.ADMIN, self.Role.PRINCIPAL,
            self.Role.COORDINATOR, self.Role.ACCOUNTANT,
            self.Role.HR_PAYROLL, self.Role.RECEPTIONIST,
        } or self.is_superuser

    @property
    def can_view_payroll(self):
        return self.role in {
            self.Role.SUPER_ADMIN, self.Role.HR_PAYROLL,
        } or self.is_superuser

    @property
    def can_view_fees(self):
        return self.role in {
            self.Role.SUPER_ADMIN, self.Role.ADMIN, self.Role.ACCOUNTANT,
        } or self.is_superuser

    def get_role_display(self):
        return dict(self.Role.choices).get(self.role, self.role)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Sync user to their role group
        if self.role:
            group_name = self.role.replace("_", " ").title()
            grp, _ = Group.objects.get_or_create(name=group_name)
            self.groups.add(grp)


# Groups map cleanly to roles
ROLE_PERMISSIONS = {
    "Super Admin": ["__all__"],
    "School Administration": [
        "students.view_student", "students.add_student", "students.change_student",
        "teachers.view_teacher", "teachers.add_teacher", "teachers.change_teacher",
        "admissions.view_admission", "admissions.add_admission", "admissions.change_admission",
        "fees.view_feechallan", "fees.add_feechallan",
        "examinations.view_termresult", "examinations.add_termresult",
        "payroll.view_payroll",
        "common.view_academicyear",
    ],
    "Principal": [
        "students.view_student", "teachers.view_teacher", "fees.view_feechallan",
        "examinations.view_termresult", "payroll.view_payroll",
        "common.view_academicyear",
    ],
    "Coordinator": [
        "students.view_student", "teachers.view_teacher",
        "syllabus.view_syllabus", "syllabus.change_syllabus",
        "examinations.view_termresult", "examinations.add_termresult",
        "common.view_class", "common.change_class",
    ],
    "Teacher": [
        "students.view_student",
        "attendance.view_attendance", "attendance.add_attendance",
        "diary.view_diaryentry", "diary.add_diaryentry",
        "homework.view_homework", "homework.add_homework",
        "syllabus.view_syllabus", "syllabus.change_syllabus",
        "examinations.view_classtest", "examinations.add_classtest",
        "examinations.view_surprisetest",
    ],
    "Accountant": [
        "fees.view_feechallan", "fees.add_feechallan", "fees.change_feechallan",
        "fees.view_feepayment", "fees.add_feepayment",
        "students.view_student",
    ],
    "HR/Payroll Officer": [
        "payroll.view_payroll", "payroll.add_payroll", "payroll.change_payroll",
        "payroll.view_salarypayment", "payroll.add_salarypayment",
        "teachers.view_teacher",
    ],
    "Receptionist": [
        "admissions.view_admission", "admissions.add_admission",
        "students.view_student",
        "parents.view_parent",
    ],
    "Student": [],
    "Parent": [],
}
