# 2026-07-12 — ORDER 020: owner writeback + AI note-drafting on the launch console

> **Status:** `complete` — PR branch `claude/order-020-owner-writeback`,
> parks READY + green for the owner (build worker; merge is deliberately
> not this session's call).

- **📊 Model:** Claude Fable 5 · build worker · order

**What this session was about:** ORDER 020 (control/inbox.md @ main
`3bfdf18`): the owner wants to "directly write reviews on the websites…
make an owner action complete or request assistance… suggest corrections,
add my ideas to certain things", with that input flowing back into the
fleet's git source of truth — or degrading honestly until the write-scoped
token exists.

## What was done

- **Writeback engine** `app/writeback.py` — each gated submission maps to
  one GitHub contents-API commit on menno420/websites: assistance requests
  append a properly-numbered ORDER to `control/inbox.md` (number read from
  the file at commit time, append-only, provenance "owner via launch
  console"); notes/corrections/ideas and mark-complete assertions append to
  `docs/owner/owner-notes.md` (seeded this PR; created at runtime with the
  same header if absent). `GITHUB_TOKEN` is read from env PER ATTEMPT via
  the new uncached `github.api_request()` (per-request token override), so
  the PAT pasted into Railway lights up without a redeploy. `committed` is
  claimed ONLY when the PUT response carries the commit SHA (stored +
  linked); otherwise the entry stays `queued`/`failed` with the exact error
  class — a commit is never faked.
- **Local audit trail** — SQLite (`WRITEBACK_DB_PATH`, default
  `app/writeback.sqlite3`, gitignored; the botsite/testing_store.py
  precedent) records every submission with timestamp/action/target/text/
  status/SHA/attempts. `/owner/queue` lists them, queued rows visibly
  queued with a retry button; the ephemeral-disk caveat is shown in the UI.
- **Console** `GET /owner/queue` + five POSTs under
  `/owner/queue/actions/*` (complete/assist/note/retry/draft) in
  `app/owner.py` — Basic auth (SITE_PASSWORD, fail-closed) + the ORDER 013
  same-origin + rate-limit floor on every state change. Server-rendered
  forms, zero JS; hard input caps (300/4000 chars), rejection over
  truncation. The public `/queue` stays read-only (one header link to the
  gated console).
- **AI note-drafting** `app/owner_assist.py` — the botsite/testing_ai.py
  Messages-over-httpx pattern ported with its guards: runtime-per-call key
  read (`ANTHROPIC_API_KEY`), honest degradation without it, in-process
  daily cap (`OWNER_ASSIST_DAILY_CAP`, default 30), one retry max
  (5xx/timeout only), injection framing (queue content + rough text are
  tagged untrusted DATA). Default model env-overridable
  (`OWNER_ASSIST_MODEL`). Drafts only ever pre-fill the form — the AI never
  writes back; the owner's separate guarded submit does.
- **Owner flag** — six-field ⚑ OWNER-ACTION appended to
  docs/owner/OWNER-ACTIONS.md: mint the fine-grained contents:write PAT
  (menno420/websites only) and paste as GITHUB_TOKEN on control-plane +
  botsite.
- **Tests** tests/test_owner_writeback.py (17, offline): auth/CSRF/rate
  limit on every route, queued-without-token, mocked-PUT commit path with
  ORDER numbering asserted, 403/no-SHA never-fake-commit pins, retry flush,
  validation caps, AI draft mocked + key-absent degradation, console
  render.

## Honest edges

- Direct pushes to `main` may be ruleset-blocked (the `quality` required
  check); if so the PUT fails and the entry queues with the exact GitHub
  error — `WRITEBACK_BRANCH` can point the engine at a side branch the
  fleet merges. Flagged in the PR body; decide-and-flag.
- Queued entries do not survive redeploys (ephemeral disk) — stated in the
  UI next to every queued row.

## 💡 Session idea

**Auto-flush queued writebacks on token arrival** — today a queued entry
commits when the owner presses retry (or on the next submit). A tiny
startup/interval sweep in the engine ("any queued entries + token now
present → attempt_commit each, oldest first") would flush the backlog the
moment the PAT lands on Railway, with zero owner clicks — and it reuses
`attempt_commit` verbatim, so the never-fake-commit contract carries over
for free. Worth having because the queued→lost-on-redeploy window is the
one honest weakness this PR ships with, and auto-flush shrinks it to
minutes.

## ⟲ Previous-session review

ORDER 019 PR1 (#187, the /queue filters) set this session up well: the
centralized listfilter left `owner_queue.overview()`'s item shape untouched
and exposed `headline()`, which this session reused verbatim for draft
grounding — zero rework at the merge seam. What it missed: nothing this
session tripped over; the one friction was inherited from earlier — the
queue items still carry no stable ID, so writeback targets are matched by
headline text (fine for provenance notes, but a future stable-ID field in
the OWNER-ACTION format would make mark-complete reconciliation mechanical).
