# 2026-07-13 — outbox grammar pin: parse the committed outbox at HEAD in CI

> **Status:** `complete` — PR #289, branch `claude/outbox-grammar-pin-0713`;
> `tests/test_outbox_grammar_pin.py` feeds this repo's own committed
> `control/outbox.md` (read from disk, zero network) through
> `briefing.latest_report` — the exact parser the /owner/briefing REPORTS
> card uses — and fails naming the drift when the real file leaves the
> grammar; lands via the auto-merge enabler on green.

- **📊 Model:** Fable (Claude 5 family) · worker · backlog-slice

**What this session was about:** backlog promotion — the captured bullet in
`docs/ideas/backlog.md` ("Outbox REPORT grammar drift pin — parse the
committed outbox at HEAD in CI", 2026-07-13, briefing-outbox session 💡,
source `.sessions/2026-07-13-briefing-outbox.md`). The REPORTS card
(PR #286) and the coordinator's hand-written outbox entries share a grammar
(`## REPORT · <ISO8601> · <from → to> · <TITLE>`) enforced by nothing —
one heading typo silently demotes the newest night report to the
honest-empty state on the page the owner opens every morning.

## What was done

- `tests/test_outbox_grammar_pin.py` — 5 offline tests, zero network,
  locating `control/outbox.md` via pathlib from the test file. The pin
  proper: (a1) the parser's own malformed-skip note must be empty (a
  `## REPORT` heading recognized but rejected on grammar is a failure
  naming the heading); (a2) every REPORT-like level-2 heading (label-
  position regex, case-insensitive, spacing-tolerant — catches `## Report`
  / `##REPORT` typos the parser can't even see) must be matched by an
  accepted parse (`total_reports` == REPORT-like count); (b) `## REPORT`
  text present ⇒ `found is True` with title + issued. Failure messages
  route the fixer: typo → `control/outbox.md`; grammar change →
  `app/briefing.py latest_report` (+ this pin's regex, together). Two
  synthetic teeth-tests prove a malformed heading and a label-typo heading
  are both detected, and that a PROPOSAL merely *mentioning* a report is
  not REPORT-like — keeping the regex and the parser aligned.
- `docs/ideas/backlog.md` — source bullet flipped `captured` → `built`
  (PR #289 cited); this session's 💡 captured as a new bullet.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 1244 passed, 1 warning (+5 over main's 1239
  baseline); `python3 bootstrap.py check --strict` — green except this
  card's own designed born-red HOLD (flipped by this commit) and the
  pre-existing never-exit-affecting `owner-action-fields` advisory on
  control/status.md (not owned here).

⚑ Self-initiated: no — backlog promotion of the outbox REPORT grammar
drift pin bullet (`docs/ideas/backlog.md`, captured 2026-07-13 by the
briefing-outbox session).

## 💡 Session idea

**Outbox grammar gate in the CI control fast lane — the pin doesn't run on
the PRs that write the outbox** — `quality.yml`'s control fast lane
short-circuits GREEN on a control/**-only diff (pytest never runs), and
outbox appends are exactly control/**-only PRs, so
`tests/test_outbox_grammar_pin.py` fires only on the NEXT non-control PR —
after the typo'd report has already spent a morning rendering honest-empty.
The fast lane already runs in-job control gates (control-status, inbox
append-only at `quality.yml` ~lines 71–102); add an outbox grammar step
there when `control/outbox.md` is in the diff — either run the single pin
test file or a tiny inline parse — so the drift reddens the PR that
introduces it. Deduped against `docs/ideas/backlog.md`: the bullet this
session built is the pytest pin itself (merge-lagged by design of the fast
lane); the grammar source-of-truth notes cover status.md/inbox/claims
kit-owned grammars; no bullet touches the fast lane's gate set or
outbox coverage inside it. Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The venture-vetting-catalog session (PR #248) did well — a linked subpage
instead of growing /products kept the 4-item store's clarity while
surfacing all 22 pipeline entries, each status derived from its packet's
own Status blockquote; what it missed: `botsite/data/catalog.json` was
curated by hand with no `gen_*` baker, unlike the review service's
committed-JSON convention (`review/data/*.json` baked by `gen_*.py`), so
refreshing from venture-lab means re-doing 22 entries of hand-curation
rather than re-running a script.
