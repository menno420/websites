"""Launch preflight verdicts (app/askverify.py) — read-only auto-verification
of the open ⚑ OWNER-ACTION asks.

Fully offline (the arcade_probe precedent: every network seam is
``github._get`` / ``railway.live_overview``, monkeypatched here — CI never
touches the network). tests/conftest.py pins GITHUB_TOKEN/RAILWAY_TOKEN to
the UNSET rung suite-wide, so the no-token honest-unknown tests hold by
default and token-armed tests opt in explicitly.

Coverage:

* matcher stability against the REAL committed docs/owner/OWNER-ACTIONS.md
  Open section (all 11 asks match, each a distinct registry entry);
* every live probe's full verdict ladder (done-detected / still-open /
  unknown), including the no-token rungs and the never-writes guarantee of
  the ORDER-020 PAT check;
* annotate(): unmatched-ask honesty, claim-once ambiguity, explicit
  not-machine-checkable registrations, fail-soft probe exceptions, rollup
  counts;
* wiring: public /queue never calls askverify and carries no chip markup
  (byte-identity pin), /owner/queue cards + /owner/briefing asks carry
  chips, the /owner board carries the rollup chip with its honest-unknown
  state.
"""

from __future__ import annotations

import asyncio
import base64
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import (  # noqa: E402
    askverify,
    briefing,
    config,
    github,
    owner_queue,
    railway,
    writeback,
)
from app.main import app  # noqa: E402

OWNER_PW = "test-owner-pw"
LEDGER_PATH = Path(__file__).resolve().parents[1] / "docs/owner/OWNER-ACTIONS.md"

BOTSITE_OWNER_URL = askverify._botsite_base() + "/testing/owner"


