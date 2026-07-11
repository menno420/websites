"""Fleet-mirror bake for the review service — registry + heartbeats to JSON.

The review service is network-free at runtime (Railway Root Directory =
``review`` ships only this folder — see ``gen_snapshot.py`` for the full
rationale), so everything the fleet pages show must be COMMITTED under
``review/data/``. This script is the bake half: run it from the repo root
(any session, or the scheduled ``review-bake`` GitHub Actions workflow) and
it writes ``review/data/fleet.json``:

- **The lane registry** — fetched live from the fleet-manager's canonical
  ``LANES`` literal in ``scripts/gen_roster.py`` (the same source the
  control-plane's ``/fleet`` parses; fleet-manager is verified anonymously
  readable over raw.githubusercontent.com — ``docs/CAPABILITIES.md``
  2026-07-10). The registry counts are recorded as found: total seats,
  repo-backed seats, and registry-only seats (a seat with ``repo: None`` has
  no repo to feature — the pages surface that split honestly instead of
  hardcoding a fleet size).
- **Every repo-backed lane's heartbeat** — ``control/status.md`` fetched raw
  and parsed with the fleet's documented key grammar (a standalone copy of
  the ``control/README.md`` format; this script deliberately imports nothing
  from ``app/`` — services never import each other's packages, and a bake
  script honors the same seam). A repo whose heartbeat cannot be fetched is
  recorded with the exact reason — never guessed, never dropped.

Fail-soft by design (this runs unattended on a cron): if the REGISTRY fetch
fails and a previously committed ``fleet.json`` exists, the old file is left
in place untouched (its ``generated_at`` ages honestly and the site's
staleness banner does the telling) and the script exits 0. Network calls are
few (1 registry + ~18 raw heartbeat fetches, no REST API) and each is
bounded by a timeout.

    python3 review/gen_fleet.py
"""

from __future__ import annotations

import ast
import datetime as dt
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

OWNER = "menno420"
REGISTRY_REPO = "fleet-manager"
REGISTRY_PATH = "scripts/gen_roster.py"
REGISTRY_RAW = (
    f"https://raw.githubusercontent.com/{OWNER}/{REGISTRY_REPO}/main/{REGISTRY_PATH}"
)
REGISTRY_URL = f"https://github.com/{OWNER}/{REGISTRY_REPO}/blob/main/{REGISTRY_PATH}"

OUT_PATH = Path(__file__).resolve().parent / "data" / "fleet.json"
TIMEOUT = 20

# The documented control/status.md field keys (control/README.md grammar —
# a standalone copy of app/fleet.KNOWN_KEYS; see module docstring for why
# this is a copy and not an import).
KNOWN_KEYS = {
    "updated", "phase", "health", "last-shipped", "blockers", "orders",
    "needs-owner", "notes", "kit", "routine", "landing", "deployed",
    "rung", "tooling",
}

_REGISTRY_LANES_RE = re.compile(r"^LANES\s*=\s*(\[.*?\n\])", re.DOTALL | re.MULTILINE)

# Per-field cap for the committed mirror. Some lanes write huge free-text
# fields (or don't follow the grammar, so a whole document lands in one
# field as continuation lines); the review pages show summary cards, not
# full bodies, and an uncapped mirror weighed 440KB. Truncation is marked
# visibly — never silent.
FIELD_CAP = 600
_TRUNC_MARK = " … [truncated for the mirror — full text at the source]"


def _fetch(url: str) -> tuple[str | None, str]:
    """(body, "") on success; (None, reason) on any failure — never raises."""
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as resp:  # noqa: S310
            return resp.read().decode("utf-8", errors="replace"), ""
    except urllib.error.HTTPError as exc:
        return None, f"HTTP {exc.code}"
    except Exception as exc:  # noqa: BLE001 — fail-soft bake, reason recorded
        return None, f"{type(exc).__name__}: {exc}"


