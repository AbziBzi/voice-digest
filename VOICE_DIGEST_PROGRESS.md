# Voice Digest Progress

Use this file as the handoff log for the overnight voice-digest R&D track.

## Rules
- Append only when there is real progress.
- Keep entries concise.
- Focus on: what was learned, what changed, blockers, and next step.
- This file is for morning handoff into Edwin's daily digest.

## Entries

### 2026-03-27
- Fixed `scripts/voice_digest_checkpoint.py` so overnight checkpoint / morning handoff summaries now treat the topmost dated section in `VOICE_DIGEST_PROGRESS.md` as the latest entry, matching the file’s newest-first layout instead of accidentally surfacing the older trailing section.
- Added `tests/test_voice_digest_checkpoint.py` to lock in that newest-first progress parsing behavior.
- Verification passed in three layers: the new unit test succeeded, the full `python3 -m unittest discover -s tests -p 'test_*.py'` suite passed, and a repo-root `voice_digest_dispatch_job.py --dry-run --send --openclaw-dry-run` run regenerated `out/morning_handoff.txt` with a `Latest progress` line from today’s 2026-03-27 section rather than the stale 2026-03-25 block.
- Learned: morning trust depends on the handoff selecting the right human-facing progress note; a small newest-vs-last parser assumption can quietly make the project look older than it is.
- Next step: once Edwin’s real input path and destination are wired, rerun the same scheduler-facing dry-run against that intended live configuration and choose the default live audio message mode from real delivery feedback.
- Tightened `scripts/voice_digest_prepare.py` so spoken-script generation no longer turns ordinary prose into `VISUAL FLAG:` lines just because it contains generic words like “image”; visual cues now require either an explicit visual prefix or a stronger “review this visual” pattern.
- Also taught the spoken-prep step to drop boilerplate end markers like `End of article.` so TTS output sounds cleaner on full-article inputs.
- Added `tests/test_voice_digest_prepare.py` with regression coverage for explicit visual markers, false-positive avoidance, review-language detection, and end-marker stripping.
- Verification passed in two layers: `python3 -m unittest tests/test_voice_digest_prepare.py` succeeded, and `python3 scripts/voice_digest_prepare.py --input out/article7-world-models-full.txt` no longer misclassified the “synthesized image” paragraph as a visual flag.
- Learned: spoken-digest UX is brittle when visual detection uses raw keyword presence; daily-digest inputs need tighter heuristics so audio emphasis feels intentional instead of noisy.
- Next step: keep pushing the listening UX toward real morning use by shortening or restructuring long-form article output into a more bounded spoken brief before synthesis.
- Hardened the notifier/dispatch failure contract so `scripts/voice_digest_openclaw_notifier.py --json` now returns structured error payloads for real `openclaw message send` failures too, not just missing-CLI cases, and `scripts/voice_digest_dispatch_job.py` now prefers those structured fields when writing `delivery_status.json` / `delivery_status.txt`.
- Added regression tests for both layers: notifier tests cover structured JSON emission on send failure, and dispatch tests cover preserving destination/mode plus a clean send-error summary in the stable status artifact.
- Verification passed in two layers: `python3 -m py_compile scripts/voice_digest_openclaw_notifier.py scripts/voice_digest_dispatch_job.py tests/test_voice_digest_notifier.py tests/test_voice_digest_dispatch_job.py` succeeded, and `python3 -m unittest tests.test_voice_digest_notifier tests.test_voice_digest_dispatch_job` passed.
- Learned: the scheduler-facing status artifact is only as good as the notifier’s error shape — once send failures stay structured, morning triage can retain both the operational context (destination/mode) and the actual transport failure instead of collapsing into opaque stderr blobs.
- Next step: keep the remaining work on the true integration boundary by exercising one real destination-wired `--openclaw-dry-run` dispatch, then one live delivery once the upstream digest drop and Signal target are in place.

