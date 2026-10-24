export const methods = ['idw', 'gcn_lstm', 'gcn_lstm_physics'] as const;
export type Method = typeof methods[number];
export type Role = 'visible' | 'train_masked' | 'holdout';
export interface Metadata {
  schema_version: '1.0.0';
  run_id: string;
  dataset_id: string;
  dataset_kind: 'real' | 'synthetic';
  artifact_kind: 'fixture' | 'model_output';
  generated_at_utc: string;
  as_of_date: string;
  default_method: Method;
  depth_unit: 'm_below_ground';
  caption: string;
}
export interface Summary {
  latest_depth_m: number | null;
  change_30d_m: number | null;
  priority: 'high' | 'watch' | 'normal' | 'unknown';
  reason_codes: string[];
}
export interface Well {
  id: string;
  latitude: number;
  longitude: number;
  role: Role;
  observations_m: (number | null)[];
  predictions_m: Record<Method, (number | null)[]>;
  summaries: Record<Method, Summary>;
}
export interface Metric {
  status: 'not_run' | 'completed' | 'failed';
  validation_mae_m: number | null;
  validation_pairs: number;
  test_mae_m: number | null;
  test_rmse_m: number | null;
  test_pairs: number;
  test_wells: number;
  lambda: number | null;
}
export interface Batch {
  predictions: { meta: Metadata; dates: string[]; wells: Well[] };
  metrics: {
    meta: Metadata;
    evaluation: { test_group: 'holdout'; same_common_mask: true; split_seed: number; notes: string };
    methods: Record<Method, Metric>;
  };
  run_info: {
    meta: Metadata;
    code_revision: string | null;
    checkpoint_sha256: string | null;
    python_version: string | null;
    torch_version: string | null;
    device: string | null;
    nodus_job_ids: string[];
    selected_positive_lambda: number | null;
    physics_assumptions: string[];
    data_sources: string[];
  };
  agent_context: {
    meta: Metadata;
    limitations: string[];
    wells: (Summary & { id: string; role: Role; method: Method })[];
  };
}
