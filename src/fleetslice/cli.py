"""CLI exit codes: 0 within tolerance, 1 regression, 2 inconclusive, 3 invalid input."""

import argparse
import json
import sys
from pathlib import Path

from fleetslice.artifacts import write_bundle
from fleetslice.demo import generate
from fleetslice.engine import Config, evaluate
from fleetslice.models import forecast
from fleetslice.schema import load_predictions, load_scenes, write_jsonl


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="FleetSlice motion forecast regression testing")
    commands = parser.add_subparsers(dest="command", required=True)
    demo = commands.add_parser("demo", help="create controlled synthetic fault-injection fixture")
    demo.add_argument("--out", type=Path, required=True)
    demo.add_argument("--count", type=int, default=200)
    demo.add_argument("--seed", type=int, default=42)
    predict = commands.add_parser("predict", help="run a history-only kinematic reference model")
    predict.add_argument("--data", type=Path, required=True)
    predict.add_argument("--model", choices=["cv", "ca"], required=True)
    predict.add_argument("--out", type=Path, required=True)
    av2 = commands.add_parser("import-av2", help="convert local labeled AV2 focal tracks")
    av2.add_argument("--input", type=Path, required=True)
    av2.add_argument("--out", type=Path, required=True)
    run = commands.add_parser(
        "evaluate", help="compare exactly paired baseline/candidate forecasts"
    )
    run.add_argument("--data", type=Path, required=True)
    run.add_argument("--baseline", type=Path, required=True)
    run.add_argument("--candidate", type=Path, required=True)
    run.add_argument("--out", type=Path, required=True)
    run.add_argument("--baseline-label", default="baseline")
    run.add_argument("--candidate-label", default="candidate")
    run.add_argument("--seed", type=int, default=42)
    run.add_argument("--resamples", type=int, default=2000)
    run.add_argument("--min-samples", type=int, default=10)
    run.add_argument("--ade-tolerance", type=float, default=0.2)
    run.add_argument("--fde-tolerance", type=float, default=0.5)
    run.add_argument("--miss-tolerance", type=float, default=0.02)
    run.add_argument("--miss-threshold", type=float, default=2.0)
    run.add_argument("--triage-budget", type=int, default=12)
    args = parser.parse_args(argv)
    try:
        if args.command == "demo":
            generate(args.out, args.count, args.seed)
        elif args.command == "import-av2":
            from fleetslice.av2 import convert

            print(json.dumps(convert(args.input, args.out)))
        elif args.command == "predict":
            if args.out.exists():
                raise ValueError("refusing to overwrite predictions")
            scenes = load_scenes(args.data)
            write_jsonl(
                args.out,
                [
                    {
                        "scene_id": s.scene_id,
                        "prediction": forecast(s.history, len(s.future), s.dt, args.model).tolist(),
                    }
                    for s in scenes
                ],
            )
        else:
            config = Config(**{key: getattr(args, key) for key in Config.__dataclass_fields__})
            scenes = load_scenes(args.data)
            report = evaluate(
                scenes,
                load_predictions(args.baseline, scenes),
                load_predictions(args.candidate, scenes),
                config,
            )
            write_bundle(
                report,
                args.out,
                {"dataset": args.data, "baseline": args.baseline, "candidate": args.candidate},
                {"baseline": args.baseline_label, "candidate": args.candidate_label},
            )
            print(
                json.dumps(
                    {
                        "gate": report["gate"],
                        "scenes": len(scenes),
                        "report": str(args.out / "report.html"),
                    }
                )
            )
            return {"within_tolerance": 0, "regression": 1, "inconclusive": 2}[report["gate"]]
        return 0
    except (ValueError, OSError, ImportError, KeyError, TypeError) as exc:
        print(f"fleetslice: {exc}", file=sys.stderr)
        return 3