### 2026-03-26
- Defaulted `scripts/voice_digest_dispatch_job.py --input-dir` to the repo’s conventional `incoming_digests/` drop directory, so the scheduler-facing entrypoint now matches the README command shape instead of failing fast on a missing required flag.
- Verification passed in two layers: `python3 -m py_compile scripts/voice_digest_dispatch_job.py` succeeded, and a temp no-flag dispatch run succeeded after copying a sample digest into `incoming_digests/`, confirming the defaulted entrypoint exercised the full dry-run send path.
- Learned: the most immediate delivery-path paper cut was no longer notifier logic but scheduler ergonomics — the “one command” dispatch wrapper should really be runnable with the repo’s conventional drop directory by default.
- Next step: provision Edwin's real Signal/OpenClaw target and run one final `voice_digest_dispatch_job.py --send --openclaw-dry-run` check against the intended live destination wiring before a true live dispatch.

- Hardened `scripts/voice_digest_openclaw_notifier.py` so `--send` now checks for an available `openclaw` CLI and returns a clean operational error instead of crashing with a Python traceback when the binary is missing or cannot be executed.
- Verification passed in three layers: `python3 -m py_compile scripts/voice_digest_openclaw_notifier.py` succeeded, a temp notifier `--send --openclaw-dry-run --json` run with `PATH=/usr/bin:/bin` returned a structured `status: error` payload with the planned send metadata, and a temp end-to-end `voice_digest_dispatch_job.py --dry-run --send --openclaw-dry-run` run under that same restricted `PATH` failed at `notifier_send` while `delivery_status.txt` preserved the resolved destination/mode plus the explicit missing-CLI error.
- Learned: the real morning send path now fails like an operational integration boundary instead of an uncaught script exception, which makes cron-visible diagnostics materially sharper before the first live destination run.
- Next step: provision Edwin's real Signal/OpenClaw target and run one final `voice_digest_dispatch_job.py --send --openclaw-dry-run` check in the intended environment before a true live dispatch.

### 2026-03-22
- Added `scripts/voice_digest_tts.py`, a minimal Python CLI for turning short digest text into MP3 with ElevenLabs.
- Added a graceful fallback path: when `ELEVENLABS_API_KEY` is missing, the script writes `*.mp3.dry-run.txt` instead of failing.
- Added `sample_digest.txt` plus README usage notes so the flow can be tested quickly.
- Learned: this repo can support a real first prototype without adding package dependencies.
- Live test completed: real ElevenLabs synthesis succeeded and produced `out/sample_digest.mp3`.
- Learned: the previous built-in default voice was a paid-only library voice for this account, so the script default was switched to the premade `River` voice to keep the default path usable.
- Next step: listen to the artifact, then decide whether to tune voice choice, pacing, or delivery.
- Added `scripts/voice_digest_prepare.py`, which converts digest text into a spoken-friendly script with a stable intro/outro and explicit `VISUAL FLAG:` markers for charts, diagrams, and similar screen-first content.
- Added `scripts/voice_digest_pipeline.py`, a tiny wrapper that generates both the spoken-script artifact and the MP3 in one command.
- Dry-run verification passed end-to-end: the pipeline wrote `out/sample_pipeline.spoken.txt` and `out/sample_pipeline.mp3.dry-run.txt` from `sample_digest.txt`.
- Learned: the right near-term product shape is probably not "read the whole digest verbatim", but "prepare a short spoken brief first, then synthesize that curated script."
- Next step: wire the morning digest flow so the scheduled digest can emit a concise spoken version automatically.
- Added `scripts/voice_digest_run.py`, a thin scheduler-oriented wrapper that creates a dated run directory with copied digest input, `spoken.txt`, audio or dry-run note, and `manifest.json`.
- Dry-run verification passed with `sample_digest.txt`, producing one inspectable run bundle under `out/runs/`.
- Learned: a manifest-backed run folder is a better contract for cron and morning handoff than loose output filenames.
- Next step: call the run wrapper from the real morning scheduler and confirm downstream delivery/inspection behavior.
- Added `scripts/voice_digest_from_latest.py`, a scheduler-oriented entrypoint that selects the newest matching digest text file from a directory and feeds it into the existing run bundler.
- Dry-run verification passed against a temp `incoming/` directory with two digest files; the script correctly selected the newer file and produced a complete run bundle with `digest.txt`, `spoken.txt`, `digest.mp3.dry-run.txt`, and `manifest.json`.
- Learned: the cleanest near-term scheduler contract is now "drop digest text files into a directory, then let the voice job pick the newest one" instead of hardcoding a single source filename.
- Next step: point a real morning cron/job at this entrypoint and validate audio delivery or retrieval in Edwin's actual morning flow.
- Added `scripts/voice_digest_scheduler_job.py`, a cron-oriented wrapper that calls the latest-digest entrypoint and writes a stable `out/latest_run.json` handoff file for downstream delivery.
- Dry-run verification passed against a temp `incoming/` directory: the scheduler job selected the newest digest, created a complete run bundle, and wrote a state file with the run directory, manifest path, spoken script path, audio path, dry-run note path, and run mode.
- Learned: the cleanest next integration contract is now "upstream digest drops text, scheduler job creates the audio bundle, downstream delivery reads `latest_run.json`".
- Next step: wire a real morning scheduler invocation to this wrapper, then validate how Signal/OpenClaw should deliver or surface the resulting audio artifact.
- Added `scripts/voice_digest_validate_latest.py`, a small readiness check that validates `out/latest_run.json`, the referenced manifest, and artifact consistency before downstream delivery tries to use them.
- Dry-run verification passed end-to-end: a temp scheduler job wrote `out/test-latest-run.json`, and the validator accepted it in `dry-run` mode while checking the manifest, spoken script, and dry-run note paths.
- Learned: the downstream contract is now strong enough to fail fast with a clear reason instead of discovering a broken handoff only at delivery time.
- Next step: wire the real scheduler job and then build or test the delivery consumer that reads validated latest-run state.

