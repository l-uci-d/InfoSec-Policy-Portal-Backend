\set ON_ERROR_STOP on

\echo '== Seeding MORE custom dummy users in public.users =='

-- NOTE:
-- These accounts are for the custom public.users table.
-- Your current /login/ endpoint authenticates against Django public.auth_user.
-- For actual login accounts, run: python manage.py create_users --reset
-- Password for all custom dummy users below: password123

INSERT INTO public.users (user_id, employee_id, first_name, last_name, email, password, status, type, role_id)
VALUES
  -- Admins
  (gen_random_uuid()::text, 'EMP-1001', 'Jeff',   'Kawabata', 'jeff.admin@gmail.com',   crypt('password123', gen_salt('bf', 6)), 'Active', 'Admin',
    (SELECT role_id FROM public.roles_permission WHERE role_name='Admin' LIMIT 1)),
  (gen_random_uuid()::text, 'EMP-1002', 'Trisha', 'Dizon',    'trisha.admin@gmail.com', crypt('password123', gen_salt('bf', 6)), 'Active', 'Admin',
    (SELECT role_id FROM public.roles_permission WHERE role_name='Admin' LIMIT 1)),
  (gen_random_uuid()::text, 'EMP-1003', 'Noah',   'Lim',      'noah.admin@gmail.com',   crypt('password123', gen_salt('bf', 6)), 'Active', 'Admin',
    (SELECT role_id FROM public.roles_permission WHERE role_name='Admin' LIMIT 1)),
  (gen_random_uuid()::text, 'EMP-1004', 'Ari',    'Santos',   'ari.admin@gmail.com',    crypt('password123', gen_salt('bf', 6)), 'Active', 'Admin',
    (SELECT role_id FROM public.roles_permission WHERE role_name='Admin' LIMIT 1)),

  -- Staff / Employees
  (gen_random_uuid()::text, 'EMP-2001', 'Maria',  'Santos',   'maria.staff@gmail.com',  crypt('password123', gen_salt('bf', 6)), 'Active', 'Employee',
    (SELECT role_id FROM public.roles_permission WHERE role_name='Staff' LIMIT 1)),
  (gen_random_uuid()::text, 'EMP-2002', 'Ana',    'Reyes',    'ana.staff@gmail.com',    crypt('password123', gen_salt('bf', 6)), 'Active', 'Employee',
    (SELECT role_id FROM public.roles_permission WHERE role_name='Staff' LIMIT 1)),
  (gen_random_uuid()::text, 'EMP-2003', 'Miguel', 'Garcia',   'miguel.staff@gmail.com', crypt('password123', gen_salt('bf', 6)), 'Active', 'Employee',
    (SELECT role_id FROM public.roles_permission WHERE role_name='Staff' LIMIT 1)),
  (gen_random_uuid()::text, 'EMP-2004', 'Lara',   'Torres',   'lara.staff@gmail.com',   crypt('password123', gen_salt('bf', 6)), 'Active', 'Employee',
    (SELECT role_id FROM public.roles_permission WHERE role_name='Staff' LIMIT 1)),
  (gen_random_uuid()::text, 'EMP-2005', 'Paolo',  'Cruz',     'paolo.staff@gmail.com',  crypt('password123', gen_salt('bf', 6)), 'Active', 'Employee',
    (SELECT role_id FROM public.roles_permission WHERE role_name='Staff' LIMIT 1)),
  (gen_random_uuid()::text, 'EMP-2006', 'Sofia',  'Navarro',  'sofia.staff@gmail.com',  crypt('password123', gen_salt('bf', 6)), 'Active', 'Employee',
    (SELECT role_id FROM public.roles_permission WHERE role_name='Staff' LIMIT 1))

ON CONFLICT (email) DO UPDATE
SET employee_id = EXCLUDED.employee_id,
    first_name   = EXCLUDED.first_name,
    last_name    = EXCLUDED.last_name,
    password     = EXCLUDED.password,
    status       = EXCLUDED.status,
    type         = EXCLUDED.type,
    role_id      = EXCLUDED.role_id,
    updated_at   = NOW();

\echo '== Quick verification: custom dummy users =='

SELECT
  u.email,
  u.status,
  u.type,
  r.role_name,
  r.permissions,
  (u.password = crypt('password123', u.password)) AS password_ok
FROM public.users u
LEFT JOIN public.roles_permission r ON r.role_id = u.role_id
WHERE u.email IN (
  'jeff.admin@gmail.com',
  'trisha.admin@gmail.com',
  'noah.admin@gmail.com',
  'ari.admin@gmail.com',
  'maria.staff@gmail.com',
  'ana.staff@gmail.com',
  'miguel.staff@gmail.com',
  'lara.staff@gmail.com',
  'paolo.staff@gmail.com',
  'sofia.staff@gmail.com'
)
ORDER BY u.email;
