"""Adaptador de correo basado en Resend."""

from __future__ import annotations

from apis.contratos.proveedor_correo import ProveedorCorreo
from apis.resend.cliente_resend import ClienteResend


class ServicioCorreoResend(ProveedorCorreo):
    """Implementación mínima del contrato de correo para Resend."""

    def __init__(self, cliente_resend: ClienteResend):
        self.cliente_resend = cliente_resend

    def enviar_correo(self, destinatario: str, asunto: str, contenido: str) -> None:
        raise NotImplementedError("La integración con Resend se implementará más adelante.")
