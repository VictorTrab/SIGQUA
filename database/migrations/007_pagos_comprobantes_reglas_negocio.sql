-- ============================================================
-- 007. Pagos, comprobantes y reglas cerradas de negocio
-- ============================================================

ALTER TABLE pagos
ADD COLUMN tipo_pago TEXT NOT NULL DEFAULT 'MENSUALIDAD'
CHECK (tipo_pago IN ('MENSUALIDAD', 'PLAN_PAGO', 'CONEXION', 'RECONEXION'));

ALTER TABLE comprobantes
ADD COLUMN tipo_comprobante TEXT NOT NULL DEFAULT 'MENSUALIDAD'
CHECK (tipo_comprobante IN ('MENSUALIDAD', 'PLAN_PAGO', 'CONEXION', 'RECONEXION'));

ALTER TABLE metodos_pago
ADD COLUMN requiere_referencia INTEGER NOT NULL DEFAULT 0
CHECK (requiere_referencia IN (0, 1));

INSERT OR IGNORE INTO metodos_pago(codigo, nombre, descripcion, requiere_referencia)
VALUES ('DEPOSITO', 'Deposito', 'Pago por deposito bancario.', 1);

UPDATE metodos_pago
SET requiere_referencia = 1
WHERE upper(codigo) IN ('TRANSFERENCIA', 'DEPOSITO');

CREATE TABLE IF NOT EXISTS correlativos_comprobantes (
    clave TEXT PRIMARY KEY,
    ultimo_numero INTEGER NOT NULL DEFAULT 0 CHECK (ultimo_numero >= 0),
    actualizado_en TEXT NOT NULL DEFAULT (datetime('now'))
);

INSERT OR IGNORE INTO correlativos_comprobantes(clave, ultimo_numero)
SELECT
    'RECIBO_GLOBAL',
    COALESCE(
        MAX(
            CAST(
                REPLACE(
                    REPLACE(UPPER(numero_comprobante), 'REC-PRUEBA-', ''),
                    'REC-',
                    ''
                ) AS INTEGER
            )
        ),
        0
    )
FROM comprobantes;

CREATE UNIQUE INDEX IF NOT EXISTS idx_pagos_adelantados_casa_periodo_unico
ON pagos_adelantados(casa_id, periodo_id);

INSERT INTO esquema_migraciones(version, descripcion, checksum)
SELECT '007', 'pagos_comprobantes_reglas_negocio', NULL
WHERE NOT EXISTS (
    SELECT 1 FROM esquema_migraciones WHERE version = '007'
);
