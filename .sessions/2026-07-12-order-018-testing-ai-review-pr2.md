# 2026-07-12 — ORDER 018 PR2: AI exit-review + screenshots for `/testing`

> **Status:** `complete` — PR `claude/order-018-testing-ai-review`, stacked on
> PR1 (#176), parks READY + green for the owner (build worker; merge is
> deliberately not this session's call).

- **📊 Model:** claude-fable-5 · build worker · order

**What this session was about:** Rung: order — ORDER 018 (tester-recruitment
site), captured in `control/inbox.md` @ `704221d` on PR #173's branch; PR2 of
the series (PR1 = #176, READY+green, parked for the owner). Scope: the
"submission + AI exit-review flow" from the order's done-when — a server-side
Anthropic Messages client (the repo's FIRST AI integration), grading +
follow-up questions on submissions, the auto-pay eligibility gate fed by the
real quality score (still queue-only: dry-run + kill switch unchanged), and
the screenshot upload deferred from PR1.

## What was done

- **AI client** `botsite/testing_ai.py` — Anthropic Messages API over httpx
  (already a botsite dep; no SDK added). Hard rules baked in: API key read
  from env `ANTHROPIC_API_KEY` at RUNTIME per call (never cached at import,
  never logged, never in any page/export — test-pinned); key absent → honest
  degraded mode (submissions accepted as before; every page says the owner
  reviews manually). Model env `TESTING_AI_MODEL` (default
  claude-haiku-4-5 dated id — cheap grading), max_tokens 1500. Spend caps
  in-process mirroring the PR1 rate-limiter style: daily cap
  `TESTING_AI_DAILY_CAP` (default 50) + per-submission cap (1 grade + 3
  follow-up rounds); ONE retry max, 5xx/timeout only (4xx never retries).
- **Prompt-injection hygiene** — tester text is untrusted visitor input:
  framed as `<untrusted_tester_submission>` data with a system prompt that
  forbids treating it as instructions; model output parsed as STRICT JSON
  against a fixed schema (any deviation → degraded, never partial trust);
  rendered escaped by Jinja autoescape; no secrets/internal URLs in prompts.
- **Exit-review flow** — on submit: grade (0–100 score, low-effort flag,
  findings each with severity, up to 3 follow-up questions on material
  gaps). Follow-ups render inline on the tester's private status page with a
  guarded POST (same-origin + rate limit like every state change); answers
  get ONE re-grade round; then claim status → `reviewed` (new status;
  approve accepts submitted|reviewed). Chosen SYNCHRONOUS on the request
  (decide-and-flag: bounded ~15 s timeout + 1 retry; the tester sees
  follow-ups immediately and tests stay deterministic).
- **Storage** — `ai_reviews` (one row/submission: status
  pending-followup|reviewed|degraded, score, low_effort, summary,
  findings_json, followups_json, degraded_reason, calls_used) +
  `screenshots` (blob rows) tables; both in the owner JSON export (blobs
  base64) so the ephemeral-disk backup valve stays complete.
- **Auto-pay gate wired to the real score** — `decide_payout(ai_score=…,
  ai_low_effort=…)` with threshold `TESTING_AUTOPAY_MIN_SCORE` (default 80);
  v1 behavior unchanged (DRY_RUN still queues everything); the owner queue
  now shows "would auto-pay: yes/no" + every held-back reason per
  submission, plus an AI-state panel (available/DEGRADED, model, calls
  today/cap, degraded-review count).
- **Screenshot upload** (the PR1 deferral, shipped) — python-multipart
  pinned in botsite/requirements.txt (the service's first added dep); ≤3
  files, ≤2 MB each, png/jpeg by content-type AND magic bytes; stored as
  SQLite blobs; served ONLY on an owner-auth route (nosniff +
  Content-Disposition); urlencoded no-file submissions still work.
- **Owner ask** appended to `docs/owner/OWNER-ACTIONS.md` (six-field + RISK):
  set `ANTHROPIC_API_KEY` on the botsite service (no such ask existed) —
  reversible, spend bounded, degraded mode holds until then.
  - *Amended same day (follow-up commit on this branch):* the coordinator
    session reported the key already wired 2026-07-12 (copied from the
    Railway "worker" service via the Railway API onto botsite + review;
    auto-redeployed) — the ⚑ block is annotated reported-resolved; not
    verifiable from this repo, so verify post-merge via the owner queue's
    AI-state panel at `/testing/owner`.
- **Tests** — 28 new (`botsite/tests/test_testing_ai.py` + fixture/assert
  updates in `test_testing.py`): degraded mode, mocked-API happy path
  (httpx seam monkeypatched — CI makes zero network calls), JSON/schema
  degrade, 5xx-one-retry, 4xx-no-retry, timeout, daily + per-submission
  caps, follow-up round + guards, score→gate wiring (high score still
  queues; low score names the threshold; low-effort holds), injection smoke
  ("ignore previous instructions" stays schema-valid data + renders
  escaped), upload caps/magic/serving/export, key-never-leaks.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 417 passed (PR1 baseline 389); `python3 bootstrap.py
  check --strict` — green (sole hold during the session was this card's
  designed born-red state).

⚑ Self-initiated: no — coordinator-routed ORDER 018 PR2 as briefed.

## 💡 Session idea

**Reuse pack for the AI-integration pattern** — `testing_ai.py` now embodies
the repo's first server-side Anthropic pattern (runtime env key, degraded
mode, in-process spend caps, one-retry rule, untrusted-data prompt framing,
strict-JSON schema gate). ORDER 017's review-site assistant (PR #172) is the
named next consumer: extracting the ~120 generic lines into a small shared
`ai_client` module (or a documented copy-the-pattern recipe, since services
never import each other) before a second copy drifts would keep the two
integrations honest twins. Worth having because the second consumer is
already ordered — the cheapest moment to standardize is before it exists.

## ⟲ Previous-session review

PR1's session (#176) did well: its dry-run payout module was shaped so this
session could wire a real score into `decide_payout` by changing one
parameter, and its 33 tests caught every behavior this PR changed (the two
assertions that needed updating failed loudly and precisely). What it
missed: the `guided-walkthrough` placeholder promised "step scripts + AI
confirmation land in PR2" in template copy while the order's PR2 scope was
the exit-review — this session shipped the reviewer but the walkthrough
step scripts remain unbuilt, so that copy now overstates by one PR (small,
honest fix for PR3's session: reword or ship the scripts).
