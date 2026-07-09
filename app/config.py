"""Configuration for the control-plane site.

Everything runtime-tunable comes from env vars (documented in docs/site.md):
  GITHUB_TOKEN        PAT used for the GitHub REST API (read scopes; admin:repo
                      needed only for the secrets panel — degrades to "unknown").
                      The PUBLIC board renders a secrets count only, never the
                      individual names; the gated /owner area un-masks them.
  SITE_PASSWORD       shared secret gating ONLY the /owner area (HTTP Basic, any
                      username). The whole public site stays credential-free; if
                      this is unset the /owner routes fail closed (503) while the
                      public site keeps working.
  PORT                bind port (Railway injects this; default 8000).
  GITHUB_API_BASE     REST base URL (default https://api.github.com; override
                      for testing behind restricted egress).
  GITHUB_RAW_BASE     raw-content base (default https://raw.githubusercontent.com).
  CACHE_TTL_SECONDS   server-side GitHub cache TTL (default 180 = 3 minutes).
"""

import os

OWNER = "menno420"

GITHUB_API_BASE = os.environ.get("GITHUB_API_BASE", "https://api.github.com").rstrip("/")
GITHUB_RAW_BASE = os.environ.get(
    "GITHUB_RAW_BASE", "https://raw.githubusercontent.com"
).rstrip("/")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
# Gates ONLY the /owner area (see app/owner.py). The public site never reads it.
SITE_PASSWORD = os.environ.get("SITE_PASSWORD", "")
CACHE_TTL_SECONDS = int(os.environ.get("CACHE_TTL_SECONDS", "180"))

# Per-repo knowledge the API cannot tell us: what the required checks are
# *supposed* to be (seeded from superbot docs/operations/repo-settings-state.md,
# the hand-maintained ledger this board generalizes), which checks are red by
# design, and where each repo keeps its journal material.
REPOS: dict = {
    "superbot": {
        "expected_required_checks": ["Code Quality", "CodeQL"],
        "advisory_checks": ["codex-final-review"],
        "red_by_design": {},
        "automerge_enabler_expected": True,
        "journal": {
            "sessions_dir": ".sessions",
            "docs": [
                ("Question router", "docs/owner/maintainer-question-router.md"),
                ("Living ledger (current-state)", "docs/current-state.md"),
                ("Journal guidebook", ".session-journal.md"),
                ("Journal archive", ".session-journal-archive.md"),
            ],
            "note": (
                "No docs/decisions.md by design — decision provenance lives in "
                "the question router (Q-NNNN) and the living ledger."
            ),
        },
    },
    "superbot-next": {
        "expected_required_checks": [
            "tests",
            "checkers",
            "lockfile-fresh",
            "pip-audit",
            "gate",
        ],
        "advisory_checks": [],
        # THE known trap: the golden-parity `report` job is red until parity is
        # reached, BY DESIGN. Annotate, never count as broken.
        "red_by_design": {
            "report": "red-until-parity BY DESIGN (golden-parity gap tracker), not a failure"
        },
        "automerge_enabler_expected": False,
        "journal": {
            "sessions_dir": ".sessions",
            "docs": [
                ("Decision ledger", "docs/decisions.md"),
                ("Question router", "docs/question-router.md"),
                ("Living ledger (current-state)", "docs/current-state.md"),
            ],
            "note": (
                "current-state.md may still be unfilled kit template — shown "
                "as-is, honestly."
            ),
        },
    },
    "substrate-kit": {
        "expected_required_checks": [
            "Kit test suite",
            "Cold-adoption smoke (adopt + check --strict)",
        ],
        "advisory_checks": [],
        "red_by_design": {},
        "automerge_enabler_expected": False,
        "journal": {
            "sessions_dir": None,
            "docs": [],
            "note": (
                "No docs/ tree and no .sessions/ at all — journal data for this "
                "repo is its PR and commit history."
            ),
        },
    },
    "websites": {
        "expected_required_checks": [],  # repo brand-new; none configured yet
        "advisory_checks": [],
        "red_by_design": {},
        "automerge_enabler_expected": False,
        "journal": {
            "sessions_dir": ".sessions",
            "docs": [
                ("Decision ledger", "docs/decisions.md"),
                ("Question router", "docs/question-router.md"),
                ("Living ledger (current-state)", "docs/current-state.md"),
            ],
            "note": "Full substrate-kit set planted by PR #1.",
        },
    },
}
