"""SQLite storage for the tester program (claims / submissions / payout ledger).

⚠️ LOUD FLAG — EPHEMERAL STORAGE (stated on the owner queue and in the PR):
this repo has NO database. ``DATABASE_URL``/Postgres is an existing OPEN owner
ask (`docs/owner/OWNER-ACTIONS.md` — the botsite submissions-Postgres ask).
Until it lands, this module keeps the tester program's state in a stdlib
``sqlite3`` file on the service's local disk — and **Railway's disk is
ephemeral: every redeploy wipes it**. Mitigations shipped with this module:

- the owner queue shows a permanent warning banner,
- ``GET /testing/owner/export.json`` (owner-auth) dumps the full DB as JSON —
  the backup valve to pull before any redeploy.

Auto-switching to Postgres is deliberately DEFERRED: no ``DATABASE_URL``
exists to test against, so a speculative dual backend would ship unverified.
The functions below are plain and small so the Postgres port is mechanical.

Layering: this is the domain/data layer for ``botsite/testing.py`` (routes).
It imports nothing from routes or templates and holds no secret. The DB path
is the one env knob: ``TESTING_DB_PATH`` (default ``botsite/testing.sqlite3``,
gitignored).
"""

from __future__ import annotations

import base64
import json
import os
import sqlite3
import time
from contextlib import closing
from pathlib import Path
from typing import Any, Optional

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR / "testing.sqlite3"

# Claim lifecycle: claimed → submitted → (AI exit-review done) reviewed →
# approved | rejected; approved → paid. A submission whose AI review is
# degraded/unavailable stays 'submitted' (the owner reviews it manually).
# A rejected claim frees its task slot (active = everything except rejected).
CLAIM_STATUSES = ("claimed", "submitted", "reviewed", "approved", "rejected", "paid")
# AI exit-review lifecycle (one review row per submission):
#   pending-followup — graded, follow-up questions await the tester
#   reviewed         — final verdict (score present)
#   degraded         — no automated verdict (no key / cap hit / API or
#                      schema failure); the reason is stored, never a secret
AI_REVIEW_STATUSES = ("pending-followup", "reviewed", "degraded")
# Ledger states: owed (approved, waiting on the owner/rail) · held (flagged) ·
# paid (owner marked it paid) · dry-run (the payout adapter's no-money record).
LEDGER_STATES = ("owed", "held", "paid", "dry-run")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS claims (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    paypal_email TEXT NOT NULL DEFAULT '',
    token TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'claimed',
    created_at TEXT NOT NULL,
    UNIQUE (task_id, email)
);
CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_id INTEGER NOT NULL REFERENCES claims(id),
    answers_json TEXT NOT NULL DEFAULT '{}',
    findings TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ai_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    submission_id INTEGER NOT NULL UNIQUE REFERENCES submissions(id),
    status TEXT NOT NULL,
    score INTEGER,
    low_effort INTEGER NOT NULL DEFAULT 0,
    summary TEXT NOT NULL DEFAULT '',
    findings_json TEXT NOT NULL DEFAULT '[]',
    followups_json TEXT NOT NULL DEFAULT '[]',
    degraded_reason TEXT NOT NULL DEFAULT '',
    calls_used INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS screenshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    submission_id INTEGER NOT NULL REFERENCES submissions(id),
    filename TEXT NOT NULL,
    content_type TEXT NOT NULL,
    data BLOB NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS guide_exchanges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_id INTEGER NOT NULL REFERENCES claims(id),
    step_index INTEGER NOT NULL DEFAULT 0,
    step_title TEXT NOT NULL DEFAULT '',
    message TEXT NOT NULL,
    reply TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS payout_ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_id INTEGER NOT NULL,
    task_id TEXT NOT NULL,
    email TEXT NOT NULL,
    amount_usd REAL NOT NULL,
    state TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);
