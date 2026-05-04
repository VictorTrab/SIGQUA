"""Cliente base para la integración con Resend."""

from __future__ import annotations


class ClienteResend:
    """Encapsula la comunicación HTTP futura con Resend."""

    def __init__(self, api_key: str):
        self.api_key = api_key
