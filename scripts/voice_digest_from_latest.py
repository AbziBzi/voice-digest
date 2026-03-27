#!/usr/bin/env python3

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Sequence


REPO_ROOT = Path(__file__).resolve().parent.parent
RUN_SCRIPT = REPO_ROOT / "scripts" / "voice_digest_run.py"
DEFAULT_INPUT_DIR = REPO_ROOT / "incoming_digests"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Find the newest digest text file and create a voice digest run bundle."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        required=True,
        help="Directory containing candidate digest text files.",
    )
    parser.add_argument(
        "--glob",
        default="*.txt",
        help="Glob pattern to search within --input-dir. Defaults to *.txt.",
    )
    parser.add_argument(
        "--runs-dir",
        type=Path,
        help="Optional override passed through to voice_digest_run.py.",
    )
    parser.add_argument(
        "--run-id",
        help="Optional explicit run ID passed through to voice_digest_run.py.",
    )
    parser.add_argument(
        "--intro",
        help="Optional intro override passed through to voice_digest_run.py.",
    )
    parser.add_argument(
        "--outro",
        help="Optional outro override passed through to voice_digest_run.py.",
    )
    parser.add_argument(
        "--voice-id",
        help="Optional ElevenLabs voice override passed through to voice_digest_run.py.",
    )
    parser.add_argument(
        "--model-id",
        help="Optional ElevenLabs model override passed through to voice_digest_run.py.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip live synthesis and write a dry-run note instead.",
    )
    return parser.parse_args()


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def format_input_dir_hint(input_dir: Path) -> str:
    resolved = input_dir.resolve()
    if resolved == DEFAULT_INPUT_DIR:
        return (
            f"default drop directory expected at {input_dir}. "
            "Create it or drop digest *.txt files there, or pass --input-dir to point at the real upstream source."
        )
    return f"pass --input-dir to point at the real upstream source directory: {input_dir}"


def newest_file(paths: Sequence[Path]) -> Path:
    if not paths:
        fail("no matching digest files found")

    return max(paths, key=lambda path: (path.stat().st_mtime_ns, str(path)))


def main() -> int:
    args = parse_args()
    input_dir = args.input_dir.resolve()
    if not input_dir.is_dir():
        fail(f"input directory does not exist: {args.input_dir} ({format_input_dir_hint(args.input_dir)})")

    candidates = sorted(path for path in input_dir.glob(args.glob) if path.is_file())
    if not candidates:
        fail(
            f"no matching digest files found in {input_dir} for glob {args.glob!r} "
            f"({format_input_dir_hint(args.input_dir)})"
        )
    selected = newest_file(candidates)

    command = [
        sys.executable,
        str(RUN_SCRIPT),
        "--input",
        str(selected),
    ]
    if args.runs_dir:
        command.extend(["--runs-dir", str(args.runs_dir)])
    if args.run_id:
        command.extend(["--run-id", args.run_id])
    if args.intro:
        command.extend(["--intro", args.intro])
    if args.outro:
        command.extend(["--outro", args.outro])
    if args.voice_id:
        command.extend(["--voice-id", args.voice_id])
    if args.model_id:
        command.extend(["--model-id", args.model_id])
    if args.dry_run:
        command.append("--dry-run")

    print(f"selected input: {selected}")
    subprocess.run(command, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
