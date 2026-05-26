"""Controlador del modulo de historial de pagos."""

from __future__ import annotations

from comun.actualizaciones import EventoModuloActualizado, bus_actualizaciones_modulos
from modulos.comprobantes import COPIA_AMBAS
from modulos.historial_pagos.entidades import FiltroHistorialPagos
from modulos.historial_pagos.servicio import ServicioHistorialPagos
from modulos.historial_pagos.vista import VistaHistorialPagos


class ControladorHistorialPagos:
    """Conecta la vista del historial con su servicio."""

    def __init__(
        self,
        servicio_historial: ServicioHistorialPagos,
        vista_historial: VistaHistorialPagos,
    ) -> None:
        self._servicio_historial = servicio_historial
        self._vista_historial = vista_historial
        self._filtros = servicio_historial.filtro_inicial()
        self._pagina_actual = 1
        self._conectar_senales()
        bus_actualizaciones_modulos.actualizacion_emitida.connect(self._manejar_actualizacion_modulo)

    def mostrar(self) -> None:
        self._refrescar()

    def _conectar_senales(self) -> None:
        self._vista_historial.filtro_texto_cambiado.connect(self._manejar_filtro_texto)
        self._vista_historial.filtro_tipo_cambiado.connect(self._manejar_filtro_tipo)
        self._vista_historial.filtro_metodo_cambiado.connect(self._manejar_filtro_metodo)
        self._vista_historial.rango_fechas_aplicado.connect(self._manejar_rango_fechas)
        self._vista_historial.pagina_cambiada.connect(self._manejar_cambio_pagina)
        self._vista_historial.detalle_pago_solicitado.connect(self._mostrar_detalle)
        self._vista_historial.reimpresion_solicitada.connect(self._reimprimir_copia)

    def _manejar_filtro_texto(self, texto: str) -> None:
        self._filtros.texto = texto.strip()
        self._pagina_actual = 1
        self._refrescar()

    def _manejar_filtro_tipo(self, tipo_pago: str) -> None:
        self._filtros.tipo_pago = tipo_pago
        self._pagina_actual = 1
        self._refrescar()

    def _manejar_filtro_metodo(self, metodo_pago: str) -> None:
        self._filtros.metodo_pago = metodo_pago
        self._pagina_actual = 1
        self._refrescar()

    def _manejar_rango_fechas(self, fecha_desde: str, fecha_hasta: str) -> None:
        self._filtros.fecha_desde = fecha_desde
        self._filtros.fecha_hasta = fecha_hasta
        self._pagina_actual = 1
        self._refrescar()

    def _manejar_cambio_pagina(self, pagina: int) -> None:
        self._pagina_actual = max(1, pagina)
        self._refrescar()

    def _mostrar_detalle(self, pago_id: int) -> None:
        detalle = self._servicio_historial.obtener_detalle(pago_id)
        if detalle is None:
            self._vista_historial.mostrar_mensaje(
                "No fue posible encontrar el pago seleccionado.",
                es_error=True,
            )
            self._refrescar()
            return
        accion = self._vista_historial.mostrar_detalle_pago(
            detalle=detalle,
            formateador_moneda=self._servicio_historial.formatear_moneda,
            formateador_fecha_hora=self._servicio_historial.formatear_fecha_hora,
            formateador_tipo=self._servicio_historial.etiqueta_tipo_pago,
        )
        if accion == "reimprimir":
            self._reimprimir_copia(pago_id, COPIA_AMBAS)
        elif accion.startswith("reimprimir:"):
            self._reimprimir_copia(pago_id, accion.split(":", maxsplit=1)[1] or COPIA_AMBAS)

    def _reimprimir_copia(self, pago_id: int, tipo_copia: str = COPIA_AMBAS) -> None:
        resultado = self._servicio_historial.reimprimir_comprobante(pago_id, tipo_copia=tipo_copia)
        self._vista_historial.mostrar_mensaje(resultado.mensaje, es_error=not resultado.exito)

    def _manejar_actualizacion_modulo(self, evento: object) -> None:
        if not isinstance(evento, EventoModuloActualizado):
            return
        if "historial_pagos" not in evento.modulos_afectados:
            return
        self._refrescar()
        self._vista_historial.mostrar_mensaje(evento.mensaje, es_error=False)

    def _refrescar(self) -> None:
        try:
            resumen = self._servicio_historial.obtener_resumen(self._filtros)
            pagina = self._servicio_historial.listar(self._filtros, pagina=self._pagina_actual)
        except ValueError as error:
            self._vista_historial.mostrar_mensaje(str(error), es_error=True)
            return
        self._pagina_actual = pagina.pagina_actual
        self._vista_historial.mostrar_resumen(
            resumen,
            self._servicio_historial.formatear_moneda,
        )
        self._vista_historial.mostrar_historial(
            pagina=pagina,
            formateador_fecha_hora=self._servicio_historial.formatear_fecha_hora,
            formateador_moneda=self._servicio_historial.formatear_moneda,
            formateador_tipo=self._servicio_historial.etiqueta_tipo_pago,
        )
