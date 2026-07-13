"""Agent-PR diagnostic tree page tests — network-free (site feed primed
from a fixture; tree data read from the committed JSON on disk or tmp
files). The honesty pins parse the committed JSON directly: every leaf must
render, every leaf must be cited, every option target must resolve, and the
verbatim production error strings must appear exactly as captured."""

from __future__ import annotations

import html
import json

import pytest
from fastapi.testclient import TestClient

from botsite import agent_pr_tree
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

# The verbatim Actions PR-creation refusal (docs/CAPABILITIES.md 2026-07-12
# wall entry) — the page's headline error, pinned exactly-once in the data.
ACTIONS_ERROR = (
    "GraphQL: GitHub Actions is not permitted to create or approve "
    "pull requests (createPullRequest)"
)

# A minimal VALID tree for degrade/loader tests to mutate.
MINI_TREE = {
    "meta": {"title": "t", "as_of": "2026-07-13", "sources": ["x@sha"]},
    "root": "q1",
    "nodes": [
        {"id": "q1", "question": "Q?", "options": [{"label": "a", "next": "l1"}]},
        {"id": "l1", "verdict": "v", "fix": "f", "sources": ["x@sha"]},
    ],
}


def _mini(**over):
    doc = json.loads(json.dumps(MINI_TREE))
    doc.update(over)
    return doc


@pytest.fixture()
def client():
    ds.clear_cache()
    ds.prime_cache(FIXTURE)
    ds.set_client(ds.make_client())  # never actually hit (cache is warm)
    with TestClient(app_module.app) as c:
        yield c
    ds.clear_cache()


# --------------------------------------------------------------------------- #
# The page, against the committed tree
# --------------------------------------------------------------------------- #
def test_page_renders_with_headline_and_lede(client):
    """Clarity: 200, hero h1, and a plain-words sb-lead purpose lede."""
    r = client.get("/agent-pr-check")
    assert r.status_code == 200
    assert "<h1>Can your agent land its own PR?</h1>" in r.text
    assert 'class="sb-lead"' in r.text
    assert "why your AI agent can't open" in html.unescape(r.text)
    assert "real production walls" in r.text


def test_nav_includes_pr_check(client):
    r = client.get("/")
    assert 'href="/agent-pr-check"' in r.text
    assert "PR Check" in r.text


def test_page_is_get_only_with_no_forms(client):
    r = client.get("/agent-pr-check")
    assert "<form" not in r.text.lower()
    assert client.post("/agent-pr-check").status_code == 405


def test_every_leaf_renders_with_verdict_fix_and_citation(client):
    """Honesty pin: every committed leaf renders on the page (verdict text
    present), and every leaf carries at least one source citation."""
    doc = agent_pr_tree.load_tree()
    assert doc["available"] is True
    text = html.unescape(client.get("/agent-pr-check").text)
    leaves = [n for n in doc["nodes"].values() if "question" not in n]
    assert leaves, "committed tree carries no leaves"
    for leaf in leaves:
        assert leaf["verdict"] in text, f"leaf '{leaf['id']}' verdict missing from the page"
        assert leaf["fix"] in text, f"leaf '{leaf['id']}' fix missing from the page"
        assert leaf["sources"], f"leaf '{leaf['id']}' carries no citation"
        for source in leaf["sources"]:
            assert source in text, f"leaf '{leaf['id']}' citation '{source}' missing from the page"
        if leaf.get("error"):
            assert leaf["error"] in text, f"leaf '{leaf['id']}' verbatim error missing from the page"


def test_every_question_renders_and_every_option_resolves(client):
    """Every question + option label renders; every option target resolves
    against the RAW committed JSON (not just the loader's view of it)."""
    raw = json.loads(agent_pr_tree.TREE_JSON_PATH.read_text(encoding="utf-8"))
    ids = {n["id"] for n in raw["nodes"]}
    assert raw["root"] in ids
    text = html.unescape(client.get("/agent-pr-check").text)
    for node in raw["nodes"]:
        if "question" not in node:
            continue
        assert node["question"] in text
        for opt in node["options"]:
            assert opt["next"] in ids, f"option target '{opt['next']}' does not resolve"
            assert opt["label"] in text


def test_actions_error_verbatim_and_exactly_once_in_the_data(client):
    """The headline Actions refusal is stored VERBATIM exactly once in the
    committed JSON, and renders on the page with its real characters."""
    raw_text = agent_pr_tree.TREE_JSON_PATH.read_text(encoding="utf-8")
    assert raw_text.count(ACTIONS_ERROR) == 1
    assert ACTIONS_ERROR in html.unescape(client.get("/agent-pr-check").text)


def test_session_403_error_renders_with_real_characters(client):
    """The session-gate 403 is a JSON body — it must render as real
    characters (quotes and braces), not as escape sequences."""
    text = html.unescape(client.get("/agent-pr-check").text)
    assert (
        '{"message":"GitHub access to this repository is not enabled for '
        'this session. Use add_repo to request access."}'
    ) in text


def test_tree_uses_native_details_disclosure_and_no_js_framework(client):
    r = client.get("/agent-pr-check")
    assert r.text.count("<details") >= 10  # nested question + option nodes
    assert "<script" not in r.text.replace(
        '<script src="/static/ds/ds.js"></script>', ""
    ).replace('<script src="/static/app.js"></script>', "").split("</head>", 1)[1]


