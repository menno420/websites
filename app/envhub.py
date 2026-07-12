"""Owner environments hub (ORDER 021 slice 1): the fleet-wide environment
inventory behind ``GET /owner/environments-hub``.

THE canonical environments home (owner refinement 2026-07-12): one page to
find every environment surface across the fleet — Railway projects/services,
GitHub Actions secret stores, claude.ai cloud environments — grouped per
project-group, each row carrying the surface's variable NAMES and a deep
link to where it is managed. The two pre-existing environment pages are its
clearly-labeled sub-views, not siblings: ``/owner/environments`` (live
estate detail — per-variable purpose + runtime presence) and
``/environments`` (the fleet-manager claude.ai schema registry, full
copyable render; stays public — it exposes nothing owner-only). Three data
halves feed the hub:

1. **Committed registry** (``app/data/environments.json``): the hand-audited
   fleet inventory, agent-updatable by PR, rendered at request time. NAMES
   and links only — the loader hard-rejects any value-like field so the
   registry can never grow a secrets column. Railway ids are recorded only
   where the repo itself proves them (docs/deployment.md SAFE literals);
   an unrecorded id is ``null`` and the UI degrades to a project-level or
   console-home link — never a fabricated deep link.

2. **Live merge** (superbot-websites group only): variable NAMES per service
   via the existing project-scoped ``RAILWAY_TOKEN`` read in
   ``app/railway.py`` (names dropped to a list at the client boundary —
   never values). Token unset → the committed names render alone with the
   honest ``not-configured`` note; tests run without it.

3. **Schema index** (``environments.index``): the fleet-manager claude.ai
   registry's file listing (names + links, no bodies) embedded as the hub's
   schema section, deep-linking the full render at ``/environments``.

RAILWAY SAFETY (docs/RAILWAY-SAFETY.md, binding): this module makes no
Railway call of its own (the one read path stays ``app/railway.py``), never
reads the ambient production-bot ids, and records the reliable-grace
production project with NO ids at all by design.

Discord-OAuth seam: authentication is owned by the route in ``app/owner.py``
(``require_owner`` today); this module is auth-agnostic on purpose so the
later OAuth swap touches only the route dependency.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import environments, listfilter, railway

REGISTRY_PATH = Path(__file__).parent / "data" / "environments.json"

# Railway's variables-tab deep link (the console format ORDER 021 pins).
# Emitted ONLY when all three ids are recorded in the registry.
RAILWAY_VARIABLES_LINK = (
    "https://railway.com/project/{project}/service/{service}"
    "/variables?environmentId={environment}"
)
RAILWAY_PROJECT_LINK = "https://railway.com/project/{project}"
CONSOLE_HOME = "https://railway.com/dashboard"

# Loader guard: NO value-like field may exist anywhere in the registry —
# names and links only, by construction. Any dict key containing one of
# these tokens fails the load (and therefore the tests + the page).
FORBIDDEN_KEY_TOKENS = ("value", "secret", "token", "password", "credential")

_GROUP_REQUIRED = ("id", "title", "kind", "purpose", "surfaces")
_SURFACE_REQUIRED = ("id", "name", "kind", "purpose", "variable_names")


def _check_no_value_keys(node: Any, path: str = "$") -> None:
    if isinstance(node, dict):
        for key, val in node.items():
            lowered = key.lower()
            if any(tok in lowered for tok in FORBIDDEN_KEY_TOKENS):
                raise ValueError(
                    f"registry field {path}.{key} looks value-like — the "
                    "environments registry stores NAMES and links only"
                )
            _check_no_value_keys(val, f"{path}.{key}")
    elif isinstance(node, list):
        for i, val in enumerate(node):
            _check_no_value_keys(val, f"{path}[{i}]")


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, Any]:
    """Parse + validate the committed registry. Raises ``ValueError`` on any
    shape violation — a broken registry commit fails tests, it never renders
    half-trusted."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("groups"), list):
        raise ValueError("registry must be an object with a 'groups' list")
    if not data["groups"]:
        raise ValueError("registry has no groups")
    _check_no_value_keys(data)
    seen_groups: set[str] = set()
    for gi, group in enumerate(data["groups"]):
        if not isinstance(group, dict):
            raise ValueError(f"groups[{gi}] is not an object")
        for key in _GROUP_REQUIRED:
            if key not in group:
                raise ValueError(f"groups[{gi}] missing required field {key!r}")
        if group["id"] in seen_groups:
            raise ValueError(f"duplicate group id {group['id']!r}")
        seen_groups.add(group["id"])
        if not isinstance(group["surfaces"], list) or not group["surfaces"]:
            raise ValueError(f"group {group['id']!r} has no surfaces")
        for si, surface in enumerate(group["surfaces"]):
            if not isinstance(surface, dict):
                raise ValueError(f"{group['id']}.surfaces[{si}] is not an object")
            for key in _SURFACE_REQUIRED:
                if key not in surface:
                    raise ValueError(
                        f"{group['id']}.surfaces[{si}] missing field {key!r}"
                    )
            names = surface["variable_names"]
            if not isinstance(names, list) or not all(
                isinstance(n, str) and n and "=" not in n and " " not in n
                for n in names
            ):
                raise ValueError(
                    f"{group['id']}.{surface['id']}: variable_names must be "
                    "bare NAME strings (no '=', no spaces — never values)"
                )
    return data


