"""Vetting catalog tests — network-free (site feed primed from a fixture,
catalog registry read from the committed JSON on disk or from tmp files)."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from botsite import app as app_module
from botsite import catalog
from botsite import data_source as ds

# Minimal site.json fixture so _base_ctx/lifespan never touch the network.
FIXTURE = {
    "meta": {"build": {"commit": "abcdef1234", "subject": "test build", "committed_at": "2026-07-09T00:00:00Z"}},
    "counts": {"commands": 0, "features": 0, "games": 0},
    "catalogue": [],
    "commands": [],
    "bot_changelog": [],
}

# The one live entry's Gumroad URL (live since 2026-07-12, OWNER-QUEUE §4).
SWTK_URL = "https://mennomagic01.gumroad.com/l/stripe-webhook-test-kit"

ALL_TITLES = (
    "Stripe Webhook Test Kit",
    "Membership-Site Boilerplate Kit",
    "Agent-Workflow Template Pack",
    "Agent Fleet Field Manual",
    "Kill-Rule Intake Kit",
    "The False-Green Test Trap",
    "The Agent Merge-Wall Cookbook",
    "The Slow Word",
    "The Weigh House",
    "Ultramarine",
    "De Waag",
    "Het trage woord",
    "De papieren sinaasappel",
    "Ship-It Bundle (Membership Kit + Template Pack)",
    "Photo Packs (Dutch Skies + Golden Hours)",
    "The Painted Stones",
    "The Marginalia Society",
    "The Night Kiln",
    "The Paper Orange",
    "The Pepper Ledger",
    "The Puddle Museum",
    "The Windmill Mouse",
)


def _entry(**overrides):
    base = {
        "slug": "ok", "title": "OK Title", "category": "adult / test fiction",
        "kind": "book", "price": "$1", "status": "parked",
        "status_note": "Parked for the test.", "url": None,
        "source": "venture-lab docs/publishing/vetting/ok.md @ 2c039e3",
        "as_of": "2026-07-13",
    }
    base.update(overrides)
    return base


@pytest.fixture()
def client():
    ds.clear_cache()
    ds.prime_cache(FIXTURE)
    ds.set_client(ds.make_client())  # never actually hit (cache is warm)
    with TestClient(app_module.app) as c:
        yield c
    ds.clear_cache()


def test_catalog_lists_every_vetted_title(client):
    r = client.get("/products/catalog")
    assert r.status_code == 200
    for title in ALL_TITLES:
        assert title in r.text, f"missing catalog title: {title}"


def test_catalog_hero_and_lede_state_what_the_page_is(client):
    """Clarity: hero container + headline + a lede saying what this is."""
    r = client.get("/products/catalog")
    assert r.status_code == 200
    assert 'class="sb-page-hero"' in r.text
    assert "<h1>Vetting Catalog</h1>" in r.text
    assert 'class="sb-lead"' in r.text
    assert "publishing pipeline" in r.text
    assert "owner" in r.text and "publish click" in r.text
    assert "Gumroad" in r.text


def test_catalog_status_groups_render(client):
    r = client.get("/products/catalog")
    assert r.status_code == 200
    assert "Live — purchasable now" in r.text
    assert "Publish-ready — awaiting the owner" in r.text
    assert "Hard-gated — blocked on components or assets" in r.text
    assert "Parked — vetted concept, blocking step flagged" in r.text


def test_catalog_exactly_the_live_entry_links_out_with_ref(client):
    """The one live entry renders a buy link with the attribution ref —
    and the only Gumroad href on the page is that entry's."""
    r = client.get("/products/catalog")
    assert r.status_code == 200
    assert f'href="{SWTK_URL}?ref=fleet-store"' in r.text
    assert r.text.count("gumroad.com") == 1
    assert r.text.count("Buy on Gumroad") == 1


