# Arquitectura

## Principio de diseño

**Claude razona; el código decide los números.** Claude entiende lenguaje natural, extrae hechos, prioriza preguntas y redacta explicaciones. El código valida todo lo que Claude propone contra el catálogo y calcula cada importe. La interfaz no contiene lógica comercial.

```
Fragmento del vendedor
        │
        ▼
claude_engine.ask()  ──►  claude_engine.validate()  ──►  ficha (persistente, con revisión)
 catálogo completo          SKUs, reglas, citas,                 │
 + ficha actual             cifras, alternativa                  ▼
                                                   confirmación del vendedor (huella)
                                                                 │
                                                                 ▼
                                                   ficha.cotizacion() → quote.cotizar()
                                                                 │
                                       ┌─────────────────────────┴─────────────────────────┐
                                       ▼                                                   ▼
                          Propuesta comercial (PDF · Word)                 Expediente interno (PDF · Word)
                          importes calculables, subtotal parcial           hechos y fuentes, escalamientos,
                                                                           pendientes, conversación
```

## Componentes

| Módulo | Responsabilidad |
|---|---|
| `copiloto/catalog.py` | Carga `data/catalogo.json`, indexa por SKU y calcula su hash (versión del catálogo en cada documento). Genera la versión compacta del catálogo para el prompt, con todas las columnas de los 45 productos. |
| `copiloto/claude_engine.py` | Construye el prompt (catálogo, ficha y conversación reciente), llama a Claude y valida la respuesta. Trata la salida del modelo como entrada no confiable. |
| `copiloto/ficha.py` | Caso persistente en `data/fichas/`, escrito de forma atómica. Revisiones, confirmación del vendedor y cotización del caso con los escalamientos que dependen de hechos. |
| `copiloto/quote.py` | Cotizador determinista con aritmética `Decimal`. |
| `copiloto/export.py` | Contenido estructurado de los dos entregables, compartido por todos los formatos. |
| `copiloto/documents.py` | Representación del mismo contenido en Markdown, PDF (ReportLab) y Word editable (python-docx). |
| `copiloto/views.py`, `app.py` | Interfaz Streamlit: Casos, Catálogo, Reunión, Alternativas, Cierre e Historial. |
| `copiloto/demo.py` | Ejemplo sintético que recorre el flujo completo sin llamar al modelo. |

## Proveedor de Claude

`claude_engine.ask()` usa el SDK de Anthropic si existe `ANTHROPIC_API_KEY` (modelo en `COPILOTO_SDK_MODEL`). Si no, usa Claude Code en modo headless (`claude -p`) con un prompt de sistema propio, sin herramientas ni configuración del usuario (modelo en `COPILOTO_MODEL`, por defecto `sonnet`). El *extended thinking* está desactivado por defecto (`COPILOTO_THINKING`) porque la tarea es extracción estructurada y la latencia importa durante la reunión.

## Validación de la salida de Claude

| Elemento | Regla |
|---|---|
| Hechos | Válidos solo si la cita aparece en lo que dijo el cliente (tolera plurales y cambios menores, no paráfrasis) y contiene las cifras del valor, incluidos números simples escritos con palabras. Las inferencias de Claude y las notas del vendedor no verifican hechos del cliente. |
| SKUs | Los candidatos, servicios existentes y alternativas con SKUs inexistentes se descartan y se registran como alerta. |
| Escalamientos | Solo se aceptan identificadores ESC-01 a ESC-10, como *confirmado* (con evidencia) o *posible* (por confirmar). |
| Cantidades | Una cantidad propuesta por Claude necesita un hecho verificado que la sustente; si no, la indica el vendedor al confirmar. |
| Fallos | Si Claude falla o devuelve una estructura inválida, la ficha no cambia. Una respuesta parcial no borra pendientes ni contradicciones previas. |

Al cargar una ficha guardada, sus hechos se revalidan con las reglas vigentes.

## Reglas de negocio

**Cotización** (`copiloto/quote.py`)

- Dependencias «requiere alguno de» evaluadas contra la selección y los servicios existentes verificados.
- Cantidades mínimas y máximas del catálogo; unidades discretas enteras y almacenamiento en TB fraccionable.
- Productos por consumo (AWS, Azure, OCI): requieren consumo estimado; sin él, el total queda incompleto.
- Soporte administrado de nube: `max(10% del consumo, 12,000 MXN)`.
- SIM-IA-01: 2,000 conversaciones incluidas y $4 por conversación adicional. SIM-IA-02: el límite de 100 se refiere a usuarios, no a unidades cobradas.
- Productos a la medida: nunca reciben precio; activan ESC-01 y pasan al expediente.
- Descuentos solo sobre mensualidades. El vendedor aplica hasta 10% y el excedente queda como *requiere autorización*. Como el catálogo no define cómo se acumulan plazo, paquete y volumen, coincidir varias fuentes **bloquea el borrador** hasta aclarar la política.
- Cargos únicos sin descuento; IVA 16%; vigencia de 30 días.

