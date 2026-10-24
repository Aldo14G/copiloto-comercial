"""Ficha persistente del cliente: lo que se dijo una vez queda guardado para vendedor y arquitecto."""
import json
import re
from datetime import datetime

from . import catalog, claude_engine
from .catalog import DATA
from .quote import cotizar

FICHAS = DATA / "fichas"


def _ahora():
    return datetime.now().isoformat(timespec="seconds")


def nueva(case_id=None, empresa="Nuevo cliente", industria="", empleados=""):
    c = catalog.caso(case_id) if case_id else None
    if c:
        empresa, industria, empleados = c["empresa"], c["industria"], c["empleados"]
    return {"case_id": case_id or f"NUEVO-{datetime.now():%H%M%S}", "empresa": empresa, "industria": industria,
            "empleados": empleados, "catalogo": catalog.load()["_sha256"], "creado": _ahora(), "actualizado": _ahora(),
            "transcript": [], "hechos": [], "servicios_existentes": [], "candidatos": [], "preguntas_pendientes": [],
            "escalamientos": [], "contradicciones": [], "guion_vendedor": "", "resumen_necesidad": "",
            "tipo_caso": "por definir", "alertas_validacion": [], "metricas": [], "plazo": 12}


def ruta(case_id):
    return FICHAS / f"{case_id}.json"


def cargar(case_id):
    p = ruta(case_id)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def guardar(f):
    FICHAS.mkdir(parents=True, exist_ok=True)
    f["actualizado"] = _ahora()
    ruta(f["case_id"]).write_text(json.dumps(f, ensure_ascii=False, indent=2), encoding="utf-8")


def procesar_mensaje(f, mensaje):
    salida, meta = claude_engine.ask(claude_engine._prompt(f, mensaje))
    f["transcript"].append({"rol": "cliente", "texto": mensaje, "ts": _ahora()})
    texto = " ".join(t["texto"] for t in f["transcript"])
    salida = claude_engine.validate(salida, texto)
    for k in ("resumen_necesidad", "hechos", "servicios_existentes", "candidatos", "preguntas_pendientes",
              "escalamientos", "contradicciones", "guion_vendedor", "tipo_caso", "alertas_validacion"):
        if k in salida:
            f[k] = salida[k]
    meta["turno"] = len(f["transcript"])
    f["metricas"].append(meta)
    guardar(f)
    return f


def _hecho_num(f, clave):
    for h in f["hechos"]:
        if h.get("clave") == clave and h.get("verificado"):
            m = re.search(r"[\d.,]+", str(h.get("valor")))
            if m:
                try:
                    return float(m.group(0).replace(",", ""))
                except ValueError:
                    return None
    return None


def cotizacion(f):
    consumo = {fam: _hecho_num(f, f"consumo_{k}_mxn") for fam, k in (("AWS", "aws"), ("AZ", "azure"), ("OCI", "oci"))}
    existentes = [s["sku"] for s in f["servicios_existentes"] if s.get("verificado")]
    r = cotizar(f["candidatos"], existentes=existentes, plazo=f.get("plazo", 12),
                consumo={k: v for k, v in consumo.items() if v is not None},
                conversaciones_mes=_hecho_num(f, "conversaciones_mes"))
    # Escalamientos: los que detecta el código + los confirmados por Claude con evidencia
    for e in f["escalamientos"]:
        if e.get("estado") == "confirmado":
            r["escalamientos"].setdefault(e["id"], e.get("evidencia", ""))
    oracle = _hecho_num(f, "oracle_tb")
    if oracle and oracle > 2:
        r["escalamientos"].setdefault("ESC-08", f"Base Oracle de {oracle:g} TB")
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
    return r
