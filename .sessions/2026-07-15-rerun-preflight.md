# 2026-07-15 — Owner console: rerun-ci preflight — preview, pinned confirm, verification chip

> **Status:** `complete` — PR #352, branch `claude/rerun-preflight-20260715`;
> `latest_failed_run`/`rerun_run` split in app/github.py, gated read-only
> previews for rerun-ci and refresh on the new generic
> `owner_preflight.html`, and a pinned fail-closed confirm with a
> post-fire verification chip.

- **📊 Model:** Claude Fable · medium · feature build (rerun-ci preflight preview + pinned confirm on the owner console)

**What this session is about:** the "preflighted" half of the owner launch
console, PR A of 2. Today `POST /owner/actions/rerun-ci` resolves "the
newest failed run on main" AT FIRE TIME — the owner fires blind at
whatever happens to be newest-failed at that instant. This slice makes the
target visible and the fire pinned:

- `app/github.py` splits `rerun_latest_failed` into a read half
  (`latest_failed_run` — resolves the newest failed run, refresh=True) and
  a fire half (`rerun_run` — POSTs rerun-failed-jobs at a PINNED run id),
  recomposed so the existing composition keeps working;
- new gated GET `/owner/actions/rerun-ci/preview?repo=X` (plain
  `require_owner`, read-only like every other /owner GET) renders a new
  generic `owner_preflight.html`: facts table (run id, workflow, branch,
  head sha, created + age, run link) and a confirm form carrying the
  hidden pinned `run_id`; no failed run → an honest "nothing to re-run"
  page;
- `POST /owner/actions/rerun-ci` now REQUIRES the pinned `run_id`,
  re-resolves with refresh=True and FAILS CLOSED when anything moved
  (missing pin, vanished run, no-longer-failed, newer failed appeared) —
  honest banner naming exactly what moved, zero fires; a match fires at
  the pinned id and a post-action chip re-GETs the run to show it really
  started (honest-unknown when the re-GET fails);
- `POST /owner/actions/refresh` gets the cheap uniform preview on the same
  template ("N cache entries will drop"); the POST contract itself is
  untouched (the ORDER 013 security tests keep passing unchanged);
- the /owner board's rerun-ci form routes through the preview instead of
  the blind fire. The `require_owner_action` floor (auth → strict
  Origin/Referer → per-route rate limit) stays exactly as-is — no new
  CSRF token this slice.

⚑ Self-initiated: no — dispatched under the owner's live work grant
(accept-edits session mode), coordinator-approved mission slice
(scouting cites @ 1e73d8a, re-verified at HEAD).

## Close-out

**Evidence:**

- files touched this branch: `.sessions/2026-07-15-rerun-preflight.md` +
  `control/claims/claude-rerun-preflight-20260715.md` (first commit; claim
  deleted at this flip), `app/github.py` (`latest_failed_run` read half,
  `rerun_run` fire half, `run_info` single-run read, `rerun_latest_failed`
  recomposed from the halves — same return shapes, existing mocks/tests
  unaffected), `app/owner.py` (GET `/owner/actions/rerun-ci/preview` +
  GET `/owner/actions/refresh/preview` behind plain `require_owner`;
  `_run_facts` via `fleet.freshness` age math; `_render_rerun_preview`
  pure view; `_stale_pin_banner` names WHICH invariant broke by re-GETting
  the pinned run; `_post_fire_chip` askverify-chip idiom; hardened
  `action_rerun_ci` requiring `run_id`), `app/templates/owner_preflight.html`
  (new generic preflight page — banner/chip/facts/empty/confirm slots),
  `app/templates/owner.html` (rerun form → preview GET; refresh keeps its
  direct POST + gains a preview link), `tests/test_owner_preflight.py`
  (new, 20 test items: preview facts, ZERO-write pins with recorded
  api_post/api_request choke points + cache-untouched assert, refresh=True
  pin minting, pinned fire with exact POST path, stale-pin fail-closed
  matrix (newer appeared / vanished / no longer failed / resolution
  failure), no-run_id rejection that never falls back, fire-rejected
  honesty, chip started/warn/honest-unknown, gate floor 401/403,
  independent per-path rate buckets, refresh preview facts + unchanged
  POST contract, board wire-in), `tests/test_app.py`
  (`test_owner_rerun_ci_action` updated to the pinned contract — the one
  existing test the contract change touched; `test_rerun_latest_failed_no_failed_run`
  passes unchanged against the recomposition).
