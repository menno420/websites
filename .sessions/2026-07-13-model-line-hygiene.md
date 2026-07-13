# 2026-07-13 — model-line hygiene: family-level examples in template + historical card sweep

> **Status:** `complete` — branch `claude/model-line-hygiene`, PR #226.

- **📊 Model:** Claude Fable 5 · worker · housekeeping sweep

**What this session was about:** coordinator-assigned housekeeping slice.
Fleet rule: session cards' `📊 Model:` lines carry FAMILY-LEVEL model names
only, never exact model IDs. The template and ender checklist in
`.sessions/README.md` demonstrated the rule with exact-ID-shaped example
strings, so new cards kept inheriting that shape (PR #224 fixed one card;
this slice fixes the source and sweeps the historical cards). Promotes the
backlog capture from the 2026-07-12 card-model-line-fix session's 💡 idea.

## What was done

- `.sessions/README.md`: the template's `📊 Model:` example (line 26) and the
  ender-checklist examples (line 57) changed from exact-ID-shaped strings to
  family-level names ("Claude Fable 5", "Claude Opus 4.8"). Rule text kept
  intact; only the examples changed.
- Swept 102 historical `.sessions/*.md` cards whose `📊 Model:` line carried
  an exact-ID-shaped model token, normalizing the token to the family-level
  name (Claude Fable 5 / Claude Opus 4.8 / Claude Sonnet 5). All matched
  cards were Status `complete` with work already merged to main (terminal);
  zero skips needed. One line per card, no other content touched; full
  before→after list in the PR #226 body.
- Determined `.sessions/README.md` is NOT kit-planted (host-authored body):
  `bootstrap.py` carries no exact-ID example strings, its
  `_adopt_sessions_readme` plant has no template block, `_merge_model_doctrine`
  is append-only/byte-preserving, and `.substrate/state.json`
  `planted_doc_hashes` omits the file — so no `control/outbox.md` upstream
  routing needed (the kit's own doctrine examples are already family-level).
- `docs/ideas/backlog.md`: flipped the promoted README-examples idea to
  `built` (PR #226); captured this session's 💡 as a new bullet.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 891 passed, 1 warning; `python3 bootstrap.py check
  --strict` — all checks passed (this card the designed born-red HOLD under
  the added-card gate until this flip; swept siblings advisory-only).

⚑ Self-initiated: no — coordinator-assigned slice promoting the captured
backlog idea from the card-model-line-fix session; text-only card edits,
contained and reversible.

## 💡 Session idea

**Kit-gate advisory for exact-ID model lines** — extend the session-card
scan in `bootstrap.py check` (the `session_markers` machinery) with an
advisory that flags any `📊 Model:` line matching the exact-ID shape
(lowercase `claude-<family>-<digit>` token), so regressions are caught at
the gate instead of by manual sweeps like this one. Worth having because a
one-time sweep decays — without a checker the template's old shape will
creep back in via copy-paste from pre-sweep cards in other fleet repos.
Deduped against `docs/ideas/backlog.md` + the queue-state NEXT list: the
backlog carries the README-example fix (promoted by this session) but no
gate/checker entry. Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The kit-upgrade-v1.15.0 session (PR #199) did well — the sha256 three-way
verification and the byte-verified bank of 1.14.0 made the upgrade fully
auditable, and it explicitly recorded what it did NOT do (lane-owed items)
instead of silently dropping them; what it missed: its lane-owed list lives
only in the card/PR body rather than a tracked queue surface, so the four
diverged-doc merges risk going stale unnoticed.
