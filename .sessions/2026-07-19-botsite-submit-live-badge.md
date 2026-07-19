# 2026-07-19 — botsite /submit live-badge fix + ledger finalize

> **Status:** `in-progress` — branch `claude/botsite-submit-live-badge`; the
> live `/submit` form still shows a hardcoded "Stub — not wired" badge even
> though the Postgres-backed intake is now live. Born red; flips to `complete`
> + PR number as the deliberate LAST code step.

- **📊 Model:** Claude Opus 4.8 · effort: high · task-class: bugfix + ledger-finalize

**Ask:** ASK-0004 / ASK-0002 · **Date:** 2026-07-19
**Branch:** `claude/botsite-submit-live-badge`

## Goal

The live `/submit` form still shows a hardcoded "Stub — not wired" badge (and
the matching "does not store or send your message anywhere yet" hint + "Heads
up" provisioning block) even though the Postgres-backed intake is now live —
gate that stale copy on `intake_live` so it disappears when the store is live,
and show a subtle "reviewed before publishing" reassurance in its place. Also
finalize the ledger: ASK-0004 (botsite DATABASE_URL) and ASK-0002 (owner
Discord login) are both satisfied and their rows are marked
satisfied-with-evidence.

## Provenance

Owner set `DATABASE_URL` + the Discord OAuth vars in his Railway hub session
2026-07-19; the durable `/submit` write was verified live (a real POST
persisted a Postgres row). The coordinator asked to finalize both ledger rows
and to gate the stale stub copy now that the intake is live.

## Plan

- `botsite/app.py` — pass `intake_live` (from `submissions_store.is_live()`)
  into the GET `/submit` form context.
- `botsite/templates/submit.html` — wrap the stale badge, hint, and "Heads up"
  provisioning block in `{% if not intake_live %}`; add a subtle
  "reviewed before publishing" note when the intake IS live. Form fields
  always render.
- `botsite/tests/test_submit.py` — two tests: stub copy hidden when live,
  shown when not live.
- `docs/owner/OWNER-ACTIONS.md` — finalize ASK-0004 + ASK-0002 to
  satisfied-with-evidence; add a new ⚑ row for the unset botsite
  `SITE_PASSWORD` (blocks the `/submit` moderation queue).
- `docs/CAPABILITIES.md` — append the 2026-07-19 note that the env vars were
  set by the OWNER manually; agent-side Railway mutations stayed
  classifier-denied.

## Verify

`python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q` and
`python3 bootstrap.py check --strict`.

## 💡 Session idea

**Assert `intake_live`-gated copy in a render snapshot pin.** The stub-vs-live
divergence on `/submit` is exactly the kind of stale-copy drift that a single
render-snapshot test (badge string present iff `not is_live()`) locks down
across every future template edit. Worth having because the "Stub — not wired"
badge outlived the intake going live by a full day precisely because nothing
pinned the copy to the store state. Deduped against `docs/ideas/backlog.md` +
the queue-state NEXT list: <pending — captured on card>.

## ⟲ Previous-session review

`.sessions/2026-07-18-botsite-durable-submissions.md` (ORDER 034) shipped the
durable store end-to-end and correctly flagged the one owner-gated
provisioning paste rather than faking it — but it left the user-facing `/submit`
stub copy hardcoded, so the form kept advertising "not wired" after the owner's
paste made it live. This session closes that gap and finalizes the two ledger
rows the paste satisfied.
