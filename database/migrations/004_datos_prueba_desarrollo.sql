BEGIN;

-- ============================================================
-- 1. Regla de semilla
-- ============================================================
-- Todos los registros insertados por esta migracion son ficticios
-- y existen unicamente para pruebas locales de desarrollo.

-- ============================================================
-- 2. Usuarios operativos de prueba
-- ============================================================

INSERT OR IGNORE INTO usuarios(
    nombre_usuario,
    nombre_completo,
    correo,
    contrasena_hash,
    estado,
    es_tecnico,
    es_oculto,
    requiere_cambio_contrasena,
    observaciones,
    creado_por,
    actualizado_por
)
VALUES
(
    'cajero_demo',
    'Cajero de Prueba',
    'cajero.demo@sicap.local',
    'scrypt$c081b3c0b1cabcfd1e173ac2293394ee$d3c88ce38c9accabda7c2beeef20c9cb0be9bf8a1014f702cc83d90c83fb8d7e8904a200712554282f89cdc1f6adc9fb2b3544f3732c7fabea9b6357a051a94d',
    'ACTIVO',
    0,
    0,
    0,
    '[PRUEBA] Usuario operativo de desarrollo local.',
    (SELECT id FROM usuarios WHERE lower(nombre_usuario) = 'admin'),
    (SELECT id FROM usuarios WHERE lower(nombre_usuario) = 'admin')
),
(
    'consulta_demo',
    'Consulta de Prueba',
    'consulta.demo@sicap.local',
    'scrypt$c081b3c0b1cabcfd1e173ac2293394ee$d3c88ce38c9accabda7c2beeef20c9cb0be9bf8a1014f702cc83d90c83fb8d7e8904a200712554282f89cdc1f6adc9fb2b3544f3732c7fabea9b6357a051a94d',
    'ACTIVO',
    0,
    0,
    0,
    '[PRUEBA] Usuario de solo consulta para desarrollo local.',
    (SELECT id FROM usuarios WHERE lower(nombre_usuario) = 'admin'),
    (SELECT id FROM usuarios WHERE lower(nombre_usuario) = 'admin')
);

INSERT OR IGNORE INTO usuarios_roles(usuario_id, rol_id)
SELECT u.id, r.id
FROM usuarios u, roles r
WHERE lower(u.nombre_usuario) = 'cajero_demo'
  AND r.nombre = 'CAJERO';

INSERT OR IGNORE INTO usuarios_roles(usuario_id, rol_id)
SELECT u.id, r.id
FROM usuarios u, roles r
WHERE lower(u.nombre_usuario) = 'consulta_demo'
  AND r.nombre = 'CONSULTA';

-- ============================================================
-- 3. Catalogos base de prueba
-- ============================================================

INSERT OR IGNORE INTO barrios(nombre, estado, observaciones)
VALUES
('Centro', 'ACTIVO', '[PRUEBA] Barrio de prueba para desarrollo local.'),
('San Jorge', 'ACTIVO', '[PRUEBA] Barrio de prueba para desarrollo local.'),
('Las Flores', 'ACTIVO', '[PRUEBA] Barrio de prueba para desarrollo local.');

UPDATE configuracion_sistema
SET valor = '35000',
    actualizado_en = datetime('now', 'localtime')
WHERE clave = 'cobro.precio_mensual_centavos'
  AND valor = '0';

-- ============================================================
-- 4. Abonados y casas de prueba
-- ============================================================

INSERT OR IGNORE INTO abonados(
    dni,
    nombre_completo,
    telefono,
    barrio_id,
    direccion_referencia,
    observaciones,
    estado
)
VALUES
(
    '0801199000011',
    'Ana Martinez',
    '9999-1001',
    (SELECT id FROM barrios WHERE nombre = 'Centro'),
    'Frente al parque central',
    '[PRUEBA] Abonado de prueba para desarrollo local.',
    'ACTIVO'
),
(
    '0801199000022',
    'Carlos Ramirez',
    '9999-1002',
    (SELECT id FROM barrios WHERE nombre = 'San Jorge'),
    'Dos cuadras al sur de la escuela',
    '[PRUEBA] Abonado de prueba para desarrollo local.',
    'ACTIVO'
),
(
    '0801199000033',
    'Diana Flores',
    '9999-1003',
    (SELECT id FROM barrios WHERE nombre = 'Las Flores'),
    'Contiguo a la cancha comunal',
    '[PRUEBA] Abonado de prueba para desarrollo local.',
    'ACTIVO'
),
(
    '0801199000044',
    'Ernesto Lopez',
    '9999-1004',
    (SELECT id FROM barrios WHERE nombre = 'Centro'),
    'Barrio abajo, casa esquinera',
    '[PRUEBA] Abonado de prueba para desarrollo local.',
    'ACTIVO'
);

