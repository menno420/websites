# 2026-07-13 — botsite: pin step-title provenance on guide exchanges

> **Status:** `in-progress` — branch `claude/step-provenance-0713`; flips to
> `complete` + PR number as the deliberate LAST code step.

- **📊 Model:** Claude Fable 5 · worker · backlog-promotion

**What this session was about:** backlog promotion — the "Guide-question
step provenance — pin what the step SAID when the question was asked"
bullet (`docs/ideas/backlog.md`, captured 2026-07-13 by the
step-question-digest session 💡). `guide_exchanges` rows pin only
`step_index`, so the question digest (PR #304) and both strips
(#294/#298/#303) attribute every persisted question to whatever text
CURRENTLY sits at that index — the first script rewrite the hotspots
trigger silently re-attributes history to the wrong step. This session
snapshots the step's title at ask time and renders it in the digest, with
an honest label for legacy rows that carry no snapshot.

## What was done

- (in progress)

⚑ Self-initiated: no — backlog promotion (the step-provenance bullet in
`docs/ideas/backlog.md`, source `.sessions/2026-07-13-step-question-digest.md` 💡).

## 💡 Session idea

(in progress)

## ⟲ Previous-session review

(in progress)
