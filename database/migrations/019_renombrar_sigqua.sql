UPDATE configuracion_sistema
SET valor = 'SIGQUA',
    descripcion = 'Nombre del sistema.'
WHERE clave = 'sistema.nombre';

UPDATE configuracion_sistema
SET descripcion = REPLACE(descripcion, 'SICAP', 'SIGQUA')
WHERE descripcion LIKE '%SICAP%';

UPDATE configuracion_sistema
SET valor = REPLACE(valor, 'SICAP', 'SIGQUA')
WHERE valor LIKE '%SICAP%';

UPDATE configuracion_sistema
SET valor = REPLACE(valor, 'sicap', 'sigqua')
WHERE valor LIKE '%sicap%';

INSERT INTO esquema_migraciones(version, descripcion, checksum)
SELECT '019', 'renombrar_sigqua', NULL
WHERE NOT EXISTS (
    SELECT 1
    FROM esquema_migraciones
    WHERE version = '019'
);
