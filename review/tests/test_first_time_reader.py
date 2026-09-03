"""Pins for the 2026-09-03 first-time-reader pass: the Story, Examples and
After pages, the grouped navigation, the honest tiles, and the promises the
site no longer makes.

The owner's ask (fleet-manager docs/prompts/2026-09-02-review-site-session.md):
"easy to navigate", "explains everything properly", "preferably with some
examples of how we want things to look" — including a mockup of the claude.ai
Projects overview with each Project's state visible, LABELLED as a mockup.
House rules pinned here: every fleet-manager citation is commit-pinned (never
``/blob/main/``), the mockup says it is a proposal with illustrative values,
the stat tiles no longer say "now running" or "standing" under a banner that
says the program ended, and the era note is on every page.

Zero network: the site renders from committed review/data/**.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from review import story  # noqa: E402
from review.app import NAV, app  # noqa: E402

client = TestClient(app)

NEW_PAGES = ["/story", "/examples", "/after"]
FM_PINNED = re.compile(r"https://github\.com/menno420/fleet-manager/blob/[0-9a-f]{40}/")


def _links(html: str) -> list[str]:
    return re.findall(r'href="([^"]+)"', html)


# --------------------------------------------------------------------------- #
# Navigation
# --------------------------------------------------------------------------- #
def test_nav_is_grouped_in_reading_order():
    groups = [entry[3] for entry in NAV]
    # groups are contiguous and in the intended order
    seen: list[str] = []
    for g in groups:
        if not seen or seen[-1] != g:
            seen.append(g)
    assert seen == ["Read first", "The record", "Questions"]
    assert [e[2] for e in NAV if e[3] == "Read first"] == ["/", "/story", "/examples", "/after"]


def test_every_page_renders_the_group_labels_and_new_links():
    for path in ["/", "/process", "/fleet", "/problems"] + NEW_PAGES:
        r = client.get(path)
        assert r.status_code == 200, path
        for label in ("Read first", "The record", "Questions"):
            assert label in r.text, (path, label)
        for href in NEW_PAGES:
            assert f'href="{href}"' in r.text, (path, href)


def test_site_map_names_every_nav_page():
    nav_hrefs = {e[2] for e in NAV}
    map_hrefs = {href for _, href, _ in story.site_map()}
    assert nav_hrefs == map_hrefs, nav_hrefs ^ map_hrefs
    r = client.get("/")
    for _, href, _ in story.site_map():
        assert f'href="{href}"' in r.text


# --------------------------------------------------------------------------- #
# The Overview no longer contradicts its own era note
# --------------------------------------------------------------------------- #
def test_overview_tiles_do_not_claim_anything_is_running():
    r = client.get("/")
    assert "now running" not in r.text
    assert "standing fleet seats" not in r.text
    assert "live services" not in r.text
    assert "generations, then the close" in r.text
    assert "this repository (websites) only" in r.text
    # the era note keeps its exact framing sentence, with its anchor
    assert "This is a record of a programme that ended." in r.text
    assert 'id="era"' in r.text
    # the reading path and the timeline strip
    for label, href, _ in story.READING_PATH:
        assert f'href="{href}"' in r.text, label
    assert "The fortnight at a glance" in r.text
    assert 'href="/process#glossary"' in r.text


def test_era_note_is_on_every_page_and_short_off_the_overview():
    for path in ["/process", "/fleet", "/problems", "/reviews", "/questions"] + NEW_PAGES:
        r = client.get(path)
        assert "A record of a programme that ended" in r.text, path
        assert 'href="/#era"' in r.text, path
        assert "This is a record of a programme that ended." not in r.text, path


# --------------------------------------------------------------------------- #
# Story
# --------------------------------------------------------------------------- #
def test_story_page_timeline_projects_and_ritual():
    r = client.get("/story")
    assert r.status_code == 200
    for t in story.STORY_TIMELINE:
        assert t["title"] in r.text, t["title"]
        assert t["evidence"], t["title"]
    # the eight Projects in the screen's order, joined to the committed mirror
    names = story.SCREEN_ORDER
    positions = [r.text.index(n) for n in names]
    assert positions == sorted(positions), "Projects not in the screen's order"
    assert "registry name: Fleet Manager" in r.text
    for step in story.PROJECT_RITUAL:
        assert step["step"] in r.text
    assert story.KEPT["quote"][:40] in r.text


def test_project_map_joins_the_mirror_and_degrades_honestly():
    rows = story.project_map({})
    assert rows == []
    rows = story.project_map(
        {"seats": [{"seat": "Fleet Manager", "role": "hub", "repos": [{"repo": "fleet-manager", "repo_url": "u"}]},
                   {"seat": "Websites", "role": "sites", "repos": []}]}
    )
    assert [x["screen_name"] for x in rows] == ["Project Manager", "Websites"]
    assert rows[0]["renamed"] and rows[0]["seat"] == "Fleet Manager"
    assert rows[0]["repos"][0]["repo"] == "fleet-manager"


# --------------------------------------------------------------------------- #
# Examples — labelled, and the mockup is a proposal
# --------------------------------------------------------------------------- #
def test_examples_page_labels_each_exemplar():
    r = client.get("/examples")
    assert r.status_code == 200
    assert r.text.count('class="rv-tag">Example</span>') == 3
    assert 'class="rv-tag rv-tag-mockup">Mockup</span>' in r.text
    assert 'id="projects-overview-mockup"' in r.text
    assert 'role="img"' not in r.text  # structured content stays readable (Codex #524 R1)
    assert "A proposal, not a screenshot." in r.text
    assert "illustrative value" in r.text
    assert "MOCKUP — proposal, illustrative values" in r.text
    # the eight names and the two Routines the screenshot showed
    for p in story.MOCKUP_PROJECTS:
        assert p["name"] in r.text
    for rt in story.MOCKUP_ROUTINES:
        assert rt["name"] in r.text
    for s in story.MOCKUP_STATES:
        assert s["label"] in r.text
    # the finding keeps its five-part shape and the card its eight fields
    for part in ("What was measured", "Evidence", "What it cost", "What would fix it"):
        assert part in r.text
    assert len(story.EXAMPLE_CARD["fields"]) == 8
    for f in story.EXAMPLE_CARD["fields"]:
        assert f["value"] and f["why"]


def test_mockup_project_names_match_the_screen_order():
    assert [p["name"] for p in story.MOCKUP_PROJECTS] == story.SCREEN_ORDER
    assert {p["state"] for p in story.MOCKUP_PROJECTS} == {s["key"] for s in story.MOCKUP_STATES}


# --------------------------------------------------------------------------- #
# After — provenance labelled
# --------------------------------------------------------------------------- #
def test_after_page_labels_provenance_per_section():
    r = client.get("/after")
    assert r.status_code == 200
    kinds = {s["kind"] for s in story.AFTER}
    assert kinds == {"OWNER", "DERIVED", "REVIEWED"}
    for s in story.AFTER:
        assert f'id="{s["id"]}"' in r.text
        assert s["evidence"], s["id"]
        assert s.get("quote") or s.get("text"), s["id"]
        # Codex #524 R1: a section that pairs an owner quote with session
        # prose labels the prose separately — never a DERIVED paragraph
        # under an OWNER heading badge.
        if s.get("quote") and s.get("text"):
            assert s.get("text_kind"), s["id"]
    assert r.text.count("rv-prov-owner") >= 5
    assert r.text.count("rv-prov-derived") >= 3


# --------------------------------------------------------------------------- #
# Citations: fleet-manager links are commit-pinned; problems/successes grew
# --------------------------------------------------------------------------- #
def test_fleet_manager_citations_are_commit_pinned_on_new_pages():
    for path in NEW_PAGES + ["/problems", "/successes"]:
        html = client.get(path).text
        for href in _links(html):
            if href.startswith("https://github.com/menno420/fleet-manager/blob/"):
                assert FM_PINNED.match(href), (path, href)
        assert "menno420/fleet-manager/blob/main/" not in html or path == "/fleet", path


def test_problems_carry_the_owners_three_and_keep_the_incident_first():
    ids = [p.get("id") for p in story.PROBLEMS]
    assert ids[0] == "incident-2026-07-12"
    assert ids[1:4] == ["coordinator-authority", "false-done", "stall-visibility"]
    r = client.get("/problems")
    for i in ids[1:4]:
        assert f'id="{i}"' in r.text
    # every new entry has all three narrative parts and evidence
    for p in story.PROBLEMS[1:4]:
        assert p["what"] and p["cost"] and p["fix"] and len(p["evidence"]) >= 3


def test_successes_carry_what_he_kept_first():
    assert story.SUCCESSES[0]["id"] == "kept"
    assert story.SUCCESSES[1]["id"] == "instruction-box"
    r = client.get("/successes")
    assert "What the owner kept, in his own words" in r.text


# --------------------------------------------------------------------------- #
# Promises the ended program cannot keep are gone from every page
# --------------------------------------------------------------------------- #
def test_no_page_promises_routing_on_the_bus():
    for path in ["/", "/questionnaire", "/questions", "/reviews", "/fleet/websites",
                 "/reviews/2026-07-11-edition-001"] + NEW_PAGES:
        html = client.get(path).text
        assert "routed to the fleet as an order" not in html, path
        assert "becomes an order on the bus" not in html, path
    # the glossary anchor the pages point at exists
    assert 'id="glossary"' in client.get("/process").text
    assert 'id="projects"' in client.get("/story").text
