# Person A status

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
