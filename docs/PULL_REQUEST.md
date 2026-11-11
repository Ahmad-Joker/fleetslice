FleetSlice compares baseline and candidate motion forecasts on identical scenes and flags regressions by city, actor type, observed speed and observed motion. A controlled fixture shows why this matters: global displacement metrics improve while turning trajectories deteriorate; the slice gate catches the change.

The implementation includes strict JSONL contracts, paired bootstrap intervals, conservative three-state decisions, diversity-aware retrospective triage, offline trajectory reports, immutable output paths, hashed provenance, CPU kinematic references, and a labeled Argoverse 2 focal-track adapter.

Validation: 48 tests passed locally; Ruff checks and formatting passed; wheel and sdist built. The public-data workflow was run on 128 official AV2 validation scenes with zero adapter skips. The constant-acceleration candidate regressed versus constant velocity; results are reported without claiming improvement. The synthetic run also correctly exits with a regression status.

Limits: one forecast mode, open-loop displacement evaluation, exploratory unadjusted intervals, small nonrandom AV2 sample, in-memory evaluation. No neural model training or vehicle safety claim. GitHub-hosted CI will run after publication; its result has not yet been observed.
