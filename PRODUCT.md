# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

Aplicación de navegador construida con Streamlit.

## Users

Vendedor de soluciones de TI con perfil comercial, no técnico, durante la reunión con el cliente y al preparar el cierre. El cliente y el equipo de preventa/arquitectura participan en el recorrido y reciben información diferenciada.

## Product Purpose

Mejorar el levantamiento desde la primera reunión y evitar que el cliente repita información entre venta y preventa. El producto convierte fragmentos escritos o pegados por el vendedor en un diagnóstico progresivo, preguntas pertinentes, soluciones justificadas del catálogo y dos entregables coherentes.

## Operating Context

- El vendedor escribe o pega fragmentos durante la reunión; el esfuerzo de esa captura forma parte de la experiencia.
- La herramienta recomienda una solución principal y una alternativa comparada cuando aporta valor. Si falta información decisiva, pregunta antes de priorizar.
- El vendedor confirma solución y cantidades antes del borrador económico. La confirmación no sustituye las validaciones ni resuelve datos desconocidos.
- Un mismo caso conserva contexto, selección y fuentes para continuar el trabajo.
- Organización principal: ficha de caso guiada, con las vistas Casos, Catálogo, Reunión, Alternativas, Cierre e Historial.

## Capabilities and Constraints

- Cobertura de todo el catálogo: 45 productos, 7 familias, 7 paquetes, 11 condiciones comerciales y 10 reglas de escalamiento, además de los disparadores por producto y las combinaciones entre familias.
- Productos estándar, configurables, por consumo y a la medida reciben su tratamiento correspondiente. Sin precio de lista, se prepara diagnóstico y expediente para diseño.
- Al cierre se generan propuesta comercial y expediente interno vinculados al mismo caso y revisión, cada uno en PDF y Word editable.
- En casos mixtos se genera un borrador parcial con los componentes definidos y separables, identificando el subtotal parcial y el diseño pendiente.
- Claude interpreta y redacta con sustento; el código valida y calcula a partir del catálogo. Las ambigüedades comerciales se tratan de forma explícita, sin inventar políticas.

## Brand Commitments

Evitar el aspecto de un CRM genérico. Identidad propia «Documento anotado», descrita en `DESIGN.md`.

## Evidence on Hand

- `data/catalogo.json`: catálogo simulado del hackathon (no contiene ofertas oficiales).
- `VERIFICACION.md`: verificación automática del catálogo completo y de los 10 casos.
- `docs/EVALUACION.md`: evaluación con Claude real del primer mensaje de los 10 casos.
- La reducción de preguntas repetidas, la completitud del levantamiento y la calidad del traspaso tienen un protocolo de evaluación definido, todavía no ejecutado.

## Product Principles

1. Conservar lo aprendido para que el siguiente participante pueda continuar.
2. Diferenciar hechos sustentados, inferencias y pendientes; una cita presente no prueba una interpretación correcta.
3. Explicar las recomendaciones y comparar alternativas solo cuando sean pertinentes y viables.
4. Distinguir lo calculable de lo sujeto a diseño y mantener coherentes las dos salidas.
5. Comprobar el catálogo completo; los casos de demostración no delimitan la cobertura funcional.
