"""Composition root de SICAP para el flujo inicial de autenticacion."""

from __future__ import annotations

import sys

from dotenv import load_dotenv
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMainWindow, QSizePolicy

from comun.base_datos import GestorBaseDatos
from comun.configuracion.gestor_rutas import GestorRutas
from comun.logs import obtener_logger_sicap
from comun.sesion import SesionAplicacion
from comun.ui import ContenedorApiladoAjustable
from modulos.autenticacion import (
    ControladorAutenticacion,
    SesionIniciada,
    RepositorioAutenticacionSQLite,
    ServicioAutenticacion,
    VistaAutenticacion,
)
from modulos.mantenimiento import (
    ControladorMantenimiento,
    RepositorioMantenimientoSQLite,
    ServicioMantenimiento,
    VistaMantenimiento,
)
from modulos.principal import (
    ControladorModuloPrincipal,
    RepositorioModuloPrincipalMemoria,
    ServicioModuloPrincipal,
    VistaModuloPrincipal,
)
from modulos.usuarios.repositorio import RepositorioUsuariosSQLite
from modulos.usuarios.servicio import ServicioUsuarios

logger = obtener_logger_sicap("app")
ANCHO_VENTANA_AUTENTICACION = 760
ALTO_VENTANA_AUTENTICACION = 680
MAXIMO_TAMANO_VENTANA = 16777215
FLAGS_VENTANA_AUTENTICACION = (
    Qt.WindowType.Window
    | Qt.WindowType.WindowTitleHint
    | Qt.WindowType.WindowSystemMenuHint
    | Qt.WindowType.WindowMinimizeButtonHint
    | Qt.WindowType.WindowCloseButtonHint
)
FLAGS_VENTANA_PRINCIPAL = (
    Qt.WindowType.Window
    | Qt.WindowType.WindowTitleHint
    | Qt.WindowType.WindowSystemMenuHint
    | Qt.WindowType.WindowMinimizeButtonHint
    | Qt.WindowType.WindowMaximizeButtonHint
    | Qt.WindowType.WindowCloseButtonHint
)


def crear_ventana_principal(
    gestor_rutas: GestorRutas | None = None,
) -> tuple[QApplication, QMainWindow, VistaAutenticacion]:
    """Construye la aplicacion y la ventana principal sin iniciar el loop."""
    gestor_rutas = gestor_rutas or GestorRutas()
    load_dotenv(gestor_rutas.obtener_ruta_env(), override=False)
    logger.info("Iniciando composition root de SICAP.")

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
    logger.info("Base de datos inicializada en %s", gestor_rutas.obtener_ruta_base_datos())

    repositorio_autenticacion = RepositorioAutenticacionSQLite(gestor_base_datos)
    servicio_autenticacion = ServicioAutenticacion(
        repositorio_autenticacion=repositorio_autenticacion,
    )
    servicio_autenticacion.asegurar_usuario_admin_desarrollo()
    repositorio_usuarios = RepositorioUsuariosSQLite(gestor_base_datos)
    servicio_usuarios = ServicioUsuarios(repositorio_usuarios)
    repositorio_mantenimiento = RepositorioMantenimientoSQLite(gestor_base_datos)
    servicio_mantenimiento = ServicioMantenimiento(repositorio_mantenimiento)

    vista_autenticacion = VistaAutenticacion(gestor_rutas=gestor_rutas)
    contenedor_central = ContenedorApiladoAjustable()
    contenedor_central.setSizePolicy(
        QSizePolicy.Policy.Expanding,
        QSizePolicy.Policy.Expanding,
    )
    contenedor_central.setMinimumSize(0, 0)
    contenedor_central.addWidget(vista_autenticacion)

    ventana_principal = QMainWindow()
    ventana_principal.setWindowTitle("SICAP | Autenticacion")
    ventana_principal.setCentralWidget(contenedor_central)
    _aplicar_modo_autenticacion(ventana_principal)
    if not icono.isNull():
        ventana_principal.setWindowIcon(icono)

    controlador = ControladorAutenticacion(
        servicio_autenticacion=servicio_autenticacion,
        vista_autenticacion=vista_autenticacion,
    )
    vista_autenticacion.autenticacion_exitosa.connect(
        lambda sesion_iniciada: _manejar_autenticacion_exitosa(
            ventana_principal,
            servicio_autenticacion,
            sesion_iniciada,
        )
    )

    ventana_principal.sesion_activa = None
    ventana_principal.contenedor_central = contenedor_central
    ventana_principal.controlador_autenticacion = controlador
    ventana_principal.servicio_autenticacion = servicio_autenticacion
    ventana_principal.servicio_usuarios = servicio_usuarios
    ventana_principal.servicio_mantenimiento = servicio_mantenimiento
    ventana_principal.vista_autenticacion = vista_autenticacion
    logger.info("Ventana principal lista y mostrando autenticacion.")
    return aplicacion, ventana_principal, vista_autenticacion


