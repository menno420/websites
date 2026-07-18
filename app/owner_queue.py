"""Owner queue view (/queue): every ⚑ needs-owner ask on ONE surface.

ORDER 005 (fleet manager, P1): the owner asked for one place to see everything
he needs to do. Two halves feed it:

1. **Fleet lanes** — every lane's ``⚑ needs-owner`` field, already fetched and
   parsed by ``fleet.overview()`` (the /fleet.json data). This module REUSES that
   pipeline (same TTL cache, same parse) — it never refetches or reparses lane
   status files independently.
2. **The manager's curated queue** — ``menno420/fleet-manager
   docs/owner-queue.md``. fleet-manager is PRIVATE: agent sessions cannot read
   it, and the deployed control-plane can only read it at runtime via
   ``GITHUB_TOKEN`` — which may be unset. Both cases degrade honestly (a clear
   "not configured / unavailable" state), never a 500, never fabricated items.

Items carrying the fleet's six-field OWNER-ACTION format
(WHAT/WHERE/HOW/WHY-IT-MATTERS/UNBLOCKS/VERIFIED-NEEDED) are parsed into
structured cards; anything else renders as an honest free-text ask. The
combined list is **deduplicated** (normalized WHAT/text; every source kept on
the surviving item) and ordered **newest first** by the source lane's heartbeat
timestamp — items with no parseable date (the fleet-manager doc has none) sort
after the dated ones, labeled honestly, never given an invented time.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Optional

from . import config, fleet, github, journal, listfilter

FLEET_MANAGER_REPO = "fleet-manager"
OWNER_QUEUE_PATH = "docs/owner-queue.md"

# A ⚑ OWNER-ACTION block marker. Lane status parsing flattens continuation
# lines into one string, so the marker can appear mid-line; owner-queue.md is
# raw markdown where it starts a line. Both split the same way.
_BLOCK_RE = re.compile(r"⚑\s*OWNER-ACTION\b")

# Stable ask id (``ID: ASK-NNNN``), written directly under the ⚑ marker —
# append-only, never reused (scheme note atop docs/owner/OWNER-ACTIONS.md's
# Open section). Only the header region before the first six-field label is
# scanned, so an ask's prose MENTIONING another ask's id never binds.
_ID_RE = re.compile(r"\bID\s*:\s*(ASK-\d{4})\b")

# Six-field labels (control/README.md § OWNER-ACTION format). Tolerates
# markdown emphasis around the label (``**WHAT:**``) and flattened one-line
# blocks. WHY-IT-MATTERS is stored under the short key ``why``.
_FIELD_RE = re.compile(
    r"\*{0,2}\b(WHAT|WHERE|HOW|WHY-IT-MATTERS|UNBLOCKS|VERIFIED-NEEDED)\b\*{0,2}\s*:\*{0,2}"
)
_FIELD_KEYS = {
    "WHAT": "what",
    "WHERE": "where",
    "HOW": "how",
    "WHY-IT-MATTERS": "why",
    "UNBLOCKS": "unblocks",
    "VERIFIED-NEEDED": "verified",
}
# Render order for the structured table (what is the headline, not a row).
FIELD_ORDER = [
    ("where", "WHERE"),
    ("how", "HOW"),
    ("why", "WHY-IT-MATTERS"),
    ("unblocks", "UNBLOCKS"),
    ("verified", "VERIFIED-NEEDED"),
]


def _is_none_ask(text: str) -> bool:
    """True when a needs-owner value means "nothing to ask" (``none``, empty,
    or a placeholder dash)."""
    t = (text or "").strip().strip("`").strip()
    return not t or t.lower().rstrip(".") in ("none", "-", "—", "n/a")


def _clean(value: str) -> str:
    """Collapse whitespace (flattened lane values arrive space-joined anyway)."""
    return " ".join((value or "").split())


def _parse_block(block: str) -> dict[str, str]:
    """Parse one OWNER-ACTION block's labeled fields (missing fields omitted —
    rendered as absent, never invented). A stable ``ID: ASK-NNNN`` line in
    the block header lands under ``ask_id``; legacy blocks without one simply
    lack the key — every consumer treats it as absent-safe."""
    fields: dict[str, str] = {}
    matches = list(_FIELD_RE.finditer(block))
    head = block[: matches[0].start()] if matches else block
    id_match = _ID_RE.search(head)
    if id_match:
        fields["ask_id"] = id_match.group(1)
    for i, m in enumerate(matches):
        key = _FIELD_KEYS[m.group(1)]
        end = matches[i + 1].start() if i + 1 < len(matches) else len(block)
        value = _clean(block[m.end() : end])
        if value and key not in fields:
            fields[key] = value
    return fields


def parse_owner_actions(text: str) -> tuple[str, list[dict[str, str]]]:
    """Split a needs-owner value / owner-queue document into (preamble, blocks).

    ``preamble`` is any free text before the first ``⚑ OWNER-ACTION`` marker
    (empty when the whole value is blocks or means "none"). ``blocks`` is one
    parsed field-dict per marker. A value with NO markers yields
    ``(text, [])`` — the caller treats the whole text as one free-text ask.
    """
    if _is_none_ask(text):
        return "", []
    parts = _BLOCK_RE.split(text)
    preamble = _clean(parts[0])
    if _is_none_ask(preamble):
        preamble = ""
    blocks = [b for b in (_parse_block(p) for p in parts[1:]) if b]
    return preamble, blocks


def _dedup_key(item: dict[str, Any]) -> str:
    """Duplicate detection key: the normalized WHAT (or the free text)."""
    basis = item.get("what") or item.get("text") or ""
    return " ".join(basis.lower().split())


def _lane_source(lane: dict[str, Any]) -> dict[str, Any]:
    fresh = lane.get("freshness") or {}
    return {
        "kind": "lane",
        "label": lane["lane"],
        "url": lane.get("github_url", ""),
        "updated_iso": fresh.get("iso") or "",
        "age_hours": fresh.get("age_hours"),
        "age_human": fresh.get("age_human", "age unknown"),
    }


def _fm_source() -> dict[str, Any]:
    return {
        "kind": "fleet-manager",
        "label": f"{FLEET_MANAGER_REPO}/{OWNER_QUEUE_PATH}",
        "url": (
            f"https://github.com/{config.OWNER}/{FLEET_MANAGER_REPO}"
            f"/blob/main/{OWNER_QUEUE_PATH}"
        ),
        "updated_iso": "",
        "age_hours": None,
        "age_human": "date unknown",
    }


def _make_item(source: dict[str, Any], *, fields: Optional[dict] = None,
               text: str = "") -> dict[str, Any]:
    item: dict[str, Any] = {
        "what": (fields or {}).get("what", ""),
        "text": _clean(text),
        # Stable ask id when the block carries one (``ID: ASK-NNNN``);
        # None for legacy blocks — downstream matching stays absent-safe.
        "ask_id": (fields or {}).get("ask_id") or None,
        "fields": {
            k: v
            for k, v in (fields or {}).items()
            if k not in ("what", "ask_id")
        },
        "sources": [source],
    }
    return item


def _sort_key(item: dict[str, Any]) -> tuple:
    """Newest first by the (newest) source heartbeat; undated items last."""
    ages = [s["age_hours"] for s in item["sources"] if s["age_hours"] is not None]
    return (0, min(ages)) if ages else (1, 0.0)


# --------------------------------------------------------------------------- #
# ORDER 019 — /queue filter dimensions over the centralized listfilter core.
# The item record stores NO task/kind fields (completion lives upstream in the
# heartbeats), so KIND is DERIVED deterministically here and labeled as such.
# --------------------------------------------------------------------------- #

# Action-type classifier: first matching pattern wins, ``other`` is the honest
# fallback (never a guess dressed as certainty — the dimension says "derived").
# Underscores normalize to spaces first so GITHUB_TOKEN matches \btoken\b.
_ACTION_TYPES: list[tuple[str, re.Pattern]] = [
    ("token/secret", re.compile(
        r"\b(token|secret|pat|credentials?|api\s?-?key|password)\b", re.I)),
    ("money", re.compile(
        r"\$|\b(pay|payment|payout|paypal|budget|invoice|billing|price|cost)\b",
        re.I)),
    ("console/settings", re.compile(
        r"\b(console|settings?|configure|config|enable|toggle|click|panel"
        r"|railway|env|variable)\b", re.I)),
    ("decision/review", re.compile(
        r"\b(decide|decision|review|approve|choose|confirm|sign\s?-?off)\b",
        re.I)),
]


def classify_action(text: str) -> str:
    """Deterministic keyword classifier over an ask's WHAT/free text →
    ``token/secret`` / ``money`` / ``console/settings`` / ``decision/review``
    / ``other`` (first match wins, in that precedence order)."""
    t = (text or "").replace("_", " ")
    for label, rx in _ACTION_TYPES:
        if rx.search(t):
            return label
    return "other"


def item_kinds(item: dict[str, Any]) -> list[str]:
    """All derived KIND values of one queue item: its form (structured ``ask``
    vs free-text ``note``), each source kind (``lane`` / ``fleet-manager``),
    and its classified action type. Multi-valued on purpose — selecting any
    of them matches the item (OR within the dimension)."""
    kinds = ["ask" if item.get("what") else "note"]
    for src_kind in sorted({s.get("kind", "") for s in item.get("sources", [])}):
        if src_kind:
            kinds.append(src_kind)
    kinds.append(classify_action(
        f"{item.get('what', '')} {item.get('text', '')}"))
    return kinds


AGE_BUCKETS = ("<24h", "1-7d", ">7d", "undated")


def age_bucket(item: dict[str, Any]) -> str:
    """Bucket by the item's NEWEST source heartbeat age (the same min
    ``_sort_key`` orders by); no parseable date anywhere → ``undated``,
    never an invented time."""
    ages = [s["age_hours"] for s in item.get("sources", [])
            if s.get("age_hours") is not None]
    if not ages:
        return "undated"
    newest = min(ages)
    if newest < 24:
        return "<24h"
    if newest <= 7 * 24:
        return "1-7d"
    return ">7d"


def headline(item: dict[str, Any]) -> str:
    return item.get("what") or item.get("text") or ""


# --------------------------------------------------------------------------- #
# Durable ask id (C15) — a stable, content-derived identifier per ask.
#
# The gated writeback console targets an ask when the owner marks it complete /
# requests assistance / notes it. That identity used to be the ask's raw
# HEADLINE TEXT (its WHAT prose) — brittle: a rewording upstream (or two asks
# that normalize alike) could point a mark-complete at the wrong ask, or none.
# ``ask_uid`` derives a deterministic id from STABLE identifying content, never
# from the ask's POSITION in the ledger, so it is identical across a reorder of
# the ledger and stable across runs:
#
#   * the ledger's ``ID: ASK-NNNN`` when the block carries one (``ask_id``) —
#     so the id survives even a rewording of the ask's WHAT;
#   * else the normalized headline (the SAME basis ``_dedup_key`` merges on),
#     hashed — the best available stable identity for an id-less ask.
#
# Distinct asks get distinct ids (different basis → different digest); the same
# ask keeps one id wherever it appears. A contentless item hashes to '' (there
# is nothing stable to key on — the caller treats it as unresolvable).
# --------------------------------------------------------------------------- #
def ask_uid(item: dict[str, Any]) -> str:
    """A durable, content-derived identifier for one owner ask (see above)."""
    basis = item.get("ask_id") or _dedup_key(item)
    if not basis:
        return ""
    digest = hashlib.sha256(basis.encode("utf-8")).hexdigest()[:12]
    return f"ask-{digest}"


def resolve_uid(
    items: list[dict[str, Any]], uid: str
) -> Optional[dict[str, Any]]:
    """The item whose durable :func:`ask_uid` equals ``uid``, or ``None``.

    Resolution is by durable content id, never by position — reordering or
    removing other asks never changes which ask a uid points at. An unknown
    uid returns ``None`` (the caller rejects it safely; it never falls through
    to some other ask). An empty uid resolves to ``None``."""
    if not uid:
        return None
    for it in items:
        if ask_uid(it) == uid:
            return it
    return None


# Age-section metadata for the default /queue view (list-IA, 2026-07-12):
# stable bucket key -> (anchor slug, section label). Anchors are jump targets
# from the page's summary header; slugs are fixed here so the header links
# and the sections can never drift apart.
AGE_GROUP_META = {
    "<24h": ("age-fresh", "last 24 hours"),
    "1-7d": ("age-week", "1–7 days old"),
    ">7d": ("age-old", "older than 7 days"),
    "undated": ("age-undated", "undated"),
}


def group_by_age(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Partition an (already ordered) item list into age-bucket sections.

    Order-preserving within each bucket, buckets in fixed freshest-first
    order, empty buckets omitted. Meant for the DEFAULT newest-first view
    only — the newest-first sort keys on the same min source age, so the
    sections read contiguously; the route skips grouping the moment any
    filter/sort/search is active (an explicit ordering beats sections)."""
    buckets: dict[str, list[dict[str, Any]]] = {k: [] for k in AGE_BUCKETS}
    for it in items:
        buckets[age_bucket(it)].append(it)
    groups = []
    for key in AGE_BUCKETS:
        if not buckets[key]:
            continue
        anchor, label = AGE_GROUP_META[key]
        groups.append(
            {"key": key, "anchor": anchor, "label": label, "items": buckets[key]}
        )
    return groups


