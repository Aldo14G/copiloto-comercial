"""Ficha persistente del cliente: lo que se dijo una vez queda guardado para vendedor y arquitecto.

Flujo de confirmación (D06): Claude propone candidatos; el vendedor confirma solución y cantidades.
La confirmación guarda una huella de los hechos y la selección; si después cambian, la confirmación
queda desactualizada y el borrador económico no se genera hasta confirmar de nuevo."""
import hashlib
import json
import re
from datetime import datetime

from . import catalog, claude_engine
from .catalog import DATA
from .quote import cotizar

FICHAS = DATA / "fichas"
CAMPOS_CLAUDE = ("resumen_necesidad", "hechos", "servicios_existentes", "candidatos", "alternativa",
                 "preguntas_pendientes", "escalamientos", "contradicciones", "guion_vendedor", "tipo_caso",
                 "alertas_validacion")


def _ahora():
    return datetime.now().isoformat(timespec="seconds")


def nueva(case_id=None, empresa="Nuevo cliente", industria="", empleados=""):
    c = catalog.caso(case_id) if case_id else None
    if c:
        empresa, industria, empleados = c["empresa"], c["industria"], c["empleados"]
    return {"case_id": case_id or f"NUEVO-{datetime.now():%H%M%S}", "empresa": empresa, "industria": industria,
            "empleados": empleados, "catalogo": catalog.load()["_sha256"], "creado": _ahora(), "actualizado": _ahora(),
            "revision": 0, "transcript": [], "hechos": [], "servicios_existentes": [], "candidatos": [],
            "alternativa": None, "preguntas_pendientes": [], "escalamientos": [], "contradicciones": [],
            "guion_vendedor": "", "resumen_necesidad": "", "tipo_caso": "por definir", "alertas_validacion": [],
            "metricas": [], "plazo": 12, "confirmacion": None}


def ruta(case_id):
    return FICHAS / f"{case_id}.json"


def cargar(case_id):
    p = ruta(case_id)
    if not p.exists():
        return None
    f = json.loads(p.read_text(encoding="utf-8"))
    base = nueva(f.get("case_id"))
    f = {**base, **f}  # fichas guardadas con versiones anteriores reciben los campos nuevos
    # Revalidar hechos con las reglas vigentes (una ficha antigua pudo verificarse con reglas más laxas)
    texto = claude_engine._norm(" ".join(t["texto"] for t in f["transcript"] if t["rol"] == "cliente"))
    for h in f["hechos"]:
        h["motivo_no_verificado"] = claude_engine._motivo_hecho(h, texto)
        h["verificado"] = h["motivo_no_verificado"] is None
    return f


