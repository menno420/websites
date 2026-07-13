# 2026-07-11 — open_work.py: content-diff classification (rung 4, build-and-hold)

> **Status:** `complete` — PR #147, branch `claude/open-work-content-diff`.
> BUILT UNDER THE #141 MERGE HOLD: the PR is READY + green and WAITS
> UNMERGED for the hold-lift relay (held-list position #1).

- **📊 Model:** Claude Fable 5 · worker · routine-fired build slice (continuous mode, slice 33 — post-18:13Z pass under the build-not-merge clarification) — family from this session's own harness, per ORDER 010.
- **⚑ Self-initiated** (rung 4, contained + reversible; the owner welcomes
  these): scripts/open_work.py has a kill-switch header and nothing depends
  on it — worst case, delete the file.

**What this session was about:** the manager's hold clarification (build,
don't idle) with the buildable-now backlog empty. Rung-4 pick this chain
genuinely believes in: `scripts/open_work.py` classified any branch whose
tip is not an ancestor of main as "unmerged commits ⚠" — but a branch can
carry commits and STILL have zero content diff vs main (an empty probe
commit like claude/probe-dash-mgmt, or content that landed via another
PR's squash like the relayed heartbeat and the merged review-site
branches). The false-positive class misfired FOUR times today, each
costing an MCP PR-state check to clear.

## What was done

- `scripts/open_work.py` — `has_content_diff(sha)` (three-dot
  `git diff --quiet origin/main...sha`); `classify()` gains an OPTIONAL
  `content_diff` map: commits-but-no-tree-diff branches read
  **NO-DIFF / "ignorable, prune candidate"** and leave the ⚠ stranded
  count; a failed comparison (None) KEEPS the alarm — unknown is never
  guessed ignorable; docstring legend updated with the incident.
- `tests/test_open_work_and_rung.py` (+3) — NO-DIFF vs real-diff
  discrimination; old-behavior pin (the param is optional — existing
  callers see the exact pre-change classification); None-stays-alarmed.
- `docs/ideas/backlog.md` — fresh 💡 captured (consumer-first pickup
  parser, below).

## Close-out (auto-drafted 2026-07-11 — edit, don't author)

<!-- substrate:auto-draft -->

**Evidence (regenerated from `git diff origin/main --stat`):**

- scripts touched (1): `scripts/open_work.py`
- tests touched (1): `tests/test_open_work_and_rung.py` (+3)
- docs touched (1): `docs/ideas/backlog.md` (close-out commit)
- sessions touched (1): `.sessions/2026-07-11-open-work-content-diff.md`
- git: branch `claude/open-work-content-diff`, born-red card first commit
  `15aa6ac`, build commit `f71eb8f`, this close-out commit flips the
  gate.
- verify: module 8/8; `python3 -m pytest tests/ -q` → **200 passed**
  (197 + 3); strict gate before push → only the designed born-red HOLD.
  LIVE RUN on the real repo: the probe branch drops from the alarm list
  (7 → 6 ⚠), real branches keep their states verbatim.

**Judgment (the half only the session knows — resolve every slot):**

- Decisions made: no D-entry — a convenience-tool improvement behind an
  optional parameter (zero behavior change for existing callers, pinned).
  Safety decision recorded: None (comparison failed) keeps the alarm.
- Next session should know: PR #147 is HELD green-open under the #141
  merge hold — land it when the lift is relayed (expect a 405
  branch-update if main moved). After it lands, wake rituals get a
  cleaner ⚠ list: NO-DIFF branches need no MCP check.

## 💡 Session idea

**Consume the pickup-persistence convention ahead of adoption** —
captured in `docs/ideas/backlog.md`. Worth having because the
manager-side ask has a buildable local half (parse `pickup: <id> <mins>`
notes tokens into durable per-lane history, honest-empty until written),
and consumer-first shipping is exactly how the tooling:/landing: tokens
rolled out — parser first, first foreign writer the same day.

## ⟲ Previous-session review

The three hold passes (16:52Z, 17:30Z, 18:13Z): compliant but the first
two were idle where this slice shows build-and-hold was possible all
along — the manager's clarification names the miss precisely; lesson:
when a constraint blocks the LAST step of the ceremony, run the ceremony
up to that step instead of skipping the ceremony. The 18:13Z pass's cron
correction (12:17Z slot delivered 13:52Z — 4/4 slots, no schedule drop)
also carries into the pending catch-up heartbeat.
