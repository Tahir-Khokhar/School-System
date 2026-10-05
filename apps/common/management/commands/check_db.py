"""
Verify the database connection and report server info.

Works for both SQLite (the default) and PostgreSQL (when configured).

Usage:
    python manage.py check_db

Exits 0 if everything is good, non-zero otherwise.
"""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connections
from django.db.utils import OperationalError, Error as DBError


class Command(BaseCommand):
    help = "Verify database connection and report server version info."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("Checking database connection..."))

        engine = settings.DATABASES["default"]["ENGINE"]
        is_postgres = engine == "django.db.backends.postgresql"
        is_sqlite = engine == "django.db.backends.sqlite3"
        db_label = "PostgreSQL" if is_postgres else "SQLite" if is_sqlite else engine.rsplit(".", 1)[-1]

        conn = connections["default"]
        try:
            conn.ensure_connection()
        except OperationalError as e:
            self.stderr.write(self.style.ERROR(
                f"\n✗ Could not connect to {db_label}: {e}\n"
                + (
                    "\nPostgreSQL troubleshooting:\n"
                    "  1. Is the PostgreSQL server running?    (sudo systemctl status postgresql)\n"
                    "  2. Did you run scripts/setup_postgres.sql?  (creates DB + user)\n"
                    "  3. Are your .env credentials correct?    (DB_NAME, DB_USER, DB_PASSWORD)\n"
                    "  4. Can you connect manually?              (psql -U school_erp_user -d school_erp -h localhost)\n"
                    if is_postgres else
                    "\nSQLite troubleshooting:\n"
                    "  1. Is the project directory writable?\n"
                    "  2. Try deleting db.sqlite3 and re-running `python manage.py migrate`\n"
                )
            ))
            raise CommandError(1)
        except DBError as e:
            self.stderr.write(self.style.ERROR(f"Database error: {e}"))
            raise CommandError(2)

        # Connected — gather info (queries differ per backend)
        with conn.cursor() as cur:
            if is_postgres:
                cur.execute("SELECT version();")
                version = cur.fetchone()[0]
                cur.execute("SELECT current_database(), current_user;")
                db_name, db_user = cur.fetchone()
                cur.execute("SHOW server_version;")
                server_version = cur.fetchone()[0]
                cur.execute("SHOW timezone;")
                tz = cur.fetchone()[0]
                cur.execute("SELECT current_setting('max_connections');")
                max_conn = cur.fetchone()[0]
                self.stdout.write(self.style.SUCCESS(f"✓ Connected to PostgreSQL {server_version}"))
                self.stdout.write(f"  Database:      {db_name}")
                self.stdout.write(f"  User:          {db_user}")
                self.stdout.write(f"  Server time:   {tz}")
                self.stdout.write(f"  Max conns:     {max_conn}")
                self.stdout.write(f"  Version:       {version}")
            elif is_sqlite:
                cur.execute("SELECT sqlite_version();")
                version = cur.fetchone()[0]
                db_path = settings.DATABASES["default"]["NAME"]
                cur.execute("SELECT datetime('now');")
                now = cur.fetchone()[0]
                # Count tables in the public schema
                cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
                table_count = cur.fetchone()[0]
                self.stdout.write(self.style.SUCCESS(f"✓ Connected to SQLite {version}"))
                self.stdout.write(f"  Database file: {db_path}")
                self.stdout.write(f"  Server time:    {now}")
                self.stdout.write(f"  Tables:         {table_count}")
                self.stdout.write(f"  Version:        SQLite {version}")
            else:
                self.stdout.write(self.style.SUCCESS(f"✓ Connected via {engine}"))

        self.stdout.write(self.style.SUCCESS("\n✓ Database connection is healthy."))
