# Voice Digest Progress

Use this file as the handoff log for the overnight voice-digest R&D track.

## Rules
- Append only when there is real progress.
- Keep entries concise.
- Focus on: what was learned, what changed, blockers, and next step.
- This file is for morning handoff into Edwin's daily digest.

## Entries

### 2026-03-29
- Added upstream-drop diagnostics to the scheduler-facing status artifact: `scripts/voice_digest_dispatch_job.py` now records the resolved `input_glob`, whether the input directory exists, how many matching digest files were present, and the newest matching candidate path before invoking the morning job.
- Added regression coverage in `tests/test_voice_digest_dispatch_job.py` for both the new input-drop diagnostic helper and the morning-job failure path, so `delivery_status.*` keeps showing what the dispatcher actually saw when the run dies before notifier setup.
- Verification passed in two layers: `python3 -m unittest tests.test_voice_digest_dispatch_job` passed (16 tests), and the full `python3 -m unittest discover -s tests -p 'test_*.py'` suite passed (34 tests).
- Learned: once the remaining blocker is environment wiring, it matters whether the scheduler saw “wrong directory,” “empty directory,” or “at least one candidate before a later failure”; preserving that distinction inside `delivery_status.*` makes the morning handoff more actionable.
- Next step: use the richer `delivery_status.*` output in the intended environment to confirm whether the real upstream digest drop is being populated as expected, then keep pushing toward the first intended-config `--send --openclaw-dry-run` and true live delivery.

### 2026-03-29
- Tightened the top-level missing-input handoff: `scripts/voice_digest_dispatch_job.py --check-setup` now recognizes the real `no matching digest files found` morning-job error and writes a concrete `next_action` that points straight at populating `incoming_digests/` or setting `--input-dir` / `VOICE_DIGEST_INPUT_DIR`.
- Added regression coverage in `tests/test_voice_digest_dispatch_job.py` for that exact empty-drop stderr shape so the morning status artifact keeps the actionable guidance even if the top-level run dies before notifier setup.
- Verification passed in three layers: `python3 -m unittest tests.test_voice_digest_dispatch_job` passed (14 tests), the full `python3 -m unittest discover -s tests -p 'test_*.py'` suite passed (32 tests), and a live `python3 scripts/voice_digest_dispatch_job.py --check-setup` run now writes `out/delivery_status.txt` with the explicit populate-input-dir / use-VOICE_DIGEST_INPUT_DIR next step.
- Learned: once the repo-side work narrows to real environment wiring, the morning handoff has to be precise about the exact remaining blocker; generic “inspect the morning-job error” text is too mushy for sleepy triage.
- Next step: populate the real upstream digest drop (or set `VOICE_DIGEST_INPUT_DIR`) in the intended environment, get `--check-setup` to `ready`, then repeat the intended-config `--send --openclaw-dry-run` before one true live delivery.

### 2026-03-29
- Overnight review checkpoint after the earlier doc/wiring work: the repo is still clean on `main`, and `python3 -m unittest discover -s tests -p 'test_*.py'` passed (31 tests).
- A live `python3 scripts/voice_digest_dispatch_job.py --check-setup` run is still blocked before the notifier stage because `incoming_digests/` has no real digest `*.txt` input here, which confirms the next meaningful milestone is environment wiring rather than more repo-side reshaping.
- Stopped cleanly without broadening scope, because anything beyond this checkpoint would be synthetic churn or risky guessing about Edwin's real upstream input path / destination config.
- Next step: populate `incoming_digests/` (or set `VOICE_DIGEST_INPUT_DIR`) in the intended environment, get `--check-setup` to `ready`, then run the intended-config `--send --openclaw-dry-run` before one true live delivery.
- Added a checked-in `.voice_digest_notifier.example.json` and documented the concrete first-live path in `README.md` / `WORKFLOW.md`, so local notifier wiring no longer depends on reverse-engineering the expected config shape from scattered prose before the intended-config dry run.
- The docs now include an explicit five-step readiness sequence: populate `incoming_digests/` (or set `VOICE_DIGEST_INPUT_DIR`), copy the example config into `.voice_digest_notifier.json`, run `--check-setup` until ready, run `--send --openclaw-dry-run`, then do the first live `--send`.
- Verification passed in two layers: `python3 -m json.tool .voice_digest_notifier.example.json` succeeded, and a doc sanity pass confirmed the sample-config path plus first-live checklist are now present in both `README.md` and `WORKFLOW.md`.
- Learned: the remaining blocker is real environment wiring, not script behavior, so repo clarity matters if we want the final handoff to be executable instead of just technically possible.
- Next step: use the sample config in Edwin's intended environment, get `scripts/voice_digest_dispatch_job.py --check-setup` to `ready`, then do the intended-config `--send --openclaw-dry-run` before one true live delivery.

