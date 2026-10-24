# Recorrido local de demostración

Ejecutar `python -m streamlit run app.py`. Todo el catálogo es simulado.

## Sin llamadas al modelo

1. **Casos → Abrir ejemplo sintético.** Crea una copia nueva del escenario de diseño; no reinicia fichas anteriores.
2. **Reunión.** Mostrar fuente, hechos con cita, necesidad y pregunta de RPO pendiente. La etiqueta del ejemplo aclara que no hubo análisis de Claude.
3. **Alternativas.** Revisar alojamiento y enlace. No se inventa una segunda opción: aparece solo cuando la ficha la sustenta. Indicar cantidad **1** en ambos componentes, plazo **12** meses, marcar revisión y confirmar.
4. **Cierre.** Mostrar **subtotal parcial de $12,100 mensuales y $11,000 únicos sin IVA**. El RTO de 2 horas exige arquitectura (ESC-07); el subtotal no incluye diseño de recuperación.
5. Revisar propuesta y expediente; **Preparar PDF y Word**, descargar cuatro archivos del mismo caso/revisión/catálogo.
6. **Casos.** Abrir otro caso y volver al ejemplo guardado. Mostrar la fuente en **Historial**.
7. **Catálogo.** Consultar los 45 productos, siete familias, paquetes, condiciones y reglas.

## Con proveedor disponible (consume cuota o puede generar cargos)

Abrir CASO-09 y analizar su mensaje inicial. Incorporar como cita del cliente: «Tenemos Microsoft 365 Business Standard para los 30. Copilot lo usarían unas 12 personas». Revisar las citas y cantidades; confirmar antes de generar un borrador. Las notas del vendedor son contexto y no verifican declaraciones del cliente.

No presentar el ejemplo sintético ni las pruebas con proveedor simulado como una evaluación de Claude. `eval/resultados.json` contiene resultados históricos del primer mensaje de diez casos; no demuestra reducción de tiempos, menos preguntas repetidas ni latencia actual. Esos beneficios requieren una evaluación posterior.
