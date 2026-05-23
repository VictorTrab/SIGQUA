INSERT OR IGNORE INTO configuracion_sistema(clave, valor, tipo_dato, categoria, descripcion, editable) VALUES
('ui.laboratorio.fondo_modo', 'DEGRADADO', 'TEXTO', 'Laboratorio visual', 'Modo temporal del fondo de prueba en configuracion.', 1),
('ui.laboratorio.fondo_color_primario', '#0A1728', 'TEXTO', 'Laboratorio visual', 'Color primario temporal del fondo de prueba en configuracion.', 1),
('ui.laboratorio.fondo_color_secundario', '#1D364E', 'TEXTO', 'Laboratorio visual', 'Color secundario temporal del fondo de prueba en configuracion.', 1),
('ui.laboratorio.modal_modo', 'SOLIDO', 'TEXTO', 'Laboratorio visual', 'Modo temporal del modal de prueba en configuracion.', 1),
('ui.laboratorio.modal_color_primario', '#1D364E', 'TEXTO', 'Laboratorio visual', 'Color primario temporal del modal de prueba en configuracion.', 1),
('ui.laboratorio.modal_color_secundario', '#243F5A', 'TEXTO', 'Laboratorio visual', 'Color secundario temporal del modal de prueba en configuracion.', 1);

INSERT INTO esquema_migraciones(version, descripcion, checksum)
SELECT '017', 'configuracion_laboratorio_visual_temporal', NULL
WHERE NOT EXISTS (
    SELECT 1
    FROM esquema_migraciones
    WHERE version = '017'
);
