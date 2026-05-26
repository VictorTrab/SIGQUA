PRAGMA foreign_keys = OFF;

BEGIN TRANSACTION;

DROP VIEW IF EXISTS vw_reportes_historial_pagos_admin;

CREATE TABLE comprobantes_escpos_023 (
    id INTEGER PRIMARY KEY,
    pago_id INTEGER NOT NULL UNIQUE,
    numero_comprobante TEXT NOT NULL UNIQUE,
    generado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    generado_por INTEGER,
    tipo_comprobante TEXT NOT NULL DEFAULT 'MENSUALIDAD'
        CHECK (tipo_comprobante IN ('MENSUALIDAD', 'PLAN_PAGO', 'CONEXION', 'RECONEXION')),
    saldo_posterior_centavos INTEGER NOT NULL DEFAULT 0
        CHECK (saldo_posterior_centavos >= 0),
    FOREIGN KEY (pago_id) REFERENCES pagos(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (generado_por) REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE SET NULL
);

INSERT INTO comprobantes_escpos_023(
    id,
    pago_id,
    numero_comprobante,
    generado_en,
    generado_por,
    tipo_comprobante,
    saldo_posterior_centavos
)
SELECT
    id,
    pago_id,
    numero_comprobante,
    generado_en,
    generado_por,
    COALESCE(tipo_comprobante, 'MENSUALIDAD'),
    COALESCE(saldo_posterior_centavos, 0)
FROM comprobantes;

DROP TABLE comprobantes;

ALTER TABLE comprobantes_escpos_023 RENAME TO comprobantes;

CREATE TABLE IF NOT EXISTS comprobantes_impresiones (
    id INTEGER PRIMARY KEY,
    comprobante_id INTEGER NOT NULL,
    tipo_copia TEXT NOT NULL CHECK (tipo_copia IN ('ORIGINAL', 'JUNTA', 'AMBAS')),
    es_reimpresion INTEGER NOT NULL DEFAULT 0 CHECK (es_reimpresion IN (0, 1)),
    estado TEXT NOT NULL CHECK (estado IN ('IMPRESO', 'FALLIDO')),
    mensaje_error TEXT NOT NULL DEFAULT '',
    impreso_por INTEGER,
    impreso_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (comprobante_id) REFERENCES comprobantes(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (impreso_por) REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_comprobantes_impresiones_comprobante
ON comprobantes_impresiones(comprobante_id, estado, tipo_copia, es_reimpresion);

DELETE FROM configuracion_sistema
WHERE clave IN (
    'factura.formato_salida',
    'documentos.abrir_pdf_automaticamente',
    'documentos.imprimir_pdf_automaticamente'
);

INSERT INTO configuracion_sistema (clave, valor, tipo_dato, categoria, descripcion, editable)
VALUES
('impresion_termica.nombre_impresora', '', 'TEXTO', 'Comprobantes', 'Nombre de la impresora termica instalada en Windows.', 1),
('impresion_termica.ancho_papel_mm', '80', 'ENTERO', 'Comprobantes', 'Ancho del papel termico en milimetros.', 1),
('impresion_termica.corte_automatico', '1', 'BOOLEANO', 'Comprobantes', 'Corta el papel al finalizar cada comprobante.', 1),
('impresion_termica.codigo_pagina', 'cp850', 'TEXTO', 'Comprobantes', 'Codigo de pagina usado para texto ESC/POS.', 1),
('impresion_reportes.nombre_impresora', '', 'TEXTO', 'Reportes', 'Nombre de la impresora predeterminada para reportes PDF en carta.', 1)
ON CONFLICT(clave) DO NOTHING;

CREATE VIEW vw_reportes_historial_pagos_admin AS
SELECT
    p.id AS pago_id,
    COALESCE(co.numero_comprobante, 'Sin comprobante') AS numero_comprobante,
    COALESCE(p.tipo_pago, 'MENSUALIDAD') AS tipo_pago,
    COALESCE(p.operacion_cobro_id, 0) AS operacion_cobro_id,
    printf('CA-%03d', p.casa_id) AS casa_codigo,
    p.casa_id,
    p.abonado_id,
    a.nombre_completo AS abonado_nombre,
    a.estado AS estado_abonado,
    COALESCE(b.nombre, '') AS barrio_nombre,
    COALESCE(mp.nombre, 'Sin metodo') AS metodo_pago,
    COALESCE(u.nombre_completo, u.nombre_usuario, '') AS usuario_registro,
    date(p.fecha_pago) AS fecha_pago,
    p.total_pagado_centavos
FROM pagos p
LEFT JOIN comprobantes co ON co.pago_id = p.id
INNER JOIN abonados a ON a.id = p.abonado_id
INNER JOIN casas c ON c.id = p.casa_id
LEFT JOIN barrios b ON b.id = c.barrio_id
LEFT JOIN metodos_pago mp ON mp.id = p.metodo_pago_id
LEFT JOIN usuarios u ON u.id = p.usuario_cobrador_id
WHERE p.estado = 'CONFIRMADO';

INSERT INTO esquema_migraciones(version, descripcion, checksum)
SELECT '023', 'separar_comprobantes_escpos_reportes_pdf', NULL
WHERE NOT EXISTS (
    SELECT 1
    FROM esquema_migraciones
    WHERE version = '023'
);

COMMIT;

PRAGMA foreign_keys = ON;
