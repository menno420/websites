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
ENV_BRANCH = "WRITEBACK_BRANCH"  # the PR BASE (default main); the base main moves by
DEFAULT_BRANCH = "main"
ENV_DB_PATH = "WRITEBACK_DB_PATH"

# Branch + auto-PR is the ONE writeback path (owner-confirmed, Q2=b): main is
# protected by a ruleset requiring the `quality` check, so a direct contents
# PUT to main 403/422s and contradicts the repo's main-moves-by-PR doctrine
# (GH013) — the owner confirmed a straight-to-main PUT is not possible with the
# PAT, so no direct-to-main escape hatch exists. Each submit commits to a fresh
# `claude/owner-writeback-<entry-id>` branch and opens an auto-merging PR into
# the base. The `claude/*` prefix is what the auto-merge-enabler +
# host-automerge-extras workflows arm, and the diff is control/**-only so the CI
# control fast-lane exempts the runtime PR from the session-card requirement.
ENV_BRANCH_PREFIX = "WRITEBACK_BRANCH_PREFIX"
DEFAULT_BRANCH_PREFIX = "claude/owner-writeback-"

WRITEBACK_REPO = "websites"
INBOX_PATH = "control/inbox.md"
# Relocated from docs/owner/owner-notes.md into control/** so a note/complete
# writeback PR is control/**-only and rides the CI fast lane (no session card).
# A pointer stays at the old docs path for back-compat.
NOTES_PATH = "control/owner-notes.md"

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
    branch TEXT NOT NULL DEFAULT '',
    pr_number INTEGER NOT NULL DEFAULT 0,
    pr_url TEXT NOT NULL DEFAULT '',
    error TEXT NOT NULL DEFAULT '',
    attempts INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

# Columns added after the original ship (the branch+PR flow). CREATE TABLE IF
# NOT EXISTS never adds columns to a pre-existing table, so a store carried
# across the change needs them backfilled — cheap, idempotent, stdlib-only.
# (The store is ephemeral by design — Railway wipes disk on redeploy — so this
# only matters within a single container's lifetime.)
_ADDED_COLUMNS = (
    ("branch", "TEXT NOT NULL DEFAULT ''"),
    ("pr_number", "INTEGER NOT NULL DEFAULT 0"),
    ("pr_url", "TEXT NOT NULL DEFAULT ''"),
)


# --------------------------------------------------------------------------
# runtime env reads — per call, never cached at import
# --------------------------------------------------------------------------
def runtime_token() -> str:
    """The write token, read from the env NOW (see module docstring)."""
    return os.environ.get(ENV_TOKEN, "")


def token_present() -> bool:
    return bool(runtime_token())


def branch() -> str:
    """The PR BASE branch (default ``main``) — the writeback PR merges INTO
    it. Never written directly (main is ruleset-protected)."""
    return os.environ.get(ENV_BRANCH) or DEFAULT_BRANCH


def branch_prefix() -> str:
    return os.environ.get(ENV_BRANCH_PREFIX) or DEFAULT_BRANCH_PREFIX


def writeback_branch_name(entry: dict) -> str:
    """The per-submit head branch — unique via the audit entry id, and
    prefixed so the auto-merge workflows arm it (claude/*)."""
    return f"{branch_prefix()}{entry['id']}"


def db_path() -> str:
    """Resolved per call so tests can monkeypatch the env."""
    return os.environ.get(ENV_DB_PATH) or str(DEFAULT_DB_PATH)


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)  # idempotent — no separate migration step
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(writeback_entries)")}
    for name, decl in _ADDED_COLUMNS:
        if name not in existing:
            conn.execute(f"ALTER TABLE writeback_entries ADD COLUMN {name} {decl}")
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
def next_order_number(inbox_text: str) -> int:
    """The ORDER number the NEXT appended block gets, per the file's own
    append-only convention (current maximum + 1). Public so the queue
    preview can show a PROVISIONAL number — the real number is always
    re-read from the file at commit time (race-safe by design)."""
    numbers = [int(m) for m in _ORDER_NUM_RE.findall(inbox_text)]
    return (max(numbers) + 1) if numbers else 1


