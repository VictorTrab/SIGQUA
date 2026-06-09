"""Vista del shell principal de SIGQUA."""

from __future__ import annotations

import re
from datetime import datetime
from statistics import fmean

from PySide6.QtCharts import (
    QBarCategoryAxis,
    QChart,
    QChartView,
    QLineSeries,
    QPieSeries,
    QValueAxis,
)
from PySide6.QtCore import (
    QEvent,
    QEasingCurve,
    QMargins,
    QPauseAnimation,
    QPoint,
    QPropertyAnimation,
    QRectF,
    QSequentialAnimationGroup,
    QSize,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QIcon,
    QLinearGradient,
    QPaintEvent,
    QPainter,
    QPen,
    QResizeEvent,
)
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from comun.configuracion.gestor_rutas import GestorRutas
from comun.ui import (
    BotonAccionContextual,
    DialogoBaseSigqua,
    DialogoConfirmacionSigqua,
    VistaPlaceholderModulo,
    aplicar_estilo_boton_operativo,
    crear_boton_operativo,
    obtener_icono_tabler_coloreado,
    obtener_pixmap_marca,
    resolver_variante_boton_modal,
)
from comun.ui.componentes import COLOR_FONDO_DIALOGO
from comun.ui.temas import (
    TEMA_SIGQUA_PREDETERMINADO,
    establecer_tema_actual,
    obtener_paleta_tema,
    resolver_nombre_tema,
)
from modulos.principal.entidades import (
    AnaliticaDashboard,
    CategoriaDashboard,
    EstadoModuloPrincipal,
    InsightDashboard,
    ModuloNavegacion,
    PuntoSerieDashboard,
)


COLOR_FONDO_PRINCIPAL = "#101214"
ANCHO_MINIMO_SHELL_PRINCIPAL = 960
ALTO_MINIMO_SHELL_PRINCIPAL = 640
ANCHO_SIDEBAR = 184
ANCHO_RUPTURA_DASHBOARD_AMPLIO = 1320
ANCHO_RUPTURA_DASHBOARD_MEDIO = 980
ANCHO_RUPTURA_METRICAS_6_COLUMNAS = 1120
ANCHO_RUPTURA_METRICAS_4_COLUMNAS = 980
ANCHO_RUPTURA_METRICAS_3_COLUMNAS = 820
ANCHO_RUPTURA_METRICAS_2_COLUMNAS = 760


def _crear_color_qt(valor: object, fallback: str = "#C5DDEE") -> QColor:
    """Convierte colores de paleta CSS a QColor para pintado manual."""
    texto = str(valor).strip()
    color = QColor(texto)
    if color.isValid():
        return color
    if texto.startswith("rgba(") and texto.endswith(")"):
        partes = [parte.strip() for parte in texto[5:-1].split(",")]
        if len(partes) == 4:
            try:
                rojo = int(float(partes[0]))
                verde = int(float(partes[1]))
                azul = int(float(partes[2]))
                alpha_bruto = float(partes[3])
                alpha = int(alpha_bruto * 255) if alpha_bruto <= 1 else int(alpha_bruto)
                return QColor(rojo, verde, azul, max(0, min(255, alpha)))
            except ValueError:
                pass
    return QColor(fallback)


class TarjetaMetricaEjecutiva(QFrame):
    """Tarjeta KPI con acento e iconografia para el dashboard ejecutivo."""

    def __init__(
        self,
        icono: str,
        color_acento: str,
        color_fondo: str,
        etiqueta_contexto: str,
        nombre_tema: str = TEMA_SIGQUA_PREDETERMINADO,
    ) -> None:
        super().__init__()
        self._icono = icono
        self._color_acento = color_acento
        self._color_fondo = color_fondo
        self._etiqueta_contexto = etiqueta_contexto
        self._tema_actual = nombre_tema
        self.setObjectName("tarjetaMetricaEjecutiva")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(142)
        self.setMaximumHeight(154)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 15)
        layout.setSpacing(9)

        fila_superior = QHBoxLayout()
        fila_superior.setContentsMargins(0, 0, 0, 0)
        fila_superior.setSpacing(8)

        self._titulo = QLabel("")
        self._titulo.setObjectName("tituloMetricaEjecutiva")
        self._titulo.setWordWrap(True)

        self._chip = QLabel(etiqueta_contexto.upper())
        self._chip.setObjectName("chipMetricaEjecutiva")
        self._chip.setAlignment(Qt.AlignmentFlag.AlignCenter)

        fila_superior.addWidget(self._titulo, 1)
        fila_superior.addStretch(1)
        fila_superior.addWidget(self._chip)

        self._valor = QLabel("")
        self._valor.setObjectName("valorMetricaEjecutiva")
        self._detalle = QLabel("")
        self._detalle.setObjectName("detalleMetricaEjecutiva")
        self._detalle.setWordWrap(True)

        layout.addLayout(fila_superior)
        layout.addWidget(self._valor)
        layout.addWidget(self._detalle)
        self._aplicar_estilo()

    def actualizar(self, titulo: str, valor: str, detalle: str) -> None:
        self._titulo.setText(titulo)
        self._valor.setText(valor)
        self._detalle.setText(detalle)

    def _aplicar_estilo(self) -> None:
        paleta = obtener_paleta_tema(self._tema_actual)
        self._chip.setStyleSheet(
            f"""
            background: {self._color_fondo};
            color: {paleta["texto_destacado"]};
            border: 1px solid {self._color_acento};
            border-radius: 10px;
            padding: 3px 8px;
            font-size: 9px;
            font-weight: 800;
            letter-spacing: 0.08em;
            """
        )
        self._titulo.setStyleSheet(
            f"color: {paleta['texto_panel_secundario']}; font-size: 11px; font-weight: 800;"
        )
        self._valor.setStyleSheet(
            f"color: {paleta['texto_panel_fuerte']}; font-size: 28px; font-weight: 900;"
        )
        self._detalle.setStyleSheet(
            f"color: {paleta['texto_panel_secundario']}; font-size: 10px; font-weight: 700;"
        )
        self.update()

    def paintEvent(self, evento: QPaintEvent) -> None:
        paleta = obtener_paleta_tema(self._tema_actual)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        recta = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        degradado = QLinearGradient(recta.topLeft(), recta.bottomRight())
        degradado.setColorAt(0.0, QColor(self._color_fondo))
        degradado.setColorAt(1.0, QColor(str(paleta["fondo_superficie_muy_suave"])))
        painter.setBrush(QBrush(degradado))
        painter.setPen(QPen(QColor(self._color_acento), 1))
        painter.drawRoundedRect(recta, 16, 16)
        painter.end()

    def aplicar_tema(self, nombre_tema: str) -> None:
        self._tema_actual = nombre_tema
        self._aplicar_estilo()


