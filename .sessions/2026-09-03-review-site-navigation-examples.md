# 2026-09-03 — the review site for a first-time Anthropic reader: navigation, explanation, examples

> **Status:** `in-progress` — branch `claude/review-site-navigation-examples`;
> flips to `complete` + PR number as the deliberate LAST code step.

- **📊 Model:** Claude Fable 5 · xhigh · site build
- **📍 Venue:** cloud-container

**What this session was about:** the owner's 2026-09-02 ask (fleet-manager
`docs/prompts/2026-09-02-review-site-session.md`): make the existing
program-review site — <https://menno420.github.io/websites/> — usable by an
Anthropic reviewer who has never seen the repositories: *"easy to navigate"*,
*"explains everything properly"*, *"preferably with some examples of how we
want things to look"*, including a mockup of the claude.ai Projects overview
redrawn so each Project shows its state (*"This screen is where I'd like the
projects to be showing whether or not they are active."*). Work-ladder rung:
owner order (the prompt), executed in one attended session with no fan-out.

The cold read of the live site (ten nav pages + a fleet detail + both
editions, read before the README or any template) produced the work order,
put to the owner before editing:

- Overview: technical banners before the title; stat tiles that contradict
  the "programme ended" banner ("gen-3 generation now running", "8 standing
  fleet seats", "4 live services"); numbers scoped to this repo without
  saying so; the site map names 8 of 10 nav pages; three question-shaped
  pages with no stated difference; a footer that links three unrelated
  Railway services; every "Ask about this page" link promising routing "as
  an order on the bus" that the ended program cannot keep.
- Process: the websites repo's own bus, present tense; nothing on how eight
  Projects were run; the glossary unreachable from the nav.
- Fleet: "Project Manager" on the owner's screen is "Fleet Manager" here
  with no map; "live" beside "33d ago · stale" unexplained.
- Problems: the three problems that matter most to the owner are absent —
  workers refusing the coordinator's authority, the false "queue exhausted",
  and not seeing which Project had stalled.
- Sitewide: no timeline, no page carrying the "time after" (Projects versus
  sessions), a three-paragraph era banner on every page.

## What was done

- **Overview rewritten for a cold reader** (`review/templates/index.html`): a plain
  one-paragraph account of what a Project was and what the owner's day looked
  like; a ten-minute reading path (`story.READING_PATH`); a cited timeline
  strip; the stat tiles scoped to *this repository only* in words; the
  generations tile now `3 · generations, then the close` and the seats tile
  `Project seats at the close` (the old labels — "generation now running",
  "standing fleet seats", "live services" — contradicted the era banner two
  inches above them); the site map names all thirteen pages; the retired
  assistant demoted from a panel to one sentence.
- **Grouped navigation** (`review/app.py` NAV now `(id, label, href, group)`;
  `base.html` renders *Read first · The record · Questions*, desktop row and
  mobile drawer; `test_nav_completeness.py` unchanged — it reads `entry[2]`).
- **Era note on every page, one line off the Overview** (`base.html`): the
  full "This is a record of a programme that ended." paragraph stays on the
  Overview at `#era`; other pages carry a one-line form linking to it. The two
  data-age paragraphs became one `rv-aged` line (same claims, same class —
  `test_questionnaire.py` selects the first `rv-aged` block and still passes).
- **Three new pages, every row cited to a commit-pinned file** (fleet-manager
  at `ef3c0c8`, superbot at `8558179`; `story.fm()`):
  `/story` — the fortnight day by day (`STORY_TIMELINE`, from the owner-reviewed
  fleet account), the eight Projects in the order of the owner's 2026-07-11
  screen joined to the committed seat registry (`story.project_map`; the
  registry's "Fleet Manager" is shown as the screen's "Project Manager" with
  the registry name beside it), how a Project was run day to day
  (`PROJECT_RITUAL`, his 2026-09-02 words + the v3 registry recipe), what he kept
  (his answer 4, quoted);
  `/examples` — a finding in the target shape (headline · measured · evidence ·
  cost · fix), a real program-era card from this repo field by field with what
  each field is for (`.sessions/2026-07-20-vendored-ast-core-guard.md`, #454),
  the timeline, and the **Projects-overview mockup** (`MOCKUP_*`): eight cards
  with Working / Idle / Stalled / Needs your input, last progress, what it is
  doing now, open asks, plus the sidebar with a missed Routine — labelled
  "A proposal, not a screenshot" and "MOCKUP — proposal, illustrative values";
  names, ages and Routine names are what his screen showed, every state and
  number illustrative, and the legend says where each state would come from;
  `/after` — what a Project adds over a session, his 2026-09-02 answers verbatim
  with `OWNER` / `DERIVED` / `REVIEWED` labels per section.
- **Problems gains the three problems the owner names first**, placed right
  after the 07-12 incident (`story.PROBLEMS`): workers refusing the
  coordinator's authority (denial texts verbatim from the fm capability ledger,
  his correction of 2026-09-02), the false "queue exhausted" (his 2026-08-30
  account, superbot-next's 533/533-but-not-ported, the evidence report's
  false-done ledger), and stall visibility (his answers 1 and 2, the mails'
  asks). **Successes gains what he kept, in his words, and the instruction box**
  (adherence numbers from the retrospective § 1.3–1.4). A new optional `more`
  field renders an on-site pointer OUTSIDE the evidence list (the evidence pin
  requires GitHub URLs).
- **Stale promises removed**: `story.ask_url` no longer says a question "will be
  routed to the fleet as an order" (the program ended); the same sentence in
  `questionnaire.html`, `questions.html`, `reviews.html`, `fleet_detail.html`;
  the footer's three Railway links relabelled "The owner's other sites (separate
  services, not part of this review)" (`test_fleet_nav.py` still passes — the
  hrefs are unchanged). Reviews lede says two editions, none since the close;
  Growth lede says the charts count this repo only; Fleet explains the
  Project-Manager/Fleet-Manager name and that "live" is the bake-time
  disposition; fleet detail says what the reader is looking at; Process gets a
  Project-level section on top and `#glossary` (seven Project-level terms added
  to `GLOSSARY`).
- **Tests**: `review/tests/test_first_time_reader.py` (16 pins: nav groups, the
  tiles, the era note on every page, the three pages, the mockup's labels, fm
  citations commit-pinned, the three problems, no page promising the bus) and
  `review/tests/test_static_links.py` — a real link checker over the export:
  every internal href/src/action on every exported page must resolve to a file
  under `/websites`, no double prefix, every fragment resolves to an id on its
  target (the exporter's exit 0 only proves 200s; the double-prefix P1 shipped
  through it). Two pins updated on purpose: `test_questionnaire.py` (the
  ask-url body) and `test_review.py` (the seats-tile label).
- `.gitignore` gains `_site/` (the local export output was untracked and unignored).
- Verified: `python3 -m pytest review/tests -q` — **315 passed**;
  `env -u DATABASE_URL python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q`
  — **2525 passed** (exit 0; the first attempt errored at collection because
  the container lacked `python-multipart` from the root `requirements.txt` — an
  environment gap, installed, not a code change);
  `python3 review/gen_static.py --out _site --base-path /websites --site-url https://menno420.github.io/websites`
  — `exported 38 routes + static/`, exit 0 (35 before: the three new pages);
  `python3 bootstrap.py check --strict` — exit 1 **solely** on this card's
  born-red `[session-card-hold]`; the rest are pre-existing NOTEs
  (`scripts/preflight.py` not found; the boot-section advisory).
  Rendered locally (chromium headless over the served export) and the renders
  sent to the owner before merge: the Overview top and the mockup section.

⚑ Self-initiated: no — owner order (the 2026-09-02 review-site prompt).

## 💡 Session idea

(filled at close)

## ⟲ Previous-session review

(filled at close)
