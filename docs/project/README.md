# docs/project — Claude Project console texts

> **Status:** `reference`

- `setup-script.sh` — paste into the websites Project's **environment settings → Setup script** field (runs at session provision; fail-soft, prints a capability probe).
- `project-instructions.md` — paste its body (below the `---`) into the websites Project's **Custom Instructions** field.
- `docs/project/routine-prompt.md` — paste its fenced block as the wake routine's prompt in the claude.ai **Routines** screen (full self-contained version; the existing trigger's shorter delegating prompt also works).
- These repo files are the **source of truth**: edit here first, then re-paste into the console — the console copies drift silently otherwise.
- Why they exist: the 2026-07-10 16:01Z routine-fired session couldn't land its work (no PR tooling, API 403, push never landed) — see `docs/CAPABILITIES.md` append log 2026-07-10.