def test_catalog_non_live_entries_carry_notes_not_buy_links(client):
    r = client.get("/products/catalog")
    assert r.status_code == 200
    # Honest notes from the packets' verdicts render.
    assert "Publish-ready up to the owner gate" in r.text
    assert "full-res originals are owner-held off-repo" in r.text
    assert "no manuscript" in r.text
    assert "illustration gate" in r.text


def test_catalog_provenance_lines_render(client):
    r = client.get("/products/catalog")
    assert r.status_code == 200
    assert "Curated from venture-lab docs/publishing/vetting/the-weigh-house.md @ 2c039e3, as of 2026-07-13" in r.text
    assert r.text.count("@ 2c039e3, as of 2026-07-13") == len(ALL_TITLES)


def test_products_page_links_to_the_catalog(client):
    r = client.get("/products")
    assert r.status_code == 200
    assert 'href="/products/catalog"' in r.text
    assert f"full vetting catalog — {len(ALL_TITLES)} titles" in r.text


def test_catalog_degrades_on_missing_file(client, monkeypatch, tmp_path):
    monkeypatch.setattr(catalog, "CATALOG_JSON_PATH", tmp_path / "does-not-exist.json")
    r = client.get("/products/catalog")
    assert r.status_code == 200
    assert "No catalog entries registered yet" in r.text


def test_catalog_degrades_on_corrupt_file(client, monkeypatch, tmp_path):
    corrupt = tmp_path / "catalog.json"
    corrupt.write_text("{ this is not json", encoding="utf-8")
    monkeypatch.setattr(catalog, "CATALOG_JSON_PATH", corrupt)
    r = client.get("/products/catalog")
    assert r.status_code == 200
    assert "No catalog entries registered yet" in r.text


def test_products_page_hides_catalog_stub_when_catalog_empty(client, monkeypatch, tmp_path):
    monkeypatch.setattr(catalog, "CATALOG_JSON_PATH", tmp_path / "does-not-exist.json")
    r = client.get("/products")
    assert r.status_code == 200
    assert 'href="/products/catalog"' not in r.text


def test_loader_skips_invalid_entries(tmp_path):
    """Entries missing required fields (or with bad enum values) are skipped, not fatal."""
    reg = tmp_path / "catalog.json"
    reg.write_text(json.dumps([
        _entry(slug="ok"),
        {k: v for k, v in _entry(slug="no-title").items() if k != "title"},
        _entry(slug="bad-status", status="vaporware"),
        _entry(slug="bad-kind", kind="hologram"),
        "not even a dict",
    ]), encoding="utf-8")
    got = catalog.load_catalog(reg)
    assert [e["slug"] for e in got] == ["ok"]


def test_loader_never_presents_live_without_url(tmp_path):
    reg = tmp_path / "catalog.json"
    reg.write_text(json.dumps([_entry(slug="claims-live", status="live", url=None)]), encoding="utf-8")
    (entry,) = catalog.load_catalog(reg)
    assert entry["is_live"] is False
    assert entry["has_link"] is False
    assert entry["link_url"] is None


def test_loader_adds_attribution_ref(tmp_path):
    reg = tmp_path / "catalog.json"
    reg.write_text(json.dumps([
        _entry(slug="really-live", status="live", url="https://example.com/buy"),
    ]), encoding="utf-8")
    (entry,) = catalog.load_catalog(reg)
    assert entry["is_live"] is True and entry["has_link"] is True
    assert entry["link_url"] == "https://example.com/buy?ref=fleet-store"


def test_group_by_status_orders_and_drops_empty_groups():
    entries = [
        _entry(slug="p", status="parked"),
        _entry(slug="r", status="publish-ready"),
        _entry(slug="r2", status="publish-ready"),
    ]
    groups = catalog.group_by_status(entries)
    assert [g["status"] for g in groups] == ["publish-ready", "parked"]
    assert [len(g["entries"]) for g in groups] == [2, 1]
    assert groups[0]["label"].startswith("Publish-ready")


