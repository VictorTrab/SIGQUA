"""Controlador del modulo de configuracion."""

from __future__ import annotations

from PySide6.QtCore import QTimer

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
        self._vista_configuracion.restaurar_respaldo_externo_solicitado.connect(
            self._restaurar_respaldo_externo
        )
        self._vista_configuracion.guardar_duracion_sesion_solicitado.connect(
            self._guardar_duracion_sesion
        )
        self._vista_configuracion.probar_impresora_comprobantes_solicitado.connect(
            self._probar_impresora_comprobantes
        )
        self._vista_configuracion.probar_impresora_reportes_solicitado.connect(
            self._probar_impresora_reportes
        )
        self._vista_configuracion.guardar_reportes_pdf_solicitado.connect(
            self._guardar_reportes_pdf
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
        texto_pie: str,
        etiqueta_copia: str,
        mostrar_correo: bool,
        mostrar_telefono: bool,
        mostrar_direccion: bool,
        mostrar_identificador_fiscal: bool,
        firma_habilitada: bool,
        firma_texto_linea: str,
        impresora_termica_nombre: str,
        impresora_termica_ancho_mm: int,
        impresora_termica_corte_automatico: bool,
        impresora_reportes_nombre: str,
    ) -> None:
        resultado = self._servicio_configuracion.guardar_parametros_factura(
            titulo_documento=titulo_documento,
            texto_pie=texto_pie,
            etiqueta_copia=etiqueta_copia,
            mostrar_correo=mostrar_correo,
            mostrar_telefono=mostrar_telefono,
            mostrar_direccion=mostrar_direccion,
            mostrar_identificador_fiscal=mostrar_identificador_fiscal,
            firma_habilitada=firma_habilitada,
            firma_texto_linea=firma_texto_linea,
            impresora_termica_nombre=impresora_termica_nombre,
            impresora_termica_ancho_mm=impresora_termica_ancho_mm,
            impresora_termica_corte_automatico=impresora_termica_corte_automatico,
            impresora_reportes_nombre=impresora_reportes_nombre,
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
        cobrar_mensualidad_prorrateada_activacion: bool,
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
            cobrar_mensualidad_prorrateada_activacion=cobrar_mensualidad_prorrateada_activacion,
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

    def _probar_impresora_comprobantes(self, nombre_impresora: str) -> None:
        resultado = self._servicio_configuracion.probar_impresora_comprobantes(nombre_impresora)
        self._vista_configuracion.mostrar_mensaje(resultado.mensaje, es_error=not resultado.exito)

    def _probar_impresora_reportes(self, nombre_impresora: str) -> None:
        resultado = self._servicio_configuracion.probar_impresora_reportes(nombre_impresora)
        self._vista_configuracion.mostrar_mensaje(resultado.mensaje, es_error=not resultado.exito)

    def _guardar_reportes_pdf(
        self,
        ruta_salida: str,
        abrir_automaticamente: bool,
        firma_habilitada: bool,
        firma_texto_linea: str,
    ) -> None:
        resultado = self._servicio_configuracion.guardar_reportes_pdf(
            ruta_salida=ruta_salida,
            abrir_automaticamente=abrir_automaticamente,
            firma_habilitada=firma_habilitada,
            firma_texto_linea=firma_texto_linea,
            actor_id=None if self._actor is None else self._actor.identificador,
        )
        self._vista_configuracion.mostrar_mensaje(
            resultado.mensaje,
            es_error=not resultado.exito,
        )
        if resultado.exito:
            self._refrescar()
            bus_actualizaciones_modulos.emitir(
                modulo_origen="configuracion",
                modulos_afectados=("reportes",),
            )

    def _restaurar_respaldo_externo(self, ruta_archivo: str) -> None:
        resultado = self._servicio_configuracion.restaurar_respaldo_externo(
            ruta_archivo=ruta_archivo,
            actor_id=None if self._actor is None else self._actor.identificador,
        )
        self._vista_configuracion.mostrar_mensaje(resultado.mensaje, es_error=not resultado.exito)
        if resultado.exito:
            self._programar_reinicio()

    def _programar_reinicio(self) -> None:
        QTimer.singleShot(
            600,
            self._vista_configuracion.reinicio_aplicacion_solicitado.emit,
        )

    def _guardar_duracion_sesion(self, duracion_sesion_horas: float) -> None:
        resultado = self._servicio_configuracion.guardar_duracion_sesion(
            duracion_sesion_horas=duracion_sesion_horas,
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
