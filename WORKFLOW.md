# Workflow notes

## Commit attribution

Current temporary setup in this repo uses a GitHub-visible Codex identity:

- Name: `Codex`
- Email: `codex@openai.com`

But the intended long-term policy is slightly different:
- assistant-driven commits should be clearly connected to Edwin as the initiating human
- assistant identity should still be visible in GitHub history
- for Codex-driven work, the preferred shape is: Edwin as author plus a visible `Co-authored-by: Codex <codex@openai.com>` trailer
- for other harnesses, use the same pattern with the appropriate visible assistant identity where possible

This keeps ownership clear while still preserving which agent contributed.

The repo-local identity/config should be updated to match that policy as part of the broader assistant commit-attribution setup.

## Overnight workflow

For overnight project work, default to this pattern:
- read `STATUS.md`, `OVERNIGHT_POLICY.md`, and `NIGHTLY_TASK.md`
- choose one bounded milestone
- verify before commit
- commit and push milestone progress
- leave the next action explicit for the next overnight phase
