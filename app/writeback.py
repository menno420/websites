"""Owner writeback engine (ORDER 020): the owner authors on the site, git
gets the truth.

The fleet's source of truth is git, so every gated /owner/queue submission
maps to ONE GitHub contents-API commit on ``menno420/websites``:

  ``assist``   (request assistance) → a new ORDER block APPENDED to
               ``control/inbox.md``, numbered after the file's current
               highest ORDER (the file's own append-only convention; the
               number is read at commit time, never guessed from memory).
  ``note``     (correction / idea / note) → appended to
               ``docs/owner/owner-notes.md`` (created with its explanatory
               header if absent).
  ``complete`` (owner asserts an owner-action is done) → appended to the
               same owner-notes log as a completion assertion. A direct
               status flip is IMPOSSIBLE by design: queue items come from
               lane heartbeats, so completion is expressed upstream by
               removing the ask — the log entry tells the fleet to do
               exactly that.

CAPABILITY IS CHECKED AT REQUEST TIME: ``GITHUB_TOKEN`` is read from the
environment per attempt (never cached at import), so the write-scoped PAT
the owner pastes into Railway lights up on the next submit/retry without a
redeploy. Today's deployed token is READ-scoped — a contents PUT will
403/404. That is handled honestly: the submission is stored FIRST in a
local SQLite audit log and only flipped to ``committed`` when the API
response carries the new commit SHA (verified, linked). On any failure the
entry stays ``queued`` (retryable) or ``failed`` (validation), with the
exact error class shown to the owner. A commit is NEVER claimed that did
not land.

LOUD FLAG — EPHEMERAL LOCAL STORE (stated in the UI): the SQLite audit log
lives on the service's local disk (``WRITEBACK_DB_PATH``, default
``app/writeback.sqlite3``, gitignored) and Railway's disk is wiped on every
redeploy. Entries that COMMITTED are safe (git holds them); entries still
queued at redeploy time are lost — the UI says so next to every queued row.
Same tradeoff, same banner style as botsite/testing_store.py (the repo's
SQLite precedent).

Layering: domain module for app/owner.py routes. Imports the client layer
(app/github.py) and config/clock only — never routes or templates.
"""

from __future__ import annotations

import base64
import os
import re
import sqlite3
from pathlib import Path
from typing import Any, Optional

from . import clock, config, github

# --------------------------------------------------------------------------
# constants / env knobs (documented in the module docstring)
# --------------------------------------------------------------------------
ACTIONS = ("complete", "assist", "note")
STATUSES = ("queued", "committed", "failed")

TARGET_MAX_CHARS = 300
TEXT_MAX_CHARS = 4000

ENV_TOKEN = "GITHUB_TOKEN"  # read per attempt — see module docstring
ENV_BRANCH = "WRITEBACK_BRANCH"
DEFAULT_BRANCH = "main"
ENV_DB_PATH = "WRITEBACK_DB_PATH"

WRITEBACK_REPO = "websites"
INBOX_PATH = "control/inbox.md"
NOTES_PATH = "docs/owner/owner-notes.md"

# Header used when the notes log must be CREATED at runtime (404 on read).
# Kept byte-identical to the committed seed file so both paths converge.
NOTES_HEADER = """# Owner notes — written from the launch console

> **Status:** `living-ledger`
>
> Append-only log written AT RUNTIME by the control-plane's gated owner
> writeback (`/owner/queue`, ORDER 020): completion assertions, corrections,
> and ideas the owner typed directly on the site. **Fleet sessions should
> read new entries on boot and act on them** — reconcile completion
> assertions into the source heartbeat's `needs-owner` field (and
> `docs/owner/OWNER-ACTIONS.md`), route ideas/corrections to the right
> backlog. Never edit or reorder past entries.
"""

