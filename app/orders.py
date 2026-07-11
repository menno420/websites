"""Orders view (/orders): every fleet repo's ``control/inbox.md`` ORDER
blocks, cross-referenced against that repo's own heartbeat.

ORDER 009's route-surface audit named per-repo inbox ORDER texts as browsable
nowhere — and the fleet protocol makes raw inboxes deliberately hard to read
at a glance: **orders stay ``status: new`` forever** (the manager is the
inbox's one writer and rarely flips them), so execution state lives ONLY in
each lane's ``control/status*.md`` ``orders: acked=… done=…`` line. This page
does the cross-reference the protocol otherwise asks every reader to do by
hand: parse each repo's ORDER blocks, parse each of its lanes' status orders
lines (the D-0028 ``fleet.parse_orders`` — outstanding = acked minus done),
and badge every order honestly:

- **done** — the order id appears in a lane status ``done=`` list;
- **claimed** — not done, but named in a lane's ``claimed-by:`` annotation
  (the claim ritual's in-between state);
- **open** — not done and unclaimed (real outstanding work);
- **unknown** — the repo has orders but NO readable status file, so
  execution state cannot be known (never guessed).

Lane set derives from the same live fleet-manifest ``/fleet`` uses
(``fleet.resolve_lanes`` — fallback stays honest); repos dedupe (a
shared-repo cohabitation like superbot-games has one inbox but several
status files — every lane's ``done=`` counts). Repos with no inbox render as
an honest absence; fetch failures as banners; the route always answers 200.
READ-ONLY toward every repo, same TTL-cached ``github`` layer.
"""

from __future__ import annotations

import asyncio
import re
from datetime import datetime, timezone
from typing import Any, Optional

from . import clock, config, fleet, github, journal

INBOX_PATH = "control/inbox.md"

# `## ORDER 007 · 2026-07-10T02:04:55Z · status: new`
_ORDER_HEAD_RE = re.compile(
    r"^#{2,3}\s*ORDER\s+(\d+)\s*(?:·\s*([0-9T:\-Z.+ ]+?))?\s*(?:·\s*status:\s*(\w+))?\s*$",
    re.IGNORECASE,
)
# Field lines inside a block: `priority: P1`, `do: …`, `why: …`, `done-when: …`
_FIELD_KEYS = {"priority", "do", "why", "done-when", "done_when"}

MAX_ORDERS_PER_REPO = 50


def _gh_blob(repo: str, path: str) -> str:
    return f"https://github.com/{config.OWNER}/{repo}/blob/main/{path}"


def parse_inbox(text: str) -> list[dict[str, Any]]:
    """Parse an inbox's ``## ORDER <nnn> · <ISO> · status: <s>`` blocks.

    Returns one dict per order: ``{id, issued, inbox_status, fields, body}``
    where ``fields`` maps the documented keys (priority/do/why/done-when) and
    ``body`` is the block's raw text (the page renders it in a collapsible so
    a long ``do:`` never hides). Non-ORDER headings end the current block.
    Tolerant: a malformed line becomes continuation text, never a crash.
    """
    orders: list[dict[str, Any]] = []
    cur: Optional[dict[str, Any]] = None
    cur_field: Optional[str] = None

    for line in (text or "").splitlines():
        stripped = line.strip()
        m = _ORDER_HEAD_RE.match(stripped)
        if m:
            if len(orders) >= MAX_ORDERS_PER_REPO:
                break
            cur = {
                "id": m.group(1),
                "issued": (m.group(2) or "").strip(),
                "inbox_status": (m.group(3) or "").strip().lower(),
                "fields": {},
                "body_lines": [stripped],
            }
            cur_field = None
            orders.append(cur)
            continue
        if stripped.startswith("#"):
            cur = None  # a non-ORDER heading closes the block
            cur_field = None
            continue
        if cur is None:
            continue
        cur["body_lines"].append(line)
        if ":" in stripped:
            key, _, value = stripped.partition(":")
            nk = key.strip().lower().replace("_", "-")
            if nk in _FIELD_KEYS or nk == "done-when":
                cur["fields"][nk] = value.strip()
                cur_field = nk
                continue
        if cur_field is not None and stripped:
            cur["fields"][cur_field] = (
                f"{cur['fields'][cur_field]} {stripped}".strip()
            )

    for o in orders:
        o["body"] = "\n".join(o.pop("body_lines")).strip()
    return orders


