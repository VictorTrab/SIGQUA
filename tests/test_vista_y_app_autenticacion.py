from __future__ import annotations

import os
import shutil
import sys
import unittest
import uuid
from datetime import datetime
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
RUTA_SRC = RAIZ_PROYECTO / "src"

if str(RUTA_SRC) not in sys.path:
    sys.path.insert(0, str(RUTA_SRC))

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication, QFrame, QLabel, QPushButton, QScrollArea, QTableWidget, QTextEdit, QToolButton, QWidget  # noqa: E402

from app import (  # noqa: E402
    ALTO_VENTANA_AUTENTICACION,
    ANCHO_VENTANA_AUTENTICACION,
    crear_ventana_principal,
)
from comun.configuracion.gestor_rutas import GestorRutas  # noqa: E402
from modulos.autenticacion.controlador import ControladorAutenticacion  # noqa: E402
from modulos.autenticacion.entidades import SesionIniciada, UsuarioAutenticado  # noqa: E402
from modulos.autenticacion.vista import (  # noqa: E402
    ANCHO_MAXIMO_TARJETA,
    VistaAutenticacion,
)
from modulos.mantenimiento.vista import VistaMantenimiento  # noqa: E402
from modulos.barrios.vista import (  # noqa: E402
    DialogoConfirmacionEstadoBarrio,
    DialogoDetalleBarrio,
    DialogoFormularioBarrio,
    VistaBarrios,
)
from modulos.barrios.entidades import Barrio  # noqa: E402
from modulos.abonados.vista import (  # noqa: E402
    DialogoConfirmacionEstadoAbonado,
    DialogoDetalleAbonado,
    DialogoFormularioAbonado,
    VistaAbonados,
)
from modulos.abonados.entidades import Abonado, OpcionBarrio  # noqa: E402
from modulos.casas.vista import (  # noqa: E402
    DialogoCambioDuenoCasa,
    DialogoConfirmacionEstadoCasa,
    DialogoDetalleCasa,
    DialogoFormularioCasa,
    DialogoHistorialPropietariosCasa,
    VistaCasas,
)
from modulos.configuracion.vista import VistaConfiguracion  # noqa: E402
from modulos.casas.entidades import (  # noqa: E402
    Casa,
    DetalleCasa,
    HistorialPropietarioCasa,
    OpcionAbonado,
    OpcionBarrio as OpcionBarrioCasa,
)
from modulos.historial_pagos.vista import VistaHistorialPagos  # noqa: E402
from modulos.morosidad.vista import VistaMorosidad  # noqa: E402
from modulos.pagos.vista import VistaPagos  # noqa: E402
from modulos.planes_pago.vista import VistaPlanesPago  # noqa: E402
from modulos.principal.vista import VistaModuloPrincipal  # noqa: E402
from modulos.principal.entidades import AnaliticaDashboard, EstadoModuloPrincipal, ModuloNavegacion  # noqa: E402
from modulos.reportes.vista import VistaReportes  # noqa: E402
from modulos.usuarios.entidades import PermisoSistema, ResumenUsuarios, RolSistema, UsuarioSistema  # noqa: E402
from modulos.usuarios.vista import VistaUsuarios  # noqa: E402


