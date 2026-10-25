import { useCallback, useReducer, useState } from 'react';
import WellMap from './WellMap';
import HistoryChart from './HistoryChart';
import OutageControls from './OutageControls';
import PriorityResults from './PriorityResults';
import AgentBriefing from './AgentBriefing';
import AboutData from './AboutData';
import AquaChat from './AquaChat';
import AquaMark from './AquaMark';
import type { ChatMessage } from './AquaChat';
import { initialWorkspace, workspaceReducer } from './data/outage';
import { methods } from './data/models';
import type { AppView } from './data/view';
import { selectView } from './data/view';
import type { Batch, Role } from './data/models';
import { depthLabel, methodAvailable, resolveSelection } from './data/selection';
import { changeText, formatDepth, methodTitles, priorityLabel } from './data/presentation';

const roleDescriptions: Record<Role, string> = {
  visible: 'Visible donor station. Previous-day observations may supply reconstruction inputs.',
  train_masked: 'Training-masked station. Its own readings are excluded from inputs.',
  holdout: 'Held-out station. Its readings stay hidden until reveal is permitted.',
};
const roleLabels: Record<Role, string> = { visible: 'Donor', train_masked: 'Training', holdout: 'Held out' };
const modeLabels = { 'sensor-available': 'Sensor available (historical setup)', 'simulated-outage': 'Simulated outage', reveal: 'Observations revealed' };

