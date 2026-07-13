# 2026-07-13 — railway reason bound: route Railway GraphQL error reasons through short_reason()

> **Status:** `complete` — PR #244, branch `claude/railway-reason-bound`;
> every error reason minted in `app/railway.py` now rides the same
> `short_reason()` bound as the GitHub envelopes from #240 (140-char
> ellipsis cap, single line, markup bodies → generic phrase), so the
> owner environments/envhub/envdrift banners can never render an
> upstream error DOCUMENT; lands via the auto-merge enabler on green.

- **📊 Model:** Claude Fable · worker · hardening-slice

**What this session is about:** finishing the alignment the #240 card
itself filed as a follow-up: PR #240 bounded every GitHub-envelope error
reason at the source (`app/github.py` `short_reason()` — 140-char cap,
single line, markup bodies → generic phrase), but `app/railway.py` still
minted its OWN GraphQL error strings with only a `[:300]` truncation and
no markup stripping, so a Railway failure could paint up to 300 chars of
raw upstream error text — including HTML — onto the owner
envhub/envdrift/environments pages. This session routes ALL error-reason
minting in `app/railway.py` through the same `short_reason()` helper,
with tests. Coordinator-assigned slice under ORDER 022 (night-run
quality floor).

## Checklist

- [x] Claim landed (`control/claims/railway-reason-bound.md`) + born-red card (first commit)
- [x] PR opened ready (not draft), auto-merge left to the enabler workflow — PR #244
- [x] `app/railway.py`: GraphQL errors-array path bounded via `short_reason` (bare `[:300]` gone)
- [x] `app/railway.py`: HTTP-status / non-JSON-body path bounded via `short_reason`
- [x] `app/railway.py`: httpx exception path bounded via `short_reason` (previously unbounded)
- [x] Tests: HTML body / huge body / multiline / short-passthrough + rendered owner-page test
- [x] All four suites green + `bootstrap.py check --strict` (only this card's designed hold)
- [x] Merge origin/main (prompts-supersession landed cleanly), flip this card, drop the claim

## What was done

- code touched (1): `app/railway.py` — `from .github import short_reason`
  (no cycle: `app/github.py` imports nothing from `app/railway.py`; both
  are app/-internal client-layer, so no shared-module lift was needed).
  All three `_graphql` mint sites routed through the helper: the GraphQL
  errors-array join (replacing the old bare `[:300]` cap, with the HTTP
  status passed through when ≥300 so markup messages get the
  `HTTP <status> — non-JSON error body` head), the HTTP-status /
  non-JSON-body phrase, and the `httpx.HTTPError` exception path (the
  one previously completely unbounded). The non-JSON-body path still
  exposes ONLY the status, never body text — behavior preserved, just
  bounded. NAMES-NEVER-VALUES untouched: `_names_only` and every
  redaction seam unchanged. A small `_make_client()` seam lets tests
  drive the REAL `_graphql` via `httpx.MockTransport`.
- tests touched (1 new): `tests/test_railway_reason_bound.py` — 8 tests
  in the #240 idiom (mock transport through `_make_client`, never
  stubbing `_graphql` itself): HTML 503 document → bounded status
  phrase; HTML inside a GraphQL errors message → generic phrase; ~62 KB
  errors message → 140-char ellipsis with head preserved; multiline
  GraphQL error → single line; short reason verbatim + bare
  `HTTP 500`; long multiline httpx exception → bounded single line;
  ok-path empty error; and a rendered `/owner/environments` pass under a
  huge-HTML GraphQL failure asserting the banner shows the bounded
  phrase and none of the raw document.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 1021 passed pre-merge (597/214/60/150), 1035
  passed after merging origin/main (prompts-supersession landed +14);
  `python3 bootstrap.py check --strict` — green except this card's own
  designed born-red HOLD (flipped by this commit) and the pre-existing
  never-exit-affecting `owner-action-fields` advisory on
  control/status.md (not owned here).

⚑ Self-initiated: no — coordinator-assigned slice under ORDER 022
(quality floor), the follow-up named by the #240 session card.

## 💡 Session idea

**Reason-bound conformance test over ALL error-minting modules** — a
single parametrized test that imports every module minting user-visible
failure reasons (github, railway, freshness, and future clients) and
asserts each routes through `short_reason` (e.g. by scanning for bare
`[:N]` caps on error strings or exercising a shared fixture), so the
next new client can't reintroduce an unbounded reason. Worth having
because this same bug has now been fixed three times (#237 page-side,
#240 github-source, #244 railway-source) — the pattern wants a gate, not
a fourth session. Deduped against `docs/ideas/backlog.md` + the
queue-state NEXT list: no existing bullet covers a cross-module
reason-bound gate. Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The #240 session drew the bound at the right choke point and its card
honestly ledgered `app/railway.py` as the known-unbounded remainder
instead of silently absorbing scope — that explicit "out of scope, noted
as a possible follow-up alignment" line is exactly what made this slice
a clean pickup; what it missed is only that the railway exception path
was not merely `[:300]`-capped but fully unbounded, which this session's
audit surfaced.
