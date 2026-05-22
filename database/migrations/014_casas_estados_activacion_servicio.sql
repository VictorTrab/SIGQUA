PRAGMA foreign_keys = OFF;

BEGIN TRANSACTION;

DROP TRIGGER IF EXISTS trg_casas_actualizado;
DROP TRIGGER IF EXISTS trg_auditoria_cambio_estado_casa;
DROP TRIGGER IF EXISTS trg_procesos_servicio_actualizado;
DROP VIEW IF EXISTS vw_casas_deuda_5_meses;
DROP VIEW IF EXISTS vw_mora_real_servicios_activos;
DROP VIEW IF EXISTS vw_deuda_total_servicios_activos;
DROP VIEW IF EXISTS vw_abonados_por_estado_servicio;
DROP VIEW IF EXISTS vw_resumen_estado_servicios;
DROP VIEW IF EXISTS vw_resumen_deuda_casas;

CREATE TABLE casas_nueva (
    id INTEGER PRIMARY KEY,
    abonado_id INTEGER NOT NULL,
    barrio_id INTEGER NOT NULL,
    direccion_referencia TEXT,
    estado_servicio TEXT NOT NULL DEFAULT 'ACTIVO' CHECK (estado_servicio IN ('ACTIVO', 'CORTADO', 'INACTIVO')),
    estado_administrativo TEXT NOT NULL DEFAULT 'OPERATIVA' CHECK (estado_administrativo IN ('OPERATIVA', 'SUSPENDIDA')),
    motivo_estado_administrativo TEXT NOT NULL DEFAULT 'NINGUNO' CHECK (
        motivo_estado_administrativo IN (
            'NINGUNO',
            'ABONADO_INACTIVO',
            'REASIGNACION_PENDIENTE',
            'REVISION_ADMINISTRATIVA'
        )
    ),
    ha_tenido_servicio_activo INTEGER NOT NULL DEFAULT 0 CHECK (ha_tenido_servicio_activo IN (0, 1)),
    fecha_alta TEXT NOT NULL DEFAULT (date('now', 'localtime')),
    observaciones TEXT,
    creado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    actualizado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    eliminado_en TEXT,
    FOREIGN KEY (abonado_id) REFERENCES abonados(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (barrio_id) REFERENCES barrios(id) ON UPDATE CASCADE ON DELETE RESTRICT
);

INSERT INTO casas_nueva (
    id,
    abonado_id,
    barrio_id,
    direccion_referencia,
    estado_servicio,
    estado_administrativo,
    motivo_estado_administrativo,
    ha_tenido_servicio_activo,
    fecha_alta,
    observaciones,
    creado_en,
    actualizado_en,
    eliminado_en
)
SELECT
    c.id,
    c.abonado_id,
    c.barrio_id,
    c.direccion_referencia,
    CASE
        WHEN c.estado_servicio = 'SUSPENDIDO' THEN 'ACTIVO'
        ELSE c.estado_servicio
    END,
    CASE
        WHEN c.estado_servicio = 'SUSPENDIDO' THEN 'SUSPENDIDA'
        ELSE 'OPERATIVA'
    END,
    CASE
        WHEN c.estado_servicio = 'SUSPENDIDO' THEN 'REVISION_ADMINISTRATIVA'
        ELSE 'NINGUNO'
    END,
    CASE
        WHEN c.estado_servicio IN ('ACTIVO', 'SUSPENDIDO') THEN 1
        WHEN EXISTS (
            SELECT 1
            FROM pagos p
            WHERE p.casa_id = c.id
              AND COALESCE(p.tipo_pago, 'MENSUALIDAD') IN ('CONEXION', 'RECONEXION')
        ) THEN 1
        WHEN EXISTS (
            SELECT 1
            FROM procesos_servicio ps
            WHERE ps.casa_id = c.id
              AND ps.tipo IN ('CORTE', 'RECONEXION')
        ) THEN 1
        WHEN EXISTS (
            SELECT 1
            FROM cargos cg
            INNER JOIN conceptos_cobro cc ON cc.id = cg.concepto_id
            WHERE cg.casa_id = c.id
              AND cc.codigo = 'SERVICIO_MENSUAL'
        ) THEN 1
        ELSE 0
    END,
    c.fecha_alta,
    c.observaciones,
    c.creado_en,
    c.actualizado_en,
    c.eliminado_en
FROM casas c;

DROP TABLE casas;
ALTER TABLE casas_nueva RENAME TO casas;

CREATE INDEX IF NOT EXISTS idx_casas_abonado_id ON casas(abonado_id);
CREATE INDEX IF NOT EXISTS idx_casas_barrio_id ON casas(barrio_id);
CREATE INDEX IF NOT EXISTS idx_casas_estado_servicio ON casas(estado_servicio);
CREATE INDEX IF NOT EXISTS idx_casas_estado_administrativo ON casas(estado_administrativo);
CREATE INDEX IF NOT EXISTS idx_casas_antecedente_servicio ON casas(ha_tenido_servicio_activo);

CREATE TRIGGER trg_casas_actualizado
AFTER UPDATE ON casas
FOR EACH ROW
WHEN NEW.actualizado_en = OLD.actualizado_en
BEGIN
    UPDATE casas SET actualizado_en = datetime('now', 'localtime') WHERE id = NEW.id;
END;

CREATE TRIGGER trg_auditoria_cambio_estado_casa
AFTER UPDATE OF estado_servicio ON casas
FOR EACH ROW
WHEN OLD.estado_servicio <> NEW.estado_servicio
BEGIN
    INSERT INTO auditoria(
        usuario_id,
        accion,
        entidad,
        entidad_id,
        resumen,
        datos_antes_json,
        datos_despues_json,
        fecha_evento
    )
    VALUES (
        NULL,
        'CAMBIAR_ESTADO_SERVICIO',
        'casas',
        NEW.id,
        'Cambio de estado fisico de casa ' || NEW.id,
        json_object('estado_servicio', OLD.estado_servicio),
        json_object('estado_servicio', NEW.estado_servicio),
        datetime('now', 'localtime')
    );
END;

CREATE TRIGGER trg_auditoria_cambio_estado_administrativo_casa
AFTER UPDATE OF estado_administrativo, motivo_estado_administrativo ON casas
FOR EACH ROW
WHEN OLD.estado_administrativo <> NEW.estado_administrativo
   OR OLD.motivo_estado_administrativo <> NEW.motivo_estado_administrativo
BEGIN
    INSERT INTO auditoria(
        usuario_id,
        accion,
        entidad,
        entidad_id,
        resumen,
        datos_antes_json,
        datos_despues_json,
        fecha_evento
    )
    VALUES (
        NULL,
        'CAMBIAR_ESTADO_ADMINISTRATIVO_CASA',
        'casas',
        NEW.id,
        'Cambio de estado administrativo de casa ' || NEW.id,
        json_object(
            'estado_administrativo', OLD.estado_administrativo,
            'motivo_estado_administrativo', OLD.motivo_estado_administrativo
        ),
        json_object(
            'estado_administrativo', NEW.estado_administrativo,
            'motivo_estado_administrativo', NEW.motivo_estado_administrativo
        ),
        datetime('now', 'localtime')
    );
END;

CREATE VIEW vw_resumen_deuda_casas AS
SELECT
    ca.id AS casa_id,
    ca.abonado_id,
    a.nombre_completo AS abonado_nombre,
    ca.estado_servicio,
    COALESCE(ca.estado_administrativo, 'OPERATIVA') AS estado_administrativo,
    COUNT(c.id) AS total_cargos_pendientes,
    COALESCE(SUM(c.saldo_pendiente_centavos), 0) AS deuda_total_centavos
FROM casas ca
INNER JOIN abonados a ON a.id = ca.abonado_id
LEFT JOIN cargos c
    ON c.casa_id = ca.id
   AND c.estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDO')
   AND c.saldo_pendiente_centavos > 0
GROUP BY ca.id, ca.abonado_id, a.nombre_completo, ca.estado_servicio, COALESCE(ca.estado_administrativo, 'OPERATIVA');

CREATE VIEW vw_resumen_estado_servicios AS
SELECT
    estado_servicio,
    COALESCE(estado_administrativo, 'OPERATIVA') AS estado_administrativo,
    COUNT(*) AS total_casas
FROM casas
GROUP BY estado_servicio, COALESCE(estado_administrativo, 'OPERATIVA');

CREATE VIEW vw_abonados_por_estado_servicio AS
SELECT
    a.id AS abonado_id,
    a.nombre_completo,
    c.id AS casa_id,
    c.estado_servicio,
    COALESCE(c.estado_administrativo, 'OPERATIVA') AS estado_administrativo
FROM abonados a
INNER JOIN casas c ON c.abonado_id = a.id;

CREATE VIEW vw_deuda_total_servicios_activos AS
SELECT
    SUM(saldo_pendiente_centavos) AS deuda_total_centavos
FROM cargos c
INNER JOIN casas ca ON ca.id = c.casa_id
WHERE ca.estado_servicio IN ('ACTIVO', 'CORTADO')
  AND c.estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDO');

CREATE VIEW vw_mora_real_servicios_activos AS
SELECT
    COUNT(*) AS cargos_vencidos,
    COALESCE(SUM(saldo_pendiente_centavos), 0) AS deuda_vencida_centavos
FROM cargos c
INNER JOIN casas ca ON ca.id = c.casa_id
WHERE ca.estado_servicio IN ('ACTIVO', 'CORTADO')
  AND c.estado = 'VENCIDO'
  AND c.saldo_pendiente_centavos > 0;

CREATE VIEW vw_casas_deuda_5_meses AS
SELECT *
FROM vw_resumen_deuda_casas
WHERE deuda_total_centavos > 0;

CREATE TABLE procesos_servicio_nueva (
    id INTEGER PRIMARY KEY,
    abonado_id INTEGER NOT NULL,
    casa_id INTEGER NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('CONEXION', 'CORTE', 'RECONEXION', 'INSPECCION', 'NOTIFICACION')),
    fecha_programada TEXT,
    fecha_ejecucion TEXT,
    fecha_activacion TEXT,
    estado TEXT NOT NULL DEFAULT 'PENDIENTE' CHECK (estado IN ('PENDIENTE', 'EJECUTADO', 'CANCELADO')),
    motivo TEXT,
    observaciones TEXT,
    plan_pago_id INTEGER,
    pago_id INTEGER,
    usuario_id INTEGER,
    cobra_mensualidad_prorrateada INTEGER NOT NULL DEFAULT 0 CHECK (cobra_mensualidad_prorrateada IN (0, 1)),
    precio_mensual_base_centavos INTEGER CHECK (precio_mensual_base_centavos IS NULL OR precio_mensual_base_centavos >= 0),
    dias_mes INTEGER CHECK (dias_mes IS NULL OR dias_mes BETWEEN 28 AND 31),
    dias_cobrados INTEGER CHECK (dias_cobrados IS NULL OR dias_cobrados BETWEEN 0 AND 31),
    monto_prorrateado_centavos INTEGER CHECK (monto_prorrateado_centavos IS NULL OR monto_prorrateado_centavos >= 0),
    monto_conexion_centavos INTEGER CHECK (monto_conexion_centavos IS NULL OR monto_conexion_centavos >= 0),
    monto_reconexion_centavos INTEGER CHECK (monto_reconexion_centavos IS NULL OR monto_reconexion_centavos >= 0),
    multa_corte_centavos INTEGER CHECK (multa_corte_centavos IS NULL OR multa_corte_centavos >= 0),
    creado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    actualizado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (abonado_id) REFERENCES abonados(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (casa_id) REFERENCES casas(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (plan_pago_id) REFERENCES planes_pago(id) ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (pago_id) REFERENCES pagos(id) ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE SET NULL
);

INSERT INTO procesos_servicio_nueva (
    id,
    abonado_id,
    casa_id,
    tipo,
    fecha_programada,
    fecha_ejecucion,
    fecha_activacion,
    estado,
    motivo,
    observaciones,
    plan_pago_id,
    pago_id,
    usuario_id,
    cobra_mensualidad_prorrateada,
    precio_mensual_base_centavos,
    dias_mes,
    dias_cobrados,
    monto_prorrateado_centavos,
    monto_conexion_centavos,
    monto_reconexion_centavos,
    multa_corte_centavos,
    creado_en,
    actualizado_en
)
SELECT
    id,
    abonado_id,
    casa_id,
    tipo,
    fecha_programada,
    fecha_ejecucion,
    NULL,
    estado,
    motivo,
    observaciones,
    plan_pago_id,
    NULL,
    usuario_id,
    0,
    NULL,
    NULL,
    NULL,
    NULL,
    NULL,
    NULL,
    NULL,
    creado_en,
    actualizado_en
FROM procesos_servicio;

DROP TABLE procesos_servicio;
ALTER TABLE procesos_servicio_nueva RENAME TO procesos_servicio;

CREATE INDEX IF NOT EXISTS idx_procesos_servicio_estado ON procesos_servicio(estado);
CREATE INDEX IF NOT EXISTS idx_procesos_servicio_tipo ON procesos_servicio(tipo);
CREATE INDEX IF NOT EXISTS idx_procesos_servicio_pago_id ON procesos_servicio(pago_id);

CREATE TRIGGER trg_procesos_servicio_actualizado
AFTER UPDATE ON procesos_servicio
FOR EACH ROW
WHEN NEW.actualizado_en = OLD.actualizado_en
BEGIN
    UPDATE procesos_servicio SET actualizado_en = datetime('now', 'localtime') WHERE id = NEW.id;
END;

ALTER TABLE cargos ADD COLUMN proceso_servicio_id INTEGER REFERENCES procesos_servicio(id) ON UPDATE CASCADE ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_cargos_proceso_servicio_id ON cargos(proceso_servicio_id);

INSERT OR IGNORE INTO conceptos_cobro(codigo, nombre, tipo, requiere_periodo, monto_global_centavos)
VALUES
('CONEXION', 'Conexion con monto definido en pago', 'OTRO', 0, NULL),
('MENSUALIDAD_PRORRATEADA', 'Mensualidad prorrateada por activacion', 'SERVICIO_MENSUAL', 1, NULL);

INSERT OR IGNORE INTO configuracion_sistema(clave, valor, tipo_dato, categoria, descripcion, editable)
VALUES (
    'cobro.cobrar_mensualidad_prorrateada_activacion',
    '0',
    'BOOLEANO',
    'Cobro',
    'Controla si conexion y reconexion agregan la primera mensualidad prorrateada al momento de activar el servicio.',
    1
);

INSERT INTO esquema_migraciones(version, descripcion, checksum)
SELECT '014', 'casas_estados_activacion_servicio', NULL
WHERE NOT EXISTS (
    SELECT 1
    FROM esquema_migraciones
    WHERE version = '014'
);

COMMIT;

PRAGMA foreign_keys = ON;

