# 2026-07-13 — committed-inventory consistency pin: railway.SERVICES vs the envhub registry

> **Status:** `complete` — PR #225, branch `claude/inventory-consistency-pin`;
> cross-check passed (independent re-diff confirmed the single drift, the pin
> proven red on pre-fix main); lands via the auto-merge-enabler on green.

- **📊 Model:** claude-fable-5 · worker · feature-slice

**What this session was about:** backlog promotion rung — executes the
captured bullet "Committed-inventory consistency pin: `railway.SERVICES` vs
the envhub registry" (`docs/ideas/backlog.md`, source
`.sessions/2026-07-12-owner-envs-name-drift.md` 💡). The repo hand-keeps TWO
committed inventories of the same four services' variable names
(`app/railway.py` SERVICES and `app/data/environments.json`'s
superbot-websites group) and they had already drifted: the registry
documents `ANTHROPIC_API_KEY` for botsite, SERVICES did not. This session
(1) reconciles the drift honestly — evidence decides which side is right —
and (2) pins the two inventories to each other with one zero-network suite
test (declared-exceptions allowlist, no silent exemptions), so the next
divergence goes red at PR time instead of lying to the owner. The PR #218
live drift check cannot catch this class: it compares each inventory
against Railway, never against the other.

## What was done

- **Exhaustive diff** (programmatic, both directions, per service, plus
  service-name sets and URLs, both inventories at `90ff3a1`): exactly ONE
  discrepancy — botsite's `ANTHROPIC_API_KEY` present in the registry,
  absent from SERVICES. control-plane (10 names), dashboard (6), review
  (4) identical on both sides; service-name sets and all four URLs agree.
- **Reconcile** `app/railway.py`: `ANTHROPIC_API_KEY` added to the botsite
  SERVICES entry (name + purpose + Anthropic-console manage link only —
  NAMES NEVER VALUES, unchanged doctrine). The registry side wins on
  evidence: `docs/owner/OWNER-ACTIONS.md` row K (Decided) records the key
  set on BOTH botsite and review per ORDER 022 ("verified present by
  name"); the registry entry's own note cites row K; and
  `botsite/testing_ai.py` is the real consumer (reads env
  `ANTHROPIC_API_KEY` at runtime for the tester-program AI exit review,
  ORDER 018 PR2). SERVICES' botsite entry simply predated the ORDER 022
  wiring.
- **Pin** `tests/test_inventory_consistency.py` (4 tests, zero network —
  pure imports of the committed module + the committed JSON via the real
  `envhub.load_registry` loader, no HTTP, no token): service-name sets
  match; per-service variable-NAME sets match in BOTH directions with
  named-variable, fix-pointing failure messages; URLs match; and the
  explicit `ALLOWED_ONLY_IN_REGISTRY` / `ALLOWED_ONLY_IN_SERVICES`
  allowlists (per-entry justification comments required; currently EMPTY —
  after the fix no legitimate one-sided variable exists) are themselves
  checked for stale entries, so an exemption cannot outlive its reason.
  Verified red on the pre-fix drift (stash test: 1 failed naming
  botsite/ANTHROPIC_API_KEY), green after.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 895 passed (+4 new), 0 failed, 1 warning;
  `python3 bootstrap.py check --strict` — green apart from this card's own
  designed born-red HOLD and the pre-existing `owner-action-fields`
  advisory on control/status.md (never exit-affecting, not owned here).

**Decisions made:** the pin compares SERVICES against the superbot-websites
group ONLY — the registry's other groups (reliable-grace,
superbot-mineverse, github-actions, claude-cloud) document other estates
with no SERVICES counterpart and are out of scope by construction, not by
exemption; the registry is read through the real `envhub.load_registry`
loader (not a raw `json.load`) so the pin also rides the loader's
value-smuggling hard-reject; and the allowlists check (service, variable)
PAIRS, not bare names, so exempting a variable on one service can never
silently exempt it fleet-wide.

⚑ Self-initiated: no — coordinator-assigned slice executing the
committed-inventory consistency backlog bullet.

## 💡 Session idea

**Code-consumed env names vs the committed inventories (the third
inventory is the code itself)** — reconciling the two committed inventories
surfaced a gap NEITHER documents: `botsite/testing_ai.py` reads
`TESTING_AI_MODEL`, `TESTING_AI_DAILY_CAP`, and `TESTING_AI_GUIDE_CAP` (all
optional, defaulted in code), but neither `railway.SERVICES` nor the envhub
registry lists them for botsite — review's equivalents (`REVIEW_AI_MODEL`
etc.) ARE documented, so the omission is inconsistent, not a policy. Either
document the three names in both inventories (they are exactly the
owner-tunable knobs the /owner/environments page exists to show), or grow
the consistency pin a third leg: scan each service package for
`os.environ`/`os.getenv` name literals and assert every code-consumed name
is documented (or explicitly allowlisted as internal). Worth having because
the just-shipped pin only proves the two ledgers agree with each other —
they can still agree on an incomplete picture, and the incompleteness found
today was found by accident. Deduped against `docs/ideas/backlog.md` + the
queue-state NEXT list: the consistency bullet this session executes covers
inventory-vs-inventory only; nothing covers code-vs-inventory.

## ⟲ Previous-session review

The owner-board env-chip session (#223) did well — its `board_rollup` kept
one honesty ladder by reusing `group_summary` unchanged (zero forked
semantics), its card's "891 passed (+11 new)" convention made this
session's baseline a subtraction instead of a re-run, and it repaired the
#219 session's capture miss by backfilling the backlog bullet with the
original text instead of paraphrasing. One observation, not a defect: its
chip names groups by registry `id` for grep-ability — the same reasoning
this session leaned on when keying the pin's allowlists by (service,
variable) pairs. Nothing it missed affects this lane.
