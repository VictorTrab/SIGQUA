BEGIN TRANSACTION;

ALTER TABLE planes_pago ADD COLUMN tipo_plan TEXT NOT NULL DEFAULT 'MESES_PENDIENTES';
ALTER TABLE planes_pago ADD COLUMN concepto_financiado TEXT NOT NULL DEFAULT 'MESES_PENDIENTES';
ALTER TABLE planes_pago ADD COLUMN prima_centavos INTEGER NOT NULL DEFAULT 0;

UPDATE planes_pago
SET tipo_plan = CASE
        WHEN tipo_plan IS NULL OR trim(tipo_plan) = '' THEN 'MESES_PENDIENTES'
        ELSE tipo_plan
    END,
    concepto_financiado = CASE
        WHEN concepto_financiado IS NULL OR trim(concepto_financiado) = '' THEN 'MESES_PENDIENTES'
        ELSE concepto_financiado
    END,
    prima_centavos = COALESCE(prima_centavos, 0);

INSERT OR IGNORE INTO conceptos_cobro(codigo, nombre, tipo, requiere_periodo, monto_global_centavos)
VALUES ('CONEXION', 'Conexion financiable segun caso operativo', 'OTRO', 0, NULL);

UPDATE configuracion_sistema
SET valor = '1',
    descripcion = 'La mora forma parte del sistema como meses vencidos no pagados y no se desactiva desde configuracion.',
    editable = 0,
    actualizado_en = datetime('now')
WHERE clave = 'cobro.mora_activa';

UPDATE configuracion_sistema
SET descripcion = 'Clave heredada. No representa un recargo automatico y no debe usarse para parametrizar mora.',
    editable = 0,
    actualizado_en = datetime('now')
WHERE clave = 'cobro.mora_monto_centavos';

INSERT OR IGNORE INTO configuracion_sistema(clave, valor, tipo_dato, categoria, descripcion, editable)
VALUES
('cobro.multa_mora_automatica_activa', '0', 'BOOLEANO', 'Cobro', 'Activa el recargo automatico adicional por cada mes vencido.', 1),
('cobro.multa_mora_automatica_centavos', '0', 'ENTERO', 'Cobro', 'Monto adicional por cada mes vencido cuando la multa automatica esta activa.', 1),
('cobro.corte_automatico_activo', '0', 'BOOLEANO', 'Cobro', 'Permite habilitar o deshabilitar el corte automatico por deuda segun las reglas operativas vigentes.', 1);

UPDATE configuracion_sistema
SET valor = '2.2.0',
    actualizado_en = datetime('now')
WHERE clave = 'sistema.version';

INSERT INTO esquema_migraciones(version, descripcion, checksum)
SELECT '006', 'planes_pago_y_configuracion_real', NULL
WHERE NOT EXISTS (
    SELECT 1
    FROM esquema_migraciones
    WHERE version = '006'
);

COMMIT;
