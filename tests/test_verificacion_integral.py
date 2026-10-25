"""Verificación integral (Bloque 6). Complementa, sin duplicar, a test_core/test_quote:
allí ya se prueban tratamientos por SKU, los 7 paquetes con descuento y dependencias,
topes de descuento, consumo y soporte. Aquí: SKU sin cantidad, SKU sin precio de lista,
persistencia de las 10 reglas y recorrido de los 10 casos con proveedor simulado."""
import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from copiloto import catalog, claude_engine as C, ficha as F
from copiloto.export import expediente_md
from copiloto.quote import cotizar

RAIZ = Path(__file__).parents[1]
CAT = json.loads((RAIZ / "data/catalogo.json").read_text(encoding="utf-8"))
SIN_CANTIDAD = {"SIM-AWS-01", "SIM-AZ-01", "SIM-OCI-01", "SIM-AWS-03", "SIM-AZ-05", "SIM-OCI-05"}
TIPO_ESPERADO = {"estándar": "estándar", "mixto": "mixto", "a la medida": "arquitectura"}

# Recorrido por caso: lo que el vendedor confirma con datos de prueba identificados.
# hechos: datos verificados del cliente; esc: escalamiento confirmado con evidencia.
RECORRIDOS = {
    "CASO-01": {"sel": [("SIM-M365-02", 25)], "hechos": {}},
    "CASO-02": {"sel": [("SIM-DC-01", 1), ("SIM-DC-08", 1), ("SIM-DC-07", 2)], "hechos": {"rto_horas": "2"}},
    "CASO-03": {"sel": [("SIM-AWS-01", 1), ("SIM-AWS-03", 1), ("SIM-AWS-06", 1)], "hechos": {"consumo_aws_mxn": "80000"}},
    "CASO-04": {"sel": [("SIM-AZ-06", 1)], "hechos": {}},
    "CASO-05": {"sel": [("SIM-IA-01", 1)], "hechos": {"conversaciones_mes": "1000"}},
    "CASO-06": {"sel": [("SIM-OCI-02", 1), ("SIM-OCI-05", 1)], "hechos": {"oracle_tb": "6"}},
    "CASO-07": {"sel": [("SIM-BK-01", 2)], "hechos": {}},
    "CASO-08": {"sel": [("SIM-AZ-06", 1)], "hechos": {}},
    "CASO-09": {"sel": [("SIM-M365-02", 30), ("SIM-M365-05", 30)], "hechos": {}},
    "CASO-10": {"sel": [("SIM-DC-09", 1)], "hechos": {}, "esc": ("ESC-04", "Expediente clínico con datos de salud")},
}


def clasificar(q):
    if q["lineas"] and "requiere_arquitecto" not in q["estados"] and "borrador_calculable" in q["estados"]:
        return "estándar"
    if q["lineas"] and "requiere_arquitecto" in q["estados"]:
        return "mixto"
    if not q["lineas"] and "requiere_arquitecto" in q["estados"]:
        return "arquitectura"
    return "incompleto"


def recorrer(case_id):
    """Primer mensaje con proveedor simulado (sin cantidades) → confirmación del vendedor → cotización."""
    r = RECORRIDOS[case_id]
    f = F.nueva(case_id)
    caso = catalog.caso(case_id)
    salida = {"hechos": [], "candidatos": [{"sku": s, "cantidad": None} for s, _ in r["sel"]]}
    with patch.object(C, "ask", return_value=(salida, {})) as ask:
        F.procesar_mensaje(f, caso["mensaje_inicial"])
        assert ask.call_count == 1
    previa = F.cotizacion(f)
    f["hechos"] = [{"clave": k, "valor": v, "verificado": True} for k, v in r["hechos"].items()]
    if "esc" in r:
        f["escalamientos"] = [{"id": r["esc"][0], "estado": "confirmado", "evidencia": r["esc"][1]}]
    F.confirmar(f, [{"sku": s, "cantidad": n} for s, n in r["sel"]])
    q = F.cotizacion(f, True)
    return f, previa, q


