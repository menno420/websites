#!/usr/bin/env python3
"""Scheduled browser-level smoke-crawl: headless Chromium over the public
pages of the three public sites + the control-plane root.

──────────────────────────────────────────────────────────────────────────────
PROVENANCE / KILL-SWITCH HEADER
  Why:   The standing healthcheck (`scripts/healthcheck.py`, healthcheck.yml)
         is curl-level — status codes only. Both 2026-07-13 manual cold passes
         (PR #228, PR #311) found real regressions it can never see (dead
         chrome wiring, a blank hamburger, a lost footer gutter, a favicon
         404) because they only exist in a rendering browser. This script is
         the cold pass as a standing gate: a real Chromium crawls each site's
         public pages at desktop + mobile viewports and fails loudly on
         console errors, non-200 pages, and broken same-site links.
  Added: 2026-07-14 (backlog promotion of the #311 session's 💡,
         `docs/ideas/backlog.md` "Scheduled browser-level smoke-crawl in CI").
  Trust: DETERMINISTIC assertions over live pages; the pages themselves are
         live and can legitimately change under the crawl.
  KILL-SWITCH: if the URLs change, update SITES (and healthcheck.py's
         SERVICES — same inventory). If the crawl proves flaky/noisy over
         several scheduled runs, tune the allowlist or DELETE this file +
         .github/workflows/smoke-crawl.yml together.
──────────────────────────────────────────────────────────────────────────────

Behavior:
- Seeds: the four live Railway URLs (the SAME inventory healthcheck.py
  probes). Same-site (same-origin) link discovery from each crawled page;
  external links are never followed and never fetched.
- Two viewports per crawled page: desktop 1280×900 and mobile 375×812 —
  the manual cold passes' geometry.
- Assertions, per site:
    1. every crawled page's final response is HTTP 200;
    2. zero console errors / uncaught page errors across BOTH viewports
       (an allowlist of regex patterns exists for known noise — seeded
       EMPTY: the #311 pass ended with zero known-noise errors);
    3. every discovered same-site link answers non-4xx/5xx (GET, redirects
       followed; links beyond the crawl cap are status-checked only).
- Bounded: a per-site page cap and a global wall-clock deadline keep a full
  run well under the 5-minute mark; blowing the deadline is itself a FAILURE
  (a silently truncated crawl would be a dishonest green).

Container/CI split (docs/CAPABILITIES.md 2026-07-13 entry): in the agent
container the full Chromium binary + an explicit --proxy-server +
--ssl-version-max=tls1.2 are required (the egress proxy resets a TLS 1.3
ClientHello; the headless shell gets ERR_CONNECTION_RESET). GitHub Actions
runners have no such proxy — CI runs plain (`playwright install chromium`,
no overrides). Hence the env/CLI overrides below; none are set in CI.

Usage:  python3 scripts/smoke_crawl.py [--max-pages N] [--deadline SECONDS]
            [--executable-path PATH] [--proxy-server URL] [--browser-arg ARG]...
Env:    SMOKE_CRAWL_EXECUTABLE_PATH, SMOKE_CRAWL_PROXY_SERVER,
        SMOKE_CRAWL_BROWSER_ARGS (whitespace-split extra Chromium args),
        SMOKE_CRAWL_MAX_PAGES, SMOKE_CRAWL_DEADLINE (CLI flags win).
Exit 0 = every assertion held on every site; exit 1 = any failure (each
printed with its page URL + reason).
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from urllib.parse import urldefrag, urljoin, urlsplit

# (label, base URL) — the SAME inventory scripts/healthcheck.py probes: the
# three public sites + the control-plane root. Keep the two tables in sync.
SITES = [
    ("control-plane", "https://control-plane-production-abb0.up.railway.app"),
    ("botsite", "https://botsite-production-cfd7.up.railway.app"),
    ("dashboard", "https://dashboard-production-a91b.up.railway.app"),
    ("review", "https://review-production-f027.up.railway.app"),
]

# Regex patterns for console-error text that is KNOWN noise and may be
# ignored. Seeded EMPTY on purpose: the 2026-07-13 cold pass #2 (PR #311)
# fixed the only recurring console error (the favicon 404) and recorded no
# other known noise. Every addition needs a one-line justification comment —
# an unexplained allowlist entry is how a real regression hides.
CONSOLE_ERROR_ALLOWLIST: list[str] = []

DESKTOP = {"width": 1280, "height": 900}
MOBILE = {"width": 375, "height": 812}

DEFAULT_MAX_PAGES_PER_SITE = 25
DEFAULT_DEADLINE_SECONDS = 240
MAX_LINK_CHECKS_PER_SITE = 150
PAGE_TIMEOUT_MS = 20_000
LINK_TIMEOUT_MS = 15_000

# Path prefixes never crawled or link-checked: gated-by-design corners whose
# non-200 answer to an anonymous browser is the documented contract, not rot
# (the /owner board is the control-plane's single gated corner —
# docs/current-state.md "Stability baseline").
SKIP_PATH_PREFIXES = ("/owner",)

# Same-site URLs with these extensions are real link targets (status-checked
# in pass 3) but are never rendered as browser pages: a raw JSON/XML view has
# no rendering layer to smoke-test, and Chromium's built-in viewer requests
# /favicon.ico on such pages — a console-error artifact of the viewer, not of
# the site's pages. (/favicon.ico is served fleet-wide since the PR that
# closed the PR #321 follow-up findings, so that request now answers 200.)
NON_PAGE_EXTENSIONS = (
    ".json", ".xml", ".md", ".sh", ".txt", ".svg", ".ico", ".png", ".jpg",
    ".css", ".js", ".zip", ".pdf",
)

_SKIPPED_SCHEMES = ("mailto:", "javascript:", "tel:", "data:")


def _same_site(url: str, base: str) -> bool:
    return urlsplit(url)[:2] == urlsplit(base)[:2]  # scheme + netloc


def _skippable(url: str) -> bool:
    path = urlsplit(url).path or "/"
    return any(path == p or path.startswith(p + "/") for p in SKIP_PATH_PREFIXES)


def _allowlisted(text: str, patterns: list[re.Pattern[str]]) -> bool:
    return any(p.search(text) for p in patterns)


class Deadline:
    def __init__(self, seconds: float) -> None:
        self._end = time.monotonic() + seconds
        self.seconds = seconds

    @property
    def exceeded(self) -> bool:
        return time.monotonic() > self._end


def crawl_site(
    context_factory,
    label: str,
    base: str,
    *,
    max_pages: int,
    deadline: Deadline,
    allowlist: list[re.Pattern[str]],
) -> tuple[list[str], dict]:
    """Crawl one site in both viewports. Returns (failures, stats)."""
    failures: list[str] = []
    stats = {
        "pages": 0,
        "links_checked": 0,
        "links_found": 0,
        "links_uncheckable": 0,
        "console_ok": True,
    }

    to_visit: list[str] = [base + "/"]
    discovered: set[str] = {base + "/"}
    visited: list[str] = []
    all_links: set[str] = set()

    desktop_ctx = context_factory(DESKTOP)
    mobile_ctx = context_factory(MOBILE)
    try:
        # ── pass 1: BFS crawl at desktop, discovering same-site links ──────
        page = desktop_ctx.new_page()
        console_errors: list[tuple[str, str]] = []
        page.on(
            "console",
            lambda msg: console_errors.append((page.url, msg.text))
            if msg.type == "error"
            else None,
        )
        page.on("pageerror", lambda exc: console_errors.append((page.url, f"pageerror: {exc}")))

        while to_visit and len(visited) < max_pages:
            if deadline.exceeded:
                failures.append(
                    f"[{label}] DEADLINE exceeded ({deadline.seconds:.0f}s) with "
                    f"{len(to_visit)} pages still queued — crawl result is INCOMPLETE"
                )
                break
            url = to_visit.pop(0)
            try:
                resp = page.goto(url, timeout=PAGE_TIMEOUT_MS, wait_until="load")
            except Exception as exc:
                failures.append(f"[{label}] {url} — navigation failed: {exc}")
                continue
            visited.append(url)
            status = resp.status if resp else 0
            if status != 200:
                failures.append(f"[{label}] {url} — HTTP {status} (expected 200)")
                continue

            hrefs = page.eval_on_selector_all(
                "a[href]",
                "els => els.map(e => e.getAttribute('href'))",
            )
            for href in hrefs:
                if not href or href.lower().startswith(_SKIPPED_SCHEMES):
                    continue
                absolute = urldefrag(urljoin(page.url, href)).url
                if not _same_site(absolute, base) or _skippable(absolute):
                    continue  # external links: never followed, never fetched
                all_links.add(absolute)
                if absolute not in discovered:
                    discovered.add(absolute)
                    path = urlsplit(absolute).path.lower()
                    if not path.endswith(NON_PAGE_EXTENSIONS):
                        to_visit.append(absolute)  # non-page URLs: pass 3 only

        # ── pass 2: re-load every crawled page at mobile 375px ─────────────
        mpage = mobile_ctx.new_page()
        mpage.on(
            "console",
            lambda msg: console_errors.append((f"{mpage.url} [mobile]", msg.text))
            if msg.type == "error"
            else None,
        )
        mpage.on(
            "pageerror",
            lambda exc: console_errors.append((f"{mpage.url} [mobile]", f"pageerror: {exc}")),
        )
        for url in visited:
            if deadline.exceeded:
                failures.append(
                    f"[{label}] DEADLINE exceeded ({deadline.seconds:.0f}s) during the "
                    f"mobile pass — crawl result is INCOMPLETE"
                )
                break
            try:
                resp = mpage.goto(url, timeout=PAGE_TIMEOUT_MS, wait_until="load")
            except Exception as exc:
                failures.append(f"[{label}] {url} [mobile] — navigation failed: {exc}")
                continue
            status = resp.status if resp else 0
            if status != 200:
                failures.append(f"[{label}] {url} [mobile] — HTTP {status} (expected 200)")

        # ── console verdict (both viewports) ────────────────────────────────
        real_errors = [
            (where, text) for where, text in console_errors if not _allowlisted(text, allowlist)
        ]
        if real_errors:
            stats["console_ok"] = False
            for where, text in real_errors:
                failures.append(f"[{label}] {where} — console error: {text}")

        # ── pass 3: status-check every discovered same-site link ───────────
        unvisited = sorted(all_links - set(visited))
        to_check = unvisited[:MAX_LINK_CHECKS_PER_SITE]
        for link in to_check:
            if deadline.exceeded:
                failures.append(
                    f"[{label}] DEADLINE exceeded ({deadline.seconds:.0f}s) during the "
                    f"link check — crawl result is INCOMPLETE"
                )
                break
            try:
                r = desktop_ctx.request.get(link, timeout=LINK_TIMEOUT_MS, max_redirects=5)
                status = r.status
            except Exception as exc:
                failures.append(f"[{label}] link {link} — request failed: {exc}")
                continue
            if status >= 400:
                failures.append(f"[{label}] link {link} — HTTP {status}")
            stats["links_checked"] += 1
        # Beyond-cap links are an honest coverage note, not a failure: this is
        # a bounded SMOKE (a different 150 get checked as content shifts), and
        # the per-site summary prints checked-of-found so shrinkage is visible.
        stats["links_uncheckable"] = max(0, len(unvisited) - MAX_LINK_CHECKS_PER_SITE)
    finally:
        desktop_ctx.close()
        mobile_ctx.close()

    stats["pages"] = len(visited)
    stats["links_checked"] += len(visited)  # crawled pages ARE checked links
    stats["links_found"] = len(all_links)
    return failures, stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--max-pages",
        type=int,
        default=int(os.environ.get("SMOKE_CRAWL_MAX_PAGES", DEFAULT_MAX_PAGES_PER_SITE)),
        help="hard cap on crawled pages per site",
    )
    parser.add_argument(
        "--deadline",
        type=float,
        default=float(os.environ.get("SMOKE_CRAWL_DEADLINE", DEFAULT_DEADLINE_SECONDS)),
        help="global wall-clock budget in seconds (exceeding it FAILS the run)",
    )
    parser.add_argument(
        "--executable-path",
        default=os.environ.get("SMOKE_CRAWL_EXECUTABLE_PATH") or None,
        help="Chromium binary override (agent-container workaround; unset in CI)",
    )
    parser.add_argument(
        "--proxy-server",
        default=os.environ.get("SMOKE_CRAWL_PROXY_SERVER") or None,
        help="explicit --proxy-server for Chromium (agent-container workaround)",
    )
    parser.add_argument(
        "--browser-arg",
        action="append",
        default=os.environ.get("SMOKE_CRAWL_BROWSER_ARGS", "").split() or None,
        help="extra Chromium arg (repeatable), e.g. --ssl-version-max=tls1.2",
    )
    args = parser.parse_args(argv)

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("smoke-crawl: playwright is not installed (pip install playwright)")
        return 1

    allowlist = [re.compile(p) for p in CONSOLE_ERROR_ALLOWLIST]
    deadline = Deadline(args.deadline)
    all_failures: list[str] = []
    summaries: list[str] = []

    with sync_playwright() as pw:
        launch_kwargs: dict = {"headless": True}
        if args.executable_path:
            launch_kwargs["executable_path"] = args.executable_path
        browser_args = list(args.browser_arg or [])
        if args.proxy_server:
            browser_args.append(f"--proxy-server={args.proxy_server}")
        if browser_args:
            launch_kwargs["args"] = browser_args
        browser = pw.chromium.launch(**launch_kwargs)
        try:
            for label, base in SITES:
                def context_factory(viewport, _base=base):
                    return browser.new_context(viewport=viewport, base_url=_base)

                failures, stats = crawl_site(
                    context_factory,
                    label,
                    base,
                    max_pages=args.max_pages,
                    deadline=deadline,
                    allowlist=allowlist,
                )
                all_failures.extend(failures)
                verdict = "PASS" if not failures else "FAIL"
                found = stats["links_checked"] + stats["links_uncheckable"]
                summaries.append(
                    f"{label:14}  {verdict:4}  pages: {stats['pages']:3} "
                    f"(desktop 1280 + mobile 375)  same-site links checked: "
                    f"{stats['links_checked']:3} of {found:3}  console errors: "
                    f"{'0' if stats['console_ok'] else 'YES'}"
                )
        finally:
            browser.close()

    print("smoke-crawl — per-site summary")
    print("-" * 78)
    for line in summaries:
        print(line)
    print("-" * 78)
    if all_failures:
        print(f"FAILURES ({len(all_failures)}):")
        for f in all_failures:
            print(f"  {f}")
        print("RESULT: FAIL")
        return 1
    print("RESULT: PASS — every page 200, zero console errors, no broken same-site links")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
