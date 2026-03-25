# Workflow notes

## Commit attribution

Current temporary setup in this repo uses a GitHub-visible Codex identity:

- Name: `Codex`
- Email: `codex@openai.com`

But the intended long-term policy is slightly different:
- assistant-driven commits should be clearly connected to Edwin as the initiating human
- assistant identity should still be visible in GitHub history
- for Codex-driven work, the preferred shape is: Edwin as author plus a visible `Co-authored-by: Codex <codex@openai.com>` trailer
- for other harnesses, use the same pattern with the appropriate visible assistant identity where possible

This keeps ownership clear while still preserving which agent contributed.

The repo-local identity/config should be updated to match that policy as part of the broader assistant commit-attribution setup.

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

Recommended morning-run shape:
- keep the real destination out of committed docs/scripts
- set env vars in the scheduler environment or provision `.voice_digest_notifier.json` locally
- use `scripts/voice_digest_dispatch_job.py` as the scheduler entrypoint once the destination is wired, because it writes stable delivery status artifacts for success and failure
- use `--openclaw-dry-run` for the first end-to-end send-path verification before one true live delivery
- if the full morning handoff is too long for an attached-audio message body, pass `--audio-message-mode caption` (or set `VOICE_DIGEST_AUDIO_MESSAGE_MODE=caption`) to send a shorter summary instead

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
