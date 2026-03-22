#!/usr/bin/env python3

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
PREPARE_SCRIPT = REPO_ROOT / "scripts" / "voice_digest_prepare.py"
TTS_SCRIPT = REPO_ROOT / "scripts" / "voice_digest_tts.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a spoken script artifact and MP3 for a digest in one run."
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        required=True,
        help="Source digest text file.",
    )
    parser.add_argument(
        "--script-output",
        type=Path,
        help="Optional spoken script output path. Defaults next to the MP3.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Target MP3 path.",
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
        help="Skip live synthesis and write the TTS dry-run note.",
    )
    return parser.parse_args()


def default_script_output(audio_output: Path) -> Path:
    return audio_output.with_suffix(".spoken.txt")


def run_step(command: list[str]) -> None:
    subprocess.run(command, check=True)


def main() -> int:
    args = parse_args()
    script_output = args.script_output or default_script_output(args.output)

    prepare_command = [
        sys.executable,
        str(PREPARE_SCRIPT),
        "--input",
        str(args.input),
        "--output",
        str(script_output),
    ]
    if args.intro:
        prepare_command.extend(["--intro", args.intro])
    if args.outro:
        prepare_command.extend(["--outro", args.outro])

    tts_command = [
        sys.executable,
        str(TTS_SCRIPT),
        "--input",
        str(script_output),
        "--output",
        str(args.output),
    ]
    if args.voice_id:
        tts_command.extend(["--voice-id", args.voice_id])
    if args.model_id:
        tts_command.extend(["--model-id", args.model_id])
    if args.dry_run:
        tts_command.append("--dry-run")

    run_step(prepare_command)
    run_step(tts_command)
    print(f"pipeline complete: script={script_output} audio={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
