import type { Batch, Method } from './models.ts';
import { methods } from './models.ts';
import { publicHttpsUrl } from './briefing.ts';
import { reportedTrainingRevisions } from './provenance.ts';

export type AssistantSource = 'export-briefing' | 'agent37';
export interface AssistantReply { source: AssistantSource; text: string }
export interface AssistantRequest { question: string; stationId?: string; chartMethod?: string }

export const suggestedQuestions = [
  'Which stations should I inspect first?',
  'Explain this station.',
  'What does this graph show?',
  'How do the reconstruction methods compare?',
  'What are the limitations?',
] as const;

const priorityOrder = { high: 0, watch: 1, normal: 2, unknown: 3 };

export function assistantEndpoint(raw: string | undefined): { kind: 'missing' | 'invalid' | 'configured'; url?: string } {
  if (!raw?.trim()) return { kind: 'missing' };
  const value = raw.trim();
  if (value.startsWith('/api/') && !value.includes('..') && !value.includes('\\') && !value.includes('?') && !value.includes('#')) {
    return { kind: 'configured', url: value };
  }
  try {
    const url = new URL(value);
    const local = url.protocol === 'http:' && (url.hostname === '127.0.0.1' || url.hostname === 'localhost')
      && url.pathname.startsWith('/api/') && !url.username && !url.password && !url.search && !url.hash;
    if (local) return { kind: 'configured', url: url.href };
  } catch { return { kind: 'invalid' }; }
  return publicHttpsUrl(value);
}

function rankedWells(batch: Batch) {
  return [...batch.agent_context.wells].sort((a, b) => priorityOrder[a.priority] - priorityOrder[b.priority]
    || (b.change_30d_m ?? -Infinity) - (a.change_30d_m ?? -Infinity)
    || (a.id < b.id ? -1 : a.id > b.id ? 1 : 0));
}

function identity(batch: Batch): string {
  const meta = batch.agent_context.meta;
  const kind = meta.artifact_kind === 'fixture'
    ? 'artifact_kind is fixture. This is illustrative UI data with no trained result.'
    : `artifact_kind is ${meta.artifact_kind}.`;
  return `Dataset kind is ${meta.dataset_kind}. ${kind} As of ${meta.as_of_date}. Default method is ${meta.default_method}. Run ${meta.run_id}.`;
}

function methodNote(batch: Batch, chartMethod?: string): string {
  const fallback = batch.agent_context.meta.default_method;
  if (!chartMethod || chartMethod === fallback || !methods.includes(chartMethod as Method)) return '';
  return `The chart method is ${chartMethod}. This briefing only has agent-context facts for the exported default method ${fallback}. It does not invent values for the chart method.`;
}

function explainStation(batch: Batch, stationId?: string, chartMethod?: string): string {
  const note = methodNote(batch, chartMethod);
  const well = batch.agent_context.wells.find(item => item.id === stationId);
  if (!well) return [note, `Station ${stationId || 'none'} is not in this export. No depth was invented.`].filter(Boolean).join(' ');
  const depth = well.latest_depth_m == null ? 'unknown' : `${well.latest_depth_m} m below ground`;
  const change = well.change_30d_m == null ? 'unknown' : `${well.change_30d_m} m`;
  return [
    note,
    `Station ${well.id} is an exported estimate for ${well.method}, not a measurement.`,
    `Latest estimated depth is ${depth}. Exported 30-day depth change is ${change}. Positive change means deeper water.`,
    `Inspection priority is ${well.priority}. Evaluation role is ${well.role}.`,
    `Reason codes: ${well.reason_codes.length ? well.reason_codes.join(', ') : 'none'}.`,
    'Verify the sensor and local conditions before any operational action. Do not pump, drill, or issue a public-safety decision from this prototype.',
    identity(batch),
  ].filter(Boolean).join(' ');
}

function inspectFirst(batch: Batch): string {
  const top = rankedWells(batch).slice(0, 5);
  const lines = top.map(well => `${well.id}: priority ${well.priority}, 30-day change ${well.change_30d_m == null ? 'unknown' : `${well.change_30d_m} m`}, role ${well.role}.`);
  return [`Inspect these stations first, using exported priority for ${batch.agent_context.meta.default_method}. These are prototype labels, not official warnings.`, ...lines, identity(batch)].join(' ');
}

function graphAnswer(batch: Batch, stationId?: string, chartMethod?: string): string {
  const dates = batch.predictions.dates;
  return [
    methodNote(batch, chartMethod),
    `The graph is a historical reconstruction for ${stationId || 'the selected station'}, not a live reading and not a forecast.`,
    `Depth is metres below ground and increases downward. Dates run from ${dates[0]} to ${dates.at(-1)} in UTC.`,
    'Gaps are missing exported values. They are not filled in.',
    'Held-out observations stay hidden until the permitted reveal action. This answer does not include those readings.',
    identity(batch),
  ].filter(Boolean).join(' ');
}

