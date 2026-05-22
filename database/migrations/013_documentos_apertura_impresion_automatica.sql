BEGIN TRANSACTION;

INSERT OR IGNORE INTO configuracion_sistema(clave, valor, tipo_dato, categoria, descripcion, editable) VALUES
('documentos.abrir_pdf_automaticamente', '1', 'BOOLEANO', 'Documentos', 'Controla si SICAP abre automaticamente el comprobante PDF despues de registrar un pago.', 1),
('documentos.imprimir_pdf_automaticamente', '0', 'BOOLEANO', 'Documentos', 'Controla si SICAP envia automaticamente el comprobante PDF a impresion despues de registrar un pago.', 1);

INSERT INTO esquema_migraciones(version, descripcion, checksum)
SELECT '013', 'documentos_apertura_impresion_automatica', NULL
WHERE NOT EXISTS (
    SELECT 1
    FROM esquema_migraciones
    WHERE version = '013'
);

COMMIT;
