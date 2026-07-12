"""Tester-task URL liveness guard — cold-fetches every ``status: "open"``
task's ``product_url`` in the committed ``testing_tasks.json`` and flags any
whose FINAL response stops being HTTP 200.

Why (docs/ideas/backlog.md, "Tester-task URL liveness guard", ORDER 018
session): every open task points a PAYING tester at a ``product_url``; if
that URL dies (service renamed, deploy broken) the program burns real
testers' time and its own credibility before anyone notices — the tester
program's whole pitch is "real products, honestly described", and a dead
link is the fastest way to break that promise. This module is the automated
reconcile: it is consumed by ``scripts/healthcheck.py`` (the 6-hourly
scheduled healthcheck), which is the ONLY place the real network fetch runs.
The required ``quality`` CI gate never touches the network — the botsite app
never imports this module, and its tests exercise it exclusively through
``httpx.MockTransport``.

Design contract (mirrors ``botsite/arcade_probe.py``, PRs #214/#220):

- **Fail-soft per URL**: every per-URL failure (non-200 final status,
  timeout, connection error, malformed or missing URL, any surprise
  exception) becomes a FLAGGED finding row; ``probe_task_urls`` itself never
  raises — even a catalog that fails to LOAD degrades to a flagged summary.
  Whether a flagged finding affects exit status is the CALLER's convention
  (``healthcheck.py`` folds it into its exit-1-on-any-failure idiom).
- **Same verdict logic as the arcade probe**: ``probe_url`` is imported, not
  forked — redirects are followed (Railway hosts interpose 301/308 freely; a
  chain ending in 200 is healthy), a FINAL redirect status stays flagged,
  and a redirect loop degrades to a flagged ``TooManyRedirects`` finding.
- **Honest coverage**: only ``status: "open"`` tasks send testers anywhere
  today, so exactly those are probed; every other status (``coming-soon``,
  ``closed``) is returned as ``skipped`` (id + status) so the caller prints
  an explicit "not probed" line — the guard never implies coverage it does
  not have. An OPEN task with NO ``product_url`` is a flagged finding (the
  catalog would send a paying tester nowhere). A catalog that loads to ZERO
  tasks is itself a flagged condition (missing/corrupt file suspected — the
  committed catalog lists eight tasks), mirroring the arcade probe's
  zero-entries alert.
- Reads the catalog through the SAME loader the /testing page renders with
  (``botsite.testing_catalog.load_tasks``, re-exported by ``testing.py``),
  so probe coverage and page content can never disagree about which tasks
  are open. The committed ``status`` field is what is probed — live slot
  fill-up (``effective_status`` auto-close) lives in the SQLite store, which
  the healthcheck host has no access to; a filled-but-still-committed-open
  task keeps its URL and still deserves the liveness check.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx

from . import testing_catalog
from .arcade_probe import TIMEOUT_S, probe_url

USER_AGENT = "websites-healthcheck-tester-task-probe"

# The committed statuses that send a tester to a product_url today — exactly
# these get probed. coming-soon/closed tasks link nothing on /testing.
PROBED_STATUSES = ("open",)

__all__ = ["PROBED_STATUSES", "TIMEOUT_S", "make_client", "probe_task_urls"]


def make_client() -> httpx.Client:
    """The real-network client used by scripts/healthcheck.py. Tests never
    call this — they inject an ``httpx.Client(transport=MockTransport(...))``."""
    return httpx.Client(
        timeout=TIMEOUT_S,
        follow_redirects=True,
        headers={"User-Agent": USER_AGENT},
    )


def probe_task_urls(
    path: Path | None = None, client: httpx.Client | None = None
) -> dict[str, Any]:
    """Probe every open task's ``product_url`` in the tester-task catalog
    (``PROBED_STATUSES`` — the statuses /testing links a product for).

    Returns a summary dict — never raises:

    - ``rows``: probed tasks, each ``{"id", "status", "url", "ok", "note"}``
    - ``flagged``: the subset of ``rows`` with ``ok`` False
    - ``skipped``: other-status tasks, each ``{"id", "status"}`` — honestly
      NOT probed
    - ``ok``: True iff the catalog loaded non-empty and nothing was flagged
    - ``note``: one-line headline (counts, or the zero-tasks alert)
    """
    try:
        tasks = testing_catalog.load_tasks(path)
    except Exception as exc:  # fail-soft: a broken catalog is a finding, not a crash
        return {
            "rows": [],
            "flagged": [],
            "skipped": [],
            "ok": False,
            "note": f"catalog failed to load ({type(exc).__name__}: {exc})",
        }
    if not tasks:
        return {
            "rows": [],
            "flagged": [],
            "skipped": [],
            "ok": False,
            "note": "catalog loaded ZERO tasks — missing/corrupt testing_tasks.json suspected",
        }

    rows: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    own_client = client is None
    cli = client or make_client()
    try:
        for task in tasks:
            task_id = str(task.get("id") or "<no id>")
            status = str(task.get("status") or "open")
            if status not in PROBED_STATUSES:
                skipped.append({"id": task_id, "status": status})
                continue
            url = task.get("product_url")
            if not url or not isinstance(url, str):
                rows.append(
                    {"id": task_id, "status": status, "url": None,
                     "ok": False,
                     "note": f'status "{status}" but no product_url to probe'}
                )
                continue
            ok, note = probe_url(url, cli)
            rows.append(
                {"id": task_id, "status": status, "url": url, "ok": ok, "note": note}
            )
    finally:
        if own_client:
            cli.close()

    flagged = [row for row in rows if not row["ok"]]
    note = (
        f"{len(rows)} open-task URL(s) probed, {len(flagged)} flagged, "
        f"{len(skipped)} other-status task{'' if len(skipped) == 1 else 's'} not probed"
    )
    return {
        "rows": rows,
        "flagged": flagged,
        "skipped": skipped,
        "ok": not flagged,
        "note": note,
    }
