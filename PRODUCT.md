# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

El prototipo actual se ejecuta en navegador mediante Streamlit. Ese dato describe la implementación existente; dispositivo principal, despliegue y framework definitivo siguen abiertos. La entrega acordada es una interfaz funcional integrada al producto.

## Users

Vendedor de soluciones de TI, durante una reunión comercial y al preparar su cierre. Cliente y preventa/arquitectura son participantes del recorrido y destinatarios de información diferenciada.

## Product Purpose

Mejorar el levantamiento y evitar repetición de información entre venta, cliente y preventa. Convertir fragmentos escritos o pegados por el vendedor en un diagnóstico progresivo, preguntas pertinentes, soluciones justificadas y entregables coherentes.

Registro de decisiones confirmado con Aldo: `../SPRINT-PRODUCTO.md`, D01–D20. Este archivo resume contexto de producto para diseño; ese registro conserva el detalle y la evolución.

## Operating Context

- El vendedor escribe o pega fragmentos durante la reunión. La captura manual debe evaluarse como parte del esfuerzo de uso.
- La herramienta recomienda una solución principal y una alternativa comparada cuando aporte valor; pregunta antes de priorizar si falta información decisiva.
- El vendedor confirma solución y cantidades antes de generar el borrador económico. Esa confirmación no sustituye validaciones ni resuelve datos desconocidos.
- Un mismo caso conserva el contexto, la selección y las fuentes para continuar el trabajo.
- La organización principal es una ficha guiada: necesidad, datos, pendientes y siguiente pregunta visibles, con captura de fragmentos e historial consultable. La implementación local usa la identidad Documento anotado y las vistas Casos, Catálogo, Reunión, Alternativas, Cierre e Historial.

## Capabilities and Constraints

- Cobertura de todo el catálogo entregado: 45 productos, siete familias y paquetes, once condiciones y diez reglas generales, además de disparadores por producto y combinaciones entre familias.
- Productos estándar, configurables, por consumo y a la medida reciben su tratamiento correspondiente. Sin precio de lista se prepara diagnóstico y expediente para diseño.
- Al cierre se preparan propuesta comercial y expediente interno vinculados al mismo caso y revisión.
- Cada documento se exporta en PDF y Word editable: cuatro archivos desde una preparación coherente de la misma revisión. Editar el Word descargado no actualiza automáticamente el caso ni sus otros archivos.
- En casos mixtos se puede generar un borrador parcial para componentes definidos y separables, identificando subtotal parcial y diseño pendiente.
- Claude interpreta y redacta con sustento; el código valida y calcula desde datos y políticas resueltos. Las ambigüedades comerciales requieren tratamiento explícito.
- La implementación integrada es local; su validación está en REVISION-IMPLEMENTACION.md. No se delegó a agentes.
- La base visual A y los formatos PDF/DOCX están definidos. Nombre definitivo, ajustes de navegación y objetivo de despliegue siguen abiertos.

## Brand Commitments

Aldo pide una experiencia que evite el aspecto de CRM típico o genérico. La ficha guiada sigue confirmada. Tras las propuestas v1 y v2, eligió identidad propia y después A — Documento anotado como base visual (D19). La referencia y sus límites se registran en `DESIGN.md`; las imágenes anteriores y B/C no son direcciones seleccionadas. El nombre definitivo sigue abierto. El método acordado es maqueta en imagen antes de código.

## Evidence on Hand

- `../catalogo-simulado/`: catálogo simulado en CSV, JSON, SQLite y Excel. No contiene productos, precios o condiciones comerciales oficiales de Alestra.
- `../Materiales-del-reto-Hackathon-Claude.pdf`: planteamiento y rúbrica del reto.
- `../COBERTURA-CATALOGO.md`: extracción de alcance y lógica por producto.
- `eval/resultados.json`: evaluación de mensajes iniciales con límites documentados en el sprint; no demuestra impacto comercial completo.
- La reducción de preguntas repetidas, la completitud del levantamiento y la calidad del traspaso tienen un protocolo de evaluación previsto, todavía no ejecutado.

## Product Principles

1. Conservar lo aprendido para que el siguiente participante pueda continuar.
2. Diferenciar hechos sustentados, inferencias y pendientes; una cita presente no prueba una interpretación correcta.
3. Explicar recomendaciones y comparar alternativas solo cuando sean pertinentes y viables.
4. Distinguir lo calculable de lo sujeto a diseño y mantener coherentes las dos salidas.
5. Comprobar el catálogo completo; los casos de demo no delimitan la cobertura funcional.
