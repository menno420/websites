# 2026-07-18 — Route owner writeback through a branch + auto-PR (O-020, Q2=b)

> **Status:** `complete` — branch `claude/writeback-branch-pr`; the gated owner
> writeback engine (ORDER 020, `app/writeback.py`) now commits each
> `/owner/queue` submission to a per-submit `claude/owner-writeback-<n>` branch
> and opens a READY auto-merging PR into `main`, instead of a direct
> Contents-API PUT to `main`. Owner-confirmed Q2=(b): "create a PR and auto
> merge it; I don't think it's possible to commit straight to main with the
> PAT." main is ruleset-protected (required `quality` check), so the direct PUT
> was structurally dead — the writeback now lands the same ruleset-safe,
> reviewable way every other change does, and the direct-to-main path was
> removed entirely (no escape hatch). RUNTIME code: built + unit-tested here
> with mocks; the live submit→branch→PR→auto-merge chain is verified after the
> deploy + the Railway control-plane `GITHUB_TOKEN` paste (ASK-0007).

- **📊 Model:** Claude Opus 4.8 · high · feature build

**What this session is about:** O-020's writeback engine was built to PUT
straight to `main`. That path 403/422s on this repo — `main` is protected by a
ruleset requiring the `quality` check, and the owner confirmed the PAT cannot
bypass it. The fix routes each writeback through the fleet's normal branch+PR
flow: commit the append to a fresh `claude/owner-writeback-<entry-id>` branch
(the `claude/*` prefix the auto-merge-enabler + host-automerge-extras arm),
then `POST /pulls` a READY PR into `main`. For the runtime-generated PR to
auto-land with **no human and no session card**, its diff must be
**`control/**`-only** (the CI control fast-lane exempts a control-only diff
from the session-card gate and short-circuits `quality` green): assist already
appends to `control/inbox.md`; note/complete were relocated from
`docs/owner/owner-notes.md` to `control/owner-notes.md`. The generated assist
ORDER was brought into inbox-gate grammar (it was missing `done-when:`, one of
the four required fields). Honest-degrade is preserved end to end.

⚑ Self-initiated: no — coordinator-dispatched (O-020 activation, Q2=b).

## Close-out

**Evidence:**

