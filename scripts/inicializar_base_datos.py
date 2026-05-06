"""Inicializa la base de datos SQLite de SICAP desde la migracion versionada."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
RUTA_SRC = RAIZ_PROYECTO / "src"

if str(RUTA_SRC) not in sys.path:
    sys.path.insert(0, str(RUTA_SRC))

from comun.base_datos import GestorBaseDatos  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--recrear",
        action="store_true",
        help="Elimina la base actual y la vuelve a crear desde el esquema inicial.",
    )
    argumentos = parser.parse_args()

    ruta_base_datos = GestorBaseDatos().inicializar_base_datos(
        forzar_recreacion=argumentos.recrear
    )
    print(f"Base de datos inicializada en: {ruta_base_datos}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
