# Evaluación con Claude

Las pruebas automáticas del repositorio usan un proveedor simulado y verifican la lógica de forma determinista ([VERIFICACION.md](../VERIFICACION.md)). Este documento cubre lo que se midió con **Claude real** y lo que todavía no.

## Qué se midió

`eval/run_cases.py` envía el **primer mensaje** de cada uno de los 10 casos del reto a Claude, valida la respuesta con las mismas reglas de la aplicación y cotiza a los candidatos resultantes. Resultados en `eval/resultados.json`.

| Métrica | Resultado |
|---|---|
| SKUs inventados que llegaron a la cotización | **0** |
| SKUs inventados propuestos por Claude (filtrados) | 0 |
| Escalamientos explícitos detectados | **4/4** (CNBV en CASO-03; Oracle de 6 TB en CASO-06; nube híbrida Azure + centro de datos en CASO-08; datos clínicos en CASO-10) |
| Escalamientos confirmados sin sustento | 0 |
| Hechos descartados por la validación | 6 de 30 |
| Casos con alternativa comparada | 1 de 10 |

**Escalamientos posibles.** Además de los confirmados, Claude marca como *posibles* los que dependen de un dato que todavía falta: CASO-01 (clínica dental) queda en posible ESC-04 hasta saber si guardan expedientes de pacientes; CASO-05 (restaurantes) en posible ESC-05 hasta saber si las reservas viven en un sistema propio. Es el comportamiento esperado: preguntar antes de escalar.

**Hechos descartados.** Los 6 descartes fueron intentos de registrar como hecho del cliente el número de empleados de la ficha del caso, que el cliente no dijo en la conversación. La validación los rechazó, así que no se usaron para dimensionar licencias.

## Cómo reproducir

```bash
python eval/run_cases.py
```

Hace llamadas reales a Claude y consume cuota del proveedor. Los disparadores esperados por caso están definidos en el propio script y fueron revisados manualmente a partir del mensaje inicial.

## Límites

- Solo cubre el **primer mensaje** de cada caso. No evalúa conversaciones completas ni la exactitud de propuestas finales.
- Los resultados corresponden a la versión del prompt vigente al momento de la corrida. Los cambios posteriores del motor están cubiertos por las pruebas automáticas, pero no se repitió la medición con Claude.
- Diez casos son una muestra pequeña; las cifras no son una garantía fuera de esa batería.
- Latencia observada: entre 20 y 45 segundos por turno según el tamaño de la respuesta. Es el principal punto a mejorar para el uso en plena reunión.

## Pendiente de medir

El reto plantea tres indicadores: sesiones hasta el requerimiento completo, tiempo de propuesta y participación de arquitectos. Medir el efecto del copiloto sobre ellos requiere:

1. Continuaciones explícitas de los 10 casos, para que cliente y respuestas sean comparables entre corridas.
2. Una comparación entre un levantamiento manual y uno asistido con los mismos materiales, registrando tiempo, preguntas repetidas, completitud del levantamiento y calidad del traspaso al arquitecto.
3. Un piloto con vendedores reales.

Hasta entonces, el impacto en esos indicadores es una hipótesis del producto, no un resultado.
