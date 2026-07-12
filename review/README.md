# review/ — the program-review site (for Anthropic reviewers)

> **Status:** `service-doc` — the fourth independent service in this repo
> (own Dockerfile / requirements / tests; Railway Root Directory = `review`).
> Read-only and **network-free at runtime**: everything the pages show is a
> committed file under `review/data/`, baked from the real record. A missing
> or stale data file banners honestly — the site cannot invent data even in
> principle.

## Surface

| Route | What it is |
|---|---|
| `/` | Overview: stat tiles, the program in one paragraph, how to read the site |
| `/process` | The bus, the landing path, the gates, glossary — written for an outsider |
| `/growth` | Per-day SVG charts + table + milestones, derived from git history |
| `/successes` · `/problems` | Evidence-linked narrative; problems are first-class |
| `/fleet` · `/fleet/{repo}` · `/fleet.json` | Every seat in the fleet-manager registry + per-lane detail from the committed mirror |
| `/reviews` · `/reviews/{slug}` · `/reviews/feed.xml` | Dated review editions + a subscribable Atom feed |
| `/questionnaire` | Anticipated reviewer questions, answered from repo evidence with citations |
| `/questions` | The questions-asked → answered ledger (+ the intake convention) |
| `/story.json` · `/healthz` · `/version` | Machine snapshot + the estate-standard probes |

## Data model — bake, commit, render

Railway Root-Directory deploys ship ONLY this folder, so runtime reads of
git/`.sessions/`/`control/` (or the network) are impossible by design. Three
generators, run from the repo root, produce the committed mirrors:

- `gen_snapshot.py` → `data/snapshot.json` — this repo's own per-day history.
- `gen_fleet.py` → `data/fleet.json` — the fleet-manager's canonical `LANES`
  registry + every repo-backed lane's `control/status.md` heartbeat
  (raw.githubusercontent.com, anonymous, fail-soft, fields capped for size)
  + every repo-backed lane's latest-commit `head` record (anonymous git
  transport: `ls-remote` + a depth-1 treeless fetch — works where the REST
  API is walled) + the 8-standing-seats structure and consolidation record
  (commit-pinned sources in the module header; seat heartbeat numbers are
  derived from the same per-repo fetches, never hand-written).
  Seat counts are recorded **as found** — the pages never hardcode a fleet
  size; registry-only seats (a seat with no repo) are surfaced as such.
- `gen_stats.py` → `data/stats.json` — two REST calls per repo (last push,
  total PRs ever, open issues+PRs), fail-soft per repo, honest reasons
  recorded. Uses `GITHUB_TOKEN` when present; anonymous otherwise.

**Freshness**: the scheduled `review-bake` workflow
(`.github/workflows/review-bake.yml`, daily cron + `workflow_dispatch`)
re-runs all three and lands the data-only diff (direct push if the ruleset
allows, else a `[bake]` PR with auto-merge, else the PR waits visibly).
Every stats surface renders its as-of timestamp; mirrors older than
`fleetdata.STALE_HOURS` (48h) banner as stale, and a deployment whose code
sha differs from the snapshot's source commit shows the snapshot-aging
banner site-wide.

**⚑ Until the owner flips one console toggle, the daily bake cannot
self-land.** Verified 2026-07-12 (both historical runs, incl. run
29184552812): the bake succeeds and pushes its `bake/…` branch, then
`gh pr create` is refused with *"GitHub Actions is not permitted to create
or approve pull requests"*. The workflow degrades honestly (job stays
green; the run summary carries a compare link). The manual refresh path,
until then:

1. GitHub → Actions → **review-bake** → *Run workflow* (`workflow_dispatch`
   on `main`) — or wait for the daily cron (`23 5 * * *`, best-effort).
2. Open the run's **Summary**: if the ruleset allowed a direct push, the
   data is already on `main` (done). Otherwise the summary names the pushed
   `bake/…` branch and links the compare page — open the PR from there
   (any session or the owner) and merge it on green `quality`.
3. **Owner fix that retires step 2** (✅ safe, reversible): repo
   **Settings → Actions → General → Workflow permissions → check "Allow
   GitHub Actions to create and approve pull requests"**. After that the
   workflow opens its own `[bake]` PR and arms auto-merge; the whole loop
   is hands-free. (Queued in `docs/owner/OWNER-ACTIONS.md`.)

Any agent session can also refresh by hand: run the three generators from
the repo root and land `review/data/**` through a normal PR (this is what
the ORDER 017 refresh did).

## Publishing a review edition (the ritual)

Editions make this site a **continuous** review channel. Any session can
publish one — no permission needed beyond the normal landing path. Publish
when there is something real to review: a significant unattended window, a
major landing, an incident worth a written account, or an answered reviewer
question.

1. Create `review/data/reviews/YYYY-MM-DD-edition-NNN.md` (lowercase
   kebab-case filename — it becomes the slug and the URL).
2. Start from this template:

   ```markdown
   ---
   title: Edition N — <one honest line>
   date: YYYY-MM-DD
   summary: <one or two plain sentences for the index and the Atom feed>
   ---
   ## The window in one line
   ## What shipped
   ## What went wrong (each with its citation)
   ## Only the owner can do these (open at press time)
   ## Next edition
   ```

3. House rules (the same ones the whole site obeys): every claim cites a
   PR/commit/file; problems get the same specificity as successes; nothing
   is estimated; "we don't know" is a valid sentence. Adapt the newest
   `docs/retro/` self-review where one exists — that is what edition 1 did.
4. Land it through the normal ceremony (card → PR → quality green → merge).
   The index, the per-edition page, and `/reviews/feed.xml` pick it up with
   zero code changes; `review/tests/` pins the format, so a malformed
   front-matter block fails CI instead of publishing broken.

## Interaction (read-only by design)

Every page footer (and the fleet/edition pages inline) carries a prefilled
GitHub new-issue link. Convention: reviewer question → issue → the manager
routes it as an order on the bus → the answer publishes in the next edition
AND lands in `data/questions.json` (rendered at `/questions`) with links to
both. A real intake form/database is a flagged future owner option — this
site holds no credentials and takes no writes.

## Verifying

```
python3 -m pytest review/tests -q          # this service
python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q
python3 bootstrap.py check --strict
```
