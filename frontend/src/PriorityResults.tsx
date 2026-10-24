import type { Batch, Method } from './data/models';
import { depthLabel } from './data/selection';
import { methodLabels, priorityRows, resultRows, resultValue } from './data/results';
import { provisionalReasons } from './data/provenance';

export default function PriorityResults({ batch, selectedId, method, onSelectWell, onSelectMethod }: {
  batch: Batch; selectedId?: string; method?: Method;
  onSelectWell: (id: string) => void; onSelectMethod: (method: Method) => void;
}) {
  const rows = method ? priorityRows(batch, method) : [];
  const meta = batch.metrics.meta;
  return <>
    <section className="panel priority-panel" aria-labelledby="priority-title">
      <p className="eyebrow">04 / Inspection</p>
      <h2 id="priority-title">Exported reconstruction priorities</h2>
      <p className="priority-method" role="status">{method ? `Priorities: ${methodLabels[method]} (${method})` : 'Choose a valid method to view priorities.'}</p>
      <p>{meta.dataset_kind} / artifact_kind={meta.artifact_kind}. Summary as of {meta.as_of_date}.</p>
      <p>Prototype inspection rules, not official warnings. Categories and reasons come from the export. Display order: high, watch, normal, unknown; decreasing exported 30-day change, then well ID.</p>
      <p>Documented prototype change rules: high above 0.50 m; watch above 0.20 m through 0.50 m; normal at or below 0.20 m; unknown when unavailable. These rules are described here, not recalculated.</p>
      {!rows.length ? <p className="empty-state">No priority entries available for this selection.</p> : <ol className="priority-list">
        {rows.map(row => <li key={row.id} data-priority-id={row.id}>
          <button type="button" aria-pressed={row.id === selectedId} onClick={() => {
            onSelectWell(row.id);
            const heading = document.getElementById('detail-title');
            heading?.focus(); heading?.scrollIntoView({ block: 'start' });
          }}>Inspect {row.id}</button>
          <p><strong>{row.priority}</strong> / {row.role}</p>
          <p>Latest estimate: {depthLabel(row.summary?.latest_depth_m)} below ground. 30-day change: {depthLabel(row.summary?.change_30d_m)}.</p>
          <p>Exported reasons: {row.summary?.reason_codes.length ? row.summary.reason_codes.join(', ') : 'Unknown'}</p>
          {!row.summary && <p>Reconstruction summary unavailable for this method.</p>}
        </li>)}
      </ol>}
    </section>
    <section className="panel results-panel" aria-labelledby="results-title">
      <p className="eyebrow">05 / Evaluation</p>
      <h2 id="results-title">Results</h2>
      <ul className="badges" aria-label="Evaluation dataset labels"><li>{meta.dataset_kind}</li><li>artifact_kind={meta.artifact_kind}</li></ul>
      {provisionalReasons(batch).length > 0 && <p className="notice">PROVISIONAL exported evaluation. Physics and source provenance acceptance remain pending. These synthetic results do not establish field accuracy.</p>}
      <p>{batch.metrics.evaluation.notes}</p>
      {meta.artifact_kind === 'fixture' && <p className="notice">Illustrative UI fixture. No evaluation has run; accuracy values are unavailable.</p>}
      <p>Run-level exported results for the {batch.metrics.evaluation.test_group} test group, not individual-well scores. Common evaluation mask: {String(batch.metrics.evaluation.same_common_mask)}. Split seed: {batch.metrics.evaluation.split_seed}.</p>
      <p>Run: {meta.run_id}. As of {meta.as_of_date}; generated (UTC) {meta.generated_at_utc}. Errors are in metres below ground.</p>
      <div className="result-grid">{resultRows(batch).map(row => <section key={row.method} className="result-card" data-result-method={row.method} aria-labelledby={`result-${row.method}`}>
        <h3 id={`result-${row.method}`}>{methodLabels[row.method]} ({row.method})</h3>
        <button type="button" aria-pressed={method === row.method} onClick={() => onSelectMethod(row.method)}>Inspect method {row.method}</button>
        <p>Status: <strong>{row.status}</strong>{!row.completed && ' - results unavailable'}</p>
        <dl className="metadata">
          <div><dt>Validation MAE</dt><dd data-metric="validationMae">{resultValue(row.validationMae, ' m')}</dd></div>
          <div><dt>Test MAE</dt><dd data-metric="testMae">{resultValue(row.testMae, ' m')}</dd></div>
          <div><dt>Test RMSE</dt><dd data-metric="testRmse">{resultValue(row.testRmse, ' m')}</dd></div>
          <div><dt>Validation pairs</dt><dd data-metric="validationPairs">{resultValue(row.validationPairs)}</dd></div>
          <div><dt>Test pairs</dt><dd data-metric="testPairs">{resultValue(row.testPairs)}</dd></div>
          <div><dt>Test wells</dt><dd data-metric="testWells">{resultValue(row.testWells)}</dd></div>
          {row.method === 'gcn_lstm_physics' && <div><dt>Exported regulariser lambda</dt><dd data-metric="lambda">{resultValue(row.lambda)}</dd></div>}
        </dl>
        {row.method === 'gcn_lstm_physics' && <p>The water-balance regulariser uses prototype assumptions; its label does not establish improved accuracy or validated hydrology.</p>}
      </section>)}</div>
    </section>
  </>;
}
