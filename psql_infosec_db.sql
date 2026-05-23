\set ON_ERROR_STOP on

\echo '== Creating/updating app role =='

SELECT format(
  'CREATE ROLE %I WITH LOGIN PASSWORD %L;',
  'infosec_app',
  'admin123'
)
WHERE NOT EXISTS (
  SELECT 1 FROM pg_roles WHERE rolname = 'infosec_app'
);
\gexec

ALTER ROLE infosec_app WITH LOGIN PASSWORD 'admin123';

\echo '== Creating database if missing =='

SELECT format(
  'CREATE DATABASE %I OWNER %I;',
  'infosec_portal',
  'infosec_app'
)
WHERE NOT EXISTS (
  SELECT 1 FROM pg_database WHERE datname = 'infosec_portal'
);
\gexec

GRANT ALL PRIVILEGES ON DATABASE infosec_portal TO infosec_app;
ALTER ROLE infosec_app IN DATABASE infosec_portal SET search_path TO public;

\echo '== Connecting to database =='
\c infosec_portal

\echo '== Enabling extensions in public schema =='
CREATE SCHEMA IF NOT EXISTS public;
CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;
CREATE EXTENSION IF NOT EXISTS citext WITH SCHEMA public;

\echo '== Removing old custom admin schema if present =='
DROP SCHEMA IF EXISTS admin CASCADE;

\echo '== Ensuring public schema privileges =='
ALTER SCHEMA public OWNER TO infosec_app;
GRANT USAGE, CREATE ON SCHEMA public TO infosec_app;

\echo '== Ensuring custom login tables match Django migration shape =='

CREATE TABLE IF NOT EXISTS public.roles_permission (
  role_id      VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
  role_name    VARCHAR(255) NOT NULL,
  description  TEXT NULL,
  permissions  TEXT NULL,
  access_level INT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS public.users (
  user_id     VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
  employee_id VARCHAR(255) NULL,
  first_name  VARCHAR(255) NOT NULL,
  last_name   VARCHAR(255) NOT NULL,
  email       VARCHAR(255) NOT NULL UNIQUE,
  password    VARCHAR(255) NOT NULL,
  status      VARCHAR(10) NOT NULL DEFAULT 'Active',
  type        VARCHAR(10) NOT NULL DEFAULT 'Employee',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  role_id     VARCHAR(255) NULL REFERENCES public.roles_permission(role_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_users_email ON public.users (email);

\echo '== Seeding base custom roles =='

WITH existing AS (
  UPDATE public.roles_permission
  SET description = 'Full access',
      permissions = 'Home, Documents, Policies, RecentNews, Others, UserManagement',
      access_level = 10
  WHERE role_name = 'Admin'
  RETURNING role_id
)
INSERT INTO public.roles_permission (role_id, role_name, description, permissions, access_level)
SELECT gen_random_uuid()::text, 'Admin', 'Full access',
       'Home, Documents, Policies, RecentNews, Others, UserManagement', 10
WHERE NOT EXISTS (SELECT 1 FROM existing);

WITH existing AS (
  UPDATE public.roles_permission
  SET description = 'Limited access',
      permissions = 'Home, Documents, Policies, RecentNews, Others',
      access_level = 3
  WHERE role_name = 'Staff'
  RETURNING role_id
)
INSERT INTO public.roles_permission (role_id, role_name, description, permissions, access_level)
SELECT gen_random_uuid()::text, 'Staff', 'Limited access',
       'Home, Documents, Policies, RecentNews, Others', 3
WHERE NOT EXISTS (SELECT 1 FROM existing);

\echo '== Seeding base custom users =='

INSERT INTO public.users (
  user_id, employee_id, first_name, last_name, email, password, status, type, role_id
)
VALUES (
  gen_random_uuid()::text,
  'EMP-0001',
  'Juan',
  'Dela Cruz',
  'juan@gmail.com',
  crypt('password123', gen_salt('bf', 6)),
  'Active',
  'Admin',
  (SELECT role_id FROM public.roles_permission WHERE role_name='Admin' LIMIT 1)
)
ON CONFLICT (email) DO UPDATE
SET first_name = EXCLUDED.first_name,
    last_name  = EXCLUDED.last_name,
    password   = EXCLUDED.password,
    status     = EXCLUDED.status,
    type       = EXCLUDED.type,
    role_id    = EXCLUDED.role_id,
    updated_at = NOW();

INSERT INTO public.users (
  user_id, employee_id, first_name, last_name, email, password, status, type, role_id
)
VALUES (
  gen_random_uuid()::text,
  'EMP-0002',
  'Maria',
  'Santos',
  'employee@gmail.com',
  crypt('password123', gen_salt('bf', 6)),
  'Active',
  'Employee',
  (SELECT role_id FROM public.roles_permission WHERE role_name='Staff' LIMIT 1)
)
ON CONFLICT (email) DO UPDATE
SET first_name = EXCLUDED.first_name,
    last_name  = EXCLUDED.last_name,
    password   = EXCLUDED.password,
    status     = EXCLUDED.status,
    type       = EXCLUDED.type,
    role_id    = EXCLUDED.role_id,
    updated_at = NOW();

\echo '== Granting privileges =='
GRANT USAGE, CREATE ON SCHEMA public TO infosec_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO infosec_app;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO infosec_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO infosec_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO infosec_app;

\echo '== Quick verification =='
SHOW search_path;

SELECT
  u.email,
  u.status,
  u.type,
  r.role_name,
  r.permissions,
  (u.password = crypt('password123', u.password)) AS password_ok
FROM public.users u
LEFT JOIN public.roles_permission r ON r.role_id = u.role_id
WHERE u.email IN ('juan@gmail.com','employee@gmail.com')
ORDER BY u.email;
