"""Servicios del módulo de casas."""

from __future__ import annotations

from modulos.casas.repositorio import RepositorioCasas


class ServicioCasas:
    """Orquesta la lógica de negocio del módulo."""

    def __init__(self, repositorio_casas: RepositorioCasas):
        self.repositorio_casas = repositorio_casas
