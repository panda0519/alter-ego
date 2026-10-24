import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { buildHistory, historyValue } from '../src/data/history.ts';

const names = ['predictions', 'metrics', 'run_info', 'agent_context'];
const batch = Object.fromEntries(await Promise.all(names.map(async name => [name,
  JSON.parse(await readFile(new URL(`../../contracts/fixtures/${name}.json`, import.meta.url), 'utf8')),
])));
const overlays = { showIdw: true, showObservations: true };
for (const well of batch.predictions.wells) {
  for (const method of ['idw', 'gcn_lstm', 'gcn_lstm_physics']) {
    test(`history aligns ${well.id}/${method} without leaking hidden observations`, () => {
      const before = JSON.stringify(batch);
      const history = buildHistory(batch, { wellId: well.id, method }, overlays);
      assert.equal(history.points.length, batch.predictions.dates.length);
      history.points.forEach((point, index) => {
        assert.equal(point.date, batch.predictions.dates[index]);
        assert.equal(new Date(point.timestamp).toISOString().slice(0, 10), point.date);
        assert.equal(point.reconstructed, well.predictions_m[method][index]);
        assert.equal(point.idw, method === 'idw' ? null : well.predictions_m.idw[index]);
        assert.equal(point.observed, well.role === 'holdout' ? null : well.observations_m[index]);
      });
      assert.equal(JSON.stringify(batch), before);
    });
  }
}
test('holdout truth changes cannot affect plotted data, including its y-domain inputs', () => {
  const altered = structuredClone(batch);
  const well = altered.predictions.wells.find(well => well.role === 'holdout');
  const selection = { wellId: well.id, method: 'gcn_lstm' };
  const before = buildHistory(altered, selection, overlays).plotPoints;
  well.observations_m.fill(999999);
  assert.deepEqual(buildHistory(altered, selection, overlays).plotPoints, before);
});
test('hidden overlay preferences never enter payload and IDW is not duplicated', () => {
  const history = buildHistory(batch, { wellId: 'SYN-001', method: 'idw' }, { showIdw: true, showObservations: false });
  assert.ok(history.points.every(point => point.observed === null && point.idw === null));
  assert.equal(history.idwVisible, false);
});
test('null runs remain null while zero is a valid depth', () => {
  const altered = structuredClone(batch);
  altered.predictions.wells[0].predictions_m.gcn_lstm.splice(4, 3, null, null, 0);
  const history = buildHistory(altered, { wellId: 'SYN-001', method: 'gcn_lstm' }, overlays);
  assert.deepEqual(history.points.slice(4, 7).map(point => point.reconstructed), [null, null, 0]);
  assert.equal(historyValue(null), 'Missing');
  assert.equal(historyValue(0), '0 m');
});
test('omitted dates break paths with a null separator at a supplied timestamp', () => {
  const altered = structuredClone(batch);
  altered.predictions.dates.splice(5, 1);
  for (const well of altered.predictions.wells) {
    well.observations_m.splice(5, 1);
    Object.values(well.predictions_m).forEach(values => values.splice(5, 1));
  }
  const history = buildHistory(altered, { wellId: 'SYN-001', method: 'idw' }, overlays);
  assert.equal(history.points.length, 59);
  assert.equal(history.plotPoints.length, 60);
  assert.equal(history.plotPoints[5].date, '2024-08-07');
  assert.equal(history.plotPoints[5].reconstructed, null);
  assert.ok(history.plotPoints.every(point => altered.predictions.dates.includes(point.date)));
});
test('unavailable selected predictions never substitute IDW unless explicitly requested', () => {
  const altered = structuredClone(batch);
  altered.predictions.wells[0].predictions_m.gcn_lstm.fill(null);
  const selection = { wellId: 'SYN-001', method: 'gcn_lstm' };
  const hidden = buildHistory(altered, selection, { showIdw: false, showObservations: false });
  assert.equal(hidden.hasData, false);
  assert.ok(hidden.points.every(point => point.reconstructed === null && point.idw === null));
  const comparison = buildHistory(altered, selection, { showIdw: true, showObservations: false });
  assert.equal(comparison.hasData, true);
  assert.ok(comparison.points.every(point => point.reconstructed === null));
});
test('empty dates and invalid selection safely return empty history', () => {
  assert.equal(buildHistory(batch, { wellId: 'missing', method: 'idw' }, overlays).points.length, 0);
  assert.equal(buildHistory(batch, { wellId: 'SYN-001', method: 'missing' }, overlays).points.length, 0);
  const altered = structuredClone(batch); altered.predictions.dates = [];
  assert.equal(buildHistory(altered, { wellId: 'SYN-001', method: 'idw' }, overlays).hasData, false);
});
test('incomplete arrays defensively become null, never extra or shifted readings', () => {
  const altered = structuredClone(batch);
  altered.predictions.wells[0].observations_m = [];
  altered.predictions.wells[0].predictions_m.gcn_lstm = [0];
  const history = buildHistory(altered, { wellId: 'SYN-001', method: 'gcn_lstm' }, overlays);
  assert.equal(history.points[0].reconstructed, 0);
  assert.ok(history.points.slice(1).every(point => point.reconstructed === null));
  assert.ok(history.points.every(point => point.observed === null));
});
test('one date stays one date and failed model-output methods remain unavailable', () => {
  const altered = structuredClone(batch); altered.predictions.dates = ['2024-08-01'];
  altered.predictions.meta.artifact_kind = 'model_output';
  altered.metrics.methods.gcn_lstm.status = 'failed';
  const history = buildHistory(altered, { wellId: 'SYN-001', method: 'gcn_lstm' }, { showIdw: false, showObservations: false });
  assert.equal(history.points.length, 1);
  assert.equal(history.hasData, false);
});
