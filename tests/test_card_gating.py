"""Unit tests for the card-gating reverse join (app/card_gating.py).

The helper answers "which public product cards does each open owner-action
ask hold closed?" by loading the four committed botsite registries from disk
and joining their ``blocker.ask_id`` to the ledger's stable ``ASK-NNNN`` id.
These tests pin the counts, the cross-registry aggregation, and the
fail-soft behaviour (missing/corrupt file, malformed entry/blocker/id all
degrade to no cards, never a crash and never an invented gated card).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import card_gating  # noqa: E402

# A registry shaped like arcade/catalog/products (a bare list of cards).
_LIST_REGISTRY = [
    {"slug": "alpha", "name": "Alpha", "blocker": {
        "owner_action": "click a", "unblocks": "u", "ask_id": "ASK-0100"}},
    {"slug": "beta", "title": "Beta", "blocker": {
        "owner_action": "click b", "unblocks": "u", "ask_id": "ASK-0100"}},
    {"slug": "gamma", "name": "Gamma", "blocker": {
        "owner_action": "click c", "unblocks": "u", "ask_id": "ASK-0200"}},
    # no blocker at all -> contributes nothing
    {"slug": "delta", "name": "Delta"},
    # malformed blocker (not a dict) -> skipped, never fatal
    {"slug": "epsilon", "name": "Epsilon", "blocker": "oops"},
    # malformed ask_id (wrong shape) -> the card is not gated by any id
    {"slug": "zeta", "name": "Zeta", "blocker": {
        "owner_action": "x", "unblocks": "u", "ask_id": "ASK-99"}},
]

# A second list registry that ALSO references ASK-0100 (cross-registry).
_LIST_REGISTRY_2 = [
    {"slug": "omega", "name": "Omega", "blocker": {
        "owner_action": "click o", "unblocks": "u", "ask_id": "ASK-0100"}},
]

# A dict-shaped registry like puddle_museum.json (blocker on a nested list;
# a sibling collection with no blockers must not break the walk).
_DICT_REGISTRY = {
    "exhibits": [
        {"slug": "no-blocker-exhibit", "name_en": "Just an exhibit"},
    ],
    "editions": [
        # editions carry no slug — the title must fall back to ``title``
        {"lang": "en", "title": "The Book (EN)", "blocker": {
            "owner_action": "decide", "unblocks": "u", "ask_id": "ASK-0300"}},
        {"lang": "nl", "title": "Het Boek (NL)", "blocker": {
            "owner_action": "decide", "unblocks": "u", "ask_id": "ASK-0300"}},
    ],
}


def _write_fixture(tmp_path: Path) -> Path:
    """Lay out the four registry filenames the helper looks for, mapping the
    two list fixtures + the dict fixture onto real names and leaving one file
    ABSENT (products.json) to exercise the missing-file path."""
    data = tmp_path / "data"
    data.mkdir()
    (data / "arcade.json").write_text(json.dumps(_LIST_REGISTRY))
    (data / "catalog.json").write_text(json.dumps(_LIST_REGISTRY_2))
    (data / "puddle_museum.json").write_text(json.dumps(_DICT_REGISTRY))
    # products.json deliberately NOT written -> missing-file fail-soft.
    return data


def test_local_ask_id_shape_matches_botsite_ledger():
    """The re-stated ASK-NNNN pattern must agree with botsite/blockers.py
    (the import rule forbids importing it, so agreement is pinned here)."""
    from botsite import blockers

    assert card_gating.ASK_ID_RE.pattern == blockers.ASK_ID_RE.pattern


def test_counts_and_cross_registry_aggregation(tmp_path):
    data = _write_fixture(tmp_path)
    gating = card_gating.load_gating(data)

    # ASK-0100 is named by alpha + beta (arcade) AND omega (catalog): 3.
    assert len(gating["ASK-0100"]) == 3
    registries = sorted(c["registry"] for c in gating["ASK-0100"])
    assert registries == ["arcade", "arcade", "catalog"]
    titles = {c["title"] for c in gating["ASK-0100"]}
    assert titles == {"Alpha", "Beta", "Omega"}

    # ASK-0200 gates only gamma.
    assert [c["slug"] for c in gating["ASK-0200"]] == ["gamma"]

    # ASK-0300 (dict registry, editions) gates both editions; a slug-less
    # edition still gets a real title (``title`` fallback), never empty.
    assert len(gating["ASK-0300"]) == 2
    assert {c["title"] for c in gating["ASK-0300"]} == {
        "The Book (EN)", "Het Boek (NL)"}
    assert all(c["slug"] == "" for c in gating["ASK-0300"])
    assert all(c["registry"] == "puddle-museum" for c in gating["ASK-0300"])


def test_malformed_and_missing_never_gate(tmp_path):
    data = _write_fixture(tmp_path)
    gating = card_gating.load_gating(data)
    # The bad ask_id shape (ASK-99) is not a key anywhere.
    assert "ASK-99" not in gating
    # The no-blocker / bad-blocker cards never appear under any id.
    all_slugs = {c["slug"] for cards in gating.values() for c in cards}
    assert "delta" not in all_slugs and "epsilon" not in all_slugs
    assert "zeta" not in all_slugs
    # The dict registry's blocker-less exhibit never gates anything.
    assert "no-blocker-exhibit" not in all_slugs


def test_missing_directory_degrades_to_empty(tmp_path):
    """A directory with none of the expected files yields an empty map, not
    a crash."""
    assert card_gating.load_gating(tmp_path / "does-not-exist") == {}


def test_corrupt_file_is_skipped(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    (data / "arcade.json").write_text("{ this is not json ")
    (data / "catalog.json").write_text(json.dumps(_LIST_REGISTRY_2))
    gating = card_gating.load_gating(data)
    # arcade contributed nothing (corrupt), catalog's omega still lands.
    assert [c["slug"] for c in gating["ASK-0100"]] == ["omega"]


def test_annotate_unblocks_sets_count_and_cards(tmp_path):
    data = _write_fixture(tmp_path)
    items = [
        {"ask_id": "ASK-0100", "what": "the multi-gate ask"},
        {"ask_id": "ASK-0200", "what": "the single-gate ask"},
        {"ask_id": "ASK-9999", "what": "an ask no card names"},
        {"ask_id": None, "what": "a legacy ask with no id"},
    ]
    card_gating.annotate_unblocks(items, data)
    assert items[0]["unblocks_count"] == 3
    assert len(items[0]["unblocks_cards"]) == 3
    assert items[1]["unblocks_count"] == 1
    # An id no card gates -> 0, empty list (the template hides the chip).
    assert items[2]["unblocks_count"] == 0
    assert items[2]["unblocks_cards"] == []
    # A None ask_id never raises and reads as 0.
    assert items[3]["unblocks_count"] == 0


def test_real_registries_load_and_aggregate():
    """Smoke over the COMMITTED registries: the join is non-empty and the
    known cross-registry ask (Gumroad publish pass, ASK-0012) spans more
    than one registry — the reverse join's whole reason to exist."""
    gating = card_gating.load_gating()
    assert gating, "expected the committed registries to gate at least one ask"
    assert all(re.fullmatch(r"ASK-\d{4}", k) for k in gating)
    if "ASK-0012" in gating:
        registries = {c["registry"] for c in gating["ASK-0012"]}
        assert len(registries) >= 2