class FilaRanking(QFrame):
    """Fila compacta con barra de progreso para ranking lateral."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("filaRanking")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self._etiqueta = QLabel("")
        self._etiqueta.setObjectName("rankingEtiqueta")
        self._barra = QProgressBar()
        self._barra.setTextVisible(False)
        self._barra.setMaximumHeight(8)
        self._barra.setObjectName("rankingBarra")
        self._valor = QLabel("")
        self._valor.setObjectName("rankingValor")

        layout.addWidget(self._etiqueta, 2)
        layout.addWidget(self._barra, 3)
        layout.addWidget(self._valor, 1, alignment=Qt.AlignmentFlag.AlignRight)

    def actualizar(self, etiqueta: str, porcentaje: float, valor_formateado: str) -> None:
        self._etiqueta.setText(etiqueta)
        self._barra.setValue(int(max(0.0, min(100.0, porcentaje))))
        self._valor.setText(valor_formateado)


class TarjetaInsight(QWidget):
    """Tarjeta compacta para lecturas rapidas del panel."""

    def __init__(self, nombre_tema: str = TEMA_SIGQUA_PREDETERMINADO) -> None:
        super().__init__()
        self._tema_actual = nombre_tema
        self._icono_actual = "info-circle.svg"
        self._color_actual = "#75C7F0"
        self.setObjectName("tarjetaInsight")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        sombra = QGraphicsDropShadowEffect(self)
        sombra.setBlurRadius(16)
        sombra.setOffset(0, 4)
        sombra.setColor(QColor(0, 0, 0, 72))
        self.setGraphicsEffect(sombra)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 11, 12, 11)
        layout.setSpacing(11)

        self._insignia = QLabel("")
        self._insignia.setObjectName("insigniaInsight")
        self._insignia.setFixedSize(38, 38)
        self._insignia.setAlignment(Qt.AlignmentFlag.AlignCenter)

        contenido = QVBoxLayout()
        contenido.setContentsMargins(0, 0, 0, 0)
        contenido.setSpacing(5)

        self._titulo = QLabel("")
        self._titulo.setObjectName("insightTitulo")
        self._valor = QLabel("")
        self._valor.setObjectName("insightValor")
        self._detalle = QLabel("")
        self._detalle.setObjectName("insightDetalle")
        self._detalle.setWordWrap(True)

        contenido.addWidget(self._titulo)
        contenido.addWidget(self._valor)
        contenido.addWidget(self._detalle)
        layout.addWidget(self._insignia, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addLayout(contenido, 1)

    def actualizar(self, insight: InsightDashboard) -> None:
        self._icono_actual, self._color_actual = self._resolver_visual_insight(insight.titulo)
        self._titulo.setText("" if self._titulo_se_repite_en_valor(insight.titulo) else insight.titulo)
        self._titulo.setVisible(not self._titulo_se_repite_en_valor(insight.titulo))
        self._valor.setText(self._formatear_valor_visible(insight.titulo, insight.valor))
        self._detalle.setText(self._resumir_detalle(insight.titulo, insight.detalle))
        self._aplicar_estilo()

    def aplicar_tema(self, nombre_tema: str) -> None:
        self._tema_actual = resolver_nombre_tema(nombre_tema)
        self._aplicar_estilo()

    @staticmethod
    def _resolver_visual_insight(titulo: str) -> tuple[str, str]:
        texto = titulo.lower()
        if "comprometidos" in texto:
            return "alert-triangle.svg", "#F27474"
        if "pagos" in texto:
            return "receipt-2.svg", "#75C7F0"
        if "cargos" in texto:
            return "urgent.svg", "#F5B84B"
        if "planes" in texto:
            return "calendar-stats.svg", "#A78BFA"
        if "ultimo" in texto:
            return "clock.svg", "#37D399"
        return "info-circle.svg", "#75C7F0"

    def _aplicar_estilo(self) -> None:
        color = QColor(self._color_actual)
        fondo = QColor(color)
        fondo.setAlpha(44)
        borde = QColor(color)
        borde.setAlpha(112)
        self._insignia.setPixmap(
            obtener_icono_tabler_coloreado(self._icono_actual, self._color_actual, tamano=18).pixmap(18, 18)
        )
        self._insignia.setStyleSheet(
            f"""
            QLabel#insigniaInsight {{
                background: rgba({fondo.red()}, {fondo.green()}, {fondo.blue()}, {fondo.alpha()});
                border: 1px solid rgba({borde.red()}, {borde.green()}, {borde.blue()}, {borde.alpha()});
                border-radius: 12px;
            }}
            """
        )

    @staticmethod
    def _resumir_detalle(titulo: str, detalle: str) -> str:
        texto = detalle.strip()
        if "ultimo pago" in titulo.lower():
            texto = texto.split(" por ", 1)[0].strip()
            coincidencia_fecha = re.search(r"\d{2}/\d{2}/\d{4}", texto)
            if coincidencia_fecha is not None:
                nombre = texto[: coincidencia_fecha.start()].strip()
                for separador in ("\u00c2\u00b7", "\u00b7", "?", "|", "-"):
                    nombre = nombre.replace(separador, " ")
                nombre = " ".join(nombre.split())
                texto = f"{nombre} - {coincidencia_fecha.group(0)}" if nombre else coincidencia_fecha.group(0)
        if len(texto) <= 92:
            return texto
        return f"{texto[:89].rstrip()}..."

    @staticmethod
    def _formatear_valor_visible(titulo: str, valor: str) -> str:
        titulo_normalizado = titulo.strip().lower()
        valor_limpio = valor.strip()
        if titulo_normalizado == "servicios comprometidos":
            return f"{valor_limpio} {'servicio comprometido' if valor_limpio == '1' else 'servicios comprometidos'}"
        if titulo_normalizado == "cargos pendientes":
            return f"{valor_limpio} {'cargo pendiente' if valor_limpio == '1' else 'cargos pendientes'}"
        if titulo_normalizado == "planes de pago activos":
            return f"{valor_limpio} {'plan activo' if valor_limpio == '1' else 'planes activos'}"
        return valor_limpio

    @staticmethod
    def _titulo_se_repite_en_valor(titulo: str) -> bool:
        return titulo.strip().lower() in {
            "servicios comprometidos",
            "cargos pendientes",
            "planes de pago activos",
        }


class GraficoBarrasEstadoServicio(QWidget):
    """Grafico compacto de barras por estado operativo del servicio."""

    def __init__(self, nombre_tema: str = TEMA_SIGQUA_PREDETERMINADO) -> None:
        super().__init__()
        self._tema_actual = nombre_tema
        self._paleta = obtener_paleta_tema(nombre_tema)
        self._categorias: tuple[CategoriaDashboard, ...] = ()
        self.setObjectName("graficoEstadoServicio")
        self.setMinimumHeight(160)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def actualizar(self, categorias: tuple[CategoriaDashboard, ...]) -> None:
        self._categorias = tuple(categorias)
        self.update()

    def aplicar_tema(self, nombre_tema: str) -> None:
        self._tema_actual = resolver_nombre_tema(nombre_tema)
        self._paleta = obtener_paleta_tema(self._tema_actual)
        self.update()

    def paintEvent(self, evento: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        recta = QRectF(self.contentsRect()).adjusted(8, 8, -8, -8)
        datos = tuple(c for c in self._categorias if c.valor >= 0)
        if not datos or sum(c.valor for c in datos) <= 0:
            self._dibujar_estado_vacio(
                painter,
                recta,
                "Sin casas registradas para mostrar estado del servicio.",
            )
            painter.end()
            return

        area = QRectF(recta.left() + 32, recta.top() + 18, recta.width() - 42, recta.height() - 50)
        maximo = max((c.valor for c in datos), default=1.0) or 1.0
        self._dibujar_grilla(painter, area, maximo)
        paso = area.width() / max(1, len(datos))
        ancho_barra = min(46.0, paso * 0.52)
        fuente_valor = QFont(str(self._paleta["familia_tipografica"]), 9, QFont.Weight.Bold)
        fuente_etiqueta = QFont(str(self._paleta["familia_tipografica"]), 8, QFont.Weight.DemiBold)

        for indice, categoria in enumerate(datos):
            alto = max(3.0, (categoria.valor / maximo) * area.height())
            x = area.left() + indice * paso + (paso - ancho_barra) / 2
            barra = QRectF(x, area.bottom() - alto, ancho_barra, alto)
            color = QColor(self._color_estado(categoria.etiqueta))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawRoundedRect(barra, 8, 8)

            painter.setFont(fuente_valor)
            painter.setPen(QColor(str(self._paleta["grafica_texto_fuerte"])))
            painter.drawText(
                QRectF(x - 18, barra.top() - 22, ancho_barra + 36, 18),
                Qt.AlignmentFlag.AlignCenter,
                f"{int(categoria.valor):,}",
            )
            painter.setFont(fuente_etiqueta)
            painter.setPen(QColor(str(self._paleta["grafica_texto_suave"])))
            etiqueta = painter.fontMetrics().elidedText(
                categoria.etiqueta.title(),
                Qt.TextElideMode.ElideRight,
                int(max(40, paso - 8)),
            )
            painter.drawText(
                QRectF(area.left() + indice * paso, area.bottom() + 8, paso, 24),
                Qt.AlignmentFlag.AlignCenter,
                etiqueta,
            )
        painter.end()

    def _color_estado(self, etiqueta: str) -> str:
        texto = etiqueta.lower()
        if "activa" in texto:
            return str(self._paleta["grafica_barra_activo"])
        if "cortada" in texto:
            return str(self._paleta["grafica_barra_cortado"])
        if "suspendida" in texto:
            return str(self._paleta["grafica_barra_suspendido"])
        if "reconexion" in texto:
            return str(self._paleta["grafica_barra_reconexion"])
        return str(self._paleta["grafica_barra_inactivo"])

    def _dibujar_grilla(self, painter: QPainter, area: QRectF, maximo: float) -> None:
        painter.setPen(QPen(_crear_color_qt(self._paleta["grafica_grid_fuerte"], "#92B6CC"), 1))
        fuente = QFont(str(self._paleta["familia_tipografica"]), 8, QFont.Weight.DemiBold)
        painter.setFont(fuente)
        for indice in range(5):
            y = area.bottom() - (area.height() * indice / 4)
            painter.drawLine(int(area.left()), int(y), int(area.right()), int(y))
            valor = int(maximo * indice / 4)
            painter.setPen(QColor(str(self._paleta["grafica_texto_suave"])))
            painter.drawText(QRectF(area.left() - 34, y - 9, 28, 18), Qt.AlignmentFlag.AlignRight, str(valor))
            painter.setPen(QPen(_crear_color_qt(self._paleta["grafica_grid_fuerte"], "#92B6CC"), 1))

    def _dibujar_estado_vacio(self, painter: QPainter, recta: QRectF, mensaje: str) -> None:
        painter.setPen(QColor(str(self._paleta["grafica_texto_suave"])))
        painter.setFont(QFont(str(self._paleta["familia_tipografica"]), 10, QFont.Weight.DemiBold))
        painter.drawText(recta, Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, mensaje)


class GraficoBarrasHorizontalesDashboard(QWidget):
    """Grafico horizontal para ranking de deuda por barrio."""

    def __init__(self, nombre_tema: str = TEMA_SIGQUA_PREDETERMINADO) -> None:
        super().__init__()
        self._tema_actual = nombre_tema
        self._paleta = obtener_paleta_tema(nombre_tema)
        self._categorias: tuple[CategoriaDashboard, ...] = ()
        self.setObjectName("graficoDeudaBarrio")
        self.setMinimumHeight(162)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def actualizar(self, categorias: tuple[CategoriaDashboard, ...]) -> None:
        self._categorias = tuple(sorted(categorias, key=lambda categoria: categoria.valor, reverse=True)[:6])
        self.update()

    def aplicar_tema(self, nombre_tema: str) -> None:
        self._tema_actual = resolver_nombre_tema(nombre_tema)
        self._paleta = obtener_paleta_tema(self._tema_actual)
        self.update()

    def paintEvent(self, evento: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        recta = QRectF(self.contentsRect()).adjusted(8, 4, -8, -6)
        datos = tuple(c for c in self._categorias if c.valor > 0)
        if not datos:
            self._dibujar_estado_vacio(painter, recta, "No hay deuda pendiente por barrio.")
            painter.end()
            return

        label_ancho = min(152.0, max(94.0, recta.width() * 0.28))
        valor_ancho = 92.0
        area = QRectF(recta.left() + label_ancho, recta.top() + 8, recta.width() - label_ancho - valor_ancho, recta.height() - 18)
        maximo = max(c.valor for c in datos)
        alto_fila = area.height() / max(1, len(datos))
        alto_barra = min(20.0, alto_fila * 0.48)
        fuente = QFont(str(self._paleta["familia_tipografica"]), 9, QFont.Weight.DemiBold)
        painter.setFont(fuente)

        for indice, categoria in enumerate(datos):
            centro_y = area.top() + indice * alto_fila + alto_fila / 2
            texto_barrio = painter.fontMetrics().elidedText(
                categoria.etiqueta,
                Qt.TextElideMode.ElideRight,
                int(label_ancho - 12),
            )
            painter.setPen(QColor(str(self._paleta["grafica_texto_fuerte"])))
            painter.drawText(
                QRectF(recta.left(), centro_y - 12, label_ancho - 10, 24),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                texto_barrio,
            )
            fondo = QRectF(area.left(), centro_y - alto_barra / 2, area.width(), alto_barra)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(str(self._paleta["fondo_superficie_muy_suave"])))
            painter.drawRoundedRect(fondo, 8, 8)
            ancho = max(4.0, area.width() * categoria.valor / maximo)
            barra = QRectF(area.left(), centro_y - alto_barra / 2, ancho, alto_barra)
            degradado = QLinearGradient(barra.left(), barra.top(), barra.right(), barra.top())
            degradado.setColorAt(0.0, QColor(str(self._paleta["grafica_deuda_barra_inicio"])))
            degradado.setColorAt(1.0, QColor(str(self._paleta["grafica_deuda_barra_fin"])))
            painter.setBrush(QBrush(degradado))
            painter.drawRoundedRect(barra, 8, 8)
            painter.setPen(QColor(str(self._paleta["grafica_texto_suave"])))
            painter.drawText(
                QRectF(area.right() + 8, centro_y - 12, valor_ancho - 8, 24),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                self._formatear_moneda(categoria.valor),
            )

        painter.setPen(QPen(_crear_color_qt(self._paleta["grafica_grid_fuerte"], "#92B6CC"), 1))
        painter.drawLine(int(area.left()), int(area.bottom() + 4), int(area.right()), int(area.bottom() + 4))
        painter.end()

    @staticmethod
    def _formatear_moneda(valor: float) -> str:
        return f"L {valor:,.2f}"

    def _dibujar_estado_vacio(self, painter: QPainter, recta: QRectF, mensaje: str) -> None:
        painter.setPen(QColor(str(self._paleta["grafica_texto_suave"])))
        painter.setFont(QFont(str(self._paleta["familia_tipografica"]), 10, QFont.Weight.DemiBold))
        painter.drawText(recta, Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, mensaje)


class LeyendaDonutDeuda(QFrame):
    """Lista compacta para acompanar el donut de antiguedad de deuda."""

    def __init__(self, nombre_tema: str = TEMA_SIGQUA_PREDETERMINADO) -> None:
        super().__init__()
        self._tema_actual = nombre_tema
        self._paleta = obtener_paleta_tema(nombre_tema)
        self._categorias: tuple[CategoriaDashboard, ...] = ()
        self.setObjectName("leyendaDonutDeuda")
        self.setMinimumWidth(210)
        self.setMaximumWidth(270)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Maximum)
        sombra = QGraphicsDropShadowEffect(self)
        sombra.setBlurRadius(18)
        sombra.setOffset(0, 6)
        sombra.setColor(QColor(0, 0, 0, 90))
        self.setGraphicsEffect(sombra)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(12, 10, 12, 10)
        self._layout.setSpacing(7)

    def actualizar(self, categorias: tuple[CategoriaDashboard, ...]) -> None:
        self._categorias = tuple(categorias)
        self._reconstruir()

    def aplicar_tema(self, nombre_tema: str) -> None:
        self._tema_actual = resolver_nombre_tema(nombre_tema)
        self._paleta = obtener_paleta_tema(self._tema_actual)
        self._reconstruir()

    def _reconstruir(self) -> None:
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        total = sum(c.valor for c in self._categorias)
        if total <= 0:
            vacio = QLabel("Sin deuda vencida registrada.")
            vacio.setObjectName("leyendaDonutTexto")
            vacio.setWordWrap(True)
            self._layout.addWidget(vacio)
            self.setMaximumHeight(74)
            return
        visibles = tuple(categoria for categoria in self._categorias if categoria.valor > 0)
        for categoria in visibles:
            self._layout.addWidget(self._crear_fila(categoria, total))
        self.setMaximumHeight(max(82, 30 + len(visibles) * 30))

    def _crear_fila(self, categoria: CategoriaDashboard, total: float) -> QWidget:
        fila = QWidget()
        fila.setObjectName("filaLeyendaDonut")
        layout = QHBoxLayout(fila)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(9)
        swatch = QFrame()
        swatch.setFixedSize(10, 10)
        swatch.setObjectName("swatchLeyendaDonut")
        swatch.setStyleSheet(
            f"QFrame#swatchLeyendaDonut {{ background: {self._color_rango(categoria.etiqueta)}; border-radius: 5px; }}"
        )
        texto = QLabel(categoria.etiqueta)
        texto.setObjectName("leyendaDonutTexto")
        valor = QLabel(f"{self._formatear_moneda(categoria.valor)} | {categoria.valor / total * 100:.0f}%")
        valor.setObjectName("leyendaDonutValor")
        valor.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(swatch)
        layout.addWidget(texto, 1)
        layout.addWidget(valor, 0)
        return fila

    def _color_rango(self, etiqueta: str) -> str:
        texto = etiqueta.lower()
        if "0-30" in texto:
            return str(self._paleta["grafica_donut_0_30"])
        if "31-60" in texto:
            return str(self._paleta["grafica_donut_31_60"])
        if "61-90" in texto:
            return str(self._paleta["grafica_donut_61_90"])
        return str(self._paleta["grafica_donut_90_mas"])

    @staticmethod
    def _formatear_moneda(valor: float) -> str:
        return f"L {valor:,.2f}"


class BotonSidebar(QPushButton):
    """Boton de navegacion con icono y texto centrados por layout."""

    def __init__(self, texto: str) -> None:
        super().__init__()
        self._texto_sidebar = texto
        self._icono_sidebar = QIcon()
        super().setText("")
        self.setObjectName("botonSidebar")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(False)
        self.setMinimumHeight(36)
        self.setMaximumHeight(38)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setIconSize(QSize(16, 16))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._contenido = QWidget()
        self._contenido.setObjectName("contenidoBotonSidebar")
        self._contenido.setFixedWidth(148)
        self._contenido.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout_contenido = QHBoxLayout(self._contenido)
        layout_contenido.setContentsMargins(0, 0, 0, 0)
        layout_contenido.setSpacing(7)

        self._icono = QLabel()
        self._icono.setObjectName("iconoBotonSidebar")
        self._icono.setFixedSize(16, 16)
        self._icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icono.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        self._texto = QLabel(texto)
        self._texto.setObjectName("textoBotonSidebar")
        self._texto.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self._texto.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._texto.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout_contenido.addWidget(self._icono, 0, Qt.AlignmentFlag.AlignVCenter)
        layout_contenido.addWidget(self._texto, 1, Qt.AlignmentFlag.AlignVCenter)
        layout.addStretch(1)
        layout.addWidget(self._contenido, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addStretch(1)

    def text(self) -> str:
        return self._texto_sidebar

    def setText(self, texto: str) -> None:  # noqa: N802
        self._texto_sidebar = texto
        super().setText("")
        if hasattr(self, "_texto"):
            self._texto.setText(texto)

    def setIcon(self, icono: QIcon) -> None:  # noqa: N802
        self._icono_sidebar = icono
        if hasattr(self, "_icono"):
            pixmap = icono.pixmap(self.iconSize())
            self._icono.setPixmap(pixmap)

    def icon(self) -> QIcon:
        return self._icono_sidebar

    def aplicar_estado_visual(
        self,
        *,
        activo: bool,
        color_texto: str,
        nombre_icono: str,
        color_icono: str,
    ) -> None:
        self.setProperty("activo", activo)
        self._texto.setProperty("activo", activo)
        self._texto.setStyleSheet(f"color: {color_texto};")
        self.setIcon(obtener_icono_tabler_coloreado(nombre_icono, color_icono, tamano=16))
        self.style().unpolish(self)
        self.style().polish(self)
        self._texto.style().unpolish(self._texto)
        self._texto.style().polish(self._texto)


class SeccionSidebarDesplegable(QFrame):
    """Agrupa modulos del sidebar en bloques compactos."""

    def __init__(self, titulo: str) -> None:
        super().__init__()
        self._titulo = titulo
        self._expandida = True
        self._modulos: set[str] = set()
        self._modulo_activo: str | None = None
        self.setObjectName("seccionSidebarCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._etiqueta_titulo = QLabel(titulo.upper())
        self._etiqueta_titulo.setObjectName("tituloSeccionSidebar")

        self._contenedor_items = QWidget()
        self._contenedor_items.setObjectName("contenedorItemsSidebar")
        self._layout_items = QVBoxLayout(self._contenedor_items)
        self._layout_items.setContentsMargins(0, 0, 0, 0)
        self._layout_items.setSpacing(6)

        layout.addWidget(self._etiqueta_titulo)
        layout.addWidget(self._contenedor_items)

    def agregar_boton(self, codigo_modulo: str, boton: QPushButton) -> None:
        self._modulos.add(codigo_modulo)
        self._layout_items.addWidget(boton)

    def marcar_modulo_activo(self, codigo_modulo: str) -> None:
        self._modulo_activo = codigo_modulo if codigo_modulo in self._modulos else None
        tiene_activo = self._modulo_activo is not None
        self._etiqueta_titulo.setProperty("activa", tiene_activo)
        self._etiqueta_titulo.style().unpolish(self._etiqueta_titulo)
        self._etiqueta_titulo.style().polish(self._etiqueta_titulo)
        if tiene_activo:
            self.establecer_expandida(True, forzar=True)

    def establecer_expandida(self, expandida: bool, forzar: bool = False) -> None:
        if not expandida and self._modulo_activo is not None and not forzar:
            return
        self._expandida = expandida
        self._contenedor_items.setVisible(expandida)
        self._etiqueta_titulo.setProperty("expandida", expandida)
        self._etiqueta_titulo.style().unpolish(self._etiqueta_titulo)
        self._etiqueta_titulo.style().polish(self._etiqueta_titulo)

    def esta_expandida(self) -> bool:
        return self._expandida


class BotonPerfilUsuario(QPushButton):
    """Tarjeta compacta que abre el perfil desde el encabezado del modulo."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("botonPerfilHeader")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(False)
        self.setMinimumHeight(48)
        self.setMaximumHeight(50)
        self.setMinimumWidth(154)
        self.setMaximumWidth(190)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setToolTip("Perfil de usuario")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(7)

        self._avatar = QLabel("US")
        self._avatar.setObjectName("avatarPerfilHeader")
        self._avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._avatar.setFixedSize(32, 32)

        bloque = QVBoxLayout()
        bloque.setContentsMargins(0, 0, 0, 0)
        bloque.setSpacing(1)
        self._nombre = QLabel("Usuario")
        self._nombre.setObjectName("nombrePerfilHeader")
        self._nombre.setWordWrap(False)
        self._rol = QLabel("")
        self._rol.setObjectName("rolPerfilHeader")
        bloque.addWidget(self._nombre)
        bloque.addWidget(self._rol)

        layout.addWidget(self._avatar, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(bloque, 1)

    def actualizar(self, nombre_completo: str, perfil: str) -> None:
        self._avatar.setText(self._resolver_iniciales(nombre_completo))
        self._nombre.setText(self._resolver_nombre_compacto(nombre_completo))
        self._rol.setText(perfil.replace("_", " ").title())
        self.setToolTip(f"{nombre_completo or 'Usuario'} · {perfil}")
        self.updateGeometry()
        self.adjustSize()

    def sizeHint(self) -> QSize:
        return QSize(174, 50)

    def minimumSizeHint(self) -> QSize:
        return QSize(154, 48)

    @staticmethod
    def _resolver_iniciales(nombre_completo: str) -> str:
        partes = [parte for parte in nombre_completo.strip().split() if parte]
        if not partes:
            return "US"
        if len(partes) == 1:
            return partes[0][:2].upper()
        return f"{partes[0][0]}{partes[1][0]}".upper()

    @staticmethod
    def _resolver_nombre_compacto(nombre_completo: str) -> str:
        partes = [parte for parte in nombre_completo.strip().split() if parte]
        if not partes:
            return "Usuario"
        if len(partes) == 1:
            return partes[0]
        return f"{partes[0]} {partes[1]}"


class PanelPerfilUsuario(QFrame):
    """Ventana flotante de perfil inspirada en el componente de Figma."""

    cerrar_sesion_solicitada = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._tema_actual = TEMA_SIGQUA_PREDETERMINADO
        self._paleta_tema = obtener_paleta_tema(self._tema_actual)
        self.setObjectName("panelPerfilUsuario")
        self.setWindowFlags(
            Qt.WindowType.Popup
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setMinimumWidth(330)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        encabezado = QFrame()
        encabezado.setObjectName("encabezadoPanelPerfil")
        layout_encabezado = QHBoxLayout(encabezado)
        layout_encabezado.setContentsMargins(14, 14, 14, 14)
        layout_encabezado.setSpacing(12)

        self._avatar = QLabel("US")
        self._avatar.setObjectName("avatarPanelPerfil")
        self._avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._avatar.setFixedSize(54, 54)

        bloque_identidad = QVBoxLayout()
        bloque_identidad.setContentsMargins(0, 0, 0, 0)
        bloque_identidad.setSpacing(2)
        self._nombre = QLabel("")
        self._nombre.setObjectName("nombrePanelPerfil")
        self._rol = QLabel("")
        self._rol.setObjectName("rolPanelPerfil")
        bloque_identidad.addWidget(self._nombre)
        bloque_identidad.addWidget(self._rol)

        layout_encabezado.addWidget(self._avatar)
        layout_encabezado.addLayout(bloque_identidad, 1)

        panel_datos = QFrame()
        panel_datos.setObjectName("bloquePanelPerfil")
        layout_datos = QVBoxLayout(panel_datos)
        layout_datos.setContentsMargins(14, 14, 14, 14)
        layout_datos.setSpacing(10)

        self._correo = self._crear_fila_dato("Correo electr\u00f3nico", "mail.svg")
        self._ultimo_acceso = self._crear_fila_dato("\u00daltimo acceso", "clock.svg")
        self._estado_sesion = self._crear_fila_dato("Estado de sesi\u00f3n", "circle-check.svg")
        layout_datos.addWidget(self._correo["contenedor"])
        layout_datos.addWidget(self._ultimo_acceso["contenedor"])
        layout_datos.addWidget(self._estado_sesion["contenedor"])

        panel_acciones = QFrame()
        panel_acciones.setObjectName("bloquePanelPerfil")
        layout_acciones = QVBoxLayout(panel_acciones)
        layout_acciones.setContentsMargins(10, 10, 10, 10)
        layout_acciones.setSpacing(6)

        self._boton_cerrar_sesion = self._crear_boton_accion(
            "Cerrar sesi\u00f3n",
            "arrow-left.svg",
            "salida",
        )
        self._boton_cerrar_sesion.clicked.connect(self._emitir_cierre_sesion)
        layout_acciones.addWidget(self._boton_cerrar_sesion)

        layout.addWidget(encabezado)
        layout.addWidget(panel_datos)
        layout.addWidget(panel_acciones)
        self._aplicar_estilos()

    def actualizar(
        self,
        nombre_completo: str,
        rol: str,
        correo: str,
        ultimo_acceso: str,
        estado_sesion: str,
    ) -> None:
        self._avatar.setText(BotonPerfilUsuario._resolver_iniciales(nombre_completo))
        self._nombre.setText(nombre_completo)
        self._rol.setText(rol)
        self._correo["valor"].setText(correo)
        self._ultimo_acceso["valor"].setText(ultimo_acceso)
        self._estado_sesion["valor"].setText(estado_sesion)

    def mostrar_desde(self, disparador: QWidget) -> bool:
        self.adjustSize()
        ventana = disparador.window().windowHandle() if disparador.window() is not None else None
        pantalla = ventana.screen() if ventana is not None else None
        geometria = pantalla.availableGeometry() if pantalla is not None else None
        posicion = disparador.mapToGlobal(disparador.rect().bottomRight())
        destino_x = posicion.x() - self.width()
        destino_y = posicion.y() + 8
        if geometria is not None:
            destino_x = min(destino_x, geometria.right() - self.width() - 8)
            destino_y = min(destino_y, geometria.bottom() - self.height() - 8)
            destino_x = max(geometria.left() + 8, destino_x)
            destino_y = max(geometria.top() + 8, destino_y)
        self.move(QPoint(destino_x, destino_y))
        self.show()
        self.raise_()
        return self.isVisible()

    def _crear_fila_dato(self, titulo: str, icono: str) -> dict[str, QWidget | QLabel]:
        contenedor = QFrame()
        contenedor.setObjectName("filaDatoPerfil")
        layout = QHBoxLayout(contenedor)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        icono_label = QLabel("")
        icono_label.setObjectName("iconoDatoPerfil")
        icono_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icono_label.setFixedSize(32, 32)
        icono_label.setPixmap(
            obtener_icono_tabler_coloreado(icono, "#d7e9ff", tamano=16).pixmap(16, 16)
        )

        bloque = QVBoxLayout()
        bloque.setContentsMargins(0, 0, 0, 0)
        bloque.setSpacing(1)
        etiqueta = QLabel(titulo)
        etiqueta.setObjectName("tituloDatoPerfil")
        valor = QLabel("")
        valor.setObjectName("valorDatoPerfil")
        valor.setWordWrap(True)
        bloque.addWidget(etiqueta)
        bloque.addWidget(valor)

        layout.addWidget(icono_label, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addLayout(bloque, 1)
        return {"contenedor": contenedor, "valor": valor}

    def _crear_boton_accion(self, texto: str, icono: str, variante: str) -> QPushButton:
        boton = BotonAccionContextual(texto, icono, variante)
        boton.setMinimumHeight(46)
        return boton

    def aplicar_tema(self, nombre_tema: str) -> None:
        self._tema_actual = (
            resolver_nombre_tema(nombre_tema)
        )
        self._paleta_tema = obtener_paleta_tema(self._tema_actual)
        self._aplicar_estilos()

    def _aplicar_estilos(self) -> None:
        paleta = self._paleta_tema
        self.setStyleSheet(
            f"""
            QFrame#panelPerfilUsuario {{
                background: {paleta["fondo_dialogo"]};
                border: 1px solid {paleta["borde_principal"]};
                border-radius: 4px;
            }}
            QFrame#encabezadoPanelPerfil,
            QFrame#bloquePanelPerfil,
            QFrame#piePanelPerfil {{
                background: {paleta["fondo_superficie_suave"]};
                border: 1px solid {paleta["borde_suave"]};
                border-radius: 10px;
            }}
            QFrame#filaDatoPerfil {{
                background: transparent;
                border: none;
            }}
            QLabel#avatarPanelPerfil {{
                background: {paleta["fondo_avatar"]};
                border: 1px solid {paleta["borde_avatar"]};
                border-radius: 27px;
                color: {paleta["texto_principal"]};
                font-size: 18px;
                font-weight: 900;
            }}
            QLabel#nombrePanelPerfil {{
                color: {paleta["texto_principal"]};
                font-size: 16px;
                font-weight: 900;
            }}
            QLabel#rolPanelPerfil,
            QLabel#tituloDatoPerfil,
            QLabel#detallePanelPerfil {{
                color: {paleta["texto_secundario"]};
                font-size: 12px;
                font-weight: {paleta["peso_cuerpo"]};
            }}
            QLabel#valorDatoPerfil,
            QLabel#sistemaPanelPerfil {{
                color: {paleta["texto_panel_principal"]};
                font-size: 13px;
                font-weight: {paleta["peso_titulo"]};
            }}
            QLabel#sistemaPanelPerfil {{
                font-size: 14px;
            }}
            QLabel#iconoDatoPerfil {{
                background: {paleta["fondo_superficie_suave"]};
                border: 1px solid {paleta["borde_suave"]};
                border-radius: 12px;
            }}
            """
        )

    def _emitir_cierre_sesion(self) -> None:
        self.hide()
        dialogo = DialogoConfirmacionSigqua(
            titulo="Cerrar sesi\u00f3n",
            descripcion="\u00bfDeseas cerrar la sesi\u00f3n actual?",
            texto_confirmar="Confirmar salida",
            icono="alert-triangle.svg",
            variante_confirmar="salida",
            color_fondo=COLOR_FONDO_DIALOGO,
            parent=self.parentWidget() or self,
        )
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            self.cerrar_sesion_solicitada.emit()


class DialogoPerfilUsuario(DialogoBaseSigqua):
    """Modal informativo del usuario y su sesión activa."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumWidth(440)

        titulo = QLabel("Perfil de usuario")
        titulo.setObjectName("tituloDialogoSigqua")
        descripcion = QLabel("Información de la sesión activa en este equipo.")
        descripcion.setObjectName("descripcionDialogoSigqua")
        self.layout_cabecera.addWidget(titulo)
        self.layout_cabecera.addWidget(descripcion)

        identidad = QFrame()
        identidad.setObjectName("bloqueDialogoSigqua")
        layout_identidad = QHBoxLayout(identidad)
        layout_identidad.setContentsMargins(14, 14, 14, 14)
        layout_identidad.setSpacing(12)

        self._avatar = QLabel("US")
        self._avatar.setObjectName("avatarPanelPerfil")
        self._avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._avatar.setFixedSize(54, 54)
        self._nombre = QLabel("")
        self._nombre.setObjectName("nombrePanelPerfil")
        self._rol = QLabel("")
        self._rol.setObjectName("rolPanelPerfil")

        bloque_nombre = QVBoxLayout()
        bloque_nombre.setContentsMargins(0, 0, 0, 0)
        bloque_nombre.setSpacing(2)
        bloque_nombre.addWidget(self._nombre)
        bloque_nombre.addWidget(self._rol)
        layout_identidad.addWidget(self._avatar)
        layout_identidad.addLayout(bloque_nombre, 1)

        datos = QFrame()
        datos.setObjectName("bloqueDialogoSigqua")
        layout_datos = QVBoxLayout(datos)
        layout_datos.setContentsMargins(14, 14, 14, 14)
        layout_datos.setSpacing(10)
        self._correo = self._crear_fila_dato("Correo electrónico", "mail.svg")
        self._ultimo_acceso = self._crear_fila_dato("Último acceso", "clock.svg")
        self._estado_sesion = self._crear_fila_dato("Estado de sesión", "circle-check.svg")
        layout_datos.addWidget(self._correo["contenedor"])
        layout_datos.addWidget(self._ultimo_acceso["contenedor"])
        layout_datos.addWidget(self._estado_sesion["contenedor"])

        self.layout_cuerpo.addWidget(identidad)
        self.layout_cuerpo.addWidget(datos)

        fila_acciones = QHBoxLayout()
        fila_acciones.addStretch(1)
        boton_cerrar = BotonAccionContextual(
            "Cerrar",
            variante="neutro",
            centrado=True,
            mostrar_icono=False,
        )
        boton_cerrar.setMinimumWidth(120)
        boton_cerrar.clicked.connect(self.accept)
        fila_acciones.addWidget(boton_cerrar)
        self.layout_pie.addLayout(fila_acciones)
        self._aplicar_estilos_perfil()

    def actualizar(
        self,
        nombre_completo: str,
        rol: str,
        correo: str,
        ultimo_acceso: str,
        estado_sesion: str,
    ) -> None:
        self._avatar.setText(BotonPerfilUsuario._resolver_iniciales(nombre_completo))
        self._nombre.setText(nombre_completo)
        self._rol.setText(rol.replace("_", " ").title())
        self._correo["valor"].setText(correo)
        self._ultimo_acceso["valor"].setText(ultimo_acceso)
        self._estado_sesion["valor"].setText(estado_sesion)

    def aplicar_tema(self, nombre_tema: str) -> None:
        super().aplicar_tema(nombre_tema)
        self._aplicar_estilos_perfil()

    def _aplicar_estilos_perfil(self) -> None:
        paleta = self._paleta_tema
        self.setStyleSheet(
            self.styleSheet()
            + f"""
            QLabel#avatarPanelPerfil {{
                background: {paleta["fondo_avatar"]};
                border: 1px solid {paleta["borde_avatar"]};
                border-radius: 27px;
                color: {paleta["texto_principal"]};
                font-size: 17px;
                font-weight: 900;
            }}
            QLabel#nombrePanelPerfil {{
                color: {paleta["texto_principal"]};
                font-size: 16px;
                font-weight: 900;
            }}
            QLabel#rolPanelPerfil,
            QLabel#tituloDatoPerfil {{
                color: {paleta["texto_secundario"]};
                font-size: 11px;
                font-weight: 700;
            }}
            QLabel#valorDatoPerfil {{
                color: {paleta["texto_principal"]};
                font-size: 12px;
                font-weight: 800;
            }}
            QLabel#iconoDatoPerfil {{
                background: {paleta["fondo_superficie_muy_suave"]};
                border: 1px solid {paleta["borde_suave"]};
                border-radius: 6px;
            }}
            """
        )

    def _crear_fila_dato(self, titulo: str, icono: str) -> dict[str, QWidget | QLabel]:
        contenedor = QFrame()
        contenedor.setObjectName("filaDatoPerfil")
        layout = QHBoxLayout(contenedor)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        icono_label = QLabel("")
        icono_label.setObjectName("iconoDatoPerfil")
        icono_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icono_label.setFixedSize(32, 32)
        icono_label.setPixmap(
            obtener_icono_tabler_coloreado(
                icono,
                str(self._paleta_tema["modal_icono_campo"]),
                tamano=16,
            ).pixmap(16, 16)
        )

        bloque = QVBoxLayout()
        bloque.setContentsMargins(0, 0, 0, 0)
        bloque.setSpacing(1)
        etiqueta = QLabel(titulo)
        etiqueta.setObjectName("tituloDatoPerfil")
        valor = QLabel("")
        valor.setObjectName("valorDatoPerfil")
        valor.setWordWrap(True)
        bloque.addWidget(etiqueta)
        bloque.addWidget(valor)

        layout.addWidget(icono_label)
        layout.addLayout(bloque, 1)
        return {"contenedor": contenedor, "valor": valor}


class DialogoPruebaModalBase(QDialog):
    """Base de laboratorio para comparar estrategias de modal."""

    def __init__(
        self,
        titulo: str,
        descripcion: str,
        etiqueta_tecnica: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._titulo_modal = titulo
        self._descripcion_modal = descripcion
        self._etiqueta_tecnica = etiqueta_tecnica
        self.setModal(True)
        self.setMinimumWidth(480)
        self._layout_raiz = QVBoxLayout(self)
        self._layout_raiz.setContentsMargins(0, 0, 0, 0)
        self._layout_raiz.setSpacing(0)

    def _construir_panel_contenido(
        self,
        contenedor: QWidget,
        color_fondo: str,
        radio: int,
        borde: str,
    ) -> None:
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        titulo = QLabel(self._titulo_modal)
        titulo.setStyleSheet("color: #75C7F0; font-size: 22px; font-weight: 900;")
        descripcion = QLabel(self._descripcion_modal)
        descripcion.setWordWrap(True)
        descripcion.setStyleSheet("color: #C5DDEE; font-size: 13px; font-weight: 700;")

        etiqueta = QLabel(self._etiqueta_tecnica)
        etiqueta.setWordWrap(True)
        etiqueta.setStyleSheet(
            "color: rgba(247, 249, 255, 0.82);"
            "background: rgba(13, 42, 69, 0.78);"
            f"border: 1px solid {borde};"
            "padding: 8px 10px;"
            "font-size: 12px;"
            "font-weight: 700;"
            "border-radius: 4px;"
        )

        bloque = QFrame()
        bloque.setStyleSheet(
            "QFrame {"
            f"background: {color_fondo};"
            f"border: 1px solid {borde};"
            f"border-radius: {0 if radio <= 0 else 4}px;"
            "}"
        )
        layout_bloque = QVBoxLayout(bloque)
        layout_bloque.setContentsMargins(0, 0, 0, 0)
        layout_bloque.setSpacing(8)
        layout_bloque.addWidget(QLabel("Vista previa del cuerpo del modal"))
        layout_bloque.addWidget(
            QLabel("Color sólido base #0D2A45, misma familia visual que el flujo actual.")
        )

        fila_acciones = QHBoxLayout()
        fila_acciones.setContentsMargins(0, 0, 0, 0)
        fila_acciones.setSpacing(10)

        boton_cancelar = BotonAccionContextual(
            "Cancelar",
            variante=resolver_variante_boton_modal("Cancelar", "neutro"),
            centrado=True,
            mostrar_icono=False,
        )
        boton_cancelar.setMinimumWidth(132)
        boton_cancelar.clicked.connect(self.reject)

        boton_confirmar = BotonAccionContextual(
            "Confirmar prueba",
            variante=resolver_variante_boton_modal("Confirmar prueba", "primario"),
            centrado=True,
            mostrar_icono=False,
        )
        boton_confirmar.setMinimumWidth(160)
        boton_confirmar.clicked.connect(self.accept)

        fila_acciones.addWidget(boton_cancelar)
        fila_acciones.addStretch(1)
        fila_acciones.addWidget(boton_confirmar)

        layout.addWidget(titulo)
        layout.addWidget(descripcion)
        layout.addWidget(etiqueta)
        layout.addWidget(bloque)
        layout.addLayout(fila_acciones)


class DialogoPruebaModalSistema(DialogoPruebaModalBase):
    """Alternativa con marco nativo del sistema."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            titulo="Prueba modal con marco del sistema",
            descripcion="Usa QDialog estándar con borde nativo de Windows y panel interno redondeado.",
            etiqueta_tecnica="Alternativa robusta: evita forma personalizada de la ventana.",
            parent=parent,
        )
        self.setWindowTitle("Prueba modal del sistema")

        panel = QFrame()
        panel.setStyleSheet(
            "QFrame {"
            f"background: {COLOR_FONDO_DIALOGO};"
            "border: 1px solid rgba(126, 167, 196, 0.30);"
            "border-radius: 4px;"
            "}"
        )
        self._construir_panel_contenido(
            panel,
            COLOR_FONDO_DIALOGO,
            4,
            "rgba(126, 167, 196, 0.30)",
        )
        self._layout_raiz.addWidget(panel)


