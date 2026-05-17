BEGIN TRANSACTION;

INSERT OR IGNORE INTO configuracion_sistema(clave, valor, tipo_dato, categoria, descripcion, editable) VALUES
('cobro.mora_leve_hasta_meses', '2', 'ENTERO', 'Cobro', 'Cantidad maxima de meses para clasificar una mora leve en la interfaz.', 1),
('cobro.mora_media_hasta_meses', '5', 'ENTERO', 'Cobro', 'Cantidad maxima de meses para clasificar una mora media en la interfaz.', 1);

INSERT INTO esquema_migraciones(version, descripcion, checksum)
SELECT '010', 'configuracion_mora_visual', NULL
WHERE NOT EXISTS (
    SELECT 1
    FROM esquema_migraciones
    WHERE version = '010'
);

COMMIT;
