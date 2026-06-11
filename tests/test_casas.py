from __future__ import annotations

import csv
import shutil
import sys
import unittest
import uuid
from contextlib import closing
from pathlib import Path

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QScrollArea, QToolButton


RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
RUTA_SRC = RAIZ_PROYECTO / "src"

if str(RUTA_SRC) not in sys.path:
    sys.path.insert(0, str(RUTA_SRC))

from comun.base_datos import GestorBaseDatos  # noqa: E402
from comun.configuracion.gestor_rutas import GestorRutas  # noqa: E402
from tests.utilidades_base_datos import inicializar_base_datos_prueba  # noqa: E402
from modulos.autenticacion.entidades import UsuarioAutenticado  # noqa: E402
from modulos.casas.controlador import ControladorCasas  # noqa: E402
from modulos.casas.entidades import (  # noqa: E402
    Casa,
    DetalleCasa,
    ESTADO_ADMINISTRATIVO_SUSPENDIDA,
    FILTRO_CASAS_CON_MORA,
    FILTRO_CASAS_TODAS,
    FILTRO_CASAS_SIN_PROPIETARIO,
    FormularioCorteServicioCasa,
    FormularioCasa,
    OpcionAbonado,
    OpcionBarrio,
    PaginaCasas,
    ResultadoGestionCasas,
)
from modulos.casas.repositorio import RepositorioCasasSQLite  # noqa: E402
from modulos.casas.servicio import ServicioCasas  # noqa: E402
from modulos.casas.vista import DialogoFormularioCasa, VistaCasas  # noqa: E402


