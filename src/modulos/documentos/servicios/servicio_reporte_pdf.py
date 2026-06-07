"""Servicio documental para reportes tabulares PDF."""

from __future__ import annotations

from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
import re
import tempfile
from typing import TYPE_CHECKING
import unicodedata

from comun.configuracion.gestor_rutas import GestorRutas
from modulos.documentos.generadores.generador_pdf_reportlab import GeneradorPdfReportLab
from modulos.documentos.modelos.dto_reporte_tabular import DTOReporteTabular

if TYPE_CHECKING:
    from modulos.reportes.entidades import TablaReporte


@dataclass(frozen=True, slots=True)
class ResultadoGeneracionReportePdf:
    ruta: str
    uso_fallback: bool = False


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
        generado_por: str = "Sistema",
        firma_habilitada: bool = False,
        firma_texto_linea: str = "Firma autorizada",
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
            generado_por=generado_por.strip() or "Sistema",
            lineas_encabezado=lineas_encabezado,
            resumen=tabla.resumen,
            orientacion=tabla.orientacion,
            firma_habilitada=firma_habilitada,
            firma_texto_linea=firma_texto_linea.strip() or "Firma autorizada",
        )

    def generar_pdf(
        self,
        tabla: "TablaReporte",
        fecha_desde: str,
        fecha_hasta: str,
        lineas_encabezado: tuple[str, ...],
        ruta_destino: str | None = None,
        directorio_destino: str | None = None,
        generado_por: str = "Sistema",
        firma_habilitada: bool = False,
        firma_texto_linea: str = "Firma autorizada",
    ) -> str:
        return self.generar_pdf_con_resultado(
            tabla=tabla,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            lineas_encabezado=lineas_encabezado,
            ruta_destino=ruta_destino,
            directorio_destino=directorio_destino,
            generado_por=generado_por,
            firma_habilitada=firma_habilitada,
            firma_texto_linea=firma_texto_linea,
        ).ruta

    def generar_pdf_con_resultado(
        self,
        tabla: "TablaReporte",
        fecha_desde: str,
        fecha_hasta: str,
        lineas_encabezado: tuple[str, ...],
        ruta_destino: str | None = None,
        directorio_destino: str | None = None,
        generado_por: str = "Sistema",
        firma_habilitada: bool = False,
        firma_texto_linea: str = "Firma autorizada",
    ) -> ResultadoGeneracionReportePdf:
        dto = self.construir_dto(
            tabla=tabla,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            lineas_encabezado=lineas_encabezado,
            generado_por=generado_por,
            firma_habilitada=firma_habilitada,
            firma_texto_linea=firma_texto_linea,
        )
        ruta, uso_fallback = self._resolver_ruta_destino(
            tabla.codigo,
            ruta_destino=ruta_destino,
            directorio_destino=directorio_destino,
        )
        ruta_generada = self._generador_pdf.generar_reporte_tabular(dto, str(ruta))
        return ResultadoGeneracionReportePdf(ruta_generada, uso_fallback)

    def ruta_sugerida(self, codigo_reporte: str) -> str:
        ruta, _ = self._resolver_ruta_destino(
            codigo_reporte,
            directorio_destino=str(self._gestor_rutas.obtener_ruta_reportes_predeterminada()),
        )
        return str(ruta)

    def _resolver_ruta_destino(
        self,
        codigo_reporte: str,
        *,
        ruta_destino: str | None = None,
        directorio_destino: str | None = None,
    ) -> tuple[Path, bool]:
        if ruta_destino:
            ruta = Path(ruta_destino).expanduser()
            if ruta.suffix.lower() != ".pdf":
                ruta = ruta.with_suffix(".pdf")
            ruta.parent.mkdir(parents=True, exist_ok=True)
            return self._evitar_colision(ruta), False

        directorio = Path(
            directorio_destino or self._gestor_rutas.obtener_ruta_reportes_predeterminada()
        ).expanduser()
        uso_fallback = False
        if not self._directorio_escribible(directorio):
            directorio = self._gestor_rutas.obtener_ruta_exportaciones_reportes()
            directorio.mkdir(parents=True, exist_ok=True)
            uso_fallback = True
        nombre = self._construir_nombre_archivo(codigo_reporte)
        return self._evitar_colision(directorio / nombre), uso_fallback

    @staticmethod
    def _directorio_escribible(directorio: Path) -> bool:
        try:
            directorio.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                dir=directorio,
                prefix=".sigqua_prueba_",
            ):
                pass
            return True
        except OSError:
            return False

    @classmethod
    def _construir_nombre_archivo(cls, codigo_reporte: str) -> str:
        marca = datetime.now().strftime("%Y%m%d_%H%M%S")
        codigo = cls._sanear_segmento(codigo_reporte).upper() or "REPORTE"
        return f"SIGQUA_{codigo}_{marca}.pdf"

    @staticmethod
    def _sanear_segmento(valor: str) -> str:
        normalizado = unicodedata.normalize("NFKD", str(valor))
        ascii_limpio = normalizado.encode("ascii", "ignore").decode("ascii")
        return re.sub(r"[^A-Za-z0-9_-]+", "_", ascii_limpio).strip("._ ")

    @staticmethod
    def _evitar_colision(ruta: Path) -> Path:
        if not ruta.exists():
            return ruta
        indice = 2
        while True:
            candidata = ruta.with_name(f"{ruta.stem}_{indice}{ruta.suffix}")
            if not candidata.exists():
                return candidata
            indice += 1

    @staticmethod
    def _fecha_emision_actual() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _validar_fecha_emision_actual(valor: str) -> None:
        fecha_emision = datetime.strptime(valor, "%Y-%m-%d %H:%M:%S").date()
        if fecha_emision != datetime.now().date():
            raise ValueError("La fecha de emisión del reporte debe coincidir con la fecha actual.")