### 2026-03-28
- Tightened the morning-handoff summary line so `scripts/voice_digest_morning_handoff.py` now prefers the actual milestone/change bullet from the latest progress entry instead of surfacing trailing `Learned:` or `Next step:` bullets when both are present.
- Added `tests/test_voice_digest_morning_handoff.py` to lock in that progress-line selection behavior, including the fallback case when an entry only has verification/learned-style bullets.
- Verification passed in three layers: `python3 -m py_compile scripts/voice_digest_morning_handoff.py tests/test_voice_digest_morning_handoff.py` succeeded, `python3 -m unittest tests.test_voice_digest_morning_handoff` passed (2 tests), and a live `python3 scripts/voice_digest_morning_handoff.py --format text` run now shows the shipped scheduler-entrypoint milestone instead of the older `Learned:` summary line.
- Learned: even a good progress log can feel stale in the morning if the handoff picks the reflective bullet instead of the concrete change; summary selection is part of the product.
- Next step: keep tightening the morning-facing contract around real delivery readiness, especially once the real input path and destination wiring are available for the first live run.

### 2026-03-28
- Surfaced notifier readiness through the top-level scheduler entrypoint: `scripts/voice_digest_dispatch_job.py --check-setup` now regenerates the morning artifacts, runs the notifier's existing readiness probe, and still writes stable `delivery_status.json` / `delivery_status.txt` outputs so overnight or cron-style preflight runs leave one place to inspect the current blocker.
- Taught the dispatch status contract about this new blocked-vs-ready preflight state, including setup blocker lines plus targeted next-step guidance when the remaining issue is missing input, missing destination wiring, invalid audio-mode config, or missing `openclaw`.
- Added regression coverage in `tests/test_voice_digest_dispatch_job.py` for both command construction and the blocked status-artifact shape.
- Verification passed in two layers: `python3 -m py_compile scripts/voice_digest_dispatch_job.py tests/test_voice_digest_dispatch_job.py` succeeded, and `python3 -m unittest tests.test_voice_digest_dispatch_job` passed (13 tests). A live repo check with a temp digest input and no destination wiring also produced `out/delivery_status.txt` with `status: blocked`, `stage: notifier_check_setup`, the preserved setup blocker, and the expected next action.
- Learned: the notifier already knew how to answer “what exactly is still unwired?”, but surfacing that answer through the scheduler-facing entrypoint is what makes overnight workers and cron handoffs materially less ambiguous.
- Next step: run `scripts/voice_digest_dispatch_job.py --input-dir <real-upstream-path> --check-setup` in Edwin's intended environment until it goes ready, then do the intended-config `--send --openclaw-dry-run` before one true live delivery.

### 2026-03-28
- Added an explicit notifier readiness probe: `scripts/voice_digest_openclaw_notifier.py --check-setup` now reports whether payload/handoff artifacts exist, destination wiring resolves, audio-message-mode config is valid, and the `openclaw` CLI is available, without needing to infer readiness from a failed preview/send attempt.
- Added regression coverage in `tests/test_voice_digest_notifier.py` for both the blocked missing-destination case and a fully ready config-backed environment, and verified with `python3 -m py_compile scripts/voice_digest_openclaw_notifier.py tests/test_voice_digest_notifier.py` plus `python3 -m unittest tests.test_voice_digest_notifier`.
- Live repo check: `python3 scripts/voice_digest_openclaw_notifier.py --check-setup --json` currently reports `status: blocked` only because the real destination is still unwired here; payload/handoff artifacts and the local `openclaw` CLI are already present.
- Learned: the remaining delivery-path ambiguity is now narrow enough that it should be checked directly before the first intended-config dry run, instead of relying on a failed notifier invocation to explain what is missing.
- Next step: add Edwin's real destination via env or local config, rerun `--check-setup` until it goes ready, then do the intended-config `scripts/voice_digest_dispatch_job.py --send --openclaw-dry-run` before one true live delivery.

