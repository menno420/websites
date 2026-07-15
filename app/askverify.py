"""Launch preflight verdicts — read-only auto-verification of the open
⚑ OWNER-ACTION asks ("auto-verified owner-actions", 2026-07-15 mission
slice).

The owner console lists the open asks as static ledger text; verifying an
errand (a pasted variable, a minted PAT, a flipped setting) has meant a
session hand-probing services. This module turns that into verdict chips on
the GATED owner surfaces (/owner, /owner/briefing, /owner/queue): a probe
REGISTRY keyed by stable keyword signatures is matched against the parsed
asks (the same ``owner_queue.parse_owner_actions`` output the briefing and
/queue already carry), and each matched ask gets one live probe.

HARD RAILS (coordinator-approved, binding):

* **Side-effect-free, always.** Every probe is a read: GETs through the
  existing TTL-cached github client, plus the one existing read-only
  Railway variable-NAME query (``railway.live_overview`` — queries only, no
  mutation strings exist in that module). The ORDER-020 contents-write PAT
  check reads ``permissions`` from ``GET /repos/<owner>/websites`` ONLY —
  it never attempts a write to find out. No secret VALUE is ever fetched or
  rendered: names and status codes only.

* **Honest-unknown beats inferred-done, everywhere.** The verdict ladder:

  - ``done-detected`` — a POSITIVE probe signal only (wording always
    carries "ledger update pending": the probe observes the world, the
    ledger row is still the human record to move);
  - ``still-open`` — the probe positively observed the not-done state;
  - ``not machine-checkable — <reason>`` — registered explicitly for asks
    that are product decisions or not externally observable, AND the
    honest state for any ask no registry entry matches (no fuzzy-match
    tuning — an unmatched ask stays unverified, with the reason);
  - ``unknown — <probe error>`` — the probe ran and could not tell
    (missing token, fetch failure, unexpected payload). Never a guess.

  A registry entry is claimed by AT MOST ONE ask per verification pass:
  if a second ask matches an already-claimed entry, the match is
  ambiguous and BOTH the second ask's chip says so honestly — a chip must
  never show done off an ambiguous signal.

Caching: every network read rides the house TTL cache (``github._get`` /
``railway.live_overview``) — ``refresh=True`` (the ``?refresh=1``
convention upstream) busts through exactly like every other page.

Layering: domain module — imports config + the client layers (github,
railway) only; routes and templates never imported. Zero new routes, zero
POST surface (the CSRF floor is untouched).
"""

from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable, Optional

from . import config, github, railway

# --------------------------------------------------------------------------- #
# Verdict ladder
# --------------------------------------------------------------------------- #
DONE = "done-detected"
STILL_OPEN = "still-open"
NOT_CHECKABLE = "not-machine-checkable"
UNKNOWN = "unknown"

# Chip presentation per rung (label prefix + the site's badge css class).
# done-detected deliberately carries "ledger update pending" in the LABEL —
# a positive probe never silently closes the human ledger row.
_CHIP = {
    DONE: ("done-detected — ledger update pending", "ok"),
    STILL_OPEN: ("still-open", "warn"),
    NOT_CHECKABLE: ("not machine-checkable", "unknown"),
    UNKNOWN: ("unknown", "unknown"),
}


def _verdict(
    verdict: str, detail: str, probe: str = "", url: str = ""
) -> dict[str, Any]:
    label, css = _CHIP[verdict]
    return {
        "verdict": verdict,
        "label": label,
        "css": css,
        "detail": github.short_reason(detail) if detail else "",
        "probe": probe,
        "url": url,
    }


# --------------------------------------------------------------------------- #
# Probes — every one a read, every one fail-soft to an honest unknown.
# --------------------------------------------------------------------------- #
def _botsite_base() -> str:
    """The botsite service base URL, derived from the same
    ``config.SERVICE_DEPLOY_TARGETS`` entry the deploy-drift cell probes
    (its recorded ``/version`` endpoint, suffix stripped)."""
    url = config.SERVICE_DEPLOY_TARGETS.get("botsite") or ""
    return url.removesuffix("/version")


