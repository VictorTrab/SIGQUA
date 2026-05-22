"""Paletas visuales compartidas para SICAP."""

from __future__ import annotations

from copy import deepcopy


TEMA_SICAP_PREDETERMINADO = "oscuro"

_TEMAS_SICAP: dict[str, dict[str, object]] = {
    "oscuro": {
        "nombre": "oscuro",
        "familia_tipografica": "Segoe UI",
        "tamano_fuente_base": 10,
        "tamano_titulo_modulo": 21,
        "tamano_titulo_panel": 14,
        "tamano_titulo_tarjeta": 20,
        "peso_titulo": 800,
        "peso_subtitulo": 700,
        "peso_cuerpo": 600,
        "fondo_principal": "#2c2966",
        "fondo_sidebar": "#393379",
        "fondo_header": "rgba(255, 255, 255, 0.12)",
        "fondo_dialogo": "#565384",
        "fondo_superficie": "rgba(255, 255, 255, 0.10)",
        "fondo_superficie_suave": "rgba(255, 255, 255, 0.05)",
        "fondo_superficie_muy_suave": "rgba(255, 255, 255, 0.03)",
        "fondo_panel_accion": "rgba(255, 255, 255, 0.06)",
        "fondo_input": "rgba(255, 255, 255, 0.11)",
        "fondo_input_focus": "rgba(255, 255, 255, 0.16)",
        "fondo_tabla_header": "rgba(255, 255, 255, 0.10)",
        "fondo_tabla_header_destacado": "rgba(108, 113, 190, 0.92)",
        "fondo_tabla_cuerpo": "rgba(74, 79, 154, 0.88)",
        "fondo_tabla_fila": "rgba(255, 255, 255, 0.03)",
        "fondo_tabla_fila_alterna": "rgba(255, 255, 255, 0.07)",
        "fondo_tabla_seleccion": "rgba(142, 201, 255, 0.10)",
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
        "borde_tabla": "rgba(255, 255, 255, 0.08)",
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
        "grafica_linea": "#35588b",
        "grafica_barras": "#4f8cff",
        "grafica_texto": "#5f6f84",
        "grafica_grid": "rgba(103, 118, 137, 0.24)",
        "grafica_borde_trozo": "#ffffff",
        "grafica_pie_colores": ("#4f8cff", "#6df1dc", "#ffb86c", "#8f7cff", "#9db2c9"),
        "icono_fila_base": "#c8d6f1",
        "icono_acento_info": "#4fa3ff",
        "icono_acento_warning": "#ff625c",
        "icono_tarjeta_info": "#8ec9ff",
        "icono_tarjeta_success": "#8de8c7",
        "icono_tarjeta_warning": "#f7cc7a",
        "icono_tarjeta_help": "#c6b6ff",
        "icono_tema_activo": "#f7cc7a",
        "icono_tema_inactivo": "#eef6ff",
        "acento_primario": "#6df1dc",
        "acento_hover": "#8ec9ff",
        "acento_seleccion": "rgba(45, 212, 191, 0.24)",
    },
    "claro": {
        "nombre": "claro",
        "familia_tipografica": "Segoe UI",
        "tamano_fuente_base": 10,
        "tamano_titulo_modulo": 22,
        "tamano_titulo_panel": 14,
        "tamano_titulo_tarjeta": 20,
        "peso_titulo": 800,
        "peso_subtitulo": 700,
        "peso_cuerpo": 600,
        "fondo_principal": "#f4f7fb",
        "fondo_sidebar": "#ffffff",
        "fondo_header": "#ffffff",
        "fondo_dialogo": "#ffffff",
        "fondo_superficie": "rgba(255, 255, 255, 0.98)",
        "fondo_superficie_suave": "rgba(250, 252, 255, 0.98)",
        "fondo_superficie_muy_suave": "rgba(246, 249, 253, 0.98)",
        "fondo_panel_accion": "rgba(244, 247, 252, 0.98)",
        "fondo_input": "rgba(247, 249, 252, 0.98)",
        "fondo_input_focus": "rgba(255, 255, 255, 1.0)",
        "fondo_tabla_header": "rgba(244, 247, 252, 1.0)",
        "fondo_tabla_header_destacado": "rgba(233, 238, 248, 1.0)",
        "fondo_tabla_cuerpo": "rgba(246, 249, 253, 0.98)",
        "fondo_tabla_fila": "rgba(255, 255, 255, 1.0)",
        "fondo_tabla_fila_alterna": "rgba(248, 250, 254, 1.0)",
        "fondo_tabla_seleccion": "rgba(30, 136, 229, 0.10)",
        "fondo_chip": "rgba(243, 246, 251, 1.0)",
        "fondo_chip_hover": "rgba(233, 239, 247, 1.0)",
        "fondo_chip_activo": "#deebff",
        "fondo_badge": "rgba(99, 115, 129, 0.10)",
        "fondo_badge_activo": "rgba(30, 136, 229, 0.12)",
        "fondo_exito": "rgba(33, 150, 83, 0.12)",
        "fondo_error": "rgba(220, 53, 69, 0.10)",
        "fondo_advertencia": "rgba(245, 158, 11, 0.14)",
        "fondo_avatar": "rgba(30, 136, 229, 0.12)",
        "borde_principal": "rgba(208, 218, 231, 0.92)",
        "borde_suave": "rgba(224, 231, 240, 0.96)",
        "borde_tabla": "rgba(224, 231, 240, 0.96)",
        "borde_medio": "rgba(194, 204, 218, 0.96)",
        "borde_foco_input": "rgba(30, 136, 229, 0.42)",
        "borde_chip_activo": "rgba(30, 136, 229, 0.24)",
        "borde_badge_activo": "rgba(30, 136, 229, 0.20)",
        "borde_exito": "rgba(33, 150, 83, 0.22)",
        "borde_error": "rgba(220, 53, 69, 0.22)",
        "borde_advertencia": "rgba(245, 158, 11, 0.24)",
        "borde_avatar": "rgba(30, 136, 229, 0.18)",
        "texto_principal": "#101828",
        "texto_secundario": "#667085",
        "texto_suave": "#6b7280",
        "texto_muted": "#7a8699",
        "texto_input": "#1f2937",
        "texto_chip": "#344054",
        "texto_chip_activo": "#0f3d91",
        "texto_badge": "#475467",
        "texto_badge_activo": "#0f3d91",
        "texto_exito": "#15803d",
        "texto_error": "#b42318",
        "texto_advertencia": "#b54708",
        "texto_panel_principal": "#0f172a",
        "texto_panel_secundario": "#64748b",
        "texto_panel_detalle": "#667085",
        "texto_panel_fuerte": "#101828",
        "tarjeta_panel_stop_1": "rgba(255, 255, 255, 255)",
        "tarjeta_panel_stop_2": "rgba(249, 251, 253, 255)",
        "tarjeta_panel_stop_3": "rgba(242, 246, 251, 255)",
        "tarjeta_panel_borde": "rgba(208, 218, 231, 0.95)",
        "ranking_barra": "rgba(208, 218, 231, 0.72)",
        "ranking_chunk": "rgba(51, 65, 85, 0.78)",
        "grafica_linea": "#334155",
        "grafica_barras": "#1e88e5",
        "grafica_texto": "#667085",
        "grafica_grid": "rgba(148, 163, 184, 0.20)",
        "grafica_borde_trozo": "#f8fafc",
        "grafica_pie_colores": ("#1e88e5", "#0ea5e9", "#22c55e", "#f59e0b", "#64748b"),
        "icono_fila_base": "#667085",
        "icono_acento_info": "#1e88e5",
        "icono_acento_warning": "#f97316",
        "icono_tarjeta_info": "#1e88e5",
        "icono_tarjeta_success": "#22c55e",
        "icono_tarjeta_warning": "#f59e0b",
        "icono_tarjeta_help": "#7c3aed",
        "icono_tema_activo": "#1e88e5",
        "icono_tema_inactivo": "#64748b",
        "acento_primario": "#1e88e5",
        "acento_hover": "#1565c0",
        "acento_seleccion": "rgba(30, 136, 229, 0.16)",
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


def obtener_fondo_header_destacado(nombre_tema: str) -> str:
    tema_resuelto = nombre_tema if nombre_tema in _TEMAS_SICAP else TEMA_SICAP_PREDETERMINADO
    if tema_resuelto == "claro":
        return str(_TEMAS_SICAP[tema_resuelto]["fondo_header"])
    return (
        "qlineargradient("
        "x1: 0, y1: 0, "
        "x2: 1, y2: 1, "
        "stop: 0 rgba(105, 96, 195, 0.92), "
        "stop: 0.55 rgba(89, 83, 179, 0.90), "
        "stop: 1 rgba(66, 63, 145, 0.94)"
        ")"
    )
