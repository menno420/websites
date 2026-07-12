"""Offline tests for the list-page IA pass (control-plane UX, 2026-07-12):
every long-list page opens with a summary header — counts by the page's
natural group plus jump-to anchor links — and its default view renders in
sections (done/settled material collapsed) instead of one flat wall.
The moment the owner picks an explicit filter/sort/search, the sectioning
steps aside and the flat ORDER 019 behavior renders exactly as before.

Also pins the /owner nav fix that rode along: app/owner.py renders base.html
through its own Jinja env, which previously lacked the NAV_* globals — the
owner pages served an EMPTY header nav.

Fixture style mirrors tests/test_queue_filters.py / test_orders_filters.py
(offline TestClient, monkeypatched github layer, frozen clock).
"""

import base64
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import activity, clock, config, github, ideas, nav, owner_queue  # noqa: E402
from app.main import app  # noqa: E402

NOW = datetime(2026, 7, 10, 12, 0, 0, tzinfo=timezone.utc)


def _res(ok=True, status=200, data=None, error=""):
    return {"ok": ok, "status": status, "data": data, "error": error,
            "fetched_at": "", "cached": False, "url": ""}


# --------------------------------------------------------------------------- #
# /queue — age sections + attention strip on the default view only
# --------------------------------------------------------------------------- #

_Q_FRESH = (  # websites — 10h before NOW -> <24h bucket
    "# websites · status\n"
    "updated: 2026-07-10T02:00Z\n"
    "health: green (ok)\n"
    "⚑ needs-owner:\n"
    "  ⚑ OWNER-ACTION\n"
    "  WHAT: Mint the control-plane PAT.\n"
    "  WHERE: github.com settings\n"
    "notes: n\n"
)
_Q_WEEK = (  # superbot-next — 24h -> 1-7d bucket
    "# superbot-next · status\n"
    "updated: 2026-07-09T12:00Z\n"
    "health: green (ok)\n"
    "⚑ needs-owner: decide the plugin cutover window\n"
    "notes: n\n"
)
_Q_OLD = (  # substrate-kit — 20 days -> >7d bucket (the attention strip)
    "# substrate-kit · status\n"
    "updated: 2026-06-20T12:00Z\n"
    "health: green (ok)\n"
    "⚑ needs-owner: approve the kit re-render budget\n"
    "notes: n\n"
)


def _queue_world(monkeypatch):
    monkeypatch.setattr(clock, "NOW_OVERRIDE", NOW)
    monkeypatch.setattr(config, "GITHUB_TOKEN", "tok")
    bodies = {
        "websites": _Q_FRESH,
        "superbot-next": _Q_WEEK,
        "substrate-kit": _Q_OLD,
    }

    async def fake_fetch(repo, path, ref="main", refresh=False):
        if repo in bodies and path == "control/status.md":
            return _res(data=bodies[repo])
        return _res(ok=False, status=404, data=None, error="nf")

    async def fake_repo_api(repo, subpath="", refresh=False):
        return _res(ok=False, status=404, data=None, error="nf")

    monkeypatch.setattr(github, "fetch_file", fake_fetch)
    monkeypatch.setattr(github, "repo_api", fake_repo_api)


def test_group_by_age_partitions_in_fixed_order():
    def item(age):
        return {"sources": [{"age_hours": age}]}

    groups = owner_queue.group_by_age(
        [item(5.0), item(30.0), item(400.0), item(None)]
    )
    assert [g["key"] for g in groups] == ["<24h", "1-7d", ">7d", "undated"]
    assert [g["anchor"] for g in groups] == [
        "age-fresh", "age-week", "age-old", "age-undated"]
    assert all(len(g["items"]) == 1 for g in groups)
    # empty buckets are omitted, order preserved within a bucket
    only_fresh = owner_queue.group_by_age([item(1.0), item(2.0)])
    assert [g["key"] for g in only_fresh] == ["<24h"]
    assert len(only_fresh[0]["items"]) == 2


