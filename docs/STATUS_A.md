# Person A status

## Agent37 connector status - 2026-10-25 IST

The Aqua proxy path is present and fail-closed. `AquaChat.tsx` calls `assistant.ts`, which uses the export briefing unless `VITE_AGENT_PROXY_URL` reaches `agent/proxy/server.mjs`. Fallback behaviour is covered by the assistant checks. Live Agent37 verification is pending. No reply `{ source: "agent37", text }` from instance `gr7nnwqxgf` has been observed. Server variables `AGENT37_API_URL`, `AGENT37_API_KEY`, and `AGENT_CONTEXT_URL` are not in Git. The Render site stays a static site. Details are in `agent/ACCEPTANCE.md`.

## Completed physics export - 2026-10-25 IST

Local training after the warmup-epoch checkpoint fix produced `b13-physics-syn40-seed42`.
Dataset `cbb724e586ee572b618b25c0fa35f23362104f402b3cc008d52c68662a49865b`, synthetic, seed 42.
All three methods are completed on one common mask: 713 validation pairs, 10 wells; 1109 holdout pairs, 8 wells.

| Method | Validation MAE (m) | Holdout test MAE (m) | Lambda |
| --- | --- | --- | --- |
| IDW | 1.1042053369012759 | 1.4958895956006708 | none |
| GCN-LSTM | 0.8590178847921711 | 1.6321938024373073 | 0 |
| Physics-enhanced GCN-LSTM | 0.795083214362352 | 2.0695366678091838 | 0.1 |

The physics checkpoint is `runs/lambda01`, epoch 13, lambda 0.1. It does not match the lambda-0 weights. Default method is `gcn_lstm_physics` by validation MAE. IDW still has the lower holdout test MAE. This is not field accuracy. Nodus was not used.

Published copies: `artifacts/exports/b13-physics-syn40-seed42/` and `frontend/public/data/`.

Checks after publication:
- `npm.cmd --prefix frontend run validate:data`: PASS.
- `npm.cmd --prefix frontend run typecheck`: PASS.
- `npm.cmd --prefix frontend test`: PASS, 130 tests.
- `npm.cmd --prefix frontend run build`: PASS, 688 modules.
- `.venv\Scripts\python.exe -m pytest tests/test_physics.py::test_positive_lambda_selection_ignores_warmup_epochs tests/test_evaluation.py tests/test_exports.py`: PASS, 21 tests.
- Fixture and candidate browser checks against `http://127.0.0.1:4173`: PASS.

## Compact analysis UI and physics checkpoint rule - 2026-10-25 IST

Superseded by the completed physics export above. At the time of this note, physics was not completed. The published batch was `b12-final-syn40-seed42-r2`.
`gcn_lstm_physics` is still `not_run`, with null validation MAE, test MAE, test RMSE, and lambda.
IDW validation MAE is 1.1042053369012759 m and holdout test MAE is 1.4958895956006706 m.
GCN-LSTM validation MAE is 0.8598469860694834 m and holdout test MAE is 1.626403108513909 m.
IDW still has the lower holdout test MAE. The default method remains `gcn_lstm`, chosen from validation.

Blocker for a real physics export on this machine:
- `data/processed/active` is absent.
- `runs/` checkpoints are absent. The earlier lambda 0.1 and lambda 1 checkpoints were epoch-3 warmup weights and were not saved as post-warmup weights.
- `.venv\Scripts\python.exe` is Python 3.11.9 with jsonschema 4.25.1 and does not have PyTorch. System Python 3.11 also has no torch.
- `data/cache/power` is absent, so the synthetic bundle cannot be regenerated offline from NASA POWER weather.

No fake completed physics JSON was written. `frontend/public/data/` and `contracts/` were not rewritten.

ML selection now keeps a positive-lambda checkpoint only for epochs after `lambda_zero_epochs` once lambda is active. Lambda 0 may still select any epoch. The exporter can write a completed physics series only when evaluation marks a distinct positive-lambda checkpoint and lambda is 0.1 or 1.0. A warmup checkpoint is refused. `pytest` was not run because PyTorch is not installed. `ast.parse` of the changed Python files succeeded.

UI: the analysis header is a station pill, role badge, and export date range. The demo opens on the first holdout station. Non-holdout stations on Analysis show one switch to that holdout. The chart uses legend pills. Method cards use IDW Baseline, GCN-LSTM, and Physics-Informed GCN-LSTM, with View / Active Model controls. Evaluation notes, artifact kind, and the water-balance statement stay in About this data. Priorities are a scrollable table and still include every well.

Checks:
- `npm.cmd --prefix frontend run validate:data`: PASS.
- `npm.cmd --prefix frontend run typecheck`: PASS.
- `npm.cmd --prefix frontend test`: PASS, 130 tests, 0 failed.
- `npm.cmd --prefix frontend run build`: PASS. Vite reported 688 modules.
- `git diff --check`: PASS.
- `node checks/browser.mjs` from `frontend/` against `http://127.0.0.1:4173`, with `ALTER_EGO_CHECK_BATCH` unset: PASS, including the fixture scenarios and no uncaught exceptions.
- `ALTER_EGO_CHECK_BATCH=candidate` then `node checks/browser.mjs`: PASS. All 120 well/method selections, 48 outage cycles, and the served batch still show physics as not completed.

Local preview: `http://127.0.0.1:4173`.

## UI refresh on feature/ui-refresh - 2026-10-25 IST

Presentation rebuild on top of integrated main `d323285`. Scientific files, contracts,
and the published `b12-final-syn40-seed42-r2` batch were not rewritten.
`feature/ui-refresh` commit `a06ce01` was not present locally or on origin, so this
refresh started from `d323285`.

What changed:
- Three views: Stations, Analysis, and AI Assistant. The selected station, method,
  and outage state stay in place when the view changes.
- Stations opens on the exported map, a searchable station list, and a station card.
  Coordinates stay the validated synthetic positions. The map is labelled as a
  demonstration region.
- Analysis keeps the existing chart, null gaps, outage/reveal/reset rules, priority
  order, and exact evaluation numbers. Display text uses IDW, GCN-LSTM, and
  Physics-enhanced GCN-LSTM. Physics stays Not available while its status is not_run.
  The comparison states that IDW has the lower holdout test MAE on this export.
- Full provenance, dirty training revisions, Nodus status, and technical metadata
  remain in About this data. The visible banner is: Simulated groundwater data —
  not real field measurements.
- Aqua is a CSS/SVG assistant. Suggested questions are answered from the validated
  export. Live Agent37 is not claimed. A minimal connector at `agent/proxy/`
  forwards questions only when `AGENT37_API_URL`, `AGENT37_API_KEY`, and
  `AGENT_CONTEXT_URL` are set on the server. Those values are not in the frontend
  or Git. The public static site uses the export briefing.

Checks on 2026-10-25:
- `npm.cmd --prefix frontend run validate:data`: PASS.
- `npm.cmd --prefix frontend run typecheck`: PASS.
- `npm.cmd --prefix frontend test`: PASS, 130 tests, 0 failed. The previous 124
  checks remain, plus navigation, export-briefing, proxy rejection, rate limit,
  unauthorized, timeout, leaked-context, and frontend-secret checks.
- `npm.cmd --prefix frontend run build`: PASS. Vite reported 688 modules.
- `node checks/browser.mjs` against `http://127.0.0.1:4173`: PASS, including the
  18 fixture combinations, map sync, chart gaps, 24 outage cycles, priorities, and
  the Agent37 context-check states.
- `ALTER_EGO_CHECK_BATCH=candidate; node checks/browser.mjs`: PASS, including all
  120 well/method selections and 48 outage/reveal/reset cycles.
- `git diff --check`: PASS. `contracts/`, `frontend/package-lock.json`, and
  `frontend/public/data/` were not modified.

Local preview: `http://127.0.0.1:4173`.
The optional proxy, from the repository root, is `node agent/proxy/server.mjs`
on `http://127.0.0.1:8787` after the three server variables are set. It was not
deployed and no Agent37 credential was used.

Render: the existing static site can deploy from `main` with the repository root
as the root directory, Node 24.22.1, build `cd frontend && npm ci && npm run build`,
and publish directory `frontend/dist`. Do not add a start command or put API keys
in Vite variables. Live Agent37 remains blocked until a separate approved proxy
host exists.

## A09 B12-r2 local integration handoff - 2026-10-24 IST

Local integration: PASS. Person B's intended final export is integrated, but remains
SYNTHETIC / PROVISIONAL. Scientific verification and final deployed A09 acceptance
are NOT claimed. This entry supersedes the B09 batch below; older entries are history.

Input frontend commit: fb98dafd53349a864eb13c414100282c50ab8a6c.
Fetched feature/model tip: 2690ac59d6940d6a72cf7fe19b6b2bb7e5b49a02.
Pinned candidate: 89d85dae75267e3c0ba99abf607f42771fa0c371, verified ancestor
of that remote tip. Candidate directory: artifacts/exports/b12-final-syn40-seed42-r2/.
Run ID: b12-final-syn40-seed42-r2.
Dataset: 05902f5167e6a8aefa02386b6437bfa984a2ec3b67e3fffee7c69d7b145c8351,
synthetic / model_output / contract 1.0.0. Generated 2026-10-24T18:03:30Z,
as_of_date 2024-12-31; 40 wells, 60 dates 2024-11-02 through 2024-12-31.
Default method gcn_lstm; depth m_below_ground.

