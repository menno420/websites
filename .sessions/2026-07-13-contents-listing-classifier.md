# 2026-07-13 — github: shared contents-listing honesty classifier (classify_listing)

> **Status:** `complete` — PR #250, branch `claude/contents-listing-classifier`;
> the four hand-rolled degraded-listing ladders (/projects overview + detail,
> the /prompts drift chip, /ideas) now share ONE classifier with the 404
> disposition as an explicit per-caller parameter; lands via the auto-merge
> enabler on green.

- **📊 Model:** Claude Fable 5 · worker · ORDER-022-item-2 slice

**What this session was about:** ORDER 022 item 2's standing quality floor,
via the backlog bullet at `docs/ideas/backlog.md:169` ("Shared
contents-listing honesty classifier" · `captured`): four surfaces hand-roll
the same degraded-listing ladder over a `github.repo_api` contents
envelope — `projects.overview`, `projects.detail`, `prompts.registry_drift`,
`ideas.repo_ideas` — and the copies have already begun to diverge. One
helper, `github.classify_listing(result, *, on_404, reason_404, subject)
-> (state, reason)`, with the 404 disposition as an explicit per-caller
parameter, makes the pages share one ladder and makes deliberate
differences declared instead of re-derived.

## What was done

- `app/github.py` — `classify_listing(result, *, on_404, reason_404=None,
  subject="the listing") -> (state, reason)` next to `short_reason`: ok
  (empty list is still ok — callers own the meaning), 404 → the caller's
  explicit disposition + prose, non-list 2xx → "unexpected listing payload
  (HTTP <status>)", other failure → not-configured (token unset, names
  itself + fetch reason) / unavailable. EVERY returned reason — including
  caller prose and composed text — re-passes `short_reason`, extending the
  #237→#240 140-char bound to composed reasons.
- `app/projects.py` `overview()` + `detail()` — migrated onto the shared
  ladder (on_404="empty" with their existing registry-still-landing prose;
  the not-configured text reproduced char-for-char via `subject`).
- `app/prompts.py` `registry_drift()` — any non-ok state maps to "unknown"
  (chip vocabulary unchanged) with the classifier's reason, so a missing
  token now names itself.
- `app/ideas.py` `repo_ideas()` — on_404="missing" (absence, not error);
  `listing_error` carries the classifier reason for
  not-configured/unavailable (token-unset failures now name the token).
- `tests/test_classify_listing.py` — 11 network-free unit pins of the
  ladder contract (ok / empty-list-ok / 404 default + custom / token-set
  vs token-unset on 403 and status-0 / non-list 2xx / composed-reason and
  custom-404 truncation at 140).
- Per-page pins for the honest improvements: `tests/test_prompts.py`
  (unknown reason names the token; non-list 2xx → unknown),
  `tests/test_app.py` (ideas listing_error token text; non-list 2xx),
  `tests/test_projects.py` (overview non-list 2xx → unavailable). All
  pre-existing ladder pins pass unedited.
- `docs/ideas/backlog.md` — the source bullet flipped `captured` → `built`
  (PR #250); this session's 💡 captured below.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 1089 passed, 1 warning; `python3 bootstrap.py check
  --strict` — green except this card's own designed born-red HOLD (flipped
  by this commit) and the pre-existing never-exit-affecting
  `owner-action-fields` advisory on control/status.md (not owned here).

⚑ Self-initiated: no (dispatched ORDER 022 item 2 slice).

## 💡 Session idea

**Pin `config.GITHUB_TOKEN` explicitly in every degradation-ladder test —
ambient-env-sensitive assertions are latent flakes** — while migrating the
ladders I found `tests/test_prompts.py::test_drift_unknown_when_listing_
unavailable_never_false_green` (and the ideas listing-error test) assert
reason text WITHOUT pinning the token: they pass today only because the
asserted substring survives both the token-set ("ConnectError: unreachable")
and token-unset (composed not-configured text) branches — the same test
exercises DIFFERENT rungs of the ladder depending on whether the runner's
environment happens to export GITHUB_TOKEN (this dev container proxy-injects
one; CI may not). One sweep adding `monkeypatch.setattr(config,
"GITHUB_TOKEN", ...)` to every test that renders a failure reason would make
each pin assert exactly one rung. Worth having because a test whose meaning
changes with ambient env is a flake waiting for the first assertion that
does NOT survive both branches — and the classifier now makes the two
branches render deliberately different text. Deduped against
`docs/ideas/backlog.md` + the queue-state NEXT list: token-related bullets
there are all about PAGE behavior when the token is unset; nothing touches
test-suite env pinning.

## ⟲ Previous-session review

The venture-vetting-catalog session (PR #248) did well — it curated all 22
vetting packets by hand with per-title states derived from each packet's own
Status/Verdict (nothing invented), kept the buy link to the one genuinely
live product, and shipped the page as a linked subpage instead of growing
/products; what it missed is that its own session idea names the weakness it
shipped with — a hand-curated registry pinned at `2c039e3` starts decaying
immediately, and the sha-drift nag that would catch it was captured as a
bullet rather than landed alongside the catalog it protects.