INSERT INTO casas(
    abonado_id,
    barrio_id,
    direccion_referencia,
    estado_servicio,
    observaciones
)
SELECT
    (SELECT id FROM abonados WHERE dni = '0801199000011'),
    (SELECT id FROM barrios WHERE nombre = 'Centro'),
    'Casa 01, avenida principal',
    'ACTIVO',
    '[PRUEBA] Casa de prueba para desarrollo local.'
WHERE NOT EXISTS (
    SELECT 1
    FROM casas
    WHERE abonado_id = (SELECT id FROM abonados WHERE dni = '0801199000011')
      AND direccion_referencia = 'Casa 01, avenida principal'
);

INSERT INTO casas(
    abonado_id,
    barrio_id,
    direccion_referencia,
    estado_servicio,
    observaciones
)
SELECT
    (SELECT id FROM abonados WHERE dni = '0801199000022'),
    (SELECT id FROM barrios WHERE nombre = 'San Jorge'),
    'Casa 02, sector escuela',
    'ACTIVO',
    '[PRUEBA] Casa de prueba para desarrollo local.'
WHERE NOT EXISTS (
    SELECT 1
    FROM casas
    WHERE abonado_id = (SELECT id FROM abonados WHERE dni = '0801199000022')
      AND direccion_referencia = 'Casa 02, sector escuela'
);

INSERT INTO casas(
    abonado_id,
    barrio_id,
    direccion_referencia,
    estado_servicio,
    observaciones
)
SELECT
    (SELECT id FROM abonados WHERE dni = '0801199000033'),
    (SELECT id FROM barrios WHERE nombre = 'Las Flores'),
    'Casa 03, pasaje las flores',
    'SUSPENDIDO',
    '[PRUEBA] Casa de prueba para desarrollo local.'
WHERE NOT EXISTS (
    SELECT 1
    FROM casas
    WHERE abonado_id = (SELECT id FROM abonados WHERE dni = '0801199000033')
      AND direccion_referencia = 'Casa 03, pasaje las flores'
);

INSERT INTO casas(
    abonado_id,
    barrio_id,
    direccion_referencia,
    estado_servicio,
    observaciones
)
SELECT
    (SELECT id FROM abonados WHERE dni = '0801199000044'),
    (SELECT id FROM barrios WHERE nombre = 'Centro'),
    'Casa 04, calle del tanque',
    'ACTIVO',
    '[PRUEBA] Casa de prueba para desarrollo local.'
WHERE NOT EXISTS (
    SELECT 1
    FROM casas
    WHERE abonado_id = (SELECT id FROM abonados WHERE dni = '0801199000044')
      AND direccion_referencia = 'Casa 04, calle del tanque'
);

-- ============================================================
-- 5. Periodos de cobro de prueba
-- ============================================================

INSERT OR IGNORE INTO periodos_cobro(
    anio,
    mes,
    nombre,
    fecha_inicio,
    fecha_fin,
    fecha_vencimiento,
    estado
)
SELECT
    CAST(strftime('%Y', date('now', 'localtime', '-2 month')) AS INTEGER),
    CAST(strftime('%m', date('now', 'localtime', '-2 month')) AS INTEGER),
    'Periodo de prueba ' || strftime('%m/%Y', date('now', 'localtime', '-2 month')),
    date(date('now', 'localtime', '-2 month'), 'start of month'),
    date(date('now', 'localtime', '-2 month'), 'start of month', '+1 month', '-1 day'),
    date(date('now', 'localtime', '-2 month'), 'start of month', '+1 month', '+9 day'),
    'CERRADO';

INSERT OR IGNORE INTO periodos_cobro(
    anio,
    mes,
    nombre,
    fecha_inicio,
    fecha_fin,
    fecha_vencimiento,
    estado
)
SELECT
    CAST(strftime('%Y', date('now', 'localtime', '-1 month')) AS INTEGER),
    CAST(strftime('%m', date('now', 'localtime', '-1 month')) AS INTEGER),
    'Periodo de prueba ' || strftime('%m/%Y', date('now', 'localtime', '-1 month')),
    date(date('now', 'localtime', '-1 month'), 'start of month'),
    date(date('now', 'localtime', '-1 month'), 'start of month', '+1 month', '-1 day'),
    date(date('now', 'localtime', '-1 month'), 'start of month', '+1 month', '+9 day'),
    'CERRADO';

