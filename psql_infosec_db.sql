\echo '== Creating app role =='

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

-- CHANGED: permissions is TEXT (module allowlist)
CREATE TABLE IF NOT EXISTS admin.roles_permission (
  role_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  role_name    TEXT UNIQUE NOT NULL,
  description  TEXT,
  permissions  TEXT NOT NULL DEFAULT 'All',
  access_level INT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS admin.users (
  user_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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

\echo '== Seeding roles =='

-- Admin can see everything
INSERT INTO admin.roles_permission (role_name, description, permissions, access_level)
VALUES ('Admin', 'Full access', 'All', 10)
ON CONFLICT (role_name) DO UPDATE
SET permissions = EXCLUDED.permissions,
    description = EXCLUDED.description,
    access_level = EXCLUDED.access_level;

-- Example limited role (shows only these modules)
INSERT INTO admin.roles_permission (role_name, description, permissions, access_level)
VALUES ('Staff', 'Limited access', 'Policies,Documents', 3)
ON CONFLICT (role_name) DO UPDATE
SET permissions = EXCLUDED.permissions,
    description = EXCLUDED.description,
    access_level = EXCLUDED.access_level;

\echo '== Seeding users =='

-- Juan (Admin)
INSERT INTO admin.users (
  first_name, last_name, email, password, status, type, role_id
)
VALUES (

  'Juan',
  'Dela Cruz',
  'juan@gmail.com',
  crypt('123', gen_salt('bf', 6)),
  'Active',
  'Admin',
  (SELECT role_id FROM admin.roles_permission WHERE role_name='Admin')
)
ON CONFLICT (email) DO NOTHING;

-- NEW USER (Staff)
INSERT INTO admin.users (
  first_name, last_name, email, password, status, type, role_id
)
VALUES (
  'Maria',
  'Santos',
  'employee@gmail.com',
  crypt('123', gen_salt('bf', 6)),
  'Active',
  'User',
  (SELECT role_id FROM admin.roles_permission WHERE role_name='Staff')
)
ON CONFLICT (email) DO NOTHING;




-- allow access to the schema
GRANT USAGE ON SCHEMA admin TO infosec_app;

-- login needs SELECT
GRANT SELECT ON TABLE admin.users TO infosec_app;

-- reset_password needs UPDATE
GRANT UPDATE ON TABLE admin.users TO infosec_app;

-- role fetch needs SELECT
GRANT SELECT ON TABLE admin.roles_permission TO infosec_app;

GRANT INSERT ON TABLE admin.users TO infosec_app;


\echo '== Quick verification =='
SELECT
  u.email,
  r.role_name,
  r.permissions,
  (u.password = crypt('password123', u.password)) AS password_ok
FROM admin.users u
LEFT JOIN admin.roles_permission r ON r.role_id = u.role_id
WHERE u.email IN ('juan@gmail.com','employee@gmail.com');