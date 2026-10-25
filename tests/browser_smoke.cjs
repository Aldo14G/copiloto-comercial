// Recorrido real sin llamadas al proveedor. NODE_PATH debe incluir Playwright.
const { chromium } = require('playwright');
const { mkdir, writeFile } = require('node:fs/promises');
const path = require('node:path');
const assert = require('node:assert/strict');

(async () => {
  const destino = path.resolve(process.argv[3] || '../outputs/validacion-20261024/navegador');
  await mkdir(destino, { recursive: true });
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1024 } });
  const errores = [];
  page.on('pageerror', e => errores.push(e.message));
  const evidencias = [];
  async function vista(nombre, texto) {
    await page.getByText(nombre, { exact: true }).first().click();
    await page.getByText(texto, { exact: true }).first().waitFor();
  }
  async function captura(nombre) {
    await page.evaluate(() => document.fonts.ready);
    await page.getByTestId('stMain').evaluate(elemento => { elemento.scrollTop = 0; });
    await page.screenshot({ path: path.join(destino, nombre + '.png'), fullPage: true });
    const geometria = await page.evaluate(() => ({ ancho: innerWidth, contenido: document.documentElement.scrollWidth }));
    assert.ok(geometria.contenido <= geometria.ancho, `${nombre}: desbordamiento horizontal`);
    assert.equal(await page.getByTestId('stException').count(), 0);
    evidencias.push({ nombre, ...geometria });
  }
  try {
    await page.goto(process.argv[2] || 'http://127.0.0.1:8524');
    await vista('Casos', 'Cada reunión conserva su contexto');
    await page.getByRole('button', { name: 'Crear caso', exact: true }).waitFor();
    await page.getByRole('textbox', { name: 'Empresa', exact: true }).fill('Validación sintética de caso nuevo');
    await page.getByRole('button', { name: 'Crear caso', exact: true }).click();
    await page.getByRole('heading', { name: 'Validación sintética de caso nuevo', exact: true }).waitFor();
    await vista('Casos', 'Cada reunión conserva su contexto');
    await page.getByRole('button', { name: 'Abrir ejemplo sintético', exact: true }).click();
    await page.getByRole('heading', { name: 'Aceros del Valle · ejemplo', exact: true }).waitFor();
    for (const ancho of [1440, 950, 390]) {
      await page.setViewportSize({ width: ancho, height: 1024 });
      await captura(`reunion-${ancho}`);
    }
    await page.setViewportSize({ width: 1440, height: 1024 });
    await vista('Alternativas', 'De la necesidad a una solución justificable');
    await page.getByRole('button', { name: 'Confirmar solución y cantidades', exact: true }).waitFor();
    await page.getByRole('spinbutton', { name: 'Cantidad', exact: true }).nth(1).waitFor();
    assert.equal(await page.getByRole('spinbutton', { name: 'Cantidad', exact: true }).count(), 2);
    for (const input of await page.getByRole('spinbutton', { name: 'Cantidad', exact: true }).all()) {
      await input.fill('1');
      await input.press('Tab');
    }
    await page.getByText('Revisé fuentes, alcance, cantidades y componentes que dependen de diseño', { exact: true }).click();
    await page.getByRole('button', { name: 'Confirmar solución y cantidades', exact: true }).click();
    await page.getByText('Selección guardada. El cierre comprobará si el importe puede calcularse.', { exact: true }).waitFor();
    await captura('alternativas-1440');
    await vista('Cierre', 'Un caso, dos entregables vinculados');
    await page.getByText('$12,100.00', { exact: true }).waitFor();
    await page.getByRole('button', { name: 'Preparar PDF y Word', exact: true }).click();
    const descargas = page.getByRole('button', { name: /^Descargar / });
    await descargas.nth(3).waitFor();
    assert.equal(await descargas.count(), 4);
    for (let i = 0; i < 4; i++) {
      const esperar = page.waitForEvent('download');
      await descargas.nth(i).click();
      const archivo = await esperar;
      await archivo.saveAs(path.join(destino, archivo.suggestedFilename()));
    }
    await captura('cierre-1440');
    await page.setViewportSize({ width: 390, height: 1024 });
    await captura('cierre-390');
    await vista('Historial', 'La conversación y sus revisiones');
    await page.getByRole('radio', { name: 'Historial', exact: true }).focus();
    await page.keyboard.press('ArrowLeft');
    await page.getByRole('heading', { name: 'Un caso, dos entregables vinculados', exact: true }).waitFor();
    await page.keyboard.press('Tab');
    const foco = await page.evaluate(() => document.activeElement.tagName);
    assert.notEqual(foco, 'BODY');
    assert.equal(errores.length, 0, errores.join('\n'));
    await writeFile(path.join(destino, 'resultado.json'), JSON.stringify({ errores, foco, evidencias, descargas: 4 }, null, 2));
    console.log(JSON.stringify({ errores, foco, capturas: evidencias.length, descargas: 4 }));
  } catch (error) {
    console.error((await page.getByTestId('stMain').innerText()).slice(-4500));
    throw error;
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
