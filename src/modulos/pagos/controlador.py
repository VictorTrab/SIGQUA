"""Controlador del modulo de pagos."""

from __future__ import annotations

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

    def mostrar_para_actor(self, actor: UsuarioAutenticado) -> None:
        self._actor = actor
        self._refrescar()

    def _conectar_senales(self) -> None:
        self.vista_pagos.buscar_solicitado.connect(self._refrescar)
        self.vista_pagos.registrar_pago_solicitado.connect(self._registrar_pago)
        self.vista_pagos.comprobante_solicitado.connect(self._mostrar_comprobante)

    def _refrescar(self, filtro: str = "") -> None:
        estado = self.servicio_pagos.obtener_estado(filtro=filtro)
        self.vista_pagos.mostrar_estado(
            estado,
            self.servicio_pagos.formatear_moneda,
            self.servicio_pagos.formatear_fecha,
        )

    def _registrar_pago(self, formulario: FormularioPago) -> None:
        confirmacion = self.servicio_pagos.preparar_confirmacion(formulario)
        if isinstance(confirmacion, ResultadoPago):
            self.vista_pagos.mostrar_mensaje(confirmacion.mensaje, es_error=True)
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
            self._refrescar()
            if resultado.comprobante is not None:
                self._abrir_dialogo_comprobante(resultado.comprobante.pago_id)

    def _mostrar_comprobante(self, pago_id: int) -> None:
        self._abrir_dialogo_comprobante(pago_id)

    def _abrir_dialogo_comprobante(self, pago_id: int) -> None:
        comprobante = self.servicio_pagos.obtener_comprobante(pago_id)
        if comprobante is None:
            self.vista_pagos.mostrar_mensaje(
                "No fue posible cargar el comprobante solicitado.",
                es_error=True,
            )
            return
        html = self.servicio_pagos.generar_html_comprobante(comprobante)
        texto = self.servicio_pagos.generar_texto_comprobante(comprobante)
        ruta_sugerida = self.servicio_pagos.ruta_sugerida_comprobante(comprobante)
        self.vista_pagos.mostrar_comprobante(
            comprobante=comprobante,
            html=html,
            texto=texto,
            ruta_sugerida=ruta_sugerida,
            exportador=lambda ruta: self.servicio_pagos.exportar_comprobante(comprobante, ruta),
            formatear_moneda=self.servicio_pagos.formatear_moneda,
            formatear_fecha=self.servicio_pagos.formatear_fecha,
        )
