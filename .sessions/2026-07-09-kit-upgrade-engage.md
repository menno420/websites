# 2026-07-09 — substrate-kit upgrade v1.0.0 → v1.2.0 + engagement audit

> **Status:** `complete` — PR #31 (`claude/kit-upgrade-engage`). First
> release-artifact kit upgrade this repo has run; engagement gate reads
> **ENGAGED**; full app suite green (95 passed).

- **📊 Model:** claude-fable-5 · high · mechanical refactor

## Honest inventory first (the briefed premise was stale)

This session was briefed off a fleet review that called websites "stranded":
unrendered `${...}` docs, `session_count` 0, inert `.claude/`, **no CI on
main**. Verified against the shipped repo before acting — most of that was
already fixed by PRs #16 (engage-kit) / #19–#20 (born-red gate fix, hardening):

- `session_count` **12**, stage `integration`, all 12 interview slots filled
  with real values; **0** UNRENDERED banners across the planted binding docs.
- CI **exists and is REQUIRED**: `.github/workflows/quality.yml` (kit
  `check --strict --require-session-log`, diff-aware card selection, Railway-ID
  guard, all three pytest suites) — required-check status verified live in
  PR #18's STEP 0.
- What WAS still true from the review: kit pinned at **v1.0.0** (two releases
  behind), **no `.claude/` at all** (the staged working agreement still sat
  under its UNRENDERED banner in `.substrate/claude/`), two interview slots
  lingering (`integration_mode` pending, `doc_roots` provisional), and no
  v1.2.0 control fast lane — every heartbeat paid the full heavy suite.

## What I did

