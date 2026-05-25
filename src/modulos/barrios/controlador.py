"""Controlador del modulo de barrios."""

from __future__ import annotations

from typing import Callable

from comun.actualizaciones import bus_actualizaciones_modulos
from modulos.barrios.entidades import Barrio, FILTRO_BARRIOS_TODOS
from modulos.barrios.servicio import ServicioBarrios
from modulos.barrios.vista import VistaBarrios


class ControladorBarrios:
    """Conecta la vista de barrios con su servicio de aplicacion."""

    def __init__(self, servicio_barrios: ServicioBarrios, vista_barrios: VistaBarrios) -> None:
        self._servicio_barrios = servicio_barrios
        self._vista_barrios = vista_barrios
        self._filtro_actual = ""
        self._filtro_rapido_actual = FILTRO_BARRIOS_TODOS
        self._pagina_actual = 1
        self._callback_ver_abonados: Callable[[str], None] | None = None
        self._callback_ver_casas: Callable[[str], None] | None = None
        self._conectar_senales()

    def mostrar(self) -> None:
        """Carga el listado inicial del modulo."""
        self._refrescar()

    def _conectar_senales(self) -> None:
        self._vista_barrios.filtro_texto_cambiado.connect(self._manejar_filtro_texto)
        self._vista_barrios.filtro_rapido_cambiado.connect(self._manejar_filtro_rapido)
        self._vista_barrios.pagina_cambiada.connect(self._manejar_cambio_pagina)
        self._vista_barrios.nuevo_barrio_solicitado.connect(self._crear_barrio)
        self._vista_barrios.detalle_barrio_solicitado.connect(self._mostrar_detalle)
        self._vista_barrios.editar_barrio_solicitado.connect(self._editar_barrio)
        self._vista_barrios.cambio_estado_solicitado.connect(self._confirmar_cambio_estado)
        self._vista_barrios.ver_abonados_barrio_solicitado.connect(self._ver_abonados_relacionados)
        self._vista_barrios.ver_casas_barrio_solicitado.connect(self._ver_casas_relacionadas)
        self._vista_barrios.exportar_solicitado.connect(self._exportar)

    def configurar_callback_ver_abonados(self, callback: Callable[[str], None]) -> None:
        self._callback_ver_abonados = callback

    def configurar_callback_ver_casas(self, callback: Callable[[str], None]) -> None:
        self._callback_ver_casas = callback

    def _manejar_filtro_texto(self, texto: str) -> None:
        self._filtro_actual = texto.strip()
        self._pagina_actual = 1
        self._refrescar()

    def _manejar_filtro_rapido(self, filtro_rapido: str) -> None:
        self._filtro_rapido_actual = filtro_rapido
        self._pagina_actual = 1
        self._refrescar()

    def _manejar_cambio_pagina(self, pagina: int) -> None:
        self._pagina_actual = max(1, pagina)
        self._refrescar()

    def _crear_barrio(self) -> None:
        formulario = self._vista_barrios.solicitar_datos_barrio()
        if formulario is None:
            return
        self._guardar_barrio(
            formulario.identificador,
            formulario.nombre,
            formulario.estado,
            formulario.observaciones,
        )

    def _mostrar_detalle(self, barrio_id: int) -> None:
        barrio = self._servicio_barrios.obtener_por_id(barrio_id)
        if barrio is None:
            self._vista_barrios.mostrar_mensaje(
                "No fue posible encontrar el barrio seleccionado.",
                es_error=True,
            )
            self._refrescar()
            return

        accion = self._vista_barrios.mostrar_detalle_barrio(
            barrio=barrio,
            fecha_creacion=self._servicio_barrios.formatear_fecha_hora(barrio.creado_en),
            fecha_actualizada=self._servicio_barrios.formatear_fecha_hora(barrio.actualizado_en),
        )
        if accion == "editar":
            self._editar_barrio(barrio_id)
        elif accion == "ver_abonados":
            self._abrir_modulo_abonados(barrio)
        elif accion == "ver_casas":
            self._abrir_modulo_casas(barrio)

    def _editar_barrio(self, barrio_id: int) -> None:
        barrio = self._servicio_barrios.obtener_por_id(barrio_id)
        if barrio is None:
            self._vista_barrios.mostrar_mensaje(
                "No fue posible encontrar el barrio seleccionado.",
                es_error=True,
            )
            self._refrescar()
            return

        formulario = self._vista_barrios.solicitar_datos_barrio(barrio)
        if formulario is None:
            return
        self._guardar_barrio(
            formulario.identificador,
            formulario.nombre,
            formulario.estado,
            formulario.observaciones,
        )

    def _guardar_barrio(
        self,
        identificador: int | None,
        nombre: str,
        estado: str,
        observaciones: str,
    ) -> None:
        resultado = self._servicio_barrios.guardar(
            identificador=identificador,
            nombre=nombre,
            estado=estado,
            observaciones=observaciones,
        )
        self._vista_barrios.mostrar_mensaje(resultado.mensaje, es_error=not resultado.exito)
        if resultado.exito:
            self._refrescar()
            bus_actualizaciones_modulos.emitir(
                "barrios",
                ("dashboard", "abonados", "casas", "reportes"),
                "Barrios actualizados.",
            )

    def _confirmar_cambio_estado(self, barrio_id: int) -> None:
        barrio = self._servicio_barrios.obtener_por_id(barrio_id)
        if barrio is None:
            self._vista_barrios.mostrar_mensaje(
                "No fue posible encontrar el barrio seleccionado.",
                es_error=True,
            )
            self._refrescar()
            return

        if not self._vista_barrios.confirmar_cambio_estado_barrio(barrio):
            return

        resultado = self._servicio_barrios.cambiar_estado(barrio_id, barrio.estado)
        self._vista_barrios.mostrar_mensaje(resultado.mensaje, es_error=not resultado.exito)
        if resultado.exito:
            self._refrescar()
            bus_actualizaciones_modulos.emitir(
                "barrios",
                ("dashboard", "abonados", "casas", "reportes"),
                "Barrios actualizados.",
            )

    def _exportar(self) -> None:
        ruta_destino = self._vista_barrios.solicitar_ruta_exportacion()
        if not ruta_destino:
            return

        resultado = self._servicio_barrios.exportar_csv(
            ruta_destino=ruta_destino,
            filtro=self._filtro_actual,
            filtro_rapido=self._filtro_rapido_actual,
        )
        self._vista_barrios.mostrar_mensaje(resultado.mensaje, es_error=not resultado.exito)

    def _ver_abonados_relacionados(self, barrio_id: int) -> None:
        barrio = self._servicio_barrios.obtener_por_id(barrio_id)
        if barrio is None:
            self._vista_barrios.mostrar_mensaje(
                "No fue posible encontrar el barrio seleccionado.",
                es_error=True,
            )
            self._refrescar()
            return
        self._abrir_modulo_abonados(barrio)

    def _ver_casas_relacionadas(self, barrio_id: int) -> None:
        barrio = self._servicio_barrios.obtener_por_id(barrio_id)
        if barrio is None:
            self._vista_barrios.mostrar_mensaje(
                "No fue posible encontrar el barrio seleccionado.",
                es_error=True,
            )
            self._refrescar()
            return
        self._abrir_modulo_casas(barrio)

    def _abrir_modulo_abonados(self, barrio: Barrio) -> None:
        if self._callback_ver_abonados is not None:
            self._callback_ver_abonados(barrio.codigo)
            return
        self._vista_barrios.mostrar_mensaje(
            "La navegacion hacia abonados no esta disponible en esta sesion.",
            es_error=True,
        )

    def _abrir_modulo_casas(self, barrio: Barrio) -> None:
        if self._callback_ver_casas is not None:
            self._callback_ver_casas(barrio.codigo)
            return
        self._vista_barrios.mostrar_mensaje(
            "La navegacion hacia casas no esta disponible en esta sesion.",
            es_error=True,
        )

    def _refrescar(self) -> None:
        pagina = self._servicio_barrios.listar(
            filtro=self._filtro_actual,
            filtro_rapido=self._filtro_rapido_actual,
            pagina=self._pagina_actual,
        )
        self._pagina_actual = pagina.pagina_actual
        self._vista_barrios.mostrar_resumen(self._servicio_barrios.obtener_resumen())
        self._vista_barrios.mostrar_barrios(
            pagina=pagina,
            formateador_fecha=self._servicio_barrios.formatear_fecha_hora,
        )
