"""The control-plane nav manifest — ONE data structure drives the whole IA.

Owner feedback (2026-07-12, live): the flat ~12-item console was "a lot of
clicking and a lot of scrolling; the ideal interface would feature a few
MAIN CATEGORIES which feature SUBCATEGORIES, and clear rows and better
placed buttons." This module is that redesign's single source of truth:

* ``CATEGORIES`` — the 2-level hierarchy as plain data. The header nav in
  ``templates/base.html`` renders the ~5 category links; the category
  landing pages (``/work``, ``/history``, ``/console`` in ``app/main.py``)
  render each category's subcategories as clear rows; the console home
  (``/``) renders the full category → subcategory map. Re-grouping a page
  is a one-line move here — no template or route surgery.
* ``category_for(active_key)`` — maps the ``active`` context value a route
  passes to its category, so the header highlights the CURRENT category
  (templates never hand-keep the mapping).
* ``tests/test_nav_manifest.py`` holds every route's ``active`` key to this
  manifest and ``tests/test_category_ia.py`` walks it for reachability —
  a page cannot be added outside the hierarchy without failing the suite.

Entry shapes (presentation only — no route, payload, or JSON-contract
impact):

* category: ``key`` / ``label`` / ``href`` / ``desc`` / ``landing`` (True
  when ``href`` is a generated category landing page that passes the
  category key as its ``active`` value) / ``gated`` / ``items``.
* item (subcategory): ``key`` (the ``active`` value the page's route
  passes; ``None`` for gated owner pages whose routes pass none) /
  ``label`` / ``href`` / ``desc`` / ``action`` (the row's primary action —
  label + href for the right-aligned button on the category landing).

Single-canonical-home doctrine (owner, same feedback round): cross-cutting
concerns live at ONE findable home — Prompts at ``/prompts``, Environments
at ``/environments`` — and every other appearance LINKS there instead of
forking the content.
"""

from __future__ import annotations

from typing import Any, Optional