def test_queue_default_view_has_summary_header_and_age_sections(monkeypatch):
    _queue_world(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/queue")
    assert r.status_code == 200
    # summary header: jump links target the age sections
    assert "jump to:" in r.text
    for anchor in ("age-fresh", "age-week", "age-old"):
        assert f'href="#{anchor}"' in r.text
        assert f'id="{anchor}"' in r.text
    # section labels + counts render
    assert "last 24 hours" in r.text and "older than 7 days" in r.text
    # the >7d ask raises the needs-attention strip
    assert "needs attention" in r.text and "more than 7 days" in r.text
    # every item still present, in its section
    assert "Mint the control-plane PAT." in r.text
    assert "approve the kit re-render budget" in r.text


def test_queue_filtered_or_sorted_view_is_flat(monkeypatch):
    _queue_world(monkeypatch)
    with TestClient(app) as c:
        for url in ("/queue?kind=note", "/queue?sort=az", "/queue?q=plugin"):
            r = c.get(url)
            assert r.status_code == 200
            assert 'id="age-fresh"' not in r.text  # sections step aside
            assert "jump to:" not in r.text


# --------------------------------------------------------------------------- #
# /orders — clickable counts, attention strip, repo anchors, done collapsed
# --------------------------------------------------------------------------- #

_O_INBOX = """# websites · inbox

## ORDER 001 · 2026-07-09T12:07Z · status: new
priority: P1
do: Adopt the protocol; then build the drift cell.

## ORDER 002 · 2026-07-09T14:52Z · status: new
priority: P0
do: Build a FLEET page.

## ORDER 003 · 2026-07-10T20:58:44Z · status: new
priority: P1
do: A brand new thing nobody started.
"""

_O_STATUS = """# websites · status
updated: 2026-07-10T21:58:00Z
health: green (fine)
orders: acked=001-003 done=001 claimed-by: 002 my-lane 2026-07-10T21:00Z
"""


def _orders_world(monkeypatch):
    monkeypatch.setattr(clock, "NOW_OVERRIDE", NOW)

    async def fake_fetch(repo, path, ref="main", refresh=False):
        if path == "control/inbox.md" and repo == "websites":
            return _res(data=_O_INBOX)
        if path.startswith("control/status") and repo == "websites":
            return _res(data=_O_STATUS)
        return _res(ok=False, status=404, data=None, error="Not Found")

    monkeypatch.setattr(github, "fetch_file", fake_fetch)


def test_orders_summary_header_counts_link_and_anchor(monkeypatch):
    _orders_world(monkeypatch)
    client = TestClient(app)
    r = client.get("/orders")
    assert r.status_code == 200
    # summary counts are filter links now
    assert 'href="/orders?state=open"' in r.text
    assert 'href="/orders?state=done"' in r.text
    # attention strip names the repos with open orders, anchored
    assert "needs attention" in r.text
    assert 'href="#repo-websites"' in r.text
    assert 'id="repo-websites"' in r.text
    assert "jump to:" in r.text


def test_orders_done_collapse_only_on_default_view(monkeypatch):
    _orders_world(monkeypatch)
    client = TestClient(app)
    r = client.get("/orders")
    assert "1 done order — collapsed" in r.text
    # explicit sort/filter -> flat list, no collapsed section
    for url in ("/orders?sort=oldest", "/orders?state=done", "/orders?q=fleet"):
        r = client.get(url)
        assert r.status_code == 200
        assert "done order — collapsed" not in r.text


# --------------------------------------------------------------------------- #
# /activity — state counts + date sections ("older" collapsed)
# --------------------------------------------------------------------------- #


def _pr(number, title, *, merged=None, updated=None, state="closed",
        draft=False):
    return {
        "number": number, "title": title, "state": state, "draft": draft,
        "merged_at": merged, "updated_at": updated, "created_at": updated,
        "user": {"login": "bot"},
        "html_url": f"https://github.com/x/y/pull/{number}",
    }


def _activity_world(monkeypatch):
    monkeypatch.setattr(clock, "NOW_OVERRIDE", NOW)
    prs = [
        _pr(10, "the today PR", state="open",
            updated="2026-07-10T08:00:00Z"),
        _pr(9, "the yesterday PR", merged="2026-07-09T08:00:00Z"),
        _pr(8, "the old PR", merged="2026-06-20T08:00:00Z"),
    ]

    async def fake_repo_api(repo, subpath="", refresh=False):
        if subpath.startswith("/pulls"):
            return _res(data=prs if repo == "websites" else [])
        return _res(ok=False, status=404, data=None, error="nf")

    monkeypatch.setattr(github, "repo_api", fake_repo_api)


def test_activity_date_groups_buckets_and_undated():
    items = [{"date": "2026-07-10"}, {"date": "2026-07-09"},
             {"date": "2026-07-05"}, {"date": "2026-06-01"}, {"date": ""}]
    groups = activity.date_groups(items, now=NOW)
    assert [g["key"] for g in groups] == [
        "today", "yesterday", "week", "older", "undated"]
    assert all(len(g["items"]) == 1 for g in groups)
    assert [g["anchor"] for g in groups] == [
        "when-today", "when-yesterday", "when-week", "when-older",
        "when-undated"]


def test_activity_page_summary_counts_and_date_sections(monkeypatch):
    _activity_world(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/activity")
    assert r.status_code == 200
    # summary header: shown-count + per-state chips
    assert "3 of 3 shown" in r.text
    assert "2 merged" in r.text and "1 open" in r.text
    # jump links + anchored sections
    assert "jump to:" in r.text
    for anchor in ("when-today", "when-yesterday", "when-older"):
        assert f'href="#{anchor}"' in r.text
        assert f'id="{anchor}"' in r.text
    # today/yesterday open; the bulky "older" section starts collapsed
    assert 'open id="when-today"' in r.text
    assert 'open id="when-older"' not in r.text
    # rows still render inside their sections
    assert "the today PR" in r.text and "the old PR" in r.text


# --------------------------------------------------------------------------- #
# /journal + /ideas + /reviews — summary headers with jump anchors
# --------------------------------------------------------------------------- #


def _offline(monkeypatch):
    async def fake_get(url, refresh=False, raw=False):
        return {"ok": False, "status": 0, "data": None, "error": "offline",
                "fetched_at": "", "cached": False, "url": url}

    monkeypatch.setattr(github, "_get", fake_get)


def test_journal_summary_header_jump_links(monkeypatch):
    _offline(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/journal")
    assert r.status_code == 200
    assert "jump to:" in r.text
    for repo in config.REPOS:
        assert f'href="#repo-{repo}"' in r.text
        assert f'id="repo-{repo}"' in r.text


_IDEA_FILES = [
    {"type": "file", "name": f"idea-{n}.md", "path": f"docs/ideas/idea-{n}.md",
     "html_url": ""}
    for n in ("a", "b", "c")
]
_IDEA_CONTENT = {
    "docs/ideas/idea-a.md": "---\nstate: captured\n---\n\n# A\n\none a\n",
    "docs/ideas/idea-b.md": "---\nstate: built\n---\n\n# B\n\none b\n",
    "docs/ideas/idea-c.md": "# C\n\nno front-matter here\n",
}


def _ideas_world(monkeypatch):
    async def fake_api(repo, subpath="", refresh=False):
        if subpath.endswith("/contents/docs/ideas") and repo == "websites":
            return _res(data=_IDEA_FILES)
        return _res(ok=False, status=404, data=None, error="nf")

    async def fake_fetch(repo, path, ref="main", refresh=False):
        if path in _IDEA_CONTENT:
            return _res(data=_IDEA_CONTENT[path])
        return _res(ok=False, status=404, data=None, error="nf")

    monkeypatch.setattr(github, "repo_api", fake_api)
    monkeypatch.setattr(github, "fetch_file", fake_fetch)


def test_ideas_totals_rollup_is_pure_aggregation():
    repos = [
        {"total": 3, "state_counts": {"captured": 1, "built": 1, "unstated": 1},
         "listing_error": None},
        {"total": 0, "state_counts": {}, "listing_error": None},
        {"total": 0, "state_counts": {}, "listing_error": "rate limited"},
    ]
    t = ideas.totals(repos)
    assert t["ideas"] == 3 and t["repos_with_ideas"] == 1
    assert t["errors"] == 1
    assert t["state_counts"] == {"captured": 1, "built": 1, "unstated": 1}


def test_ideas_summary_header_and_settled_collapse(monkeypatch):
    _ideas_world(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/ideas")
    assert r.status_code == 200
    # fleet rollup chips + counted state filter pills
    assert "3 ideas" in r.text
    assert "built · 1" in r.text and "captured · 1" in r.text
    # jump anchors per repo with ideas
    assert "jump to:" in r.text
    assert 'href="#repo-websites"' in r.text and 'id="repo-websites"' in r.text
    # built idea collapses under the live conveyor on the default view
    assert "1 built/retired — collapsed" in r.text
    # a state filter renders flat (no collapsed section)
    r = c.get("/ideas?state=built")
    assert r.status_code == 200
    assert "built/retired — collapsed" not in r.text


_REVIEW_LEDGER = """# Review queue

| PR | What to re-check | Why-risky | Drain path · status |
|---|---|---|---|
| superbot#1920 | The checker semantics change | Enforcement surface | codex · **open** |
| ~~websites#67~~ | ~~Heartbeat enrichment parse~~ | ~~KNOWN_KEYS change~~ | ~~reviewed, ok~~ |
"""


def test_reviews_summary_anchors_and_collapsed_ledger(monkeypatch):
    monkeypatch.setattr(config, "GITHUB_TOKEN", "tok")

    async def fake_fetch(repo, path, ref="main", refresh=False):
        return _res(data=_REVIEW_LEDGER)

    monkeypatch.setattr(github, "fetch_file", fake_fetch)
    with TestClient(app) as c:
        r = c.get("/reviews")
    assert r.status_code == 200
    # counts double as jump links to the anchored sections
    assert 'href="#open-reviews"' in r.text and 'id="open-reviews"' in r.text
    assert 'href="#reviewed"' in r.text and 'id="reviewed"' in r.text
    assert 'href="#ledger"' in r.text and 'id="ledger"' in r.text
    assert "1 open" in r.text and "1 reviewed" in r.text
    # the full document is still served, but collapsed behind a summary
    assert "show the full document" in r.text
    assert "superbot#1920" in r.text


# --------------------------------------------------------------------------- #
# /owner — the nav manifest now reaches owner.py's own Jinja env
# --------------------------------------------------------------------------- #


def _basic(pw: str, user: str = "owner") -> dict:
    token = base64.b64encode(f"{user}:{pw}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def test_owner_pages_render_the_header_nav(monkeypatch):
    """app/owner.py renders base.html through its OWN Jinja env; without the
    NAV_* globals registered there the /owner header nav was empty. Pin every
    manifest link into the authed /owner response."""
    _offline(monkeypatch)
    monkeypatch.setattr(config, "SITE_PASSWORD", "pw")
    with TestClient(app) as c:
        r = c.get("/owner", headers=_basic("pw"))
    assert r.status_code == 200
    for item in nav.PRIMARY + nav.GROUPED:
        assert f'href="{item["href"]}"' in r.text, item["key"]
    assert "more ▾" in r.text  # the grouped dropdown renders too