### 2026-03-28
- Verified the intended non-`--dry-run` scheduler path end-to-end without risking a real send: a temp `scripts/voice_digest_dispatch_job.py --send --openclaw-dry-run --audio-message-mode auto` run against a fresh sample input produced a real MP3 via the OpenAI fallback path after an ElevenLabs 401, wrote live-mode handoff/payload/status artifacts, and reached the OpenClaw send boundary successfully in dry-run mode.
- Learned: the repo-level blocker has narrowed again — the dispatch flow itself can now prove real audio generation plus notifier execution, so the remaining unknown is the intended live environment wiring (real input path + real destination), not whether the scheduler-facing path can synthesize audio.
- Next step: repeat that same `--send --openclaw-dry-run` verification in Edwin's intended scheduler environment with the real input directory/destination wiring, then do one true live delivery.

### 2026-03-28
- Hardened notifier message-mode wiring: `scripts/voice_digest_openclaw_notifier.py` now rejects invalid `VOICE_DIGEST_AUDIO_MESSAGE_MODE` / `.voice_digest_notifier.json` values instead of silently defaulting to `full`, and its diagnostics preserve the invalid source/value plus configured mode fields for faster scheduler triage.
- Taught `scripts/voice_digest_dispatch_job.py` to carry those invalid-mode diagnostics into `delivery_status.json` / `delivery_status.txt` and emit specific next-step guidance for bad env/config message-mode wiring instead of a generic notifier failure.
- Added regression coverage in `tests/test_voice_digest_notifier.py` and `tests/test_voice_digest_dispatch_job.py` for invalid env/config mode handling, status-artifact preservation, and the new targeted next-action guidance.
- Verification passed in three layers: `python3 -m py_compile scripts/voice_digest_openclaw_notifier.py scripts/voice_digest_dispatch_job.py tests/test_voice_digest_notifier.py tests/test_voice_digest_dispatch_job.py` succeeded, `python3 -m unittest tests.test_voice_digest_notifier tests.test_voice_digest_dispatch_job` passed (19 tests), and the full `python3 -m unittest discover -s tests -p 'test_*.py'` suite passed (25 tests).
- Learned: silently downgrading an invalid scheduler-configured message mode to `full` is the kind of tiny operational bug that only shows up on the first real morning send; failing loudly with preserved diagnostics is safer than guessing.
- Next step: once the real destination/input wiring is in place, run one intended-config `scripts/voice_digest_dispatch_job.py --send --openclaw-dry-run` without `--dry-run` so the scheduler path proves a real audio artifact under the now-stricter notifier config contract.

### 2026-03-28
- Added an `auto` live-audio message-body mode to the OpenClaw notifier/dispatch path, so morning sends can keep the full handoff when it is concise but automatically fall back to the shorter caption when the handoff grows past a safe message-length budget.
- The notifier preview/send plan now records both the requested mode and the resolved live mode plus the reason, message length, and configured limit; `delivery_status.json` / `delivery_status.txt` preserve those fields for scheduler-visible morning triage.
- Updated regression coverage in `tests/test_voice_digest_notifier.py` and `tests/test_voice_digest_dispatch_job.py` for auto-mode resolution and status-artifact preservation.
- Verification passed in three layers: `python3 -m py_compile scripts/voice_digest_openclaw_notifier.py scripts/voice_digest_dispatch_job.py tests/test_voice_digest_notifier.py tests/test_voice_digest_dispatch_job.py` succeeded, `python3 -m unittest tests.test_voice_digest_notifier tests.test_voice_digest_dispatch_job` passed (15 tests), and a temp `scripts/voice_digest_dispatch_job.py --dry-run --send --openclaw-dry-run --audio-message-mode auto ...` run wrote `out/delivery_status.txt` with `audio_message_mode_reason: auto_caption_handoff_too_long` plus the message-length fields.
- Learned: manual `full` vs `caption` selection was an avoidable operational choice for the first real morning sends; the notifier can make the safer call automatically while still surfacing exactly what it decided.
- Next step: run one non-`--dry-run` audio-producing dispatch with `--audio-message-mode auto` against the intended input path and destination wiring, then confirm whether the safe-length threshold needs tuning from real delivery feedback.

