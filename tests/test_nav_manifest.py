"""Nav-manifest membership guard: page 12 cannot skip the overflow guard.

The header nav is driven by ONE manifest (``app/nav.py``) — the template
iterates it and the overflow tests import it. This module closes the loop:
every ``active`` key a control-plane route actually passes to a template
must appear in the manifest, so adding a page without deciding its nav
group (primary vs the more ▾ dropdown) fails the suite instead of silently
rendering an un-highlighted, un-grouped page.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import nav  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
# Every module in the app package is scanned (glob, not a hand-kept list —
# the guard against hand-kept nav lists must not contain one: with the old
# ROUTE_SOURCES = [main.py, owner.py] list, splitting routes into a new
# module silently exited the scan). Source-text based on purpose; a module
# with no `active` keys (owner.py today) simply contributes nothing.
ROUTE_SOURCES = sorted((REPO_ROOT / "app").glob("*.py"))

# `"active": "board"` (context dicts) and `active="board"` (kwargs).
_ACTIVE_RE = re.compile(r'(?:"active"\s*:\s*|\bactive\s*=\s*)"([a-z_]+)"')


def _route_active_keys() -> set[str]:
    keys: set[str] = set()
    for src in ROUTE_SOURCES:
        if src.exists():
            keys.update(_ACTIVE_RE.findall(src.read_text(encoding="utf-8")))
    return keys


def test_every_route_active_key_is_in_the_manifest():
    route_keys = _route_active_keys()
    assert route_keys, "no active keys found — the scan regex rotted"
    missing = route_keys - nav.keys()
    assert not missing, (
        f"route(s) pass active key(s) {sorted(missing)} that are not in the "
        "app/nav.py manifest — add the page to PRIMARY or GROUPED (the "
        "overflow-guard decision), don't leave it outside the nav"
    )


def test_manifest_keys_are_unique_and_entries_complete():
    items = nav.PRIMARY + nav.GROUPED
    keys = [i["key"] for i in items]
    assert len(keys) == len(set(keys)), "duplicate nav key in the manifest"
    hrefs = [i["href"] for i in items]
    assert len(hrefs) == len(set(hrefs)), "duplicate nav href in the manifest"
    for item in items:
        assert item.get("href") and item.get("label") and item.get("key"), (
            f"manifest entry incomplete: {item!r}"
        )


def test_manifest_covers_no_stale_keys():
    """The manifest carries no key NO route uses (dead nav entries rot too)."""
    stale = nav.keys() - _route_active_keys()
    assert not stale, (
        f"manifest key(s) {sorted(stale)} are passed by no route — remove "
        "the dead entry or wire the page"
    )
