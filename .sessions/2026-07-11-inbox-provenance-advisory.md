# 2026-07-11 — Inbox provenance advisory on /orders (rung 3, last buildable-now)

> **Status:** `complete` — PR #139, branch `claude/inbox-provenance-advisory`.

- **📊 Model:** Claude Fable 5 · worker · routine-fired build slice (continuous mode, slice 31 — 15:44Z nudge) — family from this session's own harness, per ORDER 010.

**What this session was about:** the 15:44Z nudge (the ~16:00Z
fire-rescue window — ritual at 15:45Z found no traces yet; re-checked
before the closing heartbeat). No new orders, so rung 3 with the
designated pick: **inbox relay-order provenance advisory** — the /orders
SURFACE half (the quality.yml gate half stays captured for the kit
lane). The #125/#127 gates made the inbox TRUSTED machine-readable
input, and trusted input attracts spoofing: any green-lane author can
append a well-formed ORDER that reads as manager-issued.

## What was done

- `app/orders.py` — `parse_inbox` captures `provenance:`/`from:` fields
  (added to _FIELD_KEYS); `provenance_unverified(order)` flags orders
  where neither names a recognizable session/coordinator identity
  (cse_/session_/coordinator/manager/URL, case-insensitive) —
  ADVISORY-ONLY: never red, never affects state classification, relays
  stay legal.
- `app/templates/orders.html` — muted "provenance unverified" chip with
  a tooltip spelling out the advisory nature + accepted tokens.
- `tests/test_json_contracts.py` — ORDERS_ORDER pin moved SAME-PR
  (+provenance_unverified).
- `tests/test_orders.py` (+2) — heuristic validated against the repo's
  REAL inbox conventions (ORDER 011's cse_ provenance → verified; ORDER
  010's relay from: line → verified; URL-only → verified; absent or
  free-text → flagged); overview carries the key on every order and the
  flag never changes state classification (asserted).
- `docs/ideas/backlog.md` — provenance bullet moved to Built; fresh 💡
  captured (shared token convention for the gate half, below).

## Close-out (auto-drafted 2026-07-11 — edit, don't author)

<!-- substrate:auto-draft -->

**Evidence (regenerated from `git diff origin/main --stat`):**

- code touched (1): `app/orders.py`
- templates touched (1): `app/templates/orders.html`
- tests touched (2): `tests/test_orders.py` (+2),
  `tests/test_json_contracts.py` (pin moved)
- docs touched (1): `docs/ideas/backlog.md` (close-out commit)
- sessions touched (1): `.sessions/2026-07-11-inbox-provenance-advisory.md`
- git: branch `claude/inbox-provenance-advisory`, born-red card first
  commit `ad37367`, build commit `5ab333d`, this close-out commit flips
  the gate.
- verify: `python3 -m pytest tests/ -q` → **197 passed** (195 + 2);
  orders + contracts modules green together (17); `bootstrap.py check
  --strict` before push → only the designed born-red HOLD (flips with
  this commit, PR #139).

**Judgment (the half only the session knows — resolve every slot):**

- Decisions made: no D-entry — an advisory presentation flag over parsed
  data, pin moved per protocol. Two scoping decisions recorded: (a)
  `from:` accepted alongside `provenance:` because the manager's real
  ORDER 010 relay used it — the heuristic follows observed convention,
  not invented rules; (b) missing provenance flags TRUE (advisory noise
  on pre-convention orders is honest and motivates the convention).
- Next session should know: buildable-now backlog is EMPTY again after
  this slice — remaining: hand-kept-list audit sweep (rung-5 candidate),
  the manager asks (latency persistence, lanes.json, meta.md, token
  convention to the kit lane), cross-service clock (dormant). Rung 5 or
  new orders next.

## 💡 Session idea

**Provenance-token list to the kit lane (gate half)** — captured in
`docs/ideas/backlog.md`. Worth having because the advisory just created
the token convention de facto (cse_/session_/coordinator/manager/URL),
and when the kit lane builds the staged-gate provenance warning it
should adopt or supersede app/orders.py's _PROVENANCE_TOKENS rather than
invent a second heuristic — two half-matching spoof detectors are worse
than one, and conventions fork silently.

## ⟲ Previous-session review

Slice 30 (#137 nav-scan glob + heartbeat #138): clean — and the
mid-heartbeat absorption of sibling #132's merge worked exactly per the
standing decision tree (405 → merge main in → facts updated → re-green →
merge), proving the tree handles the merged case as smoothly as the
open/stale cases. One inherited fact double-checked this slice: the
four-service suite command (281 locally at absorption; 197 app-only
here) — keep both numbers explicit per the slice-19 lesson.