class DialogoPruebaModalRecto(DialogoPruebaModalBase):
    """Alternativa opaca rectangular sin esquinas redondeadas."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            titulo="Prueba modal rectangular",
            descripcion="Ventana opaca sin recorte ni translucencia, pensada para descartar artefactos.",
            etiqueta_tecnica="Alternativa de control: no usa máscara ni transparencia.",
            parent=parent,
        )
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setStyleSheet(f"QDialog {{ background: {COLOR_FONDO_DIALOGO}; }}")
        self._layout_raiz.setContentsMargins(0, 0, 0, 0)

        panel = QWidget()
        panel.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._construir_panel_contenido(
            panel,
            COLOR_FONDO_DIALOGO,
            0,
            "rgba(126, 167, 196, 0.30)",
        )
        self._layout_raiz.addWidget(panel)


class DialogoPruebaModalMascara(DialogoPruebaModalBase):
    """Alternativa opaca con máscara redondeada."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            titulo="Prueba modal con máscara",
            descripcion="Ventana sólida redondeada por máscara, sin translucencia ni blur.",
            etiqueta_tecnica="Alternativa actual: top-level opaco + setMask() + radio moderado.",
            parent=parent,
        )
        self._radio = 4
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._layout_raiz.setContentsMargins(0, 0, 0, 0)

        panel = QWidget()
        panel.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._construir_panel_contenido(
            panel,
            COLOR_FONDO_DIALOGO,
            self._radio,
            "rgba(126, 167, 196, 0.30)",
        )
        self._layout_raiz.addWidget(panel)

    def paintEvent(self, evento: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(COLOR_FONDO_DIALOGO))
        painter.drawRect(self.rect())
        painter.end()
        super().paintEvent(evento)