INSERT OR IGNORE INTO periodos_cobro(
    anio,
    mes,
    nombre,
    fecha_inicio,
    fecha_fin,
    fecha_vencimiento,
    estado
)
SELECT
    CAST(strftime('%Y', date('now', 'localtime')) AS INTEGER),
    CAST(strftime('%m', date('now', 'localtime')) AS INTEGER),
    'Periodo de prueba ' || strftime('%m/%Y', date('now', 'localtime')),
    date('now', 'localtime', 'start of month'),
    date('now', 'localtime', 'start of month', '+1 month', '-1 day'),
    date('now', 'localtime', 'start of month', '+1 month', '+9 day'),
    'ABIERTO';

-- ============================================================
-- 6. Cargos de prueba para dashboard y flujos locales
-- ============================================================

INSERT OR IGNORE INTO cargos(
    casa_id,
    abonado_id,
    periodo_id,
    concepto_id,
    descripcion,
    monto_centavos,
    saldo_pendiente_centavos,
    fecha_generacion,
    fecha_vencimiento,
    estado,
    origen
)
SELECT
    c.id,
    a.id,
    p.id,
    cc.id,
    '[PRUEBA] Servicio mensual cancelado',
    35000,
    0,
    p.fecha_inicio,
    p.fecha_vencimiento,
    'PAGADO',
    'MENSUAL'
FROM casas c
JOIN abonados a ON a.id = c.abonado_id
JOIN conceptos_cobro cc ON cc.codigo = 'SERVICIO_MENSUAL'
JOIN periodos_cobro p
    ON p.anio = CAST(strftime('%Y', date('now', 'localtime')) AS INTEGER)
   AND p.mes = CAST(strftime('%m', date('now', 'localtime')) AS INTEGER)
WHERE a.dni = '0801199000011';

INSERT OR IGNORE INTO cargos(
    casa_id,
    abonado_id,
    periodo_id,
    concepto_id,
    descripcion,
    monto_centavos,
    saldo_pendiente_centavos,
    fecha_generacion,
    fecha_vencimiento,
    estado,
    origen
)
SELECT
    c.id,
    a.id,
    p.id,
    cc.id,
    '[PRUEBA] Servicio mensual vencido',
    35000,
    35000,
    p.fecha_inicio,
    p.fecha_vencimiento,
    'VENCIDO',
    'MENSUAL'
FROM casas c
JOIN abonados a ON a.id = c.abonado_id
JOIN conceptos_cobro cc ON cc.codigo = 'SERVICIO_MENSUAL'
JOIN periodos_cobro p
    ON p.anio = CAST(strftime('%Y', date('now', 'localtime', '-1 month')) AS INTEGER)
   AND p.mes = CAST(strftime('%m', date('now', 'localtime', '-1 month')) AS INTEGER)
WHERE a.dni = '0801199000022';

INSERT OR IGNORE INTO cargos(
    casa_id,
    abonado_id,
    periodo_id,
    concepto_id,
    descripcion,
    monto_centavos,
    saldo_pendiente_centavos,
    fecha_generacion,
    fecha_vencimiento,
    estado,
    origen
)
SELECT
    c.id,
    a.id,
    p.id,
    cc.id,
    '[PRUEBA] Servicio mensual pendiente',
    35000,
    35000,
    p.fecha_inicio,
    p.fecha_vencimiento,
    'PENDIENTE',
    'MENSUAL'
FROM casas c
JOIN abonados a ON a.id = c.abonado_id
JOIN conceptos_cobro cc ON cc.codigo = 'SERVICIO_MENSUAL'
JOIN periodos_cobro p
    ON p.anio = CAST(strftime('%Y', date('now', 'localtime')) AS INTEGER)
   AND p.mes = CAST(strftime('%m', date('now', 'localtime')) AS INTEGER)
WHERE a.dni = '0801199000022';

INSERT OR IGNORE INTO cargos(
    casa_id,
    abonado_id,
    periodo_id,
    concepto_id,
    descripcion,
    monto_centavos,
    saldo_pendiente_centavos,
    fecha_generacion,
    fecha_vencimiento,
    estado,
    origen
)
SELECT
    c.id,
    a.id,
    p.id,
    cc.id,
    '[PRUEBA] Servicio mensual parcial',
    35000,
    15000,
    p.fecha_inicio,
    p.fecha_vencimiento,
    'PARCIAL',
    'MENSUAL'
