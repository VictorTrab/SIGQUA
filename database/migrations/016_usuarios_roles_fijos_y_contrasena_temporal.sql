ALTER TABLE usuarios ADD COLUMN contrasena_temporal_expira_en TEXT NULL;

INSERT OR IGNORE INTO permisos(codigo, nombre, descripcion, modulo)
VALUES
('modulo.dashboard', 'Acceso a Inicio', 'Permite acceder al modulo Inicio.', 'Inicio'),
('modulo.barrios', 'Acceso a Barrios', 'Permite acceder al modulo Barrios.', 'Barrios'),
('modulo.abonados', 'Acceso a Abonados', 'Permite acceder al modulo Abonados.', 'Abonados'),
('modulo.casas', 'Acceso a Casas', 'Permite acceder al modulo Casas.', 'Casas'),
('modulo.pagos', 'Acceso a Pagos', 'Permite acceder al modulo Pagos.', 'Pagos'),
('modulo.historial_pagos', 'Acceso a Historial de pagos', 'Permite acceder al modulo Historial de pagos.', 'Historial de pagos'),
('modulo.morosidad', 'Acceso a Morosidad', 'Permite acceder al modulo Morosidad.', 'Morosidad'),
('modulo.planes_pago', 'Acceso a Planes de pago', 'Permite acceder al modulo Planes de pago.', 'Planes de pago'),
('modulo.usuarios', 'Acceso a Usuarios', 'Permite acceder al modulo Usuarios.', 'Usuarios'),
('modulo.reportes', 'Acceso a Reportes', 'Permite acceder al modulo Reportes.', 'Reportes'),
('modulo.configuracion', 'Acceso a Configuracion', 'Permite acceder al modulo Configuracion.', 'Configuracion');

UPDATE roles
SET descripcion = CASE nombre
    WHEN 'SUPERADMINISTRADOR' THEN 'Rol tecnico oculto reservado para mantenimiento y soporte sensible.'
    WHEN 'ADMINISTRADOR' THEN 'Rol principal de administracion operativa.'
    WHEN 'CAJERO' THEN 'Rol operativo orientado a cobranza y consulta diaria.'
    WHEN 'CONSULTA' THEN 'Rol de revision y consulta administrativa.'
    ELSE descripcion
END,
    estado = 'ACTIVO'
WHERE nombre IN ('SUPERADMINISTRADOR', 'ADMINISTRADOR', 'CAJERO', 'CONSULTA');

CREATE TEMP TABLE _roles_personalizados AS
SELECT id
FROM roles
WHERE nombre NOT IN ('SUPERADMINISTRADOR', 'ADMINISTRADOR', 'CAJERO', 'CONSULTA');

CREATE TEMP TABLE _roles_migracion AS
SELECT
    r.id AS rol_origen_id,
    CASE
        WHEN EXISTS (
            SELECT 1
            FROM roles_permisos rp
            INNER JOIN permisos p ON p.id = rp.permiso_id
            WHERE rp.rol_id = r.id
              AND p.codigo IN ('usuarios.gestionar', 'configuracion.gestionar')
        ) THEN (SELECT id FROM roles WHERE nombre = 'ADMINISTRADOR')
        WHEN EXISTS (
            SELECT 1
            FROM roles_permisos rp
            INNER JOIN permisos p ON p.id = rp.permiso_id
            WHERE rp.rol_id = r.id
              AND p.codigo IN ('pagos.registrar', 'planes_pago.gestionar', 'abonados.gestionar', 'casas.gestionar')
        ) THEN (SELECT id FROM roles WHERE nombre = 'CAJERO')
        ELSE (SELECT id FROM roles WHERE nombre = 'CONSULTA')
    END AS rol_fijo_id
FROM roles r
WHERE r.id IN (SELECT id FROM _roles_personalizados);

INSERT OR IGNORE INTO usuarios_roles(usuario_id, rol_id)
SELECT DISTINCT ur.usuario_id, rm.rol_fijo_id
FROM usuarios_roles ur
INNER JOIN _roles_migracion rm ON rm.rol_origen_id = ur.rol_id;

