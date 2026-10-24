"""Cotizador determinista. Claude nunca calcula precios: solo propone SKUs y cantidades,
y este módulo valida y calcula todo con el catálogo.

Política de demo (explícita porque el catálogo no define cómo combinar descuentos):
- Descuentos aplican solo a mensualidades: plazo (24m 5%, 36m 10%) + paquete (8%) + volumen M365 (3%).
- Se suman por línea. El vendedor aplica hasta 10% por línea; el excedente se muestra
  como "requiere autorización del gerente" y NO se descuenta en el borrador.
- Consumo (AWS/Azure/OCI) usa el consumo estimado declarado; sin él, el total queda incompleto.
- Soporte 24/7 de nube = max(10% del consumo, 12,000).
"""
from . import catalog

IVA = 0.16
DESC_PLAZO = {12: 0.0, 24: 0.05, 36: 0.10}
TOPE_VENDEDOR = 0.10
LICENCIAS_M365 = {"SIM-M365-01", "SIM-M365-02", "SIM-M365-03", "SIM-M365-04", "SIM-M365-05"}
CONSUMO_FAMILIA = {"SIM-AWS-01": "AWS", "SIM-AZ-01": "AZ", "SIM-OCI-01": "OCI"}
SOPORTE_FAMILIA = {"SIM-AWS-03": "AWS", "SIM-AZ-05": "AZ", "SIM-OCI-05": "OCI"}
MIGRACION_SERVIDORES = {"SIM-AWS-05", "SIM-AZ-04"}


def _num(v):
    try:
        return float(v) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


def cotizar(candidatos, existentes=(), plazo=12, consumo=None, conversaciones_mes=None):
    """candidatos: [{sku, cantidad}]; existentes: SKUs que el cliente ya tiene (con evidencia).
    consumo: {"AWS": mxn_mes, ...}. Devuelve dict con líneas, bloqueos, escalamientos y totales."""
    consumo = consumo or {}
    lineas, bloqueos, avisos, escal = [], [], [], {}
    a_medida = []
    skus = [c["sku"] for c in candidatos]
    disponibles = set(skus) | set(existentes)
    incompleto = False

    if plazo not in DESC_PLAZO:
        bloqueos.append(f"Plazo {plazo} meses no existe en condiciones comerciales (12, 24 o 36).")
        plazo = 12

    # Paquetes completos dentro de la selección
    paquetes = [k for k in catalog.load()["paquetes"] if set(k["productos"]) <= set(skus)]
    sku_paquete = {s: k for k in paquetes for s in k["productos"]}
    usuarios_lic = sum((_num(c.get("cantidad")) or 0) for c in candidatos if c["sku"] in LICENCIAS_M365
                       and c["sku"] != "SIM-M365-05")
    tipos_lic = {c["sku"] for c in candidatos if c["sku"] in LICENCIAS_M365 - {"SIM-M365-05"}}

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
            if est is None:
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
            if est is None:
                incompleto = True
                linea["mensual_lista"] = float(p["precio_mensual_mxn"])
                linea["notas"].append("Mínimo mensual; el cargo real es 10% del consumo (falta consumo estimado).")
            else:
                linea["mensual_lista"] = max(0.10 * est, float(p["precio_mensual_mxn"]))
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
            mensual = float(p["precio_mensual_mxn"] or 0)
            unico = float(p["cargo_unico_mxn"] or 0)
            per_unit_unico = unidad.startswith("cargo único por") or unidad == "por mes"
            linea["mensual_lista"] = mensual * qty
            linea["unico"] = unico * (qty if per_unit_unico else 1)
            if sku == "SIM-IA-01":
                conv = _num(conversaciones_mes)
                if conv is None:
                    linea["notas"].append("Incluye 2,000 conversaciones/mes; adicionales a $4 (volumen no confirmado).")
                elif conv > 2000:
                    extra = (conv - 2000) * 4 * qty
                    linea["mensual_lista"] += extra
                    linea["notas"].append(f"{conv - 2000:,.0f} conversaciones adicionales x $4")
            if sku in MIGRACION_SERVIDORES and qty > 10:
                escal.setdefault("ESC-03", f"Migración de {qty:g} servidores")

        # Descuentos (solo mensualidades)
        d = DESC_PLAZO[plazo]
        if sku in sku_paquete:
            d += sku_paquete[sku]["descuento_pct"] / 100
            linea["notas"].append(f"Paquete {sku_paquete[sku]['id']}")
        if sku in LICENCIAS_M365 and usuarios_lic >= 100:
            d += 0.03
            linea["notas"].append("Volumen M365 ≥100 usuarios")
        linea["desc_pct"] = min(d, TOPE_VENDEDOR)
        linea["desc_pendiente_pct"] = max(0.0, d - TOPE_VENDEDOR)
        lineas.append(linea)

    if usuarios_lic > 300 or len(tipos_lic) > 1:
        escal.setdefault("ESC-02", f"{usuarios_lic:g} usuarios M365 / {len(tipos_lic)} tipos de licencia")

    for l in lineas:
        l["mensual_neto"] = round(l["mensual_lista"] * (1 - l["desc_pct"]), 2)
    mensual = round(sum(l["mensual_neto"] for l in lineas), 2)
    unico = round(sum(l["unico"] for l in lineas), 2)
    if mensual > 250000:
        escal.setdefault("ESC-09", f"Mensualidad estimada {mensual:,.0f} MXN")
    requiere_autorizacion = any(l["desc_pendiente_pct"] > 0 for l in lineas)
    if requiere_autorizacion:
        avisos.append("Hay descuento adicional sobre el 10% que requiere autorización del gerente (no aplicado).")

    return {
        "plazo": plazo, "lineas": lineas, "a_medida": a_medida, "paquetes": [k["id"] for k in paquetes],
        "bloqueos": bloqueos, "avisos": avisos, "escalamientos": escal, "incompleto": incompleto or bool(bloqueos),
        "requiere_autorizacion": requiere_autorizacion,
        "totales": {"mensual": mensual, "mensual_iva": round(mensual * (1 + IVA), 2),
                    "unico": unico, "unico_iva": round(unico * (1 + IVA), 2),
                    "contrato": round(mensual * plazo + unico, 2)},
        "catalogo": catalog.load()["_sha256"],
    }
