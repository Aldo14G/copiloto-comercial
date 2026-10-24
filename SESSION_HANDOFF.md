# Reanudación · 24/10/2026

## Proyecto y acuerdos

Repositorio activo: `C:\Users\aldog\OneDrive\Escritorio\Obsidian\Claude-Hakaton\copiloto-comercial`. Rama master, base heredada cc7d7a2. Hay cambios previos y nuevos sin commit: conservarlos y revisar `git status` antes de editar. No se autorizó commit, push, despliegue ni delegación a agentes.

Usar Ponytail full y la revisión Thermo-Nuclear. Catálogo completo: 45 productos, 7 familias, 7 paquetes, 11 condiciones, 10 reglas, 10 casos. Los datos son simulados; no son ofertas oficiales de Alestra.

Leer primero `copiloto-comercial/REVISION-IMPLEMENTACION.md`, `README.md`, `PRODUCT.md` y las decisiones de `SPRINT-PRODUCTO.md`. La identidad aprobada es A — Documento anotado. Propuesta comercial y expediente interno deben compartir caso/revisión/catálogo; cada uno sale en PDF y Word editable cuando el cierre es calculable. Sin importe calculable solo sale el expediente en ambos formatos.

## Estado comprobado

- Implementación local integrada: Casos, Catálogo, Reunión, Alternativas, Cierre e Historial.
- 67/67 pruebas pasan con proveedor simulado. Cobertura heredada de 45 SKUs y siete paquetes.
- Chrome verificó creación de caso, cierre mixto, cuatro descargas, teclado y ausencia de desbordamiento en los tamaños inspeccionados.
- Cuatro documentos del ejemplo generados y todas sus páginas revisadas; los DOCX se renderizaron con Word porque no hay LibreOffice empaquetado.
- `git diff --check` pasa. Catálogo y evaluación histórica de Opus conservados; no se hicieron nuevas llamadas pagadas a Claude.
- Servidor local iniciado en `http://127.0.0.1:8524`; comprobar si sigue activo antes de levantar otro. No se publicó.

## Ejecutar y continuar

Desde el repositorio, Python instalado: `C:\Users\aldog\AppData\Local\Programs\Python\Python313\python.exe`.

```powershell
python -B -m unittest discover tests
python -m streamlit run app.py --server.port 8524
```

Para recorrer sin proveedor: Casos → Abrir ejemplo sintético → Alternativas → cantidades 1 para SIM-DC-01 y SIM-DC-08 → plazo 12 → revisar y confirmar → Cierre → Preparar PDF y Word. Mensual parcial 12,100 y único 11,000 MXN sin IVA; recuperación pendiente ESC-07. Crear ejemplo no altera las fichas originales.

El script `tests/browser_smoke.cjs` requiere Chrome y Playwright para Node. Evidencia y archivos de muestra en `outputs/validacion-20261024/`. Las pruebas automatizadas no miden impacto comercial ni nueva latencia de Claude.

## Continuidad de Codex

Por petición explícita de Aldo, se configuró Codex CLI 0.164.0 con su API key mediante el inicio de sesión nativo. La clave permanece fuera del proyecto y no se incluye aquí. La consulta de autenticación a OpenAI devolvió HTTP 200; no se hicieron llamadas de generación. El chat de escritorio abierto no se confirmó migrado automáticamente a ese método.

Sesión local: `01a16fb2-0bef-78e0-88d6-e957c6477356`. Desde este proyecto puede intentarse `codex resume 01a16fb2-0bef-78e0-88d6-e957c6477356`; si el cliente no recupera el historial, abrir una sesión y pedir que lea este archivo. El estado de archivos y Git es la continuidad verificada. No asumir un cambio automático al alcanzar límites.

No cambiar el proveedor Claude del producto: la API de OpenAI fue conectada para Codex como herramienta de desarrollo. No iniciar llamadas pagadas de evaluación sin que Aldo lo solicite. La clave se compartió en el chat; conviene reemplazarla posteriormente mediante el flujo seguro, sin copiarla a documentos ni al repositorio.

## Siguiente trabajo útil

La implementación local y su validación funcional están cerradas. Revisar el producto con Aldo; después, si lo autoriza, medir calidad/latencia con conversaciones completas de Claude y validar utilidad con un vendedor. Aclarar con el responsable comercial la acumulación de descuentos y otros criterios cualitativos. No presentar esos pendientes como métricas ya logradas.
