#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent
DEFAULT_STATE_PATH = REPO_ROOT / "out" / "latest_run.json"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from voice_digest_validate_latest import validate_latest_run


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read and validate the latest-run handoff, then emit a notifier-ready payload "
            "describing what should be delivered in live vs dry-run mode."
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
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output file. Defaults to stdout.",
    )
    return parser.parse_args()


def read_preview(path: Path, limit: int = 280) -> str:
    text = path.read_text(encoding="utf-8").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def build_delivery_payload(state_path: Path, require_mode: str | None = None) -> dict[str, object]:
    validated = validate_latest_run(state_path, require_mode=require_mode)
    state = validated["state"]
    manifest = validated["manifest"]
    inputs = manifest.get("inputs", {})
    if not isinstance(inputs, dict):
        raise ValueError("manifest missing inputs object")

    spoken_preview = read_preview(validated["spoken_script"])
    selected_input = state.get("selected_input")
    if not isinstance(selected_input, str) or not selected_input.strip():
        raise ValueError("missing selected_input")
    timestamp = state.get("timestamp")
    if not isinstance(timestamp, str) or not timestamp.strip():
        raise ValueError("missing timestamp")

    mode = validated["mode"]
    delivery_target = (
        str(validated["audio_output"]) if mode == "live" else str(validated["dry_run_note"])
    )
    delivery_kind = "audio" if mode == "live" else "dry-run-note"
    notifier_action = "send_audio" if mode == "live" else "send_text_fallback"

    return {
        "mode": mode,
        "notifier_action": notifier_action,
        "delivery_kind": delivery_kind,
        "delivery_target": delivery_target,
        "run": {
            "timestamp": timestamp,
            "run_dir": str(validated["run_dir"]),
            "state_path": str(validated["state_path"]),
            "manifest": str(validated["manifest_path"]),
            "selected_input": selected_input,
        },
        "artifacts": {
            "spoken_script": str(validated["spoken_script"]),
            "audio_output": str(validated["audio_output"]),
            "dry_run_note": str(validated["dry_run_note"]) if validated["dry_run_note"] else None,
        },
        "summary": {
            "source_digest": inputs.get("source_digest"),
            "spoken_preview": spoken_preview,
            "voice_id_override": inputs.get("voice_id_override"),
            "model_id_override": inputs.get("model_id_override"),
        },
    }


def write_output(payload: dict[str, object], output_path: Path | None) -> None:
    rendered = json.dumps(payload, indent=2) + "\n"
    if output_path is None:
        sys.stdout.write(rendered)
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    print(f"wrote {output_path}")


def main() -> int:
    args = parse_args()
    try:
        payload = build_delivery_payload(args.state_path, require_mode=args.require_mode)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    write_output(payload, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