def _sort_key_oldest(item: dict[str, Any]) -> tuple:
    """Oldest dated first; undated items still last (their age is unknown,
    not infinite)."""
    ages = [s["age_hours"] for s in item["sources"] if s["age_hours"] is not None]
    return (0, -min(ages)) if ages else (1, 0.0)


def _search_text(item: dict[str, Any]) -> str:
    parts = [item.get("what", ""), item.get("text", "")]
    parts.extend((item.get("fields") or {}).values())
    parts.extend(s.get("label", "") for s in item.get("sources", []))
    return " ".join(parts)


FILTER_SPEC = listfilter.ListSpec(
    path="/queue",
    dimensions=(
        listfilter.Dimension(
            key="project", label="project",
            get=lambda it: sorted({s["label"] for s in it.get("sources", [])}),
        ),
        listfilter.Dimension(
            key="kind", label="kind", derived=True,
            values=("ask", "note", "lane", "fleet-manager",
                    "token/secret", "console/settings", "decision/review",
                    "money", "other"),
            get=item_kinds,
        ),
        listfilter.Dimension(
            key="age", label="age", values=AGE_BUCKETS,
            get=lambda it: [age_bucket(it)],
        ),
    ),
    sorts=(
        # ``newest`` is the default and reproduces overview()'s own order
        # exactly (same key) — no params renders identically to before.
        listfilter.SortOption("newest", "newest", sort_key=_sort_key),
        listfilter.SortOption("oldest", "oldest", sort_key=_sort_key_oldest),
        listfilter.SortOption(
            "az", "A-Z", sort_key=lambda it: headline(it).casefold()),
    ),
    search=_search_text,
)


