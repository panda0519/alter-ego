# Alter Ego: final two-person build agreement

Prepared 21 October 2026. All event times in this document are IST.
Person A: Codex, product/integration. Person B: Cursor, data/model/GPU.

## 1. Decision and return on effort

Keep the submitted technical idea: GCN + LSTM with a small simplified water-balance loss.
Build one convincing historical missing-sensor demonstration around it. Spend effort first
on usable data and an end-to-end pipeline, then on a small model, then physics, then presentation.
Return on effort means less wasted build time and a stronger demonstrable entry. It is not
a numerical prediction of prize probability or a guaranteed financial return.

The best sponsor fit is meaningful Nodus training plus an Agent37-hosted inspection assistant.
Do not add every sponsor. Nodus podium cash is INR 50,000 / 30,000 / 20,000. Agent37 podium cash
is INR 10,000 / 7,500 / 5,000; category cash is INR 2,500. Nodus and Agent37 are separate;
Agent37 podium/category awards cannot both be won by the same team. Qualified Agent37 support
is conditional, up to INR 1,000 plus USD 10 credits per project. Credits are not cash.
Judging weights are Build 40%, Problem 20%, Ingenuity 20%, Potential 20%.
These facts were checked against the official event sources listed in SOURCES.md; verify updates
at check-in. Nodus's detailed challenge rubric may still be clarified by organisers.

## 2. Frozen product

Audience: a water-resource officer deciding which unavailable sensors need a field check.
One sentence: 'When a groundwater sensor is unavailable, Alter Ego reconstructs its readings
from nearby wells and weather, then produces an evidence-based inspection briefing.'

Required demo:
1. Open the dashboard. Show 'Historical prototype', dataset type and observation dates.
2. Choose a final held-out well from a predetermined demo set.
3. Click 'Simulate outage'. Conceal measured readings and show precomputed estimates.
4. Click 'Reveal observations'. Overlay withheld observations and show test errors.
5. Inspect a priority list with explicit prototype rules and supporting changes.
6. Open the Agent37 instance in another tab and request a grounded briefing.

The outage button changes presentation only. The displayed model predictions must have been
computed with that well's readings excluded. Do not claim the click trains a model or simulates
an aquifer. Only held-out wells get the outage/reveal demo in version 1. Other wells remain
viewable, labelled with their evaluation role.

Frozen stack: React + TypeScript + Vite, plain CSS, direct Leaflet map, Recharts plots;
static JSON data; Python/PyTorch training; Render Static Site; Agent37-hosted assistant in its
native interface. No custom API, database, login or embedded paid-model endpoint.
No nationwide map, forecast, live sensor feed, mobile app, phone bot or scheduler.

## 3. Laptop setup and coding tools

Assumption: personal Windows laptops; use PowerShell. Linux/macOS may use equivalent Python
commands. Do not use the earlier shared-college-PC workflow for installing or saving this pack.
If currently on a shared PC, do these steps later on personal machines.

Both: Git, Chrome/Edge, Node.js 24.22.1 LTS (selected from the official download page during
this check), individual GitHub access to one repository. A minimum of 8 GB system RAM is a
practical starting point; B benefits from 16 GB and roughly 15 GB free disk for Python/GPU packages.
These are practical recommendations, not tested hardware requirements. No GPU is needed on A.

A: VS Code + official Codex extension, sign in using your own available ChatGPT/Codex access.
Open the project root, use local execution, normal workspace approval controls. Start with the
default coding model supplied by your plan. If reasoning is selectable: medium for UI,
high for schema/integration debugging. Avoid paying for a new tool solely for this project.
Do not run another editing agent against the same checkout at the same time.

B: Cursor, open project root, Agent mode for implementation. Use the coding model already
included in your plan; Auto is a reasonable initial choice. For leakage/physics review use a
strong reasoning model if available without unexpected charges. Exact model menus and quotas
are account-dependent, so the plan deliberately does not invent a model entitlement.
Use the same AGENTS.md. A separate .cursorrules file is unnecessary.

Both tools: explicitly read AGENTS.md + MASTER_PLAN.md + contracts/README.md at the beginning
of a new conversation. Submit one prompts/A_*.md or prompts/B_*.md at a time. Include actual
error output in follow-ups. Keep a successful phase commit before a larger change.

