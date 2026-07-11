"""Domain layer for the review service — data loading, chart geometry, content.

Layering (the repo's binding architecture): routes (``app.py``) import this
module; this module imports nothing from routes or templates. There is no
client layer — the service is deliberately network-free: its one data source
is the committed ``data/snapshot.json`` baked from the real repo at build time
(see ``gen_snapshot.py`` for why runtime reads are impossible under Railway's
Root Directory deploy model).

Two kinds of content live here:

- **Generated numbers** — loaded from the snapshot, gracefully absent when the
  file is missing/corrupt (pages render an honest banner, never invented data).
- **Curated narrative** — the process/successes/problems record, written from
  the repo's own committed evidence (retro docs, session cards, capability
  ledger, decision ledger) with a citation on every claim. Curation here means
  selection and plain-English explanation for an outside reviewer, not spin:
  the problems list leads and is as specific as the successes list.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
SNAPSHOT_PATH = BASE_DIR / "data" / "snapshot.json"

REPO_URL = "https://github.com/menno420/websites"


def pr(num: int) -> str:
    """Deep link to a PR on the websites repo."""
    return f"{REPO_URL}/pull/{num}"


def blob(path: str) -> str:
    """Deep link to a file on the websites repo at main."""
    return f"{REPO_URL}/blob/main/{path}"


# ---------------------------------------------------------------------------
# Snapshot loading — honest degradation, never invented numbers.
# ---------------------------------------------------------------------------
def load_snapshot(path: Path | None = None) -> dict[str, Any]:
    """Load the committed snapshot. Returns ``{ok, error, data}``; a missing or
    corrupt file yields ``ok=False`` and empty data — pages banner honestly.

    ``path`` defaults to the module-level ``SNAPSHOT_PATH`` at CALL time (not
    definition time) so tests can monkeypatch the attribute."""
    if path is None:
        path = SNAPSHOT_PATH
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"ok": False, "error": "snapshot file missing (data/snapshot.json)", "data": {}}
    except (json.JSONDecodeError, OSError) as exc:
        return {"ok": False, "error": f"snapshot unreadable: {exc}", "data": {}}
    if not isinstance(data, dict) or "days" not in data or "totals" not in data:
        return {"ok": False, "error": "snapshot malformed (missing days/totals)", "data": {}}
    return {"ok": True, "error": "", "data": data}


# ---------------------------------------------------------------------------
# Chart geometry — computed server-side so templates stay dumb.
# Mark specs per the program dataviz rules: columns <= 24px wide, 4px rounded
# data-end at the top, square at the baseline, single-hue magnitude encoding
# (color comes from the ds token --sb-chart-mark), text in ink tokens.
# ---------------------------------------------------------------------------
def column_chart(
    points: list[tuple[str, int]],
    *,
    height: int = 180,
    col_width: int = 24,
    gap: int = 56,
    pad_top: int = 26,
    pad_bottom: int = 24,
) -> dict[str, Any]:
    """Geometry for a small single-series column chart (one bar per day).

    Returns a dict of ready-to-render SVG coordinates. Pure and deterministic:
    unit-tested directly. Empty input -> ``{"empty": True}``.
    """
    if not points:
        return {"empty": True, "columns": [], "width": 0, "height": height}
    max_v = max(v for _, v in points) or 1
    plot_h = height - pad_top - pad_bottom
    columns = []
    for i, (label, value) in enumerate(points):
        h = round(plot_h * value / max_v) if value > 0 else 0
        x = gap // 2 + i * (col_width + gap)
        y = pad_top + (plot_h - h)
        columns.append(
            {
                "label": label,
                "value": value,
                "x": x,
                "y": y,
                "w": col_width,
                "h": h,
                "cx": x + col_width / 2,
                "baseline": pad_top + plot_h,
            }
        )
    width = gap // 2 + len(points) * (col_width + gap)
    return {
        "empty": False,
        "columns": columns,
        "width": width,
        "height": height,
        "baseline": pad_top + plot_h,
        "max": max_v,
    }


def growth_charts(snapshot_data: dict[str, Any]) -> list[dict[str, Any]]:
    """The three growth charts, from the snapshot's per-day rows."""
    days = snapshot_data.get("days") or []

    def series(key: str) -> list[tuple[str, int]]:
        return [
            (d.get("date", "?")[5:], int(d.get(key, 0) or 0))
            for d in days
            if isinstance(d, dict)
        ]

    charts = [
        {
            "id": "prs",
            "title": "Pull requests merged per day",
            "note": "Unique PR numbers referenced by merge commits on main, grouped by UTC merge date.",
            "chart": column_chart(series("prs_merged")),
        },
        {
            "id": "sessions",
            "title": "Agent session cards per day",
            "note": "Committed .sessions/ cards by filename date — one card per working session, required by CI.",
            "chart": column_chart(series("session_cards")),
        },
        {
            "id": "tests",
            "title": "Test functions at end of day",
            "note": "def test_ count across all services' suites at each day's last commit — the safety net's growth curve.",
            "chart": column_chart(series("test_functions_eod")),
        },
    ]
    return charts


