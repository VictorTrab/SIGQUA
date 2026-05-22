from __future__ import annotations

import sys
import unittest
from pathlib import Path


RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
RUTA_SRC = RAIZ_PROYECTO / "src"

if str(RUTA_SRC) not in sys.path:
    sys.path.insert(0, str(RUTA_SRC))

from comun.utilidades.moneda import formatear_monto_desde_centavos, parsear_monto_a_centavos  # noqa: E402


class TestUtilidadesMoneda(unittest.TestCase):
    def test_parsear_monto_a_centavos_acepta_enteros_y_decimales(self) -> None:
        self.assertEqual(parsear_monto_a_centavos("350"), 35000)
        self.assertEqual(parsear_monto_a_centavos("350.5"), 35050)
        self.assertEqual(parsear_monto_a_centavos("350.50"), 35050)

    def test_parsear_monto_a_centavos_rechaza_vacio_e_invalido(self) -> None:
        self.assertIsNone(parsear_monto_a_centavos(""))
        self.assertIsNone(parsear_monto_a_centavos("abc"))
        self.assertIsNone(parsear_monto_a_centavos("-5"))

    def test_formatear_monto_desde_centavos_normaliza_a_dos_decimales(self) -> None:
        self.assertEqual(formatear_monto_desde_centavos(35000), "350.00")
        self.assertEqual(formatear_monto_desde_centavos(35050), "350.50")
        self.assertEqual(formatear_monto_desde_centavos(0), "0.00")


if __name__ == "__main__":
    unittest.main()