"""


def db_path() -> str:
    """Resolve the DB path per call so tests can monkeypatch the env."""
    return os.environ.get("TESTING_DB_PATH") or str(DEFAULT_DB_PATH)


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)  # idempotent — no separate migration step
    _ensure_step_title_column(conn)
    return conn


def _ensure_step_title_column(conn: sqlite3.Connection) -> None:
    """Retrofit ``guide_exchanges.step_title`` onto DB files created before
    the provenance pin — ``CREATE TABLE IF NOT EXISTS`` never adds columns to
    an existing table. Retrofitted rows keep the ``''`` default: "no snapshot
    was taken" is their honest state, never backfilled from the current
    script (that would fake exactly the attribution this column disproves)."""
    cols = {
        r["name"]
        for r in conn.execute("PRAGMA table_info(guide_exchanges)").fetchall()
    }
    if "step_title" not in cols:
        conn.execute(
            "ALTER TABLE guide_exchanges"
            " ADD COLUMN step_title TEXT NOT NULL DEFAULT ''"
        )


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _rows(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(r) for r in rows]


# --- claims ----------------------------------------------------------------

def create_claim(
    task_id: str, name: str, email: str, paypal_email: str, token: str
) -> dict[str, Any]:
    with closing(_connect()) as conn, conn:
        cur = conn.execute(
            "INSERT INTO claims (task_id, name, email, paypal_email, token,"
            " status, created_at) VALUES (?, ?, ?, ?, ?, 'claimed', ?)",
            (task_id, name, email, paypal_email, token, _now()),
        )
        row = conn.execute(
            "SELECT * FROM claims WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
    return dict(row)


def has_claim(task_id: str, email: str) -> bool:
    with closing(_connect()) as conn:
        row = conn.execute(
            "SELECT 1 FROM claims WHERE task_id = ? AND email = ?",
            (task_id, email),
        ).fetchone()
    return row is not None


def active_claim_count(task_id: str) -> int:
    """Claims holding a slot: everything except rejected."""
    with closing(_connect()) as conn:
        (n,) = conn.execute(
            "SELECT COUNT(*) FROM claims WHERE task_id = ? AND status != 'rejected'",
            (task_id,),
        ).fetchone()
    return int(n)


def active_claims() -> list[dict[str, Any]]:
    """Every non-rejected claim (the open-bounty exposure set)."""
    with closing(_connect()) as conn:
        rows = conn.execute(
            "SELECT * FROM claims WHERE status != 'rejected' ORDER BY id"
        ).fetchall()
    return _rows(rows)


def claim_by_token(token: str) -> Optional[dict[str, Any]]:
    with closing(_connect()) as conn:
        row = conn.execute(
            "SELECT * FROM claims WHERE token = ?", (token,)
        ).fetchone()
    return dict(row) if row else None


def claim_by_id(claim_id: int) -> Optional[dict[str, Any]]:
    with closing(_connect()) as conn:
        row = conn.execute(
            "SELECT * FROM claims WHERE id = ?", (claim_id,)
        ).fetchone()
    return dict(row) if row else None


def set_claim_status(claim_id: int, status: str) -> None:
    assert status in CLAIM_STATUSES, status
    with closing(_connect()) as conn, conn:
        conn.execute(
            "UPDATE claims SET status = ? WHERE id = ?", (status, claim_id)
        )


def list_claims() -> list[dict[str, Any]]:
    with closing(_connect()) as conn:
        rows = conn.execute("SELECT * FROM claims ORDER BY id DESC").fetchall()
    return _rows(rows)


# --- submissions -----------------------------------------------------------

def create_submission(
    claim_id: int, answers: dict[str, Any], findings: str
) -> dict[str, Any]:
    with closing(_connect()) as conn, conn:
        cur = conn.execute(
            "INSERT INTO submissions (claim_id, answers_json, findings,"
            " created_at) VALUES (?, ?, ?, ?)",
            (claim_id, json.dumps(answers, ensure_ascii=False), findings, _now()),
        )
        row = conn.execute(
            "SELECT * FROM submissions WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
    return dict(row)


def submission_by_id(submission_id: int) -> Optional[dict[str, Any]]:
    with closing(_connect()) as conn:
        row = conn.execute(
            "SELECT * FROM submissions WHERE id = ?", (submission_id,)
        ).fetchone()
    return dict(row) if row else None


def submission_for_claim(claim_id: int) -> Optional[dict[str, Any]]:
    with closing(_connect()) as conn:
        row = conn.execute(
            "SELECT * FROM submissions WHERE claim_id = ? ORDER BY id DESC LIMIT 1",
            (claim_id,),
        ).fetchone()
    return dict(row) if row else None


def list_submissions() -> list[dict[str, Any]]:
    """Submissions joined to their claim (the owner-queue view)."""
    with closing(_connect()) as conn:
        rows = conn.execute(
            "SELECT s.id, s.claim_id, s.answers_json, s.findings, s.created_at,"
            " c.task_id, c.name, c.email, c.paypal_email, c.status AS claim_status"
            " FROM submissions s JOIN claims c ON c.id = s.claim_id"
            " ORDER BY s.id DESC"
        ).fetchall()
    return _rows(rows)


# --- AI exit-reviews (one row per submission) --------------------------------

def _review_row(row: sqlite3.Row) -> dict[str, Any]:
    """Row → dict with the JSON columns decoded (defensively)."""
    out = dict(row)
    for col, key, fallback in (
        ("findings_json", "findings", []),
        ("followups_json", "followups", []),
    ):
        try:
            out[key] = json.loads(out.get(col) or "[]")
        except ValueError:
            out[key] = fallback
    out["low_effort"] = bool(out.get("low_effort"))
    return out


def save_ai_review(
    submission_id: int,
    *,
    status: str,
    score: Optional[int] = None,
    low_effort: bool = False,
    summary: str = "",
    findings: Optional[list[dict[str, Any]]] = None,
    followups: Optional[list[dict[str, Any]]] = None,
    degraded_reason: str = "",
    calls_used: int = 0,
) -> dict[str, Any]:
    """Insert-or-replace the submission's single AI review row."""
    assert status in AI_REVIEW_STATUSES, status
    now = _now()
    with closing(_connect()) as conn, conn:
        existing = conn.execute(
            "SELECT id, created_at FROM ai_reviews WHERE submission_id = ?",
            (submission_id,),
        ).fetchone()
        created_at = existing["created_at"] if existing else now
        conn.execute(
            "INSERT INTO ai_reviews (submission_id, status, score, low_effort,"
            " summary, findings_json, followups_json, degraded_reason,"
            " calls_used, created_at, updated_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
            " ON CONFLICT(submission_id) DO UPDATE SET"
            " status=excluded.status, score=excluded.score,"
            " low_effort=excluded.low_effort, summary=excluded.summary,"
            " findings_json=excluded.findings_json,"
            " followups_json=excluded.followups_json,"
            " degraded_reason=excluded.degraded_reason,"
            " calls_used=excluded.calls_used, updated_at=excluded.updated_at",
            (
                submission_id,
                status,
                score,
                1 if low_effort else 0,
                summary,
                json.dumps(findings or [], ensure_ascii=False),
                json.dumps(followups or [], ensure_ascii=False),
                degraded_reason,
                calls_used,
                created_at,
                now,
            ),
        )
        row = conn.execute(
            "SELECT * FROM ai_reviews WHERE submission_id = ?", (submission_id,)
        ).fetchone()
    return _review_row(row)


