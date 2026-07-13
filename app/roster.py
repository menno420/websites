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
