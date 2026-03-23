#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TypedDict


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_STATE_PATH = REPO_ROOT / "out" / "latest_run.json"


class ValidatedLatestRun(TypedDict):
    state_path: Path
    state: dict[str, object]
    manifest_path: Path
    manifest: dict[str, object]
    mode: str
    run_dir: Path
    spoken_script: Path
    audio_output: Path
    dry_run_note: Path | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the stable latest-run handoff file and its referenced artifacts so "
            "downstream delivery can fail fast with a clear reason."
        )
    )
    parser.add_argument(
        "--state-path",
        type=Path,
        default=DEFAULT_STATE_PATH,
        help="Path to the latest-run JSON state file written by the scheduler job.",
    )
    parser.add_argument(
        "--require-mode",
        choices=["live", "dry-run"],
        help="Optional expected mode for the referenced run.",
    )
    return parser.parse_args()


def fail(message: str) -> int:
    print(f"invalid: {message}", file=sys.stderr)
    return 1


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def expect_file(path_value: object, label: str) -> Path:
    if not isinstance(path_value, str) or not path_value.strip():
        raise ValueError(f"missing {label}")
    path = Path(path_value)
    if not path.is_file():
        raise ValueError(f"missing file for {label}: {path}")
    return path


def expect_optional_file(path_value: object, label: str) -> Path | None:
    if path_value is None:
        return None
    return expect_file(path_value, label)


def validate_latest_run(state_path: Path, require_mode: str | None = None) -> ValidatedLatestRun:
    resolved_state_path = state_path.resolve()
    if not resolved_state_path.is_file():
        raise ValueError(f"state file does not exist: {state_path}")

    state = load_json(resolved_state_path)
    manifest_path = expect_file(state.get("manifest"), "manifest")
    spoken_script = expect_file(state.get("spoken_script"), "spoken_script")
    audio_output_value = state.get("audio_output")
    if not isinstance(audio_output_value, str) or not audio_output_value.strip():
        raise ValueError("missing audio_output")
    audio_output = Path(audio_output_value)
    dry_run_note = expect_optional_file(state.get("dry_run_note"), "dry_run_note")
    run_dir = state.get("run_dir")
    if not isinstance(run_dir, str) or not run_dir.strip():
        raise ValueError("missing run_dir")

    manifest = load_json(manifest_path)
    outputs = manifest.get("outputs")
    if not isinstance(outputs, dict):
        raise ValueError("manifest missing outputs object")

    manifest_run_dir = manifest_path.parent
    if Path(run_dir) != manifest_run_dir:
        raise ValueError(
            f"run_dir does not match manifest parent: {run_dir} != {manifest_run_dir}"
        )

    manifest_spoken = expect_file(outputs.get("spoken_script"), "manifest.outputs.spoken_script")
    manifest_audio_value = outputs.get("audio_output")
    if not isinstance(manifest_audio_value, str) or not manifest_audio_value.strip():
        raise ValueError("manifest missing outputs.audio_output")
    manifest_audio = Path(manifest_audio_value)
    manifest_dry_run = expect_optional_file(
        outputs.get("dry_run_note"), "manifest.outputs.dry_run_note"
    )

    if manifest_spoken != spoken_script:
        raise ValueError("state spoken_script does not match manifest")
    if manifest_audio != audio_output:
        raise ValueError("state audio_output does not match manifest")
    if manifest_dry_run != dry_run_note:
        raise ValueError("state dry_run_note does not match manifest")

    mode = manifest.get("mode")
    if mode not in {"live", "dry-run"}:
        raise ValueError(f"unexpected manifest mode: {mode!r}")
    state_mode = state.get("mode")
    if state_mode != mode:
        raise ValueError("state mode does not match manifest mode")
    if require_mode and mode != require_mode:
        raise ValueError(f"expected mode {require_mode!r}, got {mode!r}")

    if mode == "live":
        if not audio_output.is_file():
            raise ValueError(f"live mode requires audio file: {audio_output}")
        if dry_run_note is not None:
            raise ValueError("live mode should not expose a dry_run_note")
    else:
        if dry_run_note is None:
            raise ValueError("dry-run mode requires a dry_run_note")
        if audio_output.is_file():
            raise ValueError(
                f"dry-run mode should not have a synthesized audio file present: {audio_output}"
            )

    return {
        "state_path": resolved_state_path,
        "state": state,
        "manifest_path": manifest_path,
        "manifest": manifest,
        "mode": mode,
        "run_dir": manifest_run_dir,
        "spoken_script": spoken_script,
        "audio_output": audio_output,
        "dry_run_note": dry_run_note,
    }


def main() -> int:
    args = parse_args()
    try:
        validated = validate_latest_run(args.state_path, require_mode=args.require_mode)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return fail(str(exc))

    print(f"valid latest run: {validated['state_path']}")
    print(f"mode: {validated['mode']}")
    print(f"run dir: {validated['run_dir']}")
    print(f"spoken script: {validated['spoken_script']}")
    if validated["mode"] == "live":
        print(f"audio: {validated['audio_output']}")
    else:
        print(f"dry-run note: {validated['dry_run_note']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
