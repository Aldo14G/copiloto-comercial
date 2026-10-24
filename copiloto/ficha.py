"""Ficha persistente del cliente: lo que se dijo una vez queda guardado para vendedor y arquitecto.

Flujo de confirmación (D06): Claude propone candidatos; el vendedor confirma solución y cantidades.
La confirmación guarda una huella de los hechos y la selección; si después cambian, la confirmación
queda desactualizada y el borrador económico no se genera hasta confirmar de nuevo."""
import hashlib
import json
import re
from copy import deepcopy
from datetime import datetime
from tempfile import NamedTemporaryFile

from . import catalog, claude_engine
from .catalog import DATA
from .quote import cotizar, validar_cantidad

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
    if case_id is not None:
        ruta(case_id)
    return {"case_id": case_id or f"NUEVO-{datetime.now():%Y%m%d-%H%M%S%f}", "empresa": empresa, "industria": industria,
            "empleados": empleados, "catalogo": catalog.load()["_sha256"], "creado": _ahora(), "actualizado": _ahora(),
            "revision": 0, "transcript": [], "hechos": [], "servicios_existentes": [], "candidatos": [],
            "alternativa": None, "preguntas_pendientes": [], "escalamientos": [], "contradicciones": [],
            "guion_vendedor": "", "resumen_necesidad": "", "tipo_caso": "por definir", "alertas_validacion": [],
            "metricas": [], "plazo": 12, "confirmacion": None}


def ruta(case_id):
    if not isinstance(case_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", case_id) or re.fullmatch(
            r"CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9]", case_id, re.I):
        raise ValueError("Identificador de caso inválido.")
    return FICHAS / f"{case_id}.json"


def cargar(case_id):
    p = ruta(case_id)
    if not p.exists():
        return None
    f = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(f, dict) or f.get("case_id") != case_id:
        raise ValueError("La ficha guardada no corresponde al identificador solicitado.")
    base = nueva(f.get("case_id"))
    f = {**base, **f}  # fichas guardadas con versiones anteriores reciben los campos nuevos
    # Revalidar también servicios existentes: un indicador antiguo no es evidencia.
    texto = "\n".join(t["texto"] for t in f["transcript"] if t["rol"] == "cliente")
    salida = claude_engine.validate({k: f[k] for k in CAMPOS_CLAUDE}, texto)
    f.update(salida)
    return f


def guardar(f):
    destino = ruta(f["case_id"])
    FICHAS.mkdir(parents=True, exist_ok=True)
    datos = {**f, "actualizado": _ahora()}
    tmp = None
    try:
        with NamedTemporaryFile(mode="w", encoding="utf-8", dir=FICHAS, suffix=".tmp", delete=False) as archivo:
            tmp = destino.parent / archivo.name
            archivo.write(json.dumps(datos, ensure_ascii=False, indent=2, allow_nan=False))
        tmp.replace(destino)
        f["actualizado"] = datos["actualizado"]
    finally:
        if tmp is not None:
            tmp.unlink(missing_ok=True)


def _persistir(f, actualizada):
    """Publicar en memoria solo después del reemplazo atómico en disco."""
    guardar(actualizada)
    f.clear()
    f.update(actualizada)
    return f


