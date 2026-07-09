# 2026-07-09 — substrate-kit upgrade v1.2.0 → v1.6.0 (§4.3 release flow)

> **Status:** `in-progress`

- **📊 Model:** claude-fable-5 (coordinator-tasked worker session)

**What this session is about:** take the vendored `bootstrap.py` from kit
v1.2.0 (D-0019, PR #31) to the released **v1.6.0** through the kit's own §4.3
consumer upgrade flow — sha256-verified release asset, archive-first,
report-classified, nothing uninvited applied. Deltas inherited: v1.3.0
heartbeat line + adopters registry; v1.4.0 configurable `heartbeat_files`;
v1.5.0 `CAPABILITIES.md` + orientation wiring + session-close capability
nudge; v1.6.0 owner-action six-field checker + order-claim convention.
Post-upgrade: `check --strict` green (fix findings honestly), pinned deps +
full test suites green, `kit_version` test pin updated, `kit:` heartbeat line
set in `control/status.md`.

Also this session (before this card): PING-ACK ORDER 006 landed as
control-only fast-lane PR #44 (P0 latency ping — ack before any other work);
ORDER 005 verified genuinely unexecuted (manager inbox append #42; `/queue`
404 live) and acked, execution left to a session scoped to it.
