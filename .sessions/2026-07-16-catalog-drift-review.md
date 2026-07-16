# 2026-07-16 — catalog drift review: real vs cosmetic, and a correctly-declined write (ORDER 032 overnight cycle 10)

> **Status:** `complete` — branch `claude/catalog-drift-review-20260716`;
> docs-only slice: hand-reviewed all 9 drifted catalog entries from the
> prior cycle's live pin run, filed the findings as ASK-0018.

- **📊 Model:** Claude Sonnet 5 · high · review/verify

**What this session was about:** ORDER 032's next natural step from the
prior cycle's finding (9 of 22 catalog entries drifted from their pinned
venture-lab sha). Rather than blindly bumping shas, this session shallow-
cloned venture-lab (`git clone --depth 1`, confirming git-protocol access
extends beyond raw-content reads too) to get its real current HEAD
(`2348575`), then fetched and hand-diffed each of the 9 drifted packets'
full content (pinned vs current) to classify each: cosmetic wording only,
or a real content/status change.

## What was found

- **7 cosmetic-only** (price/status already correct, only prose/notes
  added upstream): merge-wall-cookbook, ultramarine, de-waag,
  het-trage-woord, de-papieren-sinaasappel, bundle-starter, photo-packs.
- **the-paper-orange — a real, clear-cut status error**: its packet's own
  verdict line reads "GRADUATED — manuscript exists (15,811 words, PR
  #122); publish-ready up to the owner gate." The committed catalog still
  says `"status": "parked"` with a note claiming no manuscript exists —
  false today. A public page currently understates a title's actual
  readiness.
- **the-night-kiln — a real but partial correction**: the packet's own
  "no manuscript" park is explicitly RELEASED (three complete manuscripts,
  real word counts, on venture-lab main) — but the packet's own verdict
  says the remaining blocker is "the packet's own graduation pass... a
  seat follow-up," not an owner click. So `status: "parked"` is still
  technically accurate; only the status_note's factual claim needs fixing.

## What was NOT done, and why

Attempted the mechanical + content fix directly (a Python script bumping
the 7 sha pins and correcting the 2 status/status_note fields) — **the
Claude Code auto-mode permission classifier blocked the write**, reason:
"Blocked by classifier." No partial write occurred (verified via `git
diff` immediately after — clean). Per the harness's own guidance on such a
block ("should not attempt to work around this denial... STOP and explain
... let the user decide"), this session did not retry through another tool
path. This matches a documented 2026-07-15 CAPABILITIES.md finding almost
exactly: the classifier does not treat ORDER 032's relayed/injected
authorization as sufficient for certain writes on its own — here, writing
PUBLIC product-catalog status data based on this session's own cross-repo
inference, not a direct user instruction. Judged correct on reflection:
changing what `/products/catalog` tells visitors about a book's
readiness IS the kind of consequential, judgment-laden write that
deserves a human or a session with clearer authorization, even though the
specific correction (the-paper-orange) is well-evidenced.

Filed the full findings — exact recommended field values for all 9
entries — as **ASK-0018** in `docs/owner/OWNER-ACTIONS.md`, so either the
owner or a future authorized session can apply them directly without
re-deriving the diffs.

⚑ Self-initiated: yes — ORDER 032's backlog-slice mandate; this is the
direct follow-up the prior cycle's session card and the heartbeat both
named as the next task.

## Landing

Same named blocker as every branch this lane has pushed tonight:
**ASK-0017** (a different ask than this session's own ASK-0018 — see the
ID-collision note inline in the OWNER-ACTIONS.md entry: this branch and
`claude/pr-tooling-ask-20260716` both forked before the other's ASK
landed, so both currently claim adjacent-but-different numbers; whichever
lands first keeps its number). Pushed for an interactive session or the
owner.

## 💡 Session idea

No new idea this session — this was itself the follow-up to a previously
captured idea, not a source of a new one.

## ⟲ Previous-session review

The catalog-sha-drift-pin session (this lane, ~23:37Z) built and
live-verified the pin correctly, including flagging its 9 findings
honestly rather than either ignoring them or over-claiming certainty. It
explicitly deferred acting on the findings to a follow-up — this session
is that follow-up, and confirms the deferral was the right call: two of
the nine needed real judgment (not just a sha bump), and the classifier's
block on writing them directly validates treating catalog-content changes
as owner/authorized-session territory rather than something to auto-apply
from a heartbeat cycle.
