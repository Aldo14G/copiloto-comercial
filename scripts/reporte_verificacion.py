"""Genera VERIFICACION.md: corre la suite y recorre los 10 casos con proveedor simulado (sin Claude)."""
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "tests"))

from copiloto import catalog, ficha as F  # noqa: E402
from test_verificacion_integral import CAT, RECORRIDOS, TIPO_ESPERADO, clasificar, recorrer  # noqa: E402


def suite():
    res = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(
        unittest.defaultTestLoader.discover(str(RAIZ / "tests")))
    return res.testsRun, len(res.failures) + len(res.errors)


def casos():
    filas = []
    with tempfile.TemporaryDirectory() as tmp, patch.object(F, "FICHAS", Path(tmp)):
        for c in CAT["casos_clientes"]:
            _, _, q = recorrer(c["id"])
            real, esperado = clasificar(q), TIPO_ESPERADO[c["tipo_de_caso"]]
            t = q["totales"]
            monto = f"{t['mensual']:,.0f} MXN/mes" + (" parcial" if q["parcial"] else "") if q["lineas"] else "sin total: arquitecto"
            esc = ", ".join(sorted(q["escalamientos"])) or "—"
            marca = "✅" if real == esperado else "❌"
            filas.append(f"- {marca} **{c['id']}** {c['empresa']}: esperado {esperado}, obtenido {real}; {monto}; escalamientos {esc}.")
    return filas


def main():
    import os
    os.chdir(RAIZ)
    total, fallas = suite()
    cat = catalog.load()
    filas = casos()
    ok = sum(f.startswith("- ✅") for f in filas)
    md = f"""# Verificación

Generado con `python scripts/reporte_verificacion.py`. Sin llamadas a Claude: proveedor simulado.

## Verificado
- Pruebas automáticas: **{total - fallas}/{total}** pasan (`python -m unittest discover tests`).
- Catálogo `{cat['_sha256'][:12]}`: {len(CAT['productos'])} SKUs, {len(CAT['paquetes'])} paquetes, {len(CAT['reglas_escalamiento'])} reglas de escalamiento, {len(CAT['casos_clientes'])} casos.
- Cada SKU: sin cantidad verificada no genera total final; los de tipo «a la medida» nunca reciben precio y van al expediente (ESC-01).
- Paquetes, descuentos por plazo, tope de 10 %, consumo y soporte de nube: `tests/test_core.py` y `tests/test_quote.py`.
- Las 10 reglas: un escalamiento confirmado persiste aunque se elija un producto estándar (incluye CASO-10, datos clínicos).
- Casos de origen llevados al cierre: **{ok}/{len(filas)}** con el tipo esperado.

## Casos (datos de prueba identificados en `tests/test_verificacion_integral.py`)
{chr(10).join(filas)}

## Hallazgos
- Consumo y soporte de nube (AWS/Azure/OCI) aparecen en la vista previa con su mínimo o en 0 antes de conocer el consumo; el resultado queda marcado incompleto. Es intencional, no un total final.
- La política de combinación de descuentos es una decisión de la demo, no una política confirmada.

## No medido aún
- Impacto comercial (tiempo por propuesta, tasa de cierre): sin medición; es hipótesis.
- Latencia y calidad de Claude en vivo: estas pruebas usan proveedor simulado.
- Uso con vendedores reales: no se ha probado.
"""
    (RAIZ / "VERIFICACION.md").write_text(md, encoding="utf-8")
    print(md)
    return 1 if fallas or ok != len(filas) else 0


if __name__ == "__main__":
    sys.exit(main())
