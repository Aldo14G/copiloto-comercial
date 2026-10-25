# Verificación

Generado con `python scripts/reporte_verificacion.py`. Sin llamadas a Claude: proveedor simulado.

## Verificado
- Pruebas automáticas: **80/80** pasan (`python -m unittest discover tests`).
- Catálogo `14a5451ca84f`: 45 SKUs, 7 paquetes, 10 reglas de escalamiento, 10 casos.
- Cada SKU: sin cantidad verificada no genera total final; los de tipo «a la medida» nunca reciben precio y van al expediente (ESC-01).
- Paquetes, descuentos por plazo, tope de 10 %, consumo y soporte de nube: `tests/test_core.py` y `tests/test_quote.py`.
- Las 10 reglas: un escalamiento confirmado persiste aunque se elija un producto estándar (incluye CASO-10, datos clínicos).
- Casos de origen llevados al cierre: **10/10** con el tipo esperado.

## Casos (datos de prueba identificados en `tests/test_verificacion_integral.py`)
- ✅ **CASO-01** Clínica Dental Sonrisa Norte: esperado estándar, obtenido estándar; 6,125 MXN/mes; escalamientos —.
- ✅ **CASO-02** Aceros del Valle: esperado mixto, obtenido mixto; 12,100 MXN/mes parcial; escalamientos ESC-07.
- ✅ **CASO-03** PagoFácil MX: esperado mixto, obtenido mixto; 92,000 MXN/mes parcial; escalamientos ESC-01.
- ✅ **CASO-04** Universidad del Noreste: esperado arquitectura, obtenido arquitectura; sin total: arquitecto; escalamientos ESC-01.
- ✅ **CASO-05** Tacos El Güero: esperado estándar, obtenido estándar; 8,500 MXN/mes; escalamientos —.
- ✅ **CASO-06** Seguros Confianza: esperado arquitectura, obtenido arquitectura; sin total: arquitecto; escalamientos ESC-08.
- ✅ **CASO-07** Contadores Asociados Garza: esperado estándar, obtenido estándar; 3,700 MXN/mes; escalamientos —.
- ✅ **CASO-08** AutoPartes Regio: esperado arquitectura, obtenido arquitectura; sin total: arquitecto; escalamientos ESC-01.
- ✅ **CASO-09** Agencia Brava: esperado estándar, obtenido estándar; 25,050 MXN/mes; escalamientos —.
- ✅ **CASO-10** Hospital San Rafael: esperado arquitectura, obtenido arquitectura; sin total: arquitecto; escalamientos ESC-01, ESC-04.

## Hallazgos
- Consumo y soporte de nube (AWS/Azure/OCI) aparecen en la vista previa con su mínimo o en 0 antes de conocer el consumo; el resultado queda marcado incompleto. Es intencional, no un total final.
- La política de combinación de descuentos es una decisión de la demo, no una política confirmada.

## No medido aún
- Impacto comercial (tiempo por propuesta, tasa de cierre): sin medición; es hipótesis.
- Latencia y calidad de Claude en vivo: estas pruebas usan proveedor simulado.
- Uso con vendedores reales: no se ha probado.
