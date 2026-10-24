"""Regresiones del cierre de backend. No consumen Claude ni modifican casos reales."""
import copy
import json
import math
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from copiloto import catalog, claude_engine as C, ficha as F
from copiloto.export import expediente_md, propuesta_md
from copiloto.quote import cotizar


class TestEntradas(unittest.TestCase):
    def test_cantidades_invalidas_no_producen_importes(self):
        for qty in (-1, 0, True, 1.5, float("nan"), float("inf"), "abc"):
            with self.subTest(qty=qty):
                q = cotizar([{"sku": "SIM-M365-02", "cantidad": qty}])
                self.assertTrue(q["bloqueos"])
                self.assertEqual(q["totales"]["mensual"], 0)
                self.assertTrue(all(math.isfinite(v) for v in q["totales"].values()))

    def test_tb_permite_fracciones_y_sku_duplicado_no_duplica_importe(self):
        q = cotizar([{"sku": "SIM-BK-01", "cantidad": 1.5}])
        self.assertEqual(q["bloqueos"], [])
        self.assertEqual(q["totales"]["mensual"], 2775)
        q = cotizar([{"sku": "SIM-M365-02", "cantidad": 10}] * 2)
        self.assertTrue(q["bloqueos"])
        self.assertEqual(q["totales"]["mensual"], 2450)

    def test_consumo_invalido_no_se_convierte_en_credito(self):
        for consumo in (-1, True, float("nan"), float("inf")):
            q = cotizar([{"sku": "SIM-AWS-01"}], consumo={"AWS": consumo})
            self.assertTrue(q["incompleto"])
            self.assertEqual(q["totales"]["mensual"], 0)

    def test_citas_no_aceptan_otras_cifras_o_palabras_omitidas(self):
        texto = C._norm("Tenemos 300 usuarios para correo y no queremos una migración")
        for cita in ("Tenemos 30 usuarios para correo", "Tenemos 300 usuarios correo",
                     "correo y queremos una migración"):
            self.assertFalse(C._cita_en_texto(cita, texto))
        self.assertFalse(C._cita_en_texto("Consumo 100 pesos", C._norm("Consumo -100 pesos")))

    def test_salida_malformada_se_rechaza(self):
        for salida in ([], {"hechos": None}, {"candidatos": [None]}, {"candidatos": [{"sku": []}]},
                       {"contradicciones": "hay conflicto"}, {"escalamientos": [{"id": "ESC-04", "evidencia": []}]}):
            with self.subTest(salida=salida), self.assertRaises(ValueError):
                C.validate(salida, "hola")

    def test_cantidad_inferida_y_escalamiento_sin_evidencia_se_retienen_como_pendientes(self):
        salida = C.validate({"hechos": [{"clave": "empleados", "valor": 30, "cita": "Somos 30"}],
                             "candidatos": [{"sku": "SIM-M365-02", "cantidad": 30, "hecho_cantidad": "usuarios_m365"}],
                             "escalamientos": [{"id": "ESC-04", "estado": "confirmado", "evidencia": "CNBV"}]},
                            "Somos 30")
        self.assertIsNone(salida["candidatos"][0]["cantidad"])
        self.assertEqual(salida["escalamientos"][0]["estado"], "posible")

    def test_umbrales_por_producto_no_se_suman_como_estandar(self):
        for sku, qty in (("SIM-DC-02", 4), ("SIM-M365-05", 501), ("SIM-BK-01", 101)):
            with self.subTest(sku=sku):
                q = cotizar([{"sku": sku, "cantidad": qty}])
                self.assertEqual(q["lineas"], [])
                self.assertEqual(q["pendiente_diseno"][0]["sku"], sku)
                self.assertTrue(q["parcial"])


