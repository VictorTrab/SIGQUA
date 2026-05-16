"""Vista PySide6 del modulo de morosidad."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from comun.ui import configurar_tabla_operativa, crear_boton_operativo, crear_item_tabla
from comun.ui.temas import TEMA_SICAP_PREDETERMINADO, obtener_paleta_tema
from modulos.morosidad.entidades import EstadoMorosidad


class VistaMorosidad(QWidget):
    """Consulta simple de casas activas con deuda vencida."""

    buscar_solicitado = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("vistaMorosidad")
        self._paleta = obtener_paleta_tema(TEMA_SICAP_PREDETERMINADO)
        self._construir_ui()
        self._aplicar_estilos()

    def mostrar_estado(
        self,
        estado: EstadoMorosidad,
        formatear_moneda: Callable[[int], str],
        formatear_fecha: Callable[[str], str],
    ) -> None:
        resumen = estado.resumen
        self._valor_casas.setText(str(resumen.total_casas))
        self._valor_meses.setText(str(resumen.total_meses_vencidos))
        self._valor_base.setText(formatear_moneda(resumen.deuda_base_centavos))
        self._valor_mora.setText(formatear_moneda(resumen.recargo_mora_centavos))
        self._valor_total.setText(formatear_moneda(resumen.deuda_total_centavos))

        self._tabla.setRowCount(len(estado.filas))
        for fila, item in enumerate(estado.filas):
            valores = (
                item.casa_codigo,
                item.abonado_nombre,
                item.abonado_dni,
                item.barrio_nombre,
                item.meses_vencidos,
                formatear_moneda(item.deuda_base_centavos),
                formatear_moneda(item.recargo_mora_centavos),
                formatear_moneda(item.deuda_total_centavos),
                formatear_fecha(item.vencimiento_mas_antiguo),
            )
            for columna, valor in enumerate(valores):
                self._tabla.setItem(fila, columna, crear_item_tabla(valor))
        self._tabla.resizeRowsToContents()

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(16)

        descripcion = QLabel(
            "Casas activas con deuda vencida. La mora se muestra separada de la deuda base."
        )
        descripcion.setObjectName("descripcionModulo")
        descripcion.setWordWrap(True)
        layout.addWidget(descripcion)

        fila_resumen = QHBoxLayout()
        fila_resumen.setSpacing(12)
        self._valor_casas = self._crear_tarjeta(fila_resumen, "Casas en mora")
        self._valor_meses = self._crear_tarjeta(fila_resumen, "Meses vencidos")
        self._valor_base = self._crear_tarjeta(fila_resumen, "Deuda base")
        self._valor_mora = self._crear_tarjeta(fila_resumen, "Recargo mora")
        self._valor_total = self._crear_tarjeta(fila_resumen, "Total vencido")
        layout.addLayout(fila_resumen)

        fila_busqueda = QHBoxLayout()
        self._input_busqueda = QLineEdit()
        self._input_busqueda.setPlaceholderText("Filtrar por casa, abonado, DNI o barrio")
        self._input_busqueda.returnPressed.connect(self._emitir_busqueda)
        boton_buscar = crear_boton_operativo("Buscar")
        boton_buscar.clicked.connect(self._emitir_busqueda)
        fila_busqueda.addWidget(self._input_busqueda, 1)
        fila_busqueda.addWidget(boton_buscar)
        layout.addLayout(fila_busqueda)

        self._tabla = QTableWidget()
        configurar_tabla_operativa(
            self._tabla,
            [
                "Casa",
                "Abonado",
                "DNI",
                "Barrio",
                "Meses",
                "Deuda base",
                "Mora",
                "Total",
                "Mas antiguo",
            ],
        )
        self._tabla.setObjectName("tablaOperativaOscura")
        self._tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self._tabla, 1)

    def _crear_tarjeta(self, layout: QHBoxLayout, titulo: str) -> QLabel:
        tarjeta = QFrame()
        tarjeta.setObjectName("tarjetaResumenSimple")
        tarjeta_layout = QVBoxLayout(tarjeta)
        tarjeta_layout.setContentsMargins(14, 12, 14, 12)
        etiqueta = QLabel(titulo)
        etiqueta.setObjectName("tarjetaTitulo")
        valor = QLabel("0")
        valor.setObjectName("tarjetaValor")
        tarjeta_layout.addWidget(etiqueta)
        tarjeta_layout.addWidget(valor)
        layout.addWidget(tarjeta)
        return valor

    def _emitir_busqueda(self) -> None:
        self.buscar_solicitado.emit(self._input_busqueda.text().strip())

    def _aplicar_estilos(self) -> None:
        paleta = self._paleta
        self.setStyleSheet(
            f"""
            QWidget#vistaMorosidad {{
                background-color: {paleta["fondo_principal"]};
                color: {paleta["texto_principal"]};
            }}
            QLabel#descripcionModulo {{
                color: {paleta["texto_secundario"]};
                font-size: 13px;
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
                font-size: 22px;
                font-weight: 800;
            }}
            QLineEdit {{
                background-color: {paleta["fondo_input"]};
                border: 1px solid {paleta["borde_medio"]};
                border-radius: 12px;
                color: {paleta["texto_input"]};
                min-height: 36px;
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