async def probe_botsite_site_password(refresh: bool = False) -> dict[str, Any]:
    """Is SITE_PASSWORD set on the botsite service?

    ``GET <botsite>/testing/owner`` unauthenticated, over the raw (tokenless)
    client — the gate's documented fail-closed split is the signal
    (``botsite/testing.py require_owner``): 503 = unset (still open),
    401 = the Basic-auth challenge, so the password IS set (done). Any
    other outcome is unknown with the reason. Read-only: the route is a
    GET behind the gate; no credential is sent, none exists here to send.
    """
    base = _botsite_base()
    if not base:
        return _verdict(
            UNKNOWN, "no botsite base URL recorded in config", "botsite-gate"
        )
    url = f"{base}/testing/owner"
    res = await github._get(url, refresh=refresh, raw=True)
    if res["status"] == 503:
        return _verdict(
            STILL_OPEN,
            "botsite /testing/owner answers 503 — SITE_PASSWORD unset "
            "(the documented fail-closed state)",
            "botsite-gate",
            url,
        )
    if res["status"] == 401:
        return _verdict(
            DONE,
            "botsite /testing/owner answers 401 (Basic-auth challenge) — "
            "SITE_PASSWORD is set on the service",
            "botsite-gate",
            url,
        )
    return _verdict(
        UNKNOWN,
        f"botsite /testing/owner answered HTTP {res['status']} "
        f"{res.get('error') or ''} — neither the 503-unset nor the "
        "401-armed signal",
        "botsite-gate",
        url,
    )


async def probe_bake_pat_secret(refresh: bool = False) -> dict[str, Any]:
    """Is BAKE_PAT among the websites Actions secret NAMES?

    The same listing the readiness board fetches (names only — the values
    are unreadable by design on this endpoint). No token / no admin scope
    → unknown, never a guessed absence.
    """
    if not config.GITHUB_TOKEN:
        return _verdict(
            UNKNOWN,
            "GITHUB_TOKEN is not set on this service — the Actions "
            "secret-name list is unreadable",
            "bake-pat",
        )
    res = await github.repo_api("websites", "/actions/secrets", refresh=refresh)
    if res["ok"] and isinstance(res["data"], dict):
        names = [
            s.get("name") for s in res["data"].get("secrets", []) or []
        ]
        if "BAKE_PAT" in names:
            return _verdict(
                DONE,
                "an Actions secret named BAKE_PAT exists on "
                "menno420/websites (name only — the value is unreadable "
                "by design)",
                "bake-pat",
            )
        return _verdict(
            STILL_OPEN,
            "the websites Actions secret-name list was read successfully "
            "and contains no BAKE_PAT",
            "bake-pat",
        )
    reason = (
        "token lacks admin scope for the secrets listing"
        if res["status"] in (401, 403)
        else res.get("error") or f"HTTP {res.get('status')}"
    )
    return _verdict(UNKNOWN, reason, "bake-pat")


async def probe_order020_write_pat(refresh: bool = False) -> dict[str, Any]:
    """Does the deployed control-plane token carry contents WRITE?

    Read-only by construction: ``GET /repos/<owner>/websites`` and inspect
    the ``permissions`` object GitHub reports for the calling token —
    ``permissions.push`` true means the token can write contents. NO write
    is ever attempted to find out. This observes the CONTROL-PLANE half of
    the ORDER-020 ask only (the botsite service's token is not observable
    from here — the detail says so).
    """
    if not config.GITHUB_TOKEN:
        return _verdict(
            UNKNOWN,
            "GITHUB_TOKEN is not set on this service — no token to "
            "inspect (no write is ever attempted)",
            "order-020-pat",
        )
    res = await github.repo_api("websites", refresh=refresh)
    if res["ok"] and isinstance(res["data"], dict):
        perms = res["data"].get("permissions")
        if not isinstance(perms, dict):
            return _verdict(
                UNKNOWN,
                "the repo payload carries no permissions object for this "
                "token — write capability not determinable read-only",
                "order-020-pat",
            )
        if perms.get("push") is True:
            return _verdict(
                DONE,
                "GET /repos/menno420/websites reports permissions.push=true "
                "for the service token — contents write is live on the "
                "control-plane (the botsite half is not observable from "
                "here)",
                "order-020-pat",
            )
        return _verdict(
            STILL_OPEN,
            "GET /repos/menno420/websites reports permissions.push=false — "
            "the deployed token is still read-scoped",
            "order-020-pat",
        )
    return _verdict(
        UNKNOWN,
        res.get("error") or f"HTTP {res.get('status')}",
        "order-020-pat",
    )


