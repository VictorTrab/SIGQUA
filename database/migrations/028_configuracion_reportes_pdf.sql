BEGIN TRANSACTION;

INSERT INTO configuracion_sistema (clave, valor, tipo_dato, categoria, descripcion, editable)
VALUES
('reportes.ruta_salida', '', 'TEXTO', 'Reportes PDF', 'Carpeta configurada para guardar reportes PDF. Vacia usa Descargas/SIGQUA Reportes.', 1),
('reportes.abrir_automaticamente', '1', 'BOOLEANO', 'Reportes PDF', 'Abre el reporte despues de generarlo.', 1),
('reportes.firma_habilitada', '0', 'BOOLEANO', 'Reportes PDF', 'Muestra una linea de firma en reportes administrativos.', 1),
('reportes.firma_texto_linea', 'Firma autorizada', 'TEXTO', 'Reportes PDF', 'Texto mostrado bajo la linea de firma del reporte.', 1)
ON CONFLICT(clave) DO NOTHING;

INSERT INTO esquema_migraciones(version, descripcion, checksum)
SELECT '028', 'configuracion_reportes_pdf', NULL
WHERE NOT EXISTS (
    SELECT 1
    FROM esquema_migraciones
    WHERE version = '028'
);

COMMIT;
