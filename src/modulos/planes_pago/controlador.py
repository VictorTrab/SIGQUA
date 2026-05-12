"""Controlador del modulo de planes de pago."""

from __future__ import annotations

from modulos.autenticacion.entidades import UsuarioAutenticado
from modulos.planes_pago.entidades import FILTRO_PLANES_TODOS
from modulos.planes_pago.servicio import ServicioPlanesPago
from modulos.planes_pago.vista import VistaPlanesPago


class ControladorPlanesPago:
    """Conecta la vista de planes con su servicio."""

    def __init__(self, servicio_planes_pago: ServicioPlanesPago, vista_planes_pago: VistaPlanesPago) -> None:
        self._servicio_planes_pago = servicio_planes_pago
        self._vista_planes_pago = vista_planes_pago
        self._actor: UsuarioAutenticado | None = None
        self._filtro_actual = ""
        self._filtro_rapido_actual = FILTRO_PLANES_TODOS
        self._pagina_actual = 1
        self._conectar_senales()

    def mostrar_para_actor(self, actor: UsuarioAutenticado) -> None:
        self._actor = actor
        self._refrescar()

    def _conectar_senales(self) -> None:
        self._vista_planes_pago.filtro_texto_cambiado.connect(self._manejar_filtro_texto)
        self._vista_planes_pago.filtro_rapido_cambiado.connect(self._manejar_filtro_rapido)
        self._vista_planes_pago.pagina_cambiada.connect(self._manejar_cambio_pagina)
        self._vista_planes_pago.nuevo_plan_solicitado.connect(self._crear_plan)
        self._vista_planes_pago.detalle_plan_solicitado.connect(self._mostrar_detalle)
        self._vista_planes_pago.editar_plan_solicitado.connect(self._editar_plan)
        self._vista_planes_pago.exportar_solicitado.connect(self._exportar)

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

    def _crear_plan(self) -> None:
        formulario = self._vista_planes_pago.solicitar_datos_plan(
            casas=self._servicio_planes_pago.listar_casas_disponibles(),
        )
        if formulario is None:
            return
        self._guardar_plan(formulario)

    def _mostrar_detalle(self, plan_id: int) -> None:
        detalle = self._servicio_planes_pago.obtener_detalle(plan_id)
        if detalle is None:
            self._vista_planes_pago.mostrar_mensaje("No fue posible encontrar el plan seleccionado.", es_error=True)
            self._refrescar()
            return
        accion = self._vista_planes_pago.mostrar_detalle_plan(
            detalle=detalle,
            formateador_moneda=self._servicio_planes_pago.formatear_moneda,
            formateador_fecha=self._servicio_planes_pago.formatear_fecha,
        )
        if accion == "editar":
            self._editar_plan(plan_id)

    def _editar_plan(self, plan_id: int) -> None:
        plan = self._servicio_planes_pago.obtener_por_id(plan_id)
        if plan is None:
            self._vista_planes_pago.mostrar_mensaje("No fue posible encontrar el plan seleccionado.", es_error=True)
            self._refrescar()
            return
        formulario = self._vista_planes_pago.solicitar_datos_plan(
            casas=self._servicio_planes_pago.listar_casas_disponibles(),
            plan=plan,
        )
        if formulario is None:
            return
        self._guardar_plan(formulario)

    def _guardar_plan(self, formulario: object) -> None:
        resultado = self._servicio_planes_pago.guardar(
            formulario=formulario,
            actor_id=None if self._actor is None else self._actor.identificador,
        )
        self._vista_planes_pago.mostrar_mensaje(resultado.mensaje, es_error=not resultado.exito)
        if resultado.exito:
            self._refrescar()

    def _exportar(self) -> None:
        ruta = self._vista_planes_pago.solicitar_ruta_exportacion()
        if not ruta:
            return
        resultado = self._servicio_planes_pago.exportar_csv(
            ruta_destino=ruta,
            filtro=self._filtro_actual,
            filtro_rapido=self._filtro_rapido_actual,
        )
        self._vista_planes_pago.mostrar_mensaje(resultado.mensaje, es_error=not resultado.exito)

    def _refrescar(self) -> None:
        pagina = self._servicio_planes_pago.listar(
            filtro=self._filtro_actual,
            filtro_rapido=self._filtro_rapido_actual,
            pagina=self._pagina_actual,
        )
        self._pagina_actual = pagina.pagina_actual
        self._vista_planes_pago.mostrar_resumen(self._servicio_planes_pago.obtener_resumen(), self._servicio_planes_pago.formatear_moneda)
        self._vista_planes_pago.mostrar_planes(
            pagina=pagina,
            formateador_moneda=self._servicio_planes_pago.formatear_moneda,
            formateador_fecha=self._servicio_planes_pago.formatear_fecha,
        )
