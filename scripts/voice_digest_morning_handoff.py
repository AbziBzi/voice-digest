#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent
DEFAULT_PROGRESS_PATH = REPO_ROOT / "VOICE_DIGEST_PROGRESS.md"
DEFAULT_STATE_PATH = REPO_ROOT / "out" / "latest_run.json"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from voice_digest_checkpoint import build_checkpoint
from voice_digest_delivery_payload import build_delivery_payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Emit a compact morning handoff that combines overnight repo checkpoint data "
            "with a delivery-ready summary when a validated latest-run handoff exists."
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
    parser.add_argument(
        "--max-age-minutes",
        type=float,
        help=(
            "Optional freshness guard. Reject the latest-run handoff when its manifest timestamp "
            "is older than this many minutes."
        ),
    )
    return parser.parse_args()


def build_handoff(
    repo_root: Path,
    progress_path: Path,
    state_path: Path,
    max_age_minutes: float | None = None,
) -> dict[str, object]:
    checkpoint = build_checkpoint(repo_root, progress_path, state_path)
    delivery: dict[str, object] | None = None
    if state_path.is_file():
        delivery = build_delivery_payload(state_path, max_age_minutes=max_age_minutes)
    return {
        "checkpoint": checkpoint,
        "delivery": delivery,
    }


def render_progress_line(progress_entry: list[str]) -> str:
    bullet_lines = [
        line.strip().lstrip("- ").strip()
        for line in progress_entry
        if line.strip().startswith("-")
    ]

    secondary_prefixes = (
        "verification passed",
        "verification:",
        "live repo check:",
        "learned:",
        "next step:",
    )

    for line in bullet_lines:
        if not line.lower().startswith(secondary_prefixes):
            return line

    for line in bullet_lines:
        if not line.lower().startswith("next step:"):
            return line
    if bullet_lines:
        return bullet_lines[0]
    if progress_entry:
        return progress_entry[-1].strip()
    return "No progress entry found."


def render_text(handoff: dict[str, object]) -> str:
    checkpoint = handoff["checkpoint"]
    if not isinstance(checkpoint, dict):
        raise ValueError("handoff missing checkpoint object")

    repo = checkpoint.get("repo")
    if not isinstance(repo, dict):
        raise ValueError("checkpoint missing repo object")

    progress_entry = checkpoint.get("latest_progress_entry")
    if not isinstance(progress_entry, list):
        raise ValueError("checkpoint missing latest progress entry")

    lines = [
        "Voice Digest Morning Handoff",
        f"- Generated: {checkpoint['generated_at']}",
        f"- Repo: {checkpoint['repo_root']}",
        f"- Branch/head: {repo['branch']} @ {repo['short_head']}",
    ]

    upstream = repo.get("upstream")
    if upstream:
        lines.append(
            f"- Sync: upstream {upstream}, ahead {repo['ahead']}, behind {repo['behind']}"
        )
    else:
        lines.append("- Sync: no upstream configured")

    dirty_entries = repo.get("dirty_entries")
    if isinstance(dirty_entries, list) and dirty_entries:
        lines.append("- Working tree: dirty")
        lines.extend(f"  - {entry}" for entry in dirty_entries)
    else:
        lines.append("- Working tree: clean")

    lines.append(f"- Latest progress: {render_progress_line(progress_entry)}")

    delivery = handoff.get("delivery")
    if delivery is None:
        lines.append("- Delivery readiness: no latest_run.json yet, so there is no current morning artifact to deliver")
        lines.append("- Next action: run the scheduler job to create and validate a fresh morning bundle")
        return "\n".join(lines) + "\n"

    if not isinstance(delivery, dict):
        raise ValueError("handoff delivery is not an object")

    summary = delivery.get("summary")
    run = delivery.get("run")
    artifacts = delivery.get("artifacts")
    if not isinstance(summary, dict) or not isinstance(run, dict) or not isinstance(artifacts, dict):
        raise ValueError("handoff delivery is missing required sections")

    lines.append(
        f"- Delivery readiness: {delivery['notifier_action']} ({delivery['delivery_kind']}, mode {delivery['mode']})"
    )
    lines.append(f"- Delivery target: {delivery['delivery_target']}")
    lines.append(f"- Selected input: {run['selected_input']}")

    run_age_minutes = run.get("age_minutes")
    if isinstance(run_age_minutes, (int, float)):
        lines.append(f"- Run age: {run_age_minutes:.1f} minutes")

    selected_input_details = summary.get("selected_input_details")
    if isinstance(selected_input_details, dict):
        modified_at = selected_input_details.get("modified_at")
        age_minutes = selected_input_details.get("age_minutes")
        size_bytes = selected_input_details.get("size_bytes")
        if modified_at:
            lines.append(f"- Selected input modified: {modified_at}")
        if isinstance(age_minutes, (int, float)):
            lines.append(f"- Selected input age: {age_minutes:.1f} minutes")
        if isinstance(size_bytes, int):
            lines.append(f"- Selected input size: {size_bytes} bytes")

    lines.append(f"- Spoken script: {artifacts['spoken_script']}")

    source_digest = summary.get("source_digest")
    if source_digest:
        lines.append(f"- Source digest: {source_digest}")

    spoken_preview = summary.get("spoken_preview")
    if spoken_preview:
        lines.append("- Spoken preview:")
        for preview_line in str(spoken_preview).splitlines():
            lines.append(f"  {preview_line}")

    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    try:
        handoff = build_handoff(
            args.repo_root,
            args.progress_path,
            args.state_path,
            max_age_minutes=args.max_age_minutes,
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        sys.stdout.write(json.dumps(handoff, indent=2) + "\n")
    else:
        sys.stdout.write(render_text(handoff))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
