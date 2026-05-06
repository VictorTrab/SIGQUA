"""Punto de entrada de aplicacion para SICAP."""

from comun.base_datos import GestorBaseDatos


def iniciar_aplicacion():
    """Inicia la aplicacion en modo minimo."""
    ruta_base_datos = GestorBaseDatos().inicializar_base_datos()
    print(f"SICAP iniciado correctamente. Base de datos lista en: {ruta_base_datos}")
