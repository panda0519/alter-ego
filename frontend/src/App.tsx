import { useEffect, useState } from 'react';
import { BatchError, loadBatch } from './data/loadBatch';
import type { Batch } from './data/models';
import WellWorkspace from './WellWorkspace';

type LoadState = { kind: 'loading' } | { kind: 'ready'; batch: Batch } | { kind: 'missing' | 'invalid'; message: string };

export default function App() {
  const [state, setState] = useState<LoadState>({ kind: 'loading' });
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setState({ kind: 'loading' });
    loadBatch(controller.signal).then(
      batch => { if (!controller.signal.aborted) setState({ kind: 'ready', batch }); },
      error => {
        if (!controller.signal.aborted) setState({
          kind: error instanceof BatchError ? error.kind : 'invalid',
          message: error instanceof Error ? error.message : 'The export batch could not be read.',
        });
      },
    );
    return () => controller.abort();
  }, [attempt]);
  const batch = state.kind === 'ready' ? state.batch : null;
  const meta = batch?.predictions.meta;
  return (
    <>
      <a className="skip-link" href="#workspace">Skip to workspace</a>
      <header className="page-header">
        <p className="eyebrow">Groundwater reconstruction</p>
        <h1>Alter Ego</h1>
        <p className="intro">A workspace for inspecting historical gaps in groundwater sensor readings.</p>
        <ul className="badges" aria-label="Prototype and dataset status">
          <li>Historical prototype</li>
          {meta ? <>
            <li>Dataset: {meta.dataset_kind}</li>
            <li>artifact_kind={meta.artifact_kind}</li>
          </> : <li>No validated dataset loaded</li>}
        </ul>
      </header>

      <main id="workspace" tabIndex={-1}>
        {state.kind === 'loading' && <p className="notice" role="status">Loading the complete export batch...</p>}
        {(state.kind === 'missing' || state.kind === 'invalid') && <aside className="notice" role="alert">
          <strong>{state.kind === 'missing' ? 'Data unavailable' : 'Invalid export batch'}</strong>
          <p>{state.message}</p>
          <p>No partial batch is displayed.</p>
          <button type="button" onClick={() => setAttempt(value => value + 1)}>Retry loading</button>
        </aside>}
        {batch && meta && <aside className="notice" aria-label="Dataset information">
          <strong>{meta.artifact_kind === 'fixture' ? 'Illustrative fixture - not trained results' : 'Validated export batch'}</strong>
          <p>{meta.caption}</p>
          {meta.dataset_kind === 'synthetic' && <p>Synthetic information does not demonstrate field accuracy.</p>}
          <dl className="metadata">
            <div><dt>Dataset ID</dt><dd>{meta.dataset_id}</dd></div>
            <div><dt>Run ID</dt><dd>{meta.run_id}</dd></div>
            <div><dt>Schema</dt><dd>{meta.schema_version}</dd></div>
            <div><dt>Observation dates</dt><dd>{batch.predictions.dates[0]} to {batch.predictions.dates.at(-1)}</dd></div>
            <div><dt>As of</dt><dd>{meta.as_of_date}</dd></div>
            <div><dt>Generated (UTC)</dt><dd>{meta.generated_at_utc}</dd></div>
            <div><dt>Wells</dt><dd>{batch.predictions.wells.length}</dd></div>
            <div><dt>Series dates</dt><dd>{batch.predictions.dates.length}</dd></div>
            <div><dt>Default method</dt><dd>{meta.default_method}</dd></div>
            <div><dt>Depth unit</dt><dd>{meta.depth_unit}</dd></div>
          </dl>
        </aside>}

        <div className="workspace-grid">
          {batch ? <WellWorkspace key={JSON.stringify(batch.predictions.meta)} batch={batch} /> : <section className="panel" aria-labelledby="wells-title">
            <p className="eyebrow">01 / Wells</p>
            <h2 id="wells-title">Well list</h2>
            <p className="empty-state">Awaiting a validated dataset.</p>
          </section>}

          {!batch && <section className="panel" aria-labelledby="map-title">
            <p className="eyebrow">02 / Region</p>
            <h2 id="map-title">Well map</h2>
            <p className="empty-state">Awaiting a validated dataset.</p>
          </section>}

          {!batch && <section className="panel" aria-labelledby="chart-title">
            <p className="eyebrow">03 / History</p>
            <h2 id="chart-title">Depth over time</h2>
            <p className="empty-state">Awaiting a validated dataset.</p>
          </section>}

          {!batch && <section className="panel" aria-labelledby="results-title">
            <p className="eyebrow">04 / Evaluation</p>
            <h2 id="results-title">Results</h2>
            <p className="empty-state">Awaiting a validated dataset.</p>
          </section>}
        </div>
      </main>

      <footer>Historical reconstruction prototype. Export validation does not verify model accuracy or leakage prevention.</footer>
    </>
  );
}
