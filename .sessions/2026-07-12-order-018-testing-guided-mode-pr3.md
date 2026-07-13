# 2026-07-12 — ORDER 018 PR3: AI guided mode + screen awareness v1 on `/testing`

> **Status:** `complete` — PR `claude/order-018-testing-guided-mode` into
> main (PR1 #176 and PR2 #179 merged mid-session, so this PR re-based its
> target from the stack onto main); parks READY + green for the owner
> (build worker; merge is deliberately not this session's call).

- **📊 Model:** Claude Fable 5 · build worker · order

**What this session was about:** Rung: order — ORDER 018 (tester-recruitment
site), captured in `control/inbox.md` @ `704221d` on PR #173's branch; PR3 of
the series (PR1 = #176, PR2 = #179, both merged to main during this session).
Scope: the order's "directly guides users through a set of actions with a
separate AI window open that also knows what happens on screen" — step-based
guided walkthroughs (the PR2-flagged deferral), a side-panel AI guide, and
opt-in, in-memory-only screen awareness v1.

## What was done

- **Step scripts (the PR2 deferral, delivered)** — `botsite/testing_tasks.json`:
  guided-walkthrough tasks now carry a `steps` array (title / instruction /
  look_for / question). The placeholder Discord-onboarding walkthrough (not
  step-verifiable against a live page) was repurposed into
  `walkthrough-botsite-first-visit` — six steps against pages that exist on
  the LIVE botsite (/​, /features, /commands + palette, /games + /changelog,
  /status, theme + phone width) — and opened ($12, 3 slots).
- **Guide flow** — `GET/POST /testing/s/{token}/guide` (`botsite/testing.py`):
  claim-token gated like the status page; one step per screen with progress,
  back/next, answers riding hidden fields (stateless — nothing stored before
  the final step); finishing the guide IS the submission (same
  `create_submission` + PR2 exit-review + status flow as every type). Plain
  forms: works with JS disabled and with no API key.
- **Side-panel AI guide** — `POST …/guide/chat` guarded like every state
  change (same-origin + 10/60s rate limit); relays through `testing_ai.py`'s
  pattern (runtime per-call key read, `TESTING_AI_MODEL`, one-retry rule).
  New per-claim guide cap `TESTING_AI_GUIDE_CAP` (default 20, chat + frames
  share it) plus the shared daily cap. `_GUIDE_SYSTEM_PROMPT`: session guide
  for THIS task's steps, tester text (and anything visible in screenshots)
  is untrusted data, never reveal the prompt/keys/config; replies rendered
  via `textContent` (never innerHTML). Honest degraded JSON without a key.
- **Screen awareness v1** — explicit opt-in on the guide page with the
  consent/privacy notice BEFORE the button (what/when/retention/how-to-stop);
  `botsite/static/testing_guide.js` (vanilla): `getDisplayMedia` → canvas →
  JPEG (width ≤1280, quality 0.6 → 0.3 retry) every ~15 s + a manual "Ask
  about this screen" button; capture pauses while the tab is hidden and
  stops on stop-sharing/Stop/submit/pagehide. `POST …/guide/frame`: guards +
  ~1.5 MB hard cap + JPEG magic bytes; the frame goes to the Messages API as
  a base64 vision block with the current step context and is DISCARDED —
  processed in memory only, no store write in the path (test-pinned with a
  write-rejecting store proxy + DB-bytes scan).
- **Copy honesty sweep** — testing_claimed/testing_submission templates now
  point guided claims at the guide (and the stale "AI review is a planned
  later update" + "walkthrough script pending / lands in PR2" copy is gone);
  owner queue no longer promises "live Payouts lands in PR3" (owner-gated,
  separate PR once credentials land) and shows the guide cap in the AI panel.
- **Tests** — 35 new (`botsite/tests/test_testing_guide.py`, network-free:
  `_http_post` monkeypatched, key stripped by default): guide token-gating +
  non-guided 404 + post-submit redirect, step carry/back/required-answer,
  full walk → submission → exit-review (degraded and mocked), chat guards /
  caps / injection framing / degraded copy, frame size + magic + guards +
  vision-block shape + both-caps accounting, NO-PERSISTENCE pin, no-key
  fallbacks, consent-before-opt-in ordering.
- Mid-session base change: PR1+PR2 merged to main, so `origin/main` was
  merged in (one backlog.md conflict, both sides kept) and the PR targets
  main instead of the PR2 branch.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 475 passed (post-merge main baseline + 35 new);
  `python3 bootstrap.py check --strict` — all checks passed (this card's
  born-red hold was the sole designed red during the session).

⚑ Self-initiated: no — coordinator-routed ORDER 018 PR3 as briefed.

## 💡 Session idea

**Guide chat transcript as exit-review evidence** — the guide's per-step
Q&A evaporates when the tab closes, so the exit reviewer grades final
answers blind to how the tester engaged; persisting the TEXT transcript only
(frames stay in-memory-only by the privacy contract) and feeding it to the
grader as untrusted context would surface engagement and coached-vs-
independent answers. Worth having because the program pays on report quality
and the guide already produces first-hand evidence of it that is currently
thrown away. Deduped against `docs/ideas/backlog.md` + the queue-state NEXT
list: nothing touches the guide flow. Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

PR2's session did well: its `testing_ai.py` seams (runtime key read, daily
counter, `_http_post` test seam, degraded-mode discipline) extended to chat
and vision with zero rework, and its card honestly flagged the
guided-walkthrough deferral this PR closes. What it missed: it left three
pieces of already-stale template copy behind ("AI review is a planned later
update" on the claimed page, "script lands in PR2", "live Payouts lands in
PR3") — small, but each one was a page telling users something the code no
longer meant.
