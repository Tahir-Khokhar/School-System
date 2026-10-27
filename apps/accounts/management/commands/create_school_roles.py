"""
Create all school ERP roles as Django groups + assign permissions.

Usage:
    python manage.py create_school_roles
    python manage.py create_school_roles --dry-run
    python manage.py create_school_roles --strict   # exit non-zero on missing perms
"""
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.models import ROLE_PERMISSIONS


ALL_FLAG = "__all__"


class Command(BaseCommand):
    help = "Create all School ERP role groups with appropriate permissions."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would change without writing to the database.",
        )
        parser.add_argument(
            "--strict",
            action="store_true",
            help="Exit with an error if any declared permission is missing.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        strict = options["strict"]

        # Pre-validate every codename so we fail before touching the DB.
        declared, malformed = self._collect_codenames()
        if malformed:
            raise CommandError(
                "Malformed permission codenames (expected 'app_label.codename'): "
                + ", ".join(malformed)
            )

        # Fetch all referenced permissions in one query.
        existing = self._fetch_existing(declared)
        missing_by_role = {
            role: [c for c in perms if c != ALL_FLAG and c not in existing]
            for role, perms in ROLE_PERMISSIONS.items()
        }

        if strict:
            any_missing = {r: m for r, m in missing_by_role.items() if m}
            if any_missing:
                raise CommandError(
                    "Missing permissions: "
                    + "; ".join(f"{r}: {', '.join(m)}" for r, m in any_missing.items())
                )

        for role_label, perms in ROLE_PERMISSIONS.items():
            self._sync_group(
                role_label,
                perms,
                existing=existing,
                missing=missing_by_role[role_label],
                dry_run=dry_run,
            )

        self.stdout.write(self.style.SUCCESS("School ERP roles created."))

    # ------------------------------------------------------------------ helpers

    def _collect_codenames(self):
        """Return (set of all codenames, list of malformed ones)."""
        declared, malformed = set(), []
        for perms in ROLE_PERMISSIONS.values():
            for codename_str in perms:
                if codename_str == ALL_FLAG:
                    continue
                if not isinstance(codename_str, str) or "." not in codename_str:
                    malformed.append(repr(codename_str))
                    continue
                declared.add(codename_str)
        return declared, malformed

    def _fetch_existing(self, codenames):
        """Map 'app_label.codename' -> Permission instance."""
        if not codenames:
            return {}
        by_app = {}
        for c in codenames:
            app_label, codename = c.split(".", 1)
            by_app.setdefault(app_label, set()).add(codename)

        result = {}
        for app_label, codenames_in_app in by_app.items():
            for perm in Permission.objects.filter(
                content_type__app_label=app_label,
                codename__in=codenames_in_app,
            ).select_related("content_type"):
                result[f"{perm.content_type.app_label}.{perm.codename}"] = perm
        return result

    def _sync_group(self, role_label, perms, *, existing, missing, dry_run):
        group_name = role_label
        grant_all = ALL_FLAG in perms

        if dry_run:
            count = Permission.objects.count() if grant_all else len(perms) - grant_all
            self.stdout.write(
                f"[dry-run] Group '{group_name}' — would grant "
                + ("ALL permissions" if grant_all else f"{count} permissions")
            )
            return

        with transaction.atomic():
            grp, created = Group.objects.get_or_create(name=group_name)
            if grant_all:
                grp.permissions.set(Permission.objects.all())
                msg = (
                    f"✔ Group '{group_name}' — granted ALL permissions "
                    f"({grp.permissions.count()})"
                )
                style = self.style.SUCCESS
            else:
                # Resolve to a *set* of Permission instances in one shot.
                perm_objs = [existing[c] for c in perms if c != ALL_FLAG and c in existing]
                grp.permissions.set(perm_objs)
                msg = f"✔ Group '{group_name}' — {len(perm_objs)} permissions"
                if missing:
                    msg += f" — missing: {missing}"
                    style = self.style.WARNING
                else:
                    style = self.style.SUCCESS
            verb = "created" if created else "updated"
            self.stdout.write(style(f"{msg} [{verb}]"))
