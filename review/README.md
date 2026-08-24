# review/ — the program-review site (for Anthropic reviewers)

> **Status:** `site-doc` — the fourth product in this repo and a public
> **GitHub Pages archive** at <https://menno420.github.io/websites/>. FastAPI
> remains its rendering source and local-test surface; `gen_static.py` exports
> it for Pages. The former Railway service retired 2026-08-20. Everything the
> public pages show is a committed file under `review/data/`, baked from the
> real record; a missing or stale file banners honestly.

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
| `/story.json` | Machine-readable archive snapshot |
| `/healthz` · `/version` | Source-app probes used locally; deliberately omitted from the static Pages artifact |

## Data model — bake, commit, render

The Pages artifact is generated entirely from this folder, so a public request
cannot read git/`.sessions/`/`control/` or call the network. Three generators,
run from the repo root, produce the committed mirrors:

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

**Freshness**: this is deliberately a dated archive. `review-bake.yml` is now
manual-only for a deliberate committed-mirror refresh. `review-pages.yml`
builds and publishes the static tree after relevant changes land on `main`
(or on manual dispatch). Every stats surface renders its own as-of timestamp;
mirrors older than `fleetdata.STALE_HOURS` (48h) banner as stale rather than
pretending to be current. An agent can refresh by running the generators and
landing `review/data/**` through a normal PR.

## Publishing a review edition (the ritual)

Editions are preserved archive records. A later agent-authored answer or
correction can add an edition through the normal landing path, but publication
is a deliberate archive update, not a claim that the concluded programme or
retired assistant is live again.

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
both. A real intake form/database is a flagged future owner option. The Pages
archive itself is static: it stores no credentials and writes no submissions;
the GitHub issue link is the active external intake.

## Verifying

```
python3 -m pytest review/tests -q          # this service
python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q
python3 bootstrap.py check --strict
```
