import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { publicHttpsUrl, checkBriefingContext } from '../src/data/briefing.ts';
import { validateAgentContext } from '../src/data/loadBatch.ts';

const expected = JSON.parse(await readFile(new URL('../../contracts/fixtures/agent_context.json', import.meta.url), 'utf8'));
test('missing native configuration remains missing', () => {
  for (const value of [undefined, '', '  ']) assert.equal(publicHttpsUrl(value).kind, 'missing');
});
test('public native URL format accepted without claiming actual service verification', () => {
  // URL parser input only, no service is contacted.
  assert.equal(publicHttpsUrl('https://briefing.example.org/qa').url, 'https://briefing.example.org/qa');
});
test('unsafe, credential-bearing or nonpublic URL formats rejected without exposing them', () => {
  for (const value of ['invalid', 'javascript:alert(1)', 'http://example.org', 'https://user:secret@example.org', 'https://example.org/?token=secret', 'https://example.org/#secret', 'https://localhost', 'https://127.0.0.1', 'https://service.internal']) assert.equal(publicHttpsUrl(value).kind, 'invalid');
});
test('fresh check GET uses no cookies, auth headers, body, selection or measured data', async () => {
  let call;
  const result = await checkBriefingContext(expected, undefined, undefined, async (...args) => { call = args; return Response.json(expected); });
  assert.equal(call[0], '/data/agent_context.json');
  assert.equal(call[1].cache, 'no-store'); assert.equal(call[1].credentials, 'omit');
  assert.equal(call[1].redirect, 'error'); assert.equal(call[1].headers, undefined); assert.equal(call[1].body, undefined);
  assert.deepEqual(result, expected);
});
for (const [name, mutate] of [
  ['run mismatch', value => { value.meta.run_id = 'other'; }],
  ['summary mismatch', value => { value.wells[0].latest_depth_m = null; }],
  ['wrong method', value => { value.wells[0].method = 'gcn_lstm'; }],
  ['duplicate IDs', value => { value.wells[1] = value.wells[0]; }],
  ['observation leak', value => { value.wells[0].observations_m = [1]; }],
  ['limitation drift', value => { value.limitations = []; }],
]) test(`context validator refuses ${name}`, () => {
  const value = structuredClone(expected); mutate(value);
  assert.throws(() => validateAgentContext(value, expected));
});
for (const [name, response, kind] of [
  ['missing file', () => new Response('', { status: 404 }), 'unavailable'],
  ['empty file', () => new Response(''), 'invalid-response'],
  ['bad JSON', () => new Response('{'), 'invalid-response'],
  ['network failure', () => { throw new TypeError('offline'); }, 'network-error'],
]) test(`check handles ${name}`, async () => {
  await assert.rejects(checkBriefingContext(expected, undefined, undefined, async () => response()), error => error.kind === kind);
});
test('check rejects stale or observation-bearing responses', async () => {
  const value = structuredClone(expected); value.observations_m = [1];
  await assert.rejects(checkBriefingContext(expected, undefined, undefined, async () => Response.json(value)), error => error.kind === 'invalid-response');
});
test('timeout is bounded and distinct from user cancellation', async () => {
  const never = async (_url, options) => new Promise((_resolve, reject) => options.signal.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError'))));
  await assert.rejects(checkBriefingContext(expected, undefined, undefined, never, 5), error => error.kind === 'timeout');
  const controller = new AbortController();
  const pending = checkBriefingContext(expected, undefined, controller.signal, never);
  controller.abort();
  await assert.rejects(pending, error => error.name === 'AbortError');
});
