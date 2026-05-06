-- ============================================================
-- SICAP - Sistema de Control Administrativo de Pagos
-- Junta de Agua de Yarumela, La Paz, Honduras
-- Script SQLite actualizado para creacion desde cero
-- Version BD: 2.0.0
-- Enfoque: arquitectura modular + SOLID
-- Motor: SQLite 3.x
-- ============================================================

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA busy_timeout = 5000;
PRAGMA encoding = 'UTF-8';

BEGIN TRANSACTION;

-- ============================================================
-- 1. Control de version
-- ============================================================

CREATE TABLE IF NOT EXISTS esquema_migraciones (
    id INTEGER PRIMARY KEY,
    version TEXT NOT NULL UNIQUE,
    descripcion TEXT NOT NULL,
    aplicado_en TEXT NOT NULL DEFAULT (datetime('now')),
    checksum TEXT
);

-- ============================================================
-- 2. Seguridad: usuarios, roles y permisos
-- ============================================================

CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL UNIQUE COLLATE NOCASE,
    descripcion TEXT,
    es_sistema INTEGER NOT NULL DEFAULT 0 CHECK (es_sistema IN (0, 1)),
    estado TEXT NOT NULL DEFAULT 'ACTIVO' CHECK (estado IN ('ACTIVO', 'INACTIVO')),
    creado_en TEXT NOT NULL DEFAULT (datetime('now')),
    actualizado_en TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS permisos (
    id INTEGER PRIMARY KEY,
    codigo TEXT NOT NULL UNIQUE COLLATE NOCASE,
    nombre TEXT NOT NULL,
    descripcion TEXT,
    modulo TEXT NOT NULL,
    creado_en TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS roles_permisos (
    rol_id INTEGER NOT NULL,
    permiso_id INTEGER NOT NULL,
    creado_en TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (rol_id, permiso_id),
    FOREIGN KEY (rol_id) REFERENCES roles(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (permiso_id) REFERENCES permisos(id) ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY,
    nombre_usuario TEXT NOT NULL UNIQUE COLLATE NOCASE,
    nombre_completo TEXT NOT NULL,
    correo TEXT NOT NULL UNIQUE COLLATE NOCASE,
    contrasena_hash TEXT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'ACTIVO' CHECK (estado IN ('ACTIVO', 'INACTIVO', 'BLOQUEADO')),
    ultimo_acceso_en TEXT,
    ultimo_cambio_contrasena_en TEXT,
    observaciones TEXT,
    creado_en TEXT NOT NULL DEFAULT (datetime('now')),
    actualizado_en TEXT NOT NULL DEFAULT (datetime('now')),
    eliminado_en TEXT,
    creado_por INTEGER,
    actualizado_por INTEGER,
    FOREIGN KEY (creado_por) REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (actualizado_por) REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS usuarios_roles (
    usuario_id INTEGER NOT NULL,
    rol_id INTEGER NOT NULL,
    creado_en TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (usuario_id, rol_id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (rol_id) REFERENCES roles(id) ON UPDATE CASCADE ON DELETE RESTRICT
);

-- ============================================================
-- 3. Catalogos y datos administrativos
-- ============================================================

CREATE TABLE IF NOT EXISTS barrios (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL UNIQUE COLLATE NOCASE,
    estado TEXT NOT NULL DEFAULT 'ACTIVO' CHECK (estado IN ('ACTIVO', 'INACTIVO')),
    observaciones TEXT,
    creado_en TEXT NOT NULL DEFAULT (datetime('now')),
    actualizado_en TEXT NOT NULL DEFAULT (datetime('now')),
    eliminado_en TEXT
);

CREATE TABLE IF NOT EXISTS abonados (
    id INTEGER PRIMARY KEY,
    dni TEXT NOT NULL UNIQUE,
    nombre_completo TEXT NOT NULL,
    telefono TEXT,
    barrio_id INTEGER NOT NULL,
    direccion_referencia TEXT,
    observaciones TEXT,
    estado TEXT NOT NULL DEFAULT 'ACTIVO' CHECK (estado IN ('ACTIVO', 'INACTIVO')),
    fecha_alta TEXT NOT NULL DEFAULT (date('now')),
    creado_en TEXT NOT NULL DEFAULT (datetime('now')),
    actualizado_en TEXT NOT NULL DEFAULT (datetime('now')),
    eliminado_en TEXT,
    FOREIGN KEY (barrio_id) REFERENCES barrios(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    CHECK (length(trim(dni)) >= 8)
);

CREATE TABLE IF NOT EXISTS casas (
    id INTEGER PRIMARY KEY,
    abonado_id INTEGER NOT NULL,
    barrio_id INTEGER NOT NULL,
    direccion_referencia TEXT,
    estado_servicio TEXT NOT NULL DEFAULT 'ACTIVO' CHECK (estado_servicio IN ('ACTIVO', 'CORTADO', 'SUSPENDIDO', 'INACTIVO')),
    fecha_alta TEXT NOT NULL DEFAULT (date('now')),
    observaciones TEXT,
    creado_en TEXT NOT NULL DEFAULT (datetime('now')),
    actualizado_en TEXT NOT NULL DEFAULT (datetime('now')),
    eliminado_en TEXT,
    FOREIGN KEY (abonado_id) REFERENCES abonados(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (barrio_id) REFERENCES barrios(id) ON UPDATE CASCADE ON DELETE RESTRICT
);

-- ============================================================
-- 4. Cobros, periodos y conceptos
-- ============================================================

CREATE TABLE IF NOT EXISTS periodos_cobro (
    id INTEGER PRIMARY KEY,
    anio INTEGER NOT NULL CHECK (anio BETWEEN 2000 AND 2100),
    mes INTEGER NOT NULL CHECK (mes BETWEEN 1 AND 12),
    nombre TEXT NOT NULL,
    fecha_inicio TEXT NOT NULL,
    fecha_fin TEXT NOT NULL,
    fecha_vencimiento TEXT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'ABIERTO' CHECK (estado IN ('ABIERTO', 'CERRADO')),
    creado_en TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (anio, mes),
    CHECK (fecha_fin >= fecha_inicio),
    CHECK (fecha_vencimiento >= fecha_inicio)
);

CREATE TABLE IF NOT EXISTS conceptos_cobro (
    id INTEGER PRIMARY KEY,
    codigo TEXT NOT NULL UNIQUE COLLATE NOCASE,
    nombre TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN (
        'SERVICIO_MENSUAL',
        'MORA',
        'MULTA',
        'RECONEXION',
        'PRIMA',
        'CUOTA_PLAN_PAGO',
        'AJUSTE',
        'PAGO_ADELANTADO',
        'OTRO'
    )),
    requiere_periodo INTEGER NOT NULL DEFAULT 1 CHECK (requiere_periodo IN (0, 1)),
    monto_global_centavos INTEGER CHECK (monto_global_centavos IS NULL OR monto_global_centavos >= 0),
    estado TEXT NOT NULL DEFAULT 'ACTIVO' CHECK (estado IN ('ACTIVO', 'INACTIVO')),
    creado_en TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS cargos (
    id INTEGER PRIMARY KEY,
    casa_id INTEGER NOT NULL,
    abonado_id INTEGER NOT NULL,
    periodo_id INTEGER,
    concepto_id INTEGER NOT NULL,
    descripcion TEXT NOT NULL,
    monto_centavos INTEGER NOT NULL CHECK (monto_centavos >= 0),
    saldo_pendiente_centavos INTEGER NOT NULL CHECK (saldo_pendiente_centavos >= 0),
    fecha_generacion TEXT NOT NULL DEFAULT (date('now')),
    fecha_vencimiento TEXT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'PENDIENTE' CHECK (estado IN ('PENDIENTE', 'PARCIAL', 'PAGADO', 'ANULADO', 'VENCIDO')),
    origen TEXT NOT NULL DEFAULT 'MANUAL' CHECK (origen IN ('MENSUAL', 'PAGO', 'PLAN_PAGO', 'PROCESO_SERVICIO', 'ADELANTO', 'MANUAL')),
    creado_en TEXT NOT NULL DEFAULT (datetime('now')),
    actualizado_en TEXT NOT NULL DEFAULT (datetime('now')),
    anulado_en TEXT,
    anulado_por INTEGER,
    motivo_anulacion TEXT,
    FOREIGN KEY (casa_id) REFERENCES casas(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (abonado_id) REFERENCES abonados(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (periodo_id) REFERENCES periodos_cobro(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (concepto_id) REFERENCES conceptos_cobro(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (anulado_por) REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE SET NULL,
    CHECK (saldo_pendiente_centavos <= monto_centavos),
    UNIQUE (casa_id, periodo_id, concepto_id)
);

CREATE TABLE IF NOT EXISTS metodos_pago (
    id INTEGER PRIMARY KEY,
    codigo TEXT NOT NULL UNIQUE COLLATE NOCASE,
    nombre TEXT NOT NULL,
    descripcion TEXT,
    estado TEXT NOT NULL DEFAULT 'ACTIVO' CHECK (estado IN ('ACTIVO', 'INACTIVO')),
    creado_en TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ============================================================
-- 5. Pagos por una sola casa y comprobantes
-- ============================================================

CREATE TABLE IF NOT EXISTS pagos (
    id INTEGER PRIMARY KEY,
    abonado_id INTEGER NOT NULL,
    casa_id INTEGER NOT NULL,
    usuario_cobrador_id INTEGER NOT NULL,
    metodo_pago_id INTEGER NOT NULL,
    referencia_externa TEXT,
    total_bruto_centavos INTEGER NOT NULL CHECK (total_bruto_centavos >= 0),
    descuento_centavos INTEGER NOT NULL DEFAULT 0 CHECK (descuento_centavos >= 0),
    total_pagado_centavos INTEGER NOT NULL CHECK (total_pagado_centavos >= 0),
    saldo_a_favor_centavos INTEGER NOT NULL DEFAULT 0 CHECK (saldo_a_favor_centavos >= 0),
    fecha_pago TEXT NOT NULL DEFAULT (datetime('now')),
    estado TEXT NOT NULL DEFAULT 'CONFIRMADO' CHECK (estado IN ('CONFIRMADO', 'ANULADO')),
    observaciones TEXT,
    anulado_en TEXT,
    anulado_por INTEGER,
    motivo_anulacion TEXT,
    creado_en TEXT NOT NULL DEFAULT (datetime('now')),
    actualizado_en TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (abonado_id) REFERENCES abonados(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (casa_id) REFERENCES casas(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (usuario_cobrador_id) REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (metodo_pago_id) REFERENCES metodos_pago(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (anulado_por) REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS pagos_detalle (
    id INTEGER PRIMARY KEY,
    pago_id INTEGER NOT NULL,
    casa_id INTEGER NOT NULL,
    cargo_id INTEGER,
    concepto_id INTEGER NOT NULL,
    descripcion TEXT NOT NULL,
    monto_pagado_centavos INTEGER NOT NULL CHECK (monto_pagado_centavos >= 0),
    periodo_id INTEGER,
    orden_aplicacion INTEGER NOT NULL DEFAULT 1 CHECK (orden_aplicacion >= 1),
    creado_en TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (pago_id) REFERENCES pagos(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (casa_id) REFERENCES casas(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (cargo_id) REFERENCES cargos(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (concepto_id) REFERENCES conceptos_cobro(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (periodo_id) REFERENCES periodos_cobro(id) ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS comprobantes (
    id INTEGER PRIMARY KEY,
    pago_id INTEGER NOT NULL UNIQUE,
    numero_comprobante TEXT NOT NULL UNIQUE,
    formato_salida TEXT NOT NULL DEFAULT 'PDF' CHECK (formato_salida IN ('PDF', 'HTML', 'TEXTO')),
    ruta_archivo TEXT,
    hash_documento TEXT,
    generado_en TEXT NOT NULL DEFAULT (datetime('now')),
    generado_por INTEGER,
    FOREIGN KEY (pago_id) REFERENCES pagos(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (generado_por) REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE SET NULL
);

-- ============================================================
-- 6. Planes de pago
-- ============================================================

CREATE TABLE IF NOT EXISTS planes_pago (
    id INTEGER PRIMARY KEY,
    abonado_id INTEGER NOT NULL,
    casa_id INTEGER NOT NULL,
    fecha_inicio TEXT NOT NULL,
    fecha_fin TEXT,
    monto_total_centavos INTEGER NOT NULL CHECK (monto_total_centavos >= 0),
    cuota_regular_centavos INTEGER NOT NULL CHECK (cuota_regular_centavos >= 0),
    cantidad_cuotas INTEGER NOT NULL CHECK (cantidad_cuotas > 0),
    cuotas_pagadas INTEGER NOT NULL DEFAULT 0 CHECK (cuotas_pagadas >= 0),
    estado TEXT NOT NULL DEFAULT 'ACTIVO' CHECK (estado IN ('ACTIVO', 'FINALIZADO', 'ANULADO', 'CANCELADO')),
    observaciones TEXT,
    creado_en TEXT NOT NULL DEFAULT (datetime('now')),
    actualizado_en TEXT NOT NULL DEFAULT (datetime('now')),
    creado_por INTEGER,
    FOREIGN KEY (abonado_id) REFERENCES abonados(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (casa_id) REFERENCES casas(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (creado_por) REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE SET NULL,
    CHECK (fecha_fin IS NULL OR fecha_fin >= fecha_inicio)
);

CREATE TABLE IF NOT EXISTS cuotas_plan_pago (
    id INTEGER PRIMARY KEY,
    plan_pago_id INTEGER NOT NULL,
    numero_cuota INTEGER NOT NULL CHECK (numero_cuota >= 1),
    fecha_vencimiento TEXT NOT NULL,
    monto_centavos INTEGER NOT NULL CHECK (monto_centavos >= 0),
    saldo_pendiente_centavos INTEGER NOT NULL CHECK (saldo_pendiente_centavos >= 0),
    estado TEXT NOT NULL DEFAULT 'PENDIENTE' CHECK (estado IN ('PENDIENTE', 'PARCIAL', 'PAGADO', 'VENCIDO', 'ANULADO')),
    cargo_id INTEGER,
    creado_en TEXT NOT NULL DEFAULT (datetime('now')),
    actualizado_en TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (plan_pago_id) REFERENCES planes_pago(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (cargo_id) REFERENCES cargos(id) ON UPDATE CASCADE ON DELETE SET NULL,
    CHECK (saldo_pendiente_centavos <= monto_centavos),
    UNIQUE (plan_pago_id, numero_cuota)
);

CREATE TABLE IF NOT EXISTS planes_pago_cargos (
    plan_pago_id INTEGER NOT NULL,
    cargo_id INTEGER NOT NULL,
    creado_en TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (plan_pago_id, cargo_id),
    FOREIGN KEY (plan_pago_id) REFERENCES planes_pago(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (cargo_id) REFERENCES cargos(id) ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS pagos_adelantados (
    id INTEGER PRIMARY KEY,
    abonado_id INTEGER NOT NULL,
    casa_id INTEGER NOT NULL,
    pago_id INTEGER NOT NULL,
    periodo_id INTEGER NOT NULL,
    monto_centavos INTEGER NOT NULL CHECK (monto_centavos >= 0),
    creado_en TEXT NOT NULL DEFAULT (datetime('now')),
    observaciones TEXT,
    FOREIGN KEY (abonado_id) REFERENCES abonados(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (casa_id) REFERENCES casas(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (pago_id) REFERENCES pagos(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (periodo_id) REFERENCES periodos_cobro(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    UNIQUE (casa_id, periodo_id, pago_id)
);

CREATE TABLE IF NOT EXISTS procesos_servicio (
    id INTEGER PRIMARY KEY,
    abonado_id INTEGER NOT NULL,
    casa_id INTEGER NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('CORTE', 'RECONEXION', 'INSPECCION', 'NOTIFICACION')),
    fecha_programada TEXT,
    fecha_ejecucion TEXT,
    estado TEXT NOT NULL DEFAULT 'PENDIENTE' CHECK (estado IN ('PENDIENTE', 'EJECUTADO', 'CANCELADO')),
    motivo TEXT,
    observaciones TEXT,
    plan_pago_id INTEGER,
    usuario_id INTEGER,
    creado_en TEXT NOT NULL DEFAULT (datetime('now')),
    actualizado_en TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (abonado_id) REFERENCES abonados(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (casa_id) REFERENCES casas(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (plan_pago_id) REFERENCES planes_pago(id) ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS historial_propietarios_casa (
    id INTEGER PRIMARY KEY,
    casa_id INTEGER NOT NULL,
    abonado_anterior_id INTEGER,
    abonado_nuevo_id INTEGER NOT NULL,
    fecha_cambio TEXT NOT NULL DEFAULT (datetime('now')),
    motivo TEXT,
    usuario_id INTEGER,
    creado_en TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (casa_id) REFERENCES casas(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (abonado_anterior_id) REFERENCES abonados(id) ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (abonado_nuevo_id) REFERENCES abonados(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE SET NULL
);

-- ============================================================
-- 7. Seguridad operativa y configuracion
-- ============================================================

CREATE TABLE IF NOT EXISTS sesiones (
    id INTEGER PRIMARY KEY,
    usuario_id INTEGER NOT NULL,
    token_sesion TEXT NOT NULL UNIQUE,
    iniciado_en TEXT NOT NULL DEFAULT (datetime('now')),
    expira_en TEXT NOT NULL,
    finalizado_en TEXT,
    ip_origen TEXT,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS tokens_recuperacion_contrasena (
    id INTEGER PRIMARY KEY,
    usuario_id INTEGER NOT NULL,
    token TEXT NOT NULL UNIQUE,
    expira_en TEXT NOT NULL,
    usado_en TEXT,
    creado_en TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS intentos_login (
    id INTEGER PRIMARY KEY,
    usuario_id INTEGER,
    nombre_usuario TEXT NOT NULL,
    exito INTEGER NOT NULL CHECK (exito IN (0, 1)),
    ip_origen TEXT,
    registrado_en TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS configuracion_sistema (
    id INTEGER PRIMARY KEY,
    clave TEXT NOT NULL UNIQUE COLLATE NOCASE,
    valor TEXT NOT NULL,
    tipo_dato TEXT NOT NULL CHECK (tipo_dato IN ('TEXTO', 'ENTERO', 'DECIMAL', 'BOOLEANO', 'JSON')),
    categoria TEXT NOT NULL,
    descripcion TEXT,
    editable INTEGER NOT NULL DEFAULT 1 CHECK (editable IN (0, 1)),
    actualizado_en TEXT NOT NULL DEFAULT (datetime('now')),
    actualizado_por INTEGER,
    FOREIGN KEY (actualizado_por) REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS auditoria (
    id INTEGER PRIMARY KEY,
    usuario_id INTEGER,
    accion TEXT NOT NULL,
    entidad TEXT NOT NULL,
    entidad_id INTEGER,
    resumen TEXT NOT NULL,
    datos_antes_json TEXT,
    datos_despues_json TEXT,
    creado_en TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS reportes_generados (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    parametros_json TEXT,
    formato TEXT NOT NULL CHECK (formato IN ('PDF', 'XLSX', 'CSV', 'HTML')),
    ruta_archivo TEXT,
    generado_en TEXT NOT NULL DEFAULT (datetime('now')),
    generado_por INTEGER,
    FOREIGN KEY (generado_por) REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE SET NULL
);

-- ============================================================
-- 8. Indices de apoyo
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_abonados_barrio_id ON abonados(barrio_id);
CREATE INDEX IF NOT EXISTS idx_abonados_nombre_completo ON abonados(nombre_completo);
CREATE INDEX IF NOT EXISTS idx_casas_abonado_id ON casas(abonado_id);
CREATE INDEX IF NOT EXISTS idx_casas_barrio_id ON casas(barrio_id);
CREATE INDEX IF NOT EXISTS idx_casas_estado_servicio ON casas(estado_servicio);
CREATE INDEX IF NOT EXISTS idx_cargos_abonado_id ON cargos(abonado_id);
CREATE INDEX IF NOT EXISTS idx_cargos_casa_id ON cargos(casa_id);
CREATE INDEX IF NOT EXISTS idx_cargos_periodo_id ON cargos(periodo_id);
CREATE INDEX IF NOT EXISTS idx_cargos_estado ON cargos(estado);
CREATE INDEX IF NOT EXISTS idx_pagos_abonado_id ON pagos(abonado_id);
CREATE INDEX IF NOT EXISTS idx_pagos_casa_id ON pagos(casa_id);
CREATE INDEX IF NOT EXISTS idx_pagos_usuario_cobrador_id ON pagos(usuario_cobrador_id);
CREATE INDEX IF NOT EXISTS idx_pagos_fecha_pago ON pagos(fecha_pago);
CREATE INDEX IF NOT EXISTS idx_pagos_estado ON pagos(estado);
CREATE INDEX IF NOT EXISTS idx_pagos_detalle_pago_id ON pagos_detalle(pago_id);
CREATE INDEX IF NOT EXISTS idx_pagos_detalle_cargo_id ON pagos_detalle(cargo_id);
CREATE INDEX IF NOT EXISTS idx_planes_pago_abonado_id ON planes_pago(abonado_id);
CREATE INDEX IF NOT EXISTS idx_planes_pago_casa_id ON planes_pago(casa_id);
CREATE INDEX IF NOT EXISTS idx_planes_pago_estado ON planes_pago(estado);
CREATE INDEX IF NOT EXISTS idx_cuotas_plan_pago_plan_id ON cuotas_plan_pago(plan_pago_id);
CREATE INDEX IF NOT EXISTS idx_cuotas_plan_pago_estado ON cuotas_plan_pago(estado);
CREATE INDEX IF NOT EXISTS idx_procesos_servicio_estado ON procesos_servicio(estado);
CREATE INDEX IF NOT EXISTS idx_procesos_servicio_tipo ON procesos_servicio(tipo);
CREATE INDEX IF NOT EXISTS idx_intentos_login_nombre_usuario ON intentos_login(nombre_usuario);
CREATE INDEX IF NOT EXISTS idx_auditoria_entidad ON auditoria(entidad, entidad_id);
CREATE INDEX IF NOT EXISTS idx_auditoria_accion ON auditoria(accion);
CREATE INDEX IF NOT EXISTS idx_reportes_generados_fecha ON reportes_generados(generado_en);

-- ============================================================
-- 9. Vistas de consulta y reportes
-- ============================================================

CREATE VIEW IF NOT EXISTS vw_cargos_pendientes_ordenados AS
SELECT
    c.id,
    c.casa_id,
    c.abonado_id,
    a.nombre_completo AS abonado_nombre,
    c.periodo_id,
    pc.nombre AS periodo_nombre,
    cc.codigo AS concepto_codigo,
    cc.nombre AS concepto_nombre,
    c.descripcion,
    c.monto_centavos,
    c.saldo_pendiente_centavos,
    c.fecha_generacion,
    c.fecha_vencimiento,
    c.estado
FROM cargos c
INNER JOIN abonados a ON a.id = c.abonado_id
LEFT JOIN periodos_cobro pc ON pc.id = c.periodo_id
INNER JOIN conceptos_cobro cc ON cc.id = c.concepto_id
WHERE c.estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDO')
  AND c.saldo_pendiente_centavos > 0
ORDER BY c.fecha_vencimiento ASC, c.fecha_generacion ASC, c.id ASC;

CREATE VIEW IF NOT EXISTS vw_resumen_deuda_casas AS
SELECT
    ca.id AS casa_id,
    ca.abonado_id,
    a.nombre_completo AS abonado_nombre,
    ca.estado_servicio,
    COUNT(c.id) AS total_cargos_pendientes,
    COALESCE(SUM(c.saldo_pendiente_centavos), 0) AS deuda_total_centavos
FROM casas ca
INNER JOIN abonados a ON a.id = ca.abonado_id
LEFT JOIN cargos c
    ON c.casa_id = ca.id
   AND c.estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDO')
   AND c.saldo_pendiente_centavos > 0
GROUP BY ca.id, ca.abonado_id, a.nombre_completo, ca.estado_servicio;

CREATE VIEW IF NOT EXISTS vw_resumen_abonados AS
SELECT
    a.id,
    a.dni,
    a.nombre_completo,
    a.telefono,
    b.nombre AS barrio_nombre,
    a.estado
FROM abonados a
INNER JOIN barrios b ON b.id = a.barrio_id;

CREATE VIEW IF NOT EXISTS vw_resumen_estado_servicios AS
SELECT
    estado_servicio,
    COUNT(*) AS total_casas
FROM casas
GROUP BY estado_servicio;

CREATE VIEW IF NOT EXISTS vw_abonados_por_estado_servicio AS
SELECT
    a.id AS abonado_id,
    a.nombre_completo,
    c.id AS casa_id,
    c.estado_servicio
FROM abonados a
INNER JOIN casas c ON c.abonado_id = a.id;

CREATE VIEW IF NOT EXISTS vw_deuda_total_servicios_activos AS
SELECT
    SUM(saldo_pendiente_centavos) AS deuda_total_centavos
FROM cargos c
INNER JOIN casas ca ON ca.id = c.casa_id
WHERE ca.estado_servicio = 'ACTIVO'
  AND c.estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDO');

CREATE VIEW IF NOT EXISTS vw_mora_real_servicios_activos AS
SELECT
    COUNT(*) AS cargos_vencidos,
    COALESCE(SUM(saldo_pendiente_centavos), 0) AS deuda_vencida_centavos
FROM cargos c
INNER JOIN casas ca ON ca.id = c.casa_id
WHERE ca.estado_servicio = 'ACTIVO'
  AND c.estado = 'VENCIDO'
  AND c.saldo_pendiente_centavos > 0;

CREATE VIEW IF NOT EXISTS vw_abonados_con_deuda AS
SELECT
    a.id AS abonado_id,
    a.nombre_completo,
    COUNT(DISTINCT c.casa_id) AS total_casas_con_deuda,
    COALESCE(SUM(c.saldo_pendiente_centavos), 0) AS deuda_total_centavos
FROM abonados a
INNER JOIN cargos c ON c.abonado_id = a.id
WHERE c.estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDO')
  AND c.saldo_pendiente_centavos > 0
GROUP BY a.id, a.nombre_completo;

CREATE VIEW IF NOT EXISTS vw_abonados_sin_deuda AS
SELECT
    a.id AS abonado_id,
    a.nombre_completo
FROM abonados a
WHERE NOT EXISTS (
    SELECT 1
    FROM cargos c
    WHERE c.abonado_id = a.id
      AND c.estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDO')
      AND c.saldo_pendiente_centavos > 0
);

CREATE VIEW IF NOT EXISTS vw_deuda_por_barrio AS
SELECT
    b.id AS barrio_id,
    b.nombre AS barrio_nombre,
    COALESCE(SUM(c.saldo_pendiente_centavos), 0) AS deuda_total_centavos
FROM barrios b
LEFT JOIN abonados a ON a.barrio_id = b.id
LEFT JOIN cargos c
    ON c.abonado_id = a.id
   AND c.estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDO')
   AND c.saldo_pendiente_centavos > 0
GROUP BY b.id, b.nombre;

CREATE VIEW IF NOT EXISTS vw_historial_pagos_abonado AS
SELECT
    p.id AS pago_id,
    p.abonado_id,
    a.nombre_completo AS abonado_nombre,
    p.casa_id,
    p.fecha_pago,
    p.total_pagado_centavos,
    mp.nombre AS metodo_pago_nombre,
    p.estado
FROM pagos p
INNER JOIN abonados a ON a.id = p.abonado_id
INNER JOIN metodos_pago mp ON mp.id = p.metodo_pago_id;

CREATE VIEW IF NOT EXISTS vw_ingresos_por_fecha AS
SELECT
    date(fecha_pago) AS fecha,
    COUNT(*) AS total_pagos,
    COALESCE(SUM(total_pagado_centavos), 0) AS total_ingresos_centavos
FROM pagos
WHERE estado = 'CONFIRMADO'
GROUP BY date(fecha_pago);

CREATE VIEW IF NOT EXISTS vw_pagos_por_cobrador AS
SELECT
    u.id AS usuario_id,
    u.nombre_completo,
    COUNT(p.id) AS total_pagos,
    COALESCE(SUM(p.total_pagado_centavos), 0) AS total_cobrado_centavos
FROM usuarios u
LEFT JOIN pagos p
    ON p.usuario_cobrador_id = u.id
   AND p.estado = 'CONFIRMADO'
GROUP BY u.id, u.nombre_completo;

CREATE VIEW IF NOT EXISTS vw_casas_deuda_5_meses AS
SELECT *
FROM vw_resumen_deuda_casas
WHERE deuda_total_centavos > 0;

CREATE VIEW IF NOT EXISTS vw_planes_pago_activos AS
SELECT
    pp.id,
    pp.abonado_id,
    a.nombre_completo AS abonado_nombre,
    pp.casa_id,
    pp.fecha_inicio,
    pp.fecha_fin,
    pp.monto_total_centavos,
    pp.cuota_regular_centavos,
    pp.cantidad_cuotas,
    pp.cuotas_pagadas,
    pp.estado
FROM planes_pago pp
INNER JOIN abonados a ON a.id = pp.abonado_id
WHERE pp.estado = 'ACTIVO';

CREATE VIEW IF NOT EXISTS vw_cuotas_vencidas AS
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
  AND cpp.fecha_vencimiento < date('now');

CREATE VIEW IF NOT EXISTS vw_pagos_adelantados AS
SELECT
    pa.id,
    pa.abonado_id,
    a.nombre_completo AS abonado_nombre,
    pa.casa_id,
    pa.periodo_id,
    pc.nombre AS periodo_nombre,
    pa.monto_centavos,
    pa.creado_en
FROM pagos_adelantados pa
INNER JOIN abonados a ON a.id = pa.abonado_id
INNER JOIN periodos_cobro pc ON pc.id = pa.periodo_id;

-- ============================================================
-- 10. Triggers de consistencia y trazabilidad
-- ============================================================

CREATE TRIGGER IF NOT EXISTS trg_usuarios_actualizado
AFTER UPDATE ON usuarios
FOR EACH ROW
WHEN NEW.actualizado_en = OLD.actualizado_en
BEGIN
    UPDATE usuarios SET actualizado_en = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_barrios_actualizado
AFTER UPDATE ON barrios
FOR EACH ROW
WHEN NEW.actualizado_en = OLD.actualizado_en
BEGIN
    UPDATE barrios SET actualizado_en = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_abonados_actualizado
AFTER UPDATE ON abonados
FOR EACH ROW
WHEN NEW.actualizado_en = OLD.actualizado_en
BEGIN
    UPDATE abonados SET actualizado_en = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_casas_actualizado
AFTER UPDATE ON casas
FOR EACH ROW
WHEN NEW.actualizado_en = OLD.actualizado_en
BEGIN
    UPDATE casas SET actualizado_en = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_cargos_actualizado
AFTER UPDATE ON cargos
FOR EACH ROW
WHEN NEW.actualizado_en = OLD.actualizado_en
BEGIN
    UPDATE cargos SET actualizado_en = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_pagos_actualizado
AFTER UPDATE ON pagos
FOR EACH ROW
WHEN NEW.actualizado_en = OLD.actualizado_en
BEGIN
    UPDATE pagos SET actualizado_en = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_planes_pago_actualizado
AFTER UPDATE ON planes_pago
FOR EACH ROW
WHEN NEW.actualizado_en = OLD.actualizado_en
BEGIN
    UPDATE planes_pago SET actualizado_en = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_cuotas_plan_pago_actualizado
AFTER UPDATE ON cuotas_plan_pago
FOR EACH ROW
WHEN NEW.actualizado_en = OLD.actualizado_en
BEGIN
    UPDATE cuotas_plan_pago SET actualizado_en = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_procesos_servicio_actualizado
AFTER UPDATE ON procesos_servicio
FOR EACH ROW
WHEN NEW.actualizado_en = OLD.actualizado_en
BEGIN
    UPDATE procesos_servicio SET actualizado_en = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_bloquear_eliminacion_pagos
BEFORE DELETE ON pagos
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'No se permite eliminar pagos. Use anulacion para conservar trazabilidad.');
END;

CREATE TRIGGER IF NOT EXISTS trg_bloquear_eliminacion_cargos
BEFORE DELETE ON cargos
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'No se permite eliminar cargos. Use estado ANULADO para conservar trazabilidad.');
END;

CREATE TRIGGER IF NOT EXISTS trg_bloquear_eliminacion_planes_pago
BEFORE DELETE ON planes_pago
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'No se permite eliminar planes de pago. Use estado ANULADO o CANCELADO.');
END;

CREATE TRIGGER IF NOT EXISTS trg_auditoria_pago_anulado
AFTER UPDATE OF estado ON pagos
FOR EACH ROW
WHEN OLD.estado <> NEW.estado AND NEW.estado = 'ANULADO'
BEGIN
    INSERT INTO auditoria(usuario_id, accion, entidad, entidad_id, resumen, datos_antes_json, datos_despues_json)
    VALUES (
        NEW.anulado_por,
        'ANULAR_PAGO',
        'pagos',
        NEW.id,
        'Pago anulado: REC-' || printf('%06d', NEW.id),
        json_object('estado', OLD.estado, 'total_pagado_centavos', OLD.total_pagado_centavos),
        json_object('estado', NEW.estado, 'motivo_anulacion', NEW.motivo_anulacion)
    );
END;

CREATE TRIGGER IF NOT EXISTS trg_auditoria_cambio_estado_casa
AFTER UPDATE OF estado_servicio ON casas
FOR EACH ROW
WHEN OLD.estado_servicio <> NEW.estado_servicio
BEGIN
    INSERT INTO auditoria(usuario_id, accion, entidad, entidad_id, resumen, datos_antes_json, datos_despues_json)
    VALUES (
        NULL,
        'CAMBIAR_ESTADO_SERVICIO',
        'casas',
        NEW.id,
        'Cambio de estado de servicio de casa ' || NEW.id,
        json_object('estado_servicio', OLD.estado_servicio),
        json_object('estado_servicio', NEW.estado_servicio)
    );
END;

-- ============================================================
-- 11. Datos iniciales
-- ============================================================

INSERT OR IGNORE INTO esquema_migraciones(version, descripcion, checksum)
VALUES ('002', 'Esquema inicial actualizado SICAP con pagos multicasa, planes, mora opcional y reportes basicos', NULL);

INSERT OR IGNORE INTO roles(id, nombre, descripcion, es_sistema) VALUES
(1, 'SUPERADMINISTRADOR', 'Acceso total al sistema.', 1),
(2, 'ADMINISTRADOR', 'Administra usuarios, catalogos, abonados, casas, pagos y reportes.', 1),
(3, 'CAJERO', 'Registra pagos y consulta historial.', 1),
(4, 'CONSULTA', 'Acceso de solo lectura a consultas y reportes.', 1);

INSERT OR IGNORE INTO permisos(codigo, nombre, descripcion, modulo) VALUES
('dashboard.ver', 'Ver dashboard', 'Permite visualizar el panel principal.', 'Dashboard'),
('abonados.gestionar', 'Gestionar abonados', 'Permite crear, editar y consultar abonados.', 'Abonados'),
('casas.gestionar', 'Gestionar casas', 'Permite crear, editar y consultar casas.', 'Casas'),
('pagos.registrar', 'Registrar pagos', 'Permite registrar pagos.', 'Pagos'),
('pagos.anular', 'Anular pagos', 'Permite anular pagos conservando auditoria.', 'Pagos'),
('planes_pago.gestionar', 'Gestionar planes de pago', 'Permite crear y consultar planes de pago.', 'Planes de pago'),
('morosidad.ver', 'Ver deuda y morosidad', 'Permite consultar cuentas con deuda.', 'Morosidad'),
('reportes.generar', 'Generar reportes', 'Permite emitir reportes.', 'Reportes'),
('usuarios.gestionar', 'Gestionar usuarios', 'Permite administrar usuarios, roles y permisos.', 'Usuarios'),
('configuracion.gestionar', 'Gestionar configuracion', 'Permite modificar parametros del sistema.', 'Configuracion');

INSERT OR IGNORE INTO roles_permisos(rol_id, permiso_id)
SELECT 1, id FROM permisos;

INSERT OR IGNORE INTO roles_permisos(rol_id, permiso_id)
SELECT 2, id FROM permisos;

INSERT OR IGNORE INTO roles_permisos(rol_id, permiso_id)
SELECT 3, id FROM permisos
WHERE codigo IN ('dashboard.ver', 'pagos.registrar', 'planes_pago.gestionar', 'morosidad.ver', 'reportes.generar');

INSERT OR IGNORE INTO roles_permisos(rol_id, permiso_id)
SELECT 4, id FROM permisos
WHERE codigo IN ('dashboard.ver', 'morosidad.ver', 'reportes.generar');

INSERT OR IGNORE INTO usuarios(id, nombre_usuario, nombre_completo, correo, contrasena_hash, estado, observaciones) VALUES
(1, 'admin', 'Administrador del Sistema', 'admin@sicap.local', 'CAMBIAR_HASH_EN_DESARROLLO', 'ACTIVO', 'Usuario inicial de desarrollo. Cambiar contrasena antes de usar en produccion.');

INSERT OR IGNORE INTO usuarios_roles(usuario_id, rol_id) VALUES (1, 1);

INSERT OR IGNORE INTO metodos_pago(codigo, nombre, descripcion) VALUES
('EFECTIVO', 'Efectivo', 'Pago recibido en efectivo.'),
('TRANSFERENCIA', 'Transferencia', 'Pago por transferencia bancaria.'),
('TARJETA', 'Tarjeta', 'Pago por tarjeta de debito o credito.'),
('OTRO', 'Otro', 'Otro metodo de pago autorizado.');

INSERT OR IGNORE INTO conceptos_cobro(codigo, nombre, tipo, requiere_periodo, monto_global_centavos) VALUES
('SERVICIO_MENSUAL', 'Servicio mensual de agua', 'SERVICIO_MENSUAL', 1, NULL),
('MORA', 'Mora opcional', 'MORA', 1, 0),
('MULTA', 'Multa configurable', 'MULTA', 0, NULL),
('RECONEXION', 'Reconexion con monto definido en pago', 'RECONEXION', 0, NULL),
('PRIMA', 'Prima inicial', 'PRIMA', 0, NULL),
('CUOTA_PLAN_PAGO', 'Cuota de plan de pago', 'CUOTA_PLAN_PAGO', 1, NULL),
('AJUSTE', 'Ajuste administrativo', 'AJUSTE', 0, NULL),
('PAGO_ADELANTADO', 'Pago adelantado', 'PAGO_ADELANTADO', 1, NULL);

INSERT OR IGNORE INTO configuracion_sistema(clave, valor, tipo_dato, categoria, descripcion, editable) VALUES
('sistema.nombre', 'SICAP', 'TEXTO', 'Sistema', 'Nombre del sistema.', 0),
('sistema.version', '2.0.0', 'TEXTO', 'Sistema', 'Version del esquema actualizado.', 0),
('sistema.respaldo_automatico', '0', 'BOOLEANO', 'Sistema', 'Permite activar respaldo automatico.', 1),
('junta.nombre', 'Junta de Agua de Yarumela', 'TEXTO', 'Junta', 'Nombre de la Junta.', 1),
('junta.telefono', '', 'TEXTO', 'Junta', 'Telefono de contacto.', 1),
('junta.correo', '', 'TEXTO', 'Junta', 'Correo de contacto.', 1),
('junta.direccion', 'Yarumela, La Paz', 'TEXTO', 'Junta', 'Direccion de la Junta.', 1),
('cobro.precio_mensual_centavos', '0', 'ENTERO', 'Cobro', 'Precio mensual global del servicio de agua.', 1),
('cobro.multa_activa', '1', 'BOOLEANO', 'Cobro', 'Permite activar o desactivar multa.', 1),
('cobro.multa_monto_centavos', '0', 'ENTERO', 'Cobro', 'Monto global de multa en centavos.', 1),
('cobro.mora_activa', '0', 'BOOLEANO', 'Cobro', 'La mora es opcional y actualmente no se utiliza.', 1),
('cobro.mora_monto_centavos', '0', 'ENTERO', 'Cobro', 'Monto de mora si en el futuro se activa.', 1),
('cobro.meses_para_corte', '5', 'ENTERO', 'Cobro', 'Cantidad de meses de deuda para destacar o cortar.', 1),
('cobro.permitir_pago_adelantado', '1', 'BOOLEANO', 'Cobro', 'Permite registrar pagos adelantados.', 1),
('cobro.meses_adelanto_maximo', '12', 'ENTERO', 'Cobro', 'Maximo de meses adelantados permitidos.', 1),
('factura.texto_pie', 'Gracias por su pago.', 'TEXTO', 'Factura', 'Texto de pie para comprobantes.', 1),
('factura.formato_salida', 'PDF', 'TEXTO', 'Factura', 'Formato de salida de comprobantes.', 1),
('resend.correo_remitente', 'no-reply@sicap.local', 'TEXTO', 'Correo', 'Correo remitente usado por Resend.', 1);

COMMIT;

-- ============================================================
-- 12. Validacion y uso recomendado
-- ============================================================
-- Ejecutar desde Python al abrir cada conexion:
-- PRAGMA foreign_keys = ON;
--
-- Validar despues de crear la base:
-- PRAGMA integrity_check;
-- PRAGMA foreign_key_check;
--
-- Regla de negocio importante:
-- El cobro de cargos pendientes debe hacerse desde el cargo mas antiguo.
-- La vista vw_cargos_pendientes_ordenados facilita esa consulta, pero la validacion
-- final debe implementarse en el servicio de pagos de Python.
--
-- Nota sobre mora:
-- La mora queda preparada como concepto y configuracion opcional, pero por defecto esta desactivada.
-- Para deuda pendiente se usan saldo_pendiente_centavos y vistas de deuda, no mora.
--
-- Nota sobre reconexion:
-- La reconexion no tiene monto global obligatorio. El monto se define en el pago,
-- cargo o proceso de servicio correspondiente.
