"""Contrato base para proveedores de correo electrónico."""

from __future__ import annotations

from typing import Protocol


class ProveedorCorreo(Protocol):
    """Define el contrato mínimo para servicios de correo."""

    def enviar_correo(self, destinatario: str, asunto: str, contenido: str) -> None:
        """Envía un correo usando un proveedor externo."""
