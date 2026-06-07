"""Generacion PDF con ReportLab para reportes administrativos."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from modulos.documentos.modelos.dto_estado_cuenta import DTOEstadoCuenta
from modulos.documentos.modelos.dto_reporte_tabular import DTOReporteTabular


class _CanvasReportePaginado(Canvas):
    """Canvas que agrega codigo, fecha y numeracion total al pie."""

    def __init__(self, *args: object, codigo: str, generado_en: str, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self._codigo = codigo
        self._generado_en = generado_en
        self._estados_paginas: list[dict[str, object]] = []

    def showPage(self) -> None:  # noqa: N802 - firma ReportLab
        self._estados_paginas.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        total = len(self._estados_paginas)
        for numero, estado in enumerate(self._estados_paginas, start=1):
            self.__dict__.update(estado)
            self._dibujar_pie(numero, total)
            super().showPage()
        super().save()

    def _dibujar_pie(self, pagina: int, total: int) -> None:
        ancho, _alto = self._pagesize
        self.saveState()
        self.setStrokeColor(colors.HexColor("#B8B8B8"))
        self.setLineWidth(0.4)
        self.line(14 * mm, 12 * mm, ancho - 14 * mm, 12 * mm)
        self.setFillColor(colors.HexColor("#555555"))
        self.setFont("Helvetica", 7.5)
        self.drawString(14 * mm, 7.5 * mm, f"{self._codigo} | {self._generado_en}")
        self.drawRightString(ancho - 14 * mm, 7.5 * mm, f"Pagina {pagina} de {total}")
        self.restoreState()


class GeneradorPdfReportLab:
    """Genera PDFs administrativos usando ReportLab Platypus."""

    def __init__(self) -> None:
        self._estilos = getSampleStyleSheet()
        self._estilos.add(
            ParagraphStyle(
                name="SigquaEncabezado",
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
                name="SigquaInstitucionReporte",
                parent=self._estilos["Normal"],
                fontName="Helvetica-Bold",
                fontSize=15,
                leading=17,
                alignment=TA_LEFT,
                textColor=colors.HexColor("#111111"),
                spaceAfter=3,
            )
        )
        self._estilos.add(
            ParagraphStyle(
                name="SigquaDatoInstitucional",
                parent=self._estilos["Normal"],
                fontName="Helvetica",
                fontSize=7.8,
                leading=9.5,
                alignment=TA_LEFT,
                textColor=colors.HexColor("#4A4A4A"),
            )
        )
        self._estilos.add(
            ParagraphStyle(
                name="SigquaCeldaReporte",
                parent=self._estilos["Normal"],
                fontName="Helvetica",
                fontSize=7.8,
                leading=9.8,
                alignment=TA_LEFT,
                textColor=colors.HexColor("#1F1F1F"),
            )
        )
        self._estilos.add(
            ParagraphStyle(
                name="SigquaCeldaReporteDerecha",
                parent=self._estilos["SigquaCeldaReporte"],
                alignment=TA_RIGHT,
            )
        )
        self._estilos.add(
            ParagraphStyle(
                name="SigquaCabeceraTablaReporte",
                parent=self._estilos["Normal"],
                fontName="Helvetica-Bold",
                fontSize=8,
                leading=10,
                alignment=TA_LEFT,
                textColor=colors.white,
            )
        )
        self._estilos.add(
            ParagraphStyle(
                name="SigquaEtiquetaTotalReporte",
                parent=self._estilos["Normal"],
                fontName="Helvetica-Bold",
                fontSize=9.5,
                leading=11.5,
                alignment=TA_LEFT,
                textColor=colors.white,
            )
        )
        self._estilos.add(
            ParagraphStyle(
                name="SigquaValorTotalReporte",
                parent=self._estilos["SigquaEtiquetaTotalReporte"],
                fontSize=10,
                alignment=TA_RIGHT,
            )
        )
        self._estilos.add(
            ParagraphStyle(
                name="SigquaFirmaReporte",
                parent=self._estilos["Normal"],
                fontName="Helvetica",
                fontSize=8.5,
                leading=10,
                alignment=TA_CENTER,
                textColor=colors.HexColor("#303030"),
                spaceBefore=2,
            )
        )
        self._estilos.add(
            ParagraphStyle(
                name="SigquaTituloTicket",
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
                name="SigquaSubtituloTicket",
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
                name="SigquaTextoTicket",
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
                name="SigquaTextoTicketNegrita",
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
                name="SigquaPieTicket",
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
                name="SigquaTituloReporte",
                parent=self._estilos["Heading1"],
                fontName="Helvetica-Bold",
                fontSize=17,
                leading=21,
                alignment=TA_LEFT,
                textColor=colors.HexColor("#151515"),
                spaceAfter=5,
            )
        )
        self._estilos.add(
            ParagraphStyle(
                name="SigquaMetaReporte",
                parent=self._estilos["Normal"],
                fontName="Helvetica",
                fontSize=8.5,
                leading=10.5,
                textColor=colors.HexColor("#454545"),
                spaceAfter=3,
            )
        )

    def generar_reporte_tabular(self, dto: DTOReporteTabular, ruta_destino: str) -> str:
        ruta = Path(ruta_destino).expanduser()
        ruta.parent.mkdir(parents=True, exist_ok=True)
        tamano_pagina = (
            landscape(letter)
            if dto.orientacion.upper() == "HORIZONTAL"
            else letter
        )
        doc = SimpleDocTemplate(
            str(ruta),
            pagesize=tamano_pagina,
            leftMargin=14 * mm,
            rightMargin=14 * mm,
            topMargin=14 * mm,
            bottomMargin=18 * mm,
            title=dto.titulo,
            author="SIGQUA",
            subject="Reporte administrativo",
        )
        elementos = self._construir_elementos_reporte(dto)
        doc.build(
            elementos,
            canvasmaker=lambda *args, **kwargs: _CanvasReportePaginado(
                *args,
                codigo=dto.codigo_reporte,
                generado_en=dto.generado_en,
                **kwargs,
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
            author="SIGQUA",
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

    def _construir_elementos_reporte(self, dto: DTOReporteTabular) -> list[object]:
        elementos: list[object] = [self._crear_encabezado_reporte(dto)]
        elementos.append(Spacer(1, 6 * mm))
        elementos.append(Paragraph(self._escapar(dto.titulo), self._estilos["SigquaTituloReporte"]))
        if dto.descripcion.strip():
            elementos.append(Paragraph(self._escapar(dto.descripcion), self._estilos["SigquaMetaReporte"]))
        rango = self._texto_rango(dto.fecha_desde, dto.fecha_hasta)
        if rango:
            elementos.append(Paragraph(self._escapar(rango), self._estilos["SigquaMetaReporte"]))
        elementos.append(Spacer(1, 3.5 * mm))
        elementos.append(self._crear_tabla_reporte(dto))
        elementos.append(Spacer(1, 5 * mm))
        elementos.append(self._crear_resumen_reporte(dto.resumen))
        elementos.extend(
            self._construir_bloque_firma(
                dto.firma_habilitada,
                dto.firma_texto_linea,
            )
        )
        return elementos

    def _crear_encabezado_reporte(self, dto: DTOReporteTabular) -> Table:
        lineas = tuple(linea for linea in dto.lineas_encabezado if str(linea).strip())
        nombre = lineas[0] if lineas else "SIGQUA"
        datos = lineas[1:] if len(lineas) > 1 else ("Sistema de Control Administrativo",)
        izquierda = [
            Paragraph(self._escapar(nombre.upper()), self._estilos["SigquaInstitucionReporte"]),
            *[
                Paragraph(self._escapar(linea), self._estilos["SigquaDatoInstitucional"])
                for linea in datos
            ],
        ]
        fecha, hora = self._separar_fecha_hora(dto.generado_en)
        estilo_etiqueta = ParagraphStyle(
            "SigquaEtiquetaDocumento",
            parent=self._estilos["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7,
            leading=8,
            textColor=colors.HexColor("#595959"),
        )
        estilo_valor = ParagraphStyle(
            "SigquaValorDocumento",
            parent=estilo_etiqueta,
            fontSize=7.5,
            leading=8.5,
            textColor=colors.HexColor("#171717"),
        )
        estilo_cabecera_documento = ParagraphStyle(
            "SigquaCabeceraDocumento",
            parent=estilo_valor,
            fontName="Helvetica-Bold",
            textColor=colors.white,
        )
        derecha = Table(
            [
                [
                    Paragraph("TIPO", estilo_cabecera_documento),
                    Paragraph("REPORTE", estilo_cabecera_documento),
                ],
                [
                    Paragraph("CÓDIGO", estilo_etiqueta),
                    Paragraph(self._escapar(dto.codigo_reporte.upper()), estilo_valor),
                ],
                [
                    Paragraph("FECHA", estilo_etiqueta),
                    Paragraph(self._escapar(fecha), estilo_valor),
                ],
                [
                    Paragraph("HORA", estilo_etiqueta),
                    Paragraph(self._escapar(hora), estilo_valor),
                ],
                [
                    Paragraph("USUARIO", estilo_etiqueta),
                    Paragraph(self._escapar(dto.generado_por), estilo_valor),
                ],
            ],
            colWidths=[19 * mm, 51 * mm],
        )
        derecha.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#202020")),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F2F2F2")),
                    ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#575757")),
                    ("LINEBELOW", (0, 0), (-1, -2), 0.35, colors.HexColor("#C4C4C4")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4.5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4.5),
                    ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        ancho_pagina = landscape(letter)[0] if dto.orientacion.upper() == "HORIZONTAL" else letter[0]
        ancho_util = ancho_pagina - 28 * mm
        encabezado = Table(
            [[izquierda, derecha]],
            colWidths=[ancho_util - 74 * mm, 74 * mm],
            hAlign="LEFT",
        )
        encabezado.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LINEBELOW", (0, 0), (-1, -1), 1.8, colors.HexColor("#222222")),
                ]
            )
        )
        return encabezado

    def _construir_elementos_estado_cuenta(self, dto: DTOEstadoCuenta) -> list[object]:
        elementos: list[object] = []
        for linea in dto.lineas_encabezado:
            elementos.append(Paragraph(self._escapar(linea), self._estilos["SigquaMetaReporte"]))
        elementos.append(Spacer(1, 3 * mm))
        elementos.append(Paragraph(self._escapar(dto.titulo), self._estilos["SigquaTituloReporte"]))
        if dto.subtitulo.strip():
            elementos.append(Paragraph(self._escapar(dto.subtitulo), self._estilos["SigquaMetaReporte"]))
        elementos.append(
            Paragraph(
                self._escapar(f"Abonado: {dto.abonado_nombre} | DNI: {dto.abonado_dni}"),
                self._estilos["SigquaMetaReporte"],
            )
        )
        elementos.append(
            Paragraph(self._escapar(f"Generado: {dto.generado_en}"), self._estilos["SigquaMetaReporte"])
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
        elementos.append(Paragraph(self._escapar(dto.observacion), self._estilos["SigquaMetaReporte"]))
        elementos.extend(
            self._construir_bloque_firma(
                dto.firma_habilitada,
                dto.firma_texto_linea,
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
                        self._estilos["SigquaTextoTicketNegrita"],
                    ),
                    Paragraph(self._escapar(casa.estado_servicio), self._estilos["SigquaTextoTicketNegrita"]),
                ],
                [
                    Paragraph(self._escapar(casa.direccion_casa), self._estilos["SigquaTextoTicket"]),
                    Paragraph(
                        self._escapar(
                            f"Meses vencidos: {casa.meses_vencidos} | Días en mora: {casa.dias_en_mora} | "
                            f"Prioridad: {casa.prioridad} | Más antiguo: {casa.vencimiento_mas_antiguo}"
                        ),
                        self._estilos["SigquaTextoTicket"],
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
        elementos.append(
            Paragraph(
                self._escapar(
                    f"Etapa de aviso: {casa.estado_aviso_cobro} | "
                    f"Ultimo aviso: {casa.fecha_ultimo_aviso or 'Sin registro'}"
                ),
                self._estilos["SigquaMetaReporte"],
            )
        )
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
                Paragraph(self._escapar(etiqueta), self._estilos["SigquaTextoTicketNegrita"]),
                Paragraph(self._escapar(valor), self._estilos["SigquaTextoTicket"]),
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
        texto_linea: str,
    ) -> list[object]:
        if not habilitada:
            return []
        elementos: list[object] = [Spacer(1, 10 * mm)]
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
        texto_firma = texto_linea.strip() or "Firma autorizada"
        elementos.append(Paragraph(self._escapar(texto_firma), self._estilos["SigquaFirmaReporte"]))
        return elementos

    def _crear_tabla_totales(self, filas: tuple[tuple[str, str], ...]) -> Table:
        data = [
            [
                Paragraph(self._escapar(etiqueta), self._estilos["SigquaTextoTicketNegrita"]),
                Paragraph(self._escapar(valor), self._estilos["SigquaTextoTicketNegrita"]),
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

    def _crear_tabla_reporte(self, dto: DTOReporteTabular) -> Table:
        columnas_derecha = self._columnas_alineadas_derecha(dto.codigo_reporte)
        cabecera = [
            Paragraph(self._escapar(columna), self._estilos["SigquaCabeceraTablaReporte"])
            for columna in dto.columnas
        ]
        filas: list[list[object]] = []
        for fila in dto.filas:
            filas.append(
                [
                    Paragraph(
                        self._escapar(valor),
                        self._estilos[
                            "SigquaCeldaReporteDerecha"
                            if indice in columnas_derecha
                            else "SigquaCeldaReporte"
                        ],
                    )
                    for indice, valor in enumerate(fila)
                ]
            )
        if not filas:
            filas = [
                [
                    Paragraph(
                        "Sin registros para los filtros aplicados.",
                        self._estilos["SigquaCeldaReporte"],
                    ),
                    *([""] * max(0, len(dto.columnas) - 1)),
                ]
            ]
        tabla = Table(
            [cabecera, *filas],
            colWidths=self._anchos_columnas_reporte(dto),
            repeatRows=1,
            hAlign="LEFT",
        )
        estilos: list[tuple[object, ...]] = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F1F1F")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#B7B7B7")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]
        for fila in range(2, len(filas) + 1, 2):
            estilos.append(("BACKGROUND", (0, fila), (-1, fila), colors.HexColor("#F3F3F3")))
        for columna in columnas_derecha:
            estilos.append(("ALIGN", (columna, 1), (columna, -1), "RIGHT"))
        if not dto.filas and len(dto.columnas) > 1:
            estilos.append(("SPAN", (0, 1), (-1, 1)))
            estilos.append(("ALIGN", (0, 1), (-1, 1), "CENTER"))
        tabla.setStyle(TableStyle(estilos))
        return tabla

    def _crear_resumen_reporte(self, resumen: tuple[tuple[str, str], ...]) -> Table:
        filas = resumen or (("Registros", "0"),)
        data = [
            [
                Paragraph(
                    self._escapar(etiqueta.upper()),
                    self._estilos["SigquaEtiquetaTotalReporte"],
                ),
                Paragraph(self._escapar(valor), self._estilos["SigquaValorTotalReporte"]),
            ]
            for etiqueta, valor in filas
        ]
        tabla = Table(data, colWidths=[72 * mm, 40 * mm], hAlign="RIGHT")
        tabla.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#202020")),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
                    ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#202020")),
                    ("LINEBELOW", (0, 0), (-1, -2), 0.35, colors.HexColor("#666666")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        return tabla

    def _anchos_columnas_reporte(self, dto: DTOReporteTabular) -> list[float]:
        proporciones = {
            "deuda_abonados_estado": (0.14, 0.24, 0.19, 0.07, 0.11, 0.13, 0.12),
            "servicio_casas": (0.09, 0.23, 0.14, 0.15, 0.13, 0.12, 0.14),
            "ingresos_mensuales_diarios": (0.20, 0.32, 0.16, 0.32),
            "historial_abonado_casa": (0.14, 0.25, 0.09, 0.12, 0.14, 0.12, 0.14),
        }.get(dto.codigo_reporte)
        total_columnas = max(1, len(dto.columnas))
        if not proporciones or len(proporciones) != total_columnas:
            proporciones = tuple(1 / total_columnas for _ in range(total_columnas))
        ancho_pagina = landscape(letter)[0] if dto.orientacion.upper() == "HORIZONTAL" else letter[0]
        ancho_disponible = ancho_pagina - 28 * mm
        return [ancho_disponible * proporcion for proporcion in proporciones]

    @staticmethod
    def _columnas_alineadas_derecha(codigo_reporte: str) -> set[int]:
        return {
            "deuda_abonados_estado": {3, 4, 5},
            "servicio_casas": set(),
            "ingresos_mensuales_diarios": {2, 3},
            "historial_abonado_casa": {5},
        }.get(codigo_reporte, set())

    @staticmethod
    def _separar_fecha_hora(generado_en: str) -> tuple[str, str]:
        partes = generado_en.strip().split(maxsplit=1)
        if len(partes) == 2:
            return partes[0], partes[1]
        return generado_en, ""

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
        canvas.setAuthor("SIGQUA")
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
