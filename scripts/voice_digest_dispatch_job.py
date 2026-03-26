#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
MORNING_JOB_SCRIPT = REPO_ROOT / "scripts" / "voice_digest_morning_job.py"
NOTIFIER_SCRIPT = REPO_ROOT / "scripts" / "voice_digest_openclaw_notifier.py"
DEFAULT_RUNS_DIR = REPO_ROOT / "out" / "runs"
DEFAULT_STATE_PATH = REPO_ROOT / "out" / "latest_run.json"
DEFAULT_HANDOFF_TEXT_PATH = REPO_ROOT / "out" / "morning_handoff.txt"
DEFAULT_HANDOFF_JSON_PATH = REPO_ROOT / "out" / "morning_handoff.json"
DEFAULT_PAYLOAD_JSON_PATH = REPO_ROOT / "out" / "delivery_payload.json"
DEFAULT_STATUS_JSON_PATH = REPO_ROOT / "out" / "delivery_status.json"
DEFAULT_STATUS_TEXT_PATH = REPO_ROOT / "out" / "delivery_status.txt"
DEFAULT_CONFIG_PATH = REPO_ROOT / ".voice_digest_notifier.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the full scheduler-facing voice-digest dispatch flow: build the latest morning "
            "artifacts, invoke the OpenClaw notifier in preview or send mode, and write stable "
            "delivery-status files that capture success or failure."
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
        "--status-json-path",
        type=Path,
        default=DEFAULT_STATUS_JSON_PATH,
        help="Stable JSON delivery status output path.",
    )
    parser.add_argument(
        "--status-text-path",
        type=Path,
        default=DEFAULT_STATUS_TEXT_PATH,
        help="Stable text delivery status output path.",
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
        "--channel",
        help="OpenClaw channel override passed to the notifier.",
    )
    parser.add_argument(
        "--target",
        help="OpenClaw target override passed to the notifier.",
    )
    parser.add_argument(
        "--config-path",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Optional notifier config file path passed through to the notifier.",
    )
    parser.add_argument(
        "--audio-message-mode",
        choices=["full", "caption"],
        help="Message-body mode passed through to the notifier for live audio sends.",
    )
    parser.add_argument(
        "--send",
        action="store_true",
        help="Actually invoke `openclaw message send`. Without this flag the notifier runs in preview mode.",
    )
    parser.add_argument(
        "--openclaw-dry-run",
        action="store_true",
        help="Pass `--dry-run` to `openclaw message send` when `--send` is enabled.",
    )
    return parser.parse_args()


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def command_preview(command: list[str]) -> str:
    return " ".join(subprocess.list2cmdline([part]) for part in command)


def clip_output(text: str, limit: int = 4000) -> str:
    stripped = text.strip()
    if len(stripped) <= limit:
        return stripped
    return stripped[: limit - 3].rstrip() + "..."


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True)


def load_optional_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object in {path}")
    return data


def build_morning_job_command(args: argparse.Namespace) -> list[str]:
    command = [
        sys.executable,
        str(MORNING_JOB_SCRIPT),
        "--input-dir",
        str(args.input_dir),
        "--glob",
        args.glob,
        "--runs-dir",
        str(args.runs_dir),
        "--state-path",
        str(args.state_path),
        "--handoff-text-path",
        str(args.handoff_text_path),
        "--handoff-json-path",
        str(args.handoff_json_path),
        "--payload-json-path",
        str(args.payload_json_path),
    ]
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
    return command


def build_notifier_command(args: argparse.Namespace) -> list[str]:
    command = [
        sys.executable,
        str(NOTIFIER_SCRIPT),
        "--payload-path",
        str(args.payload_json_path),
        "--handoff-text-path",
        str(args.handoff_text_path),
        "--config-path",
        str(args.config_path),
        "--json",
    ]
    if args.channel:
        command.extend(["--channel", args.channel])
    if args.target:
        command.extend(["--target", args.target])
    if args.audio_message_mode:
        command.extend(["--audio-message-mode", args.audio_message_mode])
    if args.send:
        command.append("--send")
    if args.openclaw_dry_run:
        command.append("--openclaw-dry-run")
    return command


