import assert from 'node:assert/strict';
import { readFile, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { validateBatch } from '../src/data/loadBatch.ts';
import { priorityRows, resultRows, resultValue } from '../src/data/results.ts';

export async function runCandidate({ send, evaluate, waitText, navigate, pause, predictions, setScenario, setTileMode }) {
  const raw = {};
  for (const name of ['predictions','metrics','run_info','agent_context']) raw[name] = JSON.parse(await readFile(new URL(`../public/data/${name}.json`, import.meta.url)));
  const batch = validateBatch(raw);
  const textValue = value => value === null ? 'Missing' : `${value} m`;
  async function select(id) {
    await evaluate(`([...document.querySelectorAll('.well-list button')].find(button => button.querySelector('span').textContent === ${JSON.stringify(id)})).click()`);
    await waitText(`Station ${id}.`);
  }
  async function method(value) {
    await evaluate(`(() => { const node = document.getElementById('reconstruction-method'); node.value = ${JSON.stringify(value)}; node.dispatchEvent(new Event('change', { bubbles: true })); })()`);
    await waitText(`Method ${value}.`);
  }
  async function demo(id, mode) {
    await evaluate(`document.getElementById(${JSON.stringify(id)}).click()`);
    assert.equal(await evaluate('document.getElementById("outage-state").dataset.mode'), mode);
  }
  async function hidden() {
    assert.equal(await evaluate('document.querySelectorAll(".history-observed").length'), 0);
    assert.equal(await evaluate('document.querySelector(".history-table thead").innerText.includes("Revealed")'), false);
    assert.equal(await evaluate('document.querySelectorAll(".history-tooltip").length'), 0);
  }
  async function showTab(name) {
    await evaluate(`document.querySelector('[data-nav="${name}"]')?.click()`);
    await pause(80);
  }
  async function openAbout() {
    await evaluate(`document.getElementById('about-data-open')?.click()`);
    for (let i = 0; i < 30; i++) {
      if (await evaluate('document.getElementById("about-data")?.open === true')) return;
      await pause(50);
    }
    throw new Error('About this data did not open');
  }
  async function closeAbout() {
    await evaluate(`document.getElementById('about-data-close')?.click()`);
    await pause(40);
  }
  await navigate('valid');
  await waitText('Nov 2 – Dec 31, 2024');
  await openAbout();
  const body = await evaluate('document.body.innerText');
  for (const label of ['SYNTHETIC / PROVISIONAL', '+dirty', predictions.meta.run_id, 'Physics reconstruction is not completed.', 'not been independently verified',
    'IDW performed better on the holdout test', 'A physics-trained model is not selected', 'Nodus and live Agent37 integrations are not verified',
    'The exporter revision is clean', 'not forecasting']) assert.ok(body.includes(label), label);
  await closeAbout();
  for (const name of Object.keys(raw)) {
    const served = await evaluate(`fetch('/data/${name}.json').then(response => response.json()).then(value => value.meta)`);
    assert.deepEqual(served, predictions.meta);
  }
  await waitText('Map tiles loaded.');
  assert.equal(await evaluate('document.querySelectorAll(".well-map [data-well-id]").length'), 40);
  for (const well of predictions.wells) {
    await select(well.id);
    for (const selectedMethod of ['idw','gcn_lstm','gcn_lstm_physics']) {
      await method(selectedMethod);
      assert.equal(await evaluate('document.querySelector(".well-map [aria-pressed=true]").dataset.wellId'), well.id);
      assert.deepEqual(await evaluate('[...document.querySelectorAll(".history-table tbody tr")].map(row => row.children[1].textContent)'), well.predictions_m[selectedMethod].map(textValue));
      assert.equal(await evaluate('document.querySelector("[data-field=status]").textContent'), batch.metrics.methods[selectedMethod].status);
      if (well.role === 'holdout') await hidden();
      if (selectedMethod === 'gcn_lstm_physics') {
        assert.equal(await evaluate('document.querySelectorAll(".history-selected").length'), 0);
        assert.equal(await evaluate('document.querySelector("[data-field=latest]").textContent'), 'Unknown');
      }
    }
  }
  console.log('PASS candidate browser: served four-file metadata; SYNTHETIC/PROVISIONAL labels; all 120 well/method selections, map sync, exact chart values/nulls, unavailable physics and hidden truth');
  for (const selectedMethod of ['idw','gcn_lstm','gcn_lstm_physics']) {
    await method(selectedMethod);
    assert.deepEqual(await evaluate('[...document.querySelectorAll("[data-priority-id]")].map(row => row.dataset.priorityId)'), priorityRows(batch, selectedMethod).map(row => row.id));
  }
  for (const row of resultRows(batch)) for (const key of ['validationMae','testMae','testRmse','validationPairs','testPairs','testWells']) {
    const suffix = ['validationMae','testMae','testRmse'].includes(key) ? ' m' : '';
    assert.equal(await evaluate(`document.querySelector('[data-result-method=${row.method}] [data-metric=${key}]').textContent`), resultValue(row[key], suffix));
  }
  const holdouts = predictions.wells.filter(well => well.role === 'holdout');
  for (const width of [1280,390]) {
    await send('Emulation.setDeviceMetricsOverride', { width, height: 1000, deviceScaleFactor: 1, mobile: width < 700 });
    for (const well of holdouts) {
      await select(well.id);
      for (const selectedMethod of ['idw','gcn_lstm','gcn_lstm_physics']) {
        await method(selectedMethod); await hidden();
        await demo('simulate-outage','simulated-outage'); await hidden();
        await demo('reveal-observations','reveal');
        assert.deepEqual(await evaluate('[...document.querySelectorAll(".history-table tbody tr")].map(row => row.lastElementChild.textContent)'), well.observations_m.map(textValue));
        await demo('reset-outage','sensor-available'); await hidden();
      }
    }
    await method('gcn_lstm');
    for (const panel of ['page-header','map-panel','history-panel','results-panel']) {
      if (panel === 'map-panel') await showTab('stations');
      if (panel === 'history-panel' || panel === 'results-panel') await showTab('analysis');
      await evaluate(`document.querySelector('.${panel}').scrollIntoView({ block: 'start' })`);
      await pause(200);
      assert.ok(await evaluate('document.documentElement.scrollWidth <= window.innerWidth'), `${panel} overflow at ${width}`);
      const capture = await send('Page.captureScreenshot', { format: 'png' });
      await writeFile(join(tmpdir(), `alter-ego-a09-${panel}-${width}.png`), Buffer.from(capture.data,'base64'));
    }
    assert.ok(await evaluate('document.querySelector(".history-panel .recharts-wrapper").getBoundingClientRect().width > 200'));
  }
  console.log('PASS candidate browser: exact exported results/priorities; 48 desktop/mobile outage/reveal/reset cycles across all 8 held-out wells and 3 methods; responsive captures and readable chart width');
  await demo('simulate-outage','simulated-outage'); await demo('reveal-observations','reveal');
  await method('idw'); await hidden();
  await demo('simulate-outage','simulated-outage'); await demo('reveal-observations','reveal');
  await select(holdouts[0].id); await hidden();
  await showTab('analysis');
  await evaluate('document.getElementById("simulate-outage").focus()');
  await send('Input.dispatchKeyEvent', { type:'keyDown', key:'Enter', code:'Enter', text:'\r', windowsVirtualKeyCode:13 });
  await send('Input.dispatchKeyEvent', { type:'keyUp', key:'Enter', code:'Enter', windowsVirtualKeyCode:13 });
  assert.equal(await evaluate('document.getElementById("outage-state").dataset.mode'), 'simulated-outage'); await hidden();
  for (const [scenario, message] of [['missing','HTTP 404'],['mixed','metadata mismatch'],['malformed','not valid JSON']]) {
    await navigate(scenario); await waitText(message);
    assert.equal(await evaluate('document.querySelectorAll(".well-list button").length'), 0);
    setScenario('valid');
    await evaluate('document.querySelector("main button").click()'); await waitText('Nov 2 – Dec 31, 2024');
    await select(holdouts[0].id); await hidden();
  }
  setTileMode('failure'); await navigate('valid'); await waitText('Background map tiles are unavailable or incomplete.');
  await select(holdouts[0].id); await method('gcn_lstm'); await hidden();
  assert.equal(await evaluate('document.querySelectorAll(".well-map [data-well-id]").length'), 40);
  await showTab('assistant');
  await evaluate('document.getElementById("check-agent-context").click()');
  await waitText('not an Agent37 fetch');
  assert.ok((await evaluate('document.querySelector(".briefing-panel").innerText')).includes('Optional backup service'));
  console.log('PASS candidate browser: well/method switch privacy reset, keyboard outage, incomplete/mismatched/malformed batch rejection and retry, map-tile failure fallback, optional Agent37 context check');
}
