#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent
DEFAULT_PROGRESS_PATH = REPO_ROOT / "VOICE_DIGEST_PROGRESS.md"
DEFAULT_STATE_PATH = REPO_ROOT / "out" / "latest_run.json"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from voice_digest_validate_latest import validate_latest_run


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Emit a compact checkpoint for overnight handoff: repo state, latest progress note, "
            "and latest-run validation when available."
        )
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root to inspect. Defaults to the current project root.",
    )
    parser.add_argument(
        "--progress-path",
        type=Path,
        default=DEFAULT_PROGRESS_PATH,
        help="Path to VOICE_DIGEST_PROGRESS.md.",
    )
    parser.add_argument(
        "--state-path",
        type=Path,
        default=DEFAULT_STATE_PATH,
        help="Path to out/latest_run.json for optional latest-run validation.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Render either human-readable text or JSON. Defaults to text.",
    )
    return parser.parse_args()


def git_output(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def get_repo_status(repo_root: Path) -> dict[str, object]:
    branch = git_output(repo_root, "branch", "--show-current")
    head = git_output(repo_root, "rev-parse", "HEAD")
    short_head = git_output(repo_root, "rev-parse", "--short", "HEAD")
    dirty_lines = git_output(repo_root, "status", "--short")
    dirty_entries = [line for line in dirty_lines.splitlines() if line.strip()]

    try:
        upstream = git_output(repo_root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    except subprocess.CalledProcessError:
        upstream = None

    ahead = 0
    behind = 0
    if upstream:
        counts = git_output(repo_root, "rev-list", "--left-right", "--count", f"{upstream}...HEAD")
        behind_str, ahead_str = counts.split()
        behind = int(behind_str)
        ahead = int(ahead_str)

    return {
        "branch": branch,
        "head": head,
        "short_head": short_head,
        "dirty": bool(dirty_entries),
        "dirty_entries": dirty_entries,
        "upstream": upstream,
        "ahead": ahead,
        "behind": behind,
    }


def extract_latest_progress_entry(progress_path: Path) -> list[str]:
    text = progress_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    current: list[str] = []
    capture = False

    for line in lines:
        if line.startswith("### "):
            if capture:
                break
            current = [line]
            capture = True
            continue
        if capture:
            current.append(line)

    entry = [line for line in current if line.strip()]
    if not entry:
        raise ValueError(f"no progress entries found in {progress_path}")

    return entry


def get_latest_run_summary(state_path: Path) -> dict[str, object] | None:
    if not state_path.is_file():
        return None

    validated = validate_latest_run(state_path)
    manifest = validated["manifest"]
    inputs = manifest.get("inputs", {})
    if not isinstance(inputs, dict):
        inputs = {}

    return {
        "mode": validated["mode"],
        "timestamp": manifest.get("timestamp"),
        "run_dir": str(validated["run_dir"]),
        "selected_input": validated["state"].get("selected_input"),
        "spoken_script": str(validated["spoken_script"]),
        "audio_output": str(validated["audio_output"]),
        "dry_run_note": str(validated["dry_run_note"]) if validated["dry_run_note"] else None,
        "source_digest": inputs.get("source_digest"),
    }


def build_checkpoint(repo_root: Path, progress_path: Path, state_path: Path) -> dict[str, object]:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(repo_root),
        "repo": get_repo_status(repo_root),
        "latest_progress_entry": extract_latest_progress_entry(progress_path),
        "latest_run": get_latest_run_summary(state_path),
    }


def render_text(checkpoint: dict[str, object]) -> str:
    repo = checkpoint["repo"]
    if not isinstance(repo, dict):
        raise ValueError("checkpoint missing repo object")

    lines = [
        f"checkpoint generated: {checkpoint['generated_at']}",
        f"repo: {checkpoint['repo_root']}",
        f"branch: {repo['branch']} @ {repo['short_head']}",
    ]

    upstream = repo.get("upstream")
    if upstream:
        lines.append(
            f"upstream: {upstream} (ahead {repo['ahead']}, behind {repo['behind']})"
        )
    else:
        lines.append("upstream: none")

    dirty_entries = repo.get("dirty_entries", [])
    if isinstance(dirty_entries, list) and dirty_entries:
        lines.append("working tree: dirty")
        lines.extend(f"  {entry}" for entry in dirty_entries)
    else:
        lines.append("working tree: clean")

    lines.append("latest progress entry:")
    progress_entry = checkpoint.get("latest_progress_entry", [])
    if isinstance(progress_entry, list):
        lines.extend(f"  {line}" for line in progress_entry)

    latest_run = checkpoint.get("latest_run")
    if latest_run is None:
        lines.append("latest run: none")
    elif isinstance(latest_run, dict):
        lines.append(
            f"latest run: {latest_run['mode']} @ {latest_run['timestamp']}"
        )
        lines.append(f"  selected input: {latest_run['selected_input']}")
        lines.append(f"  run dir: {latest_run['run_dir']}")
        lines.append(f"  spoken script: {latest_run['spoken_script']}")
        if latest_run["mode"] == "live":
            lines.append(f"  audio output: {latest_run['audio_output']}")
        else:
            lines.append(f"  dry-run note: {latest_run['dry_run_note']}")

    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    try:
        checkpoint = build_checkpoint(args.repo_root, args.progress_path, args.state_path)
    except (OSError, json.JSONDecodeError, subprocess.CalledProcessError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        sys.stdout.write(json.dumps(checkpoint, indent=2) + "\n")
    else:
        sys.stdout.write(render_text(checkpoint))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