def summarize_command_failure(result: subprocess.CompletedProcess[str], stage: str) -> dict[str, Any]:
    detail = clip_output(result.stderr) or clip_output(result.stdout) or None
    failure = {
        "stage": stage,
        "returncode": result.returncode,
        "message": f"{stage} failed with exit code {result.returncode}",
    }
    if detail:
        failure["detail"] = detail
    return failure


def render_status_text(status: dict[str, Any]) -> str:
    lines = [
        "Voice Digest Delivery Status",
        f"status: {status['status']}",
        f"stage: {status['stage']}",
        f"started_at: {status['started_at']}",
        f"finished_at: {status['finished_at']}",
        f"duration_seconds: {status['duration_seconds']}",
    ]

    summary = status.get("summary")
    if isinstance(summary, dict):
        mode = summary.get("mode")
        selected_input = summary.get("selected_input")
        notifier_action = summary.get("notifier_action")
        delivery_target = summary.get("delivery_target")
        if mode:
            lines.append(f"mode: {mode}")
        if selected_input:
            lines.append(f"selected_input: {selected_input}")
        if notifier_action:
            lines.append(f"notifier_action: {notifier_action}")
        if delivery_target:
            lines.append(f"delivery_target: {delivery_target}")

    destination = status.get("destination")
    if isinstance(destination, dict):
        channel = destination.get("channel")
        target = destination.get("target")
        source = destination.get("source")
        if channel:
            lines.append(f"channel: {channel}")
        if target:
            lines.append(f"target: {target}")
        if source:
            lines.append(f"destination_source: {source}")

    dispatch = status.get("dispatch")
    if isinstance(dispatch, dict):
        requested_mode = dispatch.get("requested_audio_message_mode")
        resolved_mode = dispatch.get("resolved_audio_message_mode")
        resolved_mode_source = dispatch.get("audio_message_mode_source")
        if requested_mode:
            lines.append(f"requested_audio_message_mode: {requested_mode}")
        if resolved_mode:
            lines.append(f"resolved_audio_message_mode: {resolved_mode}")
        if resolved_mode_source:
            lines.append(f"audio_message_mode_source: {resolved_mode_source}")

    error = status.get("error")
    if isinstance(error, dict):
        lines.append(f"error_stage: {error.get('stage')}")
        returncode = error.get("returncode")
        if returncode is not None:
            lines.append(f"error_returncode: {returncode}")
        message = error.get("message")
        if message:
            lines.append(f"error_message: {message}")
        detail = error.get("detail")
        if detail:
            lines.append("error_detail:")
            for line in str(detail).splitlines():
                lines.append(f"  {line}")

    artifacts = status.get("artifacts")
    if isinstance(artifacts, dict):
        lines.append("artifacts:")
        for key in (
            "state_path",
            "handoff_text_path",
            "handoff_json_path",
            "payload_json_path",
            "status_json_path",
        ):
            value = artifacts.get(key)
            if value:
                lines.append(f"  {key}: {value}")

    return "\n".join(lines) + "\n"


def write_status(status: dict[str, Any], status_json_path: Path, status_text_path: Path) -> None:
    ensure_parent(status_json_path)
    ensure_parent(status_text_path)
    status_json_path.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    status_text_path.write_text(render_status_text(status), encoding="utf-8")


def build_base_status(args: argparse.Namespace, started_at: str) -> dict[str, Any]:
    return {
        "status": "running",
        "stage": "starting",
        "started_at": started_at,
        "finished_at": None,
        "duration_seconds": None,
        "artifacts": {
            "state_path": str(args.state_path),
            "handoff_text_path": str(args.handoff_text_path),
            "handoff_json_path": str(args.handoff_json_path),
            "payload_json_path": str(args.payload_json_path),
            "status_json_path": str(args.status_json_path),
            "status_text_path": str(args.status_text_path),
        },
        "dispatch": {
            "send": args.send,
            "openclaw_dry_run": args.openclaw_dry_run,
            "tts_dry_run": args.dry_run,
            "requested_audio_message_mode": args.audio_message_mode,
        },
        "commands": {},
    }


def finalize_status(status: dict[str, Any], finished_at: str, started_at: datetime) -> None:
    status["finished_at"] = finished_at
    status["duration_seconds"] = round(
        (datetime.fromisoformat(finished_at) - started_at).total_seconds(),
        3,
    )


