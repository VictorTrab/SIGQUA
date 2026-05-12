"""Controlador del modulo de configuracion."""

from __future__ import annotations

from modulos.autenticacion.entidades import UsuarioAutenticado
from modulos.configuracion.servicio import ServicioConfiguracion
from modulos.configuracion.vista import VistaConfiguracion


class ControladorConfiguracion:
    """Conecta la vista de configuracion con su servicio."""

    def __init__(
        self,
        servicio_configuracion: ServicioConfiguracion,
        vista_configuracion: VistaConfiguracion,
    ) -> None:
        self._servicio_configuracion = servicio_configuracion
        self._vista_configuracion = vista_configuracion
        self._actor: UsuarioAutenticado | None = None
        self._conectar_senales()

    def mostrar_para_actor(self, actor: UsuarioAutenticado) -> None:
        self._actor = actor
        self._refrescar()

    def _conectar_senales(self) -> None:
        self._vista_configuracion.guardar_datos_junta_solicitado.connect(self._guardar_datos_junta)
        self._vista_configuracion.guardar_parametros_cobro_solicitado.connect(
            self._guardar_parametros_cobro
        )

    def _guardar_datos_junta(self, nombre: str, telefono: str, correo: str, direccion: str) -> None:
        resultado = self._servicio_configuracion.guardar_datos_junta(
            nombre=nombre,
            telefono=telefono,
            correo=correo,
            direccion=direccion,
            actor_id=None if self._actor is None else self._actor.identificador,
        )
        self._vista_configuracion.mostrar_mensaje(resultado.mensaje, es_error=not resultado.exito)
        if resultado.exito:
            self._refrescar()

    def _guardar_parametros_cobro(
        self,
        precio_mensual_centavos: int,
        multa_mora_automatica_activa: bool,
        multa_mora_automatica_centavos: int,
        corte_automatico_activo: bool,
    ) -> None:
        resultado = self._servicio_configuracion.guardar_parametros_cobro(
            precio_mensual_centavos=precio_mensual_centavos,
            multa_mora_automatica_activa=multa_mora_automatica_activa,
            multa_mora_automatica_centavos=multa_mora_automatica_centavos,
            corte_automatico_activo=corte_automatico_activo,
            actor_id=None if self._actor is None else self._actor.identificador,
        )
        self._vista_configuracion.mostrar_mensaje(resultado.mensaje, es_error=not resultado.exito)
        if resultado.exito:
            self._refrescar()

    def _refrescar(self) -> None:
        estado = self._servicio_configuracion.obtener_estado()
        self._vista_configuracion.mostrar_estado(
            estado=estado,
            formateador_moneda=self._servicio_configuracion.formatear_moneda,
        )
