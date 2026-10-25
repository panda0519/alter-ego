import { useState } from 'react';
import type { Batch, Method, Summary } from './data/models';
import { priorityRows, resultRows, resultValue } from './data/results';
import { formatDepth, holdoutComparison, methodTitles, methodViewLabels, priorityLabel, roleBadge, roundMetric, signedChangeText, statusLabel } from './data/presentation';

export default function PriorityResults({ batch, selectedId, method, onSelectWell, onSelectMethod }: {
  batch: Batch; selectedId?: string; method?: Method;
  onSelectWell: (id: string) => void; onSelectMethod: (method: Method) => void;
}) {
  const rows = method ? priorityRows(batch, method) : [];
  const meta = batch.metrics.meta;
  const [query, setQuery] = useState('');
  const [band, setBand] = useState<'all' | Summary['priority']>('all');
  const needle = query.trim().toLowerCase();
  const visible = rows.filter(row => (band === 'all' || row.priority === band) && row.id.toLowerCase().includes(needle));
  const comparison = holdoutComparison(batch);
  return <>
    <section className="panel priority-panel" aria-labelledby="priority-title">
      <h2 id="priority-title">Inspection priorities</h2>
      <p className="priority-method" role="status">{method ? `Priorities: ${methodTitles[method]}` : 'Choose a valid method to view priorities.'}</p>
      <p>Highest exported priorities are listed first. These are prototype inspection labels, not official warnings.</p>
      <div className="priority-tools">
        <label htmlFor="priority-search">Search priorities</label>
        <input id="priority-search" value={query} onChange={event => setQuery(event.target.value)} placeholder="Station ID" />
        <div className="band-row" role="group" aria-label="Priority filter">
          {(['all', 'high', 'watch', 'normal', 'unknown'] as const).map(item => <button key={item} type="button" aria-pressed={band === item} onClick={() => setBand(item)}>{item === 'all' ? 'All' : priorityLabel(item)}</button>)}
        </div>
      </div>
      {!visible.length ? <p className="empty-state">No priority entries available for this selection.</p> : <div className="priority-scroll">
        <table className="priority-table">
          <thead>
            <tr>
              <th scope="col">Station</th>
              <th scope="col">Role</th>
              <th scope="col">Latest Depth</th>
              <th scope="col">30-Day Change</th>
              <th scope="col">Priority</th>
              <th scope="col"><span className="sr-only">Open</span></th>
            </tr>
          </thead>
          <tbody>
            {visible.map(row => <tr key={row.id} data-priority-id={row.id}>
              <td>{row.id}</td>
              <td><span className="role-badge">{roleBadge(row.role)}</span></td>
              <td>{formatDepth(row.summary?.latest_depth_m)}</td>
              <td>{signedChangeText(row.summary?.change_30d_m)}</td>
              <td><span className={`priority-badge priority-${row.priority}`}>{priorityLabel(row.priority)}</span></td>
              <td><button type="button" aria-pressed={row.id === selectedId} onClick={() => {
                onSelectWell(row.id);
                document.getElementById('detail-title')?.focus();
              }}>View</button></td>
            </tr>)}
          </tbody>
        </table>
      </div>}
    </section>
    <section className="panel results-panel" aria-labelledby="results-title">
      <h2 id="results-title">Method comparison</h2>
      {comparison && <p className="caveat">{comparison}</p>}
      {meta.artifact_kind === 'fixture' && <p className="notice">Illustrative UI fixture. No evaluation has run; accuracy values are unavailable.</p>}
      <div className="result-grid">{resultRows(batch).map(row => <section key={row.method} className="result-card" data-result-method={row.method} aria-labelledby={`result-${row.method}`}>
        <h3 id={`result-${row.method}`}>{methodTitles[row.method]}</h3>
        <p className={`status-badge status-${row.status}`}>{statusLabel(row.status)}</p>
        <button type="button" aria-pressed={method === row.method} onClick={() => onSelectMethod(row.method)}>{method === row.method ? 'Active Model' : methodViewLabels[row.method]}</button>
        <p className="metric-face">Validation MAE <strong>{roundMetric(row.validationMae)}</strong></p>
        <p className="metric-face">Holdout Test MAE <strong>{roundMetric(row.testMae)}</strong></p>
        <details>
          <summary>Details</summary>
          <dl className="metadata">
            <div><dt>Validation MAE</dt><dd data-metric="validationMae">{resultValue(row.validationMae, ' m')}</dd></div>
            <div><dt>Test MAE</dt><dd data-metric="testMae">{resultValue(row.testMae, ' m')}</dd></div>
            <div><dt>Test RMSE</dt><dd data-metric="testRmse">{resultValue(row.testRmse, ' m')}</dd></div>
            <div><dt>Validation pairs</dt><dd data-metric="validationPairs">{resultValue(row.validationPairs)}</dd></div>
            <div><dt>Test pairs</dt><dd data-metric="testPairs">{resultValue(row.testPairs)}</dd></div>
            <div><dt>Test wells</dt><dd data-metric="testWells">{resultValue(row.testWells)}</dd></div>
            {row.method === 'gcn_lstm_physics' && <div><dt>Exported regulariser lambda</dt><dd data-metric="lambda">{resultValue(row.lambda)}</dd></div>}
          </dl>
        </details>
      </section>)}</div>
    </section>
  </>;
}
