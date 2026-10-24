"""Vistas de trabajo. Las reglas, persistencia y precios viven en el core."""
from html import escape

import streamlit as st

from . import catalog, ficha as F
from .demo import ejemplo
from .export import archivos, propuesta_md, expediente_md


def rotulo(texto):
    st.html(f'<p class="rotulo">{escape(texto)}</p>')


def casos(f):
    st.header("Cada reunión conserva su contexto")
    st.write("Retoma un caso o abre una conversación nueva. El catálogo completo está disponible en todos los casos.")
    opciones = {c["id"]: c["empresa"] for c in catalog.load()["casos_clientes"]}
    for path in sorted(F.FICHAS.glob("*.json")):
        opciones.setdefault(path.stem, path.stem)
    elegido = st.selectbox("Caso para continuar", list(opciones),
                          format_func=lambda k: f"{k} · {opciones[k]}")
    if st.button("Abrir caso"):
        try:
            st.session_state.ficha = F.cargar(elegido) or F.nueva(elegido)
            st.session_state.vista = "Reunión"
            st.rerun()
        except (OSError, ValueError, KeyError) as error:
            st.error(f"No se pudo recuperar el caso. La ficha actual se conserva. {error}")
    with st.expander("Nuevo caso", expanded=not f["transcript"]):
        with st.form("nuevo"):
            empresa = st.text_input("Empresa", max_chars=160)
            industria = st.text_input("Industria", max_chars=120)
            empleados = st.text_input("Empleados (contexto opcional; no determina licencias)", max_chars=40)
            crear = st.form_submit_button("Crear caso")
        if crear:
            if not empresa.strip():
                st.error("Escribe el nombre de la empresa.")
            else:
                nueva = F.nueva(empresa=empresa.strip(), industria=industria.strip(), empleados=empleados or "Por definir")
                F.guardar(nueva)
                st.session_state.ficha = nueva
                st.session_state.vista = "Reunión"
                st.rerun()
    st.divider()
    st.subheader("Recorrido de ejemplo, sin llamadas a Claude")
    st.write("Continuación sintética de Aceros del Valle: alojamiento y enlace separables; recuperación pendiente de arquitectura. Se crea una copia nueva.")
    if st.button("Abrir ejemplo sintético"):
        st.session_state.ficha = ejemplo()
        st.session_state.vista = "Reunión"
        st.rerun()


def reunion(f):
    izquierda, derecha = st.columns([1.55, 1], gap="large")
    with izquierda:
        rotulo("Evidencia del cliente")
        fuentes = [t for t in f["transcript"] if t["rol"] == "cliente"]
        inicial = (catalog.caso(f["case_id"]) or {}).get("mensaje_inicial", "")
        fuente = fuentes[-1]["texto"] if fuentes else inicial
        if fuente:
            st.html(f'<blockquote class="cita">{escape(fuente)}”</blockquote>')
            if not fuentes:
                st.caption("Mensaje inicial del caso ficticio. Todavía no se ha analizado.")
        else:
            st.subheader("La conversación empieza aquí")
            st.write("Captura lo que dijo el cliente. Conservaremos sus palabras junto a cada dato identificado.")
    with derecha:
        rotulo("Hechos identificados")
        if not f["hechos"]:
            st.write("Los datos aparecerán después de analizar el primer fragmento.")
        for h in f["hechos"]:
            estado = "Cita presente · revisar interpretación" if h.get("verificado") else h.get("motivo_no_verificado", "Sin verificar")
            st.html(f'<div class="dato"><mark>{escape(str(h["valor"]))}</mark>'
                    f'<small>{escape(h["clave"].replace("_", " "))} · {escape(estado)}</small>'
                    f'<small>«{escape(h.get("cita", ""))}»</small></div>')
    with st.container(key="decision"):
        rotulo("Decisión abierta")
        st.subheader(f["resumen_necesidad"] or "Entender la necesidad antes de recomendar")
    izquierda, derecha = st.columns([1.55, 1], gap="large")
    with izquierda:
        rotulo("Pregunta actual")
        pregunta = next(iter(f["preguntas_pendientes"]), None)
        st.html(f'<p class="pregunta">{escape(pregunta["pregunta"] if pregunta else "¿Qué necesita resolver el cliente y cómo afecta a su operación?")}</p>')
        if pregunta:
            st.caption(pregunta.get("motivo", ""))
        with st.container(key="captura"):
            rotulo("Añadir respuesta")
            with st.form(f"fragmento-{f['case_id']}-{f['revision']}"):
                origen = st.radio("Fuente de la información", ["Cita del cliente", "Nota del vendedor"], horizontal=True)
                mensaje = st.text_area("Escribe o pega el fragmento", value=inicial if not f["transcript"] else "", height=125, max_chars=12000)
                enviar = st.form_submit_button("Incorporar a la ficha", type="primary")
            if enviar:
                try:
                    with st.spinner("Contrastando el fragmento con el catálogo…"):
                        F.procesar_mensaje(f, mensaje, "cliente" if origen == "Cita del cliente" else "vendedor")
                    st.rerun()
                except (ValueError, OSError, RuntimeError, TimeoutError) as error:
                    st.error(f"No se incorporó el fragmento; se conserva la ficha. {error}")
        if f["guion_vendedor"]:
            with st.expander("Apoyo para la conversación"):
                st.write(f["guion_vendedor"])
    with derecha, st.container(key="pendientes"):
        rotulo("Datos pendientes")
        for p in f["preguntas_pendientes"]:
            st.markdown(f"**{p['pregunta']}**")
            st.caption(p.get("motivo", ""))
        for c in f["contradicciones"]:
            st.warning(f"Contradicción por aclarar: {c}")
        if f["candidatos"]:
            rotulo("Camino por evaluar")
            for c in f["candidatos"]:
                st.write(catalog.producto(c["sku"])["nombre"])
                st.caption(c.get("justificacion", "Pendiente de revisión del vendedor."))
            st.caption("Consulta Alternativas para revisar alcance y cantidades.")
        for alerta in f["alertas_validacion"]:
            st.caption(alerta)