FROM casas c
JOIN abonados a ON a.id = c.abonado_id
JOIN conceptos_cobro cc ON cc.codigo = 'SERVICIO_MENSUAL'
JOIN periodos_cobro p
    ON p.anio = CAST(strftime('%Y', date('now', 'localtime', '-2 month')) AS INTEGER)
   AND p.mes = CAST(strftime('%m', date('now', 'localtime', '-2 month')) AS INTEGER)
WHERE a.dni = '0801199000033';

INSERT OR IGNORE INTO cargos(
    casa_id,
    abonado_id,
    periodo_id,
    concepto_id,
    descripcion,
    monto_centavos,
    saldo_pendiente_centavos,
    fecha_generacion,
    fecha_vencimiento,
    estado,
    origen
)
SELECT
    c.id,
    a.id,
    p.id,
    cc.id,
    '[PRUEBA] Servicio mensual al dia',
    35000,
    0,
    p.fecha_inicio,
    p.fecha_vencimiento,
    'PAGADO',
    'MENSUAL'
FROM casas c
JOIN abonados a ON a.id = c.abonado_id
JOIN conceptos_cobro cc ON cc.codigo = 'SERVICIO_MENSUAL'
JOIN periodos_cobro p
    ON p.anio = CAST(strftime('%Y', date('now', 'localtime', '-1 month')) AS INTEGER)
   AND p.mes = CAST(strftime('%m', date('now', 'localtime', '-1 month')) AS INTEGER)
WHERE a.dni = '0801199000044';

-- ============================================================
-- 7. Plan de pago activo e historial de propietarios
-- ============================================================

INSERT INTO planes_pago(
    abonado_id,
    casa_id,
    fecha_inicio,
    fecha_fin,
    monto_total_centavos,
    cuota_regular_centavos,
    cantidad_cuotas,
    cuotas_pagadas,
    estado,
    observaciones,
    creado_por
)
SELECT
    a.id,
    c.id,
    date('now', 'localtime', 'start of month'),
    date('now', 'localtime', 'start of month', '+1 month', '+29 day'),
    70000,
    35000,
    2,
    0,
    'ACTIVO',
    '[PRUEBA] Plan activo asociado a cargos pendientes de la casa.',
    (SELECT id FROM usuarios WHERE lower(nombre_usuario) = 'admin')
FROM abonados a
JOIN casas c ON c.abonado_id = a.id
WHERE a.dni = '0801199000022'
  AND NOT EXISTS (
      SELECT 1
      FROM planes_pago pp
      WHERE pp.casa_id = c.id
        AND pp.estado = 'ACTIVO'
  );

INSERT INTO cuotas_plan_pago(
    plan_pago_id,
    numero_cuota,
    fecha_vencimiento,
    monto_centavos,
    saldo_pendiente_centavos,
    estado,
    cargo_id
)
SELECT
    pp.id,
    1,
    date('now', 'localtime', '-5 day'),
    35000,
    35000,
    'VENCIDO',
    cg.id
FROM planes_pago pp
JOIN casas c ON c.id = pp.casa_id
JOIN abonados a ON a.id = c.abonado_id
JOIN cargos cg ON cg.casa_id = c.id
WHERE a.dni = '0801199000022'
  AND cg.descripcion = '[PRUEBA] Servicio mensual vencido'
  AND NOT EXISTS (
      SELECT 1
      FROM cuotas_plan_pago cpp
      WHERE cpp.plan_pago_id = pp.id
        AND cpp.numero_cuota = 1
  );

INSERT INTO cuotas_plan_pago(
    plan_pago_id,
    numero_cuota,
    fecha_vencimiento,
    monto_centavos,
    saldo_pendiente_centavos,
    estado,
    cargo_id
)
SELECT
    pp.id,
    2,
    date('now', 'localtime', '+25 day'),
    35000,
    35000,
    'PENDIENTE',
    cg.id
FROM planes_pago pp
JOIN casas c ON c.id = pp.casa_id
JOIN abonados a ON a.id = c.abonado_id
JOIN cargos cg ON cg.casa_id = c.id
WHERE a.dni = '0801199000022'
  AND cg.descripcion = '[PRUEBA] Servicio mensual pendiente'
  AND NOT EXISTS (
      SELECT 1
      FROM cuotas_plan_pago cpp
      WHERE cpp.plan_pago_id = pp.id
        AND cpp.numero_cuota = 2
  );

INSERT INTO planes_pago_cargos(plan_pago_id, cargo_id)
SELECT
    pp.id,
    cg.id
