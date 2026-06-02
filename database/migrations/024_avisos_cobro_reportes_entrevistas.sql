ALTER TABLE casas ADD COLUMN estado_aviso_cobro TEXT NOT NULL DEFAULT 'SIN_AVISO'
    CHECK (estado_aviso_cobro IN (
        'SIN_AVISO',
        'PRIMER_AVISO',
        'SEGUNDO_AVISO',
        'TERCER_AVISO',
        'LISTO_PARA_CORTE',
        'CORTADO'
    ));

ALTER TABLE casas ADD COLUMN fecha_ultimo_aviso TEXT;
ALTER TABLE casas ADD COLUMN usuario_ultimo_aviso_id INTEGER;
ALTER TABLE casas ADD COLUMN observacion_ultimo_aviso TEXT NOT NULL DEFAULT '';

ALTER TABLE historial_propietarios_casa ADD COLUMN observacion TEXT NOT NULL DEFAULT '';

UPDATE casas
SET estado_aviso_cobro = 'CORTADO',
    fecha_ultimo_aviso = COALESCE(fecha_ultimo_aviso, actualizado_en)
WHERE estado_servicio = 'CORTADO';

CREATE INDEX IF NOT EXISTS idx_casas_estado_aviso_cobro
ON casas(estado_aviso_cobro);

CREATE INDEX IF NOT EXISTS idx_casas_fecha_ultimo_aviso
ON casas(fecha_ultimo_aviso);

CREATE INDEX IF NOT EXISTS idx_casas_usuario_ultimo_aviso
ON casas(usuario_ultimo_aviso_id);

DROP VIEW IF EXISTS vw_reportes_deuda_mensual;
CREATE VIEW vw_reportes_deuda_mensual AS
SELECT
    COALESCE(pc.anio, CAST(strftime('%Y', c.fecha_vencimiento) AS INTEGER)) AS anio,
    COALESCE(pc.mes, CAST(strftime('%m', c.fecha_vencimiento) AS INTEGER)) AS mes,
    printf('%04d-%02d',
        COALESCE(pc.anio, CAST(strftime('%Y', c.fecha_vencimiento) AS INTEGER)),
        COALESCE(pc.mes, CAST(strftime('%m', c.fecha_vencimiento) AS INTEGER))
    ) AS periodo,
    COUNT(DISTINCT c.casa_id) AS total_casas,
    COUNT(DISTINCT ca.abonado_id) AS total_abonados,
    COALESCE(SUM(c.saldo_pendiente_centavos), 0) AS deuda_total_centavos
FROM cargos c
INNER JOIN casas ca ON ca.id = c.casa_id
LEFT JOIN periodos_cobro pc ON pc.id = c.periodo_id
WHERE c.anulado_en IS NULL
  AND c.estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDO')
  AND c.saldo_pendiente_centavos > 0
GROUP BY anio, mes;

DROP VIEW IF EXISTS vw_reportes_nuevos_abonados;
CREATE VIEW vw_reportes_nuevos_abonados AS
SELECT
    a.id AS abonado_id,
    a.nombre_completo AS abonado_nombre,
    a.dni AS abonado_dni,
    COALESCE(b.nombre, '') AS barrio_nombre,
    a.estado AS estado_abonado,
    date(a.creado_en) AS fecha_registro
FROM abonados a
LEFT JOIN barrios b ON b.id = a.barrio_id
WHERE a.eliminado_en IS NULL;

DROP VIEW IF EXISTS vw_reportes_pagos_usuario;
CREATE VIEW vw_reportes_pagos_usuario AS
SELECT
    p.id AS pago_id,
    COALESCE(u.nombre_completo, u.nombre_usuario, 'Sin usuario') AS usuario_cobrador,
    COALESCE(u.nombre_usuario, '') AS nombre_usuario,
    COALESCE(p.tipo_pago, 'MENSUALIDAD') AS tipo_pago,
    COALESCE(co.numero_comprobante, 'Sin comprobante') AS numero_comprobante,
    printf('CA-%03d', p.casa_id) AS casa_codigo,
    a.nombre_completo AS abonado_nombre,
    COALESCE(mp.nombre, 'Sin metodo') AS metodo_pago,
    date(p.fecha_pago) AS fecha_pago,
    p.total_pagado_centavos
FROM pagos p
LEFT JOIN usuarios u ON u.id = p.usuario_cobrador_id
LEFT JOIN comprobantes co ON co.pago_id = p.id
INNER JOIN abonados a ON a.id = p.abonado_id
LEFT JOIN metodos_pago mp ON mp.id = p.metodo_pago_id
WHERE p.estado = 'CONFIRMADO';

INSERT INTO esquema_migraciones(version, descripcion, checksum)
SELECT '024', 'avisos_cobro_reportes_entrevistas', NULL
WHERE NOT EXISTS (
    SELECT 1
    FROM esquema_migraciones
    WHERE version = '024'
);
