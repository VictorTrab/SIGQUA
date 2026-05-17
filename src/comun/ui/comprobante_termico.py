"""Renderer canónico del recibo térmico para vista previa e impresión."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QSizeF, Qt
from PySide6.QtGui import (
    QFont,
    QPageLayout,
    QPageSize,
    QTextBlockFormat,
    QTextCharFormat,
    QTextCursor,
    QTextDocument,
    QTextFrameFormat,
    QTextLength,
    QTextTableFormat,
)
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtCore import QMarginsF


ANCHO_PAPEL_RECIBO_MM = 80.0
MARGEN_RECIBO_MM = 3.0
ANCHO_UTIL_RECIBO_MM = 72.0
ALTO_MINIMO_RECIBO_MM = 120.0
ALTO_MAXIMO_RECIBO_MM = 600.0


def mm_a_puntos(valor_mm: float) -> float:
    return valor_mm * 72.0 / 25.4


def puntos_a_mm(valor_pt: float) -> float:
    return valor_pt * 25.4 / 72.0


@dataclass(slots=True)
class ConfiguracionDocumentoRecibo:
    """Configuración textual del recibo térmico."""

    lineas_encabezado: tuple[str, ...]
    titulo_documento: str
    subtitulo_documento: str = ""
    texto_legal_superior: str = ""
    texto_pie: str = ""
    texto_legal_inferior: str = ""
    etiqueta_copia: str = ""
    firma_habilitada: bool = False
    firma_nombre: str = ""
    firma_cargo: str = ""
    firma_identificador: str = ""
    firma_texto_apoyo: str = ""


@dataclass(slots=True)
class DatosDocumentoRecibo:
    """Especificación plana reutilizable por preview e impresión."""

    numero_comprobante: str
    configuracion: ConfiguracionDocumentoRecibo
    bloque_comprobante: tuple[tuple[str, str], ...]
    bloque_servicio: tuple[tuple[str, str], ...]
    bloque_operativo: tuple[tuple[str, str], ...]
    detalles: tuple[str, ...]
    total_pagado: str
    saldo_posterior: str


def crear_documento_recibo_termico(datos: DatosDocumentoRecibo) -> QTextDocument:
    """Construye el documento canónico del recibo en formato térmico."""

    documento = QTextDocument()
    documento.setDocumentMargin(mm_a_puntos(1.2))
    documento.setDefaultFont(QFont("Courier New", 10))
    documento.setTextWidth(mm_a_puntos(ANCHO_UTIL_RECIBO_MM))

    cursor = QTextCursor(documento)
    _insertar_encabezado(cursor, datos)
    _insertar_bloque_campos(cursor, datos.bloque_comprobante)
    _insertar_bloque_campos(cursor, datos.bloque_servicio)
    _insertar_bloque_campos(cursor, datos.bloque_operativo)
    _insertar_detalles(cursor, datos.detalles)
    _insertar_totales(cursor, datos.total_pagado, datos.saldo_posterior)
    _insertar_texto_centrado(cursor, datos.configuracion.texto_pie, 10, False, 2.5)
    _insertar_texto_centrado(cursor, datos.configuracion.texto_legal_inferior, 8.8, False, 1.8)
    _insertar_texto_centrado(cursor, datos.configuracion.etiqueta_copia, 10, True, 1.5, Qt.AlignmentFlag.AlignRight)
    _insertar_firma(cursor, datos.configuracion)

    documento.adjustSize()
    return documento


def crear_impresora_recibo_termico(alto_mm: float | None = None) -> QPrinter:
    """Crea una impresora Qt preparada para tickets térmicos."""

    impresora = QPrinter(QPrinter.PrinterMode.HighResolution)
    configurar_impresora_recibo_termico(impresora, alto_mm=alto_mm)
    return impresora


def configurar_impresora_recibo_termico(
    impresora: QPrinter,
    documento: QTextDocument | None = None,
    alto_mm: float | None = None,
) -> float:
    """Ajusta el tamaño térmico del `QPrinter` y devuelve el alto aplicado."""

    alto_calculado = alto_mm if alto_mm is not None else _resolver_alto_recibo_mm(documento)
    pagina = QPageSize(
        QSizeF(ANCHO_PAPEL_RECIBO_MM, alto_calculado),
        QPageSize.Unit.Millimeter,
        "Recibo80mm",
    )
    impresora.setPageSize(pagina)
    impresora.setFullPage(False)
    impresora.setPageMargins(
        QMarginsF(MARGEN_RECIBO_MM, MARGEN_RECIBO_MM, MARGEN_RECIBO_MM, MARGEN_RECIBO_MM),
        QPageLayout.Unit.Millimeter,
    )
    return alto_calculado


def preparar_documento_para_printer(documento: QTextDocument, impresora: QPrinter) -> QTextDocument:
    """Clona y adapta el documento al área imprimible real de la impresora."""

    documento_impresion = documento.clone()
    configurar_impresora_recibo_termico(impresora, documento=documento_impresion)
    recta = impresora.pageRect(QPrinter.Unit.Point)
    documento_impresion.setPageSize(QSizeF(recta.width(), documento_impresion.size().height()))
    documento_impresion.adjustSize()
    return documento_impresion


def _resolver_alto_recibo_mm(documento: QTextDocument | None) -> float:
    if documento is None:
        return 220.0
    documento.adjustSize()
    alto_mm = puntos_a_mm(documento.size().height()) + (MARGEN_RECIBO_MM * 2.0) + 4.0
    return max(ALTO_MINIMO_RECIBO_MM, min(ALTO_MAXIMO_RECIBO_MM, alto_mm))


def _insertar_encabezado(cursor: QTextCursor, datos: DatosDocumentoRecibo) -> None:
    for linea in datos.configuracion.lineas_encabezado:
        _insertar_texto_centrado(cursor, linea, 9.6, False, 0.4)
    _insertar_texto_centrado(cursor, datos.configuracion.titulo_documento, 13, True, 1.3)
    _insertar_texto_centrado(cursor, datos.configuracion.subtitulo_documento, 9, False, 0.8)
    _insertar_texto_centrado(cursor, datos.numero_comprobante, 13, True, 1.4)
    _insertar_separador(cursor)


def _insertar_bloque_campos(cursor: QTextCursor, filas: tuple[tuple[str, str], ...]) -> None:
    if not filas:
        return
    formato = QTextTableFormat()
    formato.setBorder(0)
    formato.setCellSpacing(0)
    formato.setCellPadding(0)
    formato.setWidth(QTextLength(QTextLength.Type.PercentageLength, 100))
    formato.setColumnWidthConstraints(
        (
            QTextLength(QTextLength.Type.PercentageLength, 35),
            QTextLength(QTextLength.Type.PercentageLength, 65),
        )
    )
    tabla = cursor.insertTable(len(filas), 2, formato)
    for indice, (etiqueta, valor) in enumerate(filas):
        _escribir_celda(tabla, indice, 0, etiqueta, negrita=True, alineacion=Qt.AlignmentFlag.AlignLeft)
        _escribir_celda(tabla, indice, 1, valor, negrita=False, alineacion=Qt.AlignmentFlag.AlignRight)
    cursor.movePosition(QTextCursor.MoveOperation.End)
    _insertar_separador(cursor)


def _insertar_detalles(cursor: QTextCursor, detalles: tuple[str, ...]) -> None:
    items = detalles or ("Sin detalle registrado.",)
    _insertar_texto_multilinea(cursor, items, 10, False, alineacion=Qt.AlignmentFlag.AlignLeft)
    _insertar_separador(cursor)


def _insertar_totales(cursor: QTextCursor, total_pagado: str, saldo_posterior: str) -> None:
    filas = (
        ("Total pagado", total_pagado),
        ("Saldo posterior", saldo_posterior),
    )
    formato = QTextTableFormat()
    formato.setBorder(0)
    formato.setCellSpacing(0)
    formato.setCellPadding(0)
    formato.setWidth(QTextLength(QTextLength.Type.PercentageLength, 100))
    formato.setColumnWidthConstraints(
        (
            QTextLength(QTextLength.Type.PercentageLength, 45),
            QTextLength(QTextLength.Type.PercentageLength, 55),
        )
    )
    tabla = cursor.insertTable(len(filas), 2, formato)
    for indice, (etiqueta, valor) in enumerate(filas):
        _escribir_celda(tabla, indice, 0, etiqueta, negrita=True, alineacion=Qt.AlignmentFlag.AlignLeft)
        _escribir_celda(tabla, indice, 1, valor, negrita=True, alineacion=Qt.AlignmentFlag.AlignRight)
    cursor.movePosition(QTextCursor.MoveOperation.End)
    _insertar_separador(cursor)


def _insertar_texto_multilinea(
    cursor: QTextCursor,
    lineas: tuple[str, ...],
    tamano: float,
    negrita: bool,
    *,
    alineacion: Qt.AlignmentFlag,
) -> None:
    for linea in lineas:
        _insertar_bloque(cursor, linea, tamano, negrita, 0.6, alineacion)


def _insertar_texto_centrado(
    cursor: QTextCursor,
    texto: str,
    tamano: float,
    negrita: bool,
    margen_inferior: float,
    alineacion: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignCenter,
) -> None:
    if not texto.strip():
        return
    for linea in texto.splitlines():
        _insertar_bloque(cursor, linea, tamano, negrita, margen_inferior, alineacion)


def _insertar_bloque(
    cursor: QTextCursor,
    texto: str,
    tamano: float,
    negrita: bool,
    margen_inferior: float,
    alineacion: Qt.AlignmentFlag,
) -> None:
    formato_bloque = QTextBlockFormat()
    formato_bloque.setAlignment(alineacion)
    formato_bloque.setBottomMargin(margen_inferior)
    cursor.insertBlock(formato_bloque)
    formato_texto = QTextCharFormat()
    formato_texto.setFontPointSize(tamano)
    formato_texto.setFontWeight(QFont.Weight.Bold if negrita else QFont.Weight.Normal)
    cursor.insertText(texto, formato_texto)


def _insertar_separador(cursor: QTextCursor) -> None:
    formato_frame = QTextFrameFormat()
    formato_frame.setBorder(0)
    formato_frame.setMargin(0)
    formato_frame.setPadding(0)
    formato_frame.setWidth(QTextLength(QTextLength.Type.PercentageLength, 100))
    frame = cursor.insertFrame(formato_frame)
    subcursor = QTextCursor(frame.firstCursorPosition())
    formato_bloque = QTextBlockFormat()
    formato_bloque.setAlignment(Qt.AlignmentFlag.AlignCenter)
    formato_bloque.setBottomMargin(1.2)
    formato_bloque.setTopMargin(1.0)
    subcursor.insertBlock(formato_bloque)
    formato_texto = QTextCharFormat()
    formato_texto.setFontPointSize(8)
    subcursor.insertText("─" * 32, formato_texto)
    cursor.movePosition(QTextCursor.MoveOperation.End)


def _insertar_firma(cursor: QTextCursor, configuracion: ConfiguracionDocumentoRecibo) -> None:
    if not configuracion.firma_habilitada:
        return
    _insertar_bloque(cursor, "______________________________", 9, False, 0.8, Qt.AlignmentFlag.AlignCenter)
    _insertar_texto_centrado(cursor, configuracion.firma_nombre, 9, True, 0.4)
    _insertar_texto_centrado(cursor, configuracion.firma_cargo, 8.5, False, 0.4)
    if configuracion.firma_identificador.strip():
        _insertar_texto_centrado(
            cursor,
            f"Identificador: {configuracion.firma_identificador}",
            8.3,
            False,
            0.4,
        )
    _insertar_texto_centrado(cursor, configuracion.firma_texto_apoyo, 8.2, False, 0.8)


def _escribir_celda(tabla, fila: int, columna: int, texto: str, *, negrita: bool, alineacion: Qt.AlignmentFlag) -> None:  # type: ignore[no-untyped-def]
    celda = tabla.cellAt(fila, columna)
    cursor = celda.firstCursorPosition()
    formato_bloque = QTextBlockFormat()
    formato_bloque.setAlignment(alineacion)
    formato_bloque.setBottomMargin(0.7)
    cursor.setBlockFormat(formato_bloque)
    formato_texto = QTextCharFormat()
    formato_texto.setFontPointSize(10)
    formato_texto.setFontWeight(QFont.Weight.Bold if negrita else QFont.Weight.Normal)
    cursor.insertText(texto, formato_texto)
