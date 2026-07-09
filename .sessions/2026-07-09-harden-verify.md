# 2026-07-09 — Hardening + verification batch (P0-verify · P1a/b/c · P2-verify · OWNER-ACTIONS)

> **Status:** `complete` — the real work ships in the fix-forward PR from
> `claude/harden-verify-work`. Verified #16's definition-of-done, added an
> enforcing guard against the ambient production Railway IDs, a reusable 3-URL
> healthcheck, strengthened the stub labels, and seeded the OWNER-ACTIONS doc.
>
> **⚠️ Born-red gate did NOT hold here (workflow finding).** The first PR (#19,
> `claude/harden-verify`) opened with an in-progress card and auto-merge armed;
> `quality` went green on the card-only commit and GitHub auto-merged it before
> the work commit was pushed — so #19 merged the born-red card ALONE. This repo's
> `bootstrap.py check --require-session-log` did not fail on the `in-progress`
> card, so the born-red mechanism the workflow assumes is not actually enforced.
> Recovered by fix-forward (this branch), and captured as a workflow bug below.

- **📊 Model:** claude-opus-4-8 (pre-v1.2.0 backfill; builder-session subagent, inherited — not independently confirmed)

## P0 — verify #16 definition-of-done (DONE)

- `.substrate/state.json` `session_count` = **12** (≥ 12).
- **0** `UNRENDERED` banners / unfilled `${…}` slots across the 8 binding docs
  (CONSTITUTION.md, docs/architecture.md, ownership.md, runtime_contracts.md,
  collaboration-model.md, AGENT_ORIENTATION.md, owner-profile.md,
  ai-project-workflow.md). Remaining `UNRENDERED` hits in the repo are historical
  narrative (`.sessions/2026-07-09-engage-kit.md`, `docs/decisions.md`) and the
  substrate-internal `.substrate/claude/CLAUDE.md` template — none in the 8.
- `.github/workflows/quality.yml` exists and is **green** on `main` head
  `f2020c6` (run 29014891623, conclusion success). **P0 = DONE, no remainder.**

## P1a — enforcing guard vs. the ambient production Railway IDs

- `scripts/check_no_ambient_railway_ids.py` — deterministic, pure-stdlib. Fails
  CI if any tracked non-markdown file *reads* `RAILWAY_PROJECT_ID` /
  `RAILWAY_SERVICE_ID` / `RAILWAY_ENVIRONMENT_ID` from the env
  (`os.environ[...]`, `.get(...)`, `os.getenv(...)`, `${...}`/`$...`), AND
  asserts a safety doc carries the three-ID warning. Provenance/kill-switch
  header included. Wired into `quality.yml` as step "no ambient production
  Railway IDs".
- Verified: clean repo → exit 0; git-added planted `os.environ["RAILWAY_PROJECT_ID"]`
  → exit 1 with the offending line; clean again after removal.
- `tests/test_check_no_ambient_railway_ids.py` (6 tests): clean pass, doc-warning
  present, every env-read shape matches, the safe explicit `superbot-websites`
  UUID literals do NOT match, planted violation detected.
- Docs: loud `docs/RAILWAY-SAFETY.md` (`binding`) + a warning block in
  `docs/deployment.md`; both linked from `docs/current-state.md`.

## P1b — stub labels verified + strengthened

Against **live served HTML**:
- dashboard `/admin` (public) → `200`; renders "(stub)", "Requires owner wiring",
  "not connected to the live bot", all controls `aria-disabled` spans + "disabled
  — not connected". Already unmistakable → left as-is.
- botsite `/submit` GET → `200`; POST → `200` with "not live yet / not yet
  provisioned / not stored / Nothing here pretends [to have saved it]". The GET
  form's "Send submission" is the one clickable mutating control, so
  **strengthened**: added a visible `sb-badge sb-badge-warn` "Stub — not wired"
  beside the button + an explicit "does not store or send your message anywhere
  yet" note. Verified rendered locally.

## P1c — reusable 3-URL healthcheck (RAN)

`scripts/healthcheck.py` GETs `/healthz` and `/` on all three services, prints a
table, exits non-zero if any is down. Provenance/kill-switch header. Verbatim:

```
service        endpoint   status  ok
-------------  ---------  ------  --
control-plane  /healthz      200  PASS
control-plane  /             200  PASS
botsite        /healthz      200  PASS
botsite        /             200  PASS
dashboard      /healthz      200  PASS
dashboard      /             200  PASS

RESULT: all healthy
```

