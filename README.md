# voice-digest

R&D project for a high-quality voice/audio reading workflow.

## Goal
Build a practical listening-first reading experience for high-signal AI/software writing without losing important visual information like charts, graphs, screenshots, and diagrams.

## Current status
Early research / prototyping.

## Prototype
Small first useful prototype: a dependency-free Python path that can turn a short digest text into a spoken-friendly script and then into MP3 via ElevenLabs.

Scripts:
- `scripts/voice_digest_prepare.py`
- `scripts/voice_digest_tts.py`
- `scripts/voice_digest_pipeline.py`
- `scripts/voice_digest_run.py`
- `scripts/voice_digest_from_latest.py`
- `scripts/voice_digest_scheduler_job.py`
- `scripts/voice_digest_validate_latest.py`

What they do:
- `voice_digest_prepare.py` turns a text digest into a spoken script with intro/outro and explicit `VISUAL FLAG:` markers
- `voice_digest_tts.py` renders text to MP3 when `ELEVENLABS_API_KEY` is present
- `voice_digest_pipeline.py` runs both steps in one command and writes both the spoken script artifact and MP3
- `voice_digest_run.py` creates a dated run folder with copied input, spoken script, audio or dry-run note, and a JSON manifest
- `voice_digest_from_latest.py` finds the newest matching digest text file in a directory and feeds it into the run bundler for scheduler use
- `voice_digest_scheduler_job.py` adds a stable `out/latest_run.json` handoff file for downstream delivery
- `voice_digest_validate_latest.py` validates that `out/latest_run.json`, the manifest, and the referenced artifacts all agree before delivery
- the TTS step falls back to a dry-run note at `OUTPUT.mp3.dry-run.txt` when the key is missing or `--dry-run` is used

Convention:
- put generated audio and dry-run artifacts under `out/`
- `out/` is treated as disposable and is ignored by git except for a placeholder file

Usage:

Prepare a spoken script only:

```bash
python3 scripts/voice_digest_prepare.py \
  --input sample_digest.txt \
  --output out/digest.spoken.txt
```

Run the full pipeline:

```bash
python3 scripts/voice_digest_pipeline.py \
  --input sample_digest.txt \
  --output out/digest.mp3
```

TTS only:

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
python3 scripts/voice_digest_pipeline.py \
  --input sample_digest.txt \
  --output out/digest.mp3 \
  --dry-run
```

Create one scheduler-friendly run bundle:

```bash
python3 scripts/voice_digest_run.py \
  --input sample_digest.txt \
  --dry-run
```

Or let a scheduler pick the newest digest text from a drop directory:

```bash
python3 scripts/voice_digest_from_latest.py \
  --input-dir incoming_digests \
  --glob '*.txt' \
  --dry-run
```

This writes a run folder under `out/runs/YYYY-MM-DD/RUN_ID/` containing:
- `digest.txt`
- `spoken.txt`
- `digest.mp3` or `digest.mp3.dry-run.txt`
- `manifest.json`

And the scheduler wrapper writes a stable JSON handoff file like `out/latest_run.json` with the selected input path, run directory, manifest path, spoken script path, audio path, dry-run note path when present, and mode (`live` or `dry-run`).

You can validate that handoff before delivery with:

```bash
python3 scripts/voice_digest_validate_latest.py
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
 attribution in the repo history.
