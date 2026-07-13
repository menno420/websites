# 2026-07-13 — tests: suite-level ambient-token pin in tests/conftest.py (ORDER 027 item 5)

> **Status:** `in-progress`

- **📊 Model:** Claude 5 family · worker · ORDER-027-item-5 slice (test infra)

**What this session is about:** ORDER 027 item 5 (`control/inbox.md` —
"Suite-level token pin in `tests/conftest.py` — autouse sentinel for
`GITHUB_TOKEN`/`RAILWAY_TOKEN`, kills the unpinned-reason-assertion flake
class", `docs/ideas/backlog.md:33@31b5d00`). The protection against the
both-rungs bug #250 flagged is per-test discipline since PR #251; this
session makes it structural: a new `tests/conftest.py` autouse fixture pins
every control-plane test to the unset token rung so a test's meaning can
never again change with whether the runner exports a token.
