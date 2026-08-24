"""Cross-registry drift guard for the shared Product Forge arcade URL.

The fleet records the browser-games arcade in TWO independent registries —
``botsite/data/arcade.json`` (the Fleet Arcade) and ``app/data/web_presence.json``
(the control-plane /directory). Nothing structurally stops them from drifting:
the `games-web` arcade row and the canonical `product-forge` portfolio row. This
guard joins those deliberately shared surfaces and fails when their public URL
drifts. Individual downloadable games such as Lumen Drift are not portfolio
products and therefore do not belong in the canonical eight-row directory.

Green now (both registries synced); red only on future drift.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import web_presence  # noqa: E402
from botsite import arcade  # noqa: E402

# arcade slug -> canonical portfolio product id
SHARED_KEYS = {"games-web": "product-forge"}


def _arcade_by_slug() -> dict:
    entries = json.loads(arcade.ARCADE_JSON_PATH.read_text(encoding="utf-8"))
    return {e["slug"]: e for e in entries if isinstance(e, dict) and e.get("slug")}


def _web_presence_by_id() -> dict:
    reg = json.loads(web_presence.REGISTRY_PATH.read_text(encoding="utf-8"))
    return {r["id"]: r for r in reg["sites"] if isinstance(r, dict) and r.get("id")}


def test_shared_registry_entries_do_not_drift():
    arc = _arcade_by_slug()
    wp = _web_presence_by_id()
    for arcade_key, portfolio_key in SHARED_KEYS.items():
        assert arcade_key in arc, f"{arcade_key} missing from botsite/data/arcade.json"
        assert portfolio_key in wp, f"{portfolio_key} missing from app/data/web_presence.json"
        a, w = arc[arcade_key], wp[portfolio_key]

        # arcade's view: a game is reachable when it carries a linked availability
        # (live/download — the same source of truth the loader's has_link uses)
        # AND a real URL.
        arcade_reachable = (
            a.get("availability") in arcade.LINKED_AVAILABILITIES and bool(a.get("url"))
        )
        # web_presence's view: a row is published when it is no longer
        # pending-publish AND carries a real URL.
        wp_published = w.get("status") != "pending-publish" and bool(w.get("url"))

        assert arcade_reachable == wp_published, (
            f"{arcade_key}/{portfolio_key}: registries drifted — arcade reachable={arcade_reachable} "
            f"(availability={a.get('availability')!r}, url={a.get('url')!r}) but "
            f"web_presence published={wp_published} "
            f"(status={w.get('status')!r}, url={w.get('url')!r})"
        )

        # when both agree the game is live, the recorded URLs must match exactly —
        # the two public surfaces must send visitors to the SAME place.
        if arcade_reachable:
            assert a.get("url") == w.get("url"), (
                f"{arcade_key}/{portfolio_key}: URL drift — arcade {a.get('url')!r} != "
                f"web_presence {w.get('url')!r}"
            )
            if arcade_key == "games-web":
                description = str(w.get("description") or "").lower()
                assert "phase-1" in description and "mock" in description, (
                    "Product Forge directory copy must identify the source-backed "
                    "mock-data character-sheet demo, not overstate it as an arcade"
                )
    assert "lumen-drift" not in wp, "individual game assets are not portfolio rows"
