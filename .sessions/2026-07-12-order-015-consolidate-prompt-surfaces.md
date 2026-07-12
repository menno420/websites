# 2026-07-12 — ORDER 015: consolidate the two prompt surfaces onto one render path

> **Status:** `complete` — branch `claude/order-015-consolidate-prompts`,
> parks as a READY PR to main (build worker; merge is deliberately not this
> session's call — the auto-merge enabler arms server-side).

- **📊 Model:** claude-fable-5 · build worker · order

**What this session was about:** Rung: order — ORDER 015 (control/inbox.md):
after ORDER 014's /prompts library landed (PR #165), the control-plane had
TWO independently built surfaces rendering fleet-manager registry prompts —
/prompts and the /projects/{package} dispatch screen (PR #158) — with
parallel fetch/parse/render logic that drifts and doubles the maintenance
surface. Unify onto ONE fetch/render/copy code path; both URLs keep working;
/prompts stays the canonical page for finding prompts and the dispatch
screen links to it.

## What was done

- **Shared model — `app/prompt_artifacts.py` (new):** the single
  fetch+parse path both surfaces use. Carries `REPO`/`REF`
  (fleet-manager@main), `blob_url()`, `extract_provenance()` (moved from
  `app/prompts.py`), `build_artifact()` (the canonical artifact dict:
  seat/label/path/github_url/ok/text/error/fetched_at/cached/provenance/
  chars) and `fetch_artifact()` over the TTL-cached `github.fetch_file`
  raw-content layer. No cross-service imports; artifacts stay untrusted
  DATA (autoescaped, never `|safe`, never mutated).
- **`app/prompts.py` slimmed to the artifact REGISTRY only:** its forked
  provenance regex, `_blob_url`, and hand-rolled per-artifact dict building
  deleted; `overview()` now gathers `prompt_artifacts.fetch_artifact(...)`
  and adds page anchors. `REPO`/`REF`/`extract_provenance`/
  `_PROVENANCE_MAX_CHARS` re-exported so the import surface holds.
- **`app/projects.py` detail() rides the same path:** the duplicated
  per-role-file `github.fetch_file` + ok/text/error block replaced by
  `prompt_artifacts.fetch_artifact()`; each role file now carries the
  canonical dict under `artifact` (with `text`/`fetch_error` mirrors kept
  for meta extraction and existing consumers); module-level `REPO` +
  `_blob_url` now imported from the shared module. `detail()` output gains
  `ttl` for the shared partial's freshness line. `/projects.json`
  (overview) contract untouched.
- **Shared render partial — `app/templates/_prompt_artifact.html` (new):**
  `prompt_block(a, ttl)` — provenance line, freshness (cache/TTL) line,
  autoescaped `<pre>` paste body, honest per-artifact error banner.
  `prompts.html`'s macro body and `project_detail.html`'s role-file block
  both replaced with calls to it; the copy path was already the shared
  `static/copycode.js` on both. Dispatch screen header now links to
  /prompts as the canonical prompt-finding page (ORDER 015's "the other
  links to it").
- **Tests — `tests/test_prompt_consolidation.py` (new, 6):** canonical
  model shape (ok + failure, identical keys), fetch rides the shared
  github layer (repo/ref pinned), single-source-of-truth delegation
  (`prompts.extract_provenance is prompt_artifacts.extract_provenance`,
  `projects._blob_url is prompt_artifacts.blob_url`), byte-identical `<pre>`
  bodies on BOTH URLs from one fixture (hostile content escaped identically
  — autoescape proof), identical honest degradation on a failed fetch, and
  the dispatch→/prompts canonical link. All 37 existing prompts/projects/
  json-contract tests untouched and green.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 648 passed, 1 warning in 43.50s; `python3 bootstrap.py
  check --strict` — all checks passed (sole standing advisory:
  owner-action-fields on control/status.md, never exit-affecting).

⚑ Self-initiated: no — ORDER 015 from control/inbox.md, routed by the
coordinator.

## 💡 Session idea

**One seat-roster constant for the control-plane** — `prompts.SEATS` (the
pinned 8-seat artifact registry) and `projects._START_ORDER` (the owner
dispatch order + aliases) both hand-carry the fleet's seat names; a seat
rename upstream means editing two constants in two modules or the surfaces
disagree (one 404s, the other mis-sorts). Worth having because ORDER 015
just paid down exactly this class of duplication one layer up — extract a
`SEAT_ROSTER` (name + aliases + rank) both modules derive from. Deduped
against `docs/ideas/backlog.md`: the backlog carries prompt/dispatch UI
items but nothing on the roster constant. Not captured in the backlog by
this session (card-only; the backlog bullet is the follow-up).

## ⟲ Previous-session review

The ORDER 014 session (/prompts, PR #165) did well: the pinned 26-artifact
registry with per-artifact honest degradation and the verbatim-paste-body
discipline made today's consolidation mechanical — the artifact dict it
designed became the shared model almost unchanged. What it missed: it BUILT
the duplication ORDER 015 removes — the dispatch screen (PR #158) already
rendered the same registry files, and instead of extracting a shared block
then, it forked the fetch/parse/render logic into a second module the same
day; a "does another surface already render this?" check before building a
new page would have folded 014 and 015 into one landing.
