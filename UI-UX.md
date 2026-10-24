# Experiencia para implementación

Producto y lógica: `PRODUCT.md` y `../SPRINT-PRODUCTO.md`. Identidad: `DESIGN.md`, A — Documento anotado, elegida por Aldo. Alcance funcional: todo el catálogo, no solo los productos que aparecen en las imágenes.

## Referencias visuales

- Reunión: `../outputs/ux/identidad-a-documento.png`, base visual seleccionada (D19). Corregir la navegación activa Casos al implementarla como vista de reunión.
- Alternativas: `../outputs/ux/documento-alternativas-v1.png`, pendiente de revisión.
- Cierre: `../outputs/ux/documento-cierre-v1.png`, pendiente de revisión.

Prompts completos y estado de revisión junto a cada imagen. Las dos vistas nuevas usan una continuación explícitamente ficticia de CASO-02, registrada en `../outputs/ux/escenario-alternativas-cierre.json`. No modifica el catálogo ni las fichas de la aplicación.

## Recorrido

| Vista | Trabajo y contenido | Condición de avance |
|---|---|---|
| Casos | Crear una oportunidad o recuperar una ficha; distinguir ejemplos ficticios de casos creados por el usuario | Recuperar el estado del caso seleccionado sin mezclar clientes ni reiniciar su información |
| Reunión | Capturar cita o nota del vendedor; consultar fuente, hechos, pendientes y pregunta que desbloquea una decisión | Separar fuente e interpretación; aclarar contradicciones y datos decisivos |
| Alternativas | Recomendar y comparar cuando haya base, explicar condiciones y complementos; editar selección y cantidades | Validar unidades, requisitos y alcance; obtener confirmación explícita del vendedor antes del borrador |
| Cierre | Revisar borrador comercial y expediente interno vinculados al mismo caso y revisión | Distinguir lo calculable, lo parcial y lo sujeto a diseño; señalar pendientes antes de preparar documentos |
| Catálogo | Consultar los 45 productos y siete familias, paquetes, precios y reglas de origen | No convertir vacío en cero ni un servicio a medida en precio de lista; conservar la fuente de cada regla |

Casos y catálogo no necesitan una identidad diferente. Extender la misma composición documental y los controles de consulta, sin introducir un dashboard de indicadores.

## Qué muestran las dos vistas nuevas

La continuación ficticia especifica conservar dos servidores estándar de rack, 8U y 0.8 kVA conjuntos, una planta con enlace de 100 Mbps y recuperación deseada de dos horas. El cliente simulado acepta cotizar alojamiento y enlace como etapa separada del diseño de recuperación.

Alternativas propone SIM-DC-01 frente a la capacidad adicional de SIM-DC-02 y añade SIM-DC-08 como conectividad. La cantidad de alojamiento es una unidad para dos servidores. La pantalla mantiene pendiente la confirmación del vendedor y separa el diseño de recuperación.

Cierre ilustra una selección confirmada únicamente dentro de ese escenario de diseño. Los importes son 12,100.00 MXN mensuales sin IVA y 11,000.00 MXN de cargos únicos sin IVA. Con IVA son 14,036.00 y 12,760.00 MXN respectivamente. Se comprobaron con Decimal a partir de los valores del catálogo, sin descuentos y a 12 meses. No se ejecutó el motor de cotización actual para acreditar estas imágenes.

La recuperación no se incluye en esos importes. El expediente debe conservar el disparador ESC-07: dos horas de recuperación solicitadas están por debajo del estándar de cuatro horas. La referencia de cierre resume ese motivo, pero al implementar debe verse también el ID y la evidencia del disparador.

## Estados y continuidad

- Nuevos fragmentos conservan texto y tipo de fuente; mostrar el último resultado válido durante el análisis sin presentarlo como actualizado.
- Un fallo conserva el trabajo recuperable y explica cómo reintentar. Solo anunciar guardado tras comprobarlo.
- Dato desconocido, interpretación pendiente y contradicción tienen texto y acción de aclaración, no solo color.
- Un cambio relevante en datos, selección o catálogo señala qué confirmaciones y cálculos deben revisarse.
- Los casos mixtos pueden tener componentes calculables y arquitectura pendiente simultáneamente. La cotización parcial nunca se presenta como total de la solución.
- Las dos salidas se generan a partir de la misma revisión del caso; una exportación antigua no se actualiza por cambiar datos después.

## Entrega y criterios de revisión

Formato confirmado por Aldo en D20: PDF y Word editable de la propuesta comercial y del expediente interno. Cuatro archivos por cierre, identificados por caso y revisión. Los documentos se revisan antes de compartirlos; generar no implica enviar.

| Documento | PDF | Word |
|---|---|---|
| Propuesta comercial | Versión de esa revisión para compartir o imprimir | Texto y tablas editables del mismo alcance, componentes, condiciones e importes |
| Expediente interno | Versión de esa revisión para preventa/arquitectura | Texto y tablas editables con fuentes, pendientes, restricciones y motivos de escalamiento |

Una preparación compartida del caso alimenta los cuatro archivos; no recalcular reglas comerciales de manera diferente en cada exportación. Comprobar equivalencia de contenido entre PDF y DOCX de cada documento, manteniendo diferenciados el contenido comercial y el interno.

El Word descargado es una copia editable de esa revisión. Sus cambios externos no actualizan automáticamente la ficha ni el PDF. La importación o sincronización de Word no forma parte del alcance acordado.

Verificar los archivos finales: texto y tablas editables en DOCX; importes, IVA, cantidades, unidades, condiciones y pendientes consistentes; legibilidad y paginación sin contenido truncado en ambos formatos. Conservar de forma visible el alcance parcial y la naturaleza simulada de los datos cuando corresponda. Las plantillas serán propias de la demo mientras no se aporten las oficiales.

Comprobar el recorrido completo, los 45 productos y modelos de cobro, recuperación del caso, coherencia de documentos y confirmación del vendedor. Medir teclado, foco, contraste y adaptación a escritorio, anchos intermedios y móvil. Los ejemplos económicos no sustituyen la batería de reglas y escalamientos del catálogo.

Las imágenes son referencias de identidad y composición, no una instrucción para congelar textos, dimensiones o un único caso. Mantener hechos, alcance y claridad al adaptar contenido más largo o productos distintos.

## Implementación local integrada · 24/10/2026

Las seis vistas ya están conectadas al core y al catálogo completo. El ejemplo ejecutable no ofrece el rack completo como alternativa por defecto: la comparación aparece cuando la ficha incluye una opción sustentada. Las maquetas anteriores conservan su carácter ilustrativo y su estado de revisión.

Se ejecutó el motor del ejemplo y se comprobaron los importes de alojamiento y enlace. La confirmación guarda selección, cantidades y plazo juntos. Los cuatro documentos se habilitan con una selección vigente y un importe calculable; si falta importe o solo hay diseño pendiente, se permite descargar el expediente en dos formatos. La revisión visual de los cuatro archivos del ejemplo y las capturas de navegador se registran en REVISION-IMPLEMENTACION.md. Esto no sustituye una prueba de utilidad comercial con vendedores.
