BEGIN TRANSACTION;

INSERT OR IGNORE INTO configuracion_sistema(clave, valor, tipo_dato, categoria, descripcion, editable) VALUES
('empresa.nombre', '', 'TEXTO', 'Empresa', 'Nombre legal o comercial visible en documentos y cabeceras.', 1),
('empresa.telefono', '', 'TEXTO', 'Empresa', 'Telefono institucional visible en documentos y cabeceras.', 1),
('empresa.correo', '', 'TEXTO', 'Empresa', 'Correo institucional visible en documentos y cabeceras.', 1),
('empresa.direccion', '', 'TEXTO', 'Empresa', 'Direccion fiscal u operativa visible en documentos y cabeceras.', 1),
('empresa.identificador_fiscal', '', 'TEXTO', 'Empresa', 'Identificador fiscal visible en documentos y cabeceras.', 1),
('empresa.sitio_web', '', 'TEXTO', 'Empresa', 'Sitio web institucional visible en documentos y cabeceras.', 1),
('empresa.mensaje_contacto', '', 'TEXTO', 'Empresa', 'Mensaje de contacto institucional para documentos y cabeceras.', 1),
('seguridad.duracion_sesion_horas', '8', 'DECIMAL', 'Seguridad', 'Duracion del cierre automatico de sesion en horas.', 1),
('respaldo.ruta_principal', './respaldos', 'TEXTO', 'Respaldo', 'Carpeta principal donde SIGQUA genera los respaldos locales.', 1),
('respaldo.ruta_secundaria', '', 'TEXTO', 'Respaldo', 'Carpeta secundaria opcional para copia adicional de respaldos.', 1),
('respaldo.secundaria_activa', '0', 'BOOLEANO', 'Respaldo', 'Indica si SIGQUA debe guardar una copia secundaria del respaldo.', 1),
('respaldo.comprimir_zip', '1', 'BOOLEANO', 'Respaldo', 'Indica si el respaldo debe comprimirse como ZIP.', 1),
('respaldo.organizar_por_periodo', '1', 'BOOLEANO', 'Respaldo', 'Organiza respaldos por carpetas de año y mes.', 1),
('respaldo.retencion_dias', '30', 'ENTERO', 'Respaldo', 'Cantidad de dias a conservar respaldos gestionados por SIGQUA.', 1);

UPDATE configuracion_sistema
SET valor = COALESCE(NULLIF((SELECT valor FROM configuracion_sistema WHERE clave = 'junta.nombre'), ''), valor)
WHERE clave = 'empresa.nombre';

UPDATE configuracion_sistema
SET valor = COALESCE(NULLIF((SELECT valor FROM configuracion_sistema WHERE clave = 'junta.telefono'), ''), valor)
WHERE clave = 'empresa.telefono';

UPDATE configuracion_sistema
SET valor = COALESCE(NULLIF((SELECT valor FROM configuracion_sistema WHERE clave = 'junta.correo'), ''), valor)
WHERE clave = 'empresa.correo';

UPDATE configuracion_sistema
SET valor = COALESCE(NULLIF((SELECT valor FROM configuracion_sistema WHERE clave = 'junta.direccion'), ''), valor)
WHERE clave = 'empresa.direccion';

UPDATE configuracion_sistema
SET valor = COALESCE(NULLIF((SELECT valor FROM configuracion_sistema WHERE clave = 'junta.identificador_fiscal'), ''), valor)
WHERE clave = 'empresa.identificador_fiscal';

UPDATE configuracion_sistema
SET valor = COALESCE(NULLIF((SELECT valor FROM configuracion_sistema WHERE clave = 'junta.sitio_web'), ''), valor)
WHERE clave = 'empresa.sitio_web';

UPDATE configuracion_sistema
SET valor = COALESCE(NULLIF((SELECT valor FROM configuracion_sistema WHERE clave = 'junta.mensaje_contacto'), ''), valor)
WHERE clave = 'empresa.mensaje_contacto';

UPDATE configuracion_sistema
SET valor = COALESCE(
    NULLIF((SELECT valor FROM configuracion_sistema WHERE clave = 'mantenimiento.ruta_respaldos'), ''),
    valor
)
WHERE clave = 'respaldo.ruta_principal';

UPDATE configuracion_sistema
SET valor = COALESCE(
    NULLIF((SELECT valor FROM configuracion_sistema WHERE clave = 'mantenimiento.dias_retencion_respaldos'), ''),
    valor
)
WHERE clave = 'respaldo.retencion_dias';

INSERT INTO esquema_migraciones(version, descripcion, checksum)
SELECT '012', 'configuracion_empresa_respaldo_sesion', NULL
WHERE NOT EXISTS (
    SELECT 1
    FROM esquema_migraciones
    WHERE version = '012'
);

COMMIT;
