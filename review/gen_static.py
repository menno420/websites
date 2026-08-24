"""Static export of the review site — the whole rendered surface as files.

The program-review audience concluded 2026-07-21; the site is rendered entirely
from committed data (`review/data/**` + the committed editions). This exporter
walks every GET route through FastAPI's TestClient — no server, no network —
and writes the rendered bytes as the plain file tree GitHub Pages currently
serves. The former Railway `review` service retired on 2026-08-20
(fleet-manager `docs/planning/2026-08-20-railway-keep-bot-only-worklist.md`
slice 3; the decisions ledger carries the entry).

Route → file mapping:
  * `/`                      → `index.html`
  * an extensionless page    → `<path>/index.html`   (pretty URLs, so the
                               site works under the Pages sub-path with the
                               same `/x` link shapes browsers resolve)
  * a path with an extension → the literal file (`story.json`,
                               `reviews/feed.xml`, `robots.txt`, …)
  * `/static/**`             → copied verbatim
  * `/healthz`, `/version`   → SKIPPED with their reason: runtime probes of a
                               service process; a static tree has neither.

Parameterized routes expand from the same committed data the app reads
(`fleetdata.load_fleet()` lanes, `editions.list_editions()` slugs) — the
exact expanders `review/tests/test_clarity_structure.py` pins, so the export
walk and the clarity walk cannot disagree about the route set.

Because Pages serves the project site under `/<repo>/`, every root-relative
URL in exported HTML/XML (`href="/x"`, `src="/static/…"`) is rewritten to
carry the base path (`--base-path`, default `/websites`). Full URLs and
protocol-relative URLs are never touched. The Atom feed's absolute URLs are
handled in the same rewrite pass: the TestClient runs on the HOST half of
`--site-url` (this httpx keeps a base-URL PATH on join, so a path-carrying
base 404s every route — measured), and the host-rooted absolute URLs the
feed renders from `request.base_url` are then rewritten host-root →
site-url.

Usage:  python3 review/gen_static.py --out _site [--base-path /websites]
        [--site-url https://menno420.github.io/websites]
Exit 0 on a complete tree; exit 1 (with the route named) on any non-200 a
page route answers — a partial export must never deploy as if whole.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.routing import APIRoute  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from review import editions, fleetdata  # noqa: E402
from review.app import app  # noqa: E402

# Runtime service probes — meaningless as files (there is no process to
# probe). Named here so the completeness check below can prove nothing else
# was silently dropped.
SKIP_ROUTES = {
    "/healthz": "Railway healthcheck of a process — no process in a static tree",
    "/version": "deployed-SHA probe of a process — same reason",
    "/favicon.ico": "served from /static/favicon.svg in the export; the "
    "route only re-serves that file for browser probes",
}

# href="/x", src="/x" or form action="/x" — but never href="//host"
# (protocol-relative) and never full URLs. Double-quoted attributes only:
# Jinja templates and the rendered tree use double quotes throughout (the
# smoke-crawl extractor leans on the same fact). `action` is in the set
# because the list-filter partial renders GET search forms — un-rewritten,
# a Pages submit would land outside /websites and 404 (Codex #509 round 1).
_ROOT_REL_RE = re.compile(r'\b(href|src|action)="/(?!/)')


def _iter_get_routes(router):
    for route in getattr(router, "routes", []):
        original = getattr(route, "original_router", None)
        if original is not None:
            yield from _iter_get_routes(original)
            continue
        if isinstance(route, APIRoute) and "GET" in (route.methods or set()):
            yield route


def export_urls() -> list[str]:
    """Every concrete URL the export walks, from the router + committed data."""
    urls: list[str] = []
    for route in sorted(_iter_get_routes(app), key=lambda r: r.path):
        path = route.path
        if path in SKIP_ROUTES:
            continue
        if "{" not in path:
            urls.append(path)
        elif path == "/fleet/{repo}":
            fl = fleetdata.load_fleet()
            assert fl["ok"], f"fleet mirror failed to load: {fl['error']}"
            lanes = fl["data"].get("lanes", [])
            urls.extend(f"/fleet/{ln['repo']}" for ln in lanes if ln.get("repo"))
        elif path == "/reviews/{slug}":
            urls.extend(f"/reviews/{e['slug']}" for e in editions.list_editions())
        else:
            raise SystemExit(
                f"unexpanded parameterized GET route {path!r} — give it an "
                "expander here (mirroring tests/test_clarity_structure.py) "
                "or a SKIP_ROUTES reason before exporting"
            )
    return urls


# Non-HTML routes written as literal files — an EXPLICIT suffix set, never a
# "contains a dot" heuristic: the committed fleet carries the lane
# `codetool-lab-opus4.8`, whose page route would otherwise export as a bare
# FILE instead of a directory index (Codex #509 round 1 — the artifact was
# sitting in the first export).
FILE_SUFFIXES = (".json", ".xml", ".txt")


def out_path(url: str, out_dir: Path) -> Path:
    rel = url.lstrip("/")
    if url == "/":
        return out_dir / "index.html"
    if rel.endswith(FILE_SUFFIXES):
        return out_dir / rel
    return out_dir / rel / "index.html"


def rewrite_urls(
    body: bytes, content_type: str, base_path: str, host_root: str, site_url: str
) -> bytes:
    """Prefix root-relative href/src URLs with the Pages base path, and (for
    the Atom feed) move host-rooted absolute URLs onto the full site URL."""
    if not base_path or base_path == "/":
        return body
    if "html" not in content_type and "xml" not in content_type:
        return body
    text = body.decode("utf-8")
    text = _ROOT_REL_RE.sub(lambda m: f'{m.group(1)}="{base_path}/', text)
    # Host-root absolutes (the Atom feed renders from request.base_url) move
    # onto the full site URL — IDEMPOTENTLY: a URL already carrying the base
    # path is left alone, otherwise a hardcoded full Pages URL in a template
    # came out double-prefixed (…/websites/websites/ — Codex #510 round 2).
    prefix = host_root.rstrip("/") + "/"
    target = site_url.rstrip("/") + "/"
    if target != prefix:
        if target.startswith(prefix):
            base_seg = target[len(prefix):]
            text = re.sub(
                re.escape(prefix) + "(?!" + re.escape(base_seg) + ")",
                target,
                text,
            )
        else:
            text = text.replace(prefix, target)
    return text.encode("utf-8")


def export(out_dir: Path, base_path: str, site_url: str) -> int:
    # Static mode: templates drop the interactive surfaces (list-filter
    # forms/links, the /ask widget) and say so — read per request by
    # review/app.py _base_ctx, so setting it here binds every render below.
    os.environ["REVIEW_STATIC_EXPORT"] = "1"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    # The client runs on the HOST half only: this httpx KEEPS a base-URL path
    # segment when joining request paths, so a path-carrying base would send
    # /websites/story.json to an app that routes /story.json — every route
    # 404s (measured before this split).
    host_root = site_url
    if base_path and site_url.endswith(base_path):
        host_root = site_url[: -len(base_path)]
    failures: list[str] = []
    written = 0
    with TestClient(app, base_url=host_root) as client:
        for url in export_urls():
            resp = client.get(url)
            if resp.status_code != 200:
                failures.append(f"{url} -> HTTP {resp.status_code}")
                continue
            body = rewrite_urls(
                resp.content,
                resp.headers.get("content-type", ""),
                base_path,
                host_root,
                site_url,
            )
            dest = out_path(url, out_dir)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(body)
            written += 1
    static_src = Path(__file__).parent / "static"
    shutil.copytree(static_src, out_dir / "static")
    # Pages runs Jekyll by default, which drops underscore-prefixed paths;
    # the export must serve byte-what-was-written.
    (out_dir / ".nojekyll").write_text("")
    print(f"exported {written} routes + static/ -> {out_dir}")
    if failures:
        print("EXPORT INCOMPLETE — non-200 routes (a partial tree must not deploy):")
        for f in failures:
            print(f"  {f}")
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default="_site", help="output directory")
    ap.add_argument(
        "--base-path",
        default="/websites",
        help="Pages sub-path the site serves under ('' for a root deploy)",
    )
    ap.add_argument(
        "--site-url",
        default="https://menno420.github.io/websites",
        help="published base URL (absolute URLs in the Atom feed render from it)",
    )
    args = ap.parse_args()
    return export(Path(args.out), args.base_path.rstrip("/"), args.site_url)


if __name__ == "__main__":
    raise SystemExit(main())
