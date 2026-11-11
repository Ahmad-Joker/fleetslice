"""Atomic, immutable output bundles with input and output SHA-256 provenance."""

import csv
import hashlib
import json
import platform
import shutil
import tempfile
from importlib.resources import files
from pathlib import Path

import numpy as np

from fleetslice import __version__
from fleetslice.schema import write_jsonl


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def summary(report: dict) -> str:
    overall = next(s for s in report["slices"] if s["name"] == "all")
    text = [
        "# FleetSlice evaluation",
        "",
        f"Gate: **{report['gate']}**",
        "",
        f"Source: {report['protocol']['source']}. Scenes: {report['protocol']['scenes']}.",
        "",
        "Positive delta means the candidate is worse. Units: metres; miss rate is a fraction.",
        "",
        "| Metric | Baseline | Candidate | Delta | 95% interval | Status |",
        "|---|---:|---:|---:|---|---|",
    ]
    for name, m in overall["metrics"].items():
        text.append(
            f"| {name} | {m['baseline']:.4f} | {m['candidate']:.4f} | "
            f"{m['delta']:+.4f} | [{m['ci95'][0]:.4f}, {m['ci95'][1]:.4f}] | "
            f"{m['status']} |"
        )
    text.extend(["", "## Flagged slices", ""])
    for group in report["slices"]:
        flagged = [name for name, m in group["metrics"].items() if m["status"] == "regression"]
        if flagged:
            text.append(f"- {group['name']} (n={group['count']}): {', '.join(flagged)}")
    text.extend(
        [
            "",
            "## Interpretation",
            "",
            "Open-loop, unimodal displacement evaluation only. This is not a vehicle safety "
            "certification, collision evaluation, closed-loop simulator, or leaderboard result.",
            "Intervals are exploratory per-comparison intervals without multiplicity correction. "
            "Sparse or ambiguous slices make the overall decision inconclusive unless a regression "
            "is detected. No absence-of-regression claim follows from inconclusive results.",
            "",
        ]
    )
    return "\n".join(text)


def write_bundle(
    report: dict, output: Path, inputs: dict[str, Path], labels: dict[str, str]
) -> None:
    if output.exists():
        raise ValueError(f"output already exists: {output}; choose a new run directory")
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".fleetslice-", dir=output.parent))
    try:
        report = {**report, "labels": labels}
        (staging / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
        template = files("fleetslice").joinpath("report_template.html").read_text(encoding="utf-8")
        encoded = json.dumps(report, allow_nan=False).replace("<", "\\u003c")
        (staging / "report.html").write_text(
            template.replace("__REPORT_JSON__", encoded), encoding="utf-8"
        )
        (staging / "summary.md").write_text(summary(report), encoding="utf-8")
        write_jsonl(staging / "triage.jsonl", report["triage"])
        with (staging / "metrics.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream, lineterminator="\n")
            writer.writerow(
                [
                    "slice",
                    "n",
                    "metric",
                    "baseline",
                    "candidate",
                    "delta",
                    "ci95_low",
                    "ci95_high",
                    "tolerance",
                    "status",
                ]
            )
            for group in report["slices"]:
                for metric, m in group["metrics"].items():
                    writer.writerow(
                        [
                            group["name"],
                            group["count"],
                            metric,
                            m["baseline"],
                            m["candidate"],
                            m["delta"],
                            *m["ci95"],
                            m["tolerance"],
                            m["status"],
                        ]
                    )
        manifest = {
            "fleetslice_version": __version__,
            "python": platform.python_version(),
            "numpy": np.__version__,
            "config": report["config"],
            "labels": labels,
            "inputs": {
                name: {"name": path.name, "sha256": sha256(path)}
                for name, path in sorted(inputs.items())
            },
            "artifacts": {path.name: sha256(path) for path in sorted(staging.iterdir())},
        }
        (staging / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        staging.rename(output)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
