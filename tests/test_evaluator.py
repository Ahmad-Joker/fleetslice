import json

import numpy as np
import pytest

from fleetslice.artifacts import sha256, write_bundle
from fleetslice.cli import main
from fleetslice.demo import generate
from fleetslice.engine import Config, evaluate
from fleetslice.metrics import displacement, paired_interval
from fleetslice.models import forecast
from fleetslice.schema import Scene, load_predictions, load_scenes, write_jsonl
from fleetslice.slices import memberships, select_triage


def scene(i=0, offset=0):
    return Scene.from_dict(
        {
            "scene_id": f"scene-{i}",
            "history": [[offset, 0], [offset + 1, 0], [offset + 2, 0]],
            "future": [[offset + 3, 0], [offset + 4, 0]],
            "dt": 1.0,
            "city": "test",
            "actor_type": "vehicle",
            "source": "test",
        }
    )


@pytest.fixture
def fixture(tmp_path):
    path = tmp_path / "fixture"
    generate(path)
    scenes = load_scenes(path / "scenes.jsonl")
    return (
        path,
        scenes,
        load_predictions(path / "baseline.jsonl", scenes),
        load_predictions(path / "candidate.jsonl", scenes),
    )


def test_analytical_displacement():
    metrics = displacement(np.zeros((2, 2)), np.array([[3, 4], [0, 2]]), 2)
    assert metrics == {"ade_m": 3.5, "fde_m": 2.0, "miss_rate": 0.0}


def test_miss_threshold_is_strict():
    assert displacement(np.zeros((1, 2)), np.array([[2.001, 0]]), 2)["miss_rate"] == 1


def test_shape_mismatch_rejected():
    with pytest.raises(ValueError, match="shapes"):
        displacement(np.zeros((2, 2)), np.zeros((1, 2)), 2)


def test_bootstrap_known_constant_delta():
    assert paired_interval(np.full(20, 2.5), seed=1, resamples=200) == [2.5, 2.5]


def test_bootstrap_is_reproducible():
    data = np.arange(20.0)
    assert paired_interval(data, seed=42, resamples=200) == paired_interval(
        data, seed=42, resamples=200
    )


def test_global_improvement_cannot_hide_turning_regression(fixture):
    _, scenes, baseline, candidate = fixture
    report = evaluate(scenes, baseline, candidate, Config(resamples=200))
    overall = next(s for s in report["slices"] if s["name"] == "all")
    turning = next(s for s in report["slices"] if s["name"] == "behavior:turning")
    assert overall["metrics"]["ade_m"]["delta"] < 0
    assert all(m["status"] == "within_tolerance" for m in overall["metrics"].values())
    assert turning["count"] == 20
    assert turning["metrics"]["ade_m"]["status"] == "regression"
    assert report["gate"] == "regression"
    assert len(report["triage"]) == 12
    assert all(row["delta"]["ade_m"] > 0 for row in report["triage"])


def test_input_order_does_not_change_results(fixture):
    _, scenes, baseline, candidate = fixture
    conf = Config(resamples=100)
    assert evaluate(scenes, baseline, candidate, conf) == evaluate(
        scenes[::-1], baseline, candidate, conf
    )


def test_equal_predictions_pass_with_sufficient_coverage():
    scenes = [scene(i) for i in range(20)]
    preds = {s.scene_id: s.future for s in scenes}
    report = evaluate(scenes, preds, preds, Config(resamples=100))
    assert report["gate"] == "within_tolerance"
    assert report["triage"] == []


def test_sparse_data_never_passes():
    s = scene()
    report = evaluate([s], {s.scene_id: s.future}, {s.scene_id: s.future}, Config(resamples=100))
    assert report["gate"] == "inconclusive"
    assert all(
        m["status"] == "insufficient_data"
        for group in report["slices"]
        for m in group["metrics"].values()
    )


def test_uncertain_delta_does_not_pass():
    scenes = [scene(i) for i in range(20)]
    base = {s.scene_id: s.future for s in scenes}
    candidate = {s.scene_id: s.future + (0.0 if i < 10 else 0.4) for i, s in enumerate(scenes)}
    report = evaluate(scenes, base, candidate, Config(resamples=500))
    assert (
        next(s for s in report["slices"] if s["name"] == "all")["metrics"]["ade_m"]["status"]
        == "inconclusive"
    )


def test_predictions_require_exact_pairing():
    s = scene()
    with pytest.raises(ValueError, match="exact prediction coverage"):
        evaluate([s], {}, {s.scene_id: s.future}, Config())


def test_mixed_protocol_rejected():
    s, other = scene(), scene(1)
    other = Scene.from_dict({**other.to_dict(), "dt": 0.5})
    preds = {v.scene_id: v.future for v in [s, other]}
    with pytest.raises(ValueError, match="mixed horizons"):
        evaluate([s, other], preds, preds, Config())


def test_translation_preserves_metrics_and_slices():
    a, b = scene(), scene(offset=1000)
    pa = forecast(a.history, 2, a.dt, "cv")
    pb = forecast(b.history, 2, b.dt, "cv")
    assert displacement(a.future, pa, 2) == displacement(b.future, pb, 2)
    assert memberships(a) == memberships(b)