### 2026-03-28
- Hardened malformed-config triage for the notifier path: `scripts/voice_digest_openclaw_notifier.py` now preserves destination diagnostics even when `.voice_digest_notifier.json` exists but contains invalid JSON, records a `config_load_error` field, and reports the config path directly in the error text instead of failing without wiring context.
- Taught `scripts/voice_digest_dispatch_job.py` to carry that `config_load_error` through into `delivery_status.json` / `delivery_status.txt` and to emit a specific `next_action` for the malformed-config case instead of treating it like a generic transport failure or missing destination.
- Added regression coverage in `tests/test_voice_digest_notifier.py` and `tests/test_voice_digest_dispatch_job.py` for invalid-config handling, status-artifact preservation, and the new targeted next-step guidance.
- Verification passed in three layers: `python3 -m py_compile scripts/voice_digest_openclaw_notifier.py scripts/voice_digest_dispatch_job.py tests/test_voice_digest_notifier.py tests/test_voice_digest_dispatch_job.py` succeeded, `python3 -m unittest tests.test_voice_digest_notifier tests.test_voice_digest_dispatch_job` passed (13 tests), and the full `python3 -m unittest discover -s tests -p 'test_*.py'` suite passed (19 tests).
- Learned: a malformed local destination config is a realistic first-live-send failure mode, and without preserved diagnostics it looks too much like a generic notifier breakage; making that case explicit improves morning recovery without needing the real target wired yet.
- Next step: wire the real upstream digest path plus Edwin's real destination, then run one intended-config `scripts/voice_digest_dispatch_job.py --send --openclaw-dry-run` to prove the live send path with a valid local config or env wiring.

### 2026-03-28
- Added delivery-target artifact details to the downstream contract: `scripts/voice_digest_delivery_payload.py` now records `summary.delivery_target_details` (exists, size, modified time, age) for the actual audio file or dry-run note, and `scripts/voice_digest_dispatch_job.py` now preserves and renders those fields in `delivery_status.json` / `delivery_status.txt`.
- Added regression coverage in `tests/test_voice_digest_delivery_payload.py` for live audio payloads and extended `tests/test_voice_digest_dispatch_job.py` so stable status artifacts keep rendering the new delivery-target fields on notifier-path failures.
- Verification passed in three layers: `python3 -m py_compile scripts/voice_digest_delivery_payload.py scripts/voice_digest_dispatch_job.py tests/test_voice_digest_delivery_payload.py tests/test_voice_digest_dispatch_job.py` succeeded, `python3 -m unittest tests.test_voice_digest_delivery_payload tests.test_voice_digest_dispatch_job` passed (8 tests), and a temp `VOICE_DIGEST_INPUT_DIR=<temp>/upstream python3 scripts/voice_digest_dispatch_job.py --dry-run --channel signal --target +37060000000` run wrote `out/delivery_status.txt` with `delivery_target_exists`, `delivery_target_size_bytes`, and `delivery_target_age_minutes` lines.
- Learned: freshness/status triage was still slightly too indirect because the scheduler artifact named the delivery target path but did not prove that the generated audio or fallback note actually existed and looked recent.
- Next step: wire the real upstream digest path plus Edwin's real destination, then use the richer status artifact to verify one non-`--dry-run` audio-producing dispatch before the first live send.

### 2026-03-28
- Tightened `scripts/voice_digest_dispatch_job.py` handoff guidance for the easy-to-misread success case where dispatch only proves `send_text_fallback` because TTS is still running with `--dry-run`; the stable `next_action` now explicitly says to rerun without `--dry-run` and verify a real audio artifact before the first live morning send.
- Added regression coverage in `tests/test_voice_digest_dispatch_job.py` for that new success-path guidance while preserving the existing send-path dry-run hint for genuine audio-ready runs.
- Verification passed in three layers: `python3 -m py_compile scripts/voice_digest_dispatch_job.py tests/test_voice_digest_dispatch_job.py` succeeded, `python3 -m unittest tests.test_voice_digest_dispatch_job` passed (7 tests), and a temp dispatch run with `VOICE_DIGEST_INPUT_DIR=<temp>/upstream python3 scripts/voice_digest_dispatch_job.py --dry-run --channel signal --target +37060000000` now writes `delivery_status.txt` with a `next_action:` line that calls out the missing real-audio proof instead of implying the remaining work is only destination wiring.
- Learned: a green-ish scheduler run can still leave the core product blocker unsolved if it never synthesized audio; the morning artifact needs to distinguish “dispatch path works” from “voice digest is actually ready.”
- Next step: run the intended-config dispatch without `--dry-run` once the real input path and destination wiring are in place, confirm it produces audio rather than a dry-run note, then do one true live delivery.