Read AGENTS.md, MASTER_PLAN.md, prompts/A09.md, this status, docs/HANDOFF.md,
contracts/README.md, model config and relevant source/tests. Local ml/STATUS_B.md
is the old template because no merge was performed; reviewed the actual fetched
ml/STATUS_B.md, B_PHASE_3/4/5_SELF_CHECK.md, ml/evaluate.py and evaluation tests
from feature/model read-only. No ML implementation, contracts or B-owned files changed.

Acceptance before publication:
- git fetch origin feature/model completed without merge/checkout/remote writes.
  GitHub read-only branch listing independently confirmed tip 2690ac5 and release
  branch fb98daf. Candidate exists remotely and all four files equal the tip copies.
- Extracted four files with git show into Windows TEMP; SHA-256 matched every
  hash reported in B's fetched status. Candidate schemas exactly match local schemas.
- Ran Python validator and the full frontend suite against the staged directory
  before copying. All 123 then-existing tests passed. Only then replaced the
  complete four-file frontend/public/data batch. No JSON field was rewritten.
- frontend/src/data/handoff.json records source commit/tip/run/dataset, exact
  hashes, clean export revision and B-reported historical dirty training revisions.
  Supersedes frontend/checks/candidate.json, whose old B09 manifest was removed.

Exact SHA-256 (also checked against source/public/dist/HTTP/staged Git bytes):
- predictions.json: 3a526df6f36bea39e79210ea25def1277fffd124e5af8e0983a06c6ce4681871
- metrics.json: 187889d55c95613d7ef7b8a93b826b7a76ad131f34b8e8b53c71d24543241ec9
- run_info.json: 35be05d273c50bca33d348a27f84d5786be9327dddd52b9b3115da6833e99e4e
- agent_context.json: 7a99db5ff9671f04b83d76e34ef8986e574dfe409717732b8cb811c1fa0109a0

Frontend changes:
- App.tsx distinguishes the exporter revision from reported training revisions.
  Visible disclosures retain synthetic historical reconstruction, no forecasting/
  field accuracy, IDW's better holdout result, unavailable physics export, dirty
  training provenance and unverified Nodus/live Agent37. Agent37 stays optional.
- data/provenance.ts scopes handoff provenance to matching run/dataset/export
  revision, preventing another future batch from inheriting this run's disclosure.
  Provisional status remains; clean export code does not erase dirty training.
- checks/candidate.test.mjs supports staged data via ALTER_EGO_BATCH_DIR and
  verifies the new source identity; adds a provenance scoping regression.
- checks/candidate-browser.mjs asserts all required limitations in the rendered UI.
- No package/lock change, dependency installation, science recalculation, model
  execution, backend, contract edit, paid resource or A10 implementation.

