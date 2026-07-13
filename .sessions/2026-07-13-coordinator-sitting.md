# 2026-07-13 — Coordinator sitting record: 2026-07-12→13 overnight run + morning orders (STEP-5 RETRO)

> **Status:** `in-progress` — coordinator ender, branch
> `claude/coordinator-ender-2026-07-13`; flips to `complete` + PR number as
> the deliberate LAST commit of this ender.

- **📊 Model:** Claude Fable 5 · coordinator seat (ender worker) · session-close/retro

**What this session was about:** the coordinator sitting 2026-07-12 ~20:50Z →
2026-07-13 ~11:05Z — the ORDER 022 night run plus the morning owner orders
023–026 — closed out per the session ender (steps 5–9): this retro card,
docs trued to now, two bake proposals to the manager, the CLOSED heartbeat,
then the flip. Every claim below re-verified against `git log` / the GitHub
API / `list_triggers` at write time (Q-0120), not carried from memory.

## RETRO — (a) Shipped & parked

- **63 PRs merged to main in the sitting window** (every window commit a PR
  squash; span **#209–#275**, verified by counting `(#N)` squash subjects on
  `origin/main` between 2026-07-12T20:40Z and 2026-07-13T11:10Z), including
  the two bot-authored bake PRs **#259 = `bcf2943`** (review data refresh)
  and **#270 = `5b9c6f7`** (fleet data refresh). #268 closed-superseded
  (ORDER 025 landing raced; #271 landed it). Suite **757 at sitting start →
  1206 passed** (four-suite run green at this write, 62s).
- **Orders:** 016 DONE (#209 = `89130c4`, done-marked by heartbeat #211 =
  `8998c0b`) · 022 night run EXECUTED — tally posted #252 = `d35e619`;
  clarity bar #228/#229/#231 made CI-permanent by the 123-route structural
  gate #241; prompt library #234/#236/#239/#243; review cold pass #228 +
  privacy lint #233; initiations #232/#235/#237/#247/#248; batch-2 venture
  intake complete: seven pages #254/#255/#256/#258/#262/#266 (+#248 catalog,
  #247 museum) · 023 SERVED (#265 = `1f320a4`) · 024 DONE (#264 order,
  fix #267 = `9eb877c` — commit subject mislabeled "ORDER 023", content is
  the 024 /prompts current-files fix) · 025 DONE (#273 = `a3c511a`
  /owner/briefing + creds guidance, OWNER-ACTIONS Decided row N) ·
  026 RESOLVED CREATE-NOTHING (#275 = `cedca1e`, findings ledgered).
  Fleet-manager ledger: fm 035 standing (CI-enforced via #241) · fm 041
  SHIPPED-IN-FULL (#236+#239) · fm 042 SATISFIED (#253 ack).
- **Routines disposition (re-verified this ender via `list_triggers`,
  3×100-entry pages covering every trigger created since 2026-07-12T16:52Z):**
  pending coordinator tick `trig_016CQoxoBh97cgsTSiDyC56Z` deleted —
  **verified absent**; no enabled send_later is bound to the coordinator
  session. Failsafe `trig_019cGrUpfHSMv4qLk5tn2hgr` **LEFT ARMED** (cron
  `45 */2 * * *`, enabled=true, next fire 2026-07-13T12:45Z) as the
  successor bridge. Bake-bridge trigger self-retired 05:33Z (intended
  end-state, do not re-arm). The review-bake cron is a repo GH workflow with
  its first scheduled SUCCESS recorded (run 29235587736). No uncloseable ids.
- **Parked:** draft PRs **#245 / #249 / #257** (kit-stub lifeboats; verified
  the only open PRs at write). Landing path: owner-click close — the content
  is kit churn (auto-drafted cards + state.json), nothing valuable. **Zero
  seams left open** — no half-landed work, no stranded branches.

## RETRO — (b) Struggles (verbatims in the PR body; summarized here)

- **Platform scheduler late-delivery:** the 00:45Z failsafe + 01:39Z
  pacemaker tick arrived late; recovered 02:10Z with no lost work
  (subsequent fires on schedule).
- **GITHUB_TOKEN bake PRs can't trigger required checks:** GitHub suppresses
  workflow triggers on GITHUB_TOKEN-created events (anti-recursion), and the
  dispatch-chained run hit the 405 ruleset wall — worked around by
  close/reopen + non-author review-merge; measured limit + the BAKE_PAT ask
  landed in #274 + docs/CAPABILITIES.md.
- **Secret-store writes need owner-live-in-session authority:** the ORDER
  026 write attempt was classifier-walled; resolved honestly as
  create-nothing (#275), findings recorded.
- **Kit auto-draft session stubs repeatedly dirtied the shared checkout** —
  the real time sink of the sitting: 3 lifeboat draft PRs (#245/#249/#257)
  plus `rm` classifier denials on cleanup.
- **Background workers parked on timers/monitors 3×** (dead per fleet
  memory — workers are not resumed by sleep); fixed each time by
  re-messaging the worker.
- **Duplicate pacemaker tick** forked once (two outstanding one-shots);
  deduped by deleting the extra.
- **One enabler miss via a `control/*` branch prefix** — the auto-merge
  enabler arms `claude/*` only; re-landed on a `claude/*` branch.
- **#247/#248 botsite nav conflict:** two parallel same-service dispatches
  raced claims and collided on nav wiring; resolved at merge.

## RETRO — (c) What went well

- The **born-red → flip pipeline** landed 63 PRs with **zero bad merges**,
  and every deploy-bearing merge was live-verified via `/version` (quality
  floor held the whole sitting).
- The **close/reopen + non-author-review-merge pattern** landed both
  bot-authored bake PRs (#259, #270) despite the checks wall.
- **Reuse-first slices kept new network surfaces at zero** — every new page
  rides the existing TTL-cached raw-content/REST layers or committed JSON.
- **Honest create-nothing resolutions** (ORDER 026; the gotchas guard)
  preserved the trust surfaces instead of faking capability.

## RETRO — (d) Surprises & open questions

- **Venture WEBSITE-IDEA markers arrived mid-night and 7 of 8 were buildable
  the same night** — intake-to-live latency of hours, not days.
- **Lead:** the dashboard service carries an undocumented `SITE_PASSWORD`
  variable (ORDER 026 discovery, #275) — worth reconciling with the docs.
- **Lead:** an `ANTHROPIC_API_KEY` may live on the parallel botsite copy
  (same discovery pass) — worth a read-path check.
- **Open question:** does the ruleset ever accept dispatch-event check runs
  as the required `quality` check, or is the BAKE_PAT path the only durable
  fix? (#274 records the measured wall.)

## What was done (this ender)

- This card (first commit, born-red), then: docs/current-state.md trued to
  now + docs/site.md §3g//prompts route row rewritten to the post-#267
  reality; two manager-addressed proposals appended to control/outbox.md;
  control/status.md overwritten with the SESSION CLOSED heartbeat;
  the flip (last commit). Full shipped/parked/walls/lessons report with
  verbatim denials: this PR's body.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — **1206 passed**; `python3 bootstrap.py check --strict`
  — green apart from this card's designed born-red hold until the flip.

⚑ Self-initiated: no — session-ender steps 5–9, coordinator-assigned.

## 💡 Session idea

**Embed the manager outbox tally in /owner/briefing** — give the morning
briefing page a "reports to the manager" section that renders the newest
`control/outbox.md` REPORT entry (same committed-file read path the fleet
pages already use). Worth having because the owner's morning read and the
manager's roll-up currently live at two URLs; one briefing URL carrying both
means the ORDER 023-style "post your night report" ask is satisfied by a
page the owner already opens. Deduped against `docs/ideas/backlog.md` (83
bullets — no briefing or outbox entry) and against `app/briefing.py` at HEAD
(sections: shipped/orders/asks/fleet/watches — no outbox section). Captured
in `docs/ideas/backlog.md` (this ender's docs commit).

## ⟲ Previous-session review

The 2026-07-12 kit-upgrade sitting (v1.15.0, #199) did the carve-outs
exactly right — banked pre-regen files, split host jobs out of the kit-owned
enabler verbatim, and left a lane-owed list the night run could execute
against; what it missed is that the auto-draft Stop-hook it distributed
became this sitting's biggest time sink (three lifeboat PRs of pure kit
churn), so the workflow improvement is routed to the manager this ender:
worker briefs gain a standing "kit stubs → scratchpad, never commit" line.
