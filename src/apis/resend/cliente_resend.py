"""Cliente base para la integración con Resend."""

from __future__ import annotations


class ClienteResend:
    """Encapsula la comunicación HTTP futura con Resend."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    def construir_payload_correo(
        self,
        remitente: str,
        destinatario: str,
        asunto: str,
        contenido: str,
    ) -> dict[str, str]:
        """Construye el payload base que luego se enviaria a Resend."""
        return {
            "from": remitente,
            "to": destinatario,
            "subject": asunto,
            "html": contenido,
        }
