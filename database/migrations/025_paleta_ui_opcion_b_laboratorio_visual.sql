UPDATE configuracion_sistema
SET valor = '#071A2D'
WHERE clave = 'ui.laboratorio.fondo_color_primario'
  AND valor = '#0A1728';

UPDATE configuracion_sistema
SET valor = '#0D2A45'
WHERE clave = 'ui.laboratorio.fondo_color_secundario'
  AND valor = '#1D364E';

UPDATE configuracion_sistema
SET valor = '#0D2A45'
WHERE clave = 'ui.laboratorio.modal_color_primario'
  AND valor = '#1D364E';

UPDATE configuracion_sistema
SET valor = '#123553'
WHERE clave = 'ui.laboratorio.modal_color_secundario'
  AND valor = '#243F5A';

INSERT INTO esquema_migraciones(version, descripcion, checksum)
SELECT '025', 'paleta_ui_opcion_b_laboratorio_visual', NULL
WHERE NOT EXISTS (
    SELECT 1
    FROM esquema_migraciones
    WHERE version = '025'
);
