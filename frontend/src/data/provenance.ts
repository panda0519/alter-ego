import type { Batch } from './models.ts';

// Presentation of export status only; this does not certify a scientific run.
export function provisionalReasons(batch: Batch): string[] {
  if (batch.predictions.meta.artifact_kind === 'fixture') return [];
  const reasons: string[] = [];
  if (batch.metrics.methods.gcn_lstm_physics.status !== 'completed') reasons.push('Physics reconstruction is not completed.');
  if (batch.run_info.selected_positive_lambda === null) reasons.push('Positive-lambda selection is unavailable.');
  if (!batch.run_info.code_revision || batch.run_info.code_revision.includes('+dirty')) reasons.push('Source provenance is unresolved.');
  return reasons;
}
