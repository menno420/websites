"""Release-drift bake for the review service — expected vs. live release tags.

The review service is network-free at runtime (Railway Root Directory =
``review`` ships only this folder — see ``gen_snapshot.py`` for the full
rationale), so everything the pages show must be COMMITTED under
``review/data/``. This script is the bake half: run it from the repo root
(any session, or a scheduled bake) and it writes ``review/data/releases.json``.

**What it bakes.** For every arcade game in ``botsite/data/arcade.json`` that
names a ``source_repo``, it records two tags and whether they drift:

- **expected_tag** — the release tag the committed arcade registry expects.
  ``arcade.json`` has NO structured tag field (adding one would break the
  botsite schema-integrity guard, ``botsite/tests/test_arcade_registry_integrity``),
  so the tag is parsed with a regex out of the game's ``blocker.owner_action``
  and ``status_note`` free text — the same ``<name>-vN.N`` token the owner
  publishes the GitHub Release under (canonical: ``lumen-drift-v1.3``). A game
  whose text encodes no such tag records ``expected_tag: null`` and never
  claims drift.
- **live_tag** — the latest tag actually published on the source repo, read
  over ANONYMOUS GIT TRANSPORT (``git ls-remote --tags <url>``). Chosen over
  the REST API on purpose, exactly like ``gen_fleet.head_probe``: git
  transport is reachable from session containers whose proxy walls
  api.github.com, and needs no token. The Actions-run alternative would be
  ``GET /repos/{owner}/{repo}/releases/latest`` with ``GITHUB_TOKEN`` (see
  ``gen_stats.py`` for that REST idiom) — but git transport is used here so
  the bake works from any session container.

**Drift** is True when a known expected_tag differs from the live latest tag
(including the canonical "expected tag not yet published" case, where the live
side has no matching tag). A game with no expected_tag, or whose live tags
could not be read, records ``drift: false`` with an honest reason — a review
site never invents a signal it cannot stand behind.

Fail-soft by design (may run unattended): every network call is bounded by a
timeout and NEVER raises — a failure records its reason. If ``arcade.json`` is
unreadable and a previously committed ``releases.json`` exists, the old file is
left untouched and the script exits 0.

    python3 review/gen_releases.py
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

# review/gen_releases.py -> review/ -> <repo root>
REPO_ROOT = Path(__file__).resolve().parents[1]
ARCADE_PATH = REPO_ROOT / "botsite" / "data" / "arcade.json"
OUT_PATH = REPO_ROOT / "review" / "data" / "releases.json"

TIMEOUT = 20

NOTE = (
    "Per arcade game with a source repo: the release tag the committed "
    "botsite/data/arcade.json expects (parsed from the game's blocker/"
    "status free text — arcade.json has no structured tag field) vs. the "
    "live latest tag on that source repo, read over anonymous git transport "
    "(git ls-remote --tags) at bake time. drift=true means a known expected "
    "tag differs from the live latest tag (including an expected release not "
    "yet published). A game with no encoded tag, or whose live tags could "
    "not be read, records drift=false with an honest reason."
)

# A release-tag token: a name segment ending in ``-vN[.N...]`` — e.g.
# ``lumen-drift-v1.3``. Anchored on the ``-v<digits>`` suffix so a bare
# ``(v1.3)`` in prose (no ``-v`` boundary) is never mistaken for a tag.
_TAG_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*-v\d+(?:\.\d+)*")

# ls-remote line: ``<40-hex-sha>\trefs/tags/<name>`` (possibly ``name^{}``).
_LS_REMOTE_TAG_RE = re.compile(r"^[0-9a-f]{40}\s+refs/tags/(.+)$")


def parse_arcade(text: str) -> list[dict[str, Any]]:
    """``arcade.json`` text → ``[{slug, name, source_repo, expected_tag}]``.

    Only games that name a ``source_repo`` are included (a game with no repo
    has nothing to drift against). ``expected_tag`` is the ``<name>-vN.N``
    token found in the game's ``blocker.owner_action`` then ``status_note``
    free text, or ``None`` when the registry encodes no release tag. Malformed
    input degrades to ``[]`` — never raises."""
    try:
        data = json.loads(text or "")
    except (ValueError, TypeError):
        return []
    if not isinstance(data, list):
        return []
    out: list[dict[str, Any]] = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        source_repo = entry.get("source_repo")
        if not isinstance(source_repo, str) or not source_repo.strip():
            continue
        out.append({
            "slug": str(entry.get("slug") or ""),
            "name": str(entry.get("name") or entry.get("slug") or "?"),
            "source_repo": source_repo.strip(),
            "expected_tag": _expected_tag(entry),
        })
    return out


def _expected_tag(entry: dict[str, Any]) -> str | None:
    """The release tag encoded in a game's registry free text, or None.

    Searches the ``blocker.owner_action`` (the owner's "Publish the GitHub
    Release <tag>" instruction) first, then ``status_note``. Deliberately does
    NOT read ``description`` — a bare version like ``(v1.3)`` there is not a
    tag and must not be matched."""
    blocker = entry.get("blocker")
    owner_action = ""
    if isinstance(blocker, dict):
        owner_action = str(blocker.get("owner_action") or "")
    for text in (owner_action, str(entry.get("status_note") or "")):
        m = _TAG_RE.search(text)
        if m:
            return m.group(0)
    return None


def parse_ls_remote_tags(output: str) -> list[str]:
    """``git ls-remote --tags`` stdout → tag names (deduped, order-preserved).

    Each line is ``<sha>\\trefs/tags/<name>``; the ``<name>^{}`` peeled-tag
    lines that annotated tags emit are collapsed onto the same tag name."""
    seen: set[str] = set()
    tags: list[str] = []
    for line in (output or "").splitlines():
        m = _LS_REMOTE_TAG_RE.match(line.strip())
        if not m:
            continue
        name = m.group(1).strip()
        if name.endswith("^{}"):
            name = name[:-3]
        if name and name not in seen:
            seen.add(name)
            tags.append(name)
    return tags


def _natural_key(tag: str) -> list[Any]:
    """Split a tag into text/number chunks so ``v1.10`` sorts after ``v1.9``.
    Numbers compare numerically; text chunks compare case-folded."""
    return [
        int(part) if part.isdigit() else part.casefold()
        for part in re.split(r"(\d+)", tag)
        if part
    ]


def pick_latest_tag(tags: list[str], slug: str) -> str | None:
    """The most recent tag for one game, or None when there is nothing to pick.

    Heuristic (kept deliberately simple + deterministic): prefer tags that
    belong to this game's family — those beginning with the game's ``slug``
    (a shared repo like ``gba-homebrew`` may host several games' tags, so the
    slug prefix scopes the pick to this game). When no tag matches the family,
    fall back to all tags. The winner is the highest by a natural, version-
    aware sort (so ``lumen-drift-v1.10`` beats ``lumen-drift-v1.9``)."""
    if not tags:
        return None
    slug = (slug or "").strip()
    family = [t for t in tags if slug and t.startswith(slug)]
    candidates = family or tags
    return max(candidates, key=_natural_key)


def compute_drift(expected_tag: str | None, live_tag: str | None) -> tuple[bool, str]:
    """(drift, reason) for one game's expected vs. live tag — pure.

    Drift is True only when a KNOWN expected tag differs from the live latest
    tag (a missing live tag counts as differing — the expected release simply
    is not published). An unknown expected tag never drifts."""
    if expected_tag is None:
        return False, "no release tag is encoded in the arcade registry for this game"
    if live_tag is None:
        return True, (
            f"expected release {expected_tag} is not published on the source repo "
            f"(no matching live tag found)"
        )
    if expected_tag == live_tag:
        return False, f"expected release {expected_tag} matches the live latest tag"
    return True, (
        f"expected release {expected_tag} differs from the live latest tag {live_tag}"
    )


def fetch_tags(source_repo: str) -> tuple[list[str], str]:
    """Live tags of ``owner/repo`` over anonymous git transport — never raises.

    ``(tags, "")`` on success (an empty list is a valid success — the repo has
    no tags); ``([], reason)`` on any failure. Mirrors ``gen_fleet.head_probe``:
    ``git ls-remote --tags`` advertises tags without auth and is reachable from
    session containers whose proxy walls api.github.com. The Actions-run
    alternative is ``GET /repos/{source_repo}/releases/latest`` with
    ``GITHUB_TOKEN`` (the ``gen_stats.py`` REST idiom); git transport is used
    here so the bake works tokenless from any session container."""
    url = f"https://github.com/{source_repo}"
    try:
        out = subprocess.run(
            ["git", "ls-remote", "--tags", url],
            capture_output=True, text=True, timeout=TIMEOUT,
            env={"GIT_TERMINAL_PROMPT": "0"},
        )
    except subprocess.TimeoutExpired:
        return [], "ls-remote --tags timed out"
    except OSError as exc:
        return [], f"{type(exc).__name__}: {exc}"
    if out.returncode != 0:
        reason = (out.stderr or "").strip().splitlines()
        return [], f"unreadable over git transport ({reason[-1] if reason else 'ls-remote failed'})"
    return parse_ls_remote_tags(out.stdout), ""


def bake(arcade_text: str, tag_fetcher: Callable[[str], tuple[list[str], str]]) -> dict[str, Any]:
    """Pure bake: arcade text + an injectable tag fetcher → the releases doc.

    ``tag_fetcher(source_repo) -> (tags, reason)`` is injected so tests stub
    the network. A per-game fetch failure records its reason and leaves drift
    undetermined (False) — a review site never asserts drift on data it could
    not read."""
    games = parse_arcade(arcade_text)
    entries: list[dict[str, Any]] = []
    for game in games:
        source_repo = game["source_repo"]
        expected_tag = game["expected_tag"]
        tags, fetch_reason = tag_fetcher(source_repo)
        live_tag = pick_latest_tag(tags, game["slug"])
        if fetch_reason and not tags:
            drift = False
            reason = f"live tags unavailable ({fetch_reason}); drift undetermined"
            live_tag = None
        else:
            drift, reason = compute_drift(expected_tag, live_tag)
        entries.append({
            "slug": game["slug"],
            "name": game["name"],
            "source_repo": source_repo,
            "expected_tag": expected_tag,
            "live_tag": live_tag,
            "drift": drift,
            "reason": reason,
        })
    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "note": NOTE,
        "entries": entries,
        "drift_count": sum(1 for e in entries if e["drift"]),
    }


def main() -> int:
    try:
        arcade_text = ARCADE_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        if OUT_PATH.exists():
            print(
                f"arcade.json unreadable ({exc}) — keeping the previously "
                f"committed {OUT_PATH.name} untouched (fail-soft)."
            )
            return 0
        print(f"arcade.json unreadable ({exc}) and no committed {OUT_PATH.name} — nothing to write (fail-soft).")
        return 0

    out = bake(arcade_text, fetch_tags)

    # Fail-soft: if every game's live tags failed to read (a total network
    # wall) and a committed file already exists, don't clobber it with an
    # all-undetermined mirror — leave the last good bake in place.
    if out["entries"] and all(
        "drift undetermined" in e["reason"] for e in out["entries"]
    ) and OUT_PATH.exists():
        print(
            f"every source repo's tags were unreadable — keeping the previously "
            f"committed {OUT_PATH.name} untouched (fail-soft)."
        )
        return 0

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(
        f"wrote {OUT_PATH.name}: {len(out['entries'])} game(s), "
        f"{out['drift_count']} drifting"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