Final local checks (Node v24.22.1, frontend commands from frontend/):
- node --test --test-reporter=spec checks/*.test.mjs: PASS 124 tests, zero
  failures/skips (117 fixture regressions, 7 candidate checks). Exact identities,
  hashes, nulls, statuses, time-series alignment, summary-only context, all 120
  well/method combinations, repeated reveal/reset, all missing-file/mixed-metadata
  cases and recovery pass. Staged prepublication suite passed separately above.
- Python scripts/validate_exports.py: PASS temporary candidate before publication,
  frontend/public/data after publication, and unchanged contracts/fixtures.
  Checks exact metadata, date/series alignment, nulls, summaries/priorities and
  metric statuses. No withheld observations in agent context. Schema validation
  does not prove training correctness or leakage prevention.
- npm run build: PASS TypeScript/Vite; 682 modules, 20.26 kB CSS,
  913.12 kB JS / 268.58 kB gzip. Non-blocking >500 kB chunk warning retained.
- Production preview on http://127.0.0.1:4173: all four JSON requests HTTP 200,
  application/json, exact pinned hashes and byte equality with public and dist.
- ALTER_EGO_CHECK_BATCH=candidate; node checks/browser.mjs: PASS against actual
  local production files. All 120 well/method selections match chart/table values,
  map selection and statuses. Result fields and priority order match exports.
  48 outage/reveal/reset cycles across 8 held-out wells, 3 methods, desktop 1280px
  and mobile 390px PASS. Null truth preserved; unavailable physics never becomes
  zero or another method; switching/reset hides previous answers. Keyboard outage,
  incomplete/mismatched/malformed rejection/retry, map-tile fallback and optional
  context check PASS. All required limitation text visible. Zero uncaught errors.
- With ALTER_EGO_CHECK_BATCH unset, node checks/browser.mjs: full fixture browser
  regressions PASS, including 24 demo cycles, tooltip privacy, keyboard list/map/
  results, map failures/timeouts/recovery, null/calendar gaps, dataset reset and
  optional Agent37 malformed/missing/network/timeout/retry handling. No exceptions.
- Screenshots captured to TEMP; mobile header and history reviewed: labels/chart
  readable; page overflow assertions pass at desktop/mobile widths. Tile responses
  are intercepted locally; external map-service availability is not certified.
- React review: provenance is derived during render, escaped text, no added state
  or effects; existing keyboard/loading/error semantics remain intact.
- git diff --check and cached check PASS; staged paths/content reviewed before
  commit. Only frontend integration/checks and this note; no secrets, credentials,
  generated build/screenshots, local arrays, model weights or B files staged.

Model evidence review and limitations (B-reported, not locally reproduced):
- Exporter code_revision is clean 9ea9652f89dd79f60b8ba7c0d7a39bf32704f43b,
  ancestor of the candidate. Git confirms changes from d622419 to that revision
  are status/checklist documents only. This does not establish clean training.
- Lambda-zero training code_revision remains
  27631dc55c4c65d87e394a54ef0aa5879cb69468+dirty. Positive-run payload revisions
  remain 473bd2b4ba3c791028c805ea743e23d9a6281b4f+dirty. Neither is rewritten.
  Selected checkpoint hash: 721a5416ed797f10b87ab5d3f439d31107b39681dcd7b480305a994a65916c6a.
- B's phase 4 evidence reports positive-lambda training, but both retained epoch 3
  at lambda 0 with weights equal to the lambda-zero model. Physics-trained weights
  are not selected; gcn_lstm_physics remains not_run, predictions and metrics null,
  summaries unknown, selected_positive_lambda null. No physics accuracy gain.
- Reviewed selection/scoring code: default chosen from common validation MAE
  before holdout; one score per ending date; export checks same device and frozen
  scores. B reports 61 ML tests PASS (one sandbox CUDA warning), same-device reload
  difference 0.0 m, tolerance 0.0001 m. CPU difference 0.0009213380646091451 m was
  rejected; tolerance was not weakened. A did not run B's ML suite or GPU training:
  private bundle, checkpoint payloads, manifests and frozen evaluation are absent
  here. Full model/scientific verification remains PENDING independent reproduction.
- Reported validation: 713 pairs, 10 train-masked wells; MAE IDW 1.1042053369012759 m,
  GCN-LSTM 0.8598469860694834 m. Default stays validation-selected gcn_lstm.
- Reported holdout: 1109 common pairs / 8 wells, 1319 valid labels,
  coverage 0.8407884761182715. IDW MAE/RMSE 1.4958895956006706 / 2.034039534948381 m;
  GCN-LSTM 1.626403108513909 / 2.0547485083440558 m. IDW performed better.
- Synthetic known-location historical reconstruction, not field accuracy, live
  monitoring, forecasting, official danger thresholds or hydrological validation.
- Held-out truth never enters chart/tooltip/table before permitted Reveal and
  never enters agent context. Public predictions.json intentionally includes
  reveal observations per contract: presentation privacy is not access control.
- Nodus unverified/not run; no job IDs. Live Agent37 PENDING/OPTIONAL; account
  confirmed by user only, no live fetch/answer evidence. No joint rehearsals yet.

Release/deployment handoff (NOT performed):
- Local/remote release/alter-ego-demo observed at fb98daf. After reviewing and
  approving this commit, disable/confirm disabled Render auto-deploy first.
  Fetch release, switch to it with a clean tree, fast-forward to origin/release,
  then git merge --ff-only <this verified integration commit>. Stop on divergence;
  never reset, force-push, rewrite main or merge B automatically. Push release only
  after explicit approval; switch back to feature/person-a afterward.
- Current Render docs confirm files outside Root Directory are unavailable at
  build time. frontend imports repository-level contracts, so proposed settings:
  Static Site; repo panda0519/alter-ego; branch release/alter-ego-demo;
  Root Directory BLANK (repository root); build cd frontend && npm ci && npm run build;
  publish frontend/dist; NODE_VERSION=24.22.1; SKIP_INSTALL_DEPS=true;
  auto-deploy/PR previews disabled; no start command/router rewrite/backend;
  VITE_AGENT37_URL and VITE_AGENT_CONTEXT_URL unset. No client-side secrets.
  Sources: https://render.com/docs/monorepo-support,
  https://render.com/docs/static-sites, https://render.com/docs/node-version.
- This root/branch proposal differs explicitly from prompts/A09.md's frontend/main
  settings; user must confirm the concrete deployment target/configuration.
- Pending approval: release update/push and deployment; confirm My Workspace
  (tea-da17ge8u01pc739l275g), exact Static Site name/service ID, Render GitHub repo
  authorization and auto-deploy state. No Render resource inspection/change or
  deployment was performed. Existing remote main is untouched.
- Final deployed URL/hash checks, both-laptop acceptance and rehearsals PENDING.
  A09 local integration passes; final A09 acceptance is NOT declared. Commit only
  on feature/person-a; no push/merge/release update/deployment. SHA reported after commit.

## A09 provisional local integration checkpoint - 2026-10-24 IST

Local integration: PASS. Final scientific acceptance: PENDING. Deployment: BLOCKED
pending confirmed Render workspace/target and resolution of unrelated remote main.
This is not completion of A09's deployed-site/two-laptop acceptance. No A10 work.

Source branch: feature/model, fetched without merging. Pinned source commit:
473bd2b4ba3c791028c805ea743e23d9a6281b4f (also fetched origin/feature/model).
Run: b09-gcn-lstm-lambda0-syn40-seed42.
Source directory: artifacts/exports/b09-gcn-lstm-lambda0-syn40-seed42/ at that commit.
Dataset: 05902f5167e6a8aefa02386b6437bfa984a2ec3b67e3fffee7c69d7b145c8351.
dataset_kind=synthetic; artifact_kind=model_output; schema_version=1.0.0.
Generated 2026-10-24T17:08:20Z; as_of_date=2024-12-31; default_method=gcn_lstm.
40 wells, 60 dates (2024-11-02 through 2024-12-31), depth m_below_ground.

Publication and changed files:
- Extracted the exact predictions.json, metrics.json, run_info.json and
  agent_context.json from the pinned Git commit into a temporary directory.
  Ran scripts/validate_exports.py successfully BEFORE copying the complete
  four-file batch into frontend/public/data/. No JSON values were edited.
- frontend/checks/candidate.json records source commit/branch/run and SHA-256
  for each published file. Candidate checks assert byte identity using those hashes.
- frontend/src/data/provenance.ts presents provisional reasons from exported
  method status, positive-lambda selection and source revision; no scientific
  results, priorities, flags or metric values are recalculated.
- frontend/src/App.tsx and PriorityResults.tsx prominently show PROVISIONAL,
  synthetic limitations and pending scientific acceptance; source revision and
  physics status remain visible. styles.css wraps long provenance text on mobile.
- Existing fixture regressions now explicitly read contracts/fixtures/, independent
  of the published model batch. Their scientific/privacy assertions are retained.
  The former fixture-publication equality check is superseded by candidate hashes.
- frontend/checks/candidate.test.mjs and candidate-browser.mjs verify the actual
  candidate. browser.mjs supports fixture interception separately from real local
  candidate HTTP requests, sharing the existing installed-Edge CDP harness.
- docs/STATUS_A.md records this checkpoint. No contracts, ML code, B branch,
  dependency manifests/locks, agent configuration or remote branches changed.

Verified checks (Node v24.22.1; frontend commands run from frontend/):
- `git fetch origin feature/model`: PASS after sandbox escalation; no merge or
  checkout. Fetched head equals the pinned commit above.
- `.\.venv\Scripts\python.exe scripts/validate_exports.py <temporary-candidate-dir>`:
  PASS before publication. Same command with `frontend/public/data` and
  `contracts/fixtures`: both PASS after publication. Checks schemas, all metadata,
  dates/series/nulls, exported latest/30-day summaries, priorities, context summary
  consistency and metric statuses/common test counts. Does NOT certify training,
  leakage prevention, physics or accuracy.
- `node --test --test-reporter=spec checks/*.test.mjs`: PASS 123 tests, zero
  failures/skips (117 fixture regressions plus 6 candidate integration checks).
  Candidate covers all 120 well/method selections, exact series/null preservation,
  8 held-out wells, repeated state transitions, physics unavailable/null metrics,
  exact source bytes, summary-only context, every missing file and every metadata
  mismatch, then full successful recovery. Fixtures stay illustrative/not_run.
- `npm run build`: PASS TypeScript/Vite, 681 modules; 20.26 kB CSS,
  911.07 kB JS / 267.55 kB gzip. Existing non-failing >500 kB bundle warning.
- `npm run preview -- --host 127.0.0.1 --port 4173 --strictPort`: PASS startup.
- `$env:ALTER_EGO_CHECK_BATCH='candidate'; node checks/browser.mjs`: PASS against
  the production preview using installed Edge. Real local four-file HTTP metadata
  matches; all 120 well/method combinations show exact exported chart/table data,
  statuses and matching map selection. All exported result fields and priority
  orders match the batch. 48 outage/reveal/reset cycles across 8 held-out wells,
  3 methods and 1280px/390px layouts pass. Switch/reset hides prior answers;
  null truth remains Missing; unavailable physics is never substituted. Keyboard
  outage, missing/mixed/malformed rejection and retry, map-tile failure fallback,
  optional context check and zero uncaught runtime exceptions PASS.
- With ALTER_EGO_CHECK_BATCH unset, `node checks/browser.mjs`: full A02-A08
  fixture browser suite PASS via test-only response interception, including 24
  outage/reveal/reset cycles, tooltip privacy, keyboard list/map/results actions,
  tile errors/timeouts/map initialization recovery, incomplete/malformed/mixed
  batch/loading/retry, null/calendar chart gaps, stale dataset reset and optional
  Agent37 context invalid/network/timeout/retry states. No uncaught exceptions.
- Browser tiles are intercepted locally: failure handling is verified; external
  tile service availability is not claimed. No training/model request is made.
- Candidate screenshots captured in Windows TEMP for header/map/history/results
  at 390px and 1280px. Reviewed mobile warning/history and desktop results:
  readable labels/plot, no horizontal page overflow; chart width exceeds 200px.
- React review checklist: derived status during render, no added effects/state,
  escaped text, existing accessible selections/loading/error semantics preserved;
  no new dependency or frontend credential configuration.
- `git diff --check`: PASS. Staged review and cached diff check performed before
  commit; only the frontend integration/checks and this status note are included.
  No secrets, generated build/screenshots, raw data or checkpoints staged.

Scientific limitations and pending evidence:
- gcn_lstm_physics status is not_run (the contract has no physics_status field).
  Every physics prediction is null, summary unknown, error metrics null;
  selected_positive_lambda=null. Final positive-lambda/physics acceptance PENDING.
- Source code_revision remains exactly
  27631dc55c4c65d87e394a54ef0aa5879cb69468+dirty. Checkpoint SHA-256 is
  721a5416ed797f10b87ab5d3f439d31107b39681dcd7b480305a994a65916c6a.
  Pinned export bytes are verified, but dirty source reproducibility/checkpoint
  contents and B training/leakage evidence are NOT independently certified.
  B must reconcile provenance in a new reviewed batch; A did not rewrite it.
- Completed IDW/GCN-LSTM report 713 common validation pairs and 1109 common test
  pairs across 8 holdout wells. Exported validation MAEs: IDW 1.1042053369012759 m,
  GCN-LSTM 0.8598469860694834 m. Reported test MAEs: IDW 1.4958895956006706 m,
  GCN-LSTM 1.626403108513909 m. GCN-LSTM is the validation-selected default;
  its reported test MAE is worse than IDW. No improvement/field-accuracy claim.
- Dataset is fictional synthetic data. Reported GPU/environment and checkpoint
  facts are B-exported provenance, not a local retraining or independent audit.
  No Nodus job IDs/evidence; sponsor readiness PENDING.
- Held-out values are excluded from chart/tooltip/table until permitted reveal
  and never enter agent context. Static predictions.json intentionally contains
  reveal observations per contract; presentation privacy is not access control
  or secrecy from a user who reads the public JSON.

Deployment blockers and next handoff:
- Render workspace/target and GitHub App repository authorization PENDING.
  No Render service created, deployment attempted or paid resource changed.
- Remote main at 8cc5fd7435f706cf407ae19fba4e669d78408240 has an empty tree and
  unrelated history to feature/person-a. A09's main deployment cannot build yet.
  A history-preserving integration strategy needs explicit agreement; no merges,
  main changes, force pushes or remote writes were performed.
- Final deployed four-URL metadata checks and both-laptop site checks PENDING.
- Agent37 account VERIFIED by user; live integration PENDING / OPTIONAL.
  Core application remains independent; no active instance or credentials needed.
- This checkpoint is safe for local provisional demonstrations. Final science,
  deployment acceptance and A10 remain pending. Commit locally on feature/person-a;
  do not push/merge/deploy. Commit SHA reported after creation.

## A08 local preparation handoff - 2026-10-24 IST

Local A08 frontend preparation: COMPLETE; applicable local checks PASS.
Agent37 account: VERIFIED by explicit user confirmation (not a tool login test).
Live Agent37 integration: PENDING / OPTIONAL. User confirms no active instance
or public URL and will provide them later. Core application: INDEPENDENT OF
AGENT37, including ML export integration and deployment. Disabled by default;
no instance created, service configuration changed or charges incurred.

Scope conflict explicitly recorded: MASTER_PLAN.md's required demo includes an
Agent37 briefing, and prompts/A08.md requires genuine hosted fetch/answer evidence.
The user's latest explicit instruction makes Agent37 an OPTIONAL BACKUP, overriding
that mandatory core requirement. Shared plan/contracts are not silently rewritten.
The original live acceptance has NOT passed; it remains PENDING / OPTIONAL.
No live response, genuine agent fetch or sponsor integration is claimed.

Read AGENTS.md, README_FIRST.md, MASTER_PLAN.md, COMMON_DECISIONS.md, this status,
prompts/A08.md, agent/INSTRUCTIONS.md, context schema/fixture and relevant frontend
contracts/source/tests, plus model config. A09 read only for the handoff boundary.

Prerequisite investigation before implementation:
- No Agent37 tools/instance URL were available in connected tool discovery.
- Existing VITE_AGENT37_URL example was empty; project/process configuration
  presence check found no configured value. No private values were printed.
- No public deployed context URL or deployment configuration/resource was found
  in project source. Existing local /data/agent_context.json is available.
- Render get_selected_workspace returned no workspace selected; list_workspaces
  found My Workspace. No service reads or workspace selection were attempted
  without confirmation. The Render monitor skill requires following its access
  reference to "verify the intended workspace" before service reads:
  C:/Users/Admin/.codex/plugins/cache/openai-curated-remote/app-6a624c56bfe081918f7544f7d58f6faf/1.0.2/skills/render-monitor/SKILL.md
  This limits deployment inspection, not the independent frontend work.
- User subsequently confirmed the account exists and has no instance/public URL.

Changed files:
- frontend/src/AgentBriefing.tsx: modular optional-service panel, disabled native
  launch when unconfigured, selected-well question and dashboard/default-context
  method distinction. Configured public native URL opens a separate tab with
  noopener/noreferrer; no prompt, selection or data appended/sent automatically.
  Suggested questions are not generated answers. Fixture/type/run/dates visible.
  Local context check has idle/loading/success/unavailable/invalid-response/
  timeout/network-error/retry states. Success explicitly means exported context
  consistency, never Agent37 success. Failures leave the dashboard usable.
- frontend/src/data/briefing.ts: public HTTPS configuration validation (no embedded
  credentials/query/fragment), on-demand credential-free no-store GET, no redirects,
  eight-second timeout and cancellation cleanup. No chat API or model endpoint.
- frontend/src/data/loadBatch.ts: reuses the existing Ajv context validator;
  fetched context must match loaded batch metadata, IDs, summaries and limitations.
  Extra observation fields, stale/mismatched context and malformed data rejected.
- frontend/src/vite-env.d.ts and .env.example: typed Vite public URL configuration;
  VITE_AGENT37_URL and VITE_AGENT_CONTEXT_URL remain BLANK. No fake runtime URLs.
  Without a deployed context URL, the optional check reads the local export only.
- frontend/src/WellWorkspace.tsx and styles.css: selected well/method passed to
  independent responsive panel; no changes to chart reveal state or core loading.
- agent/INSTRUCTIONS.md: strict context/identity/privacy checks, honest failure/
  timeout behavior, fresh actual-tool evidence, default-method limitation.
- agent/SETUP.md: optional activation configuration and exact missing prerequisites;
  original live three-question/fetch-failure acceptance checklist stays pending.
- frontend/checks/briefing.test.mjs and checks/browser.mjs: local preparation and
  regression checks only; no mock agent responses or purported hosted answers.
- docs/STATUS_A.md: this verified status/conflict/handoff.

Actual checks (Node v24.22.1; frontend commands from frontend/):
- `node --test --test-reporter=spec checks/batch.test.mjs checks/selection.test.mjs checks/coordinates.test.mjs checks/history.test.mjs checks/outage.test.mjs checks/results.test.mjs checks/briefing.test.mjs`:
  PASS 118 tests, 0 failures/skips (102 regressions + 16 A08). Covers absent/invalid
  URL configuration, credential-bearing URL rejection, context-only request with
  no cookies/auth/body, matching schema/batch, stale/duplicate/mismatched context,
  added observation fields, empty/bad JSON, missing file, network error, timeout
  and cancellation. URL parser test strings are test inputs, not configured or
  contacted services; no fake URL/credential is supplied as an actual endpoint.
- `npm run build`: PASS TypeScript/Vite; 680 modules; 20.14 kB CSS and
  909.71 kB JS (267.17 kB gzip JS). Existing non-failing >500 kB warning remains.
- `.\.venv\Scripts\python.exe scripts/validate_exports.py frontend/public/data`
  from root: PASS unchanged fixture/schema/semantic checks; no trained result.
- Production preview `npm run preview -- --host 127.0.0.1 --port 4173 --strictPort`;
  final `node checks/browser.mjs`: full suite PASS including optional/disabled
  message, keyboard context check, one fresh context-only GET, explicit non-agent
  success label, well/default-method distinction, context failure simulations
  (invalid JSON, missing, stale, added observations, network, timeout), loading,
  retry, responsive captures and zero uncaught runtime exceptions. All A02-A07
  regressions pass, including 24 outage/reveal/reset cycles and privacy checks.
- Development `npm run dev -- --host 127.0.0.1 --port 5173 --strictPort` then
  `$env:ALTER_EGO_CHECK_ORIGIN='http://127.0.0.1:5173'; node checks/browser.mjs`:
  full suite PASS including StrictMode/Fast Refresh, context states and previous
  regressions; 84 canceled CDP interceptions counted separately, zero uncaught
  page exceptions. Final optional wording was subsequently verified in production.
  Browser execution used approved sandbox escalation; all map tiles intercepted.
- 1280px/390px layout checks: no horizontal overflow. Reviewed desktop/mobile
  briefing screenshots from TEMP/alter-ego-a08-{1280,390}.png. Adjusted capture
  timing after resize so mobile capture shows the briefing rather than preceding
  content. Screenshots are local QA artifacts, not staged integration evidence.
- Source/privacy review: no model calls, no automatic Agent37 requests, no
  invented responses, no exposed keys, no measured/withheld readings in context
  requests even after chart reveal. Existing batch contracts/fixtures, dependencies
  and B-owned files unchanged. No generated files/secrets staged. Working and
  staged `git diff --check`: PASS before commit.

Still PENDING for optional live activation: real public instance URL, actual
runtime fetch/validation tools and provider access, deployed public matching
agent_context.json URL, genuine three-question answers and fetch-failure evidence.
No cross-origin native agent response lifecycle can be observed by this static
dashboard; local context states do not substitute for hosted-service acceptance.
Render deployment inspection awaits workspace confirmation. Full screen-reader
certification and actual B model-export integration also remain PENDING.

A09 can begin when authorized, independently of Agent37. Its B complete export,
Render workspace/repository authorization and deployment checks remain its own
prerequisites. No A09 implementation, push, merge or deployment performed here.
Handoff unchanged: schema 1.0.0; fixture-layout-v1; synthetic-layout-six-wells;
artifact_kind=fixture. Commit: this A08 local-preparation commit, SHA reported
after creation. User's optional-backup decision is recorded above, not treated
as evidence that the original live integration checks passed.

## A07 handoff - 2026-10-24 IST

Phase: A07 implemented; required acceptance checks PASS on feature/person-a.
User confirms A00-A06 pushed; no push performed in this phase. Read AGENTS.md,
README_FIRST.md, MASTER_PLAN.md, docs/COMMON_DECISIONS.md, this status,
prompts/A07.md, relevant contracts/schemas/fixtures and frontend source/tests,
plus model config. A08 read only for the next handoff boundary.

Changed files:
- frontend/src/PriorityResults.tsx: exported per-method priority list and all
  three evaluation result cards. Displays exported reasons, estimates, 30-day
  change, role and as-of date; documented prototype rules and warning disclaimer.
  Priority buttons select the corresponding well and focus its detail heading.
  Result buttons select the exact method using the existing reducer. Run-level
  metrics are labelled as aggregate holdout results, not per-well scores.
  Fixture/real/synthetic identity, run ID and generated/as-of dates remain visible.
  not_run/failed/fixture metrics and counts render Unavailable, never zero error.
  Only validated nonfixture completed exports can report MAE/RMSE/counts/lambda.
  Physics method retains exact identity and the water-balance assumption caveat.
- frontend/src/data/results.ts: projection of exported summaries/results;
  deterministic display order high/watch/normal/unknown, descending exported
  change then stable ID. No recomputation of priority flags, errors, rankings
  from raw readings, training, or method substitution. Unavailable summaries
  render unknown safely. Projections never read observations_m.
- frontend/src/WellWorkspace.tsx: shared well/method state wired to priorities
  and results; detail heading keyboard-focusable. Existing atomic A06 reset
  rules apply when these controls change wells/methods.
- frontend/src/App.tsx: results placeholder only before a validated batch loads.
- frontend/src/styles.css: responsive priority/result card grids and selected
  button styles, wrapping long method IDs/reasons on mobile.
- frontend/checks/results.test.mjs: 9 new acceptance tests.
- frontend/checks/browser.mjs: A07 selection/status/privacy/keyboard checks and
  desktop/mobile captures alongside previous regression/failure simulations.
- docs/STATUS_A.md: verified evidence and handoff.

Actual checks (Node v24.22.1, frontend commands from frontend/):
- `node --test --test-reporter=spec checks/batch.test.mjs checks/selection.test.mjs checks/coordinates.test.mjs checks/history.test.mjs checks/outage.test.mjs checks/results.test.mjs`:
  PASS 102 tests, 0 failures/skips (93 regressions + 9 A07). Covers exact method
  summary/reason identity, documented order, category preservation instead of
  flag recalculation, unavailable summaries, stable ID ties, fixture suppression,
  completed/failed/not_run rendering, zero preservation, physics identity and
  invariance to changed withheld readings. Source batches are not mutated.
- Completed/failed branch coverage uses explicitly TEST ONLY in-memory model
  export responses with zero-error sentinel values/counts. These are UI test
  inputs, not scientific outputs; never saved under public/data, shared fixtures
  or model artifacts. Published fixture metrics remain unchanged and not_run.
  Actual completed model-result integration remains PENDING B's real handoff.
- `npm run build`: PASS TypeScript/Vite; 678 modules; 19.91 kB CSS,
  903.72 kB JS (265.36 kB gzip JS). Existing non-failing >500 kB chunk warning
  remains. No dependencies added/upgraded or warning threshold changed.
- `.\.venv\Scripts\python.exe scripts/validate_exports.py frontend/public/data`
  from root: PASS schema/semantic consistency. Not evidence of scientific accuracy.
- Production: `npm run preview -- --host 127.0.0.1 --port 4173 --strictPort`
  then `node checks/browser.mjs`: full suite PASS. All 18 priority well/method
  pairs show their exported fields and open matching well/map/chart selections.
  All fixture result cells are Unavailable. Changing method through a result
  card or well through priorities obeys A06 reveal reset; no hidden truth appears.
  Enter activates a priority and focuses the detail heading. Test-only validated
  completed/failed/not_run statuses render correctly, zero remains 0 m, unavailable
  methods show unknown priorities, and an attempted completed fixture is rejected
  by validation before result cards appear. All A02-A06 regressions pass,
  including 24 desktop/mobile outage/reveal/reset cycles, map failure/retry,
  chart null gaps/tooltips and dataset reset. Zero uncaught browser exceptions.
- Development: `npm run dev -- --host 127.0.0.1 --port 5173 --strictPort`, then
  `$env:ALTER_EGO_CHECK_ORIGIN='http://127.0.0.1:5173'; node checks/browser.mjs`:
  full suite PASS, including StrictMode and actual Fast Refresh source edit/
  restoration. 75 canceled CDP interceptions during cleanup counted separately;
  zero uncaught page exceptions. Approved Edge execution outside sandbox; all
  map tiles intercepted locally, no public tile downloads.
- Browser layout/screenshot checks at 1280px/390px: no horizontal overflow.
  Reviewed priority and results panels at both widths for readable status/labels,
  wrapping and distinct method identity. TEMP files alter-ego-a07-{priority-panel,
  results-panel}-{1280,390}.png are local QA artifacts, not staged.
- Source review: escaped data labels, semantic lists/headings/definition lists,
  native keyboard buttons, one selection state and preserved reveal sanitization.
- Git scope review: only A-owned frontend source/checks and this status; shared
  contracts, B files, dependency manifest/lock and all public fixtures unchanged.
  No generated build files/secrets staged. `git diff --check` and staged check
  PASS before commit. No push, merge or deploy.

Remaining: no A07 blocker. Bundle-size warning is non-blocking; actual completed
model-export integration, full screen-reader certification and live public tiles
remain PENDING. Fixtures demonstrate interface behavior, not field accuracy.

A08 frontend prerequisites are ready when authorized. Real Agent37 account/
instance/runtime access and a deployed agent_context.json URL still require
verification; no genuine fetch/briefing or platform readiness is claimed here.
No A08 implementation started. Handoff unchanged: schema 1.0.0;
fixture-layout-v1; synthetic-layout-six-wells; artifact_kind=fixture; not_run.
Commit: this A07 commit; final SHA reported after creation.

## A06 handoff - 2026-10-24 IST

Phase: A06 implemented; required acceptance checks PASS on feature/person-a.
Read completely: AGENTS.md, README_FIRST.md, MASTER_PLAN.md,
docs/COMMON_DECISIONS.md, this status, prompts/A06.md, contracts/README.md,
relevant schemas/fixtures, existing frontend components/tests and model config.
A07 read only to preserve its boundary. No contracts, B-owned files, dependency
manifests/locks or public fixture files changed. No A07-A10 implementation.

Files changed and resulting behavior:
- frontend/src/data/outage.ts: pure shared workspace reducer for selection and
  sensor-available / simulated-outage / reveal. Only holdout roles accept demo
  actions; Reveal requires prior outage. Well and method changes atomically
  reset the mode. Reset preserves the current well/method and clears chart
  overlays, tooltip state and revealed truth, including repeated resets.
- frontend/src/OutageControls.tsx: heldout-only native buttons, live mode status,
  exact displayed date range and historical/fixture explanation. Simulate outage
  conceals the full displayed export period; no invented outage timestamps or
  measurements. Null readings remain missing on reveal. Fixture text explicitly
  says no model was trained; clicks neither train nor execute a model.
- frontend/src/WellWorkspace.tsx: one reducer drives list, map, details and chart;
  chart epoch remount resets overlay preferences and cached tooltip state on
  mode/selection/reset changes. Stable map callback retained.
- frontend/src/App.tsx: workspace keyed by validated batch metadata so dataset/
  run changes reset selection and reveal state. Loading/errors unmount it.
- frontend/src/data/history.ts and frontend/src/HistoryChart.tsx: holdout truth
  only enters chart payload/domain, tooltip and table in explicit reveal mode.
  Revealed withheld readings have a distinct legend/tooltip/table heading.
  Missing truth or reconstruction yields Missing/unavailable notices; no method
  substitution, gap filling, error calculation or accuracy invention.
- frontend/src/styles.css: wrapped demo controls and disabled-button styling.
- frontend/checks/outage.test.mjs: 13 new state/privacy/edge-case tests.
- frontend/checks/browser.mjs: desktop/mobile outage interactions, keyboard,
  privacy, reset and new-batch tests alongside all previous regressions.
- docs/STATUS_A.md: this evidence/handoff.

Documented interpretation: A06 names an initial sensor-available state but does
not require showing held-out truth in it. To satisfy the user's explicit
before-reveal privacy requirement, this is a historical setup state with truth
still hidden. Estimates remain inspectable as in A05. Reveal is gated on outage.
A06 requires reset on well change; resetting on method change is an additional
conservative privacy choice. No conflict required a contract or scope change.
The outage uses the exported date range, not a fabricated missing-data interval.

Actual verification (Node v24.22.1, frontend commands from frontend/):
- `node --test --test-reporter=spec checks/batch.test.mjs checks/selection.test.mjs checks/coordinates.test.mjs checks/history.test.mjs checks/outage.test.mjs`:
  PASS 93 tests, 0 failures, 0 skipped (80 regressions plus 13 A06). Covers
  transition ordering, repeated cycles, invalid/nonholdout roles, same-selection
  stability, selection/reset privacy, all six heldout/method combinations,
  payload invariance to changed hidden truth, null/incomplete observations,
  unavailable estimates, no batch mutation and fresh dataset initialization.
- `npm run build`: PASS TypeScript/Vite; 676 modules; 19.17 kB CSS,
  897.85 kB JS (264.00 kB gzip JS). Existing non-failing >500 kB chunk warning
  remains; no warning suppression or dependency changes.
- `.\.venv\Scripts\python.exe scripts/validate_exports.py frontend/public/data`
  from root: PASS unchanged schema/semantic fixture validation. Not evidence of
  model training, scientific accuracy or leakage correctness in B's pipeline.
- Production preview via `npm run preview -- --host 127.0.0.1 --port 4173 --strictPort`;
  `node checks/browser.mjs`: full suite PASS, including A02-A05 regressions.
  A06 runs 24 outage/reveal/reset cycles across both heldout wells, all methods
  and 1280px/390px layouts. Every revealed table value matches the export,
  including nulls as Missing; hidden states have no observation path/column or
  stale tooltip. Buttons/selection issue no new data fetches. Well/method changes
  before/after reveal reset correctly. Enter activates outage; tooltips exclude
  truth in outage and show explicitly labelled withheld readings after reveal.
  All visible/train_masked wells have no demo controls. Unavailable predictions,
  all-null truth and a newly identified batch remain safe. No browser exceptions.
- Development via `npm run dev -- --host 127.0.0.1 --port 5173 --strictPort`;
  `$env:ALTER_EGO_CHECK_ORIGIN='http://127.0.0.1:5173'; node checks/browser.mjs`:
  full suite PASS, including the same 24 cycles, React StrictMode and actual
  Fast Refresh source edit/restoration. One working map remains. 74 canceled
  CDP interceptions during cleanup were counted separately; zero uncaught page
  exceptions. All map tiles intercepted locally; no public tile downloads.
  Browser runs used approved execution outside the sandbox as in earlier phases.
- Mobile screenshot captured to Windows TEMP/alter-ego-a06-mobile.png and
  visually reviewed: readable status/explanation and wrapped native controls.
  Screenshot is not staged. No horizontal overflow on desktop/mobile.
- Source review: one state source, atomic transitions (no effect-based delayed
  hiding), remount clears comparisons/tooltips, role restriction, preserved nulls,
  escaped data and retained fixture/synthetic/prototype labels. Results still
  shows export notes; A07's priorities/actual-result work is not implemented.
- Git scope/staged review: only A-owned frontend source/checks and this note;
  no generated build files, secrets or unrelated changes. `git diff --check`
  and `git diff --cached --check`: PASS before commit.

Remaining: no known A06 blocker. Bundle-size warning is non-blocking. Full
screen-reader certification, public tile availability and actual B model export
integration remain PENDING, as do earlier unverified account/shared facts.
Fixture reveal demonstrates software behavior, not measured field accuracy.

A07 is ready when authorized, using the validated fixture with not_run metrics.
Handoff unchanged: schema 1.0.0; fixture-layout-v1; synthetic-layout-six-wells;
artifact_kind=fixture. Commit: this A06 commit, final SHA reported after creation.
No push, merge or deployment. Run locally with `cd frontend` then
`npm run dev -- --host 127.0.0.1 --port 5173 --strictPort`.

## A05 handoff - 2026-10-24 IST

Phase: A05 implemented and required acceptance checks PASS on feature/person-a.
Read completely: AGENTS.md, README_FIRST.md, MASTER_PLAN.md,
docs/COMMON_DECISIONS.md, this status, prompts/A05.md, contracts/README.md,
all four JSON schemas and fixtures, relevant frontend source/checks, plus
ml/configs/prototype.yaml. A06 read only to preserve the phase boundary.
No contracts, Person B files, dependency manifests/locks or public data changed.

Files changed:
- frontend/src/HistoryChart.tsx: Recharts line chart from the validated batch;
  selected reconstruction, optional explicitly labelled IDW comparison and
  observed-reading overlays, legend, date/value tooltip and accessible data
  table. Units m below ground; positive depth direction explained; reversed
  vertical axis displays greater depth downward. Linear paths, no animations,
  connectNulls=false, and separate styles distinguish series without gap filling.
  Table/tooltip mark null as Missing. Empty/all-null/unavailable selections show
  helpful states without substituting another method. Invalid selections clear
  the chart; existing App loading/export-error states keep chart unmounted.
- frontend/src/data/history.ts: date/index-aligned chart projection; timestamps
  derive only from exported dates. Nulls/zero preserved. Missing calendar dates
  break paths using a null separator at the next supplied timestamp, without
  inventing readings or dates. Only actual export rows enter the data table.
  Held-out observations are excluded before generating chart payload, domain,
  tooltip and table, even when observation-overlay preference is enabled.
- frontend/src/WellWorkspace.tsx: passes the existing single well/method state
  directly to the chart; data is derived each render. Chart remount key clears
  stale tooltips when selected well/method or visible overlays change.
- frontend/src/App.tsx: unloaded chart placeholder only; loaded chart is inside
  the shared selection workspace.
- frontend/src/styles.css: full-width responsive chart, wrapped overlay controls,
  readable tooltip and scrollable accessible table.
- frontend/checks/history.test.mjs: 26 new projection/privacy/edge-case tests.
- frontend/checks/browser.mjs: A05 chart interactions, path/tooltip/overlay tests,
  screenshots and earlier-phase regressions. Sets explicit desktop dimensions
  for hover tests. Map initialization-failure injection now targets map observer
  attachment only, preserving the chart's independent ResizeObserver.
- docs/STATUS_A.md: this verified evidence and handoff.

Actual verification (Node v24.22.1; frontend commands from frontend/):
- `node --test checks/batch.test.mjs checks/selection.test.mjs checks/coordinates.test.mjs checks/history.test.mjs`:
  PASS 80 tests, 0 failures (54 regressions + 26 A05). Covers all 18 well/method
  date/value projections, mutation resistance, holdout truth exclusion, overlay
  exclusion, null runs, zeros, omitted dates, unavailable predictions with/without
  explicit IDW overlay, invalid selection, empty/incomplete arrays and one-date
  data. Incomplete arrays are also rejected upstream by existing loader tests.
- `npm run build`: PASS TypeScript/Vite; 674 modules; 18.96 kB CSS and
  894.87 kB JS (263.18 kB gzip JS). Existing non-failing >500 kB chunk warning
  persists after adding Recharts. No warning suppression or dependency changes.
- `.\.venv\Scripts\python.exe scripts/validate_exports.py frontend/public/data`
  from root: PASS schemas/semantic consistency; not model accuracy validation.
- `npm run preview -- --host 127.0.0.1 --port 4173 --strictPort` followed by
  `node checks/browser.mjs`: final production suite PASS. Chart/table dates and
  values match all 18 well/method combinations. Observed and IDW overlays work;
  actual SVG paths split at null runs and omitted calendar dates. Tooltip shows
  full export date and Missing for null observations. Held-out wells have no
  observation line, tooltip reading or table column. All-null selected series
  has an empty state; explicit IDW comparison remains distinctly labelled.
  Includes A02-A04 validation, selection, keyboard, map-failure/retry and cleanup
  regressions; zero uncaught browser runtime exceptions.
- `npm run dev -- --host 127.0.0.1 --port 5173 --strictPort` then
  `$env:ALTER_EGO_CHECK_ORIGIN='http://127.0.0.1:5173'; node checks/browser.mjs`:
  final full suite PASS, including StrictMode and actual Fast Refresh source
  edit/restoration. 58 canceled CDP interceptions during cleanup were counted
  separately; zero uncaught page exceptions. All tile requests intercepted
  locally. Headless Edge ran with approved access outside the sandbox.
- Browser checks at 390px/1280px: PASS no horizontal overflow and measurable
  chart width. Desktop, mobile panel and full mobile plot PNGs captured to
  Windows TEMP as alter-ego-a05-1280.png, alter-ego-a05-390.png and
  alter-ego-a05-390-plot.png; visually reviewed readable axes, wrapping legend,
  controls and distinct series. These temporary screenshots are not staged.
- Initial visualization attempts exposed test assumptions: an empty SVG element
  can have no geometry, dot DOM is optional, and the default headless viewport
  placed hover off-screen. Tests now inspect visible path geometry, hover its
  first screen-coordinate point and set an explicit viewport. Final checks above
  pass; no failing acceptance check is waived. An initial fixture-read command
  had a parenthesis typo and was corrected before implementation.
- React/source review: no duplicated well/method state, escaped data labels,
  native checkbox controls, semantic table, no hidden truth in chart inputs,
  no scientific recalculation, no fabricated measurements or accuracy metrics.
- Git review: A-owned frontend source/checks and this status only; generated
  files/secrets excluded. `git diff --check` and staged diff check PASS.

Remaining: no known A05 blocker. Bundle-size warning is non-blocking; full
screen-reader certification, live public tiles and Person B's actual export
integration remain PENDING. Earlier unverified shared/account items remain
PENDING. Fixture curves are illustrative; metric statuses remain not_run.

A06 can safely begin when authorized. A05 conservatively withholds all holdout
observations; no sensor-available/outage/reveal state machine or reveal control
has been implemented. A06 must explicitly authorize held-out observation
visibility after reveal while keeping outage chart inputs sanitized. No A06-A10
implementation performed here.

Handoff: schema 1.0.0; fixture-layout-v1; synthetic-layout-six-wells;
artifact_kind=fixture. Commit: this A05 commit; SHA reported after creation.
No push, merge or deployment. To run: `cd frontend` then
`npm run dev -- --host 127.0.0.1 --port 5173 --strictPort`.

## A04 handoff - 2026-10-24 IST

Phase: A04 implemented and acceptance checks PASS on feature/person-a.
Read AGENTS.md, README_FIRST.md, MASTER_PLAN.md, this status, prompts/A04.md,
contracts/README.md, relevant schema/fixture conventions and frontend source/
checks, plus ml/configs/prototype.yaml. A05 read only to preserve its boundary.
No shared contracts, B-owned files, dependencies or public fixtures changed.

Changed files:
- frontend/src/WellMap.tsx: direct Leaflet component and bundled Leaflet CSS;
  circle markers, bounds fit with capped initial zoom, keyboard selection,
  escaped tooltip text, selected-marker styling and visible OSM attribution.
  Finite/range-checked coordinates only; no coordinates are invented. Duplicate
  locations are permitted; the list keeps overlapping wells independently usable.
  ResizeObserver invalidates map size for responsive layout. Cleanup removes
  map, observer, marker keyboard listeners, tile events and timeout. A stable
  callback prevents map recreation when well or method selection changes.
  Tile failures or a 10-second loading timeout show an explicit background-map
  fallback. Circles/list/details stay usable; Retry redraws tiles without losing
  selection. Initialization errors clean up and leave list/details available.
- frontend/src/data/coordinates.ts and checks/coordinates.test.mjs: defensive
  coordinate guard and boundary/zero/missing/nonfinite/out-of-range coverage.
- frontend/src/WellWorkspace.tsx: map shares the A03 well selection directly;
  marker/list selection preserves method and updates the same detail panel.
- frontend/src/App.tsx: map placeholder only while no validated batch exists.
- frontend/src/styles.css: responsive full-width map, fixed bounded height,
  visible attribution, selected/focused SVG circle styles.
- frontend/checks/browser.mjs: A04 interaction/failure/refresh checks in addition
  to A02/A03 regressions. All tile requests fulfilled/failed/held locally via
  CDP; no automated public tile downloads. Optional ALTER_EGO_CHECK_ORIGIN
  selects the dev server for actual Fast Refresh verification.
- docs/STATUS_A.md: this evidence and handoff.

Actual verification (frontend commands from frontend/; Node v24.22.1):
- `npm run build`: PASS TypeScript and Vite, 99 modules. Output includes
  18.21 kB CSS and 523.26 kB JS (156.24 kB gzip JS). Non-failing Vite warning:
  the JS chunk exceeds 500 kB after adding Leaflet. No dependency upgrades or
  chunk-limit suppression used. This remains a possible later optimization.
- `node --test checks/batch.test.mjs checks/selection.test.mjs checks/coordinates.test.mjs`:
  PASS 54 tests, 0 failures; includes all 52 existing regressions and 2 coordinate
  tests covering ordinary/zero/boundary/duplicate and invalid coordinates.
- `.\.venv\Scripts\python.exe scripts/validate_exports.py frontend/public/data`
  from root: PASS existing schema/semantic checker. Not scientific validation.
- Production preview: `npm run preview -- --host 127.0.0.1 --port 4173 --strictPort`.
  `node checks/browser.mjs`: final full run PASS. Checks all 18 well/method pairs,
  all six selectable circle markers, list/map/detail synchronization, keyboard
  marker activation, one selected marker, persistent method and map instance,
  OSM attribution, null/unavailable methods, invalid/missing/empty/mixed-batch
  states and retry. Invalid latitude remains rejected by the unchanged loader.
  Tile-error and stalled-tile simulations show fallback; selection remains usable
  and tile retry recovers. Coincident coordinates do not crash. Initialization
  failure cleans up the map; list/details work and next mount recovers. Repeated
  reloads leave one map pane. 390px/1280px layouts have no horizontal overflow.
  No uncaught browser runtime exceptions.
- Development server: `npm run dev -- --host 127.0.0.1 --port 5173 --strictPort`.
  `$env:ALTER_EGO_CHECK_ORIGIN='http://127.0.0.1:5173'; node checks/browser.mjs`:
  final full run PASS, including React StrictMode and an actual temporary
  WellMap source edit/restoration triggering Fast Refresh. One working map and
  six markers remain after refresh. Source restored exactly by the check.
  Initial dev check incorrectly counted canceled CDP interception IDs as page
  exceptions during StrictMode cleanup; harness now distinguishes that specific
  cancellation from real Runtime exceptions. Final dev run recorded 43 canceled
  interceptions and zero uncaught page exceptions. Browser runs used approved
  execution outside the sandbox, as in preceding phases.
- React/source review: one well selection source, stable callback, lifecycle
  cleanup, local CSS/assets, native list fallback, no injected data HTML,
  no computed scientific flags/results and fixture warnings preserved.
- Git review/checks: only A-owned frontend source/checks and this note;
  generated output and secrets not staged. `git diff --check` and staged diff
  check PASS before commit. No push, merge or deployment.

OSM policy consulted: https://operations.osmfoundation.org/policies/tiles/ .
Uses the prescribed HTTPS URL and visible attribution with normal browser
caching/referrer behavior. No prefetch/offline tile download feature added.

Remaining issues: no known A04 blocker. Live public-tile availability and full
visual/screen-reader review remain PENDING; tests use locally intercepted tiles.
The >500 kB chunk warning is non-blocking. The history chart is still the A01
placeholder and remains present during tile failure; no A05 chart is claimed.
Real B export and previously unverified account/shared items remain PENDING.

A05 is ready when authorized; no chart, outage/reveal or agent implementation
started. Handoff unchanged: schema 1.0.0; fixture-layout-v1;
synthetic-layout-six-wells; artifact_kind=fixture; metrics not_run.
Commit: this A04 commit; final SHA reported after creation.

## A03 handoff - 2026-10-24 IST

Phase: A03 implemented and acceptance checks PASS on feature/person-a.
Earlier entries are historical. User confirms A02 synchronized with GitHub.
Read AGENTS.md, README_FIRST.md, MASTER_PLAN.md, COMMON_DECISIONS.md,
this status, prompts/A03.md, relevant schemas/fixtures, contracts/README.md,
ml/configs/prototype.yaml and the existing frontend/checks. Read A04 only
to preserve the phase boundary. No B-owned files or shared contracts changed.

Changed files:
- frontend/src/WellWorkspace.tsx: selectable well list, native labelled method
  selector and detail panel. One {wellId, method} state drives pressed state,
  selected metadata, evaluation role, method/status and exported summary.
  Selection preserves the method when changing wells. Initial selection uses
  export order/default method, with no hardcoded well identity.
- frontend/src/data/selection.ts: pure selection resolution, availability and
  nullable depth formatting. Details derive directly each render, with no
  cached summary or selection-sync effects. Invalid selections clear details.
  Unavailable methods stay inspectable and show Unknown without substitution.
  Fixture series remain inspectable despite not_run evaluation, explicitly
  labelled illustrative. Nonfixture failed/not_run or all-null series are
  unavailable. Partial series retain exported null/unknown summaries.
- frontend/src/App.tsx: mounts selection UI only for the fully validated batch;
  loading/error unmount it, preserving A02's complete-batch boundary.
- frontend/src/styles.css: responsive list/details grid, pressed-button styles,
  native select styling; existing focus and skip-link styles retained.
- frontend/checks/selection.test.mjs: 25 selection/edge-case checks.
- frontend/checks/browser.mjs: interaction checks plus existing A02 regressions;
  null/unavailable responses are intercepted in memory only, never published.
- docs/STATUS_A.md: evidence and handoff.

Actual checks (Node v24.22.1; frontend commands run from frontend/):
- `node --test checks/batch.test.mjs checks/selection.test.mjs`: PASS, 52 tests,
  0 failures (27 A02 regressions + 25 A03). Covers every well/method pair,
  invalid IDs/methods, empty well data, null/zero/negative values, partial/all-null
  series and nonfixture failed/not_run availability. Source batch not mutated.
- `npm run build`: PASS TypeScript and Vite; 95 modules; 2.80 kB CSS and
  370.59 kB JS (111.68 kB gzip JS), plus dist/index.html.
- `.\.venv\Scripts\python.exe scripts/validate_exports.py frontend/public/data`
  from repository root: PASS. An unrelated initial Python version command was
  mistakenly run from frontend/ and could not find the root venv; corrected
  root validator command above succeeded. No environment changes were made.
- `npm run preview -- --host 127.0.0.1 --port 4173 --strictPort`: started.
- `node checks/browser.mjs`: final run PASS against production preview using
  installed headless Edge outside the sandbox. All 18 well/method combinations
  match exported metadata/summary fields, with exactly one pressed well.
  Keyboard Enter activates a well and preserves method; select has a label.
  Invalid-method injection clears details, valid selection recovers. Null and
  unavailable method responses show Unknown, and repeated switching updates
  values without stale data. A02 invalid/missing/empty/mixed-batch, retry and
  loading regressions pass. No horizontal overflow at 390px/1280px; no uncaught
  browser exceptions. Initial keyboard test omitted Enter's character in its
  CDP event; corrected the test event, then the complete run passed. No app
  change was needed for keyboard activation.
- React/accessibility source review: single selection source of truth, derived
  details, button aria-pressed, native select/label, polite selected-status text,
  semantic detail list, no unsafe HTML or scientific flag recalculation.
- Git review: manifest/lock, public fixture files, loader, contracts and B's
  areas unchanged; generated dist/node_modules ignored. No secrets or generated
  build output staged. `git diff --check` and staged check PASS before commit.

Remaining issues: no known A03 blocker. Full visual/screen-reader certification
and a real Person B export remain PENDING. Previous account/shared sign-offs
remain PENDING unless verified independently. Fixture results demonstrate UI
behavior only; no model training or real-world accuracy is claimed.

A04 is ready when authorized. Map/chart/outage/reveal/agent features have not
been implemented. Handoff: contract 1.0.0; fixture-layout-v1;
synthetic-layout-six-wells, artifact_kind=fixture, all metric statuses not_run.
To run: `cd frontend` then `npm run dev -- --host 127.0.0.1 --port 5173 --strictPort`.
Commit: this A03 commit; final SHA reported after creation. No push/merge/deploy.

## A02 handoff - 2026-10-24 IST

Phase: A02 implemented and acceptance checks PASS on feature/person-a.
Earlier A01/A00 entries below are historical. User confirms A01 was pushed and
the desktop screenshot reviewed. No push, merge or deployment performed here.

Read AGENTS.md, MASTER_PLAN.md, README_FIRST.md, docs/COMMON_DECISIONS.md,
this status, prompts/A02.md, all four contract schemas and fixtures,
contracts/README.md and ml/configs/prototype.yaml. A03 was inspected only to
preserve its boundary. No contracts or B-owned files were modified.

Changed files:
- frontend/public/data/{predictions,metrics,run_info,agent_context}.json:
  complete, byte-identical copy of contracts/fixtures, published together.
- frontend/src/data/models.ts: typed metadata, wells, summaries, metrics,
  run evidence and agent context for contract 1.0.0.
- frontend/src/data/loadBatch.ts: one four-file no-store loader; existing
  schemas imported directly with Ajv and date formats; no schema copies/drift.
  Validates every metadata field, ordered unique dates, final as-of date,
  unique well IDs, all observation/method series lengths, agent IDs/roles/
  summaries and metric status. No scientific flags or results recalculated.
- frontend/src/App.tsx and styles.css: loading, missing/empty and invalid
  states, helpful file/path errors and Retry; only fully validated batches
  become visible. Aborted/stale requests cannot publish state after cleanup.
  Loaded dataset/artifact type, caption, run/schema/dataset IDs, observation
  range, as-of date, generated UTC timestamp, well/date counts and units shown.
  Fixture and synthetic caveats are explicit; no hardcoded scientific results.
- frontend/tsconfig.json: permits explicit TS import extensions for Node checks.
- frontend/checks/batch.test.mjs: repeatable Node loader/contract acceptance tests.
- frontend/checks/browser.mjs: installed Windows Edge checks using native CDP;
  test response interception only, no application test routes or altered fixtures.
- docs/STATUS_A.md: this evidence/handoff.

Actual checks (Node v24.22.1; frontend commands from frontend/):
- `node --test checks/batch.test.mjs`: 27 tests PASS, 0 failures. Includes exact
  four-file copy, actual fixture dates 2024-08-01 through 2024-09-29, 6 wells,
  60 dates, null preservation, not_run metrics, schema/date errors, empty
  wells/dates, batch identity mismatches, misaligned series, duplicate IDs/dates,
  agent mismatch/truth-field rejection, Infinity, false metric values, fetch
  failures, 404, empty bodies, malformed JSON and abort behavior. An in-memory
  model_output/different-identity compatibility case passes; never published.
- `npm run build`: PASS; TypeScript and Vite, 93 modules; output includes
  dist/index.html, 1.98 kB CSS and 365.87 kB JS (110.44 kB gzip JS).
- `.\.venv\Scripts\python.exe scripts/validate_exports.py frontend/public/data`
  (from root): PASS schemas, metadata, dates, series, summaries, metric status.
  This is export consistency evidence, not scientific validation.
- `npm run preview -- --host 127.0.0.1 --port 4173 --strictPort`: started.
- `node checks/browser.mjs`: PASS production-browser rendering and metadata,
  malformed JSON, 404, empty body, empty-wells schema failure, mixed run ID,
  no partial/stale display on failure, successful retry, delayed loading state,
  390px/1280px no-horizontal-overflow checks and zero uncaught runtime exceptions.
  Initial sandboxed Edge runtime initialization timed out; approved execution
  outside the sandbox passed. Final run includes all cases and layout checks.
- React review: one load-state union, cleanup abort, no separate derived-state
  effect, escaped data strings, alert/status semantics and keyboard Retry.
- Git diff/staged review: only frontend sources, public-safe fixture batch,
  frontend acceptance checks and this note; no generated output or secrets.
  Existing dependency manifest/lock and contracts unchanged.
- `git diff --check` and `git diff --cached --check`: PASS before commit.

Remaining issues: no known A02 blocker. Browser checks establish rendering and
state behavior, not full visual/accessibility certification. Person B's actual
model export integration remains PENDING receipt of a complete export batch;
the loader uses the contract and does not depend on fixture IDs or counts.
Earlier unverified external-account/shared sign-offs remain PENDING.

A03 is ready when authorized; no selectable list/details/method controls, map,
chart, outage/reveal or agent integration implemented in A02. The shell areas
remain placeholders with accurate loaded-state text.

Handoff: contract 1.0.0; fixture-layout-v1; synthetic-layout-six-wells;
artifact_kind=fixture, dataset_kind=synthetic; all metric statuses not_run.
Commit: this A02 commit, SHA reported after creation. Do not push/merge/deploy.

## A01 handoff — 2026-10-24 IST

Phase: A01 implemented and acceptance checks PASS on feature/person-a.
The A00 record below is historical; its A01-not-started statements are superseded
by this entry. User reports the A00 commit has been pushed. Person B is working
independently on Ubuntu with Cursor; no B-owned files were edited.

Read all requested inputs: AGENTS.md, README_FIRST.md, MASTER_PLAN.md,
docs/COMMON_DECISIONS.md, this status, prompts/A01.md, frontend/package.json,
contracts/README.md, plus ml/configs/prototype.yaml. A01 is authoritative.

Changed files:
- frontend/index.html: HTML entry, page title, description and viewport.
- frontend/src/main.tsx: React root and StrictMode entry.
- frontend/src/App.tsx: historical prototype and planned synthetic fixture
  badges; explicit unloaded state; well-list, map, chart and results areas.
- frontend/src/styles.css: plain CSS, responsive grid, skip link and focus styles.
- frontend/tsconfig.json: strict TypeScript checking without emitted files.
- frontend/vite.config.ts: Vite with the installed React plugin.
- docs/STATUS_A.md: actual evidence and handoff.

No manifest/lock changes, data publishing/loading, JSON contract changes,
scientific calculations, model outputs, router, backend or later-phase features.

Checks actually run (frontend commands run from frontend/):
- `node --version`: v24.22.1.
- `npm ci`: exit 0, added 71 packages in 17s. No audit result was printed;
  no new zero-vulnerability claim is made.
- `npm run build`: exit 0; `tsc --noEmit` and Vite production build passed,
  16 modules transformed. Output: dist/index.html and bundled CSS/JS.
- `npm run dev -- --host 127.0.0.1 --port 5173 --strictPort`: Vite ready
  in 419 ms at the exact required address. PowerShell Invoke-WebRequest
  confirmed HTTP 200 for /, /src/main.tsx and /src/App.tsx.
- Installed Edge headless `--dump-dom --timeout=10000` against the dev URL:
  captured rendered React DOM with Alter Ego, historical/fixture badges and all
  four section headings. Initial sandboxed Edge crashed with GPU/access errors;
  approved isolated-profile execution produced the rendered DOM in a temporary
  file outside the repository. No interactive visual or console audit claimed.
- `npm run preview -- --host 127.0.0.1 --port 4173 --strictPort`: started;
  Invoke-WebRequest confirmed HTTP 200 from production preview.
- React source review: semantic landmarks, associated section headings, keyboard
  skip link and focus styling; no effects, state, external data requests or
  unused map/chart imports. Mobile layout uses one column at <=700px.
- `git diff -- frontend/package-lock.json frontend/package.json`: no changes.
- `git check-ignore frontend/dist/index.html frontend/node_modules/react/package.json`:
  both generated paths ignored. Staged paths/content reviewed before commit;
  source/config/status only, no generated files, environment files or secrets.
- `git diff --check` and `git diff --cached --check`: PASS before commit.

Remaining issues: no known A01 blocker. Interactive visual/mobile review remains
PENDING; server/DOM verification above passed. A00 teammate and external-account
items remain PENDING unless separately verified; they do not block the shell.

A02 is ready when authorized: copy/validate the four-file fixture batch and
implement its loader/types/errors. A02 was read only to establish the boundary;
no A02 implementation performed. Handoff: contract 1.0.0, fixture-layout-v1,
synthetic-layout-six-wells (not yet loaded/published by this shell).

To run locally: `cd frontend`, then
`npm run dev -- --host 127.0.0.1 --port 5173 --strictPort`.
Commit: this A01 commit; final SHA reported after creation. No push/merge/deploy.

## Historical A00 record

Phase: A00 technical readiness verified; shared/account acceptance PENDING
Checked: 2026-10-24 (IST). Person A, Windows, VS Code/Codex.
Changed files: docs/STATUS_A.md only. No A01 implementation started.

## Instructions and scope

Read prompts/A00.md, AGENTS.md, MASTER_PLAN.md, contracts/README.md,
ml/configs/prototype.yaml and both status notes. Read prompts/A01.md solely
to assess its entry requirements. Inspected frontend/package.json and fixture
run metadata. Keep the frozen architecture, contract 1.0.0 and ownership rules.
The user's explicit branch instruction overrides the plan's feature/product
name for this session: remain on feature/person-a; no branch rename needed.

## Verified technical results

- `node --version`: v24.22.1.
- `npm --version`: 11.21.1.
- `git --version`: 2.55.0.windows.3.
- `.\.venv\Scripts\python.exe --version`: Python 3.11.9; project venv runs.
- `.\.venv\Scripts\python.exe -m pip show jsonschema`: 4.25.1 in project venv.
- `.\.venv\Scripts\python.exe scripts/validate_exports.py`: PASS for schemas,
  metadata, dates, series, summaries and metric status. This does not certify
  training, leakage prevention, physics or accuracy.
- `npm ls --depth=0 --prefix frontend`: exit 0; all 13 direct dependencies
  match the exact manifest pins. A accepts the existing manifest for A01.
- `npm ci`: user reports 71 packages and 0 vulnerabilities; not rerun in this
  finalization. A fresh installation/audit outcome is PENDING independent rerun.
- `git status --short --branch`: clean before the status edit, on
  feature/person-a tracking origin/feature/person-a.
- `git branch -avv` and `git remote -v`: local main exists; origin is configured.
- `git rev-parse HEAD`: e756549b7de11368f9af54e7f123f9a412c79f78.
- `git ls-remote origin refs/heads/feature/person-a refs/heads/main`: successful
  after approved escalation for a sandbox-blocked network connection. Remote
  feature/person-a matches the above input revision. Remote main is
  8cc5fd7435f706cf407ae19fba4e669d78408240; local main is still e756549.
  No fetch, merge or push performed. Main integration remains separate work.
- Codex local read/command execution works in this session. This verifies usable
  access, not a particular subscription, remaining quota or future entitlement.
- Render connected tool `list_workspaces`: succeeded with one accessible
  workspace. Account access is verified; no resources created or compute started.

## External and teammate prerequisites

- PENDING: Person B confirms reading the plan, role/ownership agreement,
  contract 1.0.0 acceptance and dependency manifest acceptance. Existing written
  roles are available; they do not prove mutual sign-off. ml/STATUS_B.md still
  says not started. No cross-owner files changed.
- PENDING: Person B independently demonstrates GitHub repository access and
  synchronization, and confirms their branch/workstation setup. A's successful
  remote read does not establish B's access or GitHub write permission.
- PENDING: Agent37 login, supported hosted runtime, actual instance and fresh
  JSON fetch capability, authentication/credits and required account facts.
  No accessible Agent37 account evidence was supplied; no endpoints invented.
- PENDING: Render repository authorization and static-site runtime/deployment
  compatibility. Workspace listing alone does not verify deployment readiness.
- PENDING (B-owned): Nodus organization access, invitations, activated credit
  balance, cost review and bounded smoke job; B's local GPU/environment checks.
  These are not prerequisites for A01 fixture UI work. No paid compute started.
- PENDING: submission/account email alignment and current organizer requirements.
  Private account details are intentionally omitted from this public status.

## Acceptance and next handoff

A00 is recorded honestly as technically ready for A's local fixture work, with
shared acceptance still PENDING the confirmations above. It is not a declaration
of complete sponsor readiness or a completed app/model.

A01 may safely start when requested, using the validated six-well synthetic
fixture. Keep artifact_kind=fixture and dataset labels visible; illustrative
metrics remain not_run and must never be presented as experimental results.
No external account or model training is required for the A01 shell. Do not
scaffold over the pinned manifest. A01 build/dev acceptance remains PENDING
until implementation; no build or server success is claimed here.

Commands for the next authorized phase (not executed in A00):

```powershell
cd frontend
npm ci
npm run build
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Handoff revision: contract 1.0.0; fixture-layout-v1;
dataset synthetic-layout-six-wells; input code e756549b7de11368f9af54e7f123f9a412c79f78.
Status commit: the commit containing this note (SHA reported after committing).
Commit locally to feature/person-a; do not push or merge. The new status commit
will intentionally leave the local branch ahead of its remote.
