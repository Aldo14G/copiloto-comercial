"""Evalúa el primer turno de los 10 casos: SKUs inventados, hechos sin cita, escalamientos explícitos detectados.
Uso: python -B eval/run_cases.py  → escribe eval/resultados.json"""
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from copiloto import catalog, claude_engine, ficha as F  # noqa: E402

# Disparadores explícitos en el primer mensaje (revisión humana, ver CONTEXTO.md)
ESPERADOS = {"CASO-03": {"ESC-04"}, "CASO-06": {"ESC-08"}, "CASO-08": {"ESC-06"}, "CASO-10": {"ESC-04"}}


def correr(c):
    f = F.nueva(c["id"])
    f["case_id"] = f"EVAL-{c['id']}"
    salida, meta = claude_engine.ask(claude_engine._prompt(f, c["mensaje_inicial"]))
    crudos = {x.get("sku") for x in salida.get("candidatos", [])}
    salida = claude_engine.validate(salida, c["mensaje_inicial"])
    f.update({k: salida.get(k, f[k]) for k in ("hechos", "candidatos", "escalamientos", "servicios_existentes",
                                                 "preguntas_pendientes")})
    q = F.cotizacion(f)
    skus_en_cotizacion = [l["sku"] for l in q["lineas"]] + [x["sku"] for x in q["pendiente_diseno"]]
    inventados_en_cotizacion = [s for s in skus_en_cotizacion if not catalog.producto(s)]
    detectados = set(q["escalamientos"])  # código + confirmados por Claude con evidencia
    posibles = sorted({e["id"] for e in f["escalamientos"] if e.get("estado") != "confirmado"} - detectados)
    esperados = ESPERADOS.get(c["id"], set())
    return {"caso": c["id"], "etiqueta": c["tipo_de_caso"], "tipo_claude": salida.get("tipo_caso"),
            "skus_inventados": len([s for s in crudos if not catalog.producto(s)]),
            "skus_inventados_en_cotizacion": len(inventados_en_cotizacion),
            "alternativa": (salida.get("alternativa") or {}).get("skus"),
            "motivos_no_verificado": [h["motivo_no_verificado"] for h in f["hechos"] if not h["verificado"]],
            "hechos": len(f["hechos"]), "hechos_sin_cita": sum(not h["verificado"] for h in f["hechos"]),
            "preguntas": len(f["preguntas_pendientes"]), "candidatos": [x["sku"] for x in f["candidatos"]],
            "escalamientos": sorted(detectados), "posibles": posibles, "esperados": sorted(esperados),
            "esperados_detectados": esperados <= detectados, "estados": q["estados"], **meta}


if __name__ == "__main__":
    with ThreadPoolExecutor(5) as ex:
        res = list(ex.map(correr, catalog.load()["casos_clientes"]))
    resumen = {
        "casos": len(res),
        "alcance": "Solo el primer mensaje de cada caso; no evalúa conversaciones completas ni exactitud de propuestas finales.",
        "skus_inventados_que_llegaron_al_cotizador": sum(r["skus_inventados_en_cotizacion"] for r in res),
        "skus_inventados_por_claude_filtrados": sum(r["skus_inventados"] for r in res),
        "hechos_sin_cita_filtrados": sum(r["hechos_sin_cita"] for r in res),
        "hechos_totales": sum(r["hechos"] for r in res),
        "escalamientos_explicitos_detectados": f"{sum(r['esperados_detectados'] for r in res if r['esperados'])}/{len(ESPERADOS)}",
        "casos_con_escalamiento": sum(bool(r["escalamientos"]) for r in res),
        "casos_con_alternativa": sum(bool(r["alternativa"]) for r in res),
        "latencia_media_s": round(sum(r["segundos"] for r in res) / len(res), 1),
    }
    out = {"resumen": resumen, "casos": res}
    (ROOT / "eval" / "resultados.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(resumen, ensure_ascii=False, indent=2))
    for r in res:
        print(r["caso"], r["etiqueta"], "->", r["tipo_claude"], r["escalamientos"], "posibles", r["posibles"], "esperado", r["esperados"], r["segundos"], "s")
