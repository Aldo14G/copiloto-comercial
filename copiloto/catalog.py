"""Catálogo simulado: única fuente de verdad para SKUs, precios y reglas."""
import hashlib
import json
from functools import lru_cache
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
CATALOG_PATH = DATA / "catalogo.json"


@lru_cache(maxsize=1)
def load():
    raw = CATALOG_PATH.read_bytes()
    cat = json.loads(raw)
    cat["_sha256"] = hashlib.sha256(raw).hexdigest()[:12]
    cat["_por_sku"] = {p["sku"]: p for p in cat["productos"]}
    return cat


def producto(sku):
    return load()["_por_sku"].get(sku)


def caso(case_id):
    return next((c for c in load()["casos_clientes"] if c["id"] == case_id), None)


def texto_para_claude():
    """Versión compacta del catálogo para el prompt (sin inventar campos)."""
    cat = load()
    out = ["## Familias"]
    for f in cat["familias"]:
        out.append(f"- {f['id']} {f['nombre']}: {f['problemas_que_resuelve']}")
    out.append("\n## Productos (sku | nombre | tipo | unidad | mensual | único | min-max | requiere alguno de | señal | preguntas | arquitecto si)")
    for p in cat["productos"]:
        out.append(" | ".join(str(x) for x in [
            p["sku"], p["nombre"], p["tipo"], p["unidad_cobro"],
            p["precio_mensual_mxn"], p["cargo_unico_mxn"],
            f"{p['cantidad_minima']}-{p['cantidad_maxima']}",
            ",".join(p["requiere_alguno_de"]) or "-",
            p["senal_del_cliente"], " ".join(p["preguntas_clave"]),
            p["cuando_entra_arquitecto"] or "-",
        ]) + f" | desc: {p['descripcion']}")
    out.append("\n## Paquetes")
    for k in cat["paquetes"]:
        out.append(f"- {k['id']} {k['nombre']} ({k['descuento_pct']}%): {','.join(k['productos'])}. Para: {k['para_quien']}")
    out.append("\n## Reglas de escalamiento a arquitecto")
    for r in cat["reglas_escalamiento"]:
        out.append(f"- {r['id']}: {r['cuando_entra_un_arquitecto']}")
    out.append("\n## Condiciones comerciales")
    for c in cat["condiciones_comerciales"]:
        out.append(f"- {c['concepto']}: {c['regla']}")
    return "\n".join(out)
