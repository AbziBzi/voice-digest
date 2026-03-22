# Overnight Policy

Purpose: let the voice-digest project make real progress overnight without drifting into noisy, expensive, or low-quality loops.

## Core rules
- Work in bounded milestones, not an endless loop.
- Prefer scheduler-driven runs over one giant conversation.
- Commit only after verification for the touched slice.
- Push milestone commits so progress is visible live.
- Use a GitHub-visible assistant identity for assistant-authored commits so authorship is legible in GitHub history.
- Keep durable state in files, not just chat history.

## Budgets
- Night window: stop active work by 06:45 Europe/Vilnius.
- Retry budget: at most 2 retries for transient failures per step.
- Scope budget: stop if the diff becomes broader than the current milestone.
- Cost mindset: choose practical, dependency-light steps unless a larger spend is clearly justified.

## Milestone shape
Each overnight run should do one bounded slice:
1. Read current status / progress files.
2. Pick one next milestone.
3. Implement or research that slice.
4. Verify with concrete evidence.
5. Update status files.
6. Commit and push if the milestone is real.
7. Leave the next action explicit.

## Verification before commit
Use the lightest credible proof available:
- script runs successfully
- dry-run output exists
- tests for the touched code pass
- docs match the implementation
- git diff still matches the intended scope

## Stop conditions
Stop and report blocked if any of these happen:
- same failure repeats 3 times
- no meaningful progress across 2 checkpoints
- required verification cannot be made green within budget
- the task would require risky or destructive behavior
- the diff becomes surprisingly broad

## Overnight deliverables
At minimum, every productive overnight phase should leave one or more of:
- a pushed commit
- an updated `VOICE_DIGEST_PROGRESS.md` entry
- a tighter plan / next-step note
- a runnable script or artifact
- a concise morning-ready summary
