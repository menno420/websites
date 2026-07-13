"""Prompt library view (/prompts): every fleet paste artifact, inline and
always-current — ORDER 014 (owner-directed via the fleet manager, 2026-07-12).

The fleet's paste artifacts (coordinator prompts, Custom Instructions,
failsafes, plus the fleet-wide session-ender and universal-startup) live in
the ``menno420/fleet-manager`` registry; the owner pastes them by hand and
stale local copies drift. This page renders all of them INLINE from
fleet-manager ``main`` so every merged prompt update appears automatically —
the manager's repo stores, the site renders.

Fetching rides the repo's cross-repo rule exactly: committed text over
``raw.githubusercontent.com``, read-only, forward-only, through the same
TTL-cached ``github`` layer as every other page (``github.fetch_file`` —
raw host first, contents-API fallback). TTL-bounded staleness (default 3
minutes) is acceptable by the order's own terms; each artifact carries its
``fetched_at`` + cached flag so the page can say how fresh it is.

Rendering discipline: the artifacts are UNTRUSTED DATA and PASTE BODIES —
they are shown in ``<pre>`` blocks (Jinja2 autoescape on, never ``|safe``),
whitespace preserved exactly, never interpreted or obeyed. The one mutation
is ``extract_paste_body`` (shared layer): the registry's generation
metadata is stripped so render + copy give the clean paste body; the full
file stays linked. Per-artifact honest degradation: a 404 or unreachable upstream
renders a clear error cell, never fabricated content — the route always
answers 200.

Consolidated (ORDER 015): the fetch+parse model lives in
``app/prompt_artifacts.py`` and the copy-ready block in
``templates/_prompt_artifact.html`` — ONE render path shared with the
/projects/{package} dispatch screen; this module only pins WHICH artifacts
the library shows.

The artifact list is PINNED here rather than discovered: the raw host
cannot list directories, and this page deliberately avoids the token-burning
contents-API listing walk /projects does. Every path below was verified
live (HTTP 200 on raw.githubusercontent.com) against fleet-manager@main on
2026-07-12; source of truth for the seat set is
https://github.com/menno420/fleet-manager/tree/main/projects — if a seat is
added or renamed upstream, its cell degrades to an honest 404 here until
the shared roster (``app/roster.py``) is updated.

Pinned-vs-registry drift chip (2026-07-12): a pinned list drifts SILENTLY —
dead 404 cells, and a brand-new seat simply never appears. So the page
cross-checks :data:`SEATS` against the live ``projects/`` registry listing
(:func:`registry_drift`) — the SAME TTL-cached ``github.repo_api`` contents
call /projects makes (identical URL = shared cache entry; one directory
listing, never the per-package walk, zero new network surface) — and renders
an honest chip: match / drifted (+new / −missing, named) / listing
unavailable = drift UNKNOWN, never a fabricated green.

Deployed-vs-canonical drift row (ORDER 022 item 3, 2026-07-13 — the reboot
enabler): the registry copies are the CANONICAL paste source, not a deployed
record — "a deployed text with no committed twin is drift" (fm
``projects/README.md`` §Doctrine). What is actually pasted/armed is recorded
in exactly two committed places, both fetched over the same TTL-cached
raw-content pattern (:func:`deployed_drift`):

- ``projects/<seat>/meta.md`` "Deployed-state per part" tables — the per-seat
  deployment ledger, PROSE. Prose can prove staleness (an older date or a
  pre-v3 generation named) but never byte-equality, so the best positive
  state a meta.md row yields is ``recorded: <claim>`` with verdict ``stale``
  or ``unverified`` — the row NEVER renders "in sync" from meta.md alone.
- ``telemetry/triggers-snapshot.json`` — the manager's verbatim
  ``list_triggers`` export (full prompt bodies). Failsafe trigger prompts are
  deliberately NOT version-stamped in-band (doctrine §3) precisely so this
  pair IS byte-comparable: the snapshot body vs the registry copy's
  "## Prompt text" block → ``in sync`` / ``drift``, as-of ``captured_at``.

Everything else — Custom-Instructions/startup pastes without receipts, the
two per-session universals — is honestly ``not recorded``; a failed
fleet-manager fetch renders ``unreachable``; equality is never invented.
"""