def alternativas(f):
    st.header("De la necesidad a una solución justificable")
    principal, alternativa = st.columns(2, gap="large")
    with principal:
        rotulo("Recomendación principal · por revisar")
        for c in f["candidatos"]:
            st.subheader(catalog.producto(c["sku"])["nombre"])
            st.write(c.get("justificacion", "Revisa la pertinencia con el cliente."))
        if not f["candidatos"]:
            st.write("Aún no hay recomendación. Continúa el levantamiento o selecciona componentes con sustento.")
    with alternativa:
        rotulo("Alternativa comparada")
        alt = f["alternativa"]
        if alt:
            st.subheader(alt.get("resumen", "Alternativa"))
            for k, label in (("beneficios", "Beneficios"), ("limites", "Límites"), ("cuando_conviene", "Cuándo conviene")):
                st.write(f"{label}: {alt.get(k, '')}")
            st.caption(", ".join(alt["skus"]))
        else:
            st.write("No hay una segunda opción sustentada en esta revisión. No se fuerza una alternativa.")
    st.divider()
    st.subheader("Revisa la selección y su dimensionamiento")
    st.caption("La presencia de una cita comprueba el origen del texto; el vendedor revisa su interpretación y la pertinencia de la solución.")
    base = (f.get("confirmacion") or {}).get("seleccion") or f["candidatos"]
    base = {c["sku"]: c for c in base}
    seleccion = st.multiselect("Componentes del catálogo", list(catalog.load()["_por_sku"]), default=list(base),
                             format_func=lambda sku: f"{sku} · {catalog.producto(sku)['nombre']}",
                             key=f"componentes-{f['case_id']}-{f['revision']}")
    # Elegir componentes actualiza los campos; dimensionar y confirmar es una sola operación.
    with st.form(f"confirmacion-{f['case_id']}-{f['revision']}-{'-'.join(seleccion)}"):
        filas, plazo, revisada, enviar = _dimensionamiento(f, seleccion, base)
    if enviar:
        try:
            if not revisada:
                raise ValueError("Revisa las fuentes y marca la casilla de revisión antes de confirmar.")
            F.confirmar(f, filas, plazo)
            st.success("Selección guardada. El cierre comprobará si el importe puede calcularse.")
        except (ValueError, OSError) as error:
            st.error(str(error))
    st.caption(f"Confirmación: {F.estado_confirmacion(f)}. Abre Cierre para preparar los entregables.")


def _dimensionamiento(f, seleccion, base):
    filas = []
    for sku in seleccion:
        p, c = catalog.producto(sku), base.get(sku, {})
        with st.expander(f"{sku} · {p['nombre']}", expanded=True):
            st.write(f"{p['tipo']} · {p['unidad_cobro']}")
            st.caption(p["descripcion"])
            cantidad = st.number_input("Cantidad", value=float(c["cantidad"]) if c.get("cantidad") is not None else None,
                                       min_value=0.0, step=.1 if p["unidad_cobro"] == "por TB al mes" else 1.0,
                                       key=f"qty-{f['case_id']}-{f['revision']}-{sku}")
            diseno = st.checkbox("Sujeto al diseño del arquitecto", value=bool(c.get("depende_de_diseno")),
                                 key=f"design-{f['case_id']}-{f['revision']}-{sku}")
            st.caption(f"Dependencias: {', '.join(p['requiere_alguno_de']) or 'Sin dependencia obligatoria'}. Arquitectura: {p['cuando_entra_arquitecto'] or 'Según requisitos del caso'}.")
            filas.append({"sku": sku, "cantidad": cantidad, "depende_de_diseno": diseno})
    plazo = st.radio("Plazo (meses)", [12, 24, 36], index=[12, 24, 36].index(f["plazo"]), horizontal=True,
                     key=f"plazo-{f['case_id']}-{f['revision']}")
    st.caption("Selección, cantidades y plazo se guardan juntos al confirmar.")
    revisada = st.checkbox("Revisé fuentes, alcance, cantidades y componentes que dependen de diseño", key=f"revisada-{f['case_id']}-{f['revision']}")
    enviar = st.form_submit_button("Confirmar solución y cantidades", type="primary", disabled=not filas)
    return filas, plazo, revisada, enviar


