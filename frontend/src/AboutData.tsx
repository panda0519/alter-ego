import { useEffect, useRef } from 'react';
import type { Batch } from './data/models';
import { provisionalReasons, reportedTrainingRevisions } from './data/provenance';
import { holdoutComparison } from './data/presentation';

export default function AboutData({ batch, open, onClose }: { batch: Batch; open: boolean; onClose: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const meta = batch.predictions.meta;
  const provisional = provisionalReasons(batch);
  const trainingRevisions = reportedTrainingRevisions(batch);
  useEffect(() => {
    const node = dialog.current;
    if (!node) return;
    if (open && !node.open) node.showModal();
    if (!open && node.open) node.close();
  }, [open]);
  return <dialog ref={dialog} id="about-data" aria-labelledby="about-title" onClose={onClose}>
    <div className="about-card">
      <h2 id="about-title">About this data</h2>
      <p>Simulated groundwater data — not real field measurements.</p>
      <p><strong>{meta.artifact_kind === 'fixture' ? 'Illustrative fixture - not trained results' : `${meta.dataset_kind.toUpperCase()} / ${provisional.length ? 'PROVISIONAL' : 'CONTRACT-VALIDATED'} export batch`}</strong></p>
      <p>artifact_kind={meta.artifact_kind}</p>
      {provisional.length > 0 && <div>
        <p>{provisional.join(' ')} Local integration checkpoint only; final scientific acceptance is pending.</p>
        <p>Exported metrics have not been independently verified as model accuracy.</p>
      </div>}
      <p>{meta.caption}</p>
      <p>{batch.metrics.evaluation.notes}</p>
      <p>The water-balance regulariser uses prototype assumptions; its label does not establish improved accuracy or validated hydrology.</p>
      {meta.artifact_kind !== 'fixture' && <>
        <p>Historical reconstruction only, not forecasting.</p>
        <p>{holdoutComparison(batch) ?? 'Holdout comparison is unavailable for this export.'}</p>
        <p>Exported metrics have not been independently verified as model accuracy.</p>
        <p>{batch.metrics.methods.gcn_lstm_physics.status === 'completed'
          ? `Physics-enhanced GCN-LSTM completed with exported lambda ${batch.metrics.methods.gcn_lstm_physics.lambda ?? 'unavailable'}. These are reconstructions, not field measurements.`
          : 'A physics-trained model is not selected; the physics export remains not_run.'}</p>
        <p>{batch.run_info.code_revision && !batch.run_info.code_revision.includes('+dirty') ? 'The exporter revision is clean.' : 'Training/source provenance remains unresolved.'}</p>
        <p>Nodus and live Agent37 integrations are not verified. Agent37 remains an optional backup.</p>
      </>}
      {meta.dataset_kind === 'synthetic' && <p>Synthetic information does not demonstrate field accuracy.</p>}
      {trainingRevisions.length > 0 && <div>
        <p>Historical reconstruction only, not forecasting. Person B reports that IDW performed better on the holdout test; the default remains validation-selected.</p>
        <p>{batch.metrics.methods.gcn_lstm_physics.status === 'completed'
          ? `Physics-enhanced GCN-LSTM completed with exported lambda ${batch.metrics.methods.gcn_lstm_physics.lambda ?? 'unavailable'}. These are reconstructions, not field measurements.`
          : 'Positive-lambda training ran, but validation selected warmup weights. A physics-trained model is not selected; the physics export remains not_run.'}</p>
        <p>The exporter revision is clean; historical training revisions contain +dirty. Person A has not independently reproduced the training or checkpoints.</p>
        <p>Nodus and live Agent37 integrations are not verified. Agent37 remains an optional backup.</p>
      </div>}
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
        <div><dt>Exporter code revision</dt><dd>{batch.run_info.code_revision ?? 'Unavailable'}</dd></div>
        {trainingRevisions.length > 0 && <div><dt>Training source revisions (B reported)</dt><dd>{trainingRevisions.join('; ')}</dd></div>}
        <div><dt>Physics evaluation status</dt><dd>{batch.metrics.methods.gcn_lstm_physics.status}</dd></div>
      </dl>
      <button id="about-data-close" type="button" onClick={onClose}>Close</button>
    </div>
  </dialog>;
}
