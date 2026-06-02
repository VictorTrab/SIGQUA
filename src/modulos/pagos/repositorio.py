"""Persistencia SQLite del modulo de pagos."""

from __future__ import annotations

from calendar import monthrange
from contextlib import closing
from datetime import date
from typing import Protocol

from comun.base_datos import GestorBaseDatos
from comun.configuracion.identidad_empresa import (
    CLAVES_IDENTIDAD_EMPRESA,
    CLAVES_IDENTIDAD_LEGADAS_JUNTA,
    construir_identidad_empresa,
)
from modulos.pagos.entidades import (
    CargoPago,
    CasaPago,
    ComprobantePago,
    ConfiguracionReciboPago,
    CuotaPlanCobrable,
    DetalleAplicacionPago,
    DiagnosticoPagoPlan,
    HistorialPago,
    MetodoPago,
    ResumenDeudaPago,
    ResumenConfirmacionPago,
    TIPO_PAGO_MENSUALIDAD,
    TIPO_PAGO_PLAN,
    TIPO_PAGO_RECONEXION,
)


SUBCONSULTA_DEUDA_CASA = """
    SELECT
        casa_id,
        COUNT(
            DISTINCT CASE
                WHEN estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDO')
                 AND saldo_pendiente_centavos > 0
                THEN COALESCE(periodo_id, id)
            END
        ) AS meses_pendientes,
        COUNT(
            DISTINCT CASE
                WHEN estado = 'VENCIDO' AND saldo_pendiente_centavos > 0
                THEN COALESCE(periodo_id, id)
            END
        ) AS meses_vencidos,
        COALESCE(
            SUM(
                CASE
                    WHEN estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDO')
                     AND saldo_pendiente_centavos > 0
                    THEN saldo_pendiente_centavos
                    ELSE 0
                END
            ),
            0
        ) AS deuda_total_centavos,
        COALESCE(
            SUM(
                CASE
                    WHEN estado = 'VENCIDO'
                     AND saldo_pendiente_centavos > 0
                    THEN saldo_pendiente_centavos
                    ELSE 0
                END
            ),
            0
        ) AS deuda_vencida_centavos
    FROM cargos
    WHERE anulado_en IS NULL
    GROUP BY casa_id
"""


class RepositorioPagos(Protocol):
    """Contrato de persistencia requerido por pagos."""

    def listar_casas(self, filtro: str = "", limite: int = 30) -> list[CasaPago]:
        """Lista casas cobrables con contexto de deuda."""

    def obtener_casa(self, casa_id: int) -> CasaPago | None:
        """Obtiene una casa puntual."""

    def listar_cargos_mensuales(self, casa_id: int) -> list[CargoPago]:
        """Lista cargos mensuales pendientes en orden de cobro."""

    def obtener_resumen_deuda_pago(self, casa_id: int) -> ResumenDeudaPago:
        """Obtiene totales de deuda para validar pagos."""

    def listar_metodos_pago_activos(self) -> list[MetodoPago]:
        """Lista metodos de pago activos."""

    def obtener_metodo_pago(self, metodo_pago_id: int) -> MetodoPago | None:
        """Obtiene un metodo de pago puntual."""

    def listar_historial(self, limite: int = 20) -> list[HistorialPago]:
        """Lista pagos recientes."""

    def obtener_precio_mensual_centavos(self) -> int:
        """Obtiene la tarifa mensual vigente."""

    def cobrar_mensualidad_prorrateada_en_activacion(self) -> bool:
        """Indica si conexión y reconexión deben agregar el primer prorrateo."""

    def obtener_diagnostico_plan(self, casa_id: int) -> DiagnosticoPagoPlan | None:
        """Obtiene el diagnostico de plan activo y sus cuotas cobrables para una casa."""

    def guardar_pago_confirmado(
        self,
        resumen: ResumenConfirmacionPago,
        actor_id: int,
    ) -> ComprobantePago:
        """Guarda pago, detalle y comprobante dentro de una transaccion."""

    def guardar_operacion_compuesta_confirmada(
        self,
        resumen: ResumenConfirmacionPago,
        actor_id: int,
    ) -> tuple[ComprobantePago, ...]:
        """Guarda una operacion con pagos y comprobantes separados."""

    def obtener_comprobante(self, pago_id: int) -> ComprobantePago | None:
        """Obtiene el comprobante completo de un pago confirmado."""

    def obtener_configuracion_recibo(self) -> ConfiguracionReciboPago:
        """Obtiene la configuracion visible del recibo de pago."""