CATEGORIES: list[dict[str, Any]] = [
    {
        "key": "overview",
        "label": "overview",
        "href": "/",
        "desc": "at-a-glance dashboard — fleet health plus what needs attention",
        "landing": False,  # the console home at / IS the overview dashboard
        "gated": False,
        "items": [
            {
                "key": "board",
                "label": "readiness board",
                "href": "/",
                "desc": (
                    "live per-repo readiness — CI, rulesets, required "
                    "checks, deploy drift"
                ),
                "action": {"label": "open board", "href": "/"},
            },
            {
                "key": "fleet",
                "label": "fleet heartbeats",
                "href": "/fleet",
                "desc": (
                    "heartbeat per fleet lane — which agents are running, "
                    "how far along"
                ),
                "action": {"label": "open fleet", "href": "/fleet"},
            },
        ],
    },
    {
        "key": "work",
        "label": "work",
        "href": "/work",
        "desc": "what needs doing — asks, orders, ideas, and review verdicts",
        "landing": True,
        "gated": False,
        "items": [
            {
                "key": "queue",
                "label": "owner queue",
                "href": "/queue",
                "desc": "owner action queue — asks that wait on a human decision",
                "action": {"label": "open queue", "href": "/queue"},
            },
            {
                "key": "orders",
                "label": "orders",
                "href": "/orders",
                "desc": "orders ledger — what was commanded, acked, done per lane",
                "action": {"label": "open orders", "href": "/orders"},
            },
            {
                "key": "ideas",
                "label": "ideas",
                "href": "/ideas",
                "desc": (
                    "idea conveyor per repo — captured → planned → built → "
                    "retired"
                ),
                "action": {"label": "open ideas", "href": "/ideas"},
            },
            {
                "key": "reviews",
                "label": "reviews",
                "href": "/reviews",
                "desc": "review verdicts collected over fleet PRs",
                "action": {"label": "open reviews", "href": "/reviews"},
            },
        ],
    },
    {
        "key": "history",
        "label": "history",
        "href": "/history",
        "desc": "what happened — the fleet timeline and committed journals",
        "landing": True,
        "gated": False,
        "items": [
            {
                "key": "activity",
                "label": "activity",
                "href": "/activity",
                "desc": "cross-repo timeline of recent commits and PRs",
                "action": {"label": "open timeline", "href": "/activity"},
            },
            {
                "key": "journal",
                "label": "journal",
                "href": "/journal",
                "desc": (
                    "browse + search the committed session journals across "
                    "repos"
                ),
                "action": {"label": "search journal", "href": "/journal/search"},
            },
        ],
    },
    {
        "key": "console",
        "label": "console",
        "href": "/console",
        "desc": (
            "the fleet operating assets — seats, prompts, environments, "
            "web surfaces"
        ),
        "landing": True,
        "gated": False,
        "items": [
            {
                "key": "projects",
                "label": "projects / dispatch",
                "href": "/projects",
                "desc": (
                    "fleet-manager dispatch registry — seat packages + role "
                    "coverage"
                ),
                "action": {"label": "open dispatch", "href": "/projects"},
            },
            {
                "key": "prompts",
                "label": "prompts",
                "href": "/prompts",
                "desc": (
                    "THE prompt home — universal + every per-seat paste "
                    "artifact, one library"
                ),
                "action": {"label": "browse prompts", "href": "/prompts"},
            },
            {
                # Canonical home = the owner environments hub (ORDER 021
                # slice 1, landed 2026-07-12): /owner/environments-hub
                # unifies the committed fleet registry + live Railway var
                # names + the claude.ai schema index. The public schema
                # registry (/environments, which passes this active key)
                # and the live estate detail (/owner/environments) are its
                # labeled sub-views — linked here, never forked.
                "key": "environments",
                "label": "environments 🔒",
                "href": "/owner/environments-hub",
                "desc": (
                    "THE environments home — fleet-wide inventory: Railway, "
                    "Actions secrets, claude.ai schemas (owner-gated)"
                ),
                "action": {
                    "label": "open env hub",
                    "href": "/owner/environments-hub",
                },
                "sublinks": [
                    {"label": "claude.ai schemas (public)", "href": "/environments"},
                    {"label": "live estate detail 🔒", "href": "/owner/environments"},
                ],
            },
            {
                "key": "directory",
                "label": "web directory",
                "href": "/directory",
                "desc": (
                    "every web surface we own — our sites, external "
                    "listings, live health"
                ),
                "action": {"label": "open directory", "href": "/directory"},
            },
        ],
    },
    {
        "key": "owner",
        "label": "owner 🔒",
        "href": "/owner",
        "desc": (
            "gated owner controls — unmasked board, writeback console, "
            "live Railway env view"
        ),
        "landing": False,  # /owner itself is the category's landing (gated)
        "gated": True,
        # Gated pages pass no ``active`` key (key=None): they are outside the
        # highlight machinery on purpose, but stay listed so the hierarchy —
        # and the ≤2-clicks guarantee — covers them too (home map + /owner).
        "items": [
            {
                "key": None,
                "label": "owner console",
                "href": "/owner",
                "desc": (
                    "unmasked board + privileged actions — expects the owner "
                    "login"
                ),
                "action": {"label": "open console", "href": "/owner"},
            },
            {
                "key": None,
                "label": "owner queue (writeback)",
                "href": "/owner/queue",
                "desc": (
                    "the gated /queue twin — mark complete, request assist, "
                    "add notes"
                ),
                "action": {"label": "open writeback", "href": "/owner/queue"},
            },
            {
                "key": None,
                "label": "environments hub",
                "href": "/owner/environments-hub",
                "desc": (
                    "THE environments home — also listed under console; its "
                    "sub-views link back"
                ),
                "action": {
                    "label": "open env hub",
                    "href": "/owner/environments-hub",
                },
            },
        ],
    },
]


def category(key: str) -> dict[str, Any]:
    """The category dict for ``key`` (KeyError when absent — a landing route
    for a category this manifest does not carry is a wiring bug)."""
    for cat in CATEGORIES:
        if cat["key"] == key:
            return cat
    raise KeyError(key)


def item(key: str) -> dict[str, Any]:
    """The subcategory item dict whose ``key`` matches (KeyError when absent)."""
    for cat in CATEGORIES:
        for it in cat["items"]:
            if it["key"] == key:
                return it
    raise KeyError(key)


def keys() -> set[str]:
    """Every ``active`` key the manifest recognizes — item keys plus the
    landing-page category keys. The membership test's ground truth: a route
    passing a key outside this set fails the suite."""
    out = {it["key"] for cat in CATEGORIES for it in cat["items"] if it["key"]}
    out.update(cat["key"] for cat in CATEGORIES if cat["landing"])
    return out


def category_for(active: Optional[str]) -> Optional[str]:
    """The category key an ``active`` context value belongs to (None when
    unknown/absent) — the header's current-category highlight."""
    if not active:
        return None
    for cat in CATEGORIES:
        if cat["landing"] and cat["key"] == active:
            return cat["key"]
        if any(it["key"] == active for it in cat["items"]):
            return cat["key"]
    return None


def all_hrefs() -> list[str]:
    """Every distinct href the manifest carries (categories + items +
    sub-view links), in manifest order — the reachability test's
    parametrization source: nothing in the IA may 404."""
    seen: list[str] = []
    for cat in CATEGORIES:
        hrefs = [cat["href"]]
        for it in cat["items"]:
            hrefs.append(it["href"])
            hrefs.extend(sl["href"] for sl in it.get("sublinks", ()))
        for href in hrefs:
            if href not in seen:
                seen.append(href)
    return seen
