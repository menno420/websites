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

# Primary destinations: always visible top-level.
PRIMARY = [
    {"href": "/", "label": "readiness board", "key": "board"},
    {"href": "/fleet", "label": "fleet", "key": "fleet"},
    {"href": "/queue", "label": "owner queue", "key": "queue"},
    {"href": "/activity", "label": "activity", "key": "activity"},
    {"href": "/journal", "label": "journal browser", "key": "journal"},
]

# Secondary pages: grouped under the no-JS "more ▾" dropdown.
GROUPED = [
    {"href": "/environments", "label": "environments", "key": "environments"},
    {"href": "/projects", "label": "projects", "key": "projects"},
    {"href": "/prompts", "label": "prompts", "key": "prompts"},
    {"href": "/reviews", "label": "reviews", "key": "reviews"},
    {"href": "/orders", "label": "orders", "key": "orders"},
    {"href": "/ideas", "label": "ideas", "key": "ideas"},
]


def keys() -> set[str]:
    """Every nav key (primary + grouped) — the membership test's ground truth."""
    return {item["key"] for item in PRIMARY + GROUPED}