- **design implemented (branch + auto-PR, the one path):**
  - `attempt_commit` (`app/writeback.py`) dispatches to `_commit_branch_pr`:
    (1) GET `/git/ref/heads/main` for the base head SHA; (2) POST `/git/refs`
    to create `claude/owner-writeback-<entry-id>` (env-overridable prefix
    `WRITEBACK_BRANCH_PREFIX`); (3) read the target ON the branch and
    append-compose; (4) PUT the commit to the branch; (5) `_open_pr` →
    `github.api_request("POST", "/repos/menno420/websites/pulls", …)` base
    `main`, head the branch, `draft:false`. `committed` is claimed ONLY when
    the branch commit SHA is verified AND the PR is open.
  - **control/** targeting: `NOTES_PATH` moved to `control/owner-notes.md`
    (seeded byte-identical to `NOTES_HEADER`, so the create-on-404 path
    converges); a MOVED pointer left at `docs/owner/owner-notes.md`. Assist
    stays `control/inbox.md`. Every writeback PR is therefore `control/**`-only.
  - **inbox gate:** `render_assist_block` gained a `done-when:` line — the
    generated ORDER now passes bootstrap's real
    `_order_grammar_findings` (verified in test (d): four required fields
    `priority/do/why/done-when` + the `## ORDER … · … · status:` header).
  - **honest-degrade:** no token → queued before any call; base-ref
    unresolvable / branch-create 401/403/404 / PUT rejected / PR-open failure
    each stay `queued` with the exact error class; a PUT that answers 200 with
    NO SHA is refused. Idempotent-ish: one branch per audit entry; a retry
    reuses the branch (`422 already exists` = OK), skips a duplicate append
    when the entry marker is already on the branch, and reuses an already-open
    PR (`422` → looked up). New audit columns `branch`/`pr_number`/`pr_url`
    (with an ALTER-backfill for a pre-existing ephemeral store).
  - **floor untouched:** `require_owner_action` (auth → same-origin → rate
    limit) is unchanged; test (e) re-pins it on the default path.
- **files touched (branch `claude/writeback-branch-pr`):**
  - product: `app/writeback.py` (the branch+PR engine, `NOTES_PATH`
    relocation, `done-when:`, schema cols, `state_summary` base/branch_prefix),
    `app/owner.py` (preview "lands in" + token-state copy + `_entry_banner`
    PR link), `app/templates/owner_queue.html` (lede).
  - control/docs: `control/owner-notes.md` (new relocated target seed),
    `docs/owner/owner-notes.md` (back-compat MOVED pointer), `control/status.md`
    (heartbeat).
  - tests: NEW `tests/test_owner_writeback_branch_pr.py` (a–f); the existing
    `tests/test_owner_writeback.py`, `tests/test_owner_queue_preflight.py`,
    `tests/test_durable_ask_ids.py` GitHub fakes retargeted to the branch+PR
    sequence; `tests/test_hostile_env_smoke.py` poison list +
    `WRITEBACK_BRANCH_PREFIX`.
- **confirm tests (a)–(f) pass:** (a) happy-path sequence + record-only-on-
  success; (b) targets `control/**`-only for assist AND note/complete;
  (c) honest-degrade (no token / branch-create 403 / PR-open failure → queued,
  no false success); (d) generated ORDER passes the real inbox grammar gate;
  (e) CSRF/same-origin/rate-limit floor enforced; (f) `state_summary` +
  branch/pr audit-row contract. 11/11 in the new file.
- **git:** branch from `origin/main` @ `3b08df1` (#397). Commits `e1f2dae`
  (born-red card) · `bcde47c` (build) · `ec57d34` (tests) · `8dfea01`
  (contract-pin fixes) · `6b371a4` (heartbeat) · + this flip. PR **#398** READY
  (`https://github.com/menno420/websites/pull/398`).
- **verify:** `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` → **1839 passed, 1 warning** (exit 0; the pre-existing
  Starlette/httpx TestClient deprecation is the only warning). `bootstrap.py
  check --strict` and `--require-session-log` → the only red is the DESIGNED
  born-red hold on this card, released at this flip; `--status-only` exit 0.

**Judgment:**

- Decisions made: (1) **No direct-to-main escape hatch** — I first built
  branch+PR as the default with a `WRITEBACK_DIRECT` flag, but the owner
  confirmed mid-session that a straight-to-main PUT is impossible with the PAT,
  so the flag and `_commit_direct` were removed entirely (simpler code + tests,
  one path). (2) **Seed `control/owner-notes.md`** byte-identical to
  `NOTES_HEADER` rather than relying only on create-on-404 — the file now
  exists at rest like `control/inbox.md`, and the runtime append/create paths
  converge. (3) **`done-when:` on the assist ORDER** — the inbox append-only
  gate requires four fields and the generator emitted only three; this was
  latent (direct-to-main never triggered the PR-side inbox gate), and would
  have red'd the first runtime assist PR. Fixed at the generator and pinned by
  test (d) against the kit's own checker. (4) **`committed` = commit + PR** —
  the honesty hinge moved from "a verified commit SHA" to "a verified branch
  commit SHA AND an open PR", since the change only reaches main after the PR
  merges; a commit that lands but whose PR fails stays queued (retry re-opens).
- Next session should know: this is RUNTIME code — the LIVE end-to-end verify
  (submit → `claude/owner-writeback-<n>` branch → auto-PR → merge on green) is
  still pending the deploy + the owner pasting a fine-grained PAT with BOTH
  `contents:write` AND `pull-requests:write` into the Railway control-plane
  `GITHUB_TOKEN` (ASK-0007 — the PAT now needs PR-write because the runtime
  opens the PR itself). The seat cannot verify PAT scope (CAPABILITIES proxy
  wall). Blocked-not-mine unchanged: ASK-0002 (Discord OAuth — reuse SuperBot
  app recommended), R10 (workflow-touch).

## 💡 Session idea

**One shared source for the ORDER field list, consumed by both the runtime
generator and the kit gate.** This session's whole `done-when:` bug existed
because `app/writeback.render_assist_block` hardcodes the ORDER fields
independently of the kit's `ORDER_REQUIRED_FIELDS` — the two agreed by luck
until the writeback PR started actually running the inbox gate, and only a
backlog-shaped attention (mine) caught the drift. Test (d) now pins agreement,
but a test asserts, it does not prevent divergence at the source. A cheap
durable fix: expose the kit's `ORDER_REQUIRED_FIELDS` (already kit-owned,
`engine.grammar`) as the single list the generator iterates when it composes
the block — so a field the gate starts requiring is one the generator
automatically emits, and the "generator ↔ enforcer cannot drift" guarantee the
`control/README.md` already claims for the kit's own writers extends to the
control-plane's runtime writer too. Same instinct as the kit's own
writer/enforcer single-source discipline, applied across the repo boundary.

## ⟲ Previous-session review

`.sessions/2026-07-18-test-coverage-bundle.md` (X2) pinned three shipped-but-
untested honesty signals so a regression would trip in CI rather than silently
invert. This session is the same honesty instinct at the write path: the
writeback used to *claim* a main commit that (post-ruleset) could never land;
now it only claims `committed` on a verified branch commit + open PR, and every
degraded step stays honestly `queued` — the "never assert what didn't happen"
property X2 tested for reads, enforced here for writes.
