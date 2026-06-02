"""Persistencia SQLite del modulo de morosidad."""

from __future__ import annotations

import json
from contextlib import closing
from typing import Protocol

from comun.base_datos import GestorBaseDatos
from modulos.configuracion.entidades import ParametroConfiguracion
from modulos.morosidad.entidades import (
    CasaDetalleMorosidad,
    DetalleMorosidad,
    FILTRO_MOROSIDAD_TODOS,
    FILTRO_MOROSIDAD_LISTO_CORTE,
    FilaMorosidad,
    FiltroMorosidad,
    LineaDetalleMorosidad,
)


class RepositorioMorosidad(Protocol):
    """Contrato de persistencia requerido por morosidad."""

    def listar_morosidad(self, filtros: FiltroMorosidad) -> list[FilaMorosidad]:
        """Lista casas activas con deuda vencida segun filtros."""

    def obtener_detalle_abonado(self, abonado_id: int) -> DetalleMorosidad | None:
        """Recupera todas las casas en mora de un abonado."""

    def listar_parametros_configuracion(
        self,
        claves: tuple[str, ...],
    ) -> dict[str, ParametroConfiguracion]:
        """Obtiene parametros de configuracion relevantes para la vista."""

    def registrar_aviso_cobro(
        self,
        casa_id: int,
        estado_aviso: str,
        observacion: str,
        actor_id: int | None,
    ) -> None:
        """Registra una etapa manual de aviso de cobro para una casa."""


