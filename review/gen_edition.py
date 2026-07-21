"""Edition auto-drafter for the review service — draft the next dated review
edition from the committed data mirrors, deterministically.

The review site is a CONTINUOUS review channel: each edition is one committed
markdown file under ``data/reviews/`` (the ritual + template live in
``review/README.md``). Edition 1 was hand-authored; this generator drafts every
subsequent edition from the already-baked, committed mirrors under
``review/data/*.json`` so the channel stays alive with zero owner action and —
like every other surface here — cannot invent data even in principle. Every
sentence it emits is DERIVED from a committed mirror and cites the file it came
from; a datum absent from the mirrors is simply absent from the edition
(fail-soft per mirror).

Run from the repo root (any session, any time an edition should publish):

    python3 review/gen_edition.py                      # next number, today (UTC)
    python3 review/gen_edition.py --date 2026-07-21 --number 2

The output front-matter + section structure is EXACTLY what
``review.editions.parse_edition`` requires (round-tripped in the tests), so the
index, the per-edition page, and the Atom feed pick it up with zero code
changes. Deterministic: identical ``(date, number, mirrors)`` inputs produce
byte-identical output — no wall clock enters the rendered file (the date is an
argument, never ``now()``), so the generator is idempotent.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any, Optional

# Run as a plain script (``python3 review/gen_edition.py``) — put the repo root
# on the path so ``from review import editions`` resolves (the pattern
# review/tests/test_clarity_structure.py already uses).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from review import editions  # noqa: E402

REPO_URL = "https://github.com/menno420/websites"
DATA_DIR = Path(__file__).resolve().parent / "data"
REVIEWS_DIR = DATA_DIR / "reviews"

# The committed mirrors this drafter reads, in the order the README lists them.
MIRRORS = ("stats", "fleet", "releases", "snapshot", "questions")

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #
def _blob(name: str) -> str:
    """GitHub blob URL for a committed mirror — the citation for every datum."""
    return f"{REPO_URL}/blob/main/review/data/{name}.json"


def _i(n: Any) -> str:
    """Thousands-separated integer, or the raw value if it isn't one."""
    try:
        return f"{int(n):,}"
    except (TypeError, ValueError):
        return str(n)


