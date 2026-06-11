-- SIGQUA - Esquema inicial consolidado
-- Version: 001
-- Esquema final, catalogos esenciales, configuracion y usuario administrador.
PRAGMA foreign_keys = OFF;

CREATE TABLE abonados (
    id INTEGER PRIMARY KEY,
    dni TEXT NOT NULL UNIQUE,
    nombre_completo TEXT NOT NULL,
    telefono TEXT,
    barrio_id INTEGER NOT NULL,
    direccion_referencia TEXT,
    observaciones TEXT,
    estado TEXT NOT NULL DEFAULT 'ACTIVO' CHECK (estado IN ('ACTIVO', 'INACTIVO')),
    fecha_alta TEXT NOT NULL DEFAULT (date('now', 'localtime')),
    creado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    actualizado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    eliminado_en TEXT,
    FOREIGN KEY (barrio_id) REFERENCES barrios(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    CHECK (length(trim(dni)) >= 8)
);
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
CREATE TABLE barrios (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL UNIQUE COLLATE NOCASE,
    estado TEXT NOT NULL DEFAULT 'ACTIVO' CHECK (estado IN ('ACTIVO', 'INACTIVO')),
    observaciones TEXT,
    creado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    actualizado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    eliminado_en TEXT
);
CREATE TABLE cargos (
    id INTEGER PRIMARY KEY,
    casa_id INTEGER NOT NULL,
    abonado_id INTEGER NOT NULL,
    periodo_id INTEGER,
    concepto_id INTEGER NOT NULL,
    descripcion TEXT NOT NULL,
    monto_centavos INTEGER NOT NULL CHECK (monto_centavos >= 0),
    saldo_pendiente_centavos INTEGER NOT NULL CHECK (saldo_pendiente_centavos >= 0),
    fecha_generacion TEXT NOT NULL DEFAULT (date('now', 'localtime')),
    fecha_vencimiento TEXT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'PENDIENTE' CHECK (estado IN ('PENDIENTE', 'PARCIAL', 'PAGADO', 'ANULADO', 'VENCIDO')),
    origen TEXT NOT NULL DEFAULT 'MANUAL' CHECK (origen IN ('MENSUAL', 'PAGO', 'PLAN_PAGO', 'PROCESO_SERVICIO', 'ADELANTO', 'MANUAL')),
    creado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    actualizado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    anulado_en TEXT,
    anulado_por INTEGER,
    motivo_anulacion TEXT, proceso_servicio_id INTEGER REFERENCES procesos_servicio(id) ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (casa_id) REFERENCES casas(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (abonado_id) REFERENCES abonados(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (periodo_id) REFERENCES periodos_cobro(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (concepto_id) REFERENCES conceptos_cobro(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (anulado_por) REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE SET NULL,
    CHECK (saldo_pendiente_centavos <= monto_centavos),
    UNIQUE (casa_id, periodo_id, concepto_id)
);
CREATE TABLE "casas" (
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
    eliminado_en TEXT, estado_aviso_cobro TEXT NOT NULL DEFAULT 'SIN_AVISO'
    CHECK (estado_aviso_cobro IN (
        'SIN_AVISO',
        'PRIMER_AVISO',
        'SEGUNDO_AVISO',
        'TERCER_AVISO',
        'LISTO_PARA_CORTE',
        'CORTADO'
    )), fecha_ultimo_aviso TEXT, usuario_ultimo_aviso_id INTEGER, observacion_ultimo_aviso TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (abonado_id) REFERENCES abonados(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (barrio_id) REFERENCES barrios(id) ON UPDATE CASCADE ON DELETE RESTRICT
);
CREATE TABLE "comprobantes" (
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
CREATE TABLE comprobantes_impresiones (
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
CREATE TABLE conceptos_cobro (
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
    creado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
INSERT INTO "conceptos_cobro" VALUES(1,'SERVICIO_MENSUAL','Servicio mensual de agua','SERVICIO_MENSUAL',1,NULL,'ACTIVO','2026-06-09 15:07:37');
INSERT INTO "conceptos_cobro" VALUES(2,'MORA','Mora opcional','MORA',1,0,'ACTIVO','2026-06-09 15:07:37');
INSERT INTO "conceptos_cobro" VALUES(3,'MULTA','Multa configurable','MULTA',0,NULL,'INACTIVO','2026-06-09 15:07:37');
INSERT INTO "conceptos_cobro" VALUES(4,'RECONEXION','Reconexion con monto definido en pago','RECONEXION',0,NULL,'ACTIVO','2026-06-09 15:07:37');
INSERT INTO "conceptos_cobro" VALUES(5,'PRIMA','Prima inicial','PRIMA',0,NULL,'ACTIVO','2026-06-09 15:07:37');
INSERT INTO "conceptos_cobro" VALUES(6,'CUOTA_PLAN_PAGO','Cuota de plan de pago','CUOTA_PLAN_PAGO',1,NULL,'ACTIVO','2026-06-09 15:07:37');
INSERT INTO "conceptos_cobro" VALUES(7,'AJUSTE','Ajuste administrativo','AJUSTE',0,NULL,'ACTIVO','2026-06-09 15:07:37');
INSERT INTO "conceptos_cobro" VALUES(8,'PAGO_ADELANTADO','Pago adelantado','PAGO_ADELANTADO',1,NULL,'ACTIVO','2026-06-09 15:07:37');
INSERT INTO "conceptos_cobro" VALUES(9,'CONEXION','Conexion financiable segun caso operativo','OTRO',0,NULL,'ACTIVO','2026-06-09 15:07:37');
INSERT INTO "conceptos_cobro" VALUES(10,'ABONO_EXTRAORDINARIO','Abono extraordinario a plan de pago','OTRO',0,NULL,'ACTIVO','2026-06-09 15:07:38');
INSERT INTO "conceptos_cobro" VALUES(11,'MENSUALIDAD_PRORRATEADA','Mensualidad prorrateada por activacion','SERVICIO_MENSUAL',1,NULL,'ACTIVO','2026-06-09 15:07:38');
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
INSERT INTO "configuracion_sistema" VALUES(1,'sistema.nombre','SIGQUA','TEXTO','Sistema','Nombre del sistema.',0,'2026-06-09 15:07:37',NULL);
INSERT INTO "configuracion_sistema" VALUES(2,'sistema.version','2.2.0','TEXTO','Sistema','Version del esquema actualizado.',0,'2026-06-09 15:07:37',NULL);
INSERT INTO "configuracion_sistema" VALUES(3,'sistema.respaldo_automatico','1','BOOLEANO','Sistema','Respaldo automatico obligatorio al cerrar sesion o salir del sistema.',0,'2026-06-09 15:07:37',NULL);
INSERT INTO "configuracion_sistema" VALUES(4,'junta.nombre','Junta de Agua de Yarumela','TEXTO','Junta','Nombre de la Junta.',1,'2026-06-09 15:07:37',NULL);
INSERT INTO "configuracion_sistema" VALUES(5,'junta.telefono','','TEXTO','Junta','Telefono de contacto.',1,'2026-06-09 15:07:37',NULL);
INSERT INTO "configuracion_sistema" VALUES(6,'junta.correo','','TEXTO','Junta','Correo de contacto.',1,'2026-06-09 15:07:37',NULL);
INSERT INTO "configuracion_sistema" VALUES(7,'junta.direccion','Yarumela, La Paz','TEXTO','Junta','Direccion de la Junta.',1,'2026-06-09 15:07:37',NULL);
INSERT INTO "configuracion_sistema" VALUES(8,'cobro.precio_mensual_centavos','35000','ENTERO','Cobro','Precio mensual global del servicio de agua.',1,'2026-06-09 15:07:37',NULL);
INSERT INTO "configuracion_sistema" VALUES(9,'cobro.multa_activa','1','BOOLEANO','Cobro','Permite activar o desactivar multa.',1,'2026-06-09 15:07:37',NULL);
INSERT INTO "configuracion_sistema" VALUES(10,'cobro.multa_monto_centavos','0','ENTERO','Cobro','Monto global de multa en centavos.',1,'2026-06-09 15:07:37',NULL);
INSERT INTO "configuracion_sistema" VALUES(11,'cobro.mora_activa','1','BOOLEANO','Cobro','La mora forma parte del sistema como meses vencidos no pagados y no se desactiva desde configuracion.',0,'2026-06-09 15:07:37',NULL);
INSERT INTO "configuracion_sistema" VALUES(12,'cobro.mora_monto_centavos','0','ENTERO','Cobro','Clave heredada. No representa un recargo automatico y no debe usarse para parametrizar mora.',0,'2026-06-09 15:07:37',NULL);
INSERT INTO "configuracion_sistema" VALUES(13,'cobro.meses_para_corte','5','ENTERO','Cobro','Cantidad de meses de deuda para destacar o cortar.',1,'2026-06-09 15:07:37',NULL);
INSERT INTO "configuracion_sistema" VALUES(14,'cobro.permitir_pago_adelantado','1','BOOLEANO','Cobro','Permite registrar pagos adelantados.',1,'2026-06-09 15:07:37',NULL);
INSERT INTO "configuracion_sistema" VALUES(15,'cobro.meses_adelanto_maximo','12','ENTERO','Cobro','Maximo de meses adelantados permitidos.',1,'2026-06-09 15:07:37',NULL);
INSERT INTO "configuracion_sistema" VALUES(16,'factura.texto_pie','Gracias por su pago.','TEXTO','Factura','Texto de pie para comprobantes.',1,'2026-06-09 15:07:37',NULL);
INSERT INTO "configuracion_sistema" VALUES(20,'cobro.multa_mora_automatica_activa','0','BOOLEANO','Cobro','Activa el recargo automatico adicional por cada mes vencido.',1,'2026-06-09 15:07:37',NULL);
INSERT INTO "configuracion_sistema" VALUES(21,'cobro.multa_mora_automatica_centavos','0','ENTERO','Cobro','Monto adicional por cada mes vencido cuando la multa automatica esta activa.',1,'2026-06-09 15:07:37',NULL);
INSERT INTO "configuracion_sistema" VALUES(22,'cobro.corte_automatico_activo','0','BOOLEANO','Cobro','Permite habilitar o deshabilitar el corte automatico por deuda segun las reglas operativas vigentes.',1,'2026-06-09 15:07:37',NULL);
INSERT INTO "configuracion_sistema" VALUES(23,'factura.titulo_documento','RECIBO DE PAGO','TEXTO','Factura','Titulo principal del recibo de pago.',1,'2026-06-09 15:07:38',NULL);
INSERT INTO "configuracion_sistema" VALUES(24,'factura.subtitulo_documento','','TEXTO','Factura','Subtitulo opcional del recibo de pago.',1,'2026-06-09 15:07:38',NULL);
INSERT INTO "configuracion_sistema" VALUES(25,'factura.texto_legal_superior','','TEXTO','Factura','Texto legal corto mostrado antes del detalle del recibo.',1,'2026-06-09 15:07:38',NULL);
INSERT INTO "configuracion_sistema" VALUES(26,'factura.texto_legal_inferior','','TEXTO','Factura','Texto legal corto mostrado despues del pie del recibo.',1,'2026-06-09 15:07:38',NULL);
INSERT INTO "configuracion_sistema" VALUES(27,'factura.etiqueta_copia','ORIGINAL','TEXTO','Factura','Etiqueta de copia mostrada en el recibo.',1,'2026-06-09 15:07:38',NULL);
INSERT INTO "configuracion_sistema" VALUES(28,'factura.mostrar_correo','1','BOOLEANO','Factura','Permite mostrar el correo institucional en el recibo.',1,'2026-06-09 15:07:38',NULL);
INSERT INTO "configuracion_sistema" VALUES(29,'factura.mostrar_telefono','1','BOOLEANO','Factura','Permite mostrar el telefono institucional en el recibo.',1,'2026-06-09 15:07:38',NULL);
INSERT INTO "configuracion_sistema" VALUES(30,'factura.mostrar_direccion','1','BOOLEANO','Factura','Permite mostrar la direccion institucional en el recibo.',1,'2026-06-09 15:07:38',NULL);
INSERT INTO "configuracion_sistema" VALUES(31,'factura.mostrar_identificador_fiscal','0','BOOLEANO','Factura','Permite mostrar el identificador fiscal institucional en el recibo.',1,'2026-06-09 15:07:38',NULL);
INSERT INTO "configuracion_sistema" VALUES(32,'junta.identificador_fiscal','','TEXTO','Junta','Identificador fiscal o RTN institucional.',1,'2026-06-09 15:07:38',NULL);
INSERT INTO "configuracion_sistema" VALUES(33,'junta.sitio_web','','TEXTO','Junta','Sitio web institucional.',1,'2026-06-09 15:07:38',NULL);
INSERT INTO "configuracion_sistema" VALUES(34,'junta.mensaje_contacto','','TEXTO','Junta','Mensaje institucional corto para contacto o soporte.',1,'2026-06-09 15:07:38',NULL);
INSERT INTO "configuracion_sistema" VALUES(35,'cobro.mora_leve_hasta_meses','2','ENTERO','Cobro','Cantidad maxima de meses para clasificar una mora leve en la interfaz.',1,'2026-06-09 15:07:38',NULL);
INSERT INTO "configuracion_sistema" VALUES(36,'cobro.mora_media_hasta_meses','5','ENTERO','Cobro','Cantidad maxima de meses para clasificar una mora media en la interfaz.',1,'2026-06-09 15:07:38',NULL);
INSERT INTO "configuracion_sistema" VALUES(37,'documentos.firma_habilitada','0','BOOLEANO','Documentos','Controla si los documentos operativos muestran la linea de firma.',1,'2026-06-09 15:07:38',NULL);
INSERT INTO "configuracion_sistema" VALUES(38,'empresa.nombre','Junta de Agua de Yarumela','TEXTO','Empresa','Nombre legal o comercial visible en documentos y cabeceras.',1,'2026-06-09 15:07:38',NULL);
INSERT INTO "configuracion_sistema" VALUES(39,'empresa.telefono','','TEXTO','Empresa','Telefono institucional visible en documentos y cabeceras.',1,'2026-06-09 15:07:38',NULL);
INSERT INTO "configuracion_sistema" VALUES(40,'empresa.correo','','TEXTO','Empresa','Correo institucional visible en documentos y cabeceras.',1,'2026-06-09 15:07:38',NULL);
INSERT INTO "configuracion_sistema" VALUES(41,'empresa.direccion','Yarumela, La Paz','TEXTO','Empresa','Direccion fiscal u operativa visible en documentos y cabeceras.',1,'2026-06-09 15:07:38',NULL);
INSERT INTO "configuracion_sistema" VALUES(42,'empresa.identificador_fiscal','','TEXTO','Empresa','Identificador fiscal visible en documentos y cabeceras.',1,'2026-06-09 15:07:38',NULL);
INSERT INTO "configuracion_sistema" VALUES(43,'empresa.sitio_web','','TEXTO','Empresa','Sitio web institucional visible en documentos y cabeceras.',1,'2026-06-09 15:07:38',NULL);
INSERT INTO "configuracion_sistema" VALUES(44,'empresa.mensaje_contacto','','TEXTO','Empresa','Mensaje de contacto institucional para documentos y cabeceras.',1,'2026-06-09 15:07:38',NULL);
INSERT INTO "configuracion_sistema" VALUES(45,'seguridad.duracion_sesion_horas','8','DECIMAL','Seguridad','Duracion del cierre automatico de sesion en horas.',1,'2026-06-09 15:07:38',NULL);
INSERT INTO "configuracion_sistema" VALUES(46,'respaldo.ruta_principal','./respaldos','TEXTO','Respaldo','Carpeta principal donde SIGQUA genera los respaldos locales.',1,'2026-06-09 15:07:38',NULL);
INSERT INTO "configuracion_sistema" VALUES(47,'respaldo.ruta_secundaria','','TEXTO','Respaldo','Carpeta secundaria opcional para copia adicional de respaldos.',1,'2026-06-09 15:07:38',NULL);
INSERT INTO "configuracion_sistema" VALUES(48,'respaldo.secundaria_activa','0','BOOLEANO','Respaldo','Indica si SIGQUA debe guardar una copia secundaria del respaldo.',1,'2026-06-09 15:07:38',NULL);
INSERT INTO "configuracion_sistema" VALUES(49,'respaldo.comprimir_zip','1','BOOLEANO','Respaldo','Indica si el respaldo debe comprimirse como ZIP.',1,'2026-06-09 15:07:38',NULL);
INSERT INTO "configuracion_sistema" VALUES(50,'respaldo.organizar_por_periodo','1','BOOLEANO','Respaldo','Organiza respaldos por carpetas de año y mes.',1,'2026-06-09 15:07:38',NULL);
INSERT INTO "configuracion_sistema" VALUES(51,'respaldo.retencion_dias','30','ENTERO','Respaldo','Cantidad de dias a conservar respaldos gestionados por SIGQUA.',1,'2026-06-09 15:07:38',NULL);
INSERT INTO "configuracion_sistema" VALUES(54,'cobro.cobrar_mensualidad_prorrateada_activacion','0','BOOLEANO','Cobro','Controla si conexion y reconexion agregan la primera mensualidad prorrateada al momento de activar el servicio.',1,'2026-06-09 15:07:38',NULL);
INSERT INTO "configuracion_sistema" VALUES(62,'documentos.firma_texto_linea','Firma autorizada','TEXTO','Documentos','Texto bajo la linea de firma impresa.',1,'2026-06-09 15:07:38',NULL);
INSERT INTO "configuracion_sistema" VALUES(63,'impresion_termica.nombre_impresora','','TEXTO','Comprobantes','Nombre de la impresora termica instalada en Windows.',1,'2026-06-09 15:07:38',NULL);
INSERT INTO "configuracion_sistema" VALUES(64,'impresion_termica.ancho_papel_mm','80','ENTERO','Comprobantes','Ancho del papel termico en milimetros.',1,'2026-06-09 15:07:38',NULL);
INSERT INTO "configuracion_sistema" VALUES(65,'impresion_termica.corte_automatico','1','BOOLEANO','Comprobantes','Corta el papel al finalizar cada comprobante.',1,'2026-06-09 15:07:38',NULL);
INSERT INTO "configuracion_sistema" VALUES(66,'impresion_termica.codigo_pagina','cp850','TEXTO','Comprobantes','Codigo de pagina usado para texto ESC/POS.',1,'2026-06-09 15:07:38',NULL);
INSERT INTO "configuracion_sistema" VALUES(67,'impresion_reportes.nombre_impresora','','TEXTO','Reportes','Nombre de la impresora predeterminada para reportes PDF en carta.',1,'2026-06-09 15:07:38',NULL);
INSERT INTO "configuracion_sistema" VALUES(68,'reportes.ruta_salida','','TEXTO','Reportes PDF','Carpeta configurada para guardar reportes PDF. Vacia usa Descargas/SIGQUA Reportes.',1,'2026-06-09 15:07:38',NULL);
INSERT INTO "configuracion_sistema" VALUES(69,'reportes.abrir_automaticamente','1','BOOLEANO','Reportes PDF','Abre el reporte despues de generarlo.',1,'2026-06-09 15:07:38',NULL);
INSERT INTO "configuracion_sistema" VALUES(70,'reportes.firma_habilitada','0','BOOLEANO','Reportes PDF','Muestra una linea de firma en reportes administrativos.',1,'2026-06-09 15:07:38',NULL);
INSERT INTO "configuracion_sistema" VALUES(71,'reportes.firma_texto_linea','Firma autorizada','TEXTO','Reportes PDF','Texto mostrado bajo la linea de firma del reporte.',1,'2026-06-09 15:07:38',NULL);
CREATE TABLE correlativos_comprobantes (
    clave TEXT PRIMARY KEY,
    ultimo_numero INTEGER NOT NULL DEFAULT 0 CHECK (ultimo_numero >= 0),
    actualizado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
INSERT INTO "correlativos_comprobantes" VALUES('RECIBO_GLOBAL',0,'2026-06-09 15:07:38');
CREATE TABLE cuotas_plan_pago (
    id INTEGER PRIMARY KEY,
    plan_pago_id INTEGER NOT NULL,
    numero_cuota INTEGER NOT NULL CHECK (numero_cuota >= 1),
    fecha_vencimiento TEXT NOT NULL,
    monto_centavos INTEGER NOT NULL CHECK (monto_centavos >= 0),
    saldo_pendiente_centavos INTEGER NOT NULL CHECK (saldo_pendiente_centavos >= 0),
    estado TEXT NOT NULL DEFAULT 'PENDIENTE' CHECK (estado IN ('PENDIENTE', 'PARCIAL', 'PAGADO', 'VENCIDO', 'ANULADO')),
    cargo_id INTEGER,
    creado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    actualizado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (plan_pago_id) REFERENCES planes_pago(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (cargo_id) REFERENCES cargos(id) ON UPDATE CASCADE ON DELETE SET NULL,
    CHECK (saldo_pendiente_centavos <= monto_centavos),
    UNIQUE (plan_pago_id, numero_cuota)
);
CREATE TABLE esquema_migraciones (
    id INTEGER PRIMARY KEY,
    version TEXT NOT NULL UNIQUE,
    descripcion TEXT NOT NULL,
    aplicado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    checksum TEXT
);
INSERT INTO "esquema_migraciones" VALUES(1,'001','Esquema inicial consolidado y limpio de SIGQUA','2026-06-09 15:10:27',NULL);
CREATE TABLE eventos_tecnicos (
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
CREATE TABLE historial_propietarios_casa (
    id INTEGER PRIMARY KEY,
    casa_id INTEGER NOT NULL,
    abonado_anterior_id INTEGER,
    abonado_nuevo_id INTEGER NOT NULL,
    fecha_cambio TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    motivo TEXT,
    usuario_id INTEGER,
    creado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')), observacion TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (casa_id) REFERENCES casas(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (abonado_anterior_id) REFERENCES abonados(id) ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (abonado_nuevo_id) REFERENCES abonados(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE SET NULL
);
CREATE TABLE historial_respaldos (
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
CREATE TABLE metodos_pago (
    id INTEGER PRIMARY KEY,
    codigo TEXT NOT NULL UNIQUE COLLATE NOCASE,
    nombre TEXT NOT NULL,
    descripcion TEXT,
    estado TEXT NOT NULL DEFAULT 'ACTIVO' CHECK (estado IN ('ACTIVO', 'INACTIVO')),
    creado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
, requiere_referencia INTEGER NOT NULL DEFAULT 0
CHECK (requiere_referencia IN (0, 1)));
INSERT INTO "metodos_pago" VALUES(1,'EFECTIVO','Efectivo','Pago recibido en efectivo.','ACTIVO','2026-06-09 15:07:37',0);
INSERT INTO "metodos_pago" VALUES(2,'TRANSFERENCIA','Transferencia','Pago por transferencia bancaria.','ACTIVO','2026-06-09 15:07:37',1);
INSERT INTO "metodos_pago" VALUES(3,'TARJETA','Tarjeta','Pago por tarjeta de debito o credito.','ACTIVO','2026-06-09 15:07:37',0);
INSERT INTO "metodos_pago" VALUES(4,'OTRO','Otro','Otro metodo de pago autorizado.','ACTIVO','2026-06-09 15:07:37',0);
INSERT INTO "metodos_pago" VALUES(5,'DEPOSITO','Deposito','Pago por deposito bancario.','ACTIVO','2026-06-09 15:07:38',1);
CREATE TABLE operaciones_cobro (
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
CREATE TABLE pagos (
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
    fecha_pago TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    estado TEXT NOT NULL DEFAULT 'CONFIRMADO' CHECK (estado IN ('CONFIRMADO', 'ANULADO')),
    observaciones TEXT,
    anulado_en TEXT,
    anulado_por INTEGER,
    motivo_anulacion TEXT,
    creado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    actualizado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')), tipo_pago TEXT NOT NULL DEFAULT 'MENSUALIDAD'
CHECK (tipo_pago IN ('MENSUALIDAD', 'PLAN_PAGO', 'CONEXION', 'RECONEXION')), plan_pago_id INTEGER, operacion_cobro_id INTEGER,
    FOREIGN KEY (abonado_id) REFERENCES abonados(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (casa_id) REFERENCES casas(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (usuario_cobrador_id) REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (metodo_pago_id) REFERENCES metodos_pago(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (anulado_por) REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE SET NULL
);
CREATE TABLE pagos_adelantados (
    id INTEGER PRIMARY KEY,
    abonado_id INTEGER NOT NULL,
    casa_id INTEGER NOT NULL,
    pago_id INTEGER NOT NULL,
    periodo_id INTEGER NOT NULL,
    monto_centavos INTEGER NOT NULL CHECK (monto_centavos >= 0),
    creado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    observaciones TEXT,
    FOREIGN KEY (abonado_id) REFERENCES abonados(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (casa_id) REFERENCES casas(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (pago_id) REFERENCES pagos(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (periodo_id) REFERENCES periodos_cobro(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    UNIQUE (casa_id, periodo_id, pago_id)
);
CREATE TABLE pagos_detalle (
    id INTEGER PRIMARY KEY,
    pago_id INTEGER NOT NULL,
    casa_id INTEGER NOT NULL,
    cargo_id INTEGER,
    concepto_id INTEGER NOT NULL,
    descripcion TEXT NOT NULL,
    monto_pagado_centavos INTEGER NOT NULL CHECK (monto_pagado_centavos >= 0),
    periodo_id INTEGER,
    orden_aplicacion INTEGER NOT NULL DEFAULT 1 CHECK (orden_aplicacion >= 1),
    creado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')), cuota_plan_pago_id INTEGER,
    FOREIGN KEY (pago_id) REFERENCES pagos(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (casa_id) REFERENCES casas(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (cargo_id) REFERENCES cargos(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (concepto_id) REFERENCES conceptos_cobro(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (periodo_id) REFERENCES periodos_cobro(id) ON UPDATE CASCADE ON DELETE RESTRICT
);
CREATE TABLE periodos_cobro (
    id INTEGER PRIMARY KEY,
    anio INTEGER NOT NULL CHECK (anio BETWEEN 2000 AND 2100),
    mes INTEGER NOT NULL CHECK (mes BETWEEN 1 AND 12),
    nombre TEXT NOT NULL,
    fecha_inicio TEXT NOT NULL,
    fecha_fin TEXT NOT NULL,
    fecha_vencimiento TEXT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'ABIERTO' CHECK (estado IN ('ABIERTO', 'CERRADO')),
    creado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    UNIQUE (anio, mes),
    CHECK (fecha_fin >= fecha_inicio),
    CHECK (fecha_vencimiento >= fecha_inicio)
);
CREATE TABLE permisos (
    id INTEGER PRIMARY KEY,
    codigo TEXT NOT NULL UNIQUE COLLATE NOCASE,
    nombre TEXT NOT NULL,
    descripcion TEXT,
    modulo TEXT NOT NULL,
    creado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
INSERT INTO "permisos" VALUES(1,'dashboard.ver','Ver dashboard','Permite visualizar el panel principal.','Dashboard','2026-06-09 15:07:37');
INSERT INTO "permisos" VALUES(2,'abonados.gestionar','Gestionar abonados','Permite crear, editar y consultar abonados.','Abonados','2026-06-09 15:07:37');
INSERT INTO "permisos" VALUES(3,'casas.gestionar','Gestionar casas','Permite crear, editar y consultar casas.','Casas','2026-06-09 15:07:37');
INSERT INTO "permisos" VALUES(4,'pagos.registrar','Registrar pagos','Permite registrar pagos.','Pagos','2026-06-09 15:07:37');
INSERT INTO "permisos" VALUES(5,'pagos.anular','Anular pagos','Permite anular pagos conservando auditoria.','Pagos','2026-06-09 15:07:37');
INSERT INTO "permisos" VALUES(6,'planes_pago.gestionar','Gestionar planes de pago','Permite crear y consultar planes de pago.','Planes de pago','2026-06-09 15:07:37');
INSERT INTO "permisos" VALUES(7,'morosidad.ver','Ver deuda y morosidad','Permite consultar cuentas con deuda.','Morosidad','2026-06-09 15:07:37');
INSERT INTO "permisos" VALUES(8,'reportes.generar','Generar reportes','Permite emitir reportes.','Reportes','2026-06-09 15:07:37');
INSERT INTO "permisos" VALUES(9,'usuarios.gestionar','Gestionar usuarios','Permite administrar usuarios, roles y permisos.','Usuarios','2026-06-09 15:07:37');
INSERT INTO "permisos" VALUES(10,'configuracion.gestionar','Gestionar configuracion','Permite modificar parametros del sistema.','Configuracion','2026-06-09 15:07:37');
INSERT INTO "permisos" VALUES(11,'usuarios.restablecer_contrasena','Restablecer contrasena de usuarios operativos','Permite restablecer la contrasena de usuarios operativos normales.','Usuarios','2026-06-09 15:07:37');
INSERT INTO "permisos" VALUES(12,'usuarios.desbloquear','Desbloquear usuarios operativos','Permite desbloquear usuarios operativos normales.','Usuarios','2026-06-09 15:07:37');
INSERT INTO "permisos" VALUES(19,'modulo.dashboard','Acceso a Inicio','Permite acceder al modulo Inicio.','Inicio','2026-06-09 15:07:38');
INSERT INTO "permisos" VALUES(20,'modulo.barrios','Acceso a Barrios','Permite acceder al modulo Barrios.','Barrios','2026-06-09 15:07:38');
INSERT INTO "permisos" VALUES(21,'modulo.abonados','Acceso a Abonados','Permite acceder al modulo Abonados.','Abonados','2026-06-09 15:07:38');
INSERT INTO "permisos" VALUES(22,'modulo.casas','Acceso a Casas','Permite acceder al modulo Casas.','Casas','2026-06-09 15:07:38');
INSERT INTO "permisos" VALUES(23,'modulo.pagos','Acceso a Pagos','Permite acceder al modulo Pagos.','Pagos','2026-06-09 15:07:38');
INSERT INTO "permisos" VALUES(24,'modulo.historial_pagos','Acceso a Historial de pagos','Permite acceder al modulo Historial de pagos.','Historial de pagos','2026-06-09 15:07:38');
INSERT INTO "permisos" VALUES(25,'modulo.morosidad','Acceso a Morosidad','Permite acceder al modulo Morosidad.','Morosidad','2026-06-09 15:07:38');
INSERT INTO "permisos" VALUES(26,'modulo.planes_pago','Acceso a Planes de pago','Permite acceder al modulo Planes de pago.','Planes de pago','2026-06-09 15:07:38');
INSERT INTO "permisos" VALUES(27,'modulo.usuarios','Acceso a Usuarios','Permite acceder al modulo Usuarios.','Usuarios','2026-06-09 15:07:38');
INSERT INTO "permisos" VALUES(28,'modulo.reportes','Acceso a Reportes','Permite acceder al modulo Reportes.','Reportes','2026-06-09 15:07:38');
INSERT INTO "permisos" VALUES(29,'modulo.configuracion','Acceso a Configuracion','Permite acceder al modulo Configuracion.','Configuracion','2026-06-09 15:07:38');
CREATE TABLE planes_pago (
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
    creado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    actualizado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    creado_por INTEGER, tipo_plan TEXT NOT NULL DEFAULT 'MESES_PENDIENTES', concepto_financiado TEXT NOT NULL DEFAULT 'MESES_PENDIENTES', prima_centavos INTEGER NOT NULL DEFAULT 0, deuda_financiada_centavos INTEGER NOT NULL DEFAULT 0, monto_activacion_centavos INTEGER NOT NULL DEFAULT 0, fecha_corte_deuda TEXT, tipo_activacion_origen TEXT NOT NULL DEFAULT 'RECONEXION'
    CHECK (tipo_activacion_origen IN ('CONEXION', 'RECONEXION')),
    FOREIGN KEY (abonado_id) REFERENCES abonados(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (casa_id) REFERENCES casas(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (creado_por) REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE SET NULL,
    CHECK (fecha_fin IS NULL OR fecha_fin >= fecha_inicio)
);
CREATE TABLE planes_pago_cargos (
    plan_pago_id INTEGER NOT NULL,
    cargo_id INTEGER NOT NULL,
    creado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    PRIMARY KEY (plan_pago_id, cargo_id),
    FOREIGN KEY (plan_pago_id) REFERENCES planes_pago(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (cargo_id) REFERENCES cargos(id) ON UPDATE CASCADE ON DELETE RESTRICT
);
CREATE TABLE "procesos_servicio" (
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
    creado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    actualizado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (abonado_id) REFERENCES abonados(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (casa_id) REFERENCES casas(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (plan_pago_id) REFERENCES planes_pago(id) ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (pago_id) REFERENCES pagos(id) ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE SET NULL
);
CREATE TABLE "reportes_generados" (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    parametros_json TEXT,
    formato TEXT NOT NULL DEFAULT 'PDF' CHECK (formato = 'PDF'),
    ruta_archivo TEXT,
    generado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    generado_por INTEGER,
    FOREIGN KEY (generado_por) REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE SET NULL
);
CREATE TABLE roles (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL UNIQUE COLLATE NOCASE,
    descripcion TEXT,
    es_sistema INTEGER NOT NULL DEFAULT 0 CHECK (es_sistema IN (0, 1)),
    estado TEXT NOT NULL DEFAULT 'ACTIVO' CHECK (estado IN ('ACTIVO', 'INACTIVO')),
    creado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    actualizado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
INSERT INTO "roles" VALUES(2,'ADMINISTRADOR','Rol principal de administracion operativa.',1,'ACTIVO','2026-06-09 15:07:37','2026-06-09 15:07:37');
INSERT INTO "roles" VALUES(3,'CAJERO','Rol operativo orientado a cobranza y consulta diaria.',1,'ACTIVO','2026-06-09 15:07:37','2026-06-09 15:07:37');
INSERT INTO "roles" VALUES(4,'CONSULTA','Rol de revision y consulta administrativa.',1,'ACTIVO','2026-06-09 15:07:37','2026-06-09 15:07:37');
CREATE TABLE roles_permisos (
    rol_id INTEGER NOT NULL,
    permiso_id INTEGER NOT NULL,
    creado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    PRIMARY KEY (rol_id, permiso_id),
    FOREIGN KEY (rol_id) REFERENCES roles(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (permiso_id) REFERENCES permisos(id) ON UPDATE CASCADE ON DELETE RESTRICT
);
INSERT INTO "roles_permisos" VALUES(2,21,'2026-06-09 15:07:38');
INSERT INTO "roles_permisos" VALUES(2,20,'2026-06-09 15:07:38');
INSERT INTO "roles_permisos" VALUES(2,22,'2026-06-09 15:07:38');
INSERT INTO "roles_permisos" VALUES(2,29,'2026-06-09 15:07:38');
INSERT INTO "roles_permisos" VALUES(2,19,'2026-06-09 15:07:38');
INSERT INTO "roles_permisos" VALUES(2,24,'2026-06-09 15:07:38');
INSERT INTO "roles_permisos" VALUES(2,25,'2026-06-09 15:07:38');
INSERT INTO "roles_permisos" VALUES(2,23,'2026-06-09 15:07:38');
INSERT INTO "roles_permisos" VALUES(2,26,'2026-06-09 15:07:38');
INSERT INTO "roles_permisos" VALUES(2,28,'2026-06-09 15:07:38');
INSERT INTO "roles_permisos" VALUES(2,27,'2026-06-09 15:07:38');
INSERT INTO "roles_permisos" VALUES(3,21,'2026-06-09 15:07:38');
INSERT INTO "roles_permisos" VALUES(3,22,'2026-06-09 15:07:38');
INSERT INTO "roles_permisos" VALUES(3,19,'2026-06-09 15:07:38');
INSERT INTO "roles_permisos" VALUES(3,24,'2026-06-09 15:07:38');
INSERT INTO "roles_permisos" VALUES(3,25,'2026-06-09 15:07:38');
INSERT INTO "roles_permisos" VALUES(3,23,'2026-06-09 15:07:38');
INSERT INTO "roles_permisos" VALUES(4,21,'2026-06-09 15:07:38');
INSERT INTO "roles_permisos" VALUES(4,22,'2026-06-09 15:07:38');
INSERT INTO "roles_permisos" VALUES(4,19,'2026-06-09 15:07:38');
INSERT INTO "roles_permisos" VALUES(4,24,'2026-06-09 15:07:38');
INSERT INTO "roles_permisos" VALUES(4,25,'2026-06-09 15:07:38');
INSERT INTO "roles_permisos" VALUES(4,28,'2026-06-09 15:07:38');
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
CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY,
    nombre_usuario TEXT NOT NULL UNIQUE COLLATE NOCASE,
    nombre_completo TEXT NOT NULL,
    correo TEXT NOT NULL UNIQUE COLLATE NOCASE,
    contrasena_hash TEXT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'ACTIVO' CHECK (estado IN ('ACTIVO', 'INACTIVO', 'BLOQUEADO')),
    ultimo_acceso_en TEXT,
    ultimo_cambio_contrasena_en TEXT,
    observaciones TEXT,
    creado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    actualizado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    eliminado_en TEXT,
    creado_por INTEGER,
    actualizado_por INTEGER, es_tecnico INTEGER NOT NULL DEFAULT 0 CHECK (es_tecnico IN (0, 1)), es_oculto INTEGER NOT NULL DEFAULT 0 CHECK (es_oculto IN (0, 1)), requiere_cambio_contrasena INTEGER NOT NULL DEFAULT 0 CHECK (requiere_cambio_contrasena IN (0, 1)), intentos_fallidos INTEGER NOT NULL DEFAULT 0 CHECK (intentos_fallidos >= 0), bloqueado_hasta TEXT, fecha_restablecimiento_contrasena TEXT, restablecida_por_usuario_id INTEGER REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE SET NULL, contrasena_temporal_expira_en TEXT NULL,
    FOREIGN KEY (creado_por) REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (actualizado_por) REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE SET NULL
);
INSERT INTO "usuarios" VALUES(1,'admin','Administrador del Sistema','admin@sigqua.local','scrypt$c081b3c0b1cabcfd1e173ac2293394ee$d3c88ce38c9accabda7c2beeef20c9cb0be9bf8a1014f702cc83d90c83fb8d7e8904a200712554282f89cdc1f6adc9fb2b3544f3732c7fabea9b6357a051a94d','ACTIVO',NULL,NULL,'Usuario administrador inicial.','2026-06-09 15:07:37','2026-06-09 15:07:37',NULL,NULL,NULL,0,0,0,0,NULL,NULL,NULL,NULL);
CREATE TABLE usuarios_roles (
    usuario_id INTEGER NOT NULL,
    rol_id INTEGER NOT NULL,
    creado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    PRIMARY KEY (usuario_id, rol_id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (rol_id) REFERENCES roles(id) ON UPDATE CASCADE ON DELETE RESTRICT
);
INSERT INTO "usuarios_roles" VALUES(1,2,'2026-06-09 15:07:38');
CREATE INDEX idx_abonados_barrio_id ON abonados(barrio_id);
CREATE INDEX idx_abonados_nombre_completo ON abonados(nombre_completo);
CREATE INDEX idx_cargos_abonado_id ON cargos(abonado_id);
CREATE INDEX idx_cargos_casa_id ON cargos(casa_id);
CREATE INDEX idx_cargos_periodo_id ON cargos(periodo_id);
CREATE INDEX idx_cargos_estado ON cargos(estado);
CREATE INDEX idx_pagos_abonado_id ON pagos(abonado_id);
CREATE INDEX idx_pagos_casa_id ON pagos(casa_id);
CREATE INDEX idx_pagos_usuario_cobrador_id ON pagos(usuario_cobrador_id);
CREATE INDEX idx_pagos_fecha_pago ON pagos(fecha_pago);
CREATE INDEX idx_pagos_estado ON pagos(estado);
CREATE INDEX idx_pagos_detalle_pago_id ON pagos_detalle(pago_id);
CREATE INDEX idx_pagos_detalle_cargo_id ON pagos_detalle(cargo_id);
CREATE INDEX idx_planes_pago_abonado_id ON planes_pago(abonado_id);
CREATE INDEX idx_planes_pago_casa_id ON planes_pago(casa_id);
CREATE INDEX idx_planes_pago_estado ON planes_pago(estado);
CREATE INDEX idx_cuotas_plan_pago_plan_id ON cuotas_plan_pago(plan_pago_id);
CREATE INDEX idx_cuotas_plan_pago_estado ON cuotas_plan_pago(estado);
CREATE INDEX idx_usuarios_tecnico_oculto ON usuarios(es_tecnico, es_oculto, estado);
CREATE INDEX idx_historial_respaldos_generado_en ON historial_respaldos(generado_en);
CREATE INDEX idx_historial_respaldos_generado_por ON historial_respaldos(generado_por, generado_en);
CREATE INDEX idx_eventos_tecnicos_categoria_fecha ON eventos_tecnicos(categoria, registrado_en);
CREATE INDEX idx_eventos_tecnicos_severidad_fecha ON eventos_tecnicos(severidad, registrado_en);
CREATE INDEX idx_auditoria_usuario_fecha ON auditoria(usuario_id, fecha_evento);
CREATE INDEX idx_auditoria_accion_fecha ON auditoria(accion, fecha_evento);
CREATE UNIQUE INDEX idx_pagos_adelantados_casa_periodo_unico
ON pagos_adelantados(casa_id, periodo_id);
CREATE INDEX idx_casas_abonado_id ON casas(abonado_id);
CREATE INDEX idx_casas_barrio_id ON casas(barrio_id);
CREATE INDEX idx_casas_estado_servicio ON casas(estado_servicio);
CREATE INDEX idx_casas_estado_administrativo ON casas(estado_administrativo);
CREATE INDEX idx_casas_antecedente_servicio ON casas(ha_tenido_servicio_activo);
CREATE INDEX idx_procesos_servicio_estado ON procesos_servicio(estado);
CREATE INDEX idx_procesos_servicio_tipo ON procesos_servicio(tipo);
CREATE INDEX idx_procesos_servicio_pago_id ON procesos_servicio(pago_id);
CREATE INDEX idx_cargos_proceso_servicio_id ON cargos(proceso_servicio_id);
CREATE INDEX idx_operaciones_cobro_tipo ON operaciones_cobro(tipo_operacion);
CREATE INDEX idx_operaciones_cobro_casa ON operaciones_cobro(casa_id);
CREATE INDEX idx_pagos_operacion_cobro_id ON pagos(operacion_cobro_id);
CREATE INDEX idx_comprobantes_impresiones_comprobante
ON comprobantes_impresiones(comprobante_id, estado, tipo_copia, es_reimpresion);
CREATE INDEX idx_casas_estado_aviso_cobro
ON casas(estado_aviso_cobro);
CREATE INDEX idx_casas_fecha_ultimo_aviso
ON casas(fecha_ultimo_aviso);
CREATE INDEX idx_casas_usuario_ultimo_aviso
ON casas(usuario_ultimo_aviso_id);
CREATE VIEW vw_cargos_pendientes_ordenados AS
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
CREATE VIEW vw_resumen_abonados AS
SELECT
    a.id,
    a.dni,
    a.nombre_completo,
    a.telefono,
    b.nombre AS barrio_nombre,
    a.estado
FROM abonados a
INNER JOIN barrios b ON b.id = a.barrio_id;
CREATE VIEW vw_abonados_con_deuda AS
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
CREATE VIEW vw_abonados_sin_deuda AS
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
CREATE VIEW vw_deuda_por_barrio AS
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
CREATE VIEW vw_historial_pagos_abonado AS
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
CREATE VIEW vw_ingresos_por_fecha AS
SELECT
    date(fecha_pago) AS fecha,
    COUNT(*) AS total_pagos,
    COALESCE(SUM(total_pagado_centavos), 0) AS total_ingresos_centavos
FROM pagos
WHERE estado = 'CONFIRMADO'
GROUP BY date(fecha_pago);
CREATE VIEW vw_pagos_por_cobrador AS
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
CREATE VIEW vw_planes_pago_activos AS
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
CREATE VIEW vw_pagos_adelantados AS
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
CREATE VIEW vw_usuarios_restablecibles_por_admin AS
SELECT *
FROM vw_usuarios_operativos;
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
CREATE TRIGGER trg_abonados_actualizado
AFTER UPDATE ON abonados
FOR EACH ROW
WHEN NEW.actualizado_en = OLD.actualizado_en
BEGIN
    UPDATE abonados SET actualizado_en = datetime('now', 'localtime') WHERE id = NEW.id;
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
CREATE TRIGGER trg_barrios_actualizado
AFTER UPDATE ON barrios
FOR EACH ROW
WHEN NEW.actualizado_en = OLD.actualizado_en
BEGIN
    UPDATE barrios SET actualizado_en = datetime('now', 'localtime') WHERE id = NEW.id;
END;
CREATE TRIGGER trg_bloquear_eliminacion_cargos
BEFORE DELETE ON cargos
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'No se permite eliminar cargos. Use estado ANULADO para conservar trazabilidad.');
END;
CREATE TRIGGER trg_bloquear_eliminacion_pagos
BEFORE DELETE ON pagos
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'No se permite eliminar pagos. Use anulacion para conservar trazabilidad.');
END;
CREATE TRIGGER trg_bloquear_eliminacion_planes_pago
BEFORE DELETE ON planes_pago
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'No se permite eliminar planes de pago. Use estado ANULADO o CANCELADO.');
END;
CREATE TRIGGER trg_cargos_actualizado
AFTER UPDATE ON cargos
FOR EACH ROW
WHEN NEW.actualizado_en = OLD.actualizado_en
BEGIN
    UPDATE cargos SET actualizado_en = datetime('now', 'localtime') WHERE id = NEW.id;
END;
CREATE TRIGGER trg_casas_actualizado
AFTER UPDATE ON casas
FOR EACH ROW
WHEN NEW.actualizado_en = OLD.actualizado_en
BEGIN
    UPDATE casas SET actualizado_en = datetime('now', 'localtime') WHERE id = NEW.id;
END;
CREATE TRIGGER trg_cuotas_plan_pago_actualizado
AFTER UPDATE ON cuotas_plan_pago
FOR EACH ROW
WHEN NEW.actualizado_en = OLD.actualizado_en
BEGIN
    UPDATE cuotas_plan_pago SET actualizado_en = datetime('now', 'localtime') WHERE id = NEW.id;
END;
CREATE TRIGGER trg_pagos_actualizado
AFTER UPDATE ON pagos
FOR EACH ROW
WHEN NEW.actualizado_en = OLD.actualizado_en
BEGIN
    UPDATE pagos SET actualizado_en = datetime('now', 'localtime') WHERE id = NEW.id;
END;
CREATE TRIGGER trg_planes_pago_actualizado
AFTER UPDATE ON planes_pago
FOR EACH ROW
WHEN NEW.actualizado_en = OLD.actualizado_en
BEGIN
    UPDATE planes_pago SET actualizado_en = datetime('now', 'localtime') WHERE id = NEW.id;
END;
CREATE TRIGGER trg_procesos_servicio_actualizado
AFTER UPDATE ON procesos_servicio
FOR EACH ROW
WHEN NEW.actualizado_en = OLD.actualizado_en
BEGIN
    UPDATE procesos_servicio SET actualizado_en = datetime('now', 'localtime') WHERE id = NEW.id;
END;
CREATE TRIGGER trg_usuarios_actualizado
AFTER UPDATE ON usuarios
FOR EACH ROW
WHEN NEW.actualizado_en = OLD.actualizado_en
BEGIN
    UPDATE usuarios SET actualizado_en = datetime('now', 'localtime') WHERE id = NEW.id;
END;

PRAGMA foreign_keys = ON;
