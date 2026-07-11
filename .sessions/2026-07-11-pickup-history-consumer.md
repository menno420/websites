# 2026-07-11 — Consumer-first pickup history: parse `pickup:` notes tokens (rung 3, build-and-hold)

> **Status:** `complete` — PR #148, branch `claude/pickup-history-consumer`.
> BUILT UNDER THE #141 MERGE HOLD: READY + green, WAITS UNMERGED
> (held-list position #2, after #147).

- **📊 Model:** claude-fable-5 · worker · routine-fired build slice (continuous mode, slice 34 — 18:54Z nudge) — family from this session's own harness, per ORDER 010.

**What this session was about:** the 18:54Z nudge under the
build-not-merge hold; ritual clean (no new orders; stamp frozen 16:27Z;
#141 open but now mergeable_state=behind — noted for the manager; hold
duration ~2h10m at pass). Designated build-and-hold slice: **the
latency-persistence ask's buildable LOCAL half** — the #135 rollup only
sees currently-standing claims (done orders drop their claimed-by
annotation, taking the latency datum with them — live-verified on ORDER
011); shipping the CONSUMER first means the convention works the moment
the first lane adopts it.

## What was done

- `app/orders.py` — `parse_pickup_history(notes)`: `pickup: <id> <mins>m`
  tokens (comma lists ok) → `{id: mins}`; tolerant — garbage never
  parses, never a guess; later duplicates win (a restated figure
  supersedes). Per-order latency FALLS BACK to the lane-reported figure
  when live stamps yield None (stamp-derived values keep precedence);
  recovered figures feed the fleet rollup automatically.
- NO JSON keys changed — values flow through the existing
  `pickup_latency_mins/_human` fields; no contract pin moves (contract
  suite green untouched).
- `tests/test_orders.py` (+2) — parser formats/tolerance/duplicates; a
  DONE order recovering 19.0 from the notes token and feeding
  `summary.pickup`, open orders honestly None; frozen now=NOW.
- `docs/ideas/backlog.md` — Built entry + fresh 💡 added (dogfood the
  convention as writer #1, below). NOTE: the consumer idea's `captured`
  bullet lives on held #147's branch, not main — its retirement happens
  at landing-time reconciliation (#148 lands after #147; both touch the
  backlog, expect a merge-in then).

## Close-out (auto-drafted 2026-07-11 — edit, don't author)

<!-- substrate:auto-draft -->

**Evidence (regenerated from `git diff origin/main --stat`):**

- code touched (1): `app/orders.py`
- tests touched (1): `tests/test_orders.py` (+2)
- docs touched (1): `docs/ideas/backlog.md` (close-out commit)
- sessions touched (1): `.sessions/2026-07-11-pickup-history-consumer.md`
- git: branch `claude/pickup-history-consumer` (off main, independent of
  #147's files), born-red card first commit `19a6198`, build commit
  `d1b03dd`, this close-out commit flips the gate.
- verify: orders module 15/15; `python3 -m pytest tests/ -q` →
  **199 passed** (197 on main + 2; #147's +3 live only on its own held
  branch); strict gate before push → only the designed born-red HOLD.

**Judgment (the half only the session knows — resolve every slot):**

- Decisions made: no D-entry — a tolerant parser + fallback inside the
  existing domain layer, zero contract change. Precedence decision
  recorded: stamp-derived latency (verifiable from two committed
  timestamps) beats the lane-reported token (single-writer claim); the
  token only fills gaps.
- Next session should know: HELD LIST is [#147, #148] + the pending
  catch-up heartbeat — land in that order on the lift relay (each may
  405 on branch-update; the SECOND will definitely be behind after the
  first lands). The convention now needs its first WRITER (this lane's
  own next done= move can seed it — captured 💡).

## 💡 Session idea

**Dogfood the pickup convention in this lane's own heartbeat** —
captured in `docs/ideas/backlog.md`. Worth having because a convention
with zero writers is a spec, not a protocol: this lane can be writer #1
on its next done= move (ORDER 011's known 19m figure can seed it), and
the first write live-verifies the whole parser path end-to-end.

## ⟲ Previous-session review

Slice 33 (#147 open_work NO-DIFF, held): clean — the live run on the
real repo (7→6 ⚠) was the right evidence for a tool change, and the
optional-parameter design kept every existing caller pinned. The
build-and-hold ceremony itself worked exactly as the manager described:
nothing about the full ceremony actually required a merge until the very
last step, which two earlier idle passes failed to notice — this slice
and #147 are the correction in practice.
