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
- Live audio delivery now supports `audio_message_mode=auto`, which keeps the full morning handoff when it is short enough but automatically falls back to the shorter caption when the handoff grows past the notifier's safe message-length budget; dispatch status artifacts preserve the requested mode, resolved mode, reason, and message-length details.
- Missing-destination notifier failures now emit setup diagnostics in `--json` mode (config-file presence, env-var presence, CLI override presence, and artifact paths), and dispatch status artifacts preserve those diagnostics for faster cron-side wiring triage.
- Actual notifier send-path failures now preserve that same destination/setup diagnostics block in `--json` mode, so first live-send troubleshooting still has the config/env/artifact context instead of only the transport error.
- Malformed local notifier config files now fail with explicit path-aware JSON errors plus preserved `config_load_error` diagnostics in both notifier output and stable dispatch status artifacts, so a bad `.voice_digest_notifier.json` is distinguishable from missing wiring or transport failure during morning triage.
- Invalid notifier `audio_message_mode` values from `VOICE_DIGEST_AUDIO_MESSAGE_MODE` or `.voice_digest_notifier.json` now fail explicitly instead of silently falling back to `full`, and the notifier/dispatch diagnostics preserve the bad source/value so scheduler triage can fix the exact wiring mistake.
- Delivery payloads, morning handoffs, and dispatch status artifacts now surface run age plus selected-input freshness details, so morning triage can tell at a glance whether the upstream digest and generated artifact are actually fresh without opening multiple files.
- Delivery payloads and stable dispatch status artifacts now also describe the actual delivery target artifact itself (exists, size, modified time, age), so morning triage can quickly distinguish “path present in JSON” from “real audio/note artifact exists and is fresh enough to trust.”
- The scheduler-facing dispatch entrypoint can now resolve its upstream digest drop from `VOICE_DIGEST_INPUT_DIR`, and its stable status artifacts record the resolved input path plus whether it came from CLI, env, or the repo default for easier cron wiring/debugging.
- Delivery status artifacts now also include a concise `next_action` hint for common morning states (missing input drop, missing destination wiring, missing OpenClaw CLI, preview-only success, send-path dry-run success, and TTS `--dry-run` text-fallback runs), so the stable handoff says what to do next instead of only what failed.
- Overnight checkpoint and morning handoff summaries now pull the newest top-of-file progress entry from `VOICE_DIGEST_PROGRESS.md`, so morning status no longer regresses to an older dated section when the log is kept newest-first.

## Current gap
The project can now bundle a digest run into a dated artifact folder with a manifest, select the newest digest text file from a drop directory, validate the stable `latest_run.json` handoff, optionally reject stale handoff artifacts by manifest age, emit a delivery-ready payload for a notifier to consume in live vs dry-run mode, generate a compact overnight checkpoint that summarizes repo state plus latest-run readiness, render one combined morning handoff that merges repo checkpoint + delivery-readiness details into a single text or JSON summary, surface run age plus selected-input freshness details inside those downstream payload/handoff artifacts, run one scheduler-friendly morning job that writes stable handoff + payload files for downstream automation, bridge those outputs into an `openclaw message send` call that attaches audio in live mode or sends a text fallback in dry-run mode, optionally use a shorter caption instead of the full handoff when sending live audio, resolve that live-audio message mode from the same CLI/env/local-config stack as the destination wiring, surface the resolved mode in delivery-status diagnostics, fail cleanly when the OpenClaw CLI itself is missing, surface a missing or empty default input drop as a plain operational error with concrete setup guidance, preserve missing-destination wiring diagnostics inside notifier JSON plus `delivery_status.*`, ship the repo with the conventional `incoming_digests/` drop path already present, and run one top-level dispatch job that executes both phases together while leaving stable `delivery_status.json` / `delivery_status.txt` results behind on success or failure. Those stable status artifacts now also include a concise next-step hint for the common blocked/success states plus the specific case where dispatch only proved a text fallback because TTS was still in `--dry-run`, so morning triage does not mistake “scheduler path works” for “real voice artifact is ready.” The remaining gap is no longer repo path scaffolding or opaque scheduler wiring; it is wiring the actual upstream digest input path plus Edwin's real OpenClaw/Signal destination, then exercising one non-`--dry-run` audio-producing run and one true live delivered morning run.

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
Populate the now-present `incoming_digests/` drop (or point the scheduler at the real upstream input directory) and provision Edwin's real Signal/OpenClaw destination via scheduler env vars or a local `.voice_digest_notifier.json`, then run `scripts/voice_digest_dispatch_job.py --send --openclaw-dry-run` once against the intended live input path without `--dry-run` so the pipeline proves a real audio artifact, then follow it with one true live dispatch run against Edwin's real target.

## Follow-up note
Assistant commit-attribution is now wired locally in this repo so Edwin remains the author and Codex stays visible as a co-author. The remaining operational gap is now the real upstream digest input wiring plus Edwin's real OpenClaw/Signal destination and one true delivered morning run.
