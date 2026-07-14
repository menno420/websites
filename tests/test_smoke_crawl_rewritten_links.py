"""Pins for scripts/smoke_crawl.py's sampled rewritten-link existence check
(2026-07-14, backlog promotion of the md-relative-links session's 💡).

PR #322 rewrote relative links inside rendered remote markdown into EXTERNAL
github.com blob URLs (links) and raw.githubusercontent.com URLs (images) —
moving the 404 failure class outside every gate's scope, because the
smoke-crawl never follows external links. These tests pin the pure logic of
the bounded sample that puts a floor back under the rewrite: the collector
(HTML in, (url, source page) pairs out), the deterministic sampler (≤10,
sorted + evenly strided, no randomness/clock), and the status classifier
(2xx/3xx pass, 403 pass-with-private-note, 404 fail, error warn).

Offline: pure functions only — no network, no playwright (smoke_crawl.py
lazy-imports playwright inside main(), so the module imports cleanly here).
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
_MOD_PATH = REPO_ROOT / "scripts" / "smoke_crawl.py"

_spec = importlib.util.spec_from_file_location("_smoke_crawl", _MOD_PATH)
assert _spec and _spec.loader
smoke_crawl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(smoke_crawl)

PAGE = "https://control-plane-production-abb0.up.railway.app/fleet"

# The exact URL shapes app/journal.py's rewriter emits (_resolve_source_url):
# github.com/<owner>/<repo>/blob/<ref>/<path> for links,
# raw.githubusercontent.com/<owner>/<repo>/<ref>/<path> for images.
BLOB_URL = "https://github.com/menno420/superbot/blob/main/docs/gen2-blueprint.md"
RAW_URL = "https://raw.githubusercontent.com/menno420/superbot/main/img/logo.png"
RAW_VIEW_URL = "https://github.com/menno420/superbot/raw/main/assets/kit.zip"


# ── collector ────────────────────────────────────────────────────────────────


def test_collector_extracts_rewriter_shaped_urls_with_source_page():
    html = f"""
    <div class="md">
      <p><a href="{BLOB_URL}">blueprint</a></p>
      <img src="{RAW_URL}" alt="logo">
      <a href="{RAW_VIEW_URL}">kit</a>
    </div>
    """
    pairs = smoke_crawl.collect_rewritten_links(html, PAGE)
    assert (BLOB_URL, PAGE) in pairs
    assert (RAW_URL, PAGE) in pairs
    assert (RAW_VIEW_URL, PAGE) in pairs
    assert all(src == PAGE for _url, src in pairs)


def test_collector_ignores_non_rewriter_urls():
    html = """
    <a href="/fleet">same-site relative</a>
    <a href="https://example.com/docs/x.md">external non-github</a>
    <a href="https://github.com/menno420/superbot">repo root, not blob/raw</a>
    <a href="https://github.com/menno420/superbot/issues/1">issues view</a>
    <a href="mailto:x@example.com">mail</a>
    <a href="javascript:void(0)">js</a>
    <img src="/static/logo.svg">
    """
    assert smoke_crawl.collect_rewritten_links(html, PAGE) == []


def test_collector_strips_fragments_and_unescapes_entities():
    # bleach/Chromium serialize attributes entity-escaped; fragments are the
    # rewriter's own (#L-anchors) and must not split one target into many.
    html = (
        f'<a href="{BLOB_URL}#usage">a</a>'
        '<a href="https://github.com/menno420/superbot/blob/main/a.md?x=1&amp;y=2">b</a>'
    )
    pairs = smoke_crawl.collect_rewritten_links(html, PAGE)
    assert (BLOB_URL, PAGE) in pairs
    assert (
        "https://github.com/menno420/superbot/blob/main/a.md?x=1&y=2",
        PAGE,
    ) in pairs


# ── sampler ──────────────────────────────────────────────────────────────────


def _collected(n: int) -> dict[str, set[str]]:
    return {
        f"https://github.com/menno420/superbot/blob/main/docs/f{i:03}.md": {
            f"https://cp.example/page{i % 3}"
        }
        for i in range(n)
    }


def test_sampler_is_bounded_at_ten():
    assert smoke_crawl.REWRITTEN_SAMPLE_LIMIT == 10
    sample = smoke_crawl.sample_rewritten_links(_collected(47))
    assert len(sample) == 10


def test_sampler_is_deterministic_and_sorted():
    collected = _collected(47)
    first = smoke_crawl.sample_rewritten_links(collected)
    second = smoke_crawl.sample_rewritten_links(dict(reversed(list(collected.items()))))
    assert first == second  # same set → same sample, insertion order ignored
    urls = [u for u, _src in first]
    assert urls == sorted(urls)  # stable, sorted output order


def test_sampler_strides_evenly_first_and_last_included():
    collected = _collected(47)
    urls = [u for u, _src in smoke_crawl.sample_rewritten_links(collected)]
    all_sorted = sorted(collected)
    assert urls[0] == all_sorted[0]
    assert urls[-1] == all_sorted[-1]
    assert len(set(urls)) == len(urls)  # no index collapses to a duplicate


def test_sampler_returns_everything_when_under_the_cap():
    collected = _collected(4)
    sample = smoke_crawl.sample_rewritten_links(collected)
    assert [u for u, _src in sample] == sorted(collected)


def test_sampler_source_page_is_deterministic():
    url = "https://github.com/menno420/superbot/blob/main/README.md"
    collected = {url: {"https://cp.example/z", "https://cp.example/a"}}
    assert smoke_crawl.sample_rewritten_links(collected) == [
        (url, "https://cp.example/a")  # lexicographically first source page
    ]


def test_sampler_empty_input_and_zero_limit():
    assert smoke_crawl.sample_rewritten_links({}) == []
    assert smoke_crawl.sample_rewritten_links(_collected(5), limit=0) == []


# ── classifier ───────────────────────────────────────────────────────────────


def test_classifier_2xx_3xx_pass():
    for status in (200, 204, 301, 302):
        assert smoke_crawl.classify_rewritten_status(status) == "pass"


def test_classifier_403_passes_as_private():
    assert smoke_crawl.classify_rewritten_status(403) == "pass-private"


def test_classifier_404_fails():
    assert smoke_crawl.classify_rewritten_status(404) == "fail"


def test_classifier_errors_and_odd_statuses_warn():
    for status in (None, 429, 500, 503):
        assert smoke_crawl.classify_rewritten_status(status) == "warn"


# ── check runner (fake fetch, offline) ───────────────────────────────────────


def _fake_fetch(table: dict[str, tuple[int | None, str]]):
    def fetch(url: str):
        return table[url]

    return fetch


def test_check_404_fails_naming_url_and_source_page():
    url = "https://github.com/menno420/superbot/blob/main/gone.md"
    src = "https://cp.example/reviews"
    failures, lines = smoke_crawl.check_rewritten_links(
        [(url, src)], 1, fetch=_fake_fetch({url: (404, "")})
    )
    assert len(failures) == 1
    assert url in failures[0] and src in failures[0] and "404" in failures[0]
    assert any(line.lstrip().startswith("FAIL") for line in lines)


def test_check_403_passes_with_private_repo_note():
    url = "https://github.com/menno420/private-lane/blob/main/x.md"
    failures, lines = smoke_crawl.check_rewritten_links(
        [(url, PAGE)], 1, fetch=_fake_fetch({url: (403, "")})
    )
    assert failures == []
    note = next(line for line in lines if url in line)
    assert "PASS" in note and "private repo" in note


def test_check_network_error_warns_never_fails():
    url = "https://github.com/menno420/superbot/blob/main/x.md"
    failures, lines = smoke_crawl.check_rewritten_links(
        [(url, PAGE)], 1, fetch=_fake_fetch({url: (None, "URLError: timed out")})
    )
    assert failures == []
    warn = next(line for line in lines if url in line)
    assert "WARN" in warn and "URLError: timed out" in warn


def test_check_all_alive_produces_no_failures():
    urls = [
        ("https://github.com/menno420/superbot/blob/main/a.md", PAGE),
        ("https://raw.githubusercontent.com/menno420/superbot/main/b.png", PAGE),
    ]
    failures, lines = smoke_crawl.check_rewritten_links(
        urls, 2, fetch=lambda u: (200, "")
    )
    assert failures == []
    assert sum(1 for line in lines if line.lstrip().startswith("PASS")) == 2
