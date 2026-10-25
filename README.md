# Copiloto Comercial · Hackathon Claude

**Reto:** del primer contacto a la propuesta. Hoy el cliente explica lo mismo hasta 3 veces, espera hasta 3 semanas por una propuesta y casi siempre entra un arquitecto al levantamiento.

**Solución:** el vendedor escribe o pega fragmentos durante la reunión. Claude propone hechos con citas, preguntas y soluciones del catálogo; el vendedor revisa su interpretación y confirma el alcance. El código valida y calcula. Propuesta comercial y expediente interno conservan el contexto para reducir el retrabajo entre venta y preventa. Ese beneficio comercial todavía necesita evaluación con usuarios.

> Datos SIMULADOS del catálogo del hackathon. No son productos ni precios oficiales.

## Cómo correr la demo

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/streamlit run app.py   # Claude: ANTHROPIC_API_KEY en el entorno o Claude Code CLI; nunca en el repo
.venv/bin/python -m unittest discover tests
.venv/bin/python scripts/reporte_verificacion.py   # regenera VERIFICACION.md
```

- Resultados verificados: [VERIFICACION.md](VERIFICACION.md)
- Guion de demo: [DEMO.md](DEMO.md)
- Video (~2 min): se entrega por separado como `outputs/copiloto-demo.mp4`.

## Cómo evita inventar información

| Riesgo | Control |
|---|---|
| Precio inventado | Claude nunca calcula precios; `copiloto/quote.py` los toma del catálogo. |
| SKU inventado | `validate()` descarta cualquier SKU que no exista; el cotizador lo vuelve a rechazar. |
| Dato supuesto ("1,200 empleados = 1,200 licencias") | Cada hecho necesita una **cita textual** de la conversación; sin cita queda ⚠️ y no se usa para cotizar. |
| Dependencia omitida (Copilot sin licencia base) | Reglas `requiere_alguno_de` evaluadas en código, incluyendo servicios que el cliente ya tiene con evidencia. |
| Descuento excesivo | Tope del vendedor 10% por línea; el excedente queda como *requiere autorización*. |
| Caso que no es estándar | Escalamientos ESC-01..10: los numéricos los evalúa el código, los cualitativos Claude con evidencia. |

## Flujo

```
Fragmento del vendedor → Claude (catálogo + ficha) → validación → ficha persistente
                                                       ├─ Propuesta económica (parte estándar/configurable)
                                                       └─ Expediente para arquitecto (parte a la medida)
