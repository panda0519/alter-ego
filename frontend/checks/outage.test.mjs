import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { initialWorkspace, workspaceReducer } from '../src/data/outage.ts';
import { buildHistory } from '../src/data/history.ts';

const names = ['predictions', 'metrics', 'run_info', 'agent_context'];
const batch = Object.fromEntries(await Promise.all(names.map(async name => [name,
  JSON.parse(await readFile(new URL(`../../contracts/fixtures/${name}.json`, import.meta.url), 'utf8')),
])));
const heldouts = batch.predictions.wells.filter(well => well.role === 'holdout');
const demo = (state, action, role = 'holdout') => workspaceReducer(state, { type: 'demo', action, role });

test('reveal requires a prior outage; repeated outage/reveal/reset clears state', () => {
  let state = initialWorkspace(batch);
  assert.equal(demo(state, 'reveal'), state);
  for (let i = 0; i < 5; i++) {
    state = demo(state, 'outage'); assert.equal(state.mode, 'simulated-outage');
    state = demo(state, 'reveal'); assert.equal(state.mode, 'reveal');
    assert.equal(demo(state, 'reveal'), state);
    state = demo(state, 'reset'); assert.equal(state.mode, 'sensor-available');
  }
});
test('nonholdout and missing roles cannot enter demo states', () => {
  const state = initialWorkspace(batch);
  for (const role of ['visible', 'train_masked', undefined]) {
    for (const action of ['outage', 'reveal', 'reset']) {
      assert.equal(workspaceReducer(state, { type: 'demo', action, role }), state);
    }
  }
});
test('well and method switches atomically reset reveal and invalidate cached chart controls', () => {
  let state = initialWorkspace(batch);
  state = workspaceReducer(state, { type: 'well', wellId: heldouts[0].id });
  state = demo(demo(state, 'outage'), 'reveal');
  assert.equal(workspaceReducer(state, { type: 'well', wellId: heldouts[0].id }), state);
  for (const action of [{ type: 'well', wellId: heldouts[1].id }, { type: 'method', method: 'gcn_lstm' }, { type: 'method', method: 'invalid' }]) {
    const next = workspaceReducer(state, action);
    assert.equal(next.mode, 'sensor-available');
    assert.ok(next.chartEpoch > state.chartEpoch);
  }
});
test('reset retains current well/method but resets overlays even in initial mode', () => {
  let state = initialWorkspace(batch);
  state = workspaceReducer(state, { type: 'well', wellId: heldouts[0].id });
  const reset = demo(state, 'reset');
  assert.deepEqual(reset.selection, state.selection);
  assert.ok(reset.chartEpoch > state.chartEpoch);
});
for (const well of heldouts) {
  for (const method of ['idw', 'gcn_lstm', 'gcn_lstm_physics']) {
    test(`${well.id}/${method}: truth only enters payload after reveal; estimates unchanged`, () => {
      const selection = { wellId: well.id, method };
      const before = JSON.stringify(batch);
      for (const mode of ['sensor-available', 'simulated-outage', 'reveal']) {
        const history = buildHistory(batch, selection, { showIdw: true, showObservations: true, demoMode: mode });
        assert.deepEqual(history.points.map(point => point.reconstructed), well.predictions_m[method]);
        assert.deepEqual(history.points.map(point => point.observed), mode === 'reveal' ? well.observations_m : well.observations_m.map(() => null));
        assert.equal(history.observationsVisible, mode === 'reveal');
      }
      assert.equal(JSON.stringify(batch), before);
    });
  }
}
test('outage payload and domain inputs are invariant to changing withheld truth', () => {
  const altered = structuredClone(batch);
  const well = altered.predictions.wells.find(well => well.role === 'holdout');
  const options = { showIdw: true, showObservations: true, demoMode: 'simulated-outage' };
  const selection = { wellId: well.id, method: 'gcn_lstm' };
  const before = buildHistory(altered, selection, options).plotPoints;
  well.observations_m.fill(999999);
  assert.deepEqual(buildHistory(altered, selection, options).plotPoints, before);
});
test('unavailable predictions and null/incomplete truth stay missing after reveal', () => {
  const altered = structuredClone(batch);
  const well = altered.predictions.wells.find(well => well.role === 'holdout');
  well.predictions_m.gcn_lstm.fill(null); well.observations_m = [null, 0];
  const history = buildHistory(altered, { wellId: well.id, method: 'gcn_lstm' }, { showIdw: false, showObservations: false, demoMode: 'reveal' });
  assert.ok(history.points.every(point => point.reconstructed === null));
  assert.equal(history.points[1].observed, 0);
  assert.ok(history.points.slice(2).every(point => point.observed === null));
});
test('new dataset initialization cannot retain a prior selection, reveal or chart epoch', () => {
  const other = structuredClone(batch); other.predictions.meta.dataset_id = 'test-other-batch';
  assert.equal(initialWorkspace(other).mode, 'sensor-available');
  assert.equal(initialWorkspace(other).chartEpoch, 0);
  assert.equal(initialWorkspace(other).selection.method, other.predictions.meta.default_method);
  assert.equal(initialWorkspace(batch).selection.wellId, heldouts[0].id);
});
