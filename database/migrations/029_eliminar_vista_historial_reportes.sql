BEGIN TRANSACTION;

DROP VIEW IF EXISTS vw_reportes_historial_pagos_admin;

INSERT INTO esquema_migraciones(version, descripcion, checksum)
SELECT '029', 'eliminar_vista_historial_reportes', NULL
WHERE NOT EXISTS (
    SELECT 1
    FROM esquema_migraciones
    WHERE version = '029'
);

COMMIT;
