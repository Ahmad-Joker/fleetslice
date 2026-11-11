#!/usr/bin/env python3
"""Create a dedicated repository, push a feature branch, and open an unmerged PR.

Requires GitHub CLI authentication on the machine running this script.
Dry run by default. Never writes to an existing remote repository.
"""

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path


def run(*args: str, cwd: Path | None = None) -> str:
    return subprocess.run(
        args, cwd=cwd, check=True, text=True, stdout=subprocess.PIPE
    ).stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner", default="Ahmad-Joker")
    parser.add_argument("--name", default="fleetslice")
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    if any(
        not value
        or any(
            c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
            for c in value
        )
        for value in (args.owner, args.name)
    ):
        parser.error("owner and name may contain only letters, numbers, hyphens and underscores")
    repo = f"{args.owner}/{args.name}"
    print(f"Plan: create public {repo}; main bootstrap; feat/fleetslice-mvp; open PR; no merge.")
    if not args.publish:
        print("Dry run only. Add --publish after gh auth login to execute.")
        return
    if not shutil.which("gh") or not shutil.which("git"):
        parser.error("install Git and the official GitHub CLI first")
    login = run("gh", "api", "user", "--jq", ".login")
    if login.lower() != args.owner.lower():
        parser.error(f"signed in as {login}; expected {args.owner}")
    check = subprocess.run(["gh", "repo", "view", repo], capture_output=True)
    if check.returncode == 0:
        parser.error("repository already exists; choose a new unique --name")
    # Auth is verified above; repo creation still rejects conflicts and permission failures.
    source = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="fleetslice-publish-") as tmp:
        staging = Path(tmp)
        run("git", "init", "--initial-branch=main", cwd=staging)
        run("git", "config", "user.name", "Ahmad Essam Abdelaziz", cwd=staging)
        run("git", "config", "user.email", f"{login}@users.noreply.github.com", cwd=staging)
        (staging / "README.md").write_text(
            "# FleetSlice\n\nImplementation is proposed in a feature PR.\n"
        )
        shutil.copy2(source / "LICENSE", staging)
        run("git", "add", "README.md", "LICENSE", cwd=staging)
        run("git", "commit", "-m", "Initialize FleetSlice repository", cwd=staging)
        run(
            "gh",
            "repo",
            "create",
            repo,
            "--public",
            "--source",
            str(staging),
            "--remote",
            "origin",
            "--push",
            "--description",
            "Motion forecasting regression tests, paired bootstrap gates and failure triage",
        )
        run("git", "switch", "-c", "feat/fleetslice-mvp", cwd=staging)
        # Include source and reports; exclude datasets and local caches.
        ignored = shutil.ignore_patterns(
            ".git",
            ".venv",
            "__pycache__",
            ".pytest_cache",
            ".ruff_cache",
            "*.egg-info",
            "build",
            "dist",
            "data",
            "runs",
            "*.pyc",
        )
        shutil.copytree(source, staging, dirs_exist_ok=True, ignore=ignored)
        run("git", "add", ".", cwd=staging)
        run(
            "git",
            "commit",
            "-m",
            "Build paired motion forecast evaluator and regression workbench",
            cwd=staging,
        )
        run("git", "push", "-u", "origin", "feat/fleetslice-mvp", cwd=staging)
        body = staging / "docs" / "PULL_REQUEST.md"
        url = run(
            "gh",
            "pr",
            "create",
            "--repo",
            repo,
            "--base",
            "main",
            "--head",
            "feat/fleetslice-mvp",
            "--title",
            "Add FleetSlice motion forecast regression workbench",
            "--body-file",
            str(body),
            cwd=staging,
        )
        print(url)


if __name__ == "__main__":
    main()