def cierre(f):
    st.header("Un caso, dos entregables vinculados")
    q = F.cotizacion(f, usar_confirmacion=bool(f.get("confirmacion")))
    st.caption(f"Revisión {f['revision']} · catálogo {q['catalogo']} · confirmación {q['confirmacion']}")
    if q["puede_generar_borrador"]:
        etiqueta = "Subtotal parcial" if q["parcial"] else "Total"
        mensual, unico = st.columns(2)
        mensual.metric(f"{etiqueta} mensual · sin IVA", f"${q['totales']['mensual']:,.2f}")
        unico.metric(f"{etiqueta} único · sin IVA", f"${q['totales']['unico']:,.2f}")
        st.caption(f"Con IVA: mensual {q['totales']['mensual_iva']:,.2f} MXN · único {q['totales']['unico_iva']:,.2f} MXN. Vigencia 30 días.")
    else:
        st.warning("La propuesta económica aún no está habilitada. Revisa Alternativas y los datos del importe. Puedes preparar el expediente interno.")
    for b in q["bloqueos"]:
        st.error(b)
    for a in q["avisos"]:
        st.info(a)
    for p in q["pendiente_diseno"]:
        st.write(f"En diseño: {p['nombre']}. {p['motivo']}")
    for k, v in q["escalamientos"].items():
        st.write(f"Arquitectura · {k}: {v}")
    for p in q["a_medida"]:
        st.write(f"A la medida: {p['nombre']} · sin precio de lista.")
    comercial, interno = st.columns(2, gap="large")
    with comercial:
        rotulo("Para el cliente")
        st.subheader("Propuesta comercial")
        st.write("Necesidad, solución justificada, alcance calculable, condiciones y siguiente paso.")
        with st.expander("Revisar propuesta"):
            st.markdown(propuesta_md(f, q))
    with interno:
        rotulo("Para preventa y arquitectura")
        st.subheader("Expediente interno")
        st.write("Fuentes, datos, escalamientos y pendientes para continuar sin perder contexto.")
        with st.expander("Revisar expediente"):
            st.markdown(expediente_md(f, q))
    st.caption("Corrige datos incorporando un fragmento aclaratorio en Reunión; ajusta selección y cantidades en Alternativas. Editar el Word descargado no actualiza la ficha.")
    clave = (f["case_id"], f["revision"], q["huella"], q["confirmacion"])
    if st.button("Preparar PDF y Word", type="primary"):
        try:
            st.session_state.entregables = (clave, archivos(f, q))
        except (ValueError, OSError) as error:
            st.error(f"No se generaron los entregables: {error}")
    preparados = st.session_state.get("entregables")
    if preparados and preparados[0] == clave:
        for nombre, datos in preparados[1].items():
            tipo = "application/pdf" if nombre.endswith(".pdf") else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            st.download_button(f"Descargar {nombre}", datos, file_name=nombre, mime=tipo, on_click="ignore")


def catalogo(f):
    cat = catalog.load()
    st.header("El catálogo completo, consultable")
    st.caption("45 productos · 7 familias · 7 paquetes. Catálogo simulado para el hackathon; no es información comercial oficial de Alestra.")
    familia = st.selectbox("Familia", ["Todas", *[x["id"] for x in cat["familias"]]])
    buscar = st.text_input("Buscar por SKU, producto o necesidad").casefold().strip()
    productos = [p for p in cat["productos"] if (familia == "Todas" or p["familia"] == familia)
                 and buscar in f"{p['sku']} {p['nombre']} {p['descripcion']} {p['senal_del_cliente']}".casefold()]
    st.write(f"{len(productos)} productos")
    for p in productos:
        with st.expander(f"{p['sku']} · {p['nombre']}"):
            st.write(p["descripcion"])
            for k, v in p.items():
                if k not in {"sku", "nombre", "descripcion"}:
                    st.write(f"{k.replace('_', ' ')}: {' · '.join(map(str, v)) if isinstance(v, list) else v}")
    for clave, titulo in (("paquetes", "Paquetes"), ("condiciones_comerciales", "Condiciones comerciales"),
                           ("reglas_escalamiento", "Reglas de escalamiento")):
        with st.expander(titulo):
            st.dataframe(cat[clave], hide_index=True, width="stretch")


def historial(f):
    st.header("La conversación y sus revisiones")
    for i, t in enumerate(f["transcript"], 1):
        rotulo(f"{i:02d} / {t['rol']} / {t['ts']}")
        st.write(t["texto"])
    if not f["transcript"]:
        st.write("Todavía no se han incorporado fragmentos.")
    with st.expander("Registro técnico de análisis"):
        st.write(f["metricas"] or "Sin llamadas al modelo en este caso.")
