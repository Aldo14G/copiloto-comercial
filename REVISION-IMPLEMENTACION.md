# Revisión de la implementación · 24/10/2026

## Punto de partida y resultado

Se contrastaron el código local, `Seguimiento.txt`, el contrato del README y las decisiones del sprint. La corrida heredada de **53 pruebas** se reprodujo antes de modificar la implementación. La evaluación de Opus en `eval/resultados.json` se conservó; no se repitieron llamadas pagadas a Claude.

La implementación local integra creación y recuperación de casos, captura de fragmentos, consulta del catálogo, selección confirmada y cierre con PDF/Word de propuesta y expediente. Mantiene Streamlit y el core existente. No hubo delegación, commit, publicación ni despliegue.

## Hallazgos corregidos

| Hallazgo | Cambio y comprobación |
|---|---|
| Una respuesta parcial podía vaciar pendientes o contradicciones | Se conservan campos omitidos; se rechaza un análisis sin hechos/candidatos. Regresiones con respuesta parcial y vacía. Las contradicciones anteriores también entran en el prompt. |
| Un reemplazo fallido podía cambiar la fecha en memoria | Se actualiza el estado después del reemplazo atómico; se prueba conservación de fecha, archivo y limpieza temporal. |
| Confirmación dependiente de interpretar mensajes de error en español | Regla canónica de cantidad compartida por cotización y confirmación; no se analizan textos de error para decidir validez. |
| Multiplicación binaria antes del redondeo monetario | Productos y descuentos se calculan con Decimal; prueba del caso 0.1711 TB × 1,850 = 316.54, además de límites numéricos. |
| Acumulación de descuentos sin política del catálogo | Coincidir fuentes de descuento bloquea el borrador; los importes exploratorios no constituyen una política validada. |
| Ajustar plazo podía perder cantidades en edición | Plazo, selección y confirmación se guardan juntos; formulario nativo en lugar de varios guardados y ejecuciones reactivas. |
| El prompt omitía SLA, plazos y otras columnas | Esquema JSON una sola vez y filas con todas las columnas de los 45 productos. |
| Solo existían descargas Markdown | Dos contenidos estructurados alimentan Markdown, PDF y Word. Sin convertir Markdown a Word ni duplicar cálculos por formato. |
| Interfaz anterior sin la identidad elegida ni casos nuevos | Seis vistas con Documento anotado, fuentes locales OFL, captura con origen, recuperación y consulta de todo el catálogo. |
| Simulación de cliente añadía llamadas al modelo | Se retiró el helper sin consumidores. El ejemplo sintético separado no llama al proveedor ni reinicia casos existentes. |

La revisión siguió Ponytail full y Thermo-Nuclear Code Quality Review. Se mantuvo la lógica en su módulo canónico; la UI no calcula precios. El archivo mayor de aplicación es `copiloto/views.py` (262 líneas); `app.py` tiene 32. No se añadieron frameworks de frontend, capas de repositorio ni servicios nuevos. Las dependencias de producción añadidas son las necesarias para PDF y Word: ReportLab y python-docx.

## Evidencia ejecutada

| Comprobación | Resultado |
|---|---|
| `python -B -m unittest discover tests` | **74/74** (Streamlit 1.56 y 1.66), 7 de cierre en `tests/test_tercer_tramo.py`. Proveedor simulado, sin llamadas pagadas. |
| Cobertura heredada del catálogo | 45 SKUs y siete paquetes; mínimos, dependencias, consumo, escalamientos y cierres mixtos. No acredita todas las combinaciones comerciales posibles. |
| Nuevas regresiones e integración | Conservación ante fallos, respuesta incompleta, plazo y confirmación, redondeo, descuentos ambiguos, documentos y creación/recuperación de casos. |
| `node tests/browser_smoke.cjs http://127.0.0.1:8524` | Chrome: creación de caso, ejemplo mixto, confirmación, cuatro descargas y navegación por teclado. Sin llamadas al proveedor. |
| Capturas y geometría | Seis capturas; Reunión a 1440/950/390, Alternativas a 1440 y Cierre a 1440/390. Sin desbordamiento horizontal ni errores JavaScript en ese recorrido. |
| `impeccable detect --json app.py copiloto/views.py static/documento.css` | `[]`; comprobación estática, no certificación de accesibilidad. |
| Documentos del ejemplo | Dos PDF y dos DOCX; cada uno de una página en la muestra, todas las páginas renderizadas e inspeccionadas. Word conserva texto y tablas editables. |
| Importe del ejemplo | Mensual 12,100.00 / con IVA 14,036.00; único 11,000.00 / con IVA 12,760.00 MXN. Subtotal parcial; ESC-07 y recuperación excluida. |
| `git diff --check` | Pasa; avisos de conversión LF/CRLF de Git sin errores de whitespace. |

El renderizador DOCX empaquetado no encontró LibreOffice. Se renderizaron ambos DOCX con una instancia oculta de Microsoft Word y se inspeccionaron sus PDF de comprobación. La aplicación no necesita Word para generar DOCX. Las pruebas de texto largo comprueban paginación PDF; la muestra visual no sustituye revisar documentos arbitrarios de cualquier longitud.

AppTest conserva nodos antiguos cuando el formulario de creación provoca `st.rerun`. La prueba de recuperación abre una sesión nueva después de crear el caso; el navegador real verifica la creación directamente. No se usa ese detalle del arnés para modificar reglas de negocio.

Evidencia local: `../outputs/validacion-20261024/navegador/resultado.json`, capturas en esa carpeta y documentos en `../outputs/validacion-20261024/documentos/`. El script `scripts/export_example.py` permite regenerar los cuatro entregables sin red ni cambios en las fichas originales.

## Integridad y límites

Catálogo: SHA256 `14a5451ca84f67a6d06575dbfe9606530f49752a7b949f85f66ff24a1a929a17`. Conserva 7 familias, 45 productos, 7 paquetes, 11 condiciones, 10 reglas y 10 casos ficticios. No se modificó el catálogo en esta revisión.

La evaluación histórica de Opus mantiene SHA256 `d85012261486d1a928aac435392bdce269be8775f57da81f5667944a11efdca2`. La ficha preexistente CASO-01 no fue reiniciada; se crean copias nuevas para las pruebas de navegador.

Una cita encontrada comprueba coincidencia textual, no interpretación semántica. El vendedor revisa cantidades, pertinencia, diseño y fuentes antes del borrador. Los disparadores cualitativos dependen de Claude y de esa revisión. El soporte de números en palabras es limitado.

La aplicación es local para un vendedor y escucha en loopback. No se implementaron autenticación multiusuario ni control de ediciones concurrentes. Las fuentes se conservan en disco local; editar un Word no sincroniza la ficha. Las condiciones del catálogo son simuladas y las plantillas no son ofertas oficiales de Alestra.

Pendientes de evaluación: latencia y calidad de Claude con el prompt actualizado; conversaciones completas y utilidad con vendedores; revisión comercial de descuentos y alcance separable; auditoría completa de accesibilidad. Las pruebas de software no demuestran reducción de semanas, retrabajo o preguntas repetidas.
