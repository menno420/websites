# Next-cycle plan — 2026-07-18

> Superseded by docs/PROJECT-CLOSEOUT.md (final close, 2026-07-21) — see its Continuation section.

> **Status:** `plan` — planning pass at HEAD `07b4bb9` (#421). Re-groom when new owner intent or hub capacity lands.

## Context

The curated seat backlog (`../NEXT-TASKS.md`) is essentially drained: 9 of ~11 ranked
items already shipped (verified against the tree). The remaining executable frontier is
narrow — one real feature slice plus doc hygiene. Substantive new growth now depends on
owner product decisions (15 asks in `owner/OWNER-ACTIONS.md`) or hub-venue infra (bake
wiring, cron rebind). This doc grooms what the seat can still build and routes the rest.

## Executable queue (seat · no owner gate · no workflow edit)

Ordered by value-per-effort.

### 1. B6 — dashboard `/env` config-drift flags · M · code+test
- **What:** On dashboard `/env`, cross-check env vars against a committed manifest and
  flag referenced-but-unset and set-but-unused vars.
- **Why now:** The single un-built curated *feature*. `dashboard/app.py` `env_page`
  currently renders only `data_source.env_usage(data)` with no manifest cross-check —
  silent config drift goes unsurfaced on the one page meant to show it.
- **Test shape:** unit test over the new drift classifier (referenced-but-unset,
  set-but-unused, clean) + a route test asserting the flags render on `/env`.
- **Gate:** none. `/env` is a read-only GET — no CSRF surface.

### 2. Prune `docs/NEXT-TASKS.md` · S · docs
- **What:** Move the ~9 shipped items (C1, C14, C15, A2, A4, B1, R6, C9, C11) out of the
  open ranked list into a verified-shipped section.
- **Why now:** The file actively misleads every future session into re-proposing shipped
  work — a real recurring cost. *(Done in this planning PR.)*

### 3. Refresh `docs/current-state.md` header · S · docs
- **What:** Bump the stale SHA (`#383` → `#421`) and reflect #416/#418/#419/#420/#421.
- **Why now:** Boot doc lagging main misleads orientation. *(Done in this planning PR.)*

### 4. review `/questions` empty-state polish · S · verify-first
- **What:** Confirm `/questions` renders a graceful "no questions answered yet" empty
  state (`questions.json` is intentionally `[]`); add one if missing.
- **Why now:** Honest-empty is a deliberate design choice, but a bare empty list reads as
  broken. Small clarity win consistent with the honest-empty philosophy.
- **Test shape:** route test asserting the empty-state copy renders when the log is empty.
- **Gate:** none. Verify the page first — may already be handled.

### 5. Drift-banner parity sweep · S/M · verify-first
- **What:** The release-drift banner shipped at review (ORDER 033). Check whether the
  console (`app/`) and dashboard surface a comparable drift indicator; add parity where a
  cheap committed-data signal already exists.
- **Why now:** Cross-service consistency; the drift signal is most useful where owners
  actually look (the console).
- **Test shape:** route test for the new indicator.
- **Gate:** verify the signal is available from committed data (no walled REST).

## Routed out (not seat-buildable this cycle)

One line each — full detail lives in `../owner/OWNER-ACTIONS.md`; not duplicated here.

- **15 owner asks** (ASK-0001…0016 less 0007) — Discord OAuth, control token, DBs,
  PayPal, releases, Pages source, Gumroad / illustration / proofread gates. →
  `owner/OWNER-ACTIONS.md`.
- **ORDER 021** — owner environments hub (needs the Q-0004 Discord-OAuth decision). →
  `../../control/inbox.md`.
- **Hub venue:** wire `review/gen_releases.py` into `review-bake.yml` (daily
  `releases.json` rebake); rebind the failsafe cron to a live session. Both are
  `.github/workflows/**` / trigger changes. → hub.
- **Site-consolidation retirement** — destructive; awaits explicit owner "go". →
  `site-consolidation-cutover.md`.

## Honesty note

The seat's execution backlog is genuinely at hygiene depth. After B6, remaining seat value
is doc/clarity polish (items 4–5, verify-first). Substantive new work now requires owner
product intent or hub infra capacity. This queue is not padded past what is real.
