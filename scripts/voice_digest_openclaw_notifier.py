#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PAYLOAD_PATH = REPO_ROOT / "out" / "delivery_payload.json"
DEFAULT_HANDOFF_TEXT_PATH = REPO_ROOT / "out" / "morning_handoff.txt"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read the stable voice-digest morning payload/handoff artifacts and bridge them into "
            "OpenClaw message send calls for Signal or other chat channels."
        )
    )
    parser.add_argument(
        "--payload-path",
        type=Path,
        default=DEFAULT_PAYLOAD_PATH,
        help="Path to the notifier-ready delivery payload JSON.",
    )
    parser.add_argument(
        "--handoff-text-path",
        type=Path,
        default=DEFAULT_HANDOFF_TEXT_PATH,
        help="Path to the morning handoff text file.",
    )
    parser.add_argument(
        "--channel",
        required=True,
        help="OpenClaw channel name, for example signal or telegram.",
    )
    parser.add_argument(
        "--target",
        required=True,
        help="OpenClaw message target for the selected channel.",
    )
    parser.add_argument(
        "--send",
        action="store_true",
        help="Actually invoke `openclaw message send`. Without this flag the script only prints the planned action.",
    )
    parser.add_argument(
        "--openclaw-dry-run",
        action="store_true",
        help="Pass `--dry-run` to `openclaw message send` for end-to-end verification without delivering a message.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON describing the planned action or the OpenClaw result.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object in {path}")
    return data


def load_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"{path} is empty")
    return text


def build_message_plan(payload: dict[str, object], handoff_text: str, channel: str, target: str) -> dict[str, object]:
    notifier_action = payload.get("notifier_action")
    delivery_kind = payload.get("delivery_kind")
    delivery_target = payload.get("delivery_target")
    mode = payload.get("mode")

    if not isinstance(notifier_action, str) or not notifier_action:
        raise ValueError("payload missing notifier_action")
    if not isinstance(delivery_kind, str) or not delivery_kind:
        raise ValueError("payload missing delivery_kind")
    if not isinstance(delivery_target, str) or not delivery_target:
        raise ValueError("payload missing delivery_target")
    if not isinstance(mode, str) or not mode:
        raise ValueError("payload missing mode")

    command = [
        "openclaw",
        "message",
        "send",
        "--channel",
        channel,
        "--target",
        target,
    ]

    if notifier_action == "send_audio":
        command.extend(["--message", handoff_text, "--media", delivery_target])
    elif notifier_action == "send_text_fallback":
        fallback_note = load_text(Path(delivery_target))
        message_text = f"{handoff_text}\n\nTTS status: dry run fallback\n{fallback_note}"
        command.extend(["--message", message_text])
    else:
        raise ValueError(f"unsupported notifier_action: {notifier_action}")

    return {
        "channel": channel,
        "target": target,
        "mode": mode,
        "notifier_action": notifier_action,
        "delivery_kind": delivery_kind,
        "delivery_target": delivery_target,
        "command": command,
    }


def render_preview(plan: dict[str, object]) -> str:
    command = plan["command"]
    if not isinstance(command, list) or not all(isinstance(item, str) for item in command):
        raise ValueError("plan command is invalid")
    return " ".join(subprocess.list2cmdline([part]) for part in command)


def run_openclaw(plan: dict[str, object], openclaw_dry_run: bool) -> subprocess.CompletedProcess[str]:
    command = list(plan["command"])
    if openclaw_dry_run:
        command.append("--dry-run")
    command.append("--json")
    return subprocess.run(command, check=True, capture_output=True, text=True)


def main() -> int:
    args = parse_args()

    try:
        payload = load_json(args.payload_path)
        handoff_text = load_text(args.handoff_text_path)
        plan = build_message_plan(payload, handoff_text, args.channel, args.target)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not args.send:
        if args.json:
            sys.stdout.write(json.dumps({"status": "preview", **plan}, indent=2) + "\n")
        else:
            print("status: preview")
            print(f"channel: {plan['channel']}")
            print(f"target: {plan['target']}")
            print(f"mode: {plan['mode']}")
            print(f"action: {plan['notifier_action']}")
            print(f"delivery: {plan['delivery_kind']} -> {plan['delivery_target']}")
            print("command:")
            print(render_preview(plan))
        return 0

    try:
        result = run_openclaw(plan, openclaw_dry_run=args.openclaw_dry_run)
    except subprocess.CalledProcessError as exc:
        if exc.stdout:
            sys.stdout.write(exc.stdout)
        if exc.stderr:
            sys.stderr.write(exc.stderr)
        print(f"error: openclaw message send failed with exit code {exc.returncode}", file=sys.stderr)
        return 1

    if args.json:
        try:
            parsed = json.loads(result.stdout)
        except json.JSONDecodeError:
            parsed = {"raw": result.stdout}
        sys.stdout.write(json.dumps({"status": "sent", "plan": plan, "result": parsed}, indent=2) + "\n")
    else:
        print("status: sent")
        print(f"action: {plan['notifier_action']}")
        print(result.stdout.strip())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