CREATE TEMP TABLE _usuario_rol_visible AS
SELECT
    u.id AS usuario_id,
    CASE
        WHEN EXISTS (
            SELECT 1
            FROM usuarios_roles ur
            INNER JOIN roles r ON r.id = ur.rol_id
            WHERE ur.usuario_id = u.id
              AND r.nombre = 'ADMINISTRADOR'
        ) THEN (SELECT id FROM roles WHERE nombre = 'ADMINISTRADOR')
        WHEN EXISTS (
            SELECT 1
            FROM usuarios_roles ur
            INNER JOIN roles r ON r.id = ur.rol_id
            WHERE ur.usuario_id = u.id
              AND r.nombre = 'CAJERO'
        ) THEN (SELECT id FROM roles WHERE nombre = 'CAJERO')
        WHEN EXISTS (
            SELECT 1
            FROM usuarios_roles ur
            INNER JOIN roles r ON r.id = ur.rol_id
            WHERE ur.usuario_id = u.id
              AND r.nombre = 'CONSULTA'
        ) THEN (SELECT id FROM roles WHERE nombre = 'CONSULTA')
        ELSE NULL
    END AS rol_fijo_id
FROM usuarios u
WHERE u.eliminado_en IS NULL
  AND u.es_oculto = 0;

DELETE FROM usuarios_roles
WHERE usuario_id IN (
    SELECT usuario_id
    FROM _usuario_rol_visible
    WHERE rol_fijo_id IS NOT NULL
)
AND rol_id IN (
    SELECT id
    FROM roles
    WHERE nombre IN ('ADMINISTRADOR', 'CAJERO', 'CONSULTA')
    UNION
    SELECT rol_origen_id
    FROM _roles_migracion
);

INSERT OR IGNORE INTO usuarios_roles(usuario_id, rol_id)
SELECT usuario_id, rol_fijo_id
FROM _usuario_rol_visible
WHERE rol_fijo_id IS NOT NULL;

DELETE FROM roles_permisos
WHERE rol_id IN (
    SELECT id
    FROM roles
    WHERE nombre IN ('ADMINISTRADOR', 'CAJERO', 'CONSULTA')
);

INSERT OR IGNORE INTO roles_permisos(rol_id, permiso_id)
SELECT
    (SELECT id FROM roles WHERE nombre = 'ADMINISTRADOR'),
    p.id
FROM permisos p
WHERE p.codigo IN (
    'modulo.dashboard',
    'modulo.barrios',
    'modulo.abonados',
    'modulo.casas',
    'modulo.pagos',
    'modulo.historial_pagos',
    'modulo.morosidad',
    'modulo.planes_pago',
    'modulo.usuarios',
    'modulo.reportes',
    'modulo.configuracion'
);

INSERT OR IGNORE INTO roles_permisos(rol_id, permiso_id)
SELECT
    (SELECT id FROM roles WHERE nombre = 'CAJERO'),
    p.id
FROM permisos p
WHERE p.codigo IN (
    'modulo.dashboard',
    'modulo.abonados',
    'modulo.casas',
    'modulo.pagos',
    'modulo.historial_pagos',
    'modulo.morosidad'
);

INSERT OR IGNORE INTO roles_permisos(rol_id, permiso_id)
SELECT
    (SELECT id FROM roles WHERE nombre = 'CONSULTA'),
    p.id
FROM permisos p
WHERE p.codigo IN (
    'modulo.dashboard',
    'modulo.abonados',
    'modulo.casas',
    'modulo.historial_pagos',
    'modulo.morosidad',
    'modulo.reportes'
);

INSERT OR IGNORE INTO roles_permisos(rol_id, permiso_id)
SELECT
    (SELECT id FROM roles WHERE nombre = 'SUPERADMINISTRADOR'),
    p.id
FROM permisos p
WHERE p.codigo IN (
    'modulo.dashboard',
    'modulo.barrios',
    'modulo.abonados',
    'modulo.casas',
    'modulo.pagos',
    'modulo.historial_pagos',
    'modulo.morosidad',
    'modulo.planes_pago',
    'modulo.usuarios',
    'modulo.reportes',
    'modulo.configuracion'
);

DELETE FROM roles_permisos
WHERE rol_id IN (SELECT rol_origen_id FROM _roles_migracion);

DELETE FROM usuarios_roles
WHERE rol_id IN (SELECT rol_origen_id FROM _roles_migracion);

DELETE FROM roles
WHERE id IN (SELECT rol_origen_id FROM _roles_migracion);

DROP TABLE _usuario_rol_visible;
DROP TABLE _roles_migracion;
DROP TABLE _roles_personalizados;

INSERT INTO esquema_migraciones(version, descripcion, checksum)
SELECT
    '016',
    'Normalizar roles fijos visibles y habilitar expiracion de contrasena temporal.',
    NULL
WHERE NOT EXISTS (
    SELECT 1
    FROM esquema_migraciones
    WHERE version = '016'
);
