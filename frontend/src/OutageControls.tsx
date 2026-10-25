import type { Batch, Well } from './data/models';
import type { DemoAction, DemoMode } from './data/outage';

export default function OutageControls({ batch, well, mode, onAction }: {
  batch: Batch; well: Well; mode: DemoMode; onAction: (action: DemoAction) => void;
}) {
  if (well.role !== 'holdout') return <p>Outage and reveal are available only for held-out wells. This well remains viewable in its exported evaluation role.</p>;
  const modeLabels = { 'sensor-available': 'Sensor available (historical setup)', 'simulated-outage': 'Simulated outage', reveal: 'Observations revealed' };
  return <section className="outage-controls" aria-labelledby="outage-title">
    <h3 id="outage-title">Outage demonstration</h3>
    <p id="outage-state" role="status" data-mode={mode}>{modeLabels[mode]}</p>
    <p>Show a historical gap from {batch.predictions.dates[0]} to {batch.predictions.dates.at(-1)}, then reveal withheld readings only when this station allows it.</p>
    <div className="outage-buttons">
      <button id="simulate-outage" type="button" disabled={mode === 'simulated-outage'} onClick={() => onAction('outage')}>Simulate Outage</button>
      <button id="reveal-observations" type="button" disabled={mode !== 'simulated-outage'} onClick={() => onAction('reveal')}>Reveal Observations</button>
      <button id="reset-outage" type="button" onClick={() => onAction('reset')}>Reset</button>
    </div>
  </section>;
}
