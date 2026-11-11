# FleetSlice evaluation

Gate: **regression**

Source: argoverse2-motion-forecasting-local. Scenes: 128.

Positive delta means the candidate is worse. Units: metres; miss rate is a fraction.

| Metric | Baseline | Candidate | Delta | 95% interval | Status |
|---|---:|---:|---:|---|---|
| ade_m | 4.3541 | 7.9583 | +3.6042 | [2.1654, 5.0785] | regression |
| fde_m | 11.3920 | 23.8980 | +12.5060 | [8.4506, 16.9530] | regression |
| miss_rate | 0.8672 | 0.9688 | +0.1016 | [0.0469, 0.1641] | regression |

## Flagged slices

- actor:vehicle (n=117): ade_m, fde_m
- all (n=128): ade_m, fde_m, miss_rate
- behavior:accelerating (n=51): ade_m, fde_m
- behavior:steady (n=55): miss_rate
- behavior:turning (n=22): ade_m, fde_m
- city:austin (n=37): ade_m, fde_m, miss_rate
- city:dearborn (n=10): ade_m, fde_m
- city:palo-alto (n=10): ade_m, fde_m
- city:pittsburgh (n=26): fde_m
- speed:fast (n=35): ade_m, fde_m, miss_rate
- speed:moving (n=75): ade_m, fde_m

## Interpretation

Open-loop, unimodal displacement evaluation only. This is not a vehicle safety certification, collision evaluation, closed-loop simulator, or leaderboard result.
Intervals are exploratory per-comparison intervals without multiplicity correction. Sparse or ambiguous slices make the overall decision inconclusive unless a regression is detected. No absence-of-regression claim follows from inconclusive results.
