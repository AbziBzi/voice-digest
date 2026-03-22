# Workflow notes

## Commit attribution

For now, assistant-authored commits in this repo use a distinct git author identity:

- Name: `Leslie`
- Email: placeholder under reserved `.invalid`

Reason:
- keeps assistant commits distinguishable from Edwin's
- avoids using Edwin's personal email for assistant-made commits
- avoids pretending the commits belong to a separate GitHub account that does not exist

Tradeoff:
- GitHub will not attribute these commits to a separate profile/contribution graph

If cleaner public attribution is wanted later, create a dedicated GitHub identity for Leslie and switch to that account's noreply email.

## Overnight workflow

For overnight project work, default to this pattern:
- read `STATUS.md`, `OVERNIGHT_POLICY.md`, and `NIGHTLY_TASK.md`
- choose one bounded milestone
- verify before commit
- commit and push milestone progress
- leave the next action explicit for the next overnight phase
