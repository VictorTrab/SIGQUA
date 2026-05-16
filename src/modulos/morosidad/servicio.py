"""Servicio del modulo de morosidad."""

from __future__ import annotations

from datetime import datetime

from modulos.morosidad.entidades import EstadoMorosidad
from modulos.morosidad.repositorio import RepositorioMorosidad


class ServicioMorosidad:
    """Orquesta consultas de deuda vencida sin alterar saldos."""

    def __init__(self, repositorio_morosidad: RepositorioMorosidad) -> None:
        self.repositorio_morosidad = repositorio_morosidad

    def obtener_estado(self, filtro: str = "") -> EstadoMorosidad:
        return self.repositorio_morosidad.obtener_estado(filtro=filtro)

    @staticmethod
    def formatear_moneda(valor_centavos: int) -> str:
        return f"L {valor_centavos / 100:,.2f}"

    @staticmethod
    def formatear_fecha(valor: str) -> str:
        if not valor:
            return "Sin vencimiento"
        try:
            fecha = datetime.fromisoformat(valor)
        except ValueError:
            return valor
        return fecha.strftime("%d/%m/%Y")