class TestVistaYAppAutenticacion(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.aplicacion = QApplication.instance() or QApplication([])

    @staticmethod
    def _copiar_migraciones(raiz_temporal: Path) -> None:
        for ruta_migracion in (RAIZ_PROYECTO / "database" / "migrations").glob("*.sql"):
            contenido_sql = ruta_migracion.read_text(encoding="utf-8")
            (raiz_temporal / "database" / "migrations" / ruta_migracion.name).write_text(
                contenido_sql,
                encoding="utf-8",
            )

    @staticmethod
    def _crear_raiz_temporal_prueba(prefijo: str) -> Path:
        raiz_temporal = RAIZ_PROYECTO / ".codex-temp" / f"{prefijo}_{uuid.uuid4().hex}"
        (raiz_temporal / "database" / "migrations").mkdir(parents=True, exist_ok=True)
        return raiz_temporal

    def _esperar_arranque_principal(
        self,
        ventana_principal: QWidget,
        timeout_ms: int = 700,
    ) -> None:
        transcurrido = 0
        while transcurrido < timeout_ms:
            self.aplicacion.processEvents()
            if isinstance(
                ventana_principal.contenedor_central.currentWidget(),
                VistaModuloPrincipal,
            ):
                return
            QTest.qWait(25)
            transcurrido += 25
        self.fail("El modulo principal no termino de cargar dentro del tiempo esperado.")

    def test_vista_usa_tres_paginas_reutilizables_y_navegacion_local(self) -> None:
        vista = VistaAutenticacion()
        panel_institucional = vista._pagina_login.findChild(QFrame, "panelInstitucionalLogin")
        panel_formulario = vista._pagina_login.findChild(QFrame, "panelFormularioLogin")
        badge_contexto = vista._pagina_login.findChild(QFrame, "badgeContexto")
        badge_icono = vista._pagina_login.findChild(QLabel, "badgeContextoIcono")
        badge_texto = vista._pagina_login.findChild(QLabel, "badgeContextoTexto")
        logo_institucional = vista._pagina_login.findChild(QLabel, "logoMarcaLoginInstitucional")
        logo_login = vista._pagina_login.findChild(QLabel, "logoMarcaLogin")
        lema_login = vista._pagina_login.findChild(QLabel, "lemaMarcaLogin")
        titulo_repetido = vista._pagina_login.findChild(QLabel, "nombreSistemaLogin")
        texto_ayuda = vista._pagina_login.findChild(QLabel, "textoAyudaLogin")
        enlace_ayuda = vista._pagina_login.findChild(QPushButton, "enlaceAyudaLogin")
        estado_acceso = vista._pagina_login.findChild(QFrame, "estadoAccesoLogin")
        texto_estado_acceso = vista._pagina_login.findChild(QLabel, "textoEstadoAccesoLogin")

        self.assertEqual(vista._gestor_rutas.obtener_ruta_logo_marca().name, "sigqua_logo.svg")
        self.assertFalse(hasattr(vista._gestor_rutas, "obtener_ruta_fondo_login"))
        self.assertEqual(vista._stack.count(), 3)
        self.assertEqual(panel_formulario.maximumWidth(), ANCHO_MAXIMO_TARJETA)
        self.assertGreater(vista.maximumWidth(), ANCHO_MAXIMO_TARJETA)
        self.assertIn("font-size: 10px;", vista.styleSheet())
        self.assertIn("qlineargradient", vista.styleSheet())
        self.assertNotIn("fondo_login.png", vista.styleSheet())
        self.assertNotIn("border-image", vista.styleSheet())
        self.assertNotIn("background-image", vista.styleSheet())
        self.assertIsNotNone(panel_institucional)
        self.assertIsNotNone(panel_formulario)
        self.assertEqual(panel_institucional.objectName(), "panelInstitucionalLogin")
        self.assertEqual(panel_formulario.objectName(), "panelFormularioLogin")
        self.assertIn("QFrame#panelInstitucionalLogin", vista.styleSheet())
        self.assertIn("QFrame#panelFormularioLogin", vista.styleSheet())
        self.assertIn("background: #FFFFFF", vista.styleSheet())
        self.assertIsNotNone(badge_contexto)
        self.assertIsNotNone(badge_icono)
        self.assertIsNotNone(badge_texto)
        self.assertIn("Bienvenido", [label.text() for label in vista._pagina_login.findChildren(QLabel)])
        self.assertEqual(badge_texto.text(), "Acceso seguro")
        self.assertEqual(vista._boton_login.text(), "Iniciar sesión")
        self.assertIsNotNone(texto_ayuda)
        self.assertEqual(texto_ayuda.text(), "¿Necesitas ayuda?")
        self.assertIsNotNone(enlace_ayuda)
        self.assertEqual(enlace_ayuda.text(), "Contacta al administrador")
        self.assertIsNotNone(estado_acceso)
        self.assertFalse(estado_acceso.isVisible())
        self.assertIsNotNone(texto_estado_acceso)
        self.assertEqual(texto_estado_acceso.text(), "Accediendo...")
        self.assertFalse(vista.login_en_progreso())
        self.assertIsNotNone(logo_institucional)
        self.assertIsNotNone(logo_institucional.pixmap())
        self.assertFalse(logo_institucional.pixmap().isNull())
        self.assertEqual(logo_institucional.pixmap().deviceIndependentSize().toSize().width(), 194)
        self.assertEqual(
            vista._pagina_login.findChild(QLabel, "subtituloSistemaLogin").text().splitlines(),
            ["Sistema Integrado de Gestión", "para Juntas de Agua"],
        )
        self.assertIsNone(logo_login)
        self.assertIsNone(lema_login)
        self.assertIsNone(titulo_repetido)
        self.assertIn("Versión 2.2.0", vista._label_pie_login.text())
        self.assertNotIn("SIGQUA", vista._label_pie_login.text())
        self.assertFalse(vista._campo_usuario.property("icono_usuario_a_la_derecha"))
        accion_limpiar_usuario = next(
            accion
            for accion in vista._campo_usuario.actions()
            if accion.objectName() == "accionLimpiarCampo"
        )
        self.assertFalse(accion_limpiar_usuario.isVisible())
        vista._campo_usuario.setText("admin")
        self.aplicacion.processEvents()
        self.assertTrue(accion_limpiar_usuario.isVisible())
        accion_limpiar_usuario.trigger()
        self.assertEqual(vista._campo_usuario.text(), "")
        self.assertEqual(len(vista._campo_contrasena.actions()), 1)
        self.assertEqual(vista._campo_contrasena.echoMode(), vista._campo_contrasena.EchoMode.Password)

        vista._campo_contrasena.actions()[-1].trigger()
        self.assertEqual(vista._campo_contrasena.echoMode(), vista._campo_contrasena.EchoMode.Normal)

        vista._campo_contrasena.actions()[-1].trigger()
        self.assertEqual(vista._campo_contrasena.echoMode(), vista._campo_contrasena.EchoMode.Password)
        self.assertFalse(vista._boton_login.icon().isNull())

        vista.mostrar_restablecer("admin")
        self.assertEqual(vista._campo_nueva_contrasena.echoMode(), vista._campo_nueva_contrasena.EchoMode.Password)
        vista._campo_nueva_contrasena.actions()[-1].trigger()
        self.assertEqual(vista._campo_nueva_contrasena.echoMode(), vista._campo_nueva_contrasena.EchoMode.Normal)
        vista._campo_nueva_contrasena.actions()[-1].trigger()
        self.assertEqual(vista._campo_nueva_contrasena.echoMode(), vista._campo_nueva_contrasena.EchoMode.Password)

        vista.mostrar_olvido_contrasena()
        self.assertIs(vista._stack.currentWidget(), vista._pagina_olvido)
        boton_volver_olvido = vista._pagina_olvido.findChild(type(vista._boton_login), "botonPrimario")
        self.assertIsNotNone(boton_volver_olvido)
        textos_olvido = [
            label.text().lower()
            for label in vista._pagina_olvido.findChildren(type(vista._label_pie_login))
        ]
        self.assertTrue(any("soporte o administración" in texto for texto in textos_olvido))
        self.assertFalse(any("primera version" in texto for texto in textos_olvido))

    def test_vista_olvido_muestra_mensaje_informativo_y_restablecer_retorna_a_login(self) -> None:
        vista = VistaAutenticacion()

        vista.mostrar_olvido_contrasena()
        textos = [
            label.text().lower()
            for label in vista._pagina_olvido.findChildren(type(vista._label_pie_login))
        ]
        self.assertTrue(any("soporte o administración" in texto for texto in textos))
        self.assertFalse(any("primera version" in texto for texto in textos))

        vista.mostrar_restablecer("admin", "Cambio obligatorio pendiente.")
        self.assertIs(vista._stack.currentWidget(), vista._pagina_restablecer)
        self.assertIn("admin", vista._label_usuario_restablecer.text().lower())

        vista.mostrar_exito("Tu contrasena se actualizo correctamente.")
        self.assertIs(vista._stack.currentWidget(), vista._pagina_login)
        self.assertIn("actualizo correctamente", vista._mensaje_login.text().lower())

    def test_mostrar_login_limpia_campos_al_regresar(self) -> None:
        vista = VistaAutenticacion()

        vista._campo_usuario.setText("admin")
        vista._campo_contrasena.setText("Admin123!")
        vista.mostrar_restablecer("admin")
        vista._campo_nueva_contrasena.setText("Nueva123!")
        vista._campo_confirmacion_contrasena.setText("Nueva123!")

        vista.mostrar_login()

        self.assertEqual(vista._campo_usuario.text(), "")
        self.assertEqual(vista._campo_contrasena.text(), "")
        self.assertEqual(vista._campo_nueva_contrasena.text(), "")
        self.assertEqual(vista._campo_confirmacion_contrasena.text(), "")
        self.assertIs(vista._stack.currentWidget(), vista._pagina_login)

    def test_capa_blur_no_bloquea_acciones_del_login(self) -> None:
        vista = VistaAutenticacion()
        eventos_login = []
        eventos_olvido = []
        vista.iniciar_sesion_solicitada.connect(
            lambda usuario, contrasena: eventos_login.append((usuario, contrasena))
        )
        vista.ir_a_olvido_solicitado.connect(lambda: eventos_olvido.append(True))

        vista._campo_usuario.setText("admin")
        vista._campo_contrasena.setText("Admin123!")
        vista._boton_login.click()
        vista._pagina_login.findChild(QPushButton, "enlaceAyudaLogin").click()

        self.assertEqual(eventos_login, [("admin", "Admin123!")])
        self.assertEqual(eventos_olvido, [True])

    def test_estado_acceso_login_bloquea_interaccion_y_se_restablece(self) -> None:
        vista = VistaAutenticacion()
        eventos_login = []
        vista.iniciar_sesion_solicitada.connect(
            lambda usuario, contrasena: eventos_login.append((usuario, contrasena))
        )
        vista._campo_usuario.setText("admin")
        vista._campo_contrasena.setText("Admin123!")

        vista.mostrar_estado_validando_login()

        self.assertTrue(vista.login_en_progreso())
        self.assertFalse(vista._campo_usuario.isEnabled())
        self.assertFalse(vista._campo_contrasena.isEnabled())
        self.assertFalse(vista._boton_login.isEnabled())
        self.assertFalse(vista._estado_acceso_login.isHidden())

        vista._boton_login.click()
        vista._campo_contrasena.returnPressed.emit()
        self.assertEqual(eventos_login, [])

        vista.restablecer_estado_login()

        self.assertFalse(vista.login_en_progreso())
        self.assertTrue(vista._campo_usuario.isEnabled())
        self.assertTrue(vista._campo_contrasena.isEnabled())
        self.assertTrue(vista._boton_login.isEnabled())
        self.assertTrue(vista._estado_acceso_login.isHidden())

    def test_app_compone_ventana_y_deja_login_con_tamano_fijo(self) -> None:
        raiz_temporal = self._crear_raiz_temporal_prueba("test_login_fijo")
        try:
            self._copiar_migraciones(raiz_temporal)

            gestor_rutas = GestorRutas(raiz_proyecto=raiz_temporal)
            _, ventana_principal, vista_autenticacion = crear_ventana_principal(gestor_rutas)

            self.assertIs(ventana_principal.centralWidget(), ventana_principal.contenedor_central)
            self.assertIs(ventana_principal.contenedor_central.currentWidget(), vista_autenticacion)
            self.assertEqual(ventana_principal.windowTitle(), "SIGQUA | Autenticación")
            self.assertEqual(ventana_principal.minimumWidth(), ANCHO_VENTANA_AUTENTICACION)
            self.assertEqual(ventana_principal.maximumWidth(), ANCHO_VENTANA_AUTENTICACION)
            self.assertEqual(ventana_principal.minimumHeight(), ALTO_VENTANA_AUTENTICACION)
            self.assertEqual(ventana_principal.maximumHeight(), ALTO_VENTANA_AUTENTICACION)
            self.assertFalse(
                bool(ventana_principal.windowFlags() & Qt.WindowType.WindowMaximizeButtonHint)
            )
            self.assertTrue(
                bool(ventana_principal.windowFlags() & Qt.WindowType.WindowMinimizeButtonHint)
            )
            self.assertTrue(
                bool(ventana_principal.windowFlags() & Qt.WindowType.WindowCloseButtonHint)
            )
            ventana_principal.close()
        finally:
            shutil.rmtree(raiz_temporal, ignore_errors=True)

    def test_post_login_abre_modulo_principal_provisional(self) -> None:
        raiz_temporal = self._crear_raiz_temporal_prueba("test_post_login")
        try:
            self._copiar_migraciones(raiz_temporal)

            gestor_rutas = GestorRutas(raiz_proyecto=raiz_temporal)
            _, ventana_principal, vista_autenticacion = crear_ventana_principal(gestor_rutas)

            vista_autenticacion.autenticacion_exitosa.emit(
                SesionIniciada(
                    usuario=UsuarioAutenticado(
                        identificador=1,
                        nombre_usuario="admin",
                        nombre_completo="Administrador del Sistema",
                        correo="admin@sigqua.local",
                        estado="ACTIVO",
                    ),
                    token_sesion="token-prueba-123",
                )
            )
            self.aplicacion.processEvents()
            self.assertIs(
                ventana_principal.contenedor_central.currentWidget(),
                vista_autenticacion,
            )
            self.assertTrue(vista_autenticacion.login_en_progreso())
            self.assertFalse(vista_autenticacion._estado_acceso_login.isHidden())
            self._esperar_arranque_principal(ventana_principal)

            self.assertIs(ventana_principal.centralWidget(), ventana_principal.contenedor_central)
            self.assertIsInstance(
                ventana_principal.contenedor_central.currentWidget(),
                VistaModuloPrincipal,
            )
            self.assertEqual(ventana_principal.windowTitle(), "SIGQUA | Módulo principal")
            self.assertIsNotNone(ventana_principal.sesion_activa)
            self.assertEqual(ventana_principal.sesion_activa.token_sesion, "token-prueba-123")
            self.assertEqual(ventana_principal.contenedor_central.count(), 2)
            self.assertFalse(ventana_principal.vista_modulo_principal._boton_mantenimiento.isVisible())
            self.assertIsInstance(ventana_principal.vista_casas, VistaCasas)
            self.assertIsInstance(ventana_principal.vista_planes_pago, VistaPlanesPago)
            self.assertIsInstance(ventana_principal.vista_historial_pagos, VistaHistorialPagos)
            self.assertIsInstance(ventana_principal.vista_configuracion, VistaConfiguracion)
            self.assertTrue(
                bool(ventana_principal.windowFlags() & Qt.WindowType.WindowMaximizeButtonHint)
            )
            self.assertTrue(
                bool(ventana_principal.windowState() & Qt.WindowState.WindowMaximized)
            )
            ventana_principal.close()
        finally:
            shutil.rmtree(raiz_temporal, ignore_errors=True)

    def test_logout_regresa_a_login_y_limpia_sesion(self) -> None:
        raiz_temporal = self._crear_raiz_temporal_prueba("test_logout")
        try:
            self._copiar_migraciones(raiz_temporal)

            gestor_rutas = GestorRutas(raiz_proyecto=raiz_temporal)
            _, ventana_principal, vista_autenticacion = crear_ventana_principal(gestor_rutas)

            vista_autenticacion.autenticacion_exitosa.emit(
                SesionIniciada(
                    usuario=UsuarioAutenticado(
                        identificador=1,
                        nombre_usuario="admin",
                        nombre_completo="Administrador del Sistema",
                        correo="admin@sigqua.local",
                        estado="ACTIVO",
                    ),
                    token_sesion="token-prueba-456",
                )
            )
            self._esperar_arranque_principal(ventana_principal)

            alto_minimo_principal = ventana_principal.minimumSizeHint().height()
            ventana_principal.vista_modulo_principal.cerrar_sesion_solicitada.emit()

            self.assertIs(ventana_principal.centralWidget(), ventana_principal.contenedor_central)
            self.assertIs(ventana_principal.contenedor_central.currentWidget(), vista_autenticacion)
            self.assertIsNone(ventana_principal.sesion_activa)
            self.assertEqual(ventana_principal.windowTitle(), "SIGQUA | Autenticación")
            self.assertEqual(ventana_principal.contenedor_central.count(), 2)
            self.assertGreaterEqual(alto_minimo_principal, 0)
            self.assertEqual(ventana_principal.minimumWidth(), ANCHO_VENTANA_AUTENTICACION)
            self.assertEqual(ventana_principal.maximumWidth(), ANCHO_VENTANA_AUTENTICACION)
            self.assertEqual(ventana_principal.minimumHeight(), ALTO_VENTANA_AUTENTICACION)
            self.assertEqual(ventana_principal.maximumHeight(), ALTO_VENTANA_AUTENTICACION)
            self.assertFalse(
                bool(ventana_principal.windowFlags() & Qt.WindowType.WindowMaximizeButtonHint)
            )
            self.assertTrue(
                bool(ventana_principal.windowFlags() & Qt.WindowType.WindowMinimizeButtonHint)
            )
            self.assertTrue(
                bool(ventana_principal.windowFlags() & Qt.WindowType.WindowCloseButtonHint)
            )
            self.assertIn(
                "Sesion cerrada correctamente.",
                vista_autenticacion._mensaje_login.text(),
            )
            ventana_principal.close()
        finally:
            shutil.rmtree(raiz_temporal, ignore_errors=True)

    def test_dashboard_principal_refluye_y_tiene_scroll_responsivo(self) -> None:
        raiz_temporal = RAIZ_PROYECTO / ".codex-temp" / f"test_dashboard_{uuid.uuid4().hex}"
        try:
            (raiz_temporal / "database" / "migrations").mkdir(parents=True, exist_ok=True)
            self._copiar_migraciones(raiz_temporal)

            gestor_rutas = GestorRutas(raiz_proyecto=raiz_temporal)
            _, ventana_principal, vista_autenticacion = crear_ventana_principal(gestor_rutas)

            vista_autenticacion.autenticacion_exitosa.emit(
                SesionIniciada(
                    usuario=UsuarioAutenticado(
                        identificador=1,
                        nombre_usuario="admin",
                        nombre_completo="Administrador del Sistema",
                        correo="admin@sigqua.local",
                        estado="ACTIVO",
                    ),
                    token_sesion="token-dashboard",
                )
            )
            self._esperar_arranque_principal(ventana_principal)

            vista_principal = ventana_principal.vista_modulo_principal
            ventana_principal.show()
            self.aplicacion.processEvents()
            self.assertTrue(vista_principal._scroll_dashboard.widgetResizable())

            ventana_principal.resize(1200, 760)
            self.aplicacion.processEvents()
            self.assertEqual(vista_principal._modo_dashboard_actual, "compacto")
            self.assertGreater(vista_principal._scroll_dashboard.verticalScrollBar().maximum(), 0)

            ventana_principal.resize(1500, 960)
            self.aplicacion.processEvents()
            self.assertEqual(vista_principal._modo_dashboard_actual, "medio")
            self.assertGreater(vista_principal._scroll_dashboard.verticalScrollBar().maximum(), 0)

            ventana_principal.resize(1900, 1080)
            self.aplicacion.processEvents()
            self.assertEqual(vista_principal._modo_dashboard_actual, "amplio")
            self.assertIs(
                vista_principal._stack_contenido.currentWidget(),
                vista_principal._pagina_dashboard,
            )
            self.assertGreaterEqual(vista_principal._scroll_dashboard.verticalScrollBar().maximum(), 0)
            ventana_principal.close()
        finally:
            shutil.rmtree(raiz_temporal, ignore_errors=True)

    def test_controlador_permite_abrir_restablecimiento_administrativo(self) -> None:
        raiz_temporal = self._crear_raiz_temporal_prueba("test_restablecimiento")
        try:
            self._copiar_migraciones(raiz_temporal)

            gestor_rutas = GestorRutas(raiz_proyecto=raiz_temporal)
            _, ventana_principal, vista_autenticacion = crear_ventana_principal(gestor_rutas)

            controlador: ControladorAutenticacion = ventana_principal.controlador_autenticacion
            controlador.abrir_restablecimiento_administrativo(
                "admin",
                "Cambio obligatorio pendiente.",
            )

            self.assertIs(vista_autenticacion._stack.currentWidget(), vista_autenticacion._pagina_restablecer)
            self.assertIn("admin", vista_autenticacion._label_usuario_restablecer.text().lower())
            ventana_principal.close()
        finally:
            shutil.rmtree(raiz_temporal, ignore_errors=True)

    def test_superadmin_ve_y_abre_mantenimiento_tecnico(self) -> None:
        raiz_temporal = self._crear_raiz_temporal_prueba("test_superadmin")
        try:
            self._copiar_migraciones(raiz_temporal)

            gestor_rutas = GestorRutas(raiz_proyecto=raiz_temporal)
            _, ventana_principal, vista_autenticacion = crear_ventana_principal(gestor_rutas)

            vista_autenticacion.autenticacion_exitosa.emit(
                SesionIniciada(
                    usuario=UsuarioAutenticado(
                        identificador=99,
                        nombre_usuario="superadmin",
                        nombre_completo="Superadministrador Tecnico",
                        correo="superadmin@sigqua.local",
                        estado="ACTIVO",
                        es_tecnico=True,
                        es_oculto=True,
                        roles=("SUPERADMINISTRADOR",),
                        permisos=frozenset({"mantenimiento.ver", "seguridad.ver_logs"}),
                    ),
                    token_sesion="token-superadmin-1",
                )
            )
            self._esperar_arranque_principal(ventana_principal)

            self.assertFalse(ventana_principal.vista_modulo_principal._boton_mantenimiento.isHidden())
            ventana_principal.vista_modulo_principal._boton_mantenimiento.click()
            self.assertIsInstance(
                ventana_principal.contenedor_central.currentWidget(),
                VistaMantenimiento,
            )
            ventana_principal.vista_mantenimiento.volver_solicitado.emit()
            self.assertIsInstance(
                ventana_principal.contenedor_central.currentWidget(),
                VistaModuloPrincipal,
            )
            ventana_principal.close()
        finally:
            shutil.rmtree(raiz_temporal, ignore_errors=True)

    def test_vista_barrios_usa_radio_minimo_en_panel_interno_de_tabla(self) -> None:
        vista = VistaBarrios()
        vista.show()
        self.aplicacion.processEvents()

        panel_tabla = vista.findChild(QWidget, "panelTablaBarrios")
        tabla = vista.findChild(type(vista._tabla), "tablaBarrios")
        viewport = vista._tabla.viewport()

        self.assertIsNotNone(panel_tabla)
        self.assertIs(tabla, vista._tabla)
        self.assertEqual(viewport.objectName(), "viewportTablaBarrios")
        self.assertIn("QFrame#panelTablaBarrios", vista.styleSheet())
        self.assertIn("QTableWidget#tablaBarrios", vista.styleSheet())
        self.assertIn(f"border-radius: {vista.RADIO_PANEL_TABLA}px;", vista.styleSheet())
        self.assertIn(f"padding: 0 0 {vista.RADIO_PANEL_TABLA}px 0;", vista.styleSheet())
        self.assertIn("QTableWidget#tablaBarrios QHeaderView::section", vista.styleSheet())
        self.assertEqual(vista._tabla.frameShape(), vista._tabla.Shape.NoFrame)
        self.assertFalse(vista._tabla.horizontalHeader().stretchLastSection())

        fila_acciones = vista._crear_acciones_fila(
            Barrio(identificador=1, nombre="Centro", estado="ACTIVO")
        )
        botones_accion = fila_acciones.findChildren(QToolButton, "botonIconoFilaBarrio")
        self.assertEqual(len(botones_accion), 5)
        self.assertTrue(all(not boton.text() for boton in botones_accion))
        self.assertTrue(all(not boton.icon().isNull() for boton in botones_accion))
        self.assertTrue(all(boton.iconSize().width() == 18 for boton in botones_accion))
        self.assertEqual(fila_acciones.minimumHeight(), 58)
        vista.close()

    def test_notificacion_barrios_desaparece_tras_temporizador(self) -> None:
        vista = VistaBarrios()

        vista.mostrar_mensaje("Barrio actualizado correctamente.")

        self.assertFalse(vista._mensaje.isHidden())
        self.assertTrue(vista._temporizador_mensaje.isActive())
        self.assertEqual(
            vista._temporizador_mensaje.interval(),
            vista.DURACION_MENSAJE_MS,
        )

        vista._temporizador_mensaje.timeout.emit()

        self.assertTrue(vista._mensaje.isHidden())
        self.assertEqual(vista._mensaje.text(), "")
        vista.close()

    def test_vista_abonados_usa_patron_visual_de_barrios_en_tabla_y_acciones(self) -> None:
        vista = VistaAbonados()
        vista.show()
        self.aplicacion.processEvents()

        panel_tabla = vista.findChild(QWidget, "panelTablaAbonados")
        tabla = vista.findChild(type(vista._tabla), "tablaAbonados")
        viewport = vista._tabla.viewport()

        self.assertIsNotNone(panel_tabla)
        self.assertIs(tabla, vista._tabla)
        self.assertEqual(viewport.objectName(), "viewportTablaAbonados")
        self.assertIn("QFrame#panelTablaAbonados", vista.styleSheet())
        self.assertIn("QTableWidget#tablaAbonados", vista.styleSheet())
        self.assertIn(f"border-radius: {vista.RADIO_PANEL_TABLA}px;", vista.styleSheet())
        self.assertIn(f"padding: 0 0 {vista.RADIO_PANEL_TABLA}px 0;", vista.styleSheet())
        self.assertIn("QTableWidget#tablaAbonados QHeaderView::section", vista.styleSheet())
        self.assertEqual(vista._tabla.frameShape(), vista._tabla.Shape.NoFrame)
        self.assertFalse(vista._tabla.horizontalHeader().stretchLastSection())

        fila_acciones = vista._crear_acciones_fila(
            Abonado(identificador=1, dni="0801199000011", nombre_completo="Ana Martinez", estado="ACTIVO")
        )
        botones_accion = fila_acciones.findChildren(QToolButton, "botonIconoFilaAbonado")
        self.assertEqual(len(botones_accion), 4)
        self.assertTrue(all(not boton.text() for boton in botones_accion))
        self.assertTrue(all(not boton.icon().isNull() for boton in botones_accion))
        self.assertTrue(all(boton.iconSize().width() == 18 for boton in botones_accion))
        self.assertEqual(fila_acciones.minimumHeight(), 58)
        vista.close()

    def test_notificacion_abonados_desaparece_tras_temporizador(self) -> None:
        vista = VistaAbonados()

        vista.mostrar_mensaje("Abonado actualizado correctamente.")

        self.assertFalse(vista._mensaje.isHidden())
        self.assertTrue(vista._temporizador_mensaje.isActive())
        self.assertEqual(
            vista._temporizador_mensaje.interval(),
            vista.DURACION_MENSAJE_MS,
        )

        vista._temporizador_mensaje.timeout.emit()

        self.assertTrue(vista._mensaje.isHidden())
        self.assertEqual(vista._mensaje.text(), "")
        vista.close()

    def test_vista_casas_usa_patron_visual_compatibile_y_acciones_compactas(self) -> None:
        vista = VistaCasas()
        vista.show()
        self.aplicacion.processEvents()

        panel_tabla = vista.findChild(QWidget, "panelTablaCasas")
        tabla = vista.findChild(type(vista._tabla), "tablaCasas")
        viewport = vista._tabla.viewport()

        self.assertIsNotNone(panel_tabla)
        self.assertIs(tabla, vista._tabla)
        self.assertEqual(viewport.objectName(), "viewportTablaCasas")
        self.assertIn("QFrame#panelTablaCasas", vista.styleSheet())
        self.assertIn("QTableWidget#tablaCasas", vista.styleSheet())
        self.assertIn(f"border-radius: {vista.RADIO_PANEL_TABLA}px;", vista.styleSheet())
        self.assertIn(f"padding: 0 0 {vista.RADIO_PANEL_TABLA}px 0;", vista.styleSheet())
        self.assertIn("QTableWidget#tablaCasas QHeaderView::section", vista.styleSheet())
        self.assertEqual(vista._tabla.frameShape(), vista._tabla.Shape.NoFrame)
        self.assertFalse(vista._tabla.horizontalHeader().stretchLastSection())

        fila_acciones = vista._crear_acciones_fila(
            Casa(identificador=1, abonado_nombre="Ana Martinez", barrio_nombre="Centro", estado_servicio="ACTIVO")
        )
        botones_accion = fila_acciones.findChildren(QToolButton, "botonIconoFilaCasa")
        self.assertEqual(len(botones_accion), 1)
        self.assertEqual(botones_accion[0].toolTip(), "Ver detalle")
        self.assertTrue(all(not boton.text() for boton in botones_accion))
        self.assertTrue(all(not boton.icon().isNull() for boton in botones_accion))
        self.assertTrue(all(boton.iconSize().width() == 18 for boton in botones_accion))
        self.assertEqual(fila_acciones.minimumHeight(), 74)
        self.assertEqual(vista._tabla.horizontalHeaderItem(6).text(), "Servicio")
        self.assertEqual(vista._tabla.horizontalHeaderItem(7).text(), "Operativo")
        self.assertNotIn("Aviso", [vista._tabla.horizontalHeaderItem(indice).text() for indice in range(vista._tabla.columnCount())])
        vista.close()

    def test_shell_principal_reduce_ancho_sidebar_sin_expandir_menu(self) -> None:
        vista_principal = VistaModuloPrincipal()
        logo_sidebar = vista_principal.findChild(QLabel, "logoSidebar")

        self.assertEqual(vista_principal._sidebar.minimumWidth(), 192)
        self.assertEqual(vista_principal._sidebar.maximumWidth(), 198)
        self.assertIsNotNone(logo_sidebar)
        self.assertIsNotNone(logo_sidebar.pixmap())
        self.assertFalse(logo_sidebar.pixmap().isNull())
        vista_principal.close()

    def test_shell_principal_resuelve_saludo_por_hora(self) -> None:
        self.assertEqual(
            VistaModuloPrincipal._resolver_saludo(datetime(2026, 5, 16, 6, 0, 0)),
            "Buenos dias",
        )
        self.assertEqual(
            VistaModuloPrincipal._resolver_saludo(datetime(2026, 5, 16, 13, 0, 0)),
            "Buenas tardes",
        )
        self.assertEqual(
            VistaModuloPrincipal._resolver_saludo(datetime(2026, 5, 16, 22, 0, 0)),
            "Buenas noches",
        )

    def test_shell_principal_muestra_saludo_basico_en_encabezado(self) -> None:
        vista_principal = VistaModuloPrincipal()
        estado = EstadoModuloPrincipal(
            nombre_usuario="admin",
            nombre_completo="Admin Usuario",
            perfil="ADMINISTRADOR",
            metricas=(),
            analitica=AnaliticaDashboard((), (), (), (), ()),
            modulos=(
                ModuloNavegacion("dashboard", "Inicio", "Resumen operativo del sistema.", "home.svg"),
                ModuloNavegacion("barrios", "Barrios", "Gestion de barrios y organizacion territorial.", "map-2.svg"),
                ModuloNavegacion(
                    "historial_pagos",
                    "Historial de pagos",
                    "Consulta comprobantes emitidos y reimpresion operativa.",
                    "clock.svg",
                ),
            ),
            puede_abrir_mantenimiento=False,
        )
        vista_barrios = VistaBarrios()
        vista_historial = VistaHistorialPagos()
        vista_principal.registrar_modulo("barrios", vista_barrios)
        vista_principal.registrar_modulo("historial_pagos", vista_historial)

        vista_principal.mostrar_estado(estado)
        vista_principal.show()
        self.aplicacion.processEvents()

        self.assertIn("Admin", vista_principal._label_bienvenida.text())
        self.assertIn("Monitorea ingresos", vista_principal._label_subresumen.text())
        self.assertGreaterEqual(vista_principal._boton_perfil_header.minimumWidth(), 48)

        vista_principal.mostrar_modulo("barrios")
        self.aplicacion.processEvents()

        self.assertEqual(vista_principal._label_bienvenida.text(), "Barrios")
        self.assertEqual(
            vista_principal._label_subresumen.text(),
            "Gestion de barrios y organizacion territorial.",
        )
        vista_principal.mostrar_modulo("historial_pagos")
        self.aplicacion.processEvents()

        self.assertEqual(vista_principal._label_bienvenida.text(), "Historial de pagos")
        self.assertEqual(
            vista_principal._label_subresumen.text(),
            "Consulta comprobantes emitidos y reimpresion operativa.",
        )
        vista_barrios.close()
        vista_historial.close()
        vista_principal.close()

    def test_notificacion_casas_desaparece_tras_temporizador(self) -> None:
        vista = VistaCasas()

        vista.mostrar_mensaje("Casa actualizada correctamente.")

        self.assertFalse(vista._mensaje.isHidden())
        self.assertTrue(vista._temporizador_mensaje.isActive())
        self.assertEqual(
            vista._temporizador_mensaje.interval(),
            vista.DURACION_MENSAJE_MS,
        )

        vista._temporizador_mensaje.timeout.emit()

        self.assertTrue(vista._mensaje.isHidden())
        self.assertEqual(vista._mensaje.text(), "")
        vista.close()

    def test_dialogos_casas_optimizan_detalle_scroll_y_tabla_historial_estilizada(self) -> None:
        casa = Casa(
            identificador=7,
            abonado_id=3,
            abonado_nombre="Diana Flores",
            abonado_dni="0801199000033",
            barrio_nombre="San Jorge",
            direccion_referencia="Frente al pozo principal, pasaje norte",
            observaciones="Observacion administrativa larga para validar separacion visual.",
            estado_servicio="ACTIVO",
            estado_administrativo="SUSPENDIDA",
            motivo_estado_administrativo="REVISION_ADMINISTRATIVA",
            ha_tenido_servicio_activo=True,
            deuda_total_centavos=123450,
            meses_pendientes=4,
            meses_en_mora=2,
        )
        historial = [
            HistorialPropietarioCasa(
                identificador=1,
                fecha_cambio="2026-05-01 10:30:00",
                abonado_anterior_nombre="Ana Martinez",
                abonado_nuevo_nombre="Diana Flores",
                motivo="Actualizacion administrativa",
                usuario_nombre="Administrador",
            )
        ]

        dialogo_detalle = DialogoDetalleCasa(
            detalle=DetalleCasa(
                casa=casa,
                historial_propietarios=tuple(historial),
                ultima_fecha_cambio_dueno="2026-05-01 10:30:00",
            ),
            formateador_fecha=lambda valor: valor,
            formateador_moneda=lambda valor: f"L {valor / 100:,.2f}",
        )
        dialogo_detalle.show()
        self.aplicacion.processEvents()

        scroll = dialogo_detalle.findChild(QScrollArea, "scrollDetalleCasa")
        self.assertIsNotNone(scroll)
        self.assertTrue(scroll.widgetResizable())
        self.assertIn("QScrollArea#scrollDetalleCasa", dialogo_detalle.styleSheet())
        self.assertIn("QFrame#seccionDetalleSigqua", dialogo_detalle.styleSheet())
        self.assertIn("QLabel#tituloSeccionDetalleSigqua", dialogo_detalle.styleSheet())

        dialogo_historial = DialogoHistorialPropietariosCasa(
            casa=casa,
            historial=historial,
            formateador_fecha=lambda valor: valor,
        )
        dialogo_historial.show()
        self.aplicacion.processEvents()

        tabla_historial = dialogo_historial.findChild(QTableWidget, "tablaHistorialCasa")
        self.assertIsNotNone(tabla_historial)
        self.assertEqual(tabla_historial.viewport().objectName(), "viewportTablaHistorialCasa")
        self.assertIn("QTableWidget#tablaHistorialCasa", dialogo_historial.styleSheet())
        self.assertIn("QFrame#panelHistorialCasa", dialogo_historial.styleSheet())
        self.assertIn("QTableWidget#tablaHistorialCasa QHeaderView::section", dialogo_historial.styleSheet())

        dialogo_detalle.close()
        dialogo_historial.close()

    def test_dialogos_abonados_y_barrios_usan_scroll_y_secciones_optimizadas(self) -> None:
        dialogo_abonado = DialogoDetalleAbonado(
            abonado=Abonado(
                identificador=5,
                dni="0801199000055",
                nombre_completo="Victor Hugo Lopez Hernandez",
                telefono="9999-0001",
                barrio_nombre="Centro",
                direccion_referencia="Casa esquinera frente al parque central",
                observaciones="Observacion extensa para validar lectura y separacion visual.",
                estado="ACTIVO",
                total_casas=3,
                meses_en_mora=1,
                deuda_total_centavos=80500,
                tiene_plan_activo=True,
            ),
            fecha_creacion="2026-05-01 07:30:00",
            fecha_actualizada="2026-05-09 08:00:00",
            deuda_formateada="L 805.00",
        )
        dialogo_abonado.show()
        self.aplicacion.processEvents()

        scroll_abonado = dialogo_abonado.findChild(QScrollArea, "scrollDetalleAbonado")
        self.assertIsNotNone(scroll_abonado)
        self.assertTrue(scroll_abonado.widgetResizable())
        self.assertIn("QFrame#seccionDetalleSigqua", dialogo_abonado.styleSheet())
        self.assertIn("QLabel#tituloSeccionDetalleSigqua", dialogo_abonado.styleSheet())

        dialogo_barrio = DialogoDetalleBarrio(
            barrio=Barrio(
                identificador=2,
                nombre="San Jorge",
                estado="ACTIVO",
                observaciones="Observacion territorial larga para validar el nuevo bloque de detalle.",
                total_abonados=24,
                total_casas=28,
            ),
            fecha_creacion="2026-05-01 07:30:00",
            fecha_actualizada="2026-05-09 08:00:00",
        )
        dialogo_barrio.show()
        self.aplicacion.processEvents()

        scroll_barrio = dialogo_barrio.findChild(QScrollArea, "scrollDetalleBarrio")
        self.assertIsNotNone(scroll_barrio)
        self.assertTrue(scroll_barrio.widgetResizable())
        self.assertIn("QFrame#seccionDetalleSigqua", dialogo_barrio.styleSheet())
        self.assertIn("QLabel#tituloSeccionDetalleSigqua", dialogo_barrio.styleSheet())

        dialogo_abonado.close()
        dialogo_barrio.close()

    def test_formularios_y_confirmaciones_usan_modalidad_visual_armonizada(self) -> None:
        abonado = Abonado(
            identificador=3,
            dni="0801199000033",
            nombre_completo="Diana Flores",
            telefono="9999-3030",
            barrio_id=1,
            barrio_nombre="Centro",
            direccion_referencia="Dos cuadras al sur del tanque",
            observaciones="Observacion de prueba.",
            estado="ACTIVO",
        )
        barrio = Barrio(
            identificador=2,
            nombre="San Jorge",
            estado="ACTIVO",
            observaciones="Observacion del barrio.",
            total_abonados=10,
            total_casas=12,
        )
        casa = Casa(
            identificador=8,
            abonado_id=3,
            abonado_nombre="Diana Flores",
            abonado_dni="0801199000033",
            barrio_id=2,
            barrio_nombre="San Jorge",
            direccion_referencia="Casa frente al parque",
            observaciones="Observacion de casa.",
            estado_servicio="ACTIVO",
            estado_administrativo="OPERATIVA",
            motivo_estado_administrativo="NINGUNO",
            ha_tenido_servicio_activo=False,
        )

        dialogo_form_abonado = DialogoFormularioAbonado(
            barrios=[OpcionBarrio(1, "Centro"), OpcionBarrio(2, "San Jorge")],
            abonado=abonado,
        )
        dialogo_form_barrio = DialogoFormularioBarrio(barrio=barrio)
        dialogo_form_casa = DialogoFormularioCasa(
            barrios=[OpcionBarrioCasa(1, "Centro"), OpcionBarrioCasa(2, "San Jorge")],
            abonados=[OpcionAbonado(3, "Diana Flores", "0801199000033", "ACTIVO")],
            casa=casa,
        )
        dialogo_cambio_dueno = DialogoCambioDuenoCasa(
            casa=casa,
            abonados=[
                OpcionAbonado(3, "Diana Flores", "0801199000033", "ACTIVO"),
                OpcionAbonado(4, "Ernesto Lopez", "0801199000044", "ACTIVO"),
            ],
        )
        dialogo_confirm_abonado = DialogoConfirmacionEstadoAbonado(abonado)
        dialogo_confirm_barrio = DialogoConfirmacionEstadoBarrio(barrio)
        dialogo_confirm_casa = DialogoConfirmacionEstadoCasa(casa)

        for dialogo in (
            dialogo_form_abonado,
            dialogo_form_barrio,
            dialogo_form_casa,
            dialogo_cambio_dueno,
            dialogo_confirm_abonado,
            dialogo_confirm_barrio,
            dialogo_confirm_casa,
        ):
            dialogo.show()
            self.aplicacion.processEvents()
            self.assertGreaterEqual(dialogo.minimumWidth(), 520)
            self.assertIn("QFrame#bloqueDialogoSigqua", dialogo.styleSheet())
            dialogo.close()

    def test_shell_aplica_tema_sigqua_sin_selector_de_tema(self) -> None:
        vista_principal = VistaModuloPrincipal()
        vista_barrios = VistaBarrios()
        vista_abonados = VistaAbonados()
        vista_casas = VistaCasas()
        vista_planes = VistaPlanesPago()
        vista_pagos = VistaPagos()
        vista_historial = VistaHistorialPagos()
        vista_morosidad = VistaMorosidad()
        vista_reportes = VistaReportes()
        vista_usuarios = VistaUsuarios()
        vista_configuracion = VistaConfiguracion()

        vista_principal.registrar_modulo("barrios", vista_barrios)
        vista_principal.registrar_modulo("abonados", vista_abonados)
        vista_principal.registrar_modulo("casas", vista_casas)
        vista_principal.registrar_modulo("planes_pago", vista_planes)
        vista_principal.registrar_modulo("pagos", vista_pagos)
        vista_principal.registrar_modulo("historial_pagos", vista_historial)
        vista_principal.registrar_modulo("morosidad", vista_morosidad)
        vista_principal.registrar_modulo("reportes", vista_reportes)
        vista_principal.registrar_modulo("usuarios", vista_usuarios)
        vista_principal.registrar_modulo("configuracion", vista_configuracion)
        vista_principal.show()
        self.aplicacion.processEvents()

        vista_principal.aplicar_tema("tema_sigqua")
        self.aplicacion.processEvents()

        self.assertEqual(vista_principal._tema_actual, "tema_sigqua")
        self.assertFalse(hasattr(vista_principal, "_boton_tema"))
        self.assertEqual(vista_barrios._tema_actual, "tema_sigqua")
        self.assertEqual(vista_abonados._tema_actual, "tema_sigqua")
        self.assertEqual(vista_casas._tema_actual, "tema_sigqua")
        self.assertEqual(vista_planes._tema_actual, "tema_sigqua")
        self.assertEqual(vista_pagos._tema_actual, "tema_sigqua")
        self.assertEqual(vista_historial._tema_actual, "tema_sigqua")
        self.assertEqual(vista_morosidad._tema_actual, "tema_sigqua")
        self.assertEqual(vista_reportes._tema_actual, "tema_sigqua")
        self.assertEqual(vista_usuarios._tema_actual, "tema_sigqua")
        self.assertEqual(vista_configuracion._tema_actual, "tema_sigqua")
        self.assertNotIn("botonTemaHeader", vista_principal.styleSheet())
        self.assertEqual(vista_principal._paleta_tema["fondo_principal"], "#071A2D")
        self.assertIn('font-family: "Segoe UI"', vista_principal.styleSheet())
        vista_principal.aplicar_fondo_personalizado(
            activo=True,
            modo="DEGRADADO",
            color_primario="#102040",
            color_secundario="#304060",
        )
        self.assertTrue(vista_principal._fondo_personalizado_activo)
        self.assertEqual(vista_principal._fondo_personalizado_modo, "DEGRADADO")
        vista_principal.close()
        vista_barrios.close()
        vista_abonados.close()
        vista_casas.close()
        vista_planes.close()
        vista_pagos.close()
        vista_historial.close()
        vista_morosidad.close()
        vista_reportes.close()
        vista_usuarios.close()
        vista_configuracion.close()

    def test_vistas_planes_y_configuracion_siguen_patron_visual_compartido(self) -> None:
        vista_planes = VistaPlanesPago()
        vista_configuracion = VistaConfiguracion()
        vista_planes.show()
        vista_configuracion.show()
        self.aplicacion.processEvents()

        self.assertIn("QFrame#panelTablaPlanes", vista_planes.styleSheet())
        self.assertEqual(vista_planes._tabla.viewport().objectName(), "viewportTablaPlanes")
        self.assertEqual(vista_configuracion._tabs.count(), 5)
        self.assertEqual(vista_configuracion._tabs.tabText(0), "Organización")
        self.assertEqual(vista_configuracion._tabs.tabText(1), "Comprobantes")
        self.assertEqual(vista_configuracion._tabs.tabText(2), "Cobros y morosidad")
        self.assertEqual(vista_configuracion._tabs.tabText(3), "Respaldos")
        self.assertEqual(vista_configuracion._tabs.tabText(4), "Sistema")
        self.assertIn("QTabWidget#tabsConfiguracion QTabBar::tab:hover", vista_configuracion.styleSheet())
        self.assertIn("QTabWidget#tabsConfiguracion QTabBar::tab:selected", vista_configuracion.styleSheet())
        self.assertIn("QTabWidget#tabsConfiguracion QTabBar {", vista_configuracion.styleSheet())
        self.assertIsNotNone(
            vista_configuracion.findChild(QTextEdit, "documentoPreviewComprobanteConfiguracion")
        )
        self.assertIsNone(vista_configuracion.findChild(QWidget, "previewLaboratorioFondo"))

        vista_planes.close()
        vista_configuracion.close()

    def test_modulos_base_no_replican_titulo_en_contenido(self) -> None:
        vistas = (
            VistaBarrios(),
            VistaAbonados(),
            VistaCasas(),
            VistaPlanesPago(),
            VistaHistorialPagos(),
            VistaConfiguracion(),
        )

        try:
            for vista in vistas:
                titulos = [
                    label.text()
                    for label in vista.findChildren(QLabel)
                    if label.objectName() == "tituloModulo"
                ]
                self.assertEqual(titulos, [])
        finally:
            for vista in vistas:
                vista.close()

    def test_vista_usuarios_copia_patron_visual_simplificado_con_filtros_y_acciones(self) -> None:
        vista = VistaUsuarios()
        roles = [
            RolSistema(
                identificador=1,
                nombre="ADMINISTRADOR",
                descripcion="Acceso administrativo",
                estado="ACTIVO",
                es_sistema=True,
                total_usuarios=1,
                permisos=(
                    PermisoSistema("modulo.usuarios", "Acceso a Usuarios", "", "Usuarios"),
                    PermisoSistema("modulo.reportes", "Acceso a Reportes", "", "Reportes"),
                ),
            ),
            RolSistema(
                identificador=2,
                nombre="CAJERO",
                descripcion="Acceso de caja",
                estado="ACTIVO",
                es_sistema=True,
                total_usuarios=2,
                permisos=(PermisoSistema("modulo.pagos", "Acceso a Pagos", "", "Pagos"),),
            ),
        ]
        usuarios = [
            UsuarioSistema(
                identificador=1,
                nombre_usuario="admin",
                nombre_completo="Admin Usuario",
                correo="admin@sigqua.local",
                estado="ACTIVO",
                roles=("ADMINISTRADOR",),
            )
        ]

        vista.mostrar_roles(roles, [])
        vista.mostrar_resumen(
            ResumenUsuarios(
                total_usuarios=1,
                usuarios_activos=1,
                administradores=1,
                accesos_hoy=1,
            )
        )
        vista.mostrar_usuarios(usuarios, lambda valor: "Sin registro" if valor is None else valor)
        vista.show()
        self.aplicacion.processEvents()

        self.assertEqual(vista._combo_roles.count(), 3)
        self.assertFalse(hasattr(vista, "_tabs"))
        self.assertEqual(vista._tabla.viewport().objectName(), "viewportTablaUsuarios")
        self.assertIn("QFrame#panelTablaUsuarios", vista.styleSheet())
        self.assertIn("QPushButton#chipFiltroUsuario", vista.styleSheet())

        fila_acciones = vista._crear_acciones_fila(usuarios[0])
        botones_accion = fila_acciones.findChildren(QToolButton, "botonIconoFilaUsuario")
        self.assertEqual(len(botones_accion), 4)
        self.assertTrue(all(not boton.text() for boton in botones_accion))
        self.assertTrue(all(not boton.icon().isNull() for boton in botones_accion))
        self.assertTrue(all(boton.iconSize().width() == 18 for boton in botones_accion))
        self.assertEqual(fila_acciones.minimumHeight(), 58)
        self.assertFalse(
            any(
                label.objectName() == "tituloModulo" and label.text() == "Usuarios"
                for label in vista.findChildren(type(vista._estado_vacio))
            )
        )
        vista.close()


if __name__ == "__main__":
    unittest.main()
