---
state: captured
origin: control-plane
shipped_pr: null
shipped_repo: null
merged_date: null
outcome: open
---

# `/activity.xml` — an Atom feed for the cross-repo activity timeline (2026-07-09)

> **Status:** `ideas` — capture only, not a plan and not approval. Source code
> and the binding contracts win over this file.

**One line:** emit the `/activity` timeline (see `docs/site.md`) as an Atom/RSS
feed at `/activity.xml` so the owner can subscribe to fleet PR activity in any
reader (or pipe it to a Slack/Discord webhook) instead of polling the page.

## The problem it solves

`/activity` (shipped — see `docs/site.md` § Routes) gives the owner a single glanceable screen of
recent PRs across all four fleet repos. But it is **pull-only** — you have to open
the page to see what changed. With ten Projects running in parallel, a **push**
surface (a feed a reader or a webhook can watch) is the natural next step: the
owner subscribes once and new merges arrive without visiting the site.

## Why it's cheap

`app/activity.timeline()` already produces a normalized, sorted list of
`{repo, number, title, author, state, ts, url}` items. An Atom feed is just a
second serializer over that exact list — no new fetches, no new data source, it
rides the same TTL cache. Add one route (`/activity.xml`) returning
`application/atom+xml`, map each item to an `<entry>` (title = `repo #num title`,
link = `url`, updated = `ts`, author = `author`, id = the PR URL). Bounded the
same way the HTML view is.

## Lane

Small / decided — implementable. One route + one template (or an f-string
serializer with XML-escaped fields), a couple of tests (feed validates, entries
carry links + timestamps, honest-empty when no PRs). No new dependency.

## Open considerations

- XML-escape titles/authors (reuse `html.escape`, or `xml.sax.saxutils.escape`).
- Feed `updated` = newest entry's `ts`; stable feed `id` = the route URL.
- Optionally a per-repo variant (`/activity.xml?repo=superbot`) later.
