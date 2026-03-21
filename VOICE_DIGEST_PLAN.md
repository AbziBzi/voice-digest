# Voice Digest Plan

Goal: make Edwin's reading digest easy to consume by voice without losing important non-text information like charts, graphs, screenshots, and diagrams.

## Problem framing
Edwin likes high-signal reading but often does not want to read on a PC/phone screen.
A voice mode could help, but pure TTS risks losing visual information.
Signal audio/voice delivery may or may not be practical depending on channel capabilities, so delivery format needs validation.

## Quality bar
Do this slowly and well.
Do not ship a janky "just read the article aloud" workflow if it drops key charts or makes long content painful.
Iterate toward something genuinely pleasant to use.

## Design constraints
- Preserve important visual information.
- Keep listening time reasonable.
- Prefer local / low-cost / practical approaches.
- Work well with the existing daily reading digest.
- Fit Signal delivery if possible; if not, find the next-best route.

## Candidate solution directions

### 1) Spoken digest, not full spoken article
Read only the daily digest aloud:
- short industry overview
- top links
- summaries
- why each matters
Pros: fast, cheap, easy.
Cons: does not solve full article consumption.

### 2) Audio brief + visual flags
Generate a spoken summary plus explicit cues like:
- "this article includes an important chart about X"
- "there is a graph comparing Y and Z"
- "worth opening later for the diagram"
Pros: likely best near-term balance.
Cons: requires chart/visual extraction heuristics.

### 3) Article-to-audio transformation
For selected articles, create a listenable narration adapted for audio:
- summarize structure
- describe key visuals in words
- skip boilerplate
- keep quotes where valuable
Pros: strongest user value.
Cons: harder quality problem.

### 4) Dual-delivery bundle
Send:
- text digest
- audio digest
- optional "visuals worth opening" list
Pros: flexible.
Cons: depends on Signal/media support.

## Questions to answer over time
1. Can I reliably deliver playable audio into Signal from this environment?
2. If yes, what formats are supported well?
3. What is the best TTS path here: local, existing tool, or API?
4. Can I detect/describe charts and images robustly enough for article summaries?
5. What listening length feels right for a morning brief?
6. Should the audio cover only the digest, or selected articles too?

## Milestones
- Validate Signal audio delivery path.
- Inventory available TTS options on this machine.
- Prototype a short audio digest.
- Prototype visual-aware article summary.
- Decide whether to combine digest + article audio or keep them separate.
- Ship only when the experience feels actually useful.

## Daily work style
Small progress is fine.
Each day:
- do one useful step
- record what was learned
- send Edwin a concise progress update when there is something real to report
