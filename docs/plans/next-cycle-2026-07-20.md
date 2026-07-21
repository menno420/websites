# Next cycle — 2026-07-20 (product frontier)

> Superseded by docs/PROJECT-CLOSEOUT.md (final close, 2026-07-21) — see its Continuation section.

> **Status:** `plan`
>
> Successor to docs/plans/next-cycle-2026-07-19.md (executed: hardening/hygiene
> drained through #460/#461, strict gate clean, four-suite pytest 2132). The seat
> is out of hygiene work; this cycle turns to the PRODUCT frontier. Slices below
> are owner-independent and agent-landable unless routed out.

## Context (verified 2026-07-20)

- Main at #461 (`6971249`), ≥ #460; four-suite pytest = 2132 passing.
- Hardening backlog drained; no open ORDER at HEAD; heartbeat current.
- Product mining across five angles (arcade, review editions, owner console,
  botsite submissions, cross-site nav) — evidence in the session card.

## Honest frontier read

The ungated product frontier is real but not deep. The standout is the review
edition channel, which is genuinely unbuilt (not owner-gated) — a real revival.
The rest is incremental polish (nav strip, owner panel), data growth (arcade
catalog), and one small feature (submitter status). None is blocked on the
owner; the heavier restyle and anything touching money/Discord/domains is
routed out.

## Executable slices (ranked best value-per-effort)

### S1 — Review edition auto-drafter · value: high · size: M · gate: none
- **What:** `review/gen_edition.py` that drafts the next edition markdown from the
  already-baked committed mirrors (stats/fleet/releases/snapshot json), following
  the reproducible-from-source doctrine editions.py documents.
- **Why now:** editions are hand-authored; only edition-001 exists (2026-07-11),
  so a "continuous review channel" has been silent 10 days. Drafting is neither
  automated nor owner-gated — it simply isn't built.
- **Test shape:** unit — generator produces valid front-matter + body from a
  fixture mirror set; editions.py parses the output; idempotent slug/date.
- **Follow-on (separate slice):** wire into review-bake.yml (hub venue — touches
  .github/workflows/**) so editions auto-draft+land on the BAKE_PAT path.

### S2 — Arcade catalog growth · value: med-high · size: S/game · gate: none
- **What:** add the fleet's other shipped/staged games to botsite/data/arcade.json
  with honest availability + blocker/ask_id where owner-gated.
- **Why now:** catalog is only 3 games; the blocker machinery already surfaces any
  owner gate honestly, so growth is safe + owner-independent.
- **Test shape:** schema validation + reachability-probe test per new entry.

### S3 — Cross-service fleet nav strip · value: med · size: S · gate: none
- **What:** a shared footer link row (control-plane · botsite · dashboard ·
  review) added to each base.html with live Railway URLs.
- **Why now:** no service links to any sibling today; a visitor can't move between
  the four sites.
- **Test shape:** each base.html renders the four links; reachability test.
- **Caveat:** hardcodes *.up.railway.app until the deferred custom-domain call.

### S4 — Owner "/owner" inline actions panel · value: med · size: S · gate: none
- **What:** a top-of-home "Your N open actions" panel on /owner, reusing the
  briefing.asks data already fetched in owner_board (no new fetch).
- **Why now:** the aggregation exists at /owner/queue but the home leads with the
  readiness board; the "what needs me now" list needs one click.
- **Test shape:** /owner renders the panel with the pending-ask count; empty state.

### S5 — Submitter status lookup · value: med · size: M · gate: none
- **What:** issue an opaque ref token on /submit, show it on the thank-you screen,
  add read-only GET /submit/status/{ref} → {status}.
- **Why now:** submitters get no reference and no way to check status.
- **Test shape:** submit returns a ref; status route returns the stored status;
  honest not-found fallback.
- **Note:** dual SQLite⇄Postgres schema add via _db.py.

### S6 — Arcade richer detail · value: med · size: M · gate: partial
- **What:** optional screenshots/controls/changelog in arcade_detail.html behind
  fail-soft guards (mirrors the optional-blocker pattern).
- **Why now:** detail pages are thin.
- **Gate:** some screenshot originals may be owner-held — scope to capturable.

## Routed out (not owner-independent)

- **Control-plane restyle onto sb- design system** — size L, high CI risk
  (CLARITY-BAR walks ~123 routes). Flag, don't self-initiate.
- **review-bake.yml wiring for S1** — .github/workflows/** diff → hub venue.
- **Owner-gated asks** (unchanged): PayPal Payouts (ASK-0005), Discord vars
  (ASK-0006/0017), Gumroad publish (ASK-0012), custom domains, site consolidation
  (gated on explicit go).

## This session

Landing S1 (edition auto-drafter, generator only — the workflow wiring is the
routed-out hub follow-on). Queue top after this: S2, S3.