async def probe_dashboard_site_password_gone(
    refresh: bool = False,
) -> dict[str, Any]:
    """Was the unused SITE_PASSWORD variable deleted from the dashboard
    service?

    Rides the existing names-only Railway read (``railway.live_overview``
    — the project-scoped RAILWAY_TOKEN, values dropped at the client
    boundary) and its honest-unknown ladder: token unset / read failed /
    service or its variables unreadable → unknown with the reason. The
    name absent from a SUCCESSFUL read → done; present → still open.
    """
    if not config.RAILWAY_TOKEN:
        return _verdict(
            UNKNOWN,
            "RAILWAY_TOKEN is not set on this service — live variable "
            "names are unreadable (names-only read; never values)",
            "dashboard-site-password",
        )
    live = await railway.live_overview(refresh=refresh)
    if live.get("state") != "ok":
        return _verdict(
            UNKNOWN,
            live.get("reason")
            or f"live Railway read state: {live.get('state', '?')}",
            "dashboard-site-password",
        )
    svc = next(
        (s for s in live.get("services", []) if s.get("name") == "dashboard"),
        None,
    )
    if svc is None:
        return _verdict(
            UNKNOWN,
            "the live project read succeeded but lists no 'dashboard' "
            "service — the variable's state is not observable",
            "dashboard-site-password",
        )
    if svc.get("error"):
        return _verdict(
            UNKNOWN,
            f"live variables read failed for the dashboard service: "
            f"{svc['error']}",
            "dashboard-site-password",
        )
    names = svc.get("variable_names", []) or []
    if "SITE_PASSWORD" in names:
        return _verdict(
            STILL_OPEN,
            "SITE_PASSWORD is still among the dashboard service's live "
            "variable NAMES (names only — no value was read)",
            "dashboard-site-password",
        )
    return _verdict(
        DONE,
        "SITE_PASSWORD is no longer among the dashboard service's live "
        "variable NAMES (successful names-only read)",
        "dashboard-site-password",
    )


async def probe_lumen_drift_release(refresh: bool = False) -> dict[str, Any]:
    """Is the gba-homebrew ``lumen-drift-v1.3`` release published?

    Public release-tag GET: 200 → the release exists (done), 404 → not
    published (still open), anything else → unknown.
    """
    path = "/repos/menno420/gba-homebrew/releases/tags/lumen-drift-v1.3"
    res = await github.api(path, refresh=refresh)
    url = "https://github.com/menno420/gba-homebrew/releases"
    if res["ok"] and isinstance(res["data"], dict):
        return _verdict(
            DONE,
            "the lumen-drift-v1.3 release tag exists on "
            "menno420/gba-homebrew",
            "lumen-drift-release",
            res["data"].get("html_url") or url,
        )
    if res["status"] == 404:
        return _verdict(
            STILL_OPEN,
            "no lumen-drift-v1.3 release on menno420/gba-homebrew (404)",
            "lumen-drift-release",
            url,
        )
    return _verdict(
        UNKNOWN,
        res.get("error") or f"HTTP {res.get('status')}",
        "lumen-drift-release",
        url,
    )


