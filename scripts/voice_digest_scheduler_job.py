#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
FROM_LATEST_SCRIPT = REPO_ROOT / "scripts" / "voice_digest_from_latest.py"
DEFAULT_RUNS_DIR = REPO_ROOT / "out" / "runs"
DEFAULT_STATE_PATH = REPO_ROOT / "out" / "latest_run.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scheduler-friendly morning job: select the newest digest file, create a run bundle, "
            "and write a stable latest-run state file for downstream delivery."
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
    return parser.parse_args()


def clip_output(text: str, limit: int = 2000) -> str:
    stripped = text.strip()
    if len(stripped) <= limit:
        return stripped
    return stripped[: limit - 3].rstrip() + "..."


def run_from_latest(command: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        if exc.stdout:
            sys.stdout.write(exc.stdout)
        if exc.stderr:
            sys.stderr.write(exc.stderr)
        detail = clip_output(exc.stderr) or clip_output(exc.stdout)
        if detail:
            raise RuntimeError(f"latest-digest selection failed: {detail}") from exc
        raise RuntimeError(f"latest-digest selection failed with exit code {exc.returncode}") from exc


def extract_line(prefix: str, output: str) -> str:
    for line in output.splitlines():
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
    raise RuntimeError(f"missing expected output line: {prefix!r}")


def load_manifest(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_state(*, selected_input: str, run_dir: str, manifest_path: Path, state_path: Path) -> dict[str, object]:
    manifest = load_manifest(manifest_path)
    outputs = manifest.get("outputs", {})
    return {
        "selected_input": selected_input,
        "run_dir": run_dir,
        "manifest": str(manifest_path),
        "spoken_script": outputs.get("spoken_script"),
        "audio_output": outputs.get("audio_output"),
        "dry_run_note": outputs.get("dry_run_note"),
        "mode": manifest.get("mode"),
        "timestamp": manifest.get("timestamp"),
        "updated_by": str(Path(__file__).resolve()),
        "state_path": str(state_path),
    }


def main() -> int:
    args = parse_args()
    command = [
        sys.executable,
        str(FROM_LATEST_SCRIPT),
        "--input-dir",
        str(args.input_dir),
        "--glob",
        args.glob,
        "--runs-dir",
        str(args.runs_dir),
    ]
    if args.state_path:
        args.state_path.parent.mkdir(parents=True, exist_ok=True)
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

    result = run_from_latest(command)
    if result.stdout:
        sys.stdout.write(result.stdout)
    if result.stderr:
        sys.stderr.write(result.stderr)

    selected_input = extract_line("selected input: ", result.stdout)
    run_dir = extract_line("run complete: ", result.stdout)
    manifest_path = Path(extract_line("manifest: ", result.stdout))

    state = build_state(
        selected_input=selected_input,
        run_dir=run_dir,
        manifest_path=manifest_path,
        state_path=args.state_path,
    )
    args.state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    print(f"latest state: {args.state_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from None
