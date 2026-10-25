# Copiloto Comercial Â· Hackathon Claude

**Reto:** del primer contacto a la propuesta. Hoy el cliente explica lo mismo hasta 3 veces, espera hasta 3 semanas por una propuesta y casi siempre entra un arquitecto al levantamiento.

**SoluciÃ³n:** el vendedor escribe o pega fragmentos durante la reuniÃ³n. Claude propone hechos con citas, preguntas y soluciones del catÃ¡logo; el vendedor revisa su interpretaciÃ³n y confirma el alcance. El cÃ³digo valida y calcula. Propuesta comercial y expediente interno conservan el contexto para reducir el retrabajo entre venta y preventa. Ese beneficio comercial todavÃ­a necesita evaluaciÃ³n con usuarios.

> Datos SIMULADOS del catÃ¡logo del hackathon. No son productos ni precios oficiales.

## CÃ³mo correr la demo

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/streamlit run app.py   # Claude: ANTHROPIC_API_KEY en el entorno o Claude Code CLI; nunca en el repo
.venv/bin/python -m unittest discover tests
.venv/bin/python scripts/reporte_verificacion.py   # regenera VERIFICACION.md
```

- Resultados verificados: [VERIFICACION.md](VERIFICACION.md)
- Guion de demo: [DEMO.md](DEMO.md)
- Video (~2 min): se entrega por separado como `docs/copiloto-demo.mp4`.

## CÃ³mo evita inventar informaciÃ³n

| Riesgo | Control |
|---|---|
| Precio inventado | Claude nunca calcula precios; `copiloto/quote.py` los toma del catÃ¡logo. |
| SKU inventado | `validate()` descarta cualquier SKU que no exista; el cotizador lo vuelve a rechazar. |
| Dato supuesto ("1,200 empleados = 1,200 licencias") | Cada hecho necesita una **cita textual** de la conversaciÃ³n; sin cita queda âš ï¸ y no se usa para cotizar. |
| Dependencia omitida (Copilot sin licencia base) | Reglas `requiere_alguno_de` evaluadas en cÃ³digo, incluyendo servicios que el cliente ya tiene con evidencia. |
| Descuento excesivo | Tope del vendedor 10% por lÃ­nea; el excedente queda como *requiere autorizaciÃ³n*. |
| Caso que no es estÃ¡ndar | Escalamientos ESC-01..10: los numÃ©ricos los evalÃºa el cÃ³digo, los cualitativos Claude con evidencia. |

## Flujo

```
Fragmento del vendedor â†’ Claude (catÃ¡logo + ficha) â†’ validaciÃ³n â†’ ficha persistente
                                                       â”œâ”€ Propuesta econÃ³mica (parte estÃ¡ndar/configurable)
                                                       â””â”€ Expediente para arquitecto (parte a la medida)
