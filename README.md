# voice-digest

R&D project for a high-quality voice/audio reading workflow.

## Goal
Build a practical listening-first reading experience for high-signal AI/software writing without losing important visual information like charts, graphs, screenshots, and diagrams.

## Current status
Early research / prototyping.

## Provider direction
Current provider strategy for this project:
- primary: ElevenLabs
- first fallback: OpenAI TTS
- final safe fallback: dry-run text note until more providers are wired

Reason for this policy:
- Edwin is currently on the ElevenLabs free tier, so quota/rate limits are a real operational blocker
- `OPENAI_API_KEY` is already available in the environment
- scheduled workers should therefore treat OpenAI fallback support as an active implementation target

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
- `scripts/voice_digest_delivery_payload.py`
- `scripts/voice_digest_checkpoint.py`
- `scripts/voice_digest_morning_handoff.py`
- `scripts/voice_digest_morning_job.py`
- `scripts/voice_digest_openclaw_notifier.py`
- `scripts/voice_digest_dispatch_job.py`

What they do:
- `voice_digest_prepare.py` turns a text digest into a spoken script with intro/outro and explicit `VISUAL FLAG:` markers
- `voice_digest_tts.py` renders text to MP3 when `ELEVENLABS_API_KEY` is present
- `voice_digest_pipeline.py` runs both steps in one command and writes both the spoken script artifact and MP3
- `voice_digest_run.py` creates a dated run folder with copied input, spoken script, audio or dry-run note, and a JSON manifest
- `voice_digest_from_latest.py` finds the newest matching digest text file in a directory and feeds it into the run bundler for scheduler use
- `voice_digest_scheduler_job.py` adds a stable `out/latest_run.json` handoff file for downstream delivery
- `voice_digest_validate_latest.py` validates that `out/latest_run.json`, the manifest, and the referenced artifacts all agree before delivery
- `voice_digest_delivery_payload.py` validates `out/latest_run.json` and emits a notifier-ready JSON payload that tells a downstream sender what to deliver in `live` vs `dry-run` mode, including run age plus selected-input freshness details
- `voice_digest_checkpoint.py` emits a compact overnight checkpoint with git state, the latest progress entry, and latest-run validation when a handoff file exists
- `voice_digest_morning_handoff.py` combines the checkpoint plus delivery payload into one concise morning-ready text or JSON handoff, including run/input freshness lines for faster morning triage
- `voice_digest_morning_job.py` runs the scheduler flow end-to-end and writes stable `morning_handoff.txt`, `morning_handoff.json`, and `delivery_payload.json` outputs for a cron job or notifier to consume
- `voice_digest_openclaw_notifier.py` reads those stable outputs and turns them into an `openclaw message send` call that either attaches audio in live mode or sends a text fallback in dry-run mode, with support for the full handoff text, a shorter caption, or an `auto` mode that falls back to the caption when the handoff is too long for a comfortable live message body
- `voice_digest_dispatch_job.py` runs the morning job plus notifier together and always writes stable `delivery_status.json` and `delivery_status.txt` files so cron can tell whether the send path succeeded or where it failed
- the TTS step prefers ElevenLabs, falls back to OpenAI TTS when ElevenLabs credentials/availability are the blocker, and only then falls back to a dry-run note at `OUTPUT.mp3.dry-run.txt`

Convention:
- put upstream digest text drops under `incoming_digests/`
- `incoming_digests/` ships with a placeholder file and ignores real local `*.txt` drops by default
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

Or let a scheduler pick the newest digest text from the repo's default drop directory:

```bash
python3 scripts/voice_digest_from_latest.py \
  --input-dir incoming_digests \
  --glob '*.txt' \
  --dry-run
```

The repo already includes `incoming_digests/.gitkeep` so the expected drop path exists immediately after clone; local digest text files placed there stay untracked by default.

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

And you can emit a delivery-ready payload for a notifier with:

```bash
python3 scripts/voice_digest_delivery_payload.py
```

For an overnight handoff / checkpoint summary:

```bash
python3 scripts/voice_digest_checkpoint.py
```

For one combined morning-ready handoff:

```bash
python3 scripts/voice_digest_morning_handoff.py
```

For one scheduler-friendly morning job that also writes stable handoff/payload files:

```bash
python3 scripts/voice_digest_morning_job.py \
  --input-dir incoming_digests \
  --dry-run
```

If downstream automation should reject stale artifacts instead of reusing an old `latest_run.json`, add a freshness guard:

```bash
python3 scripts/voice_digest_morning_job.py \
  --input-dir incoming_digests \
  --dry-run \
  --max-age-minutes 180
```

By default this writes:
- `out/latest_run.json`
- `out/morning_handoff.txt`
- `out/morning_handoff.json`
- `out/delivery_payload.json`

To bridge that into OpenClaw messaging in preview mode:

```bash
python3 scripts/voice_digest_openclaw_notifier.py \
  --channel signal \
  --target +37060000000
```

