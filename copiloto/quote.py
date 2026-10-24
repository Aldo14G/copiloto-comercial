"""Cotizador determinista. Claude nunca calcula precios: solo propone SKUs y cantidades,
y este módulo valida y calcula todo con el catálogo.

Política de demo (explícita porque el catálogo no define cómo combinar descuentos):
- Descuentos aplican solo a mensualidades: plazo (24m 5%, 36m 10%) + paquete (8%) + volumen M365 (3%).
- Se suman por línea. El vendedor aplica hasta 10% por línea; el excedente se muestra
  como "requiere autorización del gerente" y NO se descuenta. Combinar fuentes bloquea
  el borrador hasta aclarar su acumulación; esa suma solo permite explorar la simulación.
- Consumo (AWS/Azure/OCI) usa el consumo estimado declarado; sin él, el total queda incompleto.
- Soporte 24/7 de nube = max(10% del consumo, 12,000).
"""
import math
from decimal import Decimal, ROUND_HALF_UP

from . import catalog

DESC_PLAZO = {12: 0.0, 24: 0.05, 36: 0.10}
TOPE_VENDEDOR = 0.10
LICENCIAS_M365 = {"SIM-M365-01", "SIM-M365-02", "SIM-M365-03", "SIM-M365-04", "SIM-M365-05"}
CONSUMO_FAMILIA = {"SIM-AWS-01": "AWS", "SIM-AZ-01": "AZ", "SIM-OCI-01": "OCI"}
SOPORTE_FAMILIA = {"SIM-AWS-03": "AWS", "SIM-AZ-05": "AZ", "SIM-OCI-05": "OCI"}
MIGRACION_SERVIDORES = {"SIM-AWS-05", "SIM-AZ-04"}
# Disparadores por producto expresados en la misma unidad de su cantidad (catálogo simulado).
DISENO_CANTIDAD = {"SIM-DC-02": 3, "SIM-DC-05": 1, "SIM-DC-07": 20, "SIM-M365-04": 1000,
                   "SIM-M365-05": 500, "SIM-M365-06": 500, "SIM-BK-01": 100,
                   "SIM-BK-02": 2000, "SIM-BK-04": 1000}


def _num(v):
    try:
        n = float(v) if v not in (None, "") and not isinstance(v, bool) else None
        return n if n is not None and math.isfinite(n) else None
    except (TypeError, ValueError, OverflowError):
        return None


def validar_cantidad(producto, cantidad):
    """Una regla compartida por confirmación y cálculo; consumo y diseño no exigen unidades."""
    if producto["tipo"] == "a la medida" or producto["sku"] in CONSUMO_FAMILIA | SOPORTE_FAMILIA:
        return None
    n = _num(cantidad)
    if n is None or n <= 0 or (producto["unidad_cobro"] != "por TB al mes" and not n.is_integer()):
        return f"{producto['sku']}: cantidad inválida; debe ser positiva y entera salvo almacenamiento en TB."
    return None


