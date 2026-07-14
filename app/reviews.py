"""Review-queue view (/reviews): render fleet-manager's
``docs/review-queue.md`` — the fleet's post-merge second-review ledger.

ORDER 009 increment (3): the gen-2 merge-authority policy is "no PR ever
waits for review before landing" — a PR that deserves second eyes merges
anyway and gets a ROW in the manager's review queue (post-merge review;
veto = revert). Those rows were browsable nowhere. This page renders them:
one card per open row (`repo#N · what to re-check · why-risky · drain
path/status`), the ``repo#N`` token deep-linked to the actual PR, struck
(``~~…~~``) rows counted as reviewed, and the full ledger rendered below so
nothing is hidden by the parse.

The launch-readiness / economics **findings docs are linked from the doc
itself**: every markdown link in the ledger pointing into the manager's
``findings/`` / ``planning/`` trees is extracted and surfaced as a
"findings & records" link list — extracting instead of hardcoding dated
filenames means an upstream rename never leaves this page pointing at a
ghost.

Same honest-degradation ladder as /queue-/environments-/projects
(not-configured / unavailable / empty) over the same TTL-cached ``github``
layer; fleet-manager is READ-ONLY here and anonymously readable today (the
raw fetch path — verified live 2026-07-10).
"""

from __future__ import annotations

import re
from typing import Any

from . import config, github, journal

REPO = "fleet-manager"
PATH = "docs/review-queue.md"

# `repo#N` PR tokens (the ledger's row key), e.g. `superbot#1920`,
# `pokemon-mod-lab#8`. Owner is implicit (single-owner fleet).
_PR_TOKEN_RE = re.compile(r"\b([A-Za-z0-9._-]+)#(\d+)\b")

# Markdown links whose target sits in the manager's findings/planning trees
# (relative from docs/, absolute from the repo, or a full GitHub URL).
_DOC_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")

MAX_ROWS = 100


def _doc_url() -> str:
    return f"https://github.com/{config.OWNER}/{REPO}/blob/main/{PATH}"


def _pr_url(repo: str, num: str) -> str:
    return f"https://github.com/{config.OWNER}/{repo}/pull/{num}"


def _resolve_link(target: str) -> str:
    """A link target from review-queue.md → an absolute GitHub URL.

    The doc lives at ``docs/review-queue.md``, so a relative target like
    ``findings/night-review.md`` resolves under ``docs/``. Full URLs pass
    through; anchors-only links resolve to the doc itself.
    """
    t = target.strip()
    if t.startswith("http://") or t.startswith("https://"):
        return t
    if t.startswith("#"):
        return _doc_url() + t
    t = t.lstrip("./")
    base = f"https://github.com/{config.OWNER}/{REPO}/blob/main"
    if t.startswith("docs/"):
        return f"{base}/{t}"
    return f"{base}/docs/{t}"


def extract_findings_links(text: str) -> list[dict[str, str]]:
    """Every markdown link in the ledger that points into the manager's
    ``findings/`` or ``planning/`` trees — the launch-readiness / economics
    records the queue's rows cite. Deduplicated by resolved URL, order kept."""
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for label, target in _DOC_LINK_RE.findall(text or ""):
        if "findings/" in target or "planning/" in target:
            url = _resolve_link(target)
            if url not in seen:
                seen.add(url)
                out.append({"label": label.strip("`* "), "url": url})
    return out


def _split_cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def parse_rows(text: str) -> list[dict[str, Any]]:
    """Parse the ledger's markdown table rows into structured review items.

    Columns are located by HEADER NAME (a reorder can't shift a value —
    the fleet-manifest parser's lesson). Each row yields ``{pr_repo,
    pr_number, pr_url, what, why, status, reviewed, raw}`` where ``reviewed``
    is True for a struck (``~~…~~``) row. Free text outside tables is
    ignored here — the page renders the whole doc below the cards, so
    nothing is lost to the parse.
    """
    rows: list[dict[str, Any]] = []
    header: list[str] | None = None
    ci: dict[str, int | None] = {}

    for line in (text or "").splitlines():
        s = line.strip()
        if not (s.startswith("|") and s.endswith("|")):
            header = None
            continue
        cells = _split_cells(s)
        joined = "".join(cells)
        if joined and set(joined) <= set("-: "):
            continue  # header separator
        low = [c.lower() for c in cells]
        if any("pr" == c or c.startswith("pr ") for c in low) and any(
            "re-check" in c or "what" in c for c in low
        ):
            header = low

            def col(*needles: str) -> int | None:
                for idx, name in enumerate(header):  # type: ignore[arg-type]
                    if any(n in name for n in needles):
                        return idx
                return None

            ci = {
                "pr": col("pr"),
                "what": col("re-check", "what"),
                "why": col("why"),
                "status": col("status", "drain"),
            }
            continue
        if header is None or ci.get("pr") is None:
            continue

        def get(key: str) -> str:
            idx = ci.get(key)
            return cells[idx] if idx is not None and idx < len(cells) else ""

        pr_cell = get("pr")
        m = _PR_TOKEN_RE.search(pr_cell.replace("~~", ""))
        reviewed = "~~" in s
        rows.append(
            {
                "pr_repo": m.group(1) if m else "",
                "pr_number": m.group(2) if m else "",
                "pr_url": _pr_url(m.group(1), m.group(2)) if m else "",
                "pr_label": pr_cell.replace("~~", "").strip() or "?",
                "what": get("what").replace("~~", "").strip(),
                "why": get("why").replace("~~", "").strip(),
                "status": get("status").replace("~~", "").strip(),
                "reviewed": reviewed,
            }
        )
        if len(rows) >= MAX_ROWS:
            break
    return rows


async def overview(refresh: bool = False) -> dict[str, Any]:
    """The rendered review queue, or an honest degraded state.

    ``state``: ``ok`` | ``empty`` (doc missing upstream — 404) |
    ``not-configured`` (GITHUB_TOKEN unset and the fetch failed non-404) |
    ``unavailable`` (token set, fetch failed). Always 200 at the route."""
    token_set = bool(config.GITHUB_TOKEN)
    out: dict[str, Any] = {
        "state": "ok",
        "reason": "",
        "token_set": token_set,
        "doc_url": _doc_url(),
        "rows": [],
        "open_count": 0,
        "reviewed_count": 0,
        "findings_links": [],
        "body_html": "",
    }
    res = await github.fetch_file(REPO, PATH, refresh=refresh)
    if not (res["ok"] and isinstance(res["data"], str) and res["data"].strip()):
        reason = res.get("error") or f"HTTP {res.get('status')}"
        if res.get("status") == 404:
            out["state"] = "empty"
            out["reason"] = (
                f"{config.OWNER}/{REPO} has no `{PATH}` yet — the ledger "
                "renders here the moment it exists"
            )
        elif not token_set:
            out["state"] = "not-configured"
            out["reason"] = (
                "GITHUB_TOKEN is not set on this service and the "
                f"{config.OWNER}/{REPO} fetch failed ({reason})"
            )
        else:
            out["state"] = "unavailable"
            out["reason"] = reason
        return out

    text = res["data"]
    rows = parse_rows(text)
    out["rows"] = rows
    out["open_count"] = sum(1 for r in rows if not r["reviewed"])
    out["reviewed_count"] = sum(1 for r in rows if r["reviewed"])
    out["findings_links"] = extract_findings_links(text)
    out["body_html"] = journal.render_markdown(
        text, source={"repo": REPO, "path": PATH}
    )
    return out
