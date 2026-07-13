# 2026-07-13 — botsite: pin step-title provenance on guide exchanges

> **Status:** `complete` — PR #316, branch `claude/step-provenance-0713`;
> guide exchanges now snapshot the step's title at ask time, the owner-queue
> question digest renders "asked when this step said …" for questions that
> predate a script rewrite, and pre-pin legacy rows say the wording wasn't
> recorded instead of guessing; lands via the auto-merge enabler on green.

- **📊 Model:** Claude Fable 5 · worker · backlog-promotion

**What this session was about:** backlog promotion — the "Guide-question
step provenance — pin what the step SAID when the question was asked"
bullet (`docs/ideas/backlog.md`, captured 2026-07-13 by the
step-question-digest session 💡). `guide_exchanges` rows pin only
`step_index`, so the question digest (PR #304) and both strips
(#294/#298/#303) attribute every persisted question to whatever text
CURRENTLY sits at that index — the first script rewrite the hotspots
trigger silently re-attributes history to the wrong step. This session
snapshots the step's title at ask time and renders it in the digest, with
an honest label for legacy rows that carry no snapshot.

## What was done

- `botsite/testing_store.py` — `guide_exchanges.step_title` column
  (`NOT NULL DEFAULT ''`, `_SCHEMA` line 98) + `_ensure_step_title_column`
  (line 129) retrofitting the column in place onto pre-pin DB files
  (`CREATE TABLE IF NOT EXISTS` never adds columns; retrofitted rows keep
  `''` — "no snapshot was taken" is their honest state, never backfilled).
  `add_guide_exchange` (line 409) takes the snapshot;
  `guided_step_questions` (line 618) returns `{message, step_title}` per
  question.
- `botsite/testing.py` — `_step_title` (line 911, shared with
  `_heatmap_step_text`); the chat handler pins the title as the asker saw
  it at persist time (line 970); `_digest_question` (line 1066) resolves
  each digest question to clean (pin == current title) / stale (pin
  differs → the ask-time title, truncated like the tooltips) / unpinned
  (legacy `.get` default); the `_owner_page` digest join passes the
  current script (line 1200). No new routes, no new env reads; the
  screen-frame path stays write-free.
- `botsite/templates/testing_owner.html` (line 17) — the digest macro
  renders `q.text` plus the stale / "pre-provenance row" labels.
- `docs/ideas/backlog.md` — the step-provenance bullet flipped to `built`;
  this session's 💡 captured as a new bullet.
- Tests: `botsite/tests/test_testing_owner_question_digest.py` (store pin
  end-to-end incl. export, legacy `''` default, pre-pin DB retrofit,
  digest clean/stale/reorder/legacy rendering, `_digest_question` unit
  coverage) + `botsite/tests/test_testing_guide.py::
  test_chat_pins_step_title_at_persist_time` (route persist pin).
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 1354 passed, 1 warning (+9 over main's 1345);
  `python3 bootstrap.py check --strict` — green except this card's own
  designed born-red HOLD (flipped by this commit).

⚑ Self-initiated: no — backlog promotion (the step-provenance bullet in
`docs/ideas/backlog.md`, source `.sessions/2026-07-13-step-question-digest.md` 💡).

## 💡 Session idea

**Import valve for the testing-DB export — restore `export.json` after a
redeploy wipe** — `GET /testing/owner/export.json` dumps the tester-program
DB before a redeploy, but nothing can put the backup BACK: after the wipe
the owner holds a JSON file and the queue starts empty until the Postgres
ask lands. An owner-auth import valve (rows re-inserted with the same
honest `.get`-default handling this session used for pre-pin rows, so old
backups without newer columns restore cleanly) would close the loop the
export half-opened. Worth having because a backup valve that can't restore
is a promise the disaster will break. Deduped against
`docs/ideas/backlog.md` + the queue-state NEXT list: the export valve is
prose in the store docstring only; no import/restore bullet exists; the
submissions-Postgres OWNER-ACTIONS ask is infrastructure, not this
repo-side bridge. Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The venture-vetting-catalog session (PR #248) did well — it curated all 22
vetting packets with per-title status honesty and pinned the registry's
1/12/2/7 breakdown in a dedicated test; what it missed: the sha-drift decay
it diagnosed itself (catalog pinned at venture-lab `2c039e3`) stayed a
backlog bullet, so the hand-curated registry is already aging unwatched.
