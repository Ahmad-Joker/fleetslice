"""Predeclared descriptive slices based exclusively on observed history and metadata."""

import numpy as np

from fleetslice.schema import Scene


def features(scene: Scene) -> tuple[str, str, np.ndarray]:
    velocity = np.diff(scene.history, axis=0) / scene.dt
    speed = float(np.linalg.norm(velocity[-1]))
    speed_bin = "stopped" if speed < 0.5 else "fast" if speed >= 10 else "moving"
    headings = np.arctan2(velocity[:, 1], velocity[:, 0])
    moving = np.linalg.norm(velocity, axis=1) >= 0.5
    angles = np.unwrap(headings[moving])
    turn = float(abs(angles[-1] - angles[0])) if len(angles) > 1 else 0.0
    acceleration = float(np.linalg.norm(velocity[-1] - velocity[-2]) / scene.dt)
    behavior = (
        "turning"
        if turn >= np.deg2rad(20)
        else ("accelerating" if acceleration >= 1.0 else "steady")
    )
    vector = np.array([speed / 15, min(acceleration, 10) / 5, min(turn, np.pi) / np.pi])
    return speed_bin, behavior, vector


def memberships(scene: Scene) -> list[str]:
    speed, behavior, _ = features(scene)
    return [
        "all",
        f"city:{scene.city}",
        f"actor:{scene.actor_type}",
        f"speed:{speed}",
        f"behavior:{behavior}",
    ]


def select_triage(rows: list[dict], vectors: dict[str, np.ndarray], budget: int) -> list[dict]:
    """Greedy severity + novelty ranking; retrospective curation, not active learning."""
    pool = sorted(
        [r for r in rows if r["candidate"]["ade_m"] > r["baseline"]["ade_m"]],
        key=lambda r: r["scene_id"],
    )
    selected = []
    max_delta = max((r["delta"]["ade_m"] for r in pool), default=1.0)
    while pool and len(selected) < budget:

        def score(row: dict) -> float:
            novelty = min(
                (
                    float(np.linalg.norm(vectors[row["scene_id"]] - vectors[s["scene_id"]]))
                    for s in selected
                ),
                default=0.0,
            )
            return 0.8 * row["delta"]["ade_m"] / max_delta + 0.2 * min(novelty, 1.0)

        best = max(pool, key=score)
        selected.append({**best, "triage_score": score(best), "rank": len(selected) + 1})
        pool.remove(best)
    return selected