def classify_order(
    order_id: str,
    statuses: list[dict[str, Any]],
    now: Optional[datetime] = None,
) -> dict[str, Any]:
    """One order id against every lane status of its repo → execution state.

    ``statuses`` items are ``{lane, orders_info}`` (the D-0028 parse). done
    beats claimed beats open; a repo with zero readable statuses → unknown.
    A claimed order additionally carries **claim aging**: ``claim_stale`` is
    True past ``config.CLAIM_STALE_HOURS`` (~24h — the claim ritual's own
    expiry rule: a claim with no visible activity may be treated as abandoned
    and re-claimed; a dead lane must never deadlock an order), with
    ``claim_age_human`` for display. A claim whose timestamp did not parse
    ages honestly as unknown (never flagged stale on a guess).
    """
    base = {"claim_stale": False, "claim_age_human": "", "claimed_at": None}
    if not statuses:
        return {"state": "unknown", "by": "", **base}
    now = now or clock.now()
    claimed_by = ""
    claimed_at: Optional[str] = None
    for s in statuses:
        info = s["orders_info"]
        if order_id in info["done"]:
            return {"state": "done", "by": s["lane"], **base}
        claim = info.get("claimed") or ""
        # A claim reads `claimed-by: <ids> <lane> <ISO>` — the id spec is the
        # FIRST token (`009`, `007+008`, `007,008`). Compare numerically so
        # padding differences can't miss, and never scan the free text (a
        # bare regex over the whole claim matched ids inside the ISO
        # timestamp — the `00` in `21:00Z` — a caught false-positive class).
        if claim:
            spec = claim.split()[0] if claim.split() else ""
            ids = {t for t in re.split(r"[+,/]", spec) if t.isdigit()}
            try:
                if any(int(t) == int(order_id) for t in ids):
                    if not claimed_by:
                        claimed_by = f"{s['lane']}: {claim}"
                        claimed_at = info.get("claimed_at")
            except ValueError:
                pass
    if claimed_by:
        out = {"state": "claimed", "by": claimed_by, **base}
        out["claimed_at"] = claimed_at
        dt = fleet._parse_iso(claimed_at or "")
        if dt is not None:
            age_hours = (now - dt).total_seconds() / 3600
            out["claim_age_human"] = fleet._human_age(age_hours)
            out["claim_stale"] = age_hours >= config.CLAIM_STALE_HOURS
        return out
    return {"state": "open", "by": "", **base}


async def _repo_orders(
    repo: str,
    lanes: list[dict[str, Any]],
    refresh: bool = False,
    now: Optional[datetime] = None,
) -> dict[str, Any]:
    """One repo's inbox card: parsed orders + per-lane status cross-reference."""
    now = now or clock.now()
    status_paths = [(l["lane"], l["status_path"]) for l in lanes]
    fetches = await asyncio.gather(
        github.fetch_file(repo, INBOX_PATH, refresh=refresh),
        *[github.fetch_file(repo, p, refresh=refresh) for _, p in status_paths],
    )
    inbox_res, status_res = fetches[0], fetches[1:]

    statuses: list[dict[str, Any]] = []
    for (lane_name, _path), res in zip(status_paths, status_res):
        if res["ok"] and isinstance(res["data"], str) and res["data"].strip():
            parsed = fleet.parse_status(res["data"], lane_name)
            statuses.append(
                {
                    "lane": lane_name,
                    "orders_info": fleet.parse_orders(
                        parsed["fields"].get("orders", "")
                    ),
                }
            )

    out: dict[str, Any] = {
        "repo": repo,
        "inbox_url": _gh_blob(repo, INBOX_PATH),
        "repo_url": f"https://github.com/{config.OWNER}/{repo}",
        "missing": False,
        "fetch_error": None,
        "status_readable": bool(statuses),
        "orders": [],
        "open_count": 0,
        "claimed_count": 0,
        "done_count": 0,
        "unknown_count": 0,
    }

    if not (
        inbox_res["ok"]
        and isinstance(inbox_res["data"], str)
        and inbox_res["data"].strip()
    ):
        if inbox_res.get("status") == 404:
            out["missing"] = True  # honest absence — many repos have no inbox
        else:
            out["fetch_error"] = (
                inbox_res.get("error") or f"HTTP {inbox_res.get('status')}"
            )
        return out

    for order in parse_inbox(inbox_res["data"]):
        cls = classify_order(order["id"], statuses, now=now)
        order["state"] = cls["state"]
        order["state_by"] = cls["by"]
        order["claim_stale"] = cls["claim_stale"]
        order["claim_age_human"] = cls["claim_age_human"]
        lat = pickup_latency(order.get("issued", ""), cls.get("claimed_at"))
        order["pickup_latency_mins"] = lat["mins"]
        order["pickup_latency_human"] = lat["human"]
        order["body_html"] = journal.render_markdown(order["body"])
        out["orders"].append(order)
        out[f"{cls['state']}_count"] += 1
    return out


