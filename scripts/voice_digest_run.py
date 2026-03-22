#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
PIPELINE_SCRIPT = REPO_ROOT / "scripts" / "voice_digest_pipeline.py"
DEFAULT_RUNS_DIR = REPO_ROOT / "out" / "runs"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create one scheduler-friendly voice digest run bundle."
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        required=True,
        help="Source digest text file.",
    )
    parser.add_argument(
        "--runs-dir",
        type=Path,
        default=DEFAULT_RUNS_DIR,
        help="Base directory for dated run folders.",
    )
    parser.add_argument(
        "--run-id",
        help="Optional explicit run ID. Defaults to a local timestamp.",
    )
    parser.add_argument(
        "--intro",
        help="Optional intro override passed to the prepare step.",
    )
    parser.add_argument(
        "--outro",
        help="Optional outro override passed to the prepare step.",
    )
    parser.add_argument(
        "--voice-id",
        help="Optional ElevenLabs voice override passed to TTS.",
    )
    parser.add_argument(
        "--model-id",
        help="Optional ElevenLabs model override passed to TTS.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip live synthesis and write a dry-run note instead.",
    )
    return parser.parse_args()


def make_run_paths(runs_dir: Path, run_id: str | None) -> tuple[str, str, Path]:
    now = datetime.now().astimezone()
    date_dir = now.strftime("%Y-%m-%d")
    resolved_run_id = run_id or now.strftime("%Y%m%d-%H%M%S")
    run_dir = runs_dir / date_dir / resolved_run_id
    return resolved_run_id, now.isoformat(timespec="seconds"), run_dir


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def run_pipeline(command: list[str]) -> None:
    subprocess.run(command, check=True)


def build_manifest(
    *,
    run_id: str,
    timestamp: str,
    mode: str,
    source_input: Path,
    copied_input: Path,
    script_output: Path,
    audio_output: Path,
    dry_run_note: Path | None,
    manifest_path: Path,
    intro: str | None,
    outro: str | None,
    voice_id: str | None,
    model_id: str | None,
) -> dict[str, object]:
    return {
        "run_id": run_id,
        "timestamp": timestamp,
        "mode": mode,
        "inputs": {
            "source_digest": str(source_input),
            "copied_digest": str(copied_input),
            "intro_override": intro,
            "outro_override": outro,
            "voice_id_override": voice_id,
            "model_id_override": model_id,
        },
        "outputs": {
            "spoken_script": str(script_output),
            "audio_output": str(audio_output),
            "dry_run_note": str(dry_run_note) if dry_run_note else None,
            "manifest": str(manifest_path),
        },
    }


def main() -> int:
    args = parse_args()
    input_path = args.input.resolve()
    if not input_path.is_file():
        fail(f"input file does not exist: {args.input}")

    run_id, timestamp, run_dir = make_run_paths(args.runs_dir, args.run_id)
    if run_dir.exists():
        fail(f"run directory already exists: {run_dir}")

    run_dir.mkdir(parents=True, exist_ok=False)

    input_copy = run_dir / "digest.txt"
    script_output = run_dir / "spoken.txt"
    audio_output = run_dir / "digest.mp3"
    manifest_path = run_dir / "manifest.json"

    shutil.copyfile(input_path, input_copy)

    pipeline_command = [
        sys.executable,
        str(PIPELINE_SCRIPT),
        "--input",
        str(input_copy),
        "--script-output",
        str(script_output),
        "--output",
        str(audio_output),
    ]
    if args.intro:
        pipeline_command.extend(["--intro", args.intro])
    if args.outro:
        pipeline_command.extend(["--outro", args.outro])
    if args.voice_id:
        pipeline_command.extend(["--voice-id", args.voice_id])
    if args.model_id:
        pipeline_command.extend(["--model-id", args.model_id])
    if args.dry_run:
        pipeline_command.append("--dry-run")

    run_pipeline(pipeline_command)

    dry_run_note = audio_output.with_suffix(audio_output.suffix + ".dry-run.txt")
    manifest = build_manifest(
        run_id=run_id,
        timestamp=timestamp,
        mode="dry-run" if dry_run_note.exists() else "live",
        source_input=input_path,
        copied_input=input_copy,
        script_output=script_output,
        audio_output=audio_output,
        dry_run_note=dry_run_note if dry_run_note.exists() else None,
        manifest_path=manifest_path,
        intro=args.intro,
        outro=args.outro,
        voice_id=args.voice_id,
        model_id=args.model_id,
    )
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"run complete: {run_dir}")
    print(f"manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
