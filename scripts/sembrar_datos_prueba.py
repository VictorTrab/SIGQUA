"""Recrea la base local de SICAP incluyendo datos de prueba de desarrollo."""

from __future__ import annotations

import sys
from pathlib import Path


RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
RUTA_SRC = RAIZ_PROYECTO / "src"

if str(RUTA_SRC) not in sys.path:
    sys.path.insert(0, str(RUTA_SRC))

from comun.base_datos import GestorBaseDatos  # noqa: E402


def main() -> int:
    ruta_base_datos = GestorBaseDatos().inicializar_base_datos(
        forzar_recreacion=True,
        incluir_datos_prueba=True,
    )
    print(f"Base de datos recreada con datos de prueba en: {ruta_base_datos}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
