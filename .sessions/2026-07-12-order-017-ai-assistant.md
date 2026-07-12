# 2026-07-12 — ORDER 017 B: on-site AI review assistant (/ask)

> **Status:** `complete` — branch `claude/order-017-ai-assistant`; landed as the
> ORDER 017 workstream-B PR (number assigned at open; see the PR for this branch).

- **📊 Model:** claude-fable-5 · high · feature-build (order-directed)

**What this session was about:** ORDER 017 (inbox, P1, time-sensitive through
2026-07-14), workstream B: make "review this with an agent" real on the public
review site — an evidence-grounded Ask/Review AI assistant at `/ask`, honest
about its degraded no-key state, rate-limited and spend-capped. Rung: order.

## What was done

- `review/data/evidence/` — the committed, SHA-pinned grounding corpus (6 md
  files, ~26 KB): provenance + claim-verdict table, the 2026-07-12 scheduler
  incident, the 8-seat roster/consolidation story, the sent-email findings +
  framing, the screenshot index. Every chunk carries repo/path/commit SHA;
  UNVERIFIED claims carry their verdicts so the model attributes rather than
  asserts. This corpus is the assistant's ONLY grounding source (plus the
  service's own committed snapshot.json/questions.json, appended at load).
- `review/ai.py` — POST `/ask/api`: modes `ask` (free-form Q&A) + `review`
  (structured Strong / Weak-or-risky / What-to-verify / Suggested-probes);
  server-side Anthropic Messages API call over httpx; key read from env AT
  REQUEST TIME (absent → honest 503, lights up when the owner sets it; never
  logged, never sent to the browser); strict same-origin Origin/Referer check
  (the ORDER 013 / PR #159 pattern); server-side injection screen + delimited
  untrusted input; seeded questionnaire answers served before any key/limit
  check; per-IP 20/hour + 100/day, global 500/day, $25/month spend cap from
  real usage tokens at sticker pricing; one JSON log line per question
  (salted IP hash, truncated question, tokens — no PII, no key).
- `review/templates/ask.html` — two-tab widget, DOM-safe answer rendering
  with citation→GitHub-permalink linkification, honest degraded banner,
  seeded Q&A listed; light+dark via the shared tokens; mobile-clean.
- `review/app.py` — additive only: include `ai.router`, GET `/ask`, docstring
  note that ai.py is the one deliberate network exception.
  `review/requirements.txt` — `httpx==0.28.1` (same pin as siblings) with the
  doctrine-exception note.
- `review/tests/test_ai.py` — 24 tests: degraded-without-key (with a
  fail-loud no-network guard), CSRF origin checks, seeded path (incl. past
  rate limits), injection screen, rate-limit + spend-cap trips, mocked model
  path (payload shape, spend accounting, refusal stop_reason, env model
  override, log hygiene). Whole suite passes with NO API key present.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q`
  — 378 passed; `python3 bootstrap.py check --strict` — green after the
  card flip (one pre-existing advisory warning on control/status.md
  risk-class tokens, not from this change; never exit-affecting).

⚑ Self-initiated: no — ORDER 017 workstream B (inbox @ the order branch;
sibling PRs carry workstreams A and C).

## 💡 Session idea

**Harvest the AI-assistant question log into the /questions ledger** — the
endpoint already logs every question as a JSON line (mode, truncated text,
outcome, salted hash); a small harvest step could turn real reviewer
questions into `data/questions.json` entries so the ledger fills from real
traffic instead of staying empty. Worth having because the order itself says
the log "feeds the Q&A page" — this closes that loop. Deduped against
`docs/ideas/backlog.md` + queue-state NEXT: not present. Captured in
`docs/ideas/backlog.md`.

## ⟲ Previous-session review

The kit-v1.14.0 upgrade session (PR #171) landed clean with a tight card and
real verification output; it didn't touch the review service, so no drift to
reconcile here — a good, boring handoff.
