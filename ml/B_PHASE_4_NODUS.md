# B Phase 4 Nodus request

Observed 24 October 2026 from `/home/ghost/repo/alter-ego`. No job was created. No estimate was returned. No credit balance was visible.

## What was actually run

Client: `.venv-tools/bin/nodus`, banner `nodus 0.1.45`.

| Command | Result |
|---|---|
| `.venv-tools/bin/nodus whoami` | Exit 1. `Error: not logged in: run nodus login, or set NODUS_API_KEY`. Repeated outside the sandbox. |
| `.venv-tools/bin/nodus get jobs` | Exit 1. Same not-logged-in error. |
| `.venv-tools/bin/nodus explain job` | Exit 1. Same not-logged-in error. The server Job schema was not retrieved. |
| `.venv-tools/bin/nodus api-resources` | Exit 1. Same not-logged-in error. |
| `.venv-tools/bin/nodus run --help` | Exit 0. Local flag help only. |

`~/.nodus` is absent. No `NODUS_` environment variables. The Cursor `user-nodus` MCP namespace was in status `error` during tool discovery. `mcp_auth` was not called. `nodus login` was not run.

`nodus run --help` documents these flags that match the intended shape: `--gpu` as `TYPE[:COUNT]` with example `L4`, `--cpu`, `--memory` with example `64Gi`, `--image` with example `nodus/pytorch`, `--max-cost`, `--timeout`, `--expected-duration`, `--dry-run`, `--output NAME=/path`, and `--checkpoint` default `/nodus/state`. The help also says the command uploads the current directory unless `--no-source`, prints an estimate, and can end with a cost line. That behaviour was not exercised.

## Not submitted

These commands were not run, including not as `--dry-run`. L4 availability, the image digest, and the account cost were not observed. Caps below are the limits for a later approved request, not a platform approval.

Smoke, one process, at most `$1` and `10m`:

```text
.venv-tools/bin/nodus run --dry-run --gpu L4 --cpu 4 --memory 8Gi --image nodus/pytorch --max-cost 1 --timeout 10m --expected-duration 10m --output run=/nodus/outputs --checkpoint /nodus/state -- python -m ml.cli train --config ml/configs/prototype.yaml --bundle data/processed/active --lambda-target 0 --run-dir /nodus/outputs/lambda0-smoke --smoke
```

After that smoke is retrieved, the same shape with `--max-cost 6` and `--timeout 45m`, one GPU and one process, run one after another for lambda `0`, `0.1`, and `1`. Do not add `--nodes`, `--launcher torchrun`, or a gang. First-pass total cap `$19`. If a real estimate is above its cap, reduce the request or stop. Do not buy credits.

The training entry point is the existing CLI. Checkpoints and `train_manifest.json` would be written under the `--run-dir` passed above, which is the declared `/nodus/outputs` path. Nothing has been written there.

## Blocker

Login, organisation, project, scopes, and credits are unknown. The server schema from `nodus explain job` is unknown. Whether `nodus run` would upload the gitignored bundle in `data/processed/active` was not tested; a launch has to confirm that packaging before any submit. Local lambda-0 and positive-lambda checkpoints already exist under `runs/` and do not depend on this request.
