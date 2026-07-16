#!/usr/bin/env python3
"""Post-deploy healthcheck: GET /healthz and / on the four live services, plus
the `/fleet` registry live-parse smoke check, the arcade URL drift probe
(live+download), the tester-task URL liveness guard (open tasks) and the
release-drift flag (registry blockers vs askverify probes).

──────────────────────────────────────────────────────────────────────────────
PROVENANCE / KILL-SWITCH HEADER
  Why:   "Merge = deploy" — each service auto-redeploys on merge to main. This
         is the reusable post-deploy verification habit: one command confirms
         all four Railway services answer `/healthz` and serve their public
         `/` with HTTP 200. Beats hand-curling four URLs after every merge.
         (review joined 2026-07-13 — the service went LIVE 2026-07-12 but the
         SERVICES table was never extended; gap found by a prior session.)
  Added: 2026-07-09 (websites hardening pass, PR #19, [D-0015]).
  Trust: DETERMINISTIC (pure stdlib urllib) — but UNVERIFIED as a habit; sanity
         check its verdict against a manual curl a few times before trusting.
  KILL-SWITCH: if the URLs change or this proves flaky/noisy over several
         sessions, update the SERVICES table or DELETE this file. It is a
         convenience helper, not infrastructure.
──────────────────────────────────────────────────────────────────────────────

All four services are PUBLIC (2026-07-09 auth-drop; botsite and review were
always public), so `/` is expected 200.

The registry check (retro A3 / queue-state NEXT item 2) fetches the manager's
LIVE registry (menno420/fleet-manager scripts/gen_roster.py) and asserts the SAME parser
`/fleet` uses (`app.fleet.parse_registry` + `registry_to_lanes`) still yields a
non-empty, well-formed lane set. `/fleet` itself degrades a bad parse to the
`config.FLEET_LANES` fallback with an honest on-page banner — safe, but silent
to anyone not looking at the page. This check is what alerts a registry
reformat/move instead of letting it degrade unnoticed (it caught the
2026-07-11 manifest supersession live, on schedule run 2).

The arcade pass (docs/ideas/backlog.md "Arcade live-URL drift probe" + "Probe
download-availability arcade URLs too", ORDER 022 drift session) cold-fetches
every `availability: "live"` AND `availability: "download"` URL in
`botsite/data/arcade.json` via `botsite.arcade_probe` and FLAGS any whose
FINAL response stops being 200 (bad status / timeout / connection error /
malformed or missing URL — each with its reason; redirect chains ending in
200 count healthy). The /arcade page renders outbound links for both those
availabilities; this pass is what notices when reality drifts out from under
a committed card. Fail-soft per URL: a dead link is a FLAGGED finding folded
into the exit code below, never a traceback. Live fetches run ONLY here (and
the 6-hourly healthcheck.yml schedule) — the required `quality` gate tests the
probe against `httpx.MockTransport`, network-free.

The tester-task pass (docs/ideas/backlog.md "Tester-task URL liveness guard",
ORDER 018 session) cold-fetches every `status: "open"` task's `product_url`
in `botsite/testing_tasks.json` via `botsite.testing_probe` and FLAGS any
whose FINAL response stops being 200 — every open task points a PAYING
tester at that URL, and a dead link burns real testers' time before anyone
notices. Same contract as the arcade pass: redirects followed, fail-soft per
URL (dead/missing/malformed URL = FLAGGED finding, never a traceback),
non-open tasks reported explicitly as not probed, live fetches ONLY here
(and the healthcheck.yml schedule) — the required `quality` gate tests the
probe against `httpx.MockTransport`, network-free.

The release-drift pass (PR #349 follow-up parked as "release-drift banner",
promoted by PR #362's baton once every registry blocker carried a stable
`ask_id`) joins the four botsite registries' normalized blockers
(botsite/blockers.py via the SAME public loaders the pages read through) to
`app.askverify`'s probe REGISTRY by exact ASK-NNNN id and FLAGS the two
drifts a cleared owner ask can leave behind: a probe that positively detects
the ask DONE while the registry still gates the card (e.g. the lumen-drift
release tag going live while arcade.json still says unavailable), and an
`ask_id` that matches no askverify entry (ledger drift — the join key
dangles). Probes are askverify's own (read-only, fail-soft, deduped one
probe per ask_id per run even when one ask gates many cards — ASK-0012
gates 14); probe-less asks (product decisions, off-repo state) are listed
honestly as not machine-checkable and a probe error is an honest unknown —
neither fails the pass (live network is flaky; never invent state). No new
botsite outbound surface: the probes run from the control-plane's askverify
inside this script, which already does live fetches by design.

Usage:  python3 scripts/healthcheck.py
Exit 0 = every checked endpoint returned its expected status AND the registry
parsed to a non-empty lane set AND no probed arcade URL was flagged AND no
probed open tester-task URL was flagged AND no release drift was flagged;
exit 1 = any of those fail.
"""

