"""Controlador del modulo de morosidad."""

from __future__ import annotations

from comun.actualizaciones import EventoModuloActualizado, bus_actualizaciones_modulos
from modulos.morosidad.entidades import FiltroMorosidad
from modulos.morosidad.servicio import ServicioMorosidad
from modulos.morosidad.vista import VistaMorosidad


class ControladorMorosidad:
    """Conecta la vista de morosidad con sus consultas y documentos."""

    def __init__(
        self,
        servicio_morosidad: ServicioMorosidad,
        vista_morosidad: VistaMorosidad,
    ) -> None:
        self._servicio_morosidad = servicio_morosidad
        self._vista_morosidad = vista_morosidad
        self._filtros = servicio_morosidad.filtro_inicial()
        self._pagina_actual = 1
        self._conectar_senales()
        bus_actualizaciones_modulos.actualizacion_emitida.connect(self._manejar_actualizacion_modulo)

    def mostrar(self) -> None:
        self._refrescar()

    def _conectar_senales(self) -> None:
        self._vista_morosidad.filtro_texto_cambiado.connect(self._manejar_filtro_texto)
        self._vista_morosidad.filtro_severidad_cambiado.connect(self._manejar_filtro_severidad)
        self._vista_morosidad.pagina_cambiada.connect(self._manejar_cambio_pagina)
        self._vista_morosidad.detalle_solicitado.connect(self._mostrar_detalle)
        self._vista_morosidad.emitir_documento_solicitado.connect(self._emitir_documento)

    def _manejar_filtro_texto(self, texto: str) -> None:
        self._filtros.texto = texto.strip()
        self._pagina_actual = 1
        self._refrescar()

    def _manejar_filtro_severidad(self, severidad: str) -> None:
        self._filtros.severidad = severidad
        self._pagina_actual = 1
        self._refrescar()

    def _manejar_cambio_pagina(self, pagina: int) -> None:
        self._pagina_actual = max(1, pagina)
        self._refrescar()

    def _mostrar_detalle(self, abonado_id: int) -> None:
        detalle = self._servicio_morosidad.obtener_detalle(abonado_id)
        if detalle is None:
            self._vista_morosidad.mostrar_mensaje(
                "No fue posible encontrar el detalle del abonado seleccionado.",
                es_error=True,
            )
            return
        accion = self._vista_morosidad.mostrar_detalle(
            detalle=detalle,
            formateador_moneda=self._servicio_morosidad.formatear_moneda,
            formateador_fecha=self._servicio_morosidad.formatear_fecha,
        )
        if accion == "emitir":
            self._emitir_documento(abonado_id)

    def _emitir_documento(self, abonado_id: int) -> None:
        detalle = self._servicio_morosidad.obtener_detalle(abonado_id)
        if detalle is None:
            self._vista_morosidad.mostrar_mensaje(
                "No fue posible reconstruir la deuda del abonado seleccionado.",
                es_error=True,
            )
            return
        seleccion = self._vista_morosidad.seleccionar_casas_documento(detalle)
        if seleccion is None:
            return
        emitir_total, casas = seleccion
        casas_seleccionadas = () if emitir_total else casas
        resultado = self._servicio_morosidad.emitir_documento_deuda(
            abonado_id=abonado_id,
            casas_seleccionadas=casas_seleccionadas,
        )
        self._vista_morosidad.mostrar_mensaje(resultado.mensaje, es_error=not resultado.exito)

    def _manejar_actualizacion_modulo(self, evento: object) -> None:
        if not isinstance(evento, EventoModuloActualizado):
            return
        if "morosidad" not in evento.modulos_afectados:
            return
        self._refrescar()
        self._vista_morosidad.mostrar_mensaje(evento.mensaje, es_error=False)

    def _refrescar(self) -> None:
        estado = self._servicio_morosidad.obtener_estado(self._filtros, pagina=self._pagina_actual)
        self._pagina_actual = estado.pagina.pagina_actual
        self._vista_morosidad.establecer_filtro_severidad(self._filtros.severidad)
        self._vista_morosidad.mostrar_resumen(
            estado.resumen,
            self._servicio_morosidad.formatear_moneda,
        )
        self._vista_morosidad.mostrar_listado(
            pagina=estado.pagina,
            formatear_moneda=self._servicio_morosidad.formatear_moneda,
            formatear_fecha=self._servicio_morosidad.formatear_fecha,
            etiqueta_severidad=self._servicio_morosidad.etiqueta_severidad,
        )