class _Disco(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.p = patch.object(F, "FICHAS", Path(self.tmp.name))
        self.p.start()

    def tearDown(self):
        self.p.stop()
        self.tmp.cleanup()


class TestCadaSKU(unittest.TestCase):
    def test_los_45_skus_sin_cantidad_no_producen_importe(self):
        self.assertEqual(len(CAT["productos"]), 45)
        for p in CAT["productos"]:
            with self.subTest(sku=p["sku"]):
                self.assertIsNotNone(catalog.producto(p["sku"]))
                q = cotizar([{"sku": p["sku"], "cantidad": None}])
                # Consumo y soporte de nube no se cobran por cantidad: muestran mínimo o 0 y quedan incompletos.
                for linea in q["lineas"]:
                    self.assertIn(linea["sku"], SIN_CANTIDAD)
                self.assertTrue(q["incompleto"] or q["a_medida"], "nunca es un total final")

    def test_sku_sin_precio_de_lista_nunca_tiene_importe_inventado(self):
        precios = {p["sku"]: p for p in CAT["productos"]}
        for p in CAT["productos"]:
            if p["tipo"] != "a la medida":
                continue
            with self.subTest(sku=p["sku"]):
                q = cotizar([{"sku": p["sku"], "cantidad": 1}])
                self.assertEqual(q["lineas"], [])
                self.assertIn(p["sku"], {a["sku"] for a in q["a_medida"]})
                self.assertIn("ESC-01", q["escalamientos"])
                self.assertEqual(q["totales"]["mensual"], 0)
        self.assertIsNone(precios["SIM-DC-09"]["precio_mensual_mxn"])

    def test_iva_y_contrato_al_centavo_con_decimal(self):
        q = cotizar([{"sku": "SIM-M365-02", "cantidad": 25}], plazo=12)
        mensual = Decimal("245") * 25
        self.assertEqual(Decimal(str(q["totales"]["mensual"])), mensual)
        self.assertEqual(Decimal(str(q["totales"]["mensual_iva"])), (mensual * Decimal("1.16")).quantize(Decimal("0.01")))
        self.assertEqual(Decimal(str(q["totales"]["contrato"])), mensual * 12)


class TestReglas(_Disco):
    def test_las_10_reglas_persisten_aunque_se_elija_producto_estandar(self):
        for regla in CAT["reglas_escalamiento"]:
            with self.subTest(regla=regla["id"]):
                f = F.nueva()
                f["escalamientos"] = [{"id": regla["id"], "estado": "confirmado", "evidencia": "prueba"}]
                F.confirmar(f, [{"sku": "SIM-M365-02", "cantidad": 10}])
                q = F.cotizacion(f, True)
                self.assertIn(regla["id"], q["escalamientos"])
                self.assertIn("requiere_arquitecto", q["estados"])
                self.assertTrue(q["parcial"], "un total con arquitecto pendiente no se presenta como final")

    def test_caso10_datos_clinicos_con_producto_estandar_conserva_escalamiento(self):
        f = F.nueva("CASO-10")
        f["escalamientos"] = [{"id": "ESC-04", "estado": "confirmado", "evidencia": "datos de salud"}]
        F.confirmar(f, [{"sku": "SIM-DC-06", "cantidad": 1}])
        q = F.cotizacion(f, True)
        self.assertIn("ESC-04", q["escalamientos"])
        self.assertIn("ESC-04", expediente_md(f, q))


class TestDiezCasos(_Disco):
    def test_los_10_casos_llegan_al_cierre_esperado(self):
        self.assertEqual(sorted(RECORRIDOS), sorted(c["id"] for c in CAT["casos_clientes"]))
        for caso in CAT["casos_clientes"]:
            with self.subTest(caso=caso["id"]):
                f, previa, q = recorrer(caso["id"])
                self.assertNotIn("borrador_calculable", previa["estados"], "sin cantidades confirmadas no hay total")
                self.assertEqual(q["fuente"], "confirmada")
                self.assertEqual(clasificar(q), TIPO_ESPERADO[caso["tipo_de_caso"]])
                self.assertEqual(q["catalogo"], f["catalogo"])
                self.assertTrue(f["transcript"])


if __name__ == "__main__":
    unittest.main()
