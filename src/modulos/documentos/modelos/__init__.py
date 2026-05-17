"""DTOs del backend documental."""

from modulos.documentos.modelos.dto_comprobante_pago import (
    DTOComprobantePago,
    LineaDetalleComprobantePago,
)
from modulos.documentos.modelos.dto_reporte_tabular import DTOReporteTabular

__all__ = [
    "DTOComprobantePago",
    "DTOReporteTabular",
    "LineaDetalleComprobantePago",
]
