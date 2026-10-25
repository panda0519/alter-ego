import type { Batch, Method, Summary } from './models.ts';

export const methodTitles: Record<Method, string> = {
  idw: 'IDW',
  gcn_lstm: 'GCN-LSTM',
  gcn_lstm_physics: 'Physics-enhanced GCN-LSTM',
};

const priorityLabels: Record<Summary['priority'], string> = {
  high: 'High',
  watch: 'Watch',
  normal: 'Normal',
  unknown: 'Unknown',
};

export function priorityLabel(priority: Summary['priority'] | undefined): string {
  return priorityLabels[priority ?? 'unknown'];
}

export function statusLabel(status: 'not_run' | 'completed' | 'failed'): string {
  if (status === 'not_run') return 'Not available';
  if (status === 'failed') return 'Failed';
  return 'Completed';
}

export function formatDepth(value: number | null | undefined, digits = 2): string {
  if (value == null || !Number.isFinite(value)) return 'Unknown';
  return `${value.toFixed(digits)} m`;
}

export function changeText(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return 'Unknown';
  const amount = `${Math.abs(value).toFixed(2)} m`;
  if (value > 0) return `${amount} deeper`;
  if (value < 0) return `${amount} shallower`;
  return `${amount} no change`;
}

export function roundMetric(value: number | null, digits = 3): string {
  if (value == null || !Number.isFinite(value)) return 'Unavailable';
  return `${value.toFixed(digits)} m`;
}

export function holdoutComparison(batch: Batch): string | null {
  if (batch.metrics.meta.artifact_kind === 'fixture') return null;
  const idw = batch.metrics.methods.idw;
  const gcn = batch.metrics.methods.gcn_lstm;
  if (idw.status !== 'completed' || gcn.status !== 'completed') return null;
  if (idw.test_mae_m == null || gcn.test_mae_m == null) return null;
  if (idw.test_mae_m < gcn.test_mae_m) {
    return 'IDW has a lower holdout test MAE than GCN-LSTM on this export. The default method was chosen from validation, not from that holdout score.';
  }
  if (idw.test_mae_m > gcn.test_mae_m) {
    return 'GCN-LSTM has a lower holdout test MAE than IDW on this export.';
  }
  return 'IDW and GCN-LSTM have the same holdout test MAE on this export.';
}