### 2026-03-28
- Added morning-readable `next_action` guidance to `scripts/voice_digest_dispatch_job.py`, and threaded it into both `delivery_status.json` and `delivery_status.txt` for common states: missing input drop, missing destination wiring, missing `openclaw` CLI, preview-only success, and send-path dry-run success.
- Added regression coverage in `tests/test_voice_digest_dispatch_job.py` for the new hinting logic, including missing-input, missing-destination (preview and send), successful send dry-run, and status-artifact rendering.
- Verification passed in three layers: `python3 -m py_compile scripts/voice_digest_dispatch_job.py tests/test_voice_digest_dispatch_job.py` succeeded, `python3 -m unittest discover -s tests -p 'test_*.py'` passed (14 tests), and a temp end-to-end dispatch run with a sample digest now writes `delivery_status.txt` with a concrete `next_action:` line instead of only raw notifier failure text.
- Learned: the repo was already good at preserving failure detail, but sleepy morning triage still required humans to infer the intended follow-up; one small explicit hint makes the stable handoff materially more actionable.
- Next step: wire Edwin's real destination and real upstream input path, then run the intended-config `python3 scripts/voice_digest_dispatch_job.py --send --openclaw-dry-run` before one true live dispatch.

### 2026-03-28
- Overnight review checkpoint: handoff docs are aligned, the repo is clean on `main`, and `python3 -m unittest discover -s tests -p 'test_*.py'` passed (11 tests).
- The project is still operationally blocked for the next true milestone: there is no repo-local `.voice_digest_notifier.json`, so Edwin’s real OpenClaw/Signal destination is not wired here, and the remaining meaningful step is still the intended-config `--send --openclaw-dry-run` followed by one real live delivery.
- Stopped cleanly without broadening scope, because anything beyond this checkpoint would either be synthetic-only rework or risky guessing about real destination wiring.
- Next step: provision the real destination (env or local config), confirm the real upstream input path if it differs from `incoming_digests/`, then run `python3 scripts/voice_digest_dispatch_job.py --send --openclaw-dry-run` in that intended environment before one true live dispatch.

### 2026-03-28
- Tightened scheduler input wiring at the top-level entrypoint: `scripts/voice_digest_dispatch_job.py` can now resolve the upstream digest drop from `VOICE_DIGEST_INPUT_DIR` when `--input-dir` is omitted, and `delivery_status.json` / `delivery_status.txt` now record both the resolved `input_dir` and whether it came from `cli`, `env`, or the repo default.
- Added regression coverage for both behaviors in `tests/test_voice_digest_dispatch_job.py`, including env-vs-default input resolution and a notifier-failure status artifact that preserves the env-resolved input path for cron debugging.
- Verification passed in three layers: `python3 -m py_compile scripts/voice_digest_dispatch_job.py tests/test_voice_digest_dispatch_job.py` succeeded, `python3 -m unittest tests.test_voice_digest_dispatch_job` passed, and a repo-root `VOICE_DIGEST_INPUT_DIR=<temp>/upstream python3 scripts/voice_digest_dispatch_job.py --dry-run --channel signal --target +37060000000` run completed successfully while `out/delivery_status.txt` showed `input_dir_source: env`.
- Learned: the remaining upstream-input work is now more operationally legible for cron, because the scheduler status artifact says not just which digest path was used but where that path came from.
- Next step: set `VOICE_DIGEST_INPUT_DIR` plus Edwin's real notifier destination in the scheduler environment, then run one intended-config `voice_digest_dispatch_job.py --send --openclaw-dry-run` before the first true live dispatch.

