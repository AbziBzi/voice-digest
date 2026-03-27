#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import NoReturn


DEFAULT_INTRO = "Good morning. Here is your voice digest."
DEFAULT_OUTRO = (
    "That wraps the digest. Revisit anything marked visual when you are back at a screen."
)
VISUAL_PREFIXES = (
    "worth opening later:",
    "visual:",
    "visual flag:",
    "chart:",
    "graph:",
    "diagram:",
    "screenshot:",
    "table:",
    "image:",
)
VISUAL_NOUNS = (
    "chart",
    "graph",
    "diagram",
    "screenshot",
    "table",
    "slide",
    "figure",
)
VISUAL_REVIEW_HINTS = (
    "open",
    "look at",
    "see",
    "review",
    "inspect",
    "revisit",
    "compare",
)
SKIP_PARAGRAPHS = {
    "end of article.",
    "end of digest.",
}


def fail(message: str, exit_code: int = 1) -> NoReturn:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(exit_code)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Turn a text digest into a spoken-friendly script."
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        help="Optional digest text file. If omitted, reads from stdin.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Optional output path for the spoken script. Defaults to stdout.",
    )
    parser.add_argument(
        "--intro",
        default=DEFAULT_INTRO,
        help="Intro line for the spoken script.",
    )
    parser.add_argument(
        "--outro",
        default=DEFAULT_OUTRO,
        help="Outro line for the spoken script.",
    )
    return parser.parse_args()


def read_text(input_path: Path | None) -> str:
    if input_path is not None:
        return input_path.read_text(encoding="utf-8").strip()

    if sys.stdin.isatty():
        fail("no input provided; pass --input or pipe text on stdin")

    return sys.stdin.read().strip()


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def detect_visual_flag(paragraph: str) -> str | None:
    lowered = paragraph.lower()
    for prefix in VISUAL_PREFIXES:
        if lowered.startswith(prefix):
            content = normalize_whitespace(
                paragraph.split(":", 1)[1] if ":" in paragraph else paragraph
            )
            return content

    has_visual_noun = any(
        re.search(rf"\b{re.escape(noun)}s?\b", lowered) for noun in VISUAL_NOUNS
    )
    has_review_hint = any(
        re.search(rf"\b{re.escape(hint)}\b", lowered) for hint in VISUAL_REVIEW_HINTS
    )
    if has_visual_noun and has_review_hint:
        return normalize_whitespace(paragraph)

    return None


def spoken_line(paragraph: str) -> str | None:
    cleaned = normalize_whitespace(paragraph)
    if cleaned.lower() in SKIP_PARAGRAPHS:
        return None

    visual_flag = detect_visual_flag(cleaned)
    if visual_flag is not None:
        return f"VISUAL FLAG: {visual_flag}"

    return cleaned


def build_script(text: str, intro: str, outro: str) -> str:
    paragraphs = []
    for paragraph in re.split(r"\n\s*\n+", text.strip()):
        if not normalize_whitespace(paragraph):
            continue
        line = spoken_line(paragraph)
        if line:
            paragraphs.append(line)

    lines = [normalize_whitespace(intro), *paragraphs, normalize_whitespace(outro)]
    return "\n\n".join(line for line in lines if line)


def write_output(output_path: Path | None, script_text: str) -> None:
    if output_path is None:
        print(script_text)
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(script_text + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    text = read_text(args.input)
    if not text:
        fail("input text is empty")

    script_text = build_script(text, args.intro, args.outro)
    write_output(args.output, script_text)

    if args.output is not None:
        print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
