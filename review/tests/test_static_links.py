"""Link integrity over the STATIC EXPORT — every internal href/src on every
exported page must resolve to a file under the base path, and every fragment
must resolve to an id on its target page.

Why this exists (2026-09-03): ``gen_static.py``'s exit 0 proves every route
rendered 200 — it says nothing about the links inside the pages. The
double-prefix P1 (``/websites/websites/``) shipped through it, and a grep for
a link string passes a misspelled or double-prefixed href just the same. This
test parses the exported tree the way a browser would and stats the target.

Zero network: the export walks the app through the TestClient from committed
review/data/**; external (http) links are not fetched — they are pinned by
``test_first_time_reader.py`` and the story module's own conventions.
"""

from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from review import gen_static  # noqa: E402

BASE_PATH = "/websites"
SITE_URL = "https://menno420.github.io/websites"


class _Collector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.ids: set[str] = set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a and a["id"]:
            self.ids.add(a["id"])
        if tag == "a" and a.get("name"):
            self.ids.add(a["name"])
        for key in ("href", "src", "action"):
            v = a.get(key)
            if v:
                self.links.append(v)


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    out = tmp_path_factory.mktemp("site")
    rc = gen_static.export(out, BASE_PATH, SITE_URL)
    assert rc == 0, "export reported non-200 routes"
    pages: dict[Path, _Collector] = {}
    for html in out.rglob("*.html"):
        c = _Collector()
        c.feed(html.read_text(encoding="utf-8"))
        pages[html] = c
    assert pages, "export produced no HTML"
    return out, pages


def _target_file(out: Path, path: str) -> Path | None:
    """The file a path under the base path would serve, or None."""
    if not path.startswith(BASE_PATH + "/") and path != BASE_PATH:
        return None
    rel = path[len(BASE_PATH):].lstrip("/")
    candidates = [out / rel / "index.html", out / rel]
    if rel == "":
        candidates = [out / "index.html"]
    for c in candidates:
        if c.is_file():
            return c
    return None


def test_every_internal_link_resolves_to_a_file(site):
    out, pages = site
    broken: list[str] = []
    for html, c in pages.items():
        for link in c.links:
            parts = urlsplit(link)
            if parts.scheme or parts.netloc:
                continue  # external — pinned elsewhere, never fetched here
            if link.startswith("#") or link.startswith("mailto:"):
                continue
            if not parts.path:
                continue
            assert not parts.path.startswith("//"), (html, link)
            # a root-relative link that missed the base-path rewrite is broken
            # on Pages even though it looks fine in the source app
            if not parts.path.startswith(BASE_PATH):
                broken.append(f"{html.relative_to(out)} -> {link} (missing base path)")
                continue
            if _target_file(out, parts.path) is None:
                broken.append(f"{html.relative_to(out)} -> {link}")
    assert not broken, "\n".join(broken)


def test_no_double_prefix_anywhere(site):
    out, pages = site
    for html in pages:
        text = html.read_text(encoding="utf-8")
        assert f"{BASE_PATH}{BASE_PATH}/" not in text, html
        assert f"{SITE_URL}{BASE_PATH}" not in text, html


def test_every_fragment_resolves_to_an_id_on_its_target(site):
    out, pages = site
    missing: list[str] = []
    for html, c in pages.items():
        for link in c.links:
            parts = urlsplit(link)
            if parts.scheme or parts.netloc or not parts.fragment:
                continue
            if parts.path:
                target = _target_file(out, parts.path)
                if target is None:
                    continue  # reported by the link test above
                ids = pages[target].ids if target in pages else set()
            else:
                ids = c.ids
            if parts.fragment not in ids:
                missing.append(f"{html.relative_to(out)} -> {link}")
    assert not missing, "\n".join(missing)


def test_new_pages_are_in_the_export(site):
    out, _ = site
    for rel in ("story", "examples", "after"):
        assert (out / rel / "index.html").is_file(), rel
    # and the mockup section is there, labelled
    text = (out / "examples" / "index.html").read_text(encoding="utf-8")
    assert 'id="projects-overview-mockup"' in text
    assert "A proposal, not a screenshot." in text
