# FleetSlice evaluation

Gate: **regression**

Source: synthetic-injected-errors. Scenes: 200.

Positive delta means the candidate is worse. Units: metres; miss rate is a fraction.

| Metric | Baseline | Candidate | Delta | 95% interval | Status |
|---|---:|---:|---:|---|---|
| ade_m | 0.8985 | 0.3897 | -0.5088 | [-0.5707, -0.4405] | within_tolerance |
| fde_m | 0.8985 | 0.3897 | -0.5088 | [-0.5703, -0.4430] | within_tolerance |
| miss_rate | 0.0000 | 0.0000 | +0.0000 | [0.0000, 0.0000] | within_tolerance |

## Flagged slices

- behavior:turning (n=20): ade_m, fde_m

## Interpretation

Open-loop, unimodal displacement evaluation only. This is not a vehicle safety certification, collision evaluation, closed-loop simulator, or leaderboard result.
Intervals are exploratory per-comparison intervals without multiplicity correction. Sparse or ambiguous slices make the overall decision inconclusive unless a regression is detected. No absence-of-regression claim follows from inconclusive results.