**Cierre parcial**

- Un componente marcado como dependiente de diseño, o cuya única dependencia satisfecha está sujeta a diseño o es a la medida, no se suma: queda en `pendiente_diseno` y el importe se rotula **subtotal parcial**.
- Requisitos confirmados que exceden la capacidad estándar sacan el componente del importe: DRaaS con RTO menor a 4 h o RPO menor a 15 min; base Oracle administrada de más de 2 TB.
- Escalamientos que el código evalúa a partir de hechos: ESC-07 (RTO, RPO, disponibilidad), ESC-08 (Oracle de más de 2 TB), ESC-02, ESC-03 y ESC-09 (umbrales de cantidad e importe), ESC-01 (a la medida). Los cualitativos (ESC-04, 05, 06, 10) los propone Claude con evidencia.
- Las contradicciones abiertas bloquean el borrador.

**Confirmación del vendedor**

`ficha.confirmar()` guarda selección, cantidades y plazo con una huella de hechos, servicios existentes, plazo y catálogo. `estado_confirmacion()` devuelve `sin_confirmar`, `vigente` o `desactualizada`. La propuesta comercial solo se habilita con una confirmación vigente, un importe calculable y sin bloqueos (`puede_generar_borrador`).

**Entregables**

Ambos documentos salen de la misma cotización y llevan caso, revisión, versión del catálogo y estado de confirmación. Una exportación con una cotización obsoleta se rechaza. Sin importe calculable, solo se genera el expediente.

Estados del caso, que pueden coexistir: `faltan_datos`, `borrador_calculable`, `requiere_arquitecto`, `requiere_autorizacion`.

## API del core

La interfaz solo usa estas funciones.

| Función | Descripción |
|---|---|
| `ficha.nueva(case_id)` · `ficha.cargar(case_id)` | Crea o recupera un caso |
| `ficha.procesar_mensaje(f, texto, rol="cliente" \| "vendedor")` | Analiza un fragmento con Claude e incrementa la revisión; si falla, la ficha no cambia |
| `ficha.confirmar(f, seleccion, plazo=None)` | Confirma selección y plazo en una operación atómica; rechaza SKUs duplicados o inexistentes y cantidades inválidas |
| `ficha.cambiar_plazo(f, plazo)` | Cambia el plazo e invalida la confirmación anterior |
| `ficha.estado_confirmacion(f)` | `sin_confirmar` · `vigente` · `desactualizada` |
| `ficha.cotizacion(f, usar_confirmacion)` | Vista previa (candidatos de Claude) o borrador (selección confirmada) |
| `export.propuesta_md(f, q)` · `export.expediente_md(f, q)` | Entregables en Markdown |
| `export.archivos(f, q)` | PDF y Word de los entregables disponibles |

`cotizacion()` devuelve `lineas`, `totales`, `parcial`, `pendiente_diseno`, `a_medida`, `bloqueos`, `avisos`, `escalamientos`, `estados`, `confirmacion` y `puede_generar_borrador`.

Campos principales de la ficha: `resumen_necesidad`, `guion_vendedor`, `preguntas_pendientes`, `hechos`, `servicios_existentes`, `candidatos`, `alternativa`, `escalamientos`, `contradicciones`, `alertas_validacion`, `transcript`, `confirmacion`, `revision`.

## Pruebas

| Archivo | Cobertura |
|---|---|
| `tests/test_quote.py` | Cotizador: dependencias, topes de descuento, consumo, conversaciones adicionales |
| `tests/test_core.py` | Los 45 SKUs y los 7 paquetes; cierre parcial; validación de citas; confirmación |
| `tests/test_backend.py` | Entradas inválidas, citas, umbrales por producto, persistencia atómica, fallos de Claude o disco, cierre mixto y cambios de catálogo |
| `tests/test_completion.py` | Respuestas parciales, plazo y confirmación, redondeo decimal, acumulación de descuentos, cuatro archivos y recorridos de interfaz |
| `tests/test_tercer_tramo.py` | Cierre de punta a punta (mismos importes en PDF y Word), precios del proveedor ignorados y contenido de la interfaz |
| `tests/test_verificacion_integral.py` | Los 10 casos del reto llevados al cierre con continuaciones de prueba |
| `tests/browser_smoke.cjs` | Recorrido en Chrome con Playwright: ejemplo, confirmación, descargas, teclado y anchos 1440/950/390 |

Ninguna prueba automática llama a Claude. La evaluación con el modelo real está en [EVALUACION.md](EVALUACION.md).