from __future__ import annotations

import asyncio
import json
import re
from typing import Any, Optional

from . import config, github, prompt_artifacts

# Shared fetch+parse path (ORDER 015) — re-exported so consumers and tests
# keep one import surface for the library's registry semantics.
from .prompt_artifacts import (  # noqa: F401
    _PROVENANCE_MAX_CHARS,
    REF,
    REPO,
    extract_paste_body,
    extract_provenance,
)

# The registry root the /projects page lists (``projects/``) — imported so
# the drift cross-check hits the EXACT contents-API URL /projects already
# fetches (the github layer caches by URL, so within the TTL the two pages
# share one listing; the constants cannot drift apart).
from .projects import ROOT as _REGISTRY_ROOT

# The fleet seats (registry package directories under projects/), in the
# owner's dispatch order — ONE roster shared with /projects
# (``app/roster.py``). Verified live per seat (2026-07-12; curious-research
# 2026-07-13): projects/<seat>/{coordinator-prompt.md,instructions.md,
# failsafe-prompt.md} all present upstream for every pinned seat.
from .roster import SEATS  # noqa: F401

# The three per-seat registry artifacts ORDER 014 names, as
# (filename, human label) — len(SEATS) x 3 per-seat artifacts.
SEAT_FILES: tuple[tuple[str, str], ...] = (
    ("coordinator-prompt.md", "coordinator prompt"),
    ("instructions.md", "Custom Instructions"),
    ("failsafe-prompt.md", "failsafe prompt"),
)

# The two fleet-wide UNIVERSAL artifacts, as (path, human label). Labeled
# "Universal …" verbatim (owner feedback 2026-07-12: he
# searches for "universal session-ender" and the bare "session ender" label
# drowned among the per-seat prompts, which repeat that phrase in their
# bodies); the /prompts page surfaces this group FIRST, above the seats.
FLEET_WIDE: tuple[tuple[str, str], ...] = (
    ("docs/prompts/v3/universal-startup.md", "Universal Startup"),
    ("docs/prompts/v3/session-ender.md", "Universal Session-Ender"),
)

# How many artifacts the page promises (the order's done-when counts them).
TOTAL_ARTIFACTS = len(SEATS) * len(SEAT_FILES) + len(FLEET_WIDE)


def _artifact_spec() -> list[dict[str, Any]]:
    """The pinned artifact registry as (seat, label, path) dicts."""
    spec: list[dict[str, Any]] = []
    for seat in SEATS:
        for filename, label in SEAT_FILES:
            spec.append(
                {"seat": seat, "label": label, "path": f"projects/{seat}/{filename}"}
            )
    for path, label in FLEET_WIDE:
        spec.append({"seat": None, "label": label, "path": path})
    return spec


async def registry_drift(refresh: bool = False) -> dict[str, Any]:
    """Cross-check the pinned :data:`SEATS` against the live ``projects/``
    registry listing — the drift chip's data. Never raises.

    Reuses the ONE contents-API directory listing /projects already fetches
    (``github.repo_api`` on the same URL → same TTL cache entry): zero new
    network surface, never the per-package walk this page deliberately avoids.

    Returns::

        {"state": "ok" | "drift" | "unknown",
         "added": [names in the registry but not pinned, sorted],
         "missing": [pinned names no longer in the registry, sorted],
         "reason": why the check could not run (unknown only)}

    Honesty ladder: a listing that cannot be fetched (network failure, or
    the ``projects/`` directory 404ing because the registry has not landed)
    is ``unknown`` — drift can NOT be declared matched without the listing,
    so no green is ever fabricated. A listing that succeeds but holds no
    package directories is a real (empty) registry: every pinned seat is
    genuinely missing, and that renders as drift, not unknown. Retired-stub
    directories count as ``added`` on purpose — they exist upstream and are
    not pinned; the chip reports the raw set difference, never a guess.
    """
    out: dict[str, Any] = {"state": "ok", "added": [], "missing": [], "reason": ""}
    listing = await github.repo_api(
        REPO, f"/contents/{_REGISTRY_ROOT}", refresh=refresh
    )
    # Shared honesty ladder (github.classify_listing): ANY non-ok state maps
    # to "unknown" here — the chip's vocabulary stays ok/drift/unknown — but
    # the classifier's reason is kept, so a missing token now names itself.
    state, reason = github.classify_listing(
        listing,
        on_404="unknown",
        reason_404=(
            f"`{_REGISTRY_ROOT}/` does not exist upstream yet "
            "(registry not landed)"
        ),
        subject=f"the {REPO} `{_REGISTRY_ROOT}/` listing",
    )
    if state != "ok":
        out["state"] = "unknown"
        out["reason"] = reason
        return out

    registry = {
        e.get("name", "")
        for e in listing["data"]
        if e.get("type") == "dir" and e.get("name")
    }
    pinned = set(SEATS)
    out["added"] = sorted(registry - pinned)
    out["missing"] = sorted(pinned - registry)
    if out["added"] or out["missing"]:
        out["state"] = "drift"
    return out


