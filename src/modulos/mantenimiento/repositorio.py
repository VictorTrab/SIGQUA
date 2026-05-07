"""Contratos de persistencia del modulo de mantenimiento."""

from __future__ import annotations

from contextlib import closing
from typing import Protocol

from comun.base_datos import GestorBaseDatos
from modulos.mantenimiento.entidades import EstadoMantenimiento


class RepositorioMantenimiento(Protocol):
    """Define el acceso persistente requerido por mantenimiento."""

    def obtener_estado(self) -> EstadoMantenimiento:
        """Obtiene un resumen tecnico del sistema."""


class RepositorioMantenimientoSQLite:
    """Lee tablas tecnicas para el modulo de mantenimiento."""

    def __init__(self, gestor_base_datos: GestorBaseDatos) -> None:
        self._gestor_base_datos = gestor_base_datos

    def obtener_estado(self) -> EstadoMantenimiento:
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            total_respaldos = conexion.execute(
                "SELECT COUNT(*) AS total FROM historial_respaldos;"
            ).fetchone()["total"]
            total_eventos = conexion.execute(
                "SELECT COUNT(*) AS total FROM eventos_tecnicos;"
            ).fetchone()["total"]
            fila_ultimo_evento = conexion.execute(
                """
                SELECT mensaje, registrado_en
                FROM eventos_tecnicos
                ORDER BY registrado_en DESC, id DESC
                LIMIT 1;
                """
            ).fetchone()

        ultimo_evento = "Sin eventos tecnicos registrados."
        if fila_ultimo_evento is not None:
            ultimo_evento = (
                f"{fila_ultimo_evento['registrado_en']}: {fila_ultimo_evento['mensaje']}"
            )

        return EstadoMantenimiento(
            total_respaldos=int(total_respaldos),
            total_eventos_tecnicos=int(total_eventos),
            ultimo_evento=ultimo_evento,
        )

