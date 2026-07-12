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


# ---------------------------------------------------------------------------
# ORDER 021 slice 2 — env-creation plan/manifest generator.
#
# For one project group, generate the complete-environment MANIFEST from the
# committed registry: (a) the service definitions, (b) the env-var SCHEMA —
# variable NAMES paired with placeholders like <SET-IN-RAILWAY-CONSOLE>,
# NEVER real values, (c) copyable setup commands the OWNER executes by hand
# (Railway CLI variable sets, service-creation console steps, GitHub
# settings/secrets/actions steps).
#
# HARD BOUNDARY (docs/RAILWAY-SAFETY.md, binding): this module only ever
# GENERATES the plan. It makes no Railway call, contains no GraphQL
# mutation strings (create/upsert/delete), and handles no API key —
# RAILWAY_API_KEY never lives on an app service. Actual provisioning is
# executed by the owner (or an authorized non-app session) at the consoles
# the plan names. Placeholders are filled by hand there; a real value can
# never appear here because none is ever loaded (the registry loader above
# hard-rejects value-like fields).
# ---------------------------------------------------------------------------

# Placeholder per surface kind — the text names the console where the owner
# fills in the real value BY HAND. Never a real value, by construction.
PLACEHOLDER_BY_KIND = {
    "railway-service": "<SET-IN-RAILWAY-CONSOLE>",
    "railway-worker": "<SET-IN-RAILWAY-CONSOLE>",
    "railway-postgres": "<MANAGED-BY-RAILWAY>",
    "github-actions-secrets": "<SET-IN-GITHUB-SECRETS>",
    "claude-environment": "<SET-IN-CLAUDE-SETTINGS>",
}
DEFAULT_PLACEHOLDER = "<SET-BY-OWNER>"

# Single-source boundary notice: rendered verbatim (and prominently) on the
# manifest page; the tests assert this exact text is present.
BOUNDARY_NOTICE = (
    "OWNER-EXECUTED PLAN ONLY — this page GENERATES the plan; it performs no "
    "provisioning. Per docs/RAILWAY-SAFETY.md agents make no Railway "
    "mutations and RAILWAY_API_KEY never lives on an app service. Every "
    "<SET-...> placeholder is filled in BY HAND at the console it names by "
    "the owner (or an authorized non-app session) — real secret values never "
    "appear on this site."
)


def placeholder_for(kind: str) -> str:
    return PLACEHOLDER_BY_KIND.get(kind, DEFAULT_PLACEHOLDER)


def get_group(group_id: str, registry: dict[str, Any] | None = None):
    """The registry group for ``group_id``, or ``None`` (route → 404)."""
    reg = registry if registry is not None else load_registry()
    for group in reg["groups"]:
        if group["id"] == group_id:
            return group
    return None


def _surface_commands(group: dict[str, Any], surface: dict[str, Any]) -> list[str]:
    """The owner-executed setup steps for one surface — comments + copyable
    commands. Variable placeholders only; an empty ``variable_names`` renders
    an honest not-recorded note, never a guessed name."""
    kind = surface["kind"]
    ph = placeholder_for(kind)
    manage = manage_link(group, surface)
    names = surface["variable_names"]
    lines = [f"## {surface['name']} ({kind}) — {surface['purpose']}"]

    if kind in ("railway-service", "railway-worker"):
        lines.append(
            f"# 1. Railway console: create service '{surface['name']}' in "
            f"project '{group['title']}' ({manage['url']})"
        )
        if names:
            lines.append(
                "# 2. set its variables (Railway CLI, explicitly linked to "
                "that project/service — never ambient linkage):"
            )
            lines.extend(
                f'railway variables --service "{surface["name"]}" '
                f'--set "{name}={ph}"'
                for name in names
            )
        else:
            lines.append(
                "# variable names are not recorded in this repo — record "
                "them by PR (app/data/environments.json) before "
                "provisioning; never guess."
            )
    elif kind == "railway-postgres":
        lines.append(
            "# Railway-managed database — add it from the Railway console; "
            "connection variables are Railway-managed and never live in "
            "this repo."
        )
    elif kind == "github-actions-secrets":
        lines.append(f"# manage at: {manage['url']}")
        if names:
            lines.extend(
                f'gh secret set {name} --repo "{surface["name"]}"  '
                f"# value prompted interactively — {ph}"
                for name in names
            )
        else:
            lines.append(
                f'# per secret: gh secret set NAME --repo "{surface["name"]}" '
                "(value prompted interactively — secret names are not "
                "recorded in this repo; list them at the settings page)."
            )
    elif kind == "claude-environment":
        lines.append(f"# create/edit at: {manage['url']}")
        lines.append(
            "# env-var schema + setup script: fleet-manager environments/ "
            "registry — rendered read-only at /environments on this site."
        )
        if names:
            lines.extend(f"# variable: {name}={ph}" for name in names)
    else:
        lines.append(f"# manage at: {manage['url']}")
        if names:
            lines.extend(f"# variable: {name}={ph}" for name in names)
        else:
            lines.append("# variable names are not recorded in this repo.")
    return lines


