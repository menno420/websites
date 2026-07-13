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
    return conn


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
    claim_id: int, step_index: int, message: str, reply: str
) -> dict[str, Any]:
    with closing(_connect()) as conn, conn:
        cur = conn.execute(
            "INSERT INTO guide_exchanges (claim_id, step_index, message,"
            " reply, created_at) VALUES (?, ?, ?, ?, ?)",
            (claim_id, step_index, message, reply, _now()),
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
    died_here denominator)."""
    with closing(_connect()) as conn:
        rows = conn.execute(
            "SELECT c.task_id, g.claim_id, g.step_index"
            " FROM claims c JOIN guide_exchanges g ON g.claim_id = c.id"
            " WHERE c.status = 'claimed'"
            " AND NOT EXISTS (SELECT 1 FROM submissions s WHERE s.claim_id = c.id)"
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
    out: list[dict[str, Any]] = []
    for task_id in sorted(claims_by_task):
        claim_steps = claims_by_task[task_id]
        top = max(max(steps) for steps in claim_steps)
        out.append(
            {
                "task_id": task_id,
                "claim_count": len(claim_steps),
                "steps": [
                    {
                        "step_index": idx,
                        "touched": sum(1 for s in claim_steps if idx in s),
                        "died_here": sum(1 for s in claim_steps if max(s) == idx),
                    }
                    for idx in range(top + 1)
                ],
            }
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
