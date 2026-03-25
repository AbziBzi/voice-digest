# Nightly Task Template

When an overnight run starts, use this checklist:

1. Read:
   - `STATUS.md`
   - `OVERNIGHT_POLICY.md`
   - `VOICE_DIGEST_PROGRESS.md`
   - `WORKFLOW.md`
   - relevant project files
2. Choose exactly one bounded milestone.
   - Treat OpenAI TTS fallback support as a preferred milestone whenever ElevenLabs quota, free-tier limits, or provider availability are on the critical path.
3. Do the work.
4. Verify the result.
5. Update `STATUS.md` if the project state changed.
6. Append a concise progress note to `VOICE_DIGEST_PROGRESS.md` if real progress happened.
7. Commit and push if there is a real milestone.
8. End with:
   - what changed
   - verification evidence
   - blocker if any
   - next best action
