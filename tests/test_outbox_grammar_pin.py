"""Outbox REPORT grammar drift pin — parse the committed outbox at HEAD.

The /owner/briefing REPORTS card (PR #286) renders the newest ``## REPORT``
entry of ``control/outbox.md`` via ``briefing.latest_report``. The card and
the coordinator's hand-written outbox entries share a grammar
(``## REPORT · <ISO8601> · <from → to> · <TITLE>``) enforced by nothing —
one heading typo silently demotes the newest night report to the card's
honest-empty state. This pin feeds the repo's own committed outbox (read
from disk, ZERO network) through the exact parser the card uses and fails
when the real file drifts out of the grammar:

* a REPORT-like level-2 heading the parser skips (malformed grammar, or a
  typo the parser doesn't even recognize as a report heading), or
* zero reports parsed while ``## REPORT``-looking text exists in the file.

Plus one small synthetic case proving the pin itself detects a drifted
heading (keeps the REPORT-like regex and the parser aligned).

Backlog source: docs/ideas/backlog.md "Outbox REPORT grammar drift pin"
(from `.sessions/2026-07-13-briefing-outbox.md` 💡).
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import briefing  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTBOX_PATH = REPO_ROOT / "control" / "outbox.md"

# A level-2 heading that LOOKS like it wants to be a REPORT entry: "REPORT"
# in the label position, case-insensitive, tolerant of a missing/extra space
# after "##". Deliberately broader than the parser's own
# ``startswith("## REPORT")`` so label typos (``## Report``, ``##REPORT``,
# ``##  REPORT``) surface as drift instead of vanishing silently. Label
# position only — a PROPOSAL whose *title* mentions a report must not count.
REPORT_LIKE = re.compile(r"^##(?!#)\s*REPORT\b", re.IGNORECASE)

DRIFT_HINT = (
    "Grammar drift between control/outbox.md and the briefing parser. "
    "Either the outbox entry's heading has a typo (fix the heading in "
    "control/outbox.md — grammar: '## REPORT · <ISO8601> · <from → to> · "
    "<TITLE>', see control/outbox.md's own entries) or the briefing "
    "grammar changed (app/briefing.py latest_report — then update the "
    "outbox entries and this pin's REPORT_LIKE regex together)."
)


def _report_like_headings(text: str) -> list[str]:
    return [ln for ln in text.splitlines() if REPORT_LIKE.match(ln)]


# --------------------------------------------------------------------------- #
# The pin — the committed file at HEAD parses clean
# --------------------------------------------------------------------------- #
def test_committed_outbox_exists_and_is_nonempty():
    assert OUTBOX_PATH.is_file(), (
        f"{OUTBOX_PATH} is missing — the briefing REPORTS card reads this "
        "committed file; if it moved, update app/briefing.py OUTBOX_PATH "
        "and this pin together."
    )
    assert OUTBOX_PATH.read_text(encoding="utf-8").strip(), (
        f"{OUTBOX_PATH} is empty — an empty outbox renders the REPORTS "
        "card honest-empty; if that is intended, adjust this pin."
    )


def test_no_report_like_heading_is_skipped_by_the_parser():
    text = OUTBOX_PATH.read_text(encoding="utf-8")
    headings = _report_like_headings(text)
    r = briefing.latest_report(text)
    # (a1) headings the parser RECOGNIZED as reports but rejected on grammar
    # (missing ·-fields, missing →) are counted honestly in the note.
    assert r["note"] == "", (
        f"{r['note']} — a '## REPORT' heading in control/outbox.md is out "
        f"of the entry grammar. {DRIFT_HINT}"
    )
    # (a2) headings the parser did not even recognize (label typos) show up
    # as a count mismatch: every REPORT-like heading must be parsed.
    assert r["total_reports"] == len(headings), (
        f"{len(headings)} REPORT-like heading(s) in control/outbox.md but "
        f"the briefing parser accepted {r['total_reports']}: "
        f"{headings!r}. {DRIFT_HINT}"
    )


def test_report_text_present_means_a_report_renders():
    text = OUTBOX_PATH.read_text(encoding="utf-8")
    if not _report_like_headings(text):
        return  # nothing REPORT-like — honest-empty is the correct render
    r = briefing.latest_report(text)
    assert r["found"] is True and r["title"] and r["issued"], (
        "control/outbox.md contains '## REPORT' text but the briefing "
        "parser found zero reports — the newest night report would render "
        f"as honest-empty on /owner/briefing. {DRIFT_HINT}"
    )


# --------------------------------------------------------------------------- #
# The pin's own teeth — a drifted heading IS detected (regex ↔ parser
# alignment, synthetic)
# --------------------------------------------------------------------------- #
def test_pin_detects_a_malformed_report_heading():
    # Grammar typo (missing · separators): parser counts it skipped.
    bad = "## REPORT 2026-07-13T05:48Z websites → manager MISSING DOTS\nbody.\n"
    assert len(_report_like_headings(bad)) == 1
    r = briefing.latest_report(bad)
    assert r["total_reports"] == 0 and "skipped" in r["note"]


def test_pin_detects_a_label_typo_the_parser_cannot_see():
    # Case typo: the parser neither parses nor counts it — only the
    # REPORT-like count mismatch catches this class.
    typo = "## Report · 2026-07-13T05:48Z · websites → manager · CASE TYPO\nbody.\n"
    assert len(_report_like_headings(typo)) == 1
    r = briefing.latest_report(typo)
    assert r["total_reports"] == 0 and r["note"] == ""
    # ...and a PROPOSAL merely MENTIONING a report is not REPORT-like.
    proposal = (
        "## PROPOSAL · 2026-07-13T11:29Z · websites → manager · "
        "NIGHT REPORT FORMAT NOTE\nbody.\n"
    )
    assert _report_like_headings(proposal) == []