def main() -> int:
    args = parse_args()
    started_at_dt = datetime.now(timezone.utc)
    started_at = started_at_dt.isoformat()

    for path in (
        args.state_path,
        args.handoff_text_path,
        args.handoff_json_path,
        args.payload_json_path,
        args.status_json_path,
        args.status_text_path,
    ):
        ensure_parent(path)

    status = build_base_status(args, started_at)

    morning_command = build_morning_job_command(args)
    status["commands"]["morning_job"] = command_preview(morning_command)
    status["stage"] = "morning_job"
    morning_result = run_command(morning_command)
    status["morning_job"] = {
        "returncode": morning_result.returncode,
        "stdout": clip_output(morning_result.stdout),
        "stderr": clip_output(morning_result.stderr),
    }

    if morning_result.returncode != 0:
        status["status"] = "failed"
        status["error"] = summarize_command_failure(morning_result, "morning_job")
        finalize_status(status, iso_now(), started_at_dt)
        write_status(status, args.status_json_path, args.status_text_path)
        if morning_result.stdout:
            sys.stdout.write(morning_result.stdout)
        if morning_result.stderr:
            sys.stderr.write(morning_result.stderr)
        print(f"delivery status json: {args.status_json_path}")
        print(f"delivery status text: {args.status_text_path}")
        return 1

    notifier_command = build_notifier_command(args)
    notifier_stage = "notifier_send" if args.send else "notifier_preview"
    status["stage"] = notifier_stage
    status["commands"]["notifier"] = command_preview(notifier_command)
    notifier_result = run_command(notifier_command)
    status["notifier"] = {
        "returncode": notifier_result.returncode,
        "stdout": clip_output(notifier_result.stdout),
        "stderr": clip_output(notifier_result.stderr),
    }

    payload = load_optional_json(args.payload_json_path)
    if payload:
        run_summary = payload.get("run")
        if isinstance(run_summary, dict):
            status["run"] = run_summary
        status["summary"] = {
            "mode": payload.get("mode"),
            "notifier_action": payload.get("notifier_action"),
            "delivery_kind": payload.get("delivery_kind"),
            "delivery_target": payload.get("delivery_target"),
            "selected_input": run_summary.get("selected_input") if isinstance(run_summary, dict) else None,
        }

    notifier_json: dict[str, Any] | None = None
    if notifier_result.stdout.strip():
        try:
            parsed = json.loads(notifier_result.stdout)
            if isinstance(parsed, dict):
                notifier_json = parsed
        except json.JSONDecodeError:
            notifier_json = None

    if notifier_json:
        status["notifier_result"] = notifier_json
        plan = notifier_json.get("plan") if args.send else notifier_json
        if isinstance(plan, dict):
            status["destination"] = {
                "channel": plan.get("channel"),
                "target": plan.get("target"),
                "source": plan.get("destination_source"),
            }
            status["dispatch"]["resolved_audio_message_mode"] = plan.get("audio_message_mode")
            status["dispatch"]["audio_message_mode_source"] = plan.get("audio_message_mode_source")

    if notifier_result.returncode != 0:
        status["status"] = "failed"
        status["error"] = summarize_command_failure(notifier_result, notifier_stage)
        finalize_status(status, iso_now(), started_at_dt)
        write_status(status, args.status_json_path, args.status_text_path)
        if morning_result.stdout:
            sys.stdout.write(morning_result.stdout)
        if morning_result.stderr:
            sys.stderr.write(morning_result.stderr)
        if notifier_result.stdout:
            sys.stdout.write(notifier_result.stdout)
        if notifier_result.stderr:
            sys.stderr.write(notifier_result.stderr)
        print(f"delivery status json: {args.status_json_path}")
        print(f"delivery status text: {args.status_text_path}")
        return 1

    status["status"] = "succeeded"
    status["stage"] = "completed"
    finalize_status(status, iso_now(), started_at_dt)
    write_status(status, args.status_json_path, args.status_text_path)

    if morning_result.stdout:
        sys.stdout.write(morning_result.stdout)
    if morning_result.stderr:
        sys.stderr.write(morning_result.stderr)
    if notifier_result.stdout:
        sys.stdout.write(notifier_result.stdout)
    if notifier_result.stderr:
        sys.stderr.write(notifier_result.stderr)

    print(f"delivery status json: {args.status_json_path}")
    print(f"delivery status text: {args.status_text_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
