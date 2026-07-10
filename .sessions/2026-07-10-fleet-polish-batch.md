# 2026-07-10 — Fleet polish batch: stalled-claim aging on /orders + /queue.json + kit rollup on /fleet

> **Status:** `complete` — PR #81 (`claude/fleet-polish-batch`),
> squash-merge on `quality` green. (Flipped after the PR existed.)

- **📊 Model:** claude-fable-5 · worker · routine-fired build slice (continuous mode, slice 8 — 23:12Z nudge)

**What this session was about:** the 23:12Z send_later continuation. Inbox at
HEAD has no order past 009; latest heartbeat is this session's own (no
sibling active). Work-ladder rung 3 — the coordinator-blessed bundle of
three small backlog captures, all presentation/parse over ALREADY-FETCHED
data (zero new fetches): (a) **stalled-claim aging on `/orders`**;
(b) **`/queue.json`**; (c) **kit-version rollup on `/fleet`**.

## What was done

- **(a) `app/fleet.py` + `app/orders.py` + `app/config.py`**:
  `parse_orders` extracts the claim's ISO timestamp as `claimed_at` (never
  guessed — unparseable → None); `classify_order` gains `now` + claim aging:
  past `CLAIM_STALE_HOURS` (24h default, env-tunable — the claim ritual's
  own expiry rule) a claimed order badges `claim stale? (<age>)`; a claim
  with no parseable stamp ages honestly as unknown; `/orders` summary rolls
  up `stale_claims`, templates badge per-order and in the header.
- **(b) `app/main.py`**: `/queue.json` — same `owner_queue.overview()` dict
  minus `fleet_manager.body_html` (the /fleet.json precedent); gives the
  manager the file-an-ask → poll → confirm round-trip.
- **(c) `app/fleet.py`**: `kit_version` (token out of a `kit:` line) +
  `kit_rollup` (version → lane count over READABLE heartbeats only;
  unversioned readable heartbeats bucket as `none`, always last);
  `summary.kit_versions` + a "kit adoption: N×vX.Y.Z · M×none" header line
  on `/fleet`.
- **Live-smoked against the real fleet pre-merge**: kit rollup
  `4×v1.7.1 · 1×v1.7.0 · 1×v1.6.0 · 5×none`; orders summary
  `stale_claims: 0` (no active claims fleet-wide at the moment — the badge
  waits for its first real stall).
- **Docs:** D-0033 in the ledger; `docs/site.md` §§ 3a (claimed_at + kit
  rollup) / 3f (claim aging) / Routes (`/queue.json` row); backlog: the
  three bullets → one Built entry.
- **`tests/test_fleet_polish.py`** (+9, suites 185 → 194): claim-stamp
  extraction incl. honest None; stale / fresh / unparseable-stamp aging;
  /orders page + JSON badge + roll-up; /queue.json round-trip surfacing a
  filed six-field ask (found the item shape puts WHAT at top level — test
  fixed against the real `_make_item` contract); kit-token extraction;
  rollup bucketing (missing/errored lanes excluded); /fleet header render.

## Close-out (auto-drafted 2026-07-10 — edit, don't author)

<!-- substrate:auto-draft -->

**Evidence (auto-collected — verify, then keep or correct):**

- files touched: `app/fleet.py`, `app/orders.py`, `app/config.py`
  (`CLAIM_STALE_HOURS`), `app/main.py` (`/queue.json`),
  `app/templates/{orders,fleet}.html`, `tests/test_fleet_polish.py` (new),
  `docs/site.md`, `docs/decisions.md` (D-0033), `docs/ideas/backlog.md`,
  this card. (The auto-draft had no session-start anchor — list verified
  against `git diff origin/main --stat` by hand.)
- git: branch `claude/fleet-polish-batch`, HEAD 94588ec77 at draft time
  (this flip commit supersedes it).
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests -q` —
  **194 passed**; `python3 bootstrap.py check --strict` — **all checks
  passed** with this card complete (kit v1.7.1).

**Judgment (the half only the session knows — resolve every slot):**

- Decisions made: D-0033 (one batch decision; home: `docs/site.md`
  §§ 3a/3f/Routes + the ledger); `CLAIM_STALE_HOURS` mirrors the ritual's
  ~24h expiry wording rather than inventing a new threshold.
- Next session should know: backlog top remaining picks — `?repo=` filter
  on the activity views, PR #9 `claude/rework-dashboard` salvage re-check,
  `scripts/wait-deploy.py`, ladder-rung telemetry, review-row auto-check,
  open-PR-awareness script. The manager still owes review-queue rows for
  websites #67/#72/#75/#77 (and now #81, ~150 runtime lines — borderline;
  flagged, the manager judges).

⚑ Self-initiated: no — backlog promotion (rung 3), coordinator-suggested
bundle.

## 💡 Session idea

**`/fleet.json` shape contract test** — one test asserting the exact key
set of a `/fleet.json` lane + summary (orders_info/routine_info/
landing_info/kit_versions and their inner keys). Worth having because three
sessions in one day extended that payload (D-0028 and its reuses through
today's slices) and the manager + /queue + /orders now all consume it — an
accidental key rename would break machine consumers silently today, while a
shape test turns it into a named red with the diff in the assertion message
(the console.json pinned-contract lesson, applied to our own JSON). Deduped
against `docs/ideas/backlog.md` + queue-state NEXT: nothing covers own-JSON
shape stability. Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

Slice 7 (same wake, PR #79) made the right call twice — fact-checking pick
(b) before building (retire-not-rebuild) and documenting the fast-lane
enforcement gap honestly instead of overclaiming; what it missed: nothing
material — the smallest slice of the wake was also its cleanest; the one
improvable habit is that its retirement verification cited template line
numbers that later edits will shift (cite stable anchors — test names,
section headers — not line numbers, which this card now does).
