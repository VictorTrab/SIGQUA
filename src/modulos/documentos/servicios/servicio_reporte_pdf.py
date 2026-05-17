"""Servicio documental para reportes tabulares PDF."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from comun.configuracion.gestor_rutas import GestorRutas
from modulos.documentos.generadores.generador_pdf_reportlab import GeneradorPdfReportLab
from modulos.documentos.modelos.dto_reporte_tabular import DTOReporteTabular

if TYPE_CHECKING:
    from modulos.reportes.entidades import TablaReporte


class ServicioReportePdf:
    """Adapta tablas administrativas del dominio a PDF."""

    def __init__(
        self,
        generador_pdf: GeneradorPdfReportLab | None = None,
        gestor_rutas: GestorRutas | None = None,
    ) -> None:
        self._generador_pdf = generador_pdf or GeneradorPdfReportLab()
        self._gestor_rutas = gestor_rutas or GestorRutas()

    def construir_dto(
        self,
        tabla: "TablaReporte",
        fecha_desde: str,
        fecha_hasta: str,
        lineas_encabezado: tuple[str, ...],
        generado_en: str | None = None,
    ) -> DTOReporteTabular:
        marca_tiempo = generado_en or self._fecha_emision_actual()
        self._validar_fecha_emision_actual(marca_tiempo)
        return DTOReporteTabular(
            codigo_reporte=tabla.codigo,
            titulo=tabla.titulo,
            descripcion=tabla.descripcion,
            columnas=tabla.columnas,
            filas=tabla.filas,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            generado_en=marca_tiempo,
            lineas_encabezado=lineas_encabezado,
        )

    def generar_pdf(
        self,
        tabla: "TablaReporte",
        fecha_desde: str,
        fecha_hasta: str,
        lineas_encabezado: tuple[str, ...],
        ruta_destino: str | None = None,
    ) -> str:
        dto = self.construir_dto(
            tabla=tabla,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            lineas_encabezado=lineas_encabezado,
        )
        ruta = ruta_destino or self.ruta_sugerida(tabla.codigo)
        return self._generador_pdf.generar_reporte_tabular(dto, ruta)

    def ruta_sugerida(self, codigo_reporte: str) -> str:
        marca = datetime.now().strftime("%Y%m%d_%H%M%S")
        return str(
            self._gestor_rutas.obtener_ruta_exportaciones_reportes()
            / f"{codigo_reporte}_{marca}.pdf"
        )

    @staticmethod
    def _fecha_emision_actual() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _validar_fecha_emision_actual(valor: str) -> None:
        fecha_emision = datetime.strptime(valor, "%Y-%m-%d %H:%M:%S").date()
        if fecha_emision != datetime.now().date():
            raise ValueError("La fecha de emisión del reporte debe coincidir con la fecha actual.")
