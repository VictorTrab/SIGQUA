"""Errores personalizados para la integración con Resend."""


class ErrorResend(Exception):
    """Error base para la integración con Resend."""


class ErrorAutenticacionResend(ErrorResend):
    """Error de autenticación contra la API de Resend."""