def procesar_mensaje(f, mensaje, rol="cliente"):
    """Analiza un fragmento con Claude y actualiza la ficha. Si Claude falla, la ficha no cambia."""
    mensaje = (mensaje or "").strip()
    if rol not in {"cliente", "vendedor"}:
        raise ValueError("Rol inválido; usa cliente o vendedor.")
    if not mensaje:
        raise ValueError("El fragmento está vacío.")
    salida, meta = claude_engine.ask(claude_engine._prompt(f, mensaje, rol))
    if not isinstance(salida, dict) or not {"hechos", "candidatos"} <= salida.keys():
        raise ValueError("El análisis está incompleto; se conserva la ficha anterior. Vuelve a intentarlo.")
    nueva_ficha = deepcopy(f)
    nueva_ficha["transcript"].append({"rol": rol, "texto": mensaje, "ts": _ahora()})
    texto = "\n".join(t["texto"] for t in nueva_ficha["transcript"] if t["rol"] == "cliente")
    salida = claude_engine.validate({**{k: f[k] for k in CAMPOS_CLAUDE}, **salida}, texto)
    for k in CAMPOS_CLAUDE:
        if k in salida:
            nueva_ficha[k] = salida[k]
    nueva_ficha["revision"] += 1
    nueva_ficha["catalogo"] = catalog.load()["_sha256"]
    meta["turno"] = len(nueva_ficha["transcript"])
    meta["revision"] = nueva_ficha["revision"]
    nueva_ficha["metricas"].append(meta)
    return _persistir(f, nueva_ficha)


# ---------- Confirmación del vendedor ----------

