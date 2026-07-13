"""Questions-ledger bake for the review service — one call, merge, fail-soft.

Fills ``review/data/questions.json`` (the /questions asked → answered ledger)
from this repo's own GitHub issues, so the bake — not a session — is what
notices a reviewer question exists. One REST call, hard-capped:

- ``GET /repos/{owner}/{repo}/issues?state=all&per_page=100`` — first page
  only, no pagination walk (100 reviewer questions would be a good problem).

Intake convention (matches the ledger note + the 'Ask about this' links): an
issue whose TITLE contains ``[program-review]`` (case-insensitive) is a
reviewer question. PR objects (the issues API interleaves them, marked by a
``pull_request`` key) are excluded. Each match maps to a ledger record —
``asked`` (created_at date), ``title``, ``url``, ``status`` (open/closed).

Merge, keyed by issue url, into the COMMITTED file — never a rebuild:

- existing records keep their position and every hand-written field
  (``answer_url``/``answer_label`` above all — answers stay human);
- the bake refreshes an existing record's ``status`` from the live issue
  state UNLESS the record carries a truthy ``status_override`` (the hand's
  way to pin a status the issue state shouldn't clobber);
- new records append after the existing ledger, oldest-asked first;
- hand-written records whose url no longer matches an issue are untouched;
- the file's honest ``note`` stays; ``updated`` refreshes only on change.

Auth: ``GITHUB_TOKEN`` from the environment when present (the scheduled
``review-bake`` workflow passes the Actions token); otherwise anonymous.

Fail-soft (unattended cron): ANY failure — HTTP error, timeout, bad JSON,
unexpected shape, unreadable committed file — leaves the committed
questions.json byte-identical and exits 0. A no-change run also writes
nothing, so the bake's diff stays honest (no daily stamp-only churn).

Advisory (every run with a readable ledger): records whose ``status`` is
``closed`` but whose ``answer_url`` is missing get one ``ADVISORY:`` line
each — a question closed without its promised published answer nags the
bake log instead of rotting silently as "closed / pending".

    python3 review/gen_questions.py
"""

from __future__ import annotations

import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

OWNER = "menno420"
REPO = "websites"
DATA_DIR = Path(__file__).resolve().parent / "data"
OUT_PATH = DATA_DIR / "questions.json"
API = "https://api.github.com"
TIMEOUT = 20
TITLE_MARKER = "[program-review]"


def _api(path: str) -> tuple[Any | None, dict[str, str], str]:
    """(json_body, headers, "") on success; (None, {}, reason) on failure."""
    req = urllib.request.Request(
        f"{API}{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "websites-review-bake",
        },
    )
    token = (os.environ.get("GITHUB_TOKEN") or "").strip()
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:  # noqa: S310
            body = json.loads(resp.read().decode("utf-8", errors="replace"))
            return body, dict(resp.headers.items()), ""
    except urllib.error.HTTPError as exc:
        return None, {}, f"HTTP {exc.code}"
    except Exception as exc:  # noqa: BLE001 — fail-soft bake, reason recorded
        return None, {}, f"{type(exc).__name__}: {exc}"


def fetch_issues() -> tuple[list[dict[str, Any]] | None, str]:
    """One capped call for this repo's issues (all states, first page only)."""
    body, _, err = _api(f"/repos/{OWNER}/{REPO}/issues?state=all&per_page=100")
    if err:
        return None, err
    if not isinstance(body, list):
        return None, "unexpected API shape (issues list expected)"
    return body, ""


def is_review_question(issue: Any) -> bool:
    """A real issue (not a PR object) whose title carries the intake marker."""
    if not isinstance(issue, dict) or "pull_request" in issue:
        return False
    return TITLE_MARKER in str(issue.get("title") or "").lower()


def issue_record(issue: dict[str, Any]) -> dict[str, Any]:
    """Map one matching issue to a ledger record (the template's fields)."""
    created = str(issue.get("created_at") or "")
    return {
        "asked": created[:10],  # 2026-07-13T…Z → 2026-07-13
        "title": str(issue.get("title") or "").strip(),
        "url": str(issue.get("html_url") or ""),
        "status": "closed" if str(issue.get("state") or "open") == "closed" else "open",
    }


def unanswered_closed(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Records whose issue closed without a hand-written answer link.

    The sync flips ``status`` from the live issue state but never writes
    answers — so a closed-but-unanswered record is the ledger silently
    breaking its own promise. Pure read of the given records, no network.
    """
    return [
        rec
        for rec in records
        if str(rec.get("status") or "open") == "closed" and not rec.get("answer_url")
    ]


def advise_unanswered(records: list[dict[str, Any]]) -> None:
    """One loud advisory line per closed-but-unanswered record, every run."""
    for rec in unanswered_closed(records):
        ref = str(rec.get("url") or rec.get("title") or "?")
        print(f"ADVISORY: closed without a published answer: {ref}")


def merge_questions(
    existing: list[dict[str, Any]], issues: list[Any]
) -> list[dict[str, Any]]:
    """Merge live issue intake into the committed ledger, keyed by url.

    Existing records keep their ledger position and every hand-written field;
    only ``status`` is refreshed from the live issue (skipped when the record
    pins it with a truthy ``status_override``). New questions append after
    the existing ledger, oldest-asked first (ties broken by url) so repeated
    bakes are byte-stable.
    """
    incoming = {
        rec["url"]: rec
        for rec in (issue_record(i) for i in issues if is_review_question(i))
        if rec["url"]
    }
    merged: list[dict[str, Any]] = []
    for rec in existing:
        rec = dict(rec)  # never mutate the committed structure in place
        live = incoming.pop(str(rec.get("url") or ""), None)
        if live is not None and not rec.get("status_override"):
            rec["status"] = live["status"]
        merged.append(rec)
    merged.extend(
        sorted(incoming.values(), key=lambda r: (r["asked"], r["url"]))
    )
    return merged


def main() -> int:
    try:
        raw = OUT_PATH.read_text(encoding="utf-8")
        doc = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"questions.json unreadable ({exc}) — questions bake skipped (fail-soft).")
        return 0
    if not isinstance(doc, dict) or not isinstance(doc.get("questions"), list):
        print("questions.json malformed — questions bake skipped (fail-soft).")
        return 0

    issues, err = fetch_issues()
    if issues is None:
        # Nothing real to merge: the committed ledger stays byte-identical —
        # honest absence beats recording this container's proxy errors.
        print(f"issue fetch failed ({err}) — questions bake skipped (fail-soft).")
        advise_unanswered(doc["questions"])
        return 0

    merged = merge_questions(doc["questions"], issues)
    advise_unanswered(merged)
    if merged == doc["questions"]:
        print(f"questions ledger unchanged ({len(merged)} records) — nothing to write.")
        return 0

    doc["questions"] = merged
    doc["updated"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    OUT_PATH.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT_PATH.name}: {len(merged)} records")
    return 0


if __name__ == "__main__":
    sys.exit(main())