### 2026-03-23
- Added `scripts/voice_digest_delivery_payload.py`, a downstream consumer that validates `latest_run.json` and emits a notifier-ready JSON payload with explicit `send_audio` vs `send_text_fallback` behavior.
- Refactored `scripts/voice_digest_validate_latest.py` to expose reusable validation data so downstream consumers can share the same handoff checks instead of reimplementing them.
- Dry-run verification passed end-to-end: a temp scheduler job selected the newest digest, the validator accepted the generated `latest_run.json`, and the new payload script emitted a delivery-ready JSON summary with artifact paths and a spoken preview.
- Learned: the next integration contract is now stable enough for a notifier to remain thin, because live vs dry-run branching can be decided from one validated payload instead of re-reading multiple files.
- Next step: connect a real notifier or Signal/OpenClaw bridge to this payload and test one actual morning delivery path.
- Added `scripts/voice_digest_checkpoint.py`, a small overnight handoff helper that reports git branch/head, working-tree cleanliness, the latest progress entry, and validated latest-run details when `out/latest_run.json` exists.
- Verification passed in both text and JSON modes: the checkpoint script reported the repo state cleanly before commit and included the expected latest progress section without requiring a live delivery path.
- Learned: the delivery hop is still the risky integration boundary, so a project-local checkpoint is a good bounded milestone because it improves morning visibility without pretending Signal/OpenClaw audio sending is solved.
- Next step: either feed the checkpoint output into the morning digest handoff or move on to a thin notifier bridge once the cleanest delivery mechanism is confirmed.
- Added `scripts/voice_digest_morning_handoff.py`, a small morning-readiness wrapper that combines the overnight checkpoint and the validated delivery payload into one concise text or JSON handoff.
- Verification passed in both states: the new script reported a clear "no latest_run.json yet" next action, and after a temp dry-run scheduler run it emitted a delivery-ready handoff with selected input, artifact paths, and spoken preview.
- Learned: the morning summary no longer needs to re-stitch repo state and delivery readiness from multiple scripts, which makes the next notifier/scheduler integration thinner.
- Next step: point a real morning automation or notifier at `voice_digest_morning_handoff.py`, then test one true end-to-end delivery path.

