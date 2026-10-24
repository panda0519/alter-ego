import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { loadBatch, validateBatch } from '../src/data/loadBatch.ts';

const names = ['predictions', 'metrics', 'run_info', 'agent_context'];
const fixture = Object.fromEntries(await Promise.all(names.map(async name => [name,
  JSON.parse(await readFile(new URL(`../../contracts/fixtures/${name}.json`, import.meta.url), 'utf8')),
])));
const fresh = () => structuredClone(fixture);

test('published files are byte-for-byte copies of the complete fixture batch', async () => {
  for (const name of names) {
    assert.deepEqual(await readFile(new URL(`../public/data/${name}.json`, import.meta.url)),
      await readFile(new URL(`../../contracts/fixtures/${name}.json`, import.meta.url)));
  }
});
test('valid fixture retains identity, type, dates, counts, nulls and not_run metrics', () => {
  const batch = validateBatch(fresh());
  assert.equal(batch.predictions.meta.artifact_kind, 'fixture');
  assert.equal(batch.predictions.meta.dataset_kind, 'synthetic');
  assert.equal(batch.predictions.meta.run_id, 'fixture-layout-v1');
  assert.equal(batch.predictions.dates[0], '2024-08-01');
  assert.equal(batch.predictions.dates.at(-1), '2024-09-29');
  assert.equal(batch.predictions.wells.length, 6);
  assert.equal(batch.predictions.dates.length, 60);
  assert.ok(batch.predictions.wells.some(well => well.observations_m.includes(null)));
  assert.ok(Object.values(batch.metrics.methods).every(metric => metric.status === 'not_run' && metric.test_mae_m === null));
});
for (const [label, mutate, message] of [
  ['schema failure', b => { b.predictions.wells[0].latitude = 'invalid'; }, /predictions.json.*latitude/],
  ['invalid date', b => { b.predictions.dates[0] = '2024-02-30'; }, /predictions.json.*date/],
  ['empty wells', b => { b.predictions.wells = []; }, /predictions.json.*wells/],
  ['empty dates', b => { b.predictions.dates = []; }, /predictions.json.*dates/],
  ['run mismatch', b => { b.metrics.meta.run_id = 'other'; }, /metrics.json.*run_id/],
  ['caption mismatch', b => { b.run_info.meta.caption = 'other'; }, /run_info.json.*caption/],
  ['dataset mismatch', b => { b.agent_context.meta.dataset_id = 'other'; }, /agent_context.json.*dataset_id/],
  ['short observations', b => { b.predictions.wells[0].observations_m.pop(); }, /observations_m length/],
  ['short method series', b => { b.predictions.wells[0].predictions_m.gcn_lstm.pop(); }, /gcn_lstm series length/],
  ['duplicate dates', b => { b.predictions.dates[1] = b.predictions.dates[0]; }, /unique and chronological/],
  ['reversed dates', b => { b.predictions.dates.reverse(); }, /chronological/],
  ['wrong as-of', b => { for (const value of Object.values(b)) value.meta.as_of_date = '2024-10-01'; }, /final series date/],
  ['duplicate well', b => { b.predictions.wells[1].id = b.predictions.wells[0].id; }, /duplicate well/],
  ['agent duplicate', b => { b.agent_context.wells[1] = b.agent_context.wells[0]; }, /well IDs/],
  ['agent summary mismatch', b => { b.agent_context.wells[0].priority = 'high'; }, /summary mismatch/],
  ['agent truth leak', b => { b.agent_context.wells[0].observations_m = [1]; }, /additional properties/],
  ['nonfinite number', b => { b.predictions.wells[0].predictions_m.idw[0] = Infinity; }, /predictions.json/],
  ['false metric result', b => { b.metrics.methods.idw.test_mae_m = 1; }, /values do not match/],
]) {
  test(`rejects ${label}`, () => { const batch = fresh(); mutate(batch); assert.throws(() => validateBatch(batch), message); });
}
test('accepts a differently identified model_output batch without fixture assumptions', () => {
  // Compatibility test only: this object is never published as a scientific result.
  const batch = fresh();
  for (const value of Object.values(batch)) {
    value.meta.artifact_kind = 'model_output';
    value.meta.dataset_kind = 'real';
    value.meta.run_id = 'compatibility-test';
    value.meta.dataset_id = 'different-dataset';
  }
  assert.equal(validateBatch(batch).predictions.meta.run_id, 'compatibility-test');
});
test('loader fetches all four files with no-store and the provided abort signal', async () => {
  const calls = [];
  const controller = new AbortController();
  await loadBatch(controller.signal, async (url, options) => {
    calls.push(url);
    assert.equal(options.cache, 'no-store');
    assert.equal(options.signal, controller.signal);
    return Response.json(fixture[url.split('/').at(-1).replace('.json', '')]);
  });
  assert.equal(new Set(calls).size, 4);
});
for (const [label, responder, kind, message] of [
  ['HTTP missing', () => new Response('', { status: 404 }), 'missing', /HTTP 404/],
  ['empty body', () => new Response('  '), 'missing', /empty/],
  ['malformed JSON', () => new Response('{'), 'invalid', /not valid JSON/],
  ['network failure', () => { throw new TypeError('network'); }, 'missing', /connection/],
]) {
  test(`loader handles ${label}`, async () => {
    await assert.rejects(loadBatch(undefined, async () => responder()), error => error.kind === kind && message.test(error.message));
  });
}
test('abort remains abort rather than a missing-data error', async () => {
  const controller = new AbortController(); controller.abort();
  await assert.rejects(loadBatch(controller.signal, async () => { throw new DOMException('Aborted', 'AbortError'); }), { name: 'AbortError' });
});
