"""Utilidades compartidas para captura monetaria en SICAP."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


_PRECISION_MONEDA = Decimal("0.01")
_CIEN = Decimal("100")


def parsear_monto_a_centavos(texto: str) -> int | None:
    """Convierte un monto visible a centavos.

    Acepta entradas como ``350``, ``350.5`` o ``350.50``. Devuelve ``None``
    cuando la entrada esta vacia o no es un monto valido.
    """

    limpio = (texto or "").strip().replace(",", "")
    if not limpio:
        return None
    try:
        valor = Decimal(limpio)
    except InvalidOperation:
        return None
    if valor < 0:
        return None
    valor_normalizado = valor.quantize(_PRECISION_MONEDA, rounding=ROUND_HALF_UP)
    return int((valor_normalizado * _CIEN).to_integral_value(rounding=ROUND_HALF_UP))


def formatear_monto_desde_centavos(centavos: int | None) -> str:
    """Formatea centavos a texto visible con dos decimales."""

    if centavos is None:
        return ""
    valor = (Decimal(int(centavos)) / _CIEN).quantize(_PRECISION_MONEDA, rounding=ROUND_HALF_UP)
    return f"{valor:.2f}"