def iniciar_aplicacion() -> int:
    """Inicia la aplicacion mostrando el login en tamano fijo."""
    aplicacion, ventana_principal, _ = crear_ventana_principal()
    ventana_principal.show()
    _centrar_ventana_en_pantalla(ventana_principal)
    logger.info("Aplicacion iniciada en modo autenticacion fija.")
    return aplicacion.exec()


def _manejar_autenticacion_exitosa(
    ventana_principal: QMainWindow,
    servicio_autenticacion: ServicioAutenticacion,
    sesion_iniciada: SesionIniciada,
) -> None:
    """Abre el modulo principal provisional tras autenticacion exitosa."""
    if sesion_iniciada.usuario.requiere_cambio_contrasena:
        logger.info(
            "Usuario '%s' debe completar cambio obligatorio de contrasena.",
            sesion_iniciada.usuario.nombre_usuario,
        )
        ventana_principal.controlador_autenticacion.abrir_restablecimiento_administrativo(
            sesion_iniciada.usuario.nombre_usuario,
            "Debes cambiar tu contrasena antes de continuar.",
        )
        return

    ventana_principal.sesion_activa = SesionAplicacion(
        usuario=sesion_iniciada.usuario,
        token_sesion=sesion_iniciada.token_sesion,
    )

    logger.info(
        "Autenticacion exitosa para '%s'. Abriendo modulo principal.",
        sesion_iniciada.usuario.nombre_usuario,
    )

    if not hasattr(ventana_principal, "vista_modulo_principal"):
        vista_modulo_principal = VistaModuloPrincipal()
        servicio_modulo_principal = ServicioModuloPrincipal(
            RepositorioModuloPrincipalMemoria(),
        )
        controlador_modulo_principal = ControladorModuloPrincipal(
            servicio_modulo_principal=servicio_modulo_principal,
            vista_modulo_principal=vista_modulo_principal,
        )
        controlador_modulo_principal.configurar_callback_cierre_sesion(
            lambda: _manejar_cierre_sesion(
                ventana_principal=ventana_principal,
                servicio_autenticacion=servicio_autenticacion,
            )
        )
        controlador_modulo_principal.configurar_callback_apertura_mantenimiento(
            lambda: _manejar_apertura_mantenimiento(ventana_principal)
        )
        ventana_principal.contenedor_central.addWidget(vista_modulo_principal)
        ventana_principal.vista_modulo_principal = vista_modulo_principal
        ventana_principal.controlador_modulo_principal = controlador_modulo_principal
        ventana_principal.servicio_modulo_principal = servicio_modulo_principal

    if (
        sesion_iniciada.usuario.tiene_permiso("mantenimiento.ver")
        and not hasattr(ventana_principal, "vista_mantenimiento")
    ):
        vista_mantenimiento = VistaMantenimiento()
        controlador_mantenimiento = ControladorMantenimiento(
            servicio_mantenimiento=ventana_principal.servicio_mantenimiento,
            vista_mantenimiento=vista_mantenimiento,
        )
        controlador_mantenimiento.configurar_callback_volver(
            lambda: _manejar_retorno_desde_mantenimiento(ventana_principal)
        )
        ventana_principal.contenedor_central.addWidget(vista_mantenimiento)
        ventana_principal.vista_mantenimiento = vista_mantenimiento
        ventana_principal.controlador_mantenimiento = controlador_mantenimiento

    controlador_modulo_principal = ventana_principal.controlador_modulo_principal
    vista_modulo_principal = ventana_principal.vista_modulo_principal
    controlador_modulo_principal.mostrar_inicio(sesion_iniciada.usuario)
    ventana_principal.setWindowTitle("SICAP | Modulo principal")
    ventana_principal.contenedor_central.setCurrentWidget(vista_modulo_principal)
    _aplicar_modo_principal(ventana_principal)


