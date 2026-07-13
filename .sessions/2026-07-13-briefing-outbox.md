# 2026-07-13 — briefing outbox: newest manager REPORT on /owner/briefing

> **Status:** `in-progress`

- **📊 Model:** Fable · worker · backlog-slice

**What this session is about:** backlog rung — the captured bullet at
`docs/ideas/backlog.md` ("Embed the manager outbox tally in /owner/briefing
— one URL for the owner read AND the manager roll-up", coordinator-sitting
ender 💡). Goal: add a "reports to the manager" section to `/owner/briefing`
rendering the NEWEST `## REPORT` entry of `control/outbox.md` over the same
committed-file read path the briefing's ASKS section already rides
(`github.fetch_file`), with honest degradation — unreadable file renders
`unknown — <reason>`, a file with no REPORT entries renders an explicit
honest-empty state, never invented content.
