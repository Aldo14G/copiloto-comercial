# Copiloto Comercial · Hackathon Claude

**Reto:** del primer contacto a la propuesta. Hoy el cliente explica lo mismo hasta 3 veces, espera hasta 3 semanas por una propuesta y casi siempre entra un arquitecto al levantamiento.

**Solución:** un copiloto que acompaña al vendedor *durante* la reunión. Claude escucha lo que dice el cliente, arma una ficha persistente con cada hecho citado textualmente, le dice al vendedor qué preguntar y qué decir, y propone productos del catálogo. El **código** (no Claude) valida SKUs, dependencias, cantidades, descuentos y calcula la propuesta. Cuando aplica una regla de escalamiento, el arquitecto recibe un expediente listo y el cliente no repite nada.

> Datos SIMULADOS del catálogo del hackathon. No son productos ni precios oficiales.

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
Cliente habla → Claude (catálogo + ficha) → validación en código → ficha persistente
                                                       ├─ Propuesta económica (parte estándar/configurable)
                                                       └─ Expediente para arquitecto (parte a la medida)
```

Estados: `faltan_datos`, `borrador_calculable`, `requiere_arquitecto`, `requiere_autorizacion` (pueden coexistir: casos mixtos 60/40).

## Ejecutar

Requiere Python 3.11+ y una de estas opciones para Claude:
- **Claude Code CLI** con sesión iniciada (`claude` en el PATH), usado en modo headless (`claude -p`), o
- `ANTHROPIC_API_KEY` + `pip install anthropic`.

```bash
pip install -r requirements.txt
streamlit run app.py
python -B -m unittest discover tests      # pruebas del cotizador
python -B eval/run_cases.py               # evaluación de los 10 casos
```

## Política comercial de demo (el catálogo no la define)

- Descuentos solo sobre mensualidades: plazo 24m 5% / 36m 10% + paquete 8% + volumen M365 3%; se suman por línea con tope de 10% para el vendedor.
- Soporte administrado de nube = `max(10% del consumo estimado, 12,000)`; sin consumo estimado, el total queda incompleto.
- SIM-IA-01: 2,000 conversaciones incluidas, $4 por adicional. SIM-IA-02: el límite de 100 es capacidad de usuarios, no unidades cobradas.
- Cargos únicos sin descuento; IVA 16%; vigencia 30 días.

## Estructura

- `copiloto/catalog.py` — carga del catálogo y versión (hash).
- `copiloto/claude_engine.py` — prompt, llamada a Claude y validación de su salida.
- `copiloto/ficha.py` — ficha persistente por cliente (`data/fichas/`).
- `copiloto/quote.py` — cotizador determinista.
- `copiloto/export.py` — borrador de propuesta en Markdown.
- `app.py` — interfaz Streamlit.
