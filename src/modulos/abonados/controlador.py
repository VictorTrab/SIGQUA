"""Controlador del modulo de abonados."""

from __future__ import annotations

from typing import Callable

from comun.actualizaciones import bus_actualizaciones_modulos
from modulos.autenticacion.entidades import UsuarioAutenticado
from modulos.abonados.entidades import Abonado, FILTRO_ABONADOS_TODOS
from modulos.abonados.servicio import ServicioAbonados
from modulos.abonados.vista import VistaAbonados


class ControladorAbonados:
    """Conecta la vista de abonados con su servicio de aplicacion."""

    def __init__(self, servicio_abonados: ServicioAbonados, vista_abonados: VistaAbonados) -> None:
        self._servicio_abonados = servicio_abonados
        self._vista_abonados = vista_abonados
        self._actor: UsuarioAutenticado | None = None
        self._filtro_actual = ""
        self._filtro_rapido_actual = FILTRO_ABONADOS_TODOS
        self._pagina_actual = 1
        self._callback_ver_casas: Callable[[str], None] | None = None
        self._conectar_senales()

    def mostrar(self) -> None:
        """Carga el listado inicial del modulo."""
        self._refrescar()

    def mostrar_para_actor(self, actor: UsuarioAutenticado) -> None:
        """Carga el listado inicial dejando disponible el actor autenticado."""
        self._actor = actor
        self._refrescar()

    def _conectar_senales(self) -> None:
        self._vista_abonados.filtro_texto_cambiado.connect(self._manejar_filtro_texto)
        self._vista_abonados.filtro_rapido_cambiado.connect(self._manejar_filtro_rapido)
        self._vista_abonados.pagina_cambiada.connect(self._manejar_cambio_pagina)
        self._vista_abonados.nuevo_abonado_solicitado.connect(self._crear_abonado)
        self._vista_abonados.detalle_abonado_solicitado.connect(self._mostrar_detalle)
        self._vista_abonados.editar_abonado_solicitado.connect(self._editar_abonado)
        self._vista_abonados.cambio_estado_solicitado.connect(self._confirmar_cambio_estado)
        self._vista_abonados.ver_casas_abonado_solicitado.connect(self._ver_casas_relacionadas)
        self._vista_abonados.exportar_solicitado.connect(self._exportar)

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

    def _crear_abonado(self) -> None:
        formulario = self._vista_abonados.solicitar_datos_abonado(
            barrios=self._servicio_abonados.listar_barrios_disponibles()
        )
        if formulario is None:
            return
        self._guardar_abonado(formulario)

    def _mostrar_detalle(self, abonado_id: int) -> None:
        abonado = self._servicio_abonados.obtener_por_id(abonado_id)
        if abonado is None:
            self._vista_abonados.mostrar_mensaje(
                "No fue posible encontrar el abonado seleccionado.",
                es_error=True,
            )
            self._refrescar()
            return

        accion = self._vista_abonados.mostrar_detalle_abonado(
            abonado=abonado,
            fecha_creacion=self._servicio_abonados.formatear_fecha_hora(abonado.creado_en),
            fecha_actualizada=self._servicio_abonados.formatear_fecha_hora(abonado.actualizado_en),
            deuda_formateada=self._servicio_abonados.formatear_moneda(abonado.deuda_total_centavos),
            estados_casas=self._servicio_abonados.listar_estados_casas(abonado_id),
        )
        if accion == "editar":
            self._editar_abonado(abonado_id)
        elif accion == "ver_casas":
            self._abrir_modulo_casas(abonado)

    def _editar_abonado(self, abonado_id: int) -> None:
        abonado = self._servicio_abonados.obtener_por_id(abonado_id)
        if abonado is None:
            self._vista_abonados.mostrar_mensaje(
                "No fue posible encontrar el abonado seleccionado.",
                es_error=True,
            )
            self._refrescar()
            return

        formulario = self._vista_abonados.solicitar_datos_abonado(
            abonado=abonado,
            barrios=self._servicio_abonados.listar_barrios_disponibles(),
        )
        if formulario is None:
            return
        self._guardar_abonado(formulario)

    def _guardar_abonado(self, formulario: object) -> None:
        resultado = self._servicio_abonados.guardar(
            identificador=formulario.identificador,
            dni=formulario.dni,
            nombre_completo=formulario.nombre_completo,
            telefono=formulario.telefono,
            barrio_id=formulario.barrio_id,
            direccion_referencia=formulario.direccion_referencia,
            observaciones=formulario.observaciones,
            estado=formulario.estado,
        )
        self._vista_abonados.mostrar_mensaje(resultado.mensaje, es_error=not resultado.exito)
        if resultado.exito:
            self._refrescar()
            bus_actualizaciones_modulos.emitir(
                "abonados",
                ("dashboard", "casas", "morosidad", "reportes"),
                "Abonados actualizados.",
            )

    def _confirmar_cambio_estado(self, abonado_id: int) -> None:
        abonado = self._servicio_abonados.obtener_por_id(abonado_id)
        if abonado is None:
            self._vista_abonados.mostrar_mensaje(
                "No fue posible encontrar el abonado seleccionado.",
                es_error=True,
            )
            self._refrescar()
            return

        if not self._vista_abonados.confirmar_cambio_estado_abonado(abonado):
            return

        resultado = self._servicio_abonados.cambiar_estado(
            abonado_id,
            abonado.estado,
            actor_id=None if self._actor is None else self._actor.identificador,
        )
        self._vista_abonados.mostrar_mensaje(resultado.mensaje, es_error=not resultado.exito)
        if resultado.exito:
            self._refrescar()
            bus_actualizaciones_modulos.emitir(
                "abonados",
                ("dashboard", "casas", "morosidad", "reportes"),
                "Abonados actualizados.",
            )

    def _exportar(self) -> None:
        ruta_destino = self._vista_abonados.solicitar_ruta_exportacion()
        if not ruta_destino:
            return

        resultado = self._servicio_abonados.exportar_csv(
            ruta_destino=ruta_destino,
            filtro=self._filtro_actual,
            filtro_rapido=self._filtro_rapido_actual,
        )
        self._vista_abonados.mostrar_mensaje(resultado.mensaje, es_error=not resultado.exito)

    def _ver_casas_relacionadas(self, abonado_id: int) -> None:
        abonado = self._servicio_abonados.obtener_por_id(abonado_id)
        if abonado is None:
            self._vista_abonados.mostrar_mensaje(
                "No fue posible encontrar el abonado seleccionado.",
                es_error=True,
            )
            self._refrescar()
            return
        self._abrir_modulo_casas(abonado)

    def _abrir_modulo_casas(self, abonado: Abonado) -> None:
        if self._callback_ver_casas is not None:
            self._callback_ver_casas(abonado.dni)
            return
        self._vista_abonados.mostrar_mensaje(
            "La navegacion hacia casas no esta disponible en esta sesion.",
            es_error=True,
        )

    def _refrescar(self) -> None:
        pagina = self._servicio_abonados.listar(
            filtro=self._filtro_actual,
            filtro_rapido=self._filtro_rapido_actual,
            pagina=self._pagina_actual,
        )
        self._pagina_actual = pagina.pagina_actual
        self._vista_abonados.mostrar_resumen(self._servicio_abonados.obtener_resumen())
        self._vista_abonados.mostrar_abonados(pagina=pagina)
