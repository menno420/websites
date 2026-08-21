# 2026-08-20 — review cutover: every surface repoints to the Pages export (slice 3b)

> **Status:** `complete` — branch `claude/review-cutover-pages`, PR #510.
> Third PR of the keep-bot-only execution: 3a (#509) landed the mechanism
> and the first Pages deploy is VERIFIED SERVING (six route classes probed
> 200, banner + noindex live); this PR moves every consumer off the doomed
> Railway URL; the `serviceDelete` itself happens only after this lands and
> is recorded on the fleet-manager execution card.

- **📊 Model:** fable-5 · high · mechanical refactor

## previous-session review

The previous card (2026-08-20, review-static-export, PR #509) closed clean
under the two-round cap (R1 6/6 + R2 3/3 conceded and fixed); merged
`b596b70`; the dispatched review-pages run succeeded and
https://menno420.github.io/websites/ serves. Nothing it recorded contradicts
this tree.

## Scope

Every surface that referenced the Railway review URL or the deleted
mineverse deployment, repointed or honestly retired:

- Fleet-nav strips ×4 (app/botsite/dashboard/review base.html) → the Pages
  URL; their four test pins updated.
- `web_presence.json`: review row → Pages shape (games-web precedent);
  `review-dup-f027` row dropped (service deleted 08-14, park resolved);
  mineverse row dropped (service + project deleted 08-20); project
  descriptions updated; `test_web_directory` pins (incl. SEED_URLS
  de-duplicated and rid of the dead mineverse URL).
- `environments.json`: review surface → Pages; `review-dup-f027` surface
  dropped.
- `app/railway.py`: review entry KEPT (its code's env names stay
  documented) but marked **`retired`** with the Pages URL — new
  `DRIFT_RETIRED`/`VAR_RETIRED` states in `app/envdrift.py` render
  *"retired — absence from the live project is the designed state"* instead
  of charging drift or claiming "names match"; template branch added.
- `app/config.py` SERVICE_DEPLOY_TARGETS: review dropped (no /version
  process to poll); the deploy-state cell and its pins now cover three
  services; the parity test compares non-retired services.
- `scripts/healthcheck.py`: review out (probes Railway services only — a
  kept entry would red every 6 h against a deleted service);
  `scripts/smoke_crawl.py`: review → the Pages URL (rendering-layer
  coverage follows the record to its new home).
- botsite arcade: mineverse `availability` → `unavailable`, url null,
  honest retirement note (the no-dead-links rail); five count/shape pins
  updated; new `test_retired_service_absent_is_ok`.

## Shipped

- The Scope above, plus what the two Codex rounds added under the cap:
  **R1 8/8 [conceded]** (dashboard `/reviews` default → the Pages reviews
  index (P1 — the fc91 URL is deleted); envhub static-venue accounting —
  review's 5 documented names leave the comparable universe as
  `LIVE_STATIC`/`static_count` instead of inflating missing/unknown;
  envdrift `services_retired` out of `services_compared` so the ok rollup
  text stays true; mineverse group + the two 08-14 dup rows dropped from
  both registries with `DUPLICATE_IDS` now the empty contract set;
  reliable-grace postgres row trued; story.py + botsite testing task →
  Pages URL) and **R2 5/5 [conceded]** (P1: the hardcoded fleet-strip
  self-link exported as `/websites/websites/` in ALL 30 HTML files — link
  now root-relative AND the host-root rewrite idempotent, pinned; static
  venue no longer generates Railway setup in the manifest — explicit
  `manage_url` → the review-pages workflow, `<STATIC-VENUE-NOTHING-TO-SET>`
  placeholder; `retired` var-state template branch; retired-but-present =
  lifecycle drift, tested; reliable-grace group purpose trued).
- Test-isolation hardening bundled with the R2 commit: the six
  envhub-family files gained the autouse `owner.reset_rate_limits()`
  fixture their nine test_owner_* siblings carry (the latent cross-file
  429 recorded under Session idea).

## Verify

- Suites at the final head: tests/ **1077** · review/tests **296** ·
  dashboard/tests **130** · botsite arcade **65** — all green, real exit
  codes (separate un-piped runs).
- Exporter re-run after each fix round: exit **0**, 35 routes; the R2
  re-export greps **zero** `websites/websites` occurrences (was 30 files)
  and the self-link exports as `href="/websites/"`.
- Local `python3 bootstrap.py check --strict` exit 1 with the ONLY red the
  designed born-red card hold (this flip releases it); CI `quality` on the
  pre-flip heads red on the same single step (job log verbatim: "Designed
  hold — not a CI failure to investigate"), every prior step green.
- Codex reviewed the exact heads `88efd7e` (R1) and `6364d4a` (R2);
  dispositions posted on the PR; two-round cap reached.

## Session idea

- 💡 ~~The two remaining 08-14 dup rows in `environments.json` … one small
  follow-up drops them~~ — pulled INTO this PR at Codex round 1's ask
  (both rows + web_presence labels + the `DUPLICATE_IDS` pins, now an
  empty contract set).
- 💡 Latent test-order flake, pre-existing: the envhub-family test files
  (test_envhub*, test_owner_readiness_*) hammer the /owner gate with bad
  creds but never call `owner.reset_rate_limits()`, unlike their nine
  sibling files — a hand-picked pytest subset ran them back-to-back and
  the failed-auth throttle 429'd a later file's 401 pin. The full suite's
  fixed order has never tripped it (CI green throughout), so it stays out
  of this PR's lane; the follow-up is the sibling files' one autouse
  fixture, copied into the six.
