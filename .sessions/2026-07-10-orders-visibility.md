# 2026-07-10 — /orders: per-repo inbox ORDER visibility with outstanding computation (backlog promotion)

> **Status:** `complete` — PR #77 (`claude/orders-visibility`),
> squash-merge on `quality` green. (Flipped after the PR existed.)

- **📊 Model:** Claude Fable 5 · worker · routine-fired build slice (continuous mode, slice 6 — 22:14Z nudge)

**What this session was about:** the 22:14Z send_later continuation. Inbox at
HEAD has no order past 009; work-ladder rung 3 — promoted the backlog's
**per-repo inbox ORDER visibility** capture (ORDER 009's audit named per-repo
`control/inbox.md` ORDER texts as browsable nowhere; the bullet notes it
"pairs naturally with the heartbeat enrichment's outstanding-orders
computation"). Coordinator concurred it is the higher-value pick over the
own-heartbeat self-check. Build: an `/orders` page — every fleet repo's
inbox ORDER blocks parsed and cross-referenced against that repo's own
heartbeat `done=`/`claimed-by:` lines, so each order renders with an honest
open / claimed / done badge and "what's outstanding fleet-wide" becomes one
glance.

## What was done

- **`app/orders.py`** (new): `parse_inbox` reads `## ORDER <nnn> · <ISO> ·
  status:` blocks (priority/do/why/done-when fields, wrapped lines joined,
  non-ORDER headings close a block, bounded 50/repo); `classify_order`
  checks each id against every cohabiting lane's parsed status line —
  REUSING the D-0028 `fleet.parse_orders` (one parser for the format, no
  drift): **done** (lane named) beats **claimed** beats **open**; a repo
  with orders but zero readable statuses is **unknown**, never guessed.
  Repo set = `fleet.resolve_lanes()` deduped per repo (shared-repo
  cohabitations: ONE inbox, every lane's `done=` counts). Attention-first
  sort; fleet-wide summary.
- **Caught defect while testing** (the boundary test found it): the first
  claimed-match implementation regex-scanned the claim's free text and
  matched ids inside the ISO timestamp (`00` in `21:00Z`); fixed to match
  numerically against the claim's id spec (first token, `+`/`,` split)
  only.
- **`app/templates/orders.html`** + routes (`/orders`, `/orders.json` with
  rendered body HTML dropped) + nav link after `/reviews`; long `do:` texts
  truncate at 280 chars with the full order block in a `<details>` fold
  (sanitized `journal.render_markdown`); honest no-inbox absences, fetch
  banners, no-status "unknown" banner.
- **Live-data verification pre-merge** (app's own runtime fetch path):
  `lane_source: manifest`, 13 repos, 10 inboxes, **48 done / 5 open**
  cross-referenced correctly — superbot-next 3 open, superbot-games 2 open,
  substrate-kit 11/11 done, websites 9/9 done; the two container-proxy-
  walled repos rendered as honest error banners (a wall the Railway runtime
  does not have).
- **Docs:** D-0032 in the ledger; `docs/site.md` § 3f + Routes rows;
  backlog bullet `captured` → Built.
- **`tests/test_orders.py`** (+7, suites 173 → 180): block/field/wrap
  parsing; empty-inbox honesty; the done/claimed/open/unknown lattice incl.
  the timestamp false-positive boundary case; overview cross-reference +
  sort + absence handling; unknown-when-status-unreadable; route + JSON
  smoke; offline degradation.

## Close-out (auto-drafted 2026-07-10 — edit, don't author)

<!-- substrate:auto-draft -->

**Evidence (auto-collected — verify, then keep or correct):**

- files touched: `app/orders.py` (new), `app/templates/orders.html` (new),
  `app/main.py`, `app/templates/base.html`, `tests/test_orders.py` (new),
  `docs/site.md`, `docs/decisions.md` (D-0032), `docs/ideas/backlog.md`,
  this card.
- git: branch `claude/orders-visibility`, HEAD d81d186da at draft time
  (this flip commit supersedes it).
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests -q` —
  **180 passed** (+7); `python3 bootstrap.py check --strict` — **all checks
  passed** with this card complete (kit v1.7.1).

**Judgment (the half only the session knows — resolve every slot):**

- Decisions made: D-0032 (home: `docs/site.md` §§ 3f/Routes + the ledger);
  claimed-match must be numeric against the claim's id spec only (the
  ISO-timestamp false-positive lesson).
- Next session should know: the fleet-info surfacing wave is now fully
  built out (fleet / queue / environments / projects / reviews / orders);
  remaining backlog top picks are the own-heartbeat parse self-check
  (small) and the /fleet manifest-badge template tweak; the manager still
  owes review-queue rows for websites#67/#72/#75 — and #77 (this PR, ~300
  runtime lines) now also qualifies under the 50-line rule.

⚑ Self-initiated: no — backlog promotion (rung 3), capture sourced from the
ORDER 009 audit; coordinator concurred on the pick.

## 💡 Session idea

**"Stalled claim" aging on `/orders`** — badge a claimed order whose
`claimed-by:` timestamp is older than ~24h with `claim stale?` (the claim
ritual's own expiry rule: a claim with no visible build activity after ~24h
may be treated as abandoned and re-claimed). Worth having because `/orders`
now makes claims visible but not their AGE — the exact failure the ritual's
expiry clause exists for (a dead lane deadlocking an order) still requires
reading timestamps by hand; the claim line already carries an ISO stamp, so
this is pure presentation over parsed data. Deduped against
`docs/ideas/backlog.md` + queue-state NEXT: nothing covers claim aging.
Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

Slice 5 (same wake, PR #75) got the live-data discipline right — parsing the
REAL upstream ledger before merge caught the actual row/link shapes, and its
review-law surfacing (rows owed for #67/#72/#75) turned a silent compliance
gap into a manager ask; what it missed: it left `/orders`-class data (the
claim's ISO timestamp) unused in its own D-0028 parse — `parse_orders`
captures the claim verbatim but extracts no timestamp, which this slice's 💡
now needs; when parsing a structured line, extract ALL its documented parts
the first time, not just the ones the current page renders.
