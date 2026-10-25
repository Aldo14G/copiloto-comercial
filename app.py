"""Copiloto comercial. Ejecutar: python -m streamlit run app.py"""
from html import escape
from pathlib import Path

import streamlit as st

from copiloto import catalog, ficha as F, views

st.set_page_config(page_title="Copiloto comercial · Documento anotado", page_icon="✎", layout="wide")
st.html(f"<style>{(Path(__file__).parent / 'static/documento.css').read_text(encoding='utf-8')}</style>")
if "ficha" not in st.session_state:
    st.session_state.ficha = F.nueva()
if "vista" in st.session_state:
    st.session_state.navegacion = st.session_state.pop("vista")
st.session_state.setdefault("navegacion", "Reunión")
with st.container(key="cabecera"):
    marca, navegacion = st.columns([1, 3])
    with marca:
        st.html('<div class="marca"><strong>Copiloto</strong> comercial</div>')
    with navegacion:
        vista = st.radio("Secciones", ["Casos", "Catálogo", "Reunión", "Alternativas", "Cierre", "Historial"],
                         index=None, horizontal=True, label_visibility="collapsed", key="navegacion")
f = st.session_state.ficha
st.title(f["empresa"])
st.html(f'<p class="folio">{escape(f["case_id"])} / {escape(f["industria"] or "Industria por definir")} / Revisión {f["revision"]} '
        '<span class="etiqueta">Datos simulados</span></p>')
if f.get("synthetic"):
    st.info("Ejemplo sintético de diseño, sin análisis de Claude. No representa declaraciones de un cliente real.")
{"Casos": views.casos, "Catálogo": views.catalogo, "Reunión": views.reunion,
 "Alternativas": views.alternativas, "Cierre": views.cierre, "Historial": views.historial}[vista](f)
with st.container(key="pie"):
    cat = catalog.load()
    st.caption(f"La ficha continúa en propuesta y expediente · {len(cat['productos'])} productos / "
               f"{len(cat['familias'])} familias · catálogo {cat['_sha256']}")
