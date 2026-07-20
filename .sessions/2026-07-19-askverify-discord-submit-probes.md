# 2026-07-19 — app/: askverify probes for Discord-login + submit-live signals

> **Status:** `complete` — branch `claude/askverify-discord-submit-probes`,
> PR #451. Born red: this card's in-progress Status held the `quality` gate red
> until the new read-only probes landed green; this flip to `complete` is the
> LAST step and releases the `[session-card-hold]`.

- **📊 Model:** opus-4.8 · medium · feature build

**What this session is about:** `app/askverify.py` auto-flips owner-action
chips from "still open" to "done-detected" by observing a live read-only
signal. It carries six live probes and `probe=None` for the rest. Two classes
of ask are GENUINELY read-only-observable yet still unprobed, so their chips
can never auto-flip:

- **Discord-login configured** on botsite (ASK-0006, `/owner/login`) and the
  dashboard (ASK-0017, `/admin/login`). Both routes render an honest HTTP-200
  "not configured" page while the four `DISCORD_*/OWNER_*` vars are unset, and
  302-redirect to Discord's OAuth authorize endpoint once they are set — the
  SAME signal that satisfied control-plane ASK-0002 (`/owner/login` → 302 →
  `discord.com/oauth2/authorize`, verified live 2026-07-19). The
  `dashboard-discord-oauth` entry currently claims (askverify.py :412/:422)
  "no read-only probe exists (mirrors ASK-0002)" — but ASK-0002 WAS satisfied
  by exactly that 302 signal, so the probe IS possible. httpx defaults to
  `follow_redirects=False` and `github._get` returns the 302 status without
  chasing it, so the status code (302 vs 200) IS the observable — no Location
  header needed, exactly the status-code style the botsite-gate probe already
  uses (503 vs 401).
- **`/submit` live** (ASK-0004). The public `/submit` intake is now
  Postgres-live (DATABASE_URL set 2026-07-19, ASK-0004 satisfied). GET
  `/submit` renders a "Reviewed before publishing" badge when
  `submissions_store.is_live()` and a "Stub — not wired" badge when not — a
  read-only, positive-both-ways body signal.

**What this session is NOT:** behaviour-additive only. No route, template, or
workflow changes; existing probes keep every verdict they return for every
state they already observe.

Work-ladder rung: coordinator-assigned build — plan slice 3 of
`docs/plans/next-cycle-2026-07-19.md`.

⚑ Self-initiated: no — coordinator-assigned slice, promoting the standing
NEXT-2 baton item and the askverify.py :412/:422 "no read-only probe exists"
note into shipped probes.

## Plan

- Add `probe_dashboard_discord_login` (ASK-0017 / `dashboard-discord-oauth`)
  and give it the existing `probe=None` entry's slot: GET dashboard
  `/admin/login` (raw) — 302 → done-detected, 200 → still-open, else honest
  unknown. Add a `_dashboard_base()` resolver mirroring `_botsite_base()`
  (`config.SERVICE_DEPLOY_TARGETS["dashboard"]`, `/version` stripped) — no
  hardcoded URL.
- Add `probe_botsite_submit_live` (ASK-0004 / `botsite-database-url`): GET
  botsite `/submit` (raw) — "Reviewed before publishing" in the body →
  done-detected, "Stub — not wired" → still-open, else honest unknown.
- Extend the botsite ASK-0006 probe (`botsite-gate`,
  `probe_botsite_site_password`) with the Discord PRIMARY signal, PREPENDED so
  the existing SITE_PASSWORD `/testing/owner` fallback (503 → still-open /
  401 → done) is byte-preserved: GET `/owner/login` first — 302 → done. This
  is required because ASK-0006 is ONE ledger row covering BOTH the Discord
  login AND the optional SITE_PASSWORD fallback, so its single registry slot
  must observe both signals; a separate entry can't bind ASK-0006 (ids are
  unique and no entry may be signature-only). It also FIXES a latent
  false-still-open: a service with Discord configured but SITE_PASSWORD unset
  is unlocked, yet the SITE_PASSWORD-only probe would call it still-open.
- Registry structure is UNTOUCHED — no new entries, no signature changes, no
  ask-id rebinds — so every registry invariant (14 open asks, unique ids,
  distinct entries, unique signatures, the historical Discord+dashboard entry
  sitting above botsite-gate) holds as-is. The two `probe=None`→probe
  conversions drop their now-dead `reason` keys.
- New unit tests per probe (stubbed responses) + the offline four-suite +
  strict gate.

## What was done

