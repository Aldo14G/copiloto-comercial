"""Borrador de propuesta en Markdown (plantilla de demo; el catálogo no incluye plantillas oficiales)."""
from datetime import date

from . import catalog


def _m(v):
    return f"${v:,.2f}"


def propuesta_md(f, q):
    t = q["totales"]
    out = [f"# Propuesta económica (BORRADOR) · {f['empresa']}",
           f"*Fecha: {date.today():%d/%m/%Y} · Vigencia: 30 días naturales · Catálogo `{q['catalogo']}` · DATOS SIMULADOS*", "",
           "## Lo que entendimos", f['resumen_necesidad'], ""]
    out += [f"- {h['valor']} — “{h.get('cita', '')}”" for h in f["hechos"] if h.get("verificado")]
    out += ["", f"## Solución propuesta (plazo {q['plazo']} meses)", "",
            "| SKU | Producto | Cant. | Mensual neto | Cargo único |", "|---|---|---|---|---|"]
    for l in q["lineas"]:
        out.append(f"| {l['sku']} | {l['nombre']} | {l['cantidad'] or '-'} | {_m(l['mensual_neto'])} | {_m(l['unico'])} |")
    out += ["", f"**Mensualidad:** {_m(t['mensual'])} + IVA = {_m(t['mensual_iva'])}",
            f"**Cargos únicos:** {_m(t['unico'])} + IVA = {_m(t['unico_iva'])} (pueden pagarse en 3 mensualidades)", ""]
    for c in f["candidatos"]:
        out.append(f"- **{catalog.producto(c['sku'])['nombre']}:** {c.get('justificacion', '')}")
    if q["escalamientos"]:
        out += ["", "## Componentes en diseño con arquitecto de soluciones"]
        out += [f"- {k}: {v}" for k, v in q["escalamientos"].items()]
    if q["incompleto"] or q["bloqueos"]:
        out += ["", "## Pendientes antes de enviar"] + [f"- {b}" for b in q["bloqueos"]]
        out += [f"- {p['pregunta']}" for p in f["preguntas_pendientes"]]
    return "\n".join(out)
