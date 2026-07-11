"""Snapshot generator for the review service — bake real repo numbers to JSON.

The review service is deployed with Railway Root Directory = ``review``, so the
running container ships ONLY this folder — it cannot read the repo's git
history, ``.sessions/`` cards, or ``control/`` files at request time. The
deliberate data model (mirroring how botsite/dashboard consume superbot's
COMMITTED json feeds) is therefore: derive the machine numbers from the repo
at build time, commit them as ``review/data/snapshot.json``, and let the app
read only that local file. Deterministic, network-free, honest — the snapshot
records exactly when it was generated and at which commit.

Run from the repo root (any session, any time the numbers should refresh):

    python3 review/gen_snapshot.py

It parses, from the real repo:
- merged-PR references per UTC day (squash-merge ``(#N)`` suffixes and merge
  commits on ``main`` — each PR number counted once, on its merge date);
- commits per UTC day;
- ``.sessions/`` cards per day (from the ``YYYY-MM-DD-*.md`` filenames);
- test functions per day (``def test_`` across every service's test dir, at
  the last commit of each UTC day — the growth curve of the safety net).

Nothing here is estimated or invented; a number the repo cannot support is
simply absent from the snapshot.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = Path(__file__).resolve().parent / "data" / "snapshot.json"

TEST_GLOBS = ["tests/*.py", "botsite/tests/*.py", "dashboard/tests/*.py", "review/tests/*.py"]
PR_REF = re.compile(r"\(#(\d+)\)\s*$")
MERGE_REF = re.compile(r"^Merge (?:PR|pull request) #(\d+)")


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, check=True, capture_output=True, text=True
    ).stdout


def _utc_date(iso: str) -> str:
    """Commit timestamp (any offset) -> its UTC calendar date."""
    return dt.datetime.fromisoformat(iso).astimezone(dt.timezone.utc).date().isoformat()


def commit_and_pr_days() -> tuple[dict[str, int], dict[str, int], int, int]:
    """Commits/day and unique merged-PR refs/day from ``main``'s history."""
    log = _git("log", "--pretty=%cI\x1f%s", "main")
    commits: dict[str, int] = defaultdict(int)
    pr_seen: dict[int, str] = {}
    for line in log.splitlines():
        if "\x1f" not in line:
            continue
        iso, subject = line.split("\x1f", 1)
        day = _utc_date(iso)
        commits[day] += 1
        m = PR_REF.search(subject) or MERGE_REF.match(subject)
        if m:
            num = int(m.group(1))
            # History is newest-first, so the FIRST sighting is the merge ref.
            pr_seen.setdefault(num, day)
    prs: dict[str, int] = defaultdict(int)
    for day in pr_seen.values():
        prs[day] += 1
    return dict(commits), dict(prs), sum(commits.values()), len(pr_seen)


def session_cards_per_day() -> tuple[dict[str, int], int]:
    cards: dict[str, int] = defaultdict(int)
    total = 0
    for p in sorted((REPO_ROOT / ".sessions").glob("*.md")):
        if p.name == "README.md":
            continue
        m = re.match(r"(\d{4}-\d{2}-\d{2})-", p.name)
        if m:
            cards[m.group(1)] += 1
            total += 1
    return dict(cards), total


def test_functions_at(ref: str) -> int:
    try:
        out = _git("grep", "-c", "def test_", ref, "--", *TEST_GLOBS)
    except subprocess.CalledProcessError:
        return 0
    return sum(int(line.rsplit(":", 1)[-1]) for line in out.splitlines() if ":" in line)


def eod_commit(day: str) -> str | None:
    """Last commit on main at or before the end of the given UTC day."""
    before = f"{day}T23:59:59Z"
    sha = _git("rev-list", "-1", f"--before={before}", "main").strip()
    return sha or None


def main() -> None:
    commits, prs, total_commits, total_prs = commit_and_pr_days()
    cards, total_cards = session_cards_per_day()
    days = sorted(set(commits) | set(prs) | set(cards))
    head = _git("rev-parse", "HEAD").strip()
    today = dt.datetime.now(dt.timezone.utc).date().isoformat()

    day_rows = []
    for day in days:
        row: dict[str, object] = {
            "date": day,
            "prs_merged": prs.get(day, 0),
            "commits": commits.get(day, 0),
            "session_cards": cards.get(day, 0),
        }
        eod = eod_commit(day)
        if eod:
            row["test_functions_eod"] = test_functions_at(eod)
        if day == today:
            row["partial"] = True  # the day was still running when generated
        day_rows.append(row)

    snapshot = {
        "generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_head": head,
        "days": day_rows,
        "totals": {
            "prs_merged": total_prs,
            "commits": total_commits,
            "session_cards": total_cards,
            "test_functions": test_functions_at("HEAD"),
            "services": 4,  # control-plane, botsite, dashboard, review
        },
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT_PATH.relative_to(REPO_ROOT)} (head {head[:8]}, {len(day_rows)} days)")


if __name__ == "__main__":
    sys.exit(main())