# ---------------------------------------------------------------------------
# Curated narrative — every claim cites committed evidence.
# ---------------------------------------------------------------------------

# Who's who, for an outside reader.
GLOSSARY: list[tuple[str, str]] = [
    ("Owner", "The one human. He designs and directs by conversation; he cannot code. Every line of code here was written by Claude agents and cross-checked by other agents."),
    ("Lane / Project", "One Claude Project bound to one repo (or one area of a shared repo). This repo — websites — is one lane of a ~10-lane fleet."),
    ("Manager / fleet-manager", "A coordinating lane (repo menno420/fleet-manager) that dispatches orders to every lane and aggregates their reports."),
    ("The bus", "Committed git files as the only inter-agent channel. Sessions cannot talk to each other; control/inbox.md (orders in) and control/status.md (heartbeat out) are the entire protocol."),
    ("Order", "A numbered instruction block the manager appends to control/inbox.md — priority, what to do, why, and a checkable done-when."),
    ("Heartbeat", "control/status.md, overwritten by each session as its deliberate last step: phase, health, last shipped PR, blockers, orders acked/done, asks for the owner."),
    ("Session card", "A per-session log in .sessions/, committed born-red (status: in-progress) as the session's first commit and flipped complete as its last — CI blocks the merge until it flips."),
    ("Born-red", "The designed state where a PR's first CI run fails on purpose: the in-progress session card holds the merge until the close-out is written. A red first run is the gate working."),
    ("Work ladder", "What a session does when it wakes, in priority order: inbox orders, then queued work, then the ideas backlog, then contained self-initiated improvements, then honest upkeep."),
    ("Continuous mode", "A session chain that schedules its own next wake (a timer message ~every 30 minutes), landing one full-ceremony slice per wake — 26 slices plus 3 rescues in one 17-hour run."),
    ("Substrate kit", "A vendored workflow engine (bootstrap.py) that enforces the ceremony: doc hygiene, session-card markers, the born-red gate, heartbeat grammar. Upgraded release-by-release like any dependency."),
    ("Quality gate", "The one required CI check on main. Runs the kit checker plus every service's test suite; control-file-only diffs ride a validated fast lane."),
]

