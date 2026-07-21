# 2026-07-21 — botsite/: submitter status lookup (opaque ref + GET /submit/status/{ref})

> **Status:** `complete` — branch `claude/botsite-submit-status`; born red,
> this in-progress Status holds the `quality` gate until the slice lands green,
> and the flip to `complete` + PR number is the deliberate LAST code step.

- **📊 Model:** opus-4.8 · medium · feature build

**What this session was about:** plan slice **S5** of
`docs/plans/next-cycle-2026-07-20.md` (the product-frontier cycle) — the one
small new feature in that plan. Work-ladder rung: **order/plan slice** —
coordinator-assigned S5, ranked in the plan's executable slices (value med,
size M, gate none). Before this, a /submit submitter got no reference and no way
to check what happened to their submission; the moderation queue is owner-only,
so there was no honest public read-back at all.

## What was done

- **Schema (`botsite/submissions_store.py`):** added a nullable opaque `ref TEXT`
  column to BOTH `_SCHEMA_SQLITE` and `_SCHEMA_PG`. Nullable on purpose —
  rows written before this column existed carry no ref, so the add needs no data
  migration and the store stays fail-soft. The schema-init path (`_connect`)
  carries an idempotent guard for pre-existing deployed tables: Postgres uses
  native `ALTER TABLE submissions ADD COLUMN IF NOT EXISTS ref TEXT`; SQLite
  (no `IF NOT EXISTS` on ADD COLUMN) uses add-and-swallow the
  `OperationalError` (a fresh DB already has the column from CREATE TABLE).
- **Ref issue + reader:** `create_submission` now mints `ref =
  secrets.token_urlsafe(12)` on INSERT and returns it in the row.
  `submission_status_by_ref(ref) -> str | None` SELECTs the status ONLY
  (never title/body) and returns `None` for an unknown ref OR a not-live store —
  the caller treats both identically so the page never leaks store liveness.
  `list_submissions` (owner-authed queue) now also selects `ref`.
- **Route (`botsite/app.py`):** read-only `GET /submit/status/{ref}` (a GET,
  non-state-changing → no CSRF). Renders a server-rendered Jinja status page;
  honest not-found: unknown ref → HTTP 404 with a "no submission found for that
  reference" page, indistinguishable from the not-live case. `submit_post` now
  passes the returned `ref` into the template context.
- **Templates:** new `botsite/templates/submit_status.html` (hero + status /
  not-found branches, meets the clarity idiom); `submit.html`'s accepted branch
  now shows the ref prominently with a `/submit/status/{ref}` check-status link
  (only when a ref exists — the not-live honest-stub path is unchanged).
- **Tests:** new `botsite/tests/test_submit_status.py` (9 tests) — create issues
  a distinct opaque ref; status-by-ref returns the stored status; unknown ref
  and not-live both read None; the route surfaces the ref on the thank-you
  screen, returns the stored status, leaks no title/body, 404s an unknown ref,
  and 404s when the store is not live. Registered the new parameterized route in
  `test_clarity_structure.py`'s `PARAM_EXPANDERS` (as a page, not a non-page;
  empty expander since the clarity fixture is intentionally not-live).
- Verified (CI-equivalent, `DATABASE_URL` unset):
  `env -u DATABASE_URL python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q`
  → **2162 passed**; `env -u DATABASE_URL python3 bootstrap.py check --strict
  --added-card .sessions/2026-07-21-botsite-submit-status.md` → the only gating
  red is this card's born-red `[session-card-hold]`, released at the flip.

⚑ Self-initiated: no — coordinator-assigned plan slice S5 of
`docs/plans/next-cycle-2026-07-20.md`.

## 💡 Session idea

**The /submit form's `<select>` kinds (`idea`/`bug`/`question`) don't match the
store's `KINDS = ("feature", "bug")`, so `idea` and `question` both silently
collapse to `feature` on POST.** The route coerces any unknown kind to
`KINDS[0]`, so a submitter picking "Question" is filed as a feature with no
signal preserved — the taxonomy the form advertises is not the taxonomy stored.
Worth having because it's a latent honesty gap (the UI promises a distinction the
data throws away) and a one-file fix — either widen `KINDS` to the three the form
offers, or narrow the form's options to the two the store keeps. Deduped against
`docs/ideas/backlog.md` + the plan's NEXT/executable-slice list: not present.
To capture in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

`.sessions/2026-07-19-app-nav-reachability.md` (#450) did the right thing by
deriving its reachability guard from the FastAPI router rather than the
hand-maintained manifest — a strict superset that probes the routes the manifest
omits — and it honestly reported the guard found no real bug, only pinned the
healthy baseline; what it left for a successor (flagged, not folded in) was
consolidating `app/`'s now-two overlapping reachability probes into one, the same
"flag the follow-on, don't stretch this slice" discipline this card follows.
