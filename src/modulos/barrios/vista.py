"""Vista PySide6 del modulo de barrios."""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from comun.ui import (
    configurar_tabla_operativa,
    crear_boton_operativo,
    crear_item_tabla,
    obtener_icono_tabler_coloreado,
)
from modulos.barrios.entidades import (
    Barrio,
    FILTRO_BARRIOS_CON_ABONADOS,
    FILTRO_BARRIOS_SIN_ABONADOS,
    FILTRO_BARRIOS_TODOS,
    FormularioBarrio,
    PaginaBarrios,
    ResumenBarrios,
)


class TarjetaResumenBarrio(QFrame):
    """Tarjeta de resumen para el encabezado del modulo."""

    def __init__(self, icono: str, color_icono: str) -> None:
        super().__init__()
        self.setObjectName("tarjetaResumenBarrios")
        self.setMinimumHeight(116)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        self._icono = QLabel("")
        self._icono.setObjectName("iconoTarjetaResumen")
        self._icono.setFixedSize(44, 44)
        self._icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icono.setPixmap(
            obtener_icono_tabler_coloreado(icono, color_icono, tamano=20).pixmap(20, 20)
        )
        self._icono.setProperty("colorTarjeta", color_icono)

        bloque_texto = QVBoxLayout()
        bloque_texto.setContentsMargins(0, 0, 0, 0)
        bloque_texto.setSpacing(3)

        self._titulo = QLabel("")
        self._titulo.setObjectName("tituloTarjetaResumen")
        self._valor = QLabel("")
        self._valor.setObjectName("valorTarjetaResumen")
        self._detalle = QLabel("")
        self._detalle.setObjectName("detalleTarjetaResumen")
        self._detalle.setWordWrap(True)

        bloque_texto.addWidget(self._titulo)
        bloque_texto.addWidget(self._valor)
        bloque_texto.addWidget(self._detalle)
        bloque_texto.addStretch(1)

        layout.addWidget(self._icono, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addLayout(bloque_texto, 1)

    def actualizar(self, titulo: str, valor: str, detalle: str) -> None:
        self._titulo.setText(titulo)
        self._valor.setText(valor)
        self._detalle.setText(detalle)


class DialogoFormularioBarrio(QDialog):
    """Modal para crear o editar barrios."""

    def __init__(self, barrio: Barrio | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._barrio = barrio
        self.setModal(True)
        self.setMinimumWidth(460)
        self.setWindowTitle("Editar barrio" if barrio else "Nuevo barrio")
        self._construir_ui()
        self._aplicar_estilos()

    def obtener_formulario(self) -> FormularioBarrio:
        return FormularioBarrio(
            identificador=None if self._barrio is None else self._barrio.identificador,
            nombre=self._campo_nombre.text(),
            estado=self._combo_estado.currentText(),
            observaciones=self._campo_observaciones.toPlainText(),
        )

    def accept(self) -> None:
        if not self._campo_nombre.text().strip():
            self._mensaje.setText("Indica el nombre del barrio para continuar.")
            self._mensaje.setVisible(True)
            return
        self._mensaje.setVisible(False)
        super().accept()

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(16)

        titulo = QLabel("Editar barrio" if self._barrio else "Nuevo barrio")
        titulo.setObjectName("tituloDialogoBarrio")
        descripcion = QLabel(
            "Completa el formulario con la informacion principal del barrio."
        )
        descripcion.setObjectName("descripcionDialogoBarrio")
        descripcion.setWordWrap(True)

        formulario = QFormLayout()
        formulario.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        formulario.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        formulario.setHorizontalSpacing(12)
        formulario.setVerticalSpacing(12)

        self._campo_nombre = QLineEdit()
        self._campo_nombre.setPlaceholderText("Nombre del barrio")
        self._combo_estado = QComboBox()
        self._combo_estado.addItems(["ACTIVO", "INACTIVO"])
        self._campo_observaciones = QPlainTextEdit()
        self._campo_observaciones.setPlaceholderText("Observaciones")
        self._campo_observaciones.setFixedHeight(112)

        if self._barrio is not None:
            self._campo_nombre.setText(self._barrio.nombre)
            self._combo_estado.setCurrentText(self._barrio.estado)
            self._campo_observaciones.setPlainText(self._barrio.observaciones)

        formulario.addRow("Nombre del barrio", self._campo_nombre)
        formulario.addRow("Estado", self._combo_estado)
        formulario.addRow("Observaciones", self._campo_observaciones)

        self._mensaje = QLabel("")
        self._mensaje.setObjectName("mensajeDialogoBarrio")
        self._mensaje.setVisible(False)

        fila_acciones = QHBoxLayout()
        fila_acciones.setSpacing(10)
        fila_acciones.addStretch(1)
        boton_cancelar = crear_boton_operativo("Cancelar")
        boton_guardar = crear_boton_operativo("Guardar cambios", principal=True)
        boton_cancelar.clicked.connect(self.reject)
        boton_guardar.clicked.connect(self.accept)
        fila_acciones.addWidget(boton_cancelar)
        fila_acciones.addWidget(boton_guardar)

        layout.addWidget(titulo)
        layout.addWidget(descripcion)
        layout.addLayout(formulario)
        layout.addWidget(self._mensaje)
        layout.addLayout(fila_acciones)

    def _aplicar_estilos(self) -> None:
        self.setStyleSheet(
            """
            QDialog {
                background: #1f2a44;
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 24px;
            }
            QLabel#tituloDialogoBarrio {
                color: #ffffff;
                font-size: 20px;
                font-weight: 900;
            }
            QLabel#descripcionDialogoBarrio,
            QLabel#mensajeDialogoBarrio {
                color: rgba(232, 239, 249, 0.80);
                font-size: 13px;
            }
            QLabel#mensajeDialogoBarrio {
                color: #ffd7d2;
                background: rgba(191, 60, 44, 0.18);
                border: 1px solid rgba(255, 205, 199, 0.20);
                border-radius: 14px;
                padding: 10px 12px;
                font-weight: 700;
            }
            QLabel {
                color: #f5fbff;
                font-size: 13px;
                font-weight: 700;
            }
            QLineEdit, QComboBox, QPlainTextEdit {
                border: 1px solid rgba(255, 255, 255, 0.18);
                border-radius: 14px;
                background: rgba(255, 255, 255, 0.11);
                color: #f5fbff;
                padding: 10px 12px;
                font-size: 13px;
            }
            QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus {
                border-color: rgba(109, 241, 220, 0.40);
                background: rgba(255, 255, 255, 0.16);
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox QAbstractItemView {
                background: #24304d;
                color: #f5fbff;
                selection-background-color: rgba(109, 241, 220, 0.22);
            }
            """
        )


class DialogoDetalleBarrio(QDialog):
    """Modal para consultar detalle del barrio."""

    def __init__(
        self,
        barrio: Barrio,
        fecha_actualizada: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._barrio = barrio
        self._fecha_actualizada = fecha_actualizada
        self._accion_resultado = "cerrar"
        self.setModal(True)
        self.setMinimumWidth(560)
        self.setWindowTitle("Detalle de barrio")
        self._construir_ui()
        self._aplicar_estilos()

    @property
    def accion_resultado(self) -> str:
        return self._accion_resultado

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(16)

        titulo = QLabel("Detalle de barrio")
        titulo.setObjectName("tituloDialogoBarrio")
        descripcion = QLabel(
            "Consulta informacion general, estado operativo y estadisticas del barrio."
        )
        descripcion.setObjectName("descripcionDialogoBarrio")
        descripcion.setWordWrap(True)

        encabezado = QFrame()
        encabezado.setObjectName("bloqueDetalleBarrio")
        encabezado_layout = QVBoxLayout(encabezado)
        encabezado_layout.setContentsMargins(18, 18, 18, 18)
        encabezado_layout.setSpacing(10)

        fila_superior = QHBoxLayout()
        fila_superior.setSpacing(12)
        bloque_nombre = QVBoxLayout()
        bloque_nombre.setSpacing(4)
        codigo = QLabel(self._barrio.codigo)
        codigo.setObjectName("codigoBarrioDetalle")
        nombre = QLabel(self._barrio.nombre)
        nombre.setObjectName("nombreBarrioDetalle")
        bloque_nombre.addWidget(codigo)
        bloque_nombre.addWidget(nombre)

        estado = QLabel(self._barrio.estado.title())
        estado.setObjectName("badgeDetalleBarrio")
        estado.setProperty("activo", self._barrio.estado == "ACTIVO")
        estado.style().unpolish(estado)
        estado.style().polish(estado)

        fila_superior.addLayout(bloque_nombre, 1)
        fila_superior.addWidget(estado, alignment=Qt.AlignmentFlag.AlignTop)

        grid_info = QGridLayout()
        grid_info.setHorizontalSpacing(12)
        grid_info.setVerticalSpacing(12)
        grid_info.addWidget(self._crear_campo_detalle("Codigo", self._barrio.codigo), 0, 0)
        grid_info.addWidget(self._crear_campo_detalle("Estado", self._barrio.estado.title()), 0, 1)
        grid_info.addWidget(
            self._crear_campo_detalle("Ultima actualizacion", self._fecha_actualizada),
            1,
            0,
            1,
            2,
        )

        fila_metricas = QHBoxLayout()
        fila_metricas.setSpacing(12)
        fila_metricas.addWidget(
            self._crear_tarjeta_detalle("Abonados", str(self._barrio.total_abonados)),
            1,
        )
        fila_metricas.addWidget(
            self._crear_tarjeta_detalle("Casas", str(self._barrio.total_casas)),
            1,
        )

        observaciones = self._crear_campo_detalle(
            "Observaciones",
            self._barrio.observaciones or "Sin observaciones registradas.",
        )
        observaciones.setObjectName("campoDetalleBarrioAmplio")

        encabezado_layout.addLayout(fila_superior)
        encabezado_layout.addLayout(grid_info)
        encabezado_layout.addLayout(fila_metricas)
        encabezado_layout.addWidget(observaciones)

        fila_acciones = QHBoxLayout()
        fila_acciones.setSpacing(10)
        boton_cerrar = crear_boton_operativo("Cerrar")
        boton_ver_abonados = crear_boton_operativo("Ver abonados")
        boton_ver_casas = crear_boton_operativo("Ver casas")
        boton_editar = crear_boton_operativo("Editar", principal=True)

        boton_cerrar.clicked.connect(self.reject)
        boton_ver_abonados.clicked.connect(self._mostrar_aviso_abonados)
        boton_ver_casas.clicked.connect(self._mostrar_aviso_casas)
        boton_editar.clicked.connect(self._solicitar_edicion)

        fila_acciones.addWidget(boton_cerrar)
        fila_acciones.addStretch(1)
        fila_acciones.addWidget(boton_ver_abonados)
        fila_acciones.addWidget(boton_ver_casas)
        fila_acciones.addWidget(boton_editar)

        layout.addWidget(titulo)
        layout.addWidget(descripcion)
        layout.addWidget(encabezado)
        layout.addLayout(fila_acciones)

    def _crear_campo_detalle(self, etiqueta: str, valor: str) -> QFrame:
        tarjeta = QFrame()
        tarjeta.setObjectName("campoDetalleBarrio")
        layout = QVBoxLayout(tarjeta)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(4)

        label_etiqueta = QLabel(etiqueta)
        label_etiqueta.setObjectName("etiquetaDetalleBarrio")
        label_valor = QLabel(valor)
        label_valor.setObjectName("valorDetalleBarrio")
        label_valor.setWordWrap(True)

        layout.addWidget(label_etiqueta)
        layout.addWidget(label_valor)
        return tarjeta

    def _crear_tarjeta_detalle(self, titulo: str, valor: str) -> QFrame:
        tarjeta = QFrame()
        tarjeta.setObjectName("tarjetaMiniDetalleBarrio")
        layout = QVBoxLayout(tarjeta)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(4)

        label_titulo = QLabel(titulo)
        label_titulo.setObjectName("etiquetaDetalleBarrio")
        label_valor = QLabel(valor)
        label_valor.setObjectName("valorTarjetaMiniDetalle")
        layout.addWidget(label_titulo)
        layout.addWidget(label_valor)
        return tarjeta

    def _mostrar_aviso_abonados(self) -> None:
        QMessageBox.information(
            self,
            "Ver abonados",
            "La navegacion hacia el modulo de abonados se integrara en el siguiente hito.",
        )

    def _mostrar_aviso_casas(self) -> None:
        QMessageBox.information(
            self,
            "Ver casas",
            "La navegacion hacia el modulo de casas se integrara en el siguiente hito.",
        )

    def _solicitar_edicion(self) -> None:
        self._accion_resultado = "editar"
        self.accept()

    def _aplicar_estilos(self) -> None:
        self.setStyleSheet(
            """
            QDialog {
                background: #1f2a44;
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 24px;
            }
            QLabel#tituloDialogoBarrio {
                color: #ffffff;
                font-size: 20px;
                font-weight: 900;
            }
            QLabel#descripcionDialogoBarrio {
                color: rgba(232, 239, 249, 0.80);
                font-size: 13px;
            }
            QFrame#bloqueDetalleBarrio,
            QFrame#campoDetalleBarrio,
            QFrame#campoDetalleBarrioAmplio,
            QFrame#tarjetaMiniDetalleBarrio {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 18px;
            }
            QLabel#codigoBarrioDetalle {
                color: #8ec9ff;
                font-size: 12px;
                font-weight: 800;
                letter-spacing: 0.08em;
            }
            QLabel#nombreBarrioDetalle {
                color: #ffffff;
                font-size: 22px;
                font-weight: 900;
            }
            QLabel#badgeDetalleBarrio {
                border-radius: 12px;
                padding: 8px 12px;
                font-size: 12px;
                font-weight: 800;
                color: #ffffff;
                background: rgba(160, 174, 192, 0.22);
                border: 1px solid rgba(255, 255, 255, 0.12);
            }
            QLabel#badgeDetalleBarrio[activo="true"] {
                color: #d9fff5;
                background: rgba(16, 120, 98, 0.24);
                border-color: rgba(158, 231, 214, 0.26);
            }
            QLabel#etiquetaDetalleBarrio {
                color: rgba(232, 239, 249, 0.72);
                font-size: 12px;
                font-weight: 700;
            }
            QLabel#valorDetalleBarrio {
                color: #f7fbff;
                font-size: 14px;
                font-weight: 700;
            }
            QLabel#valorTarjetaMiniDetalle {
                color: #ffffff;
                font-size: 24px;
                font-weight: 900;
            }
            """
        )


class DialogoConfirmacionEstadoBarrio(QDialog):
    """Modal de confirmacion para activar o inactivar barrios."""

    def __init__(self, barrio: Barrio, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._barrio = barrio
        self.setModal(True)
        self.setMinimumWidth(420)
        self.setWindowTitle("Confirmar cambio de estado")
        self._construir_ui()
        self._aplicar_estilos()

    def _construir_ui(self) -> None:
        nuevo_estado = "inactivar" if self._barrio.estado == "ACTIVO" else "activar"
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(16)

        titulo = QLabel("Confirmar cambio de estado")
        titulo.setObjectName("tituloDialogoBarrio")
        descripcion = QLabel(
            f"Estas a punto de {nuevo_estado} el barrio seleccionado. Verifica los datos antes de confirmar."
        )
        descripcion.setObjectName("descripcionDialogoBarrio")
        descripcion.setWordWrap(True)

        panel = QFrame()
        panel.setObjectName("bloqueConfirmacionBarrio")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(16, 16, 16, 16)
        panel_layout.setSpacing(8)

        for etiqueta, valor in (
            ("Barrio", self._barrio.nombre),
            ("Codigo", self._barrio.codigo),
            ("Estado actual", self._barrio.estado.title()),
            ("Accion", nuevo_estado.title()),
        ):
            fila = QHBoxLayout()
            fila.setSpacing(12)
            label_etiqueta = QLabel(etiqueta)
            label_etiqueta.setObjectName("etiquetaConfirmacionBarrio")
            label_valor = QLabel(valor)
            label_valor.setObjectName("valorConfirmacionBarrio")
            fila.addWidget(label_etiqueta, 1)
            fila.addWidget(label_valor, 2)
            panel_layout.addLayout(fila)

        fila_botones = QHBoxLayout()
        fila_botones.setSpacing(10)
        fila_botones.addStretch(1)
        boton_cancelar = crear_boton_operativo("Cancelar")
        boton_confirmar = crear_boton_operativo("Confirmar", principal=True)
        boton_cancelar.clicked.connect(self.reject)
        boton_confirmar.clicked.connect(self.accept)
        fila_botones.addWidget(boton_cancelar)
        fila_botones.addWidget(boton_confirmar)

        layout.addWidget(titulo)
        layout.addWidget(descripcion)
        layout.addWidget(panel)
        layout.addLayout(fila_botones)

    def _aplicar_estilos(self) -> None:
        self.setStyleSheet(
            """
            QDialog {
                background: #1f2a44;
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 24px;
            }
            QLabel#tituloDialogoBarrio {
                color: #ffffff;
                font-size: 20px;
                font-weight: 900;
            }
            QLabel#descripcionDialogoBarrio {
                color: rgba(232, 239, 249, 0.80);
                font-size: 13px;
            }
            QFrame#bloqueConfirmacionBarrio {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 18px;
            }
            QLabel#etiquetaConfirmacionBarrio {
                color: rgba(232, 239, 249, 0.72);
                font-size: 12px;
                font-weight: 700;
            }
            QLabel#valorConfirmacionBarrio {
                color: #ffffff;
                font-size: 14px;
                font-weight: 800;
            }
            """
        )


class VistaBarrios(QWidget):
    """Pantalla principal del modulo de barrios."""

    filtro_texto_cambiado = Signal(str)
    filtro_rapido_cambiado = Signal(str)
    pagina_cambiada = Signal(int)
    exportar_solicitado = Signal()
    nuevo_barrio_solicitado = Signal()
    detalle_barrio_solicitado = Signal(int)
    editar_barrio_solicitado = Signal(int)
    cambio_estado_solicitado = Signal(int)

    def __init__(self) -> None:
        super().__init__()
        self._pagina_actual = 1
        self._total_paginas = 1
        self._construir_ui()
        self._aplicar_estilos()

    def mostrar_resumen(self, resumen: ResumenBarrios) -> None:
        self._tarjeta_total.actualizar(
            "Total de barrios",
            str(resumen.total_barrios),
            "Cobertura territorial registrada.",
        )
        self._tarjeta_activos.actualizar(
            "Barrios activos",
            str(resumen.barrios_activos),
            "Disponibles para operacion diaria.",
        )
        self._tarjeta_con_abonados.actualizar(
            "Barrios con abonados",
            str(resumen.barrios_con_abonados),
            "Zonas con relacion operativa vigente.",
        )
        detalle_destacado = (
            f"{resumen.cantidad_maxima_abonados} abonados registrados"
            if resumen.cantidad_maxima_abonados > 0
            else "Sin abonados vinculados"
        )
        self._tarjeta_destacado.actualizar(
            "Barrio con mas abonados",
            resumen.barrio_con_mas_abonados,
            detalle_destacado,
        )

    def mostrar_barrios(
        self,
        pagina: PaginaBarrios,
        formateador_fecha: Callable[[str], str],
    ) -> None:
        self._pagina_actual = pagina.pagina_actual
        self._total_paginas = pagina.total_paginas
        self._tabla.setRowCount(0)

        for barrio in pagina.items:
            fila = self._tabla.rowCount()
            self._tabla.insertRow(fila)
            self._tabla.setItem(fila, 0, crear_item_tabla(barrio.codigo))
            self._tabla.setItem(fila, 1, crear_item_tabla(barrio.nombre))
            self._tabla.setItem(fila, 2, crear_item_tabla(barrio.total_abonados))
            self._tabla.setItem(fila, 3, crear_item_tabla(barrio.total_casas))
            self._tabla.setCellWidget(fila, 4, self._crear_badge_estado(barrio.estado))
            self._tabla.setItem(fila, 5, crear_item_tabla(formateador_fecha(barrio.actualizado_en)))
            self._tabla.setCellWidget(fila, 6, self._crear_acciones_fila(barrio))

        self._tabla.resizeRowsToContents()
        self._actualizar_estado_vacio(pagina.total_registros == 0)
        self._label_paginacion.setText(
            f"Mostrando {pagina.indice_inicio}-{pagina.indice_fin} de {pagina.total_registros} barrios"
        )
        self._label_numero_pagina.setText(
            f"Pagina {self._pagina_actual} de {self._total_paginas}"
        )
        self._boton_pagina_anterior.setEnabled(self._pagina_actual > 1)
        self._boton_pagina_siguiente.setEnabled(self._pagina_actual < self._total_paginas)

    def mostrar_mensaje(self, mensaje: str, es_error: bool = False) -> None:
        self._mensaje.setText(mensaje)
        self._mensaje.setVisible(bool(mensaje))
        self._mensaje.setProperty("error", es_error)
        self._mensaje.style().unpolish(self._mensaje)
        self._mensaje.style().polish(self._mensaje)

    def solicitar_datos_barrio(self, barrio: Barrio | None = None) -> FormularioBarrio | None:
        dialogo = DialogoFormularioBarrio(barrio=barrio, parent=self)
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return None
        return dialogo.obtener_formulario()

    def mostrar_detalle_barrio(self, barrio: Barrio, fecha_actualizada: str) -> str:
        dialogo = DialogoDetalleBarrio(barrio=barrio, fecha_actualizada=fecha_actualizada, parent=self)
        dialogo.exec()
        return dialogo.accion_resultado

    def confirmar_cambio_estado_barrio(self, barrio: Barrio) -> bool:
        dialogo = DialogoConfirmacionEstadoBarrio(barrio=barrio, parent=self)
        return dialogo.exec() == QDialog.DialogCode.Accepted

    def solicitar_ruta_exportacion(self) -> str:
        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar barrios",
            "barrios.csv",
            "Archivos CSV (*.csv)",
        )
        return ruta

    def _construir_ui(self) -> None:
        self.setObjectName("vistaBarrios")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(16)

        encabezado = QHBoxLayout()
        encabezado.setSpacing(12)
        bloque_titulo = QVBoxLayout()
        bloque_titulo.setSpacing(4)
        titulo = QLabel("Barrios")
        titulo.setObjectName("tituloModulo")
        descripcion = QLabel("Gestion de barrios y organizacion territorial")
        descripcion.setObjectName("descripcionModulo")
        descripcion.setWordWrap(True)
        bloque_titulo.addWidget(titulo)
        bloque_titulo.addWidget(descripcion)

        fila_acciones = QHBoxLayout()
        fila_acciones.setSpacing(10)
        fila_acciones.addStretch(1)
        boton_exportar = crear_boton_operativo("Exportar")
        boton_nuevo = crear_boton_operativo("Nuevo barrio", principal=True)
        boton_exportar.clicked.connect(self.exportar_solicitado.emit)
        boton_nuevo.clicked.connect(self.nuevo_barrio_solicitado.emit)
        fila_acciones.addWidget(boton_exportar)
        fila_acciones.addWidget(boton_nuevo)

        encabezado.addLayout(bloque_titulo, 1)
        encabezado.addLayout(fila_acciones)

        self._mensaje = QLabel("")
        self._mensaje.setObjectName("mensajeBarrios")
        self._mensaje.setVisible(False)
        self._mensaje.setWordWrap(True)

        fila_tarjetas = QGridLayout()
        fila_tarjetas.setHorizontalSpacing(14)
        fila_tarjetas.setVerticalSpacing(14)
        self._tarjeta_total = TarjetaResumenBarrio("map-pin.svg", "#8ec9ff")
        self._tarjeta_activos = TarjetaResumenBarrio("circle-check.svg", "#8de8c7")
        self._tarjeta_con_abonados = TarjetaResumenBarrio("user.svg", "#f7cc7a")
        self._tarjeta_destacado = TarjetaResumenBarrio("home.svg", "#c6b6ff")
        fila_tarjetas.addWidget(self._tarjeta_total, 0, 0)
        fila_tarjetas.addWidget(self._tarjeta_activos, 0, 1)
        fila_tarjetas.addWidget(self._tarjeta_con_abonados, 0, 2)
        fila_tarjetas.addWidget(self._tarjeta_destacado, 0, 3)

        panel_filtros = QFrame()
        panel_filtros.setObjectName("panelOperativoBarrios")
        layout_filtros = QVBoxLayout(panel_filtros)
        layout_filtros.setContentsMargins(18, 18, 18, 18)
        layout_filtros.setSpacing(12)

        self._campo_busqueda = QLineEdit()
        self._campo_busqueda.setPlaceholderText("Buscar barrio")
        self._campo_busqueda.textChanged.connect(self.filtro_texto_cambiado.emit)

        fila_chips = QHBoxLayout()
        fila_chips.setSpacing(8)
        self._grupo_filtros = QButtonGroup(self)
        self._grupo_filtros.setExclusive(True)
        self._botones_filtros: dict[str, QPushButton] = {}
        for codigo, texto in (
            (FILTRO_BARRIOS_TODOS, "Todos"),
            (FILTRO_BARRIOS_CON_ABONADOS, "Con abonados"),
            (FILTRO_BARRIOS_SIN_ABONADOS, "Sin abonados"),
        ):
            boton = QPushButton(texto)
            boton.setObjectName("chipFiltroBarrio")
            boton.setCheckable(True)
            boton.setCursor(Qt.CursorShape.PointingHandCursor)
            boton.clicked.connect(
                lambda checked=False, valor=codigo: self.filtro_rapido_cambiado.emit(valor)
            )
            self._grupo_filtros.addButton(boton)
            self._botones_filtros[codigo] = boton
            fila_chips.addWidget(boton)
        self._botones_filtros[FILTRO_BARRIOS_TODOS].setChecked(True)
        fila_chips.addStretch(1)

        layout_filtros.addWidget(self._campo_busqueda)
        layout_filtros.addLayout(fila_chips)

        panel_tabla = QFrame()
        panel_tabla.setObjectName("panelOperativoBarrios")
        layout_tabla = QVBoxLayout(panel_tabla)
        layout_tabla.setContentsMargins(18, 18, 18, 18)
        layout_tabla.setSpacing(12)

        self._tabla = QTableWidget(0, 7)
        configurar_tabla_operativa(
            self._tabla,
            [
                "Codigo",
                "Barrio",
                "Abonados",
                "Casas",
                "Estado",
                "Ultima actualizacion",
                "Acciones",
            ],
        )
        self._tabla.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self._tabla.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self._tabla.verticalHeader().setDefaultSectionSize(54)

        self._estado_vacio = QLabel("No hay barrios que coincidan con los filtros actuales.")
        self._estado_vacio.setObjectName("estadoVacioBarrios")
        self._estado_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._estado_vacio.setVisible(False)

        pie_tabla = QHBoxLayout()
        pie_tabla.setSpacing(10)
        self._label_paginacion = QLabel("Mostrando 0-0 de 0 barrios")
        self._label_paginacion.setObjectName("textoPieBarrios")
        pie_tabla.addWidget(self._label_paginacion)
        pie_tabla.addStretch(1)

        self._boton_pagina_anterior = crear_boton_operativo("Anterior")
        self._boton_pagina_siguiente = crear_boton_operativo("Siguiente")
        self._boton_pagina_anterior.clicked.connect(
            lambda: self.pagina_cambiada.emit(max(1, self._pagina_actual - 1))
        )
        self._boton_pagina_siguiente.clicked.connect(
            lambda: self.pagina_cambiada.emit(self._pagina_actual + 1)
        )
        self._label_numero_pagina = QLabel("Pagina 1 de 1")
        self._label_numero_pagina.setObjectName("textoPieBarrios")
        pie_tabla.addWidget(self._boton_pagina_anterior)
        pie_tabla.addWidget(self._label_numero_pagina)
        pie_tabla.addWidget(self._boton_pagina_siguiente)

        layout_tabla.addWidget(self._tabla)
        layout_tabla.addWidget(self._estado_vacio)
        layout_tabla.addLayout(pie_tabla)

        layout.addLayout(encabezado)
        layout.addWidget(self._mensaje)
        layout.addLayout(fila_tarjetas)
        layout.addWidget(panel_filtros)
        layout.addWidget(panel_tabla, 1)

    def _crear_badge_estado(self, estado: str) -> QWidget:
        contenedor = QWidget()
        layout = QHBoxLayout(contenedor)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        badge = QLabel(estado.title())
        badge.setObjectName("badgeEstadoBarrio")
        badge.setProperty("activo", estado == "ACTIVO")
        badge.style().unpolish(badge)
        badge.style().polish(badge)
        layout.addWidget(badge, alignment=Qt.AlignmentFlag.AlignCenter)
        return contenedor

    def _crear_acciones_fila(self, barrio: Barrio) -> QWidget:
        contenedor = QWidget()
        layout = QHBoxLayout(contenedor)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        boton_ver = QPushButton("Ver detalle")
        boton_editar = QPushButton("Editar")
        boton_estado = QPushButton("Inactivar" if barrio.estado == "ACTIVO" else "Activar")
        for boton in (boton_ver, boton_editar, boton_estado):
            boton.setObjectName("botonFilaBarrio")
            boton.setCursor(Qt.CursorShape.PointingHandCursor)
            boton.setMinimumHeight(30)

        boton_ver.clicked.connect(
            lambda checked=False, identificador=barrio.identificador: self.detalle_barrio_solicitado.emit(
                int(identificador or 0)
            )
        )
        boton_editar.clicked.connect(
            lambda checked=False, identificador=barrio.identificador: self.editar_barrio_solicitado.emit(
                int(identificador or 0)
            )
        )
        boton_estado.clicked.connect(
            lambda checked=False, identificador=barrio.identificador: self.cambio_estado_solicitado.emit(
                int(identificador or 0)
            )
        )

        layout.addWidget(boton_ver)
        layout.addWidget(boton_editar)
        layout.addWidget(boton_estado)
        return contenedor

    def _actualizar_estado_vacio(self, sin_datos: bool) -> None:
        self._estado_vacio.setVisible(sin_datos)
        self._tabla.setVisible(not sin_datos)

    def _aplicar_estilos(self) -> None:
        self.setStyleSheet(
            """
            QWidget#vistaBarrios {
                background: transparent;
            }
            QLabel#tituloModulo {
                color: #ffffff;
                font-size: 23px;
                font-weight: 900;
            }
            QLabel#descripcionModulo,
            QLabel#textoPieBarrios,
            QLabel#detalleTarjetaResumen {
                color: rgba(235, 242, 248, 0.76);
                font-size: 12px;
                font-weight: 600;
            }
            QLabel#mensajeBarrios {
                color: #d9fff5;
                font-size: 13px;
                font-weight: 700;
                padding: 10px 12px;
                border-radius: 14px;
                background-color: rgba(16, 120, 98, 0.16);
                border: 1px solid rgba(158, 231, 214, 0.26);
            }
            QLabel#mensajeBarrios[error="true"] {
                color: #ffd4cf;
                background-color: rgba(180, 35, 24, 0.15);
                border: 1px solid rgba(255, 205, 199, 0.28);
            }
            QFrame#panelOperativoBarrios,
            QFrame#tarjetaResumenBarrios {
                background: rgba(255, 255, 255, 0.10);
                border: 1px solid rgba(255, 255, 255, 0.16);
                border-radius: 22px;
            }
            QLabel#iconoTarjetaResumen {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 14px;
            }
            QLabel#tituloTarjetaResumen {
                color: rgba(235, 242, 248, 0.72);
                font-size: 12px;
                font-weight: 700;
            }
            QLabel#valorTarjetaResumen {
                color: #ffffff;
                font-size: 24px;
                font-weight: 900;
            }
            QLineEdit {
                min-height: 42px;
                border: 1px solid rgba(255, 255, 255, 0.18);
                border-radius: 14px;
                background: rgba(255, 255, 255, 0.11);
                color: #f5fbff;
                padding: 0 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: rgba(109, 241, 220, 0.42);
                background: rgba(255, 255, 255, 0.16);
            }
            QPushButton#chipFiltroBarrio {
                min-height: 34px;
                border-radius: 12px;
                padding: 0 14px;
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.14);
                color: #ecf5ff;
                font-size: 12px;
                font-weight: 700;
            }
            QPushButton#chipFiltroBarrio:hover {
                background: rgba(255, 255, 255, 0.12);
            }
            QPushButton#chipFiltroBarrio:checked {
                color: #0f2d43;
                background: #d2f4f2;
                border-color: rgba(255, 255, 255, 0.18);
            }
            QLabel#badgeEstadoBarrio {
                border-radius: 12px;
                padding: 7px 12px;
                font-size: 12px;
                font-weight: 800;
                color: #f4f8fb;
                background: rgba(132, 146, 166, 0.22);
                border: 1px solid rgba(255, 255, 255, 0.12);
            }
            QLabel#badgeEstadoBarrio[activo="true"] {
                color: #d9fff5;
                background: rgba(16, 120, 98, 0.22);
                border-color: rgba(158, 231, 214, 0.26);
            }
            QPushButton#botonFilaBarrio {
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 0.14);
                background: rgba(255, 255, 255, 0.10);
                color: #f7fbff;
                padding: 0 10px;
                font-size: 12px;
                font-weight: 700;
            }
            QPushButton#botonFilaBarrio:hover {
                background: rgba(255, 255, 255, 0.16);
            }
            QLabel#estadoVacioBarrios {
                color: rgba(235, 242, 248, 0.76);
                font-size: 13px;
                font-weight: 700;
                padding: 24px 16px;
            }
            QLabel {
                color: #f4fbff;
            }
            """
        )
