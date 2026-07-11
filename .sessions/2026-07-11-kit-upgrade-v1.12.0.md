# 2026-07-11 — kit upgrade v1.11.0 → v1.12.0

> **Status:** `in-progress` — branch `claude/kit-upgrade-v1.12.0`, fleet
> distribution wave (Q-0261.3). Born-red: this card holds the merge until
> the payload + verification land and the badge flips.

- **📊 Model:** claude-fable-5 · distribution worker · kit upgrade (fleet-wide v1.12.0 wave)

**What this session is about:** Fleet-wide substrate-kit v1.12.0 distribution
wave (rung: order — coordinator-directed upgrade, Q-0261.3 lane, same as the
v1.11.0 #129 / v1.10.1 #113 / v1.10.0 #105 upgrades). Payload: substantive
auto-draft arrival (reflog commit-subject evidence + carried-forward pointer),
planted-orientation boot-set trim (CLAUDE.md / AGENT_ORIENTATION /
CONSTITUTION templates), untouched-auto-draft advisory in the bare strict
lane only, and the carve-out scanner three-way compare (kit #210 — first
live exercise this wave).

## What is being done

- Sync to origin/main `ebef8bd`; all three tree stamps confirmed v1.11.0.
- Download + sha256-verify `bootstrap.py` v1.12.0 before staging; canonical
  recipe (`bootstrap.py.new` + `release.json` → `python3 bootstrap.py.new
  upgrade`); verify backups, stamps, carve-out scan; bump the exact-pin test;
  run the full local gate; land by merge commit on `quality` green.
