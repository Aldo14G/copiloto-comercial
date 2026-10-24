import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from copiloto.quote import cotizar  # noqa: E402


class TestCotizar(unittest.TestCase):
    def test_copilot_con_licencia_calcula_al_centavo(self):
        r = cotizar([{"sku": "SIM-M365-02", "cantidad": 30}, {"sku": "SIM-M365-05", "cantidad": 10}])
        self.assertEqual(r["bloqueos"], [])
        self.assertEqual(r["totales"]["mensual"], 30 * 245 + 10 * 590)
        self.assertAlmostEqual(r["totales"]["mensual_iva"], 13250 * 1.16, places=2)

    def test_copilot_sin_licencia_bloquea(self):
        r = cotizar([{"sku": "SIM-M365-05", "cantidad": 10}])
        self.assertTrue(any("requiere alguno de" in b for b in r["bloqueos"]))
        self.assertTrue(r["incompleto"])

    def test_licencia_existente_satisface_dependencia(self):
        r = cotizar([{"sku": "SIM-M365-05", "cantidad": 10}], existentes=["SIM-M365-03"])
        self.assertEqual(r["bloqueos"], [])

    def test_sku_inventado_se_descarta(self):
        r = cotizar([{"sku": "SIM-XX-99", "cantidad": 1}])
        self.assertIn("SKU inexistente", r["bloqueos"][0])
        self.assertEqual(r["lineas"], [])

    def test_paquete_y_plazo_respetan_tope_10(self):
        r = cotizar([{"sku": "SIM-IA-04", "cantidad": 1}, {"sku": "SIM-IA-01", "cantidad": 1}], plazo=36)
        ia01 = next(l for l in r["lineas"] if l["sku"] == "SIM-IA-01")
        self.assertAlmostEqual(ia01["desc_pct"], 0.10)
        self.assertAlmostEqual(ia01["desc_pendiente_pct"], 0.08)
        self.assertTrue(r["requiere_autorizacion"])
        self.assertEqual(ia01["mensual_neto"], 8500 * 0.9)

    def test_conversaciones_adicionales(self):
        r = cotizar([{"sku": "SIM-IA-01", "cantidad": 1}], conversaciones_mes=5000)
        self.assertEqual(r["lineas"][0]["mensual_lista"], 8500 + 3000 * 4)

    def test_soporte_nube_minimo_y_porcentaje(self):
        r = cotizar([{"sku": "SIM-AWS-01"}, {"sku": "SIM-AWS-03"}], consumo={"AWS": 200000})
        sop = next(l for l in r["lineas"] if l["sku"] == "SIM-AWS-03")
        self.assertEqual(sop["mensual_lista"], 20000)
        r2 = cotizar([{"sku": "SIM-AWS-01"}, {"sku": "SIM-AWS-03"}])
        self.assertTrue(r2["incompleto"])

    def test_a_medida_escala(self):
        r = cotizar([{"sku": "SIM-OCI-04", "cantidad": 1}])
        self.assertIn("ESC-01", r["escalamientos"])

    def test_mas_de_300_usuarios_bloquea_y_escala(self):
        r = cotizar([{"sku": "SIM-M365-03", "cantidad": 400}])
        self.assertIn("ESC-02", r["escalamientos"])
        self.assertTrue(r["bloqueos"])

    def test_cantidad_faltante(self):
        r = cotizar([{"sku": "SIM-BK-01", "cantidad": None}])
        self.assertTrue(r["incompleto"])


if __name__ == "__main__":
    unittest.main()
