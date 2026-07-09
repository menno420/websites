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


def deployed_sha() -> str:
    """The commit SHA this container is actually running.

    Read live from the environment on every call (so Railway's per-deploy value
    is always current). Order: ``RAILWAY_GIT_COMMIT_SHA`` — the deployed commit
    Railway injects automatically — first, then a ``GIT_SHA`` baked at Docker
    build time as a local/fallback source, then empty ("unknown"). No network.
    """
    return (
        os.environ.get("RAILWAY_GIT_COMMIT_SHA")
        or os.environ.get("GIT_SHA")
        or ""
    ).strip()


def version_info(service: str) -> dict:
    """The `/version` JSON payload: which commit a service is running.

    ``sha``/``short`` fall back to the literal string ``"unknown"`` (never an
    empty string) when neither env var is set, so callers and the drift cell can
    detect the unknown state honestly instead of guessing.
    """
    sha = deployed_sha()
    return {
        "service": service,
        "sha": sha or "unknown",
        "short": sha[:8] if sha else "unknown",
    }


# Public `/version` endpoints of the three superbot-websites Railway services.
# The readiness board's websites-row "deploy state" cell compares each service's
# DEPLOYED sha to the websites repo's `main` HEAD. control-plane is THIS app, so
# its deployed sha is read straight from the environment with no network hop
# (url = None); the other two are fetched over their public /version JSON.
SERVICE_DEPLOY_TARGETS: dict = {
    "control-plane": None,
    "botsite": "https://botsite-production-cfd7.up.railway.app/version",
    "dashboard": "https://dashboard-production-a91b.up.railway.app/version",
}

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
        # The kit `quality` gate is now a REQUIRED check on main (owner set the
        # ruleset, 2026-07-09; verified live via PR #18 mergeable_state=blocked
        # while `quality` pended). The board derives the *configured* required
        # checks live from the ruleset/branch-protection; this `expected` list is
        # the ledger side, kept in sync so the row stops reading "none required".
        "expected_required_checks": ["quality"],
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

# Fleet-coordination lanes (the /fleet heartbeat page, D-0021).
#
# The fleet protocol has each Project write `control/status*.md` in its OWN repo;
# `/fleet` renders every lane's heartbeat as one glanceable screen. This list is
# the app-side copy of the canonical lane registry the MANAGER keeps in
# `menno420/superbot` → `docs/eap/fleet-manifest.md` (one row per Project). It is
# kept in sync by hand until/unless the page parses that manifest live — a
# drift-risk flagged to the owner (see docs/site.md § /fleet). Each lane names
# the repo + the status file to render (some repos hold >1 lane via
# `status-<lane>.md`, e.g. the shared superbot-games cohabitation experiment; the
# SuperBot coordinator spans two repos but writes its heartbeat to superbot-next,
# so the bare `superbot` lane is expected to have no own status file — an honest
# absence, not an error). `stale_hours` is the heartbeat-freshness threshold: an
# `updated:` older than this badges the lane stale (the manager treats a stale
# heartbeat as a dark Project).
FLEET_STALE_HOURS = int(os.environ.get("FLEET_STALE_HOURS", "12"))

FLEET_LANES: list = [
    {
        "lane": "superbot",
        "repo": "superbot",
        "status_path": "control/status.md",
        "model": "unknown",
        "note": "SuperBot coordinator (superbot + superbot-next); its heartbeat "
        "is written to superbot-next, so this repo has no own status file.",
    },
    {
        "lane": "superbot-next",
        "repo": "superbot-next",
        "status_path": "control/status.md",
        "model": "unknown",
        "note": "SuperBot coordinator heartbeat (rebuild + game-plugin host).",
    },
    {
        "lane": "substrate-kit",
        "repo": "substrate-kit",
        "status_path": "control/status.md",
        "model": "unknown",
        "note": "kit-lab.",
    },
    {
        "lane": "websites",
        "repo": "websites",
        "status_path": "control/status.md",
        "model": "unknown",
        "note": "this control-plane (dogfood entry).",
    },
    {
        "lane": "trading-strategy",
        "repo": "trading-strategy",
        "status_path": "control/status.md",
        "model": "Opus 4.8",
        "note": "trading-lab (backtesting research; research-only).",
    },
    {
        "lane": "codetool-lab-fable5",
        "repo": "codetool-lab-fable5",
        "status_path": "control/status.md",
        "model": "Fable 5",
        "note": "model-comparison coding arm.",
    },
    {
        "lane": "codetool-lab-opus4.8",
        "repo": "codetool-lab-opus4.8",
        "status_path": "control/status.md",
        "model": "Opus 4.8",
        "note": "model-comparison coding arm (identical brief; only the model differs).",
    },
    {
        "lane": "codetool-lab-sonnet5",
        "repo": "codetool-lab-sonnet5",
        "status_path": "control/status.md",
        "model": "Sonnet 5",
        "note": "model-comparison coding arm (third arm).",
    },
    {
        "lane": "superbot-games · mining",
        "repo": "superbot-games",
        "status_path": "control/status-mining.md",
        "model": "default",
        "note": "game-mining lane (superbot-games shared-repo cohabitation).",
    },
    {
        "lane": "superbot-games · exploration",
        "repo": "superbot-games",
        "status_path": "control/status-exploration.md",
        "model": "default",
        "note": "game-exploration lane (superbot-games shared-repo cohabitation).",
    },
]
