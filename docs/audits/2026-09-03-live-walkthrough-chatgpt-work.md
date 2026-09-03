# 2026-09-03 — live Program Review walkthrough through the owner’s Chrome extension

> **Status:** `audit` — point-in-time observations at live build `137b80eb`; three clear defects repaired in this PR. Read alongside the session card for final verification and landing. No mirror refresh, redesign or external question submission.
>
> **Venue:** chatgpt-work · **Method:** one attended Chrome-extension session, no delegation. The site was read cold before repository content.

**Does it feel intuitive to browse through? Yes, along the suggested reading path.** Overview → Story → Problems → Examples → After tells a coherent account. The three question labels and the density of the record pages cause hesitation.

**Does everything work? No, not without qualifications.** All 33 HTML pages and all 64 observed fragment URLs resolve, and the navigation, palette, theme switch and issue prefill work. Fragment positioning needed D1. Chrome blocked four machine-readable resources with `ERR_BLOCKED_BY_CLIENT`; ShiftLife’s external repository is Private. Those are not claimed as public browser passes.

**Does everything look as expected? No, not entirely.** The two themes are coherent, but the original phone glossary is plainly cramped/offscreen (D2), several linked headings are obscured (D1), and the roughly 1000px header becomes a bulky four-row block. D1/D2 and a repeated-word typo D3 are repaired. The header’s shape and the remaining presentation judgments are left for the owner.

Within a minute, a stranger can identify an autonomous-Projects programme run by one non-coding owner and see that it ended on 2026-07-21. The opening gives the owner’s role rather than his name. The mockup is unmistakably a **proposal with illustrative values**. **Q&A, Answer log and Archived answers are not distinguishable enough from their nav labels alone.** The owner’s three named problems are present and specific, but sit after the lengthy scheduler incident; they do not lead as strongly as the successes.

## Scope and measured state

- Chrome opened the supplied live URL. Banner: `this build renders 137b80eb`; 13 navigation links under Read first, The record, Questions. The connector confirmed main `137b80ebde1c0be2c25e5da7303ae55a48617eb3` and zero open PRs before this audit.
- 33 HTML pages: 13 navigation pages, **18 linked repository lanes**, two editions. The Fleet list has 25 entries, not 25 detail pages: seven are explicitly registry-only and have no repository-backed route. Both the visible links and `review/gen_static.py` agree.
- All 33 pages were opened at desktop width, and measured at 1000px and 390px in both themes. Screenshots inspect the shared layouts and the four email destinations. This is real Chrome with a measured CSS viewport, not a physical-phone/touch-device test. The short drawer check used 390×568; ordinary phone checks used 390×844. Desktop checks used 1440px.
- 114 distinct external evidence URLs were opened in the owner’s signed-in Chrome. All loaded their repository/file/PR/commit content. Seventeen source repositories were labelled Public/Public archive; ShiftLife was labelled Private. Anonymous authentication was not changed or separately tested.
- The three footer services explicitly marked outside the review were excluded. Historical snapshots and editions were not rewritten. No email was opened or changed.

Severity: **P1 broken**, **P2 confusing**, **P3 polish**; **—** means no separate finding. D1/D2 are clear, repairable P2 layout defects; they do not make the entire page unavailable. Chrome resource-opening failures are identified as browser-local failures rather than presumed site 404s.

## Pages, in the order first walked

### 1. Overview

