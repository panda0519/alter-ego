// Windows browser acceptance check using installed Edge and Node's built-in CDP client.
// Run against the production preview: node checks/browser.mjs
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { mkdtemp, readFile, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, resolve, dirname, basename } from 'node:path';

const origin = process.env.ALTER_EGO_CHECK_ORIGIN || 'http://127.0.0.1:4173';
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
const fixturePredictions = JSON.parse(await readFile(new URL('../public/data/predictions.json', import.meta.url), 'utf8'));
const profile = await mkdtemp(join(tmpdir(), 'alter-ego-a02-'));
const browser = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', [
  '--headless', '--disable-gpu', '--no-first-run', '--remote-debugging-port=0',
  `--user-data-dir=${profile}`, 'about:blank',
], { windowsHide: true, stdio: 'ignore' });
let socket;
let send;
try {
  let port;
  for (let i = 0; i < 100; i++) {
    try { port = (await readFile(join(profile, 'DevToolsActivePort'), 'utf8')).split('\n')[0]; break; } catch { await pause(100); }
  }
  assert.ok(port, 'Edge remote debugging startup');
  const pages = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  socket = new WebSocket(pages.find(page => page.type === 'page').webSocketDebuggerUrl);
  await new Promise((resolve, reject) => { socket.onopen = resolve; socket.onerror = reject; });
  let next = 0;
  const pending = new Map();
  const exceptions = [];
  let scenario = 'valid';
  let held = [];
  let tileMode = 'success';
  let heldTiles = [];
  let tileRequests = 0;
  let batchRequests = 0;
  let canceledInterceptions = 0;
  const interceptionError = error => {
    // StrictMode/refresh removes tiles while CDP is responding. The browser
    // invalidates those request IDs; this is not a page Runtime exception.
    if (error.message === 'Invalid InterceptionId.') canceledInterceptions++;
    else exceptions.push(error.message);
  };
  send = (method, params = {}) => new Promise((resolve, reject) => {
    const id = ++next;
    const timer = setTimeout(() => { pending.delete(id); reject(new Error(`CDP timeout: ${method}`)); }, 10000);
    pending.set(id, { resolve, reject, timer });
    socket.send(JSON.stringify({ id, method, params }));
  });
  socket.onmessage = event => {
    const message = JSON.parse(event.data);
    if (message.id) {
      const entry = pending.get(message.id);
      if (!entry) return;
      clearTimeout(entry.timer); pending.delete(message.id);
      if (message.error) entry.reject(new Error(message.error.message)); else entry.resolve(message.result);
    }
    if (message.method === 'Runtime.exceptionThrown') exceptions.push(message.params.exceptionDetails.text);
    if (message.method === 'Fetch.requestPaused') {
      const { requestId, request } = message.params;
      if (new URL(request.url).hostname === 'tile.openstreetmap.org') {
        tileRequests++;
        const result = tileMode === 'failure'
          ? send('Fetch.failRequest', { requestId, errorReason: 'InternetDisconnected' })
          : tileMode === 'delayed'
            ? (heldTiles.push(requestId), Promise.resolve())
            : send('Fetch.fulfillRequest', { requestId, responseCode: 200, responseHeaders: [{ name: 'Content-Type', value: 'image/svg+xml' }], body: Buffer.from('<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256"><rect width="256" height="256" fill="#e7eeeb"/></svg>').toString('base64') });
        void result.catch(interceptionError);
        return;
      }
      if (scenario === 'loading') { held.push(requestId); return; }
      batchRequests++;
      const name = new URL(request.url).pathname.split('/').at(-1);
      void (async () => {
        if (scenario === 'valid') return send('Fetch.continueRequest', { requestId });
        let body = await readFile(new URL(`../public/data/${name}`, import.meta.url), 'utf8');
        let responseCode = 200;
        if (name === 'predictions.json') {
          if (scenario === 'outage-unavailable' || scenario === 'outage-no-truth') {
            const value = JSON.parse(body); const well = value.wells.find(well => well.role === 'holdout');
            if (scenario === 'outage-no-truth') well.observations_m.fill(null);
            else for (const method of Object.keys(well.predictions_m)) {
              well.predictions_m[method].fill(null);
              well.summaries[method] = { latest_depth_m: null, change_30d_m: null, priority: 'unknown', reason_codes: [] };
            }
            body = JSON.stringify(value);
          }
          if (scenario === 'history-gaps') {
            const value = JSON.parse(body); value.wells[0].predictions_m.gcn_lstm.splice(5, 3, null, null, null); body = JSON.stringify(value);
          }
          if (scenario === 'history-empty') {
            const value = JSON.parse(body); value.wells[0].predictions_m.gcn_lstm.fill(null); value.wells[0].observations_m.fill(null); body = JSON.stringify(value);
          }
          if (scenario === 'history-calendar-gap') {
            const value = JSON.parse(body); value.dates.splice(5, 1);
            value.wells.forEach(well => { well.observations_m.splice(5, 1); Object.values(well.predictions_m).forEach(values => values.splice(5, 1)); });
            body = JSON.stringify(value);
          }
          if (scenario === 'invalid-coordinates') { const value = JSON.parse(body); value.wells[0].latitude = 91; body = JSON.stringify(value); }
          if (scenario === 'duplicate-coordinates') { const value = JSON.parse(body); value.wells.forEach(well => { well.latitude = 26; well.longitude = 91; }); body = JSON.stringify(value); }
          if (scenario === 'malformed') body = '{';
          if (scenario === 'missing') { body = ''; responseCode = 404; }
          if (scenario === 'empty') body = '';
          if (scenario === 'schema') { const value = JSON.parse(body); value.wells = []; body = JSON.stringify(value); }
          if (scenario === 'null-summary' || scenario === 'unavailable-method') {
            const value = JSON.parse(body);
            const well = value.wells[0];
            well.summaries.gcn_lstm = { latest_depth_m: null, change_30d_m: null, priority: 'unknown', reason_codes: [] };
            if (scenario === 'unavailable-method') well.predictions_m.gcn_lstm.fill(null);
            else well.predictions_m.gcn_lstm[well.predictions_m.gcn_lstm.length - 1] = null;
            body = JSON.stringify(value);
          }
        }
        if (scenario === 'mixed' && name === 'metrics.json') {
          const value = JSON.parse(body); value.meta.run_id = 'wrong-run'; body = JSON.stringify(value);
        }
        if (scenario === 'outage-unavailable' && name === 'agent_context.json') {
          const value = JSON.parse(body); Object.assign(value.wells.find(well => well.role === 'holdout'), { latest_depth_m: null, change_30d_m: null, priority: 'unknown', reason_codes: [] }); body = JSON.stringify(value);
        }
        if (scenario === 'new-batch') {
          const value = JSON.parse(body); value.meta.run_id = 'browser-test-new-run'; value.meta.dataset_id = 'browser-test-new-dataset'; body = JSON.stringify(value);
        }
        return send('Fetch.fulfillRequest', { requestId, responseCode, responseHeaders: [{ name: 'Content-Type', value: 'application/json' }], body: Buffer.from(body).toString('base64') });
      })().catch(interceptionError);
    }
  };
  await send('Runtime.enable');
  await send('Page.enable');
  await send('Emulation.setDeviceMetricsOverride', { width: 1280, height: 1000, deviceScaleFactor: 1, mobile: false });
  await send('Fetch.enable', { patterns: [{ urlPattern: '*/data/*.json' }, { urlPattern: 'https://tile.openstreetmap.org/*' }] });
  async function evaluate(expression) {
    const value = await send('Runtime.evaluate', { expression, returnByValue: true });
    assert.ok(!value.exceptionDetails, JSON.stringify(value.exceptionDetails));
    return value.result.value;
  }
  async function waitText(text) {
    for (let i = 0; i < 100; i++) {
      const body = await evaluate('document.body.innerText');
      if (body.includes(text)) return body;
      await pause(100);
    }
    throw new Error(`Page did not display: ${text}`);
  }
  async function navigate(mode) {
    scenario = mode;
    await send('Page.navigate', { url: origin });
  }
  await navigate('valid');
  const valid = await waitText('6 wells loaded');
  for (const expected of ['Dataset: synthetic', 'artifact_kind=fixture', '2024-08-01 to 2024-09-29', '2026-10-21T12:00:00Z', 'fixture-layout-v1', '60 series dates loaded', 'No experiment has run.']) assert.ok(valid.includes(expected), expected);
  assert.ok(!valid.includes('Retry loading'));
  console.log('PASS browser: published batch, type/dates/counts and fixture warning');
  async function chooseMethod(method) {
    await evaluate(`(() => { const select = document.getElementById('reconstruction-method'); select.value = ${JSON.stringify(method)}; select.dispatchEvent(new Event('change', { bubbles: true })); })()`);
    await waitText(`Selected method: ${method}.`);
  }
  async function readDetails() {
    return evaluate(`Object.fromEntries([...document.querySelectorAll('[data-field]')].map(node => [node.dataset.field, node.textContent]))`);
  }
  for (const well of fixturePredictions.wells) {
    await evaluate(`(() => { [...document.querySelectorAll('.well-list button')].find(button => button.querySelector('span').textContent === ${JSON.stringify(well.id)}).click(); })()`);
    await waitText(`Selected well: ${well.id}.`);
    for (const method of ['idw', 'gcn_lstm', 'gcn_lstm_physics']) {
      await chooseMethod(method);
      const details = await readDetails();
      const summary = well.summaries[method];
      assert.deepEqual(details, {
        'well-id': well.id, role: well.role, latitude: String(well.latitude), longitude: String(well.longitude),
        method, status: 'not_run', latest: `${summary.latest_depth_m} m`, change: `${summary.change_30d_m} m`,
        priority: summary.priority, reasons: summary.reason_codes.join(', '),
      });
      assert.equal(await evaluate('document.querySelectorAll(".well-list button[aria-pressed=true]").length'), 1);
      await waitText(`History: ${well.id} / ${method}`);
      assert.deepEqual(await evaluate('[...document.querySelectorAll(".history-table tbody tr")].map(row => [...row.children].map(cell => cell.textContent))'),
        fixturePredictions.dates.map((date, index) => [date, `${well.predictions_m[method][index]} m`]));
    }
  }
  console.log('PASS browser: all 18 well/method combinations show their own exported fields, with one selected well');
  console.log('PASS browser: chart/table dates and reconstructed values follow all 18 well/method combinations');
  // Real keyboard activation of a well button, preserving the chosen method.
  await send('Page.bringToFront');
  await evaluate('document.querySelector(".well-list button").focus()');
  assert.equal(await evaluate('document.activeElement === document.querySelector(".well-list button")'), true);
  await send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Enter', code: 'Enter', text: '\r', unmodifiedText: '\r', windowsVirtualKeyCode: 13 });
  await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13 });
  await waitText(`Selected well: ${fixturePredictions.wells[0].id}.`);
  assert.equal((await readDetails()).method, 'gcn_lstm_physics');
  assert.equal(await evaluate('document.querySelector("label[for=reconstruction-method]").textContent'), 'Reconstruction method');
  console.log('PASS browser: keyboard well selection and labelled method control');
  await waitText('Map tiles loaded.');
  assert.equal(await evaluate('document.querySelectorAll(".leaflet-container").length'), 1);
  assert.equal(await evaluate('document.querySelectorAll(".well-map [data-well-id]").length'), fixturePredictions.wells.length);
  assert.ok(await evaluate('!!document.querySelector(".leaflet-control-attribution a[href=\\"https://www.openstreetmap.org/copyright\\"]")'));
  const mapBefore = await evaluate('document.querySelector(".well-map")._leaflet_id');
  for (const well of fixturePredictions.wells) {
    await evaluate(`document.querySelector('.well-map [data-well-id="${well.id}"]').dispatchEvent(new MouseEvent('click', { bubbles: true }))`);
    await waitText(`Selected well: ${well.id}.`);
    assert.equal((await readDetails())['well-id'], well.id);
    assert.equal(await evaluate('document.querySelector(".well-map [aria-pressed=true]").dataset.wellId'), well.id);
  }
  await evaluate('document.querySelector(".well-list button").click()');
  await waitText(`Selected well: ${fixturePredictions.wells[0].id}.`);
  assert.equal(await evaluate('document.querySelector(".well-map [aria-pressed=true]").dataset.wellId'), fixturePredictions.wells[0].id);
  await evaluate(`document.querySelector('.well-map [data-well-id="${fixturePredictions.wells[1].id}"]').focus()`);
  await send('Input.dispatchKeyEvent', { type: 'keyDown', key: ' ', code: 'Space', windowsVirtualKeyCode: 32 });
  await send('Input.dispatchKeyEvent', { type: 'keyUp', key: ' ', code: 'Space', windowsVirtualKeyCode: 32 });
  await waitText(`Selected well: ${fixturePredictions.wells[1].id}.`);
  assert.equal((await readDetails()).method, 'gcn_lstm_physics');
  assert.equal(await evaluate('document.querySelector(".well-map")._leaflet_id'), mapBefore);
  console.log('PASS browser: all circle markers select wells; list/map/details sync; keyboard marker activation; map not recreated on selection');
  await evaluate(`(() => { const select = document.getElementById('reconstruction-method'); select.add(new Option('invalid', 'invalid')); select.value = 'invalid'; select.dispatchEvent(new Event('change', { bubbles: true })); })()`);
  await waitText('Invalid selection.');
  assert.deepEqual(await readDetails(), {});
  await chooseMethod('idw');
  assert.equal((await readDetails()).method, 'idw');
  console.log('PASS browser: invalid method clears details and valid selection recovers');
  for (const mode of ['null-summary', 'unavailable-method']) {
    await navigate(mode);
    await waitText('6 wells loaded');
    await chooseMethod('gcn_lstm');
    const details = await readDetails();
    assert.equal(details.latest, 'Unknown');
    assert.equal(details.change, 'Unknown');
    assert.equal(details.priority, 'unknown');
    assert.equal(details.reasons, 'Unknown');
    const body = await evaluate('document.body.innerText');
    assert.equal(body.includes('Method unavailable for this well.'), mode === 'unavailable-method');
    await evaluate('document.querySelectorAll(".well-list button")[1].click()');
    await waitText(`Selected well: ${fixturePredictions.wells[1].id}.`);
    assert.equal((await readDetails()).latest, `${fixturePredictions.wells[1].summaries.gcn_lstm.latest_depth_m} m`);
    await evaluate('document.querySelector(".well-list button").click()');
    await waitText(`Selected well: ${fixturePredictions.wells[0].id}.`);
    assert.equal((await readDetails()).latest, 'Unknown');
    console.log(`PASS browser: ${mode} and repeated switching never substitute or retain another well's values`);
  }
  for (const [mode, text] of [['malformed', 'not valid JSON'], ['missing', 'HTTP 404'], ['empty', 'is empty'], ['schema', 'must NOT have fewer than 1 items'], ['mixed', 'metadata mismatch at run_id'], ['invalid-coordinates', 'must be <= 90']]) {
    await navigate(mode);
    const body = await waitText(text);
    assert.ok(body.includes('Retry loading') && body.includes('No partial batch is displayed.'));
    assert.ok(!body.includes('6 wells loaded') && !body.includes('fixture-layout-v1'));
    console.log(`PASS browser: ${mode} rejected without stale/partial data`);
  }
  scenario = 'valid';
  await evaluate('document.querySelector("button").click()');
  await waitText('6 wells loaded');
  console.log('PASS browser: retry recovers a complete valid batch');
  await navigate('loading');
  await waitText('Loading the complete export batch...');
  scenario = 'valid';
  for (const requestId of held) await send('Fetch.continueRequest', { requestId }).catch(() => {});
  held = [];
  await waitText('6 wells loaded');
  console.log('PASS browser: loading state and completion');
  tileMode = 'failure';
  await navigate('valid');
  await waitText('Background map tiles are unavailable or incomplete.');
  assert.equal(await evaluate('document.querySelectorAll(".well-map [data-well-id]").length'), 6);
  await evaluate('document.querySelectorAll(".well-list button")[2].click()');
  await waitText(`Selected well: ${fixturePredictions.wells[2].id}.`);
  await chooseMethod('gcn_lstm');
  assert.equal((await readDetails()).method, 'gcn_lstm');
  assert.ok((await evaluate('document.body.innerText')).includes('60 series dates loaded'));
  tileMode = 'success';
  await evaluate('[...document.querySelectorAll("button")].find(button => button.textContent === "Retry map tiles").click()');
  await waitText('Map tiles loaded.');
  assert.equal((await readDetails())['well-id'], fixturePredictions.wells[2].id);
  console.log('PASS browser: tile failure retains markers/list/details/chart area; retry recovers without losing selection');
  tileMode = 'delayed';
  await navigate('valid');
  await waitText('Background map tiles are unavailable or incomplete.');
  assert.equal(await evaluate('document.querySelectorAll(".well-map [data-well-id]").length'), 6);
  tileMode = 'success';
  for (const requestId of heldTiles) await send('Fetch.failRequest', { requestId, errorReason: 'Aborted' }).catch(() => {});
  heldTiles = [];
  await navigate('duplicate-coordinates');
  await waitText('Map tiles loaded.');
  assert.equal(await evaluate('document.querySelectorAll(".well-map [data-well-id]").length'), 6);
  console.log('PASS browser: stalled tile requests time out gracefully; coincident coordinates do not crash');
  for (let i = 0; i < 2; i++) {
    await navigate('valid'); await waitText('Map tiles loaded.');
    assert.equal(await evaluate('document.querySelectorAll(".leaflet-container").length'), 1);
    assert.equal(await evaluate('document.querySelectorAll(".leaflet-pane.leaflet-map-pane").length'), 1);
  }
  assert.ok(tileRequests > 0);
  console.log('PASS browser: reloads retain one map; all tile requests intercepted locally');
  const failureHook = await send('Page.addScriptToEvaluateOnNewDocument', {
    source: 'window.ResizeObserver = class extends ResizeObserver { observe(target, options) { if (target.classList.contains("well-map")) throw new Error("Simulated map observer initialization failure"); return super.observe(target, options); } };',
  });
  await navigate('valid');
  await waitText('The map could not be initialized.');
  await evaluate('document.querySelectorAll(".well-list button")[3].click()');
  await waitText(`Selected well: ${fixturePredictions.wells[3].id}.`);
  assert.equal(await evaluate('document.querySelectorAll(".leaflet-map-pane").length'), 0);
  await send('Page.removeScriptToEvaluateOnNewDocument', { identifier: failureHook.identifier });
  await navigate('valid'); await waitText('Map tiles loaded.');
  console.log('PASS browser: initialization failure cleans up map and preserves list/details; next mount recovers');
  // A05 visualization: inspect real SVG path breaks and the date-aligned data.
  const selectedPath = '.history-selected .recharts-line-curve';
  await chooseMethod('gcn_lstm');
  await evaluate('document.getElementById("show-idw").click(); document.getElementById("show-observations").click()');
  for (let i = 0; i < 100; i++) {
    if (await evaluate('!!document.querySelector(".history-observed .recharts-line-curve")')) break;
    await pause(100);
  }
  assert.ok(await evaluate('!!document.querySelector(".history-idw .recharts-line-curve")'));
  assert.ok(await evaluate('(document.querySelector(".history-observed .recharts-line-curve").getAttribute("d").match(/M/g) || []).length > 1'), 'Observation nulls split the actual SVG path');
  assert.equal(await evaluate('document.querySelector(".history-table tbody tr td:last-child").textContent'), 'Missing');
  assert.ok((await evaluate('document.querySelector(".history-panel").innerText')).includes('depth increases downward'));
  async function hoverFirstHistoryPoint() {
    await evaluate('document.querySelector(".history-plot").scrollIntoView({ block: "center" })');
    for (let i = 0; i < 100; i++) {
      if (await evaluate('!!document.querySelector(".history-selected .recharts-line-curve")')) break;
      await pause(100);
    }
    const position = await evaluate('(() => { const path = document.querySelector(".history-selected .recharts-line-curve"); const point = path.getPointAtLength(0); const screen = new DOMPoint(point.x, point.y).matrixTransform(path.getScreenCTM()); return { x: screen.x + 1, y: screen.y }; })()');
    await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: position.x, y: position.y });
    for (let i = 0; i < 100; i++) {
      if (await evaluate('!!document.querySelector(".history-tooltip")')) return;
      await pause(100);
    }
    throw new Error('History tooltip did not appear');
  }
  await hoverFirstHistoryPoint();
  const observationTooltip = await evaluate('document.querySelector(".history-tooltip").innerText');
  assert.ok(observationTooltip.includes('2024-08-01') && observationTooltip.includes('Observed reading: Missing'));
  const heldout = fixturePredictions.wells.find(well => well.role === 'holdout');
  await evaluate(`document.querySelector('.well-list button span').closest('ul').querySelectorAll('button')[${fixturePredictions.wells.indexOf(heldout)}].click()`);
  await waitText(`History: ${heldout.id} / gcn_lstm`);
  assert.equal(await evaluate('document.getElementById("show-observations").disabled'), true);
  assert.equal(await evaluate('document.querySelectorAll(".history-observed").length'), 0);
  assert.equal(await evaluate('document.querySelector(".history-table thead").textContent.includes("Observed")'), false);
  await hoverFirstHistoryPoint();
  assert.equal(await evaluate('document.querySelector(".history-tooltip").innerText.includes("Observed")'), false);
  console.log('PASS browser: optional IDW/observations, real null-path breaks, units/direction and holdout observation exclusion');
  for (const mode of ['history-gaps', 'history-calendar-gap']) {
    await navigate(mode); await waitText('6 wells loaded'); await chooseMethod('gcn_lstm');
    for (let i = 0; i < 100; i++) {
      if (await evaluate(`!!document.querySelector('${selectedPath}')`)) break;
      await pause(100);
    }
    assert.ok(await evaluate(`(document.querySelector('${selectedPath}').getAttribute('d').match(/M/g) || []).length > 1`));
    console.log(`PASS browser: ${mode} produces visible path gaps, not interpolation`);
  }
  await navigate('history-empty'); await waitText('6 wells loaded'); await chooseMethod('gcn_lstm');
  await waitText('No displayable history values');
  assert.equal(await evaluate('document.querySelectorAll(".history-panel .recharts-wrapper").length'), 0);
  await evaluate('document.getElementById("show-idw").click()');
  for (let i = 0; i < 100; i++) {
    if (await evaluate('!!document.querySelector(".history-idw .recharts-line-curve")')) break;
    await pause(100);
  }
  assert.equal(await evaluate(`!!(document.querySelector('${selectedPath}')?.getAttribute('d') || '').match(/[ML]/)`), false);
  assert.ok(await evaluate('!!document.querySelector(".history-idw .recharts-line-curve")'));
  console.log('PASS browser: empty/unavailable prediction history and explicitly requested comparison remain distinct');
  await navigate('valid'); await waitText('6 wells loaded'); await chooseMethod('gcn_lstm');
  await evaluate('document.getElementById("show-idw").click(); document.getElementById("show-observations").click()');
  if (new URL(origin).port === '5173') {
    const componentPath = new URL('../src/WellMap.tsx', import.meta.url);
    const original = await readFile(componentPath, 'utf8');
    let refreshedId;
    async function waitNewMap(previous) {
      for (let i = 0; i < 100; i++) {
        const id = await evaluate('document.querySelector(".well-map")?._leaflet_id');
        if (id && id !== previous) return;
        await pause(100);
      }
      throw new Error('Development refresh did not recreate the map');
    }
    try {
      const beforeRefresh = await evaluate('document.querySelector(".well-map")._leaflet_id');
      await writeFile(componentPath, `${original}\n// Temporary A04 development refresh check.\n`);
      await waitNewMap(beforeRefresh);
      await waitText('Map tiles loaded.');
      assert.equal(await evaluate('document.querySelectorAll(".leaflet-map-pane").length'), 1);
      assert.equal(await evaluate('document.querySelectorAll(".well-map [data-well-id]").length'), 6);
      refreshedId = await evaluate('document.querySelector(".well-map")._leaflet_id');
      console.log('PASS browser: StrictMode development mount and actual Fast Refresh leave one working map');
    } finally {
      await writeFile(componentPath, original);
    }
    await waitNewMap(refreshedId);
    await waitText('Map tiles loaded.');
  }
  for (const width of [390, 1280]) {
    await send('Emulation.setDeviceMetricsOverride', { width, height: 900, deviceScaleFactor: 1, mobile: width < 700 });
    assert.ok(await evaluate('document.documentElement.scrollWidth <= window.innerWidth'), `No horizontal overflow at ${width}px`);
    await evaluate('document.querySelector(".history-panel").scrollIntoView({ block: "start" })');
    await pause(300);
    assert.ok(await evaluate('document.querySelector(".history-panel .recharts-wrapper").getBoundingClientRect().width > 200'));
    const screenshot = await send('Page.captureScreenshot', { format: 'png' });
    await writeFile(join(tmpdir(), `alter-ego-a05-${width}.png`), Buffer.from(screenshot.data, 'base64'));
    if (width === 390) {
      await evaluate('document.querySelector(".history-plot").scrollIntoView({ block: "start" })');
      const plotScreenshot = await send('Page.captureScreenshot', { format: 'png' });
      await writeFile(join(tmpdir(), 'alter-ego-a05-390-plot.png'), Buffer.from(plotScreenshot.data, 'base64'));
    }
  }
  console.log('PASS browser: 390px and 1280px layouts have no horizontal overflow');
  // A06: presentation-only, role-restricted workflow and reveal privacy.
  async function selectWell(id) {
    await evaluate(`([...document.querySelectorAll('.well-list button')].find(button => button.querySelector('span').textContent === ${JSON.stringify(id)})).click()`);
    await waitText(`Selected well: ${id}.`);
  }
  async function clickDemo(id, mode) {
    await evaluate(`document.getElementById(${JSON.stringify(id)}).click()`);
    for (let i = 0; i < 100; i++) {
      if (await evaluate(`document.getElementById('outage-state')?.dataset.mode === ${JSON.stringify(mode)}`)) return;
      await pause(50);
    }
    throw new Error(`Demo did not reach ${mode}`);
  }
  async function assertHidden() {
    assert.equal(await evaluate('document.querySelectorAll(".history-observed").length'), 0);
    assert.equal(await evaluate('document.querySelector(".history-table thead").textContent.includes("Revealed")'), false);
    assert.equal(await evaluate('!!document.querySelector(".history-tooltip")'), false);
  }
  const demoRequests = batchRequests;
  for (const width of [1280, 390]) {
    await send('Emulation.setDeviceMetricsOverride', { width, height: 1000, deviceScaleFactor: 1, mobile: width < 700 });
    for (const well of fixturePredictions.wells.filter(well => well.role === 'holdout')) {
      await selectWell(well.id);
      for (const method of ['idw', 'gcn_lstm', 'gcn_lstm_physics']) {
        await chooseMethod(method);
        await assertHidden();
        assert.equal(await evaluate('document.getElementById("reveal-observations").disabled'), true);
        for (let cycle = 0; cycle < 2; cycle++) {
          await clickDemo('simulate-outage', 'simulated-outage'); await assertHidden();
          await clickDemo('reveal-observations', 'reveal');
          assert.deepEqual(await evaluate('[...document.querySelectorAll(".history-table tbody tr")].map(row => row.lastElementChild.textContent)'), well.observations_m.map(value => value === null ? 'Missing' : `${value} m`));
          assert.ok(await evaluate('document.querySelector(".history-panel").innerText.includes("Revealed withheld readings")'));
          await clickDemo('reset-outage', 'sensor-available'); await assertHidden();
          assert.equal(await evaluate('document.getElementById("show-idw").checked'), false);
        }
      }
    }
    assert.ok(await evaluate('document.documentElement.scrollWidth <= window.innerWidth'));
  }
  assert.equal(batchRequests, demoRequests, 'Demo buttons and selection cause no data requests or training call');
  console.log('PASS browser: 24 outage/reveal/reset cycles across both held-out wells, all methods, desktop/mobile; null truth retained; no new fetches');
  await clickDemo('simulate-outage', 'simulated-outage'); await clickDemo('reveal-observations', 'reveal');
  await chooseMethod('idw'); await assertHidden();
  await clickDemo('simulate-outage', 'simulated-outage'); await clickDemo('reveal-observations', 'reveal');
  await selectWell(heldout.id); await assertHidden();
  await clickDemo('simulate-outage', 'simulated-outage');
  await chooseMethod('gcn_lstm'); await assertHidden();
  assert.equal(await evaluate('document.getElementById("outage-state").dataset.mode'), 'sensor-available');
  await evaluate('document.getElementById("simulate-outage").focus()');
  await send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Enter', code: 'Enter', text: '\r', windowsVirtualKeyCode: 13 });
  await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13 });
  await waitText('Simulated outage');
  await assertHidden();
  await hoverFirstHistoryPoint();
  assert.equal(await evaluate('document.querySelector(".history-tooltip").innerText.includes("Revealed withheld reading:")'), false);
  await clickDemo('reveal-observations', 'reveal');
  await hoverFirstHistoryPoint();
  assert.ok(await evaluate('document.querySelector(".history-tooltip").innerText.includes("Revealed withheld reading:")'));
  await clickDemo('reset-outage', 'sensor-available'); await assertHidden();
  for (const well of fixturePredictions.wells.filter(well => well.role !== 'holdout')) {
    await selectWell(well.id);
    assert.equal(await evaluate('document.querySelectorAll(".outage-controls").length'), 0);
  }
  console.log('PASS browser: switches before/after reveal reset privacy; keyboard action and reveal/outage tooltip checks; nonheldout roles have no demo controls');
  for (const scenario of ['outage-unavailable', 'outage-no-truth']) {
    await navigate(scenario); await waitText('6 wells loaded'); await selectWell(heldout.id);
    await clickDemo('simulate-outage', 'simulated-outage'); await assertHidden();
    await clickDemo('reveal-observations', 'reveal');
    if (scenario === 'outage-unavailable') assert.ok((await evaluate('document.querySelector(".history-panel").innerText')).includes('Selected-method predictions are unavailable'));
    else {
      await waitText('No exported observations are available');
      assert.ok((await evaluate('[...document.querySelectorAll(".history-table tbody tr")].map(row => row.lastElementChild.textContent)')).every(value => value === 'Missing'));
    }
    await clickDemo('reset-outage', 'sensor-available'); await assertHidden();
  }
  await navigate('valid'); await waitText('6 wells loaded'); await selectWell(heldout.id);
  await clickDemo('simulate-outage', 'simulated-outage'); await clickDemo('reveal-observations', 'reveal');
  await navigate('new-batch'); await waitText('browser-test-new-dataset'); await selectWell(heldout.id); await assertHidden();
  assert.equal(await evaluate('document.getElementById("outage-state").dataset.mode'), 'sensor-available');
  await clickDemo('simulate-outage', 'simulated-outage'); await clickDemo('reveal-observations', 'reveal');
  await evaluate('document.querySelector(".outage-controls").scrollIntoView({ block: "start" })');
  const demoScreenshot = await send('Page.captureScreenshot', { format: 'png' });
  await writeFile(join(tmpdir(), 'alter-ego-a06-mobile.png'), Buffer.from(demoScreenshot.data, 'base64'));
  console.log('PASS browser: unavailable predictions, absent truth and new dataset reset safely; mobile demo screenshot captured');
  assert.deepEqual(exceptions, [], 'No uncaught browser runtime exceptions');
  console.log('PASS browser: no uncaught runtime exceptions');
  console.log(`INFO browser: ${canceledInterceptions} canceled CDP interceptions during cleanup/refresh`);
} finally {
  if (send && socket?.readyState === WebSocket.OPEN) await send('Browser.close').catch(() => {});
  socket?.close();
  browser.kill();
  await pause(500);
  const cleanupPath = resolve(profile);
  if (dirname(cleanupPath) === resolve(tmpdir()) && basename(cleanupPath).startsWith('alter-ego-a02-')) {
    await rm(cleanupPath, { recursive: true, force: true }).catch(() => {});
  }
}
