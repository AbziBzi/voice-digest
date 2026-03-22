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


def fail(message: str, exit_code: int = 1) -> NoReturn:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(exit_code)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render a short text digest to MP3 with ElevenLabs."
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
        "--dry-run",
        action="store_true",
        help="Skip the API call and write a dry-run note instead.",
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


def write_dry_run(output_path: Path, text: str, voice_id: str, model_id: str) -> Path:
    note_path = dry_run_path(output_path)
    note_path.parent.mkdir(parents=True, exist_ok=True)
    preview = text if len(text) <= 240 else text[:237] + "..."
    note = "\n".join(
        [
            "Voice Digest dry run",
            f"target_audio={output_path}",
            f"characters={len(text)}",
            f"voice_id={voice_id}",
            f"model_id={model_id}",
            "",
            preview,
            "",
        ]
    )
    note_path.write_text(note, encoding="utf-8")
    return note_path


def synthesize(
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

    try:
        with request.urlopen(req, timeout=60) as response:
            audio = response.read()
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        fail(f"ElevenLabs request failed ({exc.code}): {body}")
    except error.URLError as exc:
        fail(f"could not reach ElevenLabs API: {exc.reason}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(audio)


def main() -> int:
    args = parse_args()
    text = read_text(args.input)
    if not text:
        fail("input text is empty")

    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if args.dry_run or not api_key:
        note_path = write_dry_run(args.output, text, args.voice_id, args.model_id)
        reason = "--dry-run requested" if args.dry_run else "ELEVENLABS_API_KEY is not set"
        print(f"{reason}; wrote {note_path}")
        return 0

    synthesize(text, args.output, api_key, args.voice_id, args.model_id)
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
