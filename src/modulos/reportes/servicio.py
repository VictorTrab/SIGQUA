"""Servicios del modulo de reportes."""

from __future__ import annotations

import csv
from datetime import datetime

from modulos.reportes.entidades import EstadoReportes
from modulos.reportes.repositorio import RepositorioReportes


class ServicioReportes:
    """Orquesta consultas de reportes basicos."""

    def __init__(self, repositorio_reportes: RepositorioReportes) -> None:
        self.repositorio_reportes = repositorio_reportes

    def obtener_estado(self, fecha_desde: str = "", fecha_hasta: str = "") -> EstadoReportes:
        self._validar_rango(fecha_desde, fecha_hasta)
        return self.repositorio_reportes.obtener_estado(
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
        )

    def exportar_csv(
        self,
        ruta_destino: str,
        codigo_reporte: str,
        fecha_desde: str = "",
        fecha_hasta: str = "",
    ) -> str:
        estado = self.obtener_estado(fecha_desde=fecha_desde, fecha_hasta=fecha_hasta)
        tabla = next((item for item in estado.tablas if item.codigo == codigo_reporte), None)
        if tabla is None:
            raise ValueError("No existe el reporte seleccionado para exportacion.")
        with open(ruta_destino, "w", newline="", encoding="utf-8") as archivo:
            escritor = csv.writer(archivo)
            escritor.writerow(tabla.columnas)
            for fila in tabla.filas:
                escritor.writerow(fila)
        return ruta_destino

    @staticmethod
    def _validar_rango(fecha_desde: str, fecha_hasta: str) -> None:
        if fecha_desde:
            datetime.strptime(fecha_desde, "%Y-%m-%d")
        if fecha_hasta:
            datetime.strptime(fecha_hasta, "%Y-%m-%d")
        if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
            raise ValueError("La fecha inicial no puede ser mayor que la fecha final.")
