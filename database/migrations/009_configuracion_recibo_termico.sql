BEGIN TRANSACTION;

INSERT OR IGNORE INTO configuracion_sistema(clave, valor, tipo_dato, categoria, descripcion, editable) VALUES
('factura.titulo_documento', 'RECIBO DE PAGO', 'TEXTO', 'Factura', 'Titulo principal del recibo de pago.', 1),
('factura.subtitulo_documento', '', 'TEXTO', 'Factura', 'Subtitulo opcional del recibo de pago.', 1),
('factura.texto_legal_superior', '', 'TEXTO', 'Factura', 'Texto legal corto mostrado antes del detalle del recibo.', 1),
('factura.texto_legal_inferior', '', 'TEXTO', 'Factura', 'Texto legal corto mostrado despues del pie del recibo.', 1),
('factura.etiqueta_copia', 'ORIGINAL', 'TEXTO', 'Factura', 'Etiqueta de copia mostrada en el recibo.', 1),
('factura.mostrar_correo', '1', 'BOOLEANO', 'Factura', 'Permite mostrar el correo institucional en el recibo.', 1),
('factura.mostrar_telefono', '1', 'BOOLEANO', 'Factura', 'Permite mostrar el telefono institucional en el recibo.', 1),
('factura.mostrar_direccion', '1', 'BOOLEANO', 'Factura', 'Permite mostrar la direccion institucional en el recibo.', 1),
('factura.mostrar_identificador_fiscal', '0', 'BOOLEANO', 'Factura', 'Permite mostrar el identificador fiscal institucional en el recibo.', 1),
('junta.identificador_fiscal', '', 'TEXTO', 'Junta', 'Identificador fiscal o RTN institucional.', 1),
('junta.sitio_web', '', 'TEXTO', 'Junta', 'Sitio web institucional.', 1),
('junta.mensaje_contacto', '', 'TEXTO', 'Junta', 'Mensaje institucional corto para contacto o soporte.', 1);

UPDATE configuracion_sistema
SET valor = 'HTML',
    actualizado_en = datetime('now')
WHERE clave = 'factura.formato_salida'
  AND upper(COALESCE(valor, '')) = 'PDF';

INSERT INTO esquema_migraciones(version, descripcion, checksum)
SELECT '009', 'configuracion_recibo_termico', NULL
WHERE NOT EXISTS (
    SELECT 1
    FROM esquema_migraciones
    WHERE version = '009'
);

COMMIT;
