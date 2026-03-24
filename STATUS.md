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
The project can now bundle a digest run into a dated artifact folder with a manifest, select the newest digest text file from a drop directory, validate the stable `latest_run.json` handoff, emit a delivery-ready payload for a notifier to consume in live vs dry-run mode, generate a compact overnight checkpoint that summarizes repo state plus latest-run readiness, render one combined morning handoff that merges repo checkpoint + delivery-readiness details into a single text or JSON summary, and run one scheduler-friendly morning job that writes stable handoff + payload files for downstream automation. The full morning path is still not yet wired so Edwin reliably receives a good spoken digest automatically.

## Overnight operating model
- Scheduler-driven bounded phases
- Commit/push at real milestones
- Quiet overnight unless something urgent/risky happens
- Morning handoff should say what changed, what works, and what is next

## Next milestone candidates
1. Point a real Signal/OpenClaw notifier at the stable `out/morning_handoff.txt` and/or `out/delivery_payload.json` outputs so the overnight summary is actually surfaced at day start.
2. Create a robust spoken-digest format for the real morning digest output.
3. Validate the cleanest delivery path for morning audio on Signal/OpenClaw.
4. Exercise one true end-to-end morning run with fresh input and a delivered artifact or fallback.
5. Tighten the scheduler contract so morning failures surface clearly without manual log inspection.

## Immediate next step
Point a real scheduler, notifier, or morning automation at `voice_digest_morning_job.py` so it writes stable `out/morning_handoff.txt` and `out/delivery_payload.json` outputs by default, then wire a Signal/OpenClaw bridge that actually sends the live artifact or dry-run fallback.

## Follow-up note
Tomorrow's daytime maintenance should also finalize the assistant commit-attribution policy so assistant-originated commits are co-authored in a way that keeps Edwin visible as initiator while showing the specific agent identity.
