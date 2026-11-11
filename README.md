# FleetSlice

**Motion forecast regressions should be visible before a model change ships.**

FleetSlice compares baseline and candidate forecasts on the same driving scenes, measures
displacement error by motion slice, flags regressions with paired bootstrap intervals, and
builds an offline report with trajectory inspection and a prioritized investigation queue.

Built by **Ahmad Essam Abdelaziz**, an Artificial Intelligence student at AAST.
Independent portfolio project; no Tesla affiliation, proprietary data, or production driving claims.

## See it in one minute

Open [the included synthetic report](examples/synthetic-report/report.html) after downloading
this repository. GitHub displays HTML source; download the file to open it in a browser.
The example intentionally improves average error while degrading turning scenarios. The evaluator
blocks the change. These are injected fixture predictions, not outputs from a trained model.

```bash
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -e '.[dev,av2]'
fleetslice demo --out data/demo
fleetslice evaluate --data data/demo/scenes.jsonl --baseline data/demo/baseline.jsonl --candidate data/demo/candidate.jsonl --out runs/demo
```

The last command intentionally returns **1** because it catches the seeded regression.
Open `runs/demo/report.html`. Each output directory is immutable; use a new path for another run.

## What it does

- Enforces exact scene pairing, finite coordinates, matching horizons and uniform sampling.
- Computes unimodal ADE, FDE, and endpoint miss rate; all deltas are candidate minus baseline.
- Slices results by city, actor type, observed speed, and observed motion behavior.
- Uses paired, scene-level 95% percentile bootstrap intervals and configurable tolerances.
- Distinguishes regressions, results within tolerance, uncertainty, and insufficient data.
- Ranks positive ADE regressions using severity and motion-feature diversity.
- Exports an interactive HTML report, JSON, CSV, triage JSONL, Markdown, and SHA-256 provenance.
- Runs history-only constant-velocity and acceleration-capped constant-acceleration references on CPU.
- Imports official Argoverse 2 labeled focal tracks without requiring the full AV2 SDK.

## Public driving-data experiment

The repository includes a measured run on 128 official AV2 validation scenes in
[examples/av2-report](examples/av2-report), with the sampling manifest and exact results in
[the experiment record](docs/EXPERIMENTS.md). The sample is lexicographic, small, and nonrandom;
it is a pipeline check, not a leaderboard or representative performance estimate.

Reproduce it with:

```bash
python scripts/fetch_av2_sample.py --count 128 --out data/av2-val
fleetslice import-av2 --input data/av2-val --out data/av2-scenes.jsonl
fleetslice predict --data data/av2-scenes.jsonl --model cv --out data/cv.jsonl
fleetslice predict --data data/av2-scenes.jsonl --model ca --out data/ca.jsonl
fleetslice evaluate --data data/av2-scenes.jsonl --baseline data/cv.jsonl --candidate data/ca.jsonl --baseline-label constant-velocity --candidate-label constant-acceleration --out runs/av2
```

No neural model is trained here. The contribution is the evaluation system. Bring model outputs
through the JSONL interface to test a learned predictor under the same protocol.

## Input contract

One focal actor per independent scene. `history` contains at least three equally spaced observed
XY positions; `future` contains the next positions, without repeating the final observed point.
Coordinates are metres in one fixed frame; `dt` is seconds.

```json
{"scene_id":"s1","history":[[0,0],[1,0],[2,0]],"future":[[3,0],[4,0]],"dt":0.1,"city":"PIT","actor_type":"vehicle","source":"my-validation-set"}
```

Prediction files contain exactly one record per dataset scene, with a single trajectory:

```json
{"scene_id":"s1","prediction":[[3.1,0],[4.2,0]]}
```

See [methodology](docs/METHODOLOGY.md) for formulas, slice thresholds, interpretation, and limits.
The engine rejects missing, extra, duplicate, nonfinite, or mismatched predictions.
Future labels are used for scoring and retrospective triage; they never enter reference predictors
or behavior/speed slice definitions.

## Use as a CI check

| Exit | Meaning |
|---:|---|
| 0 | All evaluated slice/metric intervals are within the configured tolerances |
| 1 | At least one adequately sampled slice/metric indicates a regression |
| 2 | No regression detected, but at least one comparison is uncertain or too sparse |
| 3 | Invalid input, configuration, dependency, or output path |

The default tolerances are 0.2 m ADE, 0.5 m FDE, and 0.02 absolute miss rate.
They are illustrative engineering choices, not validated automotive acceptance criteria.
Predeclare slices and thresholds for your dataset; do not tune them against final test labels.

```bash
ruff check .
ruff format --check .
pytest
python -m build
```

GitHub Actions runs the tests and builds the package on Python 3.11–3.13.
Local verification details are recorded in [VALIDATION.md](docs/VALIDATION.md).

## Why this project

[The Tesla research](docs/TESLA_RESEARCH.md) maps public internship requirements to Ahmad's
Python, ML evaluation, automation, reliability, and full-stack background. The project targets
model validation and developer tooling. It does not demonstrate custom inference hardware,
distributed clusters, Kubernetes operations, or real-time vehicle integration.

## Publish to a dedicated repository

This archive includes the complete source. If it has not already been published, use the official
GitHub CLI on an authenticated machine:

```bash
gh auth login
python scripts/publish_github.py
python scripts/publish_github.py --publish
```

The first script invocation previews the plan. The second creates `Ahmad-Joker/fleetslice`,
pushes a fresh feature branch and opens a PR. It refuses an existing repository and never merges.
Use `--name fleetslice-evaluation` if the original name has become unavailable.

## License and data

Code and synthetic outputs: [MIT](LICENSE).
AV2-derived reports: [dataset attribution and terms](examples/av2-report/DATA_LICENSE.md),
CC BY-NC-SA 4.0 with the original dataset terms. Raw AV2 files are downloaded locally and ignored
by Git. No Tesla marks or assets are bundled.
