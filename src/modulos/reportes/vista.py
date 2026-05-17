"""Vista PySide6 del modulo de reportes."""

from __future__ import annotations

from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFrame,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from comun.ui import configurar_tabla_operativa, crear_boton_operativo, crear_item_tabla
from comun.ui.temas import TEMA_SICAP_PREDETERMINADO, obtener_paleta_tema
from modulos.reportes.entidades import EstadoReportes, TablaReporte


class VistaReportes(QWidget):
    """Tablero de reportes basicos del prototipo."""

    filtros_aplicados = Signal(str, str)
    exportar_solicitado = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("vistaReportes")
        self._paleta = obtener_paleta_tema(TEMA_SICAP_PREDETERMINADO)
        self._tablas: tuple[TablaReporte, ...] = ()
        self._construir_ui()
        self._aplicar_estilos()

    def mostrar_estado(self, estado: EstadoReportes) -> None:
        self._mostrar_indicadores(estado)
        self._tablas = estado.tablas
        self._fecha_desde.blockSignals(True)
        self._fecha_hasta.blockSignals(True)
        if estado.filtros.fecha_desde:
            self._fecha_desde.setDate(QDate.fromString(estado.filtros.fecha_desde, "yyyy-MM-dd"))
        if estado.filtros.fecha_hasta:
            self._fecha_hasta.setDate(QDate.fromString(estado.filtros.fecha_hasta, "yyyy-MM-dd"))
        self._fecha_desde.blockSignals(False)
        self._fecha_hasta.blockSignals(False)
        self._combo_reportes.blockSignals(True)
        codigo_previo = self._combo_reportes.currentData()
        self._combo_reportes.clear()
        for tabla in self._tablas:
            self._combo_reportes.addItem(tabla.titulo, tabla.codigo)
        if codigo_previo is not None:
            indice = self._combo_reportes.findData(codigo_previo)
            if indice >= 0:
                self._combo_reportes.setCurrentIndex(indice)
        self._combo_reportes.blockSignals(False)
        self._mostrar_tabla_actual()

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(16)

        self._mensaje = QLabel("")
        self._mensaje.setObjectName("mensajeReportes")
        self._mensaje.setVisible(False)
        layout.addWidget(self._mensaje)

        self._fila_indicadores = QHBoxLayout()
        self._fila_indicadores.setSpacing(12)
        self._indicadores: list[tuple[QLabel, QLabel, QLabel]] = []
        for _ in range(5):
            self._indicadores.append(self._crear_tarjeta_indicador(self._fila_indicadores))
        layout.addLayout(self._fila_indicadores)

        panel_filtros = QFrame()
        panel_filtros.setObjectName("panelFiltrosReportes")
        layout_filtros = QHBoxLayout(panel_filtros)
        layout_filtros.setContentsMargins(14, 14, 14, 14)
        layout_filtros.setSpacing(10)
        self._fecha_desde = QDateEdit()
        self._fecha_desde.setObjectName("campoFechaReporte")
        self._fecha_desde.setDisplayFormat("yyyy-MM-dd")
        self._fecha_desde.setCalendarPopup(True)
        self._fecha_desde.setDate(QDate.currentDate().addDays(-29))
        self._fecha_hasta = QDateEdit()
        self._fecha_hasta.setObjectName("campoFechaReporte")
        self._fecha_hasta.setDisplayFormat("yyyy-MM-dd")
        self._fecha_hasta.setCalendarPopup(True)
        self._fecha_hasta.setDate(QDate.currentDate())
        boton_aplicar = crear_boton_operativo("Aplicar")
        boton_exportar = crear_boton_operativo("Exportar")
        boton_aplicar.clicked.connect(self._emitir_filtros)
        boton_exportar.clicked.connect(self.exportar_solicitado.emit)
        layout_filtros.addWidget(QLabel("Desde"))
        layout_filtros.addWidget(self._fecha_desde)
        layout_filtros.addWidget(QLabel("Hasta"))
        layout_filtros.addWidget(self._fecha_hasta)
        layout_filtros.addStretch(1)
        layout_filtros.addWidget(boton_aplicar)
        layout_filtros.addWidget(boton_exportar)
        layout.addWidget(panel_filtros)

        fila_selector = QHBoxLayout()
        self._combo_reportes = QComboBox()
        self._combo_reportes.currentIndexChanged.connect(self._mostrar_tabla_actual)
        self._titulo_reporte = QLabel("Selecciona un reporte")
        self._titulo_reporte.setObjectName("tituloReporte")
        self._descripcion_reporte = QLabel("")
        self._descripcion_reporte.setObjectName("descripcionReporte")
        self._descripcion_reporte.setWordWrap(True)
        bloque_texto = QVBoxLayout()
        bloque_texto.addWidget(self._titulo_reporte)
        bloque_texto.addWidget(self._descripcion_reporte)
        fila_selector.addLayout(bloque_texto, 1)
        fila_selector.addWidget(self._combo_reportes)
        layout.addLayout(fila_selector)

        self._tabla = QTableWidget()
        self._tabla.setObjectName("tablaOperativaOscura")
        layout.addWidget(self._tabla, 1)

    def mostrar_mensaje(self, mensaje: str, es_error: bool = False) -> None:
        self._mensaje.setText(mensaje)
        self._mensaje.setProperty("error", es_error)
        self._mensaje.style().unpolish(self._mensaje)
        self._mensaje.style().polish(self._mensaje)
        self._mensaje.setVisible(bool(mensaje))

    def solicitar_ruta_exportacion(self, codigo_reporte: str) -> str:
        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar reporte",
            f"{codigo_reporte}.pdf",
            "PDF (*.pdf)",
        )
        return ruta

    def obtener_reporte_actual_codigo(self) -> str:
        return str(self._combo_reportes.currentData() or "")

    def _crear_tarjeta_indicador(self, layout: QHBoxLayout) -> tuple[QLabel, QLabel, QLabel]:
        tarjeta = QFrame()
        tarjeta.setObjectName("tarjetaResumenSimple")
        tarjeta_layout = QVBoxLayout(tarjeta)
        tarjeta_layout.setContentsMargins(14, 12, 14, 12)
        titulo = QLabel("-")
        titulo.setObjectName("tarjetaTitulo")
        valor = QLabel("0")
        valor.setObjectName("tarjetaValor")
        detalle = QLabel("")
        detalle.setObjectName("tarjetaDetalle")
        detalle.setWordWrap(True)
        tarjeta_layout.addWidget(titulo)
        tarjeta_layout.addWidget(valor)
        tarjeta_layout.addWidget(detalle)
        layout.addWidget(tarjeta)
        return titulo, valor, detalle

    def _mostrar_indicadores(self, estado: EstadoReportes) -> None:
        for indice, widgets in enumerate(self._indicadores):
            titulo, valor, detalle = widgets
            if indice < len(estado.indicadores):
                indicador = estado.indicadores[indice]
                titulo.setText(indicador.titulo)
                valor.setText(indicador.valor)
                detalle.setText(indicador.detalle)
            else:
                titulo.setText("-")
                valor.setText("0")
                detalle.setText("")

    def _mostrar_tabla_actual(self) -> None:
        codigo = self._combo_reportes.currentData()
        tabla = next((item for item in self._tablas if item.codigo == codigo), None)
        if tabla is None:
            self._tabla.setRowCount(0)
            self._tabla.setColumnCount(0)
            return
        self._titulo_reporte.setText(tabla.titulo)
        self._descripcion_reporte.setText(tabla.descripcion)
        configurar_tabla_operativa(self._tabla, list(tabla.columnas))
        self._tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._tabla.setRowCount(len(tabla.filas))
        for fila, valores in enumerate(tabla.filas):
            for columna, valor in enumerate(valores):
                self._tabla.setItem(fila, columna, crear_item_tabla(valor))
        self._tabla.resizeRowsToContents()

    def _emitir_filtros(self) -> None:
        self.filtros_aplicados.emit(
            self._fecha_desde.date().toString("yyyy-MM-dd"),
            self._fecha_hasta.date().toString("yyyy-MM-dd"),
        )

    def _aplicar_estilos(self) -> None:
        paleta = self._paleta
        self.setStyleSheet(
            f"""
            QWidget#vistaReportes {{
                background-color: {paleta["fondo_principal"]};
                color: {paleta["texto_principal"]};
            }}
            QLabel#descripcionModulo,
            QLabel#descripcionReporte,
            QLabel#tarjetaDetalle {{
                color: {paleta["texto_secundario"]};
                font-size: 12px;
            }}
            QLabel#mensajeReportes {{
                border-radius: 12px;
                padding: 10px 12px;
                font-size: 12px;
                font-weight: 700;
            }}
            QLabel#mensajeReportes[error="false"] {{
                background-color: {paleta["fondo_exito"]};
                border: 1px solid {paleta["borde_exito"]};
                color: {paleta["texto_exito"]};
            }}
            QLabel#mensajeReportes[error="true"] {{
                background-color: {paleta["fondo_error"]};
                border: 1px solid {paleta["borde_error"]};
                color: {paleta["texto_error"]};
            }}
            QLabel#tituloReporte {{
                color: #ffffff;
                font-size: 16px;
                font-weight: 800;
            }}
            QFrame#panelFiltrosReportes {{
                background-color: {paleta["fondo_superficie_suave"]};
                border: 1px solid {paleta["borde_suave"]};
                border-radius: 18px;
            }}
            QFrame#tarjetaResumenSimple {{
                background-color: {paleta["fondo_superficie_suave"]};
                border: 1px solid {paleta["borde_suave"]};
                border-radius: 18px;
            }}
            QLabel#tarjetaTitulo {{
                color: {paleta["texto_secundario"]};
                font-size: 11px;
                font-weight: 700;
            }}
            QLabel#tarjetaValor {{
                color: #ffffff;
                font-size: 20px;
                font-weight: 800;
            }}
            QComboBox,
            QDateEdit#campoFechaReporte {{
                background-color: {paleta["fondo_input"]};
                border: 1px solid {paleta["borde_medio"]};
                border-radius: 12px;
                color: {paleta["texto_input"]};
                min-height: 36px;
                min-width: 260px;
                padding: 0 10px;
            }}
            QTableWidget#tablaOperativaOscura {{
                background-color: {paleta["fondo_superficie_muy_suave"]};
                alternate-background-color: {paleta["fondo_superficie_suave"]};
                border: 1px solid {paleta["borde_suave"]};
                border-radius: 14px;
                color: {paleta["texto_principal"]};
            }}
            QHeaderView::section {{
                background-color: {paleta["fondo_tabla_header"]};
                border: 0;
                color: #ffffff;
                font-weight: 800;
                padding: 8px;
            }}
            QTableWidget::item:selected {{
                background-color: rgba(45, 212, 191, 0.24);
                color: #ffffff;
            }}
            """
        )
