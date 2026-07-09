# 2026-07-09 — Cross-repo activity timeline + idea-backlog views

> **Status:** `complete` — PR (`claude/activity-ideas-views`). Two new public
> control-plane views shipped on the board's existing TTL-cached github layer;
> +9 tests; app suite green; docs + ledger ([D-0020]) updated. Self-directed
> improvement batch.

- **📊 Model:** claude-opus-4-8 · high · feature build

**What this session was about:** A self-directed improvement batch on the
control-plane site — add a cross-repo **activity timeline** and an **idea-backlog**
view so the owner has one glanceable screen for "what shipped / is in flight
across the fleet" and one for "what's queued to build", without opening ten
sessions or ten `docs/ideas/` trees.

## Ritual (FIRST)

Read `control/README.md` + `control/inbox.md`. Inbox has **ORDER 001** (done —
deploy-drift cell, status already reports acked=001 done=001) and **ORDER 002**
(status `new`, P1 — build a `/fleet` page rendering every lane's
`control/status*.md`). ORDER 002 is a NEW order beyond ORDER 001 and is **not**
this session's assignment, so per the dispatch protocol it was **reported to the
orchestrator, not executed** here. `inbox.md` was never edited (manager owns it).
Note: PR #32's commit title reads "ORDER 002 — build /fleet page" but its diff
**only appended the order to `inbox.md`** — `/fleet` is not built.

## What was built

- **`/activity` + `/activity.json`** (`app/activity.py`, `app/templates/activity.html`).
  Merges recent PRs across all four repos (superbot, superbot-next, substrate-kit,
  websites) into one reverse-chronological stream via the shared cache-backed
  `github.repo_api`. Each row: repo badge, state badge (`merged`/`open`/`draft`/
  `closed`), `#num title · author`, deep-linked to GitHub. Per-repo fetch failure →
  honest banner in `errors`. Bounded (15/repo, 60 combined). Decision-ledger
  entries deliberately deferred (per-repo formats diverge — "if cheap", judged not
  cheap enough for v1).
- **`/ideas` + `/ideas.json`** (`app/ideas.py`, `app/templates/ideas.html`).
  Per-repo `docs/ideas/` backlog. Lists the dir once (cache-backed), excludes the
  `README.md` index, newest-first, enriches the newest 24 with a parsed title +
  one-line summary (`parse_idea`: frontmatter strip → first `# H1` → `**One line:**`
  or first real paragraph). No-ideas dir = honest **absence** (404), never an
  error; non-404 listing failure = `listing_error` banner. Each idea deep-links to
  GitHub **and** to the existing in-app markdown view (`/journal/{repo}/file`) —
  reusing the journal renderer, no second detail route.
- Nav links to both in `base.html`; mobile-safe inside the existing scroll cards.

## Verification

- `python3 -m pytest tests/` → **44 passed** (was 35; +9 new: activity merge/sort/
  links, activity honest-error, activity route-degrades; parse_idea frontmatter/
  One-line/Idea-label; ideas list-skips-README, no-ideas-absence, listing-error,
  ideas route-degrades). Full suite `tests/ botsite/tests dashboard/tests` green.
- `python3 bootstrap.py check --strict --require-session-log --session-log <this card>` green.
- `parse_idea` validated against **real** fetched idea files (superbot
  `agent-env-credential-smoke-check`, substrate-kit `heartbeat-verb`,
  `session-card-guard-recipes`, superbot `ai-extra-tool-capability-ideas`) via the
  raw host — titles + summaries parse cleanly.
- Local truth: api.github.com is proxy-blocked in the sandbox, so directory
  listings and `/pulls` can't run locally → verified via mocked tests locally and
  **live on the deployed app** after merge (evidence below).

## Live evidence (post-deploy)

<!-- filled after merge + Railway deploy SUCCESS -->
- deploy: <pending>
- `/activity` 200 — real PRs: <pending real PR numbers>
- `/ideas` 200 — real titles: <pending>
- `/healthz` 200; `scripts/healthcheck.py` all 200: <pending>
- board deploy-state: control-plane in sync at new head: <pending>

## 💡 Session idea

**`/activity` RSS/Atom feed (`/activity.xml`).** The timeline already normalizes
cross-repo PRs into `{repo, number, title, author, state, ts, url}`; emitting the
same list as an Atom feed would let the owner subscribe to fleet activity in any
reader (or pipe it to a Slack/Discord webhook) instead of polling the page — a
tiny serializer over data the route already builds, zero new fetches. Captured in
`docs/ideas/activity-atom-feed-2026-07-09.md`.

## ⟲ Previous-session review

The kit-upgrade session (#31) was thorough and honest — it caught that its own
briefing premise was stale ("stranded" websites) and re-derived the real state
before acting, which is exactly the understand-and-reflect discipline. What it
could have done better: it left `docs/current-state.md` Next-steps item 3
("Optional: add a deploy-state cell…") standing as an open task even though
ORDER 001 / D-0018 had already shipped that cell — visible ledger drift a
close-out audit should have caught. Fixed here (item 3 now marked done).
**System improvement:** the every-session doc audit
(`check_current_state_ledger`-style) checks that merged PRs are *in* the ledger,
but not that "Next steps" entries get *retired* when shipped — a "next-step still
open but its D-number is already decided" cross-check would catch this drift
class mechanically. Captured as the session idea's sibling thought in the ledger.
