# 2026-08-23 — The review site says the program is still running; it ended 2026-07-21

> **Status:** `complete`

- **📊 Model:** opus-5 · high · docs-only *(the deliverable is corrected prose; it is carried through Jinja templates, one CSS class and one test assertion that pinned the old wording)*

## 💡 Session idea

Owner directive, live 2026-08-23: *"the goal will be today to send the mail but
only after we have properly looked at everything the projects created and have a
good batch of information to send them with an updated review website if
possible. ... but first make sure everything is in order etc"*

The mail is program step **E1** — the final EAP review to Anthropic, owner-written
and owner-sent. This site is the public, evidence-backed record of that program,
and it is the surface the mail's strongest section (*"what I had to build
myself"*, `fleet-manager docs/owner-reflection-2026-07-21.md`) makes demonstrable
rather than merely asserted. So the site is a prerequisite for the mail, not a
parallel nicety.

**MEASURED 2026-08-23 against the live Pages deployment** (`curl` over the seven
public pages, tags stripped, case-insensitive scan for
`program ended|closed|concluded|no longer running|terminated`):

- **0 of 7 pages state that the program ended.** Index, fleet, growth, process,
  reviews, successes, problems — none.
- `/fleet/` renders it in the **present tense**: *"The websites lane **is** one
  seat of a fleet of Claude Projects"*, **"15 live lanes"**, "17 heartbeats
  mirrored", and links the fleet-manager registry as *"the source of truth"*.
- That registry is **frozen at generation #430 (2026-08-06)** and retired — it no
  longer regenerates (fleet-manager `docs/MAP.md` marks `registry/` RECORD tier;
  the roster was retired 2026-08-07). The seats were terminated **2026-07-21**
  (fleet-manager consolidation program, OD-5).

The recipient of this mail is the vendor who **ran and ended** that program. A
public page telling them their concluded EAP has 15 live lanes reads as careless
at best, and it undercuts the credibility the rest of the mail depends on.

**Scope:** era framing only. Every number, chart, citation and evidence link
stays exactly as baked — the record is the value (OD-17: cut RECORD-tier bulk out
of *read paths*, never CORE-tier detail; this cuts nothing). What changes is that
the site stops presenting a finished program as a running one.

**Non-scope:** re-baking the data (there are no live lanes to count — a re-bake
would refresh a mirror of a dead registry and change nothing about the framing);
the three Railway services; the mail itself (owner-reserved, `OQ-E1-FINAL-EAP-EMAIL`).

## Previous-session review

⟲ websites **#511** (`d2bba01`, 2026-08-22): the dead quality gate fixed; eight of
nine kept repos green. Checked at `main` — `d2bba01` is HEAD of this clone and the
`quality` workflow is present. Its noted residue (the fix's dispatch path runs
only when main HEAD carries zero `quality` runs) is untouched here and stays open.

## What is about to happen

The era banner in `review/templates/base.html` (following the repo's own
`rv-aged` role="note" idiom — this site already carries three honest-staleness
banners, so the mechanism is established, not invented), the `/fleet/` present-tense
corrections, the gate, then a Pages dispatch so the live surface actually changes.

## Adversarial review — `@codex`, 5 rounds, 16 findings

**`[conceded]` × 16 · `[survived]` × 0.** Every one verified against source before
accepting. Rounds: 5 · 1 · 3 · 4 · 3.

The four that changed what ships:

1. **R1 — the banner attributed post-close metrics to the program.**
   `snapshot.json` is an Aug-20 bake (`totals.prs_merged` 480) against 449 at
   close, so ≥31 post-program merges sat under *"measured during the program"*.
   That is **TRAP-004** committed inside the banner announcing this site tells
   the truth about its own era.
2. **R2 — my fix for R1 then falsified the archived editions.**
   `/reviews/2026-07-21-edition-002` states its own provenance (2026-07-20
   mirrors, 430 merged PRs) and my site-wide banner stamped August over it. A
   site-wide claim is a claim about every page, and this site's pages have
   genuinely different provenance.
3. **R3 — the homepage hero contradicted the banner directly beneath it**
   (*"the review of **running** Claude Code Projects"*). I had fixed the fleet
   page and the banner and never looked at the element above them.
4. **R4/R5 — the page advertised a live assistant that no longer exists.**
   *"a live, evidence-grounded assistant"* plus two `/ask` CTAs, then
   `site_map()`'s *"plus the live AI assistant on /ask"*, then *"even while the
   live model is degraded"*. A broken promise, not a wording slip. All guarded;
   the built export now contains **zero** assistant claims.

## Accepted open — named, not silently dropped

Codex's final round raised two P2s left unfixed, deliberately:

- **"Do not announce backend retirement in live renders."** True, and it only
  affects the non-static path, which has **no deployment** — the Railway service
  was deleted 2026-08-21. Fixing it would add a branch to a code path nothing
  serves.
- **"Qualify provenance claims when the other mirrors also fail."** A nested edge
  case of the snapshot-unreadable degradation path (snapshot *and* fleet *and*
  stats all unreadable at once). The claim is already scoped to snapshot-derived
  figures; this narrows it further inside a state no one has observed.

Rounds went 5 → 1 → 3 → 4 → 3 with severity falling to all-P2, which is where the
estate's convention says to stop cycling and say what remains.

## Verify

- `python3 -m pytest review/tests -q` → **exit 0, 296 passed** (real exit code,
  redirected never piped — TRAP-002).
- `python3 bootstrap.py check --strict` → exit 1 before this flip, on the
  designed born-red hold alone.
- `python3 review/gen_static.py` → **exit 0, 35 routes**, and every fix asserted
  against the **built export** rather than the dev render — that is what ships.
- Degradation path exercised by actually moving `snapshot.json` aside, not reasoned about.
- `grep` over the built export for every live-assistant string → **0 occurrences**.

## Layer-2 handoff

`docs/repos/websites/README.md` — the review-site thread gains the era-framing
pass; the entry point's cutover facts are unchanged.
