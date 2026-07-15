# 2026-07-15 — Owner queue: writeback previews — see the exact block before it commits

> **Status:** `complete` — PR #353, branch `claude/queue-preflight-20260715`;
> stateless POST-to-preview for the three /owner/queue writeback actions
> (complete/assist/note) on the generic `owner_preflight.html`, a
> fail-closed ask-vanished check on the complete confirm, plus the
> coordinator-authorized deletion of the spent #351 merge-verification
> probe file.

- **📊 Model:** Claude Fable · medium · feature build (queue writeback previews + probe-file cleanup)

**What this session is about:** PR B of 2 of the launch-console preflight
pair (PR A: `.sessions/2026-07-15-rerun-preflight.md`, merged as #352).
Today the /owner/queue Complete / Assist / Note forms fire a real repo
write from a one-step form — the owner never sees the composed block, the
ORDER number, or whether the write token is even armed. This slice:

- new stateless `POST /owner/queue/actions/preview` behind
  `require_owner_action`: stores NOTHING (no SQLite row, no commit),
  renders the EXACT composed block (reusing writeback's
  `render_note_block`/`render_assist_block`), the target file + branch,
  the write-token state, for assist the provisional ORDER number with the
  honest "renumbered at commit time" caveat, and for complete the ask's
  live askverify verdict chip — all on the generic
  `owner_preflight.html` PR A landed;
- the preview's confirm re-POSTs the SAME action/target/text verbatim to
  the existing firing routes (contract unchanged); cancel returns to
  /owner/queue;
- one minimal firing-route change: the complete confirm re-finds the
  targeted ask by headline and FAILS CLOSED (honest banner, nothing
  stored/committed) when every source read fine and the ask is gone —
  unreadable sources stay honest-unknown and never fake a "gone";
- retry (already entry_id-pinned) and draft (stores nothing) stay
  preview-exempt, rationale documented on the page;
- cleanup rider: delete `docs/_merge_verification_2026-07-15.md` (its own
  "safe to delete after verification" note; PR #351 completed that
  verification) and drop the now-dangling `docs/audits/README.md` link.

⚑ Self-initiated: no — dispatched under the owner's live work grant
(accept-edits session mode), coordinator-approved mission slice
(scouting cites @ 1e73d8a, re-verified at HEAD 145f5ee).

## Close-out

**Evidence:**

- files touched this branch: `.sessions/2026-07-15-queue-preflight.md` +
  `control/claims/claude-queue-preflight-20260715.md` (first commit; claim
  deleted at this flip), `app/writeback.py` (`_next_order_number` →
  public `next_order_number`, one caller, for the provisional-number
  read — the commit path still re-reads and re-numbers at commit time),
  `app/owner.py` (POST `/owner/queue/actions/preview` behind
  `require_owner_action`; `_render_queue_preview` stateless composition —
  block via writeback's own renderers, facts incl. `_token_state_fact`,
  assist's provisional ORDER from a read-only `github.fetch_file` of the
  live inbox, complete's chip via `askverify.annotate` on the one found
  ask; `_find_ask` + `_sources_fully_readable`; the one confirm-side
  change in `action_queue_complete`), `app/templates/owner_preflight.html`
  (additive optional `block`/`block_label`/`block_note` pre-slot +
  `cancel` link override — PR #352's `p` dict contract untouched),
  `app/templates/owner_queue.html` (all five complete/assist/note forms →
  the preview; retry + draft untouched; the exemption rationale caption),
  `tests/test_owner_queue_preflight.py` (new, 16 tests: zero-write pins —
  raising api_post/api_request recorders + empty-SQLite asserts, PR A's
  pin class; verbatim block per action; provisional-ORDER caveat +
  unreadable-inbox placeholder honesty; token-state both ways; complete
  chip done-detected/unknown; ask-gone-no-confirm and
  unreadable-still-confirms previews; verbatim confirm round-trip with a
  landed-block-matches-preview check; ask-vanished fail-closed at confirm;
  unreadable-proceeds + ask-present-proceeds compat pins; auth+Origin;
  unknown action; would-be-rejected honesty; forms wire-in + retry/draft
  exemption), `docs/audits/README.md` + deleted
  `docs/_merge_verification_2026-07-15.md` (the rider, own commit).
- the 17 ORDER-020 tests in `tests/test_owner_writeback.py` pass
  byte-unchanged (the fail-closed rule triggers only on a POSITIVE
  all-sources-readable absence, so their offline fixtures proceed).
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — **1495 passed, 1 warning** (+16);
  `python3 bootstrap.py check --strict` — green except the DESIGNED
  born-red hold on this card (released by this flip); docs-gate green
  after the probe-file deletion.
- git: branch `claude/queue-preflight-20260715` based on `main` @
  `145f5ee`; PR #353. Isolated `git worktree` (the recorded EnterWorktree
  wall — manual substitute, same as PR A).

**Judgment:**

- Decisions made: (1) the preview is a POST, not a GET — writeback
  payloads run to `TEXT_MAX_CHARS`=4000 chars and do not belong in URLs;
  it sits behind the full `require_owner_action` floor (same-origin +
  rate limit) even though it stores nothing, because it echoes
  owner-typed text back into a page; (2) "gone" at the complete confirm
  means POSITIVELY observed absent — every lane readable AND the
  fleet-manager half `ok` AND the headline missing; any unreadable source
  keeps absence honest-unknown and the assertion proceeds, which is both
  the honest ladder and what keeps the 17 ORDER-020 tests passing
  unchanged; (3) the provisional ORDER number is shown but never carried
  in the confirm payload — pinning it would fight the module's own
  race-safe commit-time numbering, so the caveat does the honesty work
  instead; (4) the audit-entry id renders as `#pending` in the previewed
  block (it is assigned at store time by design) and the lede says so —
  exact-block means exact modulo the two commit-time values, stated, not
  hidden; (5) the general (non-item) note/assist forms route through the
  preview too — same three actions, and a blind general fire next to a
  previewed per-item fire would be an inconsistency the owner feels.
- Next session should know: the draft-approval form (the AI-draft submit)
  still fires directly by the mission's "draft forms untouched" rail —
  see the session idea; `owner_preflight.html` now has the generic
  block/cancel slots, so any future "show text before it lands" flow
  (e.g. prompts writeback, if one ever exists) rides it with zero
  template changes.

## 💡 Session idea

**Route the AI-draft approval through the same preview** — the ✨ draft
flow pre-fills an editable form whose submit still fires the writeback
route directly (this slice deliberately left draft forms untouched). One
attribute change (`action="/owner/queue/actions/preview"` on the draft
card's form, keeping the hidden `action` field) would give AI-drafted
text the same exact-block/token-state/ORDER-caveat preflight as
hand-typed text — arguably MORE valuable there, since the owner is
approving machine-composed words. Zero new routes; the confirm round-trip
already carries the payload verbatim. Deduped against `docs/ideas/`
(backlog + standalone cards): no preview/preflight/draft-routing bullet
exists.

## ⟲ Previous-session review

`.sessions/2026-07-15-rerun-preflight.md` (PR A, #352) is this card's
format reference and its close-out was consumed directly: its "next
session should know" claim — that `owner_preflight.html`'s `p` dict is
generic enough for PR B to ride with zero template changes — held
ALMOST: the writeback preview needed a verbatim-block `<pre>` and a
cancel-target override, both added as optional slots that leave PR A's
pages byte-identical, so the claim was right in contract if not in
literal bytes. Its zero-write pin class (recorders at the client choke
points + state asserts, never inference) transferred wholesale to this
suite, and its decision (2) (fail-closed re-render on the page where
re-confirming is one click) shaped the complete confirm's ask-vanished
banner. Its 💡 (preflight the failed JOBS, not just the run) remains
unpromoted and still worth promoting — this session's inbox-read-for-a-
provisional-fact idiom is the same shape that jobs listing would use.
