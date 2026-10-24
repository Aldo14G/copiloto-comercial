"""Copiloto Comercial · Streamlit. Ejecutar: streamlit run app.py"""
import os

import streamlit as st

from copiloto import catalog, claude_engine, ficha as F
from copiloto.export import expediente_md, propuesta_md

st.set_page_config(page_title="Copiloto Comercial", page_icon="🧭", layout="wide")
cat = catalog.load()
ESTADOS = {"faltan_datos": ("🟡", "Faltan datos"), "borrador_calculable": ("🟢", "Borrador calculable"),
           "requiere_arquitecto": ("🔵", "Requiere arquitecto"), "requiere_autorizacion": ("🟠", "Requiere autorización")}


def mxn(v):
    return f"${v:,.2f}"


# ---------- Sidebar: selección de cliente ----------
with st.sidebar:
    st.markdown("### 🧭 Copiloto Comercial")
    st.caption(f"Catálogo simulado · versión `{cat['_sha256']}`")
    opciones = {f"{c['id']} · {c['empresa']}": c["id"] for c in cat["casos_clientes"]}
    sel = st.selectbox("Cliente", list(opciones))
    case_id = opciones[sel]
    guardada = F.cargar(case_id)
    if "ficha" not in st.session_state or st.session_state.ficha["case_id"] != case_id:
        st.session_state.ficha = guardada or F.nueva(case_id)
    f = st.session_state.ficha
    if guardada:
        st.success(f"Ficha recuperada · {len(f['transcript'])} mensajes · {f['actualizado']}")
    if st.button("Reiniciar ficha", width="stretch"):
        st.session_state.ficha = f = F.nueva(case_id)
        F.guardar(f)
        st.rerun()
    modelo = st.radio("Modelo Claude", ["sonnet", "opus", "haiku"], horizontal=True)
    claude_engine.MODEL = os.environ.get("COPILOTO_MODEL", modelo)
    f["plazo"] = st.radio("Plazo (meses)", [12, 24, 36], index=[12, 24, 36].index(f.get("plazo", 12)), horizontal=True)
    if f["metricas"]:
        st.divider()
        st.markdown("**Métricas del caso**")
        st.write(f"Turnos: {len(f['metricas'])} · Latencia media: "
                 f"{sum(m['segundos'] for m in f['metricas']) / len(f['metricas']):.1f}s")
        st.write(f"Tokens: {sum(m['tokens_in'] + m['tokens_out'] for m in f['metricas']):,}")

caso = catalog.caso(case_id)
st.markdown(f"## {f['empresa']}")
st.caption(f"{f['industria']} · {f['empleados']} empleados · {caso['ciudad']} · etiqueta del catálogo: *{caso['tipo_de_caso']}*")

col_conv, col_ficha = st.columns([5, 7], gap="large")

# ---------- Conversación ----------
with col_conv:
    st.markdown("#### 💬 Conversación")
    for t in f["transcript"]:
        with st.chat_message("user" if t["rol"] == "cliente" else "assistant"):
            st.write(t["texto"])
    if not f["transcript"]:
        st.info(f"Primer mensaje del cliente:\n\n> {caso['mensaje_inicial']}")
        if st.button("▶ Iniciar con el primer mensaje", type="primary"):
            with st.spinner("Claude analiza el mensaje contra el catálogo…"):
                F.procesar_mensaje(f, caso["mensaje_inicial"])
            st.rerun()
    else:
        if st.button("🎭 Simular respuesta del cliente (demo)"):
            with st.spinner("El cliente ficticio responde…"):
                resp = claude_engine.simular_cliente(f)
            with st.spinner("Claude actualiza la ficha…"):
                F.procesar_mensaje(f, resp)
            st.rerun()
    msg = st.chat_input("Escribe lo que dijo el cliente…")
    if msg:
        with st.spinner("Claude actualiza la ficha…"):
            try:
                F.procesar_mensaje(f, msg)
            except Exception as e:  # noqa: BLE001
                st.error(str(e))
        st.rerun()

