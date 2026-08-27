# 2026-08-27 — connect repository review to durable owner comments

> **Status:** `in-progress` — branch `codex/fleet-owner-comments`; flips to
> `complete` + PR number as the deliberate LAST code step. Implementation and
> local review are complete; Fleet Manager #952 and exact-head Codex review
> remain ahead of the flip.

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
  CSRF, and per-route rate limiting. Mutation refreshes anonymous public
  visibility immediately, validates the repository against Fleet Manager's
  estate model, requires explicit public acknowledgement, and preserves the
  accepted wording verbatim.
- `app/owner_comment_writeback.py` uses only
  `FLEET_MANAGER_WRITEBACK_TOKEN`: it pins Fleet Manager `main`, creates record
  + repository index + root index in one Git Data commit on a deterministic
  `claude/owner-comments-*` branch, and opens a ready PR. Form-scoped
  idempotency makes lost-response replay resolve to that exact branch/payload.
  Pending PR, unavailable, retryable, and failed states are distinct; none is
  called durable before the public record is readable on Fleet Manager `main`.
- Hostile-source and upstream-response hardening rejects duplicate keys,
  noncanonical/invalid UTF-8 JSON, deep/oversized shapes, non-LF generated
  indexes, malformed nested GitHub responses, lone Unicode surrogates, and
  credential echo before truncation. Read fan-out is capped at four and eight
  seconds for the selected repository.
- `[D-0039]`, `docs/site.md`, environment manifests, and the repository route
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
- Independent contract/security audits then drove additional fail-closed work
  across idempotent recovery, bounded fan-out, malformed transports, nested
  response validation, canonical LF parsing, invalid Unicode, and token
  redaction. Final exact-worktree verdict: no remaining P0/P1/P2; no concrete
  P3 blocker.
- Remote head `f18021147e783c49b0c87eca8592fd7d4e774bda` is byte-identical to
  locally audited HEAD `7889e8a`; its exact-head Codex review was requested
  before the final flip.

## Verify

- `python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q` —
  **2,433 passed**, 5 deprecation warnings.
- Focused comment/public-read/auth/CSRF/rate-limit audit — **155 passed**.
- Independent strict contract pass — **122 passed**.
- `git diff --check` — clean locally and on the exact remote PR diff.
- `python3 bootstrap.py check --strict` — substantive checks green; only this
  deliberate `in-progress` card remains before the final flip.

## Landing

- Fleet Manager storage/index/router/consume contract: `menno420/fleet-manager#952`
  (ordered dependency; must land first).
- Website UI/read/writeback: `menno420/websites#523` — READY, held by this card
  until the dependency and exact-head review are terminal.
- Production write capability is not claimed by repository tests; after deploy,
  the owner form itself reports whether the dedicated credential is available.
