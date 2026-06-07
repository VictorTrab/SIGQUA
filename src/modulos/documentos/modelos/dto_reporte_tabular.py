"""DTOs limpios para reportes PDF."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DTOReporteTabular:
    """Reporte tabular listo para generacion PDF."""

    codigo_reporte: str
    titulo: str
    descripcion: str
    columnas: tuple[str, ...]
    filas: tuple[tuple[str, ...], ...]
    fecha_desde: str
    fecha_hasta: str
    generado_en: str
    generado_por: str
    lineas_encabezado: tuple[str, ...]
    resumen: tuple[tuple[str, str], ...] = ()
    orientacion: str = "VERTICAL"
    firma_habilitada: bool = False
    firma_texto_linea: str = "Firma autorizada"
