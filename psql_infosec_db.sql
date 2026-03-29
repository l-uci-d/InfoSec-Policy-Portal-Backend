\echo '== Creating app role =='

-- Create role only if missing (psql way)
SELECT format(
  'CREATE ROLE %I WITH LOGIN PASSWORD %L;',
  'infosec_app',
  'admin123'
)
WHERE NOT EXISTS (
  SELECT 1 FROM pg_roles WHERE rolname = 'infosec_app'
);
\gexec

\echo '== Creating database =='

-- CREATE DATABASE cannot run inside DO/transactions, so use \gexec
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

\echo '== Connecting to database =='
\c infosec_portal

\echo '== Enabling extensions =='
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS citext;

\echo '== Creating schema =='
CREATE SCHEMA IF NOT EXISTS admin AUTHORIZATION infosec_app;
GRANT USAGE, CREATE ON SCHEMA admin TO infosec_app;

\echo '== Creating tables =='

CREATE TABLE IF NOT EXISTS admin.roles_permission (
  role_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  role_name    TEXT UNIQUE NOT NULL,
  description  TEXT,
  permissions  JSONB NOT NULL DEFAULT '{}'::jsonb,
  access_level INT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS admin.users (
  user_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  employee_id TEXT,
  first_name  TEXT NOT NULL,
  last_name   TEXT NOT NULL,
  email       CITEXT NOT NULL UNIQUE,
  password    TEXT NOT NULL,
  status      TEXT NOT NULL DEFAULT 'Active',
  type        TEXT NOT NULL DEFAULT 'User',
  role_id     UUID NULL REFERENCES admin.roles_permission(role_id) ON DELETE SET NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON admin.users (email);

\echo '== Seeding role + user =='

INSERT INTO admin.roles_permission (role_name, description, permissions, access_level)
VALUES (
  'Admin',
  'Full access',
  '{"users":["read","write"],"policies":["read","write"]}'::jsonb,
  10
)
ON CONFLICT (role_name) DO NOTHING;

INSERT INTO admin.users (
  employee_id, first_name, last_name, email, password, status, type, role_id
)
VALUES (
  'EMP-0001',
  'Juan',
  'Dela Cruz',
  'juan@gmail.com',
  crypt('password123', gen_salt('bf', 6)),
  'Active',
  'Admin',
  (SELECT role_id FROM admin.roles_permission WHERE role_name='Admin')
)
ON CONFLICT (email) DO NOTHING;

\echo '== Quick verification =='
SELECT email, (password = crypt('password123', password)) AS password_ok
FROM admin.users
WHERE email='juan@gmail.com';