"""Resolucion centralizada de rutas para SIGQUA."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path


NOMBRE_APLICACION = "SIGQUA"
VERSION_SISTEMA = "2.3.0"
RAIZ_CODIGO = Path(__file__).resolve().parents[3]
RAIZ_INSTALACION = (
    Path(sys.executable).resolve().parent
    if getattr(sys, "frozen", False)
    else RAIZ_CODIGO
)
RAIZ_RECURSOS = (
    Path(getattr(sys, "_MEIPASS")).resolve()
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")
    else RAIZ_CODIGO
)


@dataclass(frozen=True, slots=True)
class GestorRutas:
    """Centraliza las rutas de trabajo y evita logica duplicada."""

    raiz_proyecto: Path = RAIZ_INSTALACION

    def obtener_ruta_directorio_base_datos(self) -> Path:
        return self.raiz_proyecto / "database"

    def obtener_ruta_base_datos(self) -> Path:
        return self.obtener_ruta_directorio_base_datos() / "sigqua.db"

    def obtener_ruta_base_datos_plantilla(self) -> Path:
        if self.raiz_proyecto.resolve() == RAIZ_INSTALACION.resolve():
            return RAIZ_RECURSOS / "database" / "sigqua_base.db"
        return self.obtener_ruta_directorio_base_datos() / "sigqua_base.db"

    def obtener_ruta_logs(self) -> Path:
        return self.raiz_proyecto / "logs"

    def obtener_ruta_exportaciones(self) -> Path:
        if self.raiz_proyecto.resolve() != RAIZ_INSTALACION.resolve():
            return self.raiz_proyecto / "exportaciones"
        return self.obtener_ruta_documentos_usuario() / "SIGQUA_EXPORTACIONES"

    def obtener_ruta_respaldos(self) -> Path:
        if self.raiz_proyecto.resolve() != RAIZ_INSTALACION.resolve():
            return self.raiz_proyecto / "respaldos"
        return Path("C:/respaldos_sigqua")

    def obtener_ruta_exportaciones_comprobantes(self) -> Path:
        return self.obtener_ruta_exportaciones() / "Comprobantes"

    def obtener_ruta_exportaciones_reportes(self) -> Path:
        return self.obtener_ruta_exportaciones() / "Reportes"

    def obtener_ruta_documentos_usuario(self) -> Path:
        return Path.home() / "Documents"

    def obtener_ruta_reportes_predeterminada(self) -> Path:
        return self.obtener_ruta_exportaciones_reportes()

    def obtener_ruta_env(self) -> Path:
        return self.raiz_proyecto / ".env"

    def obtener_ruta_logo_marca(self) -> Path:
        return (
            RAIZ_RECURSOS
            / "src"
            / "comun"
            / "ui"
            / "recursos"
            / "marca"
            / "sigqua_logo.svg"
        )

    def obtener_ruta_icono_aplicacion(self) -> Path:
        return RAIZ_RECURSOS / "src" / "comun" / "ui" / "recursos" / "marca" / "icono.ico"

    def obtener_ruta_directorio_iconos_tabler(self) -> Path:
        return RAIZ_RECURSOS / "src" / "comun" / "ui" / "recursos" / "iconos" / "tabler"

    def obtener_ruta_icono_tabler(self, nombre_icono: str) -> Path:
        return self.obtener_ruta_directorio_iconos_tabler() / nombre_icono

    def asegurar_directorios_base(self) -> None:
        self.obtener_ruta_directorio_base_datos().mkdir(parents=True, exist_ok=True)
        self.obtener_ruta_logs().mkdir(parents=True, exist_ok=True)
        self.obtener_ruta_exportaciones().mkdir(parents=True, exist_ok=True)
        self.obtener_ruta_respaldos().mkdir(parents=True, exist_ok=True)
        self.obtener_ruta_exportaciones_comprobantes().mkdir(parents=True, exist_ok=True)
        self.obtener_ruta_exportaciones_reportes().mkdir(parents=True, exist_ok=True)
