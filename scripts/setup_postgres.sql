-- ============================================================================
-- School ERP — PostgreSQL one-time setup script
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
--   1. Creates the database `school_erp` (UTF8, with C collation for fast
--      sorting — recommended for PostgreSQL on Linux)
--   2. Creates the role `school_erp_user` with a password you should change
--   3. Grants full privileges on the database to that role
--   4. Sets sensible schema defaults (extensions, timezone, etc.)
--
-- After running this, edit .env to match the password, then:
--     python manage.py migrate
--     python manage.py create_school_roles
--     python manage.py generate_demo_data
-- ============================================================================

-- 1. Database
CREATE DATABASE school_erp
    WITH ENCODING 'UTF8'
    LC_COLLATE 'C.UTF-8'
    LC_CTYPE 'C.UTF-8'
    TEMPLATE template0;

-- 2. Role (user)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'school_erp_user') THEN
        CREATE ROLE school_erp_user
            LOGIN
            PASSWORD 'change-me-to-a-strong-password'  -- ← CHANGE THIS
            NOSUPERUSER
            NOCREATEDB
            NOCREATEROLE
            NOREPLICATION;
    END IF;
END
$$;

-- 3. Grant privileges
GRANT ALL PRIVILEGES ON DATABASE school_erp TO school_erp_user;

-- 4. Connect to the DB and set up schema
\c school_erp

-- Enable useful extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;       -- fast trigram search (LIKE/ILIKE)
CREATE EXTENSION IF NOT EXISTS unaccent;     -- for accent-insensitive search
CREATE EXTENSION IF NOT EXISTS citext;        -- case-insensitive text

-- Default timezone for the connection (sessions can override)
ALTER DATABASE school_erp SET timezone TO 'Asia/Karachi';
ALTER DATABASE school_erp SET statement_timeout TO '30000';  -- 30s

-- Grant schema privileges (PostgreSQL 15+ requires this)
GRANT ALL ON SCHEMA public TO school_erp_user;
ALTER DATABASE school_erp OWNER TO school_erp_user;
ALTER SCHEMA public OWNER TO school_erp_user;

-- Done. Connect as school_erp_user to verify:
--     psql -U school_erp_user -d school_erp -h localhost
