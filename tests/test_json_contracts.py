"""Same-shape contract pins for the four sibling machine endpoints:
/orders.json, /queue.json, /projects.json, /reviews.json.

Companion to ``tests/test_fleet_json_contract.py`` (the /fleet.json pin) —
same rule: any key added, removed, or renamed goes RED here BY NAME, so the
contract is changed consciously. Update the pinned sets in the SAME PR that
changes a payload, and say so in the PR body. Each endpoint is exercised on
a mocked happy path rich enough to reach every nested structure; rendered
HTML must never appear in a JSON payload (each pin asserts its absence).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import github  # noqa: E402
from app.main import app  # noqa: E402

# --- the pinned contracts ---------------------------------------------------

ORDERS_TOP = {"cards", "summary", "lane_source"}
ORDERS_CARD = {
    "repo", "inbox_url", "repo_url", "missing", "fetch_error",
    "status_readable", "orders",
    "open_count", "claimed_count", "done_count", "unknown_count",
}
ORDERS_ORDER = {  # per-order dict, body_html dropped in JSON
    "id", "issued", "inbox_status", "fields", "body",
    "state", "state_by", "claim_stale", "claim_age_human",
    "pickup_latency_mins", "pickup_latency_human",
}
ORDERS_SUMMARY = {
    "repos", "with_inbox", "open", "claimed", "done", "unknown",
    "errored", "stale_claims",
}

QUEUE_TOP = {
    "items", "lane_notes", "fleet_manager", "field_order", "summary",
    "unreadable_lanes", "lane_source",
}
QUEUE_ITEM = {"what", "text", "fields", "sources"}
QUEUE_SOURCE = {"kind", "label", "url", "updated_iso", "age_hours", "age_human"}
QUEUE_SUMMARY = {"total", "deduped", "lanes_with_asks", "lanes_total"}
QUEUE_FM = {  # _fleet_manager_half minus body_html
    "token_set", "url", "items", "preamble", "state", "reason",
}

PROJECTS_TOP = {"state", "reason", "token_set", "repo_url", "packages", "root_files"}
PROJECTS_PACKAGE = {  # per-package dict, meta_html dropped in JSON
    "name", "path", "github_url", "files", "error", "meta_error", "state",
}
PROJECTS_FILE = {"name", "path", "role", "label", "github_url"}

REVIEWS_TOP = {  # overview minus body_html
    "state", "reason", "token_set", "doc_url", "rows",
    "open_count", "reviewed_count", "findings_links",
}
REVIEWS_ROW = {
    "pr_repo", "pr_number", "pr_url", "pr_label", "what", "why",
    "status", "reviewed",
}
REVIEWS_LINK = {"label", "url"}

# --- mocked happy-path world -------------------------------------------------

_STATUS = (
    "# websites · status\nupdated: 2026-07-10T22:00Z\nhealth: green (ok)\n"
    "orders: acked=001-002 done=001 claimed-by: 002 lane 2026-07-10T21:07Z\n"
    "⚑ needs-owner: one ask.\n"
    "  ⚑ OWNER-ACTION\n"
    "  WHAT: Flip the switch.\n  WHERE: console.\n  HOW: click.\n"
    "  WHY-IT-MATTERS: contract test.\n  UNBLOCKS: this pin.\n"
    "  VERIFIED-NEEDED: owner-only.\n"
)
_INBOX = (
    "# websites · inbox\n\n"
    "## ORDER 001 · 2026-07-09T12:07Z · status: new\npriority: P1\ndo: a.\n"
    "## ORDER 002 · 2026-07-09T14:52Z · status: new\npriority: P1\ndo: b.\n"
)
_REVIEW_QUEUE = (
    "# Review queue\n\nSee ([`findings/x.md`](findings/x.md)).\n\n"
    "| PR | What to re-check | Why-risky | Drain path · status |\n"
    "|---|---|---|---|\n"
    "| websites#1 | thing | risk | codex · open |\n"
)
_META = "# pkg\n\ndeployed: live\n"


def _res(ok=True, status=200, data=None, error=""):
    return {"ok": ok, "status": status, "data": data, "error": error,
            "fetched_at": "", "cached": False, "url": ""}


def _mock_world(monkeypatch):
    async def fake_fetch(repo, path, ref="main", refresh=False):
        if path == "control/inbox.md" and repo == "websites":
            return _res(data=_INBOX)
        if path.startswith("control/status") and repo == "websites":
            return _res(data=_STATUS)
        if path == "docs/review-queue.md":
            return _res(data=_REVIEW_QUEUE)
        if path == "docs/owner-queue.md":
            return _res(data="prose only, no blocks\n")
        if path == "projects/websites/meta.md":
            return _res(data=_META)
        return _res(ok=False, status=404, data=None, error="nf")

    async def fake_api(repo, subpath="", refresh=False):
        if subpath.endswith("/contents/projects"):
            return _res(data=[
                {"type": "dir", "name": "websites", "path": "projects/websites"},
                {"type": "file", "name": "README.md", "path": "projects/README.md"},
            ])
        if subpath.endswith("/contents/projects/websites"):
            return _res(data=[
                {"type": "file", "path": "projects/websites/meta.md"},
                {"type": "file", "path": "projects/websites/setup.sh"},
            ])
        return _res(ok=False, status=404, data=None, error="nf")

    monkeypatch.setattr(github, "fetch_file", fake_fetch)
    monkeypatch.setattr(github, "repo_api", fake_api)


def _get(monkeypatch, url):
    _mock_world(monkeypatch)
    r = TestClient(app).get(url)
    assert r.status_code == 200
    return r.json()


def _drift(actual: set, pinned: set) -> str:
    return f"contract drift: {sorted(actual ^ pinned)}"


# --- the pins ----------------------------------------------------------------


def test_orders_json_shape(monkeypatch):
    d = _get(monkeypatch, "/orders.json")
    assert set(d) == ORDERS_TOP, _drift(set(d), ORDERS_TOP)
    assert set(d["summary"]) == ORDERS_SUMMARY, _drift(set(d["summary"]), ORDERS_SUMMARY)
    card = next(c for c in d["cards"] if c["repo"] == "websites")
    assert set(card) == ORDERS_CARD, _drift(set(card), ORDERS_CARD)
    assert card["orders"], "happy path must produce orders"
    for o in card["orders"]:
        assert set(o) == ORDERS_ORDER, _drift(set(o), ORDERS_ORDER)
        assert "body_html" not in o


def test_queue_json_shape(monkeypatch):
    d = _get(monkeypatch, "/queue.json")
    assert set(d) == QUEUE_TOP, _drift(set(d), QUEUE_TOP)
    assert set(d["summary"]) == QUEUE_SUMMARY, _drift(set(d["summary"]), QUEUE_SUMMARY)
    assert set(d["fleet_manager"]) == QUEUE_FM, _drift(set(d["fleet_manager"]), QUEUE_FM)
    assert "body_html" not in d["fleet_manager"]
    assert d["items"], "happy path must surface the filed ask"
    for item in d["items"]:
        assert set(item) == QUEUE_ITEM, _drift(set(item), QUEUE_ITEM)
        for src in item["sources"]:
            assert set(src) == QUEUE_SOURCE, _drift(set(src), QUEUE_SOURCE)


def test_projects_json_shape(monkeypatch):
    d = _get(monkeypatch, "/projects.json")
    assert set(d) == PROJECTS_TOP, _drift(set(d), PROJECTS_TOP)
    assert d["packages"], "happy path must produce a package"
    for pkg in d["packages"]:
        assert set(pkg) == PROJECTS_PACKAGE, _drift(set(pkg), PROJECTS_PACKAGE)
        assert "meta_html" not in pkg
        for f in pkg["files"]:
            assert set(f) == PROJECTS_FILE, _drift(set(f), PROJECTS_FILE)


def test_reviews_json_shape(monkeypatch):
    d = _get(monkeypatch, "/reviews.json")
    assert set(d) == REVIEWS_TOP, _drift(set(d), REVIEWS_TOP)
    assert "body_html" not in d
    assert d["rows"], "happy path must parse a row"
    for row in d["rows"]:
        assert set(row) == REVIEWS_ROW, _drift(set(row), REVIEWS_ROW)
    for link in d["findings_links"]:
        assert set(link) == REVIEWS_LINK, _drift(set(link), REVIEWS_LINK)
