"""Generacion idempotente de periodos, mensualidades y vencimientos."""

from __future__ import annotations

from calendar import monthrange
from contextlib import closing
from dataclasses import dataclass
from datetime import date
import sqlite3

from comun.base_datos import GestorBaseDatos
from comun.logs import obtener_logger_sigqua


logger = obtener_logger_sigqua("cobros.ciclo")


class ErrorCicloCobro(RuntimeError):
    """Indica que no es seguro presentar informacion financiera."""


@dataclass(frozen=True, slots=True)
class ResultadoCicloCobro:
    """Resume los cambios persistidos durante una ejecucion."""

    periodos_creados: int = 0
    cargos_creados: int = 0
    cargos_vencidos: int = 0
    cuotas_vencidas: int = 0


class RepositorioCicloCobroSQLite:
    """Persiste el ciclo completo dentro de una sola transaccion SQLite."""

    def __init__(self, gestor_base_datos: GestorBaseDatos) -> None:
        self._gestor_base_datos = gestor_base_datos

    def ejecutar(self, hoy: date) -> ResultadoCicloCobro:
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            try:
                with conexion:
                    precio_mensual = self._obtener_precio_mensual(conexion)
                    concepto_mensual = self._obtener_concepto_mensual(conexion)
                    casas = self._listar_casas_cobrables(conexion)
                    periodos_creados = 0
                    cargos_creados = 0

                    for casa in casas:
                        inicio = self._resolver_primer_periodo(casa, hoy)
                        if inicio is None:
                            continue
                        for anio, mes in self._iterar_periodos(inicio, hoy):
                            periodo_id, creado = self._asegurar_periodo(
                                conexion,
                                anio,
                                mes,
                            )
                            periodos_creados += int(creado)
                            cargos_creados += int(
                                self._crear_cargo_mensual_si_falta(
                                    conexion=conexion,
                                    casa_id=int(casa["casa_id"]),
                                    abonado_id=int(casa["abonado_id"]),
                                    periodo_id=periodo_id,
                                    concepto_id=concepto_mensual,
                                    anio=anio,
                                    mes=mes,
                                    precio_mensual=precio_mensual,
                                    hoy=hoy,
                                )
                            )

                    cargos_vencidos = self._marcar_cargos_vencidos(conexion, hoy)
                    cuotas_vencidas = self._marcar_cuotas_vencidas(conexion, hoy)
            except (sqlite3.Error, ValueError) as error:
                raise ErrorCicloCobro(
                    "No fue posible actualizar el ciclo mensual de cobro."
                ) from error

        return ResultadoCicloCobro(
            periodos_creados=periodos_creados,
            cargos_creados=cargos_creados,
            cargos_vencidos=cargos_vencidos,
            cuotas_vencidas=cuotas_vencidas,
        )

    @staticmethod
    def _obtener_precio_mensual(conexion: sqlite3.Connection) -> int:
        fila = conexion.execute(
            """
            SELECT valor
            FROM configuracion_sistema
            WHERE clave = 'cobro.precio_mensual_centavos'
            LIMIT 1;
            """
        ).fetchone()
        precio = int(str(fila["valor"] or "0")) if fila is not None else 0
        if precio <= 0:
            raise ValueError("La tarifa mensual vigente no es valida.")
        return precio

    @staticmethod
    def _obtener_concepto_mensual(conexion: sqlite3.Connection) -> int:
        fila = conexion.execute(
            """
            SELECT id
            FROM conceptos_cobro
            WHERE codigo = 'SERVICIO_MENSUAL'
            LIMIT 1;
            """
        ).fetchone()
        if fila is None:
            raise ValueError("No existe el concepto SERVICIO_MENSUAL.")
        return int(fila["id"])

    @staticmethod
    def _listar_casas_cobrables(
        conexion: sqlite3.Connection,
    ) -> list[sqlite3.Row]:
        return conexion.execute(
            """
            SELECT
                c.id AS casa_id,
                c.abonado_id,
                COALESCE(
                    c.fecha_inicio_cobro,
                    (
                        SELECT MAX(COALESCE(ps.fecha_activacion, date(ps.fecha_ejecucion)))
                        FROM procesos_servicio ps
                        WHERE ps.casa_id = c.id
                          AND ps.tipo IN ('CONEXION', 'RECONEXION')
                          AND ps.estado = 'EJECUTADO'
                    ),
                    c.fecha_alta
                ) AS fecha_base_cobro
            FROM casas c
            INNER JOIN abonados a ON a.id = c.abonado_id
            WHERE c.eliminado_en IS NULL
              AND c.estado_servicio = 'ACTIVO'
              AND c.estado_administrativo = 'OPERATIVA'
              AND a.eliminado_en IS NULL
              AND a.estado = 'ACTIVO'
            ORDER BY c.id;
            """
        ).fetchall()

    @staticmethod
    def _resolver_primer_periodo(
        casa: sqlite3.Row,
        hoy: date,
    ) -> tuple[int, int] | None:
        texto_fecha = str(casa["fecha_base_cobro"] or "").strip()
        if not texto_fecha:
            return None
        try:
            fecha_base = date.fromisoformat(texto_fecha[:10])
        except ValueError as error:
            raise ValueError("Una casa tiene una fecha de inicio de cobro invalida.") from error
        anio = fecha_base.year
        mes = fecha_base.month + 1
        if mes == 13:
            anio += 1
            mes = 1
        if (anio, mes) > (hoy.year, hoy.month):
            return None
        return anio, mes

    @staticmethod
    def _iterar_periodos(
        inicio: tuple[int, int],
        hoy: date,
    ):
        anio, mes = inicio
        while (anio, mes) <= (hoy.year, hoy.month):
            yield anio, mes
            mes += 1
            if mes == 13:
                anio += 1
                mes = 1

    @staticmethod
    def _asegurar_periodo(
        conexion: sqlite3.Connection,
        anio: int,
        mes: int,
    ) -> tuple[int, bool]:
        fila = conexion.execute(
            "SELECT id FROM periodos_cobro WHERE anio = ? AND mes = ? LIMIT 1;",
            (anio, mes),
        ).fetchone()
        if fila is not None:
            return int(fila["id"]), False
        ultimo_dia = monthrange(anio, mes)[1]
        cursor = conexion.execute(
            """
            INSERT INTO periodos_cobro(
                anio, mes, nombre, fecha_inicio, fecha_fin, fecha_vencimiento
            )
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            (
                anio,
                mes,
                f"Periodo {mes:02d}/{anio:04d}",
                f"{anio:04d}-{mes:02d}-01",
                f"{anio:04d}-{mes:02d}-{ultimo_dia:02d}",
                f"{anio:04d}-{mes:02d}-10",
            ),
        )
        return int(cursor.lastrowid), True

    @staticmethod
    def _crear_cargo_mensual_si_falta(
        *,
        conexion: sqlite3.Connection,
        casa_id: int,
        abonado_id: int,
        periodo_id: int,
        concepto_id: int,
        anio: int,
        mes: int,
        precio_mensual: int,
        hoy: date,
    ) -> bool:
        fila = conexion.execute(
            """
            SELECT 1
            FROM cargos
            WHERE casa_id = ?
              AND periodo_id = ?
              AND concepto_id = ?
              AND anulado_en IS NULL
            LIMIT 1;
            """,
            (casa_id, periodo_id, concepto_id),
        ).fetchone()
        if fila is not None:
            return False
        vencimiento = date(anio, mes, 10)
        estado = "VENCIDO" if vencimiento < hoy else "PENDIENTE"
        conexion.execute(
            """
            INSERT INTO cargos(
                casa_id,
                abonado_id,
                periodo_id,
                concepto_id,
                descripcion,
                monto_centavos,
                saldo_pendiente_centavos,
                fecha_generacion,
                fecha_vencimiento,
                estado,
                origen
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'MENSUAL');
            """,
            (
                casa_id,
                abonado_id,
                periodo_id,
                concepto_id,
                f"Servicio mensual {mes:02d}/{anio:04d}",
                precio_mensual,
                precio_mensual,
                hoy.isoformat(),
                vencimiento.isoformat(),
                estado,
            ),
        )
        return True

    @staticmethod
    def _marcar_cargos_vencidos(
        conexion: sqlite3.Connection,
        hoy: date,
    ) -> int:
        cursor = conexion.execute(
            """
            UPDATE cargos
            SET estado = 'VENCIDO',
                actualizado_en = datetime('now', 'localtime')
            WHERE estado IN ('PENDIENTE', 'PARCIAL')
              AND saldo_pendiente_centavos > 0
              AND anulado_en IS NULL
              AND origen != 'ADELANTO'
              AND concepto_id = (
                  SELECT id
                  FROM conceptos_cobro
                  WHERE codigo = 'SERVICIO_MENSUAL'
                  LIMIT 1
              )
              AND date(fecha_vencimiento) < date(?);
            """,
            (hoy.isoformat(),),
        )
        return max(0, int(cursor.rowcount))

    @staticmethod
    def _marcar_cuotas_vencidas(
        conexion: sqlite3.Connection,
        hoy: date,
    ) -> int:
        cursor = conexion.execute(
            """
            UPDATE cuotas_plan_pago
            SET estado = 'VENCIDO',
                actualizado_en = datetime('now', 'localtime')
            WHERE estado IN ('PENDIENTE', 'PARCIAL')
              AND saldo_pendiente_centavos > 0
              AND date(fecha_vencimiento) < date(?)
              AND plan_pago_id IN (
                  SELECT id
                  FROM planes_pago
                  WHERE estado = 'ACTIVO'
                    AND tipo_plan = 'RECONEXION'
              );
            """,
            (hoy.isoformat(),),
        )
        return max(0, int(cursor.rowcount))


class ServicioCicloCobro:
    """Fachada de negocio para ejecutar el ciclo con fecha controlable."""

    def __init__(self, repositorio: RepositorioCicloCobroSQLite) -> None:
        self._repositorio = repositorio

    def ejecutar(self, hoy: date | None = None) -> ResultadoCicloCobro:
        try:
            return self._repositorio.ejecutar(hoy or date.today())
        except ErrorCicloCobro:
            logger.exception("Fallo la actualizacion automatica del ciclo de cobro.")
            raise
