# 2026-07-18 — Dashboard /env config-drift flags (B6)

> **Status:** `complete` — branch `claude/env-drift-flags`; the dashboard `/env`
> page rendered the bot's env-usage map (every variable → the files/lines that
> read it, required or optional) but never said whether those declarations were
> internally consistent. B6 adds a config-drift check: a pure classifier
> (`classify_env_var` + `env_drift` in `dashboard/data_source.py`) flags
> variables whose DECLARED requiredness disagrees with how the code actually
> reads them — `required_but_defaulted` (declared required, every read defaults)
> and `optional_but_undefended` (declared optional, a read has no fallback) —
> surfaced as an additive section on `/env` that degrades to an honest
> "No config drift detected" line. Names/locations only, never a value; `/env`
> stays a read-only GET.

- **📊 Model:** Opus · high · feature build — dashboard /env config-drift flags

**What this session is about:** B6 — the last open seat item from the groomed
next-cycle queue. The dashboard `/env` page renders the bot's env-usage MAP
(every variable the bot reads → the files/lines that read it, required or
optional, by layer) but said nothing about whether those declarations are
internally consistent. This session adds a config-drift check.

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
  - `dashboard/tests/test_env_drift.py` — classifier + summary unit tests (10).
  - `dashboard/tests/test_dashboard.py` — two /env route tests (clean state, flagged state).
- test coverage (+12): 10 classifier/summary units in `test_env_drift.py`
  (each drift bucket fires on the right shape; required-with-hard-read and
  optional-all-defaulted stay clean; missing/blank fields degrade clean; the
  `env_drift` summary counts + flags a mixed feed and reports clean/empty feeds),
  plus 2 route tests (`test_env_drift_clean_state_renders` — the default fixture's
  consistent DATABASE_URL shows the honest clean line; `test_env_drift_flags_render`
  — a feed carrying both drift shapes surfaces both flags with their buckets and
  human labels, and the consistent var is not flagged).
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q`
  — **1940 passed, 1 warning** (exit 0; 1928 baseline + 12 new); `python3
  bootstrap.py check --strict` — exit 0 once this card flips complete (the only
  red before the flip was the DESIGNED born-red hold on this `in-progress` card;
  the remaining advisories — orientation-headroom and a model-line payload on
  `2026-07-18-release-drift-banner.md` — are pre-existing and on other cards,
  never exit-affecting).
- git: branch `claude/env-drift-flags` from `origin/main` @ `c27d01c` (#423);
  commits `69c0f70` (born-red card + claim), `e68f37b` (config-drift flags +
  tests), + this flip.

**Judgment:**

- Decisions made: (1) Honest over impressive — the two named buckets in the brief
  (referenced-but-unset / set-but-unused) require the live Railway set-var list,
  which is never committed (secret-safety invariant); rather than fabricate that
  record I scoped the flags to the declared-vs-code drift the feed genuinely
  carries, and documented the boundary in code + card. (2) Kept the classifier a
  pure function over the feed's own fields (`required`, `has_default`) so it reads
  no value and degrades to clean on missing/blank fields, never raising. (3)
  Surfaced the flags as an additive section above the existing usage table,
  degrading to a clean-state line — the map itself is unchanged. (4) Rendered the
  model line in the checker's taught form (`<model> · <effort> · <task-class>`
  with effort ∈ {low,medium,high}, class = feature build) so it stays clean in the
  PL-004 dataset rather than a free-text variant.
- Next session should pick up: with B6 shipped, the groomed next-cycle seat queue
  (`docs/plans/next-cycle-2026-07-18.md`) is drained of executable feature slices —
  substantive new growth now depends on owner product decisions or hub-venue infra.
  The natural follow-on inside this surface is the idea below (a producer-side
  contract so the drift signal can eventually cover the live set-var axis honestly).

## 💡 Session idea

**Teach superbot's env-map generator to emit a per-usage `access` kind so the
drift check can grow a real "unused-declared" axis.** Today the honest signal is
bounded to declared-requiredness vs code-defaults because the feed carries no
record of what is actually configured. If superbot's static-analysis generator
additionally emitted, per variable, whether it is read via a hard subscript
(`os.environ[X]`), a defaulted get (`os.environ.get(X, default)`), or a bare get
(`os.environ.get(X)` → silent `None`), the dashboard could distinguish a
truly-undefended read from a get-with-`None`-tolerance and sharpen
`optional_but_undefended` into two honest sub-buckets — without ever committing a
value. It stays inside the secret-safety invariant (kinds of access, never
values) and is a pure producer-side enrichment: the consumer classifier already
degrades cleanly when the field is absent, so it can ship first and light up when
the feed catches up. Distinct from committing Railway's set-var list (which the
invariant forbids) — this enriches the *reference* side, the only side we own.

## ⟲ Previous-session review

`.sessions/2026-07-18-next-cycle-plan.md` — the planning pass that landed as #423
groomed the next-cycle queue and named B6 as the sole remaining executable feature
slice; it landed clean (and, per the coordinator, already deleted its own
`next-cycle-plan` claim at its flip, so there was no orphaned merged-branch claim
left for this session to sweep). This session is that plan executing to the letter:
the queue pointed at B6, B6 shipped. The planning pass's discipline — name the
honest frontier rather than manufacture work — is exactly what kept B6 scoped to
the genuinely-computable drift signal instead of a fabricated set-var check.
