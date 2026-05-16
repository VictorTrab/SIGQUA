"""Persistencia SQLite del modulo de morosidad."""

from __future__ import annotations

from contextlib import closing
from typing import Protocol

from comun.base_datos import GestorBaseDatos
from modulos.morosidad.entidades import EstadoMorosidad, FilaMorosidad, ResumenMorosidad


class RepositorioMorosidad(Protocol):
    """Contrato de consultas requerido por morosidad."""

    def obtener_estado(self, filtro: str = "") -> EstadoMorosidad:
        """Obtiene resumen y listado de casas con deuda vencida."""


class RepositorioMorosidadSQLite:
    """Consultas SQLite para deuda vencida operativa."""

    def __init__(self, gestor_base_datos: GestorBaseDatos) -> None:
        self._gestor_base_datos = gestor_base_datos

    def obtener_estado(self, filtro: str = "") -> EstadoMorosidad:
        filas = self._listar_filas(filtro)
        resumen = ResumenMorosidad(
            total_casas=len(filas),
            total_meses_vencidos=sum(fila.meses_vencidos for fila in filas),
            deuda_base_centavos=sum(fila.deuda_base_centavos for fila in filas),
            recargo_mora_centavos=sum(fila.recargo_mora_centavos for fila in filas),
            deuda_total_centavos=sum(fila.deuda_total_centavos for fila in filas),
        )
        return EstadoMorosidad(resumen=resumen, filas=tuple(filas))

    def _listar_filas(self, filtro: str) -> list[FilaMorosidad]:
        condiciones = [
            "ca.eliminado_en IS NULL",
            "ca.estado_servicio = 'ACTIVO'",
            "c.estado = 'VENCIDO'",
            "c.saldo_pendiente_centavos > 0",
            "c.anulado_en IS NULL",
        ]
        parametros: list[object] = []
        filtro = filtro.strip()
        if filtro:
            patron = f"%{filtro}%"
            condiciones.append(
                """
                (
                    lower(a.nombre_completo) LIKE lower(?)
                    OR a.dni LIKE ?
                    OR lower(printf('CA-%03d', ca.id)) LIKE lower(?)
                    OR lower(COALESCE(b.nombre, '')) LIKE lower(?)
                )
                """
            )
            parametros.extend([patron, patron, patron, patron])

        consulta = f"""
            SELECT
                ca.id AS casa_id,
                printf('CA-%03d', ca.id) AS casa_codigo,
                a.nombre_completo AS abonado_nombre,
                a.dni AS abonado_dni,
                COALESCE(b.nombre, '') AS barrio_nombre,
                ca.estado_servicio,
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
            INNER JOIN conceptos_cobro cc ON cc.id = c.concepto_id
            WHERE {' AND '.join(condiciones)}
            GROUP BY ca.id, a.id, b.id
            ORDER BY deuda_total_centavos DESC, vencimiento_mas_antiguo ASC, ca.id ASC;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            filas = conexion.execute(consulta, tuple(parametros)).fetchall()
        return [
            FilaMorosidad(
                casa_id=int(fila["casa_id"]),
                casa_codigo=str(fila["casa_codigo"] or ""),
                abonado_nombre=str(fila["abonado_nombre"] or ""),
                abonado_dni=str(fila["abonado_dni"] or ""),
                barrio_nombre=str(fila["barrio_nombre"] or ""),
                estado_servicio=str(fila["estado_servicio"] or ""),
                meses_vencidos=int(fila["meses_vencidos"] or 0),
                deuda_base_centavos=int(fila["deuda_base_centavos"] or 0),
                recargo_mora_centavos=int(fila["recargo_mora_centavos"] or 0),
                deuda_total_centavos=int(fila["deuda_total_centavos"] or 0),
                vencimiento_mas_antiguo=str(fila["vencimiento_mas_antiguo"] or ""),
            )
            for fila in filas
        ]
