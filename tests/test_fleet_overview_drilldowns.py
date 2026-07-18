"""/fleet count-badge drill-downs + mobile-legibility markup (owner ask
2026-07-18).

The fleet-heartbeat summary strip used to be a row of count pills that LOOKED
tappable but did nothing; the owner tapped `12 stale` expecting to see WHICH
lanes are stale. Each count is now a server-rendered inline `<details>`
drill-down whose expanded list is the exact lanes behind that count — derived in
:func:`app.fleet.overview` alongside the count itself so the two can never
disagree. These tests pin, per count, that the drill-down lists EXACTLY the
matching lanes; that a zero count degrades to an honest flat (non-drill) tag;
that the overview stays a GET view (a POST is 405 — no state-changing surface
was added, the CSRF/same-origin floor on the owner-writeback POSTs is untouched
by this PR); and that the per-seat status table carries the wrap/`.kv` markup
the mobile fix needs.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import fleet, github, projects  # noqa: E402
from app.main import app  # noqa: E402

NOW = datetime(2026, 7, 18, 12, 0, 0, tzinfo=timezone.utc)

# A fixed 3-lane set so the drill-downs are deterministic regardless of the
# live registry: alpha (STALE heartbeat + outstanding orders + a pushed/stranded
# landing), beta (FRESH green → live), gamma (no status file → no_file).
LANES = [
    {"lane": "alpha", "repo": "alpha-repo", "status_path": "control/status.md",
     "model": "unknown", "note": ""},
    {"lane": "beta", "repo": "beta-repo", "status_path": "control/status.md",
     "model": "unknown", "note": ""},
    {"lane": "gamma", "repo": "gamma-repo", "status_path": "control/status.md",
     "model": "unknown", "note": ""},
]

_ALPHA = (
    "# alpha · status\n"
    "updated: 2026-07-01T00:00Z\n"          # ~17d old → stale
    "health: green (running)\n"
    "orders: acked=001-003 done=001\n"       # outstanding 002, 003
    "landing: pushed-unmerged claude/alpha-fix\n"
)
_BETA = (
    "# beta · status\n"
    "updated: 2026-07-18T11:00Z\n"           # 1h old → fresh → live
    "health: green (running)\n"
    "orders: acked=001 done=001\n"
)


def _res(ok=True, status=200, data=None):
    return {"ok": ok, "status": status, "data": data, "error": "" if ok else "nf",
            "fetched_at": "", "cached": False, "url": ""}


def _wire(monkeypatch, cov_state="unknown", incomplete_names=None):
    async def fake_resolve(refresh=False):
        return list(LANES), {"source": "registry", "ok": True, "reason": "",
                             "count": len(LANES), "registry_url": "https://x/reg"}

    async def fake_fetch(repo, path, ref="main", refresh=False):
        if not path.startswith("control/status"):
            return _res(ok=False, status=404, data=None)
        if repo == "alpha-repo":
            return _res(data=_ALPHA)
        if repo == "beta-repo":
            return _res(data=_BETA)
        return _res(ok=False, status=404, data=None)   # gamma → no_file

    async def fake_api(repo, subpath="", refresh=False):
        return _res(ok=False, status=404, data=None)

    async def fake_cov(refresh=False):
        base = {"state": cov_state, "reason": "registry unavailable", "seats": 0,
                "complete": 0, "incomplete": 0, "incomplete_names": [],
                "unlistable": 0, "unlistable_names": []}
        if incomplete_names is not None:
            base.update(state="ok", reason="", seats=len(incomplete_names) + 2,
                        complete=2, incomplete=len(incomplete_names),
                        incomplete_names=list(incomplete_names))
        return base

    monkeypatch.setattr(fleet, "resolve_lanes", fake_resolve)
    monkeypatch.setattr(fleet.clock, "now", lambda: NOW)
    monkeypatch.setattr(github, "fetch_file", fake_fetch)
    monkeypatch.setattr(github, "repo_api", fake_api)
    monkeypatch.setattr(projects, "coverage_rollup", fake_cov)


def _fleet_html(monkeypatch, **kw):
    _wire(monkeypatch, **kw)
    r = TestClient(app).get("/fleet")
    assert r.status_code == 200
    return r.text


def _drill_list_after(text, badge_label):
    """The text of the `.drill-list` div immediately following the summary
    pill labelled ``badge_label`` — i.e. the lanes the drill-down reveals."""
    i = text.find(">" + badge_label + "<")
    assert i != -1, f"badge {badge_label!r} not rendered"
    start = text.find('class="drill-list"', i)
    assert start != -1, f"no drill-list after {badge_label!r}"
    open_gt = text.find(">", start)
    end = text.find("</div>", open_gt)
    return text[open_gt + 1:end]


# --------------------------------------------------------------------------- #
# (a) each count's drill-down lists EXACTLY the matching lanes
# --------------------------------------------------------------------------- #


def test_stale_drilldown_lists_exactly_the_stale_lanes(monkeypatch):
    html = _fleet_html(monkeypatch)
    body = _drill_list_after(html, "1 stale")
    assert "alpha" in body
    assert "beta" not in body and "gamma" not in body
    # deep-links to the stale lane's card anchor
    assert 'href="#lane-alpha-repo"' in body


def test_live_drilldown_lists_exactly_the_live_lanes(monkeypatch):
    html = _fleet_html(monkeypatch)
    body = _drill_list_after(html, "1 live")
    assert "beta" in body
    assert "alpha" not in body and "gamma" not in body


def test_no_status_file_drilldown_lists_exactly_the_missing_lanes(monkeypatch):
    html = _fleet_html(monkeypatch)
    body = _drill_list_after(html, "1 no status file")
    assert "gamma" in body
    assert "alpha" not in body and "beta" not in body


def test_outstanding_orders_drilldown_lists_lane_and_ids(monkeypatch):
    html = _fleet_html(monkeypatch)
    body = _drill_list_after(html, "2 outstanding orders")
    assert 'href="#lane-alpha-repo"' in body
    assert "002, 003" in body        # the actual outstanding order ids
    assert "beta" not in body


def test_stranded_landing_drilldown_lists_lane_and_branch(monkeypatch):
    html = _fleet_html(monkeypatch)
    body = _drill_list_after(html, "1 stranded landing")
    assert "alpha" in body
    assert "claude/alpha-fix" in body        # the stranded branch name


def test_packages_incomplete_drilldown_lists_the_seat_names(monkeypatch):
    html = _fleet_html(monkeypatch, incomplete_names=["seat-x", "seat-y"])
    body = _drill_list_after(html, "packages incomplete: 2")
    assert "seat-x" in body and "seat-y" in body


# --------------------------------------------------------------------------- #
# (b) a zero count is an honest flat (non-drill) tag, never a dead expander
# --------------------------------------------------------------------------- #


def test_zero_live_renders_flat_tag_not_a_drilldown(monkeypatch):
    # All lanes stale/missing → 0 live. The "0 live" badge must render as a
    # flat informational tag, NOT wrapped in an expandable <details>.
    async def all_stale(repo, path, ref="main", refresh=False):
        if path.startswith("control/status") and repo in ("alpha-repo", "beta-repo"):
            return _res(data=_ALPHA.replace("# alpha", f"# {repo}"))
        return _res(ok=False, status=404, data=None)

    _wire(monkeypatch)
    monkeypatch.setattr(github, "fetch_file", all_stale)
    html = TestClient(app).get("/fleet").text
    assert '<span class="b ok tag">0 live</span>' in html
    # and there is no drill-down whose summary is "0 live"
    assert ">0 live<" in html


def test_stale_count_zero_renders_no_stale_badge_at_all(monkeypatch):
    # Only beta (fresh) present → stale count 0 → the whole stale badge is
    # absent (the honest empty state — nothing to drill).
    async def only_beta(repo, path, ref="main", refresh=False):
        if path.startswith("control/status") and repo == "beta-repo":
            return _res(data=_BETA)
        return _res(ok=False, status=404, data=None)

    _wire(monkeypatch)
    monkeypatch.setattr(github, "fetch_file", only_beta)
    html = TestClient(app).get("/fleet").text
    # the stale badge only renders when the count is > 0 — a 0 count shows no
    # badge at all (nothing to drill), never a "0 stale" dead expander
    assert "0 stale" not in html
    strip = html.split('class="drillrow')[1].split("</div>", 1)[0]
    assert "stale" not in strip


# --------------------------------------------------------------------------- #
# (c) overview stays a GET view — no state-changing surface, CSRF floor intact
# --------------------------------------------------------------------------- #


def test_overview_is_get_only_no_state_route_added(monkeypatch):
    _wire(monkeypatch)
    client = TestClient(app)
    assert client.get("/fleet").status_code == 200
    # A POST to the overview is Method Not Allowed — the drill-downs added no
    # state-changing route, so the owner-writeback CSRF/same-origin floor is
    # untouched by this change.
    assert client.post("/fleet").status_code == 405


# --------------------------------------------------------------------------- #
# (d) single source of truth: every count == length of its member list
# --------------------------------------------------------------------------- #


def test_counts_equal_member_list_lengths(monkeypatch):
    import asyncio

    _wire(monkeypatch)
    # now=NOW is required by the time-discipline guard (age-measuring calls
    # pass a frozen now); it also matches the clock we froze in _wire.
    data = asyncio.run(fleet.overview(now=NOW))
    s = data["summary"]
    assert s["total"] == len(s["total_lanes"])
    assert s["healthy"] == len(s["live_lanes"])
    assert s["stale"] == len(s["stale_lanes"])
    assert s["broken"] == len(s["broken_lanes"])
    assert s["errored"] == len(s["errored_lanes"])
    assert s["no_file"] == len(s["no_file_lanes"])
    assert s["stranded"] == len(s["stranded_lanes"])
    assert s["silent_routines"] == len(s["silent_routine_lanes"])
    # outstanding_orders counts IDS across lanes, not lanes
    assert s["outstanding_orders"] == sum(
        len(e["ids"]) for e in s["outstanding_order_lanes"]
    )
    assert {m["lane"] for m in s["stale_lanes"]} == {"alpha"}
    assert {m["lane"] for m in s["live_lanes"]} == {"beta"}


# --------------------------------------------------------------------------- #
# mobile legibility: the status table carries the wrap/.kv markup + CSS
# --------------------------------------------------------------------------- #


def test_status_table_uses_kv_class_and_lane_anchor(monkeypatch):
    html = _fleet_html(monkeypatch)
    assert 'class="card" id="lane-alpha-repo"' in html
    assert '<table class="kv">' in html


def test_base_css_carries_wrap_and_contrast_and_drill_rules(monkeypatch):
    _wire(monkeypatch)
    html = TestClient(app).get("/fleet").text
    # value cells wrap instead of clipping; label column bumped off --dim grey
    assert "overflow-wrap:anywhere" in html
    assert "table.kv th { color:#c9d1d9" in html
    # the phone-width scroll rule is overridden for the kv table
    assert ".card table.kv { min-width:0; }" in html
    # informational pills drop the button-ish outline
    assert ".b.tag { border-color:transparent" in html


def test_informational_pills_are_flat_tags(monkeypatch):
    html = _fleet_html(monkeypatch)
    # per-lane status tags are flat (.tag), not interactive
    assert 'class="b warn tag">stale</span>' in html
    assert "tag\">live from registry</span>" in html
