# Voice Digest Status

## Current objective
Build a genuinely useful morning voice-digest workflow for Edwin: short spoken brief, visual-aware cues, and reliable morning delivery.

## Current baseline
- Text morning digest delivery works on Signal via explicit cron routing.
- ElevenLabs synthesis works locally via `scripts/voice_digest_tts.py`.
- `scripts/voice_digest_tts.py` now uses OpenAI TTS as the first live fallback when ElevenLabs quota, free-tier limits, or availability become the blocker.
- Spoken-script preparation works via `scripts/voice_digest_prepare.py`.
- Combined script + TTS flow works via `scripts/voice_digest_pipeline.py`.
- Scheduler-friendly run bundling works via `scripts/voice_digest_run.py`.

## Current gap
The project can now bundle a digest run into a dated artifact folder with a manifest, select the newest digest text file from a drop directory, validate the stable `latest_run.json` handoff, emit a delivery-ready payload for a notifier to consume in live vs dry-run mode, generate a compact overnight checkpoint that summarizes repo state plus latest-run readiness, render one combined morning handoff that merges repo checkpoint + delivery-readiness details into a single text or JSON summary, run one scheduler-friendly morning job that writes stable handoff + payload files for downstream automation, bridge those outputs into an `openclaw message send` call that attaches audio in live mode or sends a text fallback in dry-run mode, optionally use a shorter caption instead of the full handoff when sending live audio, and run one top-level dispatch job that executes both phases together while leaving stable `delivery_status.json` / `delivery_status.txt` results behind on success or failure. The remaining gap is no longer scheduler observability; it is wiring Edwin's real OpenClaw/Signal destination and exercising one true live delivered morning run.

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
5. Exercise both live-mode message-body variants against Edwin's real destination and choose whether `full` or `caption` should be the scheduler default.

## Immediate next step
Provision Edwin's real Signal/OpenClaw destination via scheduler env vars or a local `.voice_digest_notifier.json`, run `scripts/voice_digest_dispatch_job.py --send --openclaw-dry-run` once with the new ElevenLabs→OpenAI fallback path in place, then follow it with one true live dispatch run against Edwin's real target.

## Follow-up note
Tomorrow's daytime maintenance should also finalize the assistant commit-attribution policy so assistant-originated commits are co-authored in a way that keeps Edwin visible as initiator while showing the specific agent identity.