def _basic(pw: str = OWNER_PW, user: str = "owner") -> dict:
    token = base64.b64encode(f"{user}:{pw}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def _envelope(url, *, ok=False, status=0, data=None, error="offline test"):
    return {
        "ok": ok, "status": status, "data": data,
        "error": error, "fetched_at": "", "cached": False, "url": url,
    }


def _install_get(monkeypatch, responder):
    """Monkeypatch the ONE http seam every probe rides."""
    async def fake_get(url, refresh=False, raw=False):
        return responder(url)

    monkeypatch.setattr(github, "_get", fake_get)


def _run(coro):
    return asyncio.run(coro)


# --------------------------------------------------------------------------- #
# Matcher stability — the REAL committed ledger is the fixture
# --------------------------------------------------------------------------- #
def _open_ledger_blocks() -> list[dict]:
    text = LEDGER_PATH.read_text(encoding="utf-8")
    section, note = briefing.open_section(text)
    assert note == ""  # the ledger has its Open heading
    _pre, blocks = owner_queue.parse_owner_actions(section)
    return blocks


def _open_ledger_headlines() -> list[str]:
    return [b.get("what", "") for b in _open_ledger_blocks()]


def test_real_ledger_has_the_sixteen_open_asks_each_with_a_unique_id():
    # 9 from the 2026-07-16 id backfill + the 2 arcade launch blockers
    # (ASK-0010/0011) + the 5 registry blocker rows (ASK-0012..0016 — the
    # catalog / products / puddle-museum owner gates, same day).
    blocks = _open_ledger_blocks()
    assert len(blocks) == 16
    ids = [b.get("ask_id") for b in blocks]
    assert all(
        i and re.fullmatch(r"ASK-\d{4}", i) for i in ids
    ), f"open ask without a well-formed ID: {ids}"
    assert len(set(ids)) == 16, f"duplicated ask id in the ledger: {ids}"


def test_every_real_open_ask_matches_a_distinct_registry_entry():
    headlines = _open_ledger_headlines()
    ids = []
    for h in headlines:
        entry = askverify.match(h)
        assert entry is not None, f"unmatched real ask: {h[:80]!r}"
        ids.append(entry["id"])
    assert len(set(ids)) == len(ids), f"registry entry matched twice: {ids}"
    # ID-matching lands every ask on the SAME entry its signature chose —
    # the ids were assigned off the signature matcher's own mapping.
    for b in _open_ledger_blocks():
        by_sig = askverify.match(b["what"])
        by_id = askverify.match("", b["ask_id"])
        assert by_id is by_sig, (
            f"{b['ask_id']} lands on {by_id and by_id['id']!r}, signature "
            f"chose {by_sig and by_sig['id']!r}"
        )


def test_real_ledger_matches_land_on_the_intended_probes():
    by_id = {askverify.match(h)["id"]: h for h in _open_ledger_headlines()}
    assert set(by_id) == {
        "q-0004", "discord-oauth", "armed-service", "botsite-database-url",
        "paypal-credentials", "botsite-gate", "order-020-pat", "bake-pat",
        "dashboard-site-password", "lumen-drift-release",
        "product-forge-pages", "gumroad-publish-pass",
        "photo-packs-originals", "ultramarine-rename", "illustration-gate",
        "sinaasappel-proofread",
    }
    # Spot-check the two textually-overlapping PAT asks disambiguate.
    assert "BAKE_PAT" in by_id["bake-pat"]
    assert "BAKE_PAT" not in by_id["order-020-pat"]


def test_ledger_ids_are_never_reused_anywhere_in_the_file():
    """Uniqueness scan of the WHOLE committed ledger (Decided rows included):
    an ASK-NNNN id, once written, may appear on at most one ``ID:`` line."""
    text = LEDGER_PATH.read_text(encoding="utf-8")
    id_lines = re.findall(r"^ID:\s*(ASK-\d{4})\s*$", text, re.M)
    assert id_lines, "the ledger carries no ID: lines at all"
    dupes = {i for i in id_lines if id_lines.count(i) > 1}
    assert not dupes, f"ask id reused in the ledger: {sorted(dupes)}"


def test_registry_ask_ids_are_unique_and_well_formed():
    ids = [e["ask_id"] for e in askverify.REGISTRY if e.get("ask_id")]
    assert len(set(ids)) == len(ids), f"registry reuses an ask id: {ids}"
    assert all(re.fullmatch(r"ASK-\d{4}", i) for i in ids)
    # Every registry entry now has a ledger row (the two arcade blockers
    # gained theirs 2026-07-16 — ASK-0010/0011): none stay signature-only.
    assert not [
        e["id"] for e in askverify.REGISTRY if e.get("ask_id") is None
    ]


def test_registry_signatures_unique_and_probeless_entries_carry_reasons():
    """Registry well-formedness: no two entries share a signature tuple
    (a duplicate would make the fallback scan order-dependent), and every
    explicit not-machine-checkable registration (``probe=None``) carries a
    non-empty honest reason."""
    sigs = [tuple(e["signature"]) for e in askverify.REGISTRY]
    assert len(set(sigs)) == len(sigs), f"duplicated signature: {sigs}"
    for e in askverify.REGISTRY:
        assert e["signature"], f"{e['id']}: empty signature"
        if e["probe"] is None:
            assert e.get("reason", "").strip(), f"{e['id']}: no reason"


def test_match_unmatched_and_empty_are_none():
    assert askverify.match("Answer the briefing fixture question.") is None
    assert askverify.match("") is None
    assert askverify.match("   ") is None


def test_match_is_case_and_whitespace_insensitive():
    entry = askverify.match("set  SITE_PASSWORD   on the BOTSITE service")
    assert entry is not None and entry["id"] == "botsite-gate"


# --------------------------------------------------------------------------- #
# Stable ask IDs — exact-ID matching with honest signature fallback
# --------------------------------------------------------------------------- #
def test_id_exact_match_beats_signature():
    # The headline signature-matches botsite-gate, but the stable id says
    # dashboard-site-password — the id wins (rewording-proof by design).
    headline = "Set SITE_PASSWORD on the botsite service"
    assert askverify.match(headline)["id"] == "botsite-gate"
    entry = askverify.match(headline, "ASK-0009")
    assert entry is not None and entry["id"] == "dashboard-site-password"


def test_unknown_id_falls_back_to_signature():
    # A not-yet-registered new ask carrying a fresh id still matches
    # honestly on its keywords instead of vanishing.
    entry = askverify.match("store it as BAKE_PAT please", "ASK-9999")
    assert entry is not None and entry["id"] == "bake-pat"
    # ...and an unknown id over an unmatchable headline stays None.
    assert askverify.match("A brand new unmatched ask.", "ASK-9999") is None


def test_item_without_ask_id_keeps_the_signature_path_unchanged():
    headline = "Set SITE_PASSWORD on the botsite service"
    assert askverify.match(headline, None)["id"] == "botsite-gate"
    assert askverify.match(headline, "")["id"] == "botsite-gate"
    assert askverify.match(headline) is askverify.match(headline, None)


def test_annotate_matches_on_the_item_ask_id(monkeypatch):
    def responder(url):
        if url == BOTSITE_OWNER_URL:
            return _envelope(url, status=503)
        return _envelope(url)

    _install_get(monkeypatch, responder)
    items = [
        # Reworded beyond signature recognition, but carrying its id.
        {"what": "Completely reworded botsite password errand.",
         "ask_id": "ASK-0006"},
        # id-less item on the signature path, same pass.
        {"what": "Answer Q-0004 please."},
    ]
    rollup = _run(askverify.annotate(items))
    assert items[0]["verify"]["verdict"] == askverify.STILL_OPEN
    assert items[0]["verify"]["probe"] == "botsite-gate"
    assert items[1]["verify"]["verdict"] == askverify.NOT_CHECKABLE
    assert "Q-0004" in items[1]["verify"]["detail"]
    assert rollup["machine_verified"] == 1 and rollup["unmatched"] == 0


# --------------------------------------------------------------------------- #
# Arcade launch-blocker join — ask_id primary, signature fallback
# (the 2026-07-16 slice: botsite/data/arcade.json blockers ↔ ledger rows
# ASK-0010/0011 ↔ the two arcade probe entries, one id end to end).
# --------------------------------------------------------------------------- #
ARCADE_JSON = (
    Path(__file__).resolve().parents[1] / "botsite/data/arcade.json"
)


def _arcade_blocker_ask_ids() -> dict[str, str]:
    """slug → blocker ask_id from the committed arcade registry, read as
    plain JSON (no cross-service import — services never import each other's
    packages; the committed file IS the contract)."""
    import json

    games = json.loads(ARCADE_JSON.read_text(encoding="utf-8"))
    return {
        g["slug"]: g["blocker"]["ask_id"]
        for g in games
        if isinstance(g.get("blocker"), dict) and g["blocker"].get("ask_id")
    }


def test_arcade_blocker_joins_by_ask_id_even_when_the_signature_would_miss():
    """The primary join key is the id: an ask carrying ASK-0010 binds to the
    lumen-drift probe even when its headline has been reworded past every
    keyword the old brittle signature match needed."""
    reworded = "Publish the finished Game Boy Advance ROM's download release."
    assert askverify.match(reworded) is None  # the old key would mismatch
    entry = askverify.match(reworded, "ASK-0010")
    assert entry is not None and entry["id"] == "lumen-drift-release"
    entry = askverify.match("Flip the settings toggle.", "ASK-0011")
    assert entry is not None and entry["id"] == "product-forge-pages"


def test_arcade_blocker_idless_row_still_joins_via_signature_fallback():
    """A row with no ID (legacy block, lane copy) keeps the old matching
    logic: the keyword signature scan still lands it on the arcade probes."""
    entry = askverify.match("Publish the lumen-drift v1.3 release, please.")
    assert entry is not None and entry["id"] == "lumen-drift-release"
    entry = askverify.match(
        "In product-forge, configure GitHub Pages for games-web."
    )
    assert entry is not None and entry["id"] == "product-forge-pages"


def test_annotate_joins_the_arcade_asks_by_id_and_probes_them(monkeypatch):
    def responder(url):
        if "releases/tags/lumen-drift-v1.3" in url:
            return _envelope(url, status=404)  # release not published yet
        if url.endswith("/repos/menno420/product-forge/pages"):
            return _envelope(url, ok=True, status=200, error="",
                             data={"status": "built"})
        return _envelope(url)

    _install_get(monkeypatch, responder)
    items = [
        {"what": "Reworded ROM release errand.", "ask_id": "ASK-0010"},
        {"what": "Reworded Pages errand.", "ask_id": "ASK-0011"},
    ]
    rollup = _run(askverify.annotate(items))
    assert items[0]["verify"]["verdict"] == askverify.STILL_OPEN
    assert items[0]["verify"]["probe"] == "lumen-drift-release"
    assert items[1]["verify"]["verdict"] == askverify.DONE
    assert items[1]["verify"]["probe"] == "product-forge-pages"
    assert rollup["machine_verified"] == 2 and rollup["unmatched"] == 0


def test_committed_arcade_registry_ledger_and_probe_registry_agree():
    """The one-ledger-edit-flips-both-surfaces pin: each committed arcade
    blocker's ask_id (a) resolves by exact-ID to the registry entry whose
    probe machine-checks that very blocker, and (b) is a real row in the
    committed ledger's Open section."""
    ids = _arcade_blocker_ask_ids()
    assert ids == {"lumen-drift": "ASK-0010", "games-web": "ASK-0011"}
    expected_probe = {
        "lumen-drift": "lumen-drift-release",
        "games-web": "product-forge-pages",
    }
    for slug, ask_id in ids.items():
        entry = askverify.match("", ask_id)
        assert entry is not None, f"{slug}: {ask_id} hits no registry entry"
        assert entry["id"] == expected_probe[slug]
    ledger_ids = {b.get("ask_id") for b in _open_ledger_blocks()}
    for slug, ask_id in ids.items():
        assert ask_id in ledger_ids, (
            f"{slug}: {ask_id} is not an open ledger row"
        )


# --------------------------------------------------------------------------- #
# Cross-surface pin over ALL FOUR botsite registries (the 2026-07-16 registry
# blocker join: catalog.json / products.json / puddle_museum.json gained the
# arcade's optional blocker+ask_id object). Every committed blocker ask_id
# must be a real Open ledger row AND resolve by exact id to a registry entry
# — one ledger edit flips the public panel and the owner-console chip.
# --------------------------------------------------------------------------- #
DATA_DIR = Path(__file__).resolve().parents[1] / "botsite/data"

# The write-slice parked catalog titles: agent work (a missing manuscript),
# not owner actions — they must never carry a blocker or a ledger row.
WRITE_SLICE_SLUGS = {
    "the-marginalia-society", "the-night-kiln", "the-paper-orange",
    "the-pepper-ledger", "the-windmill-mouse",
}


def _all_registry_blocker_ask_ids() -> dict[tuple[str, str], str]:
    """(file, entry-key) → blocker ask_id across all four committed botsite
    registries, read as plain JSON (no cross-service import — services never
    import each other's packages; the committed files ARE the contract)."""
    import json

    found: dict[tuple[str, str], str] = {}

    def _collect(fname: str, entries, key: str):
        for e in entries:
            blocker = e.get("blocker")
            if isinstance(blocker, dict) and blocker.get("ask_id"):
                found[(fname, e[key])] = blocker["ask_id"]

    for fname, key in (
        ("arcade.json", "slug"),
        ("catalog.json", "slug"),
        ("products.json", "slug"),
    ):
        _collect(fname, json.loads(
            (DATA_DIR / fname).read_text(encoding="utf-8")
        ), key)
    museum = json.loads(
        (DATA_DIR / "puddle_museum.json").read_text(encoding="utf-8")
    )
    _collect("puddle_museum.json", museum.get("editions") or [], "lang")
    return found


def test_every_committed_registry_blocker_ask_id_is_an_open_ledger_row():
    found = _all_registry_blocker_ask_ids()
    assert found, "no blocker ask_ids found in any committed registry"
    ledger_ids = {b.get("ask_id") for b in _open_ledger_blocks()}
    for (fname, entry), ask_id in found.items():
        assert re.fullmatch(r"ASK-\d{4}", ask_id), (fname, entry, ask_id)
        assert ask_id in ledger_ids, (
            f"{fname}:{entry}: {ask_id} is not an open ledger row"
        )
        registry_entry = askverify.match("", ask_id)
        assert registry_entry is not None, (
            f"{fname}:{entry}: {ask_id} hits no askverify REGISTRY entry"
        )
        assert registry_entry["ask_id"] == ask_id


def test_committed_registries_join_the_expected_asks():
    """The exact committed mapping — the honest-blocker plan of record:
    the Gumroad publish pass (ASK-0012) covers the ten publish-ready
    catalog titles, their three fleet-store mirrors, and the component-
    gated bundle; the four remaining owner gates each carry their own row;
    the write-slice parked titles carry NO blocker at all."""
    import json

    found = _all_registry_blocker_ask_ids()
    gumroad_catalog = {
        "membership-kit", "template-packs", "agent-fleet-field-manual",
        "kill-rule-intake-kit", "false-green-test-trap",
        "merge-wall-cookbook", "the-slow-word", "the-weigh-house",
        "de-waag", "het-trage-woord", "bundle-starter",
    }
    for slug in gumroad_catalog:
        assert found[("catalog.json", slug)] == "ASK-0012", slug
    for slug in (
        "membership-site-boilerplate-kit", "agent-workflow-template-pack",
        "agent-fleet-field-manual",
    ):
        assert found[("products.json", slug)] == "ASK-0012", slug
    assert found[("catalog.json", "photo-packs")] == "ASK-0013"
    assert found[("catalog.json", "ultramarine")] == "ASK-0014"
    assert found[("catalog.json", "the-painted-stones")] == "ASK-0015"
    assert found[("catalog.json", "the-puddle-museum")] == "ASK-0015"
    for lang in ("en", "nl", "de"):
        assert found[("puddle_museum.json", lang)] == "ASK-0015", lang
    assert found[("catalog.json", "de-papieren-sinaasappel")] == "ASK-0016"
    # The write-slice parked titles carry no blocker (and the one live
    # catalog entry + live product don't either).
    catalog = json.loads(
        (DATA_DIR / "catalog.json").read_text(encoding="utf-8")
    )
    by_slug = {e["slug"]: e for e in catalog}
    for slug in WRITE_SLICE_SLUGS:
        assert "blocker" not in by_slug[slug], slug
    assert "blocker" not in by_slug["stripe-webhook-test-kit"]
    products = json.loads(
        (DATA_DIR / "products.json").read_text(encoding="utf-8")
    )
    (live_product,) = [p for p in products if p["availability"] == "live"]
    assert "blocker" not in live_product


def test_the_five_new_asks_are_honestly_probe_less():
    """ASK-0012..0016 are NOT machine-checkable (Gumroad state, off-repo
    files, product/money decisions): each registers with ``probe=None`` and
    a reason — never a fake probe, never a guessed verdict."""
    for ask_id in ("ASK-0012", "ASK-0013", "ASK-0014", "ASK-0015",
                   "ASK-0016"):
        entry = askverify.match("", ask_id)
        assert entry is not None, ask_id
        assert entry["probe"] is None, ask_id
        assert entry["reason"].strip(), ask_id


def test_parser_extracts_the_id_line():
    src = (
        "⚑ OWNER-ACTION\n"
        "ID: ASK-0042\n"
        "WHAT: Do the thing.\n"
        "WHERE: over there.\n"
    )
    _pre, blocks = owner_queue.parse_owner_actions(src)
    assert len(blocks) == 1
    assert blocks[0]["ask_id"] == "ASK-0042"
    assert blocks[0]["what"] == "Do the thing."
    # Flattened one-line lane copies carry the id too.
    flat = "⚑ OWNER-ACTION ID: ASK-0042 WHAT: Do the thing. WHERE: there."
    _pre, blocks = owner_queue.parse_owner_actions(flat)
    assert blocks[0]["ask_id"] == "ASK-0042"


def test_parser_is_absent_safe_for_legacy_blocks_without_an_id():
    src = "⚑ OWNER-ACTION\nWHAT: Legacy ask.\nWHERE: here.\n"
    _pre, blocks = owner_queue.parse_owner_actions(src)
    assert "ask_id" not in blocks[0]
    # An id MENTIONED in a field's prose never binds — only the header
    # region before the first field label is scanned.
    src = (
        "⚑ OWNER-ACTION\n"
        "WHAT: Legacy ask.\n"
        "HOW: extends the ID: ASK-0007 errand above.\n"
    )
    _pre, blocks = owner_queue.parse_owner_actions(src)
    assert "ask_id" not in blocks[0]


# --------------------------------------------------------------------------- #
# Probe ladders — botsite SITE_PASSWORD gate
# --------------------------------------------------------------------------- #
def test_botsite_probe_503_is_still_open(monkeypatch):
    _install_get(monkeypatch, lambda url: _envelope(url, status=503))
    v = _run(askverify.probe_botsite_site_password())
    assert v["verdict"] == askverify.STILL_OPEN
    assert "503" in v["detail"]
    assert v["url"] == BOTSITE_OWNER_URL


def test_botsite_probe_401_is_done_detected_with_pending_wording(monkeypatch):
    _install_get(monkeypatch, lambda url: _envelope(url, status=401))
    v = _run(askverify.probe_botsite_site_password())
    assert v["verdict"] == askverify.DONE
    assert "ledger update pending" in v["label"]
    assert v["css"] == "ok"


def test_botsite_probe_other_statuses_are_unknown(monkeypatch):
    for status in (0, 200, 404, 500):
        _install_get(
            monkeypatch, lambda url, s=status: _envelope(url, status=s)
        )
        v = _run(askverify.probe_botsite_site_password())
        assert v["verdict"] == askverify.UNKNOWN, status
        assert v["detail"]  # always says why


# --------------------------------------------------------------------------- #
# Probe ladders — BAKE_PAT Actions-secret name
# --------------------------------------------------------------------------- #
def test_bake_pat_no_token_is_unknown_by_default(monkeypatch):
    # conftest pins GITHUB_TOKEN unset — the probe must not even fetch.
    def boom(url):
        raise AssertionError("no fetch may happen without a token")

    _install_get(monkeypatch, boom)
    v = _run(askverify.probe_bake_pat_secret())
    assert v["verdict"] == askverify.UNKNOWN
    assert "GITHUB_TOKEN" in v["detail"]


def test_bake_pat_present_and_absent(monkeypatch):
    monkeypatch.setattr(config, "GITHUB_TOKEN", "tok")  # explicit opt-in
    _install_get(monkeypatch, lambda url: _envelope(
        url, ok=True, status=200, error="",
        data={"secrets": [{"name": "BAKE_PAT"}, {"name": "OTHER"}]},
    ))
    assert _run(askverify.probe_bake_pat_secret())["verdict"] == askverify.DONE
    _install_get(monkeypatch, lambda url: _envelope(
        url, ok=True, status=200, error="", data={"secrets": []},
    ))
    v = _run(askverify.probe_bake_pat_secret())
    assert v["verdict"] == askverify.STILL_OPEN


def test_bake_pat_scope_denied_is_unknown(monkeypatch):
    monkeypatch.setattr(config, "GITHUB_TOKEN", "tok")
    _install_get(monkeypatch, lambda url: _envelope(url, status=403))
    v = _run(askverify.probe_bake_pat_secret())
    assert v["verdict"] == askverify.UNKNOWN
    assert "admin scope" in v["detail"]


# --------------------------------------------------------------------------- #
# Probe ladders — ORDER-020 contents-write PAT (read-only, always)
# --------------------------------------------------------------------------- #
def test_order020_no_token_is_unknown_by_default(monkeypatch):
    def boom(url):
        raise AssertionError("no fetch may happen without a token")

    _install_get(monkeypatch, boom)
    v = _run(askverify.probe_order020_write_pat())
    assert v["verdict"] == askverify.UNKNOWN
    assert "GITHUB_TOKEN" in v["detail"]


def test_order020_permissions_ladder(monkeypatch):
    monkeypatch.setattr(config, "GITHUB_TOKEN", "tok")
    _install_get(monkeypatch, lambda url: _envelope(
        url, ok=True, status=200, error="",
        data={"permissions": {"push": True, "pull": True}},
    ))
    v = _run(askverify.probe_order020_write_pat())
    assert v["verdict"] == askverify.DONE
    assert "ledger update pending" in v["label"]
    _install_get(monkeypatch, lambda url: _envelope(
        url, ok=True, status=200, error="",
        data={"permissions": {"push": False, "pull": True}},
    ))
    assert (
        _run(askverify.probe_order020_write_pat())["verdict"]
        == askverify.STILL_OPEN
    )
    # No permissions object → honest unknown, never inferred.
    _install_get(monkeypatch, lambda url: _envelope(
        url, ok=True, status=200, error="", data={"name": "websites"},
    ))
    assert (
        _run(askverify.probe_order020_write_pat())["verdict"]
        == askverify.UNKNOWN
    )
    _install_get(monkeypatch, lambda url: _envelope(url, status=0))
    assert (
        _run(askverify.probe_order020_write_pat())["verdict"]
        == askverify.UNKNOWN
    )


def test_order020_probe_never_attempts_a_write(monkeypatch):
    """The hard rail: the PAT check is a GET of the repo payload only —
    api_post/api_request (the write paths) must never be touched."""
    monkeypatch.setattr(config, "GITHUB_TOKEN", "tok")

    async def no_post(*a, **k):
        raise AssertionError("askverify must never call a write path")

    monkeypatch.setattr(github, "api_post", no_post)
    monkeypatch.setattr(github, "api_request", no_post)
    seen: list[str] = []

    def responder(url):
        seen.append(url)
        return _envelope(url, ok=True, status=200, error="",
                         data={"permissions": {"push": True}})

    _install_get(monkeypatch, responder)
    v = _run(askverify.probe_order020_write_pat())
    assert v["verdict"] == askverify.DONE
    assert seen == [f"{config.GITHUB_API_BASE}/repos/menno420/websites"]


# --------------------------------------------------------------------------- #
# Probe ladders — dashboard SITE_PASSWORD deletion (Railway names-only)
# --------------------------------------------------------------------------- #
def _install_live(monkeypatch, payload):
    async def fake_live(refresh=False):
        return payload

    monkeypatch.setattr(railway, "live_overview", fake_live)


def test_dashboard_probe_no_railway_token_is_unknown_by_default(monkeypatch):
    _install_live(monkeypatch, {"state": "ok", "services": []})
    v = _run(askverify.probe_dashboard_site_password_gone())
    assert v["verdict"] == askverify.UNKNOWN
    assert "RAILWAY_TOKEN" in v["detail"]


def test_dashboard_probe_ladder_with_token(monkeypatch):
    monkeypatch.setattr(config, "RAILWAY_TOKEN", "tok")
    # still present → still-open
    _install_live(monkeypatch, {"state": "ok", "services": [
        {"name": "dashboard",
         "variable_names": ["PORT", "SITE_PASSWORD"], "error": ""},
    ]})
    v = _run(askverify.probe_dashboard_site_password_gone())
    assert v["verdict"] == askverify.STILL_OPEN
    # gone from a successful read → done-detected
    _install_live(monkeypatch, {"state": "ok", "services": [
        {"name": "dashboard", "variable_names": ["PORT"], "error": ""},
    ]})
    v = _run(askverify.probe_dashboard_site_password_gone())
    assert v["verdict"] == askverify.DONE
    # honest-unknown rungs: read failed / service absent / per-service error
    _install_live(monkeypatch, {"state": "unavailable", "reason": "boom"})
    assert (
        _run(askverify.probe_dashboard_site_password_gone())["verdict"]
        == askverify.UNKNOWN
    )
    _install_live(monkeypatch, {"state": "ok", "services": []})
    assert (
        _run(askverify.probe_dashboard_site_password_gone())["verdict"]
        == askverify.UNKNOWN
    )
    _install_live(monkeypatch, {"state": "ok", "services": [
        {"name": "dashboard", "variable_names": [], "error": "HTTP 500"},
    ]})
    assert (
        _run(askverify.probe_dashboard_site_password_gone())["verdict"]
        == askverify.UNKNOWN
    )


# --------------------------------------------------------------------------- #
# Probe ladders — arcade blockers (public reads)
# --------------------------------------------------------------------------- #
def test_lumen_drift_release_ladder(monkeypatch):
    _install_get(monkeypatch, lambda url: _envelope(
        url, ok=True, status=200, error="",
        data={"tag_name": "lumen-drift-v1.3", "html_url": "https://x/rel"},
    ))
    v = _run(askverify.probe_lumen_drift_release())
    assert v["verdict"] == askverify.DONE
    assert v["url"] == "https://x/rel"
    _install_get(monkeypatch, lambda url: _envelope(url, status=404))
    assert (
        _run(askverify.probe_lumen_drift_release())["verdict"]
        == askverify.STILL_OPEN
    )
    _install_get(monkeypatch, lambda url: _envelope(url, status=0))
    assert (
        _run(askverify.probe_lumen_drift_release())["verdict"]
        == askverify.UNKNOWN
    )


def test_product_forge_pages_ladder(monkeypatch):
    _install_get(monkeypatch, lambda url: _envelope(
        url, ok=True, status=200, error="", data={"status": "built"},
    ))
    assert (
        _run(askverify.probe_product_forge_pages())["verdict"]
        == askverify.DONE
    )
    _install_get(monkeypatch, lambda url: _envelope(url, status=404))
    assert (
        _run(askverify.probe_product_forge_pages())["verdict"]
        == askverify.STILL_OPEN
    )
    _install_get(monkeypatch, lambda url: _envelope(url, status=403))
    v = _run(askverify.probe_product_forge_pages())
    assert v["verdict"] == askverify.UNKNOWN
    assert "unreadable" in v["detail"]


# --------------------------------------------------------------------------- #
# annotate() — honesty semantics + rollup
# --------------------------------------------------------------------------- #
def test_annotate_unmatched_ask_stays_honestly_unverified(monkeypatch):
    items = [{"what": "A brand new ask nothing matches."}]
    rollup = _run(askverify.annotate(items))
    v = items[0]["verify"]
    assert v["verdict"] == askverify.NOT_CHECKABLE
    assert "no registered probe matches" in v["detail"]
    assert rollup == {
        "total": 1, "machine_verified": 0, "done": 0, "still_open": 0,
        "not_checkable": 1, "unknown": 0, "unmatched": 1, "auto_cleared": 0,
    }
    assert items[0]["auto_cleared"] is False  # nothing positively resolved


def test_annotate_not_checkable_registrations_carry_their_reason():
    items = [
        {"what": "Answer Q-0004 — decide WHERE live bot control lives."},
        {"what": "Set up PayPal Payouts for the tester program."},
    ]
    rollup = _run(askverify.annotate(items))
    assert items[0]["verify"]["verdict"] == askverify.NOT_CHECKABLE
    assert "Q-0004" in items[0]["verify"]["detail"]
    assert items[1]["verify"]["verdict"] == askverify.NOT_CHECKABLE
    assert "never be probed" in items[1]["verify"]["detail"]
    assert rollup["not_checkable"] == 2
    assert rollup["machine_verified"] == 0
    assert rollup["unmatched"] == 0


def test_annotate_claim_once_second_match_is_ambiguous_never_a_verdict():
    items = [
        {"what": "Set up PayPal Payouts for the tester program."},
        {"what": "Another paypal-flavoured duplicate ask."},
    ]
    _run(askverify.annotate(items))
    assert "never be probed" in items[0]["verify"]["detail"]
    v = items[1]["verify"]
    assert v["verdict"] == askverify.NOT_CHECKABLE
    assert v["detail"] == askverify.AMBIGUOUS_REASON


def test_annotate_probe_exception_is_honest_unknown(monkeypatch):
    async def boom(refresh):
        raise RuntimeError("kaboom")

    monkeypatch.setitem(askverify.REGISTRY[0], "probe", boom)
    items = [{"what": "store it as BAKE_PAT."}]
    rollup = _run(askverify.annotate(items))
    v = items[0]["verify"]
    assert v["verdict"] == askverify.UNKNOWN
    assert "probe error" in v["detail"] and "kaboom" in v["detail"]
    assert rollup["unknown"] == 1 and rollup["machine_verified"] == 0


def test_annotate_rollup_counts_mixed_verdicts(monkeypatch):
    def responder(url):
        if url == BOTSITE_OWNER_URL:
            return _envelope(url, status=401)  # done-detected
        if "lumen-drift" in url:
            return _envelope(url, status=404)  # still-open
        return _envelope(url)

    _install_get(monkeypatch, responder)
    items = [
        {"what": "Set SITE_PASSWORD on the botsite Railway service."},
        {"what": "Publish the lumen-drift release."},
        {"what": "Answer Q-0004 please."},
        {"what": "Totally unmatched ask."},
    ]
    rollup = _run(askverify.annotate(items))
    assert rollup == {
        "total": 4, "machine_verified": 2, "done": 1, "still_open": 1,
        "not_checkable": 2, "unknown": 0, "unmatched": 1, "auto_cleared": 1,
    }
    assert items[0]["verify"]["verdict"] == askverify.DONE
    assert items[1]["verify"]["verdict"] == askverify.STILL_OPEN
    # Only the done-detected ask is flagged for self-cleaning; the still-open,
    # not-checkable and unmatched asks all stay active.
    assert items[0]["auto_cleared"] is True
    assert [it["auto_cleared"] for it in items] == [True, False, False, False]


# --------------------------------------------------------------------------- #
# C14 self-cleaning owner queue — an ask auto-clears ONLY on a positive
# done-detected signal; every ambiguous / failed / still-open state keeps it.
# --------------------------------------------------------------------------- #
def test_self_cleaning_positive_done_auto_clears(monkeypatch):
    """(a) A probe that POSITIVELY confirms the condition resolved
    (done-detected) flags the ask auto_cleared and splits it into the
    cleared list."""
    _install_get(monkeypatch, lambda url: _envelope(url, status=401))  # DONE
    items = [{"what": "Set SITE_PASSWORD on the botsite Railway service."}]
    rollup = _run(askverify.annotate(items))
    assert items[0]["verify"]["verdict"] == askverify.DONE
    assert items[0]["auto_cleared"] is True
    assert rollup["auto_cleared"] == 1
    active, cleared = askverify.split_self_cleaned(items)
    assert active == [] and cleared == [items[0]]


def test_self_cleaning_still_open_ask_stays(monkeypatch):
    """(b) A probe that positively observes the NOT-done state (still-open)
    never clears — the ask stays in the active queue."""
    _install_get(monkeypatch, lambda url: _envelope(url, status=503))  # STILL_OPEN
    items = [{"what": "Set SITE_PASSWORD on the botsite Railway service."}]
    rollup = _run(askverify.annotate(items))
    assert items[0]["verify"]["verdict"] == askverify.STILL_OPEN
    assert items[0]["auto_cleared"] is False
    assert rollup["auto_cleared"] == 0
    active, cleared = askverify.split_self_cleaned(items)
    assert active == [items[0]] and cleared == []


def test_self_cleaning_fetch_error_keeps_the_ask(monkeypatch):
    """(c, load-bearing) A fetch failure / unreachable source is an honest
    unknown — the ask MUST stay. A real owner request never vanishes because
    a check could not complete."""
    # status 0 / offline envelope → the botsite probe's honest-unknown rung.
    _install_get(monkeypatch, lambda url: _envelope(url, status=0))
    items = [{"what": "Set SITE_PASSWORD on the botsite Railway service."}]
    rollup = _run(askverify.annotate(items))
    assert items[0]["verify"]["verdict"] == askverify.UNKNOWN
    assert items[0]["auto_cleared"] is False
    assert rollup["auto_cleared"] == 0 and rollup["unknown"] == 1
    active, cleared = askverify.split_self_cleaned(items)
    assert active == [items[0]] and cleared == []


def test_self_cleaning_raised_probe_exception_keeps_the_ask(monkeypatch):
    """(c, load-bearing) A probe that RAISES is fail-soft to unknown — never
    a crash, and above all never a silent auto-clear."""
    async def boom(refresh):
        raise RuntimeError("kaboom")

    monkeypatch.setitem(askverify.REGISTRY[0], "probe", boom)
    items = [{"what": "store it as BAKE_PAT."}]
    rollup = _run(askverify.annotate(items))
    assert items[0]["verify"]["verdict"] == askverify.UNKNOWN
    assert items[0]["auto_cleared"] is False
    assert rollup["auto_cleared"] == 0
    active, cleared = askverify.split_self_cleaned(items)
    assert active == [items[0]] and cleared == []


def test_self_cleaning_ambiguous_and_not_checkable_stay(monkeypatch):
    """The ambiguous claim-once collision and every not-machine-checkable
    registration also stay active — only a positive done clears."""
    items = [
        {"what": "Set up PayPal Payouts for the tester program."},
        {"what": "Another paypal-flavoured duplicate ask."},   # ambiguous
        {"what": "Answer Q-0004 please."},                     # not-checkable
    ]
    rollup = _run(askverify.annotate(items))
    assert rollup["auto_cleared"] == 0
    assert all(it["auto_cleared"] is False for it in items)
    active, cleared = askverify.split_self_cleaned(items)
    assert cleared == [] and active == items


def test_split_self_cleaned_preserves_order_and_partitions(monkeypatch):
    """The split is order-preserving: cleared asks come out in their original
    order, and active + cleared together reconstruct the input."""
    def responder(url):
        if url == BOTSITE_OWNER_URL:
            return _envelope(url, status=401)   # done → cleared
        if "lumen-drift" in url:
            return _envelope(url, status=404)   # still-open → active
        return _envelope(url)

    _install_get(monkeypatch, responder)
    items = [
        {"what": "Publish the lumen-drift release."},                 # active
        {"what": "Set SITE_PASSWORD on the botsite Railway service."},  # cleared
        {"what": "Answer Q-0004 please."},                            # active
    ]
    _run(askverify.annotate(items))
    active, cleared = askverify.split_self_cleaned(items)
    assert cleared == [items[1]]
    assert active == [items[0], items[2]]
    assert len(active) + len(cleared) == len(items)


def test_split_self_cleaned_treats_unannotated_items_as_active():
    """An item never passed through annotate (no auto_cleared key) is treated
    as active — the split never fabricates a clear."""
    items = [{"what": "raw ask, never annotated"}]
    active, cleared = askverify.split_self_cleaned(items)
    assert active == items and cleared == []


# --------------------------------------------------------------------------- #
# Wiring — public /queue stays chip-free and never calls askverify
# --------------------------------------------------------------------------- #
def _offline_client(monkeypatch, tmp_path, responder=None):
    monkeypatch.setattr(config, "SITE_PASSWORD", OWNER_PW)
    monkeypatch.setenv(writeback.ENV_DB_PATH, str(tmp_path / "wb.sqlite3"))
    _install_get(monkeypatch, responder or (lambda url: _envelope(url)))
    return TestClient(app)


def test_public_queue_never_calls_askverify_and_carries_no_chips(
    monkeypatch, tmp_path
):
    async def forbidden(items, refresh=False):
        raise AssertionError(
            "the PUBLIC /queue must never run preflight probes"
        )

    monkeypatch.setattr(askverify, "annotate", forbidden)
    with _offline_client(monkeypatch, tmp_path) as c:
        r = c.get("/queue")
        assert r.status_code == 200
        assert "preflight" not in r.text
        assert "machine-verified" not in r.text
        rj = c.get("/queue.json")
        assert rj.status_code == 200
        assert "verify" not in rj.json()


def test_owner_queue_renders_the_verdict_chip(monkeypatch, tmp_path):
    async def fake_overview(refresh=False):
        return {
            "items": [{
                "what": (
                    "Set SITE_PASSWORD on the botsite Railway service so "
                    "the tester-program owner queue becomes reachable."
                ),
                "text": "",
                "fields": {},
                "sources": [{
                    "kind": "lane", "label": "websites", "url": "https://x",
                    "updated_iso": "", "age_hours": 1.0, "age_human": "1h ago",
                }],
            }],
            "lane_notes": [],
            "fleet_manager": {"state": "ok", "reason": "", "items": [],
                              "preamble": "", "body_html": "",
                              "token_set": False, "url": ""},
            "field_order": owner_queue.FIELD_ORDER,
            "summary": {"total": 1, "deduped": 0, "lanes_with_asks": 1,
                        "lanes_total": 1},
            "unreadable_lanes": [],
            "lane_source": {},
        }

    monkeypatch.setattr(owner_queue, "overview", fake_overview)

    def responder(url):
        if url == BOTSITE_OWNER_URL:
            return _envelope(url, status=503)
        return _envelope(url)

    with _offline_client(monkeypatch, tmp_path, responder) as c:
        r = c.get("/owner/queue", headers=_basic())
        assert r.status_code == 200
        assert "preflight: still-open" in r.text
        assert "SITE_PASSWORD unset" in r.text
        assert "1 of 1 machine-verified" in r.text
        # A still-open ask stays in the active list, never self-cleaned.
        assert "self-cleaned this pass" not in r.text


def test_owner_queue_self_cleans_a_resolved_ask(monkeypatch, tmp_path):
    """C14 wiring: on the GATED /owner/queue, an ask whose condition is
    POSITIVELY re-verified resolved (done-detected) moves into the
    self-cleaned section, while a still-open ask stays in the active list."""
    async def fake_overview(refresh=False):
        def _ask(what):
            return {
                "what": what, "text": "", "fields": {},
                "sources": [{
                    "kind": "lane", "label": "websites", "url": "https://x",
                    "updated_iso": "", "age_hours": 1.0, "age_human": "1h ago",
                }],
            }

        return {
            "items": [
                _ask("Set SITE_PASSWORD on the botsite Railway service."),
                _ask("Publish the lumen-drift v1.3 release."),
            ],
            "lane_notes": [],
            "fleet_manager": {"state": "ok", "reason": "", "items": [],
                              "preamble": "", "body_html": "",
                              "token_set": False, "url": ""},
            "field_order": owner_queue.FIELD_ORDER,
            "summary": {"total": 2, "deduped": 0, "lanes_with_asks": 1,
                        "lanes_total": 1},
            "unreadable_lanes": [],
            "lane_source": {},
        }

    monkeypatch.setattr(owner_queue, "overview", fake_overview)

    def responder(url):
        if url == BOTSITE_OWNER_URL:
            return _envelope(url, status=401)   # done → self-cleaned
        if "lumen-drift" in url:
            return _envelope(url, status=404)   # still-open → stays active
        return _envelope(url)

    with _offline_client(monkeypatch, tmp_path, responder) as c:
        r = c.get("/owner/queue", headers=_basic())
        assert r.status_code == 200
        # The resolved botsite ask cleared into its own section.
        assert "self-cleaned this pass" in r.text
        assert "1 self-cleaned" in r.text
        assert "done-detected — ledger update pending" in r.text
        # The still-open lumen-drift ask stayed in the active list.
        assert "preflight: still-open" in r.text
        assert "2 of 2 machine-verified" in r.text


def test_owner_briefing_asks_carry_verdict_chips(monkeypatch, tmp_path):
    ledger = (
        "# Owner actions\n\n"
        "## 🟡 Open — waiting on the owner\n\n"
        "⚑ OWNER-ACTION\n"
        "WHAT: Set SITE_PASSWORD on the botsite Railway service.\n"
        "WHERE: railway.\n\n"
        "⚑ OWNER-ACTION\n"
        "WHAT: A fixture ask no probe matches.\n"
        "WHERE: nowhere.\n\n"
        "## 🟢 Decided / resolved\n"
    )

    def responder(url):
        if "OWNER-ACTIONS.md" in url:
            return _envelope(url, ok=True, status=200, error="", data=ledger)
        if url == BOTSITE_OWNER_URL:
            return _envelope(url, status=401)
        return _envelope(url)

    with _offline_client(monkeypatch, tmp_path, responder) as c:
        r = c.get("/owner/briefing", headers=_basic())
        assert r.status_code == 200
        assert "preflight verdict" in r.text
        assert "done-detected — ledger update pending" in r.text
        assert "no registered probe matches" in r.text
        assert "1 of 2 machine-verified" in r.text


def test_owner_board_rollup_chip_counts_and_honest_unknown(
    monkeypatch, tmp_path
):
    # Offline ledger → the chip is the honest unknown, nothing assumed done.
    with _offline_client(monkeypatch, tmp_path) as c:
        r = c.get("/owner", headers=_basic())
        assert r.status_code == 200
        assert "asks: preflight verdicts unknown" in r.text
        assert "machine-verified" not in r.text

    ledger = (
        "## 🟡 Open — waiting on the owner\n\n"
        "⚑ OWNER-ACTION\n"
        "WHAT: Set SITE_PASSWORD on the botsite Railway service.\n\n"
        "⚑ OWNER-ACTION\n"
        "WHAT: Set up PayPal Payouts.\n\n"
        "## 🟢 Decided / resolved\n"
    )

    def responder(url):
        if "OWNER-ACTIONS.md" in url:
            return _envelope(url, ok=True, status=200, error="", data=ledger)
        if url == BOTSITE_OWNER_URL:
            return _envelope(url, status=503)
        return _envelope(url)

    with _offline_client(monkeypatch, tmp_path, responder) as c:
        r = c.get("/owner", headers=_basic())
        assert r.status_code == 200
        assert "1 of 2 machine-verified" in r.text
        assert "still-open" in r.text
        assert "not machine-checkable" in r.text


def test_briefing_asks_unknown_state_has_no_verify_rollup(monkeypatch):
    _install_get(monkeypatch, lambda url: _envelope(url))

    data = _run(briefing.asks())
    assert data["state"] == "unknown"
    assert data["verify"] is None