1. **Upgrade v1.0.0 → v1.2.0 via the kit's §4.3 flow** ([D-0019]). Release
   assets fetched from the v1.2.0 GitHub Release; `bootstrap.py` sha256
   `258ab02aa54811d91b013f67a15d4bf13e8fc917421434746dd3ca26bc59098c` matched
   `release.json` + `bootstrap.py.sha256` + the coordinator-relayed pin.
   `python3 bootstrap.py.new upgrade` self-verified ("verified: sha256 +
   version against release.json"), archived first
   (`.substrate/backup/bootstrap-1.0.0.py` + `state.json` — the committed
   `--rollback` path, superbot-next convention), replaced the vendored dist,
   regenerated all staged artifacts (incl. the new
   `.substrate/ci/substrate-gate.yml`), recorded `kit_version 1.2.0`, and
   cleaned up its own inputs. **Upgrade-report classification**
   (`.substrate/upgrade-report.md`): **15 consumer-edited** ("template
   unchanged — consumer-owned, nothing to apply") · **3 diverged** — the
   `control/` trio, hand-planted from the superbot fleet spec (#25) before the
   kit shipped control templates, so no recorded hash ("pre-1.0 install —
   manual review"). Manual review done: kept the live copies; noted in
   status.md that the manager may re-plant README from the richer kit template.
2. **Engagement close-out.** `adopt --include-claude` planted
   `.claude/CLAUDE.md` — **fully rendered** through the filled slot context
   (0 `${...}`, no banner; "websites is built in Python 3.12 (FastAPI + Jinja2
   + httpx…)") — plus `.claude/settings.json` (the four advisory, fail-open
   kit hooks). Answered the last interview slots with real values:
   `integration_mode = guided` (confirming the live mode), `doc_roots = docs`
   (graduating the derived value). `ask` → "no pending questions — all slots
   filled"; `render --live` → "0 unfilled placeholder(s)"; adopt printed
   **"ENGAGED — the post-adopt gate is green."**
3. **CI: v1.2.0 control fast lane folded into `quality.yml`.** A
   `control/**`-only diff (status heartbeat, inbox append) now short-circuits
   the required job GREEN **in-job** — deliberately never `paths-ignore`
   (a required context that never reports jams the merge). Heartbeats stop
   paying the 3-suite install+test cost and need no session card.
   **Deliberately did NOT install a second `substrate-gate.yml` workflow**,
   despite the briefing: `quality.yml` already runs the kit gate (the
   engagement checker's own docstring accepts a hand-rolled gate — "a CI door
   exists", not "our exact file was copied"), and D-0017 established the
   one-enforced-gate rule for exactly this repo.
4. **Fresh `control/status.md` heartbeat** in the new checker's ISO-8601 shape
   (`updated: 2026-07-09T14:21Z`) — the old `2026-07-09 (session)` only
   parsed by the accident of its date prefix.
5. **Test fallout fixed properly**: `tests/test_born_red_session_gate.py` —
   fixture card gains the new v1.2.0 Model-line marker; the `kit_version`
   pin moves 1.0.0 → 1.2.0 (kept an EXACT pin so re-vendors stay conscious).
   (Kit bug found while closing: `parse_model_line` harvests the LAST
   needle-containing line, so prose that merely *mentions* the marker after
   the real telemetry line shadows it and the harvest fails — reported
   upstream via the run report; this card wordsmiths around it.)
6. **Docs**: [D-0019] decision entry; `current-state.md` Recently-shipped.

## Verification

- Before (v1.0.0, pre-session): `python3 bootstrap.py check --strict` →
  "all checks passed", exit 0.
- After upgrade, born-red card in flight: exit 1, held **only** by this card
  ("missing: Session idea, Previous-session review, Model line, a completed
  Status") — the gate working exactly as designed, now with the v1.2.0
  Model-line needle.
- After flip (recorded below in the run report): exit 0 expected on
  `check --strict --require-session-log --session-log <this card>`.
- `python3 -m pytest tests/ botsite/tests dashboard/tests -q` → **95 passed**
  (pinned deps freshly installed; fastapi et al. are not preinstalled here).
- `python3 scripts/check_no_ambient_railway_ids.py` → OK.

## 💡 Session idea

**A kit-version cell on the readiness board.** This session existed because a
fleet review went stale: it said websites was stranded at an old kit state
when the repo had moved on. The control-plane board already fetches each
fleet repo's files over raw GitHub with a TTL cache — add a "kit" column that
reads each repo's `substrate.config.json` → `kit_version` and compares it to
the latest substrate-kit release tag (one extra cached API call). The manager
then sees version lag live (`1.0.0 ← 1.2.0 available`) instead of via
hand-written reviews that rot within hours on a day like today. Small,
read-only, uses existing machinery; websites-side only.

## ⟲ Previous-session review

The ORDER 001 lane (#26–#28, deploy-drift cell + status reconciles) was
disciplined where it mattered: it refused to invent manager-owned files when
`control/README.md`/`inbox.md` were absent, acked orders only in status.md,
and its drift cell immediately caught a real deploy lag — the feature paying
for itself the same day. Two things it left for this session to find: its
heartbeat line `updated: 2026-07-09 (session)` only parsed under the new
v1.2.0 freshness checker by the accident of its date prefix (a `(session)`
suffix on a different field order would have read as no-heartbeat), and each
of its status-only commits paid the full 3-suite CI cost for a two-line
coordination write — the fast lane this session ports is the enforcing fix.
System improvement shipped rather than exhorted: heartbeats are now free.
(Also honoring the #11 console-feed-contract card as the local bar for
verification evidence — this card copies its before/after style.)

## 📤 Run report

- **Did:** kit v1.0.0 → v1.2.0 (§4.3, sha256-verified, archive-first,
  report: 15 consumer-edited / 3 diverged); `.claude/` wired rendered;
  last 2 slots answered; ENGAGED; control fast lane in `quality.yml`;
  ISO heartbeat; born-red test pin bumped; [D-0019] + ledger.
  · **Outcome:** shipped (PR #31)
- **⚑ Self-initiated:** (1) did NOT install the briefed duplicate
  `substrate-gate.yml` — the "websites has no CI" premise was stale (CI
  required since #16/#18); ported the v1.2.0 fast lane into the single
  enforced `quality` gate instead (D-0017 rule). (2) `adopt
  --include-claude` (working agreement + advisory hooks — new live surface).
  (3) `kit_version` test pin bump 1.0.0 → 1.2.0. (4) status.md heartbeat
  format hardened to ISO-8601.
- **↪ Next:** consider the board kit-version cell (idea above); manager may
  re-plant `control/README.md` from the kit's generalized template (documents
  the fast-lane + zero-check-runs lessons websites' spec copy predates).
