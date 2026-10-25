import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile, readdir } from 'node:fs/promises';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { validateBatch } from '../src/data/loadBatch.ts';
import { answerFromExport, askAssistant, assistantEndpoint } from '../src/data/assistant.ts';
import { selectView } from '../src/data/view.ts';
import { createAssistantState, handleAssistant } from '../../agent/proxy/assistant-core.mjs';

const names = ['predictions', 'metrics', 'run_info', 'agent_context'];
const fixture = validateBatch(Object.fromEntries(await Promise.all(names.map(async name => [name,
  JSON.parse(await readFile(new URL(`../../contracts/fixtures/${name}.json`, import.meta.url), 'utf8')),
]))));

test('navigation keeps analysis as the station action and preserves the three views', () => {
  assert.equal(selectView('analyze'), 'analysis');
  assert.equal(selectView('stations'), 'stations');
  assert.equal(selectView('assistant'), 'assistant');
});

test('assistant endpoint accepts only a local or public proxy URL', () => {
  assert.equal(assistantEndpoint(undefined).kind, 'missing');
  assert.equal(assistantEndpoint('/api/assistant').url, '/api/assistant');
  assert.equal(assistantEndpoint('http://127.0.0.1:8787/api/assistant').kind, 'configured');
  assert.equal(assistantEndpoint('http://127.0.0.1:8787/api/assistant?token=secret').kind, 'invalid');
  assert.equal(assistantEndpoint('https://user:pass@example.com/api').kind, 'invalid');
});

test('export briefing ranks stations, explains one station, and states limitations without measurements', () => {
  const ranked = answerFromExport(fixture, 'Which stations should I inspect first?');
  assert.equal(ranked.source, 'export-briefing');
  assert.ok(ranked.text.indexOf('SYN-006') < ranked.text.indexOf('SYN-005'));
  assert.doesNotMatch(ranked.text, /observations_m/);
  const explained = answerFromExport(fixture, 'Explain this station.', 'SYN-001', 'gcn_lstm');
  assert.match(explained.text, /SYN-001/);
  assert.match(explained.text, /estimate/i);
  assert.match(explained.text, /not a measurement/i);
  assert.match(explained.text, /chart method is gcn_lstm/i);
  const missing = answerFromExport(fixture, 'Explain this station.', 'MISSING');
  assert.match(missing.text, /not in this export/);
  const limits = answerFromExport(fixture, 'What are the limitations?');
  assert.match(limits.text, /fixture/);
  assert.match(limits.text, /not forecasting/i);
  const graph = answerFromExport(fixture, 'What does this graph show?', 'SYN-005');
  assert.match(graph.text, /not a forecast/i);
  assert.doesNotMatch(graph.text, /observations_m/);
  const methods = answerFromExport(fixture, 'How do the reconstruction methods compare?');
  assert.match(methods.text, /not_run|not available|Accuracy is not available/i);
});

test('unconfigured proxy falls back to the export briefing without calling the network', async () => {
  let called = false;
  const reply = await askAssistant(fixture, { question: 'What are the limitations?' }, undefined, async () => { called = true; throw new Error('network'); });
  assert.equal(called, false);
  assert.equal(reply.source, 'export-briefing');
  assert.match(reply.text, /fixture/);
});

test('proxy rejects secrets, limits, unauthorized calls, bad context, and timeouts', async () => {
  const state = createAssistantState();
  const env = {};
  assert.equal((await handleAssistant({ method: 'GET', bodyText: '{}' }, env, state)).status, 405);
  assert.equal((await handleAssistant({ method: 'POST', bodyText: '{' }, env, state)).payload.error, 'invalid_json');
  assert.equal((await handleAssistant({ method: 'POST', bodyText: JSON.stringify({ question: 'x'.repeat(401) }) }, env, state)).payload.error, 'invalid_question');
  assert.equal((await handleAssistant({ method: 'POST', bodyText: JSON.stringify({ question: 'Hello', url: 'https://evil.example' }) }, env, state)).payload.error, 'forwarding_rejected');
  const locked = { ASSISTANT_DEMO_TOKEN: 'demo-secret' };
  assert.equal((await handleAssistant({ method: 'POST', bodyText: JSON.stringify({ question: 'Hello' }), token: 'wrong' }, locked, createAssistantState())).status, 401);
  const limited = createAssistantState();
  for (let i = 0; i < 8; i += 1) assert.equal((await handleAssistant({ method: 'POST', bodyText: JSON.stringify({ question: 'What are the limitations?' }), ip: '203.0.113.9', now: 1_000 + i }, env, limited)).status, 503);
  assert.equal((await handleAssistant({ method: 'POST', bodyText: JSON.stringify({ question: 'What are the limitations?' }), ip: '203.0.113.9', now: 2_000 }, env, limited)).status, 429);

  const calls = [];
  const configured = { AGENT37_API_URL: 'https://agent.example/v1/chat/completions', AGENT37_API_KEY: 'server-only', AGENT_CONTEXT_URL: 'https://alter-ego.example/data/agent_context.json' };
  const leaked = await handleAssistant({ method: 'POST', bodyText: JSON.stringify({ question: 'Explain SYN-001' }) }, configured, createAssistantState(), async () => ({
    ok: true,
    json: async () => ({ meta: { run_id: 'x' }, wells: [{ id: 'SYN-001', observations_m: [1] }] }),
  }));
  assert.equal(leaked.payload.error, 'context_invalid');
  const timed = await handleAssistant({ method: 'POST', bodyText: JSON.stringify({ question: 'Explain SYN-001' }) }, configured, createAssistantState(), async () => { const error = new Error('timed out'); error.name = 'TimeoutError'; throw error; });
  assert.equal(timed.status, 504);
  const ok = await handleAssistant({ method: 'POST', bodyText: JSON.stringify({ question: 'Explain SYN-001' }) }, configured, createAssistantState(), async (url, options) => {
    calls.push({ url, authorization: options?.headers?.authorization });
    if (String(url).includes('agent_context')) return { ok: true, json: async () => fixture.agent_context };
    return { ok: true, json: async () => ({ choices: [{ message: { content: 'Grounded reply' } }] }) };
  });
  assert.equal(ok.payload.source, 'agent37');
  assert.equal(ok.payload.text, 'Grounded reply');
  assert.equal(calls[1].authorization, 'Bearer server-only');
  assert.equal(JSON.stringify(ok.payload).includes('server-only'), false);
});

test('frontend and proxy source do not contain Agent37 credentials', async () => {
  async function files(dir) {
    const entries = await readdir(dir, { withFileTypes: true });
    const found = [];
    for (const entry of entries) {
      const path = join(dir, entry.name);
      if (entry.isDirectory()) found.push(...await files(path));
      else if (/\.(tsx?|css|mjs|html)$/.test(entry.name)) found.push(path);
    }
    return found;
  }
  const srcFiles = await files(fileURLToPath(new URL('../src/', import.meta.url)));
  const frontend = (await Promise.all(srcFiles.map(path => readFile(path, 'utf8')))).join('\n');
  const proxy = await readFile(fileURLToPath(new URL('../../agent/proxy/assistant-core.mjs', import.meta.url)), 'utf8');
  for (const secret of ['a37_token', 'AGENT37_API_KEY=', 'sk-']) assert.equal(frontend.includes(secret), false, secret);
  assert.equal(proxy.includes('a37_token'), false);
});
