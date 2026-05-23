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

\echo '== Granting privileges =='
GRANT USAGE, CREATE ON SCHEMA public TO infosec_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO infosec_app;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO infosec_app;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO infosec_app;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO infosec_app;

\echo '== Base PostgreSQL setup complete =='