class RepositorioMorosidadSQLite:
    """Consultas SQLite para morosidad operativa."""

    def __init__(self, gestor_base_datos: GestorBaseDatos) -> None:
        self._gestor_base_datos = gestor_base_datos

    def listar_morosidad(self, filtros: FiltroMorosidad) -> list[FilaMorosidad]:
        condiciones = [
            "ca.eliminado_en IS NULL",
            "ca.estado_servicio IN ('ACTIVO', 'CORTADO')",
            "c.estado = 'VENCIDO'",
            "c.saldo_pendiente_centavos > 0",
            "c.anulado_en IS NULL",
        ]
        parametros: list[object] = []
        texto = filtros.texto.strip()
        if texto:
            patron = f"%{texto}%"
            condiciones.append(
                """
                (
                    lower(a.nombre_completo) LIKE lower(?)
                    OR a.dni LIKE ?
                    OR lower(printf('CA-%03d', ca.id)) LIKE lower(?)
                    OR lower(COALESCE(b.nombre, '')) LIKE lower(?)
                    OR lower(COALESCE(ca.direccion_referencia, '')) LIKE lower(?)
                )
                """
            )
            parametros.extend([patron, patron, patron, patron, patron])
        if filtros.estado_aviso != FILTRO_MOROSIDAD_TODOS:
            if filtros.estado_aviso == FILTRO_MOROSIDAD_LISTO_CORTE:
                condiciones.append(
                    "ca.estado_aviso_cobro IN ('LISTO_PARA_CORTE', 'CORTADO')"
                )
            else:
                condiciones.append("ca.estado_aviso_cobro = ?")
                parametros.append(filtros.estado_aviso)

        consulta = f"""
            SELECT
                a.id AS abonado_id,
                ca.id AS casa_id,
                printf('CA-%03d', ca.id) AS casa_codigo,
                a.nombre_completo AS abonado_nombre,
                a.dni AS abonado_dni,
                COALESCE(b.nombre, '') AS barrio_nombre,
                COALESCE(ca.direccion_referencia, '') AS direccion_casa,
                ca.estado_servicio,
                COALESCE(ca.estado_aviso_cobro, 'SIN_AVISO') AS estado_aviso_cobro,
                COALESCE(ca.fecha_ultimo_aviso, '') AS fecha_ultimo_aviso,
                COALESCE(u_aviso.nombre_completo, COALESCE(u_aviso.nombre_usuario, '')) AS usuario_ultimo_aviso,
                COALESCE(ca.observacion_ultimo_aviso, '') AS observacion_ultimo_aviso,
                COUNT(
                    DISTINCT CASE
                        WHEN cc.codigo = 'SERVICIO_MENSUAL'
                        THEN COALESCE(c.periodo_id, c.id)
                    END
                ) AS meses_vencidos,
                COALESCE(
                    SUM(
                        CASE
                            WHEN cc.tipo = 'MORA' OR cc.codigo = 'MORA'
                            THEN 0
                            ELSE c.saldo_pendiente_centavos
                        END
                    ),
                    0
                ) AS deuda_base_centavos,
                COALESCE(
                    SUM(
                        CASE
                            WHEN cc.tipo = 'MORA' OR cc.codigo = 'MORA'
                            THEN c.saldo_pendiente_centavos
                            ELSE 0
                        END
                    ),
                    0
                ) AS recargo_mora_centavos,
                COALESCE(SUM(c.saldo_pendiente_centavos), 0) AS deuda_total_centavos,
                MIN(c.fecha_vencimiento) AS vencimiento_mas_antiguo
            FROM cargos c
            INNER JOIN casas ca ON ca.id = c.casa_id
            INNER JOIN abonados a ON a.id = ca.abonado_id
            LEFT JOIN barrios b ON b.id = ca.barrio_id
            LEFT JOIN usuarios u_aviso ON u_aviso.id = ca.usuario_ultimo_aviso_id
            INNER JOIN conceptos_cobro cc ON cc.id = c.concepto_id
            WHERE {' AND '.join(condiciones)}
            GROUP BY a.id, ca.id, b.id
            ORDER BY deuda_total_centavos DESC, vencimiento_mas_antiguo ASC, ca.id ASC;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            filas = conexion.execute(consulta, tuple(parametros)).fetchall()
        return [
            FilaMorosidad(
                abonado_id=int(fila["abonado_id"]),
                casa_id=int(fila["casa_id"]),
                casa_codigo=str(fila["casa_codigo"] or ""),
                abonado_nombre=str(fila["abonado_nombre"] or ""),
                abonado_dni=str(fila["abonado_dni"] or ""),
                barrio_nombre=str(fila["barrio_nombre"] or ""),
                direccion_casa=str(fila["direccion_casa"] or ""),
                estado_servicio=str(fila["estado_servicio"] or ""),
                meses_vencidos=int(fila["meses_vencidos"] or 0),
                deuda_base_centavos=int(fila["deuda_base_centavos"] or 0),
                recargo_mora_centavos=int(fila["recargo_mora_centavos"] or 0),
                deuda_total_centavos=int(fila["deuda_total_centavos"] or 0),
                vencimiento_mas_antiguo=str(fila["vencimiento_mas_antiguo"] or ""),
                estado_aviso_cobro=str(fila["estado_aviso_cobro"] or "SIN_AVISO"),
                fecha_ultimo_aviso=str(fila["fecha_ultimo_aviso"] or ""),
                usuario_ultimo_aviso=str(fila["usuario_ultimo_aviso"] or ""),
                observacion_ultimo_aviso=str(fila["observacion_ultimo_aviso"] or ""),
            )
            for fila in filas
        ]

    def obtener_detalle_abonado(self, abonado_id: int) -> DetalleMorosidad | None:
        consulta_casas = """
            SELECT
                a.id AS abonado_id,
                a.nombre_completo AS abonado_nombre,
                a.dni AS abonado_dni,
                ca.id AS casa_id,
                printf('CA-%03d', ca.id) AS casa_codigo,
                COALESCE(b.nombre, '') AS barrio_nombre,
                COALESCE(ca.direccion_referencia, '') AS direccion_casa,
                ca.estado_servicio,
                COALESCE(ca.estado_aviso_cobro, 'SIN_AVISO') AS estado_aviso_cobro,
                COALESCE(ca.fecha_ultimo_aviso, '') AS fecha_ultimo_aviso,
                COALESCE(u_aviso.nombre_completo, COALESCE(u_aviso.nombre_usuario, '')) AS usuario_ultimo_aviso,
                COALESCE(ca.observacion_ultimo_aviso, '') AS observacion_ultimo_aviso,
                COUNT(
                    DISTINCT CASE
                        WHEN cc.codigo = 'SERVICIO_MENSUAL'
                        THEN COALESCE(c.periodo_id, c.id)
                    END
                ) AS meses_vencidos,
                COALESCE(
                    SUM(
                        CASE
                            WHEN cc.tipo = 'MORA' OR cc.codigo = 'MORA'
                            THEN 0
                            ELSE c.saldo_pendiente_centavos
                        END
                    ),
                    0
                ) AS deuda_base_centavos,
                COALESCE(
                    SUM(
                        CASE
                            WHEN cc.tipo = 'MORA' OR cc.codigo = 'MORA'
                            THEN c.saldo_pendiente_centavos
                            ELSE 0
                        END
                    ),
                    0
                ) AS recargo_mora_centavos,
                COALESCE(SUM(c.saldo_pendiente_centavos), 0) AS deuda_total_centavos,
                MIN(c.fecha_vencimiento) AS vencimiento_mas_antiguo
            FROM cargos c
            INNER JOIN casas ca ON ca.id = c.casa_id
            INNER JOIN abonados a ON a.id = ca.abonado_id
            LEFT JOIN barrios b ON b.id = ca.barrio_id
            LEFT JOIN usuarios u_aviso ON u_aviso.id = ca.usuario_ultimo_aviso_id
            INNER JOIN conceptos_cobro cc ON cc.id = c.concepto_id
            WHERE a.id = ?
              AND ca.eliminado_en IS NULL
              AND ca.estado_servicio IN ('ACTIVO', 'CORTADO')
              AND c.estado = 'VENCIDO'
              AND c.saldo_pendiente_centavos > 0
              AND c.anulado_en IS NULL
            GROUP BY a.id, ca.id, b.id
            ORDER BY ca.id ASC;
        """
        consulta_lineas = """
            SELECT
                c.id AS cargo_id,
                COALESCE(c.descripcion, cc.nombre, 'Cargo vencido') AS descripcion,
                COALESCE(c.fecha_vencimiento, '') AS fecha_vencimiento,
                COALESCE(c.saldo_pendiente_centavos, 0) AS saldo_pendiente_centavos
            FROM cargos c
            INNER JOIN conceptos_cobro cc ON cc.id = c.concepto_id
            WHERE c.casa_id = ?
              AND c.estado = 'VENCIDO'
              AND c.saldo_pendiente_centavos > 0
              AND c.anulado_en IS NULL
            ORDER BY c.fecha_vencimiento ASC, c.id ASC;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            filas_casas = conexion.execute(consulta_casas, (abonado_id,)).fetchall()
            if not filas_casas:
                return None
            casas: list[CasaDetalleMorosidad] = []
            nombre = str(filas_casas[0]["abonado_nombre"] or "")
            dni = str(filas_casas[0]["abonado_dni"] or "")
            for fila in filas_casas:
                casa_id = int(fila["casa_id"])
                filas_lineas = conexion.execute(consulta_lineas, (casa_id,)).fetchall()
                casas.append(
                    CasaDetalleMorosidad(
                        casa_id=casa_id,
                        casa_codigo=str(fila["casa_codigo"] or ""),
                        barrio_nombre=str(fila["barrio_nombre"] or ""),
                        direccion_casa=str(fila["direccion_casa"] or ""),
                        estado_servicio=str(fila["estado_servicio"] or ""),
                        meses_vencidos=int(fila["meses_vencidos"] or 0),
                        deuda_base_centavos=int(fila["deuda_base_centavos"] or 0),
                        recargo_mora_centavos=int(fila["recargo_mora_centavos"] or 0),
                        deuda_total_centavos=int(fila["deuda_total_centavos"] or 0),
                        vencimiento_mas_antiguo=str(fila["vencimiento_mas_antiguo"] or ""),
                        estado_aviso_cobro=str(fila["estado_aviso_cobro"] or "SIN_AVISO"),
                        fecha_ultimo_aviso=str(fila["fecha_ultimo_aviso"] or ""),
                        usuario_ultimo_aviso=str(fila["usuario_ultimo_aviso"] or ""),
                        observacion_ultimo_aviso=str(fila["observacion_ultimo_aviso"] or ""),
                        lineas_detalle=tuple(
                            LineaDetalleMorosidad(
                                cargo_id=int(item["cargo_id"]),
                                descripcion=str(item["descripcion"] or ""),
                                fecha_vencimiento=str(item["fecha_vencimiento"] or ""),
                                saldo_pendiente_centavos=int(item["saldo_pendiente_centavos"] or 0),
                            )
                            for item in filas_lineas
                        ),
                    )
                )
        return DetalleMorosidad(
            abonado_id=abonado_id,
            abonado_nombre=nombre,
            abonado_dni=dni,
            casas=tuple(casas),
        )

    def registrar_aviso_cobro(
        self,
        casa_id: int,
        estado_aviso: str,
        observacion: str,
        actor_id: int | None,
    ) -> None:
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                fila_actual = conexion.execute(
                    """
                    SELECT estado_aviso_cobro, fecha_ultimo_aviso, observacion_ultimo_aviso
                    FROM casas
                    WHERE id = ? AND eliminado_en IS NULL
                    LIMIT 1;
                    """,
                    (casa_id,),
                ).fetchone()
                if fila_actual is None:
                    raise ValueError("La casa indicada no existe.")
                conexion.execute(
                    """
                    UPDATE casas
                    SET estado_aviso_cobro = ?,
                        fecha_ultimo_aviso = datetime('now', 'localtime'),
                        usuario_ultimo_aviso_id = ?,
                        observacion_ultimo_aviso = ?,
                        actualizado_en = datetime('now', 'localtime')
                    WHERE id = ? AND eliminado_en IS NULL;
                    """,
                    (estado_aviso, actor_id, observacion, casa_id),
                )
                conexion.execute(
                    """
                    INSERT INTO auditoria(
                        usuario_id,
                        accion,
                        entidad,
                        entidad_id,
                        resumen,
                        datos_antes_json,
                        datos_despues_json
                    )
                    VALUES (?, 'REGISTRAR_AVISO_COBRO', 'casas', ?, ?, ?, ?);
                    """,
                    (
                        actor_id,
                        casa_id,
                        f"Aviso de cobro {estado_aviso} registrado para casa {casa_id}",
                        json.dumps(dict(fila_actual), ensure_ascii=True),
                        json.dumps(
                            {"estado_aviso_cobro": estado_aviso, "observacion": observacion},
                            ensure_ascii=True,
                        ),
                    ),
                )

    def listar_parametros_configuracion(
        self,
        claves: tuple[str, ...],
    ) -> dict[str, ParametroConfiguracion]:
        if not claves:
            return {}
        marcadores = ", ".join("?" for _ in claves)
        consulta = f"""
            SELECT
                clave,
                valor,
                tipo_dato,
                categoria,
                COALESCE(descripcion, '') AS descripcion,
                editable,
                COALESCE(actualizado_en, '') AS actualizado_en,
                actualizado_por
            FROM configuracion_sistema
            WHERE clave IN ({marcadores});
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            filas = conexion.execute(consulta, claves).fetchall()
        return {
            str(fila["clave"]): ParametroConfiguracion(
                clave=str(fila["clave"]),
                valor=str(fila["valor"] or ""),
                tipo_dato=str(fila["tipo_dato"] or "TEXTO"),
                categoria=str(fila["categoria"] or ""),
                descripcion=str(fila["descripcion"] or ""),
                editable=bool(fila["editable"]),
                actualizado_en=str(fila["actualizado_en"] or ""),
                actualizado_por=(
                    int(fila["actualizado_por"]) if fila["actualizado_por"] is not None else None
                ),
            )
            for fila in filas
        }
