"""Carga centralizada de iconos para la UI."""

from __future__ import annotations

from functools import lru_cache

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from comun.configuracion.gestor_rutas import GestorRutas


@lru_cache(maxsize=32)
def obtener_icono_tabler(nombre_icono: str) -> QIcon:
    """Obtiene un icono Tabler descargado localmente."""
    ruta_icono = GestorRutas().obtener_ruta_icono_tabler(nombre_icono)
    return QIcon(str(ruta_icono))


@lru_cache(maxsize=128)
def obtener_icono_tabler_coloreado(
    nombre_icono: str,
    color_hexadecimal: str,
    tamano: int = 20,
) -> QIcon:
    """Obtiene un icono Tabler recoloreado para contextos con alto contraste."""
    return QIcon(
        obtener_pixmap_tabler_coloreado(
            nombre_icono=nombre_icono,
            color_hexadecimal=color_hexadecimal,
            tamano=tamano,
        )
    )


@lru_cache(maxsize=256)
def obtener_pixmap_tabler_coloreado(
    nombre_icono: str,
    color_hexadecimal: str,
    tamano: int = 20,
) -> QPixmap:
    """Renderiza un SVG de Tabler como pixmap coloreado."""
    ruta_icono = GestorRutas().obtener_ruta_icono_tabler(nombre_icono)
    renderer = QSvgRenderer(str(ruta_icono))
    pixmap = QPixmap(tamano, tamano)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(pixmap.rect(), QColor(color_hexadecimal))
    painter.end()
    return pixmap
