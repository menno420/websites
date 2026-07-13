"""Offline tests for supersession/do-not-paste warnings (ORDER 022 item 3):
an artifact whose OWN raw header disclaims being the paste source must not
render indistinguishably from the pasteable ones.

The one real marker today is fleet-manager
``docs/prompts/v3/universal-startup.md`` line 5 — a FULL-LINE HTML comment
("⚠ v3.3 (2026-07-12): SUPERSEDED AS THE GENERATION SOURCE — historical
template … Do not paste this file; do not regenerate from it."). Because
``extract_paste_body`` strips full-line comments, detection runs on the RAW
upstream text in the shared layer (``app/prompt_artifacts.py``), header
region only, strong phrases only.

Pinned here: the positive (the real marker line VERBATIM, fetched live from
fleet-manager@main 2026-07-13), every known false-positive trap VERBATIM
from the 27 CURRENT per-seat registry copies + session-ender (lowercase
"supersedes", "assembly is RETIRED", "table supersedes any cron", "THIS
file stays the canonical single source" — none may flag), the scan-window
and header-region bounds, successor extraction (explicit single naming
only, never invented), the artifact-dict field, and the render path on all
three surfaces (/prompts banner + chip, /projects/{package} card,
/prompts/history/{seat} rung) with the paste-body contract untouched.
Network-free: ``github.fetch_file``/``github.repo_api`` monkeypatched,
mirroring tests/test_prompts.py.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import github, prompt_artifacts, prompts  # noqa: E402
from app.main import app  # noqa: E402
from app.prompt_artifacts import extract_supersession  # noqa: E402


def _res(ok=True, status=200, data=None, error="", cached=False):
    return {"ok": ok, "status": status, "data": data, "error": error,
            "fetched_at": "12:00:00 UTC", "cached": cached, "url": ""}


@pytest.fixture(autouse=True)
def _registry_matches_by_default(monkeypatch):
    """Network-free registry listing (the /prompts drift chip's repo_api
    call), matched — same convention as tests/test_prompts.py."""

    async def fake_api(repo, subpath="", refresh=False):
        return _res(data=[{"type": "dir", "name": s, "path": f"projects/{s}"}
                          for s in prompts.SEATS])

    monkeypatch.setattr(github, "repo_api", fake_api)


# --------------------------------------------------------------------------- #
# fixtures — the REAL upstream texts, verbatim (fleet-manager@main 2026-07-13)
# --------------------------------------------------------------------------- #

# universal-startup.md line 5, VERBATIM (the one real marker in the fleet).
REAL_MARKER_LINE = (
    "<!-- ⚠ v3.3 (2026-07-12): SUPERSEDED AS THE GENERATION SOURCE — "
    "historical template, kept verbatim as the v3.2 skeleton of record. The "
    "v3.3 rebuild (owner spec 2026-07-12) made every "
    "per-project/<seat>-startup.md an AUTHORED, EXPANDED per-seat file (no "
    "char cap; universal doctrine inlined verbatim) — B files are no longer "
    "regenerated from this template, and tools/regen_b_files.py no longer "
    "has a B-generation mode (its v3.3 job = budget/drift checks + registry "
    "sync). The v3.3 startups preserve this template's procedure text "
    "byte-for-byte outside the documented v3.3 splices (per-project/README.md "
    "v3.3 changelog). Do not paste this file; do not regenerate from it. -->"
)

# The real file's header shape: status line, two generation comments, the
# marker on line 5, one more comment, then the paste body.
SUPERSEDED_STARTUP = (
    "> **Status:** `reference`\n"
    "\n"
    "<!-- v3.2 · 2026-07-12 · provenance: owner correction 2026-07-12 -->\n"
    "<!-- char-count: see the v3.2 budget table in per-project/README.md -->\n"
    + REAL_MARKER_LINE + "\n"
    "<!-- Artifact A — universal startup template. -->\n"
    "\n"
    "v3.2 · 2026-07-12 · universal startup · {{SEAT_NAME}}\n"
    "\n"
    "You are the {{SEAT_NAME}} COORDINATOR.\n"
)

# CURRENT per-seat registry header, VERBATIM (projects/websites/
# instructions.md lines 6–14 @ main 2026-07-13): lowercase "supersedes" +
# "assembly is RETIRED" in a header blockquote — must NOT flag.
CURRENT_SEAT_HEADER = (
    "<!-- v7 · 2026-07-13 · fleet-manager projects registry — GENERATED "
    "COPY, do not edit -->\n"
    "\n"
    "> **GENERATED COPY — NOT SOURCE OF TRUTH.** This registry copy is "
    "GENERATED FROM\n"
    "> the v3 home: **docs/prompts/v3/ is the source of truth** (generation "
    "v3.6,\n"
    "> stateless, D-9). Edit the v3 sources and regenerate — never this "
    "file.\n"
    "> Version lineage: v7 (2026-07-13) supersedes the prior registry sync "
    "copy.\n"
    "> Paste FULL into the Project's Custom Instructions. Body below the "
    "marker =\n"
    "> docs/prompts/v3/per-project/websites-custom-instructions.md paste "
    "body\n"
    "> VERBATIM — v3.6 is ONE AUTHORED FILE PER SEAT (seat header + "
    "condensed\n"
    "> five-section skeleton + keyword dictionary + routes); the v3.1/v3.2\n"
    "> core+seat-block assembly is RETIRED.\n"
    "\n"
    "<!-- registry-header-end -->\n"
    "\n"
    "v3.6 websites CI — dictionary+router.\n"
)

# session-ender header comment, VERBATIM excerpt: "THIS file stays the
# canonical single source" — the opposite of superseded; must NOT flag.
SESSION_ENDER_HEADER = (
    "> **Status:** `reference`\n"
    "\n"
    "<!-- v3.3 · 2026-07-12 · provenance: v3.3 expanded-startup rebuild "
    "(owner spec 2026-07-12). v3.3 also INLINES this ender's steps verbatim "
    "into every per-project/<seat>-startup.md (the ender-blackout fix); "
    "THIS file stays the canonical single source — tools/regen_b_files.py "
    "verifies every startup's inlined copy byte-matches the step block "
    "below (drift class D-10). -->\n"
    "\n"
    "v3.3 · Universal Session-Ender\n"
)


# --------------------------------------------------------------------------- #
# extract_supersession: the positive
# --------------------------------------------------------------------------- #


def test_real_universal_startup_marker_flags():
    hit = extract_supersession(SUPERSEDED_STARTUP)
    assert hit is not None
    assert hit["phrase"] == "SUPERSEDED"
    assert hit["line"].startswith("⚠ v3.3 (2026-07-12): SUPERSEDED AS THE "
                                  "GENERATION SOURCE — historical template")
    # comment delimiters stripped, long marker prose truncated sanely
    assert "<!--" not in hit["line"] and "-->" not in hit["line"]
    assert len(hit["line"]) <= 300 and hit["line"].endswith("…")
    # the marker names the per-seat startups GENERICALLY — no single
    # successor file, so none is linked (never invented)
    assert hit["successor"] is None


def test_do_not_paste_and_historical_template_signals_flag():
    assert extract_supersession(
        "<!-- do not paste this file -->\nbody\n"
    )["phrase"] == "do not paste"
    assert extract_supersession(
        "> Historical Template — kept for the record.\nbody\n"
    )["phrase"] == "historical template"
    # heading region counts too
    assert extract_supersession(
        "# SUPERSEDED — see the v4 docs\nbody\n"
    )["phrase"] == "SUPERSEDED"


# --------------------------------------------------------------------------- #
# extract_supersession: every known false-positive trap, verbatim
# --------------------------------------------------------------------------- #


def test_current_seat_registry_header_does_not_flag():
    """Lowercase 'Version lineage: v7 … supersedes the prior registry sync
    copy.' and 'the v3.1/v3.2 core+seat-block assembly is RETIRED.' are the
    CURRENT header idiom on all 27 per-seat copies — never a warning."""
    assert extract_supersession(CURRENT_SEAT_HEADER) is None


def test_session_ender_canonical_header_does_not_flag():
    assert extract_supersession(SESSION_ENDER_HEADER) is None


def test_body_prose_traps_do_not_flag():
    # failsafe-doc body prose: lowercase "supersedes" over a table
    assert extract_supersession(
        "> registry copy header\n\n"
        "this table supersedes any cron previously recorded\n"
    ) is None
    # retirement prose: bare "retired" (any case) is not a signal
    assert extract_supersession("> first denial retired\nbody\n") is None
    assert extract_supersession(
        "> status: RETIRED-superseded by the v4 flow\nbody\n"
    ) is None


def test_strong_phrase_below_scan_window_does_not_flag():
    """The scan is the header region — the first ~15 RAW lines. A strong
    phrase deeper in the body is content, not a marker."""
    text = "> header\n" + "body line\n" * 15 + \
        "<!-- SUPERSEDED — do not paste -->\n"
    assert extract_supersession(text) is None


def test_strong_phrase_on_plain_body_line_does_not_flag():
    """Within the window but NOT in a comment/blockquote/heading line —
    plain body text mentioning the phrase is not a self-declaration."""
    assert extract_supersession(
        "v1 · title\n"
        "mark anything SUPERSEDED loudly; do not paste stale prompts\n"
    ) is None
    assert extract_supersession("") is None
    assert extract_supersession(None) is None


# --------------------------------------------------------------------------- #
# successor: explicit single naming only
# --------------------------------------------------------------------------- #


def test_successor_only_when_marker_names_one_file():
    see = extract_supersession(
        "<!-- SUPERSEDED — see docs/prompts/v4/universal-startup.md -->\n"
    )
    assert see["successor"] == "docs/prompts/v4/universal-startup.md"
    link = extract_supersession(
        "<!-- SUPERSEDED — replaced by [the v4 doc](https://example.com/v4.md) -->\n"
    )
    assert link["successor"] == "https://example.com/v4.md"
    # two candidates = ambiguous = none (never guessed)
    two = extract_supersession(
        "<!-- SUPERSEDED — see a.md and [b](b.md) and [c](c.md) -->\n"
    )
    assert two["successor"] is None


# --------------------------------------------------------------------------- #
# the artifact dict field (shared layer)
# --------------------------------------------------------------------------- #


def test_build_artifact_superseded_field():
    marked = prompt_artifacts.build_artifact(
        "docs/prompts/v3/universal-startup.md", "Universal Startup",
        _res(data=SUPERSEDED_STARTUP),
    )
    assert marked["ok"] and marked["superseded"]["phrase"] == "SUPERSEDED"
    # detection is on the RAW header; the paste body stays comment-free
    assert "<!--" not in marked["text"]
    assert "SUPERSEDED" not in marked["text"]

    clean = prompt_artifacts.build_artifact(
        "projects/websites/instructions.md", "Custom Instructions",
        _res(data=CURRENT_SEAT_HEADER), seat="websites",
    )
    assert clean["ok"] and clean["superseded"] is None

    failed = prompt_artifacts.build_artifact(
        "docs/prompts/v3/universal-startup.md", "Universal Startup",
        _res(ok=False, status=404, data=None, error="Not Found"),
    )
    assert failed["superseded"] is None  # no warning invented on failure


# --------------------------------------------------------------------------- #
# routes: /prompts banner + chip, dispatch card, history rung — one shared
# render path (ORDER 015), paste-body contract untouched
# --------------------------------------------------------------------------- #


def _patch_prompts_fetch(monkeypatch, marked_path=None):
    """Every artifact clean except ``marked_path``, which serves the real
    superseded universal-startup shape."""

    async def fake_fetch(repo, path, ref="main", refresh=False):
        if path == marked_path:
            return _res(data=SUPERSEDED_STARTUP)
        return _res(data="<!-- v7 · 2026-07-13 · reg copy -->\n"
                         f"BODY OF {path}\n")

    monkeypatch.setattr(github, "fetch_file", fake_fetch)


def _pre_blocks(html):
    return re.findall(r"<pre[^>]*>(.*?)</pre>", html, flags=re.DOTALL)


def test_prompts_route_banner_and_chip_when_one_artifact_superseded(monkeypatch):
    _patch_prompts_fetch(
        monkeypatch, marked_path="docs/prompts/v3/universal-startup.md"
    )
    r = TestClient(app).get("/prompts")
    assert r.status_code == 200
    flat = " ".join(r.text.split())
    # the unmissable banner, exactly once (1 of 29)
    assert r.text.count('class="banner superseded"') == 1
    assert "⚠ SUPERSEDED — do not paste" in r.text
    assert "SUPERSEDED AS THE GENERATION SOURCE" in flat
    assert "view the full marker on GitHub" in flat
    # no successor named → none linked, said honestly
    assert "names no single successor file" in flat
    # summary chip in the header card
    assert "⚠ 1 superseded" in r.text
    # copy demoted but not blocked: warned note + red-bordered pre, and the
    # copy path (copycode.js over .card pre) still binds
    assert "paste-ready body of a SUPERSEDED file" in flat
    assert '<pre class="superseded">' in r.text
    assert 'src="/static/copycode.js"' in r.text


def test_prompts_route_no_banner_no_chip_when_all_current(monkeypatch):
    _patch_prompts_fetch(monkeypatch)  # nothing marked
    r = TestClient(app).get("/prompts")
    assert r.status_code == 200
    # zero chip/banner noise: no banner, no chip, no demoted pre, no
    # warned copy note (the word appears only in the page's shared CSS)
    assert 'class="banner superseded"' not in r.text
    assert "⚠ SUPERSEDED — do not paste" not in r.text
    assert "superseded</span>" not in r.text  # no count chip
    assert '<pre class="superseded">' not in r.text
    assert "paste-ready body of a SUPERSEDED file" not in \
        " ".join(r.text.split())


def test_paste_body_contract_untouched_by_the_banner(monkeypatch):
    """The marker lives in the raw header only — the rendered <pre> (which
    IS the copy payload) stays comment-free and marker-free."""
    _patch_prompts_fetch(
        monkeypatch, marked_path="docs/prompts/v3/universal-startup.md"
    )
    r = TestClient(app).get("/prompts")
    pres = _pre_blocks(r.text)
    assert pres
    for pre in pres:
        assert "<!--" not in pre and "&lt;!--" not in pre
        assert "SUPERSEDED AS THE GENERATION SOURCE" not in pre
    # the superseded body itself still renders and stays copyable
    assert any("You are the {{SEAT_NAME}} COORDINATOR." in p for p in pres)


def test_dispatch_screen_card_shows_the_banner(monkeypatch):
    """ORDER 015 consolidation: the /projects/{package} card renders the
    SAME shared partial — the banner appears there with zero page-local
    code."""
    files = {
        "projects/websites/coordinator-prompt.md": SUPERSEDED_STARTUP,
        "projects/websites/instructions.md":
            "<!-- v7 · 2026-07-13 · reg copy -->\nCI BODY\n",
    }

    async def fake_api(repo, subpath="", refresh=False):
        if subpath.endswith("/contents/projects"):
            return _res(data=[{"type": "dir", "name": "websites",
                               "path": "projects/websites"}])
        if subpath.endswith("/contents/projects/websites"):
            return _res(data=[{"type": "file", "path": p} for p in files])
        return _res(ok=False, status=404, data=None, error="nf")

    async def fake_fetch(repo, path, ref="main", refresh=False):
        if path in files:
            return _res(data=files[path])
        return _res(ok=False, status=404, data=None, error="Not Found")

    monkeypatch.setattr(github, "repo_api", fake_api)
    monkeypatch.setattr(github, "fetch_file", fake_fetch)
    r = TestClient(app).get("/projects/websites")
    assert r.status_code == 200
    assert r.text.count('class="banner superseded"') == 1
    assert "⚠ SUPERSEDED — do not paste" in r.text
    assert "paste-ready body of a SUPERSEDED file" in " ".join(r.text.split())


def test_history_rung_with_marker_warns_current_rung_does_not(monkeypatch):
    """/prompts/history/{seat}: a historical version whose header carries
    the marker shows the banner on ITS rung only — the shared extractor
    populates the same field on the history dicts."""
    sha_old, sha_new = "a1" * 20, "c3" * 20
    bodies = {
        sha_old: SUPERSEDED_STARTUP,
        sha_new: "<!-- v3.6 · 2026-07-13 -->\nv3.6 websites CI.\nbody\n",
    }

    async def fake_api(repo, subpath="", refresh=False):
        assert subpath.startswith("/commits?path=")
        return _res(data=[
            {"sha": sha_new, "commit": {"committer":
             {"date": "2026-07-13T02:05:50Z"}, "message": "v3.6"}},
            {"sha": sha_old, "commit": {"committer":
             {"date": "2026-07-12T19:49:25Z"}, "message": "v3.2 skeleton"}},
        ])

    async def fake_fetch(repo, path, ref="main", refresh=False):
        return _res(data=bodies[ref])

    monkeypatch.setattr(github, "repo_api", fake_api)
    monkeypatch.setattr(github, "fetch_file", fake_fetch)
    r = TestClient(app).get("/prompts/history/websites")
    assert r.status_code == 200
    assert r.text.count('class="banner superseded"') == 1
    assert "⚠ SUPERSEDED — do not paste" in r.text
    # the marked rung is the OLD one — the banner sits after its anchor and
    # the clean rung carries no red pre
    assert r.text.count('<pre class="superseded">') == 1
    assert "v3.6 websites CI." in r.text
