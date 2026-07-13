# 2026-07-13 — /prompts: supersession warnings on artifact cards (ORDER 022 item 3)

> **Status:** in-progress

- **📊 Model:** Claude 5 family · worker (order execution) · feature-build

**What this session was about:** Detect supersession/do-not-paste markers
in fetched /prompts artifact headers and render an unmissable warning
state on affected cards. Idea provenance: 💡 Session idea in
`.sessions/2026-07-13-prompts-drift-row.md` (the PR #234 session's recon
found /prompts serving fm `docs/prompts/v3/universal-startup.md` as a
paste body while that file's own header says "SUPERSEDED AS THE
GENERATION SOURCE … Do not paste this file"). Dispatched under ORDER 022
item 3.

## Goal

- `extract_supersession(raw)` in the shared `app/prompt_artifacts.py`
  layer (ORDER 015: one render path), scanning only the first ~15 RAW
  lines (extract_paste_body strips the full-line comment the marker
  lives in, so the matcher must run on raw text like extract_provenance).
- Conservative strong-phrase matcher: caps token `SUPERSEDED`,
  case-insensitive `do not paste` / `historical template` — NOT bare
  lowercase "supersedes"/"retired" (27 current per-seat registry copies
  carry "Version lineage: … supersedes the prior registry sync copy" and
  "assembly is RETIRED" and must NOT flag). Ambiguous → no warning.
- `superseded` field on the artifact dict; unmissable banner + demoted
  (visually warned, still functional) copy affordance in the shared
  `templates/_prompt_artifact.html`; superseded-count chip in the
  /prompts header card; same field on /prompts/history/{seat} rungs.
- Expected today: exactly 1 of 29 artifacts flags (Universal Startup).

## What was done

- `app/prompt_artifacts.py` — NEW `extract_supersession(raw)` in the
  shared ORDER 015 layer: scans the first 15 RAW lines (same
  `_PROVENANCE_SCAN_LINES` window as `extract_provenance` — the marker is
  a full-line comment `extract_paste_body` strips, so raw text is the
  only place it exists), header region only (comment lines/blocks,
  blockquotes, headings — a strong phrase in plain body text does not
  flag). Strong signals only: the standalone ALL-CAPS token `SUPERSEDED`,
  case-insensitive `do not paste` / `historical template`; never bare
  "supersedes"/"retired" (the 27 CURRENT per-seat registry headers say
  "Version lineage: vN (…) supersedes the prior registry sync copy" and
  "assembly is RETIRED" — verified live they do NOT flag). Successor
  linked only when the marker line explicitly names exactly ONE file
  (markdown link or `see <path>.md`) — the real marker names per-seat
  startups generically, so None today; never invented. `build_artifact()`
  gains the `superseded` key (dict or None; None on fetch failure).
- `app/prompt_history.py` — the same shared extractor populates
  `superseded` on every history-ladder rung dict, so a historical version
  whose header carries the marker warns on /prompts/history/{seat} too.
- `app/templates/_prompt_artifact.html` — unmissable red banner above the
  provenance line when `a.superseded` (marker excerpt autoescaped, never
  |safe; successor link only when named; "view the full marker on
  GitHub"), copy DEMOTED but not blocked: the metadata line warns "copy
  gives the paste-ready body of a SUPERSEDED file" and the `<pre>` gets a
  red-bordered `superseded` class (copycode.js binds to `.card pre` —
  still matches, copy still works).
- `app/templates/prompts.html` + `base.html` — `⚠ N superseded` chip
  (`b bad`) in the header card, rendered only when N > 0 (no marker → no
  chip noise); CSS for `.banner.superseded` / `pre.superseded`.
- `app/prompts.py::overview()` — `superseded_count` field.
- `tests/test_prompt_supersession.py` — 14 new offline tests: the real
  universal-startup marker line VERBATIM (fetched live 2026-07-13) as the
  positive; every false-positive trap VERBATIM as negatives (per-seat
  lineage header, assembly-RETIRED, table-supersedes-cron, session-ender
  canonical-single-source, retired prose); scan-window + header-region
  bounds; successor exactly-one rule; artifact-dict field incl.
  fetch-failure → None; route tests on all three surfaces (/prompts
  banner+chip, /projects/{package} card, history rung) + no-marker →
  zero noise + paste-body contract untouched (no `<!--` ever in a
  rendered `<pre>`).
- Verified against the REAL upstream (live render through the app):
  /prompts → exactly 1 of 29 artifacts flags (Universal Startup), banner
  on its card, chip `⚠ 1 superseded`, no comment leakage into any of the
  29 `<pre>` bodies; /prompts/history/websites and /projects/websites
  honestly show 0 banners (their artifacts are current). Live matcher run
  over all 29 raw artifacts: 1 flagged, phrase `SUPERSEDED`, successor
  None.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — **1027 passed** (+14 new); `python3 bootstrap.py
  check --strict` — only the designed born-red hold on THIS card + one
  pre-existing owner-action advisory.

⚑ Self-initiated: no — ORDER 022 item 3 (idea from the drift-row
session card, dispatched by coordinator).