def test_committed_registry_is_honest():
    """The committed catalog loads all 22 entries; exactly one is live (SWTK,
    with its Gumroad URL), every other entry carries no URL and an honest
    status note, statuses stay inside the small taxonomy, and every entry
    cites its venture-lab source at the pinned sha."""
    got = catalog.load_catalog()
    assert len(got) == 22
    assert len({e["slug"] for e in got}) == 22  # slugs unique
    live = [e for e in got if e["status"] == "live"]
    assert len(live) == 1
    (swtk,) = live
    assert swtk["slug"] == "stripe-webhook-test-kit"
    assert swtk["url"] == SWTK_URL
    assert swtk["is_live"] is True and swtk["has_link"] is True
    assert swtk["link_url"] == f"{SWTK_URL}?ref=fleet-store"
    by_status = {s: sum(1 for e in got if e["status"] == s) for s in catalog.STATUSES}
    assert by_status == {"live": 1, "publish-ready": 12, "hard-gated": 2, "parked": 7}
    for e in got:
        assert e["status"] in catalog.STATUSES
        assert e["kind"] in catalog.KINDS
        assert e["status_note"].strip()
        assert "venture-lab" in e["source"] and "@ 2c039e3" in e["source"]
        assert e["as_of"] == "2026-07-13"
        if e["status"] != "live":
            assert e["url"] is None
            assert e["has_link"] is False


# --------------------------------------------------------------------------- #
# blocker + ask_id — the shared schema (botsite/blockers.py, the arcade's
# PR #360 object extended to the catalog 2026-07-16). Optional and fail-soft
# everywhere: a malformed blocker costs only the panel, a malformed ask_id
# costs only the ledger ref — never the entry.
# --------------------------------------------------------------------------- #

# The write-slice parked titles: agent work (a missing manuscript), not owner
# actions — they must never carry a blocker.
WRITE_SLICE_SLUGS = (
    "the-marginalia-society", "the-night-kiln", "the-paper-orange",
    "the-pepper-ledger", "the-windmill-mouse",
)

# slug → the ledger ask id its committed blocker joins (docs/owner/
# OWNER-ACTIONS.md Open rows; cross-pinned repo-wide by tests/test_askverify.py).
EXPECTED_ASK_IDS = {
    "membership-kit": "ASK-0012",
    "template-packs": "ASK-0012",
    "agent-fleet-field-manual": "ASK-0012",
    "kill-rule-intake-kit": "ASK-0012",
    "false-green-test-trap": "ASK-0012",
    "merge-wall-cookbook": "ASK-0012",
    "the-slow-word": "ASK-0012",
    "the-weigh-house": "ASK-0012",
    "de-waag": "ASK-0012",
    "het-trage-woord": "ASK-0012",
    "bundle-starter": "ASK-0012",
    "photo-packs": "ASK-0013",
    "ultramarine": "ASK-0014",
    "the-painted-stones": "ASK-0015",
    "the-puddle-museum": "ASK-0015",
    "de-papieren-sinaasappel": "ASK-0016",
}


def test_loader_normalizes_valid_blocker(tmp_path):
    reg = tmp_path / "catalog.json"
    reg.write_text(json.dumps([
        _entry(blocker={"owner_action": "  click the thing  ",
                        "unblocks": " then it ships ",
                        "ask_id": "  ASK-0042  "}),
    ]), encoding="utf-8")
    (entry,) = catalog.load_catalog(reg)
    assert entry["blocker"] == {
        "owner_action": "click the thing", "unblocks": "then it ships",
        "ask_id": "ASK-0042",
    }


@pytest.mark.parametrize("blocker", [
    None,                                        # explicit null
    "just prose",                                # wrong type
    {"owner_action": "click"},                   # missing unblocks
    {"unblocks": "ships"},                       # missing owner_action
    {"owner_action": "", "unblocks": "ships"},   # empty owner_action
    {"owner_action": 42, "unblocks": "ships"},   # wrong value type
])
def test_loader_malformed_blocker_degrades_to_none(tmp_path, blocker):
    """A missing/malformed blocker is fail-soft: it normalizes to None and
    never invalidates the catalog entry (degrade, don't invent)."""
    reg = tmp_path / "catalog.json"
    reg.write_text(json.dumps([_entry(blocker=blocker)]), encoding="utf-8")
    (entry,) = catalog.load_catalog(reg)
    assert entry["slug"] == "ok"  # the entry survives
    assert entry["blocker"] is None