# --------------------------------------------------------------------------- #
# Deployed-vs-canonical drift row (ORDER 022 item 3)
# --------------------------------------------------------------------------- #

# The manager's verbatim trigger-registry export — the ONE live,
# machine-readable deployed record in the fleet (failsafe family only).
SNAPSHOT_PATH = "telemetry/triggers-snapshot.json"

# Honest states, weakest-claim-first, and their badge classes (base.html).
STATE_CLASS = {
    "in sync": "ok",
    "drift": "bad",
    "stale": "warn",
    "unverified": "unknown",
    "not recorded": "unknown",
    "unreachable": "warn",
}

_DATE_RE = re.compile(r"\b20\d{2}-\d{2}-\d{2}\b")
# In-paste version line: the paste body's own first-lines "v3.5 …" stamp
# (doctrine §3: "the in-paste line is the point").
_BODY_VERSION_RE = re.compile(r"^v\d+(?:\.\d+)*\b")
_VERSION_TOKEN_RE = re.compile(r"\bv(\d+)(?:\.\d+)*\b", re.IGNORECASE)
# Deployed-record phrases that name a pre-v3 generation outright.
_PRE_V3_RE = re.compile(r"\bgen-2\b|\bv1-era\b|\bpre-v3\b", re.IGNORECASE)
# meta.md ledger heading: "## Deployed-state per part (2026-07-10)" on the
# restructure seats, "## Deployed-state per package part" on fleet-manager's.
_DEPLOYED_HEADING_RE = re.compile(r"^#{2,}\s+.*deployed-state per\b", re.IGNORECASE)
_CLAIM_HEADER_RE = re.compile(r"deploy|state", re.IGNORECASE)

# Which meta.md "Part" cell belongs to which pinned artifact family (the
# tables name parts "1 instructions" / "2 wake prompt (= coordinator prompt
# …)" / "`coordinator-prompt.md`" — matched on the Part cell only).
_META_PART_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Custom Instructions": ("instruction",),
    "coordinator prompt": ("coordinator", "wake prompt"),
}


def _clip(s: str, n: int = 220) -> str:
    """Single-line, bold-markers stripped, truncated with an ellipsis."""
    s = " ".join((s or "").replace("**", "").split())
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def _canonical_identity(a: dict[str, Any]) -> dict[str, Any]:
    """The CANONICAL side of a drift row: version identity parsed from the
    already-fetched registry artifact — the in-paste version line (e.g.
    "v3.5 <seat> CI …") and/or its ``Provenance:`` line, falling back to the
    header provenance the shared layer already extracted. Honest absence:
    no line found → empty ``line`` (the template shows the pinned path +
    "version line missing", never an invented stamp)."""
    if not a["ok"]:
        return {"ok": False, "line": "", "version": "", "date": ""}
    lines = [ln.strip() for ln in (a["text"] or "").splitlines() if ln.strip()]
    version_line = next((ln for ln in lines[:5] if _BODY_VERSION_RE.match(ln)), "")
    prov_line = next((ln for ln in lines if ln.startswith("Provenance:")), "")
    line = version_line or prov_line or a.get("provenance") or ""
    version, date = "", ""
    for src in (version_line, prov_line, a.get("provenance") or ""):
        if not version:
            m = _VERSION_TOKEN_RE.search(src)
            version = m.group(0) if m else ""
        if not date:
            m = _DATE_RE.search(src)
            date = m.group(0) if m else ""
    return {"ok": True, "line": _clip(line, 180), "version": version, "date": date}


