# 2026-07-11 — Fast-lane control gates: status + inbox append-only in quality.yml (rung 3)

> **Status:** `complete` — PR #125, branch `claude/fastlane-control-gates`;
> rescue #124 landed first this wake.

- **📊 Model:** Claude Fable 5 · worker · routine-fired build slice (continuous mode, slice 25 — 12:07Z nudge) — family from this session's own harness, per ORDER 010.

**What this session was about:** the 12:07Z nudge, which rituals right
after the ~12:00Z fire window. THE FIRE RAN and stranded its heartbeat
(ritual-only session, no PR tooling — it stamped `tooling: ritual-only` +
`landing: pushed-unmerged` exactly per protocol); rescued VERBATIM first
as PR #124 (rescue #3; reliability watch now: 04:03Z stranded, 08:00Z
silent, 12:05Z stranded-then-relayed). No new orders, so rung 3 with the
designated pick: **fast-lane control gates** — the folded quality.yml
fast lane short-circuited GREEN with no validation at all, while the
staged substrate-gate.yml runs (a) a control-status gate ON the fast lane
(a heartbeat-breaking control PR would otherwise merge green and
pre-redden the next unrelated PR) and (b) an inbox append-only + ORDER
grammar gate on BOTH lanes (a green control-only PR could otherwise
rewrite or erase orders — the inbox is the fleet's order of record).

## What was done

- `.github/workflows/quality.yml` (+42) — two steps ported from the
  staged gate, verbatim mechanics: control-status gate conditioned ON the
  fast lane (`check --strict --status-only`, stdlib-only system python3,
  no setup-python — the lane stays fast, heartbeat PRs stay card-free);
  inbox append-only gate on BOTH lanes (`--inbox-base` fed the merge-base
  blob git extracts in bash; self-skips when control/inbox.md untouched).
- Pre-write caution honored: `--status-only` and `--inbox-base` verified
  present in the vendored v1.10.1 bootstrap.py before writing.
- `docs/ideas/backlog.md` — fast-lane-gates bullet moved to Built; fresh
  💡 captured (pin the gate behaviors as suite tests, below).

## Close-out (auto-drafted 2026-07-11 — edit, don't author)

<!-- substrate:auto-draft -->

**Evidence (corrected — the auto-collected list was tree-wide/polluted by
sibling merges; regenerated from `git diff origin/main --stat`):**

- workflow touched (1): `.github/workflows/quality.yml` (+42)
- docs touched (1): `docs/ideas/backlog.md` (close-out commit)
- sessions touched (1): `.sessions/2026-07-11-fastlane-control-gates.md`
- rescue this wake (separate PR): #124 — verbatim relay of the 12:05Z
  fire's stranded control-only heartbeat (merged `dd10cc9`).
- git: branch `claude/fastlane-control-gates`, born-red card first commit
  `37a828b`, port commit `800f52b`, this close-out commit flips the gate.
- verify (local, pre-push, vendored v1.10.1 engine): clean heartbeat →
  exit 0; broken heartbeat → exit 1 `[status-no-heartbeat]`; inbox
  rewrite (ORDER erased) → exit 1 `[inbox-not-append]`; pure ORDER
  append → exit 0. YAML parses; app suite 182 passed; strict gate before
  push → only the designed born-red HOLD. Validation gotcha caught in
  the act: the first rewrite check printed the finding but reported
  exit 0 because `$?` came from `tail` in a pipeline — re-verified
  unpiped (exit 1).
- verify (live): run 29152280752 red on this PR's first head = the
  designed gate-regen locked-door HOLD on this born-red card (verbatim
  "HOLD (by design)" + the ##[notice] banner), NOT a port regression —
  this PR is non-control, so the new gates took their skip branches
  cleanly; the fast-lane + status-gate branch gets its live validation
  on this slice's closing heartbeat PR.

**Judgment (the half only the session knows — resolve every slot):**

- Decisions made: no D-entry — completing the already-decided fold of
  the kit's staged gate into the single required lane (#120 did the card
  lanes; this does the control lanes). The fast lane is deliberately no
  longer a pure no-op: ~1s of stdlib validation is the cost of making
  heartbeat-breaking and order-rewriting control PRs impossible to merge
  green.
- Next session should know: heartbeat PRs now RUN the status checker —
  a malformed heartbeat overwrite will red its own fast-lane PR (fix the
  heartbeat, don't fight the gate); inbox appends are grammar-checked.
  Remaining buildable: route-level clock freeze, order-ack latency line,
  nav-scan glob, gate-behavior suite tests (this slice's 💡).

## 💡 Session idea

**Pin the control-gate behaviors as suite tests** — captured in
`docs/ideas/backlog.md`. Worth having because the four lane behaviors
(clean 0 / broken heartbeat 1 / inbox rewrite 1 / pure append 0) were
validated by hand at port time and that evidence lives in a PR body; a
`tests/test_control_gates.py` driving the real CLI against fixtures —
the `test_born_red_session_gate.py` pattern — makes an engine regression
red the suite instead of surfacing on a live control PR (possibly a
manager's inbox append).

## ⟲ Previous-session review

Slice 24 (#122 nav manifest + heartbeat #123): clean — the manifest
rendered live identically and the membership guard held. The 12:00Z-fire
handling this wake validated the whole protocol stack end-to-end: the
fired session used the `tooling:` token (#107), the `landing:
pushed-unmerged` line (#67), and the relay doctrine (#99) — all three
were this chain's own builds, and the rescue took four minutes because
every piece was already documented. One self-caught validation lesson
recorded above: never read `$?` after a pipeline when the exit code is
the evidence.
