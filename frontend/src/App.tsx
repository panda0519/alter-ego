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
  if (state.kind === 'ready') return <WellWorkspace key={JSON.stringify(state.batch.predictions.meta)} batch={state.batch} />;
  return <>
    <a className="skip-link" href="#workspace">Skip to workspace</a>
    <header className="page-header">
      <p className="brand-mark">Alter Ego</p>
      <h1>Groundwater Intelligence</h1>
    </header>
    <main id="workspace" tabIndex={-1}>
      {state.kind === 'loading' && <p className="notice" role="status">Loading the complete export batch...</p>}
      {state.kind !== 'loading' && <aside className="notice" role="alert">
        <strong>{state.kind === 'missing' ? 'Data unavailable' : 'Invalid export batch'}</strong>
        <p>{state.message}</p>
        <p>No partial batch is displayed.</p>
        <button type="button" onClick={() => setAttempt(value => value + 1)}>Retry loading</button>
      </aside>}
    </main>
  </>;
}
