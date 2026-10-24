// Windows browser acceptance check using installed Edge and Node's built-in CDP client.
// Run against the production preview: node checks/browser.mjs
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, resolve, dirname, basename } from 'node:path';

const origin = 'http://127.0.0.1:4173';
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
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
      if (scenario === 'loading') { held.push(requestId); return; }
      const name = new URL(request.url).pathname.split('/').at(-1);
      void (async () => {
        if (scenario === 'valid') return send('Fetch.continueRequest', { requestId });
        let body = await readFile(new URL(`../public/data/${name}`, import.meta.url), 'utf8');
        let responseCode = 200;
        if (name === 'predictions.json') {
          if (scenario === 'malformed') body = '{';
          if (scenario === 'missing') { body = ''; responseCode = 404; }
          if (scenario === 'empty') body = '';
          if (scenario === 'schema') { const value = JSON.parse(body); value.wells = []; body = JSON.stringify(value); }
        }
        if (scenario === 'mixed' && name === 'metrics.json') {
          const value = JSON.parse(body); value.meta.run_id = 'wrong-run'; body = JSON.stringify(value);
        }
        return send('Fetch.fulfillRequest', { requestId, responseCode, responseHeaders: [{ name: 'Content-Type', value: 'application/json' }], body: Buffer.from(body).toString('base64') });
      })().catch(error => exceptions.push(error.message));
    }
  };
  await send('Runtime.enable');
  await send('Page.enable');
  await send('Fetch.enable', { patterns: [{ urlPattern: '*/data/*.json' }] });
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
  console.log('PASS browser: real production batch, type/dates/counts and fixture warning');
  for (const [mode, text] of [['malformed', 'not valid JSON'], ['missing', 'HTTP 404'], ['empty', 'is empty'], ['schema', 'must NOT have fewer than 1 items'], ['mixed', 'metadata mismatch at run_id']]) {
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
  for (const width of [390, 1280]) {
    await send('Emulation.setDeviceMetricsOverride', { width, height: 900, deviceScaleFactor: 1, mobile: width < 700 });
    assert.ok(await evaluate('document.documentElement.scrollWidth <= window.innerWidth'), `No horizontal overflow at ${width}px`);
  }
  console.log('PASS browser: 390px and 1280px layouts have no horizontal overflow');
  assert.deepEqual(exceptions, [], 'No uncaught browser runtime exceptions');
  console.log('PASS browser: no uncaught runtime exceptions');
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
