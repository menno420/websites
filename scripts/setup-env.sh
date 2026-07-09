#!/usr/bin/env bash
# setup-env.sh — defensive environment setup for the menno420/websites gen-2 lane.
#
# Written 2026-07-09 as part of the gen-1 wind-down succession pack.
# Intended home: the fresh Project's environment config (SessionStart /
# environment-setup hook), run once per fresh container before any work.
#
# CONTRACT:
#   * ALWAYS exits 0 — a broken step is PRINTED, never fatal. The gen-2 session
#     reads the summary and decides; a red setup hook must not brick the session.
#   * Assumes NOTHING about repo shape: every path is checked before use, every
#     requirements file that actually exists is installed individually and
#     non-fatally.
#   * Known gen-1 facts baked in:
#       - fresh containers lack pytest ("/usr/local/bin/python3: No module named pytest")
#       - services need python-multipart + pytest BEYOND their requirements files
#       - clones may start on a DETACHED HEAD — that is normal, not an error
#   * NEVER prints secret values — env vars are reported by NAME, present/absent only.

# ---- never-fail discipline -------------------------------------------------
set +e
set +u
trap '' ERR

FAILURES=()
INSTALLED_REQS=()
FAILED_REQS=()

# Quiet the "running pip as root" warning (env var form is ignored by old pips,
# so this can never break an install the way an unsupported flag could).
export PIP_ROOT_USER_ACTION=ignore

note() { printf '[setup-env] %s\n' "$*"; }
fail() { printf '[setup-env] FAIL: %s\n' "$*"; FAILURES+=("$*"); }

note "starting ($(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || echo 'date unavailable'))"

# ---- locate a python -------------------------------------------------------
PY=""
for cand in python3 python; do
  if command -v "$cand" >/dev/null 2>&1; then PY="$cand"; break; fi
done
if [ -z "$PY" ]; then
  fail "no python3/python on PATH — cannot install anything"
else
  note "python: $("$PY" --version 2>&1)"
fi

pip_ok=0
if [ -n "$PY" ] && "$PY" -m pip --version >/dev/null 2>&1; then
  pip_ok=1
else
  [ -n "$PY" ] && fail "$PY -m pip not available — all installs will be skipped"
fi

# ---- locate the repo (arg > env > default > cwd) ---------------------------
REPO_DIR=""
for cand in "${1:-}" "${WEBSITES_REPO_DIR:-}" /home/user/websites "$PWD"; do
  [ -n "$cand" ] || continue
  if [ -d "$cand" ] && { [ -f "$cand/bootstrap.py" ] || [ -f "$cand/requirements.txt" ]; }; then
    REPO_DIR="$cand"
    break
  fi
done
if [ -n "$REPO_DIR" ]; then
  note "repo dir: $REPO_DIR"
else
  fail "websites repo not found (tried \$1, \$WEBSITES_REPO_DIR, /home/user/websites, cwd) — repo-relative installs skipped"
fi

# ---- git state: tolerate detached HEAD, never fail on it -------------------
if [ -n "$REPO_DIR" ] && command -v git >/dev/null 2>&1; then
  # fresh clones under a different uid trip the dubious-ownership guard
  git config --global --add safe.directory "$REPO_DIR" >/dev/null 2>&1 || true
  if git -C "$REPO_DIR" rev-parse --git-dir >/dev/null 2>&1; then
    branch="$(git -C "$REPO_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
    sha="$(git -C "$REPO_DIR" rev-parse --short HEAD 2>/dev/null || echo unknown)"
    if [ "$branch" = "HEAD" ]; then
      note "git: DETACHED HEAD at $sha — normal for fresh clones; branch before committing (git switch -c <branch>)"
    else
      note "git: on branch $branch at $sha"
    fi
  else
    note "git: $REPO_DIR is not a git repository (ok for docs-only work)"
  fi
else
  note "git: skipped (no repo dir or no git binary)"
fi

# ---- install every requirements file that actually exists ------------------
# Known layout: root requirements.txt (control-plane, app/) + botsite/ +
# dashboard/ each with their own. The find is the safety net for shape drift.
REQ_FILES=()
if [ -n "$REPO_DIR" ]; then
  while IFS= read -r f; do
    [ -f "$f" ] && REQ_FILES+=("$f")
  done < <(find "$REPO_DIR" -maxdepth 2 -name 'requirements*.txt' -not -path '*/node_modules/*' 2>/dev/null | sort)
fi

if [ "${#REQ_FILES[@]}" -eq 0 ]; then
  note "no requirements*.txt files found — skipping requirements installs"
elif [ "$pip_ok" -ne 1 ]; then
  note "pip unavailable — skipping ${#REQ_FILES[@]} requirements file(s)"
else
  for req in "${REQ_FILES[@]}"; do
    note "installing: $req"
    if "$PY" -m pip install --disable-pip-version-check -q -r "$req"; then
      INSTALLED_REQS+=("$req")
    else
      FAILED_REQS+=("$req")
      fail "pip install -r $req failed (continuing)"
    fi
  done
fi

# ---- extras the requirements files do NOT cover ----------------------------
# Gen-1 verified: fresh containers lack pytest entirely; python-multipart is a
# runtime need beyond botsite/dashboard requirements. Non-fatal, one by one.
if [ "$pip_ok" -eq 1 ]; then
  for pkg in pytest python-multipart; do
    if "$PY" -m pip install --disable-pip-version-check -q "$pkg"; then
      note "extra installed: $pkg"
    else
      fail "pip install $pkg failed (continuing)"
    fi
  done
else
  note "pip unavailable — skipping extras (pytest, python-multipart)"
fi

# ---- summary ----------------------------------------------------------------
echo
echo "================ setup-env summary ================"
if [ -n "$PY" ]; then
  echo "python:        $("$PY" --version 2>&1) ($(command -v "$PY" 2>/dev/null || echo '?'))"
else
  echo "python:        NOT FOUND"
fi

if [ "${#INSTALLED_REQS[@]}" -gt 0 ]; then
  echo "requirements installed:"
  for req in "${INSTALLED_REQS[@]}"; do echo "  ok   $req"; done
else
  echo "requirements installed: none"
fi
if [ "${#FAILED_REQS[@]}" -gt 0 ]; then
  echo "requirements FAILED:"
  for req in "${FAILED_REQS[@]}"; do echo "  FAIL $req"; done
fi

if [ -n "$PY" ] && "$PY" -c 'import pytest' >/dev/null 2>&1; then
  echo "pytest importable: yes ($("$PY" -c 'import pytest; print(pytest.__version__)' 2>/dev/null))"
else
  echo "pytest importable: NO"
fi

# Presence check ONLY — never print values.
echo "env vars (names only, presence check):"
for var in GITHUB_TOKEN RAILWAY_API_KEY SITE_PASSWORD DATABASE_URL; do
  # ${!var+x} is safe under set -u: expands to x if set (even empty), else nothing
  if [ -n "${!var+x}" ]; then
    echo "  present: $var"
  else
    echo "  ABSENT:  $var"
  fi
done

if [ "${#FAILURES[@]}" -gt 0 ]; then
  echo "failures (${#FAILURES[@]}) — setup still exits 0, read these:"
  for f in "${FAILURES[@]}"; do echo "  ! $f"; done
else
  echo "failures: none"
fi
echo "==================================================="

# Contract: this script NEVER fails the hook/session.
exit 0
