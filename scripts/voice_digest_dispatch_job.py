#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
MORNING_JOB_SCRIPT = REPO_ROOT / "scripts" / "voice_digest_morning_job.py"
NOTIFIER_SCRIPT = REPO_ROOT / "scripts" / "voice_digest_openclaw_notifier.py"
DEFAULT_INPUT_DIR = REPO_ROOT / "incoming_digests"
DEFAULT_RUNS_DIR = REPO_ROOT / "out" / "runs"
DEFAULT_STATE_PATH = REPO_ROOT / "out" / "latest_run.json"
DEFAULT_HANDOFF_TEXT_PATH = REPO_ROOT / "out" / "morning_handoff.txt"
DEFAULT_HANDOFF_JSON_PATH = REPO_ROOT / "out" / "morning_handoff.json"
DEFAULT_PAYLOAD_JSON_PATH = REPO_ROOT / "out" / "delivery_payload.json"
DEFAULT_STATUS_JSON_PATH = REPO_ROOT / "out" / "delivery_status.json"
DEFAULT_STATUS_TEXT_PATH = REPO_ROOT / "out" / "delivery_status.txt"
DEFAULT_CONFIG_PATH = REPO_ROOT / ".voice_digest_notifier.json"
DEFAULT_INPUT_DIR_ENV = "VOICE_DIGEST_INPUT_DIR"


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
        help=(
            "Directory containing digest text files dropped by the upstream digest generator. "
            f"Defaults to ${DEFAULT_INPUT_DIR_ENV} when set, otherwise ./incoming_digests under the repo root."
        ),
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
        "--max-age-minutes",
        type=float,
        help=(
            "Optional freshness guard passed through to downstream validation so the dispatch job "
            "can reject stale latest-run artifacts."
        ),
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
        choices=["full", "caption", "auto"],
        help="Message-body mode passed through to the notifier for live audio sends.",
    )
    parser.add_argument(
        "--check-setup",
        action="store_true",
        help=(
            "Run the notifier's readiness probe after building morning artifacts so the dispatch job can leave "
            "stable delivery-status files for the intended environment without previewing or sending a message."
        ),
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


def resolve_input_dir(args: argparse.Namespace) -> tuple[Path, str]:
    if args.input_dir is not None:
        return args.input_dir, "cli"
    env_input_dir = os.environ.get(DEFAULT_INPUT_DIR_ENV)
    if isinstance(env_input_dir, str) and env_input_dir.strip():
        return Path(env_input_dir), "env"
    return DEFAULT_INPUT_DIR, "default"


def build_morning_job_command(args: argparse.Namespace, input_dir: Path) -> list[str]:
    command = [
        sys.executable,
        str(MORNING_JOB_SCRIPT),
        "--input-dir",
        str(input_dir),
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
    if args.max_age_minutes is not None:
        command.extend(["--max-age-minutes", str(args.max_age_minutes)])
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
    if args.check_setup:
        command.append("--check-setup")
    elif args.send:
        command.append("--send")
        if args.openclaw_dry_run:
            command.append("--openclaw-dry-run")
    return command


def extract_error_summary(*texts: str) -> str | None:
    for text in texts:
        if not text:
            continue
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("error:"):
                return stripped
    for text in texts:
        if not text:
            continue
        clipped = clip_output(text)
        if clipped:
            return clipped
    return None


def summarize_command_failure(
    result: subprocess.CompletedProcess[str],
    stage: str,
    *,
    parsed_json: dict[str, Any] | None = None,
) -> dict[str, Any]:
    message = f"{stage} failed with exit code {result.returncode}"
    detail = extract_error_summary(result.stderr, result.stdout)

    if isinstance(parsed_json, dict):
        json_error = parsed_json.get("error")
        if isinstance(json_error, str) and json_error.strip():
            detail = json_error.strip()
        json_returncode = parsed_json.get("returncode")
        if isinstance(json_returncode, int):
            message = f"{stage} failed with exit code {json_returncode}"
        stdout = parsed_json.get("stdout")
        stderr = parsed_json.get("stderr")
        if not detail:
            detail = extract_error_summary(
                stderr if isinstance(stderr, str) else "",
                stdout if isinstance(stdout, str) else "",
            )

    failure = {
        "stage": stage,
        "returncode": result.returncode,
        "message": message,
    }
    if detail:
        failure["detail"] = detail
    return failure


def derive_next_action(status: dict[str, Any]) -> str | None:
    dispatch = status.get("dispatch")
    dispatch = dispatch if isinstance(dispatch, dict) else {}
    input_dir = dispatch.get("input_dir")
    input_dir_display = str(input_dir) if input_dir else "incoming_digests/"

    diagnostics = status.get("diagnostics")
    diagnostics = diagnostics if isinstance(diagnostics, dict) else {}

    summary = status.get("summary")
    summary = summary if isinstance(summary, dict) else {}
    notifier_action = summary.get("notifier_action")
    delivery_kind = summary.get("delivery_kind")

    error = status.get("error")
    error = error if isinstance(error, dict) else {}
    detail = error.get("detail")
    detail_text = detail.lower() if isinstance(detail, str) else ""

    if status.get("status") == "blocked":
        if error.get("stage") == "notifier_check_setup":
            if diagnostics.get("config_load_error"):
                return "Fix the malformed .voice_digest_notifier.json (or point --config-path at a valid JSON file), then rerun --check-setup."
            invalid_audio_mode_source = diagnostics.get("invalid_audio_message_mode_source")
            if invalid_audio_mode_source == "env":
                return "Fix VOICE_DIGEST_AUDIO_MESSAGE_MODE so it is one of full, caption, or auto, then rerun --check-setup."
            if invalid_audio_mode_source == "config":
                return "Fix audio_message_mode in .voice_digest_notifier.json so it is one of full, caption, or auto, then rerun --check-setup."
            if "openclaw cli" in detail_text or '"openclaw_available": false' in detail_text:
                return "Ensure the openclaw CLI is installed and available on PATH for the intended scheduler environment, then rerun --check-setup."
            missing_destination = not any(
                [
                    diagnostics.get("config_has_channel") and diagnostics.get("config_has_target"),
                    diagnostics.get("env_channel_set") and diagnostics.get("env_target_set"),
                    diagnostics.get("cli_channel_set") and diagnostics.get("cli_target_set"),
                ]
            )
            if missing_destination:
                return (
                    "Provision the real OpenClaw destination via CLI flags, VOICE_DIGEST_OPENCLAW_CHANNEL / "
                    "VOICE_DIGEST_OPENCLAW_TARGET, or .voice_digest_notifier.json, then rerun --check-setup."
                )
            return "Inspect the notifier readiness blockers in delivery_status.json, fix the environment, then rerun --check-setup."

        return "Inspect the captured blockers in delivery_status.json and rerun only after the intended environment is ready."

    if status.get("status") == "failed":
        if error.get("stage") == "morning_job":
            if "no digest files matched" in detail_text or "input directory" in detail_text:
                rerun_target = "--check-setup" if dispatch.get("check_setup") else "the dispatch job"
                return (
                    f"Populate {input_dir_display} with a fresh digest text file or point the dispatch job at the real "
                    f"upstream drop via --input-dir / VOICE_DIGEST_INPUT_DIR, then rerun {rerun_target}."
                )
            rerun_target = "--check-setup" if dispatch.get("check_setup") else "the dispatch job"
            return f"Inspect the morning-job error detail, fix the upstream artifact generation issue, then rerun {rerun_target}."

        missing_destination = not any(
            [
                diagnostics.get("config_has_channel") and diagnostics.get("config_has_target"),
                diagnostics.get("env_channel_set") and diagnostics.get("env_target_set"),
                diagnostics.get("cli_channel_set") and diagnostics.get("cli_target_set"),
            ]
        )

        if error.get("stage") == "notifier_send":
            if diagnostics.get("config_load_error"):
                return "Fix the malformed .voice_digest_notifier.json (or point --config-path at a valid JSON file), then rerun with --send --openclaw-dry-run."
            invalid_audio_mode_source = diagnostics.get("invalid_audio_message_mode_source")
            if invalid_audio_mode_source == "env":
                return "Fix VOICE_DIGEST_AUDIO_MESSAGE_MODE so it is one of full, caption, or auto, then rerun with --send --openclaw-dry-run."
            if invalid_audio_mode_source == "config":
                return "Fix audio_message_mode in .voice_digest_notifier.json so it is one of full, caption, or auto, then rerun with --send --openclaw-dry-run."
            if "openclaw cli is not available" in detail_text or "openclaw cli could not be executed" in detail_text:
                return "Ensure the openclaw CLI is installed and available on PATH for the scheduler environment, then rerun with --send --openclaw-dry-run."
            if missing_destination:
                return (
                    "Provision the real OpenClaw destination via CLI flags, VOICE_DIGEST_OPENCLAW_CHANNEL / "
                    "VOICE_DIGEST_OPENCLAW_TARGET, or .voice_digest_notifier.json, then rerun with --send --openclaw-dry-run."
                )
            return "Inspect the notifier send error detail, fix the delivery wiring or transport issue, then rerun with --send --openclaw-dry-run."

        if error.get("stage") == "notifier_preview":
            if diagnostics.get("config_load_error"):
                return "Fix the malformed .voice_digest_notifier.json (or point --config-path at a valid JSON file), then rerun the preview or send path."
            invalid_audio_mode_source = diagnostics.get("invalid_audio_message_mode_source")
            if invalid_audio_mode_source == "env":
                return "Fix VOICE_DIGEST_AUDIO_MESSAGE_MODE so it is one of full, caption, or auto, then rerun the preview or send path."
            if invalid_audio_mode_source == "config":
                return "Fix audio_message_mode in .voice_digest_notifier.json so it is one of full, caption, or auto, then rerun the preview or send path."
            if missing_destination:
                return (
                    "Provision the real OpenClaw destination via CLI flags, VOICE_DIGEST_OPENCLAW_CHANNEL / "
                    "VOICE_DIGEST_OPENCLAW_TARGET, or .voice_digest_notifier.json, then rerun the preview or send path."
                )
            return "Fix the notifier preview error, then rerun the dispatch job without broadening scope."

        return "Inspect the captured error detail in delivery_status.json and rerun only after the blocked stage is fixed."

    if status.get("status") == "succeeded":
        if dispatch.get("check_setup"):
            return "Notifier setup is ready in this environment; the next milestone is an intended-config --send --openclaw-dry-run dispatch before one true live delivery."

        if notifier_action == "send_text_fallback" and delivery_kind == "dry-run-note":
            if dispatch.get("tts_dry_run"):
                return (
                    "Dispatch verification only reached the text fallback because TTS is still running with --dry-run; "
                    "rerun without --dry-run to verify a real audio artifact before the first live morning delivery."
                )
            return (
                "Dispatch completed with a text fallback instead of a real audio artifact; ensure the live TTS provider path is available, "
                "then rerun before relying on the automated morning voice digest."
            )
        if dispatch.get("send") and dispatch.get("openclaw_dry_run"):
            return "Send-path verification passed; the next milestone is one true live dispatch run without --openclaw-dry-run once the destination/input wiring is confirmed."
        if dispatch.get("send"):
            return "Live dispatch succeeded; review the delivered morning experience and choose any follow-up polish based on the real result."
        return "Preview succeeded; once the destination wiring is ready, rerun with --send --openclaw-dry-run before the first true live dispatch."

    return None


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
        run_age_minutes = summary.get("run_age_minutes")
        selected_input_details = summary.get("selected_input_details")
        delivery_target_details = summary.get("delivery_target_details")
        if mode:
            lines.append(f"mode: {mode}")
        if selected_input:
            lines.append(f"selected_input: {selected_input}")
        if notifier_action:
            lines.append(f"notifier_action: {notifier_action}")
        if delivery_target:
            lines.append(f"delivery_target: {delivery_target}")
        if run_age_minutes is not None:
            lines.append(f"run_age_minutes: {run_age_minutes}")
        if isinstance(selected_input_details, dict):
            input_age = selected_input_details.get("age_minutes")
            input_modified = selected_input_details.get("modified_at")
            input_size = selected_input_details.get("size_bytes")
            if input_age is not None:
                lines.append(f"selected_input_age_minutes: {input_age}")
            if input_modified:
                lines.append(f"selected_input_modified_at: {input_modified}")
            if input_size is not None:
                lines.append(f"selected_input_size_bytes: {input_size}")
        if isinstance(delivery_target_details, dict):
            delivery_exists = delivery_target_details.get("exists")
            delivery_size = delivery_target_details.get("size_bytes")
            delivery_modified = delivery_target_details.get("modified_at")
            delivery_age = delivery_target_details.get("age_minutes")
            if delivery_exists is not None:
                lines.append(f"delivery_target_exists: {delivery_exists}")
            if delivery_size is not None:
                lines.append(f"delivery_target_size_bytes: {delivery_size}")
            if delivery_modified:
                lines.append(f"delivery_target_modified_at: {delivery_modified}")
            if delivery_age is not None:
                lines.append(f"delivery_target_age_minutes: {delivery_age}")

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
        max_age_minutes = dispatch.get("max_age_minutes")
        input_dir = dispatch.get("input_dir")
        input_dir_source = dispatch.get("input_dir_source")
        requested_mode = dispatch.get("requested_audio_message_mode")
        resolved_mode = dispatch.get("resolved_audio_message_mode")
        resolved_mode_source = dispatch.get("audio_message_mode_source")
        resolved_mode_reason = dispatch.get("audio_message_mode_reason")
        message_text_length = dispatch.get("message_text_length")
        max_message_text_length = dispatch.get("max_audio_message_text_length")
        payload_ready = dispatch.get("payload_ready")
        handoff_ready = dispatch.get("handoff_ready")
        openclaw_available = dispatch.get("openclaw_available")
        setup_blockers = dispatch.get("setup_blockers")
        if input_dir:
            lines.append(f"input_dir: {input_dir}")
        if input_dir_source:
            lines.append(f"input_dir_source: {input_dir_source}")
        if max_age_minutes is not None:
            lines.append(f"max_age_minutes: {max_age_minutes}")
        if requested_mode:
            lines.append(f"requested_audio_message_mode: {requested_mode}")
        if resolved_mode:
            lines.append(f"resolved_audio_message_mode: {resolved_mode}")
        if resolved_mode_source:
            lines.append(f"audio_message_mode_source: {resolved_mode_source}")
        if resolved_mode_reason:
            lines.append(f"audio_message_mode_reason: {resolved_mode_reason}")
        if message_text_length is not None:
            lines.append(f"message_text_length: {message_text_length}")
        if max_message_text_length is not None:
            lines.append(f"max_audio_message_text_length: {max_message_text_length}")
        if payload_ready is not None:
            lines.append(f"payload_ready: {payload_ready}")
        if handoff_ready is not None:
            lines.append(f"handoff_ready: {handoff_ready}")
        if openclaw_available is not None:
            lines.append(f"openclaw_available: {openclaw_available}")
        if isinstance(setup_blockers, list):
            for blocker in setup_blockers:
                lines.append(f"setup_blocker: {blocker}")

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

    diagnostics = status.get("diagnostics")
    if isinstance(diagnostics, dict):
        lines.append("diagnostics:")
        for key in (
            "config_path",
            "config_exists",
            "config_has_channel",
            "config_has_target",
            "config_has_audio_message_mode",
            "config_audio_message_mode",
            "config_load_error",
            "env_channel_set",
            "env_target_set",
            "env_audio_message_mode_set",
            "env_audio_message_mode",
            "invalid_audio_message_mode_source",
            "invalid_audio_message_mode_value",
            "cli_channel_set",
            "cli_target_set",
            "cli_audio_message_mode_set",
            "payload_path",
            "handoff_text_path",
        ):
            if key in diagnostics:
                lines.append(f"  {key}: {diagnostics[key]}")

    next_action = status.get("next_action")
    if next_action:
        lines.append(f"next_action: {next_action}")

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


def build_base_status(
    args: argparse.Namespace,
    started_at: str,
    *,
    input_dir: Path,
    input_dir_source: str,
) -> dict[str, Any]:
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
            "check_setup": args.check_setup,
            "send": args.send,
            "openclaw_dry_run": args.openclaw_dry_run,
            "tts_dry_run": args.dry_run,
            "input_dir": str(input_dir),
            "input_dir_source": input_dir_source,
            "max_age_minutes": args.max_age_minutes,
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

    input_dir, input_dir_source = resolve_input_dir(args)
    status = build_base_status(
        args,
        started_at,
        input_dir=input_dir,
        input_dir_source=input_dir_source,
    )

    morning_command = build_morning_job_command(args, input_dir)
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
        status["next_action"] = derive_next_action(status)
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
    if args.check_setup:
        notifier_stage = "notifier_check_setup"
    else:
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
        payload_summary = payload.get("summary")
        selected_input_details = (
            payload_summary.get("selected_input_details")
            if isinstance(payload_summary, dict)
            else None
        )
        delivery_target_details = (
            payload_summary.get("delivery_target_details")
            if isinstance(payload_summary, dict)
            else None
        )
        status["summary"] = {
            "mode": payload.get("mode"),
            "notifier_action": payload.get("notifier_action"),
            "delivery_kind": payload.get("delivery_kind"),
            "delivery_target": payload.get("delivery_target"),
            "selected_input": run_summary.get("selected_input") if isinstance(run_summary, dict) else None,
            "run_age_minutes": run_summary.get("age_minutes") if isinstance(run_summary, dict) else None,
            "selected_input_details": selected_input_details if isinstance(selected_input_details, dict) else None,
            "delivery_target_details": delivery_target_details if isinstance(delivery_target_details, dict) else None,
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
        diagnostics = notifier_json.get("diagnostics")
        if isinstance(diagnostics, dict):
            status["diagnostics"] = diagnostics
        plan = notifier_json.get("plan") if args.send and not args.check_setup else notifier_json
        if isinstance(plan, dict):
            status["destination"] = {
                "channel": plan.get("channel"),
                "target": plan.get("target"),
                "source": plan.get("destination_source"),
            }
            status["dispatch"]["requested_audio_message_mode"] = plan.get("requested_audio_message_mode", status["dispatch"].get("requested_audio_message_mode"))
            status["dispatch"]["resolved_audio_message_mode"] = plan.get("audio_message_mode")
            status["dispatch"]["audio_message_mode_source"] = plan.get("audio_message_mode_source")
            status["dispatch"]["audio_message_mode_reason"] = plan.get("audio_message_mode_reason")
            status["dispatch"]["message_text_length"] = plan.get("message_text_length")
            status["dispatch"]["max_audio_message_text_length"] = plan.get("max_audio_message_text_length")
            if args.check_setup:
                status["dispatch"]["payload_ready"] = plan.get("payload_ready")
                status["dispatch"]["handoff_ready"] = plan.get("handoff_ready")
                status["dispatch"]["openclaw_available"] = plan.get("openclaw_available")
                blockers = plan.get("blockers")
                if isinstance(blockers, list):
                    status["dispatch"]["setup_blockers"] = blockers

    if notifier_result.returncode != 0:
        status["status"] = "blocked" if args.check_setup else "failed"
        status["error"] = summarize_command_failure(
            notifier_result,
            notifier_stage,
            parsed_json=notifier_json,
        )
        status["next_action"] = derive_next_action(status)
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
    status["next_action"] = derive_next_action(status)
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
