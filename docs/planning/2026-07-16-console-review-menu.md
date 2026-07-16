---
state: planned
origin: session:2026-07-16-console-review-menu
---

# Console + Review — overnight planning menu (2026-07-16)

> **Status:** `ideas`
>
> Per owner LIVE OVERNIGHT ORDER (event 55f13541). The buildable backlog was
> thin, so this is a deliberately LONG, veto-ready menu — small fixes through
> ambitious features — across two services: the control-plane launch console
> (`app/`) and the review service (`review/`). **Quantity is intentional; the
> owner's veto is the filter.** Nothing here is built yet. Surviving picks
> become `docs/ideas/backlog.md` bullets or build slices.
>
> Legend — effort **S**(small) / **M**(medium) / **L**(large) · risk **✅** safe
> / **↩️** reversible / **⚠** risky-or-owner-gated. Every item references real
> files/routes from a fresh read of `origin/main`.

---

## Control-plane launch console (`app/`)

### Polish & honest-status (small fixes on real routes)

**C1 · Distinguish "counter failed" from "genuine zero" on category pages** — S · ✅
The `_count_*` helpers in `main.py` fail-soft to `count=None` and render `—`, but a *failed* counter is visually indistinguishable from a real zero on `/work`, `/history`, `/console`. Add a distinct "unavailable" glyph/tooltip so a fetch failure never masquerades as an empty category. *Unblocks:* trustworthy at-a-glance counts.

**C2 · Surface pagination truncation honestly (>100 cap)** — S/M · ✅
`github.py:run_jobs` and `readiness.py:prs` both cap at `per_page=100` and truncate silently (the docstrings admit it). Add an explicit "≥100, truncated" flag wherever oldest-PR / job-count math depends on it, so a >100 run/PR-list never quietly under-reports. *Unblocks:* correct rerun-ci job naming + oldest-PR age on busy repos.

**C3 · Bounded (LRU) eviction for the GitHub TTL cache** — S · ✅
`github.py._cache` is unbounded — only TTL expiry and manual `clear_cache` evict. A long-lived process touching many URLs grows it without limit. Add a max-entries LRU bound. *Unblocks:* stable memory on the Railway replica.

**C4 · Conditional requests (ETag / If-None-Match) in `github.py`** — M · ↩️
Every cache miss is a full fetch that burns rate limit; no conditional requests. Store ETags and send `If-None-Match` so a 304 refreshes TTL without spending the body. *Unblocks:* deeper fan-out (board/fleet/search) without rate-limit pressure.

**C5 · Retire the stale coordination note on the environments nav item** — S · ✅
`main.py:256` deliberately leaves the `environments` nav chip-less with a comment citing an "in-flight parallel session" that has long since landed. Remove the note; decide the chip. *Unblocks:* nav consistency.

**C6 · Better non-markdown file rendering in `/journal/{repo}/file`** — S · ✅
The route does an inline `import html as _html` and wraps non-markdown content in a bare `<pre>` with no language awareness. Hoist the import and add minimal syntax hinting / line numbers. *Unblocks:* readable committed-file views.

**C7 · Multi-hit search snippets in cross-repo journal search** — S/M · ✅
`journal.py:search_journal` shows only the FIRST match per file (`lower.index(ql)`) then counts occurrences. Return the top-N match contexts so a file with a late-but-relevant hit isn't represented by an early throwaway. *Unblocks:* useful `/journal/search`.

**C8 · Fail-closed symmetry for `assist` / `note` writeback actions** — S · ↩️
`action_queue_complete` fails closed when the target ask is positively gone, but `action_queue_assist` / `action_queue_note` do not (asymmetric by history, not design). Add the same positively-gone guard. *Unblocks:* consistent writeback safety.

### Tests & guards (cover the silent gaps)

**C9 · Adversarial pagination-truncation tests** — S · ✅
No test exercises the >100-jobs / >100-PRs truncation path in `github.py` / `readiness.py`; the caps are silent. Add tests asserting the truncation flag is set and surfaced. *Unblocks:* C2 lands with proof.

**C10 · Guard test for hardcoded Railway deploy-target URLs** — S · ✅
`readiness.py._service_deploy_state` reads hardcoded URLs from `config.SERVICE_DEPLOY_TARGETS`; `test_check_no_ambient_railway_ids.py` guards Railway *IDs* but not these `/version` URLs. Add a test tying them to a single source so a re-provisioned service can't silently drift. *Unblocks:* honest deploy-drift board.

**C11 · Cache-eviction / unboundedness test** — S · ✅
No test asserts the cache is bounded or that transient 429/5xx are never cached (the poison guard at `github.py:204`). Lock both behaviors in. *Unblocks:* C3 lands with proof.

### New console capabilities (ambition)