FROM planes_pago pp
JOIN casas c ON c.id = pp.casa_id
JOIN abonados a ON a.id = c.abonado_id
JOIN cargos cg ON cg.casa_id = c.id
WHERE a.dni = '0801199000022'
  AND cg.descripcion IN (
      '[PRUEBA] Servicio mensual vencido',
      '[PRUEBA] Servicio mensual pendiente'
  )
  AND NOT EXISTS (
      SELECT 1
      FROM planes_pago_cargos ppc
      WHERE ppc.plan_pago_id = pp.id
        AND ppc.cargo_id = cg.id
  );

INSERT INTO historial_propietarios_casa(
    casa_id,
    abonado_anterior_id,
    abonado_nuevo_id,
    fecha_cambio,
    motivo,
    usuario_id
)
SELECT
    c.id,
    a_anterior.id,
    a_nuevo.id,
    datetime('now', 'localtime', '-18 day'),
    '[PRUEBA] Traspaso administrativo previo registrado para pruebas.',
    (SELECT id FROM usuarios WHERE lower(nombre_usuario) = 'admin')
FROM casas c
JOIN abonados a_nuevo ON a_nuevo.id = c.abonado_id
JOIN abonados a_anterior ON a_anterior.dni = '0801199000011'
WHERE a_nuevo.dni = '0801199000044'
  AND NOT EXISTS (
      SELECT 1
      FROM historial_propietarios_casa h
      WHERE h.casa_id = c.id
        AND h.abonado_nuevo_id = a_nuevo.id
  );

-- ============================================================
-- 8. Pago y comprobante de prueba
-- ============================================================

INSERT INTO pagos(
    abonado_id,
    casa_id,
    usuario_cobrador_id,
    metodo_pago_id,
    referencia_externa,
    total_bruto_centavos,
    descuento_centavos,
    total_pagado_centavos,
    saldo_a_favor_centavos,
    fecha_pago,
    estado,
    observaciones
)
SELECT
    a.id,
    c.id,
    u.id,
    mp.id,
    'PAGO-PRUEBA-001',
    35000,
    0,
    35000,
    0,
    datetime('now', 'localtime'),
    'CONFIRMADO',
    '[PRUEBA] Pago confirmado de desarrollo local.'
FROM abonados a
JOIN casas c ON c.abonado_id = a.id
JOIN usuarios u ON lower(u.nombre_usuario) = 'admin'
JOIN metodos_pago mp ON mp.codigo = 'EFECTIVO'
WHERE a.dni = '0801199000011'
  AND NOT EXISTS (
      SELECT 1 FROM pagos WHERE referencia_externa = 'PAGO-PRUEBA-001'
  );

INSERT INTO pagos_detalle(
    pago_id,
    casa_id,
    cargo_id,
    concepto_id,
    descripcion,
    monto_pagado_centavos,
    periodo_id,
    orden_aplicacion
)
SELECT
    p.id,
    c.id,
    cg.id,
    cc.id,
    '[PRUEBA] Cancelacion de cargo mensual',
    35000,
    pr.id,
    1
FROM pagos p
JOIN abonados a ON a.id = p.abonado_id
JOIN casas c ON c.id = p.casa_id
JOIN cargos cg ON cg.casa_id = c.id AND cg.abonado_id = a.id
JOIN conceptos_cobro cc ON cc.id = cg.concepto_id
JOIN periodos_cobro pr ON pr.id = cg.periodo_id
WHERE p.referencia_externa = 'PAGO-PRUEBA-001'
  AND cg.descripcion = '[PRUEBA] Servicio mensual cancelado'
  AND NOT EXISTS (
      SELECT 1
      FROM pagos_detalle pd
      WHERE pd.pago_id = p.id
        AND pd.cargo_id = cg.id
  );

INSERT INTO comprobantes(
    pago_id,
    numero_comprobante,
    formato_salida,
    ruta_archivo,
    hash_documento,
    generado_por
)
SELECT
    p.id,
    'REC-PRUEBA-001',
    'TEXTO',
    NULL,
    NULL,
    (SELECT id FROM usuarios WHERE lower(nombre_usuario) = 'admin')
FROM pagos p
WHERE p.referencia_externa = 'PAGO-PRUEBA-001'
  AND NOT EXISTS (
      SELECT 1
      FROM comprobantes c
      WHERE c.numero_comprobante = 'REC-PRUEBA-001'
  );

-- ============================================================
-- 9. Reajuste de triggers de auditoria tras migraciones legacy
-- ============================================================

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

-- ============================================================
-- 10. Registro de migracion
-- ============================================================

INSERT INTO esquema_migraciones(version, descripcion, checksum)
VALUES (
    '004',
    'Carga de datos de prueba para desarrollo local y validacion visual de SICAP',
    NULL
);

COMMIT;