def manage_link(group: dict[str, Any], surface: dict[str, Any]) -> dict[str, str]:
    """The manage-here deep link for one surface, degrading honestly:
    full Railway variables deep link (all three ids recorded) → project-level
    Railway link → the surface's explicit ``manage_url`` → the group's
    ``console_url`` → the Railway console home. Never a fabricated id."""
    project_id = group.get("railway_project_id")
    environment_id = group.get("railway_environment_id")
    service_id = surface.get("railway_service_id")
    if project_id and service_id and environment_id:
        return {
            "label": "Railway variables",
            "url": RAILWAY_VARIABLES_LINK.format(
                project=project_id, service=service_id, environment=environment_id
            ),
        }
    if project_id:
        return {
            "label": "Railway project",
            "url": RAILWAY_PROJECT_LINK.format(project=project_id),
        }
    if surface.get("manage_url"):
        return {"label": "manage", "url": surface["manage_url"]}
    if group.get("console_url"):
        return {"label": "console", "url": group["console_url"]}
    return {"label": "Railway console", "url": CONSOLE_HOME}


def _rows(registry: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten groups → one row per surface (the listfilter item unit),
    each row carrying its group identity for sectioning."""
    rows: list[dict[str, Any]] = []
    for group in registry["groups"]:
        for surface in group["surfaces"]:
            rows.append(
                {
                    "group_id": group["id"],
                    "group_title": group["title"],
                    "surface": surface,
                    "manage": manage_link(group, surface),
                    # Filled by the live merge for superbot-websites rows.
                    "live_names": None,
                    "live_error": None,
                }
            )
    return rows


def _merge_live(rows: list[dict[str, Any]], live: dict[str, Any]) -> None:
    """Attach live Railway variable NAMES to matching superbot-websites rows
    (matched by service name). Only ``ok`` snapshots carry names; per-service
    fetch errors surface as-is on the row."""
    if live.get("state") != "ok":
        return
    by_name = {s["name"]: s for s in live.get("services", [])}
    for row in rows:
        if row["group_id"] != "superbot-websites":
            continue
        svc = by_name.get(row["surface"]["name"])
        if svc is None:
            continue
        row["live_names"] = svc.get("variable_names", [])
        row["live_error"] = svc.get("error")


async def overview(refresh: bool = False) -> dict[str, Any]:
    """Everything the hub renders: the registry rows (live names merged for
    the superbot-websites group), the live-read state for the honest banner,
    and the fleet-manager schema index (the ``/environments`` sub-view's
    listing, no bodies).

    The registry is re-read per request (small committed file — a merged
    registry PR shows up on the next deploy's first render without a cache
    to expire)."""
    registry = load_registry()
    rows = _rows(registry)
    live = await railway.live_overview(refresh=refresh)
    _merge_live(rows, live)
    return {
        "as_of": registry.get("as_of", ""),
        "groups": registry["groups"],
        "rows": rows,
        "live": live,
        "schemas": await environments.index(refresh=refresh),
    }


def group_sections(
    registry_groups: list[dict[str, Any]], rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Partition (filtered) rows back into registry-ordered group sections
    with jump anchors — the list-IA summary pattern. Groups whose rows were
    all filtered out are omitted (the filter widget shows the honest count)."""
    by_group: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_group.setdefault(row["group_id"], []).append(row)
    sections = []
    for group in registry_groups:
        items = by_group.get(group["id"], [])
        if not items:
            continue
        sections.append(
            {
                "group": group,
                "anchor": f"group-{group['id']}",
                "rows": items,
            }
        )
    return sections


def _search_text(row: dict[str, Any]) -> str:
    surface = row["surface"]
    parts = [
        row["group_title"],
        surface.get("name", ""),
        surface.get("kind", ""),
        surface.get("purpose", ""),
        " ".join(surface.get("variable_names", [])),
    ]
    if row.get("live_names"):
        parts.append(" ".join(row["live_names"]))
    return " ".join(parts)


# ORDER 019 reuse: each project group is a separately reviewable filter; the
# kind dimension cuts across groups (e.g. all railway-services at once).
FILTER_SPEC = listfilter.ListSpec(
    path="/owner/environments-hub",
    dimensions=(
        listfilter.Dimension(
            key="group",
            label="project group",
            get=lambda row: [row["group_id"]],
        ),
        listfilter.Dimension(
            key="kind",
            label="kind",
            get=lambda row: [row["surface"].get("kind", "")],
        ),
    ),
    sorts=(
        # Registry order is the curated default (sort_key=None keeps it).
        listfilter.SortOption("registry", "registry order"),
        listfilter.SortOption(
            "az",
            "A-Z",
            sort_key=lambda row: row["surface"].get("name", "").casefold(),
        ),
    ),
    search=_search_text,
)
