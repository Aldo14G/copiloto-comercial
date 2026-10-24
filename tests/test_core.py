"""Cobertura del catálogo completo (D09), confirmación del vendedor (D06), cierre parcial (D08)
y validación de hechos. No llaman a Claude."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from copiloto import catalog, claude_engine, ficha as F  # noqa: E402
from copiloto.export import expediente_md, propuesta_md  # noqa: E402
from copiloto.quote import CONSUMO_FAMILIA, SOPORTE_FAMILIA, cotizar  # noqa: E402

CONSUMO = {"AWS": 100000, "AZ": 100000, "OCI": 100000}


def _qty(p):
    return p["cantidad_minima"] or 1


class TestCoberturaCatalogo(unittest.TestCase):
    def test_los_45_skus_tienen_tratamiento_correcto(self):
        productos = catalog.load()["productos"]
        self.assertEqual(len(productos), 45)
        for p in productos:
            with self.subTest(sku=p["sku"]):
                q = _qty(p)
                r = cotizar([{"sku": p["sku"], "cantidad": q}], existentes=p["requiere_alguno_de"],
                            consumo=CONSUMO, conversaciones_mes=2000)
                if p["tipo"] == "a la medida":
                    self.assertIn("ESC-01", r["escalamientos"])
                    self.assertEqual(r["lineas"], [])
                    self.assertTrue(r["parcial"])
                    continue
                self.assertEqual(r["bloqueos"], [], r["bloqueos"])
                self.assertEqual(len(r["lineas"]), 1)
                l = r["lineas"][0]
                if p["sku"] in CONSUMO_FAMILIA:
                    esperado_m, esperado_u = 100000, 0
                elif p["sku"] in SOPORTE_FAMILIA:
                    esperado_m, esperado_u = 12000, 0  # max(10% de 100,000, 12,000)
                else:
                    por_unidad = p["unidad_cobro"].startswith("cargo único por") or p["unidad_cobro"] == "por mes"
                    esperado_m = (p["precio_mensual_mxn"] or 0) * q
                    esperado_u = (p["cargo_unico_mxn"] or 0) * (q if por_unidad else 1)
                self.assertAlmostEqual(l["mensual_lista"], esperado_m, places=2)
                self.assertAlmostEqual(l["unico"], esperado_u, places=2)

    def test_los_7_paquetes_aplican_descuento_y_dependencias(self):
        for k in catalog.load()["paquetes"]:
            with self.subTest(paquete=k["id"]):
                sel = [{"sku": s, "cantidad": _qty(catalog.producto(s))} for s in k["productos"]]
                r = cotizar(sel, consumo=CONSUMO)
                self.assertIn(k["id"], r["paquetes"])
                for l in r["lineas"]:
                    self.assertAlmostEqual(l["desc_pct"], k["descuento_pct"] / 100)
                deps_faltantes = any(
                    catalog.producto(s)["requiere_alguno_de"]
                    and not set(catalog.producto(s)["requiere_alguno_de"]) & set(k["productos"])
                    for s in k["productos"])
                # Hallazgo del catálogo: PAQ-05 y PAQ-06 incluyen el soporte sin el consumo que requiere
                self.assertEqual(bool(r["bloqueos"]), deps_faltantes, r["bloqueos"])
                self.assertEqual(deps_faltantes, k["id"] in {"PAQ-05", "PAQ-06"})

    def test_paquete_con_servicio_existente_se_desbloquea(self):
        sel = [{"sku": s, "cantidad": 1} for s in ["SIM-AWS-02", "SIM-AWS-05", "SIM-AWS-03"]]
        r = cotizar(sel, existentes=["SIM-AWS-01"], consumo=CONSUMO)
        self.assertEqual(r["bloqueos"], [])

    def test_las_10_reglas_existen(self):
        self.assertEqual([r["id"] for r in catalog.load()["reglas_escalamiento"]],
                         [f"ESC-{i:02d}" for i in range(1, 11)])


class TestCierreParcial(unittest.TestCase):
    def test_componente_sujeto_a_diseno_no_suma(self):
        r = cotizar([{"sku": "SIM-M365-03", "cantidad": 20},
                     {"sku": "SIM-DC-07", "cantidad": 4, "depende_de_diseno": True}])
        self.assertEqual([l["sku"] for l in r["lineas"]], ["SIM-M365-03"])
        self.assertEqual(r["pendiente_diseno"][0]["sku"], "SIM-DC-07")
        self.assertTrue(r["parcial"])
        self.assertEqual(r["totales"]["mensual"], 20 * 425)

    def test_dependiente_de_componente_en_diseno_tambien_queda_pendiente(self):
        r = cotizar([{"sku": "SIM-OCI-02", "cantidad": 1, "depende_de_diseno": True},
                     {"sku": "SIM-OCI-05", "cantidad": 1}], consumo=CONSUMO)
        self.assertEqual(r["lineas"], [])
        self.assertEqual({p["sku"] for p in r["pendiente_diseno"]}, {"SIM-OCI-02", "SIM-OCI-05"})

    def test_un_a_la_medida_no_satisface_dependencias_ajenas(self):
        # SIM-AWS-05 requiere SIM-AWS-02; incluir el a la medida SIM-AWS-06 no lo desbloquea
        r = cotizar([{"sku": "SIM-AWS-06", "cantidad": 1}, {"sku": "SIM-AWS-05", "cantidad": 2}])
        self.assertTrue(any("SIM-AWS-05 requiere" in b for b in r["bloqueos"]))
        self.assertIn("ESC-01", r["escalamientos"])

    def test_caso_estandar_no_es_parcial(self):
        r = cotizar([{"sku": "SIM-BK-01", "cantidad": 3}])
        self.assertFalse(r["parcial"])


class TestValidacionHechos(unittest.TestCase):
    T = claude_engine._norm("Somos 1,200 personas y tenemos Business Standard para los 30")

    def m(self, **h):
        return claude_engine._motivo_hecho(h, self.T)

    def test_cita_valida(self):
        self.assertIsNone(self.m(clave="usuarios_m365", valor="30", cita="Business Standard para los 30"))

    def test_numero_con_comas(self):
        self.assertIsNone(self.m(clave="empleados", valor="1200", cita="Somos 1,200 personas"))

    def test_cita_no_contiene_el_numero(self):
        self.assertIn("no contiene", self.m(clave="usuarios_m365", valor="1200", cita="Business Standard para los 30"))

    def test_cita_inexistente(self):
        self.assertIn("no encontrada", self.m(clave="x", valor="5", cita="tenemos 5 servidores"))

    def test_numero_en_palabras(self):
        t = claude_engine._norm("Nuestro ERP corre en dos servidores en un cuarto de la planta")
        self.assertIsNone(claude_engine._motivo_hecho({"clave": "servidores", "valor": "2",
                                                       "cita": "corre en dos servidores"}, t))

    def test_cita_casi_literal_se_acepta_y_parafrasis_no(self):
        t = claude_engine._norm("Tenemos 45 sucursales y recibimos cientos de WhatsApps al día preguntando horarios")
        self.assertTrue(claude_engine._cita_en_texto("tenemos 45 sucursales y recibimos cientos de WhatsApp al día", t))
        self.assertFalse(claude_engine._cita_en_texto("el cliente opera cuarenta y cinco restaurantes", t))

    def test_inferencia_no_se_usa(self):
        self.assertEqual(self.m(clave="x", valor="30", cita="para los 30", origen="inferencia"), "inferencia de Claude")

    def test_validate_descarta_alternativa_inventada(self):
        s = claude_engine.validate({"alternativa": {"skus": ["SIM-XX-01"], "resumen": "x"}, "candidatos": []}, "hola")
        self.assertIsNone(s["alternativa"])


class TestConfirmacion(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self._orig = F.FICHAS
        F.FICHAS = Path(self.tmp.name)
        f = F.nueva("CASO-09")
        f["transcript"] = [{"rol": "cliente", "texto": "Tenemos Business Standard para los 30", "ts": ""}]
        f["hechos"] = [{"clave": "usuarios_m365", "valor": "30", "cita": "para los 30", "verificado": True}]
        f["servicios_existentes"] = [{"sku": "SIM-M365-02", "cita": "Business Standard", "verificado": True}]
        f["candidatos"] = [{"sku": "SIM-M365-05", "cantidad": 12, "justificacion": "IA"}]
        self.f = f

    def tearDown(self):
        F.FICHAS = self._orig
        self.tmp.cleanup()

    def test_sin_confirmar_no_genera_borrador(self):
        q = F.cotizacion(self.f, usar_confirmacion=True)
        self.assertEqual(q["confirmacion"], "sin_confirmar")
        self.assertFalse(q["puede_generar_borrador"])
        self.assertIn("No enviar", propuesta_md(self.f, q))

    def test_confirmar_con_cantidades_del_vendedor(self):
        F.confirmar(self.f, [{"sku": "SIM-M365-05", "cantidad": 10}])
        q = F.cotizacion(self.f, usar_confirmacion=True)
        self.assertEqual(q["confirmacion"], "vigente")
        self.assertTrue(q["puede_generar_borrador"])
        self.assertEqual(q["totales"]["mensual"], 5900)
        self.assertNotIn("No enviar", propuesta_md(self.f, q))
        self.assertTrue(F.ruta("CASO-09").exists())

    def test_cambio_de_hechos_desactualiza_confirmacion(self):
        F.confirmar(self.f, [{"sku": "SIM-M365-05", "cantidad": 10}])
        self.f["hechos"][0]["valor"] = "40"
        self.assertEqual(F.estado_confirmacion(self.f), "desactualizada")
        self.assertFalse(F.cotizacion(self.f, usar_confirmacion=True)["puede_generar_borrador"])

    def test_cambio_de_plazo_desactualiza_confirmacion(self):
        F.confirmar(self.f, [{"sku": "SIM-M365-05", "cantidad": 10}])
        self.f["plazo"] = 36
        self.assertEqual(F.estado_confirmacion(self.f), "desactualizada")

    def test_confirmar_sku_inexistente_falla(self):
        with self.assertRaises(ValueError):
            F.confirmar(self.f, [{"sku": "SIM-ZZ-01", "cantidad": 1}])

    def test_entregables_vinculados_al_mismo_caso_y_revision(self):
        self.f["revision"] = 3
        F.confirmar(self.f, [{"sku": "SIM-M365-05", "cantidad": 10}])
        q = F.cotizacion(self.f, usar_confirmacion=True)
        prop, exp = propuesta_md(self.f, q), expediente_md(self.f, q)
        for doc in (prop, exp):
            self.assertIn("Caso `CASO-09` · revisión 3", doc)
            self.assertIn(f"catálogo `{catalog.load()['_sha256']}`", doc)
            self.assertIn("confirmación: vigente", doc)

    def test_ficha_antigua_se_carga_con_campos_nuevos(self):
        F.FICHAS.mkdir(exist_ok=True)
        F.ruta("VIEJA").write_text('{"case_id": "VIEJA", "empresa": "X", "transcript": []}', encoding="utf-8")
        f = F.cargar("VIEJA")
        self.assertIsNone(f["confirmacion"])
        self.assertEqual(f["revision"], 0)


if __name__ == "__main__":
    unittest.main()