class DialogoPruebaModalTranslucido(DialogoPruebaModalBase):
    """Alternativa con translucidez y sombra suave."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            titulo="Prueba modal translúcido",
            descripcion="Ventana sin marco con fondo translúcido y panel interno redondeado con sombra.",
            etiqueta_tecnica="Alternativa de bordes suaves: depende del compositor de Windows.",
            parent=parent,
        )
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        panel = QFrame()
        panel.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        panel.setStyleSheet(
            "QFrame {"
            f"background: {COLOR_FONDO_DIALOGO};"
            "border: 1px solid rgba(126, 167, 196, 0.55);"
            "border-radius: 4px;"
            "}"
        )
        sombra = QGraphicsDropShadowEffect(panel)
        sombra.setBlurRadius(24)
        sombra.setOffset(0, 8)
        sombra.setColor(QColor(18, 18, 42, 110))
        panel.setGraphicsEffect(sombra)
        self._construir_panel_contenido(
            panel,
            COLOR_FONDO_DIALOGO,
            4,
            "rgba(126, 167, 196, 0.55)",
        )
        self._layout_raiz.addWidget(panel)


class VistaModuloPrincipal(QWidget):
    """Shell operativo con sidebar, header y area central navegable."""

    cerrar_sesion_solicitada = Signal()
    abrir_mantenimiento_solicitado = Signal()
    modulo_solicitado = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._gestor_rutas = GestorRutas()
        self.setObjectName("vistaModuloPrincipal")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._tema_actual = TEMA_SIGQUA_PREDETERMINADO
        self._paleta_tema = obtener_paleta_tema(self._tema_actual)
        self._correo_usuario_actual = "soporte@sigqua.local"
        self._modulo_activo = "dashboard"
        self._modulos_sidebar: dict[str, ModuloNavegacion] = {}
        self._botones_modulos: dict[str, QPushButton] = {}
        self._secciones_sidebar: dict[str, SeccionSidebarDesplegable] = {}
        self._estado_secciones_sidebar: dict[str, bool] = {
            "Vista general": True,
            "Registro y control": True,
            "Cobranza": True,
            "Administración": True,
            "Soporte": True,
            "Otros": True,
        }
        self._paginas_modulos: dict[str, QWidget] = {}
        self._tarjetas_metricas: dict[str, TarjetaMetricaEjecutiva] = {}
        self._orden_metricas: list[str] = []
        self._filas_ranking: list[FilaRanking] = []
        self._tarjetas_insight: list[TarjetaInsight] = []
        self._animaciones_activas: list[object] = []
        self._modo_dashboard_actual = "amplio"
        self._ultimo_ancho_dashboard = -1
        self._ultimo_estado_mostrado: EstadoModuloPrincipal | None = None
        self._fondo_personalizado_activo = False
        self._fondo_personalizado_modo = "SOLIDO"
        self._fondo_personalizado_color_primario = ""
        self._fondo_personalizado_color_secundario = ""
        self._dialogo_perfil_usuario: DialogoPerfilUsuario | None = None
        self._panel_perfil_usuario = PanelPerfilUsuario(self)
        self._panel_perfil_usuario.cerrar_sesion_solicitada.connect(
            self.cerrar_sesion_solicitada.emit
        )
        establecer_tema_actual(self._tema_actual)
        self._aplicar_estilos()
        self._construir_ui()

    def sizeHint(self) -> QSize:
        return QSize(1500, 900)

    def minimumSizeHint(self) -> QSize:
        return QSize(ANCHO_MINIMO_SHELL_PRINCIPAL, ALTO_MINIMO_SHELL_PRINCIPAL)

    def resizeEvent(self, evento: QResizeEvent) -> None:
        super().resizeEvent(evento)
        self._actualizar_disposicion_dashboard()

    def eventFilter(self, objeto: object, evento: QEvent) -> bool:
        if (
            hasattr(self, "_scroll_dashboard")
            and objeto is self._scroll_dashboard.viewport()
            and evento.type() == QEvent.Type.Resize
        ):
            self._actualizar_disposicion_dashboard()
        return super().eventFilter(objeto, evento)

    def paintEvent(self, evento: QPaintEvent) -> None:
        """Pinta el fondo principal del shell."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.setPen(Qt.PenStyle.NoPen)
        if self._fondo_personalizado_activo:
            color_primario = self._resolver_color_fondo_personalizado(
                self._fondo_personalizado_color_primario,
                str(self._paleta_tema["fondo_principal"]),
            )
            color_secundario = self._resolver_color_fondo_personalizado(
                self._fondo_personalizado_color_secundario,
                color_primario.name(),
            )
            if self._fondo_personalizado_modo == "DEGRADADO":
                degradado = QLinearGradient(self.rect().topLeft(), self.rect().bottomRight())
                degradado.setColorAt(0.0, color_primario)
                degradado.setColorAt(1.0, color_secundario)
                painter.setBrush(QBrush(degradado))
            else:
                painter.setBrush(color_primario)
        else:
            painter.setBrush(QColor(str(self._paleta_tema["fondo_principal"])))
        painter.drawRect(self.rect())
        painter.end()

        super().paintEvent(evento)

    def aplicar_fondo_personalizado(
        self,
        activo: bool,
        modo: str,
        color_primario: str,
        color_secundario: str,
    ) -> None:
        self._fondo_personalizado_activo = bool(activo)
        self._fondo_personalizado_modo = (
            modo.strip().upper() if modo.strip().upper() in {"SOLIDO", "DEGRADADO"} else "SOLIDO"
        )
        self._fondo_personalizado_color_primario = color_primario.strip().upper()
        self._fondo_personalizado_color_secundario = color_secundario.strip().upper()
        if self._fondo_personalizado_modo == "SOLIDO":
            self._fondo_personalizado_color_secundario = self._fondo_personalizado_color_primario
        self.update()

    def registrar_modulo(self, codigo: str, widget: QWidget) -> None:
        if codigo in self._paginas_modulos:
            return
        self._paginas_modulos[codigo] = widget
        if hasattr(widget, "aplicar_tema"):
            widget.aplicar_tema(self._tema_actual)
        self._stack_contenido.addWidget(widget)

    def preparar_perfil_usuario(self, correo: str) -> None:
        self._correo_usuario_actual = correo.strip() or "soporte@sigqua.local"

    def mostrar_estado(self, estado: EstadoModuloPrincipal) -> None:
        self._ultimo_estado_mostrado = estado
        self._modulos_sidebar = {modulo.codigo: modulo for modulo in estado.modulos}
        self._boton_perfil_header.actualizar(estado.nombre_completo, estado.perfil)
        self._panel_perfil_usuario.actualizar(
            nombre_completo=estado.nombre_completo,
            rol=estado.perfil,
            correo=self._correo_usuario_actual,
            ultimo_acceso=datetime.now().strftime("%d/%m/%Y %I:%M %p"),
            estado_sesion="Activa en este equipo",
        )
        if self._dialogo_perfil_usuario is not None:
            self._dialogo_perfil_usuario.actualizar(
                nombre_completo=estado.nombre_completo,
                rol=estado.perfil,
                correo=self._correo_usuario_actual,
                ultimo_acceso=datetime.now().strftime("%d/%m/%Y %I:%M %p"),
                estado_sesion="Activa en este equipo",
            )
        self._reconstruir_sidebar(estado.modulos)
        self.actualizar_dashboard(estado)
        self._boton_mantenimiento.setVisible(estado.puede_abrir_mantenimiento)
        self._panel_acciones_sidebar.setVisible(estado.puede_abrir_mantenimiento)
        self.mostrar_modulo("dashboard")
        self._actualizar_disposicion_dashboard()
        self._animar_aparicion_dashboard()

    def actualizar_dashboard(self, estado: EstadoModuloPrincipal) -> None:
        self._ultimo_estado_mostrado = estado
        self._mostrar_metricas(estado)
        self._mostrar_analitica(estado.analitica)
        self._actualizar_texto_ultima_actualizacion()
        self.establecer_dashboard_pendiente_actualizacion(False)
        self._actualizar_disposicion_dashboard()

    def establecer_dashboard_pendiente_actualizacion(self, pendiente: bool) -> None:
        boton_inicio = self._botones_modulos.get("dashboard")
        if boton_inicio is not None:
            boton_inicio.setProperty("dashboardPendienteActualizacion", pendiente)
            boton_inicio.style().unpolish(boton_inicio)
            boton_inicio.style().polish(boton_inicio)
        if hasattr(self, "_label_estado_dashboard"):
            self._label_estado_dashboard.setText("Cambios pendientes" if pendiente else "")
            self._label_estado_dashboard.setProperty("estado", "pendiente" if pendiente else "normal")
            self._label_estado_dashboard.style().unpolish(self._label_estado_dashboard)
            self._label_estado_dashboard.style().polish(self._label_estado_dashboard)

    def mostrar_resultado_actualizacion_dashboard(self, mensaje: str, *, error: bool = False) -> None:
        if not hasattr(self, "_label_estado_dashboard"):
            return
        self._label_estado_dashboard.setText(mensaje)
        self._label_estado_dashboard.setProperty("estado", "error" if error else "normal")
        self._label_estado_dashboard.style().unpolish(self._label_estado_dashboard)
        self._label_estado_dashboard.style().polish(self._label_estado_dashboard)

    def _actualizar_texto_ultima_actualizacion(self) -> None:
        if hasattr(self, "_label_actualizacion_dashboard"):
            self._label_actualizacion_dashboard.setText(
                f"Ultima actualizacion: {datetime.now().strftime('%d/%m/%Y %I:%M %p')}"
            )

    @staticmethod
    def _resolver_saludo(momento: datetime | None = None) -> str:
        referencia = momento or datetime.now()
        hora = referencia.hour
        if 5 <= hora <= 11:
            return "Buenos dias"
        if 12 <= hora <= 17:
            return "Buenas tardes"
        return "Buenas noches"

    def aplicar_tema(self, nombre_tema: str) -> None:
        self._tema_actual = (
            resolver_nombre_tema(nombre_tema)
        )
        self._paleta_tema = obtener_paleta_tema(self._tema_actual)
        establecer_tema_actual(self._tema_actual)
        self._aplicar_estilos()
        self._aplicar_tema_a_descendientes()
        if self._ultimo_estado_mostrado is not None:
            self._mostrar_metricas(self._ultimo_estado_mostrado)
            self._mostrar_analitica(self._ultimo_estado_mostrado.analitica)
        self.update()

    @staticmethod
    def _resolver_color_fondo_personalizado(color: str, predeterminado: str) -> QColor:
        color_resuelto = QColor((color or "").strip())
        if color_resuelto.isValid():
            return color_resuelto
        return QColor(predeterminado)

    def _aplicar_tema_a_descendientes(self) -> None:
        for tarjeta in self._tarjetas_metricas.values():
            tarjeta.aplicar_tema(self._tema_actual)
        for tarjeta in self._tarjetas_insight:
            tarjeta.aplicar_tema(self._tema_actual)
        if hasattr(self, "_grafica_estados"):
            self._grafica_estados.aplicar_tema(self._tema_actual)
        if hasattr(self, "_grafica_barrios"):
            self._grafica_barrios.aplicar_tema(self._tema_actual)
        if hasattr(self, "_leyenda_distribucion"):
            self._leyenda_distribucion.aplicar_tema(self._tema_actual)
        self._panel_perfil_usuario.aplicar_tema(self._tema_actual)
        if self._dialogo_perfil_usuario is not None:
            self._dialogo_perfil_usuario.aplicar_tema(self._tema_actual)
        for boton in self.findChildren(BotonAccionContextual):
            boton.aplicar_tema(self._tema_actual)
        for boton in self.findChildren(QPushButton):
            if boton.objectName() == "botonOperativo":
                aplicar_estilo_boton_operativo(boton, principal=False)
            elif boton.objectName() == "botonOperativoPrimario":
                aplicar_estilo_boton_operativo(boton, principal=True)
            elif isinstance(boton, BotonSidebar):
                nombre_icono = boton.property("iconoSidebar")
                if isinstance(nombre_icono, str):
                    activo = boton.property("activo") is True
                    color_icono = (
                        str(self._paleta_tema["icono_menu_activo"])
                        if activo
                        else str(self._paleta_tema["icono_menu_normal"])
                    )
                    color_texto = (
                        str(self._paleta_tema["texto_menu_activo"])
                        if activo
                        else str(self._paleta_tema["texto_menu_normal"])
                    )
                    boton.aplicar_estado_visual(
                        activo=activo,
                        color_texto=color_texto,
                        nombre_icono=nombre_icono,
                        color_icono=color_icono,
                    )
        for pagina in self._paginas_modulos.values():
            if hasattr(pagina, "aplicar_tema"):
                pagina.aplicar_tema(self._tema_actual)

    def mostrar_modulo(self, codigo: str) -> None:
        pagina = self._paginas_modulos.get(codigo)
        if pagina is None:
            return
        self._modulo_activo = codigo
        self._actualizar_encabezado_modulo(codigo)
        self._stack_contenido.setCurrentWidget(pagina)
        for codigo_boton, boton in self._botones_modulos.items():
            nombre_icono = boton.property("iconoSidebar")
            if isinstance(nombre_icono, str):
                activo = codigo_boton == codigo
                color_icono = (
                    str(self._paleta_tema["icono_menu_activo"])
                    if activo
                    else str(self._paleta_tema["icono_menu_normal"])
                )
                color_texto = (
                    str(self._paleta_tema["texto_menu_activo"])
                    if activo
                    else str(self._paleta_tema["texto_menu_normal"])
                )
                boton.aplicar_estado_visual(
                    activo=activo,
                    color_texto=color_texto,
                    nombre_icono=nombre_icono,
                    color_icono=color_icono,
                )
        for titulo, seccion in self._secciones_sidebar.items():
            seccion.marcar_modulo_activo(codigo)

    def _construir_ui(self) -> None:
        layout_raiz = QHBoxLayout(self)
        layout_raiz.setContentsMargins(0, 0, 0, 0)
        layout_raiz.setSpacing(0)

        self._contenedor_sidebar = QWidget()
        self._contenedor_sidebar.setObjectName("contenedorSidebarFlotante")
        self._contenedor_sidebar.setFixedWidth(ANCHO_SIDEBAR + 24)
        layout_contenedor_sidebar = QVBoxLayout(self._contenedor_sidebar)
        layout_contenedor_sidebar.setContentsMargins(14, 14, 10, 14)
        layout_contenedor_sidebar.setSpacing(0)

        self._sidebar = QFrame()
        self._sidebar.setObjectName("sidebarPrincipal")
        self._sidebar.setFixedWidth(ANCHO_SIDEBAR)
        self._sidebar.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        sombra_sidebar = QGraphicsDropShadowEffect(self._sidebar)
        sombra_sidebar.setBlurRadius(22)
        sombra_sidebar.setOffset(0, 8)
        sombra_sidebar.setColor(QColor(0, 0, 0, 76))
        self._sidebar.setGraphicsEffect(sombra_sidebar)
        layout_sidebar = QVBoxLayout(self._sidebar)
        self._layout_sidebar = layout_sidebar
        layout_sidebar.setContentsMargins(8, 14, 8, 12)
        layout_sidebar.setSpacing(10)

        layout_sidebar.addWidget(self._crear_encabezado_sidebar())

        self._scroll_navegacion = QScrollArea()
        self._scroll_navegacion.setObjectName("scrollNavegacionSidebar")
        self._scroll_navegacion.setWidgetResizable(True)
        self._scroll_navegacion.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll_navegacion.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll_navegacion.setFrameShape(QFrame.Shape.NoFrame)

        contenedor_navegacion = QWidget()
        contenedor_navegacion.setObjectName("contenedorNavegacionSidebar")
        self._contenedor_botones = QVBoxLayout(contenedor_navegacion)
        self._contenedor_botones.setContentsMargins(0, 0, 0, 0)
        self._contenedor_botones.setSpacing(12)
        self._scroll_navegacion.setWidget(contenedor_navegacion)
        layout_sidebar.addWidget(self._scroll_navegacion, 1)

        self._panel_acciones_sidebar = QFrame()
        self._panel_acciones_sidebar.setObjectName("panelAccionesSidebar")
        layout_acciones_sidebar = QVBoxLayout(self._panel_acciones_sidebar)
        layout_acciones_sidebar.setContentsMargins(0, 8, 0, 0)
        layout_acciones_sidebar.setSpacing(6)

        self._boton_mantenimiento = self._crear_boton_sidebar(
            ModuloNavegacion("mantenimiento", "Mantenimiento", "", "tool.svg"),
            tipo="accion",
        )
        self._boton_mantenimiento.clicked.connect(self.abrir_mantenimiento_solicitado.emit)
        self._boton_mantenimiento.setVisible(False)
        layout_acciones_sidebar.addWidget(self._boton_mantenimiento)
        layout_sidebar.addWidget(self._panel_acciones_sidebar)

        panel = QWidget()
        panel.setObjectName("panelPrincipal")
        layout_panel = QVBoxLayout(panel)
        layout_panel.setContentsMargins(24, 18, 24, 18)
        layout_panel.setSpacing(10)

        header = QFrame()
        header.setObjectName("headerPrincipal")
        sombra_header = QGraphicsDropShadowEffect(header)
        sombra_header.setBlurRadius(18)
        sombra_header.setOffset(0, 6)
        sombra_header.setColor(QColor(0, 0, 0, 58))
        header.setGraphicsEffect(sombra_header)
        layout_header = QHBoxLayout(header)
        layout_header.setContentsMargins(18, 14, 10, 14)
        layout_header.setSpacing(14)

        bloque_titulo = QVBoxLayout()
        bloque_titulo.setSpacing(4)
        self._label_bienvenida = QLabel("Buenas noches")
        self._label_bienvenida.setObjectName("tituloPrincipal")
        self._label_subresumen = QLabel("")
        self._label_subresumen.setObjectName("descripcionPrincipal")
        self._label_subresumen.setWordWrap(True)
        bloque_titulo.addWidget(self._label_bienvenida)
        bloque_titulo.addWidget(self._label_subresumen)

        layout_header.addLayout(bloque_titulo, 1)
        self._boton_perfil_header = BotonPerfilUsuario()
        self._boton_perfil_header.clicked.connect(self._abrir_panel_perfil_usuario)
        layout_header.addWidget(
            self._boton_perfil_header,
            0,
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight,
        )
        self._stack_contenido = QStackedWidget()
        self._stack_contenido.setObjectName("stackPrincipal")

        self._pagina_dashboard = self._crear_dashboard()
        self.registrar_modulo("dashboard", self._pagina_dashboard)

        layout_panel.addWidget(header)
        layout_panel.addWidget(self._stack_contenido, 1)

        layout_contenedor_sidebar.addWidget(self._sidebar)
        layout_raiz.addWidget(self._contenedor_sidebar)
        layout_raiz.addWidget(panel, 1)

    def _actualizar_encabezado_modulo(self, codigo: str) -> None:
        if self._ultimo_estado_mostrado is None:
            return
        if codigo == "dashboard":
            primer_nombre = (
                self._ultimo_estado_mostrado.nombre_completo.split()[0]
                if self._ultimo_estado_mostrado.nombre_completo
                else self._ultimo_estado_mostrado.nombre_usuario
            )
            perfil_legible = self._ultimo_estado_mostrado.perfil.replace("_", " ").title()
            self._label_bienvenida.setText(f"{self._resolver_saludo()}, {primer_nombre}")
            self._label_subresumen.setText(
                (
                    f"{perfil_legible} en sesion. Monitorea ingresos, pagos pendientes "
                    "y estabilidad operativa desde un solo tablero."
                )
            )
            return

        modulo = self._modulos_sidebar.get(codigo)
        if modulo is None:
            self._label_bienvenida.setText("Modulo")
            self._label_subresumen.setText("Vista operativa del sistema.")
            return

        self._label_bienvenida.setText(modulo.titulo)
        self._label_subresumen.setText(modulo.descripcion or "Vista operativa del sistema.")

    def _crear_dashboard(self) -> QWidget:
        pagina = QWidget()
        pagina.setObjectName("paginaDashboard")
        layout_pagina = QVBoxLayout(pagina)
        layout_pagina.setContentsMargins(0, 0, 0, 0)
        layout_pagina.setSpacing(0)

        self._scroll_dashboard = QScrollArea()
        self._scroll_dashboard.setObjectName("scrollDashboard")
        self._scroll_dashboard.setWidgetResizable(True)
        self._scroll_dashboard.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll_dashboard.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll_dashboard.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll_dashboard.viewport().setAutoFillBackground(False)
        self._scroll_dashboard.viewport().installEventFilter(self)

        self._contenido_dashboard = QWidget()
        self._contenido_dashboard.setObjectName("contenidoDashboard")
        self._contenido_dashboard.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        self._contenido_dashboard.setAutoFillBackground(False)
        layout = QVBoxLayout(self._contenido_dashboard)
        layout.setContentsMargins(0, 2, 0, 4)
        layout.setSpacing(10)

        self._grid_metricas = QGridLayout()
        self._grid_metricas.setHorizontalSpacing(10)
        self._grid_metricas.setVerticalSpacing(10)
        layout.addLayout(self._grid_metricas)

        self._layout_paneles_dashboard = QGridLayout()
        self._layout_paneles_dashboard.setHorizontalSpacing(10)
        self._layout_paneles_dashboard.setVerticalSpacing(10)
        layout.addLayout(self._layout_paneles_dashboard)

        self._panel_tendencia = QFrame()
        self._panel_tendencia.setObjectName("tarjetaPanel")
        self._panel_tendencia.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout_tendencia = QVBoxLayout(self._panel_tendencia)
        layout_tendencia.setContentsMargins(14, 12, 14, 12)
        layout_tendencia.setSpacing(6)

        self._titulo_tendencia = QLabel("Recaudacion")
        self._titulo_tendencia.setObjectName("tituloPanel")
        self._agregar_cabecera_panel_dashboard(
            layout_tendencia,
            self._titulo_tendencia,
            "Comparativo mensual de ingresos reales frente al ritmo promedio.",
            "Mensual",
        )

        self._grafica_tendencia = self._crear_chart_view()
        self._grafica_tendencia.setMinimumHeight(176)
        layout_tendencia.addWidget(self._grafica_tendencia, 1)

        self._panel_ranking = QFrame()
        self._panel_ranking.setObjectName("tarjetaPanel")
        self._panel_ranking.setMinimumWidth(224)
        self._panel_ranking.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        layout_ranking = QVBoxLayout(self._panel_ranking)
        layout_ranking.setContentsMargins(14, 12, 14, 12)
        layout_ranking.setSpacing(6)
        titulo_ranking = QLabel("Deuda por barrio")
        titulo_ranking.setObjectName("tituloPanel")
        self._agregar_cabecera_panel_dashboard(
            layout_ranking,
            titulo_ranking,
            "Zonas con mayor concentracion de saldo pendiente.",
            "Top zonas",
        )
        self._grafica_barrios = GraficoBarrasHorizontalesDashboard(self._tema_actual)
        self._grafica_barrios.setMinimumHeight(166)
        layout_ranking.addWidget(self._grafica_barrios, 1)

        self._panel_estados = QFrame()
        self._panel_estados.setObjectName("tarjetaPanel")
        self._panel_estados.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout_estados = QVBoxLayout(self._panel_estados)
        layout_estados.setContentsMargins(14, 12, 14, 12)
        layout_estados.setSpacing(6)
        titulo_estados = QLabel("Estado del servicio")
        titulo_estados.setObjectName("tituloPanel")
        self._agregar_cabecera_panel_dashboard(
            layout_estados,
            titulo_estados,
            "Distribucion de casas segun su condicion operativa actual.",
            "Servicios",
        )
        self._grafica_estados = GraficoBarrasEstadoServicio(self._tema_actual)
        self._grafica_estados.setMinimumHeight(166)
        layout_estados.addWidget(self._grafica_estados, 1)

        self._panel_insights = QFrame()
        self._panel_insights.setObjectName("tarjetaPanel")
        self._panel_insights.setMinimumWidth(248)
        self._panel_insights.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        layout_insights = QVBoxLayout(self._panel_insights)
        layout_insights.setContentsMargins(14, 12, 14, 12)
        layout_insights.setSpacing(6)
        titulo_insights = QLabel("Lecturas clave")
        titulo_insights.setObjectName("tituloPanel")
        self._agregar_cabecera_panel_dashboard(
            layout_insights,
            titulo_insights,
            "Señales ejecutivas para decidir rapido y con contexto.",
            "Ejecutivo",
        )
        self._layout_insights = QGridLayout()
        self._layout_insights.setHorizontalSpacing(10)
        self._layout_insights.setVerticalSpacing(10)
        layout_insights.addLayout(self._layout_insights, 1)

        self._panel_distribucion = QFrame()
        self._panel_distribucion.setObjectName("tarjetaPanel")
        self._panel_distribucion.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout_distribucion = QVBoxLayout(self._panel_distribucion)
        layout_distribucion.setContentsMargins(14, 12, 14, 12)
        layout_distribucion.setSpacing(6)
        titulo_distribucion = QLabel("Antiguedad de deuda")
        titulo_distribucion.setObjectName("tituloPanel")
        self._agregar_cabecera_panel_dashboard(
            layout_distribucion,
            titulo_distribucion,
            "Saldo vencido agrupado por rango de atraso para priorizar cobro.",
            "Mora",
        )
        self._grafica_distribucion = self._crear_chart_view()
        self._grafica_distribucion.setMinimumHeight(166)
        self._leyenda_distribucion = LeyendaDonutDeuda(self._tema_actual)
        contenedor_distribucion = QWidget()
        contenedor_distribucion.setObjectName("contenedorDistribucionDeuda")
        layout_contenedor_distribucion = QHBoxLayout(contenedor_distribucion)
        layout_contenedor_distribucion.setContentsMargins(0, 0, 0, 0)
        layout_contenedor_distribucion.setSpacing(14)
        layout_contenedor_distribucion.addWidget(self._grafica_distribucion, 1)
        layout_contenedor_distribucion.addWidget(
            self._leyenda_distribucion,
            0,
            alignment=Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
        )
        layout_distribucion.addWidget(contenedor_distribucion, 1)

        self._footer_dashboard = QFrame()
        self._footer_dashboard.setObjectName("footerDashboard")
        layout_footer = QHBoxLayout(self._footer_dashboard)
        layout_footer.setContentsMargins(12, 6, 12, 6)
        layout_footer.setSpacing(8)
        self._label_actualizacion_dashboard = QLabel(
            f"Ultima actualizacion: {datetime.now().strftime('%d/%m/%Y %I:%M %p')}"
        )
        self._label_actualizacion_dashboard.setObjectName("textoFooterDashboard")
        self._label_estado_dashboard = QLabel("")
        self._label_estado_dashboard.setObjectName("textoEstadoDashboard")
        self._label_estado_dashboard.setProperty("estado", "normal")
        layout_footer.addWidget(self._label_actualizacion_dashboard)
        layout_footer.addWidget(self._label_estado_dashboard)
        layout_footer.addStretch(1)
        layout.addWidget(self._footer_dashboard)

        self._scroll_dashboard.setWidget(self._contenido_dashboard)
        layout_pagina.addWidget(self._scroll_dashboard)
        self._actualizar_disposicion_dashboard()
        return pagina

    def _agregar_cabecera_panel_dashboard(
        self,
        layout_destino: QVBoxLayout,
        titulo: QLabel,
        descripcion: str,
        etiqueta: str,
    ) -> None:
        fila = QHBoxLayout()
        fila.setContentsMargins(0, 0, 0, 0)
        fila.setSpacing(10)
        badge = QLabel(etiqueta)
        badge.setObjectName("badgePanelDashboard")
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        descripcion_label = QLabel(descripcion)
        descripcion_label.setObjectName("descripcionPanel")
        descripcion_label.setWordWrap(True)
        fila.addWidget(titulo)
        fila.addStretch(1)
        fila.addWidget(badge)
        layout_destino.addLayout(fila)
        layout_destino.addWidget(descripcion_label)

    @staticmethod
    def _resolver_visual_metrica(codigo: str) -> tuple[str, str, str, str]:
        mapa = {
            "ingresos_hoy": ("receipt-2.svg", "#38BDF8", "#153B5A", "Hoy"),
            "ingresos_mes": ("chart-bar.svg", "#2F9BFF", "#163862", "Mensual"),
            "deuda": ("urgent.svg", "#FBBF24", "#4D3B18", "Cobranza"),
            "casas_mora": ("alert-triangle.svg", "#F87171", "#563039", "Alerta"),
            "abonados_activos": ("users.svg", "#35E6A8", "#173F36", "Registro"),
            "casas_activas": ("home-2.svg", "#2DD4BF", "#173F3E", "Servicio"),
        }
        return mapa.get(codigo, ("chart-bar.svg", "#C5DDEE", "#DFF4FF", "Resumen"))

    def _mostrar_metricas(self, estado: EstadoModuloPrincipal) -> None:
        while self._grid_metricas.count():
            item = self._grid_metricas.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        self._tarjetas_metricas.clear()
        self._orden_metricas.clear()

        for metrica in estado.metricas:
            icono, color_acento, color_fondo, etiqueta = self._resolver_visual_metrica(
                metrica.codigo
            )
            tarjeta = TarjetaMetricaEjecutiva(
                icono=icono,
                color_acento=color_acento,
                color_fondo=color_fondo,
                etiqueta_contexto=etiqueta,
                nombre_tema=self._tema_actual,
            )
            tarjeta.actualizar(metrica.titulo, metrica.valor, metrica.detalle)
            self._tarjetas_metricas[metrica.codigo] = tarjeta
            self._orden_metricas.append(metrica.codigo)
        self._actualizar_disposicion_metricas()

    def _mostrar_analitica(self, analitica: AnaliticaDashboard) -> None:
        self._construir_insights(analitica.insights)
        self._grafica_tendencia.setChart(self._crear_chart_tendencia(analitica.recaudacion_mensual))
        self._grafica_estados.actualizar(analitica.estados_servicio)
        self._grafica_barrios.actualizar(analitica.deuda_por_barrio)
        self._leyenda_distribucion.actualizar(analitica.antiguedad_deuda)
        self._grafica_distribucion.setChart(
            self._crear_chart_distribucion_deuda(analitica.antiguedad_deuda)
        )

    def _ancho_disponible_dashboard(self) -> int:
        if hasattr(self, "_scroll_dashboard") and self._scroll_dashboard is not None:
            return max(0, self._scroll_dashboard.viewport().width())
        return max(0, self.width())

    def _actualizar_disposicion_dashboard(self) -> None:
        if not hasattr(self, "_layout_paneles_dashboard"):
            return
        ancho_actual = self._ancho_disponible_dashboard()
        if ancho_actual <= 0 or ancho_actual == self._ultimo_ancho_dashboard:
            return
        self._ultimo_ancho_dashboard = ancho_actual
        self._actualizar_disposicion_metricas()
        self._actualizar_disposicion_paneles_dashboard()

    def _actualizar_disposicion_metricas(self) -> None:
        if not hasattr(self, "_grid_metricas") or not self._orden_metricas:
            return

        while self._grid_metricas.count():
            self._grid_metricas.takeAt(0)
        for columna in range(6):
            self._grid_metricas.setColumnStretch(columna, 0)
            self._grid_metricas.setColumnMinimumWidth(columna, 0)

        ancho = self._ancho_disponible_dashboard()
        if ancho >= ANCHO_RUPTURA_METRICAS_6_COLUMNAS:
            columnas_metricas = min(6, max(1, len(self._orden_metricas)))
        elif ancho >= ANCHO_RUPTURA_METRICAS_4_COLUMNAS:
            columnas_metricas = 4
        elif ancho >= ANCHO_RUPTURA_METRICAS_3_COLUMNAS:
            columnas_metricas = 3
        elif ancho >= ANCHO_RUPTURA_METRICAS_2_COLUMNAS:
            columnas_metricas = 2
        else:
            columnas_metricas = 1

        for indice, codigo_metrica in enumerate(self._orden_metricas):
            tarjeta = self._tarjetas_metricas.get(codigo_metrica)
            if tarjeta is None:
                continue
            fila, columna = divmod(indice, columnas_metricas)
            self._grid_metricas.addWidget(tarjeta, fila, columna)

        for columna in range(columnas_metricas):
            self._grid_metricas.setColumnStretch(columna, 1)

    def _actualizar_disposicion_paneles_dashboard(self) -> None:
        while self._layout_paneles_dashboard.count():
            self._layout_paneles_dashboard.takeAt(0)
        for columna in range(4):
            self._layout_paneles_dashboard.setColumnStretch(columna, 0)
            self._layout_paneles_dashboard.setColumnMinimumWidth(columna, 0)

        ancho = self._ancho_disponible_dashboard()
        limite_expandido = 16777215

        if ancho >= ANCHO_RUPTURA_DASHBOARD_AMPLIO:
            self._modo_dashboard_actual = "amplio"
            self._aplicar_alturas_paneles_dashboard(
                tendencia=285,
                ranking=255,
                estados=245,
                distribucion=245,
                insights=270,
            )
            self._panel_ranking.setMaximumWidth(limite_expandido)
            self._panel_insights.setMaximumWidth(limite_expandido)
            self._layout_paneles_dashboard.addWidget(self._panel_tendencia, 0, 0, 1, 4)
            self._layout_paneles_dashboard.addWidget(self._panel_estados, 1, 0, 1, 2)
            self._layout_paneles_dashboard.addWidget(self._panel_distribucion, 1, 2, 1, 2)
            self._layout_paneles_dashboard.addWidget(self._panel_ranking, 2, 0, 1, 2)
            self._layout_paneles_dashboard.addWidget(self._panel_insights, 2, 2, 1, 2)
            self._layout_paneles_dashboard.setColumnStretch(0, 2)
            self._layout_paneles_dashboard.setColumnStretch(1, 2)
            self._layout_paneles_dashboard.setColumnStretch(2, 2)
            self._layout_paneles_dashboard.setColumnStretch(3, 2)
            return

        self._panel_ranking.setMaximumWidth(limite_expandido)
        self._panel_insights.setMaximumWidth(limite_expandido)

        if ancho >= ANCHO_RUPTURA_DASHBOARD_MEDIO:
            self._modo_dashboard_actual = "medio"
            self._aplicar_alturas_paneles_dashboard(
                tendencia=280,
                ranking=255,
                estados=245,
                distribucion=245,
                insights=270,
            )
            self._layout_paneles_dashboard.addWidget(self._panel_tendencia, 0, 0, 1, 2)
            self._layout_paneles_dashboard.addWidget(self._panel_estados, 1, 0)
            self._layout_paneles_dashboard.addWidget(self._panel_distribucion, 1, 1)
            self._layout_paneles_dashboard.addWidget(self._panel_ranking, 2, 0)
            self._layout_paneles_dashboard.addWidget(self._panel_insights, 2, 1)
            self._layout_paneles_dashboard.setColumnStretch(0, 1)
            self._layout_paneles_dashboard.setColumnStretch(1, 1)
            return

        self._modo_dashboard_actual = "compacto"
        self._aplicar_alturas_paneles_dashboard(
            tendencia=270,
            ranking=255,
            estados=240,
            distribucion=240,
            insights=300,
        )
        self._layout_paneles_dashboard.addWidget(self._panel_tendencia, 0, 0)
        self._layout_paneles_dashboard.addWidget(self._panel_estados, 1, 0)
        self._layout_paneles_dashboard.addWidget(self._panel_distribucion, 2, 0)
        self._layout_paneles_dashboard.addWidget(self._panel_ranking, 3, 0)
        self._layout_paneles_dashboard.addWidget(self._panel_insights, 4, 0)
        self._layout_paneles_dashboard.setColumnStretch(0, 1)

    def _aplicar_alturas_paneles_dashboard(
        self,
        *,
        tendencia: int,
        ranking: int,
        estados: int,
        distribucion: int,
        insights: int,
    ) -> None:
        self._establecer_altura_panel(self._panel_tendencia, tendencia)
        self._establecer_altura_panel(self._panel_ranking, ranking)
        self._establecer_altura_panel(self._panel_estados, estados)
        self._establecer_altura_panel(self._panel_distribucion, distribucion)
        self._establecer_altura_panel(self._panel_insights, insights)

    @staticmethod
    def _establecer_altura_panel(panel: QWidget, altura: int) -> None:
        panel.setMinimumHeight(altura)
        panel.setMaximumHeight(altura)

    def _reconstruir_sidebar(self, modulos: tuple[ModuloNavegacion, ...]) -> None:
        while self._contenedor_botones.count():
            item = self._contenedor_botones.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        self._botones_modulos.clear()
        self._secciones_sidebar.clear()
        secciones: dict[str, list[ModuloNavegacion]] = {
            "Vista general": [],
            "Registro y control": [],
            "Cobranza": [],
            "Administración": [],
            "Soporte": [],
            "Otros": [],
        }

        for modulo in modulos:
            if modulo.codigo == "mantenimiento":
                continue
            secciones[self._resolver_categoria_sidebar(modulo.codigo)].append(modulo)

        for titulo_seccion, modulos_seccion in secciones.items():
            if not modulos_seccion:
                continue
            widget_seccion = SeccionSidebarDesplegable(titulo_seccion)
            self._secciones_sidebar[titulo_seccion] = widget_seccion

            for modulo in modulos_seccion:
                boton = self._crear_boton_sidebar(modulo, tipo="modulo")
                boton.clicked.connect(
                    lambda checked=False, codigo=modulo.codigo: self._solicitar_modulo(codigo)
                )
                widget_seccion.agregar_boton(modulo.codigo, boton)
                self._botones_modulos[modulo.codigo] = boton

            widget_seccion.establecer_expandida(True, forzar=True)
            widget_seccion.marcar_modulo_activo(self._modulo_activo)
            self._contenedor_botones.addWidget(widget_seccion)

        self._contenedor_botones.addStretch(1)

    def _solicitar_modulo(self, codigo: str) -> None:
        self.modulo_solicitado.emit(codigo)
        self.mostrar_modulo(codigo)

    def _abrir_dialogo_perfil_usuario(self) -> None:
        if self._dialogo_perfil_usuario is None:
            self._dialogo_perfil_usuario = DialogoPerfilUsuario(self)
            self._dialogo_perfil_usuario.aplicar_tema(self._tema_actual)
            if self._ultimo_estado_mostrado is not None:
                self._dialogo_perfil_usuario.actualizar(
                    nombre_completo=self._ultimo_estado_mostrado.nombre_completo,
                    rol=self._ultimo_estado_mostrado.perfil,
                    correo=self._correo_usuario_actual,
                    ultimo_acceso=datetime.now().strftime("%d/%m/%Y %I:%M %p"),
                    estado_sesion="Activa en este equipo",
                )
        self._dialogo_perfil_usuario.exec()

    def _abrir_panel_perfil_usuario(self) -> None:
        if not self._panel_perfil_usuario.mostrar_desde(self._boton_perfil_header):
            self._abrir_dialogo_perfil_usuario()

    def _crear_boton_sidebar(self, modulo: ModuloNavegacion, tipo: str = "modulo") -> BotonSidebar:
        boton = BotonSidebar(modulo.titulo)
        fuente = QFont(boton.font())
        fuente.setPixelSize(11)
        fuente.setWeight(QFont.Weight.ExtraBold)
        boton.setFont(fuente)
        boton._texto.setFont(fuente)
        boton.setProperty("tipoSidebar", tipo)
        boton.setProperty("iconoSidebar", modulo.icono)
        boton.setProperty("textoSidebar", modulo.titulo)
        boton.setProperty("dashboardPendienteActualizacion", False)
        boton.setIcon(
            obtener_icono_tabler_coloreado(
                modulo.icono,
                str(self._paleta_tema["icono_menu_normal"]),
                tamano=16,
            )
        )
        boton.setIconSize(QSize(16, 16))
        boton.setToolTip(modulo.descripcion or modulo.titulo)
        return boton

    def _crear_encabezado_sidebar(self) -> QWidget:
        encabezado = QWidget()
        encabezado.setObjectName("encabezadoSidebar")
        encabezado.setFixedHeight(54)
        layout = QVBoxLayout(encabezado)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(0)

        self._logo_sidebar = QLabel()
        self._logo_sidebar.setObjectName("logoSidebar")
        self._logo_sidebar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ruta_logo = GestorRutas().obtener_ruta_logo_marca()
        pixmap_logo = obtener_pixmap_marca(
            ruta_marca=ruta_logo,
            ancho_logico=128,
            factor_escala=self.devicePixelRatioF(),
        )
        self._logo_sidebar.setPixmap(pixmap_logo)
        layout.addWidget(self._logo_sidebar)
        return encabezado

    @staticmethod
    def _resolver_categoria_sidebar(codigo_modulo: str) -> str:
        if codigo_modulo == "dashboard":
            return "Vista general"
        if codigo_modulo in {"barrios", "abonados", "casas", "atencion_abonado", "conexion_reconexion"}:
            return "Registro y control"
        if codigo_modulo in {"pagos", "historial_pagos", "morosidad", "planes_pago"}:
            return "Cobranza"
        if codigo_modulo in {"usuarios", "configuracion", "reportes"}:
            return "Administración"
        if codigo_modulo in {"ayuda_soporte"}:
            return "Soporte"
        return "Otros"

    def _construir_insights(self, insights: tuple[InsightDashboard, ...]) -> None:
        while self._layout_insights.count():
            item = self._layout_insights.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        self._tarjetas_insight.clear()

        insights_visibles = self._seleccionar_insights_dashboard(insights)
        for insight in insights_visibles:
            indice = len(self._tarjetas_insight)
            tarjeta = TarjetaInsight(self._tema_actual)
            tarjeta.actualizar(insight)
            tarjeta.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self._tarjetas_insight.append(tarjeta)
            fila, columna = divmod(indice, 2)
            self._layout_insights.addWidget(tarjeta, fila, columna)
        self._layout_insights.setColumnStretch(0, 1)
        self._layout_insights.setColumnStretch(1, 1)
        for fila in range(2):
            self._layout_insights.setRowStretch(fila, 1)

    @staticmethod
    def _seleccionar_insights_dashboard(
        insights: tuple[InsightDashboard, ...],
    ) -> tuple[InsightDashboard, ...]:
        orden = (
            "servicios comprometidos",
            "cargos pendientes",
            "planes de pago activos",
            "ultimo pago registrado",
        )
        por_titulo = {insight.titulo.strip().lower(): insight for insight in insights}
        seleccionados = [
            por_titulo[titulo]
            for titulo in orden
            if titulo in por_titulo
        ]
        if len(seleccionados) < 4:
            for insight in insights:
                titulo = insight.titulo.strip().lower()
                if titulo == "pagos registrados hoy" or insight in seleccionados:
                    continue
                seleccionados.append(insight)
                if len(seleccionados) == 4:
                    break
        return tuple(seleccionados[:4])

    def _crear_fuente_chart(self, tamano: int, peso: int = 500) -> QFont:
        fuente = QFont(str(self._paleta_tema["familia_tipografica"]), tamano)
        fuente.setWeight(QFont.Weight(peso))
        return fuente

    def _aplicar_estilo_chart(
        self,
        chart: QChart,
        *,
        mostrar_leyenda: bool,
        alineacion_leyenda: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignBottom,
    ) -> None:
        paleta = self._paleta_tema
        chart.setTheme(QChart.ChartTheme.ChartThemeLight)
        chart.setBackgroundVisible(False)
        chart.setBackgroundBrush(QBrush(QColor(0, 0, 0, 0)))
        chart.setBackgroundPen(QPen(QColor(0, 0, 0, 0), 0))
        chart.setDropShadowEnabled(False)
        chart.setBackgroundRoundness(0)
        chart.setMargins(QMargins(2, 0, 2, 0))
        chart.setPlotAreaBackgroundVisible(False)
        legend = chart.legend()
        legend.setVisible(mostrar_leyenda)
        if mostrar_leyenda:
            legend.setAlignment(alineacion_leyenda)
            legend.setLabelColor(QColor(str(paleta["grafica_texto"])))
            legend.setBackgroundVisible(False)
            legend.setFont(self._crear_fuente_chart(8, 600))

    def _crear_chart_tendencia(
        self,
        serie_base: tuple[PuntoSerieDashboard, ...],
    ) -> QChart:
        serie = serie_base or ()
        if not serie or not any(punto.valor > 0 for punto in serie):
            return self._crear_chart_estado_vacio(
                "Sin recaudacion registrada en el periodo seleccionado."
            )

        actual = QLineSeries()
        actual.setName("Recaudado")
        color_linea = QColor(str(self._paleta_tema["grafica_linea_actual"]))
        actual.setColor(color_linea)
        actual.setPen(QPen(color_linea, 3.2))
        actual.setPointsVisible(True)
        actual.setMarkerSize(7.0)

        referencia = QLineSeries()
        referencia.setName("Promedio")
        color_promedio = QColor(str(self._paleta_tema["grafica_linea_promedio"]))
        pen_referencia = QPen(color_promedio, 2.0)
        pen_referencia.setStyle(Qt.PenStyle.DotLine)
        referencia.setPen(pen_referencia)
        referencia.setPointsVisible(True)
        referencia.setMarkerSize(5.0)

        valores = [punto.valor for punto in serie]
        promedio = fmean(valores) if valores else 0.0

        for indice, punto in enumerate(serie):
            actual.append(indice, punto.valor)
            referencia.append(indice, promedio)

        chart = QChart()
        chart.addSeries(actual)
        chart.addSeries(referencia)
        self._aplicar_estilo_chart(
            chart,
            mostrar_leyenda=True,
            alineacion_leyenda=Qt.AlignmentFlag.AlignTop,
        )
        chart.setMargins(QMargins(4, 8, 4, 0))

        eje_x = QBarCategoryAxis()
        eje_x.append([punto.etiqueta for punto in serie])
        eje_x.setLabelsColor(QColor(str(self._paleta_tema["grafica_texto_suave"])))
        eje_x.setGridLineVisible(False)
        eje_x.setLabelsFont(self._crear_fuente_chart(8, 600))

        eje_y = QValueAxis()
        maximo = max(valores + [promedio, 1.0])
        eje_y.setRange(0, maximo * 1.4)
        eje_y.setTickCount(5)
        eje_y.setMinorTickCount(1)
        eje_y.setLabelsColor(QColor(str(self._paleta_tema["grafica_texto_suave"])))
        eje_y.setGridLineColor(_crear_color_qt(self._paleta_tema["grafica_grid_fuerte"], "#92B6CC"))
        eje_y.setLabelFormat("L %.0f")
        eje_y.setLabelsFont(self._crear_fuente_chart(8, 600))

        chart.addAxis(eje_x, Qt.AlignmentFlag.AlignBottom)
        chart.addAxis(eje_y, Qt.AlignmentFlag.AlignLeft)
        actual.attachAxis(eje_x)
        actual.attachAxis(eje_y)
        referencia.attachAxis(eje_x)
        referencia.attachAxis(eje_y)
        return chart

    def _crear_chart_distribucion_deuda(
        self,
        categorias: tuple[CategoriaDashboard, ...],
    ) -> QChart:
        datos = tuple(categoria for categoria in categorias if categoria.valor > 0)
        if not datos:
            return self._crear_chart_estado_vacio("Sin deuda vencida registrada.")

        serie = QPieSeries()
        serie.setHoleSize(0.42)
        serie.setPieSize(0.86)
        serie.setHorizontalPosition(0.5)
        serie.setVerticalPosition(0.5)
        total = sum(categoria.valor for categoria in datos)
        for categoria in datos:
            trozo = serie.append(categoria.etiqueta, categoria.valor)
            trozo.setColor(QColor(self._color_rango_antiguedad(categoria.etiqueta)))
            trozo.setLabelVisible(total > 0 and categoria.valor / total >= 0.22)
            trozo.setLabel(f"{categoria.valor / total * 100:.0f}%")
            trozo.setLabelColor(QColor(str(self._paleta_tema["grafica_texto_fuerte"])))
            trozo.setLabelFont(self._crear_fuente_chart(8, 800))
            trozo.setBorderColor(QColor(str(self._paleta_tema["grafica_borde_trozo"])))
            trozo.setBorderWidth(1)

        chart = QChart()
        chart.addSeries(serie)
        self._aplicar_estilo_chart(
            chart,
            mostrar_leyenda=False,
        )
        return chart

    def _crear_chart_estado_vacio(self, mensaje: str) -> QChart:
        chart = QChart()
        self._aplicar_estilo_chart(chart, mostrar_leyenda=False)
        chart.setTitle(mensaje)
        chart.setTitleFont(self._crear_fuente_chart(10, 700))
        chart.setTitleBrush(QBrush(QColor(str(self._paleta_tema["grafica_texto_suave"]))))
        return chart

    def _color_rango_antiguedad(self, etiqueta: str) -> str:
        texto = etiqueta.lower()
        if "0-30" in texto:
            return str(self._paleta_tema["grafica_donut_0_30"])
        if "31-60" in texto:
            return str(self._paleta_tema["grafica_donut_31_60"])
        if "61-90" in texto:
            return str(self._paleta_tema["grafica_donut_61_90"])
        return str(self._paleta_tema["grafica_donut_90_mas"])

    @staticmethod
    def _crear_chart_view() -> QChartView:
        view = QChartView()
        view.setObjectName("chartViewDashboard")
        view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        view.setFrameShape(QFrame.Shape.NoFrame)
        view.setContentsMargins(0, 0, 0, 0)
        view.setAutoFillBackground(False)
        view.viewport().setAutoFillBackground(False)
        view.setBackgroundBrush(QBrush(QColor(0, 0, 0, 0)))
        view.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        view.setStyleSheet("background: transparent; border: none;")
        return view

    def _animar_aparicion_dashboard(self) -> None:
        widgets = [
            *self._tarjetas_metricas.values(),
            *self._filas_ranking,
            *self._tarjetas_insight,
        ]
        for animacion_activa in self._animaciones_activas:
            if isinstance(animacion_activa, QSequentialAnimationGroup):
                animacion_activa.stop()
        for widget in widgets:
            if widget.graphicsEffect() is not None:
                widget.setGraphicsEffect(None)
        self._animaciones_activas.clear()
        for indice, widget in enumerate(widgets):
            efecto = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(efecto)
            efecto.setOpacity(0.0)
            animacion = QPropertyAnimation(efecto, b"opacity", self)
            animacion.setDuration(220)
            animacion.setStartValue(0.0)
            animacion.setEndValue(1.0)
            animacion.setEasingCurve(QEasingCurve.Type.OutCubic)
            grupo = QSequentialAnimationGroup(self)
            grupo.addAnimation(QPauseAnimation(indice * 35, grupo))
            grupo.addAnimation(animacion)

            def _finalizar_animacion(
                widget_animado: QWidget = widget,
                grupo_animado: QSequentialAnimationGroup = grupo,
            ) -> None:
                widget_animado.setGraphicsEffect(None)
                if grupo_animado in self._animaciones_activas:
                    self._animaciones_activas.remove(grupo_animado)
                grupo_animado.deleteLater()

            grupo.finished.connect(_finalizar_animacion)
            self._animaciones_activas.append(grupo)
            grupo.start()

    @staticmethod
    def _formatear_moneda(valor: float) -> str:
        return f"L {valor:,.0f}"

    def _aplicar_estilos(self) -> None:
        paleta = self._paleta_tema
        self.setStyleSheet(
            f"""
            QWidget#vistaModuloPrincipal {{
                background: transparent;
                font-family: "{paleta["familia_tipografica"]}";
            }}
            QWidget#panelPrincipal,
            QWidget#paginaDashboard,
            QWidget#contenidoDashboard,
            QScrollArea#scrollDashboard,
            QScrollArea#scrollDashboard > QWidget > QWidget {{
                background: transparent;
            }}
            QScrollArea#scrollDashboard {{
                border: none;
            }}
            QWidget#contenedorSidebarFlotante {{
                background: transparent;
                border: none;
            }}
            QFrame#sidebarPrincipal {{
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 {paleta["tarjeta_panel_stop_1"]},
                    stop: 0.52 {paleta["tarjeta_panel_stop_2"]},
                    stop: 1 {paleta["tarjeta_panel_stop_3"]}
                );
                border: 1px solid {paleta["borde_medio"]};
                border-radius: 18px;
            }}
            QFrame#headerPrincipal {{
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 {paleta["tarjeta_panel_stop_1"]},
                    stop: 0.52 {paleta["tarjeta_panel_stop_2"]},
                    stop: 1 {paleta["tarjeta_panel_stop_3"]}
                );
                border: 1px solid {paleta["borde_medio"]};
                border-radius: 18px;
            }}
            QFrame#tarjetaPanel {{
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 {paleta["tarjeta_panel_stop_1"]},
                    stop: 0.52 {paleta["tarjeta_panel_stop_2"]},
                    stop: 1 {paleta["tarjeta_panel_stop_3"]}
                );
                border: 1px solid {paleta["borde_medio"]};
                border-radius: 14px;
            }}
            QFrame#footerDashboard {{
                background: {paleta["fondo_superficie_muy_suave"]};
                border: 1px solid {paleta["borde_suave"]};
                border-radius: 9px;
            }}
            QLabel#textoFooterDashboard {{
                color: {paleta["texto_panel_secundario"]};
                font-size: {paleta["tamano_fuente_base"]}px;
                font-weight: 700;
            }}
            QLabel#textoEstadoDashboard {{
                color: {paleta["texto_panel_detalle"]};
                font-size: {paleta["tamano_fuente_base"]}px;
                font-weight: 800;
                padding-left: 8px;
            }}
            QLabel#textoEstadoDashboard[estado="pendiente"] {{
                color: #6DF1DC;
            }}
            QLabel#textoEstadoDashboard[estado="error"] {{
                color: #FCA5A5;
            }}
            QWidget#contenedorNavegacionSidebar,
            QScrollArea#scrollNavegacionSidebar {{
                background: transparent;
                border: none;
            }}
            QWidget#encabezadoSidebar {{
                background: transparent;
                border: none;
                border-radius: 0;
            }}
            QFrame#contenedorMarcaSidebar {{
                background: {paleta["fondo_superficie_muy_suave"]};
                border: 1px solid {paleta["borde_suave"]};
                border-radius: 18px;
            }}
            QFrame#seccionSidebarCard,
            QFrame#panelAccionesSidebar {{
                background: transparent;
                border: none;
            }}
            QLabel#logoSidebar {{
                background: transparent;
                border: none;
            }}
            QPushButton#botonPerfilHeader {{
                background: rgba(47, 155, 255, 0.10);
                border: 1px solid {paleta["borde_suave"]};
                border-radius: 12px;
                text-align: left;
                padding: 0;
            }}
            QPushButton#botonPerfilHeader:hover {{
                background: rgba(47, 155, 255, 0.17);
                border-color: {paleta["borde_principal"]};
            }}
            QLabel#avatarPerfilHeader {{
                background: {paleta["fondo_avatar"]};
                border: 1px solid {paleta["borde_avatar"]};
                border-radius: 16px;
                color: {paleta["texto_principal"]};
                font-size: 12px;
                font-weight: 900;
            }}
            QLabel#nombrePerfilHeader {{
                color: {paleta["texto_principal"]};
                font-size: 11px;
                font-weight: 850;
            }}
            QLabel#rolPerfilHeader {{
                color: {paleta["texto_secundario"]};
                font-size: 9px;
                font-weight: 700;
            }}
            QWidget#contenedorItemsSidebar {{
                background: transparent;
            }}
            QLabel#marcaPrincipal {{
                font-size: {paleta["tamano_titulo_modulo"] + 7}px;
                font-weight: {paleta["peso_titulo"]};
                min-height: 38px;
            }}
            QLabel#subtituloMarca,
            QLabel#descripcionPrincipal {{
                color: {paleta["texto_secundario"]};
                font-size: {paleta["tamano_fuente_base"] - 1}px;
                font-weight: {paleta["peso_cuerpo"]};
            }}
            QLabel#subtituloMarca {{
                padding: 0 10px;
            }}
            QLabel#descripcionPrincipal {{
                font-size: {paleta["tamano_fuente_base"] + 1}px;
            }}
            QLabel#descripcionPanel,
            QLabel#tabsSuaves {{
                color: {paleta["texto_panel_secundario"]};
                font-size: {paleta["tamano_fuente_base"] + 1}px;
                font-weight: {paleta["peso_cuerpo"]};
            }}
            QLabel#tituloPrincipal {{
                color: {paleta["texto_principal"]};
            }}
            QLabel#tituloSeccionSidebar {{
                color: {paleta["texto_menu_seccion"]};
                font-size: {paleta["tamano_fuente_base"]}px;
                font-weight: {paleta["peso_titulo"]};
                letter-spacing: 0.8px;
                padding: 2px 6px 4px 6px;
            }}
            QLabel#tituloSeccionSidebar[activa="true"] {{
                color: {paleta["texto_menu_activo"]};
            }}
            QLabel#tituloPrincipal {{
                font-size: {paleta["tamano_titulo_modulo"] + 3}px;
                font-weight: {paleta["peso_titulo"]};
            }}
            QLabel#tituloPanel {{
                color: {paleta["texto_panel_principal"]};
                font-size: {paleta["tamano_titulo_panel"] + 3}px;
                font-weight: {paleta["peso_titulo"]};
            }}
            QLabel#badgePanelDashboard {{
                background: {paleta["fondo_badge_activo"]};
                color: {paleta["texto_badge"]};
                border: 1px solid {paleta["borde_badge_activo"]};
                border-radius: 10px;
                padding: 3px 9px;
                font-size: 9px;
                font-weight: 800;
                letter-spacing: 0.06em;
            }}
            QPushButton#botonSidebar {{
                min-height: 36px;
                border: 1px solid transparent;
                border-radius: 6px;
                background: transparent;
                padding: 0;
            }}
            QLabel#textoBotonSidebar {{
                color: {paleta["texto_menu_normal"]};
                background: transparent;
                border: none;
                font-size: {paleta["tamano_fuente_base"] + 1}px;
                font-weight: 850;
                padding: 0;
            }}
            QLabel#iconoBotonSidebar {{
                background: transparent;
                border: none;
                padding: 0;
            }}
            QPushButton#botonSidebar[tipoSidebar="accion"] {{
                background: transparent;
            }}
            QPushButton#botonSidebar[tipoSidebar="salida"] {{
                color: {paleta["texto_error"]};
                background: transparent;
            }}
            QPushButton#botonSidebar:hover {{
                background: {paleta["fondo_menu_hover"]};
                border-color: {paleta["borde_principal"]};
            }}
            QPushButton#botonSidebar[activo="true"] {{
                background: {paleta["fondo_menu_activo"]};
                border-color: transparent;
            }}
            QLabel#textoBotonSidebar[activo="true"] {{
                color: {paleta["texto_menu_activo"]};
                font-weight: 900;
            }}
            QPushButton#botonSidebar[dashboardPendienteActualizacion="true"] {{
                background: rgba(45, 212, 191, 0.14);
                border-color: rgba(109, 241, 220, 0.62);
            }}
            QPushButton#botonSidebar[dashboardPendienteActualizacion="true"][activo="true"] {{
                background: rgba(45, 212, 191, 0.18);
                border-color: rgba(109, 241, 220, 0.78);
            }}
            QWidget#tarjetaInsight {{
                background: rgba(5, 20, 35, 0.46);
                border: 1px solid rgba(120, 210, 255, 0.16);
                border-radius: 14px;
            }}
            QWidget#tarjetaInsight:hover {{
                background: rgba(8, 32, 52, 0.58);
                border-color: rgba(120, 210, 255, 0.24);
            }}
            QLabel#insigniaInsight {{
                border-radius: 14px;
            }}
            QLabel#insightTitulo {{
                color: {paleta["texto_panel_secundario"]};
                font-size: {paleta["tamano_fuente_base"] + 1}px;
                font-weight: {paleta["peso_subtitulo"]};
            }}
            QLabel#insightValor {{
                color: {paleta["texto_panel_fuerte"]};
                font-size: 15px;
                font-weight: {paleta["peso_titulo"]};
            }}
            QLabel#insightDetalle {{
                color: {paleta["texto_panel_detalle"]};
                font-size: {paleta["tamano_fuente_base"] + 1}px;
            }}
            QWidget#contenedorDistribucionDeuda {{
                background: transparent;
                border: none;
            }}
            QFrame#leyendaDonutDeuda {{
                background: rgba(5, 20, 35, 0.46);
                border: 1px solid rgba(120, 210, 255, 0.18);
                border-radius: 14px;
            }}
            QLabel#leyendaDonutTexto {{
                color: {paleta["texto_panel_secundario"]};
                font-size: {paleta["tamano_fuente_base"]}px;
                font-weight: 700;
            }}
            QLabel#leyendaDonutValor {{
                color: {paleta["texto_panel_fuerte"]};
                font-size: {paleta["tamano_fuente_base"]}px;
                font-weight: 900;
            }}
            QFrame#filaRanking {{
                background: transparent;
            }}
            QLabel#rankingEtiqueta {{
                color: {paleta["texto_panel_fuerte"]};
                font-size: {paleta["tamano_fuente_base"] + 2}px;
                font-weight: {paleta["peso_cuerpo"]};
            }}
            QLabel#rankingValor {{
                color: {paleta["texto_panel_fuerte"]};
                font-size: {paleta["tamano_fuente_base"] + 2}px;
                font-weight: {paleta["peso_subtitulo"]};
            }}
            QProgressBar#rankingBarra {{
                background: {paleta["ranking_barra"]};
                border: none;
                border-radius: 5px;
            }}
            QProgressBar#rankingBarra::chunk {{
                background: {paleta["ranking_chunk"]};
                border-radius: 5px;
            }}
            QFrame#panelPerfilUsuario {{
                background: {paleta["fondo_superficie"]};
                border: 1px solid {paleta["borde_principal"]};
                border-radius: 22px;
            }}
            QFrame#encabezadoPanelPerfil,
            QFrame#bloquePanelPerfil,
            QFrame#piePanelPerfil {{
                background: {paleta["fondo_superficie_suave"]};
                border: 1px solid {paleta["borde_suave"]};
                border-radius: 18px;
            }}
            QLabel#avatarPanelPerfil {{
                background: {paleta["fondo_avatar"]};
                border: 1px solid {paleta["borde_avatar"]};
                border-radius: 27px;
                color: {paleta["texto_principal"]};
                font-size: 18px;
                font-weight: 900;
            }}
            QLabel#nombrePanelPerfil {{
                color: {paleta["texto_principal"]};
                font-size: 16px;
                font-weight: 900;
            }}
            QLabel#rolPanelPerfil,
            QLabel#tituloDatoPerfil,
            QLabel#detallePanelPerfil {{
                color: {paleta["texto_secundario"]};
                font-size: 12px;
                font-weight: {paleta["peso_cuerpo"]};
            }}
            QLabel#valorDatoPerfil,
            QLabel#sistemaPanelPerfil {{
                color: {paleta["texto_panel_principal"]};
                font-size: 13px;
                font-weight: {paleta["peso_titulo"]};
            }}
            QLabel#sistemaPanelPerfil {{
                font-size: 14px;
            }}
            QLabel#iconoDatoPerfil {{
                background: {paleta["fondo_superficie_suave"]};
                border: 1px solid {paleta["borde_suave"]};
                border-radius: 12px;
            }}
            """
        )