def ai_review_for_submission(submission_id: int) -> Optional[dict[str, Any]]:
    with closing(_connect()) as conn:
        row = conn.execute(
            "SELECT * FROM ai_reviews WHERE submission_id = ?", (submission_id,)
        ).fetchone()
    return _review_row(row) if row else None


def degraded_review_count() -> int:
    with closing(_connect()) as conn:
        (n,) = conn.execute(
            "SELECT COUNT(*) FROM ai_reviews WHERE status = 'degraded'"
        ).fetchone()
    return int(n)


# --- screenshots (blobs — captured by the JSON export valve) -----------------

def add_screenshot(
    submission_id: int, filename: str, content_type: str, data: bytes
) -> dict[str, Any]:
    with closing(_connect()) as conn, conn:
        cur = conn.execute(
            "INSERT INTO screenshots (submission_id, filename, content_type,"
            " data, created_at) VALUES (?, ?, ?, ?, ?)",
            (submission_id, filename, content_type, data, _now()),
        )
        row = conn.execute(
            "SELECT id, submission_id, filename, content_type,"
            " LENGTH(data) AS size_bytes, created_at"
            " FROM screenshots WHERE id = ?",
            (cur.lastrowid,),
        ).fetchone()
    return dict(row)


def screenshots_for_submission(submission_id: int) -> list[dict[str, Any]]:
    """Metadata only — the blob is served by its own owner-auth route."""
    with closing(_connect()) as conn:
        rows = conn.execute(
            "SELECT id, submission_id, filename, content_type,"
            " LENGTH(data) AS size_bytes, created_at"
            " FROM screenshots WHERE submission_id = ? ORDER BY id",
            (submission_id,),
        ).fetchall()
    return _rows(rows)


def screenshot_by_id(shot_id: int) -> Optional[dict[str, Any]]:
    """Full row including the blob (owner-auth serving route only)."""
    with closing(_connect()) as conn:
        row = conn.execute(
            "SELECT * FROM screenshots WHERE id = ?", (shot_id,)
        ).fetchone()
    return dict(row) if row else None


