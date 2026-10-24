import { useCallback, useState } from 'react';
import WellMap from './WellMap';
import { methods } from './data/models';
import type { Batch, Role } from './data/models';
import { depthLabel, initialSelection, methodAvailable, resolveSelection } from './data/selection';

const roleDescriptions: Record<Role, string> = {
  visible: 'Visible donor well. Previous-day observations may supply reconstruction inputs.',
  train_masked: 'Training-masked well. Its own readings are excluded from inputs; permitted training labels may supervise reconstruction.',
  holdout: 'Held-out well. Its readings are excluded from inputs, losses, scalers and calibration.',
};

export default function WellWorkspace({ batch }: { batch: Batch }) {
  const [selection, setSelection] = useState(() => initialSelection(batch));
  const selectWell = useCallback((wellId: string) => setSelection(current => ({ ...current, wellId })), []);
  const { well, method, available, summary } = resolveSelection(batch, selection);
  const fixture = batch.predictions.meta.artifact_kind === 'fixture';
  return (
    <>
    <section className="panel selection-panel" aria-labelledby="wells-title">
      <p className="eyebrow">01 / Wells</p>
      <h2 id="wells-title">Well list and details</h2>
      <p>{batch.predictions.wells.length} wells loaded. Select a well to inspect its exported summary.</p>
      <div className="selection-grid">
        <nav aria-label="Well selection">
          <ul className="well-list">
            {batch.predictions.wells.map(item => <li key={item.id}>
              <button type="button" aria-pressed={item.id === well?.id}
                onClick={() => selectWell(item.id)}>
                <span>{item.id}</span><span className="well-role">{item.role}</span>
              </button>
            </li>)}
          </ul>
        </nav>
        <div>
          <label htmlFor="reconstruction-method">Reconstruction method</label>
          <select id="reconstruction-method" value={method ?? ''}
            aria-describedby="method-help"
            onChange={event => setSelection(current => ({ ...current, method: event.target.value }))}>
            <option value="" disabled>Choose a supported method</option>
            {methods.map(option => <option key={option} value={option}>
              {option}{well && !methodAvailable(batch, well, option) ? ' (unavailable)' : fixture ? ' (illustrative)' : ''}
            </option>)}
          </select>
          <p id="method-help">{fixture ? 'Fixture series are illustrative, including neural methods. No model has been trained.' : 'Methods use the supplied export only. Unavailable methods are never replaced by another method.'}</p>
          {(!well || !method) && <p role="alert">Invalid selection. Choose a well and a supported method to view details.</p>}
          {well && method && <section aria-labelledby="detail-title" className="well-details">
            <h3 id="detail-title">{well.id} / {method}</h3>
            <p role="status" aria-live="polite">Selected well: {well.id}. Selected method: {method}.</p>
            <p>{roleDescriptions[well.role]}</p>
            {!available && <p className="notice" role="status">Method unavailable for this well. No estimates are shown for this selection.</p>}
            <dl className="metadata">
              <div><dt>Well ID</dt><dd data-field="well-id">{well.id}</dd></div>
              <div><dt>Evaluation role</dt><dd data-field="role">{well.role}</dd></div>
              <div><dt>Latitude</dt><dd data-field="latitude">{well.latitude}</dd></div>
              <div><dt>Longitude</dt><dd data-field="longitude">{well.longitude}</dd></div>
              <div><dt>Selected method</dt><dd data-field="method">{method}</dd></div>
              <div><dt>Evaluation status</dt><dd data-field="status">{batch.metrics.methods[method].status}</dd></div>
              <div><dt>Latest estimated depth (below ground)</dt><dd data-field="latest">{depthLabel(summary?.latest_depth_m)}</dd></div>
              <div><dt>Exported 30-day depth change</dt><dd data-field="change">{depthLabel(summary?.change_30d_m)}</dd></div>
              <div><dt>Prototype inspection priority</dt><dd data-field="priority">{summary?.priority ?? 'unknown'}</dd></div>
              <div><dt>Exported reason codes</dt><dd data-field="reasons">{summary?.reason_codes.length ? summary.reason_codes.join(', ') : 'Unknown'}</dd></div>
            </dl>
            <p>Summary as of {batch.predictions.meta.as_of_date}. Priority is an illustrative inspection rule, not an official warning.</p>
          </section>}
        </div>
      </div>
    </section>
    <WellMap wells={batch.predictions.wells} selectedId={well?.id} onSelect={selectWell} />
    </>
  );
}
