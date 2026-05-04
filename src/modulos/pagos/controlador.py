"""Controladores del módulo de pagos."""

from __future__ import annotations

from modulos.pagos.servicio import ServicioPagos


class ControladorPagos:
    """Conecta la vista con los servicios del módulo."""

    def __init__(self, servicio_pagos: ServicioPagos):
        self.servicio_pagos = servicio_pagos
