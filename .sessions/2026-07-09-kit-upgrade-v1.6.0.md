# 2026-07-09 — substrate-kit upgrade v1.2.0 → v1.6.0 (§4.3 release flow)

> **Status:** `complete` — upgrade applied + doctrine merged; shipped as PR #45 (this branch), PING-ACK as fast-lane PR #44 (merged `a447514`).

- **📊 Model:** Claude Fable 5 (coordinator-tasked worker session)

**What this session was about:** take the vendored `bootstrap.py` from kit
v1.2.0 (D-0019, PR #31) to the released **v1.6.0** through the kit's own §4.3
consumer upgrade flow, inheriting the v1.3.0–v1.6.0 convention bands.

## What was done

- **Inbox first (per ritual):** found P0 **ORDER 006** (latency ping) and P1
  **ORDER 005** genuinely unexecuted (PR #42 was the manager's inbox append;
  `/queue` 404 on the live deploy at main head `9ed43cf` while `/version`
  matched HEAD). Landed **PING-ACK ORDER 006** immediately as control-only
  fast-lane **PR #44** (quality green in 6s, MCP squash-merged); ORDER 005
  acked, execution left to a session scoped to it (flagged in status notes —
  next executor should claim it per the new v1.6.0 ritual).
- **§4.3 upgrade:** release assets downloaded, sha256 `787d5617…` verified by
  hand against `release.json` + `bootstrap.py.sha256` BEFORE running;
  `python3 bootstrap.py.new upgrade` → from 1.2.0 → 1.6.0, old dist banked at
  `.substrate/backup/bootstrap-1.2.0.py` (`last-upgrade.json` correct),
  input self-cleaned. Note: the in-flow sha check was skipped because
  `release.json` wasn't copied next to `bootstrap.py.new` — copy it next time
  so the flow self-verifies too.
- **Report classification** (`.substrate/upgrade-report.md`): 13
  consumer-edited (kept) · 5 diverged (kept live; the report's additive
  template deltas hand-merged — capabilities doctrine into
  `CONSTITUTION.md` / `docs/collaboration-model.md` /
  `docs/AGENT_ORIENTATION.md`; multi-lane heartbeats + claim-FIRST ritual +
  `kit:` line + OWNER-ACTION format into `control/README.md`;
  `control/status.md` gained the `kit:` line in its close-out overwrite) ·
  1 template-improved applied (`.claude/CLAUDE.md` from staging, fully
  rendered, zero `${...}`) · 1 missing replanted (`docs/CAPABILITIES.md`).
- **CAPABILITIES.md seeded honestly** with this repo's verified findings
  (release-asset HTTPS downloads work; branch push + MCP create/merge work
  here; `/version`-vs-HEAD live verification; control-plane GITHUB_TOKEN
  degraded-cells wall) and wired into the orientation reading order.
- **check --strict**: before fixes — 1 enforced finding (CAPABILITIES.md
  orphan) + the new owner-action advisory on `control/status.md` + the
  intended born-red card hold. After — only the born-red hold (cleared by
  this flip). The ⚑ asks were six-field-reformatted: two genuinely
  actionable OWNER-ACTION blocks (submissions Postgres; durable PAT) with
  real VERIFIED-NEEDED walls; the five decision forks stay parked in
  `docs/owner/OWNER-ACTIONS.md` (fewer-clearer-asks).
- **Pins + tests:** `kit_version` → 1.6.0 (config, recorded by the upgrade)
  and the D-0019 exact-pin test moved to 1.6.0
  (`tests/test_born_red_session_gate.py`); pinned deps installed; full suite
  **125 passed**; ambient-Railway-ID guard OK. `bootstrap.py --version` →
  `substrate-kit 1.6.0`.
- **Ledger:** [D-0026] appended to `docs/decisions.md`;
  `docs/current-state.md` Recently-shipped updated; status heartbeat now
  carries `kit: v1.6.0 · check: green · engaged: yes`.

## Kit friction (relayed upstream via the coordinator)

- `upgrade` prints `replaced: bootstrap.py (v1.2.0 -> v1.6.0; old copy
  archived)` followed by `archived: .substrate/backup/bootstrap-1.6.0.py` —
  that file is the NEW dist banked alongside; the OLD dist's backup
  (`bootstrap-1.2.0.py`, per `last-upgrade.json`) is what rollback uses.
  Metadata correct, log line misleading.
- The in-flow sha verification only engages when `release.json` sits next to
  `bootstrap.py.new`; the upgrade-steps in `release.json` itself don't say to
  download `release.json` too. One line in the checklist would close it.

## 💡 Session idea

`/fleet` already parses each lane's `kit:` status line (D-0021) — add a
**kit-version rollup** to the fleet summary header (e.g. `kit: 4×v1.6.0,
2×v1.2.0, 3×none`) plus a per-card badge, so the substrate coordinator and
the owner can see kit-adoption drift across the whole fleet at a glance
instead of opening ten status files; it's pure presentation over an
already-parsed field (zero new fetch).

## ⟲ Previous-session review

The activity-atom-feed session (#41, D-0025) was a model self-directed
increment: one serializer over an existing cached list, honest degradation,
live-verified post-deploy. What it *couldn't* do — and what this session's
ORDER 006 ping (~1.5h dispatch→discovery) measured — is notice orders that
arrive between sessions: its heartbeat truthfully said "no new order" and two
orders landed within the hour. Concrete system improvement: badge lanes on
`/fleet` whose `control/inbox.md` last-commit is newer than their status
`updated:` timestamp ("unseen orders?") — the data (last-commit age) is
already fetched per repo, so the manager could spot dark lanes with pending
orders from the board instead of waiting for the next wake.
