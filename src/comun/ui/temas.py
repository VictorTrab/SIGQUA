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
    "fondo_principal": "#071A2D",
    "fondo_sidebar": "#061525",
    "fondo_header": "#0D2A45",
    "fondo_dialogo": "#0D2A45",
    "fondo_superficie": "#0D2A45",
    "fondo_superficie_suave": "#123553",
    "fondo_superficie_muy_suave": "#082238",
    "fondo_superficie_destacada": "#183F5F",
    "fondo_panel_accion": "#123553",

    # Fondos de componentes específicos
    "fondo_input": "#082238",
    "fondo_input_focus": "#0D2A45",
    "fondo_tabla_header": "#0A3152",
    "fondo_tabla_header_destacado": "#0A3152",
    "fondo_tabla_cuerpo": "#0E2B46",
    "fondo_tabla_fila": "#0E2B46",
    "fondo_tabla_fila_alterna": "#123655",
    "fondo_tabla_hover": "rgba(117, 199, 240, 0.16)",
    "fondo_tabla_seleccion": "rgba(117, 199, 240, 0.22)",
    "fondo_chip": "#082238",
    "fondo_chip_hover": "rgba(117, 199, 240, 0.14)",
    "fondo_chip_activo": "#123655",
    "fondo_badge": "#183F5F",
    "fondo_badge_activo": "rgba(55, 211, 153, 0.18)",
    "fondo_info": "rgba(117, 199, 240, 0.16)",
    "fondo_exito": "rgba(55, 211, 153, 0.18)",
    "fondo_error": "rgba(242, 116, 116, 0.18)",
    "fondo_advertencia": "rgba(245, 184, 75, 0.18)",
    "fondo_neutro": "rgba(142, 168, 188, 0.16)",
    "fondo_avatar": "rgba(117, 199, 240, 0.14)",
    "fondo_menu_activo": "rgba(117, 199, 240, 0.24)",
    "fondo_menu_hover": "rgba(117, 199, 240, 0.13)",

    # Bordes y contornos
    "borde_principal": "rgba(126, 167, 196, 0.48)",
    "borde_suave": "rgba(126, 167, 196, 0.30)",
    "borde_tabla": "rgba(126, 167, 196, 0.28)",
    "borde_medio": "rgba(126, 167, 196, 0.55)",
    "borde_foco_input": "rgba(117, 199, 240, 0.62)",
    "borde_chip_activo": "rgba(117, 199, 240, 0.42)",
    "borde_badge_activo": "rgba(117, 199, 240, 0.28)",
    "borde_info": "rgba(117, 199, 240, 0.32)",
    "borde_exito": "rgba(55, 211, 153, 0.36)",
    "borde_error": "rgba(242, 116, 116, 0.34)",
    "borde_advertencia": "rgba(245, 184, 75, 0.34)",
    "borde_neutro": "rgba(142, 168, 188, 0.28)",
    "borde_avatar": "rgba(126, 167, 196, 0.32)",
    "borde_menu_activo": "rgba(117, 199, 240, 0.66)",

    # Texto y tipografía por superficie
    "texto_principal": "#F4FAFF",
    "texto_secundario": "#C5DDEE",
    "texto_suave": "#C5DDEE",
    "texto_muted": "#92B6CC",
    "texto_destacado": "#75C7F0",
    "texto_input": "#F4FAFF",
    "texto_chip": "#C5DDEE",
    "texto_chip_activo": "#F4FAFF",
    "texto_badge": "#C5DDEE",
    "texto_badge_activo": "#DDFBF0",
    "texto_info": "#DFF4FF",
    "texto_exito": "#DDFBF0",
    "texto_error": "#FFE3E3",
    "texto_advertencia": "#FFF1C7",
    "texto_neutro": "#D7E5EE",
    "texto_panel_principal": "#F4FAFF",
    "texto_panel_secundario": "#C5DDEE",
    "texto_panel_detalle": "#92B6CC",
    "texto_panel_fuerte": "#F4FAFF",
    "texto_tabla_header": "#F4FAFF",
    "texto_tabla": "#F4FAFF",
    "texto_tabla_secundario": "#C5DDEE",
    "texto_menu_activo": "#F4FAFF",
    "texto_menu_normal": "#C5DDEE",
    "texto_menu_seccion": "#92B6CC",

    # Tarjetas, gráficos y componentes visuales específicos
    "tarjeta_panel_stop_1": "#0D2A45",
    "tarjeta_panel_stop_2": "#123553",
    "tarjeta_panel_stop_3": "#0A3152",
    "tarjeta_panel_borde": "rgba(126, 167, 196, 172)",
    "ranking_barra": "rgba(126, 167, 196, 0.28)",
    "ranking_chunk": "rgba(117, 199, 240, 0.78)",
    "grafica_linea": "#92B6CC",
    "grafica_linea_actual": "#75C7F0",
    "grafica_linea_promedio": "#37D399",
    "grafica_barras": "#49A9DC",
    "grafica_texto": "#92B6CC",
    "grafica_texto_fuerte": "#F4FAFF",
    "grafica_texto_suave": "#C5DDEE",
    "grafica_grid": "rgba(126, 167, 196, 0.22)",
    "grafica_grid_fuerte": "rgba(146, 182, 204, 0.24)",
    "grafica_borde_trozo": "#071A2D",
    "grafica_barra_activo": "#37D399",
    "grafica_barra_cortado": "#F27474",
    "grafica_barra_suspendido": "#F5B84B",
    "grafica_barra_inactivo": "#8EA8BC",
    "grafica_barra_reconexion": "#75C7F0",
    "grafica_deuda_barra_inicio": "#49A9DC",
    "grafica_deuda_barra_fin": "#75C7F0",
    "grafica_donut_0_30": "#75C7F0",
    "grafica_donut_31_60": "#37D399",
    "grafica_donut_61_90": "#F5B84B",
    "grafica_donut_90_mas": "#F27474",
    "grafica_pie_colores": ("#75C7F0", "#37D399", "#F5B84B", "#F27474", "#8EA8BC"),
    "icono_fila_base": "#C5DDEE",
    "icono_acento_info": "#75C7F0",
    "icono_acento_warning": "#F5B84B",
    "icono_tarjeta_info": "#75C7F0",
    "icono_tarjeta_success": "#37D399",
    "icono_tarjeta_warning": "#F5B84B",
    "icono_tarjeta_help": "#92B6CC",
    "icono_tema_activo": "#75C7F0",
    "icono_tema_inactivo": "#C5DDEE",
    "icono_menu_activo": "#75C7F0",

    # Iconos por función
    "icono_menu_normal": "#C5DDEE",
    "icono_ver": "#75C7F0",
    "icono_editar": "#F5B84B",
    "icono_cobrar": "#37D399",
    "icono_historial": "#A7B8FF",
    "icono_peligro": "#F27474",
    "icono_aviso": "#F5B84B",

    # Acentos y estados interactivos
    "acento_primario": "#75C7F0",
    "acento_hover": "#49A9DC",
    "acento_seleccion": "rgba(117, 199, 240, 0.22)",

    # Botones principales, secundarios y de peligro
    "boton_primario_fondo": "#75C7F0",
    "boton_primario_texto": "#061525",
    "boton_primario_hover": "#9AD8F5",
    "boton_secundario_fondo": "#183F5F",
    "boton_secundario_texto": "#F4FAFF",
    "boton_secundario_hover": "#21506F",
    "boton_peligro_fondo": "#8F3F4A",
    "boton_peligro_texto": "#FFF1F2",
    "boton_peligro_hover": "#A84B58",
    "boton_deshabilitado_fondo": "#243A4D",
    "boton_deshabilitado_texto": "#92B6CC",

    # Modales y componentes de diálogo
    "modal_fondo": "#0D2A45",
    "modal_fondo_seccion": "#123553",
    "modal_fondo_campo": "#082238",
    "modal_borde": "rgba(126, 167, 196, 0.46)",
    "modal_titulo": "#F4FAFF",
    "modal_texto": "#C5DDEE",
    "modal_texto_secundario": "#92B6CC",
    "modal_overlay": "rgba(7, 26, 45, 0.76)",
    "modal_footer_fondo": "#0D2A45",
    "modal_footer_borde": "rgba(126, 167, 196, 0.46)",
    "modal_footer_separador": "rgba(126, 167, 196, 0.32)",
    "modal_icono_campo": "#92B6CC",
    "modal_icono_accion": "#C5DDEE",
    "modal_icono_accion_principal": "#061525",
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
