# 2026-07-13 — /prompts: current files primary, superseded demoted (OWNER ORDER 023)

> **Status:** complete — branch `claude/prompts-current-files`, PR #267
> opened READY (not draft) against main; auto-merge was armed by the
> repo's enable-auto-merge lane at open — this worker opens, never merges.

- **📊 Model:** Claude Fable · worker · owner-directed (ORDER 023 dispatch,
  prompts / current files, 2026-07-13T09:15Z)

**What this session was about:** the /prompts console (control-plane, app/)
led its "Universal prompts" section with fleet-manager
`docs/prompts/v3/universal-startup.md` — a file whose OWN header says it is
"SUPERSEDED AS THE GENERATION SOURCE … Do not paste this file" (verified
live 2026-07-13). The owner wants the proper, up-to-date files displayed as
primary. Restructured the page so current artifacts are primary and
superseded files are demoted to a clearly-labeled Historical reference
section.

## What was done

- **Canonical set determined per file's OWN header** (fetched live from
  fleet-manager@main over raw.githubusercontent.com, 2026-07-13):
  - `docs/prompts/v3/universal-startup.md` — HISTORICAL: "⚠ v3.3
    (2026-07-12): SUPERSEDED AS THE GENERATION SOURCE — historical
    template … Do not paste this file; do not regenerate from it."
  - `docs/prompts/v3/session-ender.md` — CURRENT (v3.3): "THIS file stays
    the canonical single source".
  - `projects/<seat>/{coordinator-prompt,instructions,failsafe-prompt}.md`
    (9 seats) — CURRENT: v3.6 generated registry copies of the authored
    per-seat paste sources (`docs/prompts/v3/per-project/<seat>-startup.md`
    / `<seat>-custom-instructions.md`, per-project README v3.6: "ONE
    AUTHORED FILE PER SEAT" / "AUTHORED, EXPANDED coordinator brief — no
    longer generated from ../universal-startup.md").
- `app/prompts.py` — the pinned fleet-wide registry split into
  `FLEET_WIDE` (current: session-ender) + `HISTORICAL` (universal-startup);
  every spec/artifact carries a `historical` flag; `overview()` returns a
  separate `historical` list + `current_count`; historical files excluded
  from the deployed-vs-canonical drift rows (28 rows — a "pasted per
  session" claim for a do-not-paste file would be invented). The #213
  pinned-vs-registry chip, per-seat history links, and #243 supersession
  detection unchanged.
- `app/templates/prompts.html` — seats (current paste sources, startup
  leading each section) render FIRST; the Universal Session-Ender keeps its
  own labeled group after them; new collapsed "Historical reference"
  section at the bottom (`<details class="grp">`, warning banner kept, copy
  affordance removed, body still readable); header-card copy + jump links
  updated. `app/templates/_prompt_artifact.html` — shared `prompt_block`
  gains `copyable=True` param (False → `pre.nocopy` + honest note);
  `app/static/copycode.js` skips `pre.nocopy`. `app/main.py` — route
  docstring updated.
- Tests: `tests/test_prompts.py` (registry shape incl. per-file historical
  pins, current-first/historical-last ordering, collapsed + no-copy +
  still-readable demotion, drift-row exclusion),
  `tests/test_prompt_supersession.py` (banner retained inside the
  Historical section, copy removed for the do-not-paste file),
  `tests/test_prompt_paste_body.py` (attribute-tolerant `<pre>` scan).
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — **1173 passed** (tests/ 636 · botsite 327 ·
  dashboard 60 · review 150; was 1172, net +1 after the restructured
  test set); `python3 bootstrap.py check --strict` — green except this
  card's designed born-red hold, released at this flip. CI on PR #267:
  quality red on the designed hold only; sweep skipped; arm-on-open +
  enable-auto-merge green.
- Evidence: PR #267; upstream header quotes above @ fleet-manager main
  (registry copies stamped "generated from docs/prompts/v3 @ 6715ade8",
  prompts v3.6 stage-2 fold 2026-07-13).
- Decisions made: the demoted file stays ON the page (collapsed) rather
  than deleted — version history covers provenance; copy REMOVED (not just
  demoted) for do-not-paste files, body still selectable; historical files
  excluded from the drift table rather than given a false
  "pasted per session" row. ORDER 023 in control/inbox.md at HEAD is the
  night-report order — the prompts order was absent at sync time, so the
  dispatch text governed (noted per the dispatch's own instruction).
- Next session should know: rescue branch
  `rescue/2026-07-13-prompts-dirt` holds a pre-session dirty
  `.substrate/state.json`; an auto-drafted `2026-07-13-session-3.md` stub
  was moved to the scratchpad, never committed.

⚑ Self-initiated: no — owner-directed (ORDER 023 dispatch). Contained
(one page's structure + its registry module + shared partial param, no
fetch semantics changed) and reversible (restore the previous FLEET_WIDE
tuple + template section order).

## 💡 Session idea

**Registry-driven supersession demotion** — today the HISTORICAL set is
pinned by hand from each file's verified header; the shared
`extract_supersession` detector already reads those same headers at fetch
time. A follow-up could auto-demote any artifact whose fetched header
carries the marker (with the pinned set as a floor, never a ceiling), so a
newly-superseded upstream file demotes itself within one TTL instead of
waiting for a code change. Worth having because supersession events happen
upstream on the manager's schedule, not this repo's.

## ⟲ Previous-session review

The rubric-scorer session (PR #262) left a clean baton — its card named the
rescue-branch + auto-drafted-stub disposal pattern this session reused
verbatim (same dirty `.substrate/state.json`, same stub filename). What it
could not have caught: its card's test-count baseline (1172) shifted the
same morning as sibling PRs landed; counting per-suite in this card avoids
the ambiguity.