[https://menno420.github.io/websites/](https://menno420.github.io/websites/) · **Worked:** The opening explains an autonomous-Projects programme, one non-coding owner and its end date; the ten-minute reading path works. **Confusing:** Two technical notices arrive before the account, especially on a phone; the opening identifies the owner by role rather than by name. **Looks:** Consistent layout in both themes. The 1000px header grows to four rows; #era initially lands under it (D1). **Severity:** P2. **Screenshot:** [01-overview-desktop.png](2026-09-03-live-walkthrough-evidence/01-overview-desktop.png).

### 2. Story

[https://menno420.github.io/websites/story/](https://menno420.github.io/websites/story/) · **Worked:** The dated sequence and eight-Project-to-repository map make the programme easier to understand. **Confusing:** “Doctrined”, “parity” and “seats” still demand prior knowledge. **Looks:** No overflow found; linked sections initially tuck under the header (D1). **Severity:** P2. **Screenshot:** [02-story-desktop.png](2026-09-03-live-walkthrough-evidence/02-story-desktop.png).

### 3. Problems

[https://menno420.github.io/websites/problems/](https://menno420.github.io/websites/problems/) · **Worked:** Specific incidents explain the cost, the response and the evidence; all cited sources open. **Confusing:** The owner’s three priorities follow the long scheduler incident, so they do not lead as strongly as the owner-kept work on Successes. **Looks:** The direct incident, coordinator, false-done and stall links hide their opening headings (D1). **Severity:** P2. **Screenshot:** [03-problems-desktop.png](2026-09-03-live-walkthrough-evidence/03-problems-desktop.png).

### 4. Examples

[https://menno420.github.io/websites/examples/](https://menno420.github.io/websites/examples/) · **Worked:** The finding, session card and timeline are understandable examples. The email’s mockup link clearly says “A proposal, not a screenshot” and “illustrative values”. **Confusing:** On a phone, the mockup’s sidebar precedes the cards and requires substantial scrolling. The owner’s A/B/C shape decision remains open. **Looks:** Five cards repeat “last progress progress” (D3). The direct fragment can clip the introduction (D1). **Severity:** P3. **Screenshot:** [04-examples-desktop.png](2026-09-03-live-walkthrough-evidence/04-examples-desktop.png).

### 5. After

[https://menno420.github.io/websites/after/](https://menno420.github.io/websites/after/) · **Worked:** A useful direct answer to Anthropic: what a Project adds and what must improve. The contents and OWNER/DERIVED/REVIEWED labels clarify provenance. **Confusing:** “After” alone does not predict this subject; the paragraphs are long. **Looks:** Readable in both themes and at phone width; contents targets inherit D1. **Severity:** P2. **Screenshot:** [05-after-desktop.png](2026-09-03-live-walkthrough-evidence/05-after-desktop.png).

### 6. Process

[https://menno420.github.io/websites/process/](https://menno420.github.io/websites/process/) · **Worked:** The steps and source links explain how one unit of work was recorded and merged; the glossary defines both levels. **Confusing:** “Substrate workflow” is technical. The sentence saying main republishes Review omits the known manual-dispatch case for bot merges; the repo entry guide requires a separate Pages check. **Looks:** At 390px the nowrap term column makes the glossary 478px wide in a 317px container, pushing definitions offscreen (D2); glossary fragment also has D1. **Severity:** P2. **Screenshot:** [06-process-desktop.png](2026-09-03-live-walkthrough-evidence/06-process-desktop.png).

### 7. Growth

[https://menno420.github.io/websites/growth/](https://menno420.github.io/websites/growth/) · **Worked:** The dated table exposes the numbers and their scope. **Confusing:** The UTC-day table says 45 first-day merged PRs; the gen-1 milestone says 43 merged out of 46. Different cutoffs may explain it, but this page does not say so. No number was guessed or changed. **Looks:** The charts look like very small sparklines beside the large cards on desktop. The phone table intentionally scrolls sideways. **Severity:** P2. **Screenshot:** [07-growth-desktop.png](2026-09-03-live-walkthrough-evidence/07-growth-desktop.png).

### 8. Fleet

[https://menno420.github.io/websites/fleet/](https://menno420.github.io/websites/fleet/) · **Worked:** Frozen snapshot dates and missing-data explanations are explicit. All 18 repository detail links open. **Confusing:** 25 registry entries and eight standing Projects take effort to reconcile. “Live seat” is a historical registry label on a site saying the seats ended; “fleet-manager (this repo)” is inherited wording on the websites site. **Looks:** Cards wrap without page overflow. Seven registry-only entries correctly have no detail page. ShiftLife’s repository is Private in the owner’s Chrome. **Severity:** P2. **Screenshot:** [08-fleet-desktop.png](2026-09-03-live-walkthrough-evidence/08-fleet-desktop.png).

The seven entries without detail URLs were: Curious Research seat (no repo); game-lab (no repo); Ideas Lab seat (idea-engine+sim-lab); retro-games coordinator (no repo); Self Improvement seat (substrate-kit); SuperBot 2.0 seat (superbot+superbot-next); SuperBot World seat (games+idle+mineverse). Each explicitly says “registry-only seat — no repo, nothing to mirror”. All seven were inspected; no missing lane page was invented.

### 9. Successes

[https://menno420.github.io/websites/successes/](https://menno420.github.io/websites/successes/) · **Worked:** The owner-kept work leads immediately and the evidence links work. **Confusing:** Old figures such as 226 tests and 72 sessions look current beside the prose unless the reader retains the page’s archive caveat. This is a dating/interpretation finding, not a request to refresh data. **Looks:** Cards and evidence links look consistent in both themes; no separate layout defect found. **Severity:** P2. **Screenshot:** [09-successes-desktop.png](2026-09-03-live-walkthrough-evidence/09-successes-desktop.png).

### 10. Q&A

[https://menno420.github.io/websites/questionnaire/](https://menno420.github.io/websites/questionnaire/) · **Worked:** The question-based contents are useful and all twelve question fragments exist. **Confusing:** A visitor cannot distinguish its curated answers from Answer log and Archived answers by the navigation labels alone; content overlaps with the archive. **Looks:** Long but readable answers; contents fragment headings initially hide under the header (D1). **Severity:** P2. **Screenshot:** [10-q-a-desktop.png](2026-09-03-live-walkthrough-evidence/10-q-a-desktop.png).

### 11. Reviews

[https://menno420.github.io/websites/reviews/](https://menno420.github.io/websites/reviews/) · **Worked:** Both dated editions open, and the index identifies the archive and final edition. **Confusing:** A retired-filter notice takes space despite there being only two editions. **Looks:** No overflow, broken card or date alignment found. **Severity:** P3. **Screenshot:** [11-reviews-desktop.png](2026-09-03-live-walkthrough-evidence/11-reviews-desktop.png).

### 12. Answer log

[https://menno420.github.io/websites/questions/](https://menno420.github.io/websites/questions/) · **Worked:** An honest empty ledger and a working GitHub intake link; it does not pretend to submit a form. **Confusing:** “Answer log” does not say that this is the ledger for incoming reviewer questions. Its repeated explanation adds density. **Looks:** Empty state looks intentional; no separate defect found. **Severity:** P2. **Screenshot:** [12-answer-log-desktop.png](2026-09-03-live-walkthrough-evidence/12-answer-log-desktop.png).

### 13. Archived answers

[https://menno420.github.io/websites/ask/](https://menno420.github.io/websites/ask/) · **Worked:** It plainly says the old answer mechanism is retired and gives a route to GitHub questions. **Confusing:** Its overlap with Q&A leaves a stranger unsure which answer collection to trust or read first. **Looks:** Readable archive, with no fake active form or separate layout defect. **Severity:** P2. **Screenshot:** [13-archived-answers-desktop.png](2026-09-03-live-walkthrough-evidence/13-archived-answers-desktop.png).

### 14. Lane: fleet-manager

[https://menno420.github.io/websites/fleet/fleet-manager/](https://menno420.github.io/websites/fleet/fleet-manager/) · **Worked:** The repo link, snapshot date and source heartbeat open. **Confusing:** “fleet-manager (this repo)” is misleading here; the heartbeat section contains a date without the expected parsed fields. **Looks:** No overflow; the sparse section can look unfinished. **Severity:** P2. **Screenshot:** [14-lane-fleet-manager-desktop.png](2026-09-03-live-walkthrough-evidence/14-lane-fleet-manager-desktop.png).

### 15. Lane: gba-homebrew

[https://menno420.github.io/websites/fleet/gba-homebrew/](https://menno420.github.io/websites/fleet/gba-homebrew/) · **Worked:** The repo, heartbeat source and historical kit version are readable. **Confusing:** The historical “live seat” label relies on the opening caveat. **Looks:** No distinct layout problem; long source values fit. **Severity:** P3. **Screenshot:** [15-lane-gba-homebrew-desktop.png](2026-09-03-live-walkthrough-evidence/15-lane-gba-homebrew-desktop.png).

### 16. Lane: idea-engine

[https://menno420.github.io/websites/fleet/idea-engine/](https://menno420.github.io/websites/fleet/idea-engine/) · **Worked:** The order counts, kit version and source heartbeat are available. **Confusing:** Five outstanding historical orders can look like current unfinished work without the snapshot caveat. **Looks:** Raw status text is dense but wraps at phone width. **Severity:** P2. **Screenshot:** [16-lane-idea-engine-desktop.png](2026-09-03-live-walkthrough-evidence/16-lane-idea-engine-desktop.png).

### 17. Lane: product-forge

[https://menno420.github.io/websites/fleet/product-forge/](https://menno420.github.io/websites/fleet/product-forge/) · **Worked:** The snapshot, four-of-four orders and source links are clear. **Confusing:** Green/live status is historical, not a current service check. **Looks:** No distinct layout problem. **Severity:** P3. **Screenshot:** [17-lane-product-forge-desktop.png](2026-09-03-live-walkthrough-evidence/17-lane-product-forge-desktop.png).

### 18. Lane: shiftlife

[https://menno420.github.io/websites/fleet/shiftlife/](https://menno420.github.io/websites/fleet/shiftlife/) · **Worked:** Missing heartbeat and activity data are honestly labelled; the review lane itself opens. **Confusing:** The linked GitHub repository is Private. Owner access does not establish access for Anthropic; no visibility change was made. **Looks:** The error/missing-data blocks look intentional, not a failed page render. **Severity:** P2. **Screenshot:** [18-lane-shiftlife-desktop.png](2026-09-03-live-walkthrough-evidence/18-lane-shiftlife-desktop.png).

### 19. Lane: sim-lab

[https://menno420.github.io/websites/fleet/sim-lab/](https://menno420.github.io/websites/fleet/sim-lab/) · **Worked:** Snapshot and source heartbeat open. **Confusing:** The green/live label is historical despite current-looking wording. **Looks:** No distinct layout problem. **Severity:** P3. **Screenshot:** [19-lane-sim-lab-desktop.png](2026-09-03-live-walkthrough-evidence/19-lane-sim-lab-desktop.png).

### 20. Lane: substrate-kit

[https://menno420.github.io/websites/fleet/substrate-kit/](https://menno420.github.io/websites/fleet/substrate-kit/) · **Worked:** Kit version, shipped record and source heartbeat are present. **Confusing:** The release-history prose is much more technical than the introductory pages. **Looks:** Long raw status values wrap; no horizontal page overflow. **Severity:** P2. **Screenshot:** [20-lane-substrate-kit-desktop.png](2026-09-03-live-walkthrough-evidence/20-lane-substrate-kit-desktop.png).

### 21. Lane: superbot

[https://menno420.github.io/websites/fleet/superbot/](https://menno420.github.io/websites/fleet/superbot/) · **Worked:** Hub identity and the source heartbeat are explicit. **Confusing:** The status field refers to an old documentation session, not a current product verdict. **Looks:** Dense raw record text wraps; no separate layout defect. **Severity:** P2. **Screenshot:** [21-lane-superbot-desktop.png](2026-09-03-live-walkthrough-evidence/21-lane-superbot-desktop.png).

### 22. Lane: superbot-games

[https://menno420.github.io/websites/fleet/superbot-games/](https://menno420.github.io/websites/fleet/superbot-games/) · **Worked:** Seat A identity, order counts and source links work. **Confusing:** The frozen lane says live while GitHub now says Public archive; the dates explain the possibility but the reader must reconcile it. **Looks:** No separate layout defect. **Severity:** P2. **Screenshot:** [22-lane-superbot-games-desktop.png](2026-09-03-live-walkthrough-evidence/22-lane-superbot-games-desktop.png).

### 23. Lane: superbot-idle

[https://menno420.github.io/websites/fleet/superbot-idle/](https://menno420.github.io/websites/fleet/superbot-idle/) · **Worked:** Seat B, completed order count and source links work. **Confusing:** Frozen live label versus current GitHub archive, plus long operational status, makes this a record for careful reading. **Looks:** Dense text wraps at phone width. **Severity:** P2. **Screenshot:** [23-lane-superbot-idle-desktop.png](2026-09-03-live-walkthrough-evidence/23-lane-superbot-idle-desktop.png).

### 24. Lane: superbot-mineverse

[https://menno420.github.io/websites/fleet/superbot-mineverse/](https://menno420.github.io/websites/fleet/superbot-mineverse/) · **Worked:** Repo and heartbeat source open, including the source’s closed-seat record. **Confusing:** The frozen live label contrasts with the later GitHub archive. **Looks:** No separate layout defect. **Severity:** P2. **Screenshot:** [24-lane-superbot-mineverse-desktop.png](2026-09-03-live-walkthrough-evidence/24-lane-superbot-mineverse-desktop.png).

### 25. Lane: superbot-next

[https://menno420.github.io/websites/fleet/superbot-next/](https://menno420.github.io/websites/fleet/superbot-next/) · **Worked:** Repo and closed-seat source are reachable. **Confusing:** The lane’s “finalised version” description needs the false-done account for context; its parsed heartbeat section is sparse. **Looks:** No overflow, but the date-only heartbeat area looks incomplete. **Severity:** P2. **Screenshot:** [25-lane-superbot-next-desktop.png](2026-09-03-live-walkthrough-evidence/25-lane-superbot-next-desktop.png).

### 26. Lane: trading-strategy

[https://menno420.github.io/websites/fleet/trading-strategy/](https://menno420.github.io/websites/fleet/trading-strategy/) · **Worked:** Kit version and historical source are accessible. **Confusing:** Frozen live label versus current GitHub archive; nothing here verifies a current financial outcome. **Looks:** No separate layout defect. **Severity:** P2. **Screenshot:** [26-lane-trading-strategy-desktop.png](2026-09-03-live-walkthrough-evidence/26-lane-trading-strategy-desktop.png).

### 27. Lane: venture-lab

[https://menno420.github.io/websites/fleet/venture-lab/](https://menno420.github.io/websites/fleet/venture-lab/) · **Worked:** Snapshot, kit version and closed-seat source open. **Confusing:** Historical dates are essential to interpreting the live label. **Looks:** No separate layout defect. **Severity:** P3. **Screenshot:** [27-lane-venture-lab-desktop.png](2026-09-03-live-walkthrough-evidence/27-lane-venture-lab-desktop.png).

### 28. Lane: websites

[https://menno420.github.io/websites/fleet/websites/](https://menno420.github.io/websites/fleet/websites/) · **Worked:** The 38/38 order count, kit version and last-shipped record are explicit and sourced. **Confusing:** It is the old snapshot, not the present audit branch or live build. **Looks:** No separate layout defect. **Severity:** P3. **Screenshot:** [28-lane-websites-desktop.png](2026-09-03-live-walkthrough-evidence/28-lane-websites-desktop.png).

### 29. Lane: codetool-lab-fable5

[https://menno420.github.io/websites/fleet/codetool-lab-fable5/](https://menno420.github.io/websites/fleet/codetool-lab-fable5/) · **Worked:** Archived experiment, product version and source are clear. **Confusing:** Nothing additional beyond the shared frozen-data caveat. **Looks:** No defect found. **Severity:** —. **Screenshot:** [29-lane-codetool-lab-fable5-desktop.png](2026-09-03-live-walkthrough-evidence/29-lane-codetool-lab-fable5-desktop.png).

### 30. Lane: codetool-lab-opus4.8

[https://menno420.github.io/websites/fleet/codetool-lab-opus4.8/](https://menno420.github.io/websites/fleet/codetool-lab-opus4.8/) · **Worked:** Archived experiment and succession record are clear; source links open. **Confusing:** Nothing additional beyond the shared frozen-data caveat. **Looks:** No defect found. **Severity:** —. **Screenshot:** [30-lane-codetool-lab-opus4-8-desktop.png](2026-09-03-live-walkthrough-evidence/30-lane-codetool-lab-opus4-8-desktop.png).

### 31. Lane: codetool-lab-sonnet5

[https://menno420.github.io/websites/fleet/codetool-lab-sonnet5/](https://menno420.github.io/websites/fleet/codetool-lab-sonnet5/) · **Worked:** Archived experiment and succession record are clear; source links open. **Confusing:** Nothing additional beyond the shared frozen-data caveat. **Looks:** No defect found. **Severity:** —. **Screenshot:** [31-lane-codetool-lab-sonnet5-desktop.png](2026-09-03-live-walkthrough-evidence/31-lane-codetool-lab-sonnet5-desktop.png).

### 32. Edition 1

[https://menno420.github.io/websites/reviews/2026-07-11-edition-001/](https://menno420.github.io/websites/reviews/2026-07-11-edition-001/) · **Worked:** The date, founding account and source manuscript agree; source links open. **Confusing:** “Open at press time” and “next edition” are historical prose, not present requests. **Looks:** Long edition remains readable at phone width. **Severity:** P3. **Screenshot:** [32-edition-1-desktop.png](2026-09-03-live-walkthrough-evidence/32-edition-1-desktop.png).

### 33. Edition 2

[https://menno420.github.io/websites/reviews/2026-07-21-edition-002/](https://menno420.github.io/websites/reviews/2026-07-21-edition-002/) · **Worked:** The July 21 edition states its data is as of July 20 and links the exact source manuscript. **Confusing:** The index calls it the closing edition, but the edition still contains open-at-press-time asks and “Next edition”; dates must carry the distinction. **Looks:** Long tables/text wrap or scroll within their containers; no separate layout defect. **Severity:** P2. **Screenshot:** [33-edition-2-desktop.png](2026-09-03-live-walkthrough-evidence/33-edition-2-desktop.png).

### 34. story.json

[story.json](https://menno420.github.io/websites/story.json) · **Worked:** the link selected the intended address. **Confusing/looks:** Chrome displayed “menno420.github.io is blocked”, “This page has been blocked by Chrome”, and `ERR_BLOCKED_BY_CLIENT`. **Severity:** P1 browser-open failure; site response unverified. Screenshot: [34-story-json-chrome-block.jpg](2026-09-03-live-walkthrough-evidence/34-story-json-chrome-block.jpg). No protection bypass was attempted.

### 35. Atom feed

[reviews/feed.xml](https://menno420.github.io/websites/reviews/feed.xml) · **Worked:** intended URL selected. **Confusing/looks:** the same Chrome block; navigation reported `Browser Use cannot open https://menno420.github.io/websites/reviews/feed.xml in tab 240361700. Browser reported: net::ERR_BLOCKED_BY_CLIENT`. **Severity:** P1 browser-open failure; feed contents not browser-verified. Screenshot: [35-feed-xml-chrome-block.jpg](2026-09-03-live-walkthrough-evidence/35-feed-xml-chrome-block.jpg).

### 36. fleet.json

[fleet.json](https://menno420.github.io/websites/fleet.json) · **Worked:** intended URL selected. **Confusing/looks:** the same blocked-page heading and `ERR_BLOCKED_BY_CLIENT`. **Severity:** P1 browser-open failure, not a demonstrated missing export.

### 37. releases.json

[releases.json](https://menno420.github.io/websites/releases.json) · **Worked:** intended URL selected. **Confusing/looks:** the same blocked-page heading and `ERR_BLOCKED_BY_CLIENT`. **Severity:** P1 browser-open failure, not a demonstrated missing export.

## Interaction checks

| Check | Observed result |
|---|---|
| All 13 primary links | Correct destination and active-page indication; three groups present. |
| Widths 1200 / 1100 / 1000 / 900 / 881 / 880 | Header heights 75.4 / 107.4 / 139.4 / 139.4 / 139.4 / 65px. All 13 desktop links remain available through 881px; menu replaces them at 880px. |
| Short phone drawer | 390×568: drawer client height 503, scroll height 783, scrollTop reached 280. The last link, Archived answers, became visible and clicked through correctly. The #524 drawer repair works. |
| Theme toggle | Light ↔ dark switches and persists across page navigation. Neither theme produced invisible text or a new horizontal page overflow in the inspected layouts. No formal contrast-ratio certification is claimed. |
| Slash / Ctrl-K | Both open the 13-page palette. “After” narrows to one result; Enter navigates. Escape closes. An unmatched query shows No matches. No visible shortcut hint was found (P3 discoverability). |
| Fragment targets | All 64 observed fragment URLs have an existing target, including both slash/non-slash forms. D1 affected where the target appeared, not whether it existed. |
| Priority fragments | /#era; /process/#glossary; /story/#projects; /story/#ritual; /examples/#projects-overview-mockup; /problems/#coordinator-authority, #false-done, #stall-visibility, #incident-2026-07-12. All nine checked again at 1440, 1000 and 390px after D1: 27/27 targets below the header. |
| Phone tables | Growth’s wide data table has its own horizontal scroller. The glossary scroller moved from scrollLeft 0 to 161.5, proving it operated, but its forced column proportions were a clear reading defect (D2). |
| GitHub intake | Opened the Overview’s actual prefilled issue URL. Title: `[program-review] Question: overview page`. Body identifies the page and explains normal-PR archive answers and the 2026-07-21 programme end. Nothing submitted. |
| External evidence | 114/114 opened in owner Chrome, including fleet-manager files at ef3c0c8 and superbot files at 8558179. The superseded gen-1 candidate opens as that candidate, not as a claim that the candidate was sent. [Per-link ledger](2026-09-03-live-walkthrough-evidence/external-links.md). |

## Clear defects repaired in this PR

**D1 — fragment headings covered by the sticky header (P2).** The original coordinator link placed its heading around 15px from the top beneath a 65px header; the 1000px header was about 139px tall. The review page script now measures the header’s actual height, including row wrapping, and supplies native scroll padding. No heading, link destination or page order changed. [Before](2026-09-03-live-walkthrough-evidence/61-problems-link-before-light.png) · [repaired desktop preview](2026-09-03-live-walkthrough-evidence/54-coordinator-fixed-desktop-dark.jpg). Files: `review/static/site.css`, `review/static/site.js`.

**D2 — phone glossary definitions pushed offscreen (P2).** At 390px the 317px table container held a 478px table, with most width reserved for unbroken term labels. The first row was about 540px tall and initially showed only “Project”. Phone glossary columns now fit within 317px and term labels can wrap; both columns are visible together. [Before](2026-09-03-live-walkthrough-evidence/60-glossary-phone-before-light.png) · [repaired light preview](2026-09-03-live-walkthrough-evidence/57-glossary-fixed-phone-light.png) · [repaired dark preview](2026-09-03-live-walkthrough-evidence/55-glossary-fixed-phone-dark.png). File: `review/static/site.css`.

**D3 — “last progress progress” repeated in five mockup cards (P3).** Removed the duplicated leading word from those illustrative values. Times, counts, states, proposal labels and layout are unchanged. The repaired rendered page contains no “progress progress”. File: `review/story.py`.

## Verification and open decisions

- Browser proof for the repairs: 27/27 priority anchor/width combinations clear the header; phone glossary width equals its container; the mockup retains its proposal wording and no longer repeats the word. [Measured checks](2026-09-03-live-walkthrough-evidence/checks.json).
- Static exporter: `exported 38 routes + static/` (exit 0). This is export evidence, not a substitute for link or browser testing.
- `python -m pytest tests/ botsite/tests dashboard/tests review/tests -q`: **2525 passed, 5 warnings in 453.66s** (exit 0, installed Python 3.13.15). This includes the complete Review suite. The session card records the final strict-check result. The first strict run held only this session’s deliberately in-progress card. Pages requires a manual `review-pages.yml` dispatch after merge; final live-build verification belongs to the close-out message, not a pre-merge claim in this immutable report.
- **Owner decision carried:** examples shape A/B/C, and whether/how a second site pass should address the wording, ordering and visual-density findings. No choice was made on the owner’s behalf.

[Session card](../../.sessions/2026-09-03-live-walkthrough-chatgpt-work.md) · [PR #525](https://github.com/menno420/websites/pull/525)