def _huella(f, seleccion):
    contexto = {k: f.get(k) for k in ("revision", "hechos", "servicios_existentes", "candidatos",
                "escalamientos", "contradicciones", "plazo", "catalogo")}
    data = json.dumps([contexto, seleccion, catalog.load()["_sha256"]], ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(data.encode()).hexdigest()[:12]


def confirmar(f, seleccion, plazo=None):
    """El vendedor confirma la solución: [{sku, cantidad, depende_de_diseno?}]. SKUs inexistentes se rechazan."""
    if not isinstance(seleccion, list) or not seleccion or any(
            not isinstance(s, dict) or not isinstance(s.get("sku"), str) for s in seleccion):
        raise ValueError("La selección debe contener productos del catálogo.")
    invalidos = [s["sku"] for s in seleccion if not catalog.producto(s["sku"])]
    if invalidos:
        raise ValueError(f"SKUs inexistentes: {', '.join(invalidos)}")
    diseno = {c["sku"] for c in f["candidatos"] if c.get("depende_de_diseno")}
    limpia = [{"sku": s["sku"], "cantidad": s.get("cantidad"),
               "depende_de_diseno": s["sku"] in diseno or s.get("depende_de_diseno") is True}
              for s in seleccion]
    errores_cantidad = [error for s in limpia
                       if (error := validar_cantidad(catalog.producto(s["sku"]), s["cantidad"]))
                       and not (s["depende_de_diseno"] and s["cantidad"] is None)]
    if len({s["sku"] for s in limpia}) != len(limpia):
        errores_cantidad.append("La selección contiene un SKU duplicado.")
    if errores_cantidad:
        raise ValueError("; ".join(errores_cantidad))
    plazo = f["plazo"] if plazo is None else plazo
    if plazo not in (12, 24, 36):
        raise ValueError("El plazo debe ser de 12, 24 o 36 meses.")
    nueva_ficha = deepcopy(f)
    nueva_ficha["revision"] += int(plazo != f["plazo"])
    nueva_ficha["plazo"] = plazo
    nueva_ficha["catalogo"] = catalog.load()["_sha256"]
    nueva_ficha["confirmacion"] = {"seleccion": limpia, "revision": nueva_ficha["revision"], "ts": _ahora(),
                         "plazo": plazo, "huella": _huella(nueva_ficha, limpia)}
    return _persistir(f, nueva_ficha)


def cambiar_plazo(f, plazo):
    if plazo not in (12, 24, 36):
        raise ValueError("El plazo debe ser de 12, 24 o 36 meses.")
    if plazo != f["plazo"]:
        return _persistir(f, {**deepcopy(f), "plazo": plazo, "revision": f["revision"] + 1})
    return f


def estado_confirmacion(f):
    """sin_confirmar | vigente | desactualizada (cambiaron hechos, existentes, plazo o catálogo)."""
    c = f.get("confirmacion")
    if not c:
        return "sin_confirmar"
    return "vigente" if _huella(f, c["seleccion"]) == c["huella"] else "desactualizada"


# ---------- Cotización ----------

def _hecho_num(f, clave):
    valores = []
    for h in f["hechos"]:
        if h.get("clave") == clave and h.get("verificado"):
            numeros = claude_engine._numeros(h.get("valor"))
            if len(numeros) != 1:
                return None
            valores.append(float(next(iter(numeros))))
    return valores[0] if valores and len(set(valores)) == 1 else None


def cotizacion(f, usar_confirmacion=False):
    """Cotiza los candidatos de Claude (vista previa) o la selección confirmada por el vendedor (borrador)."""
    if usar_confirmacion and f.get("confirmacion"):
        seleccion = f["confirmacion"]["seleccion"]
    else:
        seleccion = f["candidatos"]
    seleccion_original = seleccion
    seleccion = deepcopy(seleccion)
    rto, rpo, oracle = (_hecho_num(f, k) for k in ("rto_horas", "rpo_minutos", "oracle_tb"))
    for c in seleccion:
        if ((c["sku"] == "SIM-DC-07" and ((rto is not None and rto < 4) or (rpo is not None and rpo < 15)))
                or (c["sku"] == "SIM-OCI-02" and oracle is not None and oracle > 2)):
            c["depende_de_diseno"] = True
            c["motivo_diseno"] = "Los requisitos confirmados exceden la capacidad estándar del producto."
    consumo = {fam: _hecho_num(f, f"consumo_{k}_mxn") for fam, k in (("AWS", "aws"), ("AZ", "azure"), ("OCI", "oci"))}
    existentes = [s["sku"] for s in f["servicios_existentes"] if s.get("verificado")]
    r = cotizar(seleccion, existentes=existentes, plazo=f.get("plazo", 12),
                consumo={k: v for k, v in consumo.items() if v is not None},
                conversaciones_mes=_hecho_num(f, "conversaciones_mes"))
    # Escalamientos: los que detecta el código + los confirmados por Claude con evidencia
    for e in f["escalamientos"]:
        if e.get("estado") == "confirmado":
            r["escalamientos"].setdefault(e["id"], e.get("evidencia", ""))
    if oracle and oracle > 2:
        r["escalamientos"].setdefault("ESC-08", f"Base Oracle de {oracle:g} TB")
    for clave, limite, inferior in (("rto_horas", 4, True), ("rpo_minutos", 15, True),
                                    ("disponibilidad_pct", 99.95, False)):
        valor = _hecho_num(f, clave)
        if valor is not None and (valor < limite if inferior else valor > limite):
            r["escalamientos"].setdefault("ESC-07", f"{clave}={valor:g}")
    if f.get("contradicciones"):
        r["bloqueos"].append("Aclarar las contradicciones del caso antes de generar el borrador.")
        r["incompleto"] = True
    if r["escalamientos"] and not r["parcial"] and r["lineas"]:
        r["parcial"] = True
        r["avisos"].append("Subtotal parcial: el caso requiere arquitecto; el alcance final puede cambiar con su diseño.")
    conf = estado_confirmacion(f)
    estados = []
    if r["incompleto"] or f["preguntas_pendientes"]:
        estados.append("faltan_datos")
    if r["lineas"] and not r["incompleto"]:
        estados.append("borrador_calculable")
    if r["escalamientos"] or r["pendiente_diseno"]:
        estados.append("requiere_arquitecto")
    if r["requiere_autorizacion"]:
        estados.append("requiere_autorizacion")
    r["estados"] = estados
    r["confirmacion"] = conf
    r["fuente"] = "confirmada" if usar_confirmacion and f.get("confirmacion") else "propuesta_claude"
    r["puede_generar_borrador"] = (usar_confirmacion and conf == "vigente" and bool(r["lineas"])
                                   and not r["incompleto"])
    r["case_id"], r["revision"] = f["case_id"], f["revision"]
    r["huella"] = _huella(f, seleccion_original)
    return r
