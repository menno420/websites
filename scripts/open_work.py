#!/usr/bin/env python3
"""Open-work check: what is IN FLIGHT on this repo right now.

──────────────────────────────────────────────────────────────────────────────
PROVENANCE / KILL-SWITCH HEADER
  Why:   Concurrent sessions are the norm (4-hourly wake + send_later chains
         + coordinator dispatches + owner sessions). The wake ritual reads
         the inbox and the heartbeat but nothing surfaces OTHER sessions'
         in-flight code — lived twice on 2026-07-10: a wake started 6 min
         after a sibling opened PR #63 (near-collision on a shared file),
         and a stale ledger called merged work "not yet merged". One glance
         at open work prevents duplicate builds, shared-file merge
         conflicts, and false rescue alarms (the order-claim fix, applied
         to branches). Run it at session start, before picking a work rung.
  Added: 2026-07-11 (continuous-mode wake, backlog promotion; idea file
         docs/ideas/open-pr-awareness-at-wake-2026-07-10.md).
  Trust: DETERMINISTIC over `git ls-remote` + `git merge-base`; the PR half
         degrades honestly when api.github.com is unreachable (the known
         session wall) — it then says "PR state unknown", never guesses.
  KILL-SWITCH: convenience helper, not infrastructure — DELETE this file if
         it proves noisy; nothing depends on it.
──────────────────────────────────────────────────────────────────────────────

Usage:  python3 scripts/open_work.py
Output: one line per remote work branch (claude/* and manager/*), classified:
  PR-OPEN <branch> (#N)   — a session's landing path is in flight: leave it
                            to its session; avoid its files.
  PR-LESS <branch>        — commits not on main and no open PR: a rescue
                            candidate (the stranded-work protocol) or a
                            session mid-work before its PR — check age.
  MERGED-STALE <branch>   — no commits beyond main: landed content, prune
                            candidate (deletion needs rights this repo's
                            sessions lack — the documented 403 wall).
Exit 0 always (informational, never a gate).
"""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.request

OWNER_REPO = "menno420/websites"
PREFIXES = ("refs/heads/claude/", "refs/heads/manager/")


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], capture_output=True, text=True, check=False
    ).stdout


def remote_branches() -> dict[str, str]:
    """Remote work branches (name → sha) from `git ls-remote` — no API."""
    out: dict[str, str] = {}
    for line in _git("ls-remote", "origin").splitlines():
        parts = line.split("\t")
        if len(parts) == 2 and parts[1].startswith(PREFIXES):
            out[parts[1].split("refs/heads/", 1)[1]] = parts[0]
    return out


def open_prs() -> dict[str, int] | None:
    """Open-PR head branches via api.github.com, or None when unreachable
    (the documented session wall) — the caller renders 'unknown', never a
    guess."""
    url = f"https://api.github.com/repos/{OWNER_REPO}/pulls?state=open&per_page=100"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.load(resp)
        return {p["head"]["ref"]: p["number"] for p in data}
    except Exception:
        return None


def has_unmerged_commits(branch: str, sha: str) -> bool | None:
    """True when the branch tip is not an ancestor of origin/main. Fetches
    the single ref shallowly; None when even that fails (state unknown)."""
    subprocess.run(
        ["git", "fetch", "-q", "origin", branch],
        capture_output=True, check=False,
    )
    probe = subprocess.run(
        ["git", "merge-base", "--is-ancestor", sha, "origin/main"],
        capture_output=True, check=False,
    )
    if probe.returncode == 0:
        return False
    if probe.returncode == 1:
        return True
    return None  # sha not present locally even after fetch — unknown


def classify(
    branches: dict[str, str],
    prs: dict[str, int] | None,
    unmerged: dict[str, bool | None],
) -> list[dict]:
    """Pure classification (unit-tested): branch rows with state + note."""
    rows: list[dict] = []
    for name, sha in sorted(branches.items()):
        if prs is not None and name in prs:
            state, note = "PR-OPEN", f"#{prs[name]} — leave to its session"
        else:
            u = unmerged.get(name)
            if u is True:
                state = "PR-LESS" if prs is not None else "PR-UNKNOWN"
                note = (
                    "rescue candidate or mid-work — check age"
                    if prs is not None
                    else "unmerged commits; PR state unknown (api unreachable)"
                )
            elif u is False:
                state, note = "MERGED-STALE", "landed content — prune candidate"
            else:
                state, note = "UNKNOWN", "could not compare against main"
        rows.append({"branch": name, "sha": sha[:9], "state": state, "note": note})
    return rows


def main() -> int:
    branches = remote_branches()
    if not branches:
        print("open-work: no remote claude/* or manager/* branches.")
        return 0
    prs = open_prs()
    unmerged = {n: has_unmerged_commits(n, s) for n, s in branches.items()}
    rows = classify(branches, prs, unmerged)

    width = max(len(r["branch"]) for r in rows)
    print(f"open-work on {OWNER_REPO} "
          f"({'PR list live' if prs is not None else 'PR LIST UNREACHABLE — states partial'}):")
    for r in rows:
        print(f"  {r['state']:<13} {r['branch']:<{width}}  {r['sha']}  {r['note']}")
    attention = [r for r in rows if r["state"] in ("PR-LESS", "PR-UNKNOWN")]
    if attention:
        print(f"\n  ⚠ {len(attention)} branch(es) carry unmerged commits without a "
              "known open PR — apply the stranded-work protocol before new work.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