def parse_registry(text: str) -> list[dict[str, Any]]:
    """The ``LANES`` literal out of gen_roster.py source — pure data via
    ``ast.literal_eval``, never executed. [] when absent/malformed."""
    m = _REGISTRY_LANES_RE.search(text or "")
    if not m:
        return []
    try:
        data = ast.literal_eval(m.group(1))
    except (ValueError, SyntaxError):
        return []
    if not isinstance(data, list):
        return []
    return [e for e in data if isinstance(e, dict)]


def _norm_key(raw: str) -> str:
    return raw.strip().lstrip("⚑").strip().lower()


def parse_heartbeat(text: str) -> dict[str, str]:
    """``control/status.md`` → the documented ``key: value`` fields, verbatim.

    Same tolerant grammar the control-plane uses: a line whose leading token
    is not a known key continues the current field (wrapped values survive);
    a colon inside a value never starts a new field.
    """
    fields: dict[str, str] = {}
    cur: str | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" in stripped:
            raw_key, _, value = stripped.partition(":")
            nk = _norm_key(raw_key)
            if nk in KNOWN_KEYS:
                fields[nk] = value.strip()
                cur = nk
                continue
        if cur is not None:
            fields[cur] = f"{fields[cur]} {stripped}".strip()
    for key, value in fields.items():
        if len(value) > FIELD_CAP:
            fields[key] = value[:FIELD_CAP].rstrip() + _TRUNC_MARK
    return fields


def bake_lane(entry: dict[str, Any]) -> dict[str, Any]:
    """One registry entry → its committed lane record (heartbeat mirrored)."""
    repo = entry.get("repo")
    lane: dict[str, Any] = {
        "lane": str(entry.get("lane") or repo or "?"),
        "repo": repo,
        "disposition": str(entry.get("disposition") or ""),
    }
    if not repo:
        lane["heartbeat"] = {
            "available": False,
            "reason": "registry-only seat — no repo, nothing to mirror",
        }
        return lane
    lane["repo_url"] = f"https://github.com/{OWNER}/{repo}"
    hb_url = f"https://raw.githubusercontent.com/{OWNER}/{repo}/main/control/status.md"
    body, err = _fetch(hb_url)
    if body is None or not body.strip():
        reason = err or "empty file"
        if err == "HTTP 404":
            reason = "HTTP 404 — no control/status.md on main (or repo not public)"
        lane["heartbeat"] = {"available": False, "reason": reason}
    else:
        lane["heartbeat"] = {
            "available": True,
            "fields": parse_heartbeat(body),
            "source_url": f"https://github.com/{OWNER}/{repo}/blob/main/control/status.md",
        }
    return lane


def main() -> int:
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    reg_text, reg_err = _fetch(REGISTRY_RAW)
    entries = parse_registry(reg_text) if reg_text else []

    if not entries:
        reason = reg_err or "registry parsed to zero seats"
        if OUT_PATH.exists():
            print(
                f"registry unavailable ({reason}) — keeping the previously "
                f"committed {OUT_PATH.name} untouched (fail-soft)."
            )
            return 0
        # First-ever bake with no registry: write an honest empty mirror so
        # the site banners rather than 500s or invents lanes.
        out = {
            "generated_at": now,
            "registry": {
                "ok": False,
                "reason": reason,
                "url": REGISTRY_URL,
                "total_seats": 0,
                "repo_seats": 0,
                "registry_only_seats": [],
            },
            "lanes": [],
        }
        OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUT_PATH.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {OUT_PATH.name} with an honest empty registry ({reason})")
        return 0

    lanes = [bake_lane(e) for e in entries]
    registry_only = [ln["lane"] for ln in lanes if not ln.get("repo")]
    out = {
        "generated_at": now,
        "registry": {
            "ok": True,
            "reason": "",
            "url": REGISTRY_URL,
            "total_seats": len(lanes),
            "repo_seats": len(lanes) - len(registry_only),
            "registry_only_seats": registry_only,
        },
        "lanes": lanes,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    mirrored = sum(1 for ln in lanes if ln.get("heartbeat", {}).get("available"))
    print(
        f"wrote {OUT_PATH.name}: {len(lanes)} seats "
        f"({len(lanes) - len(registry_only)} repo-backed, "
        f"{len(registry_only)} registry-only), {mirrored} heartbeats mirrored"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
