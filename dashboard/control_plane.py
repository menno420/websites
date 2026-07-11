"""Controller seam for the /admin bot-management flows — DRY-RUN ONLY.

This module is the deliberate seam between the management UX and any future
armed transport. The **only** implementation in this service is
:class:`DryRunController`: it validates a requested action against the bot's
live typed schema (the committed ``dashboard.json`` feed), builds the exact
contract-v1 request JSON that a wired client WOULD send (spec:
``docs/specs/bot-control-api-v1.md``; machine pin:
``dashboard/bot_control_contract.json``), and records confirmed actions to an
**in-memory, per-process audit log** — nothing is ever sent anywhere.

Why dry-run is the ceiling here, permanently: owner decision Q-0004 (where
live bot control lives) is OPEN, and repo doctrine places a wired control
panel in a **separate service**, never on this read-only surface. This
service therefore holds no control endpoint, no token, no OAuth secret, and
no write path of any kind — enforced by
``dashboard/tests/test_dashboard.py::test_no_control_api_token_or_url_anywhere``.

The audit log lives in process memory only and clears on restart/redeploy —
the templates say so honestly.
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any

from . import data_source as ds

CONTRACT_FILE = Path(__file__).resolve().parent / "bot_control_contract.json"

# The actor identity a wired client would put here comes from Discord OAuth.
# OAuth is not configured on this deployment (and never will be on THIS
# service — see the module docstring), so the actor is honestly anonymous.
ANONYMOUS_ACTOR = {"discord_user_id": None, "display": "anonymous (OAuth not configured)"}

# Actions the /admin UI can build previews for. submission.moderate is in the
# contract but deliberately NOT here — it stays gated on rework-plan Q5.
UI_ACTIONS = ("setting.write", "cog.set_enabled", "help.appearance.set")

HELP_ENTITY_TYPES = ("command", "subsystem", "home_message")


class ActionRejected(Exception):
    """A requested action failed validation against the typed schema/contract."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def load_control_contract() -> dict[str, Any]:
    """The pinned bot-control-API v1 contract this service previews against."""
    return json.loads(CONTRACT_FILE.read_text(encoding="utf-8"))


def contract_issue(request: dict[str, Any]) -> str:
    """'' when a built request matches the pinned v1 contract, else a message."""
    try:
        contract = load_control_contract()
    except (OSError, json.JSONDecodeError) as exc:  # pragma: no cover - repo file
        return f"pinned control contract unreadable ({exc})"
    if set(request) != set(contract.get("request", [])):
        return "request envelope keys do not match the pinned contract"
    if request.get("schema_version") != contract.get("version"):
        return (
            f"request schema_version={request.get('schema_version')!r} but the "
            f"pinned contract is v{contract.get('version')}"
        )
    action = request.get("action")
    spec = contract.get("actions", {}).get(action)
    if spec is None:
        return f"action {action!r} is not in the pinned contract"
    params = request.get("params")
    if not isinstance(params, dict) or set(params) != set(spec.get("params", [])):
        return f"params for {action!r} do not match the pinned contract"
    actor = request.get("actor")
    if not isinstance(actor, dict) or set(actor) != set(contract.get("actor", [])):
        return "actor shape does not match the pinned contract"
    return ""


# ---------------------------------------------------------------------------
# Typed validation against the LIVE dashboard.json shapes. Defensive like the
# rest of the data layer: every failure is an honest ActionRejected, never a
# silent coercion.
# ---------------------------------------------------------------------------
def _validate_guild_id(raw: str) -> str:
    gid = (raw or "").strip()
    if not gid.isdigit() or not (5 <= len(gid) <= 25):
        raise ActionRejected(
            "unknown_guild",
            "guild id must be the numeric Discord server id (digits only) — "
            "the feeds carry no guild list, so it cannot be looked up here",
        )
    return gid


def _find_setting(data: dict[str, Any], domain: str, key: str) -> dict[str, Any]:
    for dom in ds.settings(data):
        if dom.get("domain") == domain:
            for k in dom.get("keys") or []:
                if k.get("key") == key:
                    return k
            raise ActionRejected(
                "unknown_setting", f"setting key {key!r} is not in domain {domain!r}"
            )
    raise ActionRejected("unknown_setting", f"settings domain {domain!r} is not in the feed")


def _coerce_setting_value(spec: dict[str, Any], raw: str) -> Any:
    """Coerce a form string into the setting's typed value, or reject honestly."""
    allowed = spec.get("allowed_values") or []
    if allowed:
        for v in allowed:
            if raw == str(v):
                return v
        raise ActionRejected(
            "invalid_value",
            f"value {raw!r} is not one of the allowed values: {', '.join(str(v) for v in allowed)}",
        )
    typ = (spec.get("type") or "str").lower()
    if typ == "bool":
        if raw in ("true", "false"):
            return raw == "true"
        raise ActionRejected("invalid_value", f"value {raw!r} is not a bool (expected true/false)")
    if typ == "int":
        try:
            return int(raw.strip())
        except (ValueError, AttributeError):
            raise ActionRejected("invalid_value", f"value {raw!r} is not an int")
    if typ == "float":
        try:
            return float(raw.strip())
        except (ValueError, AttributeError):
            raise ActionRejected("invalid_value", f"value {raw!r} is not a float")
    return raw


