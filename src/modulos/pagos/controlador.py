"""Controlador del modulo de pagos."""

from __future__ import annotations

from collections.abc import Callable

from comun.actualizaciones import EventoModuloActualizado, bus_actualizaciones_modulos
from modulos.autenticacion.entidades import UsuarioAutenticado
from modulos.pagos.entidades import FormularioPago, ResumenConfirmacionPago, ResultadoPago
from modulos.pagos.servicio import ServicioPagos
from modulos.pagos.vista import VistaPagos


class ControladorPagos:
    """Conecta la vista de pagos con sus reglas de negocio."""

    def __init__(self, servicio_pagos: ServicioPagos, vista_pagos: VistaPagos):
        self.servicio_pagos = servicio_pagos
        self.vista_pagos = vista_pagos
        self._actor: UsuarioAutenticado | None = None
        self._conectar_senales()
        bus_actualizaciones_modulos.actualizacion_emitida.connect(self._manejar_actualizacion_modulo)

    def mostrar_para_actor(self, actor: UsuarioAutenticado) -> None:
        self._actor = actor
        self._refrescar()

    def _conectar_senales(self) -> None:
        self.vista_pagos.buscar_solicitado.connect(self._refrescar)
        self.vista_pagos.casa_mensual_solicitada.connect(self._cargar_cargos_mensuales)
        self.vista_pagos.casa_conexion_solicitada.connect(self._cargar_diagnostico_conexion)
        self.vista_pagos.casa_reconexion_solicitada.connect(self._cargar_diagnostico_reconexion)
        self.vista_pagos.casa_plan_solicitada.connect(self._cargar_diagnostico_plan)
        self.vista_pagos.previsualizacion_pago_solicitada.connect(self._previsualizar_pago_mensual)
        self.vista_pagos.previsualizacion_conexion_solicitada.connect(self._previsualizar_pago_conexion)
        self.vista_pagos.previsualizacion_reconexion_solicitada.connect(self._previsualizar_pago_reconexion)
        self.vista_pagos.previsualizacion_plan_solicitada.connect(self._previsualizar_pago_plan)
        self.vista_pagos.registrar_pago_solicitado.connect(self._registrar_pago)
        self.vista_pagos.registrar_pago_conexion_solicitado.connect(self._registrar_pago_conexion)
        self.vista_pagos.registrar_pago_reconexion_solicitado.connect(self._registrar_pago_reconexion)
        self.vista_pagos.registrar_pago_plan_solicitado.connect(self._registrar_pago_plan)
        self.vista_pagos.comprobante_solicitado.connect(self._mostrar_comprobante)

    def _refrescar(self, filtro: str = "") -> None:
        estado = self.servicio_pagos.obtener_estado(filtro=filtro)
        self.vista_pagos.mostrar_estado(
            estado,
            self.servicio_pagos.formatear_moneda,
            self.servicio_pagos.formatear_fecha,
            mostrar_casas=bool(filtro.strip()),
        )
        casa_id = self.vista_pagos.obtener_casa_seleccionada_id()
        if casa_id is not None:
            self._cargar_cargos_mensuales(casa_id)
        casa_conexion_id = self.vista_pagos.obtener_casa_conexion_seleccionada_id()
        if casa_conexion_id is not None:
            self._cargar_diagnostico_conexion(casa_conexion_id)
        casa_reconexion_id = self.vista_pagos.obtener_casa_reconexion_seleccionada_id()
        if casa_reconexion_id is not None:
            self._cargar_diagnostico_reconexion(casa_reconexion_id)
        casa_plan_id = self.vista_pagos.obtener_casa_plan_seleccionada_id()
        if casa_plan_id is not None:
            self._cargar_diagnostico_plan(casa_plan_id)

    def _cargar_cargos_mensuales(self, casa_id: int) -> None:
        cargos = self.servicio_pagos.obtener_cargos_mensuales(casa_id)
        diagnostico = self.servicio_pagos.obtener_diagnostico_pago_mensual(casa_id)
        self.vista_pagos.mostrar_cargos_mensuales(casa_id, cargos, diagnostico)

    def _cargar_diagnostico_conexion(self, casa_id: int) -> None:
        diagnostico = self.servicio_pagos.obtener_diagnostico_conexion(casa_id)
        self.vista_pagos.mostrar_diagnostico_conexion(casa_id, diagnostico)

    def _cargar_diagnostico_reconexion(self, casa_id: int) -> None:
        diagnostico = self.servicio_pagos.obtener_diagnostico_reconexion(casa_id)
        self.vista_pagos.mostrar_diagnostico_reconexion(casa_id, diagnostico)

    def _cargar_diagnostico_plan(self, casa_id: int) -> None:
        diagnostico = self.servicio_pagos.obtener_diagnostico_plan(casa_id)
        self.vista_pagos.mostrar_diagnostico_plan(casa_id, diagnostico)

    def _previsualizar_pago_mensual(self, formulario: FormularioPago) -> None:
        confirmacion = self.servicio_pagos.previsualizar_pago_mensual(formulario)
        if isinstance(confirmacion, ResultadoPago):
            self.vista_pagos.mostrar_previsualizacion_pago(None, confirmacion)
            return
        if not isinstance(confirmacion, ResumenConfirmacionPago):
            self.vista_pagos.mostrar_previsualizacion_pago(
                None,
                ResultadoPago(False, "No fue posible preparar la previsualizacion.", "ERROR"),
            )
            return
        self.vista_pagos.mostrar_previsualizacion_pago(
            confirmacion,
            None,
            self.servicio_pagos.formatear_moneda,
        )

    def _previsualizar_pago_conexion(self, formulario: FormularioPago) -> None:
        confirmacion = self.servicio_pagos.previsualizar_pago_conexion(formulario)
        if isinstance(confirmacion, ResultadoPago):
            self.vista_pagos.mostrar_previsualizacion_conexion(None, confirmacion)
            return
        if not isinstance(confirmacion, ResumenConfirmacionPago):
            self.vista_pagos.mostrar_previsualizacion_conexion(
                None,
                ResultadoPago(False, "No fue posible preparar la previsualizacion.", "ERROR"),
            )
            return
        self.vista_pagos.mostrar_previsualizacion_conexion(
            confirmacion,
            None,
            self.servicio_pagos.formatear_moneda,
        )

    def _previsualizar_pago_reconexion(self, formulario: FormularioPago) -> None:
        confirmacion = self.servicio_pagos.previsualizar_pago_reconexion(formulario)
        if isinstance(confirmacion, ResultadoPago):
            self.vista_pagos.mostrar_previsualizacion_reconexion(None, confirmacion)
            return
        if not isinstance(confirmacion, ResumenConfirmacionPago):
            self.vista_pagos.mostrar_previsualizacion_reconexion(
                None,
                ResultadoPago(False, "No fue posible preparar la previsualizacion.", "ERROR"),
            )
            return
        self.vista_pagos.mostrar_previsualizacion_reconexion(
            confirmacion,
            None,
            self.servicio_pagos.formatear_moneda,
        )

    def _previsualizar_pago_plan(self, formulario: FormularioPago) -> None:
        confirmacion = self.servicio_pagos.previsualizar_pago_plan(formulario)
        if isinstance(confirmacion, ResultadoPago):
            self.vista_pagos.mostrar_previsualizacion_plan(None, confirmacion)
            return
        if not isinstance(confirmacion, ResumenConfirmacionPago):
            self.vista_pagos.mostrar_previsualizacion_plan(
                None,
                ResultadoPago(False, "No fue posible preparar la previsualizacion.", "ERROR"),
            )
            return
        self.vista_pagos.mostrar_previsualizacion_plan(
            confirmacion,
            None,
            self.servicio_pagos.formatear_moneda,
        )

    def _registrar_pago(self, formulario: FormularioPago) -> None:
        confirmacion = self.servicio_pagos.preparar_confirmacion(formulario)
        if isinstance(confirmacion, ResultadoPago):
            self.vista_pagos.mostrar_previsualizacion_pago(None, confirmacion)
            return
        if not isinstance(confirmacion, ResumenConfirmacionPago):
            self.vista_pagos.mostrar_mensaje("No fue posible preparar la confirmacion.", es_error=True)
            return
        if not self.vista_pagos.confirmar_pago(
            confirmacion,
            self.servicio_pagos.formatear_moneda,
        ):
            return
        actor_id = self._actor.identificador if self._actor is not None else None
        resultado = self.servicio_pagos.registrar_pago(formulario, actor_id=actor_id)
        self.vista_pagos.mostrar_mensaje(resultado.mensaje, es_error=not resultado.exito)
        if resultado.exito:
            comprobante_id = resultado.comprobante.pago_id if resultado.comprobante is not None else None
            self.vista_pagos.reiniciar_flujo_mensual()
            self._refrescar()
            bus_actualizaciones_modulos.emitir(
                modulo_origen="pagos",
                modulos_afectados=("historial_pagos", "morosidad", "reportes"),
            )
            if comprobante_id is not None:
                self._abrir_dialogo_comprobante(comprobante_id)

    def _registrar_pago_conexion(self, formulario: FormularioPago) -> None:
        self._registrar_pago_activacion(
            formulario,
            self.vista_pagos.mostrar_previsualizacion_conexion,
            self.vista_pagos.reiniciar_flujo_conexion,
        )

    def _registrar_pago_reconexion(self, formulario: FormularioPago) -> None:
        self._registrar_pago_activacion(
            formulario,
            self.vista_pagos.mostrar_previsualizacion_reconexion,
            self.vista_pagos.reiniciar_flujo_reconexion,
        )

    def _registrar_pago_plan(self, formulario: FormularioPago) -> None:
        self._registrar_pago_activacion(
            formulario,
            self.vista_pagos.mostrar_previsualizacion_plan,
            self.vista_pagos.reiniciar_flujo_plan,
        )

    def _registrar_pago_activacion(
        self,
        formulario: FormularioPago,
        mostrar_previsualizacion: Callable[[ResumenConfirmacionPago | None, ResultadoPago | None], None],
        reiniciar_flujo: Callable[[], None],
    ) -> None:
        confirmacion = self.servicio_pagos.preparar_confirmacion(formulario)
        if isinstance(confirmacion, ResultadoPago):
            mostrar_previsualizacion(None, confirmacion)
            return
        if not isinstance(confirmacion, ResumenConfirmacionPago):
            self.vista_pagos.mostrar_mensaje("No fue posible preparar la confirmacion.", es_error=True)
            return
        if not self.vista_pagos.confirmar_pago(
            confirmacion,
            self.servicio_pagos.formatear_moneda,
        ):
            return
        actor_id = self._actor.identificador if self._actor is not None else None
        resultado = self.servicio_pagos.registrar_pago(formulario, actor_id=actor_id)
        self.vista_pagos.mostrar_mensaje(resultado.mensaje, es_error=not resultado.exito)
        if resultado.exito:
            comprobante_id = resultado.comprobante.pago_id if resultado.comprobante is not None else None
            reiniciar_flujo()
            self._refrescar()
            bus_actualizaciones_modulos.emitir(
                modulo_origen="pagos",
                modulos_afectados=("historial_pagos", "morosidad", "reportes"),
            )
            if comprobante_id is not None:
                self._abrir_dialogo_comprobante(comprobante_id)

    def _mostrar_comprobante(self, pago_id: int) -> None:
        self._abrir_dialogo_comprobante(pago_id)

    def _abrir_dialogo_comprobante(self, pago_id: int) -> None:
        try:
            ruta_documento = self.servicio_pagos.generar_comprobante_pdf(pago_id)
            configuracion = self.servicio_pagos.obtener_configuracion_recibo()
        except (OSError, ValueError) as error:
            self.vista_pagos.mostrar_mensaje(
                f"No fue posible generar el comprobante PDF. {error}",
                es_error=True,
            )
            return
        self.vista_pagos.mostrar_comprobante(
            ruta_documento=ruta_documento,
            abrir_automaticamente=configuracion.abrir_pdf_automaticamente,
            imprimir_automaticamente=configuracion.imprimir_pdf_automaticamente,
        )

    def _manejar_actualizacion_modulo(self, evento: object) -> None:
        if not isinstance(evento, EventoModuloActualizado):
            return
        if "pagos" not in evento.modulos_afectados:
            return
        self._refrescar()
        self.vista_pagos.mostrar_mensaje(evento.mensaje, es_error=False)
