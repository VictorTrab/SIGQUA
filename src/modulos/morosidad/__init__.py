"""Modulo de morosidad."""

from modulos.morosidad.controlador import ControladorMorosidad
from modulos.morosidad.repositorio import RepositorioMorosidadSQLite
from modulos.morosidad.servicio import ServicioMorosidad
from modulos.morosidad.vista import VistaMorosidad

__all__ = [
    "ControladorMorosidad",
    "RepositorioMorosidadSQLite",
    "ServicioMorosidad",
    "VistaMorosidad",
]
