"""Per-repo stats bake for the review service — few, cached, fail-soft.

Writes ``review/data/stats.json``: dated per-repo numbers for every
repo-backed seat in the committed fleet mirror (``fleet.json`` — run
``gen_fleet.py`` first). Two GitHub REST calls per repo, hard-capped:

- ``GET /repos/{owner}/{repo}`` — last-push time, open issues+PRs count,
  created date, description;
- ``GET /repos/{owner}/{repo}/pulls?state=all&per_page=1`` — the ``Link``
  header's last-page number IS the total PR count (no pagination walk).

Auth: uses ``GITHUB_TOKEN`` from the environment when present (the scheduled
``review-bake`` workflow passes the Actions token — ~1,000 req/h); otherwise
anonymous (60 req/h ceiling — ~2×18 calls fits, barely, which is why the
call count is capped and every failure is recorded per-repo instead of
aborting the bake). A repo the API won't serve gets an honest
``{"ok": false, "reason": …}`` — the site labels the gap, never fakes it.

Fail-soft (unattended cron): if fleet.json is missing/empty the previously
committed stats.json is left untouched and the script exits 0. A durable
owner PAT would lift the anonymous ceiling and unlock richer live stats —
queued in ``docs/owner/OWNER-ACTIONS.md``.

    python3 review/gen_stats.py
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

OWNER = "menno420"
DATA_DIR = Path(__file__).resolve().parent / "data"
FLEET_PATH = DATA_DIR / "fleet.json"
OUT_PATH = DATA_DIR / "stats.json"
API = "https://api.github.com"
TIMEOUT = 20

_LAST_PAGE_RE = re.compile(r'[?&]page=(\d+)>;\s*rel="last"')


def _api(path: str) -> tuple[Any | None, dict[str, str], str]:
    """(json_body, headers, "") on success; (None, {}, reason) on failure."""
    req = urllib.request.Request(
        f"{API}{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "websites-review-bake",
        },
    )
    token = (os.environ.get("GITHUB_TOKEN") or "").strip()
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:  # noqa: S310
            body = json.loads(resp.read().decode("utf-8", errors="replace"))
            return body, dict(resp.headers.items()), ""
    except urllib.error.HTTPError as exc:
        return None, {}, f"HTTP {exc.code}"
    except Exception as exc:  # noqa: BLE001 — fail-soft bake, reason recorded
        return None, {}, f"{type(exc).__name__}: {exc}"


def total_prs(repo: str) -> tuple[int | None, str]:
    """Total ever-opened PR count via the Link header's last page (per_page=1)."""
    body, headers, err = _api(f"/repos/{OWNER}/{repo}/pulls?state=all&per_page=1")
    if err:
        return None, err
    link = headers.get("Link") or headers.get("link") or ""
    m = _LAST_PAGE_RE.search(link)
    if m:
        return int(m.group(1)), ""
    # No Link header: zero or one PR total — the body length is the count.
    return (len(body) if isinstance(body, list) else 0), ""


def repo_stats(repo: str) -> dict[str, Any]:
    meta, _, err = _api(f"/repos/{OWNER}/{repo}")
    if err or not isinstance(meta, dict):
        return {"ok": False, "reason": err or "unexpected API shape"}
    prs, prs_err = total_prs(repo)
    out: dict[str, Any] = {
        "ok": True,
        "pushed_at": meta.get("pushed_at") or "",
        "created_at": meta.get("created_at") or "",
        "description": meta.get("description") or "",
        "open_issues_and_prs": meta.get("open_issues_count"),
        "default_branch": meta.get("default_branch") or "main",
    }
    if prs is not None:
        out["total_prs"] = prs
    else:
        out["total_prs_reason"] = prs_err
    return out


def main() -> int:
    try:
        fleet = json.loads(FLEET_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"fleet.json unreadable ({exc}) — stats bake skipped (fail-soft).")
        return 0
    repos = [ln["repo"] for ln in fleet.get("lanes", []) if ln.get("repo")]
    if not repos:
        print("fleet.json has no repo-backed lanes — stats bake skipped (fail-soft).")
        return 0

    token_present = bool((os.environ.get("GITHUB_TOKEN") or "").strip())
    stats: dict[str, Any] = {}
    for repo in repos:
        stats[repo] = repo_stats(repo)

    ok = sum(1 for v in stats.values() if v.get("ok"))
    if ok == 0:
        # Nothing real to record: keep whatever is committed (or nothing).
        # An all-failed file would show reviewers this container's proxy
        # errors as if GitHub said them; honest absence beats that.
        print(
            "every repo stat fetch failed — not writing stats.json (fail-soft; "
            "the previously committed file, if any, stays untouched)."
        )
        return 0

    out = {
        "generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "auth": "token" if token_present else "anonymous (60 req/h ceiling)",
        "note": (
            "Two REST calls per repo, fail-soft; a repo the API would not "
            "serve carries its exact reason. total_prs counts every PR ever "
            "opened; open_issues_and_prs is GitHub's combined open count."
        ),
        "repos": stats,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT_PATH.name}: {ok}/{len(repos)} repos with live stats")
    return 0


if __name__ == "__main__":
    sys.exit(main())