**C12 · Owner-action outcome ledger page (`/owner/history`)** — M · ✅
The writeback engine keeps a local audit log and rerun-ci mints verify chips, but nothing surfaces the *history* of owner actions over time. Add a gated `/owner/history` timeline: each action, its preflight pin, and its post-fire verify verdict. *Unblocks:* "did my last click actually work?" without re-deriving from logs.

**C13 · Verify rerun-ci by `run_attempt` counter (race-free)** — S/M · ✅
The current post-fire chip re-GETs jobs and races the status transition. GitHub's `run_attempt` increments deterministically on re-run; pin the pre-fire attempt and confirm it incremented. (Already filed as a session idea — this promotes it.) *Unblocks:* race-free rerun confirmation.

**C14 · Deeper live re-verification of owner ASKs (askverify extension)** — M · ✅
`askverify.py` verifies an ask's writeback shape; extend it to re-check the *underlying condition* still holds (e.g. the secret is still unset, the Postgres still unprovisioned) at each board render, so a stale ASK auto-resolves instead of nagging. *Unblocks:* self-cleaning owner queue.

**C15 · Stable, durable ask IDs** — M · ↩️
The next-on-file baton (`askverify.py:461`): owner asks are positionally identified, so reordering the ledger breaks writeback targeting. Assign durable IDs. *Unblocks:* C12/C14 and any cross-session ask reference.

**C16 · Cache-warm preflight owner action** — S/M · ✅
Add a gated action that proactively warms the TTL cache for the board/fleet fan-out (preview→confirm like the others), so the owner's first morning load isn't a cold-cache burst. *Unblocks:* fast first paint after a deploy.

**C17 · "New since your last visit" marker on `/activity`** — S/M · ✅
`/activity` is date-grouped but stateless. Add a zero-JS "last seen" cookie + a divider marking PRs new since the owner's previous visit. *Unblocks:* skimming only what changed overnight.

**C18 · Extend deploy-drift board beyond the `websites` repo** — M · ⚠
`_deploy_board` only computes Railway drift for `websites`. Generalize `SERVICE_DEPLOY_TARGETS` so the board honestly reports drift for every seat that publishes a `/version`. *Unblocks:* fleet-wide deploy honesty. (Risk: hardcoded-URL sprawl — pair with C10.)

**C19 · Redeploy-from-browser preflight (owner decision-table row 3)** — M · ⚠
Owner-actions decision table asks whether to wire a Railway deploy-hook. Build the *preflight-only* half now (resolve the target service, show what would redeploy, store nothing) so the owner can decide with a real screen in front of them; the fire half stays gated. *Unblocks:* one-click redeploy once the owner says go.

**C20 · Discord-OAuth gate for `/owner` (ORDER 021 seam)** — L · ⚠
The seam is documented in three `owner.py` docstrings but unbuilt; auth is still a single shared `SITE_PASSWORD` with no per-actor identity. Build the OAuth flow so actions are attributable. *Unblocks:* actor-audited owner actions. *Gated on:* ASK-0002 (Discord OAuth app) — owner-provisioned.

**C21 · Persist CSRF / rate-limit state across replicas & restarts** — M/L · ⚠
Both live in per-process memory (owner.py docstrings say so); multiple Railway replicas or a restart reset them, so the limiter is best-effort, not a defense. Move to a small shared store, or — if that's overkill — surface the "best-effort only" caveat honestly in the owner UI. *Unblocks:* a real (not cosmetic) rate limit.

---

## Review service (`review/`)

### Polish & honest-status (small fixes on real routes)

**R1 · Add `/questions` to NAV and seed the ledger** — S · ✅
`questions.json` is empty and the page is NOT in NAV — reachable only via a single link in `reviews.html:42`. Substantial machinery (`story.py` answer-debt/latency engine + `gen_questions.py`) currently surfaces nothing. Add it to `app.py:51` NAV and seed with the anticipated Q&A already in `QUESTIONNAIRE`. *Unblocks:* the whole questions surface earns its code.

**R2 · Suppress the dead `hub` facet sub-line on `/fleet`** — S · ✅
`LANES_FILTER_SPEC` / `fleet.html:40` reference a `hub` disposition, but current data has 0 hub lanes. `_suppress_empty_facet_options` hides the pill, yet the "· 0 hub" sub-line still renders. Suppress the sub-line too. *Unblocks:* clean fleet filter UI.

**R3 · Disambiguate the 24-vs-8 "seats" numbers on `/fleet`** — S · ✅
`/fleet` shows `total_seats = 24` (registry lanes, `fleet.html:33`) next to "the 8 standing seats" (`fleet.html:76`) — same fleet described two ways, confusing to a reviewer. Relabel one ("24 lanes" vs "8 standing seats"). *Unblocks:* a review site that doesn't confuse its own reviewers.

**R4 · Quantify snapshot-aging honesty** — S · ✅
`snapshot_aged` flags only a binary deployed-SHA ≠ snapshot-`git_head` mismatch. Show *how far* behind ("N PRs / M days"), computed from the snapshot rows. *Unblocks:* honest freshness on `/` and `/growth`.

