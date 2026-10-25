# Recorrido de demostración

```bash
streamlit run app.py
```

Todo el catálogo es simulado. El recorrido A no necesita conexión a Claude; el B sí.

## A · Caso mixto completo, sin llamadas al modelo

Escenario sintético basado en CASO-02 (Aceros del Valle): un ERP en dos servidores que se detiene con los apagones.

1. **Casos → Abrir ejemplo sintético.** Crea una copia nueva del escenario; no modifica los diez casos originales.
2. **Reunión.** Cada hecho muestra su cita del cliente. La necesidad está resumida y la siguiente pregunta (RPO) explica qué decisión desbloquea.
3. **Alternativas.** Alojamiento (SIM-DC-01) y enlace dedicado (SIM-DC-08). Indica cantidad **1** en ambos, plazo **12 meses**, marca la revisión y **confirma**.
4. **Cierre.** **Subtotal parcial de $12,100 mensuales y $11,000 en cargos únicos**, sin IVA. El RTO de 2 horas está por debajo del estándar de 4 horas: activa **ESC-07** y la recuperación queda fuera del importe, en diseño con arquitecto.
5. **Preparar PDF y Word.** Descarga cuatro archivos (propuesta y expediente, cada uno en PDF y Word) con el mismo caso, revisión y catálogo.
6. **Casos.** Abre otro caso y regresa: la ficha se recupera completa. En **Historial** está la fuente original.
7. **Catálogo.** Consulta los 45 productos, 7 familias, paquetes, condiciones y reglas de escalamiento.

## B · Conversación en vivo con Claude

Requiere `ANTHROPIC_API_KEY` o Claude Code con sesión iniciada. Consume cuota del proveedor.

1. Abre **CASO-09 · Agencia Brava** y analiza su mensaje inicial: *«Trabajamos con archivos muy pesados entre todo el equipo y queremos empezar a usar Copilot.»*
2. Claude pregunta por la licencia actual antes de recomendar Copilot, que requiere una licencia base de Microsoft 365.
3. Captura como cita del cliente: *«Tenemos Microsoft 365 Business Standard para los 30. Copilot lo usarían unas 12 personas.»*
4. La licencia se reconoce como servicio existente y satisface la dependencia. Revisa citas y cantidades y confirma.
5. En **Cierre**, la propuesta se calcula desde el catálogo. Cambia un dato después de confirmar: la propuesta se bloquea hasta confirmar de nuevo.

Las notas del vendedor dan contexto a Claude, pero no verifican declaraciones del cliente.

## Mensajes clave

- El cliente lo dice una vez: la ficha y el expediente conservan hechos, fuentes y pendientes.
- Claude guía la conversación; el código garantiza cada precio.
- Un caso mixto entrega a la vez la parte cotizable y la parte para el arquitecto.
- Escalar a un arquitecto cuando corresponde es un resultado correcto, no un fracaso del producto.