- the 10 ORDER 013 tests in `tests/test_owner_security.py` pass byte-unchanged.
- git: branch `claude/rerun-preflight-20260715`, based on `main` @
  `1e73d8a`; PR #352. Work in an isolated `git worktree` (the recorded
  EnterWorktree wall — manual worktree substitute).
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — **1479 passed, 1 warning** (+20 test items in
  `tests/test_owner_preflight.py`); `python3 bootstrap.py check --strict`
  — green except the DESIGNED born-red hold on this card (released by
  this flip). The kit's guard-fires telemetry ledger
  (`.substrate/guard-fires.jsonl`) is gitignored in this repo, so its
  "commit the delta" note has nothing committable — noted honestly.

**Judgment:**

- Decisions made: (1) the preview answers 200 with an honest empty state
  for unknown/missing repo instead of 404 — the structural clarity gate
  (`tests/test_clarity_structure.py`) walks every GET route bare and holds
  it to the headline+lede idiom, and an honest "no repo selected" page
  beats a JSON 404 on an owner-facing surface; (2) confirm mismatches
  re-render the PREVIEW (with a fail-closed banner and the facts of what
  is newest NOW) rather than the board — the owner lands exactly where
  re-confirming is one click, and the post-fire result page deliberately
  OMITS the confirm form so success can never invite a double-fire;
  (3) the stale-pin banner spends one extra read (`run_info` on the pinned
  id) to say WHICH invariant broke — vanished vs no-longer-failed vs
  newer-failed-appeared — because "something changed" is not an honest
  banner; (4) `rerun_latest_failed` stays alive as the composition of the
  two halves (no console caller uses it anymore, but the contract and its
  tests keep working — refactor, not a breakage).
- Next session should know: PR B of 2 (the coordinator's other half of the
  launch console) can reuse `owner_preflight.html` as-is — the `p` dict is
  deliberately generic (title/lede/banner/chip/facts/empty/confirm), and
  the refresh preview proves a second action rides it with zero template
  changes. The rate-limit floor stays 10/60s per route path; the preview
  GETs are auth-only by design (read-only, like every other /owner GET).

## 💡 Session idea

**Preflight the failed JOBS, not just the run** — the preview currently
names the run (id, workflow, age, link) but `rerun-failed-jobs` actually
re-runs a SUBSET: the run's failed jobs. GitHub exposes exactly that list
read-only (`GET /repos/{o}/{r}/actions/runs/{id}/jobs` filtered to
`conclusion=failure`), so the facts table could add one row — "jobs that
will re-run: `quality` (1 of 3)" — making the confirm claim precise down
to the job names, and the post-fire chip could then verify THOSE jobs
flipped to queued rather than the run's aggregate status. Deduped against
`docs/ideas/backlog.md`: no jobs-listing / rerun-preflight bullet exists
(pinned-* hits are all registry/contract pins; nothing touches the
Actions jobs API).

## ⟲ Previous-session review

`.sessions/2026-07-15-arcade-detail.md` is this card's format reference
and its close-out compounded here directly: its recorded worktree wall
(manual `git worktree add` substitute for EnterWorktree) was consumed
verbatim by this session's isolation setup, and its decision (2) — route
and catalog reading through the SAME loader so two surfaces can never
disagree — is the same single-source principle this session applied to
time instead of data: preview and confirm resolve through the SAME
`latest_failed_run` read (refresh=True both times), so the only way they
disagree is when the world really moved, which is precisely what the
fail-closed banner reports. Improvement it points at: that card's blocker
panels name owner clicks but nothing machine-verifies a click FIRED —
this session's post-fire chip idiom (act, then immediately re-GET the
evidence) is the missing half, and porting it to the writeback queue's
retry action would close the same loop there. Still worth promoting.