_ORDER_NUM_RE = re.compile(r"^## ORDER (\d+)\b", re.MULTILINE)

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR / "writeback.sqlite3"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS writeback_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    target TEXT NOT NULL DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'queued',
    path TEXT NOT NULL DEFAULT '',
    commit_sha TEXT NOT NULL DEFAULT '',
    commit_url TEXT NOT NULL DEFAULT '',
    error TEXT NOT NULL DEFAULT '',
    attempts INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


# --------------------------------------------------------------------------
# runtime env reads — per call, never cached at import
# --------------------------------------------------------------------------
def runtime_token() -> str:
    """The write token, read from the env NOW (see module docstring)."""
    return os.environ.get(ENV_TOKEN, "")


def token_present() -> bool:
    return bool(runtime_token())


def branch() -> str:
    return os.environ.get(ENV_BRANCH) or DEFAULT_BRANCH


def db_path() -> str:
    """Resolved per call so tests can monkeypatch the env."""
    return os.environ.get(ENV_DB_PATH) or str(DEFAULT_DB_PATH)


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)  # idempotent — no separate migration step
    return conn


def _now_iso() -> str:
    return clock.now().strftime("%Y-%m-%dT%H:%M:%SZ")


def _stamp() -> str:
    """Short stamp for the committed entries (matches the inbox's own
    ``2026-07-12T15:50Z`` convention)."""
    return clock.now().strftime("%Y-%m-%dT%H:%MZ")


# --------------------------------------------------------------------------
# local store (audit trail) — every submission, whatever its fate
# --------------------------------------------------------------------------
def _row_to_dict(row: sqlite3.Row) -> dict:
    return {k: row[k] for k in row.keys()}


def store_entry(action: str, target: str, text: str) -> dict:
    """Persist a validated submission as ``queued`` and return it."""
    now = _now_iso()
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO writeback_entries"
            " (action, target, text, status, created_at, updated_at)"
            " VALUES (?, ?, ?, 'queued', ?, ?)",
            (action, target, text, now, now),
        )
        entry_id = cur.lastrowid
    return get_entry(entry_id)  # type: ignore[return-value]


def get_entry(entry_id: int) -> Optional[dict]:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM writeback_entries WHERE id = ?", (entry_id,)
        ).fetchone()
    return _row_to_dict(row) if row else None