**R5 · Cross-service parity note: keep the vendored `listfilter.py` byte-identical** — S · ✅
A test already enforces byte-identity with `app/listfilter.py`; add a CI-visible reminder / pre-commit note so a future edit to one doesn't silently diverge before the test catches it. *Unblocks:* one filter core, two services, zero drift.

### Tests & guards

**R6 · Unit tests for the three untested generators** — M · ✅
`gen_snapshot.py`, `gen_fleet.py`, `gen_stats.py` have NO dedicated unit tests (only `gen_questions.py` does); their git/REST/parse logic is exercised only indirectly via committed-data shape assertions. Add unit tests (fixtured git log / mocked REST / sample parse). *Unblocks:* trustworthy bake output.

**R7 · Advisory-line assertion for `gen_questions` closed-without-answer** — S · ✅
`gen_questions.py` prints `ADVISORY:` lines for closed-without-answer records but nothing asserts the answer-debt nag matches them. Add a test tying the advisory to the rendered debt. *Unblocks:* the answer-debt surface can't silently lie.

### New review capabilities (ambition)

**R8 · Stats-history accumulation for real fleet trends** — M/L · ✅
`stats.json` is a single snapshot; `/fleet` renders per-repo `total_prs`/`pushed_at` but there's no trend. Have `gen_stats.py` append daily rows to a history file so the fleet gets real growth trends (like `snapshot.json` already does for PRs/tests). *Unblocks:* R9 and a fleet-growth chart.

**R9 · Fleet growth/trend view over accumulated stats** — M · ✅
Once R8 accumulates history, add a server-rendered inline-SVG trend view (reusing `story.growth_charts`) for per-repo / fleet-wide PR & test growth. *Unblocks:* the review site shows momentum, not just a still frame.

**R10 · Auto-drafted next review edition from snapshot deltas** — M · ↩️
The editions system + Atom feed + month filter are all built for a SINGLE 2026-07-11 file. Add a bake step that drafts a new edition body from snapshot/stats deltas since the last edition, for the owner to edit and publish. *Unblocks:* a continuous reviews channel that's actually continuous.

**R11 · Evidence-corpus freshness for the AI assistant** — M · ↩️
`ai.py` grounds only on 5 committed `data/evidence/*.md` chunks. Add a bake step that refreshes/adds evidence from live incident/roster data so the assistant's grounding doesn't ossify at 2026-07-12. *Unblocks:* an AI assistant that stays current.

**R12 · Persist the AI spend/rate caps across restarts** — M · ⚠
The `$25/mo` cap + per-IP/global limits in `ai.py` are in-memory and reset on every container restart, so the real monthly ceiling is unbounded across restarts. Persist the counters. *Unblocks:* a spend cap that actually caps. *Note:* live mode also needs `ANTHROPIC_API_KEY` (queued owner action).

**R13 · Reviewer-facing "what changed since edition N" diff on `/reviews`** — M · ↩️
Given R8/R10, surface a compact delta between the current snapshot and the last published edition on the `/reviews` index, so a returning reviewer sees movement at a glance. *Unblocks:* returning-reviewer orientation.

**R14 · Deep-linkable evidence anchors from narrative pages** — S/M · ✅
`SUCCESSES`/`PROBLEMS`/`QUESTIONNAIRE` items are each evidence-linked, but the AI corpus `data/evidence/*.md` chunks aren't individually anchored/browsable. Add a lightweight `/evidence/{slug}` render so a reviewer can read the exact grounding chunk a claim cites. *Unblocks:* end-to-end "claim → evidence" traceability.

---

## Cross-cutting / meta

**X1 · Promote survivors into `docs/ideas/backlog.md`** — S · ✅
After the owner vetoes, convert each surviving proposal into a backlog bullet (or a `<slug>-<date>.md` idea file for substantial ones) per `docs/ideas/README.md`, so the menu becomes a live conveyor, not a one-night artifact. *Unblocks:* the idea lifecycle (rung 3 of the work ladder).

**X2 · Bundle the S/✅ tests-and-guards items into one green PR** — S · ✅
C9, C10, C11, R6, R7 are all pure test/guard additions with no behavior change — landable together as a single low-risk green PR the moment the owner greenlights, independent of the feature votes. *Unblocks:* immediate coverage wins with zero product risk.

---

### Notes on what was deliberately NOT included
- No proposal assumes an owner-gated credential is already present (Discord OAuth, `ANTHROPIC_API_KEY`, `BAKE_PAT`, Postgres) — those items (C19, C20, R12) are explicitly marked ⚠ and their preflight-only halves are separable.
- Workflow-file (`.github/workflows/**`) changes (R10/R11 bake steps) must land as SEPARATE PRs — `host-automerge-extras.yml` labels any workflow diff `do-not-automerge` (owner-merge-only).
