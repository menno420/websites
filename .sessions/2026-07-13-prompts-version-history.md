# 2026-07-13 — /prompts: per-seat prompt version history (ORDER 041)

> **Status:** `complete` — branch `claude/prompts-version-history`; lands
> via the pre-armed auto-merge on green.

- **📊 Model:** Claude Fable · worker (order execution) · feature-build

**What this session was about:** ORDER 041 (fleet-manager inbox, dispatched
per ORDER 040 TASK 2) — make the fleet prompt versions BROWSABLE: a version
history per seat (view any version, diff between versions, copy button per
body) sourced ONLY from the fleet-manager registry, the
deployed-vs-canonical drift row made version-aware, history reachable two
clicks from the site root. Rung: order — ORDER 041.

## What was done

- `app/prompt_history.py` — NEW: the version ladder derived DYNAMICALLY
  from the git history of the seat's authored prompt sources
  (`docs/prompts/v3/per-project/<seat>-custom-instructions.md` /
  `<seat>-startup.md`; superbot-2.0's files carry the bare `superbot-`
  prefix — verified live at fm@f8527f44). Ladder =
  `github.repo_api("/commits?path=…")`, bodies = `github.fetch_file(...,
  ref=<sha>)` — the SAME TTL-cached client as every page, zero new HTTP
  surface. Version labels are PARSED from each fetched file (header
  comment / early body line); no label → short sha shown, a version name
  is never invented (the ladder moved v3.5→v3.6 within the hour ORDER 041
  was written — hardcoding is drift by construction). Diff = server-side
  `difflib.unified_diff` over the clean paste bodies, GET-only; query shas
  must be hex AND resolve inside this file's own ladder (no arbitrary-ref
  fetch). Honest degradation: commits API unreachable/empty → "history not
  available" (never a fabricated ladder); a failed file-at-sha fetch →
  "version body unavailable" for that rung only; unknown seat/file → 404.
- `GET /prompts/history/{seat}?file=ci|startup&a=<sha>&b=<sha>` —
  registration-only touch in `app/main.py`; template
  `prompt_history.html` renders each rung through the shared ORDER 015
  `prompt_block` partial (copy button per body via `static/copycode.js`,
  untrusted-data `<pre>` discipline) + a GET diff-picker form.
- `app/prompts.py` — deployed-drift rows now VERSION-AWARE: each row with
  a deployed record carries "deployed vX · canonical vY" (deployed side
  parsed from the record's own text, canonical side from the HEAD registry
  copy — the newest canonical label; a side with no token says
  `unstamped`, never invented).
- `app/roster.py` — seat 9 `curious-research` pinned (fm prompts v3.6;
  projects/curious-research/ package verified live 2026-07-13) →
  /prompts renders 29 artifacts and the registry drift chip is honest
  again. ⚑ contained bonus, decide-and-flag.
- `/prompts` links every seat (seat card + drift-table cell) to its
  history page → any seat's current + historical prompts are two clicks
  from the site root (/ → /prompts → history).
- Single source of truth kept: render-only, no prompt body copied into
  this repo.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — **962 passed** (main baseline 945; +15 new in
  tests/test_prompt_history.py, +2 in tests/test_prompts.py);
  `python3 bootstrap.py check --strict` — green except the designed
  born-red card hold (advisory warnings pre-existing). Live-path evidence
  from the dev container: /prompts rendered all 29 artifacts live (0 fetch
  failures — curious-research included) and raw fetch-at-sha returns 200
  (v3.5 commit 728dc07); the commits API is proxy-blocked here, and the
  page rendered the designed "history not available" banner — the honest
  degrade path, exercised for real.

⚑ Self-initiated: roster seat 9 only — the rest is ORDER 041.

## 💡 Session idea

**Surface the version ladder on each seat's dispatch screen
(/projects/{package}) + owner console** — ORDER 041's full text wants the
same prompt data "everywhere it helps (the /prompts library, each seat's
page on the projects/console surfaces, the owner console) as views of ONE
source". This session shipped the canonical history home (/prompts/history)
and the library links; the dispatch screen and owner console still render
only HEAD copies. `prompt_history.history()` is already the one reusable
data path — add a compact "versions: v3.6 (current) · v3.5 · v3.4 →
full history" strip to `project_detail.html` and an owner-console row,
zero new fetch semantics. Worth having because the dispatch screen is
where the owner actually pastes from — the place a stale paste gets
caught. Deduped: no versions/history entry in `docs/ideas/backlog.md`;
nothing in app/projects.py renders history today.

## ⟲ Previous-session review

`.sessions/2026-07-13-prompts-drift-row.md` (PR #234): its honest-state
ladder (never green from prose, per-row degradation) transferred directly —
this session's "history not available"/"version body unavailable"/
short-sha-fallback rules are the same principle applied to a new surface,
and its fixture discipline (copy the REAL committed shapes) made the new
version-aware assertions cheap to add. Its "940 passed (+8 new)" convention
was slightly stale as a baseline (main had moved to 945 by branch time) —
counted fresh here rather than trusting the card. Nothing misleading found.