Versions: frontend/package.json contains exact direct dependency pins. A resolved package-lock.json
is included. These are installation files, not a completed frontend. A runs npm ci with this lock,
then verifies the actual app build after A01. Both keep the same lock. Do not upgrade during the event.
Python's selected Windows installer baseline is 3.11.9; do not replace an existing system
Python or reuse the earlier Jarvis Python 3.13 environment. Create this project's .venv.
ml/requirements-common.txt pins the direct Python dependencies. Freeze the complete working
environment separately after verification. GPU and CPU environments have separate locks.

### A: commands after cloning and copying this pack into the repository root
```powershell
node --version
npm --version
git --version
cd frontend
npm ci
```
At this point execute prompt A01 to create the missing application files. Then:
```powershell
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
npm run build
npm run preview -- --host 127.0.0.1 --port 4173 --strictPort
```
Run dev/preview in separate terminal sessions as needed; they are long-running commands.
Do not run create-vite over this already-populated frontend directory.

### B: commands after cloning
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r ml/requirements-common.txt
.\.venv\Scripts\python.exe -m pip install torch==2.8.0 --index-url https://download.pytorch.org/whl/cu128
nvidia-smi
.\.venv\Scripts\python.exe -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
```
Use a supported NVIDIA driver and verify a real GPU tensor operation in B00. A CUDA wheel
does not guarantee that an unknown RTX/driver combination will work. Do not install the
full CUDA toolkit for this plain PyTorch project. If the GPU check fails, make progress with
the CPU wheel in a fresh CPU venv and resolve GPU access independently:
```powershell
py -3.11 -m venv .venv-cpu
.\.venv-cpu\Scripts\python.exe -m pip install -r ml/requirements-common.txt
.\.venv-cpu\Scripts\python.exe -m pip install torch==2.8.0 --index-url https://download.pytorch.org/whl/cpu
```
PyTorch's official previous-versions page documents both wheel variants. The small network
also runs on CPU, with runtime measured by your smoke test rather than promised here.

### Accounts
- Each teammate uses their own GitHub and coding-tool login. Do not share passwords.
- A owns Render and the Agent37 instance. Add a collaborator if the service supports it.
- B owns Nodus setup; invite A through the organisation/project controls where needed.
- Use the registered application email for submissions and identify a different platform
  email explicitly where the event form requests it.
- Agent37 web UI is the required channel. Phone channels/scheduled jobs may need paid plans.
- Do not assume a ChatGPT subscription pays for third-party API usage. Use the authentication
  or credits actually supported by the chosen Agent37 agent and verify it before the event.

## 4. Files and ownership

| Area | Owner | Rule |
|---|---|---|
| frontend/ | A | All application code, UI, package lock, data publishing |
| agent/ | A | Agent instructions, fetch/briefing integration |
| docs/, presentation/ | A | Setup docs, slides, submission and demo |
| contracts/ | A, with B review | No breaking field changes without both agreeing |
| ml/, tests/ | B | Data/model/training/export code and tests |
| data/, runs/ | B | Local raw files, arrays and checkpoints; not ordinary Git payloads |
| artifacts/exports/<run_id>/ | B | Small public-safe export batches, committed for handoff |
| Root configuration | A | Coordinate proposed changes from B |

Initialise main once; create feature/product for A and feature/model for B. A merges passing
phase commits. Use merge-based synchronisation, no force-push or destructive resets. Before
integration commit local work; merge the latest main into the feature branch. After a merge,
each tool rereads the contracts and the other person's status note.

Handoffs: B writes a complete export batch under artifacts/exports/<run_id>/, never partially
updates the deployed data. A validates it and publishes all four files together to
frontend/public/data/. All four share dataset_id, run_id and schema_version. Only A writes
frontend/public/data/. B never waits for UI to continue model work.

## 5. Data decision, downloads and preprocessing

Target: 40 wells, one compact region, 2023-01-01 through 2024-12-31 (731 days).
Accept roughly 30-60 wells and an overlapping daily year or more if the target is unavailable.
This is a prototype target, not a claim that a suitable Indian subset is already downloaded.
Choose the region based on coverage and reasonably comparable well/aquifer metadata. Do not
select a state simply to match the venue.

1. Try https://indiawris.gov.in/wris/#/timeseriesdata for telemetric/DWLR groundwater records.
2. Alternative listing: see SOURCES.md. Its CSV is around 1.5 GiB according to metadata.
   Download once only if permitted, process in pandas chunks, filter the subset and preserve
   source notes. The listing does not state a licence; do not assume redistribution rights.
3. Confirm Data Value / Data Type Description and units. Borehole well_depth is not necessarily
   the changing water reading. Do not infer a sign conversion from seasonal appearance.
4. Save observations as station_id, latitude, longitude, date, depth_m below ground.
   Preserve unmodified raw inputs locally and log conversions.
5. NASA POWER daily request: PRECTOTCORR,T2M_MAX,T2M_MIN; community=AG; format=JSON;
   start=20230101; end=20241231; time-standard=LST; coordinates for representative cells.
   Use matching dates if the groundwater period changes. Inspect returned metadata and units.
6. Cache requests and reuse the source-grid data. POWER weather is coarse; do not assume
   0.25-degree weather or independent rainfall at every well.
7. Derive Hargreaves ET0 using latitude/day of year and Tmax/Tmin. Ra in the equation must
   be equivalent evaporation in mm/day; multiply Ra in MJ/m2/day by 0.408 first. ET0 is a
   reference estimate, not measured groundwater evapotranspiration. Preserve its assumptions.

Budget two focused hours for the initial real-data access/coverage check. If blocked, switch
development to synthetic data and continue the real subset independently. If only quarterly
manual readings exist, do not fabricate daily labels. Remain explicit about a synthetic daily
prototype or revise the temporal scope by shared agreement.

Real-data cleaning: standardise time zones/daily aggregation; take a documented daily median
if multiple valid readings exist. Sort and deduplicate. Verify coordinates and source-specific
validity codes. Flag implausible readings for review; do not impose an arbitrary universal
0-100 m range or delete all flat histories as sensor failures. No interpolation of training
targets. For visible-well input lag use the immediately previous day only; absent means mask=0
and standardised lag=0. No future-looking gap filling or rolling filters.

Choose wells by training-period coverage masks (recommended >=70%) and metadata; freeze the
cohort and grouping before inspecting validation/test outcomes. Report final test missingness,
do not choose the cohort by which held-out readings make the model look best.

Synthetic fallback: 40 fictional wells x 731 days, seed 42; seasonal rain/groundwater,
heterogeneous offsets and pumping, delayed responses, moderate correlated spatial signals,
noise and missing observations. Do not make evaluation a copy of the regulariser's exact
equation. Label all synthetic results. They demonstrate software behaviour, not field validity.

## 6. Model configuration: exact first implementation

Use ml/configs/prototype.yaml. Dense graph only; no graph-library installation.
- Graph: k=6 neighbours (min(k,N-1)); haversine distances; Gaussian weights using median
  positive neighbour distance; symmetric union graph, self loops, symmetric degree normalisation.
  Handle duplicate coordinates; row order must match station IDs in every array.
- Window: 30 days, stride 1. Eight features in the fixed order in YAML.
- GCN: one linear graph-convolution layer, 8 -> 32, ReLU, external dropout 0.1.
- LSTM: one unidirectional layer, hidden=32, batch_first=True. PyTorch internal LSTM dropout=0
  because it is one layer. Apply the configured dropout outside the LSTM.
- Head: linear 32 -> 1 at every day/well. Output shape B x 30 x N.
- Reshape GCN output B x T x N x 32 into (B*N) x T x 32 for LSTM, then restore axes carefully.
- Optimiser AdamW, lr=0.001, weight_decay=0.0001, batch=16, epochs<=40, gradient norm<=1.
- Early stopping patience=8, using validation MAE at training-masked wells.
- One well split and seed 42. No broad sweeps or extra seeds until the complete demo works.
- Three neural runs with lambda target 0, 0.1 and 1.0; same split and initial seed.

Well split for 40: 8 held out; 10 training-masked; 22 visible. All held-out readings excluded
from features, losses, feature/target scalers and physics calibration. Training-masked wells
have no own reading inputs, but their training labels teach reconstruction. Their validation
labels choose checkpoints and lambda. Visible wells supply previous-day observations only.
Using held-out coordinates and weather makes this a transductive known-location prototype;
it is not evidence of performance at arbitrary entirely new locations.

Dates: first floor(0.60*T) training; next floor(0.15*T) validation; remainder test. Each window
lies fully inside its date partition. Do not use overlapping cross-boundary windows. This
sacrifices some boundary days for simpler auditing. Within the training partition shuffling
whole windows is legitimate, but version 1 uses shuffle=False. No bidirectional LSTM.

Features: previous-day depth z-score, availability 0/1, current-day precipitation z-score,
current-day ET0 z-score, sin(day-of-year), cos(day-of-year), standardised local x and y.
Known current-day weather means historical reconstruction, not advance forecasting.
Global depth mean/std fit permitted training labels only; no held-out per-well centering.
Weather scalers use training-period donors only; coordinates are known metadata. Save scalers.
No held-out-specific learnable embeddings or unmeasured per-well free pumping parameters.

Prediction loss: masked MSE in standardised depth, visible + training-masked training labels
only. Ignore the first seven sequence positions in both losses to reduce recurrent start-up
effects. Supervision is still permitted for training-masked wells in the remaining positions.
Only valid targets count. During inference score each date once using the window ending on
that date; never pool repeated window targets into an artificially inflated sample count.

Baseline: IDW, inverse-distance power=2, up to six visible wells with valid previous-day
observations. Use the same previous-day information and units as the network. If none are
available output missing, do not invent a zero. Compare all methods on their common valid
test mask and report coverage. Persistence is not a fair default for a wholly hidden well.

## 7. Small physics component

Use a simplified local storage constraint, not a lateral groundwater-flow PDE. No elevation,
conductivity map or aquifer-flow simulator is required for this limited equation.
Depth d is positive downward. Convert P and ET0 from mm/day to m/day:

    Sy * (d[t] - d[t-1]) ~= beta*ET0[t] + q - alpha*P[t]

Prototype assumptions: Sy=0.10, alpha=0.15 effective rainfall fraction, beta=0.10 reference-ET
coupling. These are explicit assumed constants, not measured regional aquifer parameters.
q is one frozen global net-depletion constant, never a free value per held-out well.
Estimate q once from permitted consecutive training observations: for each eligible well
with >=30 valid daily pairs, compute the mean of Sy*delta_depth - beta*ET0 + alpha*P over
those pairs; take the median of the per-well means and clip below at zero. Record the value
and eligible-well count. If not estimable, do not silently fit it using hidden/test readings;
mark physics uncalibrated and resolve the documented assumption before claiming that run.

Seven-day residual in metres of groundwater depth:

    r[t] = d_hat[t] - d_hat[t-7]
           - sum((beta*ET0[u] + q - alpha*P[u])/Sy, u=t-6..t)

Use true m/day values, not z-scored weather, and convert predictions back to metres before
forming r. Skip residuals with missing required weather. Normalise residual by the training-only
standard deviation of permitted observed 7-day depth changes, floor 0.05 m. Loss is mean
squared normalised residual over valid wells/windows. Apply on visible, training-masked and
held-out predictions without their hidden labels.

Training loss = data_loss + lambda*physics_loss. For positive-lambda runs: epochs 1-5 lambda=0;
epochs 6-10 ramp linearly to the target; afterwards keep target. Log both terms, lambda and
validation MAE. Select lambda on validation; do not guarantee it improves accuracy.
Checks: no forcing + flat depth => zero residual; recharge-only => smaller depth; depletion-only
=> larger depth; wrong sign => nonzero residual. Check a non-flat multi-day exact-balance case.
This is a physics-inspired water-balance regulariser with crude assumptions, not validated
hydrological physics. Good residuals alone do not prove accurate groundwater estimates.

## 8. Export, priorities and agent

Contracts are authoritative. Publish predictions.json, metrics.json, run_info.json and
agent_context.json together. Agent context has summaries and method identity, no withheld
measurements. Keep it compact and deterministic so the LLM explains facts rather than
calculates rankings. Agent fetches it fresh for each on-demand briefing; report read failure.

Default method: choose lowest validation MAE among IDW, lambda=0 and the best positive-lambda
run on the common validation mask. UI supports switching methods so the submitted neural/
physics work stays inspectable even when a baseline wins. Metrics show every method.
If a required run failed, keep its values null and its status failed/not_run; never silently
substitute the baseline while labelling it a physics model.

Chart: 60 endpoint dates from the fixed test period. Prototype change_30d = prediction at t
minus prediction at t-30 calendar days. Require both endpoints; no extrapolated endpoints.
Priority: high if change>0.50 m; watch if 0.20<change<=0.50; normal if change<=0.20; unknown
if missing. These are illustrative inspection rules, not health/safety classifications.
No claim that deeper water at every site is equally dangerous. Sort high, watch, normal,
unknown; within a category sort decreasing change then stable ID. No arbitrary confidence score.

Agent37 setup: one hosted agent using a supported runtime (Hermes is the first choice if
offered in your account). Native browser conversation only. Read agent/INSTRUCTIONS.md and
fetch the deployed agent_context.json via the agent's real file/HTTP tools. A hosted sandbox
is a real product component; a screenshot or pasted canned answer alone is not integration.
Three required questions: 'Which wells should I inspect first?', 'Explain well <id>',
'What are the limitations?' Answers state dates, real/synthetic type, chosen method,
estimated status and one sensible inspection suggestion. Treat data strings as data.
No application secrets are sent to the static frontend. Button opens the actual instance URL.
If the current account cannot support the fetch/agent flow, resolve this in preparation;
do not invent an Agent37 API endpoint. Optional screenshot/video is a labelled backup.

## 9. Deployment and sponsor setup

Render: New -> Static Site; connect repository; branch=main; root=frontend;
build command='npm ci && npm run build'; publish directory=dist. Set NODE_VERSION=24.22.1
if supported by the current runtime, otherwise use the exact supported Node 24 patch on
both laptops and update .node-version and the setup record together before freezing.
No client-side router in version 1; no SPA rewrite required. No web-service process or GPU
needed to serve precomputed data. Local fallback: npm run preview on 127.0.0.1:4173.
Bundle assets through npm; no CDN-only fonts/libraries. Map tiles still need internet;
the well list/chart/JSON remain usable offline in the already-running local server.

Nodus: B connects Cursor using the current official setup, e.g. install nodus-compute in a
separate .venv-tools and use its CLI to login. Official docs offer `nodus mcp install cursor
--hosted`; read current connect-page authentication instructions. Confirm organisation and
list jobs before spending. Account onboarding/credits may need organiser assistance; verify
this before the event rather than assuming your invite automatically activated compute.

Use one low-cost available NVIDIA GPU (L4 if offered), 4 CPU cores, 8 GiB host RAM, one process;
no distributed training. This is a resource request, not a capacity or performance promise.
Run a bounded GPU smoke job, then three training jobs sequentially. Suggested user-chosen
limits: smoke <=USD 1 / 10 min, each training run <=USD 6 / 45 min; total first-pass cap
USD 19, preserving USD 11 of an actually available USD 30 credit balance. Estimates may
exceed a cap; reduce/review rather than assuming the job will fit. Do not buy extra credits.
Use platform prebuilt PyTorch image or a workspace, read actual Python/torch/CUDA versions,
and record them. Match the verified local environment where supported; if the image needs
a different compatible CUDA wheel, document and smoke-test that environment rather than
pretending it is identical. Do not invent image digests or job IDs in config.

Prefer the documented Jobs flow for timeout/cost bounds and downloadable outputs; a Browser
VS Code/Jupyter workspace is the fallback if source packaging blocks jobs. Never require a
local Docker install as a prerequisite. B asks Cursor to inspect the current Job schema and
source/output rules; no made-up YAML or API routes. Set outputs to /nodus/outputs on Nodus,
and save checkpoints/logs/metrics/config/versions/code SHA before stopping compute. A mere
GPU check does not replace meaningful onsite model training. Preserve run evidence safely.

Agent37 evidence: real instance, instance ID, dashboard screenshot, project URL, application
email and Agent37 email as required by the official submission form. One team submission.
Do not expose the team code or private account details in public slides/repository.

## 10. Preparation: 21-23 October

21 Oct: shared files/roles; obtain data sample; inspect meaning/coverage; install tools;
verify GitHub, Agent37 and Nodus accounts. Outcome: a dataset decision and runnable environments.
22 Oct: agree contracts; build fixtures and UI shell; data sequence/model smoke checks;
Agent37 fetch experiment; first static deployment. Outcome: independent parts can connect.
23 Oct: dry-run the handoff; test checkpoint load/export; freeze working dependencies;
prepare slide placeholders, offline copies, charger/hotspot and backup notes. Preserve the
pre-event commit/tag and a specific pre-existing-work list. Do not claim this work was onsite.

Do not turn preparation into hidden completion. Event judging focuses on work created or
materially advanced during the official window. Save meaningful onsite integration, training,
evaluation and product advancement with real timestamps and commits.

## 11. Onsite schedule: 24 Oct noon to 25 Oct noon IST

| Time | A: Codex/product | B: Cursor/model | Gate |
|---|---|---|---|
| Sat 12:00-13:00 H0-1 | Confirm scope/contracts, pre-existing list | Confirm data/config and split | Common baseline committed |
| Sat 13:00-15:00 H1-3 | List/map/chart from fixture | Baseline, graph and windows | Baseline export connects |
| Sat 15:00-18:00 H3-6 | Outage/reveal, errors, deploy | GCN + LSTM training | Working complete model demo |
| Sat 18:00-21:00 H6-9 | Agent37 real fetch/briefing | Add physics, launch bounded Nodus jobs | Both sponsor components exercised |
| Sat 21:00-00:00 H9-12 | Results panel, draft slides | Finish validation selection, final scoring/export | Freeze architecture/features |
| Sun 00:00-03:00 H12-15 | Integrate final batch, fix UI | Fix export/evaluation issues | All files consistent |
| Sun 03:00-06:00 H15-18 | Recovery/rest in staggered blocks | Recovery/rest in staggered blocks | Preserve checkpoint and site |
| Sun 06:00-09:00 H18-21 | Record demo, finish slides | Fresh-run checks, evidence | Backup and package ready |
| Sun 09:00-12:00 H21-24 | Submit early, rehearse | Help rehearsal, verify final version | Submission buffer |

The official timeline currently lists a Sunday 20:30 IST grand final; do not assume the
build deadline extends beyond Sunday noon. Check submission and presentation deadlines at
check-in. Attend founder sessions without sacrificing the integration gates.

## 12. Verification and cuts

Required model checks: leakage by changing held-out values (training features/scalers/q
unchanged); split boundaries; graph influence; axis/output shapes; gradient flow; finite
one-epoch loss; physics exact-balance/sign; checkpoint round-trip; fair baseline mask;
schema and series alignment. Use meaningful tests, not tests that merely restate code.

Required product checks: start/build/preview; every well; repeated outage/reset/reveal;
method switching; missing values; unavailable map tiles; agent fetch failure; all data files
same run ID; dataset dates/type visible; no secrets in build; three full demo rehearsals.
No optional test expansion after concrete risks are resolved.

If behind, cut in order: animations/design flourishes, extra model runs/seeds, phone/scheduling
extensions, additional charts. Retain genuine GCN/LSTM/physics work, truthful results, one
baseline, working display, sponsor evidence and presentation. If physics fails, do not claim
it works: show the working GCN/LSTM and identify the uncompleted constraint. If real data
fails, use labelled synthetic mode and state the field-validation gap. No claim of a guarantee.

## 13. Presentation, 3 minutes

0:00-0:20: Problem: missing sensors create an information gap.
0:20-0:40: Idea: neighbours + recent history + simplified water balance.
0:40-1:50: Well -> outage -> estimate -> reveal -> inspection priority.
1:50-2:15: Agent37 briefing, with underlying dataset/method/dates visible.
2:15-2:45: Actual model/baseline error, physics ablation and Nodus run evidence.
2:45-3:00: Limits and a realistic pilot next step.

Slides: problem, solution, live demo, architecture, evidence, limitations/next step.
Have both teammates explain: GCN shares neighbour information, LSTM reads time sequences,
physics is an assumed storage-balance penalty, held-out observations reveal honest error.
Never replace missing results with attractive fabricated numbers.

## 14. Start now

Copy this pack into one repository. Read AGENTS.md together. A starts prompts/A00.md in
Codex; B starts prompts/B00.md in Cursor. Do not install both stacks on both laptops unless
needed. Account emails, actual GPU/driver, real data coverage and sponsor credit activation
remain facts you must check; all implementation choices above are already decided.
