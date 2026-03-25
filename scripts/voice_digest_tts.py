#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import NoReturn
from urllib import error, request


DEFAULT_VOICE_ID = "SAz9YHcvj6GT2YYXdXww"
DEFAULT_MODEL_ID = "eleven_multilingual_v2"
DEFAULT_API_BASE = "https://api.elevenlabs.io"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini-tts"
DEFAULT_OPENAI_VOICE = "alloy"
DEFAULT_OPENAI_API_BASE = "https://api.openai.com/v1"
FALLBACK_HTTP_CODES = {401, 402, 403, 408, 409, 429, 500, 502, 503, 504}


def fail(message: str, exit_code: int = 1) -> NoReturn:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(exit_code)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render a short text digest to MP3 with ElevenLabs and OpenAI fallback."
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        help="Optional text file input. If omitted, reads from stdin.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Target MP3 path.",
    )
    parser.add_argument(
        "--voice-id",
        default=os.environ.get("ELEVENLABS_VOICE_ID", DEFAULT_VOICE_ID),
        help="ElevenLabs voice ID. Defaults to ELEVENLABS_VOICE_ID or a built-in demo voice.",
    )
    parser.add_argument(
        "--model-id",
        default=os.environ.get("ELEVENLABS_MODEL_ID", DEFAULT_MODEL_ID),
        help="ElevenLabs model ID.",
    )
    parser.add_argument(
        "--openai-model",
        default=os.environ.get("OPENAI_TTS_MODEL", DEFAULT_OPENAI_MODEL),
        help="OpenAI fallback TTS model. Defaults to OPENAI_TTS_MODEL or gpt-4o-mini-tts.",
    )
    parser.add_argument(
        "--openai-voice",
        default=os.environ.get("OPENAI_TTS_VOICE", DEFAULT_OPENAI_VOICE),
        help="OpenAI fallback TTS voice. Defaults to OPENAI_TTS_VOICE or alloy.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip live synthesis and write a dry-run note instead.",
    )
    return parser.parse_args()


def read_text(input_path: Path | None) -> str:
    if input_path is not None:
        return input_path.read_text(encoding="utf-8").strip()

    if sys.stdin.isatty():
        fail("no input provided; pass --input or pipe text on stdin")

    return sys.stdin.read().strip()


def dry_run_path(output_path: Path) -> Path:
    return output_path.with_suffix(output_path.suffix + ".dry-run.txt")


def write_dry_run(
    output_path: Path,
    text: str,
    provider: str,
    voice_id: str,
    model_id: str,
    reason: str | None = None,
) -> Path:
    note_path = dry_run_path(output_path)
    note_path.parent.mkdir(parents=True, exist_ok=True)
    preview = text if len(text) <= 240 else text[:237] + "..."
    lines = [
        "Voice Digest dry run",
        f"target_audio={output_path}",
        f"characters={len(text)}",
        f"provider={provider}",
        f"voice_id={voice_id}",
        f"model_id={model_id}",
    ]
    if reason:
        lines.append(f"reason={reason}")
    note = "\n".join(lines + ["", preview, ""])
    note_path.write_text(note, encoding="utf-8")
    return note_path


def should_try_openai_fallback(exc: error.HTTPError | error.URLError) -> bool:
    if isinstance(exc, error.HTTPError):
        return exc.code in FALLBACK_HTTP_CODES
    return True


def format_http_error_body(exc: error.HTTPError) -> str:
    return exc.read().decode("utf-8", errors="replace")


def synthesize_elevenlabs(
    text: str,
    output_path: Path,
    api_key: str,
    voice_id: str,
    model_id: str,
) -> None:
    url = f"{os.environ.get('ELEVENLABS_API_BASE', DEFAULT_API_BASE).rstrip('/')}/v1/text-to-speech/{voice_id}"
    payload = json.dumps(
        {
            "text": text,
            "model_id": model_id,
            "output_format": "mp3_44100_128",
        }
    ).encode("utf-8")
    req = request.Request(
        url,
        data=payload,
        headers={
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key,
        },
        method="POST",
    )

    with request.urlopen(req, timeout=60) as response:
        audio = response.read()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(audio)


def synthesize_openai(
    text: str,
    output_path: Path,
    api_key: str,
    model_id: str,
    voice_id: str,
) -> None:
    url = f"{os.environ.get('OPENAI_API_BASE', DEFAULT_OPENAI_API_BASE).rstrip('/')}/audio/speech"
    payload = json.dumps(
        {
            "model": model_id,
            "voice": voice_id,
            "input": text,
            "format": "mp3",
        }
    ).encode("utf-8")
    req = request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with request.urlopen(req, timeout=60) as response:
        audio = response.read()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(audio)


def main() -> int:
    args = parse_args()
    text = read_text(args.input)
    if not text:
        fail("input text is empty")

    if args.dry_run:
        note_path = write_dry_run(
            args.output,
            text,
            provider="dry-run",
            voice_id=args.voice_id,
            model_id=args.model_id,
            reason="--dry-run requested",
        )
        print(f"--dry-run requested; wrote {note_path}")
        return 0

    elevenlabs_api_key = os.environ.get("ELEVENLABS_API_KEY")
    openai_api_key = os.environ.get("OPENAI_API_KEY")

    if not elevenlabs_api_key and not openai_api_key:
        note_path = write_dry_run(
            args.output,
            text,
            provider="none",
            voice_id=args.voice_id,
            model_id=args.model_id,
            reason="ELEVENLABS_API_KEY and OPENAI_API_KEY are not set",
        )
        print(f"no live TTS credentials available; wrote {note_path}")
        return 0

    if elevenlabs_api_key:
        try:
            synthesize_elevenlabs(
                text,
                args.output,
                elevenlabs_api_key,
                args.voice_id,
                args.model_id,
            )
            print(f"wrote {args.output} via elevenlabs")
            return 0
        except error.HTTPError as exc:
            body = format_http_error_body(exc)
            if not openai_api_key or not should_try_openai_fallback(exc):
                fail(f"ElevenLabs request failed ({exc.code}): {body}")
            print(
                f"warning: ElevenLabs request failed ({exc.code}); trying OpenAI fallback",
                file=sys.stderr,
            )
        except error.URLError as exc:
            if not openai_api_key:
                fail(f"could not reach ElevenLabs API: {exc.reason}")
            print(
                f"warning: could not reach ElevenLabs API ({exc.reason}); trying OpenAI fallback",
                file=sys.stderr,
            )
    else:
        print("warning: ELEVENLABS_API_KEY is not set; trying OpenAI fallback", file=sys.stderr)

    try:
        synthesize_openai(
            text,
            args.output,
            openai_api_key,
            args.openai_model,
            args.openai_voice,
        )
    except error.HTTPError as exc:
        body = format_http_error_body(exc)
        fail(f"OpenAI TTS request failed ({exc.code}): {body}")
    except error.URLError as exc:
        fail(f"could not reach OpenAI API: {exc.reason}")

    print(f"wrote {args.output} via openai")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
