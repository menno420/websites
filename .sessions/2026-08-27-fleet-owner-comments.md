# 2026-08-27 — connect repository review to durable owner comments

> **Status:** `in-progress` — Fleet Manager #952 is landed, and the three
> latest exact-head findings in website #523 are corrected and under final
> verification.

- **📊 Model:** GPT-5 · high · feature build
- **📍 Venue:** chatgpt-work

**What this session was about:** Complete the owner-directed estate review
loop after `/repos` shipped: read Fleet Manager's versioned public comment
contract, show active and consumed feedback with honest provenance, and let an
authenticated owner submit a repository-specific comment through Fleet
Manager's protected branch-and-PR path. Fleet Manager remains the record owner;
`websites` remains the UI and writeback client.

## What was done

- `app/owner_comments.py` reads only Fleet Manager's public v1 ledger through
  the existing anonymous cache boundary. `/repos` pays for one root-index read;
  `/repos/{name}` adds bounded active/consumed records for that validated
  repository, retaining source links and explicit partial/unavailable state.
- Estate domain/service models now carry stable owner-comment summaries and
  records. Templates render the owner's wording as untrusted plain text and do
  not turn missing, stale, malformed, private, or contradictory upstream data
  into invented zeros or success.
- `GET /owner/repository-comments/{name}` and
  `POST /owner/repository-comments/submit` reuse owner Basic auth, same-origin
  CSRF, and per-route rate limiting. Mutation performs an independent fresh
  anonymous visibility read that neither trusts cache nor joins an older
  in-flight request, validates the repository against Fleet Manager's estate
  model, requires explicit public acknowledgement, and preserves the accepted
  wording verbatim.
- `app/owner_comment_writeback.py` uses only
  `FLEET_MANAGER_WRITEBACK_TOKEN`: it pins Fleet Manager `main`, creates record
  + repository index + root index in one Git Data commit on a deterministic
  `claude/owner-comments-*` branch, and opens a ready PR. Form-scoped
  idempotency makes lost-response replay resolve to that exact branch/payload,
  even after `main` moves or the current ledger reaches a growth cap. Fresh
  submissions bound record count and both prospective generated indexes before
  any GitHub mutation. Pending PR, unavailable, retryable, and failed states
  are distinct; none is called durable before the public record is readable on
  Fleet Manager `main`.
- Hostile-source and upstream-response hardening rejects duplicate keys,
  noncanonical/invalid UTF-8 JSON, deep/oversized shapes, non-LF generated
  indexes, malformed nested GitHub responses, lone Unicode surrogates, and
  credential echo before truncation. Read fan-out is capped at four and eight
  seconds for the selected repository.
- Decision 0039, `docs/site.md`, environment manifests, and the repository route
  table document the ownership, security, freshness, and capability boundary.

⚑ Self-initiated: no — direct owner implementation request, following the
separate Fleet Manager storage/index/consume change.

## 💡 Session idea

After a pending PR is returned, add a small read-only landing receipt page that
polls the public Fleet Manager record path by deterministic id and changes from
pending to durable only when `main` serves the exact record. That would close
the owner's immediate visual loop after submission without persisting status in
Railway or creating another truth store.

## ⟲ Previous-session review

The estate-review session made `/repos` the canonical visual catalogue and
deliberately left comments unavailable until Fleet Manager owned a real durable
contract. This session takes that explicit next boundary without reopening the
read-surface architecture.

## Review disposition

- Codex review of `270688c44d` raised three P2 findings: raw JSON had already
  lost duplicate keys, mutation trusted cached public visibility, and successful
  POST replay could duplicate a comment. **[conceded]** All three were fixed,
  replied to with exact evidence, and their threads were resolved.
- Later exact-head reviews found and closed credential-redaction, PR identity,
  first-submit timestamp, moving-main replay, visibility-coalescing, bounded
  index growth, replay-before-growth, and malformed optional-context cases.
  **[conceded]** Every valid finding received a regression, exact-head reply,
  and resolved thread; the compare-list finding was rejected with the official
  GitHub API contract plus boundary tests.
- Exact review of remote product head
  `b2914e075723fd2695a0e8a7b0279911cb696156` found two further P2 cases: a
  replay/growth-gate TOCTOU and mutation visibility limited to the first
  repository-listing page. Both were **[conceded]**, corrected, and covered by
  regressions before the next reviewed head.
- Exact review of `6361835410` found three remaining P2 cases: a repository
  index missing from the root could be rendered as zero comments, equal counts
  did not reconcile differing latest timestamps, and a deterministic replay
  after PR merge could create duplicate work. All three are **[conceded]**.
  Root/repository reconciliation now covers presence, counts, and both latest
  timestamps; merged replays verify the exact PR, three-file payload, ancestry,
  and active current-`main` record before returning an explicit landed/replayed
  result. Focused regressions cover each finding.
- Exact review of `fb46e96755` found two final P2 cases. A replay after
  legitimate consumption still required the active record, and transient PR
  creation/lookup failures were flattened into a non-retryable result. Both
  are **[conceded]**. Replays now accept exactly one reconciled active or
  consumed record; the consumed alternative validates its canonical payload
  and consumption metadata before returning a distinct consumed-history
  result. Transient PR failures retain `failed_retryable`. Focused regressions
  cover retained/deleted branches, the owner response, and the failure matrix.
- Exact review of `6ed5b61ba6` found one remaining P2 classification gap:
  transient deterministic branch-creation failures were still flattened to
  non-retryable. **[conceded]** The branch-creation path now uses the same
  permission-aware shared classifier as the PR path, and the existing failure
  matrix pins a 503 response as `failed_retryable`.

## Verify

- `python -m pytest tests/ botsite/tests dashboard/tests review/tests -q` —
  **2,503 passed**, 5 deprecation warnings, on Windows.
- Focused owner-comment reader/writeback/routes after the final review fixes —
  **149 passed**; the earlier broader focused pass was **184 passed**, with
  surrounding estate and repository routes at **60 passed**.
- `git diff --check` — clean locally and on the exact remote PR diff.
- `python3 bootstrap.py check --strict` — held red by this deliberate
  `in-progress` status until the final corrections and review are complete.

## Landing

- Fleet Manager storage/index/router/consume contract:
  `menno420/fleet-manager#952`, merged as `089e0053791a8a6b33c51869ae4780f0d03b1ac9`.
- Website UI/read/writeback: `menno420/websites#523` — open on protected
  `main`; final corrections remain before merge-on-green.
- Production write capability is not claimed by repository tests; after deploy,
  the owner form itself reports whether the dedicated credential is available.
