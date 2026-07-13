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

(to be filled as work lands)

⚑ Self-initiated: no — ORDER 022 item 3 (idea from the drift-row
session card, dispatched by coordinator).
