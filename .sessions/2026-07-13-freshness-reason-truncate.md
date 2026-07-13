# 2026-07-13 — freshness reason truncate: sanitize failure reasons on /freshness

> **Status:** `complete` — PR #237, branch
> `claude/freshness-reason-truncate`; every user-visible /freshness
> failure reason is now bounded (markup bodies → generic
> `HTTP <status> — non-JSON error body`, 140-char ellipsis cap); lands
> via the auto-merge enabler on green.

- **📊 Model:** Fable 5 · worker · bugfix-slice

**What this session is about:** hardening the just-shipped `/freshness`
page (PR #235) against raw upstream error bodies. Live observation: during
a transient GitHub failure, the fetch envelope's `error` text — a full
HTML error page — rendered unabridged into a table cell
(`unknown — <!DOCTYPE html> <!-- Hello future GitHubber!...`). The
honest-degradation contract says "unknown — \<reason\>", but the reason
must be a short human-readable string, not a wholesale error document.
Fix: a `_short_reason()` helper in `app/freshness.py` that collapses
whitespace, replaces markup-looking bodies with a generic
`HTTP <status> — non-JSON error body` message, and hard-truncates to
140 chars with `…`; every user-visible reason (commit / card / PRs /
heartbeat cells, and the `/freshness.json` twin via the shared builder)
routes through it. Short meaningful errors like `HTTP 404` stay verbatim.
Tests in `tests/test_freshness.py` cover the HTML-body, long-plain-text,
and short-reason cases.

⚑ Self-initiated: yes — follow-up hardening of the /freshness page shipped in PR #235 (live-observed defect)

## Close-out (auto-drafted 2026-07-13 — edited)

<!-- substrate:auto-draft -->

**Evidence (auto-collect corrected — the draft swept the whole repo
history; this session's actual touches):**

- code touched (1): `app/freshness.py` — `REASON_MAX_CHARS = 140` +
  `_short_reason()` (whitespace collapse, markup body → generic
  `HTTP <status> — non-JSON error body`, hard 140-char ellipsis cap,
  short reasons verbatim, empty stays empty); `_unknown()` routes every
  reason through it (envelope status passed at the card/heartbeat call
  sites); `repo_row()` shortens the fleet-built commit/PR reasons in
  copies (bounded here, /fleet's own rendering untouched); `overview()`
  shortens the lane-source fallback-banner reason (same interpolated
  registry error, same hazard — one line beyond the enumerated cells,
  flagged in the PR). `/freshness.json` fixed by the same change — the
  twin shares the row builder.
- tests touched (1): `tests/test_freshness.py` — new section (f), 4
  tests: HTML DOCTYPE body → generic short form, no injected `<!DOCTYPE`
  in the rendered page; row-level reasons generic/single-line/bounded
  across all four signals; long plain-text → 140-char ellipsis
  truncation; short reasons (`HTTP 404`, collapsed `rate\nlimited`)
  verbatim, empty → empty. 11 → 15 tests, all offline via the existing
  monkeypatched `github._get` / `fetch_file` / `repo_api` idiom.
- git: branch `claude/freshness-reason-truncate`, main 20a00d0 →
  97dfc59 (claim + born-red card) → d10f2aa (fix + tests) → this flip.
- commits this session (3): "claim: freshness-reason-truncate — sanitize
  /freshness failure reasons…" · "/freshness: truncate non-JSON error
  bodies in unknown-reason cells" · "flip: freshness-reason-truncate
  card complete + claim released".
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` → `961 passed, 1 warning in 52.04s`;
  `python3 bootstrap.py check --strict` → green except this card's own
  designed born-red HOLD (flipped by this commit) and the pre-existing
  never-exit-affecting `owner-action-fields` advisory on
  control/status.md (not owned here).

**Judgment:**

- Decisions made: sanitize at the freshness layer, not in
  `fleet._envelope_reason` or `github._get`, so /fleet's rendering and
  the client contract stay untouched by a page-scoped hardening PR;
  markup detection is deliberately blunt (starts with `<`, or contains
  `<!doctype`/`<html`) because an error page is never a reason worth
  quoting; the envelope status is kept in the generic phrase where the
  envelope is still in hand (card/heartbeat) and honestly dropped where
  fleet's builders already discarded it (commit/PRs).
- Next session should know: PR #237 rides the auto-merge enabler; the
  live defect is reproducible only under transient GitHub failures, so
  post-merge confirmation is just "no document-shaped reasons on
  /freshness during the next hiccup".

## 💡 Session idea

**Move reason hygiene to the envelope source** — `github._get` already
truncates non-dict error bodies to 200 chars, but still hands raw HTML
chunks to every consumer; a `_short_reason`-style guard inside
`fleet._envelope_reason` (or the `_result` envelope itself) would bound
/fleet's banners, the owner UI messages, and any future page for free
instead of each page re-fixing this. Deduped against
`docs/ideas/backlog.md`: no existing bullet covers envelope-level reason
sanitization (line 174's `classify_listing` idea is adjacent but about
listing-state classification, not error-body hygiene).

## ⟲ Previous-session review

The repo-freshness-page session (#235) did well — the honest-degradation
contract ("unknown — <reason>", never a 500) is exactly why the page
survived a transient GitHub failure without crashing; what it missed is
that honesty about WHY needs a bound on HOW MUCH: it piped
`fleet._envelope_reason` output into cells verbatim without asking what
the envelope's `error` field can contain (a 200-char HTML chunk, per
`github._get`). Workflow improvement: when a design says "show the
reason", check the reason's worst-case SHAPE at the source that mints
it — one Read of `app/github.py` at build time would have caught this
before it shipped.
