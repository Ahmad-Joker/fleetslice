"""Deterministic paired evaluation and conservative three-state regression decisions."""

import hashlib
from dataclasses import asdict, dataclass

import numpy as np

from fleetslice.metrics import displacement, paired_interval
from fleetslice.schema import Scene, points
from fleetslice.slices import features, memberships, select_triage


@dataclass(frozen=True)
class Config:
    seed: int = 42
    resamples: int = 2000
    min_samples: int = 10
    ade_tolerance: float = 0.2
    fde_tolerance: float = 0.5
    miss_tolerance: float = 0.02
    miss_threshold: float = 2.0
    triage_budget: int = 12

    def __post_init__(self) -> None:
        for name in ("seed", "resamples", "min_samples", "triage_budget"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"{name} must be an integer")
        if self.seed < 0 or self.resamples < 100 or self.min_samples < 2:
            raise ValueError("seed >= 0, resamples >= 100 and min_samples >= 2 required")
        if self.triage_budget < 0:
            raise ValueError("triage_budget must be nonnegative")
        for name in ("ade_tolerance", "fde_tolerance", "miss_tolerance", "miss_threshold"):
            value = getattr(self, name)
            if isinstance(value, bool) or not np.isfinite(value) or value < 0:
                raise ValueError(f"{name} must be finite and nonnegative")
        if self.miss_threshold <= 0 or self.miss_tolerance > 1:
            raise ValueError("miss_threshold > 0 and miss_tolerance <= 1 required")


def evaluate(
    scenes: list[Scene],
    baseline: dict[str, np.ndarray],
    candidate: dict[str, np.ndarray],
    config: Config,
) -> dict:
    if not scenes:
        raise ValueError("no scenes")
    scenes = sorted(scenes, key=lambda s: s.scene_id)
    ids = {s.scene_id for s in scenes}
    if len(ids) != len(scenes) or set(baseline) != ids or set(candidate) != ids:
        raise ValueError("unique scene IDs and exact prediction coverage required")
    protocols = {(len(s.history), len(s.future), s.dt, s.source) for s in scenes}
    if len(protocols) != 1:
        raise ValueError(
            "mixed horizons, timesteps, history lengths or sources; evaluate separately"
        )
    rows, vectors = [], {}
    for scene in scenes:
        scores = {}
        for name, predictions in (("baseline", baseline), ("candidate", candidate)):
            prediction = points(predictions[scene.scene_id], name, 1)
            scores[name] = displacement(scene.future, prediction, config.miss_threshold)
        rows.append(
            {
                "scene_id": scene.scene_id,
                "slices": memberships(scene),
                **scores,
                "delta": {
                    key: scores["candidate"][key] - scores["baseline"][key]
                    for key in scores["baseline"]
                },
            }
        )
        vectors[scene.scene_id] = features(scene)[2]
    slices = []
    tolerances = {
        "ade_m": config.ade_tolerance,
        "fde_m": config.fde_tolerance,
        "miss_rate": config.miss_tolerance,
    }
    names = sorted({name for row in rows for name in row["slices"]})
    for name in names:
        group = [row for row in rows if name in row["slices"]]
        metrics = {}
        for metric, tolerance in tolerances.items():
            deltas = np.array([row["delta"][metric] for row in group])
            # Stable seed per metric/slice: adding another slice cannot change existing intervals.
            digest = hashlib.sha256(f"{config.seed}/{name}/{metric}".encode()).digest()
            interval = paired_interval(
                deltas, seed=int.from_bytes(digest[:8]), resamples=config.resamples
            )
            if len(group) < config.min_samples:
                status = "insufficient_data"
            elif interval[0] > tolerance:
                status = "regression"
            elif interval[1] <= tolerance:
                status = "within_tolerance"
            else:
                status = "inconclusive"
            metrics[metric] = {
                "baseline": float(np.mean([r["baseline"][metric] for r in group])),
                "candidate": float(np.mean([r["candidate"][metric] for r in group])),
                "delta": float(deltas.mean()),
                "ci95": interval,
                "tolerance": tolerance,
                "status": status,
            }
        slices.append({"name": name, "count": len(group), "metrics": metrics})
    statuses = [m["status"] for s in slices for m in s["metrics"].values()]
    gate = (
        "regression"
        if "regression" in statuses
        else (
            "within_tolerance" if all(s == "within_tolerance" for s in statuses) else "inconclusive"
        )
    )
    triage = select_triage(rows, vectors, config.triage_budget)
    chosen = {row["scene_id"] for row in triage}
    # Keep reports bounded while retaining at least one inspectable scene when no regression exists.
    chosen.update(s.scene_id for s in scenes[: max(1, 24 - len(chosen))])
    trajectories = [
        {
            **s.to_dict(),
            "baseline": baseline[s.scene_id].tolist(),
            "candidate": candidate[s.scene_id].tolist(),
        }
        for s in scenes
        if s.scene_id in chosen
    ]
    return {
        "schema_version": 1,
        "gate": gate,
        "config": asdict(config),
        "protocol": {
            "history_steps": len(scenes[0].history),
            "future_steps": len(scenes[0].future),
            "dt_seconds": scenes[0].dt,
            "source": scenes[0].source,
            "scenes": len(scenes),
            "modes": 1,
        },
        "slices": slices,
        "scenes": rows,
        "triage": triage,
        "trajectories": trajectories,
    }