export default function WellWorkspace({ batch }: { batch: Batch }) {
  const [state, dispatch] = useReducer(workspaceReducer, batch, initialWorkspace);
  const [view, setView] = useState<AppView>('stations');
  const [about, setAbout] = useState(false);
  const [aquaOpen, setAquaOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const { selection, mode } = state;
  const selectWell = useCallback((wellId: string) => dispatch({ type: 'well', wellId }), []);
  const { well, method, available, summary } = resolveSelection(batch, selection);
  const meta = batch.predictions.meta;
  const fixture = meta.artifact_kind === 'fixture';
  const dates = batch.predictions.dates;
  const needle = query.trim().toLowerCase();
  const listed = batch.predictions.wells.filter(item => item.id.toLowerCase().includes(needle));
  const assistantOpen = view === 'assistant' || aquaOpen;
  function openView(action: AppView | 'analyze') {
    const next = selectView(action);
    setView(next);
    if (next === 'assistant') setAquaOpen(false);
  }
  return <>
    <a className="skip-link" href="#workspace">Skip to workspace</a>
    <header className="page-header">
      <div className="brand-block">
        <p className="brand-mark">Alter Ego</p>
        <h1>Groundwater Intelligence</h1>
      </div>
      <p className="simulated-badge">Simulated groundwater data — not real field measurements.</p>
      <div className="header-actions">
        <nav className="view-nav" aria-label="Primary">
          {(['stations', 'analysis', 'assistant'] as const).map(item => <button key={item} type="button" data-nav={item} aria-selected={view === item} onClick={() => openView(item)}>
            {item === 'stations' ? 'Stations' : item === 'analysis' ? 'Analysis' : 'AI Assistant'}
          </button>)}
        </nav>
        <button id="about-data-open" type="button" className="text-button" onClick={() => setAbout(true)}>About this data</button>
      </div>
    </header>
    <main id="workspace" tabIndex={-1}>
      <section className="summary-bar" aria-label="Export summary">
        <h2 id="detail-title" tabIndex={-1} className="sr-only">{well && method ? well.id : 'Select a station'}</h2>
        <p>{batch.predictions.wells.length} wells loaded</p>
        <p>{dates.length} series dates loaded</p>
        <p>{dates[0]} to {dates.at(-1)}</p>
        <p>Dataset: {meta.dataset_kind}</p>
        <p>Selected station {well?.id ?? 'none'}</p>
        {well?.role === 'holdout' && <p className="state-pill">{modeLabels[mode]}</p>}
      </section>
      {well && method && <p className="selection-status sr-only" role="status">Selected well: {well.id}. Selected method: {method}.</p>}
      {well && method && <p className="history-identity sr-only">History: {well.id} / {method}</p>}
      {(!well || !method) && <p role="alert">Invalid selection. Choose a well and a supported method to view details.</p>}
      {well && method && !available && <p role="status">Method unavailable for this well. No estimates are shown for this selection.</p>}
      <div className="method-bar">
        <label htmlFor="reconstruction-method">Reconstruction method</label>
        <select id="reconstruction-method" value={method ?? ''} aria-describedby="method-help" onChange={event => dispatch({ type: 'method', method: event.target.value })}>
          <option value="" disabled>Choose a supported method</option>
          {methods.map(option => <option key={option} value={option}>
            {methodTitles[option]}{well && !methodAvailable(batch, well, option) ? ' (Not available)' : fixture ? ' (illustrative)' : ''}
          </option>)}
        </select>
        <p id="method-help">{fixture ? 'Fixture series are illustrative, including neural methods. No model has been trained.' : 'Methods use the supplied export only. Unavailable methods are never replaced by another method.'}</p>
      </div>

      <div hidden={view !== 'stations'} data-view="stations">
        <div className="stations-layout">
          <WellMap wells={batch.predictions.wells} selectedId={well?.id} onSelect={selectWell} active={view === 'stations'} />
          <section className="panel selection-panel" aria-labelledby="wells-title">
            <h2 id="wells-title">Stations</h2>
            <label htmlFor="station-search">Search by station ID</label>
            <input id="station-search" value={query} onChange={event => setQuery(event.target.value)} placeholder="Search station ID" autoComplete="off" />
            <nav aria-label="Well selection">
              <ul className="well-list" onKeyDown={event => {
                if (event.key !== 'ArrowDown' && event.key !== 'ArrowUp') return;
                const buttons = [...event.currentTarget.querySelectorAll('button')];
                const index = buttons.indexOf(document.activeElement as HTMLButtonElement);
                if (index < 0) return;
                event.preventDefault();
                buttons[index + (event.key === 'ArrowDown' ? 1 : -1)]?.focus();
              }}>
                {listed.map(item => {
                  const itemSummary = method ? item.summaries[method] : undefined;
                  return <li key={item.id}>
                    <button type="button" aria-pressed={item.id === well?.id} onClick={() => selectWell(item.id)}>
                      <span>{item.id}</span>
                      <span className="well-role">{roleLabels[item.role]} · {priorityLabel(itemSummary?.priority)}</span>
                    </button>
                  </li>;
                })}
              </ul>
            </nav>
            {listed.length === 0 && <p role="status">No station matches that search.</p>}
          </section>
          {well && method && <section aria-labelledby="station-card-title" className="panel station-card">
            <p className="eyebrow">Selected station</p>
            <h3 id="station-card-title">{well.id}</h3>
            <p className="depth-readout">{available ? formatDepth(summary?.latest_depth_m) : 'Unknown'}</p>
            <p>metres below ground</p>
            <p>30-day change: {available ? changeText(summary?.change_30d_m) : 'Unknown'}</p>
            <p className={`priority-badge priority-${summary?.priority ?? 'unknown'}`}>Inspection priority: {priorityLabel(summary?.priority)}</p>
            <p>{roleDescriptions[well.role]}</p>
            <button type="button" className="primary" onClick={() => openView('analyze')}>Analyze Station</button>
            <dl className="metadata exact-fields">
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
          </section>}
        </div>
      </div>

      <div hidden={view !== 'analysis'} data-view="analysis" className="analysis-layout">
        <section className="panel analysis-controls">
          <h2>Reconstruction</h2>
          {well && <OutageControls batch={batch} well={well} mode={mode} onAction={action => dispatch({ type: 'demo', action, role: well.role })} />}
        </section>
        <HistoryChart key={state.chartEpoch} batch={batch} selection={selection} demoMode={mode} />
        <PriorityResults batch={batch} selectedId={well?.id} method={method} onSelectWell={selectWell} onSelectMethod={next => dispatch({ type: 'method', method: next })} />
      </div>

      <div hidden={!assistantOpen} data-view="assistant" className={view === 'assistant' ? 'assistant-page' : 'assistant-drawer'}>
        {view !== 'assistant' && <button type="button" className="text-button drawer-close" onClick={() => setAquaOpen(false)}>Close</button>}
        <AquaChat batch={batch} stationId={well?.id} chartMethod={method} messages={messages} onMessages={setMessages} />
        <details className="connection-details" open>
          <summary>Agent37 connection check</summary>
          <AgentBriefing context={batch.agent_context} selectedId={well?.id} method={method} />
        </details>
      </div>
    </main>
    <button type="button" className="aqua-launcher" aria-expanded={assistantOpen} aria-controls="aqua-title" onClick={() => view === 'assistant' ? openView('stations') : setAquaOpen(open => !open)}>
      <AquaMark idPrefix="aqua-launcher" />
      <span className="sr-only">Aqua</span>
    </button>
    <AboutData batch={batch} open={about} onClose={() => setAbout(false)} />
    <footer>Historical reconstruction prototype. Export validation does not verify model accuracy or leakage prevention.</footer>
  </>;
}
