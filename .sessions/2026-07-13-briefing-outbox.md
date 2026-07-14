# 2026-07-13 — briefing outbox: newest manager REPORT on /owner/briefing

> **Status:** `complete` — PR #286, branch `claude/briefing-outbox-0713`;
> /owner/briefing now carries a sixth card, REPORTS, rendering the newest
> `## REPORT` entry of `control/outbox.md` over the same committed-file
> read path the ASKS section rides; lands via the auto-merge enabler on
> green.

- **📊 Model:** Fable · worker · backlog-slice

**What this session was about:** backlog rung — the captured bullet at
`docs/ideas/backlog.md` ("Embed the manager outbox tally in /owner/briefing
— one URL for the owner read AND the manager roll-up", coordinator-sitting
ender 💡). Goal: add a "reports to the manager" section to `/owner/briefing`
rendering the NEWEST `## REPORT` entry of `control/outbox.md` over the same
committed-file read path the briefing's ASKS section already rides
(`github.fetch_file`), with honest degradation — unreadable file renders
`unknown — <reason>`, a file with no REPORT entries renders an explicit
honest-empty state, never invented content.

## Close-out (auto-drafted 2026-07-13 — edited, evidence corrected)

**Evidence (auto-collected lists were repo-wide; corrected to this
session's actual diff):**

- code touched (1): `app/briefing.py` — `latest_report()` (REPORT entry
  grammar parser: append-only file, one writer → newest report is the
  LAST report heading in document order; PROPOSAL/SIM-REQUEST ignored;
  malformed REPORT-like headings skipped and COUNTED in a note; body
  bounded to `OUTBOX_REPORT_MAX_LINES = 40` with a truncation flag) +
  `outbox_report()` (fetch over `github.fetch_file`, unreadable →
  `state: unknown` + bounded reason) + wired into `overview()`'s gather.
- templates touched (1): `app/templates/owner_briefing.html` — the
  REPORTS card in the existing section idiom (`unknown_line` macro,
  badges, explicit honest-empty paragraph, truncation note).
- tests touched (1): `tests/test_owner_briefing.py` — 7 new offline
  tests (newest-entry selection incl. `###` subsections, empty/
  report-less → honest empty, malformed headings skipped with note,
  body bound, rendered section carries the newest report only, explicit
  honest-empty render, unknown render offline) + outbox assertions in
  the existing offline domain test.
- docs touched (1): `docs/ideas/backlog.md` — source bullet flipped
  `captured` → `built`; this session's 💡 appended.
- other touched (2): `control/claims/2026-07-13-briefing-outbox.md`
  (created at open, deleted in this close-out commit) + this card.
- git: branch `claude/briefing-outbox-0713` from main `096202c`;
  PR #286 opened READY.
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 1228 passed, 1 warning (+7 over main's 1221);
  `python3 bootstrap.py check --strict` — green except this card's own
  designed born-red HOLD (flipped by this commit) and the pre-existing
  never-exit-affecting `owner-action-fields` advisory on
  control/status.md (not owned here).

**Judgment:**

- Decisions made: newest = last REPORT heading in document order
  (append-only doctrine), not timestamp arithmetic; unreadable file →
  `unknown — <reason>` vs report-less file → `ok` + explicit
  honest-empty (mirrors the ASKS zero-asks distinction); body bounded
  to 40 lines with the cap noted honestly; read-only GET section on the
  already-gated page — no new route, no auth change, CSRF floor not
  triggered.
- Next session should know: the REPORTS card renders exactly ONE entry
  (the newest); older reports and PROPOSAL entries stay in the outbox
  behind the card's GitHub link. The parser is briefing-local
  (`app/briefing.py`) — if the outbox grammar ever graduates to a
  kit-owned constant, this parser is the reader to converge.

## 💡 Session idea

**Outbox REPORT grammar drift pin — parse the committed outbox at HEAD in
CI** — a small offline test feeding this repo's own committed
`control/outbox.md` (read from disk, zero network) through
`briefing.latest_report` and failing when the real file drifts out of the
grammar the briefing reads (REPORT-like headings skipped, or zero reports
found while `## REPORT` text exists). Worth having because the REPORTS
card and the coordinator's hand-written outbox entries share a grammar
enforced by nothing — one heading typo silently demotes the newest night
report to the honest-empty state on the page the owner opens every
morning. Deduped against `docs/ideas/backlog.md`: the grammar
source-of-truth notes pin status.md/inbox/claims formats (kit-owned,
`src/engine/grammar.py`); no bullet covers `control/outbox.md`'s REPORT
grammar or any local parse-the-committed-file pin for it. Captured in
`docs/ideas/backlog.md`.

## ⟲ Previous-session review

The venture-vetting-catalog session (PR #248) did well — every one of its
22 hand-curated entries derived its status from the packet's own Status
blockquote and Verdict paragraph (nothing invented), and the
`test_committed_registry_is_honest` pin locked the exact 1/12/2/7
breakdown so the registry can't quietly mutate; what it missed:
`botsite/catalog.py` MIRRORS `products.py` (loader idiom, buyable rule,
`?ref=fleet-store` tagging) instead of sharing it, so the two storefront
loaders can now drift apart edit by edit. Workflow improvement: when a
session copies an existing module's idiom wholesale, extract the shared
rule or leave a one-line "kept in sync by hand with X" marker in both
files — silent twins are the next session's trap.
