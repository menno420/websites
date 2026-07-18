"""The fleet seat roster: the owner's registry seats in dispatch order.

ONE control-plane source for the seat set — the /prompts library pins its
artifact registry to :data:`SEATS` and the /projects index sorts its seat
cards through :data:`START_ORDER`, so the two surfaces cannot drift apart.
Source of truth upstream is
https://github.com/menno420/fleet-manager/tree/main/projects — if a seat is
added or renamed there, this module is the single place to update.
"""

from __future__ import annotations

# The owner's seat start order (dispatch order, 2026-07-12 ask). Each slot
# is the set of package names (lowercased, "_"→"-") that map to it; the
# FIRST alias is the seat's canonical registry directory name under
# projects/.
START_ORDER: tuple[tuple[str, ...], ...] = (
    ("fleet-manager", "project-manager"),
    ("venture-lab",),
    ("superbot-world",),
    ("superbot-2.0", "superbot-next", "superbot-2", "superbot2.0", "superbot2"),
    ("ideas-lab",),
    ("game-lab",),
    ("self-improvement",),
    ("websites",),
    # Seat 9 (fm prompts v3.6, 2026-07-13) — verified live 2026-07-13:
    # projects/curious-research/{coordinator-prompt.md,instructions.md,
    # failsafe-prompt.md,meta.md} all present at fleet-manager@f8527f44.
    ("curious-research",),
)

# The canonical seat names (registry package directories), same order.
SEATS: tuple[str, ...] = tuple(aliases[0] for aliases in START_ORDER)

# Directories under fleet-manager ``projects/`` that are NOT render-seats and
# must NOT be pinned into :data:`SEATS` — pinning them would fetch three
# non-existent prompt files each and spray honest-404 cells across /prompts.
# They exist upstream for other reasons, so the /prompts pinned-vs-registry
# drift chip (:func:`app.prompts.registry_drift`) must treat them as EXPECTED,
# not as unpinned seats. Two kinds, both verified live against
# fleet-manager@main (2026-07-18, `projects/` contents listing):
#
#   * MERGED-source tombstone stubs from the owner's 2026-07-11 fleet
#     consolidation to the 8+1 standing seats — each holds only a ``meta.md``
#     pointer ("MERGED into <seat> … scope now lives in projects/<seat>/") and
#     no prompt artifacts (e.g. superbot-next → superbot-2.0, substrate-kit →
#     self-improvement, trading-strategy → venture-lab). ``/projects`` already
#     collapses these into its "Retired / merged stubs" section
#     (``app/projects.py``); this is the /prompts-side twin.
#   * ``_inventory`` — a metadata directory (fleet inventory + trigger-registry
#     snapshots), never a seat.
#
# These are exactly the 19 directories the /prompts "pinned list drifted"
# chip named (`projects/` listing minus the 9 SEATS). When fleet-manager adds
# a GENUINELY NEW seat (one bearing coordinator-prompt.md / instructions.md /
# failsafe-prompt.md), it will be in NEITHER set and the chip will correctly
# flag it as drift → re-pin it into START_ORDER above. When a new tombstone
# stub appears it will also flag (rare, human-classified) — the honest signal
# is "a new dir exists, decide which set it belongs in", never a false green.
NON_SEAT_DIRS: frozenset[str] = frozenset(
    {
        "_inventory",
        "codetool-lab-fable5",
        "codetool-lab-opus4.8",
        "codetool-lab-sonnet5",
        "games-program",
        "gba-homebrew",
        "idea-engine",
        "mobile-lab",
        "pokemon-mod-lab",
        "product-forge",
        "sim-lab",
        "substrate-kit",
        "superbot",
        "superbot-games",
        "superbot-idle",
        "superbot-mineverse",
        "superbot-next",
        "superbot-retro",
        "trading-strategy",
    }
)


def seat_for(name: str) -> str:
    """The canonical seat a package name maps to, or ``""`` when it maps to
    none (retired stubs, unknown directories — the caller degrades honestly,
    never guesses a seat). Same normalization as ``projects.start_rank``:
    lowercased, ``_``→``-``, matched against each slot's aliases."""
    norm = (name or "").strip().lower().replace("_", "-")
    for aliases in START_ORDER:
        if norm in aliases:
            return aliases[0]
    return ""
