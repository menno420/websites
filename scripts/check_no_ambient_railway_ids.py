#!/usr/bin/env python3
"""Enforcing guard: no code reads the ambient PRODUCTION-BOT Railway IDs.

──────────────────────────────────────────────────────────────────────────────
PROVENANCE / KILL-SWITCH HEADER
  Why:   The agent container carries three ambient env vars —
         RAILWAY_PROJECT_ID / RAILWAY_SERVICE_ID / RAILWAY_ENVIRONMENT_ID —
         that point at the **live production bot** Railway project. Passing any
         of them to a Railway API/CLI call operates on production. This repo's
         services deliberately make **no** Railway calls at all, so any code
         that even *reads* one of those three identifiers from the environment
         is a red flag that a Railway mutation path is being wired against the
         production project. This guard makes that a hard CI failure instead of
         a rule an agent has to remember.
  Added: 2026-07-09 (websites hardening pass, PR #19, [D-0015]).
  Trust: DETERMINISTIC (pure stdlib regex over tracked files) — but still
         UNVERIFIED as a load-bearing gate. Confirm its output against ground
         truth a few times across sessions before trusting its green.
  KILL-SWITCH: if this guard proves noisy or fights real work over several
         sessions, DELETE this file, its test (tests/test_check_no_ambient_
         railway_ids.py), and the `no-ambient-railway-ids` step in
         .github/workflows/quality.yml. It is a disposable convenience guard,
         not architecture — remove it rather than working around it.
──────────────────────────────────────────────────────────────────────────────

What it checks (both must hold; either failing exits non-zero):

  1. CODE SCAN — no tracked NON-markdown file (excluding this script + its test)
     *reads* any of the three ambient IDs from the environment. The env-read
     patterns flagged: os.environ["RAILWAY_PROJECT_ID"], os.environ.get(...),
     os.getenv(...), environ["..."] / environ.get(...), and bare
     `${RAILWAY_PROJECT_ID}` / `$RAILWAY_PROJECT_ID` shell interpolation. Since
     the services never call Railway, ANY such read could reach a Railway
     mutation and is therefore a violation. (The explicit `superbot-websites`
     project/service/environment IDs — the SAFE ones — are hardcoded literals in
     docs, never read from these env vars, so they are not matched.)

  2. DOC ASSERTION — the deployment safety doc(s) still carry the loud warning
     naming the three IDs, so the human-readable rule cannot silently rot.

Usage:  python3 scripts/check_no_ambient_railway_ids.py
Exit 0 = clean; exit 1 = violation(s) printed to stderr.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# The three ambient identifiers that point at the LIVE PRODUCTION BOT project.
AMBIENT_IDS = (
    "RAILWAY_PROJECT_ID",
    "RAILWAY_SERVICE_ID",
    "RAILWAY_ENVIRONMENT_ID",
)

# Files that legitimately mention the identifiers and must NOT be scanned as
# code: this guard, its test, and markdown docs (which quote the rule as a
# warning — that is the whole point of the doc assertion below).
_SELF = "scripts/check_no_ambient_railway_ids.py"
_TEST = "tests/test_check_no_ambient_railway_ids.py"
_CODE_EXCLUDE = {_SELF, _TEST}

# Env-read patterns: an ID reached through the process environment. Matching any
# of these against a code file is the violation.
_IDS_ALT = "|".join(re.escape(i) for i in AMBIENT_IDS)
ENV_READ_PATTERNS = [
    # os.environ["RAILWAY_PROJECT_ID"]  /  environ['RAILWAY_SERVICE_ID']
    re.compile(rf"""environ\s*\[\s*['"](?:{_IDS_ALT})['"]\s*\]"""),
    # os.environ.get("RAILWAY_PROJECT_ID")  /  environ.get('...')
    re.compile(rf"""environ\.get\s*\(\s*['"](?:{_IDS_ALT})['"]"""),
    # os.getenv("RAILWAY_PROJECT_ID")  /  getenv('...')
    re.compile(rf"""getenv\s*\(\s*['"](?:{_IDS_ALT})['"]"""),
    # shell interpolation: ${RAILWAY_PROJECT_ID} or $RAILWAY_PROJECT_ID
    re.compile(rf"""\$\{{?(?:{_IDS_ALT})\b"""),
]

# The doc(s) that must carry the loud warning, and the tokens that prove it does.
SAFETY_DOCS = ("docs/RAILWAY-SAFETY.md", "docs/deployment.md")
REQUIRED_DOC_TOKENS = AMBIENT_IDS  # all three named in the warning


def _tracked_files() -> list[str]:
    """Return git-tracked paths (posix, repo-relative). Falls back to rglob."""
    try:
        out = subprocess.run(
            ["git", "ls-files"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return [line for line in out.stdout.splitlines() if line]
    except (OSError, subprocess.CalledProcessError):
        return [
            p.relative_to(REPO_ROOT).as_posix()
            for p in REPO_ROOT.rglob("*")
            if p.is_file() and ".git/" not in p.as_posix()
        ]


def scan_code(files: list[str] | None = None) -> list[str]:
    """Return violation messages for any code file reading an ambient ID.

    ``files`` defaults to the git-tracked set; tests pass an explicit list so a
    planted (untracked) file can be exercised deterministically.
    """
    violations: list[str] = []
    for rel in files if files is not None else _tracked_files():
        if rel in _CODE_EXCLUDE:
            continue
        if rel.endswith(".md"):  # docs quote the rule as a warning — skip.
            continue
        path = REPO_ROOT / rel
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for pat in ENV_READ_PATTERNS:
                if pat.search(line):
                    violations.append(
                        f"{rel}:{lineno}: reads an ambient production Railway ID "
                        f"from the environment -> {line.strip()!r}"
                    )
                    break
    return violations


def check_doc_warning() -> list[str]:
    """Return messages if no safety doc carries the three-ID warning."""
    for rel in SAFETY_DOCS:
        path = REPO_ROOT / rel
        if not path.exists():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if all(tok in text for tok in REQUIRED_DOC_TOKENS):
            return []  # at least one safety doc carries the full warning.
    return [
        "no safety doc carries the loud warning naming all three ambient IDs "
        f"({', '.join(AMBIENT_IDS)}); expected in one of: {', '.join(SAFETY_DOCS)}"
    ]


def main() -> int:
    violations = scan_code() + check_doc_warning()
    if violations:
        print(
            "check_no_ambient_railway_ids: FAIL — ambient production-bot Railway "
            "IDs must never be read/used by this repo's code.",
            file=sys.stderr,
        )
        for v in violations:
            print(f"  - {v}", file=sys.stderr)
        return 1
    print(
        "check_no_ambient_railway_ids: OK — no code reads the ambient "
        "production Railway IDs; safety doc warning present."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
