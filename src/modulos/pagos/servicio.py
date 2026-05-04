"""Servicios del módulo de pagos."""

from __future__ import annotations

from modulos.pagos.repositorio import RepositorioPagos


class ServicioPagos:
    """Orquesta la lógica de negocio del módulo."""

    def __init__(self, repositorio_pagos: RepositorioPagos):
        self.repositorio_pagos = repositorio_pagos