# The landing path — one shippable unit of work, start to finish.
LANDING_PATH: list[tuple[str, str]] = [
    ("Wake", "A session starts — routine-fired on a 4-hour cron, chained by a self-scheduled timer, or opened by the owner. First act: git pull, read control/inbox.md at HEAD."),
    ("Claim", "Before building, the session claims the work on main (a claimed-by line in its own heartbeat, or a claim file) so parallel sessions don't execute the same order twice — a failure that actually happened and produced this rule."),
    ("Card, born-red", "First commit on the branch: a session card with status in-progress. CI now refuses to merge this PR — visible, on-purpose red until the work is done and written up."),
    ("Build + verify", "The work itself, plus proof: the full multi-service pytest suite and the kit's strict checker must pass locally before push."),
    ("READY PR", "A real pull request into main. The required quality check runs the whole ceremony: kit gate, session-card gate, safety guards, every service's tests."),
    ("Flip + merge", "The card flips to complete (with the real PR number) as the last code step; CI goes green; squash-merge. Main is always deployable because merge IS the deploy."),
    ("Deploy + prove", "Railway auto-deploys main. The session verifies live: every service's /version endpoint must equal the new main HEAD (a script polls until converged). 'Pushed' or 'deployed' is never recorded without proof."),
    ("Heartbeat", "Final step: overwrite control/status.md — what shipped, health, what's next, anything only the owner can do. The next session, and the manager, read the state from the repo, not from memory."),
]

SERVICES: list[dict[str, str]] = [
    {
        "name": "control-plane",
        "dir": "app/",
        "url": "https://control-plane-production-abb0.up.railway.app",
        "desc": "The fleet's mission control: readiness board, per-lane heartbeat view (/fleet), orders (/orders), owner to-do queue (/queue), cross-repo activity — all live from the GitHub API.",
    },
    {
        "name": "botsite",
        "dir": "botsite/",
        "url": "https://botsite-production-cfd7.up.railway.app",
        "desc": "Public marketing/reference site for the owner's Discord bot, rendering the bot repo's committed site.json.",
    },
    {
        "name": "dashboard",
        "dir": "dashboard/",
        "url": "https://dashboard-production-a91b.up.railway.app",
        "desc": "Read-only developer dashboard over the bot's committed inventory feeds; its live-bot write panel is a deliberate, labeled stub.",
    },
    {
        "name": "review",
        "dir": "review/",
        "url": "",
        "desc": "This site — the program explaining itself to an outside reviewer, from its own committed record.",
    },
]

