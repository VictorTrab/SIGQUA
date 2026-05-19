"""Servicio documental para comprobantes de pago."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from comun.configuracion.gestor_rutas import GestorRutas
from modulos.documentos.generadores.generador_pdf_reportlab import GeneradorPdfReportLab
from modulos.documentos.modelos.dto_comprobante_pago import (
    DTOComprobantePago,
    LineaDetalleComprobantePago,
)

if TYPE_CHECKING:
    from modulos.pagos.entidades import ComprobantePago, ConfiguracionReciboPago


class ServicioComprobantePago:
    """Adapta comprobantes del dominio al backend PDF."""

    def __init__(
        self,
        generador_pdf: GeneradorPdfReportLab | None = None,
        gestor_rutas: GestorRutas | None = None,
    ) -> None:
        self._generador_pdf = generador_pdf or GeneradorPdfReportLab()
        self._gestor_rutas = gestor_rutas or GestorRutas()

    def construir_dto(
        self,
        comprobante: "ComprobantePago",
        configuracion: "ConfiguracionReciboPago",
        formateador_moneda: callable,
        formateador_fecha: callable,
        formateador_hora: callable,
        etiqueta_tipo_pago: callable,
    ) -> DTOComprobantePago:
        marca_emision = self._fecha_emision_actual()
        self._validar_fecha_emision_actual(marca_emision)
        return DTOComprobantePago(
            numero_comprobante=comprobante.numero_comprobante,
            lineas_encabezado=tuple(self.lineas_encabezado_desde_configuracion(configuracion)),
            titulo_documento=configuracion.titulo_documento,
            subtitulo_documento=configuracion.subtitulo_documento,
            texto_legal_superior=configuracion.texto_legal_superior,
            texto_pie=configuracion.texto_pie,
            texto_legal_inferior=configuracion.texto_legal_inferior,
            etiqueta_copia=configuracion.etiqueta_copia,
            fecha=formateador_fecha(marca_emision),
            hora=formateador_hora(marca_emision),
            tipo_comprobante=etiqueta_tipo_pago(comprobante.tipo_comprobante),
            casa_codigo=comprobante.casa_codigo,
            abonado_nombre=comprobante.abonado_nombre,
            abonado_dni=comprobante.abonado_dni,
            barrio_nombre=comprobante.barrio_nombre or "Sin barrio",
            direccion_casa=comprobante.direccion_casa or "Sin referencia",
            metodo_pago=comprobante.metodo_pago,
            referencia=comprobante.referencia or "No aplica",
            usuario_registro=comprobante.usuario_registro or "Sin registro",
            lineas_detalle=tuple(
                LineaDetalleComprobantePago(
                    descripcion=descripcion,
                    monto=monto,
                )
                for descripcion, monto in self._descomponer_detalles(comprobante.detalles)
            ),
            total_pagado=formateador_moneda(comprobante.total_pagado_centavos),
            saldo_posterior=formateador_moneda(comprobante.saldo_posterior_centavos),
            firma_habilitada=configuracion.firma_habilitada,
            firma_nombre=configuracion.firma_nombre,
            firma_cargo=configuracion.firma_cargo,
            firma_identificador=configuracion.firma_identificador,
            firma_texto_apoyo=configuracion.firma_texto_apoyo,
        )

    def generar_pdf(
        self,
        comprobante: "ComprobantePago",
        configuracion: "ConfiguracionReciboPago",
        formateador_moneda: callable,
        formateador_fecha: callable,
        formateador_hora: callable,
        etiqueta_tipo_pago: callable,
        ruta_destino: str | None = None,
    ) -> str:
        dto = self.construir_dto(
            comprobante=comprobante,
            configuracion=configuracion,
            formateador_moneda=formateador_moneda,
            formateador_fecha=formateador_fecha,
            formateador_hora=formateador_hora,
            etiqueta_tipo_pago=etiqueta_tipo_pago,
        )
        ruta = ruta_destino or self.ruta_sugerida(comprobante.numero_comprobante)
        return self._generador_pdf.generar_comprobante_pago(dto, ruta)

    def ruta_sugerida(self, numero_comprobante: str) -> str:
        return str(
            self._gestor_rutas.obtener_ruta_exportaciones_comprobantes()
            / f"{numero_comprobante}.pdf"
        )

    @staticmethod
    def lineas_encabezado_desde_configuracion(
        configuracion: "ConfiguracionReciboPago",
    ) -> list[str]:
        lineas: list[str] = []
        if configuracion.nombre_junta.strip():
            lineas.append(configuracion.nombre_junta.strip())
        if configuracion.mostrar_identificador_fiscal and configuracion.identificador_fiscal.strip():
            lineas.append(f"ID fiscal: {configuracion.identificador_fiscal.strip()}")
        if configuracion.mostrar_telefono and configuracion.telefono_junta.strip():
            lineas.append(configuracion.telefono_junta.strip())
        if configuracion.mostrar_correo and configuracion.correo_junta.strip():
            lineas.append(configuracion.correo_junta.strip())
        if configuracion.mostrar_direccion and configuracion.direccion_junta.strip():
            lineas.append(configuracion.direccion_junta.strip())
        if configuracion.sitio_web.strip():
            lineas.append(configuracion.sitio_web.strip())
        if configuracion.mensaje_contacto.strip():
            lineas.append(configuracion.mensaje_contacto.strip())
        return lineas or ["Empresa no configurada"]

    @staticmethod
    def _descomponer_detalles(detalles: tuple[str, ...]) -> tuple[tuple[str, str], ...]:
        resultado: list[tuple[str, str]] = []
        for detalle in detalles:
            descripcion, separador, monto = detalle.rpartition(" - ")
            if separador:
                resultado.append((descripcion.strip(), monto.strip()))
            else:
                resultado.append((detalle.strip(), ""))
        return tuple(resultado)

    @staticmethod
    def _fecha_emision_actual() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _validar_fecha_emision_actual(valor: str) -> None:
        fecha_emision = datetime.strptime(valor, "%Y-%m-%d %H:%M:%S").date()
        if fecha_emision != datetime.now().date():
            raise ValueError("La fecha de emisión del comprobante debe coincidir con la fecha actual.")