### 2026-03-27
- Preserved notifier setup diagnostics on real send-path failures: `scripts/voice_digest_openclaw_notifier.py --json` now includes the same destination/config/env/artifact diagnostics block for `openclaw` runtime/send failures that it already emitted for missing-destination config failures, so morning triage keeps the wiring context even when transport execution is the part that breaks.
- Verification passed in three layers: `python3 -m py_compile scripts/voice_digest_openclaw_notifier.py tests/test_voice_digest_notifier.py tests/test_voice_digest_dispatch_job.py` succeeded, `python3 -m unittest tests.test_voice_digest_notifier tests.test_voice_digest_dispatch_job` passed, and a repo-root notifier run under `PATH=/usr/bin:/bin` with `--send --openclaw-dry-run --json` now returns both the missing-CLI error and the full diagnostics block.
- Learned: the first real delivery failures are likely to be messy operational edges rather than pure config absence, so preserving setup diagnostics across both failure shapes makes the stable status artifact much more useful at 8 AM.
- Next step: wire the real upstream digest drop plus Edwin's real Signal/OpenClaw destination, then run one intended-config `voice_digest_dispatch_job.py --send --openclaw-dry-run` before the first true live delivery.

### 2026-03-27
- Threaded freshness metadata into the scheduler-facing delivery status contract: `scripts/voice_digest_dispatch_job.py` now copies `run.age_minutes` plus `summary.selected_input_details.*` from `delivery_payload.json` into `delivery_status.json`, and renders run/input age, modified time, and size in `delivery_status.txt` for one-file cron triage.
- Added regression coverage in `tests/test_voice_digest_dispatch_job.py` so notifier-failure status artifacts keep those new freshness fields in both JSON and text form.
- Verification passed in three layers: `python3 -m py_compile scripts/voice_digest_dispatch_job.py tests/test_voice_digest_dispatch_job.py` succeeded, `python3 -m unittest tests.test_voice_digest_dispatch_job` passed, and a temp end-to-end `voice_digest_dispatch_job.py --dry-run --channel signal --target +37060000000` run produced a successful `delivery_status.txt` with `run_age_minutes`, `selected_input_age_minutes`, `selected_input_modified_at`, and `selected_input_size_bytes` lines.
- Learned: the morning payload/handoff already knew whether a run was fresh, but the scheduler-visible status artifact still forced operators to cross-reference files; surfacing freshness there too makes cron/debugging more self-contained.
- Next step: wire the real upstream digest drop plus Edwin’s real Signal/OpenClaw destination, then run one intended-config `voice_digest_dispatch_job.py --send --openclaw-dry-run` before the first live delivery.

### 2026-03-27
- Hardened the final notifier-wiring debug path: `scripts/voice_digest_openclaw_notifier.py --json` now emits structured setup diagnostics when destination wiring is missing (config path/presence, whether config has channel/target, whether destination env vars are set, whether CLI overrides were supplied, and which payload/handoff files it inspected), and `scripts/voice_digest_dispatch_job.py` now preserves and renders those diagnostics in `delivery_status.json` / `delivery_status.txt`.
- Added regression coverage for both layers: notifier tests lock in the new structured diagnostics on missing destination wiring, and dispatch tests confirm those diagnostics survive into the stable status artifact alongside resolved destination/mode fields.
- Verification passed in three layers: `python3 -m py_compile scripts/voice_digest_openclaw_notifier.py scripts/voice_digest_dispatch_job.py tests/test_voice_digest_notifier.py tests/test_voice_digest_dispatch_job.py` succeeded, `python3 -m unittest tests.test_voice_digest_notifier tests.test_voice_digest_dispatch_job` passed, and a repo-root `python3 scripts/voice_digest_openclaw_notifier.py --json` run now returns an explicit diagnostics block showing that no config file or destination env vars are present.
- Learned: the remaining delivery-path uncertainty is now less about “why did notifier wiring fail?” and more about the genuinely missing live config/input, because the failure artifact can say which configuration surfaces were actually populated.
- Next step: once the real upstream digest drop or `--input-dir` is known, run one scheduler-facing `voice_digest_dispatch_job.py --send --openclaw-dry-run` against that intended input plus Edwin’s real destination wiring, then do one true live dispatch.

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
