# 2026-07-11 — Anthropic review site: fourth service (`review/`) telling the program's story

> **Status:** `complete` — PR #132, branch `claude/anthropic-review-site`.

- **📊 Model:** claude-fable-5 · worker · owner-directed build (full session goal, not a slice)

**What this session was about:** owner-directed (rung 1 equivalent — direct
owner order, not an inbox ORDER): "create a website specifically for anthropic
to review the way we have been running our projects, think of it like the
control plane website, but then with the sole purpose of giving a clear visual
explanation of the problems and successes as well as the process and the way
we managed to grow so quickly." Build a FOURTH independent service `review/`
following the exact botsite/dashboard pattern (own Dockerfile + requirements +
tests, server-rendered FastAPI + Jinja2, vendored `ds/`), rendering the real
repo record — git history, `.sessions/` cards, `docs/retro/`, `control/` —
for an outside (Anthropic) reviewer. Honest by design: the problems page
leads with real failures, mirroring the ORDER 011 retro.

## What was done

- **`review/` service (new, 4th):** `app.py` (routes: `/`, `/process`,
  `/growth`, `/successes`, `/problems`, `/healthz`, `/version`,
  `/story.json`, 404) → `story.py` (domain: snapshot loading with honest
  degradation, pure-function SVG column-chart geometry, and the curated
  narrative — glossary, landing path, services, 7 successes, 8 problems,
  milestones — every item evidence-linked to PRs/files) → templates on the
  vendored `ds/` system + `static/site.css`. No client-side framework;
  charts are server-rendered inline SVG per the dataviz mark specs
  (single-hue `--sb-chart-mark`, ≤24px columns, rounded data-end, ink-token
  text, table view alongside).
- **Data model (deliberate):** Railway Root-Directory deploys ship only the
  service folder, so runtime reads of git/`.sessions`/`control` are
  impossible — `gen_snapshot.py` bakes the real numbers (PR merges, commits,
  session cards per UTC day; test functions at each day's last commit) into
  committed `data/snapshot.json` from HEAD's history; missing/corrupt
  snapshot → honest banner on every page (tested), never invented numbers.
- **Content honesty:** the problems page carries the gate leak (PR #19),
  the stranded-push incident + rescue (PR #59), silent routine fires, the
  5×-repeated cron error, the time-bomb tests (17 latent sites), the
  current-state drift, near-miss overclaims, and the verified walls — same
  specificity as the successes page, each with citations.
- **`review/Dockerfile`**, **`requirements.txt`** (fastapi/uvicorn/jinja2
  pinned as siblings; no httpx — network-free), **`Procfile`**,
  **`.dockerignore`**, **`tests/test_review.py`** (28 tests: probes, page
  renders against the real snapshot, degradation paths, chart-geometry
  units, content-integrity pins).
- **`.github/workflows/quality.yml`:** pip install gains
  `-r review/requirements.txt`; the pytest step gains `review/tests`.
- **Docs:** `docs/current-state.md` (service list + Recently shipped),
  `docs/owner/OWNER-ACTIONS.md` (six-field ⚑ for the Railway service
  creation, Root Directory = `review`), `docs/ideas/backlog.md` (idea below).
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — **273 passed** (245 baseline + 28 new); `python3
  bootstrap.py check --strict` — green except the designed born-red hold on
  THIS card (flips with this commit); PR #132's first CI run red on exactly
  that hold (job log: "Designed hold — not a CI failure to investigate").
- Follow-ups deliberately not done here: adding the review service URL to
  `scripts/healthcheck.py` and the board's deploy-drift row (needs the
  Railway service to exist first — flagged in the OWNER-ACTION's UNBLOCKS).

⚑ Self-initiated: no — direct owner order (verbatim quoted above).

## 💡 Session idea

**Snapshot-aging banner on the review site** — the review service's numbers
are baked at commit time and silently fossilize once deployed; the service
already knows its deployed sha (`/version`) and the snapshot's `git_head`,
so when they differ it can render an honest "numbers as of commit X — the
repo has moved since" banner, plus a regen habit for `gen_snapshot.py`.
Worth having because a review surface whose numbers silently age misleads
exactly the outside audience it was built for. Deduped against
`docs/ideas/backlog.md` + the queue-state NEXT list: nothing covers the
review service. Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The test-time-discipline-guard wake (#114) did well turning one live
incident into a class-wide AST guard that caught 17 latent time bombs
before they detonated one-by-one in unattended runs; what it missed — and
honestly captured rather than fixed — is the route-level half (TestClient
tests still reach the real wall clock through endpoints), which remains an
open backlog bullet rather than an enforced guard.
