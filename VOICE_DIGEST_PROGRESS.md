# Voice Digest Progress

Use this file as the handoff log for the overnight voice-digest R&D track.

## Rules
- Append only when there is real progress.
- Keep entries concise.
- Focus on: what was learned, what changed, blockers, and next step.
- This file is for morning handoff into Edwin's daily digest.

## Entries

### 2026-03-22
- Added `scripts/voice_digest_tts.py`, a minimal Python CLI for turning short digest text into MP3 with ElevenLabs.
- Added a graceful fallback path: when `ELEVENLABS_API_KEY` is missing, the script writes `*.mp3.dry-run.txt` instead of failing.
- Added `sample_digest.txt` plus README usage notes so the flow can be tested quickly.
- Learned: this repo can support a real first prototype without adding package dependencies.
- Live test completed: real ElevenLabs synthesis succeeded and produced `out/sample_digest.mp3`.
- Learned: the previous built-in default voice was a paid-only library voice for this account, so the script default was switched to the premade `River` voice to keep the default path usable.
- Next step: listen to the artifact, then decide whether to tune voice choice, pacing, or delivery.