from __future__ import annotations

import asyncio
import os
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import askverify, config, fleet, github  # noqa: E402  (path setup must run first)
from botsite import (  # noqa: E402  (path setup must run first)
    arcade,
    arcade_probe,
    catalog,
    products,
    puddle_museum,
    testing_probe,
)

# (label, base URL). Endpoints checked per service: /healthz and / (both expect
# 200 now that all four are public). The review URL is the canonical f027
# deployment documented in docs/current-state.md + app/config.py (the fc91
# copy is the labeled "parallel copy" in app/data/web_presence.json — not
# probed here).
SERVICES = [
    ("control-plane", "https://control-plane-production-abb0.up.railway.app"),
    ("botsite", "https://botsite-production-cfd7.up.railway.app"),
    ("dashboard", "https://dashboard-production-a91b.up.railway.app"),
    ("review", "https://review-production-f027.up.railway.app"),
]
ENDPOINTS = ("/healthz", "/")
EXPECTED = 200
TIMEOUT = 15

REGISTRY_URL = (
    f"{config.GITHUB_RAW_BASE}/{config.OWNER}/{fleet.REGISTRY_REPO}/main/"
    f"{fleet.REGISTRY_PATH}"
)


def _probe(url: str) -> tuple[int, str]:
    """Return (status_code, note). Network/HTTP errors degrade to (0, reason)."""
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": "healthcheck"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.status, ""
    except urllib.error.HTTPError as exc:  # a real HTTP status (e.g. 404/500)
        return exc.code, exc.reason or ""
    except (urllib.error.URLError, OSError, ValueError) as exc:
        return 0, str(getattr(exc, "reason", exc))