def test_cookbook_cta_is_honest_coming_soon(client):
    """The Merge-Wall Cookbook CTA never invents availability: catalog.json
    says publish-ready with url null, so the page says coming soon, renders
    NO buy/checkout link, and points at /products instead."""
    entries = json.loads(catalog.CATALOG_JSON_PATH.read_text(encoding="utf-8"))
    cookbook = next(e for e in entries if e["slug"] == "merge-wall-cookbook")
    assert cookbook["status"] == "publish-ready"
    assert cookbook["url"] is None
    r = client.get("/agent-pr-check")
    text = html.unescape(r.text)
    assert "The Agent Merge-Wall Cookbook" in text
    assert "$19" in text
    assert "coming soon" in text
    assert "publish-ready" in text
    assert 'href="/products"' in r.text
    assert "gumroad" not in text.lower()  # no buy link exists for it
    assert "Buy —" not in text  # the buy button never renders while url is null


def test_provenance_footer_shows_sources_and_as_of(client):
    doc = agent_pr_tree.load_tree()
    text = html.unescape(client.get("/agent-pr-check").text)
    assert doc["meta"]["as_of"] in text
    assert "botsite/data/agent_pr_tree.json" in text
    for source in doc["meta"]["sources"]:
        assert source in text


# --------------------------------------------------------------------------- #
# Degrade branch — the page stays honest on bad data
# --------------------------------------------------------------------------- #
def test_page_degrades_on_missing_file(client, monkeypatch, tmp_path):
    monkeypatch.setattr(agent_pr_tree, "TREE_JSON_PATH", tmp_path / "does-not-exist.json")
    r = client.get("/agent-pr-check")
    assert r.status_code == 200
    assert "No diagnostic tree data" in r.text
    assert "is missing" in r.text
    assert "Nothing is faked here" in r.text
    assert 'class="sb-empty' in r.text


def test_page_degrades_on_corrupt_file(client, monkeypatch, tmp_path):
    corrupt = tmp_path / "agent_pr_tree.json"
    corrupt.write_text("{ this is not json", encoding="utf-8")
    monkeypatch.setattr(agent_pr_tree, "TREE_JSON_PATH", corrupt)
    r = client.get("/agent-pr-check")
    assert r.status_code == 200
    assert "not valid JSON" in r.text


def test_page_degrades_on_unresolvable_node_ref(client, monkeypatch, tmp_path):
    doc = _mini()
    doc["nodes"][0]["options"][0]["next"] = "ghost"
    bad = tmp_path / "agent_pr_tree.json"
    bad.write_text(json.dumps(doc), encoding="utf-8")
    monkeypatch.setattr(agent_pr_tree, "TREE_JSON_PATH", bad)
    r = client.get("/agent-pr-check")
    assert r.status_code == 200
    assert "No diagnostic tree data" in r.text
    assert "unknown node" in r.text


# --------------------------------------------------------------------------- #
# The loader
# --------------------------------------------------------------------------- #
def test_loader_missing_and_corrupt_files(tmp_path):
    got = agent_pr_tree.load_tree(tmp_path / "nope.json")
    assert got["available"] is False
    assert "missing" in got["reason"]
    bad = tmp_path / "tree.json"
    bad.write_text("[not json", encoding="utf-8")
    assert agent_pr_tree.load_tree(bad)["available"] is False
    bad.write_text("[1, 2, 3]", encoding="utf-8")
    assert "not a JSON object" in agent_pr_tree.load_tree(bad)["reason"]


def _load(tmp_path, doc):
    p = tmp_path / "tree.json"
    p.write_text(json.dumps(doc), encoding="utf-8")
    return agent_pr_tree.load_tree(p)


def test_loader_validates_meta_root_and_nodes(tmp_path):
    assert "meta" in _load(tmp_path, {"root": "x", "nodes": []})["reason"]
    assert "root" in _load(tmp_path, _mini(root=""))["reason"]
    got = _load(tmp_path, _mini(root="ghost"))
    assert "does not resolve" in got["reason"]
    doc = _mini()
    doc["nodes"].append(dict(doc["nodes"][1]))  # duplicate id
    assert "duplicate node id" in _load(tmp_path, doc)["reason"]


def test_loader_validates_leaves_are_cited(tmp_path):
    doc = _mini()
    doc["nodes"][1]["sources"] = []
    got = _load(tmp_path, doc)
    assert got["available"] is False
    assert "no source citations" in got["reason"]
    doc = _mini()
    del doc["nodes"][1]["fix"]
    assert "missing its 'fix'" in _load(tmp_path, doc)["reason"]


def test_loader_rejects_cycles(tmp_path):
    doc = _mini()
    doc["nodes"].append(
        {"id": "q2", "question": "Q2?", "options": [{"label": "b", "next": "q1"}]}
    )
    doc["nodes"][0]["options"].append({"label": "loop", "next": "q2"})
    got = _load(tmp_path, doc)
    assert got["available"] is False
    assert "cycle" in got["reason"]


def test_loader_accepts_the_minimal_valid_tree(tmp_path):
    got = _load(tmp_path, _mini())
    assert got["available"] is True
    assert got["question_count"] == 1
    assert got["leaf_count"] == 1
    assert got["root"] == "q1"


def test_committed_tree_parses_with_expected_shape():
    """The committed tree: available, root resolves, sane size, every node
    classified, and the counts hold (the page's eyebrow renders them)."""
    doc = agent_pr_tree.load_tree()
    assert doc["available"] is True
    assert doc["question_count"] >= 5
    assert 10 <= doc["leaf_count"] <= 14
    assert doc["question_count"] + doc["leaf_count"] == len(doc["nodes"])
    assert doc["meta"]["as_of"] == "2026-07-13"
    assert doc["meta"]["sources"]
    # Compact committed summary, never a dump.
    assert agent_pr_tree.TREE_JSON_PATH.stat().st_size < 50_000
