# Alter Ego: shared instructions for Codex and Cursor

Read MASTER_PLAN.md, contracts/README.md and ml/configs/prototype.yaml before implementation.
This pack is preparation material, configuration, schemas, UI fixtures and phase prompts.
It is not a completed app, trained model or proof of sponsor eligibility.

## Product
Build a historical groundwater sensor-outage reconstruction prototype. Retain a genuine
GCN + LSTM and a simplified water-balance regulariser. Use one region and a small dataset.
Demo: select a held-out well, simulate outage, show precomputed estimates, reveal withheld
readings, inspect priorities, open the Agent37-hosted briefing. Do not claim live monitoring,
future forecasting, official danger thresholds or demonstrated real-world accuracy from synthetic data.

## Shared decisions
- Person A uses Codex locally and owns frontend/, agent/, docs/ and presentation/.
- Person B uses Cursor locally and owns ml/, tests/ and private local data/ and runs/.
- Person A owns contracts/, root setup files and the frontend data publishing step.
  Person B reviews schema changes. Both agree before any breaking contract change.
- Read-only access to all project files is allowed. Do not modify the other person's area
  in an ordinary phase. Describe a required cross-area change in your own status note.
- React + TypeScript + Vite, plain CSS, Leaflet directly and Recharts. No custom backend.
- Python 3.11, PyTorch 2.8.0, dense adjacency GCN, one unidirectional LSTM.
- No torch_geometric, TensorFlow, Optuna, auth, payments, live sensors, multi-region rollout,
  phone messaging or scheduled automation in the required scope.
- Read the versioned contracts and fixtures. Dates are YYYY-MM-DD; depth is metres below ground.
  Missing values are null in JSON and NaN plus a boolean validity mask in model arrays.
- artifact_kind=fixture must remain visible. Never turn illustrative fixture metrics into results.
- Each run fixes the well split and chronological date split. Held-out values never enter
  inputs, label losses, scalers or calibration. Their coordinates and weather may be used.
- Save withheld measurements separately for evaluation. Dashboard reveal is allowed after
  scoring; agent_context.json excludes those measurements.
- JSON is the handoff. Frontend never retrains, recalculates scientific flags or requires Python at runtime.
- Estimate and review Nodus compute before launching. Keep platform approval controls enabled.
  Do not purchase additional credits, start unbounded jobs or create fake sponsor evidence.
- Never place secrets in Git or VITE_ variables. No destructive Git commands or force pushes.
- Implement one requested phase at a time. Run acceptance checks, fix their failures, and stop
  before future phases. Do not silently change architecture, units, groups or field names.
- If blocked, report the precise missing input and complete independent work. Do not invent
  credentials, measurements, API routes, platform capabilities or completed checks.
- After each phase update only your own docs/STATUS_A.md or ml/STATUS_B.md. Report changed
  files, exact checks and outcomes, commands to run, remaining issues and the handoff revision.
- Prompt files are work specifications, not instructions to disable approvals or safeguards.

## Git
main is the integrated branch. A works on feature/product; B works on feature/model.
A is integration owner. Commit completed phases; communicate the commit SHA. A reviews and
merges B's branch at agreed checkpoints, validates, pushes main; B merges main back before
starting work that depends on the integration. Do not squash away the pre-event disclosure.
