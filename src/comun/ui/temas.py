"""Paleta visual unica compartida para SICAP."""

from __future__ import annotations

from copy import deepcopy


TEMA_SICAP_PREDETERMINADO = "tema_sicap"

_PALETA_TEMA_SICAP: dict[str, object] = {
    "nombre": "tema sicap",
    "familia_tipografica": "Segoe UI",
    "tamano_fuente_base": 10,
    "tamano_titulo_modulo": 21,
    "tamano_titulo_panel": 14,
    "tamano_titulo_tarjeta": 20,
    "peso_titulo": 800,
    "peso_subtitulo": 700,
    "peso_cuerpo": 600,
    "fondo_principal": "#0A1728",
    "fondo_sidebar": "#102A40",
    "fondo_header": "#1D364E",
    "fondo_dialogo": "#1D364E",
    "fondo_superficie": "#1D364E",
    "fondo_superficie_suave": "#243F5A",
    "fondo_superficie_muy_suave": "#102A40",
    "fondo_superficie_destacada": "#243F5A",
    "fondo_panel_accion": "#243F5A",
    "fondo_input": "#102A40",
    "fondo_input_focus": "#1D364E",
    "fondo_tabla_header": "#243F5A",
    "fondo_tabla_header_destacado": "#243F5A",
    "fondo_tabla_cuerpo": "#1D364E",
    "fondo_tabla_fila": "#1D364E",
    "fondo_tabla_fila_alterna": "#243F5A",
    "fondo_tabla_hover": "rgba(78, 106, 156, 0.20)",
    "fondo_tabla_seleccion": "rgba(78, 106, 156, 0.28)",
    "fondo_chip": "#102A40",
    "fondo_chip_hover": "rgba(78, 106, 156, 0.18)",
    "fondo_chip_activo": "#243F5A",
    "fondo_badge": "#243F5A",
    "fondo_badge_activo": "#2D5A68",
    "fondo_exito": "rgba(45, 90, 104, 0.28)",
    "fondo_error": "rgba(104, 61, 71, 0.24)",
    "fondo_advertencia": "rgba(109, 99, 63, 0.24)",
    "fondo_avatar": "rgba(78, 106, 156, 0.18)",
    "fondo_menu_activo": "rgba(78, 106, 156, 0.34)",
    "fondo_menu_hover": "rgba(78, 106, 156, 0.18)",
    "borde_principal": "rgba(83, 112, 139, 0.48)",
    "borde_suave": "rgba(83, 112, 139, 0.30)",
    "borde_tabla": "rgba(83, 112, 139, 0.32)",
    "borde_medio": "rgba(83, 112, 139, 0.55)",
    "borde_foco_input": "rgba(201, 219, 233, 0.55)",
    "borde_chip_activo": "rgba(201, 219, 233, 0.42)",
    "borde_badge_activo": "rgba(201, 219, 233, 0.26)",
    "borde_exito": "rgba(201, 219, 233, 0.24)",
    "borde_error": "rgba(228, 234, 204, 0.22)",
    "borde_advertencia": "rgba(228, 234, 204, 0.22)",
    "borde_avatar": "rgba(83, 112, 139, 0.32)",
    "borde_menu_activo": "rgba(201, 219, 233, 0.68)",
    "texto_principal": "#EAF2F8",
    "texto_secundario": "#C9DBE9",
    "texto_suave": "#C9DBE9",
    "texto_muted": "#8FAFC7",
    "texto_destacado": "#E4EACC",
    "texto_input": "#EAF2F8",
    "texto_chip": "#C9DBE9",
    "texto_chip_activo": "#EAF2F8",
    "texto_badge": "#C9DBE9",
    "texto_badge_activo": "#EAF2F8",
    "texto_exito": "#C9DBE9",
    "texto_error": "#E4EACC",
    "texto_advertencia": "#E4EACC",
    "texto_panel_principal": "#EAF2F8",
    "texto_panel_secundario": "#C9DBE9",
    "texto_panel_detalle": "#8FAFC7",
    "texto_panel_fuerte": "#EAF2F8",
    "texto_tabla_header": "#EAF2F8",
    "texto_tabla": "#EAF2F8",
    "texto_tabla_secundario": "#C9DBE9",
    "texto_menu_activo": "#EAF2F8",
    "texto_menu_normal": "#C9DBE9",
    "texto_menu_seccion": "#8FAFC7",
    "tarjeta_panel_stop_1": "#1D364E",
    "tarjeta_panel_stop_2": "#243F5A",
    "tarjeta_panel_stop_3": "#1D364E",
    "tarjeta_panel_borde": "rgba(83, 112, 139, 172)",
    "ranking_barra": "rgba(83, 112, 139, 0.32)",
    "ranking_chunk": "rgba(201, 219, 233, 0.78)",
    "grafica_linea": "#8FAFC7",
    "grafica_linea_actual": "#38BDF8",
    "grafica_linea_promedio": "#35E6A8",
    "grafica_barras": "#4E6A9C",
    "grafica_texto": "#8FAFC7",
    "grafica_texto_fuerte": "#EAF2F8",
    "grafica_texto_suave": "#C9DBE9",
    "grafica_grid": "rgba(83, 112, 139, 0.24)",
    "grafica_grid_fuerte": "rgba(143, 175, 199, 0.24)",
    "grafica_borde_trozo": "#0A1728",
    "grafica_barra_activo": "#35E6A8",
    "grafica_barra_cortado": "#F87171",
    "grafica_barra_suspendido": "#FBBF24",
    "grafica_barra_inactivo": "#64748B",
    "grafica_barra_reconexion": "#38BDF8",
    "grafica_deuda_barra_inicio": "#2563EB",
    "grafica_deuda_barra_fin": "#38BDF8",
    "grafica_donut_0_30": "#38BDF8",
    "grafica_donut_31_60": "#35E6A8",
    "grafica_donut_61_90": "#FBBF24",
    "grafica_donut_90_mas": "#F87171",
    "grafica_pie_colores": ("#38BDF8", "#35E6A8", "#FBBF24", "#F87171", "#64748B"),
    "icono_fila_base": "#C9DBE9",
    "icono_acento_info": "#C9DBE9",
    "icono_acento_warning": "#E4EACC",
    "icono_tarjeta_info": "#C9DBE9",
    "icono_tarjeta_success": "#E4EACC",
    "icono_tarjeta_warning": "#E4EACC",
    "icono_tarjeta_help": "#8FAFC7",
    "icono_tema_activo": "#E4EACC",
    "icono_tema_inactivo": "#C9DBE9",
    "icono_menu_activo": "#E4EACC",
    "icono_menu_normal": "#C9DBE9",
    "acento_primario": "#C9DBE9",
    "acento_hover": "#4E6A9C",
    "acento_seleccion": "rgba(78, 106, 156, 0.24)",
    "boton_primario_fondo": "#C9DBE9",
    "boton_primario_texto": "#0A1728",
    "boton_primario_hover": "#D8E6F1",
    "boton_secundario_fondo": "#243F5A",
    "boton_secundario_texto": "#EAF2F8",
    "boton_secundario_hover": "#2D4C68",
    "boton_peligro_fondo": "#6B3F4A",
    "boton_peligro_texto": "#F4E8EC",
    "boton_peligro_hover": "#84515D",
    "boton_deshabilitado_fondo": "#324556",
    "boton_deshabilitado_texto": "#8FAFC7",
    "modal_fondo": "#1D364E",
    "modal_fondo_seccion": "#243F5A",
    "modal_fondo_campo": "#102A40",
    "modal_borde": "rgba(83, 112, 139, 0.46)",
    "modal_titulo": "#EAF2F8",
    "modal_texto": "#C9DBE9",
    "modal_texto_secundario": "#8FAFC7",
    "modal_overlay": "rgba(10, 23, 40, 0.76)",
    "modal_footer_fondo": "#1D364E",
    "modal_footer_borde": "rgba(83, 112, 139, 0.46)",
    "modal_footer_separador": "rgba(83, 112, 139, 0.32)",
    "modal_icono_campo": "#8FAFC7",
    "modal_icono_accion": "#C9DBE9",
    "modal_icono_accion_principal": "#0A1728",
}

_tema_actual = TEMA_SICAP_PREDETERMINADO


def obtener_tema_actual() -> str:
    return _tema_actual


def resolver_nombre_tema(nombre_tema: str) -> str:
    _ = nombre_tema
    return TEMA_SICAP_PREDETERMINADO


def establecer_tema_actual(nombre_tema: str) -> str:
    global _tema_actual
    _tema_actual = TEMA_SICAP_PREDETERMINADO
    _ = nombre_tema
    return _tema_actual


def obtener_paleta_tema(nombre_tema: str) -> dict[str, object]:
    _ = nombre_tema
    return deepcopy(_PALETA_TEMA_SICAP)


def obtener_paleta_tema_actual() -> dict[str, object]:
    return deepcopy(_PALETA_TEMA_SICAP)


def obtener_fondo_header_destacado(nombre_tema: str) -> str:
    _ = nombre_tema
    return "#1D364E"
