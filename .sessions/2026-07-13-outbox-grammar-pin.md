# 2026-07-13 — outbox grammar pin: parse the committed outbox at HEAD in CI

> **Status:** `in-progress` — branch `claude/outbox-grammar-pin-0713`;
> building `tests/test_outbox_grammar_pin.py`: an offline test feeding this
> repo's own committed `control/outbox.md` (read from disk, zero network)
> through `briefing.latest_report` and failing when the real file drifts
> out of the grammar the /owner/briefing REPORTS card reads.

- **📊 Model:** Fable (Claude 5 family) · worker · backlog-slice

**What this session is about:** backlog promotion — the captured bullet in
`docs/ideas/backlog.md` ("Outbox REPORT grammar drift pin — parse the
committed outbox at HEAD in CI", 2026-07-13, briefing-outbox session 💡,
source `.sessions/2026-07-13-briefing-outbox.md`). The REPORTS card
(PR #286) and the coordinator's hand-written outbox entries share a grammar
enforced by nothing — one heading typo silently demotes the newest night
report to the honest-empty state on the page the owner opens every morning.
This session pins the two together: CI fails, naming the drift, when a
REPORT-like heading in the committed file is skipped by the parser or when
REPORT text exists but zero reports parse.

## What was done

- (in progress — close-out fills this section)

⚑ Self-initiated: no — backlog promotion of the outbox REPORT grammar
drift pin bullet (`docs/ideas/backlog.md`, captured 2026-07-13 by the
briefing-outbox session).

## 💡 Session idea

(provisional — filled at close-out after the build, deduped against
`docs/ideas/backlog.md`.)

## ⟲ Previous-session review

(provisional — filled at close-out; previous card:
`.sessions/2026-07-13-venture-vetting-catalog.md`.)
