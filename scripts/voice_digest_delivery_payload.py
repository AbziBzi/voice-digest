#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
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
    parser.add_argument(
        "--max-age-minutes",
        type=float,
        help=(
            "Optional freshness guard. Reject the latest-run handoff when its manifest timestamp "
            "is older than this many minutes."
        ),
    )
    return parser.parse_args()


def read_preview(path: Path, limit: int = 280) -> str:
    text = path.read_text(encoding="utf-8").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def parse_timestamp(value: object, label: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing {label}")
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"invalid {label}: {value!r}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def age_minutes_from(timestamp: datetime) -> float:
    return round((datetime.now(timezone.utc) - timestamp).total_seconds() / 60, 1)


def describe_selected_input(selected_input: str) -> dict[str, object]:
    selected_path = Path(selected_input)
    details: dict[str, object] = {
        "path": selected_input,
        "exists": selected_path.is_file(),
    }
    if not selected_path.is_file():
        return details

    stat = selected_path.stat()
    modified_at = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
    details.update(
        {
            "size_bytes": stat.st_size,
            "modified_at": modified_at.isoformat(),
            "age_minutes": age_minutes_from(modified_at),
        }
    )
    return details


def build_delivery_payload(
    state_path: Path,
    require_mode: str | None = None,
    max_age_minutes: float | None = None,
) -> dict[str, object]:
    validated = validate_latest_run(
        state_path,
        require_mode=require_mode,
        max_age_minutes=max_age_minutes,
    )
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
    run_timestamp = parse_timestamp(timestamp, "timestamp")

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
            "age_minutes": age_minutes_from(run_timestamp),
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
            "selected_input_details": describe_selected_input(selected_input),
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
        payload = build_delivery_payload(
            args.state_path,
            require_mode=args.require_mode,
            max_age_minutes=args.max_age_minutes,
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    write_output(payload, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
