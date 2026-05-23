import argparse
import getpass
import os
import shutil
import subprocess
import sys
from pathlib import Path

import psycopg2
from psycopg2 import sql


DEFAULTS = {
    "db_name": "infosec_portal",
    "db_user": "infosec_app",
    "db_password": "admin123",
    "host": "127.0.0.1",
    "port": "5432",
    "admin_user": "postgres",
    "admin_db": "postgres",
}


BASE_DIR = Path(__file__).resolve().parent


def connect(dbname, user, password, host, port):
    return psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port,
    )


def run_command(command, *, cwd=None, env=None, label=None):
    if label:
        print(f"\n== {label} ==")

    print("Running:", " ".join(str(part) for part in command))

    try:
        subprocess.run(
            [str(part) for part in command],
            cwd=str(cwd) if cwd else None,
            env=env,
            check=True,
        )
    except FileNotFoundError as exc:
        print(f"Command not found: {command[0]}")
        print(exc)
        sys.exit(1)
    except subprocess.CalledProcessError as exc:
        print(f"Command failed with exit code {exc.returncode}.")
        sys.exit(exc.returncode)


def run_psql_file(*, psql_exe, sql_file, database, args, admin_password):
    sql_file = Path(sql_file).resolve()

    if not sql_file.exists():
        print(f"SQL file not found: {sql_file}")
        sys.exit(1)

    env = os.environ.copy()

    # Lets psql run non-interactively using the same password already entered once.
    env["PGPASSWORD"] = admin_password

    run_command(
        [
            psql_exe,
            "-U",
            args.admin_user,
            "-h",
            args.host,
            "-p",
            args.port,
            "-d",
            database,
            "-v",
            "ON_ERROR_STOP=1",
            "-f",
            sql_file,
        ],
        env=env,
        label=f"Loading SQL file: {sql_file.name}",
    )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Reset/create the local PostgreSQL database for InfoSec Portal using "
            "the public schema, then optionally run Django migrations and seed SQL data."
        )
    )

    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop and recreate the local database.",
    )
    parser.add_argument(
        "--db-name",
        default=os.getenv("DB_NAME", DEFAULTS["db_name"]),
    )
    parser.add_argument(
        "--db-user",
        default=os.getenv("DB_USER", DEFAULTS["db_user"]),
    )
    parser.add_argument(
        "--db-password",
        default=os.getenv("DB_PASSWORD", DEFAULTS["db_password"]),
    )
    parser.add_argument(
        "--host",
        default=os.getenv("DB_HOST", DEFAULTS["host"]),
    )
    parser.add_argument(
        "--port",
        default=os.getenv("DB_PORT", DEFAULTS["port"]),
    )
    parser.add_argument(
        "--admin-user",
        default=os.getenv("PG_ADMIN_USER", DEFAULTS["admin_user"]),
    )
    parser.add_argument(
        "--admin-db",
        default=os.getenv("PG_ADMIN_DB", DEFAULTS["admin_db"]),
    )
    parser.add_argument(
        "--admin-password",
        default=os.getenv("PG_ADMIN_PASSWORD"),
    )

    parser.add_argument(
        "--backend-dir",
        default=os.getenv("BACKEND_DIR", str(BASE_DIR / "InfoSecBackend")),
        help="Path to the Django project folder containing manage.py.",
    )
    parser.add_argument(
        "--schema-sql",
        default=os.getenv("SCHEMA_SQL", str(BASE_DIR / "psql_infosec_db.sql")),
        help="Path to psql_infosec_db.sql.",
    )
    parser.add_argument(
        "--dummy-sql",
        default=os.getenv("DUMMY_SQL", str(BASE_DIR / "psql_dummy_data.sql")),
        help="Path to psql_dummy_data.sql.",
    )
    parser.add_argument(
        "--psql-path",
        default=os.getenv("PSQL_PATH", "psql"),
        help="Path to the psql executable if it is not available in PATH.",
    )
    parser.add_argument(
        "--skip-migrate",
        action="store_true",
        help="Do not run python manage.py migrate.",
    )
    parser.add_argument(
        "--skip-sql",
        action="store_true",
        help="Do not load psql_infosec_db.sql and psql_dummy_data.sql.",
    )
    parser.add_argument(
        "--skip-create-users",
        action="store_true",
        help="Do not run python manage.py create_users --reset.",
    )

    args = parser.parse_args()

    backend_dir = Path(args.backend_dir).resolve()
    manage_py = backend_dir / "manage.py"

    admin_password = args.admin_password
    if admin_password is None:
        admin_password = getpass.getpass(
            f"PostgreSQL admin password for '{args.admin_user}': "
        )

    try:
        admin_conn = connect(
            dbname=args.admin_db,
            user=args.admin_user,
            password=admin_password,
            host=args.host,
            port=args.port,
        )
        admin_conn.autocommit = True
    except Exception as exc:
        print("Failed to connect as PostgreSQL admin.")
        print(exc)
        sys.exit(1)

    with admin_conn.cursor() as cur:
        if args.reset:
            print(f"Terminating active connections to '{args.db_name}'...")
            cur.execute(
                """
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = %s
                  AND pid <> pg_backend_pid();
                """,
                [args.db_name],
            )

            print(f"Dropping database '{args.db_name}' if it exists...")
            cur.execute(
                sql.SQL("DROP DATABASE IF EXISTS {}").format(
                    sql.Identifier(args.db_name)
                )
            )

        print(f"Creating/updating role '{args.db_user}'...")
        cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", [args.db_user])
        role_exists = cur.fetchone() is not None

        if role_exists:
            cur.execute(
                sql.SQL("ALTER ROLE {} WITH LOGIN PASSWORD {}").format(
                    sql.Identifier(args.db_user),
                    sql.Literal(args.db_password),
                )
            )
        else:
            cur.execute(
                sql.SQL("CREATE ROLE {} WITH LOGIN PASSWORD {}").format(
                    sql.Identifier(args.db_user),
                    sql.Literal(args.db_password),
                )
            )

        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", [args.db_name])
        db_exists = cur.fetchone() is not None

        if not db_exists:
            print(f"Creating database '{args.db_name}' owned by '{args.db_user}'...")
            cur.execute(
                sql.SQL("CREATE DATABASE {} OWNER {}").format(
                    sql.Identifier(args.db_name),
                    sql.Identifier(args.db_user),
                )
            )

        print("Granting database privileges...")
        cur.execute(
            sql.SQL("ALTER DATABASE {} OWNER TO {}").format(
                sql.Identifier(args.db_name),
                sql.Identifier(args.db_user),
            )
        )
        cur.execute(
            sql.SQL("GRANT ALL PRIVILEGES ON DATABASE {} TO {}").format(
                sql.Identifier(args.db_name),
                sql.Identifier(args.db_user),
            )
        )
        cur.execute(
            sql.SQL("ALTER ROLE {} IN DATABASE {} SET search_path TO public").format(
                sql.Identifier(args.db_user),
                sql.Identifier(args.db_name),
            )
        )

    admin_conn.close()

    try:
        db_conn = connect(
            dbname=args.db_name,
            user=args.admin_user,
            password=admin_password,
            host=args.host,
            port=args.port,
        )
        db_conn.autocommit = True
    except Exception as exc:
        print(f"Failed to connect to database '{args.db_name}' as admin.")
        print(exc)
        sys.exit(1)

    with db_conn.cursor() as cur:
        print("Ensuring public schema and required extensions...")
        cur.execute("CREATE SCHEMA IF NOT EXISTS public;")
        cur.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;")
        cur.execute("CREATE EXTENSION IF NOT EXISTS citext WITH SCHEMA public;")

        print("Ensuring there is no leftover custom admin schema...")
        cur.execute("DROP SCHEMA IF EXISTS admin CASCADE;")

        print("Granting public schema privileges...")
        cur.execute(
            sql.SQL("ALTER SCHEMA public OWNER TO {}").format(
                sql.Identifier(args.db_user)
            )
        )
        cur.execute(
            sql.SQL("GRANT USAGE, CREATE ON SCHEMA public TO {}").format(
                sql.Identifier(args.db_user)
            )
        )
        cur.execute(
            sql.SQL("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO {}").format(
                sql.Identifier(args.db_user)
            )
        )
        cur.execute(
            sql.SQL(
                "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO {}"
            ).format(
                sql.Identifier(args.db_user)
            )
        )
        cur.execute(
            sql.SQL(
                "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
                "GRANT ALL PRIVILEGES ON TABLES TO {}"
            ).format(
                sql.Identifier(args.db_user)
            )
        )
        cur.execute(
            sql.SQL(
                "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
                "GRANT ALL PRIVILEGES ON SEQUENCES TO {}"
            ).format(
                sql.Identifier(args.db_user)
            )
        )

    db_conn.close()

    if not args.skip_migrate:
        if not manage_py.exists():
            print(f"manage.py not found: {manage_py}")
            print("Use --backend-dir to point to the folder containing manage.py.")
            sys.exit(1)

        run_command(
            [sys.executable, "manage.py", "migrate"],
            cwd=backend_dir,
            label="Running Django migrations",
        )

    if not args.skip_sql:
        psql_exe = args.psql_path

        if psql_exe == "psql" and shutil.which("psql") is None:
            print("psql was not found in PATH.")
            print(
                "Install PostgreSQL command-line tools or pass --psql-path "
                "with the full path to psql.exe."
            )
            print(r'Example: --psql-path "C:\Program Files\PostgreSQL\17\bin\psql.exe"')
            sys.exit(1)

        run_psql_file(
            psql_exe=psql_exe,
            sql_file=args.schema_sql,
            database=args.admin_db,
            args=args,
            admin_password=admin_password,
        )
        
        """ run_psql_file(
            psql_exe=psql_exe,
            sql_file=args.dummy_sql,
            database=args.db_name,
            args=args,
            admin_password=admin_password,
        ) """

    if not args.skip_create_users:
        if not manage_py.exists():
            print(f"manage.py not found: {manage_py}")
            print("Use --backend-dir to point to the folder containing manage.py.")
            sys.exit(1)

        run_command(
            [sys.executable, "manage.py", "create_users", "--reset"],
            cwd=backend_dir,
            label="Creating Django login demo users",
        )

    print()
    print("Local PostgreSQL DB setup complete.")
    print(f"Database: {args.db_name}")
    print(f"User: {args.db_user}")
    print("Schema: public")
    print()
    print("You can now run:")
    print("  cd InfoSecBackend")
    print("  python manage.py runserver")


if __name__ == "__main__":
    main()