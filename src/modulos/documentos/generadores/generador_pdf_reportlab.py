"""Generacion PDF con ReportLab para comprobantes y reportes."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from modulos.documentos.modelos.dto_comprobante_pago import (
    DTOComprobantePago,
    LineaDetalleComprobantePago,
)
from modulos.documentos.modelos.dto_estado_cuenta import DTOEstadoCuenta
from modulos.documentos.modelos.dto_reporte_tabular import DTOReporteTabular


class GeneradorPdfReportLab:
    """Genera PDFs administrativos usando ReportLab Platypus."""

    ANCHO_TICKET = 80 * mm
    MARGEN_TICKET = 4 * mm

    def __init__(self) -> None:
        self._estilos = getSampleStyleSheet()
        self._estilos.add(
            ParagraphStyle(
                name="SicapEncabezado",
                parent=self._estilos["Normal"],
                fontName="Helvetica",
                fontSize=8.5,
                leading=10,
                alignment=TA_CENTER,
                spaceAfter=2,
            )
        )
        self._estilos.add(
            ParagraphStyle(
                name="SicapTituloTicket",
                parent=self._estilos["Normal"],
                fontName="Helvetica-Bold",
                fontSize=12,
                leading=14,
                alignment=TA_CENTER,
                spaceAfter=2,
            )
        )
        self._estilos.add(
            ParagraphStyle(
                name="SicapSubtituloTicket",
                parent=self._estilos["Normal"],
                fontName="Helvetica-Bold",
                fontSize=8.5,
                leading=10,
                alignment=TA_CENTER,
                spaceAfter=4,
            )
        )
        self._estilos.add(
            ParagraphStyle(
                name="SicapTextoTicket",
                parent=self._estilos["Normal"],
                fontName="Helvetica",
                fontSize=8.5,
                leading=10,
                alignment=TA_LEFT,
                spaceAfter=0,
            )
        )
        self._estilos.add(
            ParagraphStyle(
                name="SicapTextoTicketNegrita",
                parent=self._estilos["Normal"],
                fontName="Helvetica-Bold",
                fontSize=8.5,
                leading=10,
                alignment=TA_LEFT,
                spaceAfter=0,
            )
        )
        self._estilos.add(
            ParagraphStyle(
                name="SicapPieTicket",
                parent=self._estilos["Normal"],
                fontName="Helvetica-Bold",
                fontSize=8.5,
                leading=10,
                alignment=TA_CENTER,
                spaceAfter=0,
            )
        )
        self._estilos.add(
            ParagraphStyle(
                name="SicapTituloReporte",
                parent=self._estilos["Heading1"],
                fontName="Helvetica-Bold",
                fontSize=16,
                leading=20,
                alignment=TA_LEFT,
                textColor=colors.black,
                spaceAfter=6,
            )
        )
        self._estilos.add(
            ParagraphStyle(
                name="SicapMetaReporte",
                parent=self._estilos["Normal"],
                fontName="Helvetica",
                fontSize=9,
                leading=11,
                textColor=colors.black,
                spaceAfter=3,
            )
        )

    def generar_comprobante_pago(self, dto: DTOComprobantePago, ruta_destino: str) -> str:
        ruta = Path(ruta_destino).expanduser()
        ruta.parent.mkdir(parents=True, exist_ok=True)
        doc = SimpleDocTemplate(
            str(ruta),
            pagesize=(self.ANCHO_TICKET, self._alto_ticket_estimado(dto)),
            leftMargin=self.MARGEN_TICKET,
            rightMargin=self.MARGEN_TICKET,
            topMargin=4 * mm,
            bottomMargin=4 * mm,
            title=dto.numero_comprobante,
            author="SICAP",
            subject="Comprobante de pago",
        )
        elementos = self._construir_elementos_comprobante(dto)
        doc.build(
            elementos,
            onFirstPage=lambda canvas, _doc: self._aplicar_metadatos(
                canvas,
                titulo=dto.numero_comprobante,
                asunto="Comprobante de pago",
            ),
        )
        return str(ruta)

    def generar_reporte_tabular(self, dto: DTOReporteTabular, ruta_destino: str) -> str:
        ruta = Path(ruta_destino).expanduser()
        ruta.parent.mkdir(parents=True, exist_ok=True)
        doc = SimpleDocTemplate(
            str(ruta),
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=18 * mm,
            bottomMargin=16 * mm,
            title=dto.titulo,
            author="SICAP",
            subject="Reporte administrativo",
        )
        elementos = self._construir_elementos_reporte(dto)
        doc.build(
            elementos,
            onFirstPage=lambda canvas, _doc: self._aplicar_metadatos(
                canvas,
                titulo=dto.titulo,
                asunto="Reporte administrativo",
            ),
        )
        return str(ruta)

    def generar_estado_cuenta_operativo(self, dto: DTOEstadoCuenta, ruta_destino: str) -> str:
        ruta = Path(ruta_destino).expanduser()
        ruta.parent.mkdir(parents=True, exist_ok=True)
        doc = SimpleDocTemplate(
            str(ruta),
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=16 * mm,
            bottomMargin=16 * mm,
            title=dto.titulo,
            author="SICAP",
            subject="Documento operativo de deuda",
        )
        elementos = self._construir_elementos_estado_cuenta(dto)
        doc.build(
            elementos,
            onFirstPage=lambda canvas, _doc: self._aplicar_metadatos(
                canvas,
                titulo=dto.titulo,
                asunto="Documento operativo de deuda",
            ),
        )
        return str(ruta)

    def _construir_elementos_comprobante(self, dto: DTOComprobantePago) -> list[object]:
        elementos: list[object] = []
        for linea in dto.lineas_encabezado:
            elementos.append(Paragraph(self._escapar(linea), self._estilos["SicapEncabezado"]))

        elementos.append(Spacer(1, 1.5 * mm))
        elementos.append(Paragraph(self._escapar(dto.titulo_documento), self._estilos["SicapTituloTicket"]))
        if dto.subtitulo_documento.strip():
            elementos.append(
                Paragraph(self._escapar(dto.subtitulo_documento), self._estilos["SicapSubtituloTicket"])
            )
        elementos.append(
            Paragraph(self._escapar(dto.numero_comprobante), self._estilos["SicapTituloTicket"])
        )
        elementos.append(Spacer(1, 2 * mm))

        elementos.append(
            self._crear_tabla_etiquetas(
                (
                    ("Fecha", dto.fecha),
                    ("Hora", dto.hora),
                    ("Tipo", dto.tipo_comprobante),
                )
            )
        )
        elementos.append(Spacer(1, 1.5 * mm))
        elementos.append(
            self._crear_tabla_etiquetas(
                (
                    ("Casa", dto.casa_codigo),
                    ("Abonado", dto.abonado_nombre),
                    ("DNI", dto.abonado_dni),
                    ("Barrio", dto.barrio_nombre),
                    ("Direccion", dto.direccion_casa),
                )
            )
        )
        elementos.append(Spacer(1, 1.5 * mm))
        elementos.append(
            self._crear_tabla_etiquetas(
                (
                    ("Metodo", dto.metodo_pago),
                    ("Referencia", dto.referencia),
                    ("Registrado por", dto.usuario_registro),
                )
            )
        )
        if dto.texto_legal_superior.strip():
            elementos.append(Spacer(1, 1.2 * mm))
            elementos.append(
                Paragraph(self._escapar(dto.texto_legal_superior), self._estilos["SicapTextoTicket"])
            )

        elementos.append(Spacer(1, 2 * mm))
        elementos.append(self._crear_tabla_detalle(dto.lineas_detalle))
        elementos.append(Spacer(1, 2 * mm))
        elementos.append(
            self._crear_tabla_totales(
                (
                    ("Total pagado", dto.total_pagado),
                    ("Saldo posterior", dto.saldo_posterior),
                )
            )
        )
        elementos.append(Spacer(1, 2 * mm))
        if dto.texto_pie.strip():
            elementos.append(Paragraph(self._escapar(dto.texto_pie), self._estilos["SicapTextoTicket"]))
            elementos.append(Spacer(1, 1.5 * mm))
        if dto.texto_legal_inferior.strip():
            elementos.append(
                Paragraph(self._escapar(dto.texto_legal_inferior), self._estilos["SicapTextoTicket"])
            )
            elementos.append(Spacer(1, 1.5 * mm))
        if dto.etiqueta_copia.strip():
            elementos.append(Paragraph(self._escapar(dto.etiqueta_copia), self._estilos["SicapPieTicket"]))
        elementos.extend(
            self._construir_bloque_firma(
                dto.firma_habilitada,
                dto.firma_nombre,
                dto.firma_cargo,
                dto.firma_identificador,
                dto.firma_texto_apoyo,
            )
        )
        return elementos

    def _construir_elementos_reporte(self, dto: DTOReporteTabular) -> list[object]:
        elementos: list[object] = []
        for linea in dto.lineas_encabezado:
            elementos.append(Paragraph(self._escapar(linea), self._estilos["SicapMetaReporte"]))
        elementos.append(Spacer(1, 3 * mm))
        elementos.append(Paragraph(self._escapar(dto.titulo), self._estilos["SicapTituloReporte"]))
        if dto.descripcion.strip():
            elementos.append(Paragraph(self._escapar(dto.descripcion), self._estilos["SicapMetaReporte"]))
        rango = self._texto_rango(dto.fecha_desde, dto.fecha_hasta)
        if rango:
            elementos.append(Paragraph(self._escapar(rango), self._estilos["SicapMetaReporte"]))
        elementos.append(
            Paragraph(
                self._escapar(f"Generado: {dto.generado_en}"),
                self._estilos["SicapMetaReporte"],
            )
        )
        elementos.append(Spacer(1, 4 * mm))
        elementos.append(self._crear_tabla_reporte(dto.columnas, dto.filas))
        return elementos

    def _construir_elementos_estado_cuenta(self, dto: DTOEstadoCuenta) -> list[object]:
        elementos: list[object] = []
        for linea in dto.lineas_encabezado:
            elementos.append(Paragraph(self._escapar(linea), self._estilos["SicapMetaReporte"]))
        elementos.append(Spacer(1, 3 * mm))
        elementos.append(Paragraph(self._escapar(dto.titulo), self._estilos["SicapTituloReporte"]))
        if dto.subtitulo.strip():
            elementos.append(Paragraph(self._escapar(dto.subtitulo), self._estilos["SicapMetaReporte"]))
        elementos.append(
            Paragraph(
                self._escapar(f"Abonado: {dto.abonado_nombre} | DNI: {dto.abonado_dni}"),
                self._estilos["SicapMetaReporte"],
            )
        )
        elementos.append(
            Paragraph(self._escapar(f"Generado: {dto.generado_en}"), self._estilos["SicapMetaReporte"])
        )
        elementos.append(Spacer(1, 4 * mm))
        for casa in dto.casas:
            elementos.extend(self._construir_bloque_casa_estado_cuenta(casa))
            elementos.append(Spacer(1, 4 * mm))
        if len(dto.casas) > 1:
            elementos.append(
                self._crear_tabla_totales_reporte(
                    (
                        ("Deuda base", dto.total_deuda_base),
                        ("Recargo mora", dto.total_recargo_mora),
                        ("Total general", dto.total_general),
                    )
                )
            )
            elementos.append(Spacer(1, 4 * mm))
        elementos.append(Paragraph(self._escapar(dto.observacion), self._estilos["SicapMetaReporte"]))
        elementos.extend(
            self._construir_bloque_firma(
                dto.firma_habilitada,
                dto.firma_nombre,
                dto.firma_cargo,
                dto.firma_identificador,
                dto.firma_texto_apoyo,
            )
        )
        return elementos

    def _construir_bloque_casa_estado_cuenta(self, casa: object) -> list[object]:
        elementos: list[object] = []
        encabezado = Table(
            [
                [
                    Paragraph(
                        self._escapar(f"{casa.casa_codigo} · {casa.barrio_nombre}"),
                        self._estilos["SicapTextoTicketNegrita"],
                    ),
                    Paragraph(self._escapar(casa.estado_servicio), self._estilos["SicapTextoTicketNegrita"]),
                ],
                [
                    Paragraph(self._escapar(casa.direccion_casa), self._estilos["SicapTextoTicket"]),
                    Paragraph(
                        self._escapar(
                            f"Meses vencidos: {casa.meses_vencidos} | Días en mora: {casa.dias_en_mora} | "
                            f"Prioridad: {casa.prioridad} | Más antiguo: {casa.vencimiento_mas_antiguo}"
                        ),
                        self._estilos["SicapTextoTicket"],
                    ),
                ],
            ],
            colWidths=[92 * mm, 74 * mm],
            hAlign="LEFT",
        )
        encabezado.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
                    ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.black),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ]
            )
        )
        elementos.append(encabezado)
        data = [["Concepto", "Vencimiento", "Saldo"]]
        for linea in casa.lineas_detalle:
            data.append([linea.descripcion, linea.fecha_vencimiento, linea.monto])
        tabla = Table(data, colWidths=[96 * mm, 32 * mm, 38 * mm], repeatRows=1, hAlign="LEFT")
        tabla.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.black),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 8.5),
                    ("FONTSIZE", (0, 1), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.35, colors.black),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("ALIGN", (2, 1), (2, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        elementos.append(tabla)
        elementos.append(
            self._crear_tabla_totales_reporte(
                (
                    ("Deuda base", casa.deuda_base),
                    ("Recargo mora", casa.recargo_mora),
                    ("Total casa", casa.deuda_total),
                )
            )
        )
        return elementos

    def _crear_tabla_etiquetas(self, filas: tuple[tuple[str, str], ...]) -> Table:
        data = [
            [
                Paragraph(self._escapar(etiqueta), self._estilos["SicapTextoTicketNegrita"]),
                Paragraph(self._escapar(valor), self._estilos["SicapTextoTicket"]),
            ]
            for etiqueta, valor in filas
        ]
        tabla = Table(data, colWidths=[20 * mm, 48 * mm], hAlign="LEFT")
        tabla.setStyle(
            TableStyle(
                [
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 1.5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("LINEBELOW", (0, -1), (-1, -1), 0.45, colors.black),
                ]
            )
        )
        return tabla

    def _construir_bloque_firma(
        self,
        habilitada: bool,
        nombre: str,
        cargo: str,
        identificador: str,
        texto_apoyo: str,
    ) -> list[object]:
        if not habilitada:
            return []
        elementos: list[object] = [Spacer(1, 6 * mm)]
        linea = Table([[""]], colWidths=[70 * mm], hAlign="CENTER")
        linea.setStyle(
            TableStyle(
                [
                    ("LINEABOVE", (0, 0), (0, 0), 0.8, colors.black),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        elementos.append(linea)
        if nombre.strip():
            elementos.append(Paragraph(self._escapar(nombre), self._estilos["SicapMetaReporte"]))
        if cargo.strip():
            elementos.append(Paragraph(self._escapar(cargo), self._estilos["SicapMetaReporte"]))
        if identificador.strip():
            elementos.append(
                Paragraph(
                    self._escapar(f"Identificador: {identificador}"),
                    self._estilos["SicapMetaReporte"],
                )
            )
        if texto_apoyo.strip():
            elementos.append(Paragraph(self._escapar(texto_apoyo), self._estilos["SicapMetaReporte"]))
        return elementos

    def _crear_tabla_detalle(self, lineas: tuple[LineaDetalleComprobantePago, ...]) -> Table:
        data = [
            [
                Paragraph(self._escapar(linea.descripcion), self._estilos["SicapTextoTicket"]),
                Paragraph(self._escapar(linea.monto), self._estilos["SicapTextoTicket"]),
            ]
            for linea in lineas
        ] or [[Paragraph("Sin detalle registrado.", self._estilos["SicapTextoTicket"]), Paragraph("", self._estilos["SicapTextoTicket"])]]
        tabla = Table(data, colWidths=[52 * mm, 16 * mm], hAlign="LEFT")
        tabla.setStyle(
            TableStyle(
                [
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("LINEBELOW", (0, 0), (-1, -1), 0.35, colors.black),
                ]
            )
        )
        return tabla

    def _crear_tabla_totales(self, filas: tuple[tuple[str, str], ...]) -> Table:
        data = [
            [
                Paragraph(self._escapar(etiqueta), self._estilos["SicapTextoTicketNegrita"]),
                Paragraph(self._escapar(valor), self._estilos["SicapTextoTicketNegrita"]),
            ]
            for etiqueta, valor in filas
        ]
        tabla = Table(data, colWidths=[40 * mm, 28 * mm], hAlign="LEFT")
        tabla.setStyle(
            TableStyle(
                [
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("LINEABOVE", (0, 0), (-1, 0), 0.5, colors.black),
                    ("LINEBELOW", (0, -1), (-1, -1), 0.5, colors.black),
                ]
            )
        )
        return tabla

    def _crear_tabla_reporte(self, columnas: tuple[str, ...], filas: tuple[tuple[str, ...], ...]) -> Table:
        data = [list(columnas), *[list(fila) for fila in filas]]
        total_columnas = max(1, len(columnas))
        ancho_disponible = A4[0] - (36 * mm)
        col_width = ancho_disponible / total_columnas
        tabla = Table(data, colWidths=[col_width] * total_columnas, repeatRows=1)
        tabla.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.black),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 9),
                    ("FONTSIZE", (0, 1), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.35, colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        return tabla

    def _crear_tabla_totales_reporte(self, filas: tuple[tuple[str, str], ...]) -> Table:
        data = [[etiqueta, valor] for etiqueta, valor in filas]
        tabla = Table(data, colWidths=[118 * mm, 48 * mm], hAlign="LEFT")
        tabla.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.35, colors.black),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ]
            )
        )
        return tabla

    @staticmethod
    def _aplicar_metadatos(canvas: object, titulo: str, asunto: str) -> None:
        canvas.setTitle(titulo)
        canvas.setAuthor("SICAP")
        canvas.setSubject(asunto)

    @staticmethod
    def _texto_rango(fecha_desde: str, fecha_hasta: str) -> str:
        if fecha_desde and fecha_hasta:
            return f"Rango aplicado: {fecha_desde} a {fecha_hasta}"
        if fecha_desde:
            return f"Desde: {fecha_desde}"
        if fecha_hasta:
            return f"Hasta: {fecha_hasta}"
        return ""

    @staticmethod
    def _escapar(valor: str) -> str:
        return (
            str(valor)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    @staticmethod
    def _alto_ticket_estimado(dto: DTOComprobantePago) -> float:
        base_mm = 105 + (len(dto.lineas_encabezado) * 4)
        base_mm += len(dto.lineas_detalle) * 8
        if dto.texto_legal_superior.strip():
            base_mm += 8
        if dto.texto_pie.strip():
            base_mm += 6
        if dto.texto_legal_inferior.strip():
            base_mm += 6
        return min(max(base_mm * mm, 140 * mm), 320 * mm)
