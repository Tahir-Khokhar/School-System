"""
Create all school ERP roles as Django groups + assign permissions.
Usage: python manage.py create_school_roles
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from apps.accounts.models import User, ROLE_PERMISSIONS


class Command(BaseCommand):
    help = "Create all School ERP role groups with appropriate permissions."

    def handle(self, *args, **options):
        # Map role -> group name as used in ROLE_PERMISSIONS
        for role_label, perms in ROLE_PERMISSIONS.items():
            group_name = role_label
            grp, _ = Group.objects.get_or_create(name=group_name)
            # Reset permissions
            grp.permissions.clear()
            all_perms_flag = perms == ["__all__"]
            if all_perms_flag:
                all_perms = Permission.objects.all()
                grp.permissions.set(all_perms)
                self.stdout.write(self.style.SUCCESS(
                    f"✔ Group '{group_name}' — granted ALL permissions ({all_perms.count()})"
                ))
                continue
            perm_objs = []
            missing = []
            for codename_str in perms:
                try:
                    app_label, codename = codename_str.split(".", 1)
                    p = Permission.objects.get(
                        content_type__app_label=app_label, codename=codename
                    )
                    perm_objs.append(p)
                except Permission.DoesNotExist:
                    missing.append(codename_str)
            grp.permissions.set(perm_objs)
            status = self.style.SUCCESS if perm_objs else self.style.WARNING
            self.stdout.write(status(
                f"✔ Group '{group_name}' — {len(perm_objs)} permissions"
                + (f" — missing: {missing}" if missing else "")
            ))
        self.stdout.write(self.style.SUCCESS("School ERP roles created."))
