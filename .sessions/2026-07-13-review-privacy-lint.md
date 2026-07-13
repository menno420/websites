# 2026-07-13 — review privacy lint: accent-aware private-token gate over all routes + data

> **Status:** `complete` — PR #233, branch `claude/review-privacy-lint`;
> the site-wide privacy lint lands green with an empty allowlist (no real
> leak found); lands via the auto-merge enabler on green.

- **📊 Model:** Fable 5 · worker · feature-slice (test suite)

**What this session was about:** backlog promotion rung under ORDER 022
item 2 ("keep executing the existing plan to completion … the Anthropic
review site") — executes the captured bullet "Site-wide privacy lint for
the review service" (`docs/ideas/backlog.md`, captured 2026-07-12 by the
ORDER 017 D private-lane-filter session). The regression tests pinned
only `/`, `/fleet`, `/fleet.json` and the committed mirrors; this session
builds the promised single suite that walks EVERY GET route in
`review/app.py` plus every committed `review/data/**` file and asserts no
private-lane token appears — accent-aware (`pok[eé]mon…`), because the
original escapees were an accented "Pokémon" that plain `grep -i pokemon`
missed. Zero network, PR #225-shaped: explicit per-entry-justified
allowlist, stale-allowlist rejection, headline failures naming route +
token.

## What was done

- **`review/tests/test_privacy_lint.py`** (5 tests, zero network): walks
  every GET `APIRoute` via `fastapi.testclient.TestClient` — parameterized
  routes expanded to every concrete variant from the committed data (all
  17 repo-backed `/fleet/{repo}` pages + the private lane's own 404 probe
  + an unknown-repo 404; every `/reviews/{slug}` edition + a 404 probe;
  all `/static/**` assets via the mount expander; the catch-all 404 page —
  30 concrete URLs today) — plus every committed `review/data/**` file
  (9 files) scanned as raw text.
- **Accent-aware matching** per the bullet's `pok[eé]mon…` spec: NFKD
  decomposition + combining-mark strip + casefold on BOTH haystack and
  tokens, with an index map back into the original text so failure
  headlines carry the real un-normalized snippet. Token list = the bullet
  stem `"pokemon"` + `fleetdata.PRIVATE_LANES` (ORDER 017 D source of
  truth), so declaring a new private lane extends the lint automatically.
- **PR #225 shape**: explicit `ALLOWLIST` of (location, token, reason)
  triples — currently EMPTY, no legitimate occurrence exists today; a
  non-allowlisted hit fails naming route/file + token + snippet; a stale
  entry (matching nothing) fails too; and a completeness guard fails any
  future parameterized route or mount lacking a registered expansion, so
  new surfaces cannot dodge the walk (expander maps are themselves checked
  for stale entries both ways).
- **Proven red, not assumed**: planted an accented token in a data file
  and on the rendered `/process` page (each failed with the naming
  headline), and a bogus allowlist entry (failed as stale); all plants
  reverted. **No real leak found** on main's current tree — the suite
  lands green with the empty allowlist.
- Backlog bullet flipped captured → built (PR #233 notation matching
  neighbors).
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 937 passed (+5 new), 1 warning;
  `python3 bootstrap.py check --strict` — green apart from this card's own
  designed born-red HOLD and the pre-existing `owner-action-fields`
  advisory on control/status.md (never exit-affecting, not owned here).

**Decisions made:** tokens are derived (`{"pokemon"} | PRIVATE_LANES`),
never duplicated by hand, so the lint and the runtime filter share one
source of truth; the walk requests the private lane's own detail URL and
lints its 404 body (a leak on an error page is still a leak); static
assets and the Atom feed are walked like any page because "site-wide"
means every byte the service serves; snippet extraction maps normalized
match positions back to original-text offsets so failures show the real
accented text.

⚑ Self-initiated: no — ORDER 022 item 2 follow-through, executing the
committed backlog bullet.

## 💡 Session idea

**Privacy-boundary decision + lint for the OTHER three services** — the
new lint covers `review/` only, but the private lane's name appears
verbatim in `app/config.py` and `app/reviews.py` and the control-plane
serves without auth; either ORDER 017 D is deliberately review-scoped
(document that boundary) or the proven walker pattern should be stamped
onto app/, botsite/ and dashboard/. Worth having because the one leak
class actually shipped (2026-07-12) escaped precisely on the surfaces
nobody had decided about. Deduped against `docs/ideas/backlog.md` + the
queue-state NEXT list: the built review bullet covers review/ only; the
dashboard denylist test covers control-API tokens, not the private lane.
Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The inventory-consistency-pin session (#225) did well — its allowlist +
stale-rejection shape ported here almost unchanged (proof the pattern is
a house style now), and its "verified red on the pre-fix drift" habit set
the bar this session met with planted leaks in both directions. One miss
worth noting: its card's close-out claimed the cross-check passed but the
pin only guards the two ledgers it names — the third-inventory gap it
found became a follow-up bullet instead of a guard, which is exactly the
scope-fence honesty this session copied (review-only lint, cross-service
boundary captured as an idea, not silently annexed).
