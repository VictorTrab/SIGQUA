"""Elementos reutilizables de interfaz."""

from comun.ui.contenedor_apilado import ContenedorApiladoAjustable
from comun.ui.componentes import (
    BotonAccionContextual,
    DialogoBaseSicap,
    DialogoConfirmacionSicap,
    DialogoMensajeSicap,
    TarjetaKPI,
    VistaPlaceholderModulo,
    aplicar_estilo_boton_operativo,
    configurar_tabla_operativa,
    crear_boton_operativo,
    crear_item_tabla,
    resolver_variante_boton_modal,
)
from comun.ui.iconos import (
    obtener_icono_tabler,
    obtener_icono_tabler_coloreado,
    obtener_pixmap_tabler_coloreado,
)

__all__ = [
    "ContenedorApiladoAjustable",
    "BotonAccionContextual",
    "DialogoBaseSicap",
    "DialogoConfirmacionSicap",
    "DialogoMensajeSicap",
    "TarjetaKPI",
    "VistaPlaceholderModulo",
    "aplicar_estilo_boton_operativo",
    "configurar_tabla_operativa",
    "crear_boton_operativo",
    "crear_item_tabla",
    "resolver_variante_boton_modal",
    "obtener_icono_tabler",
    "obtener_icono_tabler_coloreado",
    "obtener_pixmap_tabler_coloreado",
]
