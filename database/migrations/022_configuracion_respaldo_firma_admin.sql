-- Madura Configuracion para uso administrativo: firma visual y respaldo al cierre.

INSERT INTO configuracion_sistema (clave, valor, tipo_dato, categoria, descripcion, editable)
VALUES
('documentos.firma_texto_linea', 'Firma autorizada', 'TEXTO', 'Documentos', 'Texto bajo la linea de firma impresa.', 1)
ON CONFLICT(clave) DO NOTHING;

UPDATE configuracion_sistema
SET valor = COALESCE(NULLIF(TRIM(valor), ''), 'Firma autorizada')
WHERE clave = 'documentos.firma_texto_linea';

DELETE FROM configuracion_sistema
WHERE clave IN (
    'documentos.firma_nombre',
    'documentos.firma_cargo',
    'documentos.firma_identificador',
    'documentos.firma_texto_apoyo'
);

UPDATE configuracion_sistema
SET valor = '1',
    editable = 0,
    descripcion = 'Respaldo automatico obligatorio al cerrar sesion o salir del sistema.'
WHERE clave = 'sistema.respaldo_automatico';

DELETE FROM configuracion_sistema
WHERE clave IN (
    'respaldo.programacion_tipo',
    'respaldo.programacion_hora',
    'respaldo.programacion_dia_semana'
);
