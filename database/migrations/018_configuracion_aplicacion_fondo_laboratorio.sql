INSERT OR IGNORE INTO configuracion_sistema(clave, valor, tipo_dato, categoria, descripcion, editable) VALUES
('ui.laboratorio.fondo_aplicado', '0', 'BOOLEANO', 'Laboratorio visual', 'Indica si el fondo temporal se aplica al shell principal.', 1);

INSERT INTO esquema_migraciones(version, descripcion, checksum)
SELECT '018', 'configuracion_aplicacion_fondo_laboratorio', NULL
WHERE NOT EXISTS (
    SELECT 1
    FROM esquema_migraciones
    WHERE version = '018'
);
