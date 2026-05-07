"""Servicios del modulo de mantenimiento."""

from __future__ import annotations

from modulos.mantenimiento.entidades import EstadoMantenimiento
from modulos.mantenimiento.repositorio import RepositorioMantenimiento


class ServicioMantenimiento:
    """Orquesta la logica de negocio del modulo tecnico."""

    def __init__(self, repositorio_mantenimiento: RepositorioMantenimiento) -> None:
        self.repositorio_mantenimiento = repositorio_mantenimiento

    def obtener_estado(self) -> EstadoMantenimiento:
        return self.repositorio_mantenimiento.obtener_estado()

