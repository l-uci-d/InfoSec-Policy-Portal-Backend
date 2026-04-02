\echo '== Seeding MORE dummy users (Admins + Staff, gmail only) =='

-- NOTE: all these accounts use password: password123
-- Use DO UPDATE so re-running refreshes the data consistently.

INSERT INTO admin.users (first_name, last_name, email, password, status, type, role_id)
VALUES
  -- Admins
  ('Jeff',   'Kawabata',  'jeff.admin@gmail.com',    crypt('password123', gen_salt('bf', 6)), 'Active',   'Admin',
    (SELECT role_id FROM admin.roles_permission WHERE role_name='Admin')),
  ('Trisha', 'Dizon',     'trisha.admin@gmail.com',  crypt('password123', gen_salt('bf', 6)), 'Active',   'Admin',
    (SELECT role_id FROM admin.roles_permission WHERE role_name='Admin')),
  ('Noah',   'Lim',       'noah.admin@gmail.com',    crypt('password123', gen_salt('bf', 6)), 'Active',   'Admin',
    (SELECT role_id FROM admin.roles_permission WHERE role_name='Admin')),
  ('Ari',    'Santos',    'ari.admin@gmail.com',     crypt('password123', gen_salt('bf', 6)), 'Active', 'Admin',
    (SELECT role_id FROM admin.roles_permission WHERE role_name='Admin')),

  -- Staff
  ('Maria',  'Santos',    'maria.staff@gmail.com',   crypt('password123', gen_salt('bf', 6)), 'Active',   'User',
    (SELECT role_id FROM admin.roles_permission WHERE role_name='Staff')),
  ('Ana',    'Reyes',     'ana.staff@gmail.com',     crypt('password123', gen_salt('bf', 6)), 'Active',   'User',
    (SELECT role_id FROM admin.roles_permission WHERE role_name='Staff')),
  ('Miguel', 'Garcia',    'miguel.staff@gmail.com',  crypt('password123', gen_salt('bf', 6)), 'Active',   'User',
    (SELECT role_id FROM admin.roles_permission WHERE role_name='Staff')),
  ('Lara',   'Torres',    'lara.staff@gmail.com',    crypt('password123', gen_salt('bf', 6)), 'Active',   'User',
    (SELECT role_id FROM admin.roles_permission WHERE role_name='Staff')),
  ('Paolo',  'Cruz',      'paolo.staff@gmail.com',   crypt('password123', gen_salt('bf', 6)), 'Active',   'User',
    (SELECT role_id FROM admin.roles_permission WHERE role_name='Staff')),
  ('Sofia',  'Navarro',   'sofia.staff@gmail.com',   crypt('password123', gen_salt('bf', 6)), 'Active', 'User',
    (SELECT role_id FROM admin.roles_permission WHERE role_name='Staff'))

ON CONFLICT (email) DO UPDATE
SET first_name = EXCLUDED.first_name,
    last_name  = EXCLUDED.last_name,
    password   = EXCLUDED.password,
    status     = EXCLUDED.status,
    type       = EXCLUDED.type,
    role_id    = EXCLUDED.role_id;


\echo '== Quick verification (more users) =='
SELECT
  u.email,
  u.status,
  u.type,
  r.role_name,
  r.permissions,
  (u.password = crypt('password123', u.password)) AS password_ok
FROM admin.users u
LEFT JOIN admin.roles_permission r ON r.role_id = u.role_id
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
);