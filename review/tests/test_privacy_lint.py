"""Site-wide privacy lint: no private-lane token on ANY review surface.

Executes the backlog bullet "Site-wide privacy lint for the review service"
(``docs/ideas/backlog.md``, captured 2026-07-12 by the ORDER 017 D
private-lane-filter session): the existing regression tests pin only ``/``,
``/fleet``, ``/fleet.json`` and the committed mirrors, but ORDER 017 D
("the Pokémon lane stays private") is a SITE-WIDE contract. This suite is
the promised net — it walks EVERY GET route in ``review/app.py`` (every
concrete edition/lane variant expanded from the committed data, plus every
shipped static asset) and EVERY committed ``review/data/**`` file, and
asserts no private-lane token appears anywhere.

**Accent-aware by spec.** The 2026-07-12 escapees were an accented
"Pokémon" in a template footnote and an evidence table that a plain
``grep -i pokemon`` missed, so matching here normalizes BOTH haystack and
tokens — NFKD-decompose, strip combining marks, casefold — before substring
search. ``Pokémon``, ``POKÉMON``, ``pokémon-mod-lab`` etc. all reduce to the
bare token. The token list is not invented here: it is the bullet's
``pok[eé]mon…`` stem plus every lane name in ``fleetdata.PRIVATE_LANES``
(the ORDER 017 D source of truth), so declaring a NEW private lane extends
this lint automatically.

**Zero network** (same doctrine as test_ai.py): the site is network-free at
runtime by design — the one exception, the AI assistant's outbound model
call, is a POST and is additionally monkeypatched to fail loudly if any
walked page ever reaches for it.

Shape follows the PR #225 inventory-consistency pin: an explicit,
per-entry-justified allowlist for legitimate occurrences (currently EMPTY —
no surface may say the name today), enforced in BOTH directions: an
occurrence NOT allowlisted fails with a headline naming the route/file +
token + snippet, and an allowlist entry that no longer matches anything
fails as stale, so an exemption cannot outlive its reason. A completeness
guard fails the suite when a future parameterized route or mount has no
registered expansion, so new surfaces cannot dodge the walk.
"""

from __future__ import annotations

import sys
import unicodedata
from pathlib import Path
from typing import Callable

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from starlette.routing import Mount

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from review import ai, editions, fleetdata  # noqa: E402
from review.app import app  # noqa: E402

client = TestClient(app)

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "static"

# --------------------------------------------------------------------------- #
# Token list — from the backlog bullet (`pok[eé]mon…`) + the ORDER 017 D
# source of truth. NEVER hardcode new tokens elsewhere; extend PRIVATE_LANES.
# --------------------------------------------------------------------------- #
PRIVATE_TOKENS: tuple[str, ...] = tuple(
    sorted({"pokemon"} | set(fleetdata.PRIVATE_LANES))
)

# Declared exceptions — (location, token, reason) triples for LEGITIMATE
# occurrences. ``location`` is a walked URL (e.g. "/fleet") or a data-file
# path relative to review/ (e.g. "data/evidence/01-provenance.md"). Every
# entry MUST carry its reason string; a stale entry (matching nothing) fails
# test_allowlist_carries_no_stale_entries. Currently EMPTY: ORDER 017 D says
# the lane is unnamed by design on every public surface, so today ANY
# occurrence is a leak.
ALLOWLIST: tuple[tuple[str, str, str], ...] = ()


# --------------------------------------------------------------------------- #
# Accent-aware matching: normalize haystack AND tokens (NFKD, strip
# combining marks, casefold) with an index map back into the original text
# so failure snippets show the real, un-normalized context.
# --------------------------------------------------------------------------- #
def _normalize_with_map(text: str) -> tuple[str, list[int]]:
    chars: list[str] = []
    origin: list[int] = []
    for i, ch in enumerate(text):
        decomposed = unicodedata.normalize("NFKD", ch)
        for c in decomposed:
            if unicodedata.combining(c):
                continue
            for folded in c.casefold():
                chars.append(folded)
                origin.append(i)
    return "".join(chars), origin


_NORM_TOKENS: tuple[str, ...] = tuple(
    _normalize_with_map(t)[0] for t in PRIVATE_TOKENS
)


