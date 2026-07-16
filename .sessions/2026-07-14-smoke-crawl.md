# 2026-07-14 — scheduled Playwright smoke-crawl in CI (the browser-level healthcheck)

> **Status:** `complete` — PR #321, branch `claude/smoke-crawl-0714`;
> every 6 hours a real headless Chromium now crawls the three public sites +
> the control-plane root (same-site link discovery, desktop 1280×900 + mobile
> 375×812) and fails on console errors / non-200 pages / broken same-site
> links — the rendering-layer complement to the curl-level healthcheck.yml.

- **📊 Model:** Claude Fable 5 · medium · feature build (scheduled Playwright smoke-crawl, backlog promotion)

**What this session was about:** backlog promotion — the `docs/ideas/backlog.md`
bullet "Scheduled browser-level smoke-crawl in CI — a Playwright job that
cold-crawls the three live sites the way the manual cold passes do" (captured
2026-07-13 by the cold-browser-review session, PR #311). The existing
`healthcheck.yml` smoke is curl-level (`/healthz` + `/` status codes); both
2026-07-13 cold passes found real regressions it can never see (dead chrome
wiring, a blank hamburger, a lost footer gutter, a favicon 404) because they
only exist in a rendering browser. This session builds the standing gate.

## What was done

- `scripts/smoke_crawl.py` — Playwright (sync API) crawler over the SAME
  four-URL inventory `scripts/healthcheck.py` probes. Same-site BFS link
  discovery per page; external links never followed or fetched; the gated
  `/owner` corner skipped by documented design. Two viewports per page
  (desktop 1280×900, mobile 375×812). Assertions: every crawled page 200,
  zero non-allowlisted console errors / pageerrors across both viewports,
  every discovered same-site link non-4xx/5xx. Bounded: 25-page cap per
  site, 150 link checks per site (checked-of-found printed honestly), and a
  240 s global deadline whose breach is itself a FAILURE. Console-error
  allowlist seeded EMPTY — the #311 pass left zero known noise. Env/CLI
  overrides (`--executable-path`, `--proxy-server`, `--browser-arg`,
  `SMOKE_CRAWL_*`) carry the agent-container proxy workaround
  (`docs/CAPABILITIES.md` 2026-07-13 entry) so CI runs plain.
- Two documented scope cuts from the first live crawl's REAL findings (PR
  body carries both as follow-up findings, neither allowlisted away):
  (1) anchors inside rendered REMOTE-markdown containers (`<div class="md">`)
  are excluded from discovery — all 20 flagged 404 links were relative links
  inside other repos' rendered markdown (heartbeats on /fleet, the ledger on
  /reviews), unresolvable on this origin by construction; (2) non-page URLs
  (.json/.xml/…) are status-checked at request level, never rendered —
  Chromium's raw-view requests `/favicon.ico` (a fleet-wide 404 gap on
  non-HTML endpoints) as a viewer artifact.
- `.github/workflows/smoke-crawl.yml` — cron `47 2-23/6 * * *` (offset from
  healthcheck's `17 */6 * * *` on BOTH fields) + `workflow_dispatch`; NOT a
  required check, no `pull_request` trigger; failure notifies via the
  failed-workflow email, healthcheck.yml's exact mechanism; playwright
  pinned workflow-only (1.61.0) so no service requirements.txt grows a
  browser dependency. Honesty note on the PR: a green manual dispatch proves
  the JOB, not the SCHEDULE — the cron is proven only by the first
  on-schedule run.
- Local live proof (agent container, full Chromium via `--executable-path
  /opt/pw-browsers/chromium` + explicit `--proxy-server` +
  `--ssl-version-max=tls1.2`): PASS in 2m41s — 100 pages crawled at both
  viewports, 554 same-site links checked, zero console errors; verbatim
  output pasted in the PR body.
- `docs/ideas/backlog.md`: the #311 session's bullet flipped `captured` →
  `built`; this session's 💡 captured as a new bullet.
- `control/claims/2026-07-14-smoke-crawl.md` created with the born-red card
  and released in this close-out commit (claims README step 4).
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 1373 passed, 1 warning (= main's baseline; the crawler
  is a scheduled live probe, deliberately outside the network-free quality
  gate, same stance as healthcheck.py); `python3 bootstrap.py check
  --strict` — green except this card's own designed born-red HOLD (released
  by this flip).

⚑ Self-initiated: no — backlog promotion (the #311 cold-browser session's 💡
bullet in `docs/ideas/backlog.md`).

## 💡 Session idea

**Rewrite relative links inside rendered remote markdown to their GitHub
source (or de-linkify them)** — the control-plane renders other repos'
markdown verbatim in `<div class="md">` (heartbeats on /fleet, the
fleet-manager ledger on /reviews, environment docs on /environments), and
relative links inside that content (`README.md`, `gen2-blueprint.md`,
`docs/retro/…`) resolve against this origin and 404 — the first smoke-crawl
run flagged 20 of them live, every one clickable by a real user today. The
renderer already knows each document's source repo + path, so rewriting
relative hrefs to `github.com/<owner>/<repo>/blob/main/<resolved-path>` (or
the in-app `/journal/{repo}/file` view for fleet repos) is a contained fix.
Worth having because real visitors land on 404s from three public pages
right now, and fixing it lets the smoke-crawl delete its `.md`-container
exclusion — restoring browser-gate coverage over exactly the surfaces that
degrade silently. Deduped against `docs/ideas/backlog.md` + the queue-state
NEXT list: the "Deep-link fleet lane files into the widened /journal/{repo}/file
view" bullet ADDS chrome links via the in-app renderer and nothing touches
relative hrefs inside rendered markdown bodies. Captured in
`docs/ideas/backlog.md`.

## ⟲ Previous-session review

The venture-vetting-catalog session (PR #248) did well — 22 packets curated
with every status derived from its packet's own Status/Verdict text and
pinned by the registry-honesty test, one buy link for the one actually-live
product; what it missed: the catalog's provenance is a hand-pin to
venture-lab `2c039e3` with no watcher, so (as its own 💡 concedes) the
page's honesty started decaying the moment upstream moved.