async def probe_product_forge_pages(refresh: bool = False) -> dict[str, Any]:
    """Is GitHub Pages configured on menno420/product-forge?

    ``GET /repos/.../pages`` answers 200 with the site object when Pages
    is set up, 404 when not. The endpoint needs a token that can read the
    repo's Pages config — unreadable (401/403/no token) is an honest
    unknown, never an inferred absence.
    """
    res = await github.api("/repos/menno420/product-forge/pages", refresh=refresh)
    url = "https://github.com/menno420/product-forge/settings/pages"
    if res["ok"] and isinstance(res["data"], dict):
        return _verdict(
            DONE,
            "GitHub Pages is configured on menno420/product-forge "
            f"(status {res['data'].get('status') or 'reported'})",
            "product-forge-pages",
            url,
        )
    if res["status"] == 404:
        return _verdict(
            STILL_OPEN,
            "menno420/product-forge has no Pages site (404)",
            "product-forge-pages",
            url,
        )
    if res["status"] in (401, 403) or not config.GITHUB_TOKEN:
        return _verdict(
            UNKNOWN,
            "the Pages status is unreadable with this token "
            f"(HTTP {res.get('status')}) — not inferred either way",
            "product-forge-pages",
            url,
        )
    return _verdict(
        UNKNOWN,
        res.get("error") or f"HTTP {res.get('status')}",
        "product-forge-pages",
        url,
    )


# --------------------------------------------------------------------------- #
# Registry — stable keyword signatures over the ask HEADLINE (its WHAT, the
# same normalized basis /queue dedups on). A signature matches when EVERY
# keyword appears as a lowercase substring; an ask takes the FIRST matching
# entry in this order (so the more specific BAKE_PAT row sits above the
# ORDER-020 row it textually overlaps). Entries with ``probe=None`` are the
# EXPLICIT not-machine-checkable registrations — product decisions or state
# no read-only external probe can observe.
# --------------------------------------------------------------------------- #
ProbeFn = Callable[[bool], Awaitable[dict[str, Any]]]

REGISTRY: list[dict[str, Any]] = [
    {
        "id": "bake-pat",
        "signature": ("bake_pat",),
        "probe": probe_bake_pat_secret,
    },
    {
        "id": "order-020-pat",
        "signature": ("github_token", "contents"),
        "probe": probe_order020_write_pat,
    },
    {
        "id": "botsite-gate",
        "signature": ("site_password", "botsite"),
        "probe": probe_botsite_site_password,
    },
    {
        "id": "dashboard-site-password",
        "signature": ("site_password", "dashboard"),
        "probe": probe_dashboard_site_password_gone,
    },
    {
        "id": "lumen-drift-release",
        "signature": ("lumen-drift",),
        "probe": probe_lumen_drift_release,
    },
    {
        "id": "product-forge-pages",
        "signature": ("product-forge", "pages"),
        "probe": probe_product_forge_pages,
    },
    {
        "id": "q-0004",
        "signature": ("q-0004",),
        "probe": None,
        "reason": (
            "a product/topology decision only the owner can make "
            "(docs/question-router.md Q-0004) — no external state exists "
            "to probe"
        ),
    },
    {
        "id": "discord-oauth",
        "signature": ("discord", "oauth"),
        "probe": None,
        "reason": (
            "Discord developer-console state is not externally observable "
            "— no read-only probe exists"
        ),
    },
    {
        "id": "armed-service",
        "signature": ("control-api", "armed"),
        "probe": None,
        "reason": (
            "gated on Q-0004; the armed service's URL does not exist yet, "
            "so there is nothing external to probe"
        ),
    },
    {
        "id": "botsite-database-url",
        "signature": ("postgresql", "botsite"),
        "probe": None,
        "reason": (
            "a Railway-internal variable on the botsite service — not "
            "externally observable (the /submit stub is a build gap, not "
            "proof either way)"
        ),
    },
    {
        "id": "paypal-credentials",
        "signature": ("paypal",),
        "probe": None,
        "reason": (
            "PayPal credentials on the botsite service are not externally "
            "observable — and must never be probed"
        ),
    },
]

