#!/usr/bin/env python3

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEDULER_JOB_SCRIPT = REPO_ROOT / "scripts" / "voice_digest_scheduler_job.py"
MORNING_HANDOFF_SCRIPT = REPO_ROOT / "scripts" / "voice_digest_morning_handoff.py"
DELIVERY_PAYLOAD_SCRIPT = REPO_ROOT / "scripts" / "voice_digest_delivery_payload.py"
DEFAULT_RUNS_DIR = REPO_ROOT / "out" / "runs"
DEFAULT_STATE_PATH = REPO_ROOT / "out" / "latest_run.json"
DEFAULT_HANDOFF_TEXT_PATH = REPO_ROOT / "out" / "morning_handoff.txt"
DEFAULT_HANDOFF_JSON_PATH = REPO_ROOT / "out" / "morning_handoff.json"
DEFAULT_PAYLOAD_JSON_PATH = REPO_ROOT / "out" / "delivery_payload.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the full scheduler-friendly morning voice-digest flow: build the latest run bundle, "
            "validate it through downstream consumers, and write stable handoff/payload files for "
            "a notifier or cron job to consume."
        )
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        required=True,
        help="Directory containing digest text files dropped by the upstream digest generator.",
    )
    parser.add_argument(
        "--glob",
        default="*.txt",
        help="Glob pattern used to select candidate digest text files. Defaults to *.txt.",
    )
    parser.add_argument(
        "--runs-dir",
        type=Path,
        default=DEFAULT_RUNS_DIR,
        help="Base directory for dated run folders.",
    )
    parser.add_argument(
        "--state-path",
        type=Path,
        default=DEFAULT_STATE_PATH,
        help="Stable JSON file describing the newest successful run for downstream delivery.",
    )
    parser.add_argument(
        "--handoff-text-path",
        type=Path,
        default=DEFAULT_HANDOFF_TEXT_PATH,
        help="Stable text handoff output path for morning human-readable summaries.",
    )
    parser.add_argument(
        "--handoff-json-path",
        type=Path,
        default=DEFAULT_HANDOFF_JSON_PATH,
        help="Stable JSON handoff output path for automation or debugging.",
    )
    parser.add_argument(
        "--payload-json-path",
        type=Path,
        default=DEFAULT_PAYLOAD_JSON_PATH,
        help="Stable notifier-ready payload output path.",
    )
    parser.add_argument(
        "--run-id",
        help="Optional explicit run ID passed through to the run bundler.",
    )
    parser.add_argument(
        "--intro",
        help="Optional intro override passed through to the run bundler.",
    )
    parser.add_argument(
        "--outro",
        help="Optional outro override passed through to the run bundler.",
    )
    parser.add_argument(
        "--voice-id",
        help="Optional ElevenLabs voice override passed through to the run bundler.",
    )
    parser.add_argument(
        "--model-id",
        help="Optional ElevenLabs model override passed through to the run bundler.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip live synthesis and write the TTS dry-run note instead.",
    )
    parser.add_argument(
        "--max-age-minutes",
        type=float,
        help=(
            "Optional freshness guard passed through to morning handoff and delivery payload validation. "
            "Useful when downstream automation should reject stale latest-run artifacts."
        ),
    )
    return parser.parse_args()


def run_command(command: list[str], label: str) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        if exc.stdout:
            sys.stdout.write(exc.stdout)
        if exc.stderr:
            sys.stderr.write(exc.stderr)
        raise RuntimeError(f"{label} failed with exit code {exc.returncode}") from exc

    if result.stdout:
        sys.stdout.write(result.stdout)
    if result.stderr:
        sys.stderr.write(result.stderr)
    return result


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def main() -> int:
    args = parse_args()

    for path in (args.state_path, args.handoff_text_path, args.handoff_json_path, args.payload_json_path):
        ensure_parent(path)

    scheduler_command = [
        sys.executable,
        str(SCHEDULER_JOB_SCRIPT),
        "--input-dir",
        str(args.input_dir),
        "--glob",
        args.glob,
        "--runs-dir",
        str(args.runs_dir),
        "--state-path",
        str(args.state_path),
    ]
    if args.run_id:
        scheduler_command.extend(["--run-id", args.run_id])
    if args.intro:
        scheduler_command.extend(["--intro", args.intro])
    if args.outro:
        scheduler_command.extend(["--outro", args.outro])
    if args.voice_id:
        scheduler_command.extend(["--voice-id", args.voice_id])
    if args.model_id:
        scheduler_command.extend(["--model-id", args.model_id])
    if args.dry_run:
        scheduler_command.append("--dry-run")

    run_command(scheduler_command, "scheduler job")

    handoff_text_command = [
        sys.executable,
        str(MORNING_HANDOFF_SCRIPT),
        "--state-path",
        str(args.state_path),
        "--format",
        "text",
    ]
    if args.max_age_minutes is not None:
        handoff_text_command.extend(["--max-age-minutes", str(args.max_age_minutes)])
    handoff_json_command = [
        sys.executable,
        str(MORNING_HANDOFF_SCRIPT),
        "--state-path",
        str(args.state_path),
        "--format",
        "json",
    ]
    if args.max_age_minutes is not None:
        handoff_json_command.extend(["--max-age-minutes", str(args.max_age_minutes)])
    payload_command = [
        sys.executable,
        str(DELIVERY_PAYLOAD_SCRIPT),
        "--state-path",
        str(args.state_path),
        "--output",
        str(args.payload_json_path),
    ]
    if args.max_age_minutes is not None:
        payload_command.extend(["--max-age-minutes", str(args.max_age_minutes)])

    handoff_text = run_command(handoff_text_command, "morning handoff text")
    handoff_json = run_command(handoff_json_command, "morning handoff json")
    run_command(payload_command, "delivery payload")

    args.handoff_text_path.write_text(handoff_text.stdout, encoding="utf-8")
    args.handoff_json_path.write_text(handoff_json.stdout, encoding="utf-8")

    print(f"handoff text: {args.handoff_text_path}")
    print(f"handoff json: {args.handoff_json_path}")
    print(f"payload json: {args.payload_json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