async def _fleet_manager_half(refresh: bool = False) -> dict[str, Any]:
    """Fetch + parse the manager's owner-queue.md, degrading honestly.

    States: ``ok`` (fetched; blocks parsed + full body rendered),
    ``not-configured`` (GITHUB_TOKEN unset on this service — the documented
    production state until the owner mints the PAT), ``unavailable`` (token
    present but the fetch failed — reason surfaced).
    """
    token_set = bool(config.GITHUB_TOKEN)
    fetch = await github.fetch_file(
        FLEET_MANAGER_REPO, OWNER_QUEUE_PATH, refresh=refresh
    )
    out: dict[str, Any] = {
        "token_set": token_set,
        "url": _fm_source()["url"],
        "items": [],
        "preamble": "",
        "body_html": "",
        "state": "ok",
        "reason": "",
    }
    if fetch["ok"] and isinstance(fetch["data"], str) and fetch["data"].strip():
        preamble, blocks = parse_owner_actions(fetch["data"])
        src = _fm_source()
        if blocks:
            out["items"] = [_make_item(src, fields=b) for b in blocks]
            out["preamble"] = preamble
        # No structured blocks -> NO list items from this doc (flattening a
        # whole markdown document into one giant "ask" would be noise, not an
        # item). The full rendered document below stays the honest surface;
        # the template labels the absence.
        out["body_html"] = journal.render_markdown(
            fetch["data"],
            source={"repo": FLEET_MANAGER_REPO, "path": OWNER_QUEUE_PATH},
        )
        return out
    reason = fetch.get("error") or f"HTTP {fetch.get('status')}"
    if not token_set:
        out["state"] = "not-configured"
        out["reason"] = (
            "GITHUB_TOKEN is not set on this service, and "
            f"{config.OWNER}/{FLEET_MANAGER_REPO} is private — the manager's "
            f"owner-queue cannot be read (fetch: {reason})"
        )
    else:
        out["state"] = "unavailable"
        out["reason"] = reason
    return out


