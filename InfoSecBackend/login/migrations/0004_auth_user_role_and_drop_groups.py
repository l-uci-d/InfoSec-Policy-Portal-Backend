from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('login', '0003_role_userprofile_delete_rolespermission'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE public.auth_user
                ADD COLUMN IF NOT EXISTS role_id VARCHAR(255) NULL;

                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1
                        FROM pg_constraint
                        WHERE conname = 'auth_user_role_id_fkey'
                    ) THEN
                        ALTER TABLE public.auth_user
                        ADD CONSTRAINT auth_user_role_id_fkey
                        FOREIGN KEY (role_id)
                        REFERENCES public.role(role_id)
                        ON DELETE SET NULL;
                    END IF;
                END $$;
            """,
            reverse_sql="""
                ALTER TABLE public.auth_user
                DROP CONSTRAINT IF EXISTS auth_user_role_id_fkey;
                ALTER TABLE public.auth_user
                DROP COLUMN IF EXISTS role_id;
            """,
        ),
        migrations.RunSQL(
            sql="""
                DROP TABLE IF EXISTS public.auth_user_user_permissions CASCADE;
                DROP TABLE IF EXISTS public.auth_user_groups CASCADE;
                DROP TABLE IF EXISTS public.auth_group_permissions CASCADE;
                DROP TABLE IF EXISTS public.auth_group CASCADE;
            """,
            reverse_sql="""
                -- Recreating Django auth group tables is intentionally omitted.
            """,
        ),
    ]