def test_future_does_not_affect_slices():
    a = scene()
    b = Scene.from_dict({**a.to_dict(), "future": [[1000, 1000], [-1000, -1000]]})
    assert memberships(a) == memberships(b)


def test_constant_velocity_exact_forecast():
    s = scene()
    np.testing.assert_allclose(forecast(s.history, 2, 1, "cv"), s.future)


def test_constant_acceleration_exact_forecast():
    # x(t)=0.5*t^2, t=0,1,2; next positions t=3,4.
    np.testing.assert_allclose(
        forecast(np.array([[0, 0], [0.5, 0], [2, 0]]), 2, 1, "ca"), [[4.5, 0], [8, 0]]
    )


@pytest.mark.parametrize(
    "change",
    [
        {"dt": 0},
        {"dt": -1},
        {"dt": float("nan")},
        {"dt": True},
        {"history": [[0, 0]]},
        {"history": [[0, 0, 1]] * 3},
        {"future": [[float("inf"), 0]]},
        {"scene_id": ""},
        {"city": None},
        {"future": []},
    ],
)
def test_invalid_scenes_rejected(change):
    with pytest.raises(ValueError):
        Scene.from_dict({**scene().to_dict(), **change})


@pytest.mark.parametrize(
    "change",
    [
        {"resamples": 1},
        {"min_samples": 1},
        {"ade_tolerance": -1},
        {"miss_threshold": 0},
        {"miss_tolerance": 2},
        {"fde_tolerance": float("nan")},
        {"seed": -1},
        {"triage_budget": -1},
        {"seed": True},
    ],
)
def test_invalid_configuration_rejected(change):
    with pytest.raises(ValueError):
        Config(**change)


def test_duplicate_dataset_rejected(tmp_path):
    data = tmp_path / "data.jsonl"
    write_jsonl(data, [scene().to_dict()] * 2)
    with pytest.raises(ValueError, match="duplicate"):
        load_scenes(data)


@pytest.mark.parametrize("problem", ["duplicate", "missing", "extra", "horizon", "multimode"])
def test_prediction_contract(tmp_path, problem):
    data = tmp_path / "predictions.jsonl"
    s = scene()
    row = {"scene_id": s.scene_id, "prediction": s.future.tolist()}
    rows = [row]
    if problem == "duplicate":
        rows *= 2
    elif problem == "missing":
        rows = [{**row, "scene_id": "wrong"}]
    elif problem == "extra":
        rows.append({**row, "scene_id": "extra"})
    elif problem == "horizon":
        rows[0] = {**row, "prediction": [[0, 0]]}
    else:
        rows[0] = {**row, "prediction": [s.future.tolist(), s.future.tolist()]}
    write_jsonl(data, rows)
    with pytest.raises(ValueError):
        load_predictions(data, [s])


def test_empty_and_malformed_json(tmp_path):
    data = tmp_path / "input.jsonl"
    data.write_text("\n")
    with pytest.raises(ValueError, match="no records"):
        load_scenes(data)
    data.write_text("{broken")
    with pytest.raises(ValueError, match="input.jsonl:1"):
        load_scenes(data)


def test_bundle_hashes_immutability_and_html_escape(tmp_path, fixture):
    path, scenes, baseline, candidate = fixture
    report = evaluate(scenes, baseline, candidate, Config(resamples=100))
    out = tmp_path / "report"
    labels = {"baseline": "</script><script>alert(1)</script>", "candidate": "candidate"}
    write_bundle(report, out, {"dataset": path / "scenes.jsonl"}, labels)
    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["inputs"]["dataset"]["sha256"] == sha256(path / "scenes.jsonl")
    for filename, digest in manifest["artifacts"].items():
        assert sha256(out / filename) == digest
    assert labels["baseline"] not in (out / "report.html").read_text()
    with pytest.raises(ValueError, match="already exists"):
        write_bundle(report, out, {}, labels)


def test_cli_expected_failure_and_validation_exit(tmp_path, fixture):
    path, *_ = fixture
    args = [
        "evaluate",
        "--data",
        str(path / "scenes.jsonl"),
        "--baseline",
        str(path / "baseline.jsonl"),
        "--candidate",
        str(path / "candidate.jsonl"),
        "--out",
        str(tmp_path / "report"),
        "--resamples",
        "100",
    ]
    assert main(args) == 1
    assert main(args) == 3  # immutable output: no silent overwrite
    assert (
        main(
            [
                "predict",
                "--data",
                str(path / "scenes.jsonl"),
                "--model",
                "cv",
                "--out",
                str(tmp_path / "pred.jsonl"),
            ]
        )
        == 0
    )


def test_triage_budget_and_stable_ties():
    rows = [
        {
            "scene_id": str(i),
            "baseline": {"ade_m": 0},
            "candidate": {"ade_m": 1},
            "delta": {"ade_m": 1},
        }
        for i in range(5)
    ]
    vectors = {r["scene_id"]: np.zeros(3) for r in rows}
    assert select_triage(rows, vectors, 0) == []
    assert [r["scene_id"] for r in select_triage(rows[::-1], vectors, 2)] == ["0", "1"]
