"""Dos contenidos por caso/revisión; Markdown, PDF y Word comparten los mismos bloques."""
from datetime import date

from . import catalog, ficha
from .documents import Documento, Texto, Tabla, markdown, pdf, word


def _m(v):
    return f"${v:,.2f}"


def _propuesta(f, q):
    if not q["puede_generar_borrador"]:
        return [Texto("No enviar: falta confirmar la solución vigente o completar los datos del importe."),
                Texto("Pendientes antes de generar el borrador", 1),
                *[Texto(b) for b in q["bloqueos"]],
                *[Texto(p["pregunta"]) for p in f["preguntas_pendientes"]]]
    bloques = [Texto("Plantilla de demostración para revisión del vendedor. No constituye una oferta oficial de Alestra."),
               Texto("Lo que entendimos", 1), Texto(f["resumen_necesidad"])]
    bloques += [Texto(f"{h['clave'].replace('_', ' ')}: {h['valor']} — «{h.get('cita', '')}»") for h in f["hechos"] if h.get("verificado")]
    bloques += [Texto(f"Solución propuesta · plazo {q['plazo']} meses", 1),
                Tabla(("Componente", "Cantidad / unidad", "Mensual neto", "Cargo único"), [
                    (f"{l['sku']}\n{l['nombre']}", f"{l['cantidad'] if l['cantidad'] is not None else 'Según consumo'}\n{l['unidad']}",
                     _m(l["mensual_neto"]), _m(l["unico"])) for l in q["lineas"]])]
    t, etiqueta = q["totales"], "Subtotal parcial" if q["parcial"] else "Total"
    bloques += [Texto(f"{etiqueta} mensual: {_m(t['mensual'])} + IVA = {_m(t['mensual_iva'])}"),
                Texto(f"{etiqueta} cargos únicos: {_m(t['unico'])} + IVA = {_m(t['unico_iva'])}"),
                Texto("MXN. Vigencia: 30 días naturales. Cargos únicos pagaderos en 3 mensualidades."),
                Texto("Justificación y condiciones", 1)]
    incluidos = {l["sku"] for l in q["lineas"]}
    bloques += [Texto(f"{c['sku']}: {c['justificacion']}") for c in f["candidatos"] if c.get("justificacion") and c["sku"] in incluidos]
    bloques += [Texto(f"{l['nombre']}: {'; '.join(l['notas'])}") for l in q["lineas"] if l["notas"]]
    bloques += [Texto(a) for a in q["avisos"]]
    pendientes = q["pendiente_diseno"] + [{"nombre": p["nombre"], "motivo": "Solución a la medida"} for p in q["a_medida"]]
    if pendientes or q["escalamientos"]:
        bloques += [Texto("Alcance en diseño con arquitectura; no incluido en el importe", 1)]
        bloques += [Texto(f"{p['nombre']}: {p['motivo']}") for p in pendientes]
        bloques += [Texto(f"{k}: {v}") for k, v in q["escalamientos"].items()]
    bloques += [Texto("Pendientes antes de enviar", 1)]
    bloques += [Texto(p["pregunta"]) for p in f["preguntas_pendientes"]] or [Texto("Revisar alcance y condiciones con el vendedor.")]
    return bloques + [Texto("Siguiente paso", 1), Texto(f["guion_vendedor"])]