def _build_params(action: str, form: dict[str, str], data: dict[str, Any]) -> dict[str, Any]:
    """Validate raw form fields against the live feed; return typed action params."""
    if action == "setting.write":
        gid = _validate_guild_id(form.get("guild_id", ""))
        domain = (form.get("domain") or "").strip()
        key = (form.get("key") or "").strip()
        spec = _find_setting(data, domain, key)
        value = _coerce_setting_value(spec, form.get("value", ""))
        return {"guild_id": gid, "domain": domain, "key": key, "value": value}

    if action == "cog.set_enabled":
        gid = _validate_guild_id(form.get("guild_id", ""))
        name = (form.get("cog") or "").strip()
        enabled_raw = form.get("enabled", "")
        entry = next((c for c in ds.cogs(data) if c.get("cog") == name), None)
        if entry is None:
            raise ActionRejected("unknown_cog", f"cog {name!r} is not in the feed's cog inventory")
        if not entry.get("is_cog"):
            raise ActionRejected("not_a_cog", f"{name!r} is a module, not a loadable cog")
        if enabled_raw not in ("true", "false"):
            raise ActionRejected("invalid_params", "enabled must be true or false")
        return {"guild_id": gid, "cog": name, "enabled": enabled_raw == "true"}

    if action == "help.appearance.set":
        gid = _validate_guild_id(form.get("guild_id", ""))
        entity_type = (form.get("entity_type") or "").strip()
        entity = (form.get("entity") or "").strip()
        if entity_type not in HELP_ENTITY_TYPES:
            raise ActionRejected(
                "invalid_params",
                f"entity_type must be one of: {', '.join(HELP_ENTITY_TYPES)}",
            )
        if entity_type == "command":
            if entity not in ds.command_names(data):
                raise ActionRejected("unknown_entity", f"command {entity!r} is not in the feed")
        elif entity_type == "subsystem":
            if entity not in {c.get("key") for c in ds.catalogue(data)}:
                raise ActionRejected("unknown_entity", f"subsystem {entity!r} is not in the feed")
        else:  # home_message — a singleton; no entity name applies
            entity = ""
        changes: dict[str, Any] = {}
        if form.get("hidden") == "true":
            changes["hidden"] = True
        if (form.get("display_name") or "").strip():
            changes["display_name"] = form["display_name"].strip()
        if (form.get("description") or "").strip():
            changes["description"] = form["description"].strip()
        if not changes:
            raise ActionRejected(
                "no_changes", "at least one change (hide / rename / re-describe) is required"
            )
        return {"guild_id": gid, "entity_type": entity_type, "entity": entity, "changes": changes}

    raise ActionRejected(
        "invalid_action",
        f"action {action!r} cannot be previewed here"
        + (" — submission moderation stays gated on Q5" if action == "submission.moderate" else ""),
    )


def _utc_stamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


class DryRunController:
    """The only controller in this service. Mode is fixed: ``"dry-run"``.

    ``build_request`` validates an action against the typed schema derived
    from the live ``dashboard.json`` and returns the exact contract-v1
    request JSON that a wired client WOULD send (with ``dry_run: true`` and
    the honest anonymous actor). ``record`` appends a confirmed action to the
    in-memory audit log. No transport exists; nothing leaves the process.
    """

    mode = "dry-run"

    def __init__(self) -> None:
        self._entries: list[dict[str, Any]] = []
        self._next_id = 1

    def build_request(
        self,
        action: str,
        form: dict[str, str],
        data: dict[str, Any],
        *,
        idempotency_key: str | None = None,
        requested_at: str | None = None,
    ) -> dict[str, Any]:
        params = _build_params(action, form, data)
        request = {
            "schema_version": 1,
            "action": action,
            "params": params,
            "dry_run": True,
            "actor": dict(ANONYMOUS_ACTOR),
            "idempotency_key": idempotency_key or uuid.uuid4().hex,
            "requested_at": requested_at or _utc_stamp(),
        }
        issue = contract_issue(request)
        if issue:  # pragma: no cover - guards a code/contract drift, not user input
            raise ActionRejected("invalid_params", f"built request violates the pinned contract: {issue}")
        return request

    def record(self, request: dict[str, Any]) -> dict[str, Any]:
        entry = {
            "id": self._next_id,
            "time": _utc_stamp(),
            "actor": request.get("actor", {}).get("display", ""),
            "action": request.get("action", ""),
            "guild_id": request.get("params", {}).get("guild_id", ""),
            "request": request,
            "outcome": "dry-run: recorded, not sent",
        }
        self._next_id += 1
        self._entries.append(entry)
        return entry

    def entries(self) -> list[dict[str, Any]]:
        return list(self._entries)

    def clear(self) -> None:
        self._entries.clear()
        self._next_id = 1


# One per-process controller. In-memory by design: the audit log is a preview
# tool, not a store — it clears on restart/redeploy and the pages say so.
controller = DryRunController()
