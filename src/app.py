"""Composition root de SICAP para el flujo inicial de autenticacion."""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox

from apis.resend.cliente_resend import ClienteResend
from apis.resend.servicio_correo_resend import ServicioCorreoResend
from comun.base_datos import GestorBaseDatos
from comun.configuracion.gestor_rutas import GestorRutas
from modulos.autenticacion import (
    ControladorAutenticacion,
    RepositorioAutenticacionSQLite,
    ServicioAutenticacion,
    VistaAutenticacion,
)


def crear_ventana_principal(
    gestor_rutas: GestorRutas | None = None,
) -> tuple[QApplication, QMainWindow, VistaAutenticacion]:
    """Construye la aplicacion y la ventana principal sin iniciar el loop."""
    gestor_rutas = gestor_rutas or GestorRutas()
    load_dotenv(gestor_rutas.obtener_ruta_env(), override=False)

    aplicacion = QApplication.instance() or QApplication(sys.argv)
    aplicacion.setApplicationName("SICAP")

    ruta_icono = gestor_rutas.obtener_ruta_icono_aplicacion()
    if ruta_icono.exists():
        icono = QIcon(str(ruta_icono))
        aplicacion.setWindowIcon(icono)
    else:
        icono = QIcon()

    gestor_base_datos = GestorBaseDatos(gestor_rutas=gestor_rutas)
    gestor_base_datos.inicializar_base_datos()

    cliente_resend = ClienteResend(os.getenv("RESEND_API_KEY", ""))
    servicio_correo = ServicioCorreoResend(
        cliente_resend=cliente_resend,
        correo_remitente=os.getenv("CORREO_REMITENTE", "no-reply@sicap.local"),
    )

    repositorio_autenticacion = RepositorioAutenticacionSQLite(gestor_base_datos)
    servicio_autenticacion = ServicioAutenticacion(
        repositorio_autenticacion=repositorio_autenticacion,
        proveedor_correo=servicio_correo,
        entorno=os.getenv("APP_ENV", "desarrollo"),
    )
    servicio_autenticacion.asegurar_usuario_admin_desarrollo()

    vista_autenticacion = VistaAutenticacion(gestor_rutas=gestor_rutas)
    ventana_principal = QMainWindow()
    ventana_principal.setWindowTitle("SICAP | Autenticacion")
    ventana_principal.setCentralWidget(vista_autenticacion)
    ventana_principal.resize(1366, 900)
    if not icono.isNull():
        ventana_principal.setWindowIcon(icono)

    controlador = ControladorAutenticacion(
        servicio_autenticacion=servicio_autenticacion,
        vista_autenticacion=vista_autenticacion,
    )
    vista_autenticacion.autenticacion_exitosa.connect(
        lambda usuario: _manejar_autenticacion_exitosa(
            ventana_principal,
            vista_autenticacion,
            usuario.nombre_completo,
        )
    )

    ventana_principal.controlador_autenticacion = controlador
    ventana_principal.servicio_autenticacion = servicio_autenticacion
    ventana_principal.vista_autenticacion = vista_autenticacion
    return aplicacion, ventana_principal, vista_autenticacion


def iniciar_aplicacion() -> int:
    """Inicia la aplicacion de escritorio mostrando autenticacion maximizada."""
    aplicacion, ventana_principal, _ = crear_ventana_principal()
    ventana_principal.showMaximized()
    return aplicacion.exec()


def _manejar_autenticacion_exitosa(
    ventana_principal: QMainWindow,
    vista_autenticacion: VistaAutenticacion,
    nombre_completo: str,
) -> None:
    """Resuelve temporalmente el post-login mientras el shell principal no existe."""
    QMessageBox.information(
        ventana_principal,
        "Autenticacion correcta",
        (
            f"Bienvenido, {nombre_completo}. "
            "La apertura del modulo principal se integrara en una fase posterior."
        ),
    )
    vista_autenticacion.mostrar_login(
        mensaje="Autenticacion correcta. El modulo principal se integrara despues.",
        es_exito=True,
    )
