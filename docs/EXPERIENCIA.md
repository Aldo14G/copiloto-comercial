# Experiencia de uso

La interfaz organiza el trabajo como una **ficha de caso guiada**: necesidad, hechos y pendientes siempre a la vista, la siguiente pregunta destacada y la captura de fragmentos a un clic. La dirección visual está descrita en [DESIGN.md](../DESIGN.md).

## Vistas

| Vista | Trabajo que permite | Condición para avanzar |
|---|---|---|
| **Casos** | Crear una oportunidad o recuperar una ficha guardada. Los diez clientes del reto son ejemplos, no una lista cerrada. | Recuperar el caso seleccionado sin mezclar clientes ni reiniciar su información. |
| **Reunión** | Capturar una cita del cliente o una nota del vendedor; consultar fuentes, hechos, pendientes y la pregunta que desbloquea la siguiente decisión. | Separar fuente e interpretación; aclarar contradicciones y datos decisivos. |
| **Alternativas** | Ver la recomendación principal y, cuando hay base, una alternativa comparada con beneficios, límites y condiciones. Editar selección y cantidades. | Validar unidades, requisitos y alcance; confirmación explícita del vendedor. |
| **Cierre** | Revisar la propuesta comercial y el expediente interno del mismo caso y revisión; descargar PDF y Word. | Distinguir lo calculable, lo parcial y lo sujeto a diseño antes de preparar documentos. |
| **Catálogo** | Consultar los 45 productos, 7 familias, paquetes, condiciones y reglas de escalamiento. | Un precio vacío no es cero; un servicio a la medida no tiene precio de lista. |
| **Historial** | Revisar la conversación capturada y el origen de cada fragmento. | — |

## Estados

- **Análisis en curso:** el fragmento se contrasta con el catálogo; la ficha solo cambia cuando el análisis termina y se valida.
- **Fallo de análisis o guardado:** el fragmento no se incorpora y la ficha anterior se conserva; la interfaz lo explica. Solo se anuncia «guardado» cuando lo está.
- **Dato desconocido, interpretación pendiente o contradicción:** se expresan con texto y una acción de aclaración, no solo con color.
- **Cambio después de confirmar:** la interfaz señala que la confirmación quedó desactualizada y la propuesta se bloquea hasta renovarla.
- **Caso mixto:** los componentes calculables y el diseño pendiente conviven; la cotización parcial nunca se presenta como total de la solución.
- **Caso recuperado:** se restituyen contexto y estado de confirmación, no solo el historial.

## Entregables

Cada cierre produce hasta cuatro archivos identificados por caso y revisión:

| Documento | PDF | Word |
|---|---|---|
| Propuesta comercial | Versión para revisar, compartir o imprimir | Texto y tablas editables con el mismo alcance, componentes, condiciones e importes |
| Expediente interno | Versión para preventa/arquitectura | Texto y tablas editables con fuentes, pendientes, restricciones y motivos de escalamiento |

Los cuatro archivos salen de una sola preparación del caso: las reglas comerciales no se recalculan por formato. Sin importe calculable, solo se genera el expediente. Generar un documento no lo envía; el vendedor lo revisa antes de compartirlo. Editar el Word descargado no actualiza la ficha ni el PDF.

## Accesibilidad

Controles etiquetados, uso completo con teclado, foco visible, orden de lectura lógico, contraste legible y estados expresados con texto. El recorrido de demostración se comprobó en navegador a 1440, 950 y 390 px de ancho, sin desbordamiento horizontal (`tests/browser_smoke.cjs`). Esto no sustituye una auditoría completa de accesibilidad.
