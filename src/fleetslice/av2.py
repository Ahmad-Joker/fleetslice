"""Local official AV2 parquet adapter; one focal actor, 50 observed + 60 future frames."""

from pathlib import Path

from fleetslice.schema import Scene, write_jsonl


def convert(input_dir: Path, output: Path) -> dict:
    import pandas as pd

    paths = sorted(input_dir.rglob("scenario_*.parquet"))
    if not paths:
        raise ValueError("no scenario_*.parquet found")
    scenes, skipped = [], []
    required = {
        "scene_id",
        "focal_track_id",
        "track_id",
        "timestep",
        "position_x",
        "position_y",
        "object_type",
        "observed",
        "city",
    } - {"scene_id"}
    required.add("scenario_id")
    for path in paths:
        frame = pd.read_parquet(path)
        if not required.issubset(frame.columns):
            raise ValueError(f"invalid AV2 columns in {path.name}")
        focal = str(frame["focal_track_id"].iloc[0])
        track = frame[frame["track_id"].astype(str) == focal].sort_values("timestep")
        if (
            len(track) != 110
            or track["timestep"].tolist() != list(range(110))
            or track["observed"].tolist() != [True] * 50 + [False] * 60
        ):
            skipped.append({"file": path.name, "reason": "requires 50 observed + 60 labeled steps"})
            continue
        positions = track[["position_x", "position_y"]].to_numpy(dtype=float)
        # Translation only; preserve the map frame and metric distances.
        positions -= positions[49]
        scene = Scene.from_dict(
            {
                "scene_id": str(track["scenario_id"].iloc[0]),
                "history": positions[:50].tolist(),
                "future": positions[50:].tolist(),
                "dt": 0.1,
                "city": str(track["city"].iloc[0]),
                "actor_type": str(track["object_type"].iloc[0]),
                "source": "argoverse2-motion-forecasting-local",
            }
        )
        scenes.append(scene.to_dict())
    if not scenes:
        raise ValueError("no complete labeled focal tracks; AV2 test inputs may lack future labels")
    if len({s["scene_id"] for s in scenes}) != len(scenes):
        raise ValueError("duplicate AV2 scenario IDs")
    if output.exists():
        raise ValueError("refusing to overwrite existing dataset")
    write_jsonl(output, scenes)
    return {"accepted": len(scenes), "skipped": skipped, "files_seen": len(paths)}