def load_mirror(data_dir: Path, name: str) -> Optional[dict[str, Any]]:
    """One mirror JSON → dict, or ``None`` if missing/unreadable/malformed.

    Fail-soft by design: an absent mirror drops its section rather than
    crashing the draft (the site itself banners a missing mirror; the edition
    simply omits what it cannot cite)."""
    try:
        data = json.loads((data_dir / f"{name}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def load_mirrors(data_dir: Path = DATA_DIR) -> dict[str, Optional[dict[str, Any]]]:
    """All known mirrors, each loaded fail-soft."""
    return {name: load_mirror(data_dir, name) for name in MIRRORS}


# --------------------------------------------------------------------------- #
# Derived facts — pure functions over one mirror each, all guarded
# --------------------------------------------------------------------------- #
def _stats_facts(stats: Optional[dict[str, Any]]) -> Optional[dict[str, int]]:
    if not stats:
        return None
    repos = stats.get("repos", {})
    if not isinstance(repos, dict) or not repos:
        return None
    ok = {k: v for k, v in repos.items() if isinstance(v, dict) and v.get("ok")}
    return {
        "repos_total": len(repos),
        "repos_ok": len(ok),
        "total_prs": sum(int(v.get("total_prs", 0) or 0) for v in ok.values()),
        "open_count": sum(int(v.get("open_issues_and_prs", 0) or 0) for v in ok.values()),
        "repos_bad": len(repos) - len(ok),
    }


def _fleet_facts(fleet: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    if not fleet:
        return None
    reg = fleet.get("registry", {}) if isinstance(fleet.get("registry"), dict) else {}
    seats = fleet.get("seats", []) if isinstance(fleet.get("seats"), list) else []
    repos = [r for s in seats for r in s.get("repos", []) if isinstance(r, dict)]
    return {
        "total_seats": reg.get("total_seats", "?"),
        "repo_seats": reg.get("repo_seats", "?"),
        "standing_seats": len(seats),
        "hb_total": len(repos),
        "hb_avail": sum(1 for r in repos if r.get("heartbeat_available")),
    }


def _releases_facts(rel: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    if not rel:
        return None
    entries = rel.get("entries", []) if isinstance(rel.get("entries"), list) else []
    return {
        "checked": len(entries),
        "drift_count": int(rel.get("drift_count", 0) or 0),
        "drifted": [e.get("name") or e.get("slug") for e in entries if e.get("drift")],
    }


def _snapshot_facts(snap: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    if not snap:
        return None
    totals = snap.get("totals", {}) if isinstance(snap.get("totals"), dict) else {}
    days = snap.get("days", []) if isinstance(snap.get("days"), list) else []
    tf = [d.get("test_functions_eod") for d in days
          if isinstance(d.get("test_functions_eod"), int)]
    return {
        "generated_at": snap.get("generated_at", ""),
        "git_head": str(snap.get("git_head", ""))[:8],
        "prs_merged": totals.get("prs_merged", 0),
        "commits": totals.get("commits", 0),
        "test_functions": totals.get("test_functions", 0),
        "services": totals.get("services", "?"),
        "days": len(days),
        "tf_first": tf[0] if tf else None,
        "tf_last": tf[-1] if tf else None,
    }


def _questions_count(q: Optional[dict[str, Any]]) -> Optional[int]:
    if not q:
        return None
    qs = q.get("questions", [])
    return len(qs) if isinstance(qs, list) else 0


# --------------------------------------------------------------------------- #
# Rendering — mirrors → one edition markdown string
# --------------------------------------------------------------------------- #
def render_edition(
    number: int,
    date: str,
    mirrors: dict[str, Optional[dict[str, Any]]],
) -> str:
    """Draft one edition markdown (front-matter + body) from the mirrors.

    Pure: no wall clock, no IO — same inputs give byte-identical output."""
    s = _stats_facts(mirrors.get("stats"))
    f = _fleet_facts(mirrors.get("fleet"))
    r = _releases_facts(mirrors.get("releases"))
    snap = _snapshot_facts(mirrors.get("snapshot"))
    q_count = _questions_count(mirrors.get("questions"))

    # "as of" prefers the snapshot's own bake date so the headline is honest
    # about which record it summarises; falls back to the edition date.
    as_of = (snap["generated_at"][:10] if snap and snap.get("generated_at") else date) or date

    # --- summary (single line — the index + Atom feed lede) ----------------- #
    parts: list[str] = []
    if s:
        parts.append(f"{s['repos_ok']} repositories")
        parts.append(f"{_i(s['total_prs'])} pull requests opened all-time")
    if snap:
        parts.append(f"a test suite at {_i(snap['test_functions'])} functions")
    if f:
        parts.append(f"{f['total_seats']} fleet seats")
    if r:
        parts.append(f"{r['drift_count']} release drift")
    if q_count is not None:
        parts.append(f"{q_count} reviewer questions on the ledger")
    summary = (
        "A data-derived edition, drafted by review/gen_edition.py from the "
        "committed mirrors as of " + as_of
        + (": " + ", ".join(parts) + "." if parts else ".")
    )

    title = f"Edition {number} — the fleet by its own committed numbers, as of {as_of}"

    # --- body --------------------------------------------------------------- #
    lines: list[str] = []

    lines += ["## Why this edition exists", ""]
    lines += [
        "This is a **data-derived** edition: unlike the hand-authored "
        f"[edition 1](/reviews/2026-07-11-edition-001), it is drafted by "
        f"[`review/gen_edition.py`]({REPO_URL}/blob/main/review/gen_edition.py) "
        "purely from the committed data mirrors under "
        f"[`review/data/`]({REPO_URL}/tree/main/review/data) that the daily "
        "`review-bake` already produces. Every figure below cites the mirror it "
        "comes from; nothing here is estimated, and a number the mirrors do not "
        "hold is simply absent.",
        "",
    ]

    # The window in one line — snapshot totals
    if snap:
        lines += ["## The window in one line", ""]
        lines += [
            f"The committed snapshot mirror (generated {snap['generated_at']}, "
            f"git HEAD `{snap['git_head']}`) records **{_i(snap['prs_merged'])} "
            f"merged PRs** and {_i(snap['commits'])} commits across "
            f"{snap['days']} tracked days in this repository, with the test "
            f"suite standing at **{_i(snap['test_functions'])} functions** over "
            f"{snap['services']} services "
            f"([snapshot.json]({_blob('snapshot')}), rendered at [/growth](/growth)).",
            "",
        ]

    # What the committed mirrors record — one bullet per available mirror
    bullets: list[str] = []
    if f:
        bullets.append(
            f"- **Fleet:** {f['total_seats']} seats in the fleet-manager "
            f"registry ({f['repo_seats']} repo-backed), organised into "
            f"{f['standing_seats']} standing seats; {f['hb_avail']}/{f['hb_total']} "
            "repo-backed lanes carry a live heartbeat in the mirror "
            f"([fleet.json]({_blob('fleet')}), rendered at [/fleet](/fleet))."
        )
    if s:
        bullets.append(
            f"- **Repositories:** the stats bake reached {s['repos_ok']} of "
            f"{s['repos_total']} repositories; {_i(s['total_prs'])} pull "
            "requests have been opened across them all-time, with "
            f"{_i(s['open_count'])} issues and PRs open right now "
            f"([stats.json]({_blob('stats')}))."
        )
    if snap and snap.get("tf_first") is not None and snap.get("tf_last") is not None:
        bullets.append(
            "- **Safety net:** the committed daily history shows the test suite "
            f"growing from {_i(snap['tf_first'])} to {_i(snap['tf_last'])} "
            "functions across the tracked window "
            f"([snapshot.json]({_blob('snapshot')}), rendered at [/growth](/growth))."
        )
    if r:
        bullets.append(
            f"- **Release drift:** {r['checked']} arcade titles are checked for "
            f"release-tag drift; the current drift count is {r['drift_count']} "
            f"([releases.json]({_blob('releases')}))."
        )
    if bullets:
        lines += ["## What the committed mirrors record", ""]
        lines += bullets
        lines += [""]

    # What went wrong — honest, from the mirrors
    lines += ["## What went wrong (from the mirrors)", ""]
    faults: list[str] = []
    if s and s["repos_bad"]:
        faults.append(
            f"the stats bake could not reach {s['repos_bad']} repository/ies "
            f"([stats.json]({_blob('stats')}) carries the exact per-repo reason)"
        )
    if r and r["drifted"]:
        named = ", ".join(str(n) for n in r["drifted"])
        faults.append(
            f"release-tag drift is recorded for {named} "
            f"([releases.json]({_blob('releases')}))"
        )
    if faults:
        lines += [
            "The mirrors record the following in this bake: " + "; ".join(faults) + ".",
            "",
        ]
    else:
        drift_txt = f"{r['drift_count']}" if r else "not recorded"
        lines += [
            "Every repository the stats bake reached returned `ok`"
            + (f", and the release-drift count is {drift_txt}" if r else "")
            + " — the committed mirrors record no repository fault or release "
            "drift in this bake. That is a health snapshot, not an incident log: "
            "the narrative account of what has broken in this program, with "
            "per-incident citations, lives in "
            "[edition 1](/reviews/2026-07-11-edition-001) and on the "
            "[/problems](/problems) page.",
            "",
        ]

    # Reviewer questions
    if q_count is not None:
        lines += ["## Reviewer questions", ""]
        if q_count == 0:
            lines += [
                "No external reviewer questions are on the ledger yet "
                f"([questions.json]({_blob('questions')})). The intake "
                "convention — a question opened as a GitHub issue, routed by the "
                "fleet manager as an order, then answered in a future edition and "
                "recorded with links to both — is documented at "
                "[/questions](/questions).",
                "",
            ]
        else:
            lines += [
                f"{q_count} reviewer question(s) are on the ledger; each answered "
                "entry links its question issue and the edition that answered it "
                f"([questions.json]({_blob('questions')}), rendered at "
                "[/questions](/questions)).",
                "",
            ]

    # Only the owner can do these — honest pointer (the queue isn't a mirror)
    lines += ["## Only the owner can do these (open at press time)", ""]
    lines += [
        "This edition is derived only from the committed data mirrors, which do "
        "not encode the owner-action queue; the canonical, click-level list of "
        "what only the owner can do lives in "
        f"[docs/owner/OWNER-ACTIONS.md]({REPO_URL}/blob/main/docs/owner/OWNER-ACTIONS.md).",
        "",
    ]

    # Next edition
    lines += ["## Next edition", ""]
    lines += [
        "This edition was drafted mechanically by "
        f"[`review/gen_edition.py`]({REPO_URL}/blob/main/review/gen_edition.py) "
        "from the committed mirrors, so a fresh edition can publish whenever the "
        "mirrors are re-baked — the continuous channel no longer needs a "
        "hand-authored draft to stay alive. The publishing ritual and template "
        f"remain in [review/README.md]({REPO_URL}/blob/main/review/README.md).",
        "",
    ]

    body = "\n".join(lines).rstrip() + "\n"
    header = f"title: {title}\ndate: {date}\nsummary: {summary}"
    return f"---\n{header}\n---\n{body}"


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def slug_for(date: str, number: int) -> str:
    return f"{date}-edition-{number:03d}"


def next_number(reviews_dir: Path = REVIEWS_DIR) -> int:
    """One past the count of existing well-formed editions."""
    return len(editions.list_editions(reviews_dir)) + 1


def _parse_args(argv: Optional[list[str]]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--date", default=None,
        help="edition date YYYY-MM-DD (default: today, UTC)",
    )
    p.add_argument(
        "--number", type=int, default=None,
        help="edition number (default: count of existing editions + 1)",
    )
    p.add_argument(
        "--data-dir", type=Path, default=DATA_DIR,
        help="directory holding the committed mirror JSON files",
    )
    p.add_argument(
        "--reviews-dir", type=Path, default=REVIEWS_DIR,
        help="directory the edition markdown is written to",
    )
    p.add_argument(
        "--out", type=Path, default=None,
        help="explicit output path (default: <reviews-dir>/<slug>.md)",
    )
    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)

    date = args.date or dt.datetime.now(dt.timezone.utc).date().isoformat()
    if not _DATE_RE.match(date):
        print(f"error: --date must be YYYY-MM-DD, got {date!r}", file=sys.stderr)
        return 2

    number = args.number if args.number is not None else next_number(args.reviews_dir)

    mirrors = load_mirrors(args.data_dir)
    text = render_edition(number, date, mirrors)

    out = args.out or (args.reviews_dir / f"{slug_for(date, number)}.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")

    present = [n for n in MIRRORS if mirrors.get(n) is not None]
    try:
        shown = out.relative_to(Path(__file__).resolve().parents[1])
    except ValueError:
        shown = out
    print(f"wrote {shown} (edition {number}, {date}, mirrors: {', '.join(present) or 'none'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
