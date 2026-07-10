#!/usr/bin/env bash
# websites — Claude Project ENVIRONMENT setup script.
# Paste into: claude.ai console → websites Project → environment settings →
# "Setup script" field (runs at session provision). Source of truth is THIS
# file in the repo — re-paste after editing it here.
#
# Contract: non-interactive, idempotent, FAIL-SOFT. A setup script that exits
# nonzero can kill the session at provision (the substrate-kit PR #47
# provisioning-death lesson) — so nothing here may abort: warn and continue.
set +e  # never fail the provision; every probe degrades to a warning

REPO_DIR="${REPO_DIR:-$(pwd)}"
warn() { echo "[setup:WARN] $*"; }
note() { echo "[setup] $*"; }

# ── 1. Python ────────────────────────────────────────────────────────────────
# The services target Python 3.12 (Dockerfile: python:3.12-slim; CI quality.yml:
# setup-python 3.12). Any 3.11+ runs the suite fine — warn on drift, don't die.
PYV="$(python3 -V 2>&1)"
note "python3 = ${PYV}"
case "$PYV" in *" 3.12"*) : ;; *) warn "CI runs 3.12; local is ${PYV} — tests usually still pass, but match CI when a red is version-shaped." ;; esac

# ── 2. Dependencies ─────────────────────────────────────────────────────────
# All three services' pinned runtime deps + pytest (the only extra the test
# suites need — they import only fastapi.testclient/pytest/stdlib). Idempotent:
# pip skips already-satisfied pins.
for req in requirements.txt botsite/requirements.txt dashboard/requirements.txt; do
  [ -f "$REPO_DIR/$req" ] || { warn "missing $req (wrong cwd?)"; continue; }
  python3 -m pip install -q -r "$REPO_DIR/$req" || warn "pip install -r $req failed — run it manually before pytest"
done
python3 -m pip install -q pytest || warn "pytest install failed"

# ── 3. Git identity + safety ────────────────────────────────────────────────
# Idempotent: only fill identity if unset (the CCR env usually pre-sets
# Claude <noreply@anthropic.com> in ~/.gitconfig — don't fight it).
git config --global --get user.name  >/dev/null || git config --global user.name  "Claude"
git config --global --get user.email >/dev/null || git config --global user.email "noreply@anthropic.com"
git config --global --add safe.directory "$REPO_DIR" 2>/dev/null || warn "could not set safe.directory"

# ── 4. Capability probes — print the walls so no session guesses ────────────
# (docs/CAPABILITIES.md discovery rule: verified facts, never assumptions.
#  2026-07-10 lesson: a routine-fired session RECORDED a push that never
#  landed — every session now starts with proof instead.)
note "── capability probe ──"

# 4a. Commit signing: CCR envs default commit.gpgsign=true with an SSH signer
# (gpg.ssh.program → /tmp/code-sign → env-runner). If the signer is missing,
# commits fail with "failed to write commit object" — know it NOW, not mid-work.
if [ "$(git config --get commit.gpgsign)" = "true" ]; then
  SIGNER="$(git config --get gpg.ssh.program)"
  if [ -n "$SIGNER" ] && [ -x "$SIGNER" ]; then note "commit signing: ON, signer present ($SIGNER)"
  else warn "commit signing REQUIRED but signer '$SIGNER' missing/not executable — commits may fail; report this wall in the session card, do not silently disable signing"; fi
else note "commit signing: off"
fi

# 4b. Git read + PUSH credential (the wall that stranded the 16:01Z session).
# Dry-run push proves the per-session repo grant without writing anything.
if git -C "$REPO_DIR" ls-remote --heads origin >/dev/null 2>&1; then
  note "git read (ls-remote origin): OK"
  if git -C "$REPO_DIR" push --dry-run origin HEAD:refs/heads/claude/probe-$$ >/dev/null 2>&1; then
    note "git push credential: OK (dry-run accepted)"
  else
    warn "git push credential: ABSENT/blocked — commit locally, record branch+state in the session card and control/status.md, hand landing to a tooled session (docs/project/project-instructions.md § routine-fired protocol)"
  fi
else
  warn "git read: ls-remote origin FAILED — repo may not be granted to this session (the add_repo gate)"
fi

# 4c. GitHub API gate (CCR proxy): 403 'not enabled for this session' is the
# known per-session repo-grant wall — PR-open must then go through MCP tools
# or a later tooled session.
API_CODE="$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 https://api.github.com/rate_limit 2>/dev/null)"
note "api.github.com probe: HTTP ${API_CODE:-none} (403 = proxy repo-grant gate; PR-open needs MCP tooling or a later tooled session)"

note "── setup done (fail-soft: warnings above are walls, not failures) ──"
exit 0
