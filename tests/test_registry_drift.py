"""Cross-registry drift guard: arcade.json vs web_presence.json.

The fleet records the same games in TWO independent registries —
``botsite/data/arcade.json`` (the Fleet Arcade) and ``app/data/web_presence.json``
(the control-plane /directory). Nothing structurally stops them from drifting:
the 2026-07-18 arcade flip (#428) left web_presence still marking Lumen Drift and
games-web ``pending-publish`` with ``url:null`` while arcade already listed them
reachable — a silent public-surface disagreement. This guard joins the two
registries on their SHARED product keys and fails the moment they disagree about
a game's reachability or its recorded URL, so a future one-sided edit is caught
the way ``test_askverify.py`` pins arcade blockers to the ledger.

Green now (both registries synced); red only on future drift.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import web_presence  # noqa: E402
from botsite import arcade  # noqa: E402

# Games recorded in BOTH registries under the same key (arcade slug == web
# presence id). Extend this map whenever a game is added to both surfaces.
SHARED_KEYS = ("lumen-drift", "games-web")


def _arcade_by_slug() -> dict:
    entries = json.loads(arcade.ARCADE_JSON_PATH.read_text(encoding="utf-8"))
    return {e["slug"]: e for e in entries if isinstance(e, dict) and e.get("slug")}


def _web_presence_by_id() -> dict:
    reg = json.loads(web_presence.REGISTRY_PATH.read_text(encoding="utf-8"))
    return {r["id"]: r for r in reg["sites"] if isinstance(r, dict) and r.get("id")}


def test_shared_registry_entries_do_not_drift():
    arc = _arcade_by_slug()
    wp = _web_presence_by_id()
    for key in SHARED_KEYS:
        assert key in arc, f"{key} missing from botsite/data/arcade.json"
        assert key in wp, f"{key} missing from app/data/web_presence.json"
        a, w = arc[key], wp[key]

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
            f"{key}: registries drifted — arcade reachable={arcade_reachable} "
            f"(availability={a.get('availability')!r}, url={a.get('url')!r}) but "
            f"web_presence published={wp_published} "
            f"(status={w.get('status')!r}, url={w.get('url')!r})"
        )

        # when both agree the game is live, the recorded URLs must match exactly —
        # the two public surfaces must send visitors to the SAME place.
        if arcade_reachable:
            assert a.get("url") == w.get("url"), (
                f"{key}: URL drift — arcade {a.get('url')!r} != "
                f"web_presence {w.get('url')!r}"
            )
