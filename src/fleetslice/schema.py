"""Strict JSONL contracts. All coordinates are XY metres in one fixed scene frame."""

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np


def points(value: object, name: str, minimum: int) -> np.ndarray:
    try:
        array = np.asarray(value, dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name}: expected numeric XY points") from exc
    if array.ndim != 2 or array.shape[1] != 2 or len(array) < minimum:
        raise ValueError(f"{name}: expected shape (T, 2), T >= {minimum}")
    if not np.isfinite(array).all():
        raise ValueError(f"{name}: all coordinates must be finite")
    return array


def label(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 200:
        raise ValueError(f"{name}: expected nonempty string up to 200 characters")
    return value


@dataclass(frozen=True)
class Scene:
    scene_id: str
    history: np.ndarray
    future: np.ndarray
    dt: float
    city: str
    actor_type: str
    source: str

    @classmethod
    def from_dict(cls, data: dict) -> "Scene":
        required = {"scene_id", "history", "future", "dt", "city", "actor_type", "source"}
        if not isinstance(data, dict) or set(data) != required:
            raise ValueError(f"scene must contain exactly {sorted(required)}")
        dt = data["dt"]
        if isinstance(dt, bool) or not isinstance(dt, (int, float)):
            raise ValueError("dt must be a finite positive number in seconds")
        if not np.isfinite(dt) or dt <= 0:
            raise ValueError("dt must be a finite positive number in seconds")
        return cls(
            label(data["scene_id"], "scene_id"),
            points(data["history"], "history", 3),
            points(data["future"], "future", 1),
            float(dt),
            label(data["city"], "city"),
            label(data["actor_type"], "actor_type"),
            label(data["source"], "source"),
        )

    def to_dict(self) -> dict:
        return {
            "scene_id": self.scene_id,
            "history": self.history.tolist(),
            "future": self.future.tolist(),
            "dt": self.dt,
            "city": self.city,
            "actor_type": self.actor_type,
            "source": self.source,
        }


def read_jsonl(path: Path) -> list[dict]:
    records = []
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                if not isinstance(record, dict):
                    raise ValueError("record must be an object")
            except ValueError as exc:
                raise ValueError(f"{path.name}:{line_number}: {exc}") from exc
            records.append(record)
    if not records:
        raise ValueError(f"{path.name}: no records")
    return records


def load_scenes(path: Path) -> list[Scene]:
    scenes = [Scene.from_dict(row) for row in read_jsonl(path)]
    ids = [s.scene_id for s in scenes]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate scene_id; one focal actor per independent scene is required")
    return sorted(scenes, key=lambda s: s.scene_id)


def load_predictions(path: Path, scenes: list[Scene]) -> dict[str, np.ndarray]:
    predictions = {}
    for row in read_jsonl(path):
        if set(row) != {"scene_id", "prediction"}:
            raise ValueError("prediction record must contain scene_id and prediction only")
        scene_id = label(row["scene_id"], "scene_id")
        if scene_id in predictions:
            raise ValueError(f"duplicate prediction: {scene_id}")
        predictions[scene_id] = points(row["prediction"], "prediction", 1)
    expected = {s.scene_id for s in scenes}
    if set(predictions) != expected:
        raise ValueError("prediction scene IDs must exactly match dataset IDs (no silent drops)")
    for scene in scenes:
        if predictions[scene.scene_id].shape != scene.future.shape:
            raise ValueError(f"prediction horizon mismatch: {scene.scene_id}")
    return predictions


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, allow_nan=False, sort_keys=True) + "\n")
