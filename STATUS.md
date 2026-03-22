# Voice Digest Status

## Current objective
Build a genuinely useful morning voice-digest workflow for Edwin: short spoken brief, visual-aware cues, and reliable morning delivery.

## Current baseline
- Text morning digest delivery works on Signal via explicit cron routing.
- ElevenLabs synthesis works locally via `scripts/voice_digest_tts.py`.
- Spoken-script preparation works via `scripts/voice_digest_prepare.py`.
- Combined script + TTS flow works via `scripts/voice_digest_pipeline.py`.
- Scheduler-friendly run bundling works via `scripts/voice_digest_run.py`.

## Current gap
The project can now bundle a digest run into a dated artifact folder with a manifest, but the full morning path is not yet wired so Edwin reliably receives a good spoken digest automatically.

## Overnight operating model
- Scheduler-driven bounded phases
- Commit/push at real milestones
- Quiet overnight unless something urgent/risky happens
- Morning handoff should say what changed, what works, and what is next

## Next milestone candidates
1. Add a project-local checkpoint script / status updater for overnight runs.
2. Create a robust spoken-digest format for the real morning digest output.
3. Wire a safe scheduled job that can create the spoken artifact from the morning digest text.
4. Validate the cleanest delivery path for morning audio on Signal/OpenClaw.
5. Add a morning summary that reports overnight repo progress clearly.

## Immediate next step
Use the new run bundle in a real scheduled job, then validate the cleanest delivery path for the generated audio artifact.
