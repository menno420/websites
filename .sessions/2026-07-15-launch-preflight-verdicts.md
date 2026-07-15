# 2026-07-15 — Launch preflight verdicts: auto-verified owner asks

> **Status:** `in-progress`

- **📊 Model:** Claude Fable · medium · feature build (askverify domain module + owner console verdict chips)

**What this session is about:** the mission phrase "auto-verified
owner-actions", implemented as read-only launch-preflight verdicts. A new
domain module `app/askverify.py` holds a probe REGISTRY keyed by stable
keyword signatures matched against the parsed ⚑ OWNER-ACTION asks (the
same `owner_queue.parse_owner_actions` parse /queue and the briefing use).
Each matched ask gets a live, side-effect-free probe (GETs and the existing
read-only Railway names query only — never a write, never a value fetched)
and renders a verdict chip on the GATED owner console surfaces:
`/owner/briefing` asks section, `/owner/queue` cards, and a one-line
rollup chip on the `/owner` board ("N of M asks machine-verified").

Verdict ladder (honest-unknown beats inferred-done, everywhere):
`done-detected` (positive probe; wording carries "ledger update pending") /
`still-open` / `not machine-checkable — <reason>` / `unknown — <probe
error>`. Unmatched or ambiguously-matched asks stay honestly unverified —
no fuzzy-match tuning. The public `/queue` stays byte-identical (pinned by
test). Zero new POST routes.

⚑ Self-initiated: no — dispatched under the owner's live work grant
(accept-edits session mode), coordinator-approved mission slice.

## Close-out

**Evidence:**

- [[fill: files touched + verify lines at the flip]]

**Judgment:**

- [[fill: decisions + baton at the flip]]

## 💡 Session idea

[[fill: genuine deduped idea at the flip]]

## ⟲ Previous-session review

[[fill: review of the previous 2026-07-15 card at the flip]]
