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
