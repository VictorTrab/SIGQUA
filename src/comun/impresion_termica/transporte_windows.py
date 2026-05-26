"""Transporte RAW de Windows para impresoras ESC/POS."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import sys

from comun.impresion_termica.entidades import ResultadoImpresionTicket


class DOC_INFO_1(ctypes.Structure):
    """Estructura requerida por StartDocPrinterW."""

    _fields_ = [
        ("pDocName", wintypes.LPWSTR),
        ("pOutputFile", wintypes.LPWSTR),
        ("pDatatype", wintypes.LPWSTR),
    ]


class TransporteWindowsRawEscpos:
    """Envia bytes ESC/POS a una impresora instalada en Windows."""

    def enviar(self, nombre_impresora: str, datos: bytes, nombre_documento: str) -> ResultadoImpresionTicket:
        nombre_impresora = nombre_impresora.strip()
        if not nombre_impresora:
            return ResultadoImpresionTicket(
                False,
                "No hay impresora termica configurada.",
                "SIN_IMPRESORA",
            )
        if sys.platform != "win32":
            return ResultadoImpresionTicket(
                False,
                "La impresion ESC/POS RAW solo esta disponible en Windows.",
                "PLATAFORMA_NO_SOPORTADA",
            )
        try:
            self._enviar_windows(nombre_impresora, datos, nombre_documento)
        except OSError as error:
            return ResultadoImpresionTicket(
                False,
                f"No fue posible enviar el ticket a la impresora termica. {error}",
                "ERROR_IMPRESION",
            )
        return ResultadoImpresionTicket(True, "Ticket enviado a impresion termica.", "OK")

    @staticmethod
    def _enviar_windows(nombre_impresora: str, datos: bytes, nombre_documento: str) -> None:
        winspool = ctypes.WinDLL("winspool.drv")
        manejador = wintypes.HANDLE()
        if not winspool.OpenPrinterW(nombre_impresora, ctypes.byref(manejador), None):
            raise ctypes.WinError()
        try:
            info = DOC_INFO_1(nombre_documento, None, "RAW")
            if not winspool.StartDocPrinterW(manejador, 1, ctypes.byref(info)):
                raise ctypes.WinError()
            try:
                if not winspool.StartPagePrinter(manejador):
                    raise ctypes.WinError()
                escritos = wintypes.DWORD(0)
                buffer = ctypes.create_string_buffer(datos)
                if not winspool.WritePrinter(
                    manejador,
                    buffer,
                    len(datos),
                    ctypes.byref(escritos),
                ):
                    raise ctypes.WinError()
                if int(escritos.value) != len(datos):
                    raise OSError("La impresora no acepto todos los bytes del ticket.")
                if not winspool.EndPagePrinter(manejador):
                    raise ctypes.WinError()
            finally:
                winspool.EndDocPrinter(manejador)
        finally:
            winspool.ClosePrinter(manejador)
