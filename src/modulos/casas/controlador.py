"""Controlador del modulo de casas."""

from __future__ import annotations

from comun.actualizaciones import bus_actualizaciones_modulos
from modulos.autenticacion.entidades import UsuarioAutenticado
from modulos.casas.entidades import FILTRO_CASAS_TODAS
from modulos.casas.servicio import ServicioCasas
from modulos.casas.vista import VistaCasas


class ControladorCasas:
    """Conecta la vista de casas con su servicio de aplicacion."""

    def __init__(self, servicio_casas: ServicioCasas, vista_casas: VistaCasas) -> None:
        self._servicio_casas = servicio_casas
        self._vista_casas = vista_casas
        self._actor: UsuarioAutenticado | None = None
        self._filtro_actual = ""
        self._filtro_rapido_actual = FILTRO_CASAS_TODAS
        self._pagina_actual = 1
        self._conectar_senales()

    def mostrar(self) -> None:
        """Carga el listado inicial del modulo."""
        self._refrescar()

    def mostrar_para_actor(self, actor: UsuarioAutenticado) -> None:
        """Carga el modulo dejando disponible el actor autenticado."""
        self._actor = actor
        self._refrescar()

    def _conectar_senales(self) -> None:
        self._vista_casas.filtro_texto_cambiado.connect(self._manejar_filtro_texto)
        self._vista_casas.filtro_rapido_cambiado.connect(self._manejar_filtro_rapido)
        self._vista_casas.pagina_cambiada.connect(self._manejar_cambio_pagina)
        self._vista_casas.nueva_casa_solicitada.connect(self._crear_casa)
        self._vista_casas.detalle_casa_solicitado.connect(self._mostrar_detalle)
        self._vista_casas.editar_casa_solicitado.connect(self._editar_casa)
        self._vista_casas.cambio_estado_solicitado.connect(self._confirmar_cambio_estado)
        self._vista_casas.corte_servicio_solicitado.connect(self._confirmar_corte_servicio)
        self._vista_casas.historial_casa_solicitado.connect(self._mostrar_historial)
        self._vista_casas.cambio_dueno_solicitado.connect(self._cambiar_dueno)
        self._vista_casas.exportar_solicitado.connect(self._exportar)

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

    def _crear_casa(self) -> None:
        formulario = self._vista_casas.solicitar_datos_casa(
            barrios=self._servicio_casas.listar_barrios_disponibles(),
            abonados=self._servicio_casas.listar_abonados_disponibles(),
        )
        if formulario is None:
            return
        self._guardar_casa(formulario)

    def _mostrar_detalle(self, casa_id: int) -> None:
        detalle = self._servicio_casas.obtener_detalle(casa_id)
        if detalle is None:
            self._vista_casas.mostrar_mensaje(
                "No fue posible encontrar la casa seleccionada.",
                es_error=True,
            )
            self._refrescar()
            return

        accion = self._vista_casas.mostrar_detalle_casa(
            detalle=detalle,
            formateador_fecha=self._servicio_casas.formatear_fecha_hora,
            formateador_moneda=self._servicio_casas.formatear_moneda,
        )
        if accion == "editar":
            self._editar_casa(casa_id)
        elif accion == "historial":
            self._mostrar_historial(casa_id)
        elif accion == "cambiar_dueno":
            self._cambiar_dueno(casa_id)
        elif accion == "cortar_servicio":
            self._confirmar_corte_servicio(casa_id)

    def _editar_casa(self, casa_id: int) -> None:
        casa = self._servicio_casas.obtener_por_id(casa_id)
        if casa is None:
            self._vista_casas.mostrar_mensaje(
                "No fue posible encontrar la casa seleccionada.",
                es_error=True,
            )
            self._refrescar()
            return

        formulario = self._vista_casas.solicitar_datos_casa(
            barrios=self._servicio_casas.listar_barrios_disponibles(),
            abonados=self._servicio_casas.listar_abonados_disponibles(),
            casa=casa,
        )
        if formulario is None:
            return
        self._guardar_casa(formulario)

    def _guardar_casa(self, formulario: object) -> None:
        resultado = self._servicio_casas.guardar(
            identificador=formulario.identificador,
            abonado_id=formulario.abonado_id,
            barrio_id=formulario.barrio_id,
            direccion_referencia=formulario.direccion_referencia,
            observaciones=formulario.observaciones,
            estado_servicio=formulario.estado_servicio,
            estado_administrativo=formulario.estado_administrativo,
            motivo_estado_administrativo=formulario.motivo_estado_administrativo,
            ha_tenido_servicio_activo=formulario.ha_tenido_servicio_activo,
        )
        self._vista_casas.mostrar_mensaje(resultado.mensaje, es_error=not resultado.exito)
        if resultado.exito:
            self._refrescar()
            bus_actualizaciones_modulos.emitir(
                "casas",
                ("dashboard", "morosidad", "pagos", "reportes"),
                "Casas actualizadas.",
            )

    def _confirmar_cambio_estado(self, casa_id: int) -> None:
        casa = self._servicio_casas.obtener_por_id(casa_id)
        if casa is None:
            self._vista_casas.mostrar_mensaje(
                "No fue posible encontrar la casa seleccionada.",
                es_error=True,
            )
            self._refrescar()
            return

        if not self._vista_casas.confirmar_cambio_estado_casa(casa):
            return

        resultado = self._servicio_casas.cambiar_estado(
            casa_id,
            casa.estado_administrativo,
            casa.motivo_estado_administrativo,
        )
        self._vista_casas.mostrar_mensaje(resultado.mensaje, es_error=not resultado.exito)
        if resultado.exito:
            self._refrescar()
            bus_actualizaciones_modulos.emitir(
                "casas",
                ("dashboard", "morosidad", "pagos", "reportes"),
                "Casas actualizadas.",
            )

    def _confirmar_corte_servicio(self, casa_id: int) -> None:
        detalle = self._servicio_casas.obtener_detalle(casa_id)
        if detalle is None:
            self._vista_casas.mostrar_mensaje(
                "No fue posible encontrar la casa seleccionada.",
                es_error=True,
            )
            self._refrescar()
            return

        formulario = self._vista_casas.solicitar_corte_servicio(
            detalle=detalle,
            formateador_moneda=self._servicio_casas.formatear_moneda,
        )
        if formulario is None:
            return

        resultado = self._servicio_casas.cortar_servicio(
            casa_id=formulario.casa_id,
            observaciones=formulario.observaciones,
            actor_id=None if self._actor is None else self._actor.identificador,
        )
        self._vista_casas.mostrar_mensaje(resultado.mensaje, es_error=not resultado.exito)
        if resultado.exito:
            self._refrescar()
            bus_actualizaciones_modulos.emitir(
                "casas",
                ("dashboard", "morosidad", "pagos", "reportes"),
                "Servicio cortado.",
            )

    def _mostrar_historial(self, casa_id: int) -> None:
        casa = self._servicio_casas.obtener_por_id(casa_id)
        if casa is None:
            self._vista_casas.mostrar_mensaje(
                "No fue posible encontrar la casa seleccionada.",
                es_error=True,
            )
            self._refrescar()
            return

        historial = self._servicio_casas.listar_historial_propietarios(casa_id)
        self._vista_casas.mostrar_historial_propietarios(
            casa=casa,
            historial=historial,
            formateador_fecha=self._servicio_casas.formatear_fecha_hora,
        )

    def _cambiar_dueno(self, casa_id: int) -> None:
        casa = self._servicio_casas.obtener_por_id(casa_id)
        if casa is None:
            self._vista_casas.mostrar_mensaje(
                "No fue posible encontrar la casa seleccionada.",
                es_error=True,
            )
            self._refrescar()
            return

        formulario = self._vista_casas.solicitar_cambio_dueno(
            casa=casa,
            abonados=self._servicio_casas.listar_abonados_disponibles(),
        )
        if formulario is None:
            return

        resultado = self._servicio_casas.cambiar_dueno(
            casa_id=casa_id,
            nuevo_abonado_id=formulario.nuevo_abonado_id,
            motivo=formulario.motivo,
            actor_id=None if self._actor is None else self._actor.identificador,
        )
        self._vista_casas.mostrar_mensaje(resultado.mensaje, es_error=not resultado.exito)
        if resultado.exito:
            self._refrescar()
            bus_actualizaciones_modulos.emitir(
                "casas",
                ("dashboard", "morosidad", "pagos", "reportes"),
                "Casa actualizada.",
            )

    def _exportar(self) -> None:
        ruta_destino = self._vista_casas.solicitar_ruta_exportacion()
        if not ruta_destino:
            return

        resultado = self._servicio_casas.exportar_csv(
            ruta_destino=ruta_destino,
            filtro=self._filtro_actual,
            filtro_rapido=self._filtro_rapido_actual,
        )
        self._vista_casas.mostrar_mensaje(resultado.mensaje, es_error=not resultado.exito)

    def _refrescar(self) -> None:
        pagina = self._servicio_casas.listar(
            filtro=self._filtro_actual,
            filtro_rapido=self._filtro_rapido_actual,
            pagina=self._pagina_actual,
        )
        self._pagina_actual = pagina.pagina_actual
        self._vista_casas.mostrar_resumen(self._servicio_casas.obtener_resumen())
        self._vista_casas.mostrar_casas(pagina=pagina)
