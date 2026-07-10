# 2026-07-10 — substrate-kit upgrade v1.6.0 → v1.7.0 (§4.3 release flow)

> **Status:** `in-progress`

- **📊 Model:** claude-fable-5 (coordinator-tasked distribution-wave worker)

**What this session is about:** take the vendored `bootstrap.py` from kit
v1.6.0 (D-0026, PR #45) to the released **v1.7.0** through the kit's own §4.3
consumer upgrade flow: download the pinned release assets (sha256
`00f4f4cd…3238`), run `bootstrap.py.new upgrade`, verify
`python3 bootstrap.py check --strict` + the full pytest suite, move the
D-0019 exact-pin test to 1.7.0, ship as one kit-scoped PR.

Scope note (wave directive Q-0261.3): kit-owned files only — `control/` is
untouched by this session; the lane's own next heartbeat records the new
`kit:` line.