def manifest(group_id: str) -> dict[str, Any] | None:
    """The complete-environment manifest for one project group, generated
    from the committed registry alone (no network, no live reads, no
    mutations). ``None`` for an unknown group (route → 404)."""
    registry = load_registry()
    group = get_group(group_id, registry)
    if group is None:
        return None

    services: list[dict[str, Any]] = []
    for surface in group["surfaces"]:
        services.append(
            {
                "surface": surface,
                "manage": manage_link(group, surface),
                "placeholder": placeholder_for(surface["kind"]),
                "schema": [
                    {"name": n, "placeholder": placeholder_for(surface["kind"])}
                    for n in surface["variable_names"]
                ],
            }
        )

    header = [
        f"# complete-environment plan — {group['title']}",
        f"# generated from app/data/environments.json (as of "
        f"{registry.get('as_of', '')}) — names + placeholders only",
        "# " + BOUNDARY_NOTICE,
        "",
    ]
    command_lines = list(header)
    for svc in services:
        command_lines.extend(_surface_commands(group, svc["surface"]))
        command_lines.append("")

    json_doc = {
        "generated_from": "app/data/environments.json",
        "as_of": registry.get("as_of", ""),
        "boundary": BOUNDARY_NOTICE,
        "group": {
            "id": group["id"],
            "title": group["title"],
            "kind": group["kind"],
            "purpose": group["purpose"],
        },
        "services": [
            {
                "name": svc["surface"]["name"],
                "kind": svc["surface"]["kind"],
                "purpose": svc["surface"]["purpose"],
                "url": svc["surface"].get("url"),
                "managed_at": svc["manage"]["url"],
                "env_schema": svc["schema"],
                "notes": svc["surface"].get("notes", ""),
            }
            for svc in services
        ],
    }

    return {
        "group": group,
        "as_of": registry.get("as_of", ""),
        "services": services,
        "boundary": BOUNDARY_NOTICE,
        "commands_text": "\n".join(command_lines).rstrip() + "\n",
        "manifest_json": json.dumps(json_doc, indent=2),
        # Filled by annotate_completeness (the route always calls it);
        # None = pure plan generation, no live comparison attached.
        "completeness": None,
    }


# ---------------------------------------------------------------------------
# Completeness diff — "what is left to finish this environment".
#
# Merges the slice-1 live variable-NAME read (railway.live_overview: the
# project-scoped RAILWAY_TOKEN, names dropped to a list at the client
# boundary — never values) into the slice-2 manifest so every schema row is
# badged set-live / missing-live, turning the owner-executed plan into a
# run-down checklist. Read-only annotation over the existing read path: no
# new Railway call shape, no mutation, and the copyable plan blocks
# (commands_text / manifest_json) stay the pure committed-registry artifact.
# ---------------------------------------------------------------------------

LIVE_SET = "set-live"
LIVE_MISSING = "missing-live"
LIVE_UNKNOWN = "unknown"

# The one group the project-scoped RAILWAY_TOKEN can see (its own scope pins
# it — docs/RAILWAY-SAFETY.md). Every other group's live truth is unknowable
# from here and is badged so, never assumed.
LIVE_GROUP_ID = "superbot-websites"


