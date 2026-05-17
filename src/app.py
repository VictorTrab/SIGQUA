"""Composition root de SICAP para el flujo inicial de autenticacion."""

from __future__ import annotations

import sys

from dotenv import load_dotenv
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication, QMainWindow, QSizePolicy

from comun.base_datos import GestorBaseDatos
from comun.configuracion.gestor_rutas import GestorRutas
from comun.logs import obtener_logger_sicap
from comun.sesion import SesionAplicacion
from comun.ui import ContenedorApiladoAjustable
from comun.ui.qt_mensajes import configurar_filtro_mensajes_qt
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
from modulos.morosidad import (
    ControladorMorosidad,
    RepositorioMorosidadSQLite,
    ServicioMorosidad,
    VistaMorosidad,
)
from modulos.barrios import (
    ControladorBarrios,
    RepositorioBarriosSQLite,
    ServicioBarrios,
    VistaBarrios,
)
from modulos.abonados import (
    ControladorAbonados,
    RepositorioAbonadosSQLite,
    ServicioAbonados,
    VistaAbonados,
)
from modulos.casas import (
    ControladorCasas,
    RepositorioCasasSQLite,
    ServicioCasas,
    VistaCasas,
)
from modulos.configuracion import (
    ControladorConfiguracion,
    RepositorioConfiguracionSQLite,
    ServicioConfiguracion,
    VistaConfiguracion,
)
from modulos.planes_pago import (
    ControladorPlanesPago,
    RepositorioPlanesPagoSQLite,
    ServicioPlanesPago,
    VistaPlanesPago,
)
from modulos.pagos import (
    ControladorPagos,
    RepositorioPagosSQLite,
    ServicioPagos,
    VistaPagos,
)
from modulos.historial_pagos import (
    ControladorHistorialPagos,
    RepositorioHistorialPagosSQLite,
    ServicioHistorialPagos,
    VistaHistorialPagos,
)
from modulos.principal import (
    ControladorModuloPrincipal,
    RepositorioModuloPrincipalSQLite,
    ServicioModuloPrincipal,
    VistaModuloPrincipal,
)
from modulos.reportes import (
    ControladorReportes,
    RepositorioReportesSQLite,
    ServicioReportes,
    VistaReportes,
)
from modulos.usuarios import (
    ControladorUsuarios,
    RepositorioUsuariosSQLite,
    ServicioUsuarios,
    VistaUsuarios,
)

logger = obtener_logger_sicap("app")
ANCHO_VENTANA_AUTENTICACION = 760
ALTO_VENTANA_AUTENTICACION = 680
ANCHO_VENTANA_PRINCIPAL = 1360
ALTO_VENTANA_PRINCIPAL = 820
MARGEN_VENTANA_PRINCIPAL = 72
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
    configurar_filtro_mensajes_qt()
    logger.info("Iniciando composition root de SICAP.")

    aplicacion = QApplication.instance() or QApplication(sys.argv)
    aplicacion.setApplicationName("SICAP")
    fuente_aplicacion = QFont(aplicacion.font())
    if fuente_aplicacion.pointSize() <= 0:
        fuente_aplicacion.setPointSize(10)
    aplicacion.setFont(fuente_aplicacion)

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
    repositorio_barrios = RepositorioBarriosSQLite(gestor_base_datos)
    servicio_barrios = ServicioBarrios(repositorio_barrios)
    repositorio_casas = RepositorioCasasSQLite(gestor_base_datos)
    servicio_casas = ServicioCasas(repositorio_casas)
    repositorio_abonados = RepositorioAbonadosSQLite(gestor_base_datos)
    servicio_abonados = ServicioAbonados(repositorio_abonados, repositorio_casas)
    repositorio_planes_pago = RepositorioPlanesPagoSQLite(gestor_base_datos)
    servicio_planes_pago = ServicioPlanesPago(repositorio_planes_pago)
    repositorio_pagos = RepositorioPagosSQLite(gestor_base_datos)
    servicio_pagos = ServicioPagos(repositorio_pagos, gestor_rutas=gestor_rutas)
    repositorio_historial_pagos = RepositorioHistorialPagosSQLite(gestor_base_datos)
    servicio_historial_pagos = ServicioHistorialPagos(
        repositorio_historial_pagos,
        gestor_rutas=gestor_rutas,
    )
    repositorio_morosidad = RepositorioMorosidadSQLite(gestor_base_datos)
    servicio_morosidad = ServicioMorosidad(
        repositorio_morosidad,
        gestor_rutas=gestor_rutas,
    )
    repositorio_reportes = RepositorioReportesSQLite(gestor_base_datos)
    repositorio_configuracion = RepositorioConfiguracionSQLite(gestor_base_datos)
    servicio_reportes = ServicioReportes(
        repositorio_reportes,
        repositorio_configuracion=repositorio_configuracion,
        gestor_rutas=gestor_rutas,
    )
    servicio_configuracion = ServicioConfiguracion(repositorio_configuracion, gestor_rutas)
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
    ventana_principal.gestor_base_datos = gestor_base_datos
    ventana_principal.servicio_autenticacion = servicio_autenticacion
    ventana_principal.servicio_usuarios = servicio_usuarios
    ventana_principal.servicio_barrios = servicio_barrios
    ventana_principal.servicio_casas = servicio_casas
    ventana_principal.servicio_abonados = servicio_abonados
    ventana_principal.servicio_planes_pago = servicio_planes_pago
    ventana_principal.servicio_pagos = servicio_pagos
    ventana_principal.servicio_historial_pagos = servicio_historial_pagos
    ventana_principal.servicio_morosidad = servicio_morosidad
    ventana_principal.servicio_reportes = servicio_reportes
    ventana_principal.servicio_configuracion = servicio_configuracion
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
    """Abre el modulo principal tras autenticacion exitosa."""
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
            RepositorioModuloPrincipalSQLite(ventana_principal.gestor_base_datos),
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
        _registrar_modulos_operativos(ventana_principal)

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
    _refrescar_modulos_operativos(ventana_principal, sesion_iniciada.usuario)
    controlador_modulo_principal.mostrar_inicio(sesion_iniciada.usuario)
    ventana_principal.setWindowTitle("SICAP | Modulo principal")
    ventana_principal.contenedor_central.setCurrentWidget(vista_modulo_principal)
    _aplicar_modo_principal(ventana_principal)


