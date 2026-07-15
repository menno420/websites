# 2026-07-15 — Owner queue: writeback previews — see the exact block before it commits

> **Status:** `in-progress` — branch `claude/queue-preflight-20260715`;
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

**Evidence:** [[fill: files touched, test counts, verify lines, PR]]

**Judgment:** [[fill: decisions + what the next session should know]]

## 💡 Session idea

[[fill: one genuine idea, deduped against docs/ideas/ — honest none if none]]

## ⟲ Previous-session review

[[fill: review of .sessions/2026-07-15-rerun-preflight.md]]
