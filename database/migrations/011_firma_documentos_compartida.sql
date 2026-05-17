BEGIN TRANSACTION;

INSERT OR IGNORE INTO configuracion_sistema(clave, valor, tipo_dato, categoria, descripcion, editable) VALUES
('documentos.firma_habilitada', '0', 'BOOLEANO', 'Documentos', 'Controla si los documentos operativos muestran la firma compartida.', 1),
('documentos.firma_nombre', '', 'TEXTO', 'Documentos', 'Nombre visible de la firma compartida para comprobantes y deuda.', 1),
('documentos.firma_cargo', '', 'TEXTO', 'Documentos', 'Cargo visible de la firma compartida para comprobantes y deuda.', 1),
('documentos.firma_identificador', '', 'TEXTO', 'Documentos', 'Identificador complementario de la firma compartida.', 1),
('documentos.firma_texto_apoyo', '', 'TEXTO', 'Documentos', 'Texto auxiliar mostrado debajo de la firma compartida.', 1);

INSERT INTO esquema_migraciones(version, descripcion, checksum)
SELECT '011', 'firma_documentos_compartida', NULL
WHERE NOT EXISTS (
    SELECT 1
    FROM esquema_migraciones
    WHERE version = '011'
);

COMMIT;
