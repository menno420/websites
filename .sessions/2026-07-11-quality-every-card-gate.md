# 2026-07-11 — quality.yml every-card gate port (rung 3, backlog promotion)

> **Status:** `complete` — PR #120, branch `claude/quality-every-card-gate`.

- **📊 Model:** Claude Fable 5 · worker · routine-fired build slice (continuous mode, slice 23 — 10:55Z nudge) — family from this session's own harness, per ORDER 010.

**What this session was about:** the 10:55Z nudge; ritual clean (no new
orders, no collision), so rung 3 with the twice-deferred designated pick:
**port the kit v1.10.1 every-card session gate into the live folded
`quality.yml` lane**. The live workflow still derived the PR's card with a
`tail -1` single-card picker — the exact multi-card shadowing shape the
staged `.substrate/ci/substrate-gate.yml` fixed: a PR that ADDS a born-red
card and MODIFIES a later-sorting sibling grades only the sibling and
ships the in-progress card green. CI-integrity slice: quality.yml IS the
required check, so the port was validated on this PR's own runs — and
because this PR both adds a card AND touches the gate file, it exercised
the new gate-regen locked-door branch live (semantics may only tighten
mid-PR).

## What was done

- `.github/workflows/quality.yml` — the single-card picker replaced with
  the staged gate's every-card loop, all four lanes: added cards → per-card
  born-red HOLD (absent sentinel + `--added-card`; modified siblings
  advisory-only); modified-only diffs → locked door per card; no card →
  explicit nonexistent sentinel WITHOUT `--require-session-log` (advisory
  by engine contract — never the mtime fallback); PRs touching the gate
  file → full locked door + `--simulate-added-card` per added card.
  `gate_regen` detection adapted from `substrate-gate.yml` to
  `quality.yml` for the folded world. Control fast lane untouched.
- Cautions honored: fast-lane short-circuit byte-identical; born-red HOLD
  semantics identical (same engine verdicts, richer per-card banners).
- `docs/ideas/backlog.md` — gate-port bullet moved to Built; fresh 💡
  captured (fast-lane control gates, below).

## Close-out (auto-drafted 2026-07-11 — edit, don't author)

<!-- substrate:auto-draft -->

**Evidence (corrected — the auto-collected list was tree-wide/polluted by
sibling merges; regenerated from `git diff origin/main --stat`):**

- workflow touched (1): `.github/workflows/quality.yml` (+62/−16)
- docs touched (1): `docs/ideas/backlog.md` (close-out commit)
- sessions touched (1): `.sessions/2026-07-11-quality-every-card-gate.md`
- git: branch `claude/quality-every-card-gate`, born-red card first commit
  `53210e0`, port commit `aea7227`, this close-out commit flips the gate.
- verify (local, pre-push, against the vendored v1.10.1 engine): YAML
  parses; added-card lane exit 1 `[session-card-hold] born-red HOLD`;
  gate-regen lane exit 1 locked door + `simulate-added-card … advisory-only`;
  no-card sentinel exit 0 advisory; locked door on a complete card exit 0;
  card/added/gate_regen detection replicated on this branch's real diff;
  app suite 179 passed.
- verify (LIVE, this PR's first run 29150232291): the new gate-regen
  branch executed on CI — "card … is ADDED but this PR also touches the
  gate workflow itself — locked-door gate", the simulation advisory
  banner, "HOLD (by design)" and the ##[notice] banner, exit 1 as
  designed; flips green with this commit.

**Judgment (the half only the session knows — resolve every slot):**

- Decisions made: no D-entry — a faithful port of the kit-owned staged
  gate into the host-owned folded lane (the fold itself is the
  long-standing recorded decision); the only adaptation is the gate_regen
  path (substrate-gate.yml → quality.yml), documented in the workflow
  comment. Scope decision: the staged gate's fast-lane control-status +
  inbox append-only steps deliberately NOT ported in this slice
  (CI-integrity slice kept minimal on the required check) — captured as
  the follow-up idea instead.
- Next session should know: the every-card gate is LIVE — multi-card PRs
  now grade every card; the no-card sentinel means card-less non-control
  PRs are advisory (unchanged behavior, now explicit). Next designated
  pick: nav manifest; the fast-lane control-gates idea is the natural
  CI-integrity successor.

## 💡 Session idea

**Port the staged fast-lane control gates into quality.yml too** —
captured in `docs/ideas/backlog.md`. Worth having because the folded fast
lane currently short-circuits green with NO validation: the staged gate
runs a control-status check on the fast lane (a heartbeat-deleting
control PR would otherwise merge green and pre-redden the next unrelated
PR) plus an inbox append-only + ORDER-grammar gate on both lanes (a green
control-only PR could otherwise rewrite or erase orders) — and ~half this
lane's PRs are fast-lane heartbeats/claims while the inbox is the fleet's
order of record.

## ⟲ Previous-session review

Slice 22 (ORDER 011: #117 claim + #118 review + #119 heartbeat): clean —
the claim-first pattern worked exactly as the doctrine describes, and the
review's own CI red taught the lesson this slice applied (run the strict
gate BEFORE the first docs push; zero fixup commits here). The #119 merge
504/"already in progress"/retry sequence resolved cleanly — transient
GitHub, not the ruleset; worth remembering that "merge already in
progress" after a 504 usually means the first request is still landing:
poll before retrying.
