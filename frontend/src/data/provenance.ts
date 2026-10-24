import type { Batch } from './models.ts';
import handoff from './handoff.json' with { type: 'json' };

export function reportedTrainingRevisions(batch: Batch): string[] {
  const meta = batch.predictions.meta;
  return meta.run_id === handoff.run_id && meta.dataset_id === handoff.dataset_id
    && batch.run_info.code_revision === handoff.export_code_revision
    ? handoff.reported_training_code_revisions : [];
}

// Presentation of export status only; this does not certify a scientific run.
export function provisionalReasons(batch: Batch): string[] {
  if (batch.predictions.meta.artifact_kind === 'fixture') return [];
  const reasons: string[] = [];
  if (batch.metrics.methods.gcn_lstm_physics.status !== 'completed') reasons.push('Physics reconstruction is not completed.');
  if (batch.run_info.selected_positive_lambda === null) reasons.push('Positive-lambda selection is unavailable.');
  if (!batch.run_info.code_revision || batch.run_info.code_revision.includes('+dirty')
    || reportedTrainingRevisions(batch).some(revision => revision.includes('+dirty'))) reasons.push('Training/source provenance remains unresolved.');
  return reasons;
}
