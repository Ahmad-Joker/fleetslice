"""Controlled harness fixture: injected forecast errors, explicitly not learned predictions."""

from pathlib import Path

import numpy as np

from fleetslice.schema import Scene, write_jsonl


def generate(path: Path, count: int = 200, seed: int = 42) -> None:
    if count < 20:
        raise ValueError("demo requires at least 20 scenes")
    rng = np.random.default_rng(seed)
    scenes, baseline, candidate = [], [], []
    for i in range(count):
        dt = 0.1
        t = np.arange(-19, 31) * dt
        speed = rng.uniform(4, 14)
        kind = i % 10
        if kind == 0:
            radius = speed / 0.4
            xy = np.column_stack((radius * np.sin(0.4 * t), radius * (1 - np.cos(0.4 * t))))
        elif kind == 1:
            xy = np.column_stack((speed * t + 0.75 * t**2, np.zeros_like(t)))
        else:
            xy = np.column_stack((speed * t, np.zeros_like(t)))
        xy += rng.uniform(-30, 30, 2)
        scene = Scene(
            f"synthetic-{i:05d}",
            xy[:20],
            xy[20:],
            dt,
            ["demo-east", "demo-west"][i % 2],
            "vehicle",
            "synthetic-injected-errors",
        )
        # Ground truth use here is deliberate fault injection, isolated from real reference models.
        base = scene.future + np.array([0, 0.9 + rng.uniform(-0.03, 0.03)])
        error = 1.8 if kind == 0 else 0.5 if kind == 1 else 0.2
        cand = scene.future + np.array([0, error + rng.uniform(-0.02, 0.02)])
        scenes.append(scene.to_dict())
        baseline.append({"scene_id": scene.scene_id, "prediction": base.tolist()})
        candidate.append({"scene_id": scene.scene_id, "prediction": cand.tolist()})
    path.mkdir(parents=True, exist_ok=False)
    write_jsonl(path / "scenes.jsonl", scenes)
    write_jsonl(path / "baseline.jsonl", baseline)
    write_jsonl(path / "candidate.jsonl", candidate)
