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

import json
import os
import sqlite3
import time
from contextlib import closing
from pathlib import Path
from typing import Any, Optional

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR / "testing.sqlite3"

# Claim lifecycle: claimed → submitted → approved | rejected; approved → paid.
# A rejected claim frees its task slot (active = everything except rejected).
CLAIM_STATUSES = ("claimed", "submitted", "approved", "rejected", "paid")
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
        ledger = _rows(
            conn.execute("SELECT * FROM payout_ledger ORDER BY id").fetchall()
        )
    return {
        "exported_at": _now(),
        "db_path": db_path(),
        "warning": (
            "SQLite on Railway's ephemeral disk — this export is the backup; "
            "data is lost on redeploy until the Postgres ask lands"
        ),
        "claims": claims,
        "submissions": submissions,
        "payout_ledger": ledger,
    }
