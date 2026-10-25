# B Phase 0 setup

Observed 24 October 2026 on this Ubuntu checkout. This note records the environment that was actually installed and checked. It is not a trained model, a Nodus job, or a field-accuracy claim.

## Machine

- OS: Ubuntu 26.04.1 LTS (Resolute Raccoon), x86_64, kernel 7.0.0-38-generic, glibc 2.43.
- Memory at inspection: 22 GiB total, about 11 GiB available. Swap 8 GiB, unused.
- Disk: `/` has 446 GiB available.
- GPU: NVIDIA GeForce RTX 5050 Laptop GPU, 8151 MiB, compute capability 12.0, PCI device 0x2D9810DE.
- Driver already present: NVIDIA UNIX Open Kernel Module 595.99.02. `nvidia-smi` reports CUDA Version 13.2. No driver or CUDA toolkit was installed in this phase.
- A sandboxed `nvidia-smi` could not see the device. The same command outside the sandbox printed the GPU above at 24 Oct 2026 18:45:33 local time. That unsandboxed reading is the one recorded here.

## Cursor

- Working app: `/usr/bin/cursor` -> `/usr/share/cursor/bin/cursor`, version 3.24.18, commit `be4c9e5350d77747b42cd467cbd3370a753d4640`, x64.
- This Phase 0 session is that local Cursor agent, with the repository root open.
- `command -v cursor` resolves to an empty file, `/home/ghost/.local/bin/cursor` (0 bytes, dated 21 Oct 2026). Use `/usr/bin/cursor` until that empty file is removed by the operator. It was left in place.

## Repository

- Root: `/home/ghost/repo/alter-ego`
- Branch: `feature/model`
- Parent of this setup: `e756549b7de11368f9af54e7f123f9a412c79f78` (`Add original Alter Ego shared build pack`)
- Remote: `origin` `https://github.com/panda0519/alter-ego`
- `git ls-remote --heads origin` returned:
  - `refs/heads/feature/person-a` `c9317d9b71180db00f43a888405888711da08c26`
  - `refs/heads/main` `8cc5fd7435f706cf407ae19fba4e669d78408240`
  - `refs/heads/setup/alter-ego-build-pack` `e756549b7de11368f9af54e7f123f9a412c79f78`
- `feature/model` has no upstream. It matches `origin/setup/alter-ego-build-pack`.
- `git merge-base feature/model origin/feature/person-a` is `e756549b7de11368f9af54e7f123f9a412c79f78`. Person A's product commits sit on top of the pack.
- `git merge-base main feature/model` exits 1. `origin/main` is a different history. It was not merged.
- The pack commit `e756549b7de11368f9af54e7f123f9a412c79f78` is authored `panda0519 <shubhamsgh198@gmail.com>`.
- Repo-local Git identity, written only in `.git/config`: `user.name` `theravij`, `user.email` `2501640100693@psit.ac.in`. `git config --local --show-origin` reports both from `file:.git/config`. There is no `~/.gitconfig`.
- `gh` is not installed. Push was not attempted.

## Python and PyTorch

System `/usr/bin/python3` remains Python 3.14.4. It was not replaced.

uv 0.13.5 installed a separate CPython 3.11.17 at:

`/home/ghost/.local/share/uv/python/cpython-3.11-linux-x86_64-gnu/bin/python3.11`

That patch is the Linux runtime used here. It is not the Windows installer baseline 3.11.9.

Project environment: `/home/ghost/repo/alter-ego/.venv`, created with `uv venv --seed --python 3.11 .venv`.

Installed from `ml/requirements-common.txt` plus the explicit format extra, then:

`torch==2.8.0` from `https://download.pytorch.org/whl/cu128`

Observed torch build: `2.8.0+cu128`, wheel CUDA 12.8. `torch.cuda.is_available()` is true on the RTX 5050. An 8x8 tensor forward and backward on `cuda` returned finite values and a finite gradient.

