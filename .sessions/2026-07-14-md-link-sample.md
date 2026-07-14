# 2026-07-14 — smoke-crawl: sampled existence check of rewritten github.com links

> **Status:** `complete` — PR #328, branch `claude/md-link-sample-0714`;
> the smoke-crawl now deterministically samples up to 10 of the github.com
> blob/raw + raw.githubusercontent.com links the PR #322 markdown rewriter
> mints on control-plane pages and fails loudly on a 404, naming the URL and
> its source page.

- **📊 Model:** Claude Fable 5 · worker · backlog promotion

**What this session was about:** backlog promotion — the `docs/ideas/backlog.md`
bullet "Sample-verify rewritten source-link targets — a bounded existence check
on the github.com blob URLs the markdown rewriter mints" (captured 2026-07-14,
md-relative-links session 💡). PR #322 converted same-origin 404s inside
rendered remote markdown into EXTERNAL github.com/raw links, and the
smoke-crawl never follows or fetches external links by documented design — so
a wrong path resolution, or an upstream file rename after the TTL cache
refreshes, now yields a GitHub 404 nothing measures. This session put a floor
back under the rewrite.

## What was done

- `scripts/smoke_crawl.py` — new pass 4 (control-plane only, no new crawl
  surface): `collect_rewritten_links` extracts every `<a href>`/`<img src>`
  matching the exact URL shapes `app/journal.py`'s rewriter emits
  (`github.com/<owner>/<repo>/blob|raw/…`, `raw.githubusercontent.com/…`)
  from pages the crawl already fetches; `sample_rewritten_links` takes a
  deterministic bounded sample (sorted deduped URLs, evenly-strided slice of
  ≤10, first + last always included — no randomness, no clock);
  `check_rewritten_links` HEAD-checks each (GET fallback, ~5s/request, own
  30s budget) and `classify_rewritten_status` grades: 2xx/3xx pass, 403
  passes with a private-repo note (repo privacy, not a rewrite defect), 404
  fails naming the URL AND the page it was collected from, network errors
  are report-only warnings.
- `tests/test_smoke_crawl_rewritten_links.py` — 17 pure-logic pins
  (collector / sampler / classifier / runner), offline, no playwright.
- `docs/ideas/backlog.md` — source bullet flipped to `built`; this
  session's 💡 captured as a new bullet.
- Live proof (container, proxy workaround per docs/CAPABILITIES.md, TLS on):
  crawl of the live control-plane collected 189 rewritten links, sampled 10,
  9× 403 (the container proxy's per-session GitHub gate) + 1× 200 —
  `RESULT: PASS`.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 1414 passed, 1 warning (+17 over main's 1397);
  `python3 bootstrap.py check --strict` — green except this card's own
  designed born-red HOLD (flipped by this commit).

⚑ Self-initiated: no — backlog promotion (the md-relative-links session's 💡
bullet in `docs/ideas/backlog.md`).

## 💡 Session idea

**Disambiguate pass-4 404s from repo privacy — GitHub answers anonymous
requests to PRIVATE repos with 404, not 403** — the classification table
passes 403 as "private repo", but that 403 is the agent container's
per-session proxy gate (verified this session: the response body is the CCR
"access not enabled for this session" JSON); in proxy-less CI, GitHub itself
returns 404 for a private repo's blob URL, indistinguishable from a genuine
rewrite defect — so a scheduled-run FAIL can be repo privacy, not rot. A
small disambiguator (retry the failing repo's public visibility via the
already-whitelisted raw host or a committed known-private-repo list, and
downgrade those 404s to the private-repo note) would keep the gate's reds
honest. Worth having because the first real scheduled-run 404 will otherwise
be triaged as a rewriter bug when it may just be a private lane repo.
Deduped against `docs/ideas/backlog.md` + the queue-state NEXT list: the
flipped sample-verify bullet ships the check itself; the private-lane-filter
work is botsite-side; nothing addresses 404-vs-privacy ambiguity. Captured
in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The venture-vetting-catalog session (PR #248) did well — it derived every one
of the 22 catalog statuses from each packet's own Status/Verdict rather than
inventing, and pinned the exact 1/12/2/7 breakdown in a committed-registry
honesty test; what it missed: everything hangs off the hand-pinned
venture-lab `2c039e3` sha with no freshness signal, and its own sha-drift-pin
💡 still sits in the backlog as prose, so the page decays silently the moment
the vetting lane moves.
