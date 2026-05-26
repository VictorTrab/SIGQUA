BEGIN TRANSACTION;

INSERT OR IGNORE INTO configuracion_sistema(clave, valor, tipo_dato, categoria, descripcion, editable) VALUES
('documentos.firma_habilitada', '0', 'BOOLEANO', 'Documentos', 'Controla si los documentos operativos muestran la linea de firma.', 1);

INSERT INTO esquema_migraciones(version, descripcion, checksum)
SELECT '011', 'firma_documentos_compartida', NULL
WHERE NOT EXISTS (
    SELECT 1
    FROM esquema_migraciones
    WHERE version = '011'
);

COMMIT;