### 2026-03-24
- Added `scripts/voice_digest_morning_job.py`, a scheduler-friendly wrapper that runs the latest-digest selection + run bundle step and writes stable `morning_handoff.txt`, `morning_handoff.json`, and `delivery_payload.json` outputs for downstream automation.
- Dry-run verification passed end-to-end against a temp incoming digest directory: the new morning job selected the newest digest, created a run bundle, wrote `latest_run.json`, and emitted the stable handoff/payload files with delivery-ready content.
- Learned: the cleanest next integration contract is now a single job invocation that leaves stable files for a notifier or OpenClaw bridge, instead of requiring cron to chain multiple scripts itself.
- Next step: wire a real Signal/OpenClaw notifier to consume `out/delivery_payload.json` and/or `out/morning_handoff.txt`, then test one true end-to-end morning delivery path.
- Added `scripts/voice_digest_openclaw_notifier.py`, a thin OpenClaw bridge that reads the stable morning payload/handoff files and turns them into an `openclaw message send` call, attaching audio in live mode or sending a text fallback in dry-run mode.
- Verification passed in two layers: preview mode rendered the exact send command from temp-generated `morning_handoff.txt` and `delivery_payload.json`, and `--send --openclaw-dry-run` successfully exercised the OpenClaw CLI send path without actually delivering a message.
- Learned: the repo now has a real notifier boundary with a safe dry-run path, so the remaining unknown is the real destination wiring and message shape rather than whether the project can bridge into OpenClaw at all.
- Next step: configure Edwin's real Signal/OpenClaw target and run one live end-to-end morning delivery, then decide whether the live-mode message should send the full handoff text or a shorter caption with the audio attachment.

