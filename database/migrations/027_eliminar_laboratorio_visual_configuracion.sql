DELETE FROM configuracion_sistema
WHERE clave LIKE 'ui.laboratorio.%';

INSERT INTO esquema_migraciones(version, descripcion, checksum)
SELECT '027', 'eliminar_laboratorio_visual_configuracion', NULL
WHERE NOT EXISTS (
    SELECT 1
    FROM esquema_migraciones
    WHERE version = '027'
);
