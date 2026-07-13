"""Offline tests for ``extract_paste_body``: the /prompts library (and the
/projects dispatch screen — same shared layer) must render AND copy only the
clean paste body of each registry artifact, never the generation metadata
the fleet-manager generator prepends (comment headers, the ``> **GENERATED
COPY — NOT SOURCE OF TRUTH**`` provenance blockquote, the ``> char-count``
budget blockquote, the ``<!-- registry-header-end -->`` marker).

Pinned here: the authoritative-delimiter rule (everything after
``registry-header-end`` when present), the heuristic top-strip for artifacts
without the marker (universals: comment header only; multi-line comment
headers too), the no-``<!--``-ever guarantee, idempotence on already-clean
text, and — via the route with a stubbed fetcher — that the rendered
``<pre>`` (which IS the copy payload: copycode.js copies ``pre.textContent``)
carries the cleaned body. Network-free: ``github.fetch_file`` monkeypatched
(the route test also pins ``github.repo_api`` — the drift chip's registry
listing).
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import github, prompt_artifacts, prompts  # noqa: E402
from app.main import app  # noqa: E402
from app.prompt_artifacts import extract_paste_body  # noqa: E402


def _res(ok=True, status=200, data=None, error="", cached=False):
    return {"ok": ok, "status": status, "data": data, "error": error,
            "fetched_at": "12:00:00 UTC", "cached": cached, "url": ""}


# --------------------------------------------------------------------------- #
# representative upstream fixtures
# --------------------------------------------------------------------------- #

# (a) per-seat instructions.md: comment headers + GENERATED COPY blockquote +
#     char-count blockquote + the authoritative registry-header-end marker.
INSTRUCTIONS = (
    "<!-- v6 · 2026-07-12 · fleet-manager projects registry — "
    "GENERATED COPY, do not edit -->\n"
    "<!-- generated from docs/prompts/v3/instructions-core.md @ abc1234 -->\n"
    "\n"
    "> **GENERATED COPY — NOT SOURCE OF TRUTH** — edit the source in\n"
    "> docs/prompts/v3/ and re-run the generator; direct edits are\n"
    "> overwritten.\n"
    "\n"
    "> char-count: 2861 / budget 3000 (Custom Instructions limit)\n"
    "\n"
    "<!-- registry-header-end -->\n"
    "\n"
    "v3.4 · websites — Custom Instructions\n"
    "\n"
    "You are the websites seat. HANDOFF.md first.\n"
)
INSTRUCTIONS_FIRST_LINE = "v3.4 · websites — Custom Instructions"

# (b) session-ender: leading single-line comment header, NO marker.
SESSION_ENDER = (
    "<!-- v3.3 · 2026-07-12 · provenance: docs/prompts/v3/session-ender.md "
    "· GENERATED COPY, do not edit -->\n"
    "\n"
    "v3.3 · Universal Session-Ender\n"
    "\n"
    "Wrap up: commit, update the journal, write the handoff.\n"
)
SESSION_ENDER_FIRST_LINE = "v3.3 · Universal Session-Ender"

# (c) universal-startup: leading MULTI-LINE comment header, NO marker.
UNIVERSAL_STARTUP = (
    "<!--\n"
    "  v3.2 · 2026-07-12 · universal-startup\n"
    "  GENERATED COPY, do not edit — source: docs/prompts/v3/\n"
    "-->\n"
    "\n"
    "v3.2 · Universal Startup\n"
    "\n"
    "Read HANDOFF.md, then docs/current-state.md.\n"
)
UNIVERSAL_STARTUP_FIRST_LINE = "v3.2 · Universal Startup"

_CASES = (
    (INSTRUCTIONS, INSTRUCTIONS_FIRST_LINE),
    (SESSION_ENDER, SESSION_ENDER_FIRST_LINE),
    (UNIVERSAL_STARTUP, UNIVERSAL_STARTUP_FIRST_LINE),
)


# --------------------------------------------------------------------------- #
# the helper
# --------------------------------------------------------------------------- #


def test_extract_paste_body_strips_all_generation_metadata():
    for raw, first_line in _CASES:
        body = extract_paste_body(raw)
        assert "<!--" not in body
        assert "GENERATED COPY" not in body
        assert "char-count" not in body
        assert "registry-header-end" not in body
        # the clean body starts at the real first content line …
        assert body.startswith(first_line)
        # … and keeps everything after it (spot-check the last real line)
        assert body.rstrip("\n").splitlines()[-1] == \
            raw.rstrip("\n").splitlines()[-1]


def test_registry_header_end_is_the_authoritative_delimiter():
    # everything BEFORE the marker goes, even unrecognized junk; everything
    # AFTER it stays (minus leading blanks) — no heuristics involved.
    raw = ("weird unrecognized preamble line\n"
           "<!-- registry-header-end -->\n\n\nBODY LINE 1\n> a real quote\n")
    assert extract_paste_body(raw) == "BODY LINE 1\n> a real quote\n"


def test_full_line_comments_are_dropped_anywhere_in_the_body():
    raw = ("v1 · title\n"
           "<!-- a stray full-line generator comment -->\n"
           "line after\n"
           "<!-- multi\nline\ncomment -->\n"
           "last line\n")
    body = extract_paste_body(raw)
    assert "<!--" not in body
    assert body == "v1 · title\nline after\nlast line\n"


def test_idempotent_on_already_clean_text():
    for raw, _ in _CASES:
        clean = extract_paste_body(raw)
        assert extract_paste_body(clean) == clean
    # untouched apart from leading-blank stripping
    plain = "v3.4 · a title\n\nbody   with  spaces\tand tabs\n"
    assert extract_paste_body(plain) == plain
    assert extract_paste_body("\n\n" + plain) == plain
    assert extract_paste_body("") == ""
    # a real body-opening blockquote is NOT metadata — it survives
    quoted = "> **Status:** `binding`\n\nreal body\n"
    assert extract_paste_body(quoted) == quoted


def test_build_artifact_text_is_the_clean_body_provenance_from_full_file():
    a = prompt_artifacts.build_artifact(
        "projects/websites/instructions.md", "Custom Instructions",
        _res(data=INSTRUCTIONS), seat="websites",
    )
    assert a["ok"] and a["text"] == extract_paste_body(INSTRUCTIONS)
    assert a["chars"] == len(a["text"])
    # the version line lives in the stripped header — provenance still found
    assert a["provenance"].startswith("v6 · 2026-07-12")


# --------------------------------------------------------------------------- #
# route: the rendered <pre> — which copycode.js copies verbatim — is clean
# --------------------------------------------------------------------------- #


def _pre_blocks(html):
    # attribute-tolerant: the historical-reference pre carries class=nocopy
    return re.findall(r"<pre[^>]*>(.*?)</pre>", html, flags=re.DOTALL)


def test_prompts_route_renders_and_copies_only_the_clean_body(monkeypatch):
    fixtures = {
        "instructions.md": INSTRUCTIONS,
        "session-ender.md": SESSION_ENDER,
        "universal-startup.md": UNIVERSAL_STARTUP,
    }

    async def fake_fetch(repo, path, ref="main", refresh=False):
        return _res(data=fixtures.get(path.rsplit("/", 1)[-1],
                                      "v0 · plain body\n"))

    async def fake_api(repo, subpath="", refresh=False):
        # the drift chip's registry listing — matched, and network-free
        return _res(data=[{"type": "dir", "name": s, "path": f"projects/{s}"}
                          for s in prompts.SEATS])

    monkeypatch.setattr(github, "fetch_file", fake_fetch)
    monkeypatch.setattr(github, "repo_api", fake_api)
    r = TestClient(app).get("/prompts")
    assert r.status_code == 200
    pres = _pre_blocks(r.text)
    assert pres
    for pre in pres:
        # escaped or not, no metadata may reach the copy payload
        assert "<!--" not in pre and "&lt;!--" not in pre
        assert "GENERATED COPY" not in pre
        assert "char-count" not in pre
        assert "registry-header-end" not in pre
    for first_line in (INSTRUCTIONS_FIRST_LINE, SESSION_ENDER_FIRST_LINE,
                       UNIVERSAL_STARTUP_FIRST_LINE):
        assert any(pre.startswith(first_line) for pre in pres)
    # the full file (with metadata) stays reachable + the note says so
    assert "full file on GitHub" in r.text
    assert "generation metadata hidden" in r.text
