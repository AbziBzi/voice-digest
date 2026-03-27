# Voice Digest Status

## Current objective
Build a genuinely useful morning voice-digest workflow for Edwin: short spoken brief, visual-aware cues, and reliable morning delivery.

## Current baseline
- Text morning digest delivery works on Signal via explicit cron routing.
- ElevenLabs synthesis works locally via `scripts/voice_digest_tts.py`.
- `scripts/voice_digest_tts.py` now uses OpenAI TTS as the first live fallback when ElevenLabs quota, free-tier limits, or availability become the blocker.
- Spoken-script preparation works via `scripts/voice_digest_prepare.py`, now with tighter visual-flag heuristics that avoid false positives from ordinary prose and skip boilerplate end markers.
- Combined script + TTS flow works via `scripts/voice_digest_pipeline.py`.
- Scheduler-friendly run bundling works via `scripts/voice_digest_run.py`.
- Dispatch status artifacts now include the underlying failing notifier/morning-job error detail, so missing destination wiring and similar cron issues surface directly in `out/delivery_status.*`.
- The OpenClaw notifier send path now fails cleanly when the `openclaw` CLI is missing from `PATH`, returning a structured operational error instead of a Python traceback.
- OpenClaw send failures now stay structured in `--json` mode, so dispatch status artifacts can preserve the notifier plan plus a clear send-error summary instead of degrading into generic stderr parsing.
- Delivery payloads and morning handoffs now surface run age plus selected-input freshness details, so morning triage can tell at a glance whether the upstream digest and generated artifact are actually fresh.

## Current gap
The project can now bundle a digest run into a dated artifact folder with a manifest, select the newest digest text file from a drop directory, validate the stable `latest_run.json` handoff, optionally reject stale handoff artifacts by manifest age, emit a delivery-ready payload for a notifier to consume in live vs dry-run mode, generate a compact overnight checkpoint that summarizes repo state plus latest-run readiness, render one combined morning handoff that merges repo checkpoint + delivery-readiness details into a single text or JSON summary, surface run age plus selected-input freshness details inside those downstream payload/handoff artifacts, run one scheduler-friendly morning job that writes stable handoff + payload files for downstream automation, bridge those outputs into an `openclaw message send` call that attaches audio in live mode or sends a text fallback in dry-run mode, optionally use a shorter caption instead of the full handoff when sending live audio, resolve that live-audio message mode from the same CLI/env/local-config stack as the destination wiring, surface the resolved mode in delivery-status diagnostics, fail cleanly when the OpenClaw CLI itself is missing, surface a missing or empty default input drop as a plain operational error with concrete setup guidance, ship the repo with the conventional `incoming_digests/` drop path already present, and run one top-level dispatch job that executes both phases together while leaving stable `delivery_status.json` / `delivery_status.txt` results behind on success or failure. The remaining gap is no longer repo path scaffolding, downstream artifact freshness, or missing-CLI diagnostics; it is wiring the actual upstream digest input path plus Edwin's real OpenClaw/Signal destination and exercising one true live delivered morning run.

## Overnight operating model
- Scheduler-driven bounded phases
- Commit/push at real milestones
- Quiet overnight unless something urgent/risky happens
- Morning handoff should say what changed, what works, and what is next

## Next milestone candidates
1. Point the new OpenClaw notifier at Edwin's real Signal/OpenClaw target so the overnight summary is actually surfaced at day start.
2. Exercise one true end-to-end morning run with fresh input and a delivered artifact or fallback.
3. Create a robust spoken-digest format for the real morning digest output.
4. Tighten the scheduler contract so morning failures surface clearly without manual log inspection. (Now improved for dispatch-status artifacts, missing-CLI notifier failures, and structured OpenClaw send-failure reporting; remaining work is exercising the real wired destination.)
5. Exercise both live-mode message-body variants against Edwin's real destination and choose whether `full` or `caption` should be the scheduler default.

## Immediate next step
Populate the now-present `incoming_digests/` drop (or point the scheduler at the real upstream input directory) and provision Edwin's real Signal/OpenClaw destination via scheduler env vars or a local `.voice_digest_notifier.json`, then run `scripts/voice_digest_dispatch_job.py --send --openclaw-dry-run` once with the intended live input path and message mode, then follow it with one true live dispatch run against Edwin's real target.

## Follow-up note
Assistant commit-attribution is now wired locally in this repo so Edwin remains the author and Codex stays visible as a co-author. The remaining operational gap is now the real upstream digest input wiring plus Edwin's real OpenClaw/Signal destination and one true delivered morning run.