def _expediente(f, q, seleccion):
    bloques = [Texto(f"{f['industria']} · {f['empleados']} empleados · tipo de caso: {f['tipo_caso']}"),
               Texto("Necesidad", 1), Texto(f["resumen_necesidad"]), Texto("Hechos y fuentes", 1),
               Tabla(("Dato / valor", "Cita del cliente", "Validación"), [
                   (f"{h.get('clave')}: {h.get('valor')}", h.get("cita", ""),
                    "Cita presente; interpretación por revisar" if h.get("verificado") else
                    h.get("motivo_no_verificado") or "Sin verificar") for h in f["hechos"]])]
    if f["servicios_existentes"]:
        bloques += [Texto("Servicios existentes", 1)]
        bloques += [Texto(f"{s['sku']}: «{s.get('cita', '')}» ({'cita presente' if s.get('verificado') else 'sin verificar'})")
                    for s in f["servicios_existentes"]]
    reglas = {r["id"]: r["cuando_entra_un_arquitecto"] for r in catalog.load()["reglas_escalamiento"]}
    bloques += [Texto("Motivos de escalamiento", 1)]
    bloques += [Texto(f"{k} ({reglas.get(k, '')}): {v}") for k, v in q["escalamientos"].items()] or [Texto("Ninguno confirmado.")]
    bloques += [Texto(f"Posible {e['id']}: {e.get('evidencia', '')}") for e in f["escalamientos"] if e.get("estado") != "confirmado"]
    pendientes = {p["sku"] for p in q["pendiente_diseno"]}
    filas = []
    for s in seleccion:
        p = catalog.producto(s["sku"])
        estado = ("A la medida" if p["tipo"] == "a la medida" else "Sujeto a diseño" if s["sku"] in pendientes
                  else "Pendiente" if q["incompleto"] else "Calculable")
        filas.append((f"{s['sku']}\n{p['nombre']}", str(s.get("cantidad") or "Por definir"), estado,
                      p["cuando_entra_arquitecto"] or "—"))
    bloques += [Texto("Solución evaluada", 1), Tabla(("Componente", "Cantidad", "Estado", "Arquitectura si"), filas),
                Texto("Pendientes y contradicciones", 1)]
    bloques += [Texto(p["pregunta"]) for p in f["preguntas_pendientes"]]
    bloques += [Texto(f"Contradicción: {c}") for c in f["contradicciones"]]
    bloques += [Texto(f"Bloqueo: {b}") for b in q["bloqueos"]]
    return bloques + [Texto("Conversación capturada", 1), *[Texto(f"[{t['rol']}] {t['texto']}") for t in f["transcript"]]]


def documento(f, q, tipo):
    if tipo not in {"propuesta", "expediente"}:
        raise ValueError("Tipo de documento desconocido.")
    seleccion = f["confirmacion"]["seleccion"] if q["fuente"] == "confirmada" else f["candidatos"]
    if (q.get("case_id"), q.get("revision"), q.get("huella"), q.get("catalogo")) != (
            f["case_id"], f["revision"], ficha._huella(f, seleccion), catalog.load()["_sha256"]):
        raise ValueError("La cotización está desactualizada o pertenece a otro caso; vuelve a calcularla.")
    meta = (f"Caso `{f['case_id']}` · revisión {f['revision']} · catálogo `{q['catalogo']}` · "
            f"confirmación: {q['confirmacion']} · {date.today():%d/%m/%Y} · DATOS SIMULADOS")
    titulo = ("Propuesta comercial (BORRADOR)" if tipo == "propuesta" else "Expediente interno") + f" · {f['empresa']}"
    bloques = _propuesta(f, q) if tipo == "propuesta" else _expediente(f, q, seleccion)
    alt = f.get("alternativa")
    if alt:
        bloques += [Texto("Alternativa a considerar", 1), Texto(f"{', '.join(alt['skus'])}: {alt.get('resumen', '')}"),
                    Texto(f"Beneficios: {alt.get('beneficios', '')}"), Texto(f"Límites: {alt.get('limites', '')}"),
                    Texto(f"Cuándo conviene: {alt.get('cuando_conviene', '')}")]
    return Documento(titulo, meta, bloques)


def propuesta_md(f, q):
    return markdown(documento(f, q, "propuesta"))


def expediente_md(f, q):
    return markdown(documento(f, q, "expediente"))


def archivos(f, q):
    salida = {}
    for tipo in (["propuesta", "expediente"] if q["puede_generar_borrador"] else ["expediente"]):
        doc = documento(f, q, tipo)
        nombre = f"{f['case_id']}-r{f['revision']}-{tipo}"
        salida[f"{nombre}.pdf"] = pdf(doc)
        salida[f"{nombre}.docx"] = word(doc)
    return salida