function compareMethods(batch: Batch, chartMethod?: string): string {
  const rows = methods.map(method => {
    const metric = batch.metrics.methods[method];
    if (batch.metrics.meta.artifact_kind === 'fixture' || metric.status !== 'completed' || metric.test_mae_m == null || metric.validation_mae_m == null) {
      return `${method}: status ${metric.status}. Accuracy is not available.`;
    }
    return `${method}: status ${metric.status}, validation MAE ${metric.validation_mae_m} m, holdout test MAE ${metric.test_mae_m} m.`;
  });
  const idw = batch.metrics.methods.idw;
  const gcn = batch.metrics.methods.gcn_lstm;
  const comparison = idw.status === 'completed' && gcn.status === 'completed' && idw.test_mae_m != null && gcn.test_mae_m != null && idw.test_mae_m < gcn.test_mae_m
    ? 'IDW has the lower holdout test MAE. Do not describe GCN-LSTM as better on that holdout score.'
    : 'No holdout win is claimed beyond the exported numbers above.';
  const physics = batch.metrics.methods.gcn_lstm_physics.status === 'not_run'
    ? 'Physics-enhanced GCN-LSTM is not_run and is not a completed prediction.'
    : '';
  return [methodNote(batch, chartMethod), 'Method comparison uses the loaded evaluation export.', ...rows, comparison, physics, identity(batch)].filter(Boolean).join(' ');
}

function limitations(batch: Batch, chartMethod?: string): string {
  const extra = [
    'Reconstruction is historical, not forecasting.',
    'Field accuracy has not been verified.',
    batch.metrics.methods.gcn_lstm_physics.status === 'not_run' ? 'Physics output is not_run.' : '',
    reportedTrainingRevisions(batch).some(revision => revision.includes('+dirty')) ? 'Training provenance contains historical dirty revisions. Training and checkpoints have not been independently reproduced.' : '',
    'Nodus usage has not been verified.',
    'Estimates are not measurements and are not official pumping or public-safety guidance.',
  ].filter(Boolean);
  return [methodNote(batch, chartMethod), ...batch.agent_context.limitations, ...extra, identity(batch)].filter(Boolean).join(' ');
}

export function answerFromExport(batch: Batch, question: string, stationId?: string, chartMethod?: string): AssistantReply {
  const asked = question.trim().toLowerCase();
  let text: string;
  if (asked.includes('limitation')) text = limitations(batch, chartMethod);
  else if (asked.includes('compare') || asked.includes('method')) text = compareMethods(batch, chartMethod);
  else if (asked.includes('graph') || asked.includes('chart')) text = graphAnswer(batch, stationId, chartMethod);
  else if (asked.includes('inspect first') || asked.includes('which station') || asked.includes('which well')) text = inspectFirst(batch);
  else if (asked.includes('explain') || (stationId && asked.includes(stationId.toLowerCase()))) text = explainStation(batch, stationId, chartMethod);
  else {
    const named = batch.agent_context.wells.find(well => asked.includes(well.id.toLowerCase()));
    text = named
      ? explainStation(batch, named.id, chartMethod)
      : `${identity(batch)} Ask about inspection priority, this station, the graph, method comparison, or limitations. No other groundwater values were invented.`;
  }
  return { source: 'export-briefing', text };
}

export async function askAssistant(batch: Batch, request: AssistantRequest, signal?: AbortSignal, fetcher: typeof fetch = fetch): Promise<AssistantReply> {
  const local = answerFromExport(batch, request.question, request.stationId, request.chartMethod);
  const endpoint = assistantEndpoint(import.meta.env?.VITE_AGENT_PROXY_URL);
  if (endpoint.kind !== 'configured' || !endpoint.url) return local;
  try {
    const response = await fetcher(endpoint.url, {
      method: 'POST',
      headers: { 'content-type': 'application/json', accept: 'application/json' },
      body: JSON.stringify({ question: request.question.slice(0, 400), stationId: request.stationId, chartMethod: request.chartMethod }),
      signal,
      credentials: 'omit',
      cache: 'no-store',
    });
    if (!response.ok) {
      return { source: 'export-briefing', text: `${local.text} Live Agent37 did not answer (HTTP ${response.status}). This text is the verified export briefing.` };
    }
    const payload = await response.json() as { source?: string; text?: string };
    if (payload.source !== 'agent37' || typeof payload.text !== 'string' || !payload.text.trim()) {
      return { source: 'export-briefing', text: `${local.text} Live Agent37 returned an unusable response. This text is the verified export briefing.` };
    }
    return { source: 'agent37', text: payload.text };
  } catch {
    return { source: 'export-briefing', text: `${local.text} Live Agent37 could not be reached. This text is the verified export briefing.` };
  }
}
