"""Paleta visual unica compartida para SIGQUA."""

from __future__ import annotations

from copy import deepcopy


TEMA_SIGQUA_PREDETERMINADO = "tema_sigqua"

# ---------------------------------------------------------------------------
# Paleta de colores y estilos compartidos para el tema SIGQUA
# ---------------------------------------------------------------------------

_PALETA_TEMA_SIGQUA: dict[str, object] = {
    "nombre": "tema sigqua",
    "familia_tipografica": "Segoe UI",
    "tamano_fuente_base": 10,
    "tamano_titulo_modulo": 21,
    "tamano_titulo_panel": 14,
    "tamano_titulo_tarjeta": 20,
    "peso_titulo": 800,
    "peso_subtitulo": 700,
    "peso_cuerpo": 600,

    # Fondo general y superficies principales
    "fondo_principal": "#101214",
    "fondo_sidebar": "#071823",
    "fondo_header": "#101214",
    "fondo_dialogo": "#171A1E",
    "fondo_superficie": "#171A1E",
    "fondo_superficie_suave": "#1D2126",
    "fondo_superficie_muy_suave": "#13161A",
    "fondo_superficie_destacada": "#242A31",
    "fondo_panel_accion": "#1D2126",

    # Fondos de componentes específicos
    "fondo_input": "#121519",
    "fondo_input_focus": "#181D23",
    "fondo_tabla_header": "#20262D",
    "fondo_tabla_header_destacado": "#20262D",
    "fondo_tabla_cuerpo": "#15191D",
    "fondo_tabla_fila": "#171B20",
    "fondo_tabla_fila_alterna": "#1D2228",
    "fondo_tabla_hover": "rgba(47, 155, 255, 0.16)",
    "fondo_tabla_seleccion": "rgba(47, 155, 255, 0.24)",
    "fondo_chip": "#14181C",
    "fondo_chip_hover": "rgba(47, 155, 255, 0.14)",
    "fondo_chip_activo": "#202A35",
    "fondo_badge": "#242A31",
    "fondo_badge_activo": "rgba(55, 211, 153, 0.18)",
    "fondo_info": "rgba(117, 199, 240, 0.16)",
    "fondo_exito": "rgba(55, 211, 153, 0.18)",
    "fondo_error": "rgba(242, 116, 116, 0.18)",
    "fondo_advertencia": "rgba(245, 184, 75, 0.18)",
    "fondo_neutro": "rgba(142, 168, 188, 0.16)",
    "fondo_avatar": "rgba(47, 155, 255, 0.16)",
    "fondo_menu_activo": "rgba(47, 155, 255, 0.22)",
    "fondo_menu_hover": "rgba(47, 155, 255, 0.11)",

    # Bordes y contornos
    "borde_principal": "rgba(111, 151, 190, 0.46)",
    "borde_suave": "rgba(137, 153, 168, 0.22)",
    "borde_tabla": "rgba(147, 163, 178, 0.24)",
    "borde_medio": "rgba(137, 153, 168, 0.42)",
    "borde_foco_input": "rgba(47, 155, 255, 0.78)",
    "borde_chip_activo": "rgba(47, 155, 255, 0.48)",
    "borde_badge_activo": "rgba(47, 155, 255, 0.34)",
    "borde_info": "rgba(47, 155, 255, 0.40)",
    "borde_exito": "rgba(55, 211, 153, 0.36)",
    "borde_error": "rgba(242, 116, 116, 0.34)",
    "borde_advertencia": "rgba(245, 184, 75, 0.34)",
    "borde_neutro": "rgba(142, 168, 188, 0.28)",
    "borde_avatar": "rgba(47, 155, 255, 0.38)",
    "borde_menu_activo": "rgba(47, 155, 255, 0.72)",

    # Texto y tipografía por superficie
    "texto_principal": "#F4F7FA",
    "texto_secundario": "#B8C0C8",
    "texto_suave": "#B8C0C8",
    "texto_muted": "#89939D",
    "texto_destacado": "#57AEFF",
    "texto_input": "#F4F7FA",
    "texto_chip": "#B8C0C8",
    "texto_chip_activo": "#F4F7FA",
    "texto_badge": "#B8C0C8",
    "texto_badge_activo": "#DDFBF0",
    "texto_info": "#DFF4FF",
    "texto_exito": "#DDFBF0",
    "texto_error": "#FFE3E3",
    "texto_advertencia": "#FFF1C7",
    "texto_neutro": "#D7E5EE",
    "texto_panel_principal": "#F4F7FA",
    "texto_panel_secundario": "#B8C0C8",
    "texto_panel_detalle": "#89939D",
    "texto_panel_fuerte": "#F4F7FA",
    "texto_tabla_header": "#F4F7FA",
    "texto_tabla": "#E8EDF2",
    "texto_tabla_secundario": "#B8C0C8",
    "texto_menu_activo": "#F4F7FA",
    "texto_menu_normal": "#B8C0C8",
    "texto_menu_seccion": "#7F8993",

    # Tarjetas, gráficos y componentes visuales específicos
    "tarjeta_panel_stop_1": "#181C20",
    "tarjeta_panel_stop_2": "#1C2127",
    "tarjeta_panel_stop_3": "#171B20",
    "tarjeta_panel_borde": "rgba(137, 153, 168, 120)",
    "ranking_barra": "rgba(137, 153, 168, 0.24)",
    "ranking_chunk": "rgba(47, 155, 255, 0.82)",
    "grafica_linea": "#92B6CC",
    "grafica_linea_actual": "#2F9BFF",
    "grafica_linea_promedio": "#37D399",
    "grafica_barras": "#2F9BFF",
    "grafica_texto": "#89939D",
    "grafica_texto_fuerte": "#F4F7FA",
    "grafica_texto_suave": "#B8C0C8",
    "grafica_grid": "rgba(137, 153, 168, 0.18)",
    "grafica_grid_fuerte": "rgba(137, 153, 168, 0.24)",
    "grafica_borde_trozo": "#101214",
    "grafica_barra_activo": "#37D399",
    "grafica_barra_cortado": "#F27474",
    "grafica_barra_suspendido": "#F5B84B",
    "grafica_barra_inactivo": "#8EA8BC",
    "grafica_barra_reconexion": "#75C7F0",
    "grafica_deuda_barra_inicio": "#257FD1",
    "grafica_deuda_barra_fin": "#57AEFF",
    "grafica_donut_0_30": "#2F9BFF",
    "grafica_donut_31_60": "#37D399",
    "grafica_donut_61_90": "#F5B84B",
    "grafica_donut_90_mas": "#F27474",
    "grafica_pie_colores": ("#75C7F0", "#37D399", "#F5B84B", "#F27474", "#8EA8BC"),
    "icono_fila_base": "#B8C0C8",
    "icono_acento_info": "#57AEFF",
    "icono_acento_warning": "#F5B84B",
    "icono_tarjeta_info": "#57AEFF",
    "icono_tarjeta_success": "#37D399",
    "icono_tarjeta_warning": "#F5B84B",
    "icono_tarjeta_help": "#92B6CC",
    "icono_tema_activo": "#57AEFF",
    "icono_tema_inactivo": "#AEB7C0",
    "icono_menu_activo": "#57AEFF",

    # Iconos por función
    "icono_menu_normal": "#AEB7C0",
    "icono_ver": "#57AEFF",
    "icono_editar": "#F5B84B",
    "icono_cobrar": "#37D399",
    "icono_historial": "#A7B8FF",
    "icono_peligro": "#F27474",
    "icono_aviso": "#F5B84B",

    # Acentos y estados interactivos
    "acento_primario": "#2F9BFF",
    "acento_hover": "#57AEFF",
    "acento_seleccion": "rgba(47, 155, 255, 0.24)",

    # Botones principales, secundarios y de peligro
    "boton_primario_fondo": "#2F9BFF",
    "boton_primario_texto": "#071019",
    "boton_primario_hover": "#57AEFF",
    "boton_secundario_fondo": "#242A31",
    "boton_secundario_texto": "#F4F7FA",
    "boton_secundario_hover": "#303841",
    "boton_peligro_fondo": "#8F3F4A",
    "boton_peligro_texto": "#FFF1F2",
    "boton_peligro_hover": "#A84B58",
    "boton_deshabilitado_fondo": "#252A30",
    "boton_deshabilitado_texto": "#77818B",

    # Modales y componentes de diálogo
    "modal_fondo": "#171A1E",
    "modal_fondo_seccion": "#1D2126",
    "modal_fondo_campo": "#121519",
    "modal_borde": "rgba(137, 153, 168, 0.34)",
    "modal_titulo": "#F4F7FA",
    "modal_texto": "#B8C0C8",
    "modal_texto_secundario": "#89939D",
    "modal_overlay": "rgba(5, 7, 9, 0.78)",
    "modal_footer_fondo": "#171A1E",
    "modal_footer_borde": "rgba(137, 153, 168, 0.34)",
    "modal_footer_separador": "rgba(137, 153, 168, 0.24)",
    "modal_icono_campo": "#89939D",
    "modal_icono_accion": "#B8C0C8",
    "modal_icono_accion_principal": "#071019",
}

# ---------------------------------------------------------------------------
# Estado interno del tema activo
# ---------------------------------------------------------------------------

_tema_actual = TEMA_SIGQUA_PREDETERMINADO


# ---------------------------------------------------------------------------
# API de temas: resolución, lectura y escritura del tema actual
# ---------------------------------------------------------------------------


def obtener_tema_actual() -> str:
    return _tema_actual


def resolver_nombre_tema(nombre_tema: str) -> str:
    _ = nombre_tema
    return TEMA_SIGQUA_PREDETERMINADO


def establecer_tema_actual(nombre_tema: str) -> str:
    global _tema_actual
    _tema_actual = TEMA_SIGQUA_PREDETERMINADO
    _ = nombre_tema
    return _tema_actual


def obtener_paleta_tema(nombre_tema: str) -> dict[str, object]:
    _ = nombre_tema
    return deepcopy(_PALETA_TEMA_SIGQUA)


def obtener_paleta_tema_actual() -> dict[str, object]:
    return deepcopy(_PALETA_TEMA_SIGQUA)


def obtener_fondo_header_destacado(nombre_tema: str) -> str:
    _ = nombre_tema
    return str(_PALETA_TEMA_SIGQUA["fondo_header"])
