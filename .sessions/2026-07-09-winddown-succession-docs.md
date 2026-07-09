# 2026-07-09 — gen-1 wind-down: succession docs pack

> **Status:** `complete` — the five reviewed succession/retro deliverables plus
> `scripts/setup-env.sh` landed at their durable homes, wired into the read
> path, verified green (pytest 67 passed exit 0; `check --strict` red only on
> this card's own born-red badge until this flip).

- **📊 Model:** claude-fable-5 (wind-down Phase-3 worker session)

**What this session was about:** the gen-1 → gen-2 handover ends with the
succession pack committed to `main`. Drafts were written and reviewed by the
Phase-2 wind-down workers; this session landed them at their intended homes,
linked them from the read path, and drove the PR to merged.

## What was done

- **Placed the pack:** `docs/retro/gen1-final-retro-2026-07-09.md` (the
  closing gen-1 retrospective), `docs/succession/next-boot-2026-07-09.md`
  (the fresh gen-2 session's entry point), `docs/succession/`
  `proposed-custom-instructions-2026-07-09.md`, `environment-spec-2026-07-09.md`,
  `gen2-feedback-2026-07-09.md`, and `scripts/setup-env.sh` (executable).
- **Read-path wiring:** new "Succession (gen-1 → gen-2)" section in
  `docs/AGENT_ORIENTATION.md` linking all five docs + the script — clears the
  `[reachable] … orphan` gate the environment-spec's assembler note predicted.
- **Stamp discipline:** `check --strict` flagged 23 `[stamp]` findings —
  the new docs' bracketed decision-ID citations gave many decisions a second
  home (e.g. `D-0005 cited from 3 docs … — stamp each decision at one home`).
  Fixed minimally by rewording citations to plain prose ("ledger decision
  0005"), keeping `docs/decisions.md` the single stamp home; no content
  rewritten.
- **Draft-era residue removed:** "Intended home:" lines and the
  environment-spec assembler note deleted; the spec's setup-script pointer now
  names the committed `scripts/setup-env.sh`.
- Verification before push, unpiped, exit codes checked: `python3 -m pytest
  tests/ -q` → 67 passed, exit 0; `python3 bootstrap.py check --strict` →
  exit 1 solely on this card's in-progress badge (the born-red hold working
  as designed), all other findings cleared.

## 💡 Session idea

The `[stamp]` one-home discipline and retrospective/aggregator docs are
structurally at odds: a final retro that cites decision provenance inline
must either double-cite (red) or drop greppable IDs (this session's fix).
Give the kit a sanctioned citation form for non-home references — e.g.
`[see D-0005]` excluded from `check_stamp_discipline` while `[D-0005]`
stays the unique stamp — so provenance stays machine-greppable in exactly
one home *and* readable everywhere else, instead of forcing prose
paraphrases that break `grep D-0005`.

## ⟲ Previous-session review

The queue-state session (PR #46) left an unusually clean runway: its dossier
handoff (scratchpad `winddown/dossier.md`) predicted every wall this session
would hit — the badge vocabulary, the reachability orphan gate, the born-red
message text — and each prediction was verbatim-accurate, which is the
strongest possible endorsement of the "capture exact error text" discipline.
One genuine miss it could not have foreseen but a future assembler should:
it did not flag the `[stamp]` one-home collision that decision-citing
succession docs would trigger (23 findings, the single largest fix of this
session). Improvement for the system: a Phase-2 draft reviewer should run the
drafts through `bootstrap.py check` *staged at their intended homes* — the
environment-spec worker did exactly that (its assembler note caught the
orphan gate) and the practice should be the norm for every drafted doc, which
would have caught the stamp collisions before Phase 3.