class TestCasas(unittest.TestCase):
    def setUp(self) -> None:
        self.raiz_temporal = RAIZ_PROYECTO / "tests" / f"_tmp_casas_{uuid.uuid4().hex}"
        (self.raiz_temporal / "database" / "migrations").mkdir(parents=True, exist_ok=True)

        for ruta_migracion in (RAIZ_PROYECTO / "database" / "migrations").glob("*.sql"):
            (self.raiz_temporal / "database" / "migrations" / ruta_migracion.name).write_text(
                ruta_migracion.read_text(encoding="utf-8"),
                encoding="utf-8",
            )

        self.gestor_rutas = GestorRutas(raiz_proyecto=self.raiz_temporal)
        self.gestor_base_datos = GestorBaseDatos(self.gestor_rutas)
        inicializar_base_datos_prueba(self.gestor_base_datos)
        self.repositorio = RepositorioCasasSQLite(self.gestor_base_datos)
        self.servicio = ServicioCasas(self.repositorio)

    def tearDown(self) -> None:
        if self.raiz_temporal.exists():
            shutil.rmtree(self.raiz_temporal, ignore_errors=True)

    def test_resumen_y_listado_inicial_reflejan_semilla(self) -> None:
        resumen = self.servicio.obtener_resumen()
        pagina = self.servicio.listar()

        self.assertEqual(resumen.total_casas, 4)
        self.assertEqual(resumen.casas_activas, 3)
        self.assertEqual(resumen.casas_con_deuda, 2)
        self.assertEqual(resumen.casas_morosas, 1)
        self.assertEqual(pagina.total_registros, 4)
        self.assertEqual(pagina.items[1].codigo, "CA-002")
        self.assertTrue(pagina.items[1].tiene_plan_activo)

    def test_detalle_muestra_plan_activo_y_historial(self) -> None:
        detalle_plan = self.servicio.obtener_detalle(2)
        detalle_historial = self.servicio.obtener_detalle(4)

        self.assertIsNotNone(detalle_plan)
        self.assertIsNotNone(detalle_historial)
        assert detalle_plan is not None
        assert detalle_historial is not None
        self.assertIsNotNone(detalle_plan.plan_activo)
        self.assertEqual(detalle_plan.plan_activo.cuotas_pendientes, 2)
        self.assertEqual(detalle_plan.plan_activo.saldo_pendiente_centavos, 70000)
        self.assertEqual(len(detalle_historial.historial_propietarios), 1)
        self.assertIn("Ana Martinez", detalle_historial.historial_propietarios[0].abonado_anterior_nombre)
        self.assertIn("Ernesto Lopez", detalle_historial.historial_propietarios[0].abonado_nuevo_nombre)

    def test_cambio_dueno_migra_deuda_plan_e_historial(self) -> None:
        resultado = self.servicio.cambiar_dueno(
            casa_id=2,
            nuevo_abonado_id=1,
            motivo="Traspaso administrativo de prueba",
            actor_id=1,
        )

        self.assertTrue(resultado.exito)
        detalle = self.servicio.obtener_detalle(2)
        self.assertIsNotNone(detalle)
        assert detalle is not None
        self.assertEqual(detalle.casa.abonado_nombre, "Ana Martinez")
        self.assertIsNotNone(detalle.plan_activo)

        with closing(self.gestor_base_datos.obtener_conexion()) as conexion:
            cargos = conexion.execute(
                """
                SELECT DISTINCT abonado_id
                FROM cargos
                WHERE casa_id = 2
                  AND estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDO')
                  AND saldo_pendiente_centavos > 0;
                """
            ).fetchall()
            plan = conexion.execute(
                "SELECT abonado_id FROM planes_pago WHERE casa_id = 2 AND estado = 'ACTIVO' LIMIT 1;"
            ).fetchone()

        self.assertEqual([int(fila["abonado_id"]) for fila in cargos], [1])
        self.assertEqual(int(plan["abonado_id"]), 1)
        historial = self.servicio.listar_historial_propietarios(2)
        self.assertGreaterEqual(len(historial), 1)
        self.assertEqual(historial[0].abonado_nuevo_nombre, "Ana Martinez")

    def test_guardar_rechaza_abonado_inactivo(self) -> None:
        with closing(self.gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                conexion.execute("UPDATE abonados SET estado = 'INACTIVO' WHERE id = 1;")

        resultado = self.servicio.guardar(
            identificador=None,
            abonado_id=1,
            barrio_id=1,
            direccion_referencia="Casa de prueba",
            observaciones="",
            estado_servicio="ACTIVO",
            estado_administrativo="OPERATIVA",
            motivo_estado_administrativo="NINGUNO",
            ha_tenido_servicio_activo=False,
        )

        self.assertFalse(resultado.exito)
        self.assertIn("abonados activos", resultado.mensaje)

    def test_guardar_permite_editar_casa_con_abonado_actual_inactivo(self) -> None:
        with closing(self.gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                conexion.execute("UPDATE abonados SET estado = 'INACTIVO' WHERE id = 2;")

        resultado = self.servicio.guardar(
            identificador=2,
            abonado_id=2,
            barrio_id=2,
            direccion_referencia="Casa 02 actualizada",
            observaciones="Actualizacion valida con abonado actual inactivo",
            estado_servicio="ACTIVO",
            estado_administrativo="SUSPENDIDA",
            motivo_estado_administrativo="REVISION_ADMINISTRATIVA",
            ha_tenido_servicio_activo=True,
        )

        self.assertTrue(resultado.exito)
        casa = self.servicio.obtener_por_id(2)
        self.assertIsNotNone(casa)
        assert casa is not None
        self.assertEqual(casa.direccion_referencia, "Casa 02 actualizada")
        self.assertEqual(casa.estado_servicio, "ACTIVO")
        self.assertEqual(casa.estado_administrativo, "SUSPENDIDA")

    def test_guardar_rechaza_cambio_fisico_desde_edicion_normal(self) -> None:
        resultado = self.servicio.guardar(
            identificador=2,
            abonado_id=2,
            barrio_id=2,
            direccion_referencia="Casa 02 actualizada",
            observaciones="Intento de corte desde formulario",
            estado_servicio="CORTADO",
            estado_administrativo="OPERATIVA",
            motivo_estado_administrativo="NINGUNO",
            ha_tenido_servicio_activo=True,
        )

        self.assertFalse(resultado.exito)
        self.assertIn("estado fisico del servicio no se edita", resultado.mensaje)

    def test_cortar_servicio_registra_proceso_y_conserva_dimension_administrativa(self) -> None:
        with closing(self.gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                conexion.execute(
                    """
                    UPDATE casas
                    SET estado_administrativo = 'SUSPENDIDA',
                        motivo_estado_administrativo = 'REVISION_ADMINISTRATIVA'
                    WHERE id = 2;
                    """
                )

        resultado = self.servicio.cortar_servicio(
            casa_id=2,
            observaciones="Corte operativo manual de prueba",
            actor_id=1,
        )

        self.assertTrue(resultado.exito)
        casa = self.servicio.obtener_por_id(2)
        self.assertIsNotNone(casa)
        assert casa is not None
        self.assertEqual(casa.estado_servicio, "CORTADO")
        self.assertEqual(casa.estado_administrativo, ESTADO_ADMINISTRATIVO_SUSPENDIDA)

        with closing(self.gestor_base_datos.obtener_conexion()) as conexion:
            proceso = conexion.execute(
                """
                SELECT tipo, estado, observaciones, usuario_id
                FROM procesos_servicio
                WHERE casa_id = 2 AND tipo = 'CORTE'
                ORDER BY id DESC
                LIMIT 1;
                """
            ).fetchone()

        self.assertIsNotNone(proceso)
        assert proceso is not None
        self.assertEqual(str(proceso["tipo"]), "CORTE")
        self.assertEqual(str(proceso["estado"]), "EJECUTADO")
        self.assertEqual(str(proceso["observaciones"]), "Corte operativo manual de prueba")
        self.assertEqual(int(proceso["usuario_id"]), 1)

    def test_cortar_servicio_rechaza_casa_ya_cortada(self) -> None:
        with closing(self.gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                conexion.execute("UPDATE casas SET estado_servicio = 'CORTADO' WHERE id = 2;")

        resultado = self.servicio.cortar_servicio(
            casa_id=2,
            observaciones="No deberia aplicar",
            actor_id=3,
        )

        self.assertFalse(resultado.exito)
        self.assertIn("ya tiene el servicio cortado", resultado.mensaje)

    def test_filtros_y_exportacion(self) -> None:
        pagina_con_mora = self.servicio.listar(filtro_rapido=FILTRO_CASAS_CON_MORA)
        pagina_sin_propietario = self.servicio.listar(filtro_rapido=FILTRO_CASAS_SIN_PROPIETARIO)
        pagina_por_codigo = self.servicio.listar(filtro="CA-002")

        self.assertEqual(pagina_con_mora.total_registros, 1)
        self.assertEqual(pagina_con_mora.items[0].codigo, "CA-002")
        self.assertEqual(pagina_sin_propietario.total_registros, 0)
        self.assertEqual(pagina_por_codigo.total_registros, 1)
        self.assertEqual(pagina_por_codigo.items[0].codigo, "CA-002")

        ruta_exportacion = self.raiz_temporal / "casas.csv"
        resultado_exportacion = self.servicio.exportar_csv(str(ruta_exportacion))

        self.assertTrue(resultado_exportacion.exito)
        with ruta_exportacion.open("r", encoding="utf-8", newline="") as archivo_csv:
            filas = list(csv.reader(archivo_csv))

        self.assertEqual(
            filas[0],
            [
                "Codigo",
                "Abonado actual",
                "DNI",
                "Barrio",
                "Referencia",
                "Meses pendientes",
                "Meses en mora",
                "Estado",
                "Creado",
                "Ultima actualizacion",
                "Plan activo",
                "Deuda pendiente",
            ],
        )
        self.assertEqual(filas[2][0], "CA-002")
        self.assertTrue(filas[2][8])


class VistaCasasStub(QObject):
    filtro_texto_cambiado = Signal(str)
    filtro_rapido_cambiado = Signal(str)
    pagina_cambiada = Signal(int)
    exportar_solicitado = Signal()
    nueva_casa_solicitada = Signal()
    detalle_casa_solicitado = Signal(int)
    editar_casa_solicitado = Signal(int)
    cambio_estado_solicitado = Signal(int)
    corte_servicio_solicitado = Signal(int)
    historial_casa_solicitado = Signal(int)
    cambio_dueno_solicitado = Signal(int)

    def __init__(self) -> None:
        super().__init__()
        self.mensajes: list[tuple[str, bool]] = []
        self.resumen = None
        self.pagina = None
        self.formulario = None
        self.formulario_cambio_dueno = None
        self.formulario_corte = None
        self.detalle_resultado = "cerrar"
        self.confirmacion_estado = True
        self.exportacion = ""
        self.detalle_mostrado = None
        self.historial_mostrado = None

    def mostrar_resumen(self, resumen) -> None:
        self.resumen = resumen

    def mostrar_casas(self, pagina) -> None:
        self.pagina = pagina

    def mostrar_mensaje(self, mensaje: str, es_error: bool = False) -> None:
        self.mensajes.append((mensaje, es_error))

    def solicitar_datos_casa(self, barrios, abonados, casa=None):
        return self.formulario

    def solicitar_cambio_dueno(self, casa, abonados):
        return self.formulario_cambio_dueno

    def solicitar_corte_servicio(self, detalle, formateador_moneda):
        return self.formulario_corte

    def mostrar_detalle_casa(self, detalle, formateador_fecha, formateador_moneda):
        self.detalle_mostrado = detalle
        return self.detalle_resultado

    def mostrar_historial_propietarios(self, casa, historial, formateador_fecha) -> None:
        self.historial_mostrado = (casa, tuple(historial))

    def confirmar_cambio_estado_casa(self, casa) -> bool:
        return self.confirmacion_estado

    def solicitar_ruta_exportacion(self) -> str:
        return self.exportacion


class ServicioCasasStub:
    def __init__(self) -> None:
        self.resumen = object()
        self.pagina = PaginaCasas(
            items=[],
            pagina_actual=1,
            tamano_pagina=10,
            total_registros=0,
        )
        self.casa = Casa(
            identificador=2,
            abonado_id=2,
            abonado_nombre="Carlos Ramirez",
            abonado_dni="0801199000022",
            abonado_estado="ACTIVO",
            barrio_id=2,
            barrio_nombre="San Jorge",
            direccion_referencia="Casa 02",
            estado_servicio="ACTIVO",
            estado_administrativo="OPERATIVA",
            motivo_estado_administrativo="NINGUNO",
            ha_tenido_servicio_activo=True,
        )
        self.detalle = DetalleCasa(casa=self.casa)
        self.guardados: list[tuple] = []
        self.cambios_estado: list[tuple] = []
        self.cortes: list[tuple] = []
        self.cambios_dueno: list[tuple] = []
        self.exportaciones: list[tuple] = []

    def obtener_resumen(self):
        return self.resumen

    def listar(self, filtro="", filtro_rapido="", pagina=1):
        return self.pagina

    def listar_barrios_disponibles(self):
        return [OpcionBarrio(1, "Centro")]

    def listar_abonados_disponibles(self):
        return [OpcionAbonado(1, "Ana Martinez", "0801199000011", "ACTIVO")]

    def obtener_por_id(self, casa_id: int):
        return self.casa if casa_id == 2 else None

    def obtener_detalle(self, casa_id: int):
        return self.detalle if casa_id == 2 else None

    def listar_historial_propietarios(self, casa_id: int):
        return []

    def guardar(self, **kwargs):
        self.guardados.append(tuple(kwargs.items()))
        return ResultadoGestionCasas(True, "ok", "OK")

    def cambiar_estado(self, casa_id: int, estado_actual: str, motivo_actual: str):
        self.cambios_estado.append((casa_id, estado_actual, motivo_actual))
        return ResultadoGestionCasas(True, "estado", "OK")

    def cortar_servicio(self, casa_id: int, observaciones: str, actor_id: int | None):
        self.cortes.append((casa_id, observaciones, actor_id))
        return ResultadoGestionCasas(True, "corte", "OK")

    def cambiar_dueno(
        self,
        casa_id: int,
        nuevo_abonado_id: int | None,
        motivo: str,
        actor_id: int | None,
        observacion: str = "",
    ):
        self.cambios_dueno.append((casa_id, nuevo_abonado_id, motivo, actor_id, observacion))
        return ResultadoGestionCasas(True, "dueno", "OK")

    def exportar_csv(self, ruta_destino: str, filtro: str = "", filtro_rapido: str = ""):
        self.exportaciones.append((ruta_destino, filtro, filtro_rapido))
        return ResultadoGestionCasas(True, "exportado", "OK")

    @staticmethod
    def formatear_fecha_hora(valor: str) -> str:
        return valor

    @staticmethod
    def formatear_moneda(valor: int) -> str:
        return str(valor)


class TestControladorCasas(unittest.TestCase):
    def test_acciones_crud_y_auxiliares_disparan_servicio_correcto(self) -> None:
        vista = VistaCasasStub()
        servicio = ServicioCasasStub()
        controlador = ControladorCasas(servicio, vista)
        actor = UsuarioAutenticado(
            identificador=9,
            nombre_usuario="admin",
            nombre_completo="Administrador",
            correo="admin@sigqua.local",
            estado="ACTIVO",
        )

        controlador.mostrar_para_actor(actor)
        self.assertIs(vista.resumen, servicio.resumen)
        self.assertIs(vista.pagina, servicio.pagina)

        vista.formulario = FormularioCasa(
            identificador=None,
            abonado_id=1,
            barrio_id=1,
            direccion_referencia="Nueva referencia",
            observaciones="Obs",
            estado_servicio="ACTIVO",
            estado_administrativo="OPERATIVA",
            motivo_estado_administrativo="NINGUNO",
            ha_tenido_servicio_activo=False,
        )
        vista.nueva_casa_solicitada.emit()
        self.assertEqual(len(servicio.guardados), 1)

        vista.formulario = FormularioCasa(
            identificador=2,
            abonado_id=1,
            barrio_id=1,
            direccion_referencia="Referencia editada",
            observaciones="Obs editada",
            estado_servicio="ACTIVO",
            estado_administrativo="SUSPENDIDA",
            motivo_estado_administrativo="REVISION_ADMINISTRATIVA",
            ha_tenido_servicio_activo=True,
        )
        vista.editar_casa_solicitado.emit(2)
        self.assertEqual(len(servicio.guardados), 2)

        vista.detalle_resultado = "editar"
        vista.detalle_casa_solicitado.emit(2)
        self.assertEqual(len(servicio.guardados), 3)

        vista.formulario_corte = FormularioCorteServicioCasa(
            casa_id=2,
            observaciones="Corte solicitado desde detalle",
        )
        vista.detalle_resultado = "cortar_servicio"
        vista.detalle_casa_solicitado.emit(2)
        self.assertEqual(servicio.cortes, [(2, "Corte solicitado desde detalle", 9)])

        vista.confirmacion_estado = True
        vista.cambio_estado_solicitado.emit(2)
        self.assertEqual(servicio.cambios_estado, [(2, "OPERATIVA", "NINGUNO")])

        class CambioDuenoStub:
            nuevo_abonado_id = 1
            motivo = "Prueba de cambio"
            observacion = "Observacion de cambio"

        vista.formulario_cambio_dueno = CambioDuenoStub()
        vista.cambio_dueno_solicitado.emit(2)
        self.assertEqual(servicio.cambios_dueno, [(2, 1, "Prueba de cambio", 9, "Observacion de cambio")])

        vista.historial_casa_solicitado.emit(2)
        self.assertIsNotNone(vista.historial_mostrado)

        vista.exportacion = "casas.csv"
        vista.exportar_solicitado.emit()
        self.assertEqual(servicio.exportaciones, [("casas.csv", "", FILTRO_CASAS_TODAS)])


class TestVistaCasasAcciones(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.aplicacion = QApplication.instance() or QApplication([])

    def test_botones_de_fila_emiten_senales_reales(self) -> None:
        vista = VistaCasas()
        eventos: list[tuple[str, int]] = []
        vista.detalle_casa_solicitado.connect(lambda casa_id: eventos.append(("detalle", casa_id)))

        vista.mostrar_casas(
            PaginaCasas(
                items=[
                    Casa(
                        identificador=2,
                        abonado_nombre="Carlos Ramirez",
                        barrio_nombre="San Jorge",
                        estado_servicio="ACTIVO",
                        estado_administrativo="OPERATIVA",
                    )
                ],
                pagina_actual=1,
                tamano_pagina=10,
                total_registros=1,
            )
        )
        vista.show()
        self.aplicacion.processEvents()

        contenedor_acciones = vista._tabla.cellWidget(0, 8)
        self.assertIsNotNone(contenedor_acciones)
        botones = contenedor_acciones.findChildren(QToolButton, "botonIconoFilaCasa")
        self.assertEqual(len(botones), 1)
        self.assertEqual(botones[0].toolTip(), "Ver detalle")

        QTest.mouseClick(botones[0], Qt.MouseButton.LeftButton)
        self.aplicacion.processEvents()

        self.assertEqual(eventos, [("detalle", 2)])
        vista.close()

    def test_boton_cortar_no_se_muestra_para_casa_cortada(self) -> None:
        vista = VistaCasas()
        vista.mostrar_casas(
            PaginaCasas(
                items=[
                    Casa(
                        identificador=3,
                        abonado_nombre="Ana Martinez",
                        barrio_nombre="Centro",
                        estado_servicio="CORTADO",
                        estado_administrativo="OPERATIVA",
                    )
                ],
                pagina_actual=1,
                tamano_pagina=10,
                total_registros=1,
            )
        )
        vista.show()
        self.aplicacion.processEvents()

        contenedor_acciones = vista._tabla.cellWidget(0, 8)
        self.assertIsNotNone(contenedor_acciones)
        botones = contenedor_acciones.findChildren(QToolButton, "botonIconoFilaCasa")
        tooltips = {boton.toolTip() for boton in botones}
        self.assertNotIn("Cortar servicio", tooltips)
        self.assertEqual(tooltips, {"Ver detalle"})
        vista.close()

    def test_formulario_edicion_bloquea_estado_fisico(self) -> None:
        dialogo = DialogoFormularioCasa(
            barrios=[OpcionBarrio(1, "Centro")],
            abonados=[OpcionAbonado(2, "Carlos Ramirez", "0801199000022", "ACTIVO")],
            casa=Casa(
                identificador=2,
                abonado_id=2,
                abonado_nombre="Carlos Ramirez",
                abonado_dni="0801199000022",
                barrio_id=1,
                barrio_nombre="Centro",
                estado_servicio="ACTIVO",
                estado_administrativo="OPERATIVA",
                ha_tenido_servicio_activo=True,
            ),
        )
        self.assertFalse(dialogo._combo_estado.isEnabled())
        dialogo.close()

    def test_formulario_casa_usa_buscadores_y_preserva_ids(self) -> None:
        dialogo = DialogoFormularioCasa(
            barrios=[OpcionBarrio(1, "Centro"), OpcionBarrio(2, "San Jorge")],
            abonados=[
                OpcionAbonado(2, "Carlos Ramirez", "0801199000022", "ACTIVO"),
                OpcionAbonado(3, "Diana Flores", "0801199000033", "ACTIVO"),
            ],
        )
        dialogo._campo_abonado.seleccionar_por_id(3, "Diana Flores | 0801199000033")
        dialogo._campo_barrio.seleccionar_por_id(2, "San Jorge")

        formulario = dialogo.obtener_formulario()
        scroll = dialogo.findChild(QScrollArea, "scrollFormularioCasa")

        self.assertEqual(formulario.abonado_id, 3)
        self.assertEqual(formulario.barrio_id, 2)
        self.assertIsNotNone(scroll)
        dialogo.close()


if __name__ == "__main__":
    unittest.main()

