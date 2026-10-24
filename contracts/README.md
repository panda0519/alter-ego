# Contract 1.0.0

Four files form one export batch. Their run_id, dataset_id and schema_version must match.
Person B exports under artifacts/exports/<run_id>/; A validates then copies all four to
frontend/public/data/. Do not replace one file without the rest of the batch.

- predictions.json: dates, metadata and per-well observations, method series and summaries.
- metrics.json: permitted validation and final hold-out test MAE/RMSE/counts per method.
- run_info.json: actual environment and run/evidence identity; unknown facts are null.
- agent_context.json: summary-only input for Agent37, excluding withheld observations.

Methods: idw, gcn_lstm, gcn_lstm_physics. A positive-lambda run is selected using validation;
the test is not used to pick it. default_method is validation-selected across those methods.
On each well, predictions_m has one date-aligned nullable series per method; summaries has
latest_depth_m, change_30d_m, priority and reason_codes per method. An unavailable method
has all-null series and unknown summary. Never label substituted IDW as a neural method.

role is visible, train_masked or holdout. observations_m may include withheld truth for the
dashboard reveal, but never flows back to training or agent_context. series dates are shared,
unique and chronological. Unit is m_below_ground. Missing is null; JSON NaN/Infinity forbidden.
The current date is not the observation date. Both generated_at_utc and as_of_date must show.

artifact_kind=fixture means illustrative UI numbers, never trained results. The six-well fixture
is smaller than the forty-well training target. Its metrics are not_run and cannot be cited as
an experiment. artifact_kind=model_output is only used for real completed pipeline output;
dataset_kind may still be synthetic and must remain visible.

Contract changes need A+B agreement, schema update, fixture update and validation together.
Use scripts/validate_exports.py for schema + semantic consistency. This checker does not
verify hydrological assumptions or model leakage; those require B's meaningful tests.
