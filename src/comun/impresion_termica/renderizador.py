"""Renderizador ESC/POS simple para tickets de comprobantes."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from comun.impresion_termica.entidades import ConfiguracionImpresoraTermica


class LineaTicket(Protocol):
    descripcion: str
    monto: str


class TicketEscpos(Protocol):
    lineas_encabezado: tuple[str, ...]
    numero_comprobante: str
    tipo_comprobante: str
    fecha_hora: str
    usuario_cobrador: str
    abonado_nombre: str
    abonado_dni: str
    casa_codigo: str
    barrio_nombre: str
    direccion_casa: str
    metodo_pago: str
    referencia: str
    lineas_detalle: tuple[LineaTicket, ...]
    total_pagado: str
    texto_pie: str
    firma_habilitada: bool
    firma_texto_linea: str


class RenderizadorTicketEscpos:
    """Convierte un ticket plano a bytes ESC/POS imprimibles."""

    ESC = b"\x1b"
    GS = b"\x1d"

    def renderizar(
        self,
        ticket: TicketEscpos,
        configuracion: ConfiguracionImpresoraTermica,
        *,
        tipo_copia: str,
        es_reimpresion: bool = False,
    ) -> bytes:
        ancho = 42 if configuracion.ancho_papel_mm >= 80 else 32
        lineas: list[str] = []
        lineas.extend(self._centrar(linea, ancho) for linea in ticket.lineas_encabezado if linea.strip())
        lineas.append("")
        lineas.append(self._centrar("COMPROBANTE DE PAGO", ancho))
        lineas.append(self._centrar(tipo_copia, ancho))
        if es_reimpresion:
            lineas.append(self._centrar("REIMPRESION", ancho))
        lineas.append(self._separador(ancho))
        lineas.extend(
            self._formatear_campos(
                (
                    ("Numero", ticket.numero_comprobante),
                    ("Tipo", ticket.tipo_comprobante),
                    ("Fecha", ticket.fecha_hora),
                    ("Cobrador", ticket.usuario_cobrador),
                    ("Abonado", ticket.abonado_nombre),
                    ("DNI", ticket.abonado_dni or "No registrado"),
                    ("Casa", ticket.casa_codigo),
                    ("Barrio", ticket.barrio_nombre or "Sin barrio"),
                    ("Direccion", ticket.direccion_casa or "Sin referencia"),
                    ("Metodo", ticket.metodo_pago),
                    ("Referencia", ticket.referencia or "No aplica"),
                ),
                ancho,
            )
        )
        lineas.append(self._separador(ancho))
        lineas.append("Detalle")
        for linea in ticket.lineas_detalle:
            lineas.extend(self._formatear_linea_detalle(linea.descripcion, linea.monto, ancho))
        lineas.append(self._separador(ancho))
        lineas.append(self._formatear_total("TOTAL PAGADO", ticket.total_pagado, ancho))
        if ticket.texto_pie.strip():
            lineas.append("")
            lineas.extend(self._envolver(ticket.texto_pie.strip(), ancho))
        if ticket.firma_habilitada:
            lineas.append("")
            lineas.append("")
            lineas.append("_" * min(28, ancho))
            lineas.append(self._centrar(ticket.firma_texto_linea or "Firma autorizada", ancho))
        lineas.append("")
        lineas.append("")

        contenido = "\n".join(lineas) + "\n"
        datos = bytearray()
        datos.extend(self.ESC + b"@")
        datos.extend(contenido.encode(configuracion.codigo_pagina or "cp850", errors="replace"))
        if configuracion.corte_automatico:
            datos.extend(self.GS + b"V\x00")
        return bytes(datos)

    @staticmethod
    def _centrar(texto: str, ancho: int) -> str:
        return texto.strip()[:ancho].center(ancho)

    @staticmethod
    def _separador(ancho: int) -> str:
        return "-" * ancho

    def _formatear_campos(self, campos: Iterable[tuple[str, str]], ancho: int) -> list[str]:
        lineas: list[str] = []
        for etiqueta, valor in campos:
            prefijo = f"{etiqueta}: "
            disponible = max(8, ancho - len(prefijo))
            partes = self._envolver(str(valor or ""), disponible)
            if not partes:
                partes = [""]
            lineas.append(f"{prefijo}{partes[0]}")
            for extra in partes[1:]:
                lineas.append(f"{' ' * len(prefijo)}{extra}")
        return lineas

    def _formatear_linea_detalle(self, descripcion: str, monto: str, ancho: int) -> list[str]:
        ancho_monto = min(13, max(9, len(monto)))
        ancho_desc = ancho - ancho_monto - 1
        partes = self._envolver(descripcion, ancho_desc)
        if not partes:
            partes = [""]
        lineas = [f"{partes[0]:<{ancho_desc}} {monto:>{ancho_monto}}"]
        for extra in partes[1:]:
            lineas.append(f"{extra:<{ancho_desc}} {'':>{ancho_monto}}")
        return lineas

    @staticmethod
    def _formatear_total(etiqueta: str, total: str, ancho: int) -> str:
        disponible = max(1, ancho - len(etiqueta))
        return f"{etiqueta}{total:>{disponible}}"

    @staticmethod
    def _envolver(texto: str, ancho: int) -> list[str]:
        texto = " ".join(str(texto or "").split())
        if not texto:
            return []
        palabras = texto.split(" ")
        lineas: list[str] = []
        actual = ""
        for palabra in palabras:
            candidato = palabra if not actual else f"{actual} {palabra}"
            if len(candidato) <= ancho:
                actual = candidato
                continue
            if actual:
                lineas.append(actual)
            while len(palabra) > ancho:
                lineas.append(palabra[:ancho])
                palabra = palabra[ancho:]
            actual = palabra
        if actual:
            lineas.append(actual)
        return lineas
