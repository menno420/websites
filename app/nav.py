"""The control-plane nav manifest — ONE list drives the header nav.

The overflow-guard decision ("which pages are primary, which live under
the more ▾ dropdown") used to exist twice by hand: template markup in
``templates/base.html`` and GROUPED/PRIMARY tuples in
``tests/test_nav_overflow.py``. This module is now the single source:

* ``base.html`` iterates ``PRIMARY`` and ``GROUPED`` (registered as Jinja
  globals in ``app.main``) — adding a page here adds it to the rendered
  nav, in the right group, with the right active-state handling;
* ``tests/test_nav_overflow.py`` imports the same lists for reachability
  and dropdown-state assertions;
* ``tests/test_nav_manifest.py`` asserts every ``active`` key the routes
  actually pass appears here — so page 12 physically cannot be added
  outside the guard.

Each entry: ``href`` (link target), ``label`` (visible text), ``key``
(the ``active`` context value the page's route passes). Presentation
only — no route, payload, or JSON-contract impact.
"""

# Primary destinations: always visible top-level. Kept to ~7 so the header
# survives a phone width — the console-home section map (below) carries the
# long tail, so "primary" means "the owner's habit paths", not "everything".
PRIMARY = [
    {"href": "/", "label": "readiness board", "key": "board"},
    {"href": "/fleet", "label": "fleet", "key": "fleet"},
    {"href": "/queue", "label": "owner queue", "key": "queue"},
    {"href": "/activity", "label": "activity", "key": "activity"},
    {"href": "/journal", "label": "journal browser", "key": "journal"},
    {"href": "/projects", "label": "projects", "key": "projects"},
    {"href": "/orders", "label": "orders", "key": "orders"},
]

# Secondary pages: grouped under the no-JS "more ▾" dropdown.
GROUPED = [
    {"href": "/environments", "label": "environments", "key": "environments"},
    {"href": "/prompts", "label": "prompts", "key": "prompts"},
    {"href": "/reviews", "label": "reviews", "key": "reviews"},
    {"href": "/ideas", "label": "ideas", "key": "ideas"},
    {"href": "/directory", "label": "web directory", "key": "directory"},
]


def keys() -> set[str]:
    """Every nav key (primary + grouped) — the membership test's ground truth."""
    return {item["key"] for item in PRIMARY + GROUPED}


# ---------------------------------------------------------------------------
# Console-home section map (templates/board.html) — one card per feature
# page, one line of honest description each. Derived from PRIMARY + GROUPED
# so a page added to the nav manifest above cannot silently miss the home
# map: section_map() raises KeyError (and the suite pins coverage) if an
# entry here has no description.
DESCRIPTIONS = {
    "board": "live per-repo readiness — CI, rulesets, required checks, deploy drift",
    "fleet": "heartbeat per fleet lane — which agents are running, how far along",
    "queue": "owner action queue — asks that wait on a human decision",
    "activity": "cross-repo timeline of recent commits and PRs",
    "journal": "browse + search the committed session journals across repos",
    "projects": "fleet-manager dispatch registry — seat packages + role coverage",
    "orders": "orders ledger — what was commanded, acked, done per lane",
    "environments": "environment inventory and copy-paste setup commands",
    "prompts": "the prompt library each fleet seat runs on",
    "reviews": "review verdicts collected over fleet PRs",
    "ideas": "idea conveyor per repo — captured → planned → built → retired",
    "directory": "every web surface we own — our sites, external listings, live health",
}

# The owner console is deliberately OUTSIDE the header manifest (it is
# owner-gated and its routes pass no `active` key), but it must stay
# findable: the section map and the base-template footer both link it.
OWNER_LINK = {
    "href": "/owner",
    "label": "owner console",
    "desc": "unmasked board + privileged actions — gated, expects the owner login",
}


def section_map() -> list[dict]:
    """Every feature page as a home-page card: nav manifest order, then the
    gated owner console last."""
    items = [{**item, "desc": DESCRIPTIONS[item["key"]]} for item in PRIMARY + GROUPED]
    items.append(dict(OWNER_LINK))
    return items
