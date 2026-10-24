# Person A status

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
