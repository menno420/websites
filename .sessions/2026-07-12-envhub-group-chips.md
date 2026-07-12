# 2026-07-12 — envhub: completeness chips on the environments-hub group headers

> **Status:** `complete` — PR #219, branch `claude/envhub-group-chips`;
> lands via the auto-merge-enabler on green.

- **📊 Model:** Claude Fable 5 · worker · feature-slice

**What this session was about:** the hub (`/owner/environments-hub`) links
each group's create-complete-environment manifest but gives no hint which
environment is unfinished — the completeness checklist (PR #216) is one
click deep per group, while the hub index is where the owner actually
decides where to spend the next console visit. This session promoted the
captured backlog bullet "Completeness chip on the environments-hub group
headers" (`docs/ideas/backlog.md`, source
`.sessions/2026-07-12-envhub-completeness-diff.md` 💡): reuse
`envhub.annotate_completeness` to compute a per-group summary from the SAME
cached `railway.live_overview` read the page already makes (zero new
network calls) and render it as a chip beside each group's manifest link.

## What was done

- **Summary helper** `app/envhub.py` `group_summary(group, live)`: builds a
  minimal manifest-shaped stub (the group + one schema row per recorded
  variable name) and runs it through the EXISTING `annotate_completeness`
  (PR #216) — pure reuse, so every honesty rule holds by construction: no
  live truth (token unset / read failed / per-service fetch error / group
  outside the project-scoped token's scope) yields the honest
  `comparable: False` summary WITH the reason, never a fabricated 0/Y.
  `overview()` attaches a per-group `summaries` map computed from the one
  cached live snapshot it already holds — zero new network surface.
- **Template** `app/templates/owner_environments_hub.html`: the chip beside
  each group's create-complete-environment manifest link — `b ok`
  "X/Y set live" when every expected variable is set live, `b warn`
  "X/Y set live" when unfinished (with the partial-read reason appended
  when some services could not be read), `b unknown` "live status unknown"
  + the exact reason otherwise — the existing hub chip idiom, no new CSS.
- **Tests** `tests/test_envhub_group_chips.py` (13, fully offline —
  GraphQL monkeypatched, GitHub canned): all-set → green chip; partial
  (incl. a service absent from a successful read = honest missing, the
  #216 semantics) → amber chip; live read failure and token-unset → the
  unknown chip on EVERY group with the exact reason and zero numeric
  chips; mixed groups on one page (one numeric chip, every out-of-scope
  group unknown with the scope reason); `group_summary` unit precision
  (counts, per-service-error unknowns, out-of-scope, no-live-truth);
  NAMES-NEVER-VALUES (sentinel live values asserted absent from the
  rendered HTML); the /owner gate re-pinned (401 without/wrong creds).
- **Backlog** `docs/ideas/backlog.md`: the source bullet flipped
  `captured → built` (PR #219); claim file deleted at close.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 848 passed (+13 new), 0 failed, 1 warning;
  `python3 bootstrap.py check --strict` — green apart from this card's own
  designed born-red HOLD (flipped by this commit) and the pre-existing
  `owner-action-fields` advisory on control/status.md (never
  exit-affecting, not owned here).

**Decisions made:** the group summary is computed by feeding a minimal
manifest-shaped stub through the UNCHANGED `annotate_completeness` rather
than by duplicating its counting logic or calling the heavier
`envhub.manifest()` per group — one honesty ladder, zero forked semantics,
and no per-group plan-text generation on the index render; green means
strictly complete (`set_count == total`), so a comparable-but-partially-
unreadable group renders amber with the partial-read reason instead of a
false all-clear.

⚑ Self-initiated: no — coordinator-assigned slice executing an existing
backlog bullet.

## 💡 Session idea

**Environments-completeness rollup chip on the /owner board** — the group
completeness summary now exists as a cheap pure function
(`envhub.group_summary`) over the cached live read, but it only renders on
the hub index; the /owner readiness board — the owner's actual habit path —
says nothing about unfinished environments. One header chip there (green
"environments complete" / amber "environment unfinished: X/Y set live" with
a hub deep link / honest unknown-with-reason), computed from the same
cached `railway.live_overview` snapshot, would repeat the exact promotion
ladder that just paid off twice (#213's /prompts drift chip → #217's /fleet
coverage rollup). Worth having because the hub is a click the owner must
remember to make, while the board is where he already looks every session.
Deduped against `docs/ideas/backlog.md` + the queue-state NEXT list:
nothing rolls environment completeness up to the board (the #217 rollup is
projects role coverage on /fleet; the committed-inventory pin bullet is
repo-internal doc drift, not a board surface).

## ⟲ Previous-session review

The /owner/environments name-drift session (#218) did well — putting the
diff in a new pure module (`app/envdrift.py`) instead of the read layer
kept this session's reuse story clean, and its card's "835 passed (+16
new)" convention again made the baseline check a subtraction; one honest
carry-forward: its 💡 (the SERVICES-vs-registry consistency pin) documents
that the registry and `railway.SERVICES` have ALREADY drifted, and this
session's chip denominators trust the registry half alone — until that pin
lands, an "X/Y" here can inherit that repo-internal drift silently.