def check_fleet_registry() -> tuple[bool, str]:
    """Fetch the live fleet-manager registry (LANES in gen_roster.py) and
    assert it parses to a non-empty, well-formed lane set — the alert that
    caught the 2026-07-11 manifest supersession lives on against the NEW
    source."""
    req = urllib.request.Request(REGISTRY_URL, headers={"User-Agent": "healthcheck"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            text = resp.read().decode("utf-8")
    except (urllib.error.URLError, OSError, ValueError) as exc:
        return False, f"fetch failed: {getattr(exc, 'reason', exc)}"

    try:
        lanes = fleet.registry_to_lanes(fleet.parse_registry(text))
    except Exception as exc:  # defensive: a parser bug shouldn't crash the check
        return False, f"parse raised {type(exc).__name__}: {exc}"

    if not lanes:
        return False, "parsed to ZERO lanes — registry reformat/move suspected"

    unresolved = [lane["lane"] for lane in lanes if not lane.get("repo") or not lane.get("status_path")]
    if unresolved:
        return False, f"lanes with unresolved repo/status_path: {unresolved}"

    return True, f"{len(lanes)} lanes parsed"


def check_arcade_urls() -> tuple[bool, list[str]]:
    """Cold-fetch every live- and download-availability arcade URL
    (botsite.arcade_probe) and flag drift — a dead game link must never
    quietly outlive its card. Returns (ok, printable lines). Never raises:
    per-URL failures are FLAGGED findings inside the probe, and a probe bug
    itself degrades to a FAIL line (defensive, same stance as
    check_fleet_registry's parse guard)."""
    try:
        result = arcade_probe.probe_registry_urls()
    except Exception as exc:  # defensive: a probe bug shouldn't crash the check
        return False, [f"probe raised {type(exc).__name__}: {exc}"]

    lines: list[str] = []
    for row in result["rows"]:
        mark = "PASS" if row["ok"] else "FLAGGED"
        availability = row.get("availability", "?")
        lines.append(
            f"{row['slug']:12}  {mark:7}  [{availability}]  "
            f"{row['url'] or '<no url>'}  ({row['note']})"
        )
    for entry in result["skipped"]:
        lines.append(f"{entry['slug']:12}  not probed (availability: {entry['availability']})")
    lines.append(result["note"])
    return result["ok"], lines


def check_testing_urls() -> tuple[bool, list[str]]:
    """Cold-fetch every open tester task's product_url
    (botsite.testing_probe) and flag drift — a dead product link must never
    quietly keep collecting paid testers. Returns (ok, printable lines).
    Never raises: per-URL failures are FLAGGED findings inside the probe,
    and a probe bug itself degrades to a FAIL line (defensive, same stance
    as check_arcade_urls)."""
    try:
        result = testing_probe.probe_task_urls()
    except Exception as exc:  # defensive: a probe bug shouldn't crash the check
        return False, [f"probe raised {type(exc).__name__}: {exc}"]

    lines: list[str] = []
    for row in result["rows"]:
        mark = "PASS" if row["ok"] else "FLAGGED"
        status = row.get("status", "?")
        lines.append(
            f"{row['id']:36}  {mark:7}  [{status}]  "
            f"{row['url'] or '<no url>'}  ({row['note']})"
        )
    for entry in result["skipped"]:
        lines.append(f"{entry['id']:36}  not probed (status: {entry['status']})")
    lines.append(result["note"])
    return result["ok"], lines


def _collect_registry_blockers() -> list[tuple[str, str, dict]]:
    """Every normalized blocker across the four botsite registries as
    (registry, entry id, blocker) rows — read through the SAME public
    loaders the pages render from (each already runs
    ``botsite.blockers.normalized_blocker``), so this pass and the public
    site can never disagree about what is gated. Disk reads only — the
    committed JSON, no botsite network surface."""
    rows: list[tuple[str, str, dict]] = []
    for game in arcade.load_games():
        if game.get("blocker"):
            rows.append(("arcade", game["slug"], game["blocker"]))
    for item in catalog.load_catalog():
        if item.get("blocker"):
            rows.append(("catalog", item["slug"], item["blocker"]))
    for product in products.load_products():
        if product.get("blocker"):
            rows.append(("products", product["slug"], product["blocker"]))
    for edition in puddle_museum.load_museum()["editions"]:
        if edition.get("blocker"):
            rows.append(("puddle-museum", edition["lang"], edition["blocker"]))
    return rows


def check_release_drift() -> tuple[bool, list[str]]:
    """Join every registry blocker's ``ask_id`` to its askverify REGISTRY
    entry (exact ASK-NNNN id — ``askverify.match`` with no headline, so the
    signature fallback never fires) and flag RELEASE DRIFT: a probe that
    positively detects the ask done while the registry still gates the
    card, or an ask_id no askverify entry knows (ledger drift). Probes are
    askverify's own machinery (``annotate`` — claim-once, concurrent,
    fail-soft: a probe exception is an honest unknown), deduped to one
    probe per ask_id per run however many cards share the ask. still-open
    is a PASS row; not-machine-checkable / unknown / id-less blockers are
    honest info rows that never fail the pass (never invent state).
    Returns (ok, printable lines). Never raises: a pass bug itself degrades
    to a FAIL line (defensive, same stance as check_arcade_urls)."""
    try:
        blocker_rows = _collect_registry_blockers()
    except Exception as exc:  # defensive: a loader bug shouldn't crash the check
        return False, [f"registry collection raised {type(exc).__name__}: {exc}"]

    # One join + one probe per DISTINCT ask_id per run (ASK-0012 alone gates
    # many catalog cards); annotate's claim-once machinery then runs each
    # matched entry's probe exactly once, concurrently.
    ask_ids: list[str] = []
    for _registry, _ident, blocker in blocker_rows:
        aid = blocker.get("ask_id")
        if aid and aid not in ask_ids:
            ask_ids.append(aid)
    entries = {aid: askverify.match("", aid) for aid in ask_ids}
    items = [{"ask_id": aid} for aid in ask_ids if entries[aid] is not None]

    async def _annotate() -> None:
        # askverify's probes ride the app's lifespan-managed httpx clients;
        # this script has no lifespan, so wire the SAME client pair up around
        # the one annotate call (the app/main.py lifespan idiom, scoped).
        client = github.make_client()
        raw_client = github.make_raw_client()
        github.set_clients(client, raw_client)
        try:
            await askverify.annotate(items)
        finally:
            await client.aclose()
            await raw_client.aclose()

    try:
        asyncio.run(_annotate())
        verdicts = {item["ask_id"]: item.get("verify") or {} for item in items}
    except Exception as exc:  # defensive: a machinery bug shouldn't crash the check
        return False, [f"askverify annotate raised {type(exc).__name__}: {exc}"]

    lines: list[str] = []
    flagged = 0
    for registry, ident, blocker in blocker_rows:
        ref = f"{registry}/{ident}"
        aid = blocker.get("ask_id")
        if not aid:
            # An id-less blocker has no ledger row to join — honest info
            # only, never a flag (the blocker itself is still rendered).
            lines.append(f"{ref:40}  {'info':7}  <no ask_id>  (blocker carries no ledger id — nothing to join)")
            continue
        entry = entries[aid]
        if entry is None:
            flagged += 1
            lines.append(f"{ref:40}  {'FLAGGED':7}  {aid}  (ledger drift: ask_id matches no askverify entry)")
            continue
        verdict = verdicts.get(aid, {}).get("verdict")
        detail = verdicts.get(aid, {}).get("detail") or ""
        if verdict == askverify.DONE:
            flagged += 1
            lines.append(f"{ref:40}  {'FLAGGED':7}  {aid}  (drift: ask done-detected but registry still gated)")
        elif verdict == askverify.STILL_OPEN:
            lines.append(f"{ref:40}  {'PASS':7}  {aid}  (still-open — registry gate matches reality)")
        elif verdict == askverify.NOT_CHECKABLE:
            lines.append(f"{ref:40}  {'info':7}  {aid}  (not machine-checkable — {detail or 'no probe registered'})")
        else:  # UNKNOWN (probe error / unreadable) — never invent state
            lines.append(f"{ref:40}  {'info':7}  {aid}  (unknown — {detail or 'probe could not tell'})")
    lines.append(
        f"{len(blocker_rows)} blocker(s) across the 4 registries, "
        f"{len(items)} distinct ask(s) joined, {flagged} flagged"
    )
    return flagged == 0, lines


def main() -> int:
    rows: list[tuple[str, str, int, bool, str]] = []
    ok_all = True
    for label, base in SERVICES:
        for ep in ENDPOINTS:
            status, note = _probe(base + ep)
            ok = status == EXPECTED
            ok_all = ok_all and ok
            rows.append((label, ep, status, ok, note))

    width = max(len(lbl) for lbl, _ in SERVICES)
    print(f"{'service'.ljust(width)}  {'endpoint':9}  status  ok")
    print(f"{'-' * width}  {'-' * 9}  ------  --")
    for label, ep, status, ok, note in rows:
        mark = "PASS" if ok else "FAIL"
        shown = str(status) if status else "DOWN"
        extra = f"  ({note})" if note and not ok else ""
        print(f"{label.ljust(width)}  {ep:9}  {shown:>6}  {mark}{extra}")

    registry_ok, registry_note = check_fleet_registry()
    ok_all = ok_all and registry_ok
    print()
    print(f"fleet-registry live parse: {'PASS' if registry_ok else 'FAIL'} ({registry_note})")

    arcade_ok, arcade_lines = check_arcade_urls()
    ok_all = ok_all and arcade_ok
    print()
    print(f"arcade URL drift probe (live+download): {'PASS' if arcade_ok else 'FAIL'}")
    for line in arcade_lines:
        print(f"  {line}")

    testing_ok, testing_lines = check_testing_urls()
    ok_all = ok_all and testing_ok
    print()
    print(f"tester-task URL liveness guard (open tasks): {'PASS' if testing_ok else 'FAIL'}")
    for line in testing_lines:
        print(f"  {line}")

    drift_ok, drift_lines = check_release_drift()
    ok_all = ok_all and drift_ok
    print()
    print(f"release-drift flag (registry blockers vs askverify): {'PASS' if drift_ok else 'FAIL'}")
    for line in drift_lines:
        print(f"  {line}")

    print()
    print("RESULT:", "all healthy" if ok_all else "ONE OR MORE DOWN")
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