# Problems — honest, specific, evidenced. This list leads the site's story:
# a review surface that hides failures is worthless (the ORDER 011 retro's
# own framing). Each entry: what happened, what it cost, what changed.
PROBLEMS: list[dict[str, Any]] = [
    {
        "title": "A gate that was supposed to block merges let an empty PR through",
        "what": "The session-card gate is meant to hold every PR red until its card flips complete. On day one, PR #19 auto-merged effectively EMPTY on its in-progress card alone — the checker never inspected the card's status value, and the card was picked by file mtime, which a fresh CI checkout flattens.",
        "cost": "One meaningless merge on main; more importantly, proof the safety ceremony was decorative until tested.",
        "fix": "Root-caused same day; fixed by adopting the upstream kit v1.0.0 engine plus a diff-aware card-selection step in CI, proven in both directions and pinned by a regression test.",
        "evidence": [("PR #24 (the fix)", pr(24)), ("tests/test_born_red_session_gate.py", blob("tests/test_born_red_session_gate.py"))],
    },
    {
        "title": "A session recorded work as pushed that never left its container",
        "what": "A routine-fired session's git push silently failed (its per-session GitHub grant was never provisioned), yet its own session card recorded the branch as pushed. Hours later the remote had no such branch.",
        "cost": "Stranded work, a misleading record, and a rescue: another lane re-landed the commits from a format-patch (PR #59).",
        "fix": "A standing rule in the capability ledger — NEVER record 'pushed' without proof (push exit 0 AND git ls-remote showing the commit) — plus a landing: line in every heartbeat so stranded work flags on the fleet page instead of hiding.",
        "evidence": [("PR #59 (the rescue)", pr(59)), ("docs/CAPABILITIES.md (the wall, verbatim errors)", blob("docs/CAPABILITIES.md"))],
    },
    {
        "title": "Scheduled wakes are unreliable — one fire stranded its work, one left no trace",
        "what": "The lane's self-armed 4-hourly wake routine fired sessions that lack PR tooling: the 04:03Z fire did real work but could not open a PR (heartbeat rescued verbatim as PR #98); the ~08:00Z fire left no trace at all. GitHub Actions cron is similarly best-effort — a fresh schedule's first fire arrived ~3.4 hours late.",
        "cost": "Silent coverage gaps in unattended operation; the send_later timer chain became the only consistent producer.",
        "fix": "A relay doctrine (any session may land another session's green, control-only work verbatim), attention-first flagging of armed-but-silent routines on /fleet, and a recorded rule: cron timing is ±hours, never gate anything on a slot.",
        "evidence": [("PR #98 (heartbeat rescue)", pr(98)), ("control/README.md (relay doctrine)", blob("control/README.md")), ("docs/retro/self-review-2026-07-11.md", blob("docs/retro/self-review-2026-07-11.md"))],
    },
    {
        "title": "The same cron-arithmetic mistake, repeated five times in writing",
        "what": "Five consecutive heartbeats stated a 17 */6 cron's next slot as '~02:17Z'. Cron anchors to wall-clock hours (00/06/12/18) — the real slot was 06:17Z. Self-caught on the sixth write.",
        "cost": "Five wrong statements in the committed record before anyone noticed; harmless this time, but the failure class (confidently restating an unchecked derivation) is not.",
        "fix": "A cron-slot calculator script with the exact incident pinned as a test, plus a capability-ledger lesson: compute slots from the epoch, never from 'now'.",
        "evidence": [("PR #96 (scripts/cron_slots.py)", pr(96)), ("docs/retro/self-review-2026-07-11.md § 1", blob("docs/retro/self-review-2026-07-11.md"))],
    },
    {
        "title": "Tests with time bombs: a green suite that would have gone red on its own",
        "what": "At 08:45Z a test began failing on an UNTOUCHED tree — its fixed fixture timestamps crossed a staleness threshold against the real wall clock. A guard written the same day found 17 more latent time bombs across 5 test files.",
        "cost": "One live detonation; without the class-wide sweep, every later PR would have gone mystery-red one bomb at a time — poison for unattended runs.",
        "fix": "Injectable clocks (now=) on every age-measuring function, all 17 sites threaded with frozen constants, and an AST-scanning guard test that fails any future age-measuring call without a frozen clock.",
        "evidence": [("PR #111 (defusal)", pr(111)), ("PR #114 (class-wide guard)", pr(114)), ("tests/test_time_discipline.py", blob("tests/test_time_discipline.py"))],
    },
    {
        "title": "The status ledger drifted 17 slices out of date — in the repo that renders drift for a living",
        "what": "docs/current-state.md, the orientation file every session reads second, went stale across 17 rapid slices and carried four claims that were no longer true (wrong kit version, 'the PAT is set', a superseded registry mechanism, an exhausted work pointer).",
        "cost": "Every booting session oriented on partly false state until a dedicated truth sweep fixed it.",
        "fix": "The sweep itself (each correction verified against main HEAD and annotated in place), and 'truth sweep' now exists as a named upkeep rung sessions run when unrouted.",
        "evidence": [("PR #111 (truth sweep)", pr(111)), ("docs/current-state.md", blob("docs/current-state.md"))],
    },
    {
        "title": "Overclaims caught at the door — the review culture working, barely",
        "what": "A session card claimed 'pytest tests/ -> 235 passed' when 235 was the FULL multi-service suite (tests/ alone was 177). Another card pre-wrote its PR number and guessed wrong when a sibling took it. An order-claim matcher matched order id '00' inside a timestamp string.",
        "cost": "Nearly-shipped wrong statements; each was caught pre-merge by this program's own checks and habits, not by luck — but each got as far as a written claim.",
        "fix": "Cards now state both suite numbers; PRs are opened before their number is written anywhere; the matcher was rewritten against tokenized ids with the boundary case pinned as a test.",
        "evidence": [("PR #109 close-out", pr(109)), ("PR #77 (matcher fix)", pr(77)), ("docs/retro/self-review-2026-07-11.md § 1", blob("docs/retro/self-review-2026-07-11.md"))],
    },
    {
        "title": "Real walls: things agents here verifiably cannot do",
        "what": "Direct api.github.com calls are proxy-blocked (GitHub goes through MCP tools, scoped per session). Branch deletion 403s on every path. Some session kinds cannot open PRs at all. Creating Railway resources is policy-forbidden without the owner's explicit go. The deployed board runs tokenless on GitHub's anonymous 60-requests/hour ceiling until the owner mints a PAT.",
        "cost": "Stale branches accumulate until a human deletes them; routine-fired sessions need rescue landings; two owner asks have been open for days on the owner's scarcest resource — his attention.",
        "fix": "Every wall lives in docs/CAPABILITIES.md with its exact error text and workaround, under a discovery rule: check the ledger, check the environment, attempt once and capture the error, append the finding — so no session re-pays a known wall.",
        "evidence": [("docs/CAPABILITIES.md", blob("docs/CAPABILITIES.md")), ("docs/owner/OWNER-ACTIONS.md", blob("docs/owner/OWNER-ACTIONS.md"))],
    },
]

