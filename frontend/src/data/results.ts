import { methods } from './models.ts';
import type { Batch, Method, Summary } from './models.ts';
import { resolveSelection } from './selection.ts';

export const methodLabels: Record<Method, string> = {
  idw: 'IDW', gcn_lstm: 'GCN + LSTM', gcn_lstm_physics: 'GCN + LSTM + water-balance regulariser',
};
const priorityOrder: Record<Summary['priority'], number> = { high: 0, watch: 1, normal: 2, unknown: 3 };

export function priorityRows(batch: Batch, method: Method) {
  return batch.predictions.wells.map(well => {
    const { summary } = resolveSelection(batch, { wellId: well.id, method });
    return { id: well.id, role: well.role, summary, priority: summary?.priority ?? 'unknown' };
  }).sort((a, b) => priorityOrder[a.priority] - priorityOrder[b.priority]
    || (b.summary?.change_30d_m ?? -Infinity) - (a.summary?.change_30d_m ?? -Infinity)
    || (a.id < b.id ? -1 : a.id > b.id ? 1 : 0));
}

export function resultRows(batch: Batch) {
  return methods.map(method => {
    const metric = batch.metrics.methods[method];
    // Fixture/not_run/failed values never become reported experimental results.
    const completed = batch.metrics.meta.artifact_kind !== 'fixture' && metric.status === 'completed';
    return { method, status: metric.status, completed,
      validationMae: completed ? metric.validation_mae_m : null,
      testMae: completed ? metric.test_mae_m : null,
      testRmse: completed ? metric.test_rmse_m : null,
      validationPairs: completed ? metric.validation_pairs : null,
      testPairs: completed ? metric.test_pairs : null,
      testWells: completed ? metric.test_wells : null,
      lambda: completed ? metric.lambda : null };
  });
}

export function resultValue(value: number | null, unit = ''): string {
  return value === null ? 'Unavailable' : `${value}${unit}`;
}
