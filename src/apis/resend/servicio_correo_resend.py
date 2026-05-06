"""Adaptador de correo basado en Resend."""

from __future__ import annotations

from apis.contratos.proveedor_correo import ProveedorCorreo
from apis.resend.cliente_resend import ClienteResend


class ServicioCorreoResend(ProveedorCorreo):
    """Implementacion segura para preparar correos sin enviarlos aun."""

    def __init__(
        self,
        cliente_resend: ClienteResend,
        correo_remitente: str = "no-reply@sicap.local",
    ):
        self.cliente_resend = cliente_resend
        self.correo_remitente = correo_remitente
        self.ultimo_payload_generado: dict[str, str] | None = None

    def enviar_correo(self, destinatario: str, asunto: str, contenido: str) -> None:
        self.ultimo_payload_generado = self.cliente_resend.construir_payload_correo(
            remitente=self.correo_remitente,
            destinatario=destinatario,
            asunto=asunto,
            contenido=contenido,
        )
