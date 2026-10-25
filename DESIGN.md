# Dirección visual: Documento anotado

## Identidad

- Un documento de trabajo que relaciona la evidencia del cliente con hechos y decisiones. Cada anotación cumple una función comprensible.
- Superficie clara con matiz vegetal, tinta verde profunda y un acento verde para el trabajo activo (`#287556` sobre `#F5F7F2`, texto `#19382D`; ver `.streamlit/config.toml` y `static/documento.css`).
- Encabezados y controles con voz condensada de trabajo (Barlow Condensed); citas y texto documental en serif legible (Source Serif 4). Ambas fuentes se incluyen localmente bajo licencia OFL en `static/fonts/`.
- Separación por ritmo, alineación y reglas cuando aportan estructura. No convertir cada dato en una tarjeta ni introducir un tablero de indicadores ajeno al trabajo.
- La navegación pesa menos que el documento.

## Gramática funcional

- **Reunión:** evidencia y anotaciones que permiten formular una pregunta pertinente.
- **Alternativas:** comparación apoyada en datos y restricciones, con confirmación del vendedor.
- **Cierre:** dos salidas vinculadas que explican alcance, importes calculables y diseño pendiente.

Se mantienen diferenciados fuente, interpretación, pendiente y selección confirmada. El color acompaña al texto, nunca lo sustituye. La numeración y los conectores solo aparecen si representan un orden o una relación reales.

## Verificación

El recorrido se comprobó en navegador a 1440, 950 y 390 px de ancho, con navegación por teclado y las cuatro descargas (`tests/browser_smoke.cjs`). No equivale a una auditoría completa de accesibilidad ni a una validación de utilidad con vendedores.
