import numpy as np
import pytest

from fleetslice.av2 import convert
from fleetslice.schema import load_scenes

pd = pytest.importorskip("pandas")
pytest.importorskip("pyarrow")


def make_parquet(path, timesteps=110, observed=50):
    frame = pd.DataFrame(
        {
            "scenario_id": ["av2-scene"] * timesteps,
            "focal_track_id": ["actor"] * timesteps,
            "track_id": ["actor"] * timesteps,
            "timestep": np.arange(timesteps),
            "position_x": np.arange(timesteps) * 0.5 + 100,
            "position_y": np.full(timesteps, 20),
            "object_type": ["vehicle"] * timesteps,
            "observed": [i < observed for i in range(timesteps)],
            "city": ["PIT"] * timesteps,
        }
    )
    frame.to_parquet(path)


def test_real_format_focal_split_and_translation(tmp_path):
    make_parquet(tmp_path / "scenario_fixture.parquet")
    out = tmp_path / "converted.jsonl"
    assert convert(tmp_path, out) == {"accepted": 1, "skipped": [], "files_seen": 1}
    scene = load_scenes(out)[0]
    assert scene.history.shape == (50, 2)
    assert scene.future.shape == (60, 2)
    np.testing.assert_allclose(scene.history[-1], [0, 0])
    np.testing.assert_allclose(scene.future[0], [0.5, 0])
    assert scene.dt == 0.1


def test_unlabeled_test_scene_rejected(tmp_path):
    make_parquet(tmp_path / "scenario_fixture.parquet", timesteps=50)
    with pytest.raises(ValueError, match="no complete"):
        convert(tmp_path, tmp_path / "converted.jsonl")


def test_wrong_observation_boundary_rejected(tmp_path):
    make_parquet(tmp_path / "scenario_fixture.parquet", observed=49)
    with pytest.raises(ValueError, match="no complete"):
        convert(tmp_path, tmp_path / "converted.jsonl")
