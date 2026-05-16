"""Persistencia SQLite del modulo de pagos."""

from __future__ import annotations

from calendar import monthrange
from contextlib import closing
from typing import Protocol

from comun.base_datos import GestorBaseDatos
from modulos.pagos.entidades import (
    CargoPago,
    CasaPago,
    ComprobantePago,
    DetalleAplicacionPago,
    HistorialPago,
    MetodoPago,
    ResumenDeudaPago,
    ResumenConfirmacionPago,
    TIPO_PAGO_MENSUALIDAD,
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

    def guardar_pago_confirmado(
        self,
        resumen: ResumenConfirmacionPago,
        actor_id: int,
    ) -> ComprobantePago:
        """Guarda pago, detalle y comprobante dentro de una transaccion."""

    def obtener_comprobante(self, pago_id: int) -> ComprobantePago | None:
        """Obtiene el comprobante completo de un pago confirmado."""

    def actualizar_documento_comprobante(
        self,
        pago_id: int,
        ruta_archivo: str,
        formato_salida: str,
        hash_documento: str,
    ) -> None:
        """Actualiza la huella y ruta del archivo exportado del comprobante."""


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
                COALESCE(dd.meses_pendientes, 0) AS meses_pendientes,
                COALESCE(dd.meses_vencidos, 0) AS meses_vencidos,
                COALESCE(dd.deuda_total_centavos, 0) AS deuda_total_centavos,
                COALESCE(dd.deuda_vencida_centavos, 0) AS deuda_vencida_centavos
            FROM casas c
            INNER JOIN abonados a ON a.id = c.abonado_id
            LEFT JOIN barrios b ON b.id = c.barrio_id
            LEFT JOIN ({SUBCONSULTA_DEUDA_CASA}) dd ON dd.casa_id = c.id
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
                COALESCE(dd.meses_pendientes, 0) AS meses_pendientes,
                COALESCE(dd.meses_vencidos, 0) AS meses_vencidos,
                COALESCE(dd.deuda_total_centavos, 0) AS deuda_total_centavos,
                COALESCE(dd.deuda_vencida_centavos, 0) AS deuda_vencida_centavos
            FROM casas c
            INNER JOIN abonados a ON a.id = c.abonado_id
            LEFT JOIN barrios b ON b.id = c.barrio_id
            LEFT JOIN ({SUBCONSULTA_DEUDA_CASA}) dd ON dd.casa_id = c.id
            WHERE c.id = ? AND c.eliminado_en IS NULL
            LIMIT 1;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            fila = conexion.execute(consulta, (casa_id,)).fetchone()
        return self._fila_a_casa(fila) if fila is not None else None

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

    def guardar_pago_confirmado(
        self,
        resumen: ResumenConfirmacionPago,
        actor_id: int,
    ) -> ComprobantePago:
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                pago_id = self._insertar_pago(conexion, resumen, actor_id)
                concepto_mensualidad_id = self._obtener_concepto_id(
                    conexion,
                    "SERVICIO_MENSUAL",
                )
                for orden, detalle in enumerate(resumen.detalles, start=1):
                    cargo_id = detalle.cargo_id
                    periodo_id = detalle.periodo_id
                    if detalle.es_adelantado:
                        if detalle.periodo_anio is None or detalle.periodo_mes is None:
                            raise ValueError("Periodo adelantado incompleto.")
                        periodo_id = self._asegurar_periodo(
                            conexion,
                            detalle.periodo_anio,
                            detalle.periodo_mes,
                        )
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

                numero_comprobante = self._generar_numero_comprobante(conexion)
                cursor = conexion.execute(
                    """
                    INSERT INTO comprobantes(
                        pago_id,
                        numero_comprobante,
                        tipo_comprobante,
                        formato_salida,
                        saldo_posterior_centavos,
                        generado_por
                    )
                    VALUES (?, ?, ?, 'PDF', ?, ?);
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

    def obtener_comprobante(self, pago_id: int) -> ComprobantePago | None:
        consulta = """
            SELECT
                p.id AS pago_id,
                co.numero_comprobante,
                COALESCE(co.tipo_comprobante, 'MENSUALIDAD') AS tipo_comprobante,
                COALESCE(co.formato_salida, 'PDF') AS formato_salida,
                COALESCE(co.ruta_archivo, '') AS ruta_archivo,
                COALESCE(co.saldo_posterior_centavos, 0) AS saldo_posterior_centavos,
                co.generado_en,
                printf('CA-%03d', p.casa_id) AS casa_codigo,
                a.nombre_completo AS abonado_nombre,
                a.dni AS abonado_dni,
                mp.nombre AS metodo_pago,
                COALESCE(p.referencia_externa, '') AS referencia,
                p.total_pagado_centavos
            FROM comprobantes co
            INNER JOIN pagos p ON p.id = co.pago_id
            INNER JOIN abonados a ON a.id = p.abonado_id
            INNER JOIN metodos_pago mp ON mp.id = p.metodo_pago_id
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
            metodo_pago=str(fila["metodo_pago"] or ""),
            referencia=str(fila["referencia"] or ""),
            total_pagado_centavos=int(fila["total_pagado_centavos"] or 0),
            saldo_posterior_centavos=int(fila["saldo_posterior_centavos"] or 0),
            detalles=detalles,
            formato_salida=str(fila["formato_salida"] or "PDF"),
            ruta_archivo=str(fila["ruta_archivo"] or ""),
        )

    def actualizar_documento_comprobante(
        self,
        pago_id: int,
        ruta_archivo: str,
        formato_salida: str,
        hash_documento: str,
    ) -> None:
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                conexion.execute(
                    """
                    UPDATE comprobantes
                    SET ruta_archivo = ?,
                        formato_salida = ?,
                        hash_documento = ?,
                        generado_en = datetime('now')
                    WHERE pago_id = ?;
                    """,
                    (ruta_archivo, formato_salida, hash_documento, pago_id),
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
                tipo_pago
            )
            VALUES (?, ?, ?, ?, ?, ?, 0, ?, 0, ?, ?);
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
            ),
        )
        return int(cursor.lastrowid)

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
                actualizado_en = datetime('now')
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
                actualizado_en = datetime('now')
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
            meses_pendientes=int(fila["meses_pendientes"] or 0),
            meses_vencidos=int(fila["meses_vencidos"] or 0),
            deuda_total_centavos=int(fila["deuda_total_centavos"] or 0),
            deuda_vencida_centavos=int(fila["deuda_vencida_centavos"] or 0),
        )

    @staticmethod
    def _fila_a_metodo(fila: object) -> MetodoPago:
        return MetodoPago(
            identificador=int(fila["id"]),
            codigo=str(fila["codigo"] or ""),
            nombre=str(fila["nombre"] or ""),
            requiere_referencia=bool(int(fila["requiere_referencia"] or 0)),
        )
