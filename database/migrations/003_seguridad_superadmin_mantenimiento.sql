PRAGMA foreign_keys = OFF;

BEGIN TRANSACTION;

ALTER TABLE usuarios ADD COLUMN es_tecnico INTEGER NOT NULL DEFAULT 0 CHECK (es_tecnico IN (0, 1));
ALTER TABLE usuarios ADD COLUMN es_oculto INTEGER NOT NULL DEFAULT 0 CHECK (es_oculto IN (0, 1));
ALTER TABLE usuarios ADD COLUMN requiere_cambio_contrasena INTEGER NOT NULL DEFAULT 0 CHECK (requiere_cambio_contrasena IN (0, 1));
ALTER TABLE usuarios ADD COLUMN intentos_fallidos INTEGER NOT NULL DEFAULT 0 CHECK (intentos_fallidos >= 0);
ALTER TABLE usuarios ADD COLUMN bloqueado_hasta TEXT;
ALTER TABLE usuarios ADD COLUMN fecha_restablecimiento_contrasena TEXT;
ALTER TABLE usuarios ADD COLUMN restablecida_por_usuario_id INTEGER REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE sesiones RENAME TO sesiones_legacy_003;
CREATE TABLE sesiones (
    id INTEGER PRIMARY KEY,
    usuario_id INTEGER NOT NULL,
    token_sesion_hash TEXT NOT NULL UNIQUE,
    iniciado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    expira_en TEXT,
    cerrado_en TEXT,
    equipo TEXT,
    estado TEXT NOT NULL DEFAULT 'ACTIVA' CHECK (estado IN ('ACTIVA', 'CERRADA', 'EXPIRADA')),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE RESTRICT
);
INSERT INTO sesiones(usuario_id, token_sesion_hash, iniciado_en, expira_en, cerrado_en, equipo, estado)
SELECT
    usuario_id,
    lower(hex(randomblob(32))),
    COALESCE(iniciado_en, datetime('now', 'localtime')),
    expira_en,
    finalizado_en,
    ip_origen,
    CASE
        WHEN finalizado_en IS NOT NULL THEN 'CERRADA'
        ELSE 'EXPIRADA'
    END
FROM sesiones_legacy_003;
DROP TABLE sesiones_legacy_003;

ALTER TABLE intentos_login RENAME TO intentos_login_legacy_003;
CREATE TABLE intentos_login (
    id INTEGER PRIMARY KEY,
    usuario_o_correo TEXT NOT NULL,
    usuario_id INTEGER,
    intento_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    resultado TEXT NOT NULL CHECK (resultado IN ('EXITOSO', 'FALLIDO')),
    motivo TEXT,
    equipo TEXT,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE SET NULL
);
INSERT INTO intentos_login(id, usuario_o_correo, usuario_id, intento_en, resultado, motivo, equipo)
SELECT
    id,
    nombre_usuario,
    usuario_id,
    COALESCE(registrado_en, datetime('now', 'localtime')),
    CASE WHEN exito = 1 THEN 'EXITOSO' ELSE 'FALLIDO' END,
    NULL,
    ip_origen
FROM intentos_login_legacy_003;
DROP TABLE intentos_login_legacy_003;

ALTER TABLE configuracion_sistema RENAME TO configuracion_sistema_legacy_003;
CREATE TABLE configuracion_sistema (
    id INTEGER PRIMARY KEY,
    clave TEXT NOT NULL UNIQUE COLLATE NOCASE,
    valor TEXT,
    tipo_dato TEXT NOT NULL DEFAULT 'TEXTO' CHECK (tipo_dato IN ('TEXTO', 'ENTERO', 'DECIMAL', 'BOOLEANO', 'FECHA', 'JSON')),
    categoria TEXT NOT NULL,
    descripcion TEXT,
    editable INTEGER NOT NULL DEFAULT 1 CHECK (editable IN (0, 1)),
    actualizado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    actualizado_por INTEGER,
    FOREIGN KEY (actualizado_por) REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE SET NULL
);
INSERT INTO configuracion_sistema(id, clave, valor, tipo_dato, categoria, descripcion, editable, actualizado_en, actualizado_por)
SELECT
    id,
    clave,
    valor,
    tipo_dato,
    categoria,
    descripcion,
    editable,
    actualizado_en,
    actualizado_por
