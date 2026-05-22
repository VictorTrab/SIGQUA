BEGIN TRANSACTION;

ALTER TABLE comprobantes
ADD COLUMN saldo_posterior_centavos INTEGER NOT NULL DEFAULT 0
CHECK (saldo_posterior_centavos >= 0);

ALTER TABLE pagos
ADD COLUMN plan_pago_id INTEGER;

ALTER TABLE pagos_detalle
ADD COLUMN cuota_plan_pago_id INTEGER;

INSERT OR IGNORE INTO conceptos_cobro(codigo, nombre, tipo, requiere_periodo, monto_global_centavos)
VALUES ('ABONO_EXTRAORDINARIO', 'Abono extraordinario a plan de pago', 'OTRO', 0, NULL);

UPDATE planes_pago
SET tipo_plan = 'RECONEXION',
    concepto_financiado = 'RECONEXION',
    observaciones = trim(
        CASE
            WHEN COALESCE(observaciones, '') = '' THEN
                '[Migrado] Plan legado alineado al flujo de reconexion del prototipo.'
            ELSE
                observaciones || ' [Migrado] Plan legado alineado al flujo de reconexion del prototipo.'
        END
    ),
    actualizado_en = datetime('now', 'localtime')
WHERE tipo_plan NOT IN ('CONEXION', 'RECONEXION')
   OR concepto_financiado NOT IN ('CONEXION', 'RECONEXION');

INSERT INTO esquema_migraciones(version, descripcion, checksum)
SELECT '008', 'comprobantes_reportes_planes_pago', NULL
WHERE NOT EXISTS (
    SELECT 1
    FROM esquema_migraciones
    WHERE version = '008'
);

COMMIT;

