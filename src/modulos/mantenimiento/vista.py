"""Vista del modulo tecnico de mantenimiento."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from comun.ui.temas import TEMA_SICAP_PREDETERMINADO, obtener_paleta_tema

from modulos.mantenimiento.entidades import EstadoMantenimiento


class VistaMantenimiento(QWidget):
    """Muestra un panel tecnico reservado para superadministrador."""

    volver_solicitado = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._tema_actual = TEMA_SICAP_PREDETERMINADO
        self._paleta_tema = obtener_paleta_tema(self._tema_actual)
        self.setObjectName("vistaMantenimiento")
        self._aplicar_estilos()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(0)

        layout.addStretch(1)

        tarjeta = QFrame()
        tarjeta.setObjectName("tarjetaMantenimiento")
        tarjeta.setMaximumWidth(780)
        tarjeta.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        tarjeta_layout = QVBoxLayout(tarjeta)
        tarjeta_layout.setContentsMargins(32, 30, 32, 30)
        tarjeta_layout.setSpacing(16)

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

        tarjeta_layout.addWidget(titulo)
        tarjeta_layout.addWidget(descripcion)
        tarjeta_layout.addWidget(self._label_resumen)
        tarjeta_layout.addWidget(aviso)
        tarjeta_layout.addWidget(boton_volver, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(tarjeta, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch(1)

    def aplicar_tema(self, nombre_tema: str) -> None:
        self._tema_actual = nombre_tema if nombre_tema in ("oscuro", "claro") else TEMA_SICAP_PREDETERMINADO
        self._paleta_tema = obtener_paleta_tema(self._tema_actual)
        self._aplicar_estilos()

    def _aplicar_estilos(self) -> None:
        paleta = self._paleta_tema
        self.setStyleSheet(
            f"""
            QWidget#vistaMantenimiento {{
                background: transparent;
            }}
            QFrame#tarjetaMantenimiento {{
                background: {paleta["fondo_superficie"]};
                border: 1px solid {paleta["borde_principal"]};
                border-radius: 24px;
            }}
            QLabel#tituloMantenimiento {{
                color: {paleta["texto_principal"]};
                font-size: 25px;
                font-weight: 800;
            }}
            QLabel#textoMantenimiento {{
                color: {paleta["texto_secundario"]};
                font-size: 14px;
            }}
            QLabel#avisoMantenimiento {{
                color: {paleta["texto_advertencia"]};
                background-color: {paleta["fondo_advertencia"]};
                border: 1px solid {paleta["borde_advertencia"]};
                border-radius: 14px;
                padding: 14px 16px;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton {{
                min-height: 42px;
                border: 1px solid {paleta["borde_medio"]};
                border-radius: 14px;
                background-color: {paleta["fondo_input"]};
                color: {paleta["texto_input"]};
                font-size: 13px;
                font-weight: 700;
                padding: 0 14px;
            }}
            QPushButton:hover {{
                background-color: {paleta["fondo_superficie"]};
                border-color: {paleta["borde_principal"]};
            }}
            """
        )

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

    def sizeHint(self) -> QSize:
        return QSize(780, 420)

    def minimumSizeHint(self) -> QSize:
        return QSize(620, 360)