class RepositorioPagosSQLite:
    """Implementacion SQLite del modulo de pagos."""

    def __init__(self, gestor_base_datos: GestorBaseDatos) -> None:
        self._gestor_base_datos = gestor_base_datos

    def listar_casas(self, filtro: str = "", limite: int = 30) -> list[CasaPago]:
        condiciones = ["c.eliminado_en IS NULL"]
        parametros: list[object] = []
        filtro = filtro.strip()
        if filtro:
            patron = f"%{filtro}%"
            condiciones.append(
                """
                (
                    lower(a.nombre_completo) LIKE lower(?)
                    OR a.dni LIKE ?
                    OR lower(printf('CA-%03d', c.id)) LIKE lower(?)
                    OR lower(COALESCE(b.nombre, '')) LIKE lower(?)
                )
                """
            )
            parametros.extend([patron, patron, patron, patron])
        parametros.append(limite)
        consulta = f"""
            SELECT
                c.id AS casa_id,
                printf('CA-%03d', c.id) AS casa_codigo,
                a.id AS abonado_id,
                a.nombre_completo AS abonado_nombre,
                a.dni AS abonado_dni,
                a.estado AS abonado_estado,
                COALESCE(b.nombre, '') AS barrio_nombre,
                c.estado_servicio,
                COALESCE(c.estado_administrativo, 'OPERATIVA') AS estado_administrativo,
                COALESCE(c.motivo_estado_administrativo, 'NINGUNO') AS motivo_estado_administrativo,
                COALESCE(c.ha_tenido_servicio_activo, 0) AS ha_tenido_servicio_activo,
                COALESCE(dd.meses_pendientes, 0) AS meses_pendientes,
                COALESCE(dd.meses_vencidos, 0) AS meses_vencidos,
                COALESCE(dd.deuda_total_centavos, 0) AS deuda_total_centavos,
                COALESCE(dd.deuda_vencida_centavos, 0) AS deuda_vencida_centavos,
                COALESCE(pp.total_planes_activos, 0) AS total_planes_activos
            FROM casas c
            INNER JOIN abonados a ON a.id = c.abonado_id
            LEFT JOIN barrios b ON b.id = c.barrio_id
            LEFT JOIN ({SUBCONSULTA_DEUDA_CASA}) dd ON dd.casa_id = c.id
            LEFT JOIN (
                SELECT casa_id, COUNT(*) AS total_planes_activos
                FROM planes_pago
                WHERE estado = 'ACTIVO'
                GROUP BY casa_id
            ) pp ON pp.casa_id = c.id
            WHERE {' AND '.join(condiciones)}
            ORDER BY dd.deuda_vencida_centavos DESC, c.id ASC
            LIMIT ?;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            filas = conexion.execute(consulta, tuple(parametros)).fetchall()
        return [self._fila_a_casa(fila) for fila in filas]

    def obtener_casa(self, casa_id: int) -> CasaPago | None:
        consulta = f"""
            SELECT
                c.id AS casa_id,
                printf('CA-%03d', c.id) AS casa_codigo,
                a.id AS abonado_id,
                a.nombre_completo AS abonado_nombre,
                a.dni AS abonado_dni,
                a.estado AS abonado_estado,
                COALESCE(b.nombre, '') AS barrio_nombre,
                c.estado_servicio,
                COALESCE(c.estado_administrativo, 'OPERATIVA') AS estado_administrativo,
                COALESCE(c.motivo_estado_administrativo, 'NINGUNO') AS motivo_estado_administrativo,
                COALESCE(c.ha_tenido_servicio_activo, 0) AS ha_tenido_servicio_activo,
                COALESCE(dd.meses_pendientes, 0) AS meses_pendientes,
                COALESCE(dd.meses_vencidos, 0) AS meses_vencidos,
                COALESCE(dd.deuda_total_centavos, 0) AS deuda_total_centavos,
                COALESCE(dd.deuda_vencida_centavos, 0) AS deuda_vencida_centavos,
                COALESCE(pp.total_planes_activos, 0) AS total_planes_activos
            FROM casas c
            INNER JOIN abonados a ON a.id = c.abonado_id
            LEFT JOIN barrios b ON b.id = c.barrio_id
            LEFT JOIN ({SUBCONSULTA_DEUDA_CASA}) dd ON dd.casa_id = c.id
            LEFT JOIN (
                SELECT casa_id, COUNT(*) AS total_planes_activos
                FROM planes_pago
                WHERE estado = 'ACTIVO'
                GROUP BY casa_id
            ) pp ON pp.casa_id = c.id
            WHERE c.id = ? AND c.eliminado_en IS NULL
            LIMIT 1;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            fila = conexion.execute(consulta, (casa_id,)).fetchone()
        return self._fila_a_casa(fila) if fila is not None else None

    def obtener_diagnostico_plan(self, casa_id: int) -> DiagnosticoPagoPlan | None:
        casa = self.obtener_casa(casa_id)
        if casa is None:
            return None
        consulta_planes = """
            SELECT
                pp.id,
                COALESCE(pp.tipo_plan, 'RECONEXION') AS tipo_plan,
                COALESCE(pp.estado, 'ACTIVO') AS estado_plan,
                COALESCE(qc.cuotas_pendientes, 0) AS cuotas_pendientes,
                COALESCE(qc.cuotas_en_mora, 0) AS cuotas_en_mora,
                COALESCE(qc.saldo_pendiente_centavos, 0) AS saldo_pendiente_centavos
            FROM planes_pago pp
            LEFT JOIN (
                SELECT
                    plan_pago_id,
                    COUNT(
                        CASE
                            WHEN estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDO')
                             AND saldo_pendiente_centavos > 0
                            THEN 1
                        END
                    ) AS cuotas_pendientes,
                    COUNT(
                        CASE
                            WHEN estado = 'VENCIDO' AND saldo_pendiente_centavos > 0
                            THEN 1
                        END
                    ) AS cuotas_en_mora,
                    COALESCE(
                        SUM(
                            CASE
                                WHEN estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDO')
                                 AND saldo_pendiente_centavos > 0
                                THEN saldo_pendiente_centavos
                                ELSE 0
                            END
                        ),
                        0
                    ) AS saldo_pendiente_centavos
                FROM cuotas_plan_pago
                GROUP BY plan_pago_id
            ) qc ON qc.plan_pago_id = pp.id
            WHERE pp.casa_id = ?
              AND pp.estado = 'ACTIVO'
            ORDER BY pp.id ASC;
        """
        consulta_cuotas = """
            SELECT
                id,
                plan_pago_id,
                numero_cuota,
                fecha_vencimiento,
                estado,
                saldo_pendiente_centavos
            FROM cuotas_plan_pago
            WHERE plan_pago_id = ?
              AND estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDO')
              AND saldo_pendiente_centavos > 0
            ORDER BY fecha_vencimiento ASC, numero_cuota ASC, id ASC;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            filas_planes = conexion.execute(consulta_planes, (casa_id,)).fetchall()
            if not filas_planes:
                return DiagnosticoPagoPlan(
                    casa_id=casa_id,
                    cantidad_planes_activos=0,
                    plan_pago_id=None,
                    codigo_plan="Sin plan activo",
                    tipo_plan="",
                    estado_plan="SIN_PLAN",
                    cuotas_pendientes=0,
                    cuotas_en_mora=0,
                    saldo_vivo_centavos=0,
                    cuotas_cobrables=(),
                    permite_continuar=False,
                    estado_visual="",
                    mensaje_diagnostico="",
                    alertas=(),
                )
            if len(filas_planes) > 1:
                return DiagnosticoPagoPlan(
                    casa_id=casa_id,
                    cantidad_planes_activos=len(filas_planes),
                    plan_pago_id=None,
                    codigo_plan="Inconsistencia de planes",
                    tipo_plan="",
                    estado_plan="INCONSISTENTE",
                    cuotas_pendientes=0,
                    cuotas_en_mora=0,
                    saldo_vivo_centavos=0,
                    cuotas_cobrables=(),
                    permite_continuar=False,
                    estado_visual="",
                    mensaje_diagnostico="",
                    alertas=(),
                )
            fila_plan = filas_planes[0]
            cuotas = conexion.execute(consulta_cuotas, (int(fila_plan["id"]),)).fetchall()
        cuotas_cobrables = tuple(
            CuotaPlanCobrable(
                cuota_id=int(fila["id"]),
                plan_pago_id=int(fila["plan_pago_id"]),
                numero_cuota=int(fila["numero_cuota"]),
                fecha_vencimiento=str(fila["fecha_vencimiento"] or ""),
                estado=str(fila["estado"] or "PENDIENTE"),
                saldo_pendiente_centavos=int(fila["saldo_pendiente_centavos"] or 0),
            )
            for fila in cuotas
        )
        plan_id = int(fila_plan["id"])
        return DiagnosticoPagoPlan(
            casa_id=casa_id,
            cantidad_planes_activos=1,
            plan_pago_id=plan_id,
            codigo_plan=f"PP-{plan_id:03d}",
            tipo_plan=str(fila_plan["tipo_plan"] or ""),
            estado_plan=str(fila_plan["estado_plan"] or "ACTIVO"),
            cuotas_pendientes=int(fila_plan["cuotas_pendientes"] or 0),
            cuotas_en_mora=int(fila_plan["cuotas_en_mora"] or 0),
            saldo_vivo_centavos=int(fila_plan["saldo_pendiente_centavos"] or 0),
            cuotas_cobrables=cuotas_cobrables,
            permite_continuar=bool(cuotas_cobrables),
            estado_visual="",
            mensaje_diagnostico="",
            alertas=(),
        )

    def listar_cargos_mensuales(self, casa_id: int) -> list[CargoPago]:
        consulta = """
            SELECT
                v.id,
                v.casa_id,
                v.abonado_id,
                v.periodo_id,
                pc.anio AS periodo_anio,
                pc.mes AS periodo_mes,
                v.periodo_nombre,
                v.concepto_codigo,
                v.descripcion,
                v.saldo_pendiente_centavos,
                v.fecha_vencimiento,
                v.estado
            FROM vw_cargos_pendientes_ordenados v
            LEFT JOIN periodos_cobro pc ON pc.id = v.periodo_id
            WHERE v.casa_id = ?
              AND v.concepto_codigo = 'SERVICIO_MENSUAL'
            ORDER BY v.fecha_vencimiento ASC, v.id ASC;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            filas = conexion.execute(consulta, (casa_id,)).fetchall()
        return [
            CargoPago(
                identificador=int(fila["id"]),
                casa_id=int(fila["casa_id"]),
                abonado_id=int(fila["abonado_id"]),
                periodo_id=int(fila["periodo_id"]) if fila["periodo_id"] is not None else None,
                periodo_anio=int(fila["periodo_anio"]) if fila["periodo_anio"] is not None else None,
                periodo_mes=int(fila["periodo_mes"]) if fila["periodo_mes"] is not None else None,
                periodo_nombre=str(fila["periodo_nombre"] or ""),
                concepto_codigo=str(fila["concepto_codigo"] or ""),
                descripcion=str(fila["descripcion"] or ""),
                saldo_pendiente_centavos=int(fila["saldo_pendiente_centavos"] or 0),
                fecha_vencimiento=str(fila["fecha_vencimiento"] or ""),
                estado=str(fila["estado"] or "PENDIENTE"),
            )
            for fila in filas
        ]

    def obtener_resumen_deuda_pago(self, casa_id: int) -> ResumenDeudaPago:
        consulta = """
            SELECT
                COALESCE(SUM(c.saldo_pendiente_centavos), 0) AS deuda_total_centavos,
                COALESCE(
                    SUM(
                        CASE
                            WHEN cc.codigo = 'SERVICIO_MENSUAL'
                            THEN c.saldo_pendiente_centavos
                            ELSE 0
                        END
                    ),
                    0
                ) AS deuda_mensual_centavos,
                COALESCE(
                    SUM(
                        CASE
                            WHEN c.estado = 'VENCIDO'
                            THEN c.saldo_pendiente_centavos
                            ELSE 0
                        END
                    ),
                    0
                ) AS deuda_vencida_centavos,
                COALESCE(
                    SUM(
                        CASE
                            WHEN c.estado = 'VENCIDO'
                             AND cc.codigo <> 'SERVICIO_MENSUAL'
                            THEN c.saldo_pendiente_centavos
                            ELSE 0
                        END
                    ),
                    0
                ) AS deuda_vencida_no_mensual_centavos
            FROM cargos c
            INNER JOIN conceptos_cobro cc ON cc.id = c.concepto_id
            WHERE c.casa_id = ?
              AND c.estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDO')
              AND c.saldo_pendiente_centavos > 0
              AND c.anulado_en IS NULL;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            fila = conexion.execute(consulta, (casa_id,)).fetchone()
        return ResumenDeudaPago(
            deuda_total_centavos=int(fila["deuda_total_centavos"] or 0),
            deuda_mensual_centavos=int(fila["deuda_mensual_centavos"] or 0),
            deuda_vencida_centavos=int(fila["deuda_vencida_centavos"] or 0),
            deuda_vencida_no_mensual_centavos=int(
                fila["deuda_vencida_no_mensual_centavos"] or 0
            ),
        )

    def listar_metodos_pago_activos(self) -> list[MetodoPago]:
        consulta = """
            SELECT id, codigo, nombre, COALESCE(requiere_referencia, 0) AS requiere_referencia
            FROM metodos_pago
            WHERE estado = 'ACTIVO'
            ORDER BY
                CASE codigo
                    WHEN 'EFECTIVO' THEN 1
                    WHEN 'TRANSFERENCIA' THEN 2
                    WHEN 'DEPOSITO' THEN 3
                    ELSE 9
                END,
                nombre;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            filas = conexion.execute(consulta).fetchall()
        return [self._fila_a_metodo(fila) for fila in filas]

    def obtener_metodo_pago(self, metodo_pago_id: int) -> MetodoPago | None:
        consulta = """
            SELECT id, codigo, nombre, COALESCE(requiere_referencia, 0) AS requiere_referencia
            FROM metodos_pago
            WHERE id = ? AND estado = 'ACTIVO'
            LIMIT 1;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            fila = conexion.execute(consulta, (metodo_pago_id,)).fetchone()
        return self._fila_a_metodo(fila) if fila is not None else None

    def listar_historial(self, limite: int = 20) -> list[HistorialPago]:
        consulta = """
            SELECT
                p.id AS pago_id,
                COALESCE(c.numero_comprobante, 'Sin comprobante') AS numero_comprobante,
                COALESCE(p.tipo_pago, 'MENSUALIDAD') AS tipo_pago,
                a.nombre_completo AS abonado_nombre,
                printf('CA-%03d', p.casa_id) AS casa_codigo,
                mp.nombre AS metodo_pago,
                p.total_pagado_centavos,
                p.fecha_pago
            FROM pagos p
            INNER JOIN abonados a ON a.id = p.abonado_id
            INNER JOIN metodos_pago mp ON mp.id = p.metodo_pago_id
            LEFT JOIN comprobantes c ON c.pago_id = p.id
            WHERE p.estado = 'CONFIRMADO'
            ORDER BY p.fecha_pago DESC, p.id DESC
            LIMIT ?;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            filas = conexion.execute(consulta, (limite,)).fetchall()
        return [
            HistorialPago(
                pago_id=int(fila["pago_id"]),
                numero_comprobante=str(fila["numero_comprobante"] or ""),
                tipo_pago=str(fila["tipo_pago"] or TIPO_PAGO_MENSUALIDAD),
                abonado_nombre=str(fila["abonado_nombre"] or ""),
                casa_codigo=str(fila["casa_codigo"] or ""),
                metodo_pago=str(fila["metodo_pago"] or ""),
                total_pagado_centavos=int(fila["total_pagado_centavos"] or 0),
                fecha_pago=str(fila["fecha_pago"] or ""),
            )
            for fila in filas
        ]

    def obtener_precio_mensual_centavos(self) -> int:
        consulta = """
            SELECT valor
            FROM configuracion_sistema
            WHERE clave = 'cobro.precio_mensual_centavos'
            LIMIT 1;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            fila = conexion.execute(consulta).fetchone()
        if fila is None:
            return 0
        try:
            return int(str(fila["valor"] or "0"))
        except ValueError:
            return 0

    def cobrar_mensualidad_prorrateada_en_activacion(self) -> bool:
        consulta = """
            SELECT valor
            FROM configuracion_sistema
            WHERE clave = 'cobro.cobrar_mensualidad_prorrateada_activacion'
            LIMIT 1;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            fila = conexion.execute(consulta).fetchone()
        if fila is None:
            return False
        return self._a_booleano(str(fila["valor"] or "0"))

    def guardar_pago_confirmado(
        self,
        resumen: ResumenConfirmacionPago,
        actor_id: int,
    ) -> ComprobantePago:
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                pago_id = self._insertar_pago(conexion, resumen, actor_id)
                if resumen.tipo_pago == TIPO_PAGO_MENSUALIDAD:
                    self._persistir_detalles_mensualidad(conexion, pago_id, resumen)
                elif resumen.tipo_pago == TIPO_PAGO_PLAN:
                    self._persistir_detalles_plan_pago(conexion, pago_id, resumen)
                else:
                    self._persistir_detalles_activacion(conexion, pago_id, resumen, actor_id)

                numero_comprobante = self._generar_numero_comprobante(conexion)
                conexion.execute(
                    """
                    INSERT INTO comprobantes(
                        pago_id,
                        numero_comprobante,
                        tipo_comprobante,
                        saldo_posterior_centavos,
                        generado_por
                    )
                    VALUES (?, ?, ?, ?, ?);
                    """,
                    (
                        pago_id,
                        numero_comprobante,
                        resumen.tipo_pago,
                        resumen.saldo_posterior_centavos,
                        actor_id,
                    ),
                )
        comprobante = self.obtener_comprobante(pago_id)
        if comprobante is None:
            raise ValueError("No fue posible recuperar el comprobante recien generado.")
        return comprobante

    def guardar_operacion_compuesta_confirmada(
        self,
        resumen: ResumenConfirmacionPago,
        actor_id: int,
    ) -> tuple[ComprobantePago, ...]:
        if not resumen.es_operacion_compuesta:
            comprobante = self.guardar_pago_confirmado(resumen, actor_id)
            return (comprobante,)
        detalles_regularizacion = tuple(
            detalle
            for detalle in resumen.detalles
            if detalle.tipo_pago_destino == TIPO_PAGO_MENSUALIDAD
        )
        detalles_activacion = tuple(
            detalle
            for detalle in resumen.detalles
            if detalle.tipo_pago_destino != TIPO_PAGO_MENSUALIDAD
        )
        if not detalles_regularizacion or not detalles_activacion:
            raise ValueError("La reconexion compuesta requiere detalles separados de regularizacion y activacion.")
        total_regularizacion = sum(detalle.monto_centavos for detalle in detalles_regularizacion)
        total_activacion = sum(detalle.monto_centavos for detalle in detalles_activacion)
        saldo_posterior = max(0, resumen.saldo_anterior_centavos - total_regularizacion)
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                cursor_operacion = conexion.execute(
                    """
                    INSERT INTO operaciones_cobro(
                        abonado_id,
                        casa_id,
                        tipo_operacion,
                        estado,
                        descripcion,
                        creado_por
                    )
                    VALUES (?, ?, 'RECONEXION_COMPUESTA', 'CONFIRMADA', ?, ?);
                    """,
                    (
                        resumen.casa.abonado_id,
                        resumen.casa.casa_id,
                        "Reconexion con regularizacion de deuda activa.",
                        actor_id,
                    ),
                )
                operacion_id = int(cursor_operacion.lastrowid)
                resumen_regularizacion = ResumenConfirmacionPago(
                    casa=resumen.casa,
                    tipo_pago=TIPO_PAGO_MENSUALIDAD,
                    metodo_pago=resumen.metodo_pago,
                    detalles=detalles_regularizacion,
                    saldo_anterior_centavos=resumen.saldo_anterior_centavos,
                    total_pago_centavos=total_regularizacion,
                    saldo_posterior_centavos=saldo_posterior,
                    referencia=resumen.referencia,
                    observaciones=(resumen.observaciones or "").strip() or "Regularizacion previa a reconexion.",
                    operacion_cobro_id=operacion_id,
                )
                pago_regularizacion_id = self._insertar_pago(conexion, resumen_regularizacion, actor_id)
                self._persistir_detalles_mensualidad(conexion, pago_regularizacion_id, resumen_regularizacion)
                numero_regularizacion = self._generar_numero_comprobante(conexion)
                conexion.execute(
                    """
                    INSERT INTO comprobantes(
                        pago_id,
                        numero_comprobante,
                        tipo_comprobante,
                        saldo_posterior_centavos,
                        generado_por
                    )
                    VALUES (?, ?, ?, ?, ?);
                    """,
                    (
                        pago_regularizacion_id,
                        numero_regularizacion,
                        TIPO_PAGO_MENSUALIDAD,
                        saldo_posterior,
                        actor_id,
                    ),
                )
                resumen_activacion = ResumenConfirmacionPago(
                    casa=self.obtener_casa(resumen.casa.casa_id) or resumen.casa,
                    tipo_pago=TIPO_PAGO_RECONEXION,
                    metodo_pago=resumen.metodo_pago,
                    detalles=detalles_activacion,
                    saldo_anterior_centavos=saldo_posterior,
                    total_pago_centavos=total_activacion,
                    saldo_posterior_centavos=saldo_posterior,
                    referencia=resumen.referencia,
                    observaciones=resumen.observaciones,
                    fecha_activacion=resumen.fecha_activacion,
                    operacion_cobro_id=operacion_id,
                    prorrateo_pendiente_centavos=resumen.prorrateo_pendiente_centavos,
                    prorrateo_pendiente_anio=resumen.prorrateo_pendiente_anio,
                    prorrateo_pendiente_mes=resumen.prorrateo_pendiente_mes,
                    prorrateo_pendiente_descripcion=resumen.prorrateo_pendiente_descripcion,
                )
                pago_activacion_id = self._insertar_pago(conexion, resumen_activacion, actor_id)
                self._persistir_detalles_activacion(conexion, pago_activacion_id, resumen_activacion, actor_id)
                numero_activacion = self._generar_numero_comprobante(conexion)
                conexion.execute(
                    """
                    INSERT INTO comprobantes(
                        pago_id,
                        numero_comprobante,
                        tipo_comprobante,
                        saldo_posterior_centavos,
                        generado_por
                    )
                    VALUES (?, ?, ?, ?, ?);
                    """,
                    (
                        pago_activacion_id,
                        numero_activacion,
                        TIPO_PAGO_RECONEXION,
                        saldo_posterior,
                        actor_id,
                    ),
                )
        comprobante_regularizacion = self.obtener_comprobante(pago_regularizacion_id)
        comprobante_activacion = self.obtener_comprobante(pago_activacion_id)
        if comprobante_regularizacion is None or comprobante_activacion is None:
            raise ValueError("No fue posible recuperar los comprobantes de la reconexion compuesta.")
        return (comprobante_regularizacion, comprobante_activacion)

    def obtener_comprobante(self, pago_id: int) -> ComprobantePago | None:
        consulta = """
            SELECT
                p.id AS pago_id,
                co.numero_comprobante,
                COALESCE(co.tipo_comprobante, 'MENSUALIDAD') AS tipo_comprobante,
                COALESCE(co.saldo_posterior_centavos, 0) AS saldo_posterior_centavos,
                co.generado_en,
                printf('CA-%03d', p.casa_id) AS casa_codigo,
                a.nombre_completo AS abonado_nombre,
                a.dni AS abonado_dni,
                COALESCE(b.nombre, '') AS barrio_nombre,
                COALESCE(c.direccion_referencia, '') AS direccion_casa,
                mp.nombre AS metodo_pago,
                COALESCE(p.referencia_externa, '') AS referencia,
                COALESCE(u.nombre_completo, u.nombre_usuario, '') AS usuario_registro,
                p.total_pagado_centavos
            FROM comprobantes co
            INNER JOIN pagos p ON p.id = co.pago_id
            INNER JOIN abonados a ON a.id = p.abonado_id
            INNER JOIN casas c ON c.id = p.casa_id
            LEFT JOIN barrios b ON b.id = c.barrio_id
            INNER JOIN metodos_pago mp ON mp.id = p.metodo_pago_id
            LEFT JOIN usuarios u ON u.id = p.usuario_cobrador_id
            WHERE p.id = ?
            LIMIT 1;
        """
        consulta_detalles = """
            SELECT descripcion, monto_pagado_centavos
            FROM pagos_detalle
            WHERE pago_id = ?
            ORDER BY orden_aplicacion ASC, id ASC;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            fila = conexion.execute(consulta, (pago_id,)).fetchone()
            if fila is None:
                return None
            filas_detalle = conexion.execute(consulta_detalles, (pago_id,)).fetchall()
        detalles = tuple(
            f"{str(item['descripcion'] or '').strip()} - L {int(item['monto_pagado_centavos'] or 0) / 100:,.2f}"
            for item in filas_detalle
        )
        return ComprobantePago(
            pago_id=int(fila["pago_id"]),
            numero_comprobante=str(fila["numero_comprobante"] or ""),
            tipo_comprobante=str(fila["tipo_comprobante"] or TIPO_PAGO_MENSUALIDAD),
            generado_en=str(fila["generado_en"] or ""),
            casa_codigo=str(fila["casa_codigo"] or ""),
            abonado_nombre=str(fila["abonado_nombre"] or ""),
            abonado_dni=str(fila["abonado_dni"] or ""),
            barrio_nombre=str(fila["barrio_nombre"] or ""),
            direccion_casa=str(fila["direccion_casa"] or ""),
            metodo_pago=str(fila["metodo_pago"] or ""),
            referencia=str(fila["referencia"] or ""),
            usuario_registro=str(fila["usuario_registro"] or ""),
            total_pagado_centavos=int(fila["total_pagado_centavos"] or 0),
            saldo_posterior_centavos=int(fila["saldo_posterior_centavos"] or 0),
            detalles=detalles,
        )

    def obtener_configuracion_recibo(self) -> ConfiguracionReciboPago:
        claves = (
            *CLAVES_IDENTIDAD_EMPRESA,
            *CLAVES_IDENTIDAD_LEGADAS_JUNTA,
            "factura.titulo_documento",
            "factura.subtitulo_documento",
            "factura.texto_legal_superior",
            "factura.texto_pie",
            "factura.texto_legal_inferior",
            "factura.etiqueta_copia",
            "factura.mostrar_correo",
            "factura.mostrar_telefono",
            "factura.mostrar_direccion",
            "factura.mostrar_identificador_fiscal",
            "documentos.firma_habilitada",
            "documentos.firma_texto_linea",
        )
        marcadores = ", ".join("?" for _ in claves)
        consulta = f"""
            SELECT clave, COALESCE(valor, '') AS valor
            FROM configuracion_sistema
            WHERE clave IN ({marcadores});
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            filas = conexion.execute(consulta, claves).fetchall()
        valores = {str(fila["clave"]): str(fila["valor"] or "") for fila in filas}
        identidad = construir_identidad_empresa(valores, nombre_predeterminado="SIGQUA")
        texto_firma = valores.get("documentos.firma_texto_linea", "").strip() or "Firma autorizada"
        return ConfiguracionReciboPago(
            nombre_junta=identidad.nombre,
            telefono_junta=identidad.telefono,
            correo_junta=identidad.correo,
            direccion_junta=identidad.direccion,
            identificador_fiscal=identidad.identificador_fiscal,
            sitio_web=identidad.sitio_web,
            mensaje_contacto=identidad.mensaje_contacto,
            titulo_documento=valores.get("factura.titulo_documento", "RECIBO DE PAGO") or "RECIBO DE PAGO",
            subtitulo_documento=valores.get("factura.subtitulo_documento", ""),
            texto_legal_superior=valores.get("factura.texto_legal_superior", ""),
            texto_pie=valores.get("factura.texto_pie", ""),
            texto_legal_inferior=valores.get("factura.texto_legal_inferior", ""),
            etiqueta_copia=valores.get("factura.etiqueta_copia", "ORIGINAL") or "ORIGINAL",
            mostrar_correo=self._a_booleano(valores.get("factura.mostrar_correo", "1")),
            mostrar_telefono=self._a_booleano(valores.get("factura.mostrar_telefono", "1")),
            mostrar_direccion=self._a_booleano(valores.get("factura.mostrar_direccion", "1")),
            mostrar_identificador_fiscal=self._a_booleano(
                valores.get("factura.mostrar_identificador_fiscal", "0")
            ),
            firma_habilitada=self._a_booleano(valores.get("documentos.firma_habilitada", "0")),
            firma_texto_linea=texto_firma,
        )

    def _insertar_pago(
        self,
        conexion: object,
        resumen: ResumenConfirmacionPago,
        actor_id: int,
    ) -> int:
        cursor = conexion.execute(
            """
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
                observaciones,
                tipo_pago,
                plan_pago_id,
                operacion_cobro_id
            )
            VALUES (?, ?, ?, ?, ?, ?, 0, ?, 0, ?, ?, ?, ?);
            """,
            (
                resumen.casa.abonado_id,
                resumen.casa.casa_id,
                actor_id,
                resumen.metodo_pago.identificador,
                resumen.referencia or None,
                resumen.total_pago_centavos,
                resumen.total_pago_centavos,
                resumen.observaciones or None,
                resumen.tipo_pago,
                resumen.plan_pago_id,
                resumen.operacion_cobro_id,
            ),
        )
        return int(cursor.lastrowid)

    def _persistir_detalles_mensualidad(
        self,
        conexion: object,
        pago_id: int,
        resumen: ResumenConfirmacionPago,
    ) -> None:
        concepto_mensualidad_id = self._obtener_concepto_id(conexion, "SERVICIO_MENSUAL")
        for orden, detalle in enumerate(resumen.detalles, start=1):
            cargo_id = detalle.cargo_id
            periodo_id = detalle.periodo_id
            if detalle.es_adelantado:
                if detalle.periodo_anio is None or detalle.periodo_mes is None:
                    raise ValueError("Periodo adelantado incompleto.")
                periodo_id = self._asegurar_periodo(conexion, detalle.periodo_anio, detalle.periodo_mes)
                cargo_id = self._crear_cargo_adelantado(
                    conexion,
                    resumen,
                    detalle,
                    periodo_id,
                    concepto_mensualidad_id,
                )
                conexion.execute(
                    """
                    INSERT INTO pagos_adelantados(
                        abonado_id,
                        casa_id,
                        pago_id,
                        periodo_id,
                        monto_centavos,
                        observaciones
                    )
                    VALUES (?, ?, ?, ?, ?, ?);
                    """,
                    (
                        resumen.casa.abonado_id,
                        resumen.casa.casa_id,
                        pago_id,
                        periodo_id,
                        detalle.monto_centavos,
                        "Mensualidad pagada por adelantado.",
                    ),
                )
            elif cargo_id is not None:
                self._actualizar_saldo_cargo(conexion, cargo_id, detalle.monto_centavos)

            conexion.execute(
                """
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
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    pago_id,
                    resumen.casa.casa_id,
                    cargo_id,
                    concepto_mensualidad_id,
                    detalle.descripcion,
                    detalle.monto_centavos,
                    periodo_id,
                    orden,
                ),
            )

    def _persistir_detalles_plan_pago(
        self,
        conexion: object,
        pago_id: int,
        resumen: ResumenConfirmacionPago,
    ) -> None:
        if not resumen.detalles:
            raise ValueError("El pago de plan requiere al menos una cuota seleccionada.")
        concepto_cuota_id = self._obtener_concepto_id(conexion, "CUOTA_PLAN_PAGO")
        plan_pago_id: int | None = None
        cuotas_pagadas = 0
        for orden, detalle in enumerate(resumen.detalles, start=1):
            if detalle.cargo_id is None:
                raise ValueError("Cada detalle de plan debe identificar una cuota del plan.")
            fila_cuota = conexion.execute(
                """
                SELECT plan_pago_id, saldo_pendiente_centavos
                FROM cuotas_plan_pago
                WHERE id = ?
                LIMIT 1;
                """,
                (detalle.cargo_id,),
            ).fetchone()
            if fila_cuota is None:
                raise ValueError("Una de las cuotas seleccionadas ya no existe.")
            plan_id_actual = int(fila_cuota["plan_pago_id"])
            saldo_actual = int(fila_cuota["saldo_pendiente_centavos"] or 0)
            if plan_pago_id is None:
                plan_pago_id = plan_id_actual
            elif plan_pago_id != plan_id_actual:
                raise ValueError("No se pueden mezclar cuotas de planes distintos en un mismo pago.")
            if saldo_actual <= 0:
                raise ValueError("Una de las cuotas seleccionadas ya no tiene saldo pendiente.")
            nuevo_saldo = max(0, saldo_actual - detalle.monto_centavos)
            nuevo_estado = "PAGADO" if nuevo_saldo == 0 else "PARCIAL"
            conexion.execute(
                """
                UPDATE cuotas_plan_pago
                SET saldo_pendiente_centavos = ?,
                    estado = ?,
                    actualizado_en = datetime('now', 'localtime')
                WHERE id = ?;
                """,
                (nuevo_saldo, nuevo_estado, detalle.cargo_id),
            )
            if nuevo_estado == "PAGADO":
                cuotas_pagadas += 1
            conexion.execute(
                """
                INSERT INTO pagos_detalle(
                    pago_id,
                    casa_id,
                    concepto_id,
                    descripcion,
                    monto_pagado_centavos,
                    orden_aplicacion,
                    cuota_plan_pago_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    pago_id,
                    resumen.casa.casa_id,
                    concepto_cuota_id,
                    detalle.descripcion,
                    detalle.monto_centavos,
                    orden,
                    detalle.cargo_id,
                ),
            )
        if plan_pago_id is None:
            raise ValueError("No fue posible resolver el plan asociado al pago.")
        fila_resumen = conexion.execute(
            """
            SELECT
                COUNT(*) AS total_cuotas,
                COUNT(CASE WHEN estado = 'PAGADO' THEN 1 END) AS cuotas_pagadas,
                COUNT(
                    CASE
                        WHEN estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDO')
                         AND saldo_pendiente_centavos > 0
                        THEN 1
                    END
                ) AS cuotas_pendientes
            FROM cuotas_plan_pago
            WHERE plan_pago_id = ?;
            """,
            (plan_pago_id,),
        ).fetchone()
        total_cuotas = int(fila_resumen["total_cuotas"] or 0)
        cuotas_pagadas_reales = int(fila_resumen["cuotas_pagadas"] or 0)
        cuotas_pendientes = int(fila_resumen["cuotas_pendientes"] or 0)
        estado_plan = "FINALIZADO" if total_cuotas > 0 and cuotas_pendientes == 0 else "ACTIVO"
        conexion.execute(
            """
            UPDATE planes_pago
            SET cuotas_pagadas = ?,
                estado = ?,
                actualizado_en = datetime('now', 'localtime')
            WHERE id = ?;
            """,
            (cuotas_pagadas_reales, estado_plan, plan_pago_id),
        )

    def _persistir_detalles_activacion(
        self,
        conexion: object,
        pago_id: int,
        resumen: ResumenConfirmacionPago,
        actor_id: int,
    ) -> None:
        observaciones = (resumen.fecha_activacion or "").strip()
        try:
            fecha_activacion = date.fromisoformat(observaciones)
        except ValueError:
            fecha_activacion = date.today()

        monto_conexion = 0
        monto_reconexion = 0
        cobra_prorrateo = 0
        precio_mensual_base = None
        dias_mes = None
        dias_cobrados = None
        monto_prorrateado = 0
        for detalle in resumen.detalles:
            if detalle.concepto_codigo == "CONEXION":
                monto_conexion = detalle.monto_centavos
            elif detalle.concepto_codigo == "RECONEXION":
                monto_reconexion = detalle.monto_centavos
            elif detalle.concepto_codigo == "MENSUALIDAD_PRORRATEADA":
                cobra_prorrateo = 1
                monto_prorrateado = detalle.monto_centavos
                precio_mensual_base = self.obtener_precio_mensual_centavos()
                dias_mes = monthrange(fecha_activacion.year, fecha_activacion.month)[1]
                dias_cobrados = (dias_mes - fecha_activacion.day) + 1
        if resumen.prorrateo_pendiente_centavos > 0 and not cobra_prorrateo:
            monto_prorrateado = resumen.prorrateo_pendiente_centavos
            precio_mensual_base = self.obtener_precio_mensual_centavos()
            dias_mes = monthrange(fecha_activacion.year, fecha_activacion.month)[1]
            dias_cobrados = (dias_mes - fecha_activacion.day) + 1

        cursor_proceso = conexion.execute(
            """
            INSERT INTO procesos_servicio(
                abonado_id,
                casa_id,
                tipo,
                fecha_ejecucion,
                fecha_activacion,
                estado,
                motivo,
                observaciones,
                pago_id,
                usuario_id,
                cobra_mensualidad_prorrateada,
                precio_mensual_base_centavos,
                dias_mes,
                dias_cobrados,
                monto_prorrateado_centavos,
                monto_conexion_centavos,
                monto_reconexion_centavos
            )
            VALUES (?, ?, ?, datetime('now', 'localtime'), ?, 'EJECUTADO', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                resumen.casa.abonado_id,
                resumen.casa.casa_id,
                resumen.tipo_pago,
                fecha_activacion.isoformat(),
                f"{resumen.tipo_pago} ejecutada desde pagos",
                resumen.observaciones or None,
                pago_id,
                actor_id,
                cobra_prorrateo,
                precio_mensual_base,
                dias_mes,
                dias_cobrados,
                monto_prorrateado if monto_prorrateado > 0 else None,
                monto_conexion if monto_conexion > 0 else None,
                monto_reconexion if monto_reconexion > 0 else None,
            ),
        )
        proceso_servicio_id = int(cursor_proceso.lastrowid)

        for orden, detalle in enumerate(resumen.detalles, start=1):
            periodo_id = detalle.periodo_id
            if detalle.concepto_codigo == "MENSUALIDAD_PRORRATEADA":
                if detalle.periodo_anio is None or detalle.periodo_mes is None:
                    raise ValueError("El prorrateo requiere periodo.")
                periodo_id = self._asegurar_periodo(conexion, detalle.periodo_anio, detalle.periodo_mes)
            concepto_id = self._obtener_concepto_id(conexion, detalle.concepto_codigo)
            fecha_vencimiento = fecha_activacion.isoformat()
            if periodo_id is not None:
                fila_periodo = conexion.execute(
                    "SELECT fecha_vencimiento FROM periodos_cobro WHERE id = ? LIMIT 1;",
                    (periodo_id,),
                ).fetchone()
                if fila_periodo is not None:
                    fecha_vencimiento = str(fila_periodo["fecha_vencimiento"] or fecha_vencimiento)
            cursor_cargo = conexion.execute(
                """
                INSERT INTO cargos(
                    casa_id,
                    abonado_id,
                    periodo_id,
                    concepto_id,
                    proceso_servicio_id,
                    descripcion,
                    monto_centavos,
                    saldo_pendiente_centavos,
                    fecha_generacion,
                    fecha_vencimiento,
                    estado,
                    origen
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, 0, date('now', 'localtime'), ?, 'PAGADO', 'PROCESO_SERVICIO');
                """,
                (
                    resumen.casa.casa_id,
                    resumen.casa.abonado_id,
                    periodo_id,
                    concepto_id,
                    proceso_servicio_id,
                    detalle.descripcion,
                    detalle.monto_centavos,
                    fecha_vencimiento,
                ),
            )
            cargo_id = int(cursor_cargo.lastrowid)
            conexion.execute(
                """
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
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    pago_id,
                    resumen.casa.casa_id,
                    cargo_id,
                    concepto_id,
                    detalle.descripcion,
                    detalle.monto_centavos,
                    periodo_id,
                    orden,
                ),
            )

        if resumen.prorrateo_pendiente_centavos > 0:
            if resumen.prorrateo_pendiente_anio is None or resumen.prorrateo_pendiente_mes is None:
                raise ValueError("El prorrateo pendiente requiere periodo.")
            periodo_id = self._asegurar_periodo(
                conexion,
                resumen.prorrateo_pendiente_anio,
                resumen.prorrateo_pendiente_mes,
            )
            concepto_id = self._obtener_concepto_id(conexion, "MENSUALIDAD_PRORRATEADA")
            fila_periodo = conexion.execute(
                "SELECT fecha_vencimiento FROM periodos_cobro WHERE id = ? LIMIT 1;",
                (periodo_id,),
            ).fetchone()
            fecha_vencimiento = (
                str(fila_periodo["fecha_vencimiento"])
                if fila_periodo is not None and fila_periodo["fecha_vencimiento"]
                else fecha_activacion.isoformat()
            )
            conexion.execute(
                """
                INSERT INTO cargos(
                    casa_id,
                    abonado_id,
                    periodo_id,
                    concepto_id,
                    proceso_servicio_id,
                    descripcion,
                    monto_centavos,
                    saldo_pendiente_centavos,
                    fecha_generacion,
                    fecha_vencimiento,
                    estado,
                    origen
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, date('now', 'localtime'), ?, 'PENDIENTE', 'PROCESO_SERVICIO');
                """,
                (
                    resumen.casa.casa_id,
                    resumen.casa.abonado_id,
                    periodo_id,
                    concepto_id,
                    proceso_servicio_id,
                    resumen.prorrateo_pendiente_descripcion
                    or f"Mensualidad prorrateada desde {fecha_activacion.isoformat()}",
                    resumen.prorrateo_pendiente_centavos,
                    resumen.prorrateo_pendiente_centavos,
                    fecha_vencimiento,
                ),
            )

        conexion.execute(
            """
            UPDATE casas
            SET estado_servicio = 'ACTIVO',
                estado_administrativo = 'OPERATIVA',
                motivo_estado_administrativo = 'NINGUNO',
                ha_tenido_servicio_activo = 1,
                actualizado_en = datetime('now', 'localtime')
            WHERE id = ?;
            """,
            (resumen.casa.casa_id,),
        )

    @staticmethod
    def _actualizar_saldo_cargo(conexion: object, cargo_id: int, monto_pagado: int) -> None:
        fila = conexion.execute(
            """
            SELECT saldo_pendiente_centavos
            FROM cargos
            WHERE id = ?;
            """,
            (cargo_id,),
        ).fetchone()
        if fila is None:
            raise ValueError("Cargo no encontrado.")
        saldo_actual = int(fila["saldo_pendiente_centavos"] or 0)
        if monto_pagado > saldo_actual:
            raise ValueError("El pago excede el saldo del cargo.")
        nuevo_saldo = saldo_actual - monto_pagado
        nuevo_estado = "PAGADO" if nuevo_saldo == 0 else "PARCIAL"
        conexion.execute(
            """
            UPDATE cargos
            SET saldo_pendiente_centavos = ?,
                estado = ?,
                actualizado_en = datetime('now', 'localtime')
            WHERE id = ?;
            """,
            (nuevo_saldo, nuevo_estado, cargo_id),
        )

    @staticmethod
    def _obtener_concepto_id(conexion: object, codigo: str) -> int:
        fila = conexion.execute(
            "SELECT id FROM conceptos_cobro WHERE codigo = ? LIMIT 1;",
            (codigo,),
        ).fetchone()
        if fila is None:
            raise ValueError(f"No existe el concepto de cobro {codigo}.")
        return int(fila["id"])

    @staticmethod
    def _asegurar_periodo(conexion: object, anio: int, mes: int) -> int:
        fila = conexion.execute(
            "SELECT id FROM periodos_cobro WHERE anio = ? AND mes = ? LIMIT 1;",
            (anio, mes),
        ).fetchone()
        if fila is not None:
            return int(fila["id"])
        ultimo_dia = monthrange(anio, mes)[1]
        fecha_inicio = f"{anio:04d}-{mes:02d}-01"
        fecha_fin = f"{anio:04d}-{mes:02d}-{ultimo_dia:02d}"
        fecha_vencimiento = f"{anio:04d}-{mes:02d}-10"
        cursor = conexion.execute(
            """
            INSERT INTO periodos_cobro(
                anio,
                mes,
                nombre,
                fecha_inicio,
                fecha_fin,
                fecha_vencimiento
            )
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            (
                anio,
                mes,
                f"Periodo {mes:02d}/{anio:04d}",
                fecha_inicio,
                fecha_fin,
                fecha_vencimiento,
            ),
        )
        return int(cursor.lastrowid)

    @staticmethod
    def _crear_cargo_adelantado(
        conexion: object,
        resumen: ResumenConfirmacionPago,
        detalle: DetalleAplicacionPago,
        periodo_id: int,
        concepto_id: int,
    ) -> int:
        fila_periodo = conexion.execute(
            """
            SELECT fecha_vencimiento
            FROM periodos_cobro
            WHERE id = ?;
            """,
            (periodo_id,),
        ).fetchone()
        cursor = conexion.execute(
            """
            INSERT INTO cargos(
                casa_id,
                abonado_id,
                periodo_id,
                concepto_id,
                descripcion,
                monto_centavos,
                saldo_pendiente_centavos,
                fecha_vencimiento,
                estado,
                origen
            )
            VALUES (?, ?, ?, ?, ?, ?, 0, ?, 'PAGADO', 'ADELANTO');
            """,
            (
                resumen.casa.casa_id,
                resumen.casa.abonado_id,
                periodo_id,
                concepto_id,
                detalle.descripcion,
                detalle.monto_centavos,
                str(fila_periodo["fecha_vencimiento"]),
            ),
        )
        return int(cursor.lastrowid)

    @staticmethod
    def _generar_numero_comprobante(conexion: object) -> str:
        conexion.execute(
            """
            INSERT OR IGNORE INTO correlativos_comprobantes(clave, ultimo_numero)
            VALUES ('RECIBO_GLOBAL', 0);
            """
        )
        conexion.execute(
            """
            UPDATE correlativos_comprobantes
            SET ultimo_numero = ultimo_numero + 1,
                actualizado_en = datetime('now', 'localtime')
            WHERE clave = 'RECIBO_GLOBAL';
            """
        )
        fila = conexion.execute(
            """
            SELECT ultimo_numero
            FROM correlativos_comprobantes
            WHERE clave = 'RECIBO_GLOBAL';
            """
        ).fetchone()
        return f"REC-{int(fila['ultimo_numero']):06d}"

    @staticmethod
    def _fila_a_casa(fila: object) -> CasaPago:
        return CasaPago(
            casa_id=int(fila["casa_id"]),
            casa_codigo=str(fila["casa_codigo"]),
            abonado_id=int(fila["abonado_id"]),
            abonado_nombre=str(fila["abonado_nombre"] or ""),
            abonado_dni=str(fila["abonado_dni"] or ""),
            abonado_estado=str(fila["abonado_estado"] or "ACTIVO"),
            barrio_nombre=str(fila["barrio_nombre"] or ""),
            estado_servicio=str(fila["estado_servicio"] or "ACTIVO"),
            estado_administrativo=str(fila["estado_administrativo"] or "OPERATIVA"),
            motivo_estado_administrativo=str(
                fila["motivo_estado_administrativo"] or "NINGUNO"
            ),
            ha_tenido_servicio_activo=bool(int(fila["ha_tenido_servicio_activo"] or 0)),
            meses_pendientes=int(fila["meses_pendientes"] or 0),
            meses_vencidos=int(fila["meses_vencidos"] or 0),
            deuda_total_centavos=int(fila["deuda_total_centavos"] or 0),
            deuda_vencida_centavos=int(fila["deuda_vencida_centavos"] or 0),
            tiene_plan_activo=bool(int(fila["total_planes_activos"] or 0)),
        )

    @staticmethod
    def _fila_a_metodo(fila: object) -> MetodoPago:
        return MetodoPago(
            identificador=int(fila["id"]),
            codigo=str(fila["codigo"] or ""),
            nombre=str(fila["nombre"] or ""),
            requiere_referencia=bool(int(fila["requiere_referencia"] or 0)),
        )

    @staticmethod
    def _a_booleano(valor: str) -> bool:
        return valor.strip().upper() in {"1", "TRUE", "SI", "S", "YES", "ON"}