def annotate_completeness(
    manifest_data: dict[str, Any], live: dict[str, Any] | None
) -> None:
    """Badge every env-var schema row of a generated manifest against the
    live Railway variable-NAME snapshot: ``set-live`` / ``missing-live``,
    or the honest ``unknown`` whenever the live truth is not knowable.
    Mutates ``manifest_data`` in place — each service gains a ``live``
    annotation (``by_name`` status map + note), the manifest gains a
    group-level ``completeness`` summary.

    Honesty rules — a green/red badge is never fabricated:

    - no live snapshot / token unset / read failed → every row ``unknown``
      with the exact reason;
    - a group outside the token's scope (only ``superbot-websites`` is
      readable) → ``unknown``;
    - a per-service variables fetch error → that service's rows ``unknown``;
    - the live project read SUCCEEDED but the service is absent from it →
      the service is not created yet, so every recorded name is honestly
      ``missing-live`` (exactly the checklist's job);
    - otherwise: name in the live set → ``set-live``, else ``missing-live``.

    NAMES ONLY: the live snapshot's ``variable_names`` lists are all this
    function reads — the values were dropped at the client boundary
    (``railway._names_only``) and do not exist here to leak.
    """
    group = manifest_data["group"]
    services = manifest_data["services"]
    total = sum(len(svc["schema"]) for svc in services)

    def _all_unknown(reason: str, state: str) -> None:
        for svc in services:
            svc["live"] = {
                "known": False,
                "note": "",
                "by_name": {row["name"]: LIVE_UNKNOWN for row in svc["schema"]},
                "set_count": 0,
            }
        manifest_data["completeness"] = {
            "comparable": False,
            "state": state,
            "reason": reason,
            "set_count": 0,
            "known_total": 0,
            "unknown_count": total,
            "total": total,
        }

    if live is None:
        _all_unknown("live comparison not performed", "not-read")
        return
    if group["id"] != LIVE_GROUP_ID:
        _all_unknown(
            "no live read exists for this group — the project-scoped "
            f"RAILWAY_TOKEN reads {LIVE_GROUP_ID} only "
            "(docs/RAILWAY-SAFETY.md); live status is unknown here, "
            "never assumed",
            "out-of-scope",
        )
        return
    if live.get("state") != "ok":
        _all_unknown(
            live.get("reason")
            or f"live Railway read state: {live.get('state', '?')}",
            str(live.get("state", "?")),
        )
        return

    by_service = {s.get("name"): s for s in live.get("services", [])}
    set_count = 0
    known_total = 0
    for svc in services:
        rows = svc["schema"]
        lsvc = by_service.get(svc["surface"]["name"])
        if lsvc is None:
            # The authoritative live service list came back without this
            # service: it is not created yet — every recorded name is
            # honestly missing live.
            svc["live"] = {
                "known": True,
                "note": (
                    "service not found in the live project — the live read "
                    "succeeded, so this service (and every variable below) "
                    "is not created yet"
                ),
                "by_name": {row["name"]: LIVE_MISSING for row in rows},
                "set_count": 0,
            }
            known_total += len(rows)
            continue
        if lsvc.get("error"):
            svc["live"] = {
                "known": False,
                "note": (
                    "live variables read failed for this service: "
                    f"{lsvc['error']} — its rows stay unknown, not guessed"
                ),
                "by_name": {row["name"]: LIVE_UNKNOWN for row in rows},
                "set_count": 0,
            }
            continue
        live_names = set(lsvc.get("variable_names", []))
        by_name = {
            row["name"]: (
                LIVE_SET if row["name"] in live_names else LIVE_MISSING
            )
            for row in rows
        }
        n_set = sum(1 for status in by_name.values() if status == LIVE_SET)
        svc["live"] = {
            "known": True,
            "note": "",
            "by_name": by_name,
            "set_count": n_set,
        }
        set_count += n_set
        known_total += len(rows)

    manifest_data["completeness"] = {
        "comparable": known_total > 0,
        "state": "ok",
        "reason": (
            ""
            if known_total == total
            else "some services' live variables could not be read"
        ),
        "set_count": set_count,
        "known_total": known_total,
        "unknown_count": total - known_total,
        "total": total,
        "fetched_at": live.get("fetched_at", ""),
        "cached": bool(live.get("cached")),
        "project_name": live.get("project_name", ""),
    }


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
