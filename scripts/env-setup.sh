#!/usr/bin/env bash
# env-setup.sh — wrapper invoking the tested scripts/setup-env.sh (ORDER 007
# step 4). The pinned-research environment archetype expects this exact path
# (scripts/env-setup.sh); gen-1 shipped the logic as setup-env.sh, leaving a
# silent env gap — a fresh container configured with the archetype's hook path
# found no script and skipped setup. This wrapper retires that gap without
# duplicating logic: one real implementation (setup-env.sh), two entry paths.
# Contract matches setup-env.sh: ALWAYS exits 0, never prints secret values.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" >/dev/null 2>&1 && pwd)"
if [ -f "$SCRIPT_DIR/setup-env.sh" ]; then
  exec bash "$SCRIPT_DIR/setup-env.sh" "$@"
fi
printf '[env-setup] FAIL: %s/setup-env.sh not found — nothing to run\n' "$SCRIPT_DIR"
# Same never-fail contract as the wrapped script.
exit 0