For cron-friendly use, you can also configure the destination once via env vars:

```bash
export VOICE_DIGEST_OPENCLAW_CHANNEL=signal
export VOICE_DIGEST_OPENCLAW_TARGET=+37060000000
python3 scripts/voice_digest_openclaw_notifier.py
```

Or via a repo-local config file at `.voice_digest_notifier.json`:

```json
{
  "channel": "signal",
  "target": "+37060000000",
  "audio_message_mode": "caption"
}
```

The notifier resolves the destination in this order: CLI args, then env vars, then config file. For live audio sends, `audio_message_mode` follows the same precedence: CLI flag, then `VOICE_DIGEST_AUDIO_MESSAGE_MODE`, then config file, then `full`. Supported values are `full`, `caption`, and `auto`; `auto` keeps the full handoff until it exceeds the notifier's safe message-length budget, then switches to the shorter caption automatically.

To verify the real OpenClaw send path without delivering a message:

```bash
python3 scripts/voice_digest_openclaw_notifier.py \
  --send \
  --openclaw-dry-run
```

And to actually send the morning digest once the target is confirmed:

```bash
python3 scripts/voice_digest_openclaw_notifier.py \
  --send
```

If the attached-audio message body should be shorter than the full morning handoff, use caption mode:

```bash
python3 scripts/voice_digest_openclaw_notifier.py \
  --send \
  --audio-message-mode caption
```

If you want the notifier to keep the full handoff when it is reasonably short but automatically switch to the shorter caption for long morning summaries, use auto mode:

```bash
python3 scripts/voice_digest_openclaw_notifier.py \
  --send \
  --audio-message-mode auto
```

Or set it once for the scheduler environment:

```bash
export VOICE_DIGEST_AUDIO_MESSAGE_MODE=caption
```

```bash
export VOICE_DIGEST_AUDIO_MESSAGE_MODE=auto
```

For one scheduler-facing command that builds the morning artifacts, exercises the notifier, and leaves stable delivery-status files behind:

```bash
python3 scripts/voice_digest_dispatch_job.py \
  --input-dir incoming_digests \
  --send \
  --openclaw-dry-run
```

If you want the top-level scheduler entrypoint to stop after an environment/readiness check, use:

```bash
python3 scripts/voice_digest_dispatch_job.py \
  --input-dir incoming_digests \
  --check-setup
```

That run still builds the current morning artifacts, then calls the notifier's readiness probe and writes stable `out/delivery_status.json` / `out/delivery_status.txt` outputs that say whether the remaining blocker is upstream input generation, the referenced delivery artifact itself missing, destination wiring, config validity, or `openclaw` availability.

Recommended first-live checklist:

1. Put a fresh digest text file in `incoming_digests/` or set `VOICE_DIGEST_INPUT_DIR` to the real upstream drop.
2. Copy `.voice_digest_notifier.example.json` to `.voice_digest_notifier.json` and replace the sample target with the real Signal/OpenClaw destination.
3. Run `python3 scripts/voice_digest_dispatch_job.py --check-setup` until `out/delivery_status.txt` reports a ready notifier environment.
4. Run `python3 scripts/voice_digest_dispatch_job.py --send --openclaw-dry-run` to verify the true send path without delivering.
5. Run `python3 scripts/voice_digest_dispatch_job.py --send` for the first real morning delivery.

If cron should point at a different upstream drop path without carrying another CLI flag, set:

```bash
export VOICE_DIGEST_INPUT_DIR=/absolute/path/to/upstream/digests
python3 scripts/voice_digest_dispatch_job.py \
  --send \
  --openclaw-dry-run
```

`delivery_status.json` / `delivery_status.txt` now record both the resolved `input_dir` and whether it came from `cli`, `env`, or the repo `default`.

That same entrypoint can carry the freshness guard through to the morning handoff + payload validation steps:

```bash
python3 scripts/voice_digest_dispatch_job.py \
  --input-dir incoming_digests \
  --send \
  --openclaw-dry-run \
  --max-age-minutes 180
```

To test the shorter live-audio caption path through the full dispatch flow:

```bash
python3 scripts/voice_digest_dispatch_job.py \
  --input-dir incoming_digests \
  --send \
  --openclaw-dry-run \
  --audio-message-mode caption
```

By default this also writes:
- `out/delivery_status.json`
- `out/delivery_status.txt`

`delivery_status.json` records whether the failure happened in the morning build or notifier stage, plus the selected input, mode, destination when known, notifier setup diagnostics (for example whether the local config file exists and whether destination env vars were set), and the stable artifact paths a scheduler can inspect.

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

## Commit attribution policy
Assistant-driven commits in this repo should keep Edwin as the author and add a visible assistant trailer such as:

`Co-authored-by: Codex <codex@openai.com>`

The repo-local commit template `.gitmessage-assistant` is intended to make that shape the easy default.
