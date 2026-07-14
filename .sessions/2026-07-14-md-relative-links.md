# 2026-07-14 — rewrite relative links in rendered remote markdown + fleet-wide /favicon.ico

> **Status:** `complete` — PR #322, branch `claude/md-relative-links-0714`;
> relative links inside remotely-rendered markdown now rewrite to their
> GitHub source (or de-linkify when the source is unknown), the smoke-crawl's
> `.md`-container carve-out is deleted so the browser gate guards the fix,
> and all four services answer `GET /favicon.ico`.

- **📊 Model:** Claude Fable 5 · worker · backlog promotion + fleet gap fix

**What this session was about:** backlog promotion — the `docs/ideas/backlog.md`
bullet "Rewrite relative links inside rendered remote markdown to their GitHub
source (or de-linkify them)" (captured 2026-07-14 by the smoke-crawl session,
PR #321). The control-plane renders other repos' markdown verbatim in
`<div class="md">` (heartbeats on /fleet, the fleet-manager ledger on /reviews,
environment docs on /environments), and relative links inside that content
resolve against this origin and 404 — the first smoke-crawl run flagged 20 of
them live. Plus the second PR #321 follow-up finding: the fleet-wide
`/favicon.ico` 404 on raw JSON/XML views — the route added to all four
services.

## What was done

- `app/journal.py` — `render_markdown(text, source=None)`: when the fetched
  document's source (`{"repo", "path", "ref"}`, owner always `config.OWNER`)
  is known, relative link hrefs rewrite to
  `github.com/<owner>/<repo>/blob/<ref>/<resolved-path>` and relative image
  srcs to `<GITHUB_RAW_BASE>/<owner>/<repo>/<ref>/<resolved-path>`, resolved
  against the fetched file's directory (`./`, `../`, and root-relative `/`
  handled via posixpath; fragments preserved on links). Absolute
  http(s)/mailto, protocol-relative `//`, and pure `#fragment` links are
  untouched. Unknown source, or a `../` path escaping the repo root →
  DE-LINKIFY: the link text survives, the anchor dies (images degrade to
  their alt text). The rewrite runs on the FINAL bleach-sanitized HTML
  (bleach's serializer normalizes attributes, raw inline HTML included);
  only percent-quoted paths and HTML-escaped fragments enter the rewritten
  attribute — the sanitization pipeline itself is unchanged.
- All 7 render sites pass their source: `app/fleet.py` (lane heartbeat),
  `app/orders.py` (inbox order bodies), `app/projects.py` (registry meta.md),
  `app/owner_queue.py` (owner-queue doc), `app/environments.py` (registry
  files), `app/reviews.py` (review ledger), `app/main.py`
  (/journal/{repo}/file, ref-aware).
- `scripts/smoke_crawl.py` — the documented `.md`-container carve-out
  (`RENDERED_REMOTE_MD_SELECTOR` + its comment block + the `closest()`
  filter in link discovery) DELETED: the crawler discovers anchors inside
  rendered remote markdown again, so a regression here goes red on the next
  scheduled crawl. The removal proves itself on the first scheduled crawl
  after merge+deploy — the crawler probes the LIVE Railway URLs, so a local
  run pre-merge would only re-flag the 20 not-yet-fixed prod links.
- `GET /favicon.ico` on all four services (`app/main.py`, `botsite/app.py`,
  `dashboard/app.py`, `review/app.py`) — `FileResponse` of the existing
  `static/favicon.svg` (`image/svg+xml`), the icon base.html already
  declares; closes the PR #321 raw-view console-404 finding. The route is
  classified non-page in each service's clarity-structure registry.
- Tests: `tests/test_app.py` — rewrite of bare/./../root-relative links +
  image, fragment preservation, non-main ref, absolute/#fragment/mailto
  untouched, de-linkify without source (text kept, no anchor, img → alt),
  de-linkify on root escape; plus a favicon test per service
  (`tests/test_app.py`, `botsite/tests/test_botsite.py`,
  `dashboard/tests/test_dashboard.py`, `review/tests/test_review.py`).
- `docs/ideas/backlog.md` — the relative-links bullet flipped `captured` →
  `built` (PR #322); this session's 💡 appended.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 1381 passed, 1 warning (baseline 1373 + 8 new);
  `python3 bootstrap.py check --strict` — green once this card flipped
  complete (the only red during the session was this card's designed
  born-red hold).

⚑ Self-initiated: no — backlog promotion (the smoke-crawl session's 💡 bullet
in `docs/ideas/backlog.md`) + the PR #321 follow-up favicon finding.

## 💡 Session idea

**Sample-verify rewritten source-link targets — a bounded existence check on
the github.com blob URLs the markdown rewriter mints** — the fix converts
same-origin 404s inside rendered remote markdown into EXTERNAL github.com/raw
links, and the smoke-crawl never follows external links by documented design:
the failure class didn't die, it moved outside every gate's scope (a wrong
path resolution or an upstream file rename now yields a GitHub 404 nothing
measures). A bounded sample — ~10 rewritten targets per scheduled crawl,
HEAD via the raw host the app already uses — puts a floor back under the
rewrite without hammering GitHub. Worth having because a rewriter that mints
dead external links is exactly as broken for the visitor as the 404s it
replaced — just invisible to the gate that caught the originals. Deduped
against `docs/ideas/backlog.md` + the queue-state NEXT list: the rewrite
bullet ships the rewriter; nothing checks external/rewritten link liveness.
Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The testing-import-valve session (PR #320) did well — one-transaction
restore with ids preserved, honest legacy-column defaults, and 8 tests that
cover the CSRF and oversize edges most restore endpoints skip; what it
missed: its own 💡 concedes orphan-row corruption still imports silently
(SQLite foreign keys are off), so the valve's "faithful restore" promise has
one admitted hole the proposed referential pass hasn't closed yet.
