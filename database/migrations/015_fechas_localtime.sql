PRAGMA foreign_keys = OFF;

BEGIN TRANSACTION;

DROP VIEW IF EXISTS vw_cuotas_vencidas;
CREATE VIEW vw_cuotas_vencidas AS
SELECT
    cpp.id,
    cpp.plan_pago_id,
    cpp.numero_cuota,
    cpp.fecha_vencimiento,
    cpp.monto_centavos,
    cpp.saldo_pendiente_centavos,
    cpp.estado
FROM cuotas_plan_pago cpp
WHERE cpp.estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDO')
  AND cpp.fecha_vencimiento < date('now', 'localtime');

DROP TRIGGER IF EXISTS trg_usuarios_actualizado;
CREATE TRIGGER trg_usuarios_actualizado
AFTER UPDATE ON usuarios
FOR EACH ROW
WHEN NEW.actualizado_en = OLD.actualizado_en
BEGIN
    UPDATE usuarios SET actualizado_en = datetime('now', 'localtime') WHERE id = NEW.id;
END;

DROP TRIGGER IF EXISTS trg_barrios_actualizado;
CREATE TRIGGER trg_barrios_actualizado
AFTER UPDATE ON barrios
FOR EACH ROW
WHEN NEW.actualizado_en = OLD.actualizado_en
BEGIN
    UPDATE barrios SET actualizado_en = datetime('now', 'localtime') WHERE id = NEW.id;
END;

DROP TRIGGER IF EXISTS trg_abonados_actualizado;
CREATE TRIGGER trg_abonados_actualizado
AFTER UPDATE ON abonados
FOR EACH ROW
WHEN NEW.actualizado_en = OLD.actualizado_en
BEGIN
    UPDATE abonados SET actualizado_en = datetime('now', 'localtime') WHERE id = NEW.id;
END;

DROP TRIGGER IF EXISTS trg_casas_actualizado;
CREATE TRIGGER trg_casas_actualizado
AFTER UPDATE ON casas
FOR EACH ROW
WHEN NEW.actualizado_en = OLD.actualizado_en
BEGIN
    UPDATE casas SET actualizado_en = datetime('now', 'localtime') WHERE id = NEW.id;
END;

DROP TRIGGER IF EXISTS trg_cargos_actualizado;
CREATE TRIGGER trg_cargos_actualizado
AFTER UPDATE ON cargos
FOR EACH ROW
WHEN NEW.actualizado_en = OLD.actualizado_en
BEGIN
    UPDATE cargos SET actualizado_en = datetime('now', 'localtime') WHERE id = NEW.id;
END;

DROP TRIGGER IF EXISTS trg_pagos_actualizado;
CREATE TRIGGER trg_pagos_actualizado
AFTER UPDATE ON pagos
FOR EACH ROW
WHEN NEW.actualizado_en = OLD.actualizado_en
BEGIN
    UPDATE pagos SET actualizado_en = datetime('now', 'localtime') WHERE id = NEW.id;
END;

DROP TRIGGER IF EXISTS trg_planes_pago_actualizado;
CREATE TRIGGER trg_planes_pago_actualizado
AFTER UPDATE ON planes_pago
FOR EACH ROW
WHEN NEW.actualizado_en = OLD.actualizado_en
BEGIN
    UPDATE planes_pago SET actualizado_en = datetime('now', 'localtime') WHERE id = NEW.id;
END;

DROP TRIGGER IF EXISTS trg_cuotas_plan_pago_actualizado;
CREATE TRIGGER trg_cuotas_plan_pago_actualizado
AFTER UPDATE ON cuotas_plan_pago
FOR EACH ROW
WHEN NEW.actualizado_en = OLD.actualizado_en
BEGIN
    UPDATE cuotas_plan_pago SET actualizado_en = datetime('now', 'localtime') WHERE id = NEW.id;
END;

DROP TRIGGER IF EXISTS trg_procesos_servicio_actualizado;
CREATE TRIGGER trg_procesos_servicio_actualizado
AFTER UPDATE ON procesos_servicio
FOR EACH ROW
WHEN NEW.actualizado_en = OLD.actualizado_en
BEGIN
    UPDATE procesos_servicio SET actualizado_en = datetime('now', 'localtime') WHERE id = NEW.id;
END;

DROP TRIGGER IF EXISTS trg_auditoria_pago_anulado;
CREATE TRIGGER trg_auditoria_pago_anulado
AFTER UPDATE OF estado ON pagos
FOR EACH ROW
WHEN OLD.estado <> NEW.estado AND NEW.estado = 'ANULADO'
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
        NEW.anulado_por,
        'ANULAR_PAGO',
        'pagos',
        NEW.id,
        'Pago anulado: REC-' || printf('%06d', NEW.id),
        json_object('estado', OLD.estado, 'total_pagado_centavos', OLD.total_pagado_centavos),
        json_object('estado', NEW.estado, 'motivo_anulacion', NEW.motivo_anulacion),
        datetime('now', 'localtime')
    );
END;

DROP TRIGGER IF EXISTS trg_auditoria_cambio_estado_casa;
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

DROP TRIGGER IF EXISTS trg_auditoria_cambio_estado_administrativo_casa;
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

DROP TRIGGER IF EXISTS trg_auditoria_restablecimiento_contrasena;
CREATE TRIGGER trg_auditoria_restablecimiento_contrasena
AFTER UPDATE OF contrasena_hash ON usuarios
FOR EACH ROW
WHEN NEW.contrasena_hash <> OLD.contrasena_hash
  AND NEW.restablecida_por_usuario_id IS NOT NULL
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
        NEW.restablecida_por_usuario_id,
        'RESTABLECER_CONTRASENA',
        'usuarios',
        NEW.id,
        'Restablecimiento de contrasena del usuario ' || NEW.nombre_usuario,
        json_object(
            'requiere_cambio_contrasena', OLD.requiere_cambio_contrasena,
            'estado', OLD.estado
        ),
        json_object(
            'requiere_cambio_contrasena', NEW.requiere_cambio_contrasena,
            'estado', NEW.estado,
            'fecha_restablecimiento_contrasena', NEW.fecha_restablecimiento_contrasena
        ),
        datetime('now', 'localtime')
    );
END;

INSERT INTO esquema_migraciones(version, descripcion, checksum)
VALUES (
    '015',
    'Actualiza triggers y vistas dependientes de fecha para usar hora local del equipo',
    NULL
);

COMMIT;

PRAGMA foreign_keys = ON;
