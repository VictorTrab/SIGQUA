"""Servicios del módulo de abonados."""

from __future__ import annotations

from modulos.abonados.repositorio import RepositorioAbonados


class ServicioAbonados:
    """Orquesta la lógica de negocio del módulo."""

    def __init__(self, repositorio_abonados: RepositorioAbonados):
        self.repositorio_abonados = repositorio_abonados