def _parse_meta_table(text: str) -> Optional[dict[str, Any]]:
    """Best-effort parse of a meta.md "Deployed-state per part" table.

    Handles both committed shapes: the 4-column restructure-seat table
    (``| Part | This package file | Deployed today | Citation |``, date in
    the heading) and fleet-manager's 2-column ``| Part | State |``. Returns
    ``None`` when the heading or table is absent/unparseable — the caller
    renders ``not recorded``, never a guess.
    """
    lines = (text or "").splitlines()
    start, heading_date = None, ""
    for i, line in enumerate(lines):
        if _DEPLOYED_HEADING_RE.match(line.strip()):
            start = i
            m = _DATE_RE.search(line)
            heading_date = m.group(0) if m else ""
            break
    if start is None:
        return None
    header: Optional[list[str]] = None
    rows: list[list[str]] = []
    for line in lines[start + 1 :]:
        s = line.strip()
        if s.startswith("#"):
            break  # next section
        if not s.startswith("|"):
            if rows:
                break
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if all(set(c) <= set("-: ") for c in cells):
            continue  # the |---|---| separator row
        if header is None:
            header = cells
            continue
        rows.append(cells)
    if header is None or not rows:
        return None
    claim_idx = next(
        (j for j, h in enumerate(header) if j > 0 and _CLAIM_HEADER_RE.search(h)),
        min(2, len(header) - 1),
    )
    return {"date": heading_date, "claim_idx": claim_idx, "rows": rows}


def _meta_claim(parsed: dict[str, Any], keywords: tuple[str, ...]):
    """The (claim text, record date) for the part row matching ``keywords``
    on its Part cell, or ``None`` when the table has no such row."""
    for cells in parsed["rows"]:
        part = cells[0].lower()
        if any(k in part for k in keywords):
            idx = parsed["claim_idx"]
            claim = cells[idx] if idx < len(cells) else ""
            dates = _DATE_RE.findall(claim)
            return claim, (max(dates) if dates else parsed["date"])
    return None


def _meta_verdict(claim: str, record_date: str, canon: dict[str, Any]) -> str:
    """``stale`` when the record predates the canonical version/date or
    names a pre-v3 generation; otherwise ``unverified`` — meta.md prose can
    never prove byte-equality, so "in sync" is unreachable from here."""
    if canon.get("date") and record_date and record_date < canon["date"]:
        return "stale"
    if _PRE_V3_RE.search(claim):
        return "stale"
    versions = [int(m.group(1)) for m in _VERSION_TOKEN_RE.finditer(claim)]
    if versions and max(versions) < 3:
        return "stale"
    return "unverified"