UNMATCHED_REASON = (
    "no registered probe matches this ask — left honestly unverified "
    "(stable ask IDs would make matching exact; deliberately no fuzzy "
    "matching)"
)
AMBIGUOUS_REASON = (
    "another ask already matched this probe this pass — an ambiguous "
    "signature match never yields a verdict"
)


def _normalize(text: str) -> str:
    return " ".join((text or "").lower().split())


def headline_of(item: dict[str, Any]) -> str:
    """The matching basis: the ask's WHAT (or its free text) — the same
    identity /queue dedups on."""
    return item.get("what") or item.get("text") or ""


def match(headline: str) -> Optional[dict[str, Any]]:
    """The first REGISTRY entry whose every signature keyword appears in
    the normalized headline; ``None`` when nothing matches (the honest
    unmatched state — never a fuzzy fallback)."""
    text = _normalize(headline)
    if not text:
        return None
    for entry in REGISTRY:
        if all(kw in text for kw in entry["signature"]):
            return entry
    return None


async def annotate(
    items: list[dict[str, Any]], refresh: bool = False
) -> dict[str, Any]:
    """Attach one verdict per ask (``item["verify"]``) and return the
    rollup.

    Matching is claim-once per pass (an entry matched by a second ask
    yields the honest ambiguous chip for that ask). Each claimed entry's
    probe runs exactly once, concurrently; every probe is fail-soft — an
    exception is an honest ``unknown — <error>``, never a crash and never
    a fabricated rung.

    Rollup: ``total`` asks · ``machine_verified`` (chips carrying a live
    probe verdict: done-detected or still-open) · per-rung counts ·
    ``unmatched`` (asks no registry entry matched, ambiguous included).
    """
    matches: list[Optional[dict[str, Any]]] = []
    claimed: dict[str, int] = {}
    ambiguous: set[int] = set()
    for i, item in enumerate(items):
        entry = match(headline_of(item))
        if entry is not None:
            if entry["id"] in claimed:
                ambiguous.add(i)
                entry = None
            else:
                claimed[entry["id"]] = i
        matches.append(entry)

    async def _run(entry: dict[str, Any]) -> dict[str, Any]:
        try:
            return await entry["probe"](refresh)
        except Exception as exc:  # fail-soft: a broken probe is an unknown
            return _verdict(
                UNKNOWN,
                f"probe error: {type(exc).__name__}: {exc}",
                entry["id"],
            )

    # Claim-once above guarantees each entry appears at most once here.
    to_probe = [
        e for e in matches if e is not None and e["probe"] is not None
    ]
    probed = await asyncio.gather(*[_run(e) for e in to_probe])
    verdict_by_id = {e["id"]: v for e, v in zip(to_probe, probed)}

    rollup = {
        "total": len(items),
        "machine_verified": 0,
        "done": 0,
        "still_open": 0,
        "not_checkable": 0,
        "unknown": 0,
        "unmatched": 0,
    }
    for i, (item, entry) in enumerate(zip(items, matches)):
        if entry is None:
            reason = AMBIGUOUS_REASON if i in ambiguous else UNMATCHED_REASON
            v = _verdict(NOT_CHECKABLE, reason)
            rollup["unmatched"] += 1
        elif entry["probe"] is None:
            v = _verdict(NOT_CHECKABLE, entry["reason"], entry["id"])
        else:
            v = verdict_by_id[entry["id"]]
        item["verify"] = v
        if v["verdict"] == DONE:
            rollup["done"] += 1
            rollup["machine_verified"] += 1
        elif v["verdict"] == STILL_OPEN:
            rollup["still_open"] += 1
            rollup["machine_verified"] += 1
        elif v["verdict"] == NOT_CHECKABLE:
            rollup["not_checkable"] += 1
        else:
            rollup["unknown"] += 1
    return rollup
