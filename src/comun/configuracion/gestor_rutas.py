"""Resolución centralizada de rutas para SICAP."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


NOMBRE_APLICACION = "SICAP"


@dataclass(frozen=True, slots=True)
class GestorRutas:
    """Centraliza las rutas de trabajo y evita lógica duplicada."""

    raiz_proyecto: Path = Path(__file__).resolve().parents[3]

    def obtener_ruta_base_datos(self) -> Path:
        return self.raiz_proyecto / "database" / "sicap.db"

    def obtener_ruta_logs(self) -> Path:
        return self.raiz_proyecto / "logs"

    def obtener_ruta_documentacion_tecnica(self) -> Path:
        ruta_configurada = os.getenv("RUTA_DOCUMENTACION_TECNICA")
        if ruta_configurada:
            return Path(ruta_configurada).expanduser()

        return Path.home() / "Documents" / f"{NOMBRE_APLICACION} DOCUMENTACION"

    def asegurar_directorios_base(self) -> None:
        self.obtener_ruta_logs().mkdir(parents=True, exist_ok=True)
        self.obtener_ruta_documentacion_tecnica().mkdir(parents=True, exist_ok=True)
