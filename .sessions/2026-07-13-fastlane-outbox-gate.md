# 2026-07-13 — outbox grammar gate on the CI control fast lane

> **Status:** `complete` — PR #314, branch `claude/fastlane-outbox-gate-0713`;
> the control fast lane now runs `tests/test_outbox_grammar_pin.py` on
> control-only diffs touching `control/outbox.md` and
> `tests/test_own_heartbeat.py` on ones touching `control/status.md`
> (the incident-#307 class); diffs touching neither keep the bare fast
> path; lands via the auto-merge enabler on green.

- **📊 Model:** Claude Fable 5 · worker · order-slice

**What this session was about:** ORDER 027 item 7 (`control/inbox.md`,
P1 EAP final-night worklist) — "Outbox grammar gate on the control fast
lane". `quality.yml`'s control fast lane short-circuits GREEN on a
control/**-only diff, so `tests/test_outbox_grammar_pin.py` (PR #289)
never ran on exactly the PRs that write `control/outbox.md`; a typo'd
REPORT heading merged green and only reddened the NEXT non-control PR,
after /owner/briefing had already rendered honest-empty. Same class as
incident PR #307: heartbeat-only PRs skipped
`tests/test_own_heartbeat.py`. Backlog source: "Outbox grammar gate in
the CI control fast lane" (`docs/ideas/backlog.md`).

## What was done

- `.github/workflows/quality.yml` — the `lane` step now also emits a
  `pin_tests` output (exact-match `grep -Fxq` per file, same diff-range
  logic), and a new gate (c) — `Set up Python 3.12 (fast lane — grammar
  pins only)` + `control grammar pins` — runs
  `pip install --quiet pytest httpx` (the pins' only third-party import
  chain, via `app.github`) then `python3 -m pytest $pin_tests -q`, both
  steps gated on `control_only == 'true' && pin_tests != ''` so
  control-only diffs touching neither file keep today's fast path
  byte-for-byte.
- `tests/test_own_heartbeat.py` — trued the docstring's "fast lane skips
  pytest by design / running this file there was rejected" scope note,
  which incident #307 overturned and this gate now contradicts.
- `docs/ideas/backlog.md` — source bullet flipped to `built`
  (PR #314); this session's 💡 captured as a new bullet.
- Proof: lane logic extracted verbatim and run against synthetic
  changed-file lists — (a) outbox-only → outbox pin runs, (b)
  status-only → heartbeat pin runs, (c) inbox-only → both pin steps
  skip, (d) outbox+status → both pins, (e) mixed control+code → full
  lane; both pin files then executed in a minimal venv holding ONLY
  pytest + httpx (what the gate installs): 5 + 5 = 10 passed.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 1345 passed, 1 warning; `python3 bootstrap.py
  check --strict` — green except this card's own designed born-red HOLD
  (flipped by this commit).

⚑ Self-initiated: no — ORDER 027 item 7 (`[improve]`), backlog bullet
"Outbox grammar gate in the CI control fast lane".

## 💡 Session idea

**Fast-lane pin-map drift pin — assert quality.yml's grammar-pin
selection stays aligned with the machine-read control files and real
test paths** — a small pytest that parses the workflow's lane step and
asserts every referenced pin test file exists and every machine-read
control file (`app/briefing.py` OUTBOX_PATH, `app/fleet.py` status
parsing) has a pin entry. Worth having because the new gate is
unexecuted shell inside a workflow file — a renamed test or a third
machine-read control file hollows it out silently, the same merge-lag
class this session just closed. Deduped against `docs/ideas/backlog.md`
+ the queue-state NEXT list: the "Fast-lane control gates" bullet is the
gates themselves, the env-sweep shape-coverage bullet covers the env
scanner, nothing pins the CI pin map. Captured in
`docs/ideas/backlog.md`.

## ⟲ Previous-session review

The venture-vetting-catalog session (PR #248) did well — 22 packets
hand-curated into committed JSON with honest per-title states and a
registry-honesty pin (1/12/2/7 breakdown, every source at a fixed sha);
what it missed: that fixed sha is also its weakness — upstream drift
detection shipped only as its 💡 bullet, so the catalog decays silently
until someone builds it.
