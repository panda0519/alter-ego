import type { Batch, Well } from './data/models';
import type { DemoAction, DemoMode } from './data/outage';

export default function OutageControls({ batch, well, mode, onAction }: {
  batch: Batch; well: Well; mode: DemoMode; onAction: (action: DemoAction) => void;
}) {
  if (well.role !== 'holdout') return <p>Outage and reveal are available only for held-out wells. This well remains viewable in its exported evaluation role.</p>;
  const modeLabels = { 'sensor-available': 'Sensor available (historical setup)', 'simulated-outage': 'Simulated outage', reveal: 'Observations revealed' };
  return <section className="outage-controls" aria-labelledby="outage-title">
    <h3 id="outage-title">Historical outage demonstration</h3>
    <p id="outage-state" role="status" data-mode={mode}>{modeLabels[mode]}</p>
    <p>The demonstration covers {batch.predictions.dates[0]} to {batch.predictions.dates.at(-1)}. This is a historical presentation, not a live sensor status.</p>
    <p>{batch.predictions.meta.artifact_kind === 'fixture'
      ? 'These are illustrative fixture estimates. No model has been trained. In a model export, estimates are precomputed with this well\'s readings excluded.'
      : 'These estimates were precomputed with this well\'s readings excluded from reconstruction inputs.'} Buttons change presentation only; they do not train or execute a model.</p>
    <p>{mode === 'reveal' ? 'Withheld readings are now overlaid for comparison. Originally missing readings remain missing.' : 'Held-out readings stay hidden until you simulate an outage and then reveal observations.'}</p>
    <div className="outage-buttons">
      <button id="simulate-outage" type="button" disabled={mode === 'simulated-outage'} onClick={() => onAction('outage')}>Simulate outage</button>
      <button id="reveal-observations" type="button" disabled={mode !== 'simulated-outage'} onClick={() => onAction('reveal')}>Reveal observations</button>
      <button id="reset-outage" type="button" onClick={() => onAction('reset')}>Reset demonstration</button>
    </div>
  </section>;
}
