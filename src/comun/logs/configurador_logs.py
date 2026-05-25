"""Configuracion centralizada de logs para SIGQUA."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from comun.configuracion.gestor_rutas import GestorRutas


NOMBRE_LOGGER_SIGQUA = "sigqua"
FORMATO_LOGS = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
LOGGER_SIGQUA_BASE = logging.getLogger(NOMBRE_LOGGER_SIGQUA)

if not LOGGER_SIGQUA_BASE.handlers:
    LOGGER_SIGQUA_BASE.addHandler(logging.NullHandler())
LOGGER_SIGQUA_BASE.propagate = False


def configurar_logs_basicos(
    gestor_rutas: GestorRutas | None = None,
    nivel: int = logging.INFO,
    nivel_consola: int = logging.WARNING,
) -> logging.Logger:
    """Configura logging a consola y archivo rotativo de forma idempotente."""
    gestor_rutas = gestor_rutas or GestorRutas()
    gestor_rutas.obtener_ruta_logs().mkdir(parents=True, exist_ok=True)

    logger_principal = LOGGER_SIGQUA_BASE
    logger_principal.setLevel(nivel)
    logger_principal.propagate = False

    ruta_log = gestor_rutas.obtener_ruta_logs() / "sigqua.log"
    ruta_actual = Path(getattr(logger_principal, "_ruta_log_sigqua", ruta_log))

    if getattr(logger_principal, "_sigqua_logs_configurados", False) and ruta_actual == ruta_log:
        return logger_principal

    _cerrar_handlers(logger_principal)

    formateador = logging.Formatter(FORMATO_LOGS)

    handler_consola = logging.StreamHandler()
    handler_consola.setLevel(nivel_consola)
    handler_consola.setFormatter(formateador)

    handler_archivo = RotatingFileHandler(
        ruta_log,
        maxBytes=1_048_576,
        backupCount=3,
        encoding="utf-8",
    )
    handler_archivo.setLevel(nivel)
    handler_archivo.setFormatter(formateador)

    logger_principal.addHandler(handler_consola)
    logger_principal.addHandler(handler_archivo)
    logger_principal._sigqua_logs_configurados = True  # type: ignore[attr-defined]
    logger_principal._ruta_log_sigqua = str(ruta_log)  # type: ignore[attr-defined]
    return logger_principal


def obtener_logger_sigqua(nombre: str | None = None) -> logging.Logger:
    """Devuelve un logger hijo del namespace principal de SIGQUA."""
    if not nombre:
        return logging.getLogger(NOMBRE_LOGGER_SIGQUA)
    return logging.getLogger(f"{NOMBRE_LOGGER_SIGQUA}.{nombre}")


def _cerrar_handlers(logger: logging.Logger) -> None:
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()