async def overview(refresh: bool = False) -> dict[str, Any]:
    """The owner's single to-do surface: deduplicated, newest-first asks.

    Lane half rides ``fleet.overview()`` (shared fetch + parse + TTL cache);
    the fleet-manager half degrades honestly when the token is unset or the
    fetch fails. Duplicates (same normalized WHAT/text) merge into one item
    that keeps EVERY source; lanes whose status could not be fetched are
    counted so the page can say "asks may be missing", never pretend complete.
    """
    fleet_data = await fleet.overview(refresh=refresh)

    raw_items: list[dict[str, Any]] = []
    lane_notes: list[dict[str, str]] = []
    lanes_with_asks = 0
    for lane in fleet_data["lanes"]:
        raw = (lane.get("fields") or {}).get("needs-owner", "")
        preamble, blocks = parse_owner_actions(raw)
        if not preamble and not blocks:
            continue
        lanes_with_asks += 1
        src = _lane_source(lane)
        if blocks:
            raw_items.extend(_make_item(src, fields=b) for b in blocks)
            if preamble:
                # Context sentence before the blocks (e.g. a pointer to the
                # canonical list) — shown as a small lane note, not an ask.
                lane_notes.append({"lane": lane["lane"], "text": preamble})
        else:
            raw_items.append(_make_item(src, text=preamble))

    fm = await _fleet_manager_half(refresh=refresh)
    raw_items.extend(fm["items"])

    # Deduplicate: same normalized WHAT/text merges; every source is kept.
    merged: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for item in raw_items:
        key = _dedup_key(item)
        if not key:
            continue
        if key in merged:
            merged[key]["sources"].extend(item["sources"])
            # Prefer structured fields from whichever copy has them.
            for k, v in item["fields"].items():
                merged[key]["fields"].setdefault(k, v)
            if not merged[key].get("ask_id") and item.get("ask_id"):
                merged[key]["ask_id"] = item["ask_id"]
        else:
            merged[key] = item
            order.append(key)
    items = [merged[k] for k in order]
    items.sort(key=_sort_key)

    # Durable content id per ask (C15) — stable across this reorder and across
    # runs; the gated writeback console resolves its target by this id instead
    # of by the ask's raw headline text. Additive: /queue.json carries it
    # (contract-pinned) and every downstream consumer stays absent-safe.
    for it in items:
        it["uid"] = ask_uid(it)

    unreadable_lanes = [
        lane["lane"] for lane in fleet_data["lanes"] if lane.get("fetch_error")
    ]
    return {
        "items": items,
        "lane_notes": lane_notes,
        "fleet_manager": fm,
        "field_order": FIELD_ORDER,
        "summary": {
            "total": len(items),
            "deduped": len(raw_items) - len(items),
            "lanes_with_asks": lanes_with_asks,
            "lanes_total": fleet_data["summary"]["total"],
        },
        "unreadable_lanes": unreadable_lanes,
        "lane_source": fleet_data["lane_source"],
    }
