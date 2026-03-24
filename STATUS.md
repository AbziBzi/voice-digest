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
The project can now bundle a digest run into a dated artifact folder with a manifest, select the newest digest text file from a drop directory, validate the stable `latest_run.json` handoff, emit a delivery-ready payload for a notifier to consume in live vs dry-run mode, generate a compact overnight checkpoint that summarizes repo state plus latest-run readiness, and render one combined morning handoff that merges repo checkpoint + delivery-readiness details into a single text or JSON summary. The full morning path is still not yet wired so Edwin reliably receives a good spoken digest automatically.

## Overnight operating model
- Scheduler-driven bounded phases
- Commit/push at real milestones
- Quiet overnight unless something urgent/risky happens
- Morning handoff should say what changed, what works, and what is next

## Next milestone candidates
1. Point a real scheduler or notifier at the new morning handoff output so the overnight summary is actually surfaced at day start.
2. Create a robust spoken-digest format for the real morning digest output.
3. Wire a safe scheduled job that can create the spoken artifact from the morning digest text.
4. Validate the cleanest delivery path for morning audio on Signal/OpenClaw.
5. Exercise one true end-to-end morning run with fresh input and a delivered artifact or fallback.

## Immediate next step
Point a real scheduler, notifier, or morning automation at `voice_digest_morning_handoff.py` so the overnight summary becomes visible by default, then wire a notifier or Signal/OpenClaw bridge that consumes `voice_digest_delivery_payload.py` output and actually sends the live artifact or dry-run fallback.

## Follow-up note
Tomorrow's daytime maintenance should also finalize the assistant commit-attribution policy so assistant-originated commits are co-authored in a way that keeps Edwin visible as initiator while showing the specific agent identity.
