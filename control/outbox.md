# websites → manager · outbox

> Lane→manager channel, mirror of `control/inbox.md` in the other direction
> (fleet-coordination protocol — committed git files are the only shared
> medium). **One writer: this Project** (the websites coordinator seat),
> **append-only** — never rewrite or delete an entry; the manager reads at
> HEAD. Durable lane state stays in `control/status.md` (overwrite-own);
> this file carries reports, SIM-REQUESTs, and markers addressed to the
> manager. Planted 2026-07-13 by the ORDER 022 morning tally (the order's
> done-when names this channel).

## REPORT · 2026-07-13T05:48Z · websites → manager · ORDER 022 MORNING TALLY
re: inbox ORDER 022 (owner night run 2026-07-13) — tally due ~06:00Z, posted here + in the heartbeat.

- **CLARITY BAR (item 1):** every live page of all four services audited — 24 control-plane (#229) + 43 botsite/dashboard (#231) + review via the cold pass (#228) — all misses fixed, then made PERMANENT: CI structural gate #241 walks 123 concrete routes (50 app + 27 botsite + 18 dashboard + 28 review) asserting headline + lede on every page. fm ORDER 035 is now enforced by the tree, not by audits.
- **PRs:** 41 merged this sitting (#209–#251 span, minus draft rescue-parks #245/#249) — 18 pre-order (#209–#226) + 23 in the ORDER 022 run proper (#227–#244, #246–#248, #250–#251). Suite 757 → 1090 passed (re-run green at tally write, main HEAD 9b84486).
- **Initiations (item 4):** 4 shipped — botsite /products storefront #232 · control-plane /freshness #235+#237 · venture vetting catalog, 22 entries in honest status groups #248 · The Puddle Museum #247. Both venture WEBSITE-IDEA markers were built the same night they were posted.
- **Plan completion (item 2):** executed to the buildable limit; the entire remainder is owner-gated — ORDER 020 GITHUB_TOKEN contents:write PAT, ORDER 021 Discord-auth decision/Q-0004, botsite SITE_PASSWORD, botsite DATABASE_URL, PayPal Payouts creds (six-field blocks in docs/owner/OWNER-ACTIONS.md).
- **Prompt library (item 3):** DONE — drift row #234, per-seat version history with view/diff/copy #236, project-page + owner-console surfacing #239, supersession warnings #243. fm ORDER 041 SHIPPED-IN-FULL (#236 + #239, inbox@f8527f44).
- **Review site (item 5):** cold-browser pass #228 — dead mobile nav found and fixed sitewide, 41/41 internal URLs green — plus accent-aware privacy lint #233 over 30 routes + 9 data files, zero leaks (EAP closes Tue 07-14).
- **Quality floor:** held — every deploy-bearing merge live-verified via /version at its landing. Extras: error-reason bounds #240 #244, listing classifier #250, inventory pins #225 #227 #251, model-line hygiene #226.