def find_private_tokens(text: str) -> list[tuple[str, str]]:
    """All private-token hits in ``text`` → [(token, original-text snippet)].

    Longer tokens are folded into shorter ones by substring math (a
    "pokemon-mod-lab" hit is also a "pokemon" hit); each hit is reported
    once, under the token that matched at that position.
    """
    norm, origin = _normalize_with_map(text)
    hits: list[tuple[str, str]] = []
    for raw, token in zip(PRIVATE_TOKENS, _NORM_TOKENS):
        start = 0
        while True:
            pos = norm.find(token, start)
            if pos < 0:
                break
            lo = origin[pos]
            hi = origin[min(pos + len(token), len(origin)) - 1]
            snippet = text[max(0, lo - 40): hi + 41].replace("\n", " ")
            hits.append((raw, snippet))
            start = pos + 1
    return hits


# --------------------------------------------------------------------------- #
# Route walk: every GET APIRoute, parameterized paths expanded to every
# concrete variant the committed data defines, plus every static asset.
# --------------------------------------------------------------------------- #
def _fleet_repo_urls() -> list[str]:
    fl = fleetdata.load_fleet()
    assert fl["ok"], f"fleet mirror failed to load: {fl['error']}"
    repos = [ln.get("repo") for ln in fl["data"].get("lanes", []) if ln.get("repo")]
    assert repos, "fleet mirror lists no repo-backed lanes — expander is dead"
    # The private lane never appears in the filtered mirror; probe its
    # detail URL anyway (must 404 without echoing the name) plus a plain
    # unknown repo, so the 404 surface is linted too.
    return (
        [f"/fleet/{r}" for r in repos]
        + [f"/fleet/{lane}" for lane in sorted(fleetdata.PRIVATE_LANES)]
        + ["/fleet/no-such-repo"]
    )


def _review_slug_urls() -> list[str]:
    slugs = [e["slug"] for e in editions.list_editions()]
    assert slugs, "no committed review editions — expander is dead"
    return [f"/reviews/{s}" for s in slugs] + ["/reviews/no-such-edition"]


# Every parameterized GET route in review/app.py needs exactly one entry
# here; the completeness test fails when a new one appears without it (and
# when an entry goes stale because its route was removed).
PARAM_EXPANDERS: dict[str, Callable[[], list[str]]] = {
    "/fleet/{repo}": _fleet_repo_urls,
    "/reviews/{slug}": _review_slug_urls,
}


def _static_urls() -> list[str]:
    files = [p for p in STATIC_DIR.rglob("*") if p.is_file()]
    assert files, "review/static is empty — mount expander is dead"
    return [f"/static/{p.relative_to(STATIC_DIR).as_posix()}" for p in files]


# Mount paths in review/app.py → their concrete-URL expanders.
MOUNT_EXPANDERS: dict[str, Callable[[], list[str]]] = {
    "/static": _static_urls,
}


def _get_api_routes() -> list[APIRoute]:
    return [
        r for r in app.routes
        if isinstance(r, APIRoute) and "GET" in (r.methods or set())
    ]


def concrete_get_urls() -> list[str]:
    """Every concrete GET URL the walk covers — fails on an unexpandable
    route rather than silently skipping it."""
    urls: list[str] = []
    for route in _get_api_routes():
        if "{" in route.path:
            expander = PARAM_EXPANDERS.get(route.path)
            assert expander is not None, (
                f"parameterized GET route {route.path!r} has no expander in "
                "PARAM_EXPANDERS — register one so the privacy lint walks "
                "every concrete variant"
            )
            urls.extend(expander())
        else:
            urls.append(route.path)
    for route in app.routes:
        if isinstance(route, Mount):
            expander = MOUNT_EXPANDERS.get(route.path)
            assert expander is not None, (
                f"mount {route.path!r} has no expander in MOUNT_EXPANDERS — "
                "register one so the privacy lint walks its files"
            )
            urls.extend(expander())
    urls.append("/no-such-page")  # the catch-all 404 handler's surface
    return urls


def data_files() -> list[Path]:
    files = [p for p in DATA_DIR.rglob("*") if p.is_file()]
    assert files, "review/data is empty — the payload lint has nothing to scan"
    return files


def _loc(path: Path) -> str:
    return path.relative_to(BASE_DIR).as_posix()