def _failsafe_canonical_body(text: str) -> Optional[str]:
    """The create_trigger prompt body inside a registry failsafe copy: the
    first fenced block under its "## Prompt text" heading. ``None`` when the
    copy carries no such block (→ unverified, never a guessed compare)."""
    m = re.search(
        r"^#{2,}[^\n]*Prompt text[^\n]*\n.*?^```[^\n]*\n(.*?)^```",
        text or "",
        re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    return m.group(1) if m else None


def _norm_body(s: str) -> str:
    """Whitespace-normalized compare form: outer blank space and per-line
    trailing whitespace dropped, every content byte kept."""
    return "\n".join(ln.rstrip() for ln in (s or "").strip().splitlines())


def _squash(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def _trigger_prompt(record: dict[str, Any]) -> Optional[str]:
    """The verbatim prompt body a snapshot trigger record carries."""
    try:
        content = record["job_config"]["ccr"]["events"][0]["data"]["message"][
            "content"
        ]
        return content if isinstance(content, str) else None
    except (KeyError, IndexError, TypeError):
        return None


def _snapshot_trigger(seat: str, records: list) -> Optional[dict[str, Any]]:
    """The seat's failsafe wake trigger among the snapshot records — named
    ``"<Seat Name> failsafe wake"`` upstream; matched squashed so
    ``superbot-2.0`` finds ``SuperBot 2.0 …``. Enabled records win."""
    matches = [
        r
        for r in records
        if isinstance(r, dict)
        and "failsafe" in (r.get("name") or "").lower()
        and _squash(seat) in _squash(r.get("name") or "")
    ]
    enabled = [r for r in matches if r.get("enabled")]
    return (enabled or matches or [None])[0]


def _deployed_version(text: str) -> str:
    """The first version token a deployed record names (e.g. the ``v1-era``
    prompt a meta.md row cites) — ``""`` when the record carries none
    (failsafe bodies are deliberately unstamped; honest absence, never a
    guessed version)."""
    m = _VERSION_TOKEN_RE.search(text or "")
    return m.group(0) if m else ""


def _version_line(row: dict[str, Any]) -> str:
    """The row's version-aware summary (ORDER 041): "deployed v3.4 ·
    canonical v3.6". Rendered only when a deployed record EXISTS; a side
    whose version cannot be parsed says ``unstamped`` — a version label is
    never invented. The canonical side is the version parsed from the HEAD
    registry copy (the newest canonical label)."""
    if not row["deployed"]:
        return ""
    cv, dv = row["canonical_version"], row["deployed_version"]
    deployed = f"deployed {dv}" if dv else "deployed unstamped"
    canonical = f"canonical {cv}" if cv else "canonical unstamped"
    return f"{deployed} · {canonical}"


def _row(
    seat: Optional[str], a: dict[str, Any], canon: dict[str, Any]
) -> dict[str, Any]:
    """A drift-row skeleton (state filled in by the caller)."""
    return {
        "seat": seat,
        "label": a["label"],
        "path": a["path"],
        "canonical": canon["line"],
        "canonical_ok": canon["ok"],
        "canonical_version": canon.get("version", ""),
        "deployed_version": "",
        "version_line": "",
        "deployed": "",
        "as_of": "",
        "source": "",
        "state": "not recorded",
        "cls": STATE_CLASS["not recorded"],
        "reason": "",
    }


def _finish(row: dict[str, Any], state: str, reason: str = "") -> dict[str, Any]:
    row["state"] = state
    row["cls"] = STATE_CLASS[state]
    row["reason"] = reason
    return row


def _build_deployed(
    artifacts: list[dict[str, Any]],
    metas: dict[str, dict[str, Any]],
    snap_res: dict[str, Any],
    seats: tuple[str, ...] = SEATS,
) -> dict[str, Any]:
    """Assemble the per-artifact drift rows from already-fetched results
    (pure). ``seats`` defaults to the full roster; :func:`seat_drift` passes
    a single seat to reuse the exact same row model for one seat's strip."""
    by_key = {(a["seat"], a["label"]): a for a in artifacts}

    # Snapshot: parsed once, looked up per seat. 404 = never committed
    # (not recorded); network/5xx = unreachable; bad JSON = an honest
    # degenerate record, never a verdict.
    snapshot: dict[str, Any] = {
        "ok": False,
        "captured_at": "",
        "error": "",
        "path": SNAPSHOT_PATH,
        "url": prompt_artifacts.blob_url(SNAPSHOT_PATH),
    }
    records: list = []
    snap_unreachable = False
    if snap_res["ok"] and isinstance(snap_res["data"], str):
        try:
            parsed = json.loads(snap_res["data"])
            records = parsed.get("data") or []
            snapshot["ok"] = True
            snapshot["captured_at"] = parsed.get("captured_at", "")
        except (ValueError, AttributeError):
            snapshot["error"] = "snapshot is not valid JSON"
    elif snap_res.get("status") == 404:
        snapshot["error"] = "no snapshot committed upstream (404)"
    else:
        snapshot["error"] = snap_res.get("error") or f"HTTP {snap_res.get('status')}"
        snap_unreachable = True

    seats_out: list[dict[str, Any]] = []
    for seat in seats:
        rows: list[dict[str, Any]] = []

        # meta.md once per seat — 404 = no ledger (not recorded);
        # network failure = unreachable; present = best-effort table parse.
        meta_res = metas[seat]
        meta_parsed = None
        meta_unreachable = False
        meta_note = ""
        if meta_res["ok"] and isinstance(meta_res["data"], str):
            meta_parsed = _parse_meta_table(meta_res["data"])
            if meta_parsed is None:
                meta_note = "meta.md has no parseable Deployed-state table"
        elif meta_res.get("status") == 404:
            meta_note = "no meta.md in the registry package"
        else:
            meta_unreachable = True
            meta_note = meta_res.get("error") or f"HTTP {meta_res.get('status')}"

        for filename, label in SEAT_FILES:
            a = by_key[(seat, label)]
            canon = _canonical_identity(a)
            row = _row(seat, a, canon)

            if label == "failsafe prompt":
                row["source"] = SNAPSHOT_PATH
                if snap_unreachable:
                    _finish(row, "unreachable", snapshot["error"])
                elif not snapshot["ok"]:
                    _finish(row, "not recorded", snapshot["error"])
                else:
                    rec = _snapshot_trigger(seat, records)
                    prompt = _trigger_prompt(rec) if rec else None
                    if rec is None:
                        _finish(
                            row,
                            "not recorded",
                            "no failsafe trigger for this seat in the snapshot",
                        )
                    elif prompt is None:
                        _finish(
                            row,
                            "not recorded",
                            "snapshot record carries no prompt body",
                        )
                    else:
                        row["as_of"] = snapshot["captured_at"]
                        row["deployed_version"] = _deployed_version(prompt)
                        row["deployed"] = _clip(
                            f"{rec.get('name', '')} · cron "
                            f"{rec.get('cron_expression', '?')} · "
                            f"{'enabled' if rec.get('enabled') else 'DISABLED'} · "
                            f"{rec.get('id', '')}"
                        )
                        if not canon["ok"]:
                            _finish(
                                row,
                                "unverified",
                                "canonical registry copy could not be fetched "
                                "— nothing to compare against",
                            )
                        else:
                            body = _failsafe_canonical_body(a["text"] or "")
                            if body is None:
                                _finish(
                                    row,
                                    "unverified",
                                    "no Prompt-text block found in the "
                                    "registry copy",
                                )
                            elif _norm_body(prompt) == _norm_body(body):
                                _finish(
                                    row,
                                    "in sync",
                                    "snapshot prompt body byte-matches the "
                                    "registry copy",
                                )
                            else:
                                _finish(
                                    row,
                                    "drift",
                                    "snapshot prompt body differs from the "
                                    "registry copy",
                                )
            else:
                row["source"] = f"projects/{seat}/meta.md"
                if meta_unreachable:
                    _finish(row, "unreachable", meta_note)
                elif meta_parsed is None:
                    _finish(row, "not recorded", meta_note)
                else:
                    hit = _meta_claim(meta_parsed, _META_PART_KEYWORDS[label])
                    if hit is None:
                        _finish(
                            row,
                            "not recorded",
                            "no row for this part in the Deployed-state table",
                        )
                    else:
                        claim, record_date = hit
                        row["deployed"] = "recorded: " + _clip(claim)
                        row["deployed_version"] = _deployed_version(claim)
                        row["as_of"] = record_date
                        verdict = _meta_verdict(claim, record_date, canon)
                        _finish(
                            row,
                            verdict,
                            "meta.md prose cannot prove byte-equality"
                            + (
                                " — record predates the canonical copy"
                                if verdict == "stale"
                                else ""
                            ),
                        )
            row["version_line"] = _version_line(row)
            rows.append(row)
        seats_out.append({"name": seat, "rows": rows})

    universals = []
    for a in artifacts:
        if a["seat"] is None:
            row = _row(None, a, _canonical_identity(a))
            _finish(
                row,
                "not recorded",
                "pasted per session — no deployed record exists anywhere "
                "in the fleet",
            )
            universals.append(row)

    all_rows = [r for s in seats_out for r in s["rows"]] + universals
    counts = {state: 0 for state in STATE_CLASS}
    for r in all_rows:
        counts[r["state"]] += 1
    chips = [
        {"state": state, "count": counts[state], "cls": STATE_CLASS[state]}
        for state in STATE_CLASS
        if counts[state]
    ]
    return {
        "seats": seats_out,
        "universals": universals,
        "snapshot": snapshot,
        "counts": counts,
        "chips": chips,
        "total": len(all_rows),
    }


async def deployed_drift(
    artifacts: list[dict[str, Any]], refresh: bool = False
) -> dict[str, Any]:
    """The deployed-vs-canonical drift rows (ORDER 022 item 3). Never raises.

    CANONICAL comes from ``artifacts`` — the registry copies
    :func:`overview` already fetched (zero extra canonical fetches).
    DEPLOYED comes from the fleet's only committed deployment records, both
    on fleet-manager main over the same TTL-cached raw-content pattern:
    ``projects/<seat>/meta.md`` (prose ledger → ``recorded`` + stale/
    unverified, never "in sync") and ``telemetry/triggers-snapshot.json``
    (verbatim trigger export → byte-comparable ``in sync``/``drift`` for the
    failsafe family only; ONE fetch, per-seat lookup). Universals are
    ``not recorded`` by design (per-session pastes, no record exists).
    Failed fetches degrade per-row to ``unreachable`` — never a 500, never
    an invented verdict.
    """
    fetches = [
        github.fetch_file(REPO, f"projects/{seat}/meta.md", refresh=refresh)
        for seat in SEATS
    ]
    fetches.append(github.fetch_file(REPO, SNAPSHOT_PATH, refresh=refresh))
    *meta_res, snap_res = await asyncio.gather(*fetches)
    return _build_deployed(artifacts, dict(zip(SEATS, meta_res)), snap_res)


# --------------------------------------------------------------------------- #
# ORDER 041 remainder — the drift rows reduced for the other surfaces
# (the dispatch screen's strip + the owner console's per-seat rows).
# Views over the ONE source the /prompts table already renders: same
# canonical registry copies, same two committed deployment records, same
# row model (:func:`_build_deployed`) — no second fetch path, no copies.
# --------------------------------------------------------------------------- #

# Attention order for a seat's worst state: byte-proven drift first, then
# provably stale prose, then the couldn't-check states, "in sync" last.
_SEVERITY: tuple[str, ...] = (
    "drift", "stale", "unreachable", "unverified", "not recorded", "in sync",
)


def _worst_state(rows: list[dict[str, Any]]) -> str:
    return next(
        (s for s in _SEVERITY if any(r["state"] == s for r in rows)),
        "not recorded",
    )


async def seat_drift(seat: str, refresh: bool = False) -> Optional[dict[str, Any]]:
    """ONE seat's deployed-vs-canonical rows — the exact row model the
    /prompts drift table renders (:func:`_build_deployed`), fetched for a
    single seat: its 3 registry artifacts + its meta.md + the trigger
    snapshot, all over the same TTL-cached client (URLs identical to the
    /prompts fetches → shared cache entries; zero new fetch semantics).

    ``None`` for a non-roster seat. Never raises; every upstream failure
    degrades inside its row (unreachable / not recorded), equality is never
    invented.
    """
    if seat not in SEATS:
        return None
    *artifacts, meta_res, snap_res = await asyncio.gather(
        *[
            prompt_artifacts.fetch_artifact(
                f"projects/{seat}/{filename}", label, seat=seat, refresh=refresh
            )
            for filename, label in SEAT_FILES
        ],
        github.fetch_file(REPO, f"projects/{seat}/meta.md", refresh=refresh),
        github.fetch_file(REPO, SNAPSHOT_PATH, refresh=refresh),
    )
    built = _build_deployed(
        list(artifacts), {seat: meta_res}, snap_res, seats=(seat,)
    )
    rows = built["seats"][0]["rows"]
    return {
        "seat": seat,
        "rows": rows,
        "snapshot": built["snapshot"],
        "worst": _worst_state(rows),
        "worst_cls": STATE_CLASS[_worst_state(rows)],
        "stale": sum(1 for r in rows if r["state"] in ("stale", "drift")),
    }


async def console_rollup(refresh: bool = False) -> dict[str, Any]:
    """The owner console's per-seat prompt-state rows (ORDER 041 remainder):
    every roster seat reduced to one row — deployed vs canonical (the
    Custom-Instructions version line), stale count across the seat's 3
    artifacts, worst state, and the /prompts/history deep link.

    Pure reduction over :func:`deployed_drift` — the same canonical
    registry copies and committed deployment records the /prompts table
    renders (identical URLs → shared TTL cache), no new fetch path, no
    prompt copy stored. Never raises; failures degrade per row exactly as
    they do on /prompts.
    """
    spec = [s for s in _artifact_spec() if s["seat"] is not None]
    artifacts = list(
        await asyncio.gather(
            *[
                prompt_artifacts.fetch_artifact(
                    s["path"], s["label"], seat=s["seat"], refresh=refresh
                )
                for s in spec
            ]
        )
    )
    built = await deployed_drift(artifacts, refresh=refresh)
    rows: list[dict[str, Any]] = []
    for s in built["seats"]:
        seat_rows = s["rows"]
        ci = next(
            (r for r in seat_rows if r["label"] == "Custom Instructions"), None
        )
        worst = _worst_state(seat_rows)
        rows.append(
            {
                "seat": s["name"],
                "version_line": ci["version_line"] if ci else "",
                "note": (ci["reason"] if ci else "") or "no deployed record",
                "stale": sum(
                    1 for r in seat_rows if r["state"] in ("stale", "drift")
                ),
                "total": len(seat_rows),
                "state": worst,
                "cls": STATE_CLASS[worst],
                "states": [
                    {"label": r["label"], "state": r["state"], "cls": r["cls"]}
                    for r in seat_rows
                ],
                "history_url": f"/prompts/history/{s['name']}",
            }
        )
    return {
        "rows": rows,
        "snapshot": built["snapshot"],
        "counts": built["counts"],
        "stale_total": sum(r["stale"] for r in rows),
    }


async def overview(refresh: bool = False) -> dict[str, Any]:
    """Every fleet paste artifact, fetched live (TTL-cached) — never raises
    for upstream failures; the route always renders 200.

    Returns::

        {
          "seats": [{"name", "anchor", "github_url", "artifacts": [...]}, ...],
          "fleet_wide": [ artifact, ... ],
          "total", "ok_count", "error_count",
          "drift": registry_drift() result (pinned-vs-registry chip),
          "deployed": deployed_drift() result (deployed-vs-canonical rows),
          "ttl": CACHE_TTL_SECONDS, "repo_url",
        }

    Each artifact dict is the canonical shared model
    (:func:`app.prompt_artifacts.build_artifact`) plus a page-local
    ``anchor``. ``text`` is the clean paste body — the upstream file with
    its generation metadata stripped by
    :func:`app.prompt_artifacts.extract_paste_body`, body otherwise
    byte-exact; on failure ``text`` is ``None`` and
    ``error`` says why — content is never fabricated and stale-cache
    serving is the ``github`` layer's TTL behaviour, surfaced via
    ``cached``/``fetched_at``.
    """
    spec = _artifact_spec()
    *artifacts, drift = await asyncio.gather(
        *[
            prompt_artifacts.fetch_artifact(
                s["path"], s["label"], seat=s["seat"], refresh=refresh
            )
            for s in spec
        ],
        registry_drift(refresh=refresh),
    )
    for i, a in enumerate(artifacts):
        a["anchor"] = f"artifact-{i}"

    # Deployed-vs-canonical rows: canonical side reuses the artifacts just
    # fetched; the deployed-record fetches (per-seat meta.md + the snapshot)
    # run concurrently inside, all TTL-cached.
    deployed = await deployed_drift(artifacts, refresh=refresh)

    seats = [
        {
            "name": seat,
            "anchor": f"seat-{seat}",
            "github_url": (
                f"https://github.com/{config.OWNER}/{REPO}/tree/{REF}/projects/{seat}"
            ),
            "artifacts": [a for a in artifacts if a["seat"] == seat],
        }
        for seat in SEATS
    ]
    fleet_wide = [a for a in artifacts if a["seat"] is None]
    ok_count = sum(1 for a in artifacts if a["ok"])
    return {
        "seats": seats,
        "fleet_wide": fleet_wide,
        "total": len(artifacts),
        "ok_count": ok_count,
        "error_count": len(artifacts) - ok_count,
        # Artifacts whose OWN raw header carries a supersession/do-not-paste
        # marker (shared detection: prompt_artifacts.extract_supersession) —
        # each is banner-flagged on its card; 0 renders no chip (no noise).
        "superseded_count": sum(1 for a in artifacts if a["superseded"]),
        "drift": drift,
        "deployed": deployed,
        "ttl": config.CACHE_TTL_SECONDS,
        "repo_url": f"https://github.com/{config.OWNER}/{REPO}/tree/{REF}",
    }