def _manejar_cierre_sesion(
    ventana_principal: QMainWindow,
    servicio_autenticacion: ServicioAutenticacion,
) -> None:
    """Cierra la sesion activa y retorna al login."""
    sesion_activa = getattr(ventana_principal, "sesion_activa", None)
    if sesion_activa is not None:
        resultado_cierre = servicio_autenticacion.cerrar_sesion(sesion_activa.token_sesion)
        if resultado_cierre.exito:
            logger.info(
                "Sesion cerrada para '%s'.",
                sesion_activa.usuario.nombre_usuario,
            )
        else:
            logger.warning("No fue posible cerrar la sesion activa: %s", resultado_cierre.mensaje)
    else:
        logger.info("Se solicito cierre de sesion sin una sesion activa en memoria.")

    ventana_principal.sesion_activa = None
    vista_autenticacion = ventana_principal.vista_autenticacion
    ventana_principal.setWindowTitle("SICAP | Autenticacion")
    ventana_principal.contenedor_central.setCurrentWidget(vista_autenticacion)
    vista_autenticacion.mostrar_login(
        mensaje="Sesion cerrada correctamente.",
        es_exito=True,
    )
    _aplicar_modo_autenticacion(ventana_principal)
    logger.info("Se regreso al flujo de autenticacion.")


def _manejar_apertura_mantenimiento(ventana_principal: QMainWindow) -> None:
    """Abre el panel tecnico si la sesion actual tiene permisos."""
    sesion_activa = getattr(ventana_principal, "sesion_activa", None)
    if sesion_activa is None or not sesion_activa.usuario.tiene_permiso("mantenimiento.ver"):
        logger.warning("Se intento abrir mantenimiento sin permisos suficientes.")
        return

    if not hasattr(ventana_principal, "controlador_mantenimiento"):
        logger.warning("No existe un controlador de mantenimiento inicializado.")
        return

    ventana_principal.controlador_mantenimiento.mostrar_panel()
    ventana_principal.setWindowTitle("SICAP | Mantenimiento tecnico")
    ventana_principal.contenedor_central.setCurrentWidget(ventana_principal.vista_mantenimiento)
    _aplicar_modo_principal(ventana_principal)


def _manejar_retorno_desde_mantenimiento(ventana_principal: QMainWindow) -> None:
    """Regresa del mantenimiento tecnico al modulo principal."""
    if hasattr(ventana_principal, "vista_modulo_principal"):
        ventana_principal.setWindowTitle("SICAP | Modulo principal")
        ventana_principal.contenedor_central.setCurrentWidget(
            ventana_principal.vista_modulo_principal
        )
        _aplicar_modo_principal(ventana_principal)


def _aplicar_modo_autenticacion(ventana_principal: QMainWindow) -> None:
    """Aplica un tamano fijo al login para evitar deformaciones al volver."""
    estaba_visible = ventana_principal.isVisible()
    ventana_principal.showNormal()
    ventana_principal.setWindowFlags(FLAGS_VENTANA_AUTENTICACION)
    ventana_principal.setMinimumSize(
        ANCHO_VENTANA_AUTENTICACION,
        ALTO_VENTANA_AUTENTICACION,
    )
    ventana_principal.setMaximumSize(
        ANCHO_VENTANA_AUTENTICACION,
        ALTO_VENTANA_AUTENTICACION,
    )
    ventana_principal.resize(
        ANCHO_VENTANA_AUTENTICACION,
        ALTO_VENTANA_AUTENTICACION,
    )
    ventana_principal.adjustSize()
    if estaba_visible:
        ventana_principal.show()
    _centrar_ventana_en_pantalla(ventana_principal)


def _aplicar_modo_principal(ventana_principal: QMainWindow) -> None:
    """Libera restricciones del login y devuelve un area de trabajo amplia."""
    estaba_visible = ventana_principal.isVisible()
    ventana_principal.setWindowFlags(FLAGS_VENTANA_PRINCIPAL)
    ventana_principal.setMinimumSize(0, 0)
    ventana_principal.setMaximumSize(MAXIMO_TAMANO_VENTANA, MAXIMO_TAMANO_VENTANA)
    if estaba_visible:
        ventana_principal.showMaximized()


def _centrar_ventana_en_pantalla(ventana_principal: QMainWindow) -> None:
    """Centra la ventana actual dentro del area util de la pantalla activa."""
    pantalla = ventana_principal.screen() or QApplication.primaryScreen()
    if pantalla is None:
        return

    geometria_disponible = pantalla.availableGeometry()
    geometria_ventana = ventana_principal.frameGeometry()
    geometria_ventana.moveCenter(geometria_disponible.center())

    posicion_x = max(geometria_disponible.left(), geometria_ventana.left())
    posicion_y = max(geometria_disponible.top(), geometria_ventana.top())
    ventana_principal.move(posicion_x, posicion_y)
