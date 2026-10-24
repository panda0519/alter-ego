import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { methodLabels, priorityRows, resultRows, resultValue } from '../src/data/results.ts';
import { validateBatch } from '../src/data/loadBatch.ts';

const names = ['predictions', 'metrics', 'run_info', 'agent_context'];
const batch = Object.fromEntries(await Promise.all(names.map(async name => [name,
  JSON.parse(await readFile(new URL(`../public/data/${name}.json`, import.meta.url), 'utf8')),
])));
for (const method of ['idw', 'gcn_lstm', 'gcn_lstm_physics']) {
  test(`${method} priorities/reasons use only its own exported summaries`, () => {
    const before = JSON.stringify(batch);
    const rows = priorityRows(batch, method);
    assert.deepEqual(rows.map(row => row.id), ['SYN-006', 'SYN-005', 'SYN-004', 'SYN-003', 'SYN-002', 'SYN-001']);
    for (const row of rows) assert.equal(row.summary, batch.predictions.wells.find(well => well.id === row.id).summaries[method]);
    assert.equal(JSON.stringify(batch), before);
  });
}
test('display order respects exported category rather than deriving a new flag from change', () => {
  const altered = structuredClone(batch);
  altered.predictions.wells[0].summaries.idw.priority = 'high';
  altered.predictions.wells[0].summaries.idw.change_30d_m = -1;
  const rows = priorityRows(altered, 'idw');
  assert.equal(rows[2].id, 'SYN-001');
  assert.equal(rows[2].priority, 'high');
});
test('missing summary/series shows unknown and stable ID breaks ties', () => {
  const altered = structuredClone(batch);
  for (const well of altered.predictions.wells) well.predictions_m.idw.fill(null);
  assert.deepEqual(priorityRows(altered, 'idw').map(row => row.id), altered.predictions.wells.map(well => well.id));
  assert.ok(priorityRows(altered, 'idw').every(row => row.summary === null && row.priority === 'unknown'));
});
test('fixture/not_run metrics never report numeric errors or evaluation counts', () => {
  assert.ok(resultRows(batch).every(row => !row.completed && row.testMae === null && row.testPairs === null));
  assert.equal(resultValue(null, ' m'), 'Unavailable');
});
test('completed/failed/not_run paths consume validated test-only values without replacing methods', () => {
  // Branch-coverage data only. This object is never saved/published as a run.
  const altered = structuredClone(batch);
  for (const value of Object.values(altered)) {
    value.meta.artifact_kind = 'model_output'; value.meta.caption = 'TEST ONLY - no experiment';
  }
  Object.assign(altered.metrics.methods.idw, { status: 'completed', validation_mae_m: 0, test_mae_m: 0, test_rmse_m: 0, validation_pairs: 1, test_pairs: 1, test_wells: 1 });
  altered.metrics.methods.gcn_lstm.status = 'failed';
  const rows = resultRows(validateBatch(altered));
  assert.equal(rows[0].testMae, 0); assert.equal(rows[0].testPairs, 1);
  assert.equal(resultValue(rows[0].testMae, ' m'), '0 m');
  assert.equal(rows[1].status, 'failed'); assert.equal(rows[1].testMae, null);
  assert.equal(rows[2].status, 'not_run'); assert.equal(rows[2].testMae, null);
  assert.equal(rows[2].method, 'gcn_lstm_physics');
  assert.ok(methodLabels.gcn_lstm_physics.includes('water-balance regulariser'));
});
test('fixture cannot claim completed metrics even if raw status is tampered', () => {
  const altered = structuredClone(batch); altered.metrics.methods.idw.status = 'completed';
  assert.equal(resultRows(altered)[0].testMae, null);
  assert.throws(() => validateBatch(altered));
});
test('priority/result projection is unaffected by withheld observation changes', () => {
  const altered = structuredClone(batch);
  altered.predictions.wells.forEach(well => well.observations_m.fill(999999));
  assert.deepEqual(priorityRows(altered, 'idw'), priorityRows(batch, 'idw'));
  assert.deepEqual(resultRows(altered), resultRows(batch));
});
