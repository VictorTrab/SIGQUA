PRAGMA foreign_keys = OFF;

BEGIN TRANSACTION;

UPDATE configuracion_sistema
SET valor = 'PDF',
    actualizado_en = datetime('now', 'localtime')
WHERE clave = 'factura.formato_salida'
  AND upper(COALESCE(valor, '')) <> 'PDF';

UPDATE comprobantes
SET formato_salida = 'PDF'
WHERE upper(COALESCE(formato_salida, '')) <> 'PDF';

UPDATE reportes_generados
SET formato = 'PDF'
WHERE upper(COALESCE(formato, '')) <> 'PDF';

CREATE TABLE comprobantes_pdf_021 (
    id INTEGER PRIMARY KEY,
    pago_id INTEGER NOT NULL UNIQUE,
    numero_comprobante TEXT NOT NULL UNIQUE,
    formato_salida TEXT NOT NULL DEFAULT 'PDF' CHECK (formato_salida = 'PDF'),
    ruta_archivo TEXT,
    hash_documento TEXT,
    generado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    generado_por INTEGER,
    tipo_comprobante TEXT NOT NULL DEFAULT 'MENSUALIDAD'
        CHECK (tipo_comprobante IN ('MENSUALIDAD', 'PLAN_PAGO', 'CONEXION', 'RECONEXION')),
    saldo_posterior_centavos INTEGER NOT NULL DEFAULT 0
        CHECK (saldo_posterior_centavos >= 0),
    FOREIGN KEY (pago_id) REFERENCES pagos(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (generado_por) REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE SET NULL
);

INSERT INTO comprobantes_pdf_021(
    id,
    pago_id,
    numero_comprobante,
    formato_salida,
    ruta_archivo,
    hash_documento,
    generado_en,
    generado_por,
    tipo_comprobante,
    saldo_posterior_centavos
)
SELECT
    id,
    pago_id,
    numero_comprobante,
    'PDF',
    ruta_archivo,
    hash_documento,
    generado_en,
    generado_por,
    COALESCE(tipo_comprobante, 'MENSUALIDAD'),
    COALESCE(saldo_posterior_centavos, 0)
FROM comprobantes;

DROP VIEW IF EXISTS vw_reportes_historial_pagos_admin;

DROP TABLE comprobantes;

ALTER TABLE comprobantes_pdf_021 RENAME TO comprobantes;

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

CREATE TABLE reportes_generados_pdf_021 (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    parametros_json TEXT,
    formato TEXT NOT NULL DEFAULT 'PDF' CHECK (formato = 'PDF'),
    ruta_archivo TEXT,
    generado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    generado_por INTEGER,
    FOREIGN KEY (generado_por) REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE SET NULL
);

INSERT INTO reportes_generados_pdf_021(
    id,
    nombre,
    parametros_json,
    formato,
    ruta_archivo,
    generado_en,
    generado_por
)
SELECT
    id,
    nombre,
    parametros_json,
    'PDF',
    ruta_archivo,
    generado_en,
    generado_por
FROM reportes_generados;

DROP TABLE reportes_generados;

ALTER TABLE reportes_generados_pdf_021 RENAME TO reportes_generados;

INSERT INTO esquema_migraciones(version, descripcion, checksum)
SELECT '021', 'comprobantes_solo_pdf', NULL
WHERE NOT EXISTS (
    SELECT 1
    FROM esquema_migraciones
    WHERE version = '021'
);

COMMIT;

PRAGMA foreign_keys = ON;
