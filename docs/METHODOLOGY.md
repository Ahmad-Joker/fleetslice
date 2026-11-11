# Methodology

## Scope

This is an open-loop, unimodal forecast evaluator. A predictor receives historical actor positions
and produces one future trajectory. We compare that trajectory to recorded future positions.
The evaluated actor's actions cannot alter the recorded world. Consequently these results say
nothing about closed-loop planning, collisions, road compliance, social interaction, or FSD safety.

There is one focal actor per scenario. Scene-level bootstrap assumes independent scenarios.
Overlapping clips from the same drive require grouped resampling before meaningful confidence
claims; this version does not implement drive-level grouping.

## Metrics

For truth positions `y_t` and predictions `p_t` at T future instants:

- `ADE = mean_t ||p_t - y_t||₂` in metres.
- `FDE = ||p_T - y_T||₂` in metres.
- `miss = 1[FDE > miss_threshold]`, averaged across scenes; default threshold 2 m.

These are K=1 metrics. There is no best-of-K selection, probability calibration, or official AV2
challenge evaluator. A 2 m endpoint threshold alone does not reproduce an entire benchmark.
The standard displacement definitions can be inspected in the
[official Argoverse evaluation code](https://github.com/argoverse/argoverse-api/blob/master/argoverse/evaluation/eval_forecasting.py).
Implementation here is original; no upstream evaluation code is copied.

## Slice construction

Every scene belongs to `all`, its city, its actor type, one speed bin, and one behavior bin.
Slice membership uses observed history and metadata only.

| Feature | Definition |
|---|---|
| Speed | Norm of last observed displacement divided by dt |
| Stopped | Speed < 0.5 m/s |
| Moving | 0.5 ≤ speed < 10 m/s |
| Fast | Speed ≥ 10 m/s |
| Turning | Absolute net unwrapped heading change across moving history intervals ≥ 20° |
| Accelerating | Non-turning; norm of final velocity difference / dt ≥ 1 m/s² |
| Steady | Remaining scenes |

Heading excludes observed intervals slower than 0.5 m/s. Net heading change can miss S-turns.
The acceleration label includes changes in direction; it is a motion-change heuristic, not a
longitudinal vehicle-dynamics measurement. Thresholds are fixed in the source and must be reviewed
for other sampling rates, noisier sensors, or actor types. Object-type/city slices can overlap behavior
and speed slices, so counts should not be summed.

## Paired inference and decisions

For each scene and metric, compute `delta_i = candidate_i - baseline_i`. Sample N complete scene
deltas with replacement, compute their mean, and repeat 2,000 times by default. The 2.5th and 97.5th
percentiles form a two-sided 95% interval. This keeps the baseline/candidate pair together.
Resampling uses bounded memory and a stable seed derived from run seed, slice name, and metric.
Sorted scene IDs make results invariant to input row order. Reproducibility assumes compatible
NumPy versions; each run records the actual version.

For each slice and metric:

| Condition | Result |
|---|---|
| N < minimum sample count (default 10) | Insufficient data |
| Lower interval endpoint > tolerance | Regression |
| Upper interval endpoint ≤ tolerance | Within tolerance |
| Otherwise | Inconclusive |

The overall gate returns regression if any comparison regresses; otherwise it returns within
tolerance only if every comparison is within tolerance. Remaining cases are inconclusive.
The minimum count is an operational guard, not a guarantee of statistical power. Rare binary misses
can yield deceptively narrow percentile intervals. Treat the results as exploratory evidence.
There is no family-wise or false-discovery-rate correction across metrics and overlapping slices.
A formal release process needs a predeclared primary family, power analysis, and appropriate
multiplicity controls. The software's pass state is never a vehicle release authorization.

## Reference models

CV extrapolates the last interval velocity. CA estimates acceleration from the last three observed
positions, caps its vector norm at 5 m/s², estimates instantaneous velocity from midpoint velocity,
then extrapolates. CA is intentionally simple and sensitive to noise; it can deteriorate over a
six-second horizon. Neither model uses maps, interactions, a GPU, learned weights, or future labels.

## Investigation queue

Consider only scenes with positive ADE delta. Greedy priority is 80% normalized ADE regression
severity and 20% minimum feature distance from already chosen scenes, clipped at 1. Features are
normalized last speed, acceleration magnitude, and net heading change. The first pick uses severity
only; sorted scene IDs break ties. Features use only history. This is retrospective failure curation
using labeled outcomes, not online active learning or a measured label-efficiency improvement.

## Integrity and scale

JSONL input validation rejects partial coverage rather than silently dropping scenes. Runs reject
mixed sources, horizons, dt or history lengths. The AV2 adapter requires all 110 focal timestamps,
with exactly 50 observed and 60 labeled future frames, and reports skipped files. It translates the
last observation to the origin and preserves the global XY orientation.

Output bundles are assembled in a temporary sibling directory and renamed after success. Existing
output paths are refused. `manifest.json` records all three input hashes, configuration, versions,
and hashes of the other output artifacts. The manifest does not hash itself. This detects later
content changes; it is not a cryptographic signature or proof that inputs were trustworthy.

This version loads scenes and predictions into RAM. Bootstrap index allocation is bounded, but
scoring and reports are not a distributed streaming pipeline. The HTML includes a bounded selection
of trajectories plus all per-scene metrics. No fleet-scale throughput claim has been measured.
