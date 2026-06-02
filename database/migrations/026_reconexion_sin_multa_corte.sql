-- ============================================================
-- 026. Reconexion sin multa por corte separada
-- ============================================================

UPDATE pagos_detalle
SET monto_pagado_centavos = monto_pagado_centavos + (
    SELECT COALESCE(SUM(pd_multa.monto_pagado_centavos), 0)
    FROM pagos_detalle pd_multa
    INNER JOIN conceptos_cobro cc_multa ON cc_multa.id = pd_multa.concepto_id
    WHERE pd_multa.pago_id = pagos_detalle.pago_id
      AND cc_multa.codigo = 'MULTA'
)
WHERE concepto_id = (SELECT id FROM conceptos_cobro WHERE codigo = 'RECONEXION' LIMIT 1)
  AND id = (
      SELECT MIN(pd_reconexion.id)
      FROM pagos_detalle pd_reconexion
      INNER JOIN conceptos_cobro cc_reconexion ON cc_reconexion.id = pd_reconexion.concepto_id
      WHERE pd_reconexion.pago_id = pagos_detalle.pago_id
        AND cc_reconexion.codigo = 'RECONEXION'
  )
  AND EXISTS (
      SELECT 1
      FROM pagos_detalle pd_multa
      INNER JOIN conceptos_cobro cc_multa ON cc_multa.id = pd_multa.concepto_id
      WHERE pd_multa.pago_id = pagos_detalle.pago_id
        AND cc_multa.codigo = 'MULTA'
  );

UPDATE cargos
SET monto_centavos = monto_centavos + (
        SELECT COALESCE(SUM(pd_multa.monto_pagado_centavos), 0)
        FROM pagos_detalle pd_reconexion
        INNER JOIN pagos_detalle pd_multa ON pd_multa.pago_id = pd_reconexion.pago_id
        INNER JOIN conceptos_cobro cc_multa ON cc_multa.id = pd_multa.concepto_id
        WHERE pd_reconexion.cargo_id = cargos.id
          AND cc_multa.codigo = 'MULTA'
    ),
    saldo_pendiente_centavos = 0,
    estado = 'PAGADO',
    actualizado_en = datetime('now', 'localtime')
WHERE id IN (
    SELECT pd_reconexion.cargo_id
    FROM pagos_detalle pd_reconexion
    INNER JOIN conceptos_cobro cc_reconexion ON cc_reconexion.id = pd_reconexion.concepto_id
    WHERE cc_reconexion.codigo = 'RECONEXION'
      AND pd_reconexion.cargo_id IS NOT NULL
      AND EXISTS (
          SELECT 1
          FROM pagos_detalle pd_multa
          INNER JOIN conceptos_cobro cc_multa ON cc_multa.id = pd_multa.concepto_id
          WHERE pd_multa.pago_id = pd_reconexion.pago_id
            AND cc_multa.codigo = 'MULTA'
      )
);

UPDATE cargos
SET saldo_pendiente_centavos = 0,
    estado = 'ANULADO',
    anulado_en = datetime('now', 'localtime'),
    motivo_anulacion = 'Fusionado historicamente en el cargo de reconexion.',
    actualizado_en = datetime('now', 'localtime')
WHERE id IN (
    SELECT pd_multa.cargo_id
    FROM pagos_detalle pd_multa
    INNER JOIN conceptos_cobro cc_multa ON cc_multa.id = pd_multa.concepto_id
    WHERE cc_multa.codigo = 'MULTA'
      AND pd_multa.cargo_id IS NOT NULL
      AND EXISTS (
          SELECT 1
          FROM pagos_detalle pd_reconexion
          INNER JOIN conceptos_cobro cc_reconexion ON cc_reconexion.id = pd_reconexion.concepto_id
          WHERE pd_reconexion.pago_id = pd_multa.pago_id
            AND cc_reconexion.codigo = 'RECONEXION'
      )
);

DELETE FROM pagos_detalle
WHERE concepto_id = (SELECT id FROM conceptos_cobro WHERE codigo = 'MULTA' LIMIT 1)
  AND EXISTS (
      SELECT 1
      FROM pagos_detalle pd_reconexion
      INNER JOIN conceptos_cobro cc_reconexion ON cc_reconexion.id = pd_reconexion.concepto_id
      WHERE pd_reconexion.pago_id = pagos_detalle.pago_id
        AND cc_reconexion.codigo = 'RECONEXION'
  );

UPDATE procesos_servicio
SET monto_reconexion_centavos = COALESCE(monto_reconexion_centavos, 0) + COALESCE(multa_corte_centavos, 0),
    actualizado_en = datetime('now', 'localtime')
WHERE tipo = 'RECONEXION'
  AND COALESCE(multa_corte_centavos, 0) > 0;

UPDATE conceptos_cobro
SET estado = 'INACTIVO'
WHERE codigo = 'MULTA';

ALTER TABLE procesos_servicio DROP COLUMN multa_corte_centavos;

INSERT INTO esquema_migraciones(version, descripcion, checksum)
SELECT '026', 'reconexion_sin_multa_corte', NULL
WHERE NOT EXISTS (
    SELECT 1
    FROM esquema_migraciones
    WHERE version = '026'
);