def _registrar_modulos_operativos(ventana_principal: QMainWindow) -> None:
    """Registra paginas persistentes dentro del shell principal."""
    vista_modulo_principal = ventana_principal.vista_modulo_principal

    vista_barrios = VistaBarrios()
    controlador_barrios = ControladorBarrios(
        servicio_barrios=ventana_principal.servicio_barrios,
        vista_barrios=vista_barrios,
    )
    vista_modulo_principal.registrar_modulo("barrios", vista_barrios)

    vista_abonados = VistaAbonados()
    controlador_abonados = ControladorAbonados(
        servicio_abonados=ventana_principal.servicio_abonados,
        vista_abonados=vista_abonados,
    )
    vista_modulo_principal.registrar_modulo("abonados", vista_abonados)

    vista_casas = VistaCasas()
    controlador_casas = ControladorCasas(
        servicio_casas=ventana_principal.servicio_casas,
        vista_casas=vista_casas,
    )
    vista_modulo_principal.registrar_modulo("casas", vista_casas)

    vista_planes_pago = VistaPlanesPago()
    controlador_planes_pago = ControladorPlanesPago(
        servicio_planes_pago=ventana_principal.servicio_planes_pago,
        vista_planes_pago=vista_planes_pago,
    )
    vista_modulo_principal.registrar_modulo("planes_pago", vista_planes_pago)

    vista_pagos = VistaPagos()
    controlador_pagos = ControladorPagos(
        servicio_pagos=ventana_principal.servicio_pagos,
        vista_pagos=vista_pagos,
    )
    vista_modulo_principal.registrar_modulo("pagos", vista_pagos)

    vista_historial_pagos = VistaHistorialPagos()
    controlador_historial_pagos = ControladorHistorialPagos(
        servicio_historial=ventana_principal.servicio_historial_pagos,
        vista_historial=vista_historial_pagos,
    )
    vista_modulo_principal.registrar_modulo("historial_pagos", vista_historial_pagos)

    vista_morosidad = VistaMorosidad()
    controlador_morosidad = ControladorMorosidad(
        servicio_morosidad=ventana_principal.servicio_morosidad,
        vista_morosidad=vista_morosidad,
    )
    vista_modulo_principal.registrar_modulo("morosidad", vista_morosidad)

    vista_reportes = VistaReportes()
    controlador_reportes = ControladorReportes(
        servicio_reportes=ventana_principal.servicio_reportes,
        vista_reportes=vista_reportes,
    )
    vista_modulo_principal.registrar_modulo("reportes", vista_reportes)

    vista_usuarios = VistaUsuarios()
    controlador_usuarios = ControladorUsuarios(
        servicio_usuarios=ventana_principal.servicio_usuarios,
        vista_usuarios=vista_usuarios,
    )
    vista_modulo_principal.registrar_modulo("usuarios", vista_usuarios)

    vista_configuracion = VistaConfiguracion()
    controlador_configuracion = ControladorConfiguracion(
        servicio_configuracion=ventana_principal.servicio_configuracion,
        vista_configuracion=vista_configuracion,
    )
    vista_modulo_principal.registrar_modulo("configuracion", vista_configuracion)

    ventana_principal.vista_barrios = vista_barrios
    ventana_principal.controlador_barrios = controlador_barrios
    ventana_principal.vista_abonados = vista_abonados
    ventana_principal.controlador_abonados = controlador_abonados
    ventana_principal.vista_casas = vista_casas
    ventana_principal.controlador_casas = controlador_casas
    ventana_principal.vista_planes_pago = vista_planes_pago
    ventana_principal.controlador_planes_pago = controlador_planes_pago
    ventana_principal.vista_pagos = vista_pagos
    ventana_principal.controlador_pagos = controlador_pagos
    ventana_principal.vista_historial_pagos = vista_historial_pagos
    ventana_principal.controlador_historial_pagos = controlador_historial_pagos
    ventana_principal.vista_morosidad = vista_morosidad
    ventana_principal.controlador_morosidad = controlador_morosidad
    ventana_principal.vista_reportes = vista_reportes
    ventana_principal.controlador_reportes = controlador_reportes
    ventana_principal.vista_usuarios = vista_usuarios
    ventana_principal.controlador_usuarios = controlador_usuarios
    ventana_principal.vista_configuracion = vista_configuracion
    ventana_principal.controlador_configuracion = controlador_configuracion