`.venv/bin/python -m pip check` printed `No broken requirements found.`

No `.venv-cpu` was created. The CPU wheel was not installed. TensorFlow, torch_geometric, and Optuna are not installed.

## Requirements correction for A

Before the edit, `ml/requirements-common.txt` SHA-256 was `a1619c46f50f9c53c1940ec9da9c5dec1a5c6a76cc3af7536875ab102b4eceff`, matching `CONTENTS_SHA256.txt`. The original archive was not modified.

The B-owned line is now:

`jsonschema[format-nongpl]==4.25.1`

SHA-256 after the edit: `4534cd3f7dcd70a949c494dc13d88284b854cc8aa3bf7d41c9d01c32d9a90d5c`.

The installed environment has `rfc3339-validator==0.1.4`, and `date-time` is registered on `jsonschema.FormatChecker`. `scripts/validate_exports.py` accepts `contracts/fixtures` and rejects the same fixture batch after every `generated_at_utc` is set to `not-a-timestamp`. The rejection is `'not-a-timestamp' is not a 'date-time'`. A owns `scripts/validate_exports.py`; it was not edited.

## Lock

`ml/locks/ubuntu-cuda128-working.txt` is `pip freeze --all` from `.venv` (64 lines). `ml/locks/ubuntu-cuda128-pip-check.txt` is the matching pip check. The freeze contains `torch==2.8.0+cu128` and the common pins. A scan found no `file:` URLs, credentials, TensorFlow, torch_geometric, or Optuna. This lock is the local CUDA environment only. It is not a Nodus image lock.

## Nodus

Separate tools environment: `.venv-tools`, also CPython 3.11.17. It is gitignored and is not part of the model lock.

- Package: `nodus-compute` 1.0.27 (Apache-2.0).
- CLI banner from `nodus version`: `nodus 0.1.45`.
- `nodus --version` exits 2: `unknown flag: --version`.
- `nodus whoami` and `nodus get jobs` both exit 1: `not logged in: run nodus login, or set NODUS_API_KEY`.
- No `~/.nodus` directory and no `NODUS_*` environment variables.
- `nodus mcp install --help` documents `nodus mcp install cursor --hosted`. That command was not run. This Cursor session has no Nodus MCP namespace, and `~/.cursor/mcp.json` is absent.
- No login, no job, no credit purchase, and no spend. Organisation, project, and credit balance were not visible.

The operator still needs to run `nodus login` in their own browser, then `nodus whoami`, and only then decide whether to install hosted MCP. Login was not started here because it submits an account authorisation.

## Shared config and the later B05 handoff

`ml/configs/prototype.yaml` is schema 1.0.0: seed 42, 40 wells, 2023-01-01 through 2024-12-31, depth `m_below_ground`, one GCN layer 8->32, one unidirectional LSTM hidden 32, lambda targets 0.0, 0.1, and 1.0. It was read and left unchanged.

B will follow the existing contract 1.0.0 handoff when B05 starts:

- One directory, `artifacts/exports/<run_id>/`, containing `predictions.json`, `metrics.json`, `run_info.json`, and `agent_context.json`.
- All four `meta` objects match, including `schema_version` 1.0.0.
- B05's neural methods stay all-null with status `not_run` until a real neural run exists. IDW is not labelled as a neural method.
- `agent_context.json` stays summary-only for the default method and excludes withheld measurements.
- A validates the batch and is the only person who copies it to `frontend/public/data/`.

No export batch was written in this phase. A has not been messaged from this session. The pin change above is the item that needs A's review.

## Left outside this phase

- Model, baseline, data download, and synthetic generator code.
- Node 24.22.1. System `node` is v24.21.0. The user-local Node installer was not run.
- `gh`, and a push of `feature/model`.
- Nodus login, organisation, credits, MCP, and any compute. `nodus whoami` is still not logged in.
