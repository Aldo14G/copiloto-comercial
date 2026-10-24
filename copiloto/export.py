"""Dos entregables vinculados al mismo caso, revisión y catálogo (D10):
- propuesta_md: borrador comercial para revisión del vendedor (plantilla de demo; no hay plantillas oficiales).
- expediente_md: expediente interno para preventa/arquitectura."""
from datetime import date

from . import catalog


def _m(v):
    return f"${v:,.2f}"


def _encabezado(f, q, tipo):
    c = f.get("confirmacion") or {}
    return [f"*{tipo} · Caso `{f['case_id']}` · revisión {f['revision']} · catálogo `{q['catalogo']}` · "
            f"confirmación: {q['confirmacion']}" + (f" (rev. {c.get('revision')}, {c.get('ts')})" if c else "") +
            f" · {date.today():%d/%m/%Y} · DATOS SIMULADOS*", ""]


def propuesta_md(f, q):
    t = q["totales"]
    out = [f"# Propuesta económica (BORRADOR) · {f['empresa']}"] + _encabezado(f, q, "Propuesta comercial")
    if not q.get("puede_generar_borrador"):
        out += ["> ⚠️ **No enviar:** la solución no está confirmada por el vendedor, la confirmación está "
                "desactualizada o hay bloqueos.", ""]
    out += ["## Lo que entendimos", f["resumen_necesidad"], ""]
    out += [f"- {h['valor']} — “{h.get('cita', '')}”" for h in f["hechos"] if h.get("verificado")]
    out += ["", f"## Solución propuesta (plazo {q['plazo']} meses)", "",
            "| SKU | Producto | Cant. | Unidad | Mensual neto | Cargo único |", "|---|---|---|---|---|---|"]
    for l in q["lineas"]:
        out.append(f"| {l['sku']} | {l['nombre']} | {l['cantidad'] or '-'} | {l['unidad']} | "
                   f"{_m(l['mensual_neto'])} | {_m(l['unico'])} |")
    etiqueta = "Subtotal parcial" if q["parcial"] else "Total"
    out += ["", f"**{etiqueta} mensual:** {_m(t['mensual'])} + IVA = {_m(t['mensual_iva'])}",
            f"**{etiqueta} cargos únicos:** {_m(t['unico'])} + IVA = {_m(t['unico_iva'])} "
            "(pueden pagarse en 3 mensualidades)", "Vigencia: 30 días naturales. Precios en MXN.", ""]
    just = {c["sku"]: c.get("justificacion", "") for c in f["candidatos"]}
    for l in q["lineas"]:
        if just.get(l["sku"]):
            out.append(f"- **{l['nombre']}:** {just[l['sku']]}")
    notas = [f"- {l['nombre']}: {'; '.join(l['notas'])}" for l in q["lineas"] if l["notas"]]
    if notas:
        out += ["", "## Supuestos y condiciones"] + notas + [f"- {a}" for a in q["avisos"]]
    alt = f.get("alternativa")
    if alt:
        out += ["", "## Alternativa a considerar", alt.get("resumen", ""),
                f"- Beneficios: {alt.get('beneficios', '')}", f"- Límites: {alt.get('limites', '')}",
                f"- Cuándo conviene: {alt.get('cuando_conviene', '')}"]
    pend = q["pendiente_diseno"] + [{"nombre": p["nombre"], "motivo": "Solución a la medida"} for p in q["a_medida"]]
    if pend or q["escalamientos"]:
        out += ["", "## Alcance en diseño con arquitecto de soluciones (no incluido en el importe)"]
        out += [f"- {p['nombre']}: {p['motivo']}" for p in pend]
    if q["bloqueos"] or f["preguntas_pendientes"]:
        out += ["", "## Pendientes antes de enviar"] + [f"- {b}" for b in q["bloqueos"]]
        out += [f"- {p['pregunta']}" for p in f["preguntas_pendientes"]]
    out += ["", "## Siguiente paso", f.get("guion_vendedor", "")]
    return "\n".join(out)


def expediente_md(f, q):
    reglas = {r["id"]: r["cuando_entra_un_arquitecto"] for r in catalog.load()["reglas_escalamiento"]}
    out = [f"# Expediente interno · {f['empresa']}"] + _encabezado(f, q, "Expediente preventa/arquitectura")
    out += [f"{f['industria']} · {f['empleados']} empleados · tipo de caso: {f.get('tipo_caso')}", "",
            "## Necesidad", f["resumen_necesidad"], "", "## Hechos",
            "| Dato | Valor | Fuente | Estado |", "|---|---|---|---|"]
    for h in f["hechos"]:
        estado = "verificado" if h.get("verificado") else f"⚠️ {h.get('motivo_no_verificado') or 'no verificado'}"
        out.append(f"| {h.get('clave')} | {h.get('valor')} | “{h.get('cita', '')}” ({h.get('origen', 'cliente')}) | {estado} |")
    if f["servicios_existentes"]:
        out += ["", "## Servicios existentes"]
        out += [f"- {s['sku']} {catalog.producto(s['sku'])['nombre']} — “{s.get('cita', '')}” "
                f"({'verificado' if s.get('verificado') else 'sin verificar'})" for s in f["servicios_existentes"]]
    out += ["", "## Motivos de escalamiento"]
    if q["escalamientos"]:
        out += [f"- **{k}** ({reglas.get(k, '')}): {v}" for k, v in q["escalamientos"].items()]
    else:
        out.append("- Ninguno confirmado.")
    posibles = [e for e in f["escalamientos"] if e.get("estado") != "confirmado" and e["id"] not in q["escalamientos"]]
    out += [f"- Posible {e['id']}: {e.get('evidencia', '')} (confirmar)" for e in posibles]
    out += ["", "## Solución evaluada", "| SKU | Producto | Tipo | Cantidad | Sustento | Estado |", "|---|---|---|---|---|---|"]
    sel = (f.get("confirmacion") or {}).get("seleccion") or f["candidatos"]
    sustento = {c["sku"]: c.get("hecho_cantidad") for c in f["candidatos"]}
    pend = {p["sku"] for p in q["pendiente_diseno"]}
    for s in sel:
        p = catalog.producto(s["sku"])
        est = "a la medida" if p["tipo"] == "a la medida" else ("sujeto a diseño" if s["sku"] in pend else "calculable")
        out.append(f"| {s['sku']} | {p['nombre']} | {p['tipo']} | {s.get('cantidad') or '?'} | "
                   f"{sustento.get(s['sku']) or '-'} | {est} |")
        if p["cuando_entra_arquitecto"]:
            out.append(f"|  | ↳ arquitecto si: {p['cuando_entra_arquitecto']} |  |  |  |  |")
    alt = f.get("alternativa")
    if alt:
        out += ["", "## Alternativa evaluada", f"{', '.join(alt['skus'])}: {alt.get('resumen', '')}",
                f"- Beneficios: {alt.get('beneficios', '')}", f"- Límites: {alt.get('limites', '')}"]
    out += ["", "## Pendientes y contradicciones"]
    out += [f"- {p['pregunta']} ({p.get('motivo', '')})" for p in f["preguntas_pendientes"]]
    out += [f"- Contradicción: {c}" for c in f.get("contradicciones") or []]
    out += [f"- Bloqueo: {b}" for b in q["bloqueos"]]
    out += ["", "## Conversación capturada"]
    out += [f"- [{t['rol']}] {t['texto']}" for t in f["transcript"]]
    return "\n".join(out)
