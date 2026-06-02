"""Servicio documental para documentos operativos de deuda."""

from __future__ import annotations

from datetime import datetime

from comun.configuracion.documentos import lineas_encabezado_documental
from comun.configuracion.gestor_rutas import GestorRutas
from modulos.documentos.generadores.generador_pdf_reportlab import GeneradorPdfReportLab
from modulos.documentos.modelos.dto_estado_cuenta import (
    CasaEstadoCuenta,
    DTOEstadoCuenta,
    LineaDetalleEstadoCuenta,
)


class ServicioEstadoCuenta:
    """Construye PDFs de deuda por abonado o por casas seleccionadas."""

    def __init__(
        self,
        generador_pdf: GeneradorPdfReportLab | None = None,
        gestor_rutas: GestorRutas | None = None,
    ) -> None:
        self._generador_pdf = generador_pdf or GeneradorPdfReportLab()
        self._gestor_rutas = gestor_rutas or GestorRutas()

    def generar_pdf(
        self,
        detalle: object,
        casas_seleccionadas: tuple[int, ...],
        lineas_encabezado: tuple[str, ...],
        formateador_moneda: callable,
        formateador_fecha: callable,
        firma: object | None = None,
        ruta_destino: str | None = None,
    ) -> str:
        dto = self.construir_dto(
            detalle=detalle,
            casas_seleccionadas=casas_seleccionadas,
            lineas_encabezado=lineas_encabezado,
            formateador_moneda=formateador_moneda,
            formateador_fecha=formateador_fecha,
            firma=firma,
        )
        ruta = ruta_destino or self.ruta_sugerida(dto.abonado_nombre)
        return self._generador_pdf.generar_estado_cuenta_operativo(dto, ruta)

    def construir_dto(
        self,
        detalle: object,
        casas_seleccionadas: tuple[int, ...],
        lineas_encabezado: tuple[str, ...],
        formateador_moneda: callable,
        formateador_fecha: callable,
        firma: object | None = None,
    ) -> DTOEstadoCuenta:
        casas_fuente = tuple(
            casa
            for casa in getattr(detalle, "casas", ())
            if not casas_seleccionadas or casa.casa_id in casas_seleccionadas
        )
        deuda_base = sum(casa.deuda_base_centavos for casa in casas_fuente)
        recargo = sum(casa.recargo_mora_centavos for casa in casas_fuente)
        total = sum(casa.deuda_total_centavos for casa in casas_fuente)
        marca_emision = self._fecha_emision_actual()
        self._validar_fecha_emision_actual(marca_emision)
        return DTOEstadoCuenta(
            titulo="DOCUMENTO DE DEUDA",
            subtitulo="Detalle operativo generado desde morosidad",
            lineas_encabezado=lineas_encabezado,
            abonado_nombre=getattr(detalle, "abonado_nombre", ""),
            abonado_dni=getattr(detalle, "abonado_dni", ""),
            generado_en=datetime.strptime(marca_emision, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M"),
            observacion=(
                "Documento de consulta operativa. Los montos reflejan cargos vencidos y recargos "
                "vigentes al momento de la emision."
            ),
            casas=tuple(
                CasaEstadoCuenta(
                    casa_codigo=casa.casa_codigo,
                    barrio_nombre=casa.barrio_nombre or "Sin barrio",
                    direccion_casa=casa.direccion_casa or "Sin referencia",
                    estado_servicio=casa.estado_servicio,
                    meses_vencidos=casa.meses_vencidos,
                    dias_en_mora=getattr(casa, "dias_en_mora", 0),
                    prioridad=getattr(casa, "prioridad", "Baja"),
                    vencimiento_mas_antiguo=formateador_fecha(casa.vencimiento_mas_antiguo),
                    deuda_base=formateador_moneda(casa.deuda_base_centavos),
                    recargo_mora=formateador_moneda(casa.recargo_mora_centavos),
                    deuda_total=formateador_moneda(casa.deuda_total_centavos),
                    estado_aviso_cobro=getattr(casa, "estado_aviso_cobro", "SIN_AVISO"),
                    fecha_ultimo_aviso=formateador_fecha(getattr(casa, "fecha_ultimo_aviso", "")),
                    lineas_detalle=tuple(
                        LineaDetalleEstadoCuenta(
                            descripcion=linea.descripcion,
                            fecha_vencimiento=formateador_fecha(linea.fecha_vencimiento),
                            monto=formateador_moneda(linea.saldo_pendiente_centavos),
                        )
                        for linea in casa.lineas_detalle
                    ),
                )
                for casa in casas_fuente
            ),
            total_deuda_base=formateador_moneda(deuda_base),
            total_recargo_mora=formateador_moneda(recargo),
            total_general=formateador_moneda(total),
            firma_habilitada=bool(getattr(firma, "firma_habilitada", False)),
            firma_texto_linea=str(getattr(firma, "firma_texto_linea", "Firma autorizada")),
        )

    def ruta_sugerida(self, abonado_nombre: str) -> str:
        base = "".join(
            caracter.lower() if caracter.isalnum() else "_"
            for caracter in abonado_nombre.strip()
        ).strip("_")
        nombre = base or "abonado"
        sello = datetime.now().strftime("%Y%m%d_%H%M%S")
        return str(
            self._gestor_rutas.obtener_ruta_exportaciones_reportes()
            / f"deuda_{nombre}_{sello}.pdf"
        )

    @staticmethod
    def lineas_encabezado_desde_configuracion(configuracion: object) -> tuple[str, ...]:
        return tuple(lineas_encabezado_documental(configuracion))

    @staticmethod
    def _fecha_emision_actual() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _validar_fecha_emision_actual(valor: str) -> None:
        fecha_emision = datetime.strptime(valor, "%Y-%m-%d %H:%M:%S").date()
        if fecha_emision != datetime.now().date():
            raise ValueError("La fecha de emisión del documento de deuda debe coincidir con la fecha actual.")
