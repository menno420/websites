# 2026-07-13 — document TESTING_AI_* config vars in both inventories + extend the code-vs-inventory pin

> **Status:** `complete` — PR #227, branch `claude/testing-ai-inventory`;
> both inventories now document every genuinely code-consumed name for
> botsite + control-plane, and the #225 pin grew a code-vs-inventory third
> leg (proven red on the pre-fix inventories); lands via the
> auto-merge-enabler on green.

- **📊 Model:** Claude Fable 5 · worker · feature-slice

**What this session was about:** backlog promotion rung — executes the 💡
from `.sessions/2026-07-13-inventory-consistency-pin.md` (PR #225):
`botsite/testing_ai.py` consumes `TESTING_AI_MODEL`, `TESTING_AI_DAILY_CAP`,
`TESTING_AI_GUIDE_CAP`, but neither `app/railway.py` SERVICES nor the envhub
registry documented them for botsite — review's equivalents ARE documented,
so the omission was inconsistent, not a policy. The two ledgers agreed with
each other on an incomplete picture; the code is the third inventory.

## What was done

- **Full four-service env-consumption scan** (`os.environ`/`os.getenv`,
  kit machinery excluded): botsite had 12 genuinely-consumed undocumented
  names (the three `TESTING_AI_*`; `SITE_PASSWORD` (testing.py:186),
  `TESTING_DB_PATH`, `TESTING_BOUNTY_CAP_USD`, `TESTING_AUTOPAY_ENABLED`,
  `TESTING_AUTOPAY_MIN_SCORE`, `TESTING_PAYOUT_DAILY_CAP_USD`,
  `TESTING_PAYOUT_MONTHLY_CAP_USD`, `PAYPAL_CLIENT_ID`,
  `PAYPAL_CLIENT_SECRET`); control-plane had 5 (`ANTHROPIC_API_KEY` +
  `OWNER_ASSIST_MODEL`/`OWNER_ASSIST_DAILY_CAP` from app/owner_assist.py,
  `WRITEBACK_BRANCH`/`WRITEBACK_DB_PATH` from app/writeback.py); dashboard
  and review had none. Deliberate omissions (in the PR body with reasons):
  `RAILWAY_GIT_COMMIT_SHA`/`GIT_SHA` (platform-injected build stamp),
  review's gen_*.py reads (build-time scripts, not the running service).
- **Documented all 17 in BOTH inventories** — `app/railway.py` SERVICES
  (purpose + manage link per name, new `PAYPAL_` manage-link prefix) and
  `app/data/environments.json` (matching surfaces + notes). Names, purpose,
  manage links ONLY — never values, unchanged doctrine.
- **Pin third leg** in `tests/test_inventory_consistency.py`:
  `botsite/testing_ai.py`'s consumed names (imported from its own `ENV_*`
  constants, not source-scraped) must be ⊆ both documented botsite sets,
  with an explicit `TESTING_AI_ALLOWED_UNDOCUMENTED` allowlist (empty) +
  stale-entry check, plus a completeness guard: a targeted regex over that
  ONE file asserts every environ read goes through an `ENV_*` constant so a
  literal-string read cannot dodge the pin. Proven red on the pre-fix
  inventories (stash test: fails naming exactly the three `TESTING_AI_*`
  names), green after.
- **Downstream count pins repaired**: `tests/test_envhub_group_chips.py` +
  `tests/test_envhub_manifest_completeness.py` hardcoded the old 25-var
  estate total ("18/25 set live"); their expected counts now derive from
  the registry so they pin chip/badge RENDERING while the inventory grows.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 898 passed, 1 warning (baseline 895, +3 new);
  `python3 bootstrap.py check --strict` — green apart from this card's own
  designed born-red HOLD and the pre-existing `owner-action-fields`
  advisory on control/status.md (never exit-affecting, not owned here).

**Decisions made:** documented ALL genuinely-consumed undocumented names,
not just the minimum three — same shape, same doctrine, and a half-honest
inventory is the exact failure class this lane exists to close; the
`PAYPAL_*` pair is documented by NAME only with the dry-run caveat; the
code-vs-inventory leg covers `botsite/testing_ai.py` only (the one file
with importable `ENV_*` constants throughout) rather than forcing a brittle
repo-wide source scrape.

⚑ Self-initiated: no — coordinator-assigned slice executing the captured
code-vs-inventory idea from the #225 session card (backfilled into
`docs/ideas/backlog.md` this session as a capture-miss repair, now `built`).

## 💡 Session idea

**Generalize the code-vs-inventory leg to every service module** — the new
pin covers ONE file; this session found the other 14 undocumented names by
hand-grepping `os.environ` across `botsite/testing*.py`, `app/owner_assist.py`
and `app/writeback.py`. A per-service scan (module `ENV_*` constants where
they exist + a literal-string regex over each service package) asserting
every code-consumed name is documented or explicitly allowlisted
(platform-injected `GIT_SHA`/`RAILWAY_GIT_COMMIT_SHA`, gen-script reads)
would make the next `testing_payouts.py`-style knob impossible to ship
undocumented. Worth having because today's completeness was restored by a
one-off manual grep — the pin only holds for the one module it watches.
Deduped against `docs/ideas/backlog.md` + the queue-state NEXT list: the
code-vs-inventory bullet (built this session) covers `testing_ai.py` only;
nothing covers a repo-wide code-consumption scan. Captured in
`docs/ideas/backlog.md`.

## ⟲ Previous-session review

The inventory-consistency-pin session (#225) did well — its exhaustive
programmatic both-direction diff, evidence-first reconciliation, and
proven-red-then-green pin discipline were the template this session reused
verbatim for the third leg; one miss: its card said the 💡 was "Captured in
docs/ideas/backlog.md" but the bullet never landed — backfilled here.
