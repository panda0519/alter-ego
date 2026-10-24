import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { depthLabel, initialSelection, methodAvailable, resolveSelection } from '../src/data/selection.ts';

const names = ['predictions', 'metrics', 'run_info', 'agent_context'];
const batch = Object.fromEntries(await Promise.all(names.map(async name => [name,
  JSON.parse(await readFile(new URL(`../../contracts/fixtures/${name}.json`, import.meta.url), 'utf8')),
])));
const methods = ['idw', 'gcn_lstm', 'gcn_lstm_physics'];

test('initial selection uses export order and default method rather than fixture IDs', () => {
  const different = structuredClone(batch);
  different.predictions.wells[0].id = 'another-well';
  different.predictions.meta.default_method = 'gcn_lstm_physics';
  assert.deepEqual(initialSelection(different), { wellId: 'another-well', method: 'gcn_lstm_physics' });
});
for (const well of batch.predictions.wells) {
  for (const method of methods) {
    test(`${well.id}/${method} returns its own exported metadata/summary without mutation`, () => {
      const before = JSON.stringify(batch);
      const selected = resolveSelection(batch, { wellId: well.id, method });
      assert.equal(selected.well, well);
      assert.equal(selected.method, method);
      assert.equal(selected.summary, well.summaries[method]);
      assert.equal(selected.available, true);
      assert.equal(JSON.stringify(batch), before);
    });
  }
}
test('invalid well/method never returns previous or fallback summary', () => {
  for (const selection of [{ wellId: 'missing', method: 'idw' }, { wellId: 'SYN-001', method: 'missing' }, { wellId: 'SYN-001', method: '__proto__' }]) {
    const result = resolveSelection(batch, selection);
    assert.equal(result.summary, null);
    assert.equal(result.available, false);
  }
});
test('null is unknown; zero and negative changes are preserved', () => {
  assert.equal(depthLabel(null), 'Unknown');
  assert.equal(depthLabel(undefined), 'Unknown');
  assert.equal(depthLabel(0), '0 m');
  assert.equal(depthLabel(-0.652), '-0.652 m');
});
test('all-null method stays unavailable with no substitution even if its summary is inconsistent', () => {
  const altered = structuredClone(batch);
  altered.predictions.wells[0].predictions_m.gcn_lstm.fill(null);
  const selected = resolveSelection(altered, { wellId: 'SYN-001', method: 'gcn_lstm' });
  assert.equal(selected.method, 'gcn_lstm');
  assert.equal(selected.available, false);
  assert.equal(selected.summary, null);
});
test('partial series and null exported endpoints remain inspectable without recalculation', () => {
  const altered = structuredClone(batch);
  const well = altered.predictions.wells[0];
  well.predictions_m.gcn_lstm[59] = null;
  well.summaries.gcn_lstm.latest_depth_m = null;
  well.summaries.gcn_lstm.change_30d_m = null;
  well.summaries.gcn_lstm.priority = 'unknown';
  const selected = resolveSelection(altered, { wellId: well.id, method: 'gcn_lstm' });
  assert.equal(selected.available, true);
  assert.equal(selected.summary.latest_depth_m, null);
  assert.equal(selected.summary.change_30d_m, null);
  assert.equal(selected.summary.priority, 'unknown');
});
test('nonfixture failed/not_run methods unavailable; completed requires a nonnull series', () => {
  const altered = structuredClone(batch);
  altered.predictions.meta.artifact_kind = 'model_output';
  const well = altered.predictions.wells[0];
  for (const status of ['failed', 'not_run']) {
    altered.metrics.methods.gcn_lstm.status = status;
    assert.equal(methodAvailable(altered, well, 'gcn_lstm'), false);
  }
  altered.metrics.methods.gcn_lstm.status = 'completed';
  assert.equal(methodAvailable(altered, well, 'gcn_lstm'), true);
  well.predictions_m.gcn_lstm.fill(null);
  assert.equal(methodAvailable(altered, well, 'gcn_lstm'), false);
});
test('empty well data safely yields no selection', () => {
  const altered = structuredClone(batch); altered.predictions.wells = [];
  assert.equal(initialSelection(altered).wellId, '');
  assert.equal(resolveSelection(altered, initialSelection(altered)).summary, null);
});