# ---------- Ficha ----------
with col_ficha:
    q = F.cotizacion(f) if f["transcript"] else None
    if q:
        st.markdown(" ".join(f"{ESTADOS[e][0]} **{ESTADOS[e][1]}**" for e in q["estados"]))
    tab_sig, tab_hechos, tab_prop, tab_arq = st.tabs(["🎯 Siguiente paso", "📋 Ficha", "💰 Propuesta", "🏗️ Arquitecto"])

    with tab_sig:
        if not f["transcript"]:
            st.caption("Inicia la conversación para que Claude prepare el guion.")
        else:
            st.markdown(f"**Necesidad:** {f['resumen_necesidad']}")
            st.success(f"🗣️ **Di ahora:** {f['guion_vendedor']}")
            st.markdown("**Preguntas pendientes**")
            for p in f["preguntas_pendientes"]:
                st.markdown(f"{p.get('prioridad', '·')}. {p['pregunta']}  \n<span style='color:gray;font-size:0.85em'>↳ {p.get('motivo', '')}</span>",
                            unsafe_allow_html=True)
            for c in f.get("contradicciones") or []:
                st.warning(f"Contradicción: {c}")

    with tab_hechos:
        st.markdown("**Hechos confirmados por el cliente** (cada uno con su cita textual)")
        for h in f["hechos"]:
            icon = "✅" if h.get("verificado") else f"⚠️ ({h.get('motivo_no_verificado') or 'no verificado'})"
            st.markdown(f"{icon} `{h['clave']}` = **{h['valor']}**  \n<span style='color:gray;font-size:0.85em'>“{h.get('cita', '')}”</span>",
                        unsafe_allow_html=True)
        if f["servicios_existentes"]:
            st.markdown("**Ya contratado por el cliente**")
            for s in f["servicios_existentes"]:
                st.markdown(f"{'✅' if s.get('verificado') else '⚠️'} {s['sku']} — {catalog.producto(s['sku'])['nombre']}")
        st.markdown("**Productos candidatos**")
        for c in f["candidatos"]:
            p = catalog.producto(c["sku"])
            st.markdown(f"- **{c['sku']}** {p['nombre']} · *{p['tipo']}* · cantidad: {c.get('cantidad') or '❓'}  \n  {c.get('justificacion', '')}")
        for a in f.get("alertas_validacion") or []:
            st.caption(f"🛡️ {a}")

    with tab_prop:
        if not q:
            st.caption("Sin datos aún.")
        else:
            st.caption("Calculado por código desde el catálogo. Claude no genera precios.")
            alt = f.get("alternativa")
            if alt:
                with st.expander(f"Alternativa: {', '.join(alt['skus'])}"):
                    st.markdown(f"{alt.get('resumen', '')}\n\n**Beneficios:** {alt.get('beneficios', '')}\n\n"
                                f"**Límites:** {alt.get('limites', '')}\n\n**Cuándo conviene:** {alt.get('cuando_conviene', '')}")
            st.markdown("**1. Revisa y confirma la solución** (ajusta cantidades si hace falta)")
            base = (f.get("confirmacion") or {}).get("seleccion") or f["candidatos"]
            editada = st.data_editor(
                [{"sku": c["sku"], "producto": catalog.producto(c["sku"])["nombre"], "cantidad": c.get("cantidad"),
                  "depende_de_diseno": bool(c.get("depende_de_diseno"))} for c in base],
                disabled=["sku", "producto"], num_rows="dynamic", hide_index=True, key=f"sel-{f['case_id']}-{f['revision']}")
            estado_conf = F.estado_confirmacion(f)
            st.caption({"sin_confirmar": "Sin confirmar", "vigente": "✅ Confirmada",
                        "desactualizada": "⚠️ Confirmación desactualizada: cambiaron datos o plazo"}[estado_conf])
            if st.button("Confirmar solución y cantidades", type="primary"):
                try:
                    F.confirmar(f, [r for r in editada if r.get("sku")])
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
            usar = estado_conf != "sin_confirmar"
            q = F.cotizacion(f, usar_confirmacion=usar)
            st.markdown(f"**2. {'Borrador' if q['puede_generar_borrador'] else 'Vista previa'} económico**")
            if q["lineas"]:
                st.dataframe([{
                    "SKU": l["sku"], "Producto": l["nombre"], "Cant.": l["cantidad"], "Unidad": l["unidad"],
                    "Mensual lista": mxn(l["mensual_lista"]), "Desc.": f"{l['desc_pct']:.0%}",
                    "Mensual neto": mxn(l["mensual_neto"]), "Cargo único": mxn(l["unico"]),
                    "Notas": "; ".join(l["notas"])} for l in q["lineas"]], hide_index=True, width="stretch")
            t = q["totales"]
            etiqueta = "Subtotal parcial" if q["parcial"] else "Total"
            m1, m2, m3 = st.columns(3)
            m1.metric(f"{etiqueta} mensual (sin IVA)", mxn(t["mensual"]))
            m2.metric(f"{etiqueta} único (sin IVA)", mxn(t["unico"]))
            m3.metric(f"Contrato {q['plazo']} meses", mxn(t["contrato"]))
            st.caption(f"Con IVA: mensual {mxn(t['mensual_iva'])} · único {mxn(t['unico_iva'])}. Vigencia 30 días.")
            for p in q["pendiente_diseno"]:
                st.info(f"🏗️ {p['sku']} {p['nombre']}: {p['motivo']} (no incluido en el importe)")
            for b in q["bloqueos"]:
                st.error(f"⛔ {b}")
            for a in q["avisos"]:
                st.warning(a)
            st.markdown("**3. Entregables del caso**")
            d1, d2 = st.columns(2)
            d1.download_button("⬇️ Propuesta comercial", propuesta_md(f, q),
                               file_name=f"propuesta-{f['case_id']}-r{f['revision']}.md",
                               disabled=not q["puede_generar_borrador"])
            d2.download_button("⬇️ Expediente interno", expediente_md(f, q),
                               file_name=f"expediente-{f['case_id']}-r{f['revision']}.md")
            if not q["puede_generar_borrador"]:
                st.caption("La propuesta se habilita con la solución confirmada, vigente y sin bloqueos.")

    with tab_arq:
        if not q or not q["escalamientos"]:
            st.caption("Sin disparadores de escalamiento: el vendedor puede avanzar solo.")
        else:
            st.info("Expediente listo para arquitecto: recibe la ficha completa, el cliente no repite nada.")
            reglas = {r["id"]: r["cuando_entra_un_arquitecto"] for r in cat["reglas_escalamiento"]}
            for k, v in q["escalamientos"].items():
                st.markdown(f"- **{k}** — {reglas.get(k, '')}  \n  Evidencia: *{v}*")
            posibles = [e for e in f["escalamientos"] if e.get("estado") == "posible"]
            if posibles:
                st.markdown("**Posibles (confirmar con el cliente)**")
                for e in posibles:
                    st.markdown(f"- {e['id']}: {e.get('evidencia', '')}")
            for p in q["a_medida"]:
                st.markdown(f"- 🏗️ {p['sku']} {p['nombre']} (a la medida, {p['tiempo_implementacion']})")