# --- guide chat transcript (TEXT only — never screen frames) -----------------
# One row per successful tester↔guide chat exchange. Bounded per claim by the
# guide-message cap (writes happen only after ai.consume_guide_call succeeded
# and a reply came back), and per row by the route's input cap + the guide's
# reply cap. The screen-frame path stays write-free (test-pinned privacy
# contract) — nothing derived from a shared screen ever lands here.

def add_guide_exchange(
    claim_id: int, step_index: int, message: str, reply: str,
    step_title: str = "",
) -> dict[str, Any]:
    """``step_title`` is the provenance pin: the step's title AS THE ASKER SAW
    IT, snapshotted by the route at persist time. ``step_index`` alone decays —
    the moment the walkthrough script inserts, removes, or reorders a step,
    the index points at different text and history silently re-attributes.
    Default ``''`` = no snapshot (rows persisted before the pin existed)."""
    with closing(_connect()) as conn, conn:
        cur = conn.execute(
            "INSERT INTO guide_exchanges (claim_id, step_index, step_title,"
            " message, reply, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (claim_id, step_index, step_title, message, reply, _now()),
        )
        row = conn.execute(
            "SELECT * FROM guide_exchanges WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
    return dict(row)


def guide_transcript_for_claim(claim_id: int) -> list[dict[str, Any]]:
    """The claim's chat transcript, oldest first (the conversation order)."""
    with closing(_connect()) as conn:
        rows = conn.execute(
            "SELECT * FROM guide_exchanges WHERE claim_id = ? ORDER BY id",
            (claim_id,),
        ).fetchall()
    return _rows(rows)


def abandoned_guided_claims() -> list[dict[str, Any]]:
    """Claimed-but-never-submitted claims with guide-chat activity.

    The owner queue's drop-off view: the claim is still 'claimed' (no
    submission row exists), yet at least one guide exchange persisted — the
    tester engaged with the guide and gave up. Each row is the claim plus
    ``exchange_count`` and ``last_exchange_at``, newest activity first."""
    with closing(_connect()) as conn:
        rows = conn.execute(
            "SELECT c.*, COUNT(g.id) AS exchange_count,"
            " MAX(g.created_at) AS last_exchange_at"
            " FROM claims c JOIN guide_exchanges g ON g.claim_id = c.id"
            " WHERE c.status = 'claimed'"
            " AND NOT EXISTS (SELECT 1 FROM submissions s WHERE s.claim_id = c.id)"
            " GROUP BY c.id"
            " ORDER BY last_exchange_at DESC, c.id DESC"
        ).fetchall()
    return _rows(rows)


def guided_step_dropoff() -> list[dict[str, Any]]:
    """Per-task step heatmap over the abandoned guided claims.

    Same scope as ``abandoned_guided_claims()`` (status 'claimed', no
    submission row, at least one guide exchange). For each task and each
    step_index: ``touched`` counts claims whose chat has ≥1 exchange at that
    step, ``died_here`` counts claims whose chat ENDED there (their highest
    step_index — the step where the tester gave up). Steps run dense from 0
    to the task's highest observed step so gaps render as zeros; tasks are
    ordered by task_id. ``claim_count`` is the task's drop-off total (the
    died_here denominator).

    Survival contrast: ``finished`` counts FINISHER claims — a submission
    row exists, the tester pushed through — whose chat has ≥1 exchange at
    that step (PR #292 persists their transcripts too; the drop-off scope
    merely excludes them), and ``died_share`` is died_here over ALL
    touchers of the step (drop-off + finisher claims; 0.0 when nobody
    touched it) — the lethality signal that separates "hard but passable"
    (many finishers asked, few died) from "wall" (every toucher died).
    ``finisher_count`` is the task's total of finisher claims with any
    guide chat. Finisher chats extend the dense range when they reach past
    the last drop-off step; tasks still appear only when they have
    drop-offs — the strip stays a drop-off view, finishers are contrast."""
    with closing(_connect()) as conn:
        rows = conn.execute(
            "SELECT c.task_id, g.claim_id, g.step_index"
            " FROM claims c JOIN guide_exchanges g ON g.claim_id = c.id"
            " WHERE c.status = 'claimed'"
            " AND NOT EXISTS (SELECT 1 FROM submissions s WHERE s.claim_id = c.id)"
            " GROUP BY c.task_id, g.claim_id, g.step_index"
        ).fetchall()
        finisher_rows = conn.execute(
            "SELECT c.task_id, g.claim_id, g.step_index"
            " FROM claims c JOIN guide_exchanges g ON g.claim_id = c.id"
            " WHERE EXISTS (SELECT 1 FROM submissions s WHERE s.claim_id = c.id)"
            " GROUP BY c.task_id, g.claim_id, g.step_index"
        ).fetchall()
    # (task_id, claim_id) → the steps that claim's chat touched; the max of
    # that set is where the claim died.
    steps_by_claim: dict[tuple[str, int], set[int]] = {}
    for r in rows:
        key = (r["task_id"], r["claim_id"])
        steps_by_claim.setdefault(key, set()).add(int(r["step_index"]))
    claims_by_task: dict[str, list[set[int]]] = {}
    for (task_id, _claim_id), steps in steps_by_claim.items():
        claims_by_task.setdefault(task_id, []).append(steps)
    # Same shape for the finishers — their max is just "furthest step they
    # asked at", nothing died there.
    fin_by_claim: dict[tuple[str, int], set[int]] = {}
    for r in finisher_rows:
        key = (r["task_id"], r["claim_id"])
        fin_by_claim.setdefault(key, set()).add(int(r["step_index"]))
    finishers_by_task: dict[str, list[set[int]]] = {}
    for (task_id, _claim_id), steps in fin_by_claim.items():
        finishers_by_task.setdefault(task_id, []).append(steps)
    out: list[dict[str, Any]] = []
    for task_id in sorted(claims_by_task):
        claim_steps = claims_by_task[task_id]
        fin_steps = finishers_by_task.get(task_id, [])
        top = max(max(steps) for steps in claim_steps)
        if fin_steps:
            top = max(top, max(max(steps) for steps in fin_steps))
        steps_out: list[dict[str, Any]] = []
        for idx in range(top + 1):
            touched = sum(1 for s in claim_steps if idx in s)
            died_here = sum(1 for s in claim_steps if max(s) == idx)
            finished = sum(1 for s in fin_steps if idx in s)
            touchers = touched + finished
            steps_out.append(
                {
                    "step_index": idx,
                    "touched": touched,
                    "died_here": died_here,
                    "finished": finished,
                    "died_share": died_here / touchers if touchers else 0.0,
                }
            )
        out.append(
            {
                "task_id": task_id,
                "claim_count": len(claim_steps),
                "finisher_count": len(fin_steps),
                "steps": steps_out,
            }
        )
    return out


def guided_finisher_hotspots() -> list[dict[str, Any]]:
    """Per-task step aggregate over FINISHER chats on tasks with NO drop-offs.

    The complement of ``guided_step_dropoff()``'s survival contrast: that
    strip only renders tasks that HAVE drop-offs, so a task where every
    tester finished but half of them asked the guide about one step surfaces
    nothing — the "needs a hint" signal is invisible exactly where it's
    purest. This aggregate covers the leftover tasks: at least one finisher
    claim (a submission row EXISTS — same scope as the contrast side of the
    drop-off strip) with guide-chat activity, and zero drop-off claims
    (status 'claimed', no submission, ≥1 exchange — tasks with any drop-off
    already show their finisher counts as contrast on the heatmap).

    For each task and each step_index: ``finished`` counts finisher claims
    whose chat has ≥1 exchange at that step (claims, not exchanges — same
    counting rule as the heatmap). Steps run dense from 0 to the task's
    highest observed step so gaps render as zeros; tasks are ordered by
    task_id. ``finisher_count`` is the task's total of finisher claims with
    any guide chat. No lethality here — nobody died; the counts alone are
    the hotspot signal."""
    with closing(_connect()) as conn:
        finisher_rows = conn.execute(
            "SELECT c.task_id, g.claim_id, g.step_index"
            " FROM claims c JOIN guide_exchanges g ON g.claim_id = c.id"
            " WHERE EXISTS (SELECT 1 FROM submissions s WHERE s.claim_id = c.id)"
            " GROUP BY c.task_id, g.claim_id, g.step_index"
        ).fetchall()
        dropoff_tasks = {
            r["task_id"]
            for r in conn.execute(
                "SELECT DISTINCT c.task_id"
                " FROM claims c JOIN guide_exchanges g ON g.claim_id = c.id"
                " WHERE c.status = 'claimed'"
                " AND NOT EXISTS"
                " (SELECT 1 FROM submissions s WHERE s.claim_id = c.id)"
            ).fetchall()
        }
    fin_by_claim: dict[tuple[str, int], set[int]] = {}
    for r in finisher_rows:
        if r["task_id"] in dropoff_tasks:
            continue  # already on the drop-off strip as contrast
        key = (r["task_id"], r["claim_id"])
        fin_by_claim.setdefault(key, set()).add(int(r["step_index"]))
    finishers_by_task: dict[str, list[set[int]]] = {}
    for (task_id, _claim_id), steps in fin_by_claim.items():
        finishers_by_task.setdefault(task_id, []).append(steps)
    out: list[dict[str, Any]] = []
    for task_id in sorted(finishers_by_task):
        fin_steps = finishers_by_task[task_id]
        top = max(max(steps) for steps in fin_steps)
        steps_out = [
            {
                "step_index": idx,
                "finished": sum(1 for s in fin_steps if idx in s),
            }
            for idx in range(top + 1)
        ]
        out.append(
            {
                "task_id": task_id,
                "finisher_count": len(fin_steps),
                "steps": steps_out,
            }
        )
    return out


QUESTION_DIGEST_CAP = 5  # newest tester questions kept per (task, step) cell


def guided_step_questions(
    cap: int = QUESTION_DIGEST_CAP,
) -> dict[str, dict[int, dict[str, Any]]]:
    """Tester questions grouped by (task, step) across ALL claims.

    The digest behind the heatmap / hotspot cells: the strips
    (``guided_step_dropoff()`` / ``guided_finisher_hotspots()``) count WHO
    asked per step; this returns WHAT they asked — the persisted
    ``guide_exchanges`` MESSAGE text (tester side only, never the guide's
    replies), keyed ``task_id → step_index → cell``. Scope is every claim
    with chat activity regardless of outcome — drop-offs AND finishers
    (PR #292 persists both) — because a hint-needing step reads the same
    whatever became of the asker; a task only surfaces where a strip row
    exists to hang it on, so extra tasks in the mapping are inert.

    Each cell carries ``total`` (every exchange at that task+step) and
    ``questions`` — the newest ``cap`` entries, newest first, so one chatty
    claim can't scroll the strip. Each entry is ``{"message", "step_title"}``:
    the message is RAW tester input (the caller renders it escaped and
    truncated for display) and ``step_title`` is the row's provenance pin —
    the step's title at ask time, ``''`` for rows persisted before the pin
    existed. The caller compares the pin against the CURRENT script to flag
    questions asked against an older version of the step."""
    with closing(_connect()) as conn:
        rows = conn.execute(
            "SELECT c.task_id, g.step_index, g.step_title, g.message"
            " FROM guide_exchanges g JOIN claims c ON c.id = g.claim_id"
            " ORDER BY g.id DESC"
        ).fetchall()
    out: dict[str, dict[int, dict[str, Any]]] = {}
    for r in rows:
        cell = out.setdefault(r["task_id"], {}).setdefault(
            int(r["step_index"]), {"total": 0, "questions": []}
        )
        cell["total"] += 1
        if len(cell["questions"]) < cap:
            cell["questions"].append(
                {"message": r["message"], "step_title": r["step_title"]}
            )
    return out


# --- payout ledger ----------------------------------------------------------

def add_ledger_entry(
    claim_id: int,
    task_id: str,
    email: str,
    amount_usd: float,
    state: str,
    note: str = "",
) -> dict[str, Any]:
    assert state in LEDGER_STATES, state
    with closing(_connect()) as conn, conn:
        cur = conn.execute(
            "INSERT INTO payout_ledger (claim_id, task_id, email, amount_usd,"
            " state, note, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (claim_id, task_id, email, amount_usd, state, note, _now()),
        )
        row = conn.execute(
            "SELECT * FROM payout_ledger WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
    return dict(row)


def ledger_entries() -> list[dict[str, Any]]:
    with closing(_connect()) as conn:
        rows = conn.execute(
            "SELECT * FROM payout_ledger ORDER BY id DESC"
        ).fetchall()
    return _rows(rows)


def ledger_totals() -> dict[str, float]:
    """USD total per ledger state (owed / held / paid / dry-run), zeros kept."""
    totals = {state: 0.0 for state in LEDGER_STATES}
    with closing(_connect()) as conn:
        rows = conn.execute(
            "SELECT state, COALESCE(SUM(amount_usd), 0) AS total"
            " FROM payout_ledger GROUP BY state"
        ).fetchall()
    for row in rows:
        totals[row["state"]] = float(row["total"])
    return totals


def has_payout(task_id: str, email: str) -> bool:
    """One payout per email per task — counts paid AND owed (already promised)."""
    with closing(_connect()) as conn:
        row = conn.execute(
            "SELECT 1 FROM payout_ledger WHERE task_id = ? AND email = ?"
            " AND state IN ('owed', 'paid')",
            (task_id, email),
        ).fetchone()
    return row is not None


def paid_total_since(since_iso: str) -> float:
    """USD sum of paid entries at/after an ISO stamp (daily/monthly cap input)."""
    with closing(_connect()) as conn:
        (total,) = conn.execute(
            "SELECT COALESCE(SUM(amount_usd), 0) FROM payout_ledger"
            " WHERE state = 'paid' AND created_at >= ?",
            (since_iso,),
        ).fetchone()
    return float(total)


# --- import (the other half of the backup valve — restore after a wipe) ------

class ImportValidationError(ValueError):
    """The uploaded payload is not a valid export.json backup (route → 400)."""


class ImportNotEmptyError(RuntimeError):
    """Refusal to import over live rows without the explicit replace flag
    (route → 409). Losing current data to a stale backup must be opt-in."""


_REQUIRED = object()  # sentinel: the field must be present in every backup

# Per-table import spec: (export field, default). ``_REQUIRED`` marks fields
# every export version carried; everything else takes its schema default via
# ``.get`` so LEGACY backups restore cleanly — e.g. ``step_title`` on
# guide_exchanges (the provenance pin added after early exports) falls back
# to ``''``, the same honest "no snapshot was taken" state the column
# retrofit uses. A whole missing table key also imports as empty (tables
# were added over time). ``screenshots.data_base64`` is decoded to the
# ``data`` blob column at insert time.
_IMPORT_SPEC: dict[str, tuple[tuple[str, Any], ...]] = {
    "claims": (
        ("id", _REQUIRED),
        ("task_id", _REQUIRED),
        ("name", _REQUIRED),
        ("email", _REQUIRED),
        ("paypal_email", ""),
        ("token", _REQUIRED),
        ("status", "claimed"),
        ("created_at", _REQUIRED),
    ),
    "submissions": (
        ("id", _REQUIRED),
        ("claim_id", _REQUIRED),
        ("answers_json", "{}"),
        ("findings", ""),
        ("created_at", _REQUIRED),
    ),
    "ai_reviews": (
        ("id", _REQUIRED),
        ("submission_id", _REQUIRED),
        ("status", _REQUIRED),
        ("score", None),
        ("low_effort", 0),
        ("summary", ""),
        ("findings_json", "[]"),
        ("followups_json", "[]"),
        ("degraded_reason", ""),
        ("calls_used", 0),
        ("created_at", _REQUIRED),
        ("updated_at", _REQUIRED),
    ),
    "screenshots": (
        ("id", _REQUIRED),
        ("submission_id", _REQUIRED),
        ("filename", _REQUIRED),
        ("content_type", _REQUIRED),
        ("data_base64", _REQUIRED),
        ("created_at", _REQUIRED),
    ),
    "guide_exchanges": (
        ("id", _REQUIRED),
        ("claim_id", _REQUIRED),
        ("step_index", 0),
        ("step_title", ""),  # pre-provenance-pin backups lack this column
        ("message", _REQUIRED),
        ("reply", _REQUIRED),
        ("created_at", _REQUIRED),
    ),
    "payout_ledger": (
        ("id", _REQUIRED),
        ("claim_id", _REQUIRED),
        ("task_id", _REQUIRED),
        ("email", _REQUIRED),
        ("amount_usd", _REQUIRED),
        ("state", _REQUIRED),
        ("note", ""),
        ("created_at", _REQUIRED),
    ),
}

# Enum columns re-checked on import — a backup edited by hand (or the wrong
# file entirely) fails loudly instead of planting impossible states.
_IMPORT_ENUMS: dict[str, tuple[str, tuple[str, ...]]] = {
    "claims": ("status", CLAIM_STATUSES),
    "ai_reviews": ("status", AI_REVIEW_STATUSES),
    "payout_ledger": ("state", LEDGER_STATES),
}


def _validated_import_rows(payload: Any) -> dict[str, list[dict[str, Any]]]:
    """export.json payload → per-table row dicts, or ImportValidationError."""
    if not isinstance(payload, dict):
        raise ImportValidationError(
            "backup must be a JSON object (the export.json shape)"
        )
    if not isinstance(payload.get("claims"), list):
        raise ImportValidationError(
            "backup has no 'claims' list — this is not an export.json backup"
        )
    tables: dict[str, list[dict[str, Any]]] = {}
    for table, spec in _IMPORT_SPEC.items():
        raw = payload.get(table, [])
        if not isinstance(raw, list):
            raise ImportValidationError(f"'{table}' must be a list of records")
        rows: list[dict[str, Any]] = []
        for i, rec in enumerate(raw):
            if not isinstance(rec, dict):
                raise ImportValidationError(f"{table}[{i}] is not an object")
            row: dict[str, Any] = {}
            for field, default in spec:
                if default is _REQUIRED:
                    if rec.get(field) is None:
                        raise ImportValidationError(
                            f"{table}[{i}] is missing required field '{field}'"
                        )
                    row[field] = rec[field]
                else:
                    # Legacy backups lack columns added after they were taken
                    # — the schema default is their honest value.
                    value = rec.get(field, default)
                    row[field] = default if value is None else value
            rows.append(row)
        tables[table] = rows
    for table, (field, allowed) in _IMPORT_ENUMS.items():
        for i, row in enumerate(tables[table]):
            if row[field] not in allowed:
                raise ImportValidationError(
                    f"{table}[{i}] has unknown {field} {row[field]!r}"
                )
    for i, row in enumerate(tables["screenshots"]):
        raw_b64 = row.pop("data_base64")
        try:
            row["data"] = base64.b64decode(str(raw_b64), validate=True)
        except (ValueError, TypeError):
            raise ImportValidationError(
                f"screenshots[{i}] has undecodable base64 in 'data_base64'"
            )
    return tables


def import_all(payload: Any, *, replace: bool = False) -> dict[str, int]:
    """Restore an ``export_all()`` backup into the store — the import valve.

    REPLACE-into-empty semantics: without ``replace`` the import REFUSES
    (``ImportNotEmptyError``) when any table already holds rows; with
    ``replace=True`` every table is wiped and the backup inserted, all in
    ONE transaction (a failed import rolls back to the pre-call state, never
    a half-restored DB). Row ids are preserved so cross-table references
    (claim_id, submission_id) survive the round trip. Returns the per-table
    inserted-row counts.
    """
    tables = _validated_import_rows(payload)
    with closing(_connect()) as conn, conn:
        existing = sum(
            conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            for t in _IMPORT_SPEC
        )
        if existing and not replace:
            raise ImportNotEmptyError(
                f"testing DB already holds {existing} rows — import only "
                "restores into an empty DB unless replace is explicitly set"
            )
        if replace:
            for table in _IMPORT_SPEC:
                conn.execute(f"DELETE FROM {table}")
        for table, rows in tables.items():
            for row in rows:
                cols = list(row)
                conn.execute(
                    f"INSERT INTO {table} ({', '.join(cols)})"
                    f" VALUES ({', '.join('?' for _ in cols)})",
                    [row[c] for c in cols],
                )
    return {table: len(rows) for table, rows in tables.items()}


# --- export (the ephemeral-disk backup valve) --------------------------------

def export_all() -> dict[str, Any]:
    with closing(_connect()) as conn:
        claims = _rows(conn.execute("SELECT * FROM claims ORDER BY id").fetchall())
        submissions = _rows(
            conn.execute("SELECT * FROM submissions ORDER BY id").fetchall()
        )
        ai_reviews = _rows(
            conn.execute("SELECT * FROM ai_reviews ORDER BY id").fetchall()
        )
        shots = _rows(
            conn.execute("SELECT * FROM screenshots ORDER BY id").fetchall()
        )
        guide_exchanges = _rows(
            conn.execute("SELECT * FROM guide_exchanges ORDER BY id").fetchall()
        )
        ledger = _rows(
            conn.execute("SELECT * FROM payout_ledger ORDER BY id").fetchall()
        )
    # Screenshot blobs base64 so the export stays a single valid JSON backup.
    for s in shots:
        s["data_base64"] = base64.b64encode(s.pop("data")).decode("ascii")
    return {
        "exported_at": _now(),
        "db_path": db_path(),
        "warning": (
            "SQLite on Railway's ephemeral disk — this export is the backup; "
            "data is lost on redeploy until the Postgres ask lands"
        ),
        "claims": claims,
        "submissions": submissions,
        "ai_reviews": ai_reviews,
        "screenshots": shots,
        "guide_exchanges": guide_exchanges,
        "payout_ledger": ledger,
    }
