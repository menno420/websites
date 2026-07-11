---
state: built
origin: control-plane
shipped_pr: null
shipped_repo: menno420/websites
merged_date: 2026-07-11
outcome: shipped
---

# `?repo=` filter on the activity views (`/activity`, `.json`, `.xml`) (2026-07-09)

> **Status:** `ideas` — capture only, not a plan and not approval. Source code
> and the binding contracts win over this file.

**One line:** accept an optional `?repo=<name>` query on `/activity`,
`/activity.json`, and `/activity.xml` so the owner can watch (or subscribe to) a
single lane's PR stream instead of the whole fleet — the per-repo Atom variant the
`/activity.xml` idea explicitly flagged as the natural follow-up.

## The problem it solves

With the Atom feed shipped (`/activity.xml`; see the decision ledger), the owner can subscribe to
fleet PR activity in a reader. But it is all-or-nothing: one feed of every repo.
When the owner cares about *one* lane (say `superbot-next` during the rebuild), a
per-repo feed is the difference between a focused subscription and noise. The HTML
and JSON views have the same want — "show me just this repo's recent PRs".

## Why it's cheap

`activity.timeline()` already merges per-repo `repo_activity()` results into one
list and tags every item with its `repo`. A `?repo=` filter is a one-line
post-filter over that list (validate the name against `config.REPOS`, 404/empty-
honest on an unknown repo), threaded through the three existing routes — the same
cached data, no new fetch. The Atom `self` link and feed `title` gain the repo
suffix so a reader shows *"SuperBot fleet activity · superbot-next"*.

## Lane

Small / decided — implementable. One optional query param on three routes + a
validated filter + a couple of tests (filtered stream contains only the named
repo; unknown repo is an honest empty/404, not a crash; the `.xml` self link and
title reflect the filter). No new dependency, no new data source.

## Open considerations

- Unknown/invalid `?repo=` → honest empty result (or 404), never a silent
  full-fleet fallback that misleads a subscriber.
- Keep the unfiltered default exactly as today (no `repo=` ⇒ whole fleet).
- The feed `id`/`self` must differ per filter so readers treat per-repo feeds as
  distinct subscriptions.
