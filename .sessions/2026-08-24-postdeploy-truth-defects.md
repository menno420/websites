# 2026-08-24 — Post-deployment truth and phone smoke defects

> **Status:** `complete` — PR #514 is ready and deliberately unmerged pending Menno's approval for the auto-deploying merge.

- **📊 Model:** GPT-5 · high · runtime bugfix

**What this session was about:** Follow the deployed first truth-and-defects tranche through its canonical browser smoke and repair only the newly measured misses: SuperBot phone overflow, one additional exact private owner link that anonymous GitHub masks as 404, and contradictory Review archive/intake wording. Preserve strict detection of every other public 404 and stop again before an auto-deploying merge.

## What remains outside this completed code session

PR #514's pinned Python 3.12 quality run supplies the hosted-interpreter verdict. The unchanged strict browser smoke and deployed-revision re-read wait for Menno's separately approved auto-deploying merge; the recovered one-off Review 503 requires no source or crawler change.

## What was done

- **Exact private navigation, not a broad crawler exception.** Control Plane deliberately renders both `pokemon-mod-lab/control/inbox.md` and `control/status.md` as useful owner destinations. Anonymous GitHub masks each as 404, so the smoke classifier now recognizes exactly those two URLs. Wrong repo, wrong ref, sibling/missing path and arbitrary public 404s still fail; ambiguous 403s remain warnings without an invented privacy claim.
- **SuperBot's three measured phone overflows fixed without clipping content.** Command-index rows become a compact two-row phone grid: long real command names wrap, summaries keep a one-line ellipsis with full details one tap away, status stays visible, and only secondary alias/permission chrome is hidden. Tighter phone-only padding and row gaps keep the 365-item reference scannable. Agent PR Check moves its recursive layout out of inline styles so phone indentation can collapse, and its leaf/footer citations wrap. Webhook Analyzer's four provenance URLs use the same explicit break utility; its generated result table remains deliberately contained in its own horizontal scroller.
- **Review's archive and intake now agree.** `/ask` limits only the retired on-page assistant and explicitly names **Ask about this page** as the active GitHub-issue intake for a later evidence-backed archive update. The live-source mode, retired endpoint/widget notice, historical answers and issue generator are unchanged.
- **Real desktop and phone use.** At 375 px, all 365 command rows fit the 360 px document surface; `!toggle_reset_on_wrong_count` wrapped to a 189 px name cell, its compact 278 px summary occupied the second row, and no permission badges remained visible. The final one-line/tighter-spacing pass reduced the Commands document from the first repair's 36,079 px to 29,806 px. A real click path through Local CLI → Merge → Branch protection → `mergeable_state=blocked` opened six nested disclosures and its verdict while body/document stayed 360 px. Webhook sample load + Analyze kept the page at 360 px, wrapped all four source URLs to 225 px, and contained the 416 px result table inside a 270 px `overflow-x:auto` wrapper. Review `/ask` rendered the scoped copy and active issue link at both 1280 px and 390 px with no page overflow. Desktop Commands retained its flex rows, original padding/gap, one-line name/summary treatment and all 365 permission badges; Agent PR Check retained its original desktop margins and padding.
- **Verification.** Focused regressions: **115 passed**, then **41 passed** after independent-review hardening, and **35 passed** for the final compact-row trim. Full trusted Python 3.13.15 suite: `python -m pytest tests/ botsite/tests dashboard/tests review/tests -q` → **2,233 passed, 5 deprecation warnings**. `scripts/check_no_ambient_railway_ids.py`, JSON parse, `git diff --check`, and the final `bootstrap.py check --strict` → **green**. The pre-flip strict run was red only on this card's designed in-progress hold.

⚑ Self-initiated: no — this is the bounded live-verification follow-up to Menno's requested 2026-08-24 website truth-and-defects tranche.

## 💡 Session idea

No new idea this session; this bounded regression repair came first, and an honest absence is better than forcing unrelated scope.

## ⟲ Previous-session review

The first tranche correctly repaired the audited truth and journey defects and proved its changed routes locally, but its deployed smoke follow-through exposed three additional source-backed edge cases that this session now owns explicitly.
