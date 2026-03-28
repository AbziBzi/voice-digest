# Workflow notes

## Commit attribution

This repo now uses the intended assistant-attribution policy locally:

- git author: Edwin (`Edwin Zubowicz <edwin.zubowicz@gmail.com>`)
- assistant visibility: a visible `Co-authored-by: Codex <codex@openai.com>` trailer in assistant-driven commits
- repo-local helper: `.gitmessage-assistant`, wired via `git config --local commit.template .gitmessage-assistant`

For other harnesses, keep the same shape:
- Edwin remains the commit author when he is the initiating human
- the specific assistant stays visible through a matching `Co-authored-by:` trailer when possible

This keeps ownership clear while still preserving which agent contributed.

## Overnight workflow

For overnight project work, default to this pattern:
- read `STATUS.md`, `OVERNIGHT_POLICY.md`, and `NIGHTLY_TASK.md`
- choose one bounded milestone
- verify before commit
- commit and push milestone progress
- leave the next action explicit for the next overnight phase

## Notifier destination wiring

The morning notifier can now get its OpenClaw destination from any of these sources, in priority order:
- CLI flags: `--channel ... --target ...`
- env vars: `VOICE_DIGEST_OPENCLAW_CHANNEL` and `VOICE_DIGEST_OPENCLAW_TARGET`
- repo-local config file: `.voice_digest_notifier.json`

The live-audio message-body mode now follows the same operational pattern:
- CLI flag: `--audio-message-mode ...`
- env var: `VOICE_DIGEST_AUDIO_MESSAGE_MODE`
- repo-local config file field: `audio_message_mode`
- default: `full`

Recommended morning-run shape:
- keep the real destination out of committed docs/scripts
- set env vars in the scheduler environment or provision `.voice_digest_notifier.json` locally
- if the upstream digest generator writes somewhere other than the repo default drop, set `VOICE_DIGEST_INPUT_DIR` for `voice_digest_dispatch_job.py` so cron wiring can point at the real source path without growing another flag in the scheduler entry
- if the preferred live message shape is already known, store `audio_message_mode` alongside the destination in that same local config so cron does not need an extra flag
- use `scripts/voice_digest_dispatch_job.py` as the scheduler entrypoint once the destination is wired, because it writes stable delivery status artifacts for success and failure
- consider `--max-age-minutes 180` (or a similar window) in scheduler automation so downstream delivery rejects stale `latest_run.json` artifacts instead of reusing yesterday's bundle by accident
- use `python3 scripts/voice_digest_openclaw_notifier.py --check-setup --json` when you want a direct readiness answer about payload/handoff/config/CLI wiring only
- use `python3 scripts/voice_digest_dispatch_job.py --input-dir ... --check-setup` when you want the top-level scheduler entrypoint to regenerate morning artifacts, run that same readiness probe, and leave stable `delivery_status.*` artifacts behind for morning triage
- use `--openclaw-dry-run` for the first end-to-end send-path verification before one true live delivery
- if the full morning handoff is too long for an attached-audio message body, pass `--audio-message-mode caption`, set `VOICE_DIGEST_AUDIO_MESSAGE_MODE=caption`, or write `"audio_message_mode": "caption"` in `.voice_digest_notifier.json`

## TTS provider policy

The intended provider order for this project is:
1. ElevenLabs as the primary premium voice path
2. OpenAI TTS as the first fallback when ElevenLabs quota, free-tier limits, or transient provider issues block synthesis
3. dry-run note output as the safe final fallback until additional providers are wired

Important operating assumptions:
- `OPENAI_API_KEY` is already available in the environment and should be preferred over asking Edwin for another OpenAI key
- scheduled workers should treat OpenAI fallback support as a real project requirement, not a speculative idea
- if ElevenLabs fails for quota/capacity reasons, the next best milestone is usually OpenAI fallback wiring rather than more ElevenLabs-only polish
- future fallback providers like AWS Polly, Google Cloud TTS, or a local model can be added later, but OpenAI is the current planned fallback target
