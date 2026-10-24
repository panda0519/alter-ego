import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { validateBatch, loadBatch } from '../src/data/loadBatch.ts';
import { methods } from '../src/data/models.ts';
import { buildHistory } from '../src/data/history.ts';
import { initialWorkspace, workspaceReducer } from '../src/data/outage.ts';
import { resultRows, priorityRows } from '../src/data/results.ts';
import { provisionalReasons } from '../src/data/provenance.ts';

const manifest = JSON.parse(await readFile(new URL('./candidate.json', import.meta.url)));
const raw = {};
for (const [name, hash] of Object.entries(manifest.sha256)) {
  const content = await readFile(new URL(`../public/data/${name}`, import.meta.url));
  assert.equal(createHash('sha256').update(content).digest('hex'), hash, `${name}: exact source bytes`);
  raw[name.replace('.json', '')] = JSON.parse(content);
}
const batch = validateBatch(raw);
test('pinned four-file candidate retains identity, provenance and provisional limitations', () => {
  assert.equal(manifest.source_commit, '473bd2b4ba3c791028c805ea743e23d9a6281b4f');
  assert.equal(batch.predictions.meta.run_id, manifest.run_id);
  assert.equal(batch.predictions.meta.dataset_kind, 'synthetic');
  assert.equal(batch.predictions.meta.artifact_kind, 'model_output');
  assert.equal(batch.predictions.wells.length, 40);
  assert.equal(batch.predictions.dates.length, 60);
  assert.equal(batch.predictions.dates[0], '2024-11-02');
  assert.equal(batch.predictions.dates.at(-1), '2024-12-31');
  assert.ok(batch.run_info.code_revision.endsWith('+dirty'));
  assert.equal(batch.run_info.selected_positive_lambda, null);
  assert.equal(provisionalReasons(batch).length, 3);
});
test('candidate statuses and exported metrics remain exact; physics is unavailable, never zero', () => {
  for (const row of resultRows(batch)) {
    const metric = batch.metrics.methods[row.method];
    assert.equal(row.testMae, metric.test_mae_m);
    assert.equal(row.testRmse, metric.test_rmse_m);
    if (row.method === 'gcn_lstm_physics') {
      assert.equal(row.status, 'not_run'); assert.equal(row.testPairs, null);
      for (const well of batch.predictions.wells) {
        assert.ok(well.predictions_m[row.method].every(value => value === null));
        assert.equal(well.summaries[row.method].priority, 'unknown');
      }
    } else { assert.equal(row.status, 'completed'); assert.equal(row.testPairs, 1109); assert.equal(row.testWells, 8); }
  }
});
test('all 120 candidate selections preserve aligned data, nulls, priorities and reveal privacy', () => {
  for (const well of batch.predictions.wells) for (const method of methods) {
    const selection = { wellId: well.id, method };
    const options = { showIdw: false, showObservations: true };
    const hidden = buildHistory(batch, selection, { ...options, demoMode: 'sensor-available' });
    assert.deepEqual(hidden.points.map(point => point.reconstructed), well.predictions_m[method]);
    assert.deepEqual(hidden.points.map(point => point.date), batch.predictions.dates);
    if (well.role === 'holdout') {
      for (const mode of ['sensor-available', 'simulated-outage']) assert.ok(buildHistory(batch, selection, { ...options, demoMode: mode }).points.every(point => point.observed === null));
      assert.deepEqual(buildHistory(batch, selection, { ...options, demoMode: 'reveal' }).points.map(point => point.observed), well.observations_m);
    }
    const row = priorityRows(batch, method).find(row => row.id === well.id);
    if (method !== 'gcn_lstm_physics') assert.deepEqual(row.summary, well.summaries[method]);
    else assert.equal(row.summary, null);
  }
});
test('repeated candidate outage, reveal, reset and selection transitions clear answers', () => {
  for (const well of batch.predictions.wells.filter(well => well.role === 'holdout')) {
    let state = initialWorkspace(batch);
    state = workspaceReducer(state, { type: 'well', wellId: well.id });
    for (const method of methods) {
      state = workspaceReducer(state, { type: 'method', method });
      for (let cycle = 0; cycle < 2; cycle++) {
        state = workspaceReducer(state, { type: 'demo', action: 'outage', role: well.role });
        state = workspaceReducer(state, { type: 'demo', action: 'reveal', role: well.role });
        assert.equal(state.mode, 'reveal');
        state = workspaceReducer(state, { type: 'demo', action: 'reset', role: well.role });
        assert.equal(state.mode, 'sensor-available');
      }
    }
  }
});
test('agent context contains only contracted summaries, no observation arrays', () => {
  for (const well of batch.agent_context.wells) {
    assert.deepEqual(Object.keys(well).sort(), ['id','role','method','latest_depth_m','change_30d_m','priority','reason_codes'].sort());
    assert.equal(well.method, batch.predictions.meta.default_method);
  }
  assert.equal(JSON.stringify(batch.agent_context).includes('observations_m'), false);
});
test('candidate loader rejects incomplete/mismatched batches and recovers without partial data', async () => {
  const fetcher = (name, response) => async url => url.endsWith(name) ? response : Response.json(raw[url.split('/').at(-1).replace('.json','')]);
  for (const name of Object.keys(manifest.sha256)) {
    await assert.rejects(loadBatch(undefined, fetcher(name, new Response('', { status: 404 }))), /HTTP 404/);
    const mismatch = structuredClone(raw[name.replace('.json','')]); mismatch.meta.dataset_id = 'mismatch';
    await assert.rejects(loadBatch(undefined, fetcher(name, Response.json(mismatch))), /metadata mismatch/);
  }
  const recovered = await loadBatch(undefined, async url => Response.json(raw[url.split('/').at(-1).replace('.json','')]));
  assert.deepEqual(recovered, batch);
});