- `app/askverify.py` — three read-only probes, registry structure untouched:
  - **`probe_dashboard_discord_login`** (ASK-0017 / `dashboard-discord-oauth`)
    — GET dashboard `/admin/login` (raw): 302 → done-detected, 200 → still-open
    (the honest "not configured" page), else honest-unknown. The entry's
    `probe=None` + `reason` became `probe=probe_dashboard_discord_login`
    (dead `reason` dropped); its "no read-only probe exists (mirrors ASK-0002)"
    comment updated to name the 302 signal.
  - **`probe_botsite_submit_live`** (ASK-0004 / `botsite-database-url`) — GET
    botsite `/submit` (raw): the "Reviewed before publishing" badge →
    done-detected (intake live), the "Stub — not wired" badge → still-open,
    neither (fetch error / unexpected body) → honest-unknown. `probe=None` +
    `reason` → `probe=probe_botsite_submit_live` (dead `reason` dropped).
  - **`probe_botsite_site_password`** (ASK-0006 / `botsite-gate`) — the Discord
    PRIMARY signal PREPENDED: GET `/owner/login` (raw) 302 → done, then the
    UNCHANGED SITE_PASSWORD `/testing/owner` fallback (401 → done / 503 →
    still-open / else unknown). ASK-0006 is ONE ledger row covering both the
    Discord login and the optional SITE_PASSWORD fallback, so its single
    registry slot must observe both; this also fixes a latent false-still-open
    when Discord is configured but SITE_PASSWORD is not.
  - New `_dashboard_base()` resolver mirroring `_botsite_base()`
    (`config.SERVICE_DEPLOY_TARGETS["dashboard"]`, `/version` stripped) — no
    hardcoded URL. The signal is the status code (302 vs 200), not a Location
    header: httpx keeps `follow_redirects=False` and `github._get` returns the
    302 status, exactly the style the botsite-gate 503/401 probe already uses.
- `tests/test_askverify.py` — 8 new unit tests against stubbed responses:
  the botsite Discord-302 done path + the non-302 fall-through preserving the
  SITE_PASSWORD 401/503 ladder; the dashboard 302/200/other ladder; the
  `/submit` live-badge / stub-badge / unexpected-body-and-fetch-error ladder.
  New `BOTSITE_LOGIN_URL` / `BOTSITE_SUBMIT_URL` / `DASHBOARD_LOGIN_URL`
  constants. No existing test weakened — the registry invariant tests
  (14 open asks, unique ids, distinct entries, unique signatures, the
  intended-probes set) are unchanged because no registry entry, signature, or
  ask-id binding moved.
- `control/claims/askverify-discord-submit-probes-2026-07-19.md` — removed in
  this flip commit so it merges away clean (no drift-gate orphan).
- Verified (CI-equivalent, `DATABASE_URL` unset):
  `env -u DATABASE_URL python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q`
  → **2092 passed** (exit 0; 2084 baseline + 8 new tests);
  `env -u DATABASE_URL python3 -m pytest tests/test_askverify.py -q` → **60
  passed**; `python3 bootstrap.py check --strict` → the only gating red was
  this card's born-red `[session-card-hold]`, released at this flip (the other
  output is pre-existing model-line advisories on unrelated cards, never
  exit-affecting).

## 💡 Session idea

**Fold the two Discord-login probes into one parameterised `_login_probe(base,
path, probe_id)` helper.** `probe_dashboard_discord_login` (dashboard
`/admin/login`) and the Discord-primary half of `probe_botsite_site_password`
(botsite `/owner/login`) are the identical 302-vs-200 shape — 302 → done, 200
→ still-open, else honest-unknown — copied across two functions. A single
parameterised helper would make them one owner of that ladder, so the THIRD
fleet Discord login (the future armed control service, ASK-0003, when its URL
exists) is a one-line registration rather than a third copy — the same
"single owner for a repeated shape" discipline `botsite/_db.py` (#447) applied
to the store connection logic. Contained, test-only-adjacent, reversible.
Deduped against `docs/ideas/backlog.md` + the NEXT-2 baton (slices 4/5 are the
signal-registry data file + the vendored-copy AST guard — unrelated): not
present. To capture in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

`.sessions/2026-07-19-app-nav-reachability.md` (#450, plan slice 2) closed the
`app/` reachability gap the right way: it derived its GET guard from the
FastAPI **router** rather than the hand-maintained nav manifest, making it a
strict superset that also probes the 21 top-level routes the manifest omits
(the feeds, `/journal/search`, `/owner/login`, the gated `/owner/*` twins) —
and it *derived* every allowed status by GETting the routes first (31 public
→ 200, 10 gated → 503, `/owner/login` → 200) rather than inventing the
expected set, which is the honest way to pin a baseline. The lesson this card
carries forward: that guard proved every route *responds*, and this slice
extends the same "observe the live signal, never infer it" discipline to the
owner-action chips — a probe emits done-detected ONLY on a positive live
observation (a 302, a live-badge body), and stays honest-unknown on anything
it cannot tell, never a guessed done. Like slice 2's `/owner/login`-is-a-
public-200-door finding, this slice leans on the exact status-code contract
those login routes expose (200 unconfigured, 302 configured) as the drift-
proof signal.