def list_entries(limit: int = 100) -> list[dict]:
    """Newest first — the /owner/queue audit-log listing."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM writeback_entries ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def _update_entry(entry_id: int, **fields: Any) -> None:
    fields["updated_at"] = _now_iso()
    keys = ", ".join(f"{k} = ?" for k in fields)
    with _connect() as conn:
        conn.execute(
            f"UPDATE writeback_entries SET {keys} WHERE id = ?",
            (*fields.values(), entry_id),
        )


def validate(action: str, target: str, text: str) -> str:
    """Return an owner-readable rejection reason, or '' when acceptable.

    Length caps are hard rejections (never silent truncation — the commit
    must carry exactly what the owner approved)."""
    if action not in ACTIONS:
        return f"unknown action {action!r}"
    target = target.strip()
    text = text.strip()
    if len(target) > TARGET_MAX_CHARS:
        return f"target too long ({len(target)} > {TARGET_MAX_CHARS} chars)"
    if len(text) > TEXT_MAX_CHARS:
        return f"text too long ({len(text)} > {TEXT_MAX_CHARS} chars)"
    if action == "complete" and not target:
        return "mark-complete needs the target owner-action"
    if action in ("assist", "note") and not text:
        return "the text field is empty — nothing to write back"
    return ""


# --------------------------------------------------------------------------
# entry rendering — what actually lands in git
# --------------------------------------------------------------------------
def _next_order_number(inbox_text: str) -> int:
    numbers = [int(m) for m in _ORDER_NUM_RE.findall(inbox_text)]
    return (max(numbers) + 1) if numbers else 1


def render_assist_block(entry: dict, inbox_text: str) -> str:
    """A new inbox ORDER, numbered per the file's own current maximum and
    following the existing block grammar (## ORDER header, provenance,
    verbatim owner text between markers)."""
    nnn = f"{_next_order_number(inbox_text):03d}"
    target = entry["target"] or "general (no specific queue item)"
    return (
        f"## ORDER {nnn} · {_stamp()} · status: new\n"
        "priority: P1\n"
        "executor: Websites coordinator\n"
        "provenance: owner via launch console (gated /owner/queue writeback, "
        f"ORDER 020 machinery; console audit entry #{entry['id']})\n"
        "why: the owner requested assistance directly from the site's owner "
        "queue.\n"
        f"do: OWNER ASSISTANCE REQUEST — target: {target}. The owner's text "
        "VERBATIM between the markers:\n"
        "BEGIN ORDER TEXT\n"
        f"{entry['text']}\n"
        "END ORDER TEXT\n"
    )


def render_note_block(entry: dict) -> str:
    kind = (
        "owner marked COMPLETE"
        if entry["action"] == "complete"
        else "owner note/correction/idea"
    )
    lines = [
        f"## {_stamp()} · {kind} · via launch console "
        f"(console audit entry #{entry['id']})",
        f"target: {entry['target'] or '-'}",
        "",
        entry["text"] or "(no additional note)",
    ]
    if entry["action"] == "complete":
        lines += [
            "",
            "Fleet: this is the owner's completion assertion for the ask "
            "named above — remove it from the source heartbeat's "
            "needs-owner field (and reconcile docs/owner/OWNER-ACTIONS.md) "
            "on the next session.",
        ]
    return "\n".join(lines) + "\n"


def target_path(action: str) -> str:
    return INBOX_PATH if action == "assist" else NOTES_PATH


# --------------------------------------------------------------------------
# the commit attempt — honest at every branch
# --------------------------------------------------------------------------
def _contents_api_path(path: str) -> str:
    return f"/repos/{config.OWNER}/{WRITEBACK_REPO}/contents/{path}"


async def attempt_commit(entry_id: int) -> dict:
    """Try to land one stored entry as a git commit; update + return it.

    Every outcome is recorded on the entry: ``committed`` ONLY when the
    contents-API response carries the new commit SHA; ``queued`` with the
    exact error for anything retryable (no token, read/write 401/403/404,
    409 sha race, network); ``failed`` for validation-class rejections
    (HTTP 422) a retry cannot fix without change.
    """
    entry = get_entry(entry_id)
    if entry is None:
        raise ValueError(f"unknown writeback entry {entry_id}")
    if entry["status"] == "committed":
        return entry  # never re-commit — the SHA already landed

    _update_entry(entry_id, attempts=entry["attempts"] + 1)

    token = runtime_token()
    if not token:
        _update_entry(
            entry_id,
            status="queued",
            error=(
                f"write token not available — {ENV_TOKEN} is not set on "
                "this service; entry stays queued locally (paste the "
                "contents:write PAT per docs/owner/OWNER-ACTIONS.md and "
                "retry)"
            ),
        )
        return get_entry(entry_id)  # type: ignore[return-value]

    path = target_path(entry["action"])
    ref = branch()

    # 1) Fresh read of the target file (content + blob sha for the PUT).
    read = await github.api_request(
        "GET", f"{_contents_api_path(path)}?ref={ref}", token=token
    )
    sha: Optional[str] = None
    old_text = ""
    if read["ok"] and isinstance(read["data"], dict) and read["data"].get("content"):
        sha = read["data"].get("sha")
        try:
            old_text = base64.b64decode(read["data"]["content"]).decode(
                "utf-8", "replace"
            )
        except Exception:
            _update_entry(
                entry_id,
                status="queued",
                error=f"could not decode {path} from the contents API",
            )
            return get_entry(entry_id)  # type: ignore[return-value]
    elif read["status"] == 404 and path == NOTES_PATH:
        # The notes log does not exist yet — create it with its header.
        old_text = NOTES_HEADER
    else:
        reason = read.get("error") or f"HTTP {read.get('status')}"
        _update_entry(
            entry_id,
            status="queued",
            error=f"could not read {path}@{ref} ({reason}) — entry stays queued",
        )
        return get_entry(entry_id)  # type: ignore[return-value]

    # 2) Append-only compose.
    if entry["action"] == "assist":
        block = render_assist_block(entry, old_text)
    else:
        block = render_note_block(entry)
    new_text = old_text.rstrip("\n") + "\n\n" + block

    # 3) The PUT — one commit, verified by the SHA in the response.
    body: dict[str, Any] = {
        "message": (
            f"owner writeback ({entry['action']}) via launch console "
            "[ORDER 020]"
        ),
        "content": base64.b64encode(new_text.encode("utf-8")).decode("ascii"),
        "branch": ref,
    }
    if sha:
        body["sha"] = sha
    put = await github.api_request(
        "PUT", _contents_api_path(path), json_body=body, token=token
    )

    commit_sha = ""
    if put["ok"] and isinstance(put["data"], dict):
        commit_sha = (put["data"].get("commit") or {}).get("sha") or ""
    if commit_sha:
        commit_url = (put["data"].get("commit") or {}).get("html_url") or (
            f"https://github.com/{config.OWNER}/{WRITEBACK_REPO}"
            f"/commit/{commit_sha}"
        )
        _update_entry(
            entry_id,
            status="committed",
            path=path,
            commit_sha=commit_sha,
            commit_url=commit_url,
            error="",
        )
        return get_entry(entry_id)  # type: ignore[return-value]

    # NEVER claim a commit that did not land — classify the failure.
    reason = put.get("error") or f"HTTP {put.get('status')}"
    if put["status"] in (401, 403, 404):
        # 404 on a PUT is GitHub's "token cannot see/write this" answer.
        status, msg = "queued", (
            f"write rejected (HTTP {put['status']}: {reason}) — the token "
            "has no contents:write on menno420/websites; entry stays "
            "queued (mint the PAT per docs/owner/OWNER-ACTIONS.md, then "
            "retry)"
        )
    elif put["status"] == 409:
        status, msg = "queued", (
            f"write conflict (HTTP 409: {reason}) — the file moved under "
            "us; retry re-reads and re-appends"
        )
    elif put["status"] == 422:
        status, msg = "failed", (
            f"write rejected as invalid (HTTP 422: {reason}) — a retry "
            "will not help without change (branch protection on "
            f"{ref!r} is one known cause)"
        )
    elif put["ok"]:
        status, msg = "queued", (
            "the API answered success but carried NO commit SHA — refusing "
            "to claim a commit that cannot be verified; entry stays queued"
        )
    else:
        status, msg = "queued", (
            f"write failed ({reason}) — transient; entry stays queued, retry"
        )
    _update_entry(entry_id, status=status, path=path, error=msg)
    return get_entry(entry_id)  # type: ignore[return-value]


async def submit(action: str, target: str, text: str) -> dict:
    """Validate → store (audit trail first) → attempt the commit.

    Returns the stored entry in its post-attempt state. Raises ValueError
    only on validation failure (the caller shows the reason; nothing is
    stored for a rejected submission)."""
    target = (target or "").strip()
    text = (text or "").strip()
    problem = validate(action, target, text)
    if problem:
        raise ValueError(problem)
    entry = store_entry(action, target, text)
    return await attempt_commit(entry["id"])


def state_summary() -> dict:
    """The /owner/queue capability panel — names only, never token values."""
    return {
        "token_set": token_present(),
        "token_env": ENV_TOKEN,
        "branch": branch(),
        "repo": f"{config.OWNER}/{WRITEBACK_REPO}",
        "inbox_path": INBOX_PATH,
        "notes_path": NOTES_PATH,
        "entries": len(list_entries(limit=1000)),
    }
