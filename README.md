# voice-digest

R&D project for a high-quality voice/audio reading workflow.

## Goal
Build a practical listening-first reading experience for high-signal AI/software writing without losing important visual information like charts, graphs, screenshots, and diagrams.

## Current status
Early research / prototyping.

## Prototype
Small first useful prototype: a dependency-free Python CLI that can turn a short digest text into MP3 via ElevenLabs.

Script:
- `scripts/voice_digest_tts.py`

What it does:
- reads digest text from `stdin` or `--input`
- writes an MP3 to `--output` when `ELEVENLABS_API_KEY` is present
- falls back to a dry-run note at `OUTPUT.mp3.dry-run.txt` when the key is missing or `--dry-run` is used

Convention:
- put generated audio and dry-run artifacts under `out/`
- `out/` is treated as disposable and is ignored by git except for a placeholder file

Usage:

```bash
python3 scripts/voice_digest_tts.py \
  --input sample_digest.txt \
  --output out/digest.mp3
```

```bash
printf 'Short digest for audio.\n' | python3 scripts/voice_digest_tts.py --output out/digest.mp3
```

Dry run without hitting the API:

```bash
python3 scripts/voice_digest_tts.py \
  --input sample_digest.txt \
  --output out/digest.mp3 \
  --dry-run
```

Optional environment variables:
- `ELEVENLABS_API_KEY` for real synthesis
- `ELEVENLABS_VOICE_ID` to override the default voice

Tested note:
- live synthesis succeeded on 2026-03-22 with the built-in premade voice `River` and wrote `out/sample_digest.mp3`
- `ELEVENLABS_MODEL_ID` to override the default model
- `ELEVENLABS_API_BASE` only if a non-default API base is needed

Notes:
- the script never prints secret values
- generated audio is not committed; keep outputs under ignored or disposable paths as needed
- this is intentionally small and only targets short digest text for now

## Principles
- Quality over speed
- Keep secrets out of the repo
- Prefer practical and low-cost solutions
- Treat this like a real product project: notes, commits, experiments, iteration

## Attribution test
This commit exists to validate assistant-vs-human git attribution in the repo history.
