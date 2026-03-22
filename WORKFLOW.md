# Workflow notes

## Commit attribution

Assistant-authored commits in this repo now use a GitHub-visible Codex identity:

- Name: `Codex`
- Email: `codex@openai.com`

Reason:
- keeps assistant commits distinguishable from Edwin's
- makes Codex-authored commits show up cleanly in GitHub UI instead of using a hidden `.invalid` placeholder
- matches the current coding harness for this project

If a different coding harness becomes the primary author later, update the repo-local git identity to match that harness.

## Overnight workflow

For overnight project work, default to this pattern:
- read `STATUS.md`, `OVERNIGHT_POLICY.md`, and `NIGHTLY_TASK.md`
- choose one bounded milestone
- verify before commit
- commit and push milestone progress
- leave the next action explicit for the next overnight phase