Documented in `docs/deployment.md` § Post-deploy verification.

## P2 — board renders live signals for all four repos (VERIFIED)

Curled the live board (`/api/readiness.json` + `/`). All four repo rows render
real data — no blank/unknown-where-data-exists:

| repo | rulesets | required + run-state | CODEOWNERS | secrets | auto-merge | open PRs |
|---|---|---|---|---|---|---|
| superbot | 2 active | `code-quality` in_progress (live) | absent (no file) | 5 (count) | allowed + enabler | 1 (oldest #1889) |
| superbot-next | 1 active | 6 checks all success; `report` red-by-design annotated | present, not enforced | 0 | allowed, no enabler | 1 (#54) |
| substrate-kit | 1 active | rows "missing" — configured contexts ≠ live run names on a mid-run head | present, not enforced | 0 | allowed + enabler | 1 (#25) |
| websites | 1 active | `quality` success (live) | absent (no file) | 0 | allowed | 0 |

The only non-green cells are legitimately real states (no CODEOWNERS file;
substrate-kit's ruleset check names don't match its live run names while it is
mid-run; superbot-next `report` red-by-design). **No `app/readiness.py` fix
needed.** (Observation flagged: `config.REPOS` `expected_required_checks` for
superbot + superbot-next are stale vs. live `configured` — ledger drift, not a
render bug; left for a follow-up rather than silently rewriting owner-intent.)

## OWNER-ACTIONS doc

`docs/owner/OWNER-ACTIONS.md` (`owner-guidance`) — living list. Open: /admin
control, /submit Postgres, redeploy hook, custom domains, v1-design-vs-restyle,
OLD-site cutover. Decided/resolved: required `quality` check (owner-set),
auth-drop, and the superbot kickoff-doc README link (now 200 — the doc merged, so
that item is resolved, not open).

## Verification

- `python3 bootstrap.py check --strict --require-session-log` → green.
- `python3 -m pytest tests/ botsite/tests dashboard/tests -q` → **73 passed**
  (was 67; +6 guard tests). No new runtime dep (guard + healthcheck are stdlib).
- Guard: clean exit 0, planted violation exit 1. Healthcheck: all six 200.

## ⚑ Self-initiated

None beyond the directed scope — the whole batch is owner-directed. Fixed
visible ledger drift on sight: added PR #18 to Recently-shipped and corrected
the stale "no required checks / ruleset on this repo yet" line in current-state.md.

## 💡 Session idea

**Make the readiness board derive `expected_required_checks` from the live
ruleset by default, keeping the hand-maintained list only as a red-by-design
override.** P2 surfaced that `config.REPOS[...]["expected_required_checks"]` for
superbot and superbot-next has drifted from what the ruleset actually requires
(e.g. superbot-next expects `tests/checkers/…` but the live ruleset requires
`code-quality/manifest-validate/architecture/sim-gate/golden-parity/check_compat_frozen`).
The board already fetches the live `configured` set — so "configured vs expected"
is two lists that can silently disagree. Deriving expected from configured (and
treating the config list purely as an override for known red-by-design cases)
removes a whole drift class, the same enforce-don't-exhort instinct the kit
embodies. This is the same idea the PR #18 card raised as a workflow improvement —
recording it here as a concrete, buildable follow-up so it stops being noticed
and never done.

## ⟲ Previous-session review

The journal-search-mobile session (PR #18, [D-0014]) did a genuinely high-value
thing well: its **STEP 0** empirically *proved* the `quality` gate is a required
check (reading `mergeable_state: blocked` with only `quality` pending) instead of
assuming it — exactly the "a green check that contradicts evidence is a bug in
the check" discipline. What it left for this session: it flagged the
`expected_required_checks` drift for the *websites* row and fixed that one row,
but the **same drift already existed on the superbot + superbot-next rows** and
was left unaddressed, so the board still ships two hand-maintained lists that
disagree with live state. **Workflow improvement surfaced:** point-fixing one
instance of a drift class (one repo's row) without checking the others is how
drift survives — a "fix the class, not the instance" habit (grep every peer for
the same shape before calling a drift fixed) belongs alongside the bugs-first
rule. Captured concretely as this session's 💡 idea.