# Successes — same discipline: specific, evidenced.
SUCCESSES: list[dict[str, Any]] = [
    {
        "title": "Three public services shipped and deployed in the repo's first day",
        "what": "From an empty repo at dawn to three live Railway services by evening: the control-plane board, the bot marketing site, and the developer dashboard — 45 PR merges on the first UTC day, each through the full branch → card → PR → CI → squash-merge ceremony (3 more PRs closed unmerged, casualties of early parallel-checkout churn the retro documents).",
        "evidence": [("PR #2 (control-plane)", pr(2)), ("PR #7 (botsite)", pr(7)), ("PR #8 (dashboard)", pr(8)), ("gen-1 final retro", blob("docs/retro/gen1-final-retro-2026-07-09.md"))],
    },
    {
        "title": "The system catches its own failures",
        "what": "The board's deploy-drift cell (built as ORDER 001) immediately exposed that the dashboard service was silently serving a stale build — its deploy trigger had never existed. Later, a scheduled healthcheck's very second run caught an upstream registry migration that had broken the fleet page to zero lanes, and the same wake shipped the repoint. Both were found by surfaces this program built to watch itself.",
        "evidence": [("PR #26 (drift cell)", pr(26)), ("PR #29 (trigger root-cause)", pr(29)), ("PR #102 (registry repoint)", pr(102))],
    },
    {
        "title": "An unattended 17-hour chain landed 26 slices and 3 rescues",
        "what": "A continuous-mode session chain — each wake self-scheduling the next — ran overnight and through the morning landing one verified slice per wake: seven new fleet-visibility pages, JSON shape contracts, board chips, nav hardening, five kit upgrades, and three rescues of other sessions' stranded work. The owner slept; the record shows every step.",
        "evidence": [("heartbeat at slice 26", blob("control/status.md")), ("self-review of the window", blob("docs/retro/self-review-2026-07-11.md"))],
    },
    {
        "title": "Gates got harder faster than work got faster",
        "what": "The safety net grew from 0 to 226 test functions in three days, and the gates themselves became test subjects: the born-red gate has a both-directions regression test, the CI fast lane's control gates are driven end-to-end against the real checker CLI, JSON payloads are pinned by shape contracts, and a meta-guard AST-scans the test suite for time discipline.",
        "evidence": [("tests/test_born_red_session_gate.py", blob("tests/test_born_red_session_gate.py")), ("PR #127 (gate suite tests)", pr(127)), ("PR #114 (time-discipline guard)", pr(114))],
    },
    {
        "title": "Sessions learned to arm their own clocks",
        "what": "Told that routine creation might be possible, a worker session self-armed the lane's 4-hourly wake trigger, confirmed the first fire from inside the fired session, and withdrew the fallback ask to the owner — an owner-click saved by an agent verifying its own capability instead of assuming a wall.",
        "evidence": [("ORDER 008 record", blob("control/inbox.md")), ("docs/CAPABILITIES.md append log", blob("docs/CAPABILITIES.md"))],
    },
    {
        "title": "Honesty is enforced, not aspirational",
        "what": "Every degraded state renders as itself: an unset token shows 'unknown (needs token)', a missing feed shows a banner, a stub is badged as a stub, secret names are masked to a count on the public board. Tests assert the absence of faked data. The fleet's own retro doctrine: a review that hides failures is worthless — the ORDER 011 self-review leads with five mistakes, each cited.",
        "evidence": [("ORDER 011 self-review", blob("docs/retro/self-review-2026-07-11.md")), ("PR #12 (secrets masked to a count)", pr(12))],
    },
    {
        "title": "Knowledge survives session death",
        "what": "Sessions are amnesiac — everything durable lives in the repo: a capability ledger with exact error texts, a decision ledger, an ideas backlog with dedup discipline, succession docs that booted generation 2 from main alone, and session cards for all 72 sessions. The gen-1 retro's strongest finding: the orientation chain reconstructed the whole project without any chat history.",
        "evidence": [("docs/CAPABILITIES.md", blob("docs/CAPABILITIES.md")), ("succession pack", blob("docs/succession/next-boot-2026-07-09.md")), (".sessions/", f"{REPO_URL}/tree/main/.sessions")],
    },
]

