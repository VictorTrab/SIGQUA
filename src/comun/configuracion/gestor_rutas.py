"""Resolucion centralizada de rutas para SIGQUA."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


NOMBRE_APLICACION = "SIGQUA"
VERSION_SISTEMA = "2.2.0"


@dataclass(frozen=True, slots=True)
class GestorRutas:
    """Centraliza las rutas de trabajo y evita logica duplicada."""

    raiz_proyecto: Path = Path(__file__).resolve().parents[3]

    def obtener_ruta_directorio_base_datos(self) -> Path:
        return self.raiz_proyecto / "database"

    def obtener_ruta_base_datos(self) -> Path:
        return self.obtener_ruta_directorio_base_datos() / "sigqua.db"

    def obtener_ruta_migraciones_base_datos(self) -> Path:
        return self.obtener_ruta_directorio_base_datos() / "migrations"

    def obtener_ruta_esquema_inicial_base_datos(self) -> Path:
        return self.obtener_ruta_migraciones_base_datos() / "002_esquema_inicial.sql"

    def obtener_ruta_logs(self) -> Path:
        return self.raiz_proyecto / "logs"

    def obtener_ruta_exportaciones(self) -> Path:
        return self.raiz_proyecto / "exportaciones"

    def obtener_ruta_respaldos(self) -> Path:
        return self.raiz_proyecto / "respaldos"

    def obtener_ruta_exportaciones_comprobantes(self) -> Path:
        return self.obtener_ruta_exportaciones() / "comprobantes"

    def obtener_ruta_exportaciones_reportes(self) -> Path:
        return self.obtener_ruta_exportaciones() / "reportes"

    def obtener_ruta_env(self) -> Path:
        return self.raiz_proyecto / ".env"

    def obtener_ruta_logo_marca(self) -> Path:
        return (
            self.raiz_proyecto
            / "src"
            / "comun"
            / "ui"
            / "recursos"
            / "marca"
            / "sigqua_logo.svg"
        )

    def obtener_ruta_icono_aplicacion(self) -> Path:
        return self.raiz_proyecto / "src" / "comun" / "ui" / "recursos" / "marca" / "icono.ico"

    def obtener_ruta_directorio_iconos_tabler(self) -> Path:
        return self.raiz_proyecto / "src" / "comun" / "ui" / "recursos" / "iconos" / "tabler"

    def obtener_ruta_icono_tabler(self, nombre_icono: str) -> Path:
        return self.obtener_ruta_directorio_iconos_tabler() / nombre_icono

    def obtener_ruta_documentacion_tecnica(self) -> Path:
        ruta_configurada = os.getenv("RUTA_DOCUMENTACION_TECNICA")
        if ruta_configurada:
            return Path(ruta_configurada).expanduser()

        return Path.home() / "Documents" / f"{NOMBRE_APLICACION} DOCUMENTACION"

    def asegurar_directorios_base(self) -> None:
        self.obtener_ruta_directorio_base_datos().mkdir(parents=True, exist_ok=True)
        self.obtener_ruta_migraciones_base_datos().mkdir(parents=True, exist_ok=True)
        self.obtener_ruta_logs().mkdir(parents=True, exist_ok=True)
        self.obtener_ruta_exportaciones().mkdir(parents=True, exist_ok=True)
        self.obtener_ruta_respaldos().mkdir(parents=True, exist_ok=True)
        self.obtener_ruta_exportaciones_comprobantes().mkdir(parents=True, exist_ok=True)
        self.obtener_ruta_exportaciones_reportes().mkdir(parents=True, exist_ok=True)
        self.obtener_ruta_documentacion_tecnica().mkdir(parents=True, exist_ok=True)
