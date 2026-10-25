import { methods } from './models.ts';
import type { Batch, Method, Well } from './models.ts';

export interface Selection { wellId: string; method: string }

export function firstHoldoutId(batch: Batch): string | undefined {
  return batch.predictions.wells.find(well => well.role === 'holdout')?.id;
}

export function initialSelection(batch: Batch): Selection {
  const well = batch.predictions.wells.find(item => item.role === 'holdout') ?? batch.predictions.wells[0];
  return { wellId: well?.id ?? '', method: batch.predictions.meta.default_method };
}

export function methodAvailable(batch: Batch, well: Well, method: Method): boolean {
  const status = batch.metrics.methods[method].status;
  const permitted = batch.predictions.meta.artifact_kind === 'fixture'
    ? status !== 'failed'
    : status === 'completed';
  return permitted && well.predictions_m[method].some(value => value !== null);
}

export function resolveSelection(batch: Batch, selection: Selection) {
  const well = batch.predictions.wells.find(well => well.id === selection.wellId);
  const method = methods.find(method => method === selection.method);
  if (!well || !method) return { well, method, available: false, summary: null };
  const available = methodAvailable(batch, well, method);
  return { well, method, available, summary: available ? well.summaries[method] : null };
}

export function depthLabel(value: number | null | undefined): string {
  return value == null ? 'Unknown' : `${value} m`;
}
