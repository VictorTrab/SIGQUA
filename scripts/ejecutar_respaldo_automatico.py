from __future__ import annotations

import sys
from pathlib import Path


RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
RUTA_SRC = RAIZ_PROYECTO / "src"

if str(RUTA_SRC) not in sys.path:
    sys.path.insert(0, str(RUTA_SRC))

from comun.base_datos import GestorBaseDatos  # noqa: E402
from comun.configuracion.gestor_rutas import GestorRutas  # noqa: E402
from comun.respaldo import ServicioRespaldoLocal  # noqa: E402
from modulos.configuracion.repositorio import RepositorioConfiguracionSQLite  # noqa: E402
from modulos.configuracion.servicio import ServicioConfiguracion  # noqa: E402


def main() -> int:
    gestor_rutas = GestorRutas(raiz_proyecto=RAIZ_PROYECTO)
    gestor_base_datos = GestorBaseDatos(gestor_rutas)
    gestor_base_datos.inicializar_base_datos()
    repositorio_configuracion = RepositorioConfiguracionSQLite(gestor_base_datos)
    servicio_respaldo = ServicioRespaldoLocal(
        gestor_base_datos=gestor_base_datos,
        gestor_rutas=gestor_rutas,
    )
    servicio_configuracion = ServicioConfiguracion(
        repositorio_configuracion=repositorio_configuracion,
        gestor_rutas=gestor_rutas,
        servicio_respaldo=servicio_respaldo,
    )
    resultado = servicio_configuracion.crear_respaldo_automatico(actor_id=None)
    return 0 if resultado.exito else 1


if __name__ == "__main__":
    raise SystemExit(main())
