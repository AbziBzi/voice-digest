from __future__ import annotations

import importlib.util
import io
import json
import os
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from subprocess import CompletedProcess
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "voice_digest_dispatch_job.py"
spec = importlib.util.spec_from_file_location("voice_digest_dispatch_job", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class VoiceDigestDispatchJobTests(unittest.TestCase):
    def test_build_notifier_command_uses_check_setup_instead_of_send(self) -> None:
        args = Namespace(
            payload_json_path=Path("/tmp/delivery_payload.json"),
            handoff_text_path=Path("/tmp/morning_handoff.txt"),
            config_path=Path("/tmp/.voice_digest_notifier.json"),
            channel="signal",
            target="+37060000000",
            audio_message_mode="auto",
            check_setup=True,
            send=True,
            openclaw_dry_run=True,
        )

        command = module.build_notifier_command(args)

        self.assertIn("--check-setup", command)
        self.assertNotIn("--send", command)
        self.assertNotIn("--openclaw-dry-run", command)

    def test_build_notifier_check_setup_command_rewrites_send_invocation(self) -> None:
        args = Namespace(
            payload_json_path=Path("/tmp/delivery_payload.json"),
            handoff_text_path=Path("/tmp/morning_handoff.txt"),
            config_path=Path("/tmp/.voice_digest_notifier.json"),
            channel="signal",
            target="+37060000000",
            audio_message_mode="auto",
            check_setup=False,
            send=True,
            openclaw_dry_run=True,
        )

        command = module.build_notifier_check_setup_command(args)

        self.assertIn("--check-setup", command)
        self.assertNotIn("--send", command)
        self.assertNotIn("--openclaw-dry-run", command)

    def test_resolve_input_dir_prefers_cli_then_env_then_default(self) -> None:
        cli_args = Namespace(input_dir=Path("/tmp/cli-digests"))
        self.assertEqual(
            module.resolve_input_dir(cli_args),
            (Path("/tmp/cli-digests"), "cli"),
        )

        env_args = Namespace(input_dir=None)
        with mock.patch.dict(module.os.environ, {module.DEFAULT_INPUT_DIR_ENV: "/tmp/env-digests"}, clear=False):
            self.assertEqual(
                module.resolve_input_dir(env_args),
                (Path("/tmp/env-digests"), "env"),
            )

        default_args = Namespace(input_dir=None)
        with mock.patch.dict(module.os.environ, {}, clear=True):
            self.assertEqual(
                module.resolve_input_dir(default_args),
                (module.DEFAULT_INPUT_DIR, "default"),
            )

    def test_summarize_command_failure_prefers_structured_json_error(self) -> None:
        result = CompletedProcess(
            args=["python3", "notifier"],
            returncode=1,
            stdout='{"status": "error", "error": "gateway unavailable", "returncode": 9}',
            stderr="",
        )
        summary = module.summarize_command_failure(
            result,
            "notifier_send",
            parsed_json={"status": "error", "error": "gateway unavailable", "returncode": 9},
        )
        self.assertEqual(summary["message"], "notifier_send failed with exit code 9")
        self.assertEqual(summary["detail"], "gateway unavailable")
        self.assertEqual(summary["returncode"], 1)

    def test_summarize_command_failure_falls_back_to_structured_blockers(self) -> None:
        result = CompletedProcess(
            args=["python3", "notifier", "--check-setup"],
            returncode=1,
            stdout='{"status": "blocked", "blockers": ["destination missing"]}',
            stderr="",
        )
        summary = module.summarize_command_failure(
            result,
            "downstream_notifier_check",
            parsed_json={"status": "blocked", "blockers": ["destination missing"]},
        )
        self.assertEqual(summary["detail"], "destination missing")

    def test_collect_input_dir_diagnostics_reports_match_count_and_newest_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir) / "incoming"
            input_dir.mkdir()
            older = input_dir / "older.txt"
            newer = input_dir / "newer.txt"
            ignored = input_dir / "notes.md"
            older.write_text("older\n", encoding="utf-8")
            newer.write_text("newer\n", encoding="utf-8")
            ignored.write_text("ignored\n", encoding="utf-8")
            os.utime(older, (1_700_000_000, 1_700_000_000))
            os.utime(newer, (1_700_000_100, 1_700_000_100))

            diagnostics = module.collect_input_dir_diagnostics(input_dir, "*.txt")

        self.assertEqual(diagnostics["input_glob"], "*.txt")
        self.assertEqual(diagnostics["input_dir_exists"], True)
        self.assertEqual(diagnostics["input_match_count"], 2)
        self.assertEqual(diagnostics["newest_matching_input"], str(newer.resolve()))

    def test_main_check_setup_preserves_downstream_notifier_snapshot_when_morning_job_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            args = Namespace(
                input_dir=None,
                glob="*.txt",
                runs_dir=tmp / "out" / "runs",
                state_path=tmp / "out" / "latest_run.json",
                handoff_text_path=tmp / "out" / "morning_handoff.txt",
                handoff_json_path=tmp / "out" / "morning_handoff.json",
                payload_json_path=tmp / "out" / "delivery_payload.json",
                status_json_path=tmp / "out" / "delivery_status.json",
                status_text_path=tmp / "out" / "delivery_status.txt",
                run_id=None,
                intro=None,
                outro=None,
                voice_id=None,
                model_id=None,
                dry_run=False,
                max_age_minutes=None,
                channel=None,
                target=None,
                config_path=tmp / ".voice_digest_notifier.json",
                audio_message_mode="auto",
                check_setup=True,
                send=False,
                openclaw_dry_run=False,
            )

            morning_result = CompletedProcess(
                args=["python3", "morning"],
                returncode=1,
                stdout="",
                stderr=(
                    "error: no matching digest files found in /tmp/incoming for glob '*.txt'\n"
                ),
            )
            notifier_probe = {
                "status": "blocked",
                "channel": "signal",
                "target": "+37060000000",
                "destination_source": "config",
                "requested_audio_message_mode": "auto",
                "audio_message_mode": "caption",
                "audio_message_mode_source": "config",
                "payload_ready": True,
                "handoff_ready": True,
                "openclaw_available": True,
                "blockers": ["destination is not configured"],
            }
            notifier_result = CompletedProcess(
                args=["python3", "notifier", "--check-setup"],
                returncode=1,
                stdout=json.dumps(notifier_probe),
                stderr="",
            )

            with mock.patch.object(module, "parse_args", return_value=args), mock.patch.object(
                module,
                "run_command",
                side_effect=[morning_result, notifier_result],
            ), mock.patch("sys.stdout", new_callable=io.StringIO), mock.patch(
                "sys.stderr", new_callable=io.StringIO
            ):
                exit_code = module.main()

            self.assertEqual(exit_code, 1)
            status = json.loads(args.status_json_path.read_text(encoding="utf-8"))
            self.assertEqual(status["status"], "failed")
            self.assertEqual(status["error"]["stage"], "morning_job")
            self.assertEqual(
                status["downstream_notifier_check"]["status"],
                "blocked",
            )
            self.assertEqual(
                status["downstream_notifier_check"]["channel"],
                "signal",
            )
            self.assertEqual(
                status["downstream_notifier_check"]["audio_message_mode"],
                "caption",
            )
            self.assertEqual(
                status["downstream_notifier_check"]["payload_ready"],
                True,
            )
            self.assertEqual(
                status["commands"]["downstream_notifier_check"].endswith("--check-setup"),
                True,
            )
            self.assertEqual(
                status["next_action"],
                "Inspect the morning-job error detail, fix the upstream artifact generation issue, then rerun --check-setup.",
            )

            status_text = args.status_text_path.read_text(encoding="utf-8")
            self.assertIn("downstream_notifier_check:", status_text)
            self.assertIn("  status: blocked", status_text)
            self.assertIn("  payload_ready: True", status_text)
            self.assertIn("  blocker: destination is not configured", status_text)

    def test_main_writes_structured_notifier_failure_into_status_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            args = Namespace(
                input_dir=None,
                glob="*.txt",
                runs_dir=tmp / "out" / "runs",
                state_path=tmp / "out" / "latest_run.json",
                handoff_text_path=tmp / "out" / "morning_handoff.txt",
                handoff_json_path=tmp / "out" / "morning_handoff.json",
                payload_json_path=tmp / "out" / "delivery_payload.json",
                status_json_path=tmp / "out" / "delivery_status.json",
                status_text_path=tmp / "out" / "delivery_status.txt",
                run_id=None,
                intro=None,
                outro=None,
                voice_id=None,
                model_id=None,
                dry_run=True,
                max_age_minutes=180.0,
                channel=None,
                target=None,
                config_path=tmp / ".voice_digest_notifier.json",
                audio_message_mode="auto",
                check_setup=False,
                send=True,
                openclaw_dry_run=True,
            )

            morning_result = CompletedProcess(
                args=["python3", "morning"],
                returncode=0,
                stdout="morning ok\n",
                stderr="",
            )
            notifier_payload = {
                "status": "error",
                "error": "gateway unavailable",
                "returncode": 9,
                "diagnostics": {
                    "config_path": str(tmp / ".voice_digest_notifier.json"),
                    "config_exists": True,
                    "config_has_channel": True,
                    "config_has_target": True,
                    "env_channel_set": False,
                    "env_target_set": False,
                    "env_audio_message_mode_set": False,
                    "cli_channel_set": False,
                    "cli_target_set": False,
                    "cli_audio_message_mode_set": True,
                    "payload_path": str(tmp / "out" / "delivery_payload.json"),
                    "handoff_text_path": str(tmp / "out" / "morning_handoff.txt"),
                },
                "plan": {
                    "channel": "signal",
                    "target": "+37060000000",
                    "destination_source": "config",
                    "requested_audio_message_mode": "auto",
                    "audio_message_mode": "caption",
                    "audio_message_mode_source": "config",
                    "audio_message_mode_reason": "auto_caption_handoff_too_long",
                    "message_text_length": 122,
                    "max_audio_message_text_length": 1200,
                },
            }
            notifier_result = CompletedProcess(
                args=["python3", "notifier"],
                returncode=1,
                stdout=json.dumps(notifier_payload),
                stderr="",
            )
            payload_json = {
                "mode": "live",
                "notifier_action": "send_audio",
                "delivery_kind": "audio",
                "delivery_target": str(tmp / "out" / "runs" / "digest.mp3"),
                "run": {
                    "selected_input": str(tmp / "incoming_digests" / "digest.txt"),
                    "age_minutes": 12.5,
                },
                "summary": {
                    "selected_input_details": {
                        "path": str(tmp / "incoming_digests" / "digest.txt"),
                        "exists": True,
                        "size_bytes": 321,
                        "modified_at": "2026-03-27T18:00:00+00:00",
                        "age_minutes": 9.0,
                    },
                    "delivery_target_details": {
                        "path": str(tmp / "out" / "runs" / "digest.mp3"),
                        "exists": True,
                        "size_bytes": 4567,
                        "modified_at": "2026-03-27T18:02:00+00:00",
                        "age_minutes": 7.0,
                    },
                },
            }

            with mock.patch.object(module, "parse_args", return_value=args), mock.patch.dict(
                module.os.environ,
                {module.DEFAULT_INPUT_DIR_ENV: str(tmp / "wired-digests")},
                clear=False,
            ), mock.patch.object(
                module,
                "run_command",
                side_effect=[morning_result, notifier_result],
            ), mock.patch.object(module, "load_optional_json", return_value=payload_json), mock.patch(
                "sys.stdout", new_callable=io.StringIO
            ), mock.patch("sys.stderr", new_callable=io.StringIO):
                exit_code = module.main()

            self.assertEqual(exit_code, 1)
            status = json.loads(args.status_json_path.read_text(encoding="utf-8"))
            self.assertEqual(status["status"], "failed")
            self.assertEqual(status["error"]["stage"], "notifier_send")
            self.assertEqual(status["error"]["message"], "notifier_send failed with exit code 9")
            self.assertEqual(status["error"]["detail"], "gateway unavailable")
            self.assertEqual(status["destination"]["channel"], "signal")
            self.assertEqual(status["destination"]["source"], "config")
            self.assertEqual(status["dispatch"]["input_dir"], str(tmp / "wired-digests"))
            self.assertEqual(status["dispatch"]["input_dir_source"], "env")
            self.assertEqual(status["dispatch"]["requested_audio_message_mode"], "auto")
            self.assertEqual(status["dispatch"]["resolved_audio_message_mode"], "caption")
            self.assertEqual(status["dispatch"]["audio_message_mode_source"], "config")
            self.assertEqual(status["dispatch"]["audio_message_mode_reason"], "auto_caption_handoff_too_long")
            self.assertEqual(status["dispatch"]["message_text_length"], 122)
            self.assertEqual(status["dispatch"]["max_audio_message_text_length"], 1200)
            self.assertEqual(status["summary"]["run_age_minutes"], 12.5)
            self.assertEqual(status["summary"]["selected_input_details"]["age_minutes"], 9.0)
            self.assertEqual(status["summary"]["delivery_target_details"]["size_bytes"], 4567)
            self.assertEqual(status["diagnostics"]["config_exists"], True)
            self.assertEqual(status["diagnostics"]["config_has_channel"], True)
            self.assertEqual(
                status["next_action"],
                "Inspect the notifier send error detail, fix the delivery wiring or transport issue, then rerun with --send --openclaw-dry-run.",
            )

            status_text = args.status_text_path.read_text(encoding="utf-8")
            self.assertIn(f"input_dir: {tmp / 'wired-digests'}", status_text)
            self.assertIn("input_dir_source: env", status_text)
            self.assertIn("run_age_minutes: 12.5", status_text)
            self.assertIn("selected_input_age_minutes: 9.0", status_text)
            self.assertIn("selected_input_size_bytes: 321", status_text)
            self.assertIn("delivery_target_exists: True", status_text)
            self.assertIn("delivery_target_size_bytes: 4567", status_text)
            self.assertIn("delivery_target_age_minutes: 7.0", status_text)
            self.assertIn("requested_audio_message_mode: auto", status_text)
            self.assertIn("resolved_audio_message_mode: caption", status_text)
            self.assertIn("audio_message_mode_reason: auto_caption_handoff_too_long", status_text)
            self.assertIn("message_text_length: 122", status_text)
            self.assertIn("max_audio_message_text_length: 1200", status_text)
            self.assertIn("next_action: Inspect the notifier send error detail", status_text)

    def test_main_check_setup_writes_blocked_status_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            args = Namespace(
                input_dir=None,
                glob="*.txt",
                runs_dir=tmp / "out" / "runs",
                state_path=tmp / "out" / "latest_run.json",
                handoff_text_path=tmp / "out" / "morning_handoff.txt",
                handoff_json_path=tmp / "out" / "morning_handoff.json",
                payload_json_path=tmp / "out" / "delivery_payload.json",
                status_json_path=tmp / "out" / "delivery_status.json",
                status_text_path=tmp / "out" / "delivery_status.txt",
                run_id=None,
                intro=None,
                outro=None,
                voice_id=None,
                model_id=None,
                dry_run=False,
                max_age_minutes=180.0,
                channel=None,
                target=None,
                config_path=tmp / ".voice_digest_notifier.json",
                audio_message_mode="auto",
                check_setup=True,
                send=True,
                openclaw_dry_run=True,
            )

            morning_result = CompletedProcess(
                args=["python3", "morning"],
                returncode=0,
                stdout="morning ok\n",
                stderr="",
            )
            notifier_payload = {
                "status": "blocked",
                "ready": False,
                "payload_ready": True,
                "handoff_ready": True,
                "delivery_target_ready": True,
                "openclaw_available": True,
                "blockers": ["destination is not configured"],
                "diagnostics": {
                    "config_path": str(tmp / ".voice_digest_notifier.json"),
                    "config_exists": False,
                    "config_has_channel": False,
                    "config_has_target": False,
                    "config_has_audio_message_mode": False,
                    "env_channel_set": False,
                    "env_target_set": False,
                    "env_audio_message_mode_set": False,
                    "cli_channel_set": False,
                    "cli_target_set": False,
                    "cli_audio_message_mode_set": True,
                    "payload_path": str(tmp / "out" / "delivery_payload.json"),
                    "handoff_text_path": str(tmp / "out" / "morning_handoff.txt"),
                },
                "requested_audio_message_mode": "auto",
                "audio_message_mode_source": "cli",
            }
            notifier_result = CompletedProcess(
                args=["python3", "notifier"],
                returncode=1,
                stdout=json.dumps(notifier_payload),
                stderr="",
            )
            payload_json = {
                "mode": "live",
                "notifier_action": "send_audio",
                "delivery_kind": "audio",
                "delivery_target": str(tmp / "out" / "runs" / "digest.mp3"),
                "run": {
                    "selected_input": str(tmp / "incoming_digests" / "digest.txt"),
                    "age_minutes": 5.0,
                },
                "summary": {
                    "selected_input_details": {
                        "path": str(tmp / "incoming_digests" / "digest.txt"),
                        "exists": True,
                        "size_bytes": 123,
                        "modified_at": "2026-03-28T18:00:00+00:00",
                        "age_minutes": 4.0,
                    },
                    "delivery_target_details": {
                        "path": str(tmp / "out" / "runs" / "digest.mp3"),
                        "exists": True,
                        "size_bytes": 456,
                        "modified_at": "2026-03-28T18:01:00+00:00",
                        "age_minutes": 3.0,
                    },
                },
            }

            with mock.patch.object(module, "parse_args", return_value=args), mock.patch.object(
                module,
                "run_command",
                side_effect=[morning_result, notifier_result],
            ), mock.patch.object(module, "load_optional_json", return_value=payload_json), mock.patch(
                "sys.stdout", new_callable=io.StringIO
            ), mock.patch("sys.stderr", new_callable=io.StringIO):
                exit_code = module.main()

            self.assertEqual(exit_code, 1)
            status = json.loads(args.status_json_path.read_text(encoding="utf-8"))
            self.assertEqual(status["status"], "blocked")
            self.assertEqual(status["error"]["stage"], "notifier_check_setup")
            self.assertEqual(status["dispatch"]["check_setup"], True)
            self.assertEqual(status["dispatch"]["payload_ready"], True)
            self.assertEqual(status["dispatch"]["handoff_ready"], True)
            self.assertEqual(status["dispatch"]["delivery_target_ready"], True)
            self.assertEqual(status["dispatch"]["openclaw_available"], True)
            self.assertEqual(status["dispatch"]["setup_blockers"], ["destination is not configured"])
            self.assertEqual(
                status["next_action"],
                "Provision the real OpenClaw destination via CLI flags, VOICE_DIGEST_OPENCLAW_CHANNEL / VOICE_DIGEST_OPENCLAW_TARGET, or .voice_digest_notifier.json, then rerun --check-setup.",
            )

            status_text = args.status_text_path.read_text(encoding="utf-8")
            self.assertIn("status: blocked", status_text)
            self.assertIn("payload_ready: True", status_text)
            self.assertIn("handoff_ready: True", status_text)
            self.assertIn("delivery_target_ready: True", status_text)
            self.assertIn("openclaw_available: True", status_text)
            self.assertIn("setup_blocker: destination is not configured", status_text)
            self.assertIn("next_action: Provision the real OpenClaw destination", status_text)

    def test_derive_next_action_flags_missing_delivery_target_for_check_setup(self) -> None:
        status = {
            "status": "blocked",
            "error": {
                "stage": "notifier_check_setup",
                "detail": "delivery target is missing: /tmp/out/digest.mp3",
            },
            "diagnostics": {
                "config_has_channel": True,
                "config_has_target": True,
                "env_channel_set": False,
                "env_target_set": False,
                "cli_channel_set": False,
                "cli_target_set": False,
            },
        }

        self.assertEqual(
            module.derive_next_action(status),
            "Regenerate the morning artifacts so the referenced audio or dry-run note exists at the payload's delivery_target path, then rerun --check-setup.",
        )

    def test_derive_next_action_flags_missing_destination_wiring(self) -> None:
        send_status = {
            "status": "failed",
            "error": {
                "stage": "notifier_send",
                "detail": "destination is required",
            },
            "diagnostics": {
                "config_has_channel": False,
                "config_has_target": False,
                "env_channel_set": False,
                "env_target_set": False,
                "cli_channel_set": False,
                "cli_target_set": False,
            },
        }

        self.assertEqual(
            module.derive_next_action(send_status),
            "Provision the real OpenClaw destination via CLI flags, VOICE_DIGEST_OPENCLAW_CHANNEL / VOICE_DIGEST_OPENCLAW_TARGET, or .voice_digest_notifier.json, then rerun with --send --openclaw-dry-run.",
        )

        preview_status = {
            "status": "failed",
            "error": {
                "stage": "notifier_preview",
                "detail": "destination is required",
            },
            "diagnostics": {
                "config_has_channel": False,
                "config_has_target": False,
                "env_channel_set": False,
                "env_target_set": False,
                "cli_channel_set": False,
                "cli_target_set": False,
            },
        }

        self.assertEqual(
            module.derive_next_action(preview_status),
            "Provision the real OpenClaw destination via CLI flags, VOICE_DIGEST_OPENCLAW_CHANNEL / VOICE_DIGEST_OPENCLAW_TARGET, or .voice_digest_notifier.json, then rerun the preview or send path.",
        )

    def test_derive_next_action_flags_malformed_config(self) -> None:
        send_status = {
            "status": "failed",
            "error": {
                "stage": "notifier_send",
                "detail": "Expecting property name enclosed in double quotes",
            },
            "diagnostics": {
                "config_exists": True,
                "config_load_error": "Expecting property name enclosed in double quotes: line 1 column 2 (char 1)",
                "config_has_channel": False,
                "config_has_target": False,
                "env_channel_set": False,
                "env_target_set": False,
                "cli_channel_set": False,
                "cli_target_set": False,
            },
        }

        self.assertEqual(
            module.derive_next_action(send_status),
            "Fix the malformed .voice_digest_notifier.json (or point --config-path at a valid JSON file), then rerun with --send --openclaw-dry-run.",
        )

        preview_status = {
            "status": "failed",
            "error": {
                "stage": "notifier_preview",
                "detail": "Expecting property name enclosed in double quotes",
            },
            "diagnostics": {
                "config_exists": True,
                "config_load_error": "Expecting property name enclosed in double quotes: line 1 column 2 (char 1)",
                "config_has_channel": False,
                "config_has_target": False,
                "env_channel_set": False,
                "env_target_set": False,
                "cli_channel_set": False,
                "cli_target_set": False,
            },
        }

        self.assertEqual(
            module.derive_next_action(preview_status),
            "Fix the malformed .voice_digest_notifier.json (or point --config-path at a valid JSON file), then rerun the preview or send path.",
        )

    def test_derive_next_action_flags_invalid_audio_message_mode_source(self) -> None:
        send_env_status = {
            "status": "failed",
            "error": {
                "stage": "notifier_send",
                "detail": "invalid VOICE_DIGEST_AUDIO_MESSAGE_MODE value: 'long'; expected one of full, caption, auto",
            },
            "diagnostics": {
                "invalid_audio_message_mode_source": "env",
                "invalid_audio_message_mode_value": "long",
                "config_has_channel": True,
                "config_has_target": True,
                "env_channel_set": False,
                "env_target_set": False,
                "cli_channel_set": False,
                "cli_target_set": False,
            },
        }
        self.assertEqual(
            module.derive_next_action(send_env_status),
            "Fix VOICE_DIGEST_AUDIO_MESSAGE_MODE so it is one of full, caption, or auto, then rerun with --send --openclaw-dry-run.",
        )

        preview_config_status = {
            "status": "failed",
            "error": {
                "stage": "notifier_preview",
                "detail": "invalid audio_message_mode in .voice_digest_notifier.json: 'verbose'; expected one of full, caption, auto",
            },
            "diagnostics": {
                "invalid_audio_message_mode_source": "config",
                "invalid_audio_message_mode_value": "verbose",
                "config_has_channel": True,
                "config_has_target": True,
                "env_channel_set": False,
                "env_target_set": False,
                "cli_channel_set": False,
                "cli_target_set": False,
            },
        }
        self.assertEqual(
            module.derive_next_action(preview_config_status),
            "Fix audio_message_mode in .voice_digest_notifier.json so it is one of full, caption, or auto, then rerun the preview or send path.",
        )

    def test_main_preserves_invalid_audio_message_mode_diagnostics_in_status_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            args = Namespace(
                input_dir=None,
                glob="*.txt",
                runs_dir=tmp / "out" / "runs",
                state_path=tmp / "out" / "latest_run.json",
                handoff_text_path=tmp / "out" / "morning_handoff.txt",
                handoff_json_path=tmp / "out" / "morning_handoff.json",
                payload_json_path=tmp / "out" / "delivery_payload.json",
                status_json_path=tmp / "out" / "delivery_status.json",
                status_text_path=tmp / "out" / "delivery_status.txt",
                run_id=None,
                intro=None,
                outro=None,
                voice_id=None,
                model_id=None,
                dry_run=False,
                max_age_minutes=None,
                channel=None,
                target=None,
                config_path=tmp / ".voice_digest_notifier.json",
                audio_message_mode=None,
                check_setup=False,
                send=False,
                openclaw_dry_run=False,
            )

            morning_result = CompletedProcess(
                args=["python3", "morning"],
                returncode=0,
                stdout="morning ok\n",
                stderr="",
            )
            notifier_payload = {
                "status": "error",
                "error": f"invalid audio_message_mode in {tmp / '.voice_digest_notifier.json'}: 'verbose'; expected one of full, caption, auto",
                "diagnostics": {
                    "config_path": str(tmp / ".voice_digest_notifier.json"),
                    "config_exists": True,
                    "config_has_channel": True,
                    "config_has_target": True,
                    "config_has_audio_message_mode": True,
                    "config_audio_message_mode": "verbose",
                    "env_channel_set": False,
                    "env_target_set": False,
                    "env_audio_message_mode_set": False,
                    "cli_channel_set": False,
                    "cli_target_set": False,
                    "cli_audio_message_mode_set": False,
                    "invalid_audio_message_mode_source": "config",
                    "invalid_audio_message_mode_value": "verbose",
                    "payload_path": str(tmp / "out" / "delivery_payload.json"),
                    "handoff_text_path": str(tmp / "out" / "morning_handoff.txt"),
                },
            }
            notifier_result = CompletedProcess(
                args=["python3", "notifier"],
                returncode=1,
                stdout=json.dumps(notifier_payload),
                stderr="",
            )

            with mock.patch.object(module, "parse_args", return_value=args), mock.patch.object(
                module,
                "run_command",
                side_effect=[morning_result, notifier_result],
            ), mock.patch.object(module, "load_optional_json", return_value=None), mock.patch(
                "sys.stdout", new_callable=io.StringIO
            ), mock.patch("sys.stderr", new_callable=io.StringIO):
                exit_code = module.main()

            self.assertEqual(exit_code, 1)
            status = json.loads(args.status_json_path.read_text(encoding="utf-8"))
            self.assertEqual(status["diagnostics"]["invalid_audio_message_mode_source"], "config")
            self.assertEqual(status["diagnostics"]["invalid_audio_message_mode_value"], "verbose")
            self.assertEqual(status["diagnostics"]["config_audio_message_mode"], "verbose")
            self.assertEqual(
                status["next_action"],
                "Fix audio_message_mode in .voice_digest_notifier.json so it is one of full, caption, or auto, then rerun the preview or send path.",
            )
            status_text = args.status_text_path.read_text(encoding="utf-8")
            self.assertIn("config_audio_message_mode: verbose", status_text)
            self.assertIn("invalid_audio_message_mode_source: config", status_text)
            self.assertIn("invalid_audio_message_mode_value: verbose", status_text)
            self.assertIn("next_action: Fix audio_message_mode in .voice_digest_notifier.json", status_text)

    def test_main_preserves_config_load_error_in_status_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            args = Namespace(
                input_dir=None,
                glob="*.txt",
                runs_dir=tmp / "out" / "runs",
                state_path=tmp / "out" / "latest_run.json",
                handoff_text_path=tmp / "out" / "morning_handoff.txt",
                handoff_json_path=tmp / "out" / "morning_handoff.json",
                payload_json_path=tmp / "out" / "delivery_payload.json",
                status_json_path=tmp / "out" / "delivery_status.json",
                status_text_path=tmp / "out" / "delivery_status.txt",
                run_id=None,
                intro=None,
                outro=None,
                voice_id=None,
                model_id=None,
                dry_run=False,
                max_age_minutes=None,
                channel=None,
                target=None,
                config_path=tmp / ".voice_digest_notifier.json",
                audio_message_mode=None,
                check_setup=False,
                send=False,
                openclaw_dry_run=False,
            )

            morning_result = CompletedProcess(
                args=["python3", "morning"],
                returncode=0,
                stdout="morning ok\n",
                stderr="",
            )
            notifier_payload = {
                "status": "error",
                "error": f"Expecting property name enclosed in double quotes: line 1 column 2 (char 1) in {tmp / '.voice_digest_notifier.json'}",
                "diagnostics": {
                    "config_path": str(tmp / ".voice_digest_notifier.json"),
                    "config_exists": True,
                    "config_has_channel": False,
                    "config_has_target": False,
                    "config_load_error": f"Expecting property name enclosed in double quotes: line 1 column 2 (char 1) in {tmp / '.voice_digest_notifier.json'}",
                    "env_channel_set": False,
                    "env_target_set": False,
                    "env_audio_message_mode_set": False,
                    "cli_channel_set": False,
                    "cli_target_set": False,
                    "cli_audio_message_mode_set": False,
                    "payload_path": str(tmp / "out" / "delivery_payload.json"),
                    "handoff_text_path": str(tmp / "out" / "morning_handoff.txt"),
                },
            }
            notifier_result = CompletedProcess(
                args=["python3", "notifier"],
                returncode=1,
                stdout=json.dumps(notifier_payload),
                stderr="",
            )

            with mock.patch.object(module, "parse_args", return_value=args), mock.patch.object(
                module,
                "run_command",
                side_effect=[morning_result, notifier_result],
            ), mock.patch.object(module, "load_optional_json", return_value=None), mock.patch(
                "sys.stdout", new_callable=io.StringIO
            ), mock.patch("sys.stderr", new_callable=io.StringIO):
                exit_code = module.main()

            self.assertEqual(exit_code, 1)
            status = json.loads(args.status_json_path.read_text(encoding="utf-8"))
            self.assertEqual(status["diagnostics"]["config_exists"], True)
            self.assertIn("config_load_error", status["diagnostics"])
            self.assertEqual(
                status["next_action"],
                "Fix the malformed .voice_digest_notifier.json (or point --config-path at a valid JSON file), then rerun the preview or send path.",
            )
            status_text = args.status_text_path.read_text(encoding="utf-8")
            self.assertIn("config_load_error:", status_text)
            self.assertIn("next_action: Fix the malformed .voice_digest_notifier.json", status_text)

    def test_main_preserves_input_drop_diagnostics_when_morning_job_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            input_dir = tmp / "incoming_digests"
            input_dir.mkdir()
            digest = input_dir / "digest.txt"
            digest.write_text("hello\n", encoding="utf-8")
            args = Namespace(
                input_dir=input_dir,
                glob="*.txt",
                runs_dir=tmp / "out" / "runs",
                state_path=tmp / "out" / "latest_run.json",
                handoff_text_path=tmp / "out" / "morning_handoff.txt",
                handoff_json_path=tmp / "out" / "morning_handoff.json",
                payload_json_path=tmp / "out" / "delivery_payload.json",
                status_json_path=tmp / "out" / "delivery_status.json",
                status_text_path=tmp / "out" / "delivery_status.txt",
                run_id=None,
                intro=None,
                outro=None,
                voice_id=None,
                model_id=None,
                dry_run=False,
                max_age_minutes=None,
                channel=None,
                target=None,
                config_path=tmp / ".voice_digest_notifier.json",
                audio_message_mode=None,
                check_setup=False,
                send=False,
                openclaw_dry_run=False,
            )
            morning_result = CompletedProcess(
                args=["python3", "morning"],
                returncode=1,
                stdout="",
                stderr="error: upstream bundler failed\n",
            )

            with mock.patch.object(module, "parse_args", return_value=args), mock.patch.object(
                module,
                "run_command",
                return_value=morning_result,
            ), mock.patch("sys.stdout", new_callable=io.StringIO), mock.patch(
                "sys.stderr", new_callable=io.StringIO
            ):
                exit_code = module.main()

            self.assertEqual(exit_code, 1)
            status = json.loads(args.status_json_path.read_text(encoding="utf-8"))
            self.assertEqual(status["dispatch"]["input_glob"], "*.txt")
            self.assertEqual(status["dispatch"]["input_dir_exists"], True)
            self.assertEqual(status["dispatch"]["input_match_count"], 1)
            self.assertEqual(status["dispatch"]["newest_matching_input"], str(digest.resolve()))

            status_text = args.status_text_path.read_text(encoding="utf-8")
            self.assertIn("input_glob: *.txt", status_text)
            self.assertIn("input_dir_exists: True", status_text)
            self.assertIn("input_match_count: 1", status_text)
            self.assertIn(f"newest_matching_input: {digest.resolve()}", status_text)

    def test_derive_next_action_flags_missing_input_drop(self) -> None:
        status = {
            "status": "failed",
            "error": {
                "stage": "morning_job",
                "detail": "error: input directory /tmp/incoming_digests does not exist. Create it or point --input-dir at the real upstream digest drop.",
            },
            "dispatch": {
                "input_dir": "/tmp/incoming_digests",
            },
        }

        self.assertEqual(
            module.derive_next_action(status),
            "Populate /tmp/incoming_digests with a fresh digest text file or point the dispatch job at the real upstream drop via --input-dir / VOICE_DIGEST_INPUT_DIR, then rerun the dispatch job.",
        )

    def test_derive_next_action_flags_missing_input_drop_when_no_matching_files_found(self) -> None:
        status = {
            "status": "failed",
            "error": {
                "stage": "morning_job",
                "detail": "error: no matching digest files found in /tmp/incoming_digests for glob '*.txt'",
            },
            "dispatch": {
                "input_dir": "/tmp/incoming_digests",
                "check_setup": True,
            },
        }

        self.assertEqual(
            module.derive_next_action(status),
            "Populate /tmp/incoming_digests with a fresh digest text file or point the dispatch job at the real upstream drop via --input-dir / VOICE_DIGEST_INPUT_DIR, then rerun --check-setup.",
        )

    def test_derive_next_action_flags_tts_dry_run_text_fallback_after_success(self) -> None:
        status = {
            "status": "succeeded",
            "dispatch": {
                "tts_dry_run": True,
                "send": False,
                "openclaw_dry_run": False,
            },
            "summary": {
                "notifier_action": "send_text_fallback",
                "delivery_kind": "dry-run-note",
            },
        }

        self.assertEqual(
            module.derive_next_action(status),
            "Dispatch verification only reached the text fallback because TTS is still running with --dry-run; rerun without --dry-run to verify a real audio artifact before the first live morning delivery.",
        )

    def test_derive_next_action_guides_after_successful_send_dry_run(self) -> None:
        status = {
            "status": "succeeded",
            "dispatch": {
                "send": True,
                "openclaw_dry_run": True,
                "tts_dry_run": False,
            },
            "summary": {
                "notifier_action": "send_audio",
                "delivery_kind": "audio",
            },
        }

        self.assertEqual(
            module.derive_next_action(status),
            "Send-path verification passed; the next milestone is one true live dispatch run without --openclaw-dry-run once the destination/input wiring is confirmed.",
        )


if __name__ == "__main__":
    unittest.main()