def _refrescar_modulos_operativos(
    ventana_principal: QMainWindow,
    usuario: object,
) -> None:
    """Actualiza los modulos con datos dependientes de la sesion activa."""
    if hasattr(ventana_principal, "controlador_barrios"):
        ventana_principal.controlador_barrios.mostrar()
    if hasattr(ventana_principal, "controlador_abonados"):
        ventana_principal.controlador_abonados.mostrar_para_actor(usuario)
    if hasattr(ventana_principal, "controlador_casas"):
        ventana_principal.controlador_casas.mostrar_para_actor(usuario)
    if hasattr(ventana_principal, "controlador_planes_pago"):
        ventana_principal.controlador_planes_pago.mostrar_para_actor(usuario)
    if hasattr(ventana_principal, "controlador_pagos"):
        ventana_principal.controlador_pagos.mostrar_para_actor(usuario)
    if hasattr(ventana_principal, "controlador_historial_pagos"):
        ventana_principal.controlador_historial_pagos.mostrar()
    if hasattr(ventana_principal, "controlador_morosidad"):
        ventana_principal.controlador_morosidad.mostrar()
    if hasattr(ventana_principal, "controlador_reportes"):
        ventana_principal.controlador_reportes.mostrar()
    if hasattr(ventana_principal, "controlador_usuarios"):
        ventana_principal.controlador_usuarios.mostrar_para_actor(usuario)
    if hasattr(ventana_principal, "controlador_configuracion"):
        ventana_principal.controlador_configuracion.mostrar_para_actor(usuario)


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
    if estaba_visible:
        ventana_principal.hide()
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
        ventana_principal.showNormal()
        ventana_principal.show()
    _centrar_ventana_en_pantalla(ventana_principal)


def _aplicar_modo_principal(ventana_principal: QMainWindow) -> None:
    """Libera restricciones del login y abre el shell principal maximizado."""
    estaba_visible = ventana_principal.isVisible()
    if estaba_visible:
        ventana_principal.hide()
    ventana_principal.showNormal()
    ventana_principal.setWindowFlags(FLAGS_VENTANA_PRINCIPAL)
    ventana_principal.setMinimumSize(0, 0)
    ventana_principal.setMaximumSize(MAXIMO_TAMANO_VENTANA, MAXIMO_TAMANO_VENTANA)
    pantalla = ventana_principal.screen() or QApplication.primaryScreen()
    if pantalla is not None:
        geometria_disponible = pantalla.availableGeometry()
        ancho_objetivo = max(
            min(ANCHO_VENTANA_PRINCIPAL, geometria_disponible.width()),
            geometria_disponible.width() - MARGEN_VENTANA_PRINCIPAL,
        )
        alto_objetivo = max(
            min(ALTO_VENTANA_PRINCIPAL, geometria_disponible.height()),
            geometria_disponible.height() - MARGEN_VENTANA_PRINCIPAL,
        )
        ancho_objetivo = min(ancho_objetivo, geometria_disponible.width())
        alto_objetivo = min(alto_objetivo, geometria_disponible.height())
        ventana_principal.resize(ancho_objetivo, alto_objetivo)
    else:
        ventana_principal.resize(ANCHO_VENTANA_PRINCIPAL, ALTO_VENTANA_PRINCIPAL)
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
