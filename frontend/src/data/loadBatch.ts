import Ajv from 'ajv';
import addFormats from 'ajv-formats';
import predictions from '../../../contracts/predictions.schema.json' with { type: 'json' };
import metrics from '../../../contracts/metrics.schema.json' with { type: 'json' };
import run_info from '../../../contracts/run_info.schema.json' with { type: 'json' };
import agent_context from '../../../contracts/agent_context.schema.json' with { type: 'json' };
import { methods } from './models.ts';
import type { Batch, Metadata } from './models.ts';

const schemas = { predictions, metrics, run_info, agent_context };
const names = Object.keys(schemas) as (keyof Batch)[];
const ajv = new Ajv({ allErrors: true, strict: true });
addFormats(ajv);
const validators = Object.fromEntries(names.map(name => [name, ajv.compile(schemas[name])]));

export class BatchError extends Error {
  kind: 'missing' | 'invalid';
  constructor(kind: 'missing' | 'invalid', message: string) {
    super(message);
    this.name = 'BatchError';
    this.kind = kind;
  }
}

function ensure(condition: boolean, message: string): asserts condition {
  if (!condition) throw new BatchError('invalid', message);
}

export function validateAgentContext(raw: unknown, expected: Batch['agent_context']): Batch['agent_context'] {
  const validate = validators.agent_context;
  if (!validate(raw)) throw new BatchError('invalid', `agent_context.json: ${validate.errors?.[0]?.instancePath || '/'} ${validate.errors?.[0]?.message || 'invalid context'}.`);
  const context = raw as Batch['agent_context'];
  for (const key of Object.keys(expected.meta) as (keyof Metadata)[]) {
    ensure(context.meta[key] === expected.meta[key], `agent_context.json: metadata mismatch at ${key}.`);
  }
  const ids = new Set(context.wells.map(well => well.id));
  ensure(ids.size === context.wells.length && context.wells.length === expected.wells.length, 'agent_context.json: well IDs do not match the loaded batch.');
  for (const well of expected.wells) {
    const received = context.wells.find(item => item.id === well.id);
    ensure(!!received, 'agent_context.json: well IDs do not match the loaded batch.');
    for (const key of Object.keys(well) as (keyof typeof well)[]) {
      ensure(JSON.stringify(received[key]) === JSON.stringify(well[key]), `agent_context.json: summary mismatch for ${well.id}/${key}.`);
    }
  }
  ensure(JSON.stringify(context.limitations) === JSON.stringify(expected.limitations), 'agent_context.json: limitations mismatch.');
  return context;
}

export function validateBatch(raw: Record<keyof Batch, unknown>): Batch {
  for (const name of names) {
    const validate = validators[name];
    if (!validate(raw[name])) {
      const error = validate.errors?.[0];
      throw new BatchError('invalid', `${name}.json ${error?.instancePath || '/'}: ${error?.message || 'invalid data'}.`);
    }
  }
  // Cast only after all four authoritative schemas have passed.
  const batch = raw as Batch;
  const { meta, dates, wells } = batch.predictions;
  ensure(meta.artifact_kind !== 'fixture' || meta.dataset_kind === 'synthetic', 'predictions.json: fixture data must be labelled synthetic.');
  for (const name of names) {
    for (const key of Object.keys(meta) as (keyof Metadata)[]) {
      ensure(batch[name].meta[key] === meta[key], `${name}.json: metadata mismatch at ${key}. Publish all four files from one batch.`);
    }
  }
  ensure(dates.every((date, i) => i === 0 || dates[i - 1] < date), 'predictions.json: dates must be unique and chronological.');
  ensure(dates.at(-1) === meta.as_of_date, 'predictions.json: as_of_date must match the final series date.');
  const ids = new Set(wells.map(well => well.id));
  ensure(ids.size === wells.length, 'predictions.json: duplicate well ID.');
  for (const well of wells) {
    ensure(well.observations_m.length === dates.length, `predictions.json: ${well.id} observations_m length does not match dates.`);
    for (const method of methods) {
      ensure(well.predictions_m[method].length === dates.length, `predictions.json: ${well.id}/${method} series length does not match dates.`);
    }
  }
  const agentIds = new Set(batch.agent_context.wells.map(well => well.id));
  ensure(agentIds.size === wells.length && batch.agent_context.wells.length === wells.length && [...agentIds].every(id => ids.has(id)), 'agent_context.json: well IDs must match predictions.json exactly.');
  for (const agent of batch.agent_context.wells) {
    const well = wells.find(well => well.id === agent.id)!;
    ensure(agent.role === well.role && agent.method === meta.default_method, `agent_context.json: ${agent.id} role or method mismatch.`);
    const summary = well.summaries[agent.method];
    ensure(agent.latest_depth_m === summary.latest_depth_m && agent.change_30d_m === summary.change_30d_m && agent.priority === summary.priority && JSON.stringify(agent.reason_codes) === JSON.stringify(summary.reason_codes), `agent_context.json: ${agent.id} summary mismatch.`);
  }
  for (const method of methods) {
    const metric = batch.metrics.methods[method];
    const errors = [metric.validation_mae_m, metric.test_mae_m, metric.test_rmse_m];
    ensure(metric.status === 'completed'
      ? errors.every(value => value !== null && value >= 0) && metric.validation_pairs > 0 && metric.test_pairs > 0 && metric.test_wells > 0
      : errors.every(value => value === null), `metrics.json: ${method} values do not match its status.`);
    ensure(meta.artifact_kind !== 'fixture' || metric.status === 'not_run', 'metrics.json: fixture metrics must remain not_run.');
  }
  return batch;
}

export async function loadBatch(signal?: AbortSignal, fetcher: typeof fetch = fetch): Promise<Batch> {
  const entries = await Promise.all(names.map(async name => {
    let response: Response;
    try {
      response = await fetcher(`/data/${name}.json`, { signal, cache: 'no-store' });
    } catch (error) {
      if (signal?.aborted) throw error;
      throw new BatchError('missing', `${name}.json could not be loaded. Check the connection and publish the complete four-file batch.`);
    }
    if (!response.ok) throw new BatchError('missing', `${name}.json is unavailable (HTTP ${response.status}). Publish the complete four-file batch.`);
    const text = await response.text();
    if (!text.trim()) throw new BatchError('missing', `${name}.json is empty. Publish the complete four-file batch.`);
    try {
      return [name, JSON.parse(text)] as const;
    } catch {
      throw new BatchError('invalid', `${name}.json is not valid JSON. Check the export file.`);
    }
  }));
  return validateBatch(Object.fromEntries(entries) as Record<keyof Batch, unknown>);
}
