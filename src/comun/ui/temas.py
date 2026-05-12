"""Paletas visuales compartidas para SICAP."""

from __future__ import annotations

from copy import deepcopy


TEMA_SICAP_PREDETERMINADO = "oscuro"

_TEMAS_SICAP: dict[str, dict[str, object]] = {
    "oscuro": {
        "nombre": "oscuro",
        "fondo_principal": "#2c2966",
        "fondo_dialogo": "#565384",
        "fondo_superficie": "rgba(255, 255, 255, 0.10)",
        "fondo_superficie_suave": "rgba(255, 255, 255, 0.05)",
        "fondo_superficie_muy_suave": "rgba(255, 255, 255, 0.03)",
        "fondo_panel_accion": "rgba(255, 255, 255, 0.06)",
        "fondo_input": "rgba(255, 255, 255, 0.11)",
        "fondo_input_focus": "rgba(255, 255, 255, 0.16)",
        "fondo_tabla_header": "rgba(255, 255, 255, 0.10)",
        "fondo_chip": "rgba(255, 255, 255, 0.06)",
        "fondo_chip_hover": "rgba(255, 255, 255, 0.12)",
        "fondo_chip_activo": "#d2f4f2",
        "fondo_badge": "rgba(132, 146, 166, 0.22)",
        "fondo_badge_activo": "rgba(16, 120, 98, 0.22)",
        "fondo_exito": "rgba(16, 120, 98, 0.16)",
        "fondo_error": "rgba(180, 35, 24, 0.15)",
        "fondo_advertencia": "rgba(255, 206, 120, 0.12)",
        "fondo_avatar": "rgba(109, 241, 220, 0.16)",
        "borde_principal": "rgba(255, 255, 255, 0.16)",
        "borde_suave": "rgba(255, 255, 255, 0.10)",
        "borde_medio": "rgba(255, 255, 255, 0.18)",
        "borde_foco_input": "rgba(109, 241, 220, 0.42)",
        "borde_chip_activo": "rgba(255, 255, 255, 0.18)",
        "borde_badge_activo": "rgba(158, 231, 214, 0.26)",
        "borde_exito": "rgba(158, 231, 214, 0.26)",
        "borde_error": "rgba(255, 205, 199, 0.28)",
        "borde_advertencia": "rgba(255, 206, 120, 0.26)",
        "borde_avatar": "rgba(109, 241, 220, 0.24)",
        "texto_principal": "#ffffff",
        "texto_secundario": "rgba(235, 242, 248, 0.76)",
        "texto_suave": "rgba(232, 239, 249, 0.80)",
        "texto_muted": "rgba(232, 239, 249, 0.72)",
        "texto_input": "#f5fbff",
        "texto_chip": "#ecf5ff",
        "texto_chip_activo": "#0f2d43",
        "texto_badge": "#f4f8fb",
        "texto_badge_activo": "#d9fff5",
        "texto_exito": "#d9fff5",
        "texto_error": "#ffd4cf",
        "texto_advertencia": "#fff0c7",
        "texto_panel_principal": "#1b2430",
        "texto_panel_secundario": "#8b96a8",
        "texto_panel_detalle": "#55606f",
        "texto_panel_fuerte": "#1f2530",
        "tarjeta_panel_stop_1": "rgba(255, 255, 255, 138)",
        "tarjeta_panel_stop_2": "rgba(246, 252, 255, 118)",
        "tarjeta_panel_stop_3": "rgba(225, 241, 249, 96)",
        "tarjeta_panel_borde": "rgba(255, 255, 255, 156)",
        "ranking_barra": "rgba(255, 255, 255, 0.18)",
        "ranking_chunk": "rgba(31, 37, 48, 0.72)",
        "grafica_linea": "#1f2530",
        "grafica_barras": "#1f2530",
        "grafica_texto": "#687588",
        "grafica_grid": "rgba(103, 118, 137, 0.24)",
        "grafica_borde_trozo": "#ffffff",
        "grafica_pie_colores": ("#000000", "#8fb2ec", "#9ee4c4", "#7fb8ff", "#c5d2dd"),
        "icono_fila_base": "#c8d6f1",
        "icono_acento_info": "#4fa3ff",
        "icono_acento_warning": "#ff625c",
        "icono_tarjeta_info": "#8ec9ff",
        "icono_tarjeta_success": "#8de8c7",
        "icono_tarjeta_warning": "#f7cc7a",
        "icono_tarjeta_help": "#c6b6ff",
        "icono_tema_activo": "#f7cc7a",
        "icono_tema_inactivo": "#eef6ff",
    },
    "claro": {
        "nombre": "claro",
        "fondo_principal": "#eef2f7",
        "fondo_dialogo": "#e7ebf2",
        "fondo_superficie": "rgba(248, 250, 253, 0.94)",
        "fondo_superficie_suave": "rgba(255, 255, 255, 0.74)",
        "fondo_superficie_muy_suave": "rgba(242, 245, 250, 0.92)",
        "fondo_panel_accion": "rgba(240, 244, 249, 0.96)",
        "fondo_input": "rgba(244, 247, 251, 0.96)",
        "fondo_input_focus": "rgba(255, 255, 255, 0.98)",
        "fondo_tabla_header": "rgba(230, 236, 244, 0.96)",
        "fondo_chip": "rgba(235, 240, 247, 0.96)",
        "fondo_chip_hover": "rgba(223, 231, 241, 0.96)",
        "fondo_chip_activo": "#dceef6",
        "fondo_badge": "rgba(147, 159, 176, 0.16)",
        "fondo_badge_activo": "rgba(57, 158, 116, 0.14)",
        "fondo_exito": "rgba(57, 158, 116, 0.12)",
        "fondo_error": "rgba(191, 77, 66, 0.10)",
        "fondo_advertencia": "rgba(237, 185, 96, 0.16)",
        "fondo_avatar": "rgba(83, 166, 235, 0.14)",
        "borde_principal": "rgba(131, 145, 164, 0.24)",
        "borde_suave": "rgba(131, 145, 164, 0.20)",
        "borde_medio": "rgba(131, 145, 164, 0.28)",
        "borde_foco_input": "rgba(62, 153, 221, 0.42)",
        "borde_chip_activo": "rgba(135, 171, 196, 0.32)",
        "borde_badge_activo": "rgba(57, 158, 116, 0.24)",
        "borde_exito": "rgba(57, 158, 116, 0.24)",
        "borde_error": "rgba(191, 77, 66, 0.22)",
        "borde_advertencia": "rgba(237, 185, 96, 0.28)",
        "borde_avatar": "rgba(83, 166, 235, 0.24)",
        "texto_principal": "#213547",
        "texto_secundario": "#617489",
        "texto_suave": "#6b7c91",
        "texto_muted": "#72839a",
        "texto_input": "#24374b",
        "texto_chip": "#365169",
        "texto_chip_activo": "#1e4259",
        "texto_badge": "#4f6072",
        "texto_badge_activo": "#267553",
        "texto_exito": "#267553",
        "texto_error": "#a84336",
        "texto_advertencia": "#8d6b28",
        "texto_panel_principal": "#24374b",
        "texto_panel_secundario": "#6e8095",
        "texto_panel_detalle": "#7a889a",
        "texto_panel_fuerte": "#233447",
        "tarjeta_panel_stop_1": "rgba(251, 252, 255, 240)",
        "tarjeta_panel_stop_2": "rgba(242, 246, 251, 232)",
        "tarjeta_panel_stop_3": "rgba(231, 238, 246, 226)",
        "tarjeta_panel_borde": "rgba(166, 180, 199, 0.42)",
        "ranking_barra": "rgba(179, 191, 207, 0.30)",
        "ranking_chunk": "rgba(60, 82, 110, 0.70)",
        "grafica_linea": "#3d5877",
        "grafica_barras": "#45617f",
        "grafica_texto": "#6f8195",
        "grafica_grid": "rgba(120, 136, 158, 0.18)",
        "grafica_borde_trozo": "#d9e0ea",
        "grafica_pie_colores": ("#5b6f8f", "#84a5d6", "#79cbb1", "#7ebfe1", "#b6c4d6"),
        "icono_fila_base": "#6b7f95",
        "icono_acento_info": "#2f7cc3",
        "icono_acento_warning": "#c45146",
        "icono_tarjeta_info": "#5c8fc7",
        "icono_tarjeta_success": "#4ea68d",
        "icono_tarjeta_warning": "#c89647",
        "icono_tarjeta_help": "#8b7ac4",
        "icono_tema_activo": "#c89647",
        "icono_tema_inactivo": "#556b83",
    },
}

_tema_actual = TEMA_SICAP_PREDETERMINADO


def obtener_tema_actual() -> str:
    return _tema_actual


def establecer_tema_actual(nombre_tema: str) -> str:
    global _tema_actual
    _tema_actual = nombre_tema if nombre_tema in _TEMAS_SICAP else TEMA_SICAP_PREDETERMINADO
    return _tema_actual


def obtener_paleta_tema(nombre_tema: str) -> dict[str, object]:
    tema_resuelto = nombre_tema if nombre_tema in _TEMAS_SICAP else TEMA_SICAP_PREDETERMINADO
    return deepcopy(_TEMAS_SICAP[tema_resuelto])


def obtener_paleta_tema_actual() -> dict[str, object]:
    return obtener_paleta_tema(_tema_actual)