def _allowed(location: str, token: str) -> bool:
    return any(loc == location and tok == token for loc, tok, _ in ALLOWLIST)


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    """Belt-and-braces: the walk is GET-only and the site is network-free at
    runtime, but if any page ever reaches for the one outbound call, fail
    loudly instead of touching the network (same guard as test_ai.py)."""
    monkeypatch.setattr(
        ai, "_post_anthropic",
        lambda payload, api_key: (_ for _ in ()).throw(
            AssertionError("outbound model call attempted in a network-free test")
        ),
    )


# --------------------------------------------------------------------------- #
# The lint
# --------------------------------------------------------------------------- #
def test_expanders_match_the_apps_routes_exactly():
    """Completeness both ways: every parameterized GET route has an
    expander (concrete_get_urls asserts that), and every expander entry
    still names a live route/mount — a stale entry means the walk's map has
    drifted from the app."""
    param_paths = {r.path for r in _get_api_routes() if "{" in r.path}
    mount_paths = {r.path for r in app.routes if isinstance(r, Mount)}
    stale = [p for p in PARAM_EXPANDERS if p not in param_paths]
    stale += [p for p in MOUNT_EXPANDERS if p not in mount_paths]
    assert not stale, (
        f"stale expander entries (route/mount no longer exists): {stale}"
    )
    assert param_paths == set(PARAM_EXPANDERS)
    assert mount_paths == set(MOUNT_EXPANDERS)


def test_no_private_token_on_any_get_route():
    """Walk every concrete GET URL; no response body may carry a private
    token (unless explicitly allowlisted, with reason). 404 bodies are
    linted too — a leak on an error page is still a leak."""
    problems: list[str] = []
    urls = concrete_get_urls()
    for url in urls:
        r = client.get(url)
        assert r.status_code < 500, f"GET {url} → {r.status_code}"
        body = r.content.decode("utf-8", errors="replace")
        for token, snippet in find_private_tokens(body):
            if _allowed(url, token):
                continue
            problems.append(
                f"PRIVATE-LANE LEAK — route {url} carries {token!r}: "
                f"…{snippet}…"
            )
    assert not problems, (
        "private-lane token rendered on a public route (ORDER 017 D):\n"
        + "\n".join(problems)
    )
    # The walk itself must stay honest — the known page set, expanded.
    assert len(urls) >= 20, f"suspiciously small route walk: {sorted(urls)}"


def test_no_private_token_in_committed_data_files():
    """Every committed review/data/** file, scanned as raw text — the
    payload side of the lint, independent of what any route renders."""
    problems: list[str] = []
    for path in data_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        loc = _loc(path)
        for token, snippet in find_private_tokens(text):
            if _allowed(loc, token):
                continue
            problems.append(
                f"PRIVATE-LANE LEAK — {loc} carries {token!r}: …{snippet}…"
            )
    assert not problems, (
        "private-lane token in a committed review payload (ORDER 017 D):\n"
        + "\n".join(problems)
    )


def test_allowlist_carries_no_stale_entries():
    """An allowlist entry that matches nothing would silently pre-excuse
    the NEXT leak at that location — fail it (PR #225 shape)."""
    data_by_loc = {_loc(p): p for p in data_files()}
    urls = set(concrete_get_urls())
    stale: list[str] = []
    for loc, token, reason in ALLOWLIST:
        if loc in urls:
            text = client.get(loc).content.decode("utf-8", errors="replace")
        elif loc in data_by_loc:
            text = data_by_loc[loc].read_text(encoding="utf-8", errors="replace")
        else:
            stale.append(f"({loc!r}, {token!r}) — location no longer exists")
            continue
        if not any(t == token for t, _ in find_private_tokens(text)):
            stale.append(f"({loc!r}, {token!r}) — token no longer occurs there")
    assert not stale, (
        "stale ALLOWLIST entries (remove them):\n" + "\n".join(stale)
    )


def test_matching_is_accent_aware():
    """The 2026-07-12 escapee class: accented variants a plain
    case-insensitive grep misses must still hit."""
    variants = (
        "Pok\u00e9mon",             # composed \u00e9 (the template-footnote escapee)
        "POK\u00c9MON",             # composed \u00c9, uppercase
        "Poke\u0301mon",            # decomposed e + combining acute
        "pok\u00e9mon-mod-lab",     # accented lane name
        "pokemon",                 # the plain stem still matches
    )
    for variant in variants:
        assert find_private_tokens(f"footnote about {variant} here"), variant
    assert find_private_tokens("clean text about game lab lanes") == []
