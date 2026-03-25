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
