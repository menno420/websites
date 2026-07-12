# Canonical findings + framing — the second Anthropic email & review pack

> Provenance: superbot `docs/eap/anthropic-email-2-draft-2026-07-11.md` @
> `8558179e6a90670ed18c778234d789c65c2b5789` (status: SENT 2026-07-12 13:24Z
> per `docs/current-state.md` banner @ `0999c33`); superbot
> `docs/eap/external-review-pack-2026-07-09.md` @
> `b0e9ab20601e8a44da87c6e72f712f517b62adc0`; superbot
> `docs/eap/night-review-2026-07-11.md` @
> `e1090dbcfdf63ffd955399dc2325b9ad1a2f8c8d`.

## The narrative arc and register (the tone all answers must match)

Two-part format: Part 1 = the operator (Menno, a non-coder who runs a ship
moving oil through the rivers of Europe and, in his off-hours, this fleet);
Part 2 = the agents. Arc: the July 8 email reported "a handful of careful
tests" → since then the project became a self-running fleet: ~15 Projects
each on its own repo, coordinated by one manager Project over a
committed-file message bus; ran in generations (gen-1 → gen-2 → gen-3,
consolidated 07-11 to 8 standing seats — "the scale experiment ended, the
standing program began").

Register requirements, visible throughout the sent email:
- Evidence-first: "every specific maps to a public commit".
- Fairness updates when Anthropic fixed something ("we want to be fair here
  … this looks improved or fixed").
- Honest nulls kept: the spent trading holdout found **no** strategy
  clearing significance — and said so.
- Self-blame owned: "the #1 friction from July 8 had a root cause, and it
  was partly ours."

## Load-bearing findings (each linkable to `8558179`)

- **Throughline:** "strong where it is mechanical … weak where it is social:
  nothing tells a session what it is allowed to do except trying and reading
  the refusal."
- **Merge-permission root cause (b1):** "The classifier was tracking the
  SESSION, not the PR" — three sessions were denied merging PR #68
  (metadata-identical to ten agent-merged PRs around it) because their
  context was saturated with merge-authority text; "auditing the
  merge-permission problem is what tripped the merge-permission classifier."
  Rule distilled: "live human context IS the permission; anything relayed or
  inferred is not." Own contribution owned: the fleet's shared instructions
  coached every seat to "arm auto-merge at creation or REST-merge on green"
  — coaching the fleet to trip the classifier; one instruction fix
  propagated to all lanes.
- **Model mismatch (b2):** routines configured Opus 4.8 woke a session that
  stated "I'm running as Sonnet 5 … given to me directly as fact" (figs
  15a/15b/15c) — with the 2026-07-12 fairness update: newly-created Routines
  now display the running model correctly.
- **Routines spawn without their repo (b3):** `add_repo` at boot "fails ~1
  in 3 times" in one game lane; operator hand-fix works (figs 23a/23b).
- **Value stalls behind owner clicks (b4):** "Three revenue products are
  built and CI-green but cannot go live without the operator … measured in
  unrealized revenue rather than wait time."
- **Two-vantage split (b5):** in auto mode a tool call "raise[s] a
  Deny/Allow prompt on the operator's screen while the identical call
  returns a clean success to the agent."
- **Observability thin (b6)** + fairness update: a real Routines run surface
  arrived (fig-33), "but only runs that happened appear, so a silently
  missed slot leaves no trace at all."
- **Finding 7** = the 2026-07-12 scheduler incident (see the incident chunk).
- **What earned trust (a):** shared memory across 15 repos ("the cold-start
  tax is gone"), durable-state recoverability ("any single agent is
  replaceable because the state outlives it"), born-red card + auto-merge
  composition, agent-armed Routines.
- **Coping patterns (c)** — "each a feature spec written in scar tissue":
  committed-file message bus, self-poll routines, generated fleet roster,
  CAPABILITIES ledger + "never probe a documented wall twice",
  decide-and-flag, owner command vocabulary, boot "know thyself" ritual.
- **Asks (d), in order:** (1) one real wake/scheduling primitive instead of
  three half-ones; (2) capability & config self-awareness; (3) scoped
  owner-declared pre-authorization + document the classifier's line;
  (4) routines carry repo + model; (5) PR events + merge queue; (6) fleet
  visibility one level above the sidebar; (7) non-fatal setup, larger
  child-brief budget, post-hoc session summaries.
- **Operator beats (Part 1):** the never-sleep proposal; "the system even
  dropped the reminder they had set to check on the dropped reminders";
  "My agents ended up building me a website for exactly this because I
  couldn't get it from the product."

## External review pack structure (@ `b0e9ab2`, a dated 07-09 snapshot)

1. §1 The program in one page — non-coder owner; agents plan/build/test/
   review/merge/deploy; committed-file message bus (inbox.md/status.md,
   one-writer-per-file).
2. §2 The central question — every finding classified (a) our
   instructions/setup, (b) platform limitations/bugs, (c) genuinely
   deficient work. Known systemic risk named: "a closed self-verification
   loop: author = gatekeeper = merger … You are the missing control."
3. §3 Repo register — per repo: purpose, health, entry docs, "boldest
   claims to verify" with evidence pointers.
4. §4 Required output shape — findings table with "no URL, no finding";
   verdicts verified / refuted / could-not-verify; exactly 3 recommendations.
5. §5 Integrity notes — "The repos ARE the record"; "The fleet's own
   reports may be wrong. That is the point."; "a `could-not-verify` beats
   an invented confirmation."

Present the pack as the reviewer-onboarding document (10-Project era,
pre-consolidation), not as current fleet state.

## Night review 07-11 (@ `e1090db`) — the bridge document

Most site-worthy points: "The night went well on output, poorly on
realization … almost none of the value is live — it's stuck behind a short
queue of owner clicks"; both owner-flagged platform bugs evidenced
(add_repo denials ~1-in-2 to 1-in-3; model config-vs-actual mismatch);
gate integrity reactive (a PR "auto-merged 28 s before pytest finished");
best-in-fleet report = websites `docs/retro/self-review-2026-07-11.md`
("own mistakes first, each tied to a PR/commit/run"). Bottom line: "a
genuinely strong night of *production* and a weak night of *shipping*."
