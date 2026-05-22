PRAGMA foreign_keys = OFF;

BEGIN TRANSACTION;

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
        'Cambio de estado de servicio de casa ' || NEW.id,
        json_object('estado_servicio', OLD.estado_servicio),
        json_object('estado_servicio', NEW.estado_servicio),
        datetime('now', 'localtime')
    );
END;

INSERT INTO esquema_migraciones(version, descripcion, checksum)
VALUES (
    '005',
    'Repara triggers de auditoria que quedaron apuntando a tablas legacy tras la migracion 003',
    NULL
);

COMMIT;

PRAGMA foreign_keys = ON;

