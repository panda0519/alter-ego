import type { Batch } from './models.ts';
import { methodAvailable, resolveSelection } from './selection.ts';
import type { Selection } from './selection.ts';

export interface HistoryPoint {
  date: string;
  timestamp: number;
  reconstructed: number | null;
  idw: number | null;
  observed: number | null;
}
export interface HistoryOptions { showIdw: boolean; showObservations: boolean }

export function buildHistory(batch: Batch, selection: Selection, options: HistoryOptions) {
  const { well, method, available } = resolveSelection(batch, selection);
  const observationsVisible = !!well && well.role !== 'holdout' && options.showObservations;
  const idwVisible = !!well && !!method && method !== 'idw' && options.showIdw;
  const idwAvailable = !!well && methodAvailable(batch, well, 'idw');
  const points: HistoryPoint[] = well && method ? batch.predictions.dates.map((date, index) => ({
    date,
    timestamp: Date.parse(`${date}T00:00:00Z`),
    reconstructed: available ? well.predictions_m[method][index] ?? null : null,
    idw: idwVisible && idwAvailable ? well.predictions_m.idw[index] ?? null : null,
    // Hidden truth never enters the chart payload, tooltip, domain or table.
    observed: observationsVisible ? well.observations_m[index] ?? null : null,
  })) : [];
  // A missing calendar date must also break paths. A null separator reuses the
  // next supplied date/x position; it adds no measurement or invented timestamp.
  const plotPoints: HistoryPoint[] = [];
  for (const point of points) {
    const previous = plotPoints.at(-1);
    if (previous && point.timestamp - previous.timestamp > 86400000) {
      plotPoints.push({ ...point, reconstructed: null, idw: null, observed: null });
    }
    plotPoints.push(point);
  }
  return { well, method, available, observationsVisible, idwVisible, idwAvailable, points, plotPoints,
    hasData: points.some(point => point.reconstructed !== null || point.idw !== null || point.observed !== null) };
}

export function historyValue(value: number | null): string {
  return value === null ? 'Missing' : `${value} m`;
}
