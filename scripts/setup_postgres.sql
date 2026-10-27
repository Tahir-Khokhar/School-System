-- ============================================================================
-- School ERP — PostgreSQL one-time setup script (corrected)
-- ============================================================================
-- Run as a PostgreSQL superuser (usually `postgres`):
--
--     sudo -u postgres psql -f scripts/setup_postgres.sql
--
-- Or interactively:
--     sudo -u postgres psql
--     \i scripts/setup_postgres.sql
--
-- What this does:
--   1. Creates the database `school_erp` (UTF8)
--   2. Creates the role `school_erp_user` with a password you should change
--   3. Grants full privileges on the database to that role
--   4. Sets sensible schema defaults (extensions, timezone, etc.)
--
-- After running this, edit .env to match the password, then:
--     python manage.py migrate
--     python manage.py create_school_roles
--     python manage.py generate_demo_data
-- ============================================================================

-- ============================================================================
-- 0. Fail fast on errors
-- ============================================================================
\set ON_ERROR_STOP on

-- ============================================================================
-- 1. Role first (must exist before we GRANT on the database)
-- ============================================================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'school_erp_user') THEN
        CREATE ROLE school_erp_user
            LOGIN
            PASSWORD 'change-me-to-a-strong-password'  -- ← CHANGE THIS
            NOSUPERUSER
            NOCREATEDB
            NOCREATEROLE
            NOREPLICATION
            NOINHERIT;
    END IF;
END
$$;

-- ============================================================================
-- 2. Database
--    - template0 is required for custom LC_* (template1 has inherited locale)
--    - OWNER set here so the role owns it immediately (no separate ALTER)
--    - LC_COLLATE/LC_CTYPE must be a locale that exists on the OS.
--      'C.UTF-8' is Debian/Ubuntu; on RHEL/Fedora use 'en_US.UTF-8'.
--      If 'C.UTF-8' is unavailable, comment these two lines to use the
--      cluster default (usually safe).
-- ============================================================================
CREATE DATABASE school_erp
    WITH ENCODING 'UTF8'
    LC_COLLATE 'C.UTF-8'
    LC_CTYPE 'C.UTF-8'
    TEMPLATE template0
    OWNER school_erp_user;

-- ============================================================================
-- 3. Grant privileges
-- ============================================================================
GRANT ALL PRIVILEGES ON DATABASE school_erp TO school_erp_user;

-- ============================================================================
-- 4. Database-level settings
--    (Must be set from a connection to the DB, but ALTER DATABASE works from
--     any DB — so this is fine before \c)
-- ============================================================================
ALTER DATABASE school_erp SET timezone TO 'Asia/Karachi';
ALTER DATABASE school_erp SET statement_timeout TO '30000';

-- ============================================================================
-- 5. Connect to the DB, create extensions, fix schema ownership
-- ============================================================================
\c school_erp

-- Extensions require superuser (or a role with CREATE on the DB).
-- Run these as postgres, not as school_erp_user.
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS citext;

-- Grant schema access (PostgreSQL 15+ revoked CREATE on public by default)
GRANT ALL ON SCHEMA public TO school_erp_user;
ALTER SCHEMA public OWNER TO school_erp_user;

-- Transfer ownership of any extensions already created in public
-- (so the app role can manage them if needed). Skip if you want them
-- to remain owned by postgres — usually you DO want this.
ALTER EXTENSION pg_trgm  OWNER TO school_erp_user;
ALTER EXTENSION unaccent OWNER TO school_erp_user;
ALTER EXTENSION citext   OWNER TO school_erp_user;

-- Done. Connect as school_erp_user to verify:
--     psql -U school_erp_user -d school_erp -h localhost