### 2026-03-25
- Tightened `scripts/voice_digest_openclaw_notifier.py` so it can resolve its destination from CLI args, `VOICE_DIGEST_OPENCLAW_CHANNEL` / `VOICE_DIGEST_OPENCLAW_TARGET`, or a repo-local ignored `.voice_digest_notifier.json` file, with a clear error when none are configured.
- Updated docs/workflow notes and ignored the local notifier config file so the real destination can be wired for cron without committing Edwin's contact target into the repo.
- Verification passed in four steps: a temp `voice_digest_morning_job.py --dry-run` run regenerated stable handoff/payload files, the notifier failed cleanly with no destination configured, preview mode succeeded via env vars, `--send --openclaw-dry-run` succeeded via env vars, and preview mode also succeeded via the local config file.
- Learned: the safest remaining path to first live delivery is now operational wiring, not script shape — the repo can support one-time local config plus a final dry-run check before a real morning send.
- Next step: provision Edwin's real Signal/OpenClaw destination in the scheduler environment or local config, then perform one final dry-run send-path check and one true live delivery.
- Added `scripts/voice_digest_dispatch_job.py`, a scheduler-facing wrapper that runs `voice_digest_morning_job.py` and `voice_digest_openclaw_notifier.py` together and always writes stable `delivery_status.json` / `delivery_status.txt` artifacts.
- Verification passed in two end-to-end cases: a temp `--dry-run --send --openclaw-dry-run` dispatch succeeded against the real OpenClaw CLI boundary and produced a `succeeded` status artifact with destination details, and a temp `--dry-run --send` dispatch without destination config failed at the notifier stage while still leaving a `failed` status artifact for cron/debugging.
- Learned: the missing production piece is now almost entirely external configuration, because the repo has one command that both performs the dispatch and leaves a machine-readable success/failure record behind.
- Next step: point the scheduler at `voice_digest_dispatch_job.py`, wire Edwin's real destination, then run one final dry-run dispatch and one true live delivery.
- Wired real OpenAI fallback into `scripts/voice_digest_tts.py`: the TTS step now tries ElevenLabs first, then falls back to OpenAI when ElevenLabs is missing, rate-limited, or temporarily unavailable, and only writes a dry-run note when no live provider is usable.
- Verification passed in three layers: `py_compile` succeeded for the touched scripts, `voice_digest_tts.py --dry-run` still wrote the expected dry-run note, and a local mock-server test forced an ElevenLabs 429 before confirming the script produced an MP3 via the OpenAI fallback path.
- Learned: the morning pipeline is now materially closer to a real delivered digest because ElevenLabs free-tier quota pressure no longer has to collapse the run into text-only dry-run output.
- Next step: run `scripts/voice_digest_dispatch_job.py --send --openclaw-dry-run` with the real destination wired so the new fallback path is exercised inside the scheduler-facing flow before one live morning delivery.
- Added configurable live-audio message-body modes to the OpenClaw notifier and dispatch job: `full` preserves the whole morning handoff as the message text, while `caption` sends a shorter summary alongside the audio attachment.
- Verification passed in three layers: `py_compile` succeeded for the touched notifier/dispatch scripts, notifier preview in `caption` mode rendered the expected shorter `openclaw message send` command, and a temp end-to-end `voice_digest_dispatch_job.py --send --openclaw-dry-run --audio-message-mode caption` run completed successfully while writing stable delivery-status artifacts.
- Learned: the remaining delivery decision is now operational/product-level rather than implementation-level, because the repo can exercise both long-form and short-caption live audio message shapes before choosing a default.
- Next step: wire Edwin's real destination, run one final dry-run dispatch in both `full` and `caption` modes if needed, then choose the default based on the real Signal/OpenClaw delivery experience.
- Added config-backed live-audio message-mode resolution to `scripts/voice_digest_openclaw_notifier.py`, so `.voice_digest_notifier.json` can now carry `audio_message_mode` alongside `channel` and `target`, with the same precedence model as the destination wiring.
- Tightened `scripts/voice_digest_dispatch_job.py` status reporting so `delivery_status.json` / `delivery_status.txt` record the resolved audio message mode and where it came from, which makes morning diagnostics clearer when cron uses config instead of CLI flags.
- Verification passed in three layers: `py_compile` succeeded for the touched notifier/dispatch scripts, notifier preview resolved `audio_message_mode: caption` from a temp config file, and an end-to-end `voice_digest_dispatch_job.py --dry-run --send --openclaw-dry-run --config-path <temp>` run completed successfully while `delivery_status.txt` showed `resolved_audio_message_mode: caption` and `audio_message_mode_source: config`.
- Learned: the notifier config file is now a complete local scheduler contract for both destination routing and preferred live message shape, so the remaining morning-send risk is mostly the final real-target wiring rather than operational flag drift.
- Next step: provision Edwin's real destination in the scheduler env or local config, then do one final `--openclaw-dry-run` dispatch using the intended live message mode before a true live delivery.
- Tightened `scripts/voice_digest_dispatch_job.py` failure reporting so `delivery_status.json` / `delivery_status.txt` now capture the underlying command error detail from the failing stage instead of only a generic exit-code summary.
- Verification passed in three layers: `py_compile` succeeded for the touched dispatch script, a temp `--dry-run --send` dispatch without destination config failed as expected while `delivery_status.txt` showed the exact missing-destination guidance inline, and a temp `--dry-run --send --openclaw-dry-run --channel signal --target ... --audio-message-mode caption` dispatch still succeeded while preserving the resolved mode/destination fields.
- Learned: the sharpest remaining scheduler risk is now less about hidden notifier failures and more about real destination provisioning, because cron-visible status artifacts now explain the common wiring failure directly.
- Next step: wire Edwin's real destination, run one final `--openclaw-dry-run` dispatch with the intended live mode, then do one true live morning send.
- Added an optional stale-artifact freshness guard across `voice_digest_validate_latest.py`, `voice_digest_delivery_payload.py`, `voice_digest_morning_handoff.py`, `voice_digest_morning_job.py`, and `voice_digest_dispatch_job.py` via `--max-age-minutes`, so downstream automation can reject an old `latest_run.json` instead of silently reusing stale morning output.
- Verification passed in two layers: `py_compile` succeeded for all touched scripts, and a temp `voice_digest_morning_job.py --dry-run --max-age-minutes 60` run generated fresh artifacts while a follow-up `voice_digest_delivery_payload.py --max-age-minutes 60` check failed as expected after the manifest/state timestamps were forced stale.
- Learned: delivery readiness now has an explicit freshness contract, which removes a subtle morning risk where scheduler wiring could otherwise surface yesterday's artifact as if it were current.
- Next step: wire Edwin's real destination and choose a scheduler freshness window (for example `--max-age-minutes 180`) before the final dry-run and live morning send.
- Finalized repo-local commit attribution policy: this repo now uses Edwin as the local git author, a checked-in `.gitmessage-assistant` template with `Co-authored-by: Codex <codex@openai.com>`, and updated workflow/docs so assistant-driven commits stay attributable without hiding the human initiator.
- Verification passed in two layers: the repo-local git config now resolves `user.name=Edwin Zubowicz`, `user.email=edwin.zubowicz@gmail.com`, and `commit.template=.gitmessage-assistant`, and the checked-in docs no longer describe the old Codex-only author identity as the active setup.
- Learned: commit provenance is now an operational default instead of a remembered convention, which reduces overnight drift while keeping the remaining production risk focused on real destination wiring.
- Next step: provision Edwin's real Signal/OpenClaw target and exercise one final `voice_digest_dispatch_job.py --send --openclaw-dry-run` run before a true live dispatch.
- Tightened the scheduler failure path so a missing default `incoming_digests/` drop now shows up as a direct operational blocker in `delivery_status.txt` instead of forcing morning triage through nested Python tracebacks.
- Verification passed in two layers: `python3 -m py_compile` succeeded for the touched scheduler/morning/dispatch scripts, and a repo-root `python3 scripts/voice_digest_dispatch_job.py --dry-run --send --openclaw-dry-run --audio-message-mode caption` run failed as expected while `out/delivery_status.txt` now highlighted the missing `incoming_digests/` path through concise `error:` lines.
- Learned: the sharpest remaining automation blocker is now clearly visible as input wiring first, destination wiring second — before a real morning send, the upstream digest generator must actually populate the default drop directory or the scheduler must be pointed at the right one.
- Next step: wire the real upstream digest drop plus Edwin's real Signal/OpenClaw target, then rerun the dry-run dispatch against that intended live configuration before one true live delivery.
- Surfaced freshness metadata in downstream artifacts: `voice_digest_delivery_payload.py` now records run age plus selected-input file details (exists, size, modified time, age), and `voice_digest_morning_handoff.py` now prints those values in the morning summary for faster freshness triage.
- Verification passed in two layers: `python3 -m py_compile scripts/voice_digest_delivery_payload.py scripts/voice_digest_morning_handoff.py` succeeded, and a temp `voice_digest_morning_job.py --dry-run` run produced a payload with `run.age_minutes` plus `summary.selected_input_details.*` while `morning_handoff.txt` showed the new run/input age lines.
- Learned: freshness validation is more usable when the handoff says not just “valid” but also “how old is this run and its source input right now?”, which shortens sleepy morning debugging.
- Next step: wire the real upstream digest drop and real destination, then use the richer handoff/status artifacts to confirm one final dry-run dispatch before the first true live send.
- Made the documented default input path real: the repo now ships with `incoming_digests/.gitkeep`, ignores local digest drops under that directory by default, and `voice_digest_from_latest.py` now fails with concrete guidance when the default drop is missing or empty instead of only naming the path.
- Verification passed in three layers: `python3 -m py_compile scripts/voice_digest_from_latest.py` succeeded, a temp default-path run with no digest files failed with the new setup guidance, and a follow-up temp dry-run with one sample digest in `incoming_digests/` succeeded through `voice_digest_dispatch_job.py --dry-run` using the repo-default path.
- Learned: the remaining upstream-input work is now a real integration boundary rather than repo scaffolding drift — cloning the repo already gives cron the expected drop directory contract.
- Next step: point the real upstream digest generator at `incoming_digests/` (or set `--input-dir` to its true output path), then rerun the dry-run dispatch with Edwin's real destination wiring before the first live send.
