# 2026-07-13 — /prompts: supersession warnings on artifact cards (ORDER 022 item 3)

> **Status:** complete — PR #243, branch `claude/prompts-supersession`;
> lands via the repo's auto-merge enabler on green (never self-armed).

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

**Backlog note (honest):** `docs/ideas/backlog.md` has no bullet for this
idea — it lived only in the drift-row session card's 💡 Session idea
section (`.sessions/2026-07-13-prompts-drift-row.md`), so there is
nothing to tick off in the backlog; this card is the closure record.

## Close-out (auto-drafted 2026-07-13 — edit, don't author)

<!-- substrate:auto-draft -->

**Evidence (auto-draft corrected — the collector listed the whole tree;
this session actually touched):**

- code touched (3): `app/prompt_artifacts.py` (NEW `extract_supersession`
  + `superseded` artifact-dict key), `app/prompt_history.py` (same field
  on ladder rungs), `app/prompts.py` (`superseded_count`).
- templates touched (3): `app/templates/_prompt_artifact.html` (banner +
  demoted copy), `app/templates/prompts.html` (chip),
  `app/templates/base.html` (CSS only).
- tests touched (1, new): `tests/test_prompt_supersession.py` (14 tests).
- sessions/claims: this card + `control/claims/prompts-supersession.md`
  (created born-red, deleted at this flip).
- git: branch `claude/prompts-supersession`; commits this session:
  `94b3d87` (born-red card + claim), `4af5ffa` (implementation), plus
  this flip commit. The auto-draft's "rescue: dirty .substrate/state.json"
  commit is NOT this session's — it predates the branch point.
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` → **1027 passed** (+14 new); `python3 bootstrap.py
  check --strict` → passes except the DESIGNED born-red hold on this card
  (flipped by this commit) + one pre-existing owner-action advisory
  (`owner-action-fields` on control/status.md, untouched here).

**Judgment:**

- Decisions made: (1) the matcher runs on RAW upstream text, not the
  paste body — the marker is a full-line comment `extract_paste_body`
  strips; (2) a strong-phrase allowlist over fuzzy scoring — caps
  `SUPERSEDED` / `do not paste` / `historical template`, header region
  only, verified live against all 29 real artifacts (exactly 1 flags; the
  27 current lineage headers don't); (3) copy demoted, never blocked —
  the owner may legitimately need the text; (4) no successor link
  invented — the real marker names no single file and the banner says so.
- Next session should know: PR #243 lands on green via the enabler. If
  the fm registry idiom ever changes (e.g. current headers start using
  caps SUPERSEDED), the verbatim negative fixtures in
  `tests/test_prompt_supersession.py` are where the assumption is pinned.
  Follow-up candidate (out of scope, not done): the deployed-drift table
  row for a superseded artifact could carry the flag too.

## ⟲ Previous-session review

`.sessions/2026-07-13-prompts-drift-row.md` (PR #234): its 💡 Session
idea was dispatch-ready — scoped, deduped against the backlog, with the
exact marker file and phrases named — which made this session's recon
nearly free; that discipline is worth copying. One improvement on its
trail: the idea cited the marker line but not the false-positive
landscape (the 27 current headers' lowercase "supersedes" idiom), which
the dispatch recon had to establish separately — future ideas proposing a
matcher should name the near-miss negatives too, since that is where the
real design risk lives.
