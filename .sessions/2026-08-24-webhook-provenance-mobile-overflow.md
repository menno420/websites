# 2026-08-24 — Webhook provenance mobile overflow

> **Status:** `complete` — PR #516 is ready to merge under Menno's standing approval; post-merge deployment and the unchanged live crawl are the remaining operational verification.

- **📊 Model:** GPT-5 · high · runtime bugfix

**What this session is about:** Close the one remaining failure from the post-deployment canonical browser crawl: SuperBot `/webhook-analyzer` makes the body 13 px wider than the exact 375 px phone viewport in CI. Trace the concrete overflowing content, repair it without hiding real page overflow or removing the result table's local horizontal scroller, prove the exact live geometry through the unchanged crawl, and merge the finished green repair under Menno's standing approval.

## Post-merge verification

- Merge PR #516 once its real quality gate turns green.
- Verify SuperBot deploy convergence and rerun the unchanged live browser smoke to green.

## Shipped on the branch

- `2b7db96` — `botsite/templates/webhook_analyzer.html`: moved the existing `sb-break-anywhere` contract from URL anchors to every complete provenance list item. This covers the first source's plain-text 40-character venture-lab SHA as well as labels, details, and URLs; no factual copy or analyzer behavior changed.
- `2b7db96` — `botsite/tests/test_webhook_analyzer.py`: asserts that every configured provenance source renders inside the complete-entry wrapping boundary and that the shared utility remains defined.
- Claim PR #515 merged as `c2f31e4`; ready implementation PR: #516.

## Verification so far

- `.venv\\Scripts\\python.exe -m pytest botsite/tests/test_webhook_analyzer.py -q` → **19 passed, 1 warning**.
- `.venv\\Scripts\\python.exe -m pytest botsite/tests -q` → **722 passed** (independent repair pass).
- `.venv\\Scripts\\python.exe -m pytest tests/ botsite/tests dashboard/tests review/tests -q` → **2,233 passed, 5 warnings in 61.38s**.
- `.venv\\Scripts\\python.exe scripts/check_no_ambient_railway_ids.py` → **OK**; `git diff --check` → clean.
- Exact 375 px content canvas in a real browser: body/document **375/375** before and after Load sample + Analyze; all five provenance entries had `scrollWidth == clientWidth`; zero console errors. The generated field table stayed **416 px** inside a **285 px** `overflow-x:auto` wrapper, so only the table scrolls locally.
- Pre-flip `.venv\\Scripts\\python.exe bootstrap.py check --strict` → red only on this card's designed `in-progress` hold; the same output selected this exact card from the merge-base diff.
- Independent diff review → **GREEN, no blocking issue**. It confirmed zero user-facing text/truth changes, inherited wrapping across label/detail/SHA/URL content, and an untouched generated-table scroller; its focused rerun also passed **19 tests**.

## Capability delta

None. This was a source-level layout defect exposed by the existing Linux Chromium gate, not a new tool capability or environment wall.

⚑ Self-initiated: no — this is the final measured follow-up to Menno's requested first truth-and-defects tranche.

## 💡 Session idea

When the crawler detects horizontal overflow, report the widest few DOM scroll boxes (tag, class, client width, scroll width) alongside the page totals. Keep the assertion equally strict; richer failure evidence would have pointed straight to the provenance list item instead of requiring a second deployed investigation.

## ⟲ Previous-session review

PR #514 repaired the three known post-deployment misses and passed direct 390 px use, but the unchanged canonical crawl's exact 375 px Linux browser exposed one smaller provenance-layout edge that the earlier manual viewport did not reproduce.

## PR

PR #516 — ready; hosted `quality` was inspected and its only red was the deliberate born-red session-card hold. Flip commit and terminal green/merge are probed after this card is written.
