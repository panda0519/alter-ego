import { useState } from 'react';
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import type { Batch } from './data/models';
import type { Selection } from './data/selection';
import { buildHistory, historyValue } from './data/history';
import type { DemoMode } from './data/outage';

export default function HistoryChart({ batch, selection, demoMode = 'sensor-available' }: { batch: Batch; selection: Selection; demoMode?: DemoMode }) {
  const [showIdw, setShowIdw] = useState(false);
  const [showObservations, setShowObservations] = useState(false);
  const history = buildHistory(batch, selection, { showIdw, showObservations, demoMode });
  const { well, method, points, plotPoints, observationsVisible, idwVisible, hasData } = history;
  const fixture = batch.predictions.meta.artifact_kind === 'fixture';
  const chartKey = `${well?.id}/${method}/${idwVisible}/${observationsVisible}/${demoMode}`;
  const observationLabel = well?.role === 'holdout' ? 'Revealed withheld readings' : 'Observed readings';
  return <section className="panel history-panel" aria-labelledby="chart-title">
    <p className="eyebrow">03 / History</p>
    <h2 id="chart-title">Depth over time</h2>
    <p className="history-identity" role="status">{well && method ? `History: ${well.id} / ${method}` : 'Choose a valid well and method to view history.'}</p>
    <p>{batch.predictions.dates.length} series dates loaded. Depth in m below ground ({batch.predictions.meta.depth_unit}). Larger values mean deeper water; depth increases downward on this chart.</p>
    <p>{batch.predictions.meta.dataset_kind} / artifact_kind={batch.predictions.meta.artifact_kind}{fixture ? ' - Illustrative series, not trained results or measured field accuracy.' : ''}</p>
    {well && method && <>
      <fieldset className="chart-options">
        <legend>Optional history overlays</legend>
        <label><input type="checkbox" id="show-idw" checked={showIdw && method !== 'idw'} disabled={method === 'idw'} onChange={event => setShowIdw(event.target.checked)} /> Compare IDW estimates</label>
        <label><input type="checkbox" id="show-observations" checked={observationsVisible} disabled={well.role === 'holdout'} onChange={event => setShowObservations(event.target.checked)} /> Show observed readings</label>
      </fieldset>
      {well.role === 'holdout' && <p className="notice">{demoMode === 'reveal' ? 'Revealed withheld readings are shown alongside estimates. Nulls remain missing.' : 'Held-out observations are hidden from the chart, tooltip and data table.'}</p>}
      {observationsVisible && !points.some(point => point.observed !== null) && <p role="status">No exported observations are available for these dates. Missing readings remain missing.</p>}
      {!history.available && <p role="status">Selected-method predictions are unavailable for this well. No other method is substituted.</p>}
      {idwVisible && !history.idwAvailable && <p role="status">IDW comparison is unavailable for this well.</p>}
      <p id="history-help">Solid teal: selected reconstruction. Dashed amber: optional IDW. Purple points and dashed segments: optional observed readings. Gaps mean missing exported values; no gap filling is performed. Lines between adjacent daily readings are visual guides.</p>
      {!hasData ? <p className="empty-state" role="status">No displayable history values for this selection and these overlays.</p> : <div className="history-plot" aria-label={`Depth history for ${well.id}, ${method}`} aria-describedby="history-help">
        <ResponsiveContainer width="100%" height="100%" minWidth={0} initialDimension={{ width: 300, height: 320 }}>
          <LineChart key={chartKey} data={plotPoints} margin={{ top: 16, right: 12, bottom: 20, left: 0 }} accessibilityLayer>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="timestamp" type="number" scale="time" domain={['dataMin', 'dataMax']} minTickGap={28} tick={{ fontSize: 12 }} tickFormatter={value => new Date(value).toISOString().slice(5, 10)} label={{ value: 'Date (MM-DD, UTC)', position: 'insideBottom', offset: -14 }} />
            <YAxis reversed domain={['auto', 'auto']} width={48} tick={{ fontSize: 12 }} />
            <Tooltip filterNull={false} content={({ active, label }) => {
              const point = points.find(point => point.timestamp === Number(label));
              return active && point ? <div className="history-tooltip">
                <strong>{point.date}</strong>
                <p>Reconstructed ({method}): {historyValue(point.reconstructed)}</p>
                {idwVisible && <p>IDW comparison: {historyValue(point.idw)}</p>}
                {observationsVisible && <p>{well.role === 'holdout' ? 'Revealed withheld reading' : 'Observed reading'}: {historyValue(point.observed)}</p>}
              </div> : null;
            }} />
            <Legend verticalAlign="top" wrapperStyle={{ fontSize: 12 }} />
            <Line className="history-selected" dataKey="reconstructed" name={`Reconstructed (${method})`} type="linear" stroke="#176b70" strokeWidth={2} dot={{ r: 2 }} connectNulls={false} isAnimationActive={false} />
            {idwVisible && <Line className="history-idw" dataKey="idw" name="IDW comparison" type="linear" stroke="#9b510b" strokeDasharray="7 4" dot={false} connectNulls={false} isAnimationActive={false} />}
            {observationsVisible && <Line className="history-observed" dataKey="observed" name={observationLabel} type="linear" stroke="#7242a0" strokeDasharray="2 4" dot={{ r: 3 }} connectNulls={false} isAnimationActive={false} />}
          </LineChart>
        </ResponsiveContainer>
      </div>}
      <details className="history-table">
        <summary>View date-aligned history data</summary>
        <div className="table-scroll" role="region" aria-label="History data table" tabIndex={0}>
          <table>
            <caption>{well.id} / {method} - m below ground; {batch.predictions.meta.dataset_kind}, {batch.predictions.meta.artifact_kind}</caption>
            <thead><tr><th scope="col">Date</th><th scope="col">Reconstructed ({method})</th>{idwVisible && <th scope="col">IDW comparison</th>}{observationsVisible && <th scope="col">{observationLabel}</th>}</tr></thead>
            <tbody>{points.map(point => <tr key={point.date}><th scope="row">{point.date}</th><td>{historyValue(point.reconstructed)}</td>{idwVisible && <td>{historyValue(point.idw)}</td>}{observationsVisible && <td>{historyValue(point.observed)}</td>}</tr>)}</tbody>
          </table>
        </div>
      </details>
    </>}
  </section>;
}
