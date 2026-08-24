# 2026-08-24 — Website truth and verified defects

> **Status:** `complete` — PR #513 is ready and deliberately unmerged pending Menno's approval for the auto-deploying merge.

- **📊 Model:** GPT-5 · implementation coordinator · runtime bugfix

**What this session is about:** Complete the first evidence-led truth-and-defects tranche from Menno's 2026-08-24 live website UX audit. Repair verified broken journeys and contradictory public claims across the four products in this repository, preserve its public/read-only and owner-gated boundaries, and stop before the auto-deploying merge for Menno's approval.

## What remains outside this completed code session

PR #513's pinned Python 3.12 quality run supplies the hosted interpreter verdict. The live smoke crawl and deployed-revision re-read wait for Menno's separately approved auto-deploying merge.

## What was done

- **Three Control Plane crawl failures fixed at source.** Fleet-only file views now return to their useful `/fleet#lane-…` seat instead of minting a nonexistent journal route; `_inventory` remains visible as registry metadata through its GitHub tree but is no longer rendered as an internal project package; and the crawler's anonymous GitHub-404 allowance is path-exact to the verified-private `pokemon-mod-lab/control/inbox.md`. A public 404 and a near-miss private path still fail; an arbitrary 403 remains a visible warning and is never mislabeled as proof of privacy.
- **Dashboard defects made measurable.** `/ideas` now emits one semantic `<article>` per idea instead of invalid nested anchors that Chromium expanded into empty duplicates. `/commands` has a page-scoped phone layout that wraps long names/descriptions/metadata, and the smoke crawl measures both body and document width so global clipping cannot hide overflow. Public read-only copy now distinguishes the separately Discord-gated `/admin` actions.
- **SuperBot's numbers now name different concepts.** Source data contains 485 registry entries and 365 distinct command names; the 297 feature-area names plus an explicit 68-name `Other` category reconcile to 365. Home and Commands state that taxonomy, the Other filter works, and Status calls itself a dated committed-inventory snapshot rather than live uptime. Phone navigation keeps Add Bot and Menu visible; equivalent Search and Theme controls live at the top of the scrollable mobile drawer.
- **Portfolio, Review and boundary truth corrected.** `/directory` is the exact audited eight-product inventory with friendly URLs and explicit public/read-only/archive boundaries. At 390 px each product becomes a labelled card instead of a squeezed five-column sideways-scroll view. Program Review's public/static mode calls the retired assistant material **Archived answers**, retains its active external GitHub-issue intake, and no longer advertises a live model. Current-state, product docs, source comments, OAuth callback guidance and the Review README now agree on three Railway services plus the GitHub Pages archive, and distinguish site OAuth/session secrets from the deliberately absent live bot-control credential.
- **Real-browser proof.** Desktop and 390 px runs exercised Control Plane, SuperBot, Dashboard and Review from local source. Dashboard rendered 256 nonempty idea cards for 256 ideas; its 485 command rows had zero width offenders. SuperBot rendered 365 command rows, filtered to 68 Other rows, and its phone Status page fit a 375 px content viewport. The mobile drawer's Search opened and focused the command palette, Theme changed the active theme, and the drawer scrolled without page overflow. The directory rendered eight products with every field visible and no page/table overflow; the Product Forge backlink was clicked through to its fleet lane; `_inventory` had no internal route; Review's archive CTA opened an `Archived answers` page. Browser-console errors: zero.
- **Verification.** Trusted local Python 3.13.15: `python -m pytest tests/ botsite/tests dashboard/tests review/tests -q` → **2,231 passed, 5 deprecation warnings** in 3m54s. Focused adversarial regressions → **90 passed** for shared/SuperBot/Review and **33 passed** for Dashboard. `scripts/check_no_ambient_railway_ids.py` → **green**; `git diff --check` and JSON parse → **green**. The pre-flip `bootstrap.py check --strict` was red only on this card's designed in-progress hold; the final strict gate runs against this completed card before the closing commit. The repo-local `uv` Python 3.12.14 `_ssl` Application Control wall and safe trusted-interpreter workaround are recorded in `docs/CAPABILITIES.md`; GitHub Actions supplies the pinned 3.12 verdict.

⚑ Self-initiated: no — this tranche is directly requested by Menno and grounded in `Hub/records/2026-08-24 live website UX audit.md`.

## 💡 Session idea

No new idea yet; the evidence-led repair work comes first, and an honest absence is better than forcing an unrelated addition.

## ⟲ Previous-session review

The 2026-08-23 Review era-framing session rigorously removed live-program and live-assistant claims from the static export; it left the intentionally bounded reader-facing label simplification and repository-wide current-state drift for this follow-on tranche.
