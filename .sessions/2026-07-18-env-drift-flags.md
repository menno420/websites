# 2026-07-18 — Dashboard /env config-drift flags (B6)

> **Status:** `in-progress`

- **📊 Model:** [[fill: model · effort · task-class — resolved at flip]]

**What this session is about:** B6 — the last open seat item from the groomed
next-cycle queue. The dashboard `/env` page renders the bot's env-usage MAP
(every variable → the files/lines that read it, required or optional, by layer)
but says nothing about whether those declarations are internally consistent. This
session adds a config-drift check.

HONEST SCOPE, stated up front: the env map is STATIC ANALYSIS of the bot source —
variable names + code locations only, and per the secret-safety invariant it
NEVER carries a value. Railway's live set-var list is deliberately never committed
anywhere this service can read, so the LITERAL "referenced-but-unset" (referenced
in code but not set in Railway) and "set-but-unused" (set in Railway, read by
nothing) are NOT honestly computable here — there is no committed record of what
is set, and this session does NOT fabricate one. What IS genuinely computable, from
fields already in the committed feed (`required` + per-usage `has_default`), is
drift between a variable's DECLARED requiredness and how the code actually reads
it: `required_but_defaulted` (declared required, yet every read supplies a default
— the requiredness is misleading) and `optional_but_undefended` (declared optional,
yet a read has no fallback — the honest analog of a referenced-but-unset RISK).
Everything else is clean. The classifier is a pure function over the feed; `/env`
is a read-only GET, so no CSRF surface and no state change. Born red on this
`in-progress` card; flips to `complete` on green.

⚑ Self-initiated: no — coordinator-dispatched backlog slice (B6).

## Close-out

**Evidence:**

- files touched this branch:
  - `control/claims/env-drift-flags.md` — this session's claim (born-red card + work).
  - `.sessions/2026-07-18-env-drift-flags.md` — this card.
  - `dashboard/data_source.py` — added `classify_env_var` (pure, per-var drift
    bucket) + `env_drift` (feed summary: flagged vars, counts, `any`), with a
    scope-honesty comment on why the literal referenced-but-unset / set-but-unused
    signal is out of reach and what is computed instead. No value is ever read.
  - `dashboard/app.py` — `env_page` now passes `env_drift` into the template ctx.
  - `dashboard/templates/env.html` — a config-drift section: a flagged banner
    (per-var bucket badge + plain-language reason) when drift exists, degrading to
    an honest "No config drift detected" line when clean. Names/locations only.
  - `dashboard/tests/test_env_drift.py` — classifier + summary unit tests.
  - `dashboard/tests/test_dashboard.py` — two /env route tests (clean state, flagged state).
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q`
  — [[fill: verify result — pytest summary line]]; `python3 bootstrap.py check --strict`
  — [[fill: bootstrap check result]].
- git: branch `claude/env-drift-flags`; commits [[fill: commit trail — resolved at flip]].

**Judgment:**

- Decisions made: (1) Honest over impressive — the two named buckets in the brief
  (referenced-but-unset / set-but-unused) require the live Railway set-var list,
  which is never committed (secret-safety invariant); rather than fabricate that
  record I scoped the flags to the declared-vs-code drift the feed genuinely
  carries, and documented the boundary in code + card. (2) Kept the classifier a
  pure function over the feed's own fields (`required`, `has_default`) so it reads
  no value and degrades to clean on missing/blank fields, never raising. (3)
  Surfaced the flags as an additive section above the existing usage table,
  degrading to a clean-state line — the map itself is unchanged.
- Next session should pick up: [[fill: Next-session pointer — resolved at flip]].

## 💡 Session idea

[[fill: session idea — resolved at flip]]

## ⟲ Previous-session review

[[fill: previous-session remark — resolved at flip]]
