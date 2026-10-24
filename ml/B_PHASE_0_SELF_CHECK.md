# B Phase 0 self-check

Date: 24 October 2026. Checkout: `/home/ghost/repo/alter-ego`, branch `feature/model`, parent `e756549b7de11368f9af54e7f123f9a412c79f78`. Commands ran from the repository root unless noted. A row is PASS only when the observed result happened.

| Check | Command or action | Expected | Observed | Result |
|---|---|---|---|---|
| OS and architecture | `cat /etc/os-release`; `uname -m`; `getconf GNU_LIBC_VERSION` | Ubuntu x86_64 facts recorded | Ubuntu 26.04.1 LTS, x86_64, glibc 2.43, kernel 7.0.0-38-generic | PASS |
| Memory and disk | `free -h`; `df -h "$HOME"` | Practical room for the Python/GPU install | 22 GiB RAM, about 11 GiB available; 446 GiB free on `/` | PASS |
| Git root and branch | `git rev-parse --show-toplevel`; `git status --short --branch` | Existing checkout kept on `feature/model` | Root `/home/ghost/repo/alter-ego`. Branch `feature/model` at the pack commit. No second repository created | PASS |
| Remote heads | `git ls-remote --heads origin` | A's shared repo is reachable | `feature/person-a` `c9317d9b71180db00f43a888405888711da08c26`; `main` `8cc5fd7435f706cf407ae19fba4e669d78408240`; `setup/alter-ego-build-pack` `e756549b7de11368f9af54e7f123f9a412c79f78` | PASS |
| Unrelated main left alone | `git merge-base main feature/model` | Do not merge a different history | Exit 1, no merge-base. `origin/feature/person-a` does share parent `e756549b7de11368f9af54e7f123f9a412c79f78` | PASS |
| Git author identity | `git config --local user.name theravij`; `git config --local user.email 2501640100693@psit.ac.in`; `git config --local --show-origin --get user.name`; `git config --local --show-origin --get user.email` | Repo-local author recorded | `file:.git/config` has `theravij` and `2501640100693@psit.ac.in`. No `~/.gitconfig`. Pack commit author remains `panda0519 <shubhamsgh198@gmail.com>` | PASS |
| GitHub CLI and push | `command -v gh`; push not run | Push permission known before a handoff | `gh` is absent. Fetch of heads succeeded. Push was not attempted | PENDING |
| Cursor app | `/usr/bin/cursor --version` | Installed Cursor retained | `3.24.18`, `be4c9e5350d77747b42cd467cbd3370a753d4640`, `x64`. `~/.local/bin/cursor` is an empty 0-byte file and is first on `PATH` | PASS |
| Python 3.11 isolation | `uv python install 3.11`; `.venv/bin/python --version`; `/usr/bin/python3 --version` | Isolated 3.11, system Python unchanged | uv 0.13.5 installed CPython 3.11.17. `.venv/bin/python` is 3.11.17. `/usr/bin/python3` remains 3.14.4 | PASS |
| Common pins and format extra | `.venv/bin/python -m pip install -r ml/requirements-common.txt 'jsonschema[format-nongpl]==4.25.1'` | Exact common pins plus date-time checking | numpy 2.2.6, pandas 2.2.3, scipy 1.15.3, scikit-learn 1.6.1, requests 2.32.5, PyYAML 6.0.2, jsonschema 4.25.1, pytest 8.4.2, rfc3339-validator 0.1.4. `date-time` is in `FormatChecker.checkers` | PASS |
| pip check | `.venv/bin/python -m pip check` | No broken requirements | `No broken requirements found.` Saved in `ml/locks/ubuntu-cuda128-pip-check.txt` | PASS |
| Torch wheel and GPU tensor | `.venv/bin/python` script importing the common packages and running an 8x8 `cuda` forward/backward | Finite loss and finite gradient on the real device | `Torch: 2.8.0+cu128 wheel CUDA: 12.8`. Device `NVIDIA GeForce RTX 5050 Laptop GPU`, capability (12, 0). Printed `PASS: actual tensor forward/backward on cuda` | PASS |
| Driver reading | `nvidia-smi` outside the sandbox | Actual driver, or an explicit CPU fallback | Driver 595.99.02, CUDA Version 13.2, RTX 5050 Laptop GPU, 8151 MiB. CPU fallback was not used | PASS |
| Good fixture batch | `.venv/bin/python scripts/validate_exports.py contracts/fixtures` | Checker accepts the shared fixtures | Exit 0. `PASS: schemas, metadata, dates, series, summaries and metric status consistent.` | PASS |
| Bad `generated_at_utc` | `.venv/bin/python -m pytest tests -q` | Checker rejects an invalid timestamp shared by all four meta objects | `2 passed in 2.17s`. Direct checker on the mutated batch exited 1 with `'not-a-timestamp' is not a 'date-time'` | PASS |
| Environment lock | `.venv/bin/python -m pip freeze --all > ml/locks/ubuntu-cuda128-working.txt` | CUDA freeze kept separate and free of private URLs | 64 lines. Contains `torch==2.8.0+cu128`. No `file:` URL, TensorFlow, torch_geometric, or Optuna. No CPU lock written | PASS |
| Requirements digest | `sha256sum ml/requirements-common.txt` before and after the one-line edit | Original digest captured, then only the format extra changes | Before `a1619c46f50f9c53c1940ec9da9c5dec1a5c6a76cc3af7536875ab102b4eceff` (matches `CONTENTS_SHA256.txt`). After `4534cd3f7dcd70a949c494dc13d88284b854cc8aa3bf7d41c9d01c32d9a90d5c` | PASS |
| Nodus CLI | `.venv-tools/bin/python -m pip install nodus-compute`; `.venv-tools/bin/nodus version` | Current CLI installed in a separate venv | Package `nodus-compute` 1.0.27. Banner `nodus 0.1.45`. `nodus --version` exits 2, unknown flag | PASS |
| Nodus account, org, credits, jobs | `.venv-tools/bin/nodus whoami`; `.venv-tools/bin/nodus get jobs` | Real org and credit observed, with no compute launched | Both exit 1: `not logged in`. No `~/.nodus`, no `NODUS_*` variables, no job id | PENDING |
| Nodus MCP in Cursor | Inspect `nodus mcp install --help` and the live Cursor tool list | Hosted tools visible only after a real install | Help documents `nodus mcp install cursor --hosted`. Command not run. No Nodus tools in this session. No `~/.cursor/mcp.json` | PENDING |
| prototype.yaml and B05 handoff | Read `ml/configs/prototype.yaml`, `contracts/README.md`, and `prompts/B05.md` | Four-file schema 1.0.0 handoff recorded for A | YAML left unchanged. B acceptance is in `ml/B_PHASE_0_SETUP.md`. No export written. A was not messaged | PASS |
| Node 24.22.1 | `node --version` | Record only; training does not need it | System node is v24.21.0. The user-local 24.22.1 installer was not run | PENDING |
| Setup commit | Stage the B-owned Phase 0 files and `git commit` with the repo-local identity | One commit on `feature/model` by `theravij <2501640100693@psit.ac.in>` | The first attempt, before this identity existed, exited 128 with `fatal: unable to auto-detect email address (got 'ghost@ghost.(none)')`. Repo-local identity is now set. This commit uses it. Nodus login stays PENDING | PASS |

## Commit attempt

The first `git commit` exited 128 because no author was configured:

```text
fatal: unable to auto-detect email address (got 'ghost@ghost.(none)')
```

Repo-local `.git/config` was then set to `user.name=theravij` and `user.email=2501640100693@psit.ac.in`. No global git config was written. The Phase 0 commit uses that identity. Nodus remains not logged in.

## Evidence files

- `ml/locks/ubuntu-cuda128-working.txt`
- `ml/locks/ubuntu-cuda128-pip-check.txt`
- `tests/test_generated_at_utc_format.py`
- `ml/requirements-common.txt`

## Explicit non-claims

The CUDA tensor step does not exercise GCN, LSTM, the water-balance regulariser, or a data pipeline. Nodus was not used. No dataset was frozen. No `artifacts/exports/<run_id>/` batch exists. Fixture metrics remain illustrative.
