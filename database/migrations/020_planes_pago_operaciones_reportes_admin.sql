-- 020. Planes de pago integrados con activacion y reportes administrativos

ALTER TABLE planes_pago ADD COLUMN deuda_financiada_centavos INTEGER NOT NULL DEFAULT 0;
ALTER TABLE planes_pago ADD COLUMN monto_activacion_centavos INTEGER NOT NULL DEFAULT 0;
ALTER TABLE planes_pago ADD COLUMN fecha_corte_deuda TEXT;
ALTER TABLE planes_pago ADD COLUMN tipo_activacion_origen TEXT NOT NULL DEFAULT 'RECONEXION'
    CHECK (tipo_activacion_origen IN ('CONEXION', 'RECONEXION'));

ALTER TABLE pagos ADD COLUMN operacion_cobro_id INTEGER;

CREATE TABLE IF NOT EXISTS operaciones_cobro (
    id INTEGER PRIMARY KEY,
    abonado_id INTEGER NOT NULL,
    casa_id INTEGER NOT NULL,
    tipo_operacion TEXT NOT NULL CHECK (tipo_operacion IN ('RECONEXION_COMPUESTA', 'PLAN_ACTIVACION')),
    estado TEXT NOT NULL DEFAULT 'CONFIRMADA' CHECK (estado IN ('PENDIENTE', 'CONFIRMADA', 'CANCELADA')),
    descripcion TEXT,
    creado_por INTEGER,
    creado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    actualizado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (abonado_id) REFERENCES abonados(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (casa_id) REFERENCES casas(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (creado_por) REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_operaciones_cobro_tipo ON operaciones_cobro(tipo_operacion);
CREATE INDEX IF NOT EXISTS idx_operaciones_cobro_casa ON operaciones_cobro(casa_id);
CREATE INDEX IF NOT EXISTS idx_pagos_operacion_cobro_id ON pagos(operacion_cobro_id);

DROP VIEW IF EXISTS vw_reportes_deuda_abonado_estado;
CREATE VIEW vw_reportes_deuda_abonado_estado AS
SELECT
    a.id AS abonado_id,
    a.estado AS estado_abonado,
    c.id AS casa_id,
    printf('CA-%03d', c.id) AS casa_codigo,
    a.nombre_completo AS abonado_nombre,
    a.dni AS abonado_dni,
    COALESCE(b.nombre, '') AS barrio_nombre,
    c.estado_servicio,
    COALESCE(c.estado_administrativo, 'OPERATIVA') AS estado_administrativo,
    COALESCE(
        SUM(
            CASE
                WHEN cg.estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDO')
                 AND cg.saldo_pendiente_centavos > 0
                 AND cg.anulado_en IS NULL
                 AND NOT EXISTS (
                    SELECT 1
                    FROM planes_pago_cargos ppc
                    INNER JOIN planes_pago pp ON pp.id = ppc.plan_pago_id
                    WHERE ppc.cargo_id = cg.id
                      AND pp.estado = 'ACTIVO'
                 )
                 AND cc.tipo <> 'MORA'
                THEN cg.saldo_pendiente_centavos
                ELSE 0
            END
        ),
        0
    ) AS deuda_base_centavos,
    COALESCE(
        SUM(
            CASE
                WHEN cg.estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDO')
                 AND cg.saldo_pendiente_centavos > 0
                 AND cg.anulado_en IS NULL
                 AND NOT EXISTS (
                    SELECT 1
                    FROM planes_pago_cargos ppc
                    INNER JOIN planes_pago pp ON pp.id = ppc.plan_pago_id
                    WHERE ppc.cargo_id = cg.id
                      AND pp.estado = 'ACTIVO'
                 )
                 AND (cc.tipo = 'MORA' OR cc.codigo = 'MORA')
                THEN cg.saldo_pendiente_centavos
                ELSE 0
            END
        ),
        0
    ) AS mora_centavos,
    COALESCE((
        SELECT SUM(cpp.saldo_pendiente_centavos)
        FROM planes_pago pp
        INNER JOIN cuotas_plan_pago cpp ON cpp.plan_pago_id = pp.id
        WHERE pp.casa_id = c.id
          AND pp.estado = 'ACTIVO'
          AND cpp.estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDO')
          AND cpp.saldo_pendiente_centavos > 0
    ), 0) AS saldo_plan_centavos
FROM casas c
INNER JOIN abonados a ON a.id = c.abonado_id
LEFT JOIN barrios b ON b.id = c.barrio_id
LEFT JOIN cargos cg ON cg.casa_id = c.id
LEFT JOIN conceptos_cobro cc ON cc.id = cg.concepto_id
WHERE c.eliminado_en IS NULL
GROUP BY a.id, a.estado, c.id, b.nombre, c.estado_servicio, c.estado_administrativo;

DROP VIEW IF EXISTS vw_reportes_servicio_casas;
CREATE VIEW vw_reportes_servicio_casas AS
SELECT
    c.id AS casa_id,
    printf('CA-%03d', c.id) AS casa_codigo,
    a.nombre_completo AS abonado_nombre,
    a.estado AS estado_abonado,
    COALESCE(b.nombre, '') AS barrio_nombre,
    c.estado_servicio,
    COALESCE(c.estado_administrativo, 'OPERATIVA') AS estado_administrativo,
    CASE
        WHEN c.estado_servicio = 'ACTIVO' THEN 1
        ELSE 0
    END AS tiene_servicio
FROM casas c
INNER JOIN abonados a ON a.id = c.abonado_id
LEFT JOIN barrios b ON b.id = c.barrio_id
WHERE c.eliminado_en IS NULL;

DROP VIEW IF EXISTS vw_reportes_planes_pago_activos_admin;
CREATE VIEW vw_reportes_planes_pago_activos_admin AS
SELECT
    pp.id AS plan_pago_id,
    printf('PP-%03d', pp.id) AS plan_codigo,
    pp.casa_id,
    printf('CA-%03d', pp.casa_id) AS casa_codigo,
    pp.abonado_id,
    a.nombre_completo AS abonado_nombre,
    a.estado AS estado_abonado,
    COALESCE(b.nombre, '') AS barrio_nombre,
    pp.tipo_plan,
    pp.tipo_activacion_origen,
    pp.fecha_corte_deuda,
    COALESCE(pp.deuda_financiada_centavos, 0) AS deuda_financiada_centavos,
    COALESCE(pp.monto_activacion_centavos, 0) AS monto_activacion_centavos,
    COALESCE(pp.prima_centavos, 0) AS prima_centavos,
    pp.monto_total_centavos,
    pp.cuota_regular_centavos,
    pp.cantidad_cuotas,
    pp.estado,
    COALESCE((
        SELECT COUNT(*)
        FROM cuotas_plan_pago cpp
        WHERE cpp.plan_pago_id = pp.id
          AND cpp.estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDO')
          AND cpp.saldo_pendiente_centavos > 0
    ), 0) AS cuotas_pendientes,
    COALESCE((
        SELECT SUM(cpp.saldo_pendiente_centavos)
        FROM cuotas_plan_pago cpp
        WHERE cpp.plan_pago_id = pp.id
          AND cpp.estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDO')
          AND cpp.saldo_pendiente_centavos > 0
    ), 0) AS saldo_vivo_centavos
FROM planes_pago pp
INNER JOIN abonados a ON a.id = pp.abonado_id
INNER JOIN casas c ON c.id = pp.casa_id
LEFT JOIN barrios b ON b.id = c.barrio_id;

DROP VIEW IF EXISTS vw_reportes_historial_pagos_admin;
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
SELECT '020', 'planes_pago_operaciones_reportes_admin', NULL
WHERE NOT EXISTS (
    SELECT 1
    FROM esquema_migraciones
    WHERE version = '020'
);
