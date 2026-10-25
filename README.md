# Copiloto Comercial

**Del primer contacto a la propuesta, sin que el cliente repita su historia.**

Copiloto Comercial acompaña al vendedor de soluciones de TI *durante* la reunión con el cliente. Claude convierte lo que el cliente dice en hechos citados, preguntas pertinentes y soluciones del catálogo; el código valida cada producto y calcula cada importe. Al cierre, el mismo caso produce una **propuesta comercial** y un **expediente interno** para preventa/arquitectura, en PDF y Word.

Proyecto desarrollado para el **Hackathon Claude** (ClaudeTec · Tec de Monterrey, 24 de octubre de 2026), reto *«Del primer contacto a la propuesta»*.

> Todos los productos, precios y condiciones provienen del **catálogo simulado** del hackathon. No son ofertas oficiales de ninguna empresa.

---

## El problema

| Indicador del reto | Hoy |
|---|---|
| Sesiones hasta tener el requerimiento completo | 3 en promedio |
| Tiempo para elaborar una propuesta económica | hasta 3 semanas |
| Participación de arquitectos en el levantamiento | casi siempre |

La causa no es la capacidad de los arquitectos: el conocimiento del portafolio existe, pero no llega al vendedor en el momento en que el cliente pregunta. El levantamiento queda incompleto, el cliente repite su explicación al arquitecto y la propuesta se arma a mano, aunque la mayor parte sean productos con precio de lista.

## La solución

| Momento | Qué hace el copiloto |
|---|---|
| **Reunión** | El vendedor escribe o pega lo que dice el cliente. Claude actualiza la ficha del caso: necesidad, hechos con su cita textual, pendientes y la siguiente pregunta con el motivo que la justifica. |
| **Alternativas** | Recomendación principal del catálogo y, cuando aporta valor, una alternativa comparada. El vendedor ajusta cantidades y **confirma** la solución. |
| **Cierre** | El código calcula lo que es cotizable. En un caso mixto separa el **subtotal parcial** de lo que requiere diseño. Genera propuesta y expediente vinculados al mismo caso y revisión. |
| **Continuidad** | La ficha persiste. Si entra un arquitecto, recibe el expediente con hechos, fuentes, motivos de escalamiento y pendientes: el cliente no vuelve a empezar. |

## Cómo evita inventar información

Claude interpreta y redacta; **nunca decide un precio**. Cada salida del modelo se trata como una entrada no confiable.

| Riesgo frente al cliente | Control |
|---|---|
| Precio inventado | Los importes los calcula `copiloto/quote.py` desde el catálogo, con aritmética decimal. |
| Producto inexistente | Todo SKU propuesto se valida contra el catálogo y se descarta si no existe. |
| Dato supuesto (p. ej. «1,200 empleados = 1,200 licencias») | Un hecho solo cuenta si tiene una cita textual del cliente que contiene sus cifras. Las inferencias de Claude no se usan para dimensionar. |
| Dependencia omitida (p. ej. Copilot sin licencia base) | Las reglas «requiere alguno de» se evalúan en código, incluidos los servicios que el cliente ya tiene. |
| Caso que no es estándar | Las 10 reglas de escalamiento del catálogo: las cuantitativas las evalúa el código; las cualitativas, Claude con evidencia y revisión del vendedor. |
| Borrador desactualizado | La confirmación guarda una huella de hechos, selección, plazo y catálogo. Si algo cambia, la propuesta se bloquea hasta confirmar de nuevo. |

## Probarlo

Requiere **Python 3.11+**.

```bash
git clone https://github.com/Aldo14G/copiloto-comercial.git
cd copiloto-comercial
python -m venv .venv
# Windows: .venv\Scripts\activate    ·    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

**Sin conexión a Claude:** en *Casos*, elige **Abrir ejemplo sintético** y sigue el [recorrido de demostración](docs/DEMO.md). Todo el flujo, de la reunión a los cuatro documentos, funciona sin llamadas al modelo.

**Con Claude**, la aplicación usa la primera opción disponible:

1. `ANTHROPIC_API_KEY` en el entorno (SDK oficial de Anthropic). Modelo configurable con `COPILOTO_SDK_MODEL`.
2. [Claude Code](https://claude.com/claude-code) con sesión iniciada, invocado en modo headless (`claude -p`). Modelo configurable con `COPILOTO_MODEL` (por defecto `sonnet`).

La clave nunca se guarda en el repositorio. En Streamlit Community Cloud se declara como *secret*.

## Verificación

```bash
pip install -r requirements-dev.txt
python -m unittest discover tests        # 80 pruebas, sin llamadas a Claude
python scripts/reporte_verificacion.py   # regenera VERIFICACION.md
```

| Verificado | Resultado |
|---|---|
| Pruebas automáticas | **80/80** |
| Cobertura del catálogo | 45 SKUs, 7 paquetes y 10 reglas de escalamiento; productos estándar, configurables, por consumo y a la medida |
| Casos del reto llevados al cierre (continuaciones de prueba) | **10/10** con el tipo de cierre esperado |
| Primer mensaje de los 10 casos con Claude real | 0 SKUs inventados en la cotización · 4/4 escalamientos explícitos detectados |

Detalle en [VERIFICACION.md](VERIFICACION.md) y [docs/EVALUACION.md](docs/EVALUACION.md). El impacto comercial (sesiones, semanas, participación de arquitectos) es una **hipótesis** que requiere un piloto con vendedores; no se presenta como resultado medido.

## Documentación

| Documento | Contenido |
|---|---|
| [docs/DEMO.md](docs/DEMO.md) | Recorrido de demostración paso a paso |
| [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md) | Componentes, flujo de datos, reglas de negocio y API del core |
| [docs/EVALUACION.md](docs/EVALUACION.md) | Qué se midió con Claude, cómo y con qué límites |
| [docs/EXPERIENCIA.md](docs/EXPERIENCIA.md) | Vistas, estados y entregables de la interfaz |
| [PRODUCT.md](PRODUCT.md) · [DESIGN.md](DESIGN.md) | Definición de producto y dirección visual |

## Estructura

```
app.py                  Entrada de la aplicación Streamlit
copiloto/
  claude_engine.py      Prompt, llamada a Claude y validación de su salida
  ficha.py              Caso persistente, confirmación del vendedor y cotización del caso
  quote.py              Cotizador determinista
  catalog.py            Carga del catálogo y versión (hash)
  export.py             Contenido de propuesta y expediente
  documents.py          Representación en Markdown, PDF y Word
  views.py              Vistas de la interfaz
  demo.py               Ejemplo sintético sin llamadas al modelo
data/catalogo.json      Catálogo simulado del hackathon
eval/                   Evaluación con Claude real
scripts/                Reporte de verificación y exportación de ejemplo
tests/                  Pruebas automáticas
```

## Límites conocidos

- Prototipo local de un solo vendedor: sin autenticación ni edición concurrente.
- Una cita verificada comprueba coincidencia textual, no la interpretación; el vendedor la revisa al confirmar.
- El catálogo no define cómo se acumulan los descuentos de plazo, paquete y volumen. Cuando coinciden, el borrador se bloquea hasta confirmar la política; no se inventa una regla.
- Las plantillas de propuesta son propias de la demo; el reto no incluyó plantillas oficiales.
- Editar el Word descargado no actualiza el caso.