# Growth timeline — the milestone spine under the charts.
MILESTONES: list[dict[str, str]] = [
    {"date": "2026-07-09 am", "title": "Repo born; workflow engine adopted; control-plane built", "detail": "Intent commit, substrate-kit adoption (PR #1), the readiness board + journal browser (PR #2), deployed to a fresh Railway project (PR #3)."},
    {"date": "2026-07-09 pm", "title": "Botsite + dashboard rebuilt and deployed; sites made public", "detail": "Two more services through the same ceremony (PRs #7, #8); auth dropped on the owner's word with secret names masked to a count (PR #12); the gated /owner overlay (PR #14)."},
    {"date": "2026-07-09 late", "title": "The gate leak found and fixed; fleet coordination adopted", "detail": "PR #19's empty merge exposed the born-red leak, fixed via kit v1.0.0 (PR #24); the control/ bus adopted; /fleet renders every lane's heartbeat (PR #35). Gen-1 winds down after its 46-PR day (43 merged, 3 closed superseded) leaving succession docs a fresh generation can boot from."},
    {"date": "2026-07-10", "title": "Gen-2 boots from main alone; sessions arm their own wakes", "detail": "Walking skeleton proves the landing path (PR #51); /queue + /environments ship (PR #53); ORDER 008 self-arms the 4-hourly routine; the stranded-push incident and its rescue (PR #59) produce the proof-of-push rule; continuous mode begins (~PR #64)."},
    {"date": "2026-07-11", "title": "The 26-slice chain: fleet visibility wave + hardening", "detail": "/orders, /reviews, /projects, JSON contracts, board chips, nav guard; the healthcheck cron catches the registry break (fixed, PR #102); the time-bomb class defused (PRs #111/#114); fast-lane control gates (PR #125/#127); kit upgraded five versions; ORDER 011 self-review lands."},
]

# Overview stat tiles (labels only — values come from the snapshot).
STAT_TILES: list[tuple[str, str, str]] = [
    ("prs_merged", "pull requests merged", "each through the full CI ceremony"),
    ("session_cards", "agent sessions on record", "one committed card per session"),
    ("test_functions", "test functions", "grown from zero, all green at HEAD"),
    ("services", "live services in this repo", "independently deployed from one main"),
]


def overview_stats(snapshot_data: dict[str, Any]) -> list[dict[str, Any]]:
    totals = snapshot_data.get("totals") or {}
    tiles = []
    for key, label, sub in STAT_TILES:
        value = totals.get(key)
        if value is None:
            continue  # honest absence — no tile without a real number
        tiles.append({"key": key, "label": label, "sub": sub, "value": value})
    return tiles
