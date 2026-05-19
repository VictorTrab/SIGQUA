"""Controlador del modulo de configuracion."""

from __future__ import annotations

from comun.actualizaciones import bus_actualizaciones_modulos
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
        self._vista_configuracion.guardar_parametros_factura_solicitado.connect(
            self._guardar_parametros_factura
        )
        self._vista_configuracion.guardar_parametros_cobro_solicitado.connect(
            self._guardar_parametros_cobro
        )
        self._vista_configuracion.guardar_operacion_respaldo_solicitado.connect(
            self._guardar_operacion_respaldo
        )
        self._vista_configuracion.crear_respaldo_manual_solicitado.connect(
            self._crear_respaldo_manual
        )

    def _guardar_datos_junta(
        self,
        nombre: str,
        telefono: str,
        correo: str,
        direccion: str,
        identificador_fiscal: str,
        sitio_web: str,
        mensaje_contacto: str,
    ) -> None:
        resultado = self._servicio_configuracion.guardar_datos_junta(
            nombre=nombre,
            telefono=telefono,
            correo=correo,
            direccion=direccion,
            identificador_fiscal=identificador_fiscal,
            sitio_web=sitio_web,
            mensaje_contacto=mensaje_contacto,
            actor_id=None if self._actor is None else self._actor.identificador,
        )
        self._vista_configuracion.mostrar_mensaje(resultado.mensaje, es_error=not resultado.exito)
        if resultado.exito:
            self._refrescar()
            bus_actualizaciones_modulos.emitir(
                modulo_origen="configuracion",
                modulos_afectados=("pagos", "morosidad", "reportes"),
            )

    def _guardar_parametros_factura(
        self,
        titulo_documento: str,
        subtitulo_documento: str,
        texto_legal_superior: str,
        texto_pie: str,
        texto_legal_inferior: str,
        etiqueta_copia: str,
        formato_salida: str,
        mostrar_correo: bool,
        mostrar_telefono: bool,
        mostrar_direccion: bool,
        mostrar_identificador_fiscal: bool,
        firma_habilitada: bool,
        firma_nombre: str,
        firma_cargo: str,
        firma_identificador: str,
        firma_texto_apoyo: str,
    ) -> None:
        resultado = self._servicio_configuracion.guardar_parametros_factura(
            titulo_documento=titulo_documento,
            subtitulo_documento=subtitulo_documento,
            texto_legal_superior=texto_legal_superior,
            texto_pie=texto_pie,
            texto_legal_inferior=texto_legal_inferior,
            etiqueta_copia=etiqueta_copia,
            formato_salida=formato_salida,
            mostrar_correo=mostrar_correo,
            mostrar_telefono=mostrar_telefono,
            mostrar_direccion=mostrar_direccion,
            mostrar_identificador_fiscal=mostrar_identificador_fiscal,
            firma_habilitada=firma_habilitada,
            firma_nombre=firma_nombre,
            firma_cargo=firma_cargo,
            firma_identificador=firma_identificador,
            firma_texto_apoyo=firma_texto_apoyo,
            actor_id=None if self._actor is None else self._actor.identificador,
        )
        self._vista_configuracion.mostrar_mensaje(resultado.mensaje, es_error=not resultado.exito)
        if resultado.exito:
            self._refrescar()
            bus_actualizaciones_modulos.emitir(
                modulo_origen="configuracion",
                modulos_afectados=("reportes",),
            )

    def _guardar_parametros_cobro(
        self,
        precio_mensual_centavos: int,
        multa_mora_automatica_activa: bool,
        multa_mora_automatica_centavos: int,
        corte_automatico_activo: bool,
        meses_para_corte: int,
        permitir_pago_adelantado: bool,
        meses_adelanto_maximo: int,
        mora_leve_hasta_meses: int,
        mora_media_hasta_meses: int,
    ) -> None:
        resultado = self._servicio_configuracion.guardar_parametros_cobro(
            precio_mensual_centavos=precio_mensual_centavos,
            multa_mora_automatica_activa=multa_mora_automatica_activa,
            multa_mora_automatica_centavos=multa_mora_automatica_centavos,
            corte_automatico_activo=corte_automatico_activo,
            meses_para_corte=meses_para_corte,
            permitir_pago_adelantado=permitir_pago_adelantado,
            meses_adelanto_maximo=meses_adelanto_maximo,
            mora_leve_hasta_meses=mora_leve_hasta_meses,
            mora_media_hasta_meses=mora_media_hasta_meses,
            actor_id=None if self._actor is None else self._actor.identificador,
        )
        self._vista_configuracion.mostrar_mensaje(resultado.mensaje, es_error=not resultado.exito)
        if resultado.exito:
            self._refrescar()
            bus_actualizaciones_modulos.emitir(
                modulo_origen="configuracion",
                modulos_afectados=("pagos", "morosidad", "reportes"),
            )

    def _guardar_operacion_respaldo(
        self,
        respaldo_automatico: bool,
        ruta_principal: str,
        ruta_secundaria: str,
        secundaria_activa: bool,
        comprimir_zip: bool,
        organizar_por_periodo: bool,
        retencion_dias: int,
        programacion_tipo: str,
        programacion_hora: str,
        programacion_dia_semana: str,
        duracion_sesion_horas: float,
    ) -> None:
        resultado = self._servicio_configuracion.guardar_operacion_respaldo(
            respaldo_automatico=respaldo_automatico,
            ruta_principal=ruta_principal,
            ruta_secundaria=ruta_secundaria,
            secundaria_activa=secundaria_activa,
            comprimir_zip=comprimir_zip,
            organizar_por_periodo=organizar_por_periodo,
            retencion_dias=retencion_dias,
            programacion_tipo=programacion_tipo,
            programacion_hora=programacion_hora,
            programacion_dia_semana=programacion_dia_semana,
            duracion_sesion_horas=duracion_sesion_horas,
            actor_id=None if self._actor is None else self._actor.identificador,
        )
        self._vista_configuracion.mostrar_mensaje(resultado.mensaje, es_error=not resultado.exito)
        if resultado.exito:
            self._refrescar()

    def _crear_respaldo_manual(self) -> None:
        resultado = self._servicio_configuracion.crear_respaldo_manual(
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
