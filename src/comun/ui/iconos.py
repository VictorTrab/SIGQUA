"""Carga centralizada de iconos para la UI."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from comun.configuracion.gestor_rutas import GestorRutas


@lru_cache(maxsize=32)
def obtener_icono_tabler(nombre_icono: str) -> QIcon:
    """Obtiene un icono Tabler descargado localmente."""
    ruta_icono = _resolver_ruta_icono_tabler(nombre_icono)
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
    ruta_icono = _resolver_ruta_icono_tabler(nombre_icono)
    renderer = QSvgRenderer(str(ruta_icono))
    pixmap = QPixmap(tamano, tamano)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(pixmap.rect(), QColor(color_hexadecimal))
    painter.end()
    return pixmap


def _resolver_ruta_icono_tabler(nombre_icono: str) -> Path:
    """Normaliza nombres Tabler y evita avisos de Qt si falta un recurso."""
    gestor_rutas = GestorRutas()
    ruta_icono = gestor_rutas.obtener_ruta_icono_tabler(nombre_icono)
    if ruta_icono.exists():
        return ruta_icono

    if not ruta_icono.suffix:
        ruta_con_extension = ruta_icono.with_suffix(".svg")
        if ruta_con_extension.exists():
            return ruta_con_extension

    return gestor_rutas.obtener_ruta_icono_tabler("help.svg")


def obtener_pixmap_marca(
    ruta_marca: Path,
    ancho_logico: int,
    factor_escala: float = 1.0,
) -> QPixmap:
    """Renderiza la marca al tamano final para evitar reescalados borrosos."""
    factor = max(1.0, float(factor_escala or 1.0))
    ancho = max(1, int(ancho_logico))

    if ruta_marca.suffix.lower() == ".svg":
        return _renderizar_svg_marca(ruta_marca, ancho, factor)

    pixmap_original = QPixmap(str(ruta_marca))
    if pixmap_original.isNull():
        return QPixmap()

    pixmap = pixmap_original.scaledToWidth(
        round(ancho * factor),
        Qt.TransformationMode.SmoothTransformation,
    )
    pixmap.setDevicePixelRatio(factor)
    return pixmap


def _renderizar_svg_marca(ruta_marca: Path, ancho_logico: int, factor_escala: float) -> QPixmap:
    renderer = QSvgRenderer(str(ruta_marca))
    if not renderer.isValid():
        return QPixmap()

    tamano_svg = renderer.defaultSize()
    if tamano_svg.isEmpty() or tamano_svg.width() <= 0:
        proporcion_alto = 0.25
    else:
        proporcion_alto = tamano_svg.height() / tamano_svg.width()

    alto_logico = max(1, round(ancho_logico * proporcion_alto))
    pixmap = QPixmap(
        round(ancho_logico * factor_escala),
        round(alto_logico * factor_escala),
    )
    pixmap.setDevicePixelRatio(factor_escala)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    renderer.render(painter, QRectF(0, 0, ancho_logico, alto_logico))
    painter.end()
    return pixmap