class TestFichaBackend(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.storage = patch.object(F, "FICHAS", Path(self.tmp.name))
        self.storage.start()
        self.f = F.nueva("PRUEBA")
        self.f["candidatos"] = [{"sku": "SIM-M365-02", "cantidad": 10}]

    def tearDown(self):
        self.storage.stop()
        self.tmp.cleanup()

    def test_fallo_de_claude_validacion_o_disco_no_modifica_ficha(self):
        for salida, fallo in ((None, "claude"), ({"hechos": None}, "validacion"), ({}, "disco")):
            with self.subTest(fallo=fallo):
                antes = copy.deepcopy(self.f)
                with patch.object(C, "ask", side_effect=RuntimeError("sin conexión") if fallo == "claude" else None,
                                  return_value=(salida, {})), patch.object(F, "guardar", side_effect=OSError("sin espacio")):
                    with self.assertRaises((ValueError, OSError, RuntimeError)):
                        F.procesar_mensaje(self.f, "Tenemos 10 usuarios")
                self.assertEqual(self.f, antes)

    def test_fallo_de_reemplazo_conserva_archivo_y_limpia_temporal(self):
        F.guardar(self.f)
        antes = F.ruta("PRUEBA").read_bytes()
        with patch.object(Path, "replace", side_effect=OSError("archivo ocupado")):
            with self.assertRaises(OSError):
                F.guardar({**self.f, "empresa": "Cambio no guardado"})
        self.assertEqual(F.ruta("PRUEBA").read_bytes(), antes)
        self.assertEqual(list(Path(self.tmp.name).glob("*.tmp")), [])

    def test_conversacion_completa_persistida_y_confirmacion_renovada(self):
        salida = {"hechos": [{"clave": "usuarios_m365", "valor": "10", "cita": "Tenemos diez usuarios"}],
                  "candidatos": [{"sku": "SIM-M365-02", "cantidad": 10, "hecho_cantidad": "usuarios_m365"}]}
        with patch.object(C, "ask", return_value=(salida, {})):
            F.procesar_mensaje(self.f, "Tenemos diez usuarios")
        F.confirmar(self.f, self.f["candidatos"])
        recargada = F.cargar("PRUEBA")
        self.assertEqual(F.estado_confirmacion(recargada), "vigente")
        self.assertTrue(F.cotizacion(recargada, True)["puede_generar_borrador"])
        with patch.object(C, "ask", return_value=(salida, {})):
            F.procesar_mensaje(recargada, "Conservamos los diez usuarios")
        self.assertEqual(F.estado_confirmacion(recargada), "desactualizada")

    def test_importe_incompleto_o_contradiccion_impide_borrador(self):
        for seleccion in ([{"sku": "SIM-AWS-01"}], [{"sku": "SIM-IA-01", "cantidad": 1}]):
            F.confirmar(self.f, seleccion)
            q = F.cotizacion(self.f, True)
            self.assertFalse(q["puede_generar_borrador"])
            self.assertNotIn("borrador_calculable", q["estados"])
            self.assertNotIn("Total mensual", propuesta_md(self.f, q))
        self.f["contradicciones"] = ["Usuarios: 10 o 30; confirmar"]
        F.confirmar(self.f, self.f["candidatos"])
        self.assertFalse(F.cotizacion(self.f, True)["puede_generar_borrador"])

    def test_cantidades_invalidas_no_sobrescriben_confirmacion(self):
        F.confirmar(self.f, self.f["candidatos"])
        antes = copy.deepcopy(self.f)
        for cantidad in (-1, 0, True, float("inf"), None):
            with self.subTest(cantidad=cantidad), self.assertRaises(ValueError):
                F.confirmar(self.f, [{"sku": "SIM-M365-02", "cantidad": cantidad}])
            self.assertEqual(self.f, antes)

    def test_sujeto_a_diseno_no_se_elimina_al_confirmar(self):
        self.f["candidatos"] = [{"sku": "SIM-DC-07", "cantidad": 2, "depende_de_diseno": True}]
        F.confirmar(self.f, [{"sku": "SIM-DC-07", "cantidad": 2}])
        q = F.cotizacion(self.f, True)
        self.assertFalse(q["puede_generar_borrador"])
        self.assertIn("requiere_arquitecto", q["estados"])
        self.assertEqual(q["lineas"], [])

    def test_numeros_en_palabras_activan_umbrales(self):
        self.f["hechos"] = [{"clave": "rto_horas", "valor": "dos", "verificado": True}]
        self.assertEqual(F._hecho_num(self.f, "rto_horas"), 2)
        self.assertIn("ESC-07", F.cotizacion(self.f)["escalamientos"])

    def test_cierre_mixto_separa_oracle_y_dependientes_y_vincula_entregables(self):
        self.f["hechos"] = [{"clave": "oracle_tb", "valor": "6", "verificado": True}]
        seleccion = [{"sku": "SIM-OCI-02", "cantidad": 1}, {"sku": "SIM-OCI-05", "cantidad": 1},
                     {"sku": "SIM-M365-02", "cantidad": 10}]
        F.confirmar(self.f, seleccion)
        q = F.cotizacion(self.f, True)
        self.assertEqual([l["sku"] for l in q["lineas"]], ["SIM-M365-02"])
        self.assertEqual(q["totales"]["mensual"], 2450)
        self.assertEqual({p["sku"] for p in q["pendiente_diseno"]}, {"SIM-OCI-02", "SIM-OCI-05"})
        self.assertIn("ESC-08", q["escalamientos"])
        self.assertTrue(q["puede_generar_borrador"])
        self.assertIn("Subtotal parcial mensual", propuesta_md(self.f, q))
        self.assertIn("ESC-08", expediente_md(self.f, q))

    def test_recuperacion_fuera_del_sla_no_se_cotiza_como_estandar(self):
        self.f["hechos"] = [{"clave": "rto_horas", "valor": "2", "verificado": True}]
        F.confirmar(self.f, [{"sku": "SIM-DC-07", "cantidad": 2}])
        q = F.cotizacion(self.f, True)
        self.assertEqual(q["lineas"], [])
        self.assertFalse(q["puede_generar_borrador"])
        self.assertIn("ESC-07", q["escalamientos"])

    def test_ficha_antigua_revalida_existentes(self):
        self.f["servicios_existentes"] = [{"sku": "SIM-M365-02", "verificado": True, "cita": "licencia inexistente"}]
        F.guardar(self.f)
        self.assertFalse(F.cargar("PRUEBA")["servicios_existentes"][0]["verificado"])

    def test_id_invalido_no_escribe_fuera_del_directorio(self):
        for case_id in ("../escape", "..\\escape", "C:\\escape", "CON", "", None):
            with self.subTest(case_id=case_id), self.assertRaises(ValueError):
                F.ruta(case_id)

    def test_exportacion_no_mezcla_revisiones_ni_selecciones(self):
        F.confirmar(self.f, [{"sku": "SIM-BK-01", "cantidad": 2}])
        previa = F.cotizacion(self.f)
        self.assertIn("Microsoft 365", expediente_md(self.f, previa))
        self.assertNotIn("Backup inmutable", expediente_md(self.f, previa))
        q = F.cotizacion(self.f, True)
        self.f["revision"] += 1
        for exportar in (propuesta_md, expediente_md):
            with self.assertRaises(ValueError):
                exportar(self.f, q)

    def test_catalogo_actualizado_invalida_confirmacion_y_cache(self):
        path = Path(self.tmp.name) / "catalogo.json"
        path.write_bytes(catalog.CATALOG_PATH.read_bytes())
        with patch.object(catalog, "CATALOG_PATH", path):
            F.confirmar(self.f, self.f["candidatos"])
            q = F.cotizacion(self.f, True)
            data = json.loads(path.read_text(encoding="utf-8"))
            data["productos"][0]["precio_mensual_mxn"] += 100
            path.write_text(json.dumps(data), encoding="utf-8")
            self.assertEqual(F.estado_confirmacion(self.f), "desactualizada")
            self.assertNotEqual(q["catalogo"], catalog.load()["_sha256"])
            with self.assertRaises(ValueError):
                propuesta_md(self.f, q)


if __name__ == "__main__":
    unittest.main()