```

Estados: `faltan_datos`, `borrador_calculable`, `requiere_arquitecto`, `requiere_autorizacion` (pueden coexistir; no implican porcentajes fijos del alcance).

## Ejecutar

Requiere Python 3.11+ y una de estas opciones para Claude:
- **Claude Code CLI** con sesión iniciada (`claude` en el PATH), usado en modo headless (`claude -p`), o
- `ANTHROPIC_API_KEY` + `pip install anthropic`.

```bash
pip install -r requirements.txt
streamlit run app.py
python -B -m unittest discover tests      # pruebas del cotizador
```

Para ejecutar todas las pruebas instala `pip install -r requirements-dev.txt`. Para recorrer la UI sin proveedor: **Casos → Abrir ejemplo sintético → Alternativas**, indica cantidad 1 para alojamiento y enlace, revisa las fuentes y confirma. **Cierre → Preparar PDF y Word** habilita cuatro descargas del mismo caso. El ejemplo no altera los diez casos originales. Se pueden crear y recuperar casos propios.

`python -B eval/run_cases.py` hace llamadas reales a Claude y puede consumir cuota o generar cargos; no forma parte de las pruebas locales. La aplicación escucha solo en `127.0.0.1` por defecto. Es un prototipo local para un vendedor; no incluye autenticación ni coordinación de ediciones simultáneas.

## Política comercial de demo (el catálogo no la define)

- Descuentos solo sobre mensualidades: plazo 24m 5% / 36m 10% + paquete 8% + volumen M365 3%; se suman por línea con tope de 10% para el vendedor.
- Esa suma es exploratoria: si coinciden varias fuentes de descuento, el borrador queda bloqueado hasta confirmar la política de acumulación. No se presenta esa hipótesis como una regla comercial validada.
- Soporte administrado de nube = `max(10% del consumo estimado, 12,000)`; sin consumo estimado, el total queda incompleto.
- SIM-IA-01: 2,000 conversaciones incluidas, $4 por adicional. SIM-IA-02: el límite de 100 es capacidad de usuarios, no unidades cobradas.
- Cargos únicos sin descuento; IVA 16%; vigencia 30 días.

## Estructura

- `copiloto/catalog.py` — carga del catálogo y versión (hash).
- `copiloto/claude_engine.py` — prompt, llamada a Claude y validación de su salida.
- `copiloto/ficha.py` — ficha persistente por cliente (`data/fichas/`).
- `copiloto/quote.py` — cotizador determinista.
- `copiloto/export.py` — contenido común y controles de revisión de los dos entregables.
- `copiloto/documents.py` — representaciones Markdown, PDF y Word editable del mismo contenido.
- `app.py`, `copiloto/views.py`, `static/documento.css` — interfaz Documento anotado.

## API del core (para la UI)

La UI solo debe llamar a estas funciones; toda la lógica comercial vive en `copiloto/`.

| Función | Qué hace |
|---|---|
| `ficha.nueva(case_id)` / `ficha.cargar(case_id)` | Crea o recupera un caso (al cargar, revalida los hechos con las reglas vigentes) |
| `ficha.procesar_mensaje(f, texto, rol="cliente"\|"vendedor")` | Claude analiza el fragmento y actualiza la ficha; si Claude falla, la ficha no cambia. Incrementa `f["revision"]` |
| `ficha.confirmar(f, [{sku, cantidad, depende_de_diseno}], plazo=None)` | Guarda selección y plazo en una operación atómica; rechaza SKUs/cantidades inválidos |
| `ficha.cambiar_plazo(f, plazo)` | Guarda un cambio independiente de plazo e invalida la confirmación anterior |
| `ficha.estado_confirmacion(f)` | `sin_confirmar` \| `vigente` \| `desactualizada` (cambiaron hechos, existentes, plazo o catálogo) |
| `ficha.cotizacion(f, usar_confirmacion)` | Vista previa (candidatos de Claude) o borrador (selección confirmada). Devuelve `lineas`, `totales`, `parcial`, `pendiente_diseno`, `a_medida`, `bloqueos`, `avisos`, `escalamientos`, `estados`, `puede_generar_borrador` |
| `export.propuesta_md(f, q)` / `export.expediente_md(f, q)` | Los dos entregables vinculados (D10), con caso, revisión, catálogo y estado de confirmación |
| `export.archivos(f, q)` | PDF y DOCX de ambos documentos si hay borrador calculable; solo expediente en ambos formatos si falta confirmación, importe o diseño |

Campos de la ficha útiles para la UI: `resumen_necesidad`, `guion_vendedor`, `preguntas_pendientes[{pregunta, motivo, prioridad}]`, `hechos[{clave, valor, cita, origen, verificado, motivo_no_verificado}]`, `servicios_existentes`, `candidatos[{sku, cantidad, justificacion, hecho_cantidad, depende_de_diseno}]`, `alternativa{skus, resumen, beneficios, limites, cuando_conviene}`, `escalamientos[{id, estado, evidencia}]`, `contradicciones`, `alertas_validacion`, `transcript`, `confirmacion`.

## Límites conocidos

- La verificación de hechos exige una cita contigua (tolera plurales) y las cifras del valor; reconoce los números simples en palabras del motor, pero no todas las expresiones numéricas del español. **No prueba la interpretación** (p. ej., que "30" sean usuarios y no empleados). Esa revisión la hace el vendedor al confirmar.
- La evaluación (`eval/run_cases.py`) cubre solo el primer mensaje de los 10 casos.
- La combinación de descuentos es una política de demo, no una política confirmada del catálogo.
- Los disparadores cualitativos y la pertinencia de las alternativas necesitan interpretación y revisión; recorrer los 45 SKUs en pruebas no demuestra que todas sus combinaciones comerciales estén resueltas.
- Los Word descargados se editan externamente; esas ediciones no se sincronizan con el caso ni con los PDF.

## Cierre del backend · 24/10/2026

- `procesar_mensaje()` valida en una copia y persiste antes de actualizar la ficha en memoria. Fallos del proveedor, estructura JSON o disco conservan el caso anterior. Las notas del vendedor no verifican hechos del cliente.
- Cantidades positivas y finitas; unidades discretas enteras, almacenamiento en TB fraccionable. Se rechazan SKUs duplicados. La cantidad propuesta por Claude necesita un `hecho_cantidad` verificado; el vendedor puede indicar la cantidad al confirmar.
- `confirmar()` rechaza selección vacía y cantidades inválidas mediante `ValueError`; conserva las marcas de diseño. Cambiar datos, revisión o catálogo invalida la confirmación. Las confirmaciones anteriores a este endurecimiento necesitan renovarse una vez.
- Consumo o conversaciones desconocidos y contradicciones impiden el borrador. `puede_generar_borrador` es la condición para habilitar la descarga comercial. Sin ella, `propuesta_md()` entrega solo un aviso y pendientes, sin importes.
- RTO/RPO y tamaño de Oracle confirmados excluyen los componentes estándar incompatibles y sus dependientes. Los umbrales por cantidad de nueve productos también pasan a diseño. Los disparadores cualitativos siguen dependiendo de la interpretación de Claude con evidencia y revisión del vendedor.
- Ambas exportaciones exigen una cotización recién calculada del mismo caso y revisión (`ValueError` si quedó obsoleta). `expediente_md()` respeta la selección de esa cotización, incluso en vista previa.
- Verificación local: `python -B -m unittest discover tests`. Cubre los 45 SKUs, siete paquetes, cierres estándar/mixto/arquitectura y regresiones de validación y persistencia. Las llamadas a Claude en estas pruebas están simuladas.

`eval/resultados.json` conserva la evaluación real heredada de Opus, anterior a este cierre. No se repitieron llamadas pagadas ni se midió una nueva latencia; sus métricas no validan estos cambios ni conversaciones completas.

## Validación de la implementación integrada

`python -B -m unittest discover tests` incluye conservación ante fallos, revisión obsoleta, redondeo decimal, ambigüedad de descuentos, cuatro archivos nativos y recorridos de interfaz con proveedor simulado. `tests/test_core.py` conserva la cobertura de 45 SKUs y siete paquetes.

`node tests/browser_smoke.cjs http://127.0.0.1:8524` requiere Chrome y Playwright para Node (`NODE_PATH` puede apuntar al runtime de Codex). Recorre el ejemplo en navegador, descarga los cuatro archivos y comprueba navegación con teclado y ausencia de desbordamiento en anchos 1440, 950 y 390. No llama a Claude.

`python -B scripts/export_example.py ../outputs/validacion-20261024/documentos` genera el ejemplo imprimible sin red ni modificaciones en fichas existentes. La generación PDF/DOCX no requiere Word instalado; Word solo se usó para la revisión visual local de los DOCX, porque el renderizador empaquetado no encontró LibreOffice.

Resultados y límites en `REVISION-IMPLEMENTACION.md`. La evaluación histórica de Opus se conserva separada de esta verificación funcional.