```

Estados: `faltan_datos`, `borrador_calculable`, `requiere_arquitecto`, `requiere_autorizacion` (pueden coexistir; no implican porcentajes fijos del alcance).

## Ejecutar

Requiere Python 3.11+ y una de estas opciones para Claude:
- **Claude Code CLI** con sesiÃ³n iniciada (`claude` en el PATH), usado en modo headless (`claude -p`), o
- `ANTHROPIC_API_KEY` + `pip install anthropic`.

```bash
pip install -r requirements.txt
streamlit run app.py
python -B -m unittest discover tests      # pruebas del cotizador
```

Para ejecutar todas las pruebas instala `pip install -r requirements-dev.txt`. Para recorrer la UI sin proveedor: **Casos â†’ Abrir ejemplo sintÃ©tico â†’ Alternativas**, indica cantidad 1 para alojamiento y enlace, revisa las fuentes y confirma. **Cierre â†’ Preparar PDF y Word** habilita cuatro descargas del mismo caso. El ejemplo no altera los diez casos originales. Se pueden crear y recuperar casos propios.

`python -B eval/run_cases.py` hace llamadas reales a Claude y puede consumir cuota o generar cargos; no forma parte de las pruebas locales. La aplicaciÃ³n escucha solo en `127.0.0.1` por defecto. Es un prototipo local para un vendedor; no incluye autenticaciÃ³n ni coordinaciÃ³n de ediciones simultÃ¡neas.

## PolÃ­tica comercial de demo (el catÃ¡logo no la define)

- Descuentos solo sobre mensualidades: plazo 24m 5% / 36m 10% + paquete 8% + volumen M365 3%; se suman por lÃ­nea con tope de 10% para el vendedor.
- Esa suma es exploratoria: si coinciden varias fuentes de descuento, el borrador queda bloqueado hasta confirmar la polÃ­tica de acumulaciÃ³n. No se presenta esa hipÃ³tesis como una regla comercial validada.
- Soporte administrado de nube = `max(10% del consumo estimado, 12,000)`; sin consumo estimado, el total queda incompleto.
- SIM-IA-01: 2,000 conversaciones incluidas, $4 por adicional. SIM-IA-02: el lÃ­mite de 100 es capacidad de usuarios, no unidades cobradas.
- Cargos Ãºnicos sin descuento; IVA 16%; vigencia 30 dÃ­as.

## Estructura

- `copiloto/catalog.py` â€” carga del catÃ¡logo y versiÃ³n (hash).
- `copiloto/claude_engine.py` â€” prompt, llamada a Claude y validaciÃ³n de su salida.
- `copiloto/ficha.py` â€” ficha persistente por cliente (`data/fichas/`).
- `copiloto/quote.py` â€” cotizador determinista.
- `copiloto/export.py` â€” contenido comÃºn y controles de revisiÃ³n de los dos entregables.
- `copiloto/documents.py` â€” representaciones Markdown, PDF y Word editable del mismo contenido.
- `app.py`, `copiloto/views.py`, `static/documento.css` â€” interfaz Documento anotado.

## API del core (para la UI)

La UI solo debe llamar a estas funciones; toda la lÃ³gica comercial vive en `copiloto/`.

| FunciÃ³n | QuÃ© hace |
|---|---|
| `ficha.nueva(case_id)` / `ficha.cargar(case_id)` | Crea o recupera un caso (al cargar, revalida los hechos con las reglas vigentes) |
| `ficha.procesar_mensaje(f, texto, rol="cliente"\|"vendedor")` | Claude analiza el fragmento y actualiza la ficha; si Claude falla, la ficha no cambia. Incrementa `f["revision"]` |
| `ficha.confirmar(f, [{sku, cantidad, depende_de_diseno}], plazo=None)` | Guarda selecciÃ³n y plazo en una operaciÃ³n atÃ³mica; rechaza SKUs/cantidades invÃ¡lidos |
| `ficha.cambiar_plazo(f, plazo)` | Guarda un cambio independiente de plazo e invalida la confirmaciÃ³n anterior |
| `ficha.estado_confirmacion(f)` | `sin_confirmar` \| `vigente` \| `desactualizada` (cambiaron hechos, existentes, plazo o catÃ¡logo) |
| `ficha.cotizacion(f, usar_confirmacion)` | Vista previa (candidatos de Claude) o borrador (selecciÃ³n confirmada). Devuelve `lineas`, `totales`, `parcial`, `pendiente_diseno`, `a_medida`, `bloqueos`, `avisos`, `escalamientos`, `estados`, `puede_generar_borrador` |
| `export.propuesta_md(f, q)` / `export.expediente_md(f, q)` | Los dos entregables vinculados (D10), con caso, revisiÃ³n, catÃ¡logo y estado de confirmaciÃ³n |
| `export.archivos(f, q)` | PDF y DOCX de ambos documentos si hay borrador calculable; solo expediente en ambos formatos si falta confirmaciÃ³n, importe o diseÃ±o |

Campos de la ficha Ãºtiles para la UI: `resumen_necesidad`, `guion_vendedor`, `preguntas_pendientes[{pregunta, motivo, prioridad}]`, `hechos[{clave, valor, cita, origen, verificado, motivo_no_verificado}]`, `servicios_existentes`, `candidatos[{sku, cantidad, justificacion, hecho_cantidad, depende_de_diseno}]`, `alternativa{skus, resumen, beneficios, limites, cuando_conviene}`, `escalamientos[{id, estado, evidencia}]`, `contradicciones`, `alertas_validacion`, `transcript`, `confirmacion`.

## LÃ­mites conocidos

- La verificaciÃ³n de hechos exige una cita contigua (tolera plurales) y las cifras del valor; reconoce los nÃºmeros simples en palabras del motor, pero no todas las expresiones numÃ©ricas del espaÃ±ol. **No prueba la interpretaciÃ³n** (p. ej., que "30" sean usuarios y no empleados). Esa revisiÃ³n la hace el vendedor al confirmar.
- La evaluaciÃ³n (`eval/run_cases.py`) cubre solo el primer mensaje de los 10 casos.
- La combinaciÃ³n de descuentos es una polÃ­tica de demo, no una polÃ­tica confirmada del catÃ¡logo.
- Los disparadores cualitativos y la pertinencia de las alternativas necesitan interpretaciÃ³n y revisiÃ³n; recorrer los 45 SKUs en pruebas no demuestra que todas sus combinaciones comerciales estÃ©n resueltas.
- Los Word descargados se editan externamente; esas ediciones no se sincronizan con el caso ni con los PDF.

## Cierre del backend Â· 24/10/2026

- `procesar_mensaje()` valida en una copia y persiste antes de actualizar la ficha en memoria. Fallos del proveedor, estructura JSON o disco conservan el caso anterior. Las notas del vendedor no verifican hechos del cliente.
- Cantidades positivas y finitas; unidades discretas enteras, almacenamiento en TB fraccionable. Se rechazan SKUs duplicados. La cantidad propuesta por Claude necesita un `hecho_cantidad` verificado; el vendedor puede indicar la cantidad al confirmar.
- `confirmar()` rechaza selecciÃ³n vacÃ­a y cantidades invÃ¡lidas mediante `ValueError`; conserva las marcas de diseÃ±o. Cambiar datos, revisiÃ³n o catÃ¡logo invalida la confirmaciÃ³n. Las confirmaciones anteriores a este endurecimiento necesitan renovarse una vez.
- Consumo o conversaciones desconocidos y contradicciones impiden el borrador. `puede_generar_borrador` es la condiciÃ³n para habilitar la descarga comercial. Sin ella, `propuesta_md()` entrega solo un aviso y pendientes, sin importes.
- RTO/RPO y tamaÃ±o de Oracle confirmados excluyen los componentes estÃ¡ndar incompatibles y sus dependientes. Los umbrales por cantidad de nueve productos tambiÃ©n pasan a diseÃ±o. Los disparadores cualitativos siguen dependiendo de la interpretaciÃ³n de Claude con evidencia y revisiÃ³n del vendedor.
- Ambas exportaciones exigen una cotizaciÃ³n reciÃ©n calculada del mismo caso y revisiÃ³n (`ValueError` si quedÃ³ obsoleta). `expediente_md()` respeta la selecciÃ³n de esa cotizaciÃ³n, incluso en vista previa.
- VerificaciÃ³n local: `python -B -m unittest discover tests`. Cubre los 45 SKUs, siete paquetes, cierres estÃ¡ndar/mixto/arquitectura y regresiones de validaciÃ³n y persistencia. Las llamadas a Claude en estas pruebas estÃ¡n simuladas.

`eval/resultados.json` conserva la evaluaciÃ³n real heredada de Opus, anterior a este cierre. No se repitieron llamadas pagadas ni se midiÃ³ una nueva latencia; sus mÃ©tricas no validan estos cambios ni conversaciones completas.

## ValidaciÃ³n de la implementaciÃ³n integrada

`python -B -m unittest discover tests` incluye conservaciÃ³n ante fallos, revisiÃ³n obsoleta, redondeo decimal, ambigÃ¼edad de descuentos, cuatro archivos nativos y recorridos de interfaz con proveedor simulado. `tests/test_core.py` conserva la cobertura de 45 SKUs y siete paquetes.

`node tests/browser_smoke.cjs http://127.0.0.1:8524` requiere Chrome y Playwright para Node (`NODE_PATH` puede apuntar al runtime de Codex). Recorre el ejemplo en navegador, descarga los cuatro archivos y comprueba navegaciÃ³n con teclado y ausencia de desbordamiento en anchos 1440, 950 y 390. No llama a Claude.

`python -B scripts/export_example.py ../outputs/validacion-20261024/documentos` genera el ejemplo imprimible sin red ni modificaciones en fichas existentes. La generaciÃ³n PDF/DOCX no requiere Word instalado; Word solo se usÃ³ para la revisiÃ³n visual local de los DOCX, porque el renderizador empaquetado no encontrÃ³ LibreOffice.

Resultados y lÃ­mites en `REVISION-IMPLEMENTACION.md`. La evaluaciÃ³n histÃ³rica de Opus se conserva separada de esta verificaciÃ³n funcional.