FROM configuracion_sistema_legacy_003;
DROP TABLE configuracion_sistema_legacy_003;

ALTER TABLE auditoria RENAME TO auditoria_legacy_003;
CREATE TABLE auditoria (
    id INTEGER PRIMARY KEY,
    usuario_id INTEGER,
    accion TEXT NOT NULL,
    entidad TEXT NOT NULL,
    entidad_id INTEGER,
    resumen TEXT,
    datos_antes_json TEXT,
    datos_despues_json TEXT,
    fecha_evento TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE SET NULL
);
INSERT INTO auditoria(id, usuario_id, accion, entidad, entidad_id, resumen, datos_antes_json, datos_despues_json, fecha_evento)
SELECT
    id,
    usuario_id,
    accion,
    entidad,
    entidad_id,
    resumen,
    datos_antes_json,
    datos_despues_json,
    creado_en
FROM auditoria_legacy_003;
DROP TABLE auditoria_legacy_003;

CREATE TABLE IF NOT EXISTS historial_respaldos (
    id INTEGER PRIMARY KEY,
    tipo_respaldo TEXT NOT NULL DEFAULT 'MANUAL' CHECK (tipo_respaldo IN ('MANUAL', 'AUTOMATICO', 'PRE_MANTENIMIENTO')),
    nombre_archivo TEXT NOT NULL,
    ruta_archivo TEXT NOT NULL,
    tamano_bytes INTEGER CHECK (tamano_bytes IS NULL OR tamano_bytes >= 0),
    hash_archivo TEXT,
    estado TEXT NOT NULL DEFAULT 'GENERADO' CHECK (estado IN ('GENERADO', 'VALIDADO', 'RESTAURADO', 'FALLIDO')),
    observaciones TEXT,
    generado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    generado_por INTEGER,
    FOREIGN KEY (generado_por) REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS eventos_tecnicos (
    id INTEGER PRIMARY KEY,
    categoria TEXT NOT NULL CHECK (categoria IN ('LOG', 'MANTENIMIENTO', 'RESPALDO', 'RESTAURACION', 'SEGURIDAD', 'DIAGNOSTICO')),
    severidad TEXT NOT NULL DEFAULT 'INFO' CHECK (severidad IN ('INFO', 'ADVERTENCIA', 'ERROR', 'CRITICO')),
    mensaje TEXT NOT NULL,
    detalle TEXT,
    origen TEXT,
    entidad TEXT,
    entidad_id INTEGER,
    equipo TEXT,
    registrado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    registrado_por INTEGER,
    resuelto_en TEXT,
    FOREIGN KEY (registrado_por) REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE SET NULL
);

INSERT OR IGNORE INTO permisos(codigo, nombre, descripcion, modulo) VALUES
('usuarios.restablecer_contrasena', 'Restablecer contrasena de usuarios operativos', 'Permite restablecer la contrasena de usuarios operativos normales.', 'Usuarios'),
('usuarios.desbloquear', 'Desbloquear usuarios operativos', 'Permite desbloquear usuarios operativos normales.', 'Usuarios'),
('mantenimiento.ver', 'Ver modulo de mantenimiento', 'Permite acceder al modulo tecnico de mantenimiento.', 'Mantenimiento'),
('mantenimiento.gestionar', 'Gestionar modulo de mantenimiento', 'Permite ejecutar tareas de mantenimiento.', 'Mantenimiento'),
('seguridad.ver_logs', 'Ver logs del sistema', 'Permite consultar eventos tecnicos y logs del sistema.', 'Seguridad'),
('seguridad.generar_respaldo', 'Generar respaldo', 'Permite crear respaldos manuales de la base de datos.', 'Seguridad'),
('seguridad.restaurar_respaldo', 'Restaurar respaldo', 'Permite restaurar respaldos del sistema.', 'Seguridad'),
('seguridad.configuracion_sensible', 'Gestionar configuracion sensible', 'Permite modificar configuraciones sensibles o tecnicas.', 'Seguridad');

DELETE FROM roles_permisos WHERE rol_id = 2;
INSERT OR IGNORE INTO roles_permisos(rol_id, permiso_id)
SELECT 2, id FROM permisos
WHERE codigo IN (
    'dashboard.ver',
    'abonados.gestionar',
    'casas.gestionar',
    'pagos.registrar',
    'pagos.anular',
    'planes_pago.gestionar',
    'morosidad.ver',
    'reportes.generar',
    'usuarios.gestionar',
    'usuarios.restablecer_contrasena',
    'usuarios.desbloquear',
    'configuracion.gestionar'
);

INSERT OR IGNORE INTO roles_permisos(rol_id, permiso_id)
SELECT 1, id FROM permisos;

INSERT OR IGNORE INTO usuarios(
    nombre_usuario,
    nombre_completo,
    correo,
    contrasena_hash,
    estado,
    es_tecnico,
    es_oculto,
    requiere_cambio_contrasena,
    observaciones
) VALUES (
    'superadmin',
    'Superadministrador Tecnico',
    'superadmin@sicap.local',
    'CAMBIAR_HASH_EN_DESARROLLO',
    'ACTIVO',
    1,
    1,
    1,
    'Usuario tecnico de emergencia y mantenimiento. No visible para administradores normales.'
);

UPDATE usuarios
SET
    es_tecnico = 1,
    es_oculto = 1,
    requiere_cambio_contrasena = CASE
        WHEN lower(nombre_usuario) = 'superadmin' THEN 1
        ELSE requiere_cambio_contrasena
    END,
    observaciones = COALESCE(
        observaciones,
        'Usuario tecnico de emergencia y mantenimiento. No visible para administradores normales.'
    )
WHERE lower(nombre_usuario) = 'superadmin';

UPDATE usuarios
SET
    es_tecnico = 0,
    es_oculto = 0,
    requiere_cambio_contrasena = 1,
    observaciones = COALESCE(
        observaciones,
        'Usuario administrativo inicial. Cambiar contrasena antes de uso productivo.'
    )
WHERE lower(nombre_usuario) = 'admin';

INSERT OR IGNORE INTO usuarios_roles(usuario_id, rol_id)
SELECT id, 1 FROM usuarios WHERE lower(nombre_usuario) = 'superadmin';

INSERT OR IGNORE INTO usuarios_roles(usuario_id, rol_id)
SELECT id, 2 FROM usuarios WHERE lower(nombre_usuario) = 'admin';

DELETE FROM usuarios_roles
WHERE rol_id = 1
  AND usuario_id IN (
      SELECT id FROM usuarios WHERE lower(nombre_usuario) = 'admin'
  );

INSERT OR IGNORE INTO configuracion_sistema(clave, valor, tipo_dato, categoria, descripcion, editable) VALUES
('mantenimiento.ruta_respaldos', './respaldos', 'TEXTO', 'Mantenimiento', 'Ruta local sugerida para almacenar respaldos.', 1),
('mantenimiento.dias_retencion_respaldos', '30', 'ENTERO', 'Mantenimiento', 'Cantidad sugerida de dias para conservar respaldos.', 1);

UPDATE configuracion_sistema
SET valor = '2.1.0',
    actualizado_en = datetime('now', 'localtime')
WHERE clave = 'sistema.version';

DROP VIEW IF EXISTS vw_usuarios_operativos;
CREATE VIEW vw_usuarios_operativos AS
SELECT
    u.id,
    u.nombre_usuario,
    u.nombre_completo,
    u.correo,
    u.estado,
    u.requiere_cambio_contrasena,
    u.intentos_fallidos,
    u.bloqueado_hasta,
    u.ultimo_acceso_en,
    u.creado_en,
    GROUP_CONCAT(r.nombre, ', ') AS roles
FROM usuarios u
LEFT JOIN usuarios_roles ur ON ur.usuario_id = u.id
LEFT JOIN roles r ON r.id = ur.rol_id
WHERE u.eliminado_en IS NULL
  AND u.es_oculto = 0
  AND u.es_tecnico = 0
GROUP BY
    u.id,
    u.nombre_usuario,
    u.nombre_completo,
    u.correo,
    u.estado,
    u.requiere_cambio_contrasena,
    u.intentos_fallidos,
    u.bloqueado_hasta,
    u.ultimo_acceso_en,
    u.creado_en;

DROP VIEW IF EXISTS vw_usuarios_tecnicos;
CREATE VIEW vw_usuarios_tecnicos AS
SELECT
    u.id,
    u.nombre_usuario,
    u.nombre_completo,
    u.correo,
    u.estado,
    u.ultimo_acceso_en,
    u.creado_en,
    GROUP_CONCAT(r.nombre, ', ') AS roles
FROM usuarios u
LEFT JOIN usuarios_roles ur ON ur.usuario_id = u.id
LEFT JOIN roles r ON r.id = ur.rol_id
WHERE u.eliminado_en IS NULL
  AND (u.es_oculto = 1 OR u.es_tecnico = 1)
GROUP BY
    u.id,
    u.nombre_usuario,
    u.nombre_completo,
    u.correo,
    u.estado,
    u.ultimo_acceso_en,
    u.creado_en;

DROP VIEW IF EXISTS vw_usuarios_restablecibles_por_admin;
CREATE VIEW vw_usuarios_restablecibles_por_admin AS
SELECT *
FROM vw_usuarios_operativos;

CREATE INDEX IF NOT EXISTS idx_usuarios_tecnico_oculto ON usuarios(es_tecnico, es_oculto, estado);
CREATE INDEX IF NOT EXISTS idx_historial_respaldos_generado_en ON historial_respaldos(generado_en);
CREATE INDEX IF NOT EXISTS idx_historial_respaldos_generado_por ON historial_respaldos(generado_por, generado_en);
CREATE INDEX IF NOT EXISTS idx_eventos_tecnicos_categoria_fecha ON eventos_tecnicos(categoria, registrado_en);
CREATE INDEX IF NOT EXISTS idx_eventos_tecnicos_severidad_fecha ON eventos_tecnicos(severidad, registrado_en);
CREATE INDEX IF NOT EXISTS idx_auditoria_usuario_fecha ON auditoria(usuario_id, fecha_evento);
CREATE INDEX IF NOT EXISTS idx_auditoria_accion_fecha ON auditoria(accion, fecha_evento);

CREATE TRIGGER IF NOT EXISTS trg_bloquear_actualizacion_usuario_tecnico_por_no_superadmin
BEFORE UPDATE ON usuarios
FOR EACH ROW
WHEN OLD.es_tecnico = 1
  AND NEW.actualizado_por IS NOT NULL
  AND NOT EXISTS (
      SELECT 1
      FROM usuarios_roles ur
      JOIN roles r ON r.id = ur.rol_id
      WHERE ur.usuario_id = NEW.actualizado_por
        AND r.nombre = 'SUPERADMINISTRADOR'
  )
BEGIN
    SELECT RAISE(ABORT, 'Solo SUPERADMINISTRADOR puede modificar usuarios tecnicos.');
END;

CREATE TRIGGER IF NOT EXISTS trg_auditoria_restablecimiento_contrasena
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
    '003',
    'Esquema incremental de seguridad con superadministrador tecnico, mantenimiento y restablecimiento local',
    NULL
);

COMMIT;

PRAGMA foreign_keys = ON;