def guardar(f):
    FICHAS.mkdir(parents=True, exist_ok=True)
    f["actualizado"] = _ahora()
    tmp = ruta(f["case_id"]).with_suffix(".tmp")
    tmp.write_text(json.dumps(f, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(ruta(f["case_id"]))  # escritura atómica: un fallo no deja la ficha a medias


def procesar_mensaje(f, mensaje, rol="cliente"):
    """Analiza un fragmento con Claude y actualiza la ficha. Si Claude falla, la ficha no cambia."""
    mensaje = (mensaje or "").strip()
    if not mensaje:
        raise ValueError("El fragmento está vacío.")
    salida, meta = claude_engine.ask(claude_engine._prompt(f, mensaje, rol))
    f["transcript"].append({"rol": rol, "texto": mensaje, "ts": _ahora()})
    texto = " ".join(t["texto"] for t in f["transcript"] if t["rol"] == "cliente")
    salida = claude_engine.validate(salida, texto)
    for k in CAMPOS_CLAUDE:
        if k in salida:
            f[k] = salida[k]
    f["revision"] += 1
    meta["turno"] = len(f["transcript"])
    meta["revision"] = f["revision"]
    f["metricas"].append(meta)
    guardar(f)
    return f


# ---------- Confirmación del vendedor ----------

def _huella(f, seleccion):
    hechos = sorted((h.get("clave"), str(h.get("valor")), bool(h.get("verificado"))) for h in f["hechos"])
    sel = sorted((s["sku"], s.get("cantidad"), bool(s.get("depende_de_diseno"))) for s in seleccion)
    exist = sorted(s["sku"] for s in f["servicios_existentes"] if s.get("verificado"))
    data = json.dumps([hechos, sel, exist, f.get("plazo", 12), f["catalogo"]], ensure_ascii=False, default=str)
    return hashlib.sha256(data.encode()).hexdigest()[:12]


def confirmar(f, seleccion):
    """El vendedor confirma la solución: [{sku, cantidad, depende_de_diseno?}]. SKUs inexistentes se rechazan."""
    invalidos = [s["sku"] for s in seleccion if not catalog.producto(s["sku"])]
    if invalidos:
        raise ValueError(f"SKUs inexistentes: {', '.join(invalidos)}")
    limpia = [{"sku": s["sku"], "cantidad": s.get("cantidad"), "depende_de_diseno": bool(s.get("depende_de_diseno"))}
              for s in seleccion]
    f["confirmacion"] = {"seleccion": limpia, "revision": f["revision"], "ts": _ahora(),
                         "plazo": f.get("plazo", 12), "huella": _huella(f, limpia)}
    guardar(f)
    return f


def estado_confirmacion(f):
    """sin_confirmar | vigente | desactualizada (cambiaron hechos, existentes, plazo o catálogo)."""
    c = f.get("confirmacion")
    if not c:
        return "sin_confirmar"
    return "vigente" if _huella(f, c["seleccion"]) == c["huella"] else "desactualizada"


# ---------- Cotización ----------

def _hecho_num(f, clave):
    for h in f["hechos"]:
        if h.get("clave") == clave and h.get("verificado"):
            m = re.search(r"\d[\d,]*(?:\.\d+)?", str(h.get("valor")))
            if m:
                try:
                    return float(m.group(0).replace(",", ""))
                except ValueError:
                    return None
    return None


def cotizacion(f, usar_confirmacion=False):
    """Cotiza los candidatos de Claude (vista previa) o la selección confirmada por el vendedor (borrador)."""
    if usar_confirmacion and f.get("confirmacion"):
        seleccion = f["confirmacion"]["seleccion"]
    else:
        seleccion = f["candidatos"]
    consumo = {fam: _hecho_num(f, f"consumo_{k}_mxn") for fam, k in (("AWS", "aws"), ("AZ", "azure"), ("OCI", "oci"))}
    existentes = [s["sku"] for s in f["servicios_existentes"] if s.get("verificado")]
    r = cotizar(seleccion, existentes=existentes, plazo=f.get("plazo", 12),
                consumo={k: v for k, v in consumo.items() if v is not None},
                conversaciones_mes=_hecho_num(f, "conversaciones_mes"))
    # Escalamientos: los que detecta el código + los confirmados por Claude con evidencia
    for e in f["escalamientos"]:
        if e.get("estado") == "confirmado":
            r["escalamientos"].setdefault(e["id"], e.get("evidencia", ""))
    oracle = _hecho_num(f, "oracle_tb")
    if oracle and oracle > 2:
        r["escalamientos"].setdefault("ESC-08", f"Base Oracle de {oracle:g} TB")
    if r["escalamientos"] and not r["parcial"] and r["lineas"]:
        r["parcial"] = True
        r["avisos"].append("Subtotal parcial: el caso requiere arquitecto; el alcance final puede cambiar con su diseño.")
    conf = estado_confirmacion(f)
    estados = []
    if r["incompleto"] or f["preguntas_pendientes"]:
        estados.append("faltan_datos")
    if r["lineas"] and not r["bloqueos"]:
        estados.append("borrador_calculable")
    if r["escalamientos"]:
        estados.append("requiere_arquitecto")
    if r["requiere_autorizacion"]:
        estados.append("requiere_autorizacion")
    r["estados"] = estados
    r["confirmacion"] = conf
    r["fuente"] = "confirmada" if usar_confirmacion and f.get("confirmacion") else "propuesta_claude"
    r["puede_generar_borrador"] = (usar_confirmacion and conf == "vigente" and bool(r["lineas"])
                                   and not r["bloqueos"])
    return r