def pickup_latency(issued: str, claimed_at: Optional[str]) -> dict[str, Any]:
    """filed→claimed latency — the fleet's order-routing SLO, finally visible.

    Both timestamps already live in the data /orders parses (the ORDER
    header's issued stamp; the lane claim's ISO token); this subtracts
    them. Honest on any miss: an unparseable/absent stamp or a negative
    delta (clock skew between two hand-written timestamps) yields
    ``{"mins": None, "human": ""}`` — latency is never guessed.
    """
    filed = fleet._parse_iso(issued or "")
    claimed = fleet._parse_iso(claimed_at or "")
    if filed is None or claimed is None:
        return {"mins": None, "human": ""}
    mins = (claimed - filed).total_seconds() / 60
    if mins < 0:
        return {"mins": None, "human": ""}
    return {"mins": round(mins, 1), "human": fleet._human_age(mins / 60)}


def _sort_key(card: dict[str, Any]) -> tuple:
    """Attention-first: fetch errors, then open orders (most first), then
    claimed, then all-done, then unknown-state, then no-inbox repos."""
    if card["fetch_error"]:
        return (0, 0)
    if card["open_count"]:
        return (1, -card["open_count"])
    if card["claimed_count"]:
        return (2, -card["claimed_count"])
    if card["unknown_count"]:
        return (3, 0)
    if card["orders"]:
        return (4, -card["done_count"])
    return (5, 0)


async def overview(
    refresh: bool = False, now: datetime | None = None
) -> dict[str, Any]:
    """Every fleet repo's inbox orders, cross-referenced and attention-sorted.

    Repos derive from the live manifest lane set (deduped — one inbox per
    repo, every cohabiting lane's status counts) plus honest ``lane_source``
    passthrough. Never raises for upstream failures; the route stays 200.
    ``now`` is injectable (module convention) so fixed-stamp test fixtures
    stay deterministic.
    """
    now = now or clock.now()
    lane_defs, lane_source = await fleet.resolve_lanes(refresh=refresh)
    by_repo: dict[str, list[dict[str, Any]]] = {}
    for lane in lane_defs:
        by_repo.setdefault(lane["repo"], []).append(lane)

    cards = list(
        await asyncio.gather(
            *[
                _repo_orders(repo, lanes, refresh=refresh, now=now)
                for repo, lanes in sorted(by_repo.items())
            ]
        )
    )
    cards.sort(key=_sort_key)

    summary = {
        "repos": len(cards),
        "with_inbox": sum(1 for c in cards if c["orders"] or c["fetch_error"]),
        "open": sum(c["open_count"] for c in cards),
        "claimed": sum(c["claimed_count"] for c in cards),
        "done": sum(c["done_count"] for c in cards),
        "unknown": sum(c["unknown_count"] for c in cards),
        "errored": sum(1 for c in cards if c["fetch_error"]),
        # Claim aging (the ritual's ~24h expiry): stale claims fleet-wide.
        "stale_claims": sum(
            1 for c in cards for o in c["orders"] if o.get("claim_stale")
        ),
    }
    return {"cards": cards, "summary": summary, "lane_source": lane_source}
