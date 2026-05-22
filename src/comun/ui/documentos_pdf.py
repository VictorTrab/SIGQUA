"""Acciones reutilizables para documentos PDF generados por SICAP."""

from __future__ import annotations

import os
from pathlib import Path
import sys

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtPrintSupport import QPrinterInfo


def describir_estado_automatizacion_documental(
    abrir_automaticamente: bool,
    imprimir_automaticamente: bool,
) -> str:
    """Construye una descripcion legible de la politica documental actual."""

    return (
        "Estado documental: "
        f"apertura automatica {'Activa' if abrir_automaticamente else 'Inactiva'} | "
        f"impresion automatica {'Activa' if imprimir_automaticamente else 'Inactiva'}"
    )


def ejecutar_acciones_documento_pdf(
    ruta_documento: str | Path,
    *,
    etiqueta_documento: str,
    abrir_automaticamente: bool,
    imprimir_automaticamente: bool,
) -> str:
    """Ejecuta la politica configurada para un PDF y devuelve un mensaje uniforme."""

    ruta_local = Path(ruta_documento).resolve()
    nombre_archivo = ruta_local.name
    acciones_exitosas: list[str] = []
    advertencias: list[str] = []

    if imprimir_automaticamente:
        impresion_ok, mensaje_impresion = imprimir_documento_pdf(ruta_local)
        if impresion_ok:
            acciones_exitosas.append("enviado a impresion")
        else:
            advertencias.append(mensaje_impresion)

    if abrir_automaticamente:
        if abrir_documento_pdf(ruta_local):
            acciones_exitosas.append("abierto")
        else:
            advertencias.append("no fue posible abrirlo automaticamente")

    mensaje = f"{etiqueta_documento} generado correctamente: {nombre_archivo}."
    if acciones_exitosas:
        mensaje = f"{mensaje} Acciones ejecutadas: {', '.join(acciones_exitosas)}."
    mensaje = f"{mensaje} Ruta del documento: {ruta_local}."
    if advertencias:
        mensaje = f"{mensaje} {'; '.join(advertencias)}."
    return mensaje


def abrir_documento_pdf(ruta_documento: Path) -> bool:
    """Abre un PDF con la aplicacion predeterminada del sistema."""

    return QDesktopServices.openUrl(QUrl.fromLocalFile(str(ruta_documento)))


def imprimir_documento_pdf(ruta_documento: Path) -> tuple[bool, str]:
    """Envía un PDF a impresion con la aplicacion predeterminada de Windows."""

    if not QPrinterInfo.availablePrinters() or QPrinterInfo.defaultPrinter().isNull():
        return (
            False,
            "no se detecto una impresora disponible; verifica que este conectada y encendida",
        )
    if not hasattr(os, "startfile") or sys.platform != "win32":
        return (
            False,
            "la impresion automatica solo esta disponible en Windows con una impresora configurada",
        )
    try:
        os.startfile(str(ruta_documento), "print")
    except OSError:
        return (
            False,
            "no fue posible enviarlo a impresion automaticamente; verifica que la impresora este conectada",
        )
    return True, ""
