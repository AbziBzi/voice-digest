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
The project can now bundle a digest run into a dated artifact folder with a manifest, select the newest digest text file from a drop directory, validate the stable `latest_run.json` handoff, emit a delivery-ready payload for a notifier to consume in live vs dry-run mode, generate a compact overnight checkpoint that summarizes repo state plus latest-run readiness, render one combined morning handoff that merges repo checkpoint + delivery-readiness details into a single text or JSON summary, run one scheduler-friendly morning job that writes stable handoff + payload files for downstream automation, and bridge those outputs into an `openclaw message send` call that attaches audio in live mode or sends a text fallback in dry-run mode. The full morning path is still not yet wired end-to-end to Edwin's real destination and has not yet been exercised as one live delivered morning run.

## Overnight operating model
- Scheduler-driven bounded phases
- Commit/push at real milestones
- Quiet overnight unless something urgent/risky happens
- Morning handoff should say what changed, what works, and what is next

## Next milestone candidates
1. Point the new OpenClaw notifier at Edwin's real Signal/OpenClaw target so the overnight summary is actually surfaced at day start.
2. Exercise one true end-to-end morning run with fresh input and a delivered artifact or fallback.
3. Create a robust spoken-digest format for the real morning digest output.
4. Tighten the scheduler contract so morning failures surface clearly without manual log inspection.
5. Decide whether the live-mode message body should stay as the full morning handoff or become a shorter caption plus attached audio.

## Immediate next step
Configure the real Signal/OpenClaw destination for `voice_digest_openclaw_notifier.py`, then run one true end-to-end morning delivery against that target using the existing `voice_digest_morning_job.py` outputs.

## Follow-up note
Tomorrow's daytime maintenance should also finalize the assistant commit-attribution policy so assistant-originated commits are co-authored in a way that keeps Edwin visible as initiator while showing the specific agent identity.
