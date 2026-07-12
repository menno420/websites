"""Nav-manifest membership guard: a page cannot be added outside the IA.

The whole information architecture is driven by ONE structure
(``app/nav.py`` ``CATEGORIES`` — the 2-level category → subcategory
hierarchy): the header renders the categories, the landing pages render the
rows, the home map renders both. This module closes the loop: every
``active`` key a control-plane route actually passes to a template must
appear in the manifest, so adding a page without deciding its category
fails the suite instead of silently rendering an un-highlighted page.
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
        "app/nav.py manifest — place the page in a category (the IA "
        "decision), don't leave it outside the hierarchy"
    )


def test_manifest_keys_are_unique_and_entries_complete():
    cat_keys = [c["key"] for c in nav.CATEGORIES]
    assert len(cat_keys) == len(set(cat_keys)), "duplicate category key"
    item_keys = [
        it["key"] for c in nav.CATEGORIES for it in c["items"] if it["key"]
    ]
    assert len(item_keys) == len(set(item_keys)), "duplicate item key"
    assert not set(item_keys) & set(cat_keys), (
        "an item key shadows a category key — category_for would be ambiguous"
    )
    for cat in nav.CATEGORIES:
        for field in ("key", "label", "href", "desc", "items"):
            assert cat.get(field), f"category entry incomplete: {cat['key']!r}"
        assert isinstance(cat["landing"], bool) and isinstance(
            cat["gated"], bool
        )
        for it in cat["items"]:
            assert it.get("label") and it.get("href") and it.get("desc"), (
                f"item entry incomplete under {cat['key']!r}: {it!r}"
            )
            action = it.get("action")
            assert action and action.get("label") and action.get("href"), (
                f"item missing its primary action: {it.get('label')!r}"
            )


def test_manifest_covers_no_stale_keys():
    """The manifest carries no key NO route uses (dead nav entries rot too)."""
    stale = nav.keys() - _route_active_keys()
    assert not stale, (
        f"manifest key(s) {sorted(stale)} are passed by no route — remove "
        "the dead entry or wire the page"
    )


def test_category_for_maps_every_key_and_rejects_unknowns():
    for cat in nav.CATEGORIES:
        if cat["landing"]:
            assert nav.category_for(cat["key"]) == cat["key"]
        for it in cat["items"]:
            if it["key"]:
                assert nav.category_for(it["key"]) == cat["key"]
    assert nav.category_for(None) is None
    assert nav.category_for("") is None
    assert nav.category_for("no-such-page") is None


def test_lookup_helpers():
    assert nav.category("work")["href"] == "/work"
    assert nav.item("prompts")["href"] == "/prompts"
    hrefs = nav.all_hrefs()
    assert len(hrefs) == len(set(hrefs)), "all_hrefs must be deduped"
    for expected in ("/", "/work", "/history", "/console", "/owner",
                     "/queue", "/prompts", "/owner/environments-hub"):
        assert expected in hrefs
