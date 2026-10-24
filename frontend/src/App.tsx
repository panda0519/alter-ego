export default function App() {
  return (
    <>
      <a className="skip-link" href="#workspace">Skip to workspace</a>
      <header className="page-header">
        <p className="eyebrow">Groundwater reconstruction</p>
        <h1>Alter Ego</h1>
        <p className="intro">A workspace for inspecting historical gaps in groundwater sensor readings.</p>
        <ul className="badges" aria-label="Prototype and dataset status">
          <li>Historical prototype</li>
          <li>Synthetic fixture planned · artifact_kind=fixture</li>
          <li>No dataset loaded</li>
        </ul>
      </header>

      <main id="workspace" tabIndex={-1}>
        <aside className="notice" aria-label="Prototype limitations">
          <strong>Frontend shell</strong>
          <p>Data has not been loaded. No estimates, observations or accuracy results are displayed.</p>
        </aside>

        <div className="workspace-grid">
          <section className="panel" aria-labelledby="wells-title">
            <p className="eyebrow">01 / Wells</p>
            <h2 id="wells-title">Well list</h2>
            <p className="empty-state">Well locations and evaluation roles will appear here after a dataset is loaded.</p>
          </section>

          <section className="panel" aria-labelledby="map-title">
            <p className="eyebrow">02 / Region</p>
            <h2 id="map-title">Well map</h2>
            <p className="empty-state">No well locations loaded.</p>
          </section>

          <section className="panel" aria-labelledby="chart-title">
            <p className="eyebrow">03 / History</p>
            <h2 id="chart-title">Depth over time</h2>
            <p className="empty-state">No time series loaded. Depth will be shown in metres below ground.</p>
          </section>

          <section className="panel" aria-labelledby="results-title">
            <p className="eyebrow">04 / Evaluation</p>
            <h2 id="results-title">Results</h2>
            <p className="empty-state">No evaluation results loaded. Illustrative fixture metrics are not trained model results.</p>
          </section>
        </div>
      </main>

      <footer>Historical reconstruction prototype. Field accuracy has not been demonstrated.</footer>
    </>
  );
}