def _dinero(valor):
    return float(Decimal(str(valor)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def cotizar(candidatos, existentes=(), plazo=12, consumo=None, conversaciones_mes=None):
    """candidatos: [{sku, cantidad, depende_de_diseno?}]; existentes: SKUs que el cliente ya tiene (con evidencia).
    consumo: {"AWS": mxn_mes, ...}. Devuelve dict con líneas, bloqueos, escalamientos y totales.
    Un candidato con depende_de_diseno no se suma: queda en "pendiente_diseno" (cierre parcial, D08)."""
    consumo = consumo or {}
    lineas, bloqueos, avisos, escal = [], [], [], {}
    a_medida, pendiente_diseno = [], []
    # Un SKU representa una sola línea; duplicarlo puede duplicar importes y descuentos.
    vistos, validos = set(), []
    for c in candidatos:
        sku = c.get("sku")
        if sku in vistos:
            bloqueos.append(f"SKU duplicado: {sku}.")
            continue
        vistos.add(sku)
        p = catalog.producto(sku)
        qty = _num(c.get("cantidad"))
        error = validar_cantidad(p, c.get("cantidad")) if p else None
        if error and not c.get("depende_de_diseno"):
            bloqueos.append(error)
            continue
        if sku in DISENO_CANTIDAD and qty is not None and qty > DISENO_CANTIDAD[sku]:
            c = {**c, "depende_de_diseno": True,
                 "motivo_diseno": f"Cantidad {qty:g} supera el umbral de arquitectura del producto ({DISENO_CANTIDAD[sku]})"}
        validos.append(c)
    candidatos = validos
    usuarios_escalamiento = sum((_num(c.get("cantidad")) or 0) for c in candidatos if c["sku"] in LICENCIAS_M365
                       and c["sku"] != "SIM-M365-05")
    tipos_lic = {c["sku"] for c in candidatos if c["sku"] in LICENCIAS_M365 - {"SIM-M365-05"}}
    for c in candidatos:
        p = catalog.producto(c["sku"])
        if c.get("depende_de_diseno") and p and p["tipo"] != "a la medida":
            pendiente_diseno.append({"sku": c["sku"], "nombre": p["nombre"], "cantidad": c.get("cantidad"),
                                     "motivo": c.get("motivo_diseno") or "Su viabilidad o dimensionamiento depende del diseño del arquitecto"})
    # Cascada: si un componente solo tiene satisfecha su dependencia con algo sujeto a diseño (o a la medida),
    # tampoco es separable aunque tenga precio de catálogo.
    while True:
        bloqueados = {x["sku"] for x in pendiente_diseno} | {
            c["sku"] for c in candidatos if (catalog.producto(c["sku"]) or {}).get("tipo") == "a la medida"}
        restantes = {c["sku"] for c in candidatos} - bloqueados
        nuevos = []
        for c in candidatos:
            p = catalog.producto(c["sku"])
            if not p or c["sku"] in bloqueados or not p["requiere_alguno_de"]:
                continue
            req = set(p["requiere_alguno_de"])
            if not req & (restantes | set(existentes)) and req & bloqueados:
                nuevos.append({"sku": c["sku"], "nombre": p["nombre"], "cantidad": c.get("cantidad"),
                               "motivo": f"Depende de {', '.join(sorted(req & bloqueados))}, sujeto a diseño"})
        if not nuevos:
            break
        pendiente_diseno += nuevos
    candidatos = [c for c in candidatos if c["sku"] not in {x["sku"] for x in pendiente_diseno}]
    skus = [c["sku"] for c in candidatos]
    disponibles = set(skus) | set(existentes)
    incompleto = False

    if plazo not in DESC_PLAZO:
        bloqueos.append(f"Plazo {plazo} meses no existe en condiciones comerciales (12, 24 o 36).")
        plazo = 12

    # Paquetes completos dentro de la selección
    paquetes = [k for k in catalog.load()["paquetes"] if set(k["productos"]) <= set(skus)]
    sku_paquete = {s: k for k in paquetes for s in k["productos"]}
    usuarios_lic = sum((_num(c.get("cantidad")) or 0) for c in candidatos
                       if c["sku"] in LICENCIAS_M365 - {"SIM-M365-05"})

    for c in candidatos:
        sku, p = c["sku"], catalog.producto(c["sku"])
        if p is None:
            bloqueos.append(f"SKU inexistente propuesto: {sku} (descartado).")
            continue
        if p["tipo"] == "a la medida":
            a_medida.append(p)
            escal.setdefault("ESC-01", f"{sku} {p['nombre']} es a la medida")
            continue
        qty = _num(c.get("cantidad"))
        unidad = p["unidad_cobro"]
        linea = {"sku": sku, "nombre": p["nombre"], "unidad": unidad, "cantidad": qty,
                 "mensual_lista": 0.0, "unico": 0.0, "desc_pct": 0.0, "desc_pendiente_pct": 0.0,
                 "notas": []}

        # Dependencias OR
        req = p["requiere_alguno_de"]
        if req and not (set(req) & disponibles):
            bloqueos.append(f"{sku} requiere alguno de {', '.join(req)} (no está en la propuesta ni verificado como existente).")

        if p["plazo_minimo_meses"] and plazo < p["plazo_minimo_meses"]:
            bloqueos.append(f"{sku} exige plazo mínimo de {p['plazo_minimo_meses']} meses.")

        if sku in CONSUMO_FAMILIA:
            est = _num(consumo.get(CONSUMO_FAMILIA[sku]))
            if est is None or est < 0:
                incompleto = True
                linea["notas"].append("Falta consumo mensual estimado; se cobra por uso real.")
            else:
                linea["mensual_lista"] = est
                linea["notas"].append("Consumo estimado declarado por el cliente; se cobra por uso real.")
                if est > 250000:
                    escal.setdefault("ESC-09", f"Consumo estimado {est:,.0f} MXN/mes")
            lineas.append(linea)
            continue

        if sku in SOPORTE_FAMILIA:
            est = _num(consumo.get(SOPORTE_FAMILIA[sku]))
            if est is None or est < 0:
                incompleto = True
                linea["mensual_lista"] = float(p["precio_mensual_mxn"])
                linea["notas"].append("Mínimo mensual; el cargo real es 10% del consumo (falta consumo estimado).")
            else:
                linea["mensual_lista"] = max(Decimal("0.10") * Decimal(str(est)), Decimal(str(p["precio_mensual_mxn"])))
                linea["notas"].append(f"max(10% de {est:,.0f}, 12,000)")
            linea["cantidad"] = 1
        else:
            if qty is None:
                incompleto = True
                bloqueos.append(f"Falta cantidad para {sku} ({unidad}).")
                lineas.append(linea)
                continue
            qmin, qmax = p["cantidad_minima"], p["cantidad_maxima"]
            if sku == "SIM-IA-02":
                qmax = None  # el 100 del catálogo es capacidad de usuarios, no unidades
                linea["notas"].append("Incluye hasta 100 usuarios.")
            if qmin and qty < qmin:
                bloqueos.append(f"{sku}: cantidad {qty:g} menor al mínimo {qmin}.")
            if qmax and qty > qmax:
                bloqueos.append(f"{sku}: cantidad {qty:g} mayor al máximo {qmax}.")
            mensual = Decimal(str(p["precio_mensual_mxn"] or 0))
            unico = Decimal(str(p["cargo_unico_mxn"] or 0))
            per_unit_unico = unidad.startswith("cargo único por") or unidad == "por mes"
            linea["mensual_lista"] = mensual * Decimal(str(qty))
            linea["unico"] = unico * (Decimal(str(qty)) if per_unit_unico else 1)
            if sku == "SIM-IA-01":
                conv = _num(conversaciones_mes)
                if conv is None or conv < 0 or not conv.is_integer():
                    incompleto = True
                    linea["notas"].append("Incluye 2,000 conversaciones/mes; adicionales a $4 (volumen no confirmado).")
                elif conv > 2000:
                    extra = Decimal(str(conv - 2000)) * 4 * Decimal(str(qty))
                    linea["mensual_lista"] += extra
                    linea["notas"].append(f"{conv - 2000:,.0f} conversaciones adicionales x $4")
            if sku in MIGRACION_SERVIDORES and qty > 10:
                escal.setdefault("ESC-03", f"Migración de {qty:g} servidores")

        # Descuentos (solo mensualidades)
        d = DESC_PLAZO[plazo]
        fuentes_descuento = int(d > 0)
        if sku in sku_paquete:
            d += sku_paquete[sku]["descuento_pct"] / 100
            fuentes_descuento += 1
            linea["notas"].append(f"Paquete {sku_paquete[sku]['id']}")
        if sku in LICENCIAS_M365 and usuarios_lic >= 100:
            d += 0.03
            fuentes_descuento += 1
            linea["notas"].append("Volumen M365 ≥100 usuarios")
        if fuentes_descuento > 1 and linea["mensual_lista"] > 0:
            bloqueos.append(f"{sku}: confirmar la política de acumulación de descuentos; el catálogo no la define. La simulación no habilita un borrador.")
        linea["desc_pct"] = min(d, TOPE_VENDEDOR)
        linea["desc_pendiente_pct"] = max(0.0, d - TOPE_VENDEDOR)
        lineas.append(linea)

    if usuarios_escalamiento > 300 or len(tipos_lic) > 1:
        escal.setdefault("ESC-02", f"{usuarios_escalamiento:g} usuarios M365 / {len(tipos_lic)} tipos de licencia")

    for l in lineas:
        if not all(math.isfinite(l[k]) and abs(l[k]) <= 1e12 for k in ("mensual_lista", "unico")):
            bloqueos.append(f"{l['sku']}: importe fuera del rango numérico permitido.")
            l["mensual_lista"] = l["unico"] = 0.0
        l["mensual_neto"] = _dinero(Decimal(str(l["mensual_lista"])) * (1 - Decimal(str(l["desc_pct"]))))
        l["mensual_lista"] = _dinero(l["mensual_lista"])
        l["unico"] = _dinero(l["unico"])
    mensual = _dinero(sum((Decimal(str(l["mensual_neto"])) for l in lineas), Decimal(0)))
    unico = _dinero(sum((Decimal(str(l["unico"])) for l in lineas), Decimal(0)))
    if mensual > 250000:
        escal.setdefault("ESC-09", f"Mensualidad estimada {mensual:,.0f} MXN")
    requiere_autorizacion = any(l["desc_pendiente_pct"] > 0 for l in lineas)
    if requiere_autorizacion:
        avisos.append("Hay descuento adicional sobre el 10% que requiere autorización del gerente (no aplicado).")

    parcial = bool(pendiente_diseno or a_medida)
    if parcial:
        avisos.append("Subtotal parcial: no incluye componentes a la medida ni sujetos a diseño del arquitecto.")
    return {
        "plazo": plazo, "lineas": lineas, "a_medida": a_medida, "pendiente_diseno": pendiente_diseno,
        "paquetes": [k["id"] for k in paquetes], "parcial": parcial,
        "bloqueos": bloqueos, "avisos": avisos, "escalamientos": escal, "incompleto": incompleto or bool(bloqueos),
        "requiere_autorizacion": requiere_autorizacion,
        "totales": {"mensual": mensual, "mensual_iva": _dinero(Decimal(str(mensual)) * Decimal("1.16")),
                    "unico": unico, "unico_iva": _dinero(Decimal(str(unico)) * Decimal("1.16")),
                    "contrato": _dinero(Decimal(str(mensual)) * plazo + Decimal(str(unico)))},
        "catalogo": catalog.load()["_sha256"],
    }
