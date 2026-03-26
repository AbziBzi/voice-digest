#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PAYLOAD_PATH = REPO_ROOT / "out" / "delivery_payload.json"
DEFAULT_HANDOFF_TEXT_PATH = REPO_ROOT / "out" / "morning_handoff.txt"
DEFAULT_CONFIG_PATH = REPO_ROOT / ".voice_digest_notifier.json"
DEFAULT_CHANNEL_ENV = "VOICE_DIGEST_OPENCLAW_CHANNEL"
DEFAULT_TARGET_ENV = "VOICE_DIGEST_OPENCLAW_TARGET"
DEFAULT_AUDIO_MESSAGE_MODE_ENV = "VOICE_DIGEST_AUDIO_MESSAGE_MODE"


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
        help=(
            "OpenClaw channel name, for example signal or telegram. "
            f"Defaults to ${DEFAULT_CHANNEL_ENV} or config file when present."
        ),
    )
    parser.add_argument(
        "--target",
        help=(
            "OpenClaw message target for the selected channel. "
            f"Defaults to ${DEFAULT_TARGET_ENV} or config file when present."
        ),
    )
    parser.add_argument(
        "--config-path",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help=(
            "Optional JSON config file with `channel` and `target` fields. "
            "CLI args win over env vars, which win over config file."
        ),
    )
    parser.add_argument(
        "--audio-message-mode",
        choices=["full", "caption"],
        help=(
            "How to build the message body when sending live audio. `full` sends the whole morning handoff, "
            "while `caption` sends a shorter summary. Defaults to CLI override, then $"
            f"{DEFAULT_AUDIO_MESSAGE_MODE_ENV}, then config file, then full."
        ),
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


def load_optional_config(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    return load_json(path)


def load_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"{path} is empty")
    return text


def resolve_destination(args: argparse.Namespace, config: dict[str, object]) -> tuple[str, str, str]:
    config_channel = config.get("channel")
    config_target = config.get("target")
    env_channel = os.environ.get(DEFAULT_CHANNEL_ENV)
    env_target = os.environ.get(DEFAULT_TARGET_ENV)

    channel = args.channel or env_channel or (config_channel if isinstance(config_channel, str) else None)
    target = args.target or env_target or (config_target if isinstance(config_target, str) else None)

    if not channel or not target:
        raise ValueError(
            "destination is not configured; pass --channel/--target, set "
            f"{DEFAULT_CHANNEL_ENV}/{DEFAULT_TARGET_ENV}, or write {args.config_path} with "
            '{"channel": "signal", "target": "+370..."}'
        )

    source = "cli"
    if not (args.channel and args.target):
        if env_channel and env_target and channel == env_channel and target == env_target:
            source = "env"
        elif isinstance(config_channel, str) and isinstance(config_target, str) and channel == config_channel and target == config_target:
            source = "config"
        else:
            source = "mixed"

    return channel, target, source


def resolve_audio_message_mode(
    args: argparse.Namespace,
    config: dict[str, object],
) -> tuple[str, str]:
    config_mode = config.get("audio_message_mode")
    env_mode = os.environ.get(DEFAULT_AUDIO_MESSAGE_MODE_ENV)

    if args.audio_message_mode:
        return args.audio_message_mode, "cli"
    if isinstance(env_mode, str) and env_mode in {"full", "caption"}:
        return env_mode, "env"
    if isinstance(config_mode, str) and config_mode in {"full", "caption"}:
        return config_mode, "config"
    return "full", "default"


def build_audio_caption(payload: dict[str, object]) -> str:
    run = payload.get("run")
    summary = payload.get("summary")
    if not isinstance(run, dict) or not isinstance(summary, dict):
        raise ValueError("payload missing run/summary for audio caption")

    selected_input = run.get("selected_input")
    spoken_preview = summary.get("spoken_preview")
    source_digest = summary.get("source_digest")

    if not isinstance(selected_input, str) or not selected_input.strip():
        raise ValueError("payload missing run.selected_input for audio caption")
    if not isinstance(spoken_preview, str) or not spoken_preview.strip():
        raise ValueError("payload missing summary.spoken_preview for audio caption")

    caption_lines = [
        "Voice digest is ready.",
        f"Input: {selected_input}",
    ]
    if isinstance(source_digest, str) and source_digest.strip():
        caption_lines.append(f"Source: {source_digest}")
    caption_lines.extend([
        "Preview:",
        spoken_preview,
    ])
    return "\n".join(caption_lines)


def build_message_plan(
    payload: dict[str, object],
    handoff_text: str,
    channel: str,
    target: str,
    destination_source: str,
    audio_message_mode: str,
) -> dict[str, object]:
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

    message_text = handoff_text
    if notifier_action == "send_audio" and audio_message_mode == "caption":
        message_text = build_audio_caption(payload)

    if notifier_action == "send_audio":
        command.extend(["--message", message_text, "--media", delivery_target])
    elif notifier_action == "send_text_fallback":
        fallback_note = load_text(Path(delivery_target))
        message_text = f"{handoff_text}\n\nTTS status: dry run fallback\n{fallback_note}"
        command.extend(["--message", message_text])
    else:
        raise ValueError(f"unsupported notifier_action: {notifier_action}")

    return {
        "channel": channel,
        "target": target,
        "destination_source": destination_source,
        "mode": mode,
        "notifier_action": notifier_action,
        "delivery_kind": delivery_kind,
        "delivery_target": delivery_target,
        "audio_message_mode": audio_message_mode,
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
        config = load_optional_config(args.config_path)
        channel, target, destination_source = resolve_destination(args, config)
        audio_message_mode, audio_message_mode_source = resolve_audio_message_mode(args, config)
        plan = build_message_plan(
            payload,
            handoff_text,
            channel,
            target,
            destination_source,
            audio_message_mode,
        )
        plan["audio_message_mode_source"] = audio_message_mode_source
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
            print(f"destination source: {plan['destination_source']}")
            print(f"action: {plan['notifier_action']}")
            print(f"delivery: {plan['delivery_kind']} -> {plan['delivery_target']}")
            print(f"audio message mode: {plan['audio_message_mode']}")
            print(f"audio message mode source: {plan['audio_message_mode_source']}")
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
