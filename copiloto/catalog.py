"""Catálogo simulado: única fuente de verdad para SKUs, precios y reglas."""
import hashlib
import json
from functools import lru_cache
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
CATALOG_PATH = DATA / "catalogo.json"


def load():
    stat = CATALOG_PATH.stat()
    return _load(CATALOG_PATH, stat.st_mtime_ns, stat.st_size)


@lru_cache(maxsize=1)
def _load(path, mtime_ns, size):
    raw = path.read_bytes()
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
    # Esquema una sola vez: conserva SLA, plazos y recomendaciones sin repetir claves por SKU.
    campos = list(cat["productos"][0])
    out.append("\n## Productos: cada fila sigue este esquema JSON\n" + json.dumps(campos, ensure_ascii=False))
    out.extend(json.dumps([p[k] for k in campos], ensure_ascii=False, separators=(",", ":"))
               for p in cat["productos"])
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
