"""Vista del modulo tecnico de mantenimiento."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from modulos.mantenimiento.entidades import EstadoMantenimiento


class VistaMantenimiento(QWidget):
    """Muestra un panel tecnico reservado para superadministrador."""

    volver_solicitado = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("vistaMantenimiento")
        self.setStyleSheet(
            """
            QWidget#vistaMantenimiento {
                background-color: #f5f7fb;
            }
            QLabel#tituloMantenimiento {
                color: #10233d;
                font-size: 28px;
                font-weight: 700;
            }
            QLabel#textoMantenimiento {
                color: #4a6279;
                font-size: 14px;
            }
            QLabel#avisoMantenimiento {
                color: #9a6400;
                background-color: #fff6df;
                border: 1px solid #f2d18b;
                border-radius: 14px;
                padding: 14px 16px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton {
                min-height: 42px;
                border: 1px solid #c9d7e5;
                border-radius: 14px;
                background-color: #ffffff;
                color: #17324d;
                font-size: 13px;
                font-weight: 600;
                padding: 0 14px;
            }
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 40, 48, 40)
        layout.setSpacing(16)

        titulo = QLabel("Modulo de mantenimiento tecnico")
        titulo.setObjectName("tituloMantenimiento")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        descripcion = QLabel(
            "Acceso reservado para SUPERADMINISTRADOR. Aqui se preparan tareas de "
            "diagnostico, respaldo, restauracion y revision de logs."
        )
        descripcion.setObjectName("textoMantenimiento")
        descripcion.setWordWrap(True)
        descripcion.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._label_resumen = QLabel()
        self._label_resumen.setObjectName("textoMantenimiento")
        self._label_resumen.setWordWrap(True)
        self._label_resumen.setAlignment(Qt.AlignmentFlag.AlignCenter)

        aviso = QLabel("Aviso: este modulo aun esta en desarrollo.")
        aviso.setObjectName("avisoMantenimiento")
        aviso.setWordWrap(True)
        aviso.setAlignment(Qt.AlignmentFlag.AlignCenter)

        boton_volver = QPushButton("Volver al modulo principal")
        boton_volver.clicked.connect(self.volver_solicitado.emit)

        layout.addStretch(1)
        layout.addWidget(titulo)
        layout.addWidget(descripcion)
        layout.addWidget(self._label_resumen)
        layout.addWidget(aviso)
        layout.addWidget(boton_volver, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch(1)

    def mostrar_estado(self, estado: EstadoMantenimiento) -> None:
        self._label_resumen.setText(
            "Respaldos registrados: {0}\n"
            "Eventos tecnicos: {1}\n"
            "Ultimo evento: {2}".format(
                estado.total_respaldos,
                estado.total_eventos_tecnicos,
                estado.ultimo_evento,
            )
        )