def test_loader_missing_blocker_is_none(tmp_path):
    reg = tmp_path / "catalog.json"
    reg.write_text(json.dumps([_entry()]), encoding="utf-8")
    (entry,) = catalog.load_catalog(reg)
    assert entry["blocker"] is None


@pytest.mark.parametrize("ask_id", [
    42, "", "   ", "ASK-42", "ASK-00100", "ask-0010",
    "see ASK-0010", "ASK-0010 maybe",
])
def test_loader_malformed_ask_id_degrades_to_none_but_keeps_blocker(tmp_path, ask_id):
    """A bad ``ask_id`` costs only the ledger ref — the blocker itself (the
    honest owner click + unblocks story) always survives (fail-soft)."""
    reg = tmp_path / "catalog.json"
    reg.write_text(json.dumps([
        _entry(blocker={"owner_action": "click", "unblocks": "ships",
                        "ask_id": ask_id}),
    ]), encoding="utf-8")
    (entry,) = catalog.load_catalog(reg)
    assert entry["blocker"] is not None
    assert entry["blocker"]["owner_action"] == "click"
    assert entry["blocker"]["ask_id"] is None


def test_committed_registry_blockers_join_the_ledger():
    """Every genuinely owner-gated committed entry carries a blocker with its
    ledger ask id; the live entry and the write-slice parked titles carry
    none (agent work, not owner actions)."""
    by_slug = {e["slug"]: e for e in catalog.load_catalog()}
    for slug, ask_id in EXPECTED_ASK_IDS.items():
        blocker = by_slug[slug]["blocker"]
        assert blocker is not None, slug
        assert blocker["owner_action"].strip(), slug
        assert blocker["unblocks"].strip(), slug
        assert blocker["ask_id"] == ask_id, slug
    assert by_slug["stripe-webhook-test-kit"]["blocker"] is None
    for slug in WRITE_SLICE_SLUGS:
        assert by_slug[slug]["blocker"] is None, slug


def test_catalog_page_renders_blocker_panels_with_ledger_refs(client):
    """Non-live entries with committed blockers render the panel: the owner
    click, how it unblocks, and the guarded ledger ref (one panel per
    blocker-carrying entry; the live entry and write-slice titles get none)."""
    r = client.get("/products/catalog")
    assert r.status_code == 200
    assert r.text.count("The owner click:") == len(EXPECTED_ASK_IDS)
    assert r.text.count("How it unblocks:") == len(EXPECTED_ASK_IDS)
    assert r.text.count("Ledger ref:") == len(EXPECTED_ASK_IDS)
    for ask_id in sorted(set(EXPECTED_ASK_IDS.values())):
        assert f"<code>{ask_id}</code>" in r.text, ask_id
    assert "owner-actions ledger" in r.text


def test_catalog_page_idless_blocker_renders_panel_without_ledger_ref(
    client, monkeypatch, tmp_path
):
    """An id-less blocker still renders its full panel — just no ledger ref
    line (the fallback path: the owner console then joins by signature)."""
    reg = tmp_path / "catalog.json"
    reg.write_text(json.dumps([
        _entry(blocker={"owner_action": "click the thing",
                        "unblocks": "then it ships"}),
    ]), encoding="utf-8")
    monkeypatch.setattr(catalog, "CATALOG_JSON_PATH", reg)
    r = client.get("/products/catalog")
    assert r.status_code == 200
    assert "The owner click:" in r.text
    assert "click the thing" in r.text
    assert "Ledger ref:" not in r.text