def render_assist_block(entry: dict, inbox_text: str) -> str:
    """A new inbox ORDER, numbered per the file's own current maximum and
    following the existing block grammar (## ORDER header, provenance,
    verbatim owner text between markers)."""
    nnn = f"{next_order_number(inbox_text):03d}"
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
        "done-when: the coordinator has actioned the owner's request above (or "
        "routed it to the right lane) and reported it in the close-out; this "
        "ORDER's status flips new→done.\n"
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

    # The ONE writeback path (owner-confirmed, Q2=b): commit to a claude/*
    # branch and open an auto-merging PR into the base. A commit is claimed
    # only with a verified SHA — honest-degrade at every step.
    return await _commit_branch_pr(entry, token)


# --- shared commit primitives ----------------------------------------------
def _commit_message(entry: dict) -> str:
    return (
        f"owner writeback ({entry['action']}) via launch console [ORDER 020]"
    )


def _entry_marker(entry: dict) -> str:
    """The unique per-entry string every rendered block embeds — used to make
    a retry idempotent (never double-append when a prior attempt's commit is
    already on the branch)."""
    return f"console audit entry #{entry['id']}"


def _b64(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def _compose(entry: dict, old_text: str) -> str:
    """Append-only compose: the rendered block after the file's current body."""
    if entry["action"] == "assist":
        block = render_assist_block(entry, old_text)
    else:
        block = render_note_block(entry)
    return old_text.rstrip("\n") + "\n\n" + block


async def _read_target(
    path: str, ref: str, token: str
) -> tuple[str, str, Optional[str], str]:
    """Fresh read of the target file at ``ref``.

    Returns ``(state, old_text, blob_sha, reason)``: ``state`` is ``"ok"``
    (file read, blob_sha set), ``"create"`` (a 404 on the notes log → seed
    with its header, no blob sha), or ``"error"`` (reason set for the queued
    entry)."""
    read = await github.api_request(
        "GET", f"{_contents_api_path(path)}?ref={ref}", token=token
    )
    if read["ok"] and isinstance(read["data"], dict) and read["data"].get("content"):
        try:
            old_text = base64.b64decode(read["data"]["content"]).decode(
                "utf-8", "replace"
            )
        except Exception:
            return "error", "", None, f"could not decode {path} from the contents API"
        return "ok", old_text, read["data"].get("sha"), ""
    if read["status"] == 404 and path == NOTES_PATH:
        # The notes log does not exist yet — create it with its header.
        return "create", NOTES_HEADER, None, ""
    reason = read.get("error") or f"HTTP {read.get('status')}"
    return (
        "error", "", None,
        f"could not read {path}@{ref} ({reason}) — entry stays queued",
    )


def _extract_commit(put: dict) -> tuple[str, str]:
    """Return ``(commit_sha, commit_url)`` from a contents-PUT response, or
    ``("", "")`` when the response carries no verifiable SHA — the honesty
    hinge: a commit is claimed ONLY on a real SHA."""
    if put["ok"] and isinstance(put["data"], dict):
        commit = put["data"].get("commit") or {}
        commit_sha = commit.get("sha") or ""
        if commit_sha:
            commit_url = commit.get("html_url") or (
                f"https://github.com/{config.OWNER}/{WRITEBACK_REPO}"
                f"/commit/{commit_sha}"
            )
            return commit_sha, commit_url
    return "", ""


def _classify_write_failure(put: dict, ref: str) -> tuple[str, str]:
    """Classify a rejected write (contents PUT or a git-ref POST) into an
    honest ``(status, message)`` — never a claimed success."""
    reason = put.get("error") or f"HTTP {put.get('status')}"
    if put["status"] in (401, 403, 404):
        # 404 on a write is GitHub's "token cannot see/write this" answer.
        return "queued", (
            f"write rejected (HTTP {put['status']}: {reason}) — the token "
            "has no contents:write on menno420/websites; entry stays "
            "queued (mint the PAT per docs/owner/OWNER-ACTIONS.md, then "
            "retry)"
        )
    if put["status"] == 409:
        return "queued", (
            f"write conflict (HTTP 409: {reason}) — the ref moved under "
            "us; retry re-reads and re-appends"
        )
    if put["status"] == 422:
        return "failed", (
            f"write rejected as invalid (HTTP 422: {reason}) — a retry "
            "will not help without change (branch protection on "
            f"{ref!r} is one known cause)"
        )
    if put["ok"]:
        return "queued", (
            "the API answered success but carried NO commit SHA — refusing "
            "to claim a commit that cannot be verified; entry stays queued"
        )
    return "queued", (
        f"write failed ({reason}) — transient; entry stays queued, retry"
    )


# --- branch + auto-PR (the one writeback path, Q2=b) -----------------------
_PR_BODY = (
    "Runtime-generated owner writeback (ORDER 020 machinery, gated "
    "`/owner/queue`). The owner authored this on the live control-plane; the "
    "engine committed it to this `claude/owner-writeback-*` branch and opened "
    "this PR so it lands the ruleset-safe way — main moves by PR only.\n\n"
    "The diff is **control/**-only**, so the CI control fast-lane grades it "
    "green with no session card, and the `claude/*` head arms auto-merge. If "
    "the auto-merge-enabler does not arm it, the host-automerge-extras sweep "
    "(cron) picks it up.\n\nConsole audit entry #{id} · action: {action}."
)


async def _open_pr(
    repo: str, entry: dict, head: str, base: str, token: str
) -> dict:
    """Open (or, on a retry, re-find) the auto-merging PR for ``head``.

    Returns ``{ok, number, url}`` on success, or ``{ok: False, error}`` — the
    caller keeps the entry queued so nothing is falsely claimed."""
    payload = {
        "title": _commit_message(entry),
        "head": head,
        "base": base,
        "body": _PR_BODY.format(id=entry["id"], action=entry["action"]),
        "draft": False,
    }
    res = await github.api_request(
        "POST", f"/repos/{repo}/pulls", json_body=payload, token=token
    )
    if res["ok"] and isinstance(res["data"], dict) and res["data"].get("html_url"):
        return {
            "ok": True,
            "number": res["data"].get("number") or 0,
            "url": res["data"]["html_url"],
        }
    # A PR for this head may already exist (a prior attempt opened it) — 422 is
    # GitHub's "a pull request already exists" answer; re-find it rather than
    # claim a failure.
    if res["status"] == 422:
        existing = await github.api_request(
            "GET",
            f"/repos/{repo}/pulls?head={config.OWNER}:{head}&base={base}"
            "&state=open",
            token=token,
        )
        if existing["ok"] and isinstance(existing["data"], list) and existing["data"]:
            pr0 = existing["data"][0]
            return {
                "ok": True,
                "number": pr0.get("number") or 0,
                "url": pr0.get("html_url", ""),
            }
    reason = res.get("error") or f"HTTP {res.get('status')}"
    return {
        "ok": False,
        "error": (
            f"the commit landed on branch {head} but opening the auto-merge "
            f"PR failed (HTTP {res.get('status')}: {reason}) — entry stays "
            "queued; a retry re-uses the branch and re-opens the PR"
        ),
    }


async def _commit_branch_pr(entry: dict, token: str) -> dict:
    """Default path (Q2=b): commit the append to a per-submit
    `claude/owner-writeback-<id>` branch, then open an auto-merging PR into the
    base. ``committed`` is claimed ONLY when the branch commit SHA is verified
    AND the PR is open; every other outcome stays honestly ``queued``."""
    entry_id = entry["id"]
    path = target_path(entry["action"])
    base = branch()
    wb_branch = writeback_branch_name(entry)
    repo = f"{config.OWNER}/{WRITEBACK_REPO}"

    # 1) Resolve the base branch head SHA (the branch-point for the new ref).
    ref_res = await github.api_request(
        "GET", f"/repos/{repo}/git/ref/heads/{base}", token=token
    )
    base_sha = ""
    if ref_res["ok"] and isinstance(ref_res["data"], dict):
        base_sha = (ref_res["data"].get("object") or {}).get("sha") or ""
    if not base_sha:
        reason = ref_res.get("error") or f"HTTP {ref_res.get('status')}"
        _update_entry(
            entry_id, status="queued", branch=wb_branch,
            error=(
                f"could not resolve {base} head ({reason}) — entry stays "
                "queued, retry"
            ),
        )
        return get_entry(entry_id)  # type: ignore[return-value]

    # 2) Ensure the writeback branch exists (create at the base head). A 422
    #    means a prior attempt already created it — treat as OK and read the
    #    file FROM the branch below so we never double-append.
    create = await github.api_request(
        "POST", f"/repos/{repo}/git/refs",
        json_body={"ref": f"refs/heads/{wb_branch}", "sha": base_sha},
        token=token,
    )
    if not create["ok"] and create["status"] != 422:
        status, msg = _classify_write_failure(create, wb_branch)
        _update_entry(entry_id, status=status, branch=wb_branch, error=msg)
        return get_entry(entry_id)  # type: ignore[return-value]

    # 3) Read the target ON THE BRANCH (idempotency: a prior attempt's append
    #    shows here) and compose/commit unless it is already present.
    state, old_text, sha, reason = await _read_target(path, wb_branch, token)
    if state == "error":
        _update_entry(entry_id, status="queued", branch=wb_branch, error=reason)
        return get_entry(entry_id)  # type: ignore[return-value]

    if _entry_marker(entry) in old_text:
        # A prior attempt already committed this entry's append to the branch —
        # do NOT double-append; verify the branch head SHA and go open the PR.
        head_res = await github.api_request(
            "GET", f"/repos/{repo}/git/ref/heads/{wb_branch}", token=token
        )
        commit_sha = ""
        if head_res["ok"] and isinstance(head_res["data"], dict):
            commit_sha = (head_res["data"].get("object") or {}).get("sha") or ""
        commit_url = (
            f"https://github.com/{config.OWNER}/{WRITEBACK_REPO}"
            f"/commit/{commit_sha}"
        )
        if not commit_sha:
            _update_entry(
                entry_id, status="queued", path=path, branch=wb_branch,
                error=(
                    f"the append is on branch {wb_branch} but its commit SHA "
                    "could not be verified — entry stays queued, retry"
                ),
            )
            return get_entry(entry_id)  # type: ignore[return-value]
    else:
        body: dict[str, Any] = {
            "message": _commit_message(entry),
            "content": _b64(_compose(entry, old_text)),
            "branch": wb_branch,
        }
        if sha:
            body["sha"] = sha
        put = await github.api_request(
            "PUT", _contents_api_path(path), json_body=body, token=token
        )
        commit_sha, commit_url = _extract_commit(put)
        if not commit_sha:
            status, msg = _classify_write_failure(put, wb_branch)
            _update_entry(
                entry_id, status=status, path=path, branch=wb_branch, error=msg
            )
            return get_entry(entry_id)  # type: ignore[return-value]

    # 4) Open (or re-find) the auto-merging PR. Only now is the writeback
    #    'committed' — a landed branch commit whose PR is open.
    pr = await _open_pr(repo, entry, wb_branch, base, token)
    if not pr["ok"]:
        _update_entry(
            entry_id, status="queued", path=path, branch=wb_branch,
            commit_sha=commit_sha, error=pr["error"],
        )
        return get_entry(entry_id)  # type: ignore[return-value]

    _update_entry(
        entry_id, status="committed", path=path, branch=wb_branch,
        commit_sha=commit_sha, commit_url=pr["url"],
        pr_number=pr["number"], pr_url=pr["url"], error="",
    )
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
        "base": branch(),
        # Back-compat alias — the base branch the writeback PR merges into.
        "branch": branch(),
        "branch_prefix": branch_prefix(),
        "repo": f"{config.OWNER}/{WRITEBACK_REPO}",
        "inbox_path": INBOX_PATH,
        "notes_path": NOTES_PATH,
        "entries": len(list_entries(limit=1000)),
    }
