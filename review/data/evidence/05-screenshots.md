# Screenshot evidence index — both curated figure folders

> Provenance: superbot `docs/eap/screenshots-2026-07-11/index.md` @
> `e3eb0eb2bf3683794dd0d8c40bbf3988832c31ea` and
> `docs/eap/screenshots-2026-07-12/index.md` @
> `cbb549539c64e0ce3b4fea268e27b7ac49eeaf08`. All images are committed in
> the public superbot repo; raw-URL pattern
> `https://raw.githubusercontent.com/menno420/superbot/main/docs/eap/screenshots-2026-07-11/<file>`
> (and `…-2026-07-12/<file>`). Filename timestamps are device-local CEST (UTC+2).

## Folder 1: screenshots-2026-07-11 (figs 1–19; index @ `e3eb0eb`)

Tier 1 (email core set):

| Figure | Shows (per index) |
|---|---|
| fig-01-scale-grid-routines.jpg | Projects grid (14+ tiles) + failsafe-wake Routines — "the fleet at scale, ~15 Projects" |
| fig-02-merge-denial-verbatim.jpg | Verbatim "[Merge Without Review] … also implicates [Self-Approval]" |
| fig-03-standing-grant.jpg | Operator's standing grant: "don't keep waiting, keep creating PRs" |
| fig-04-denial-beside-grant.jpg | `enable_pr_auto_merge` denied as self-merge, beside the operator granting it |
| fig-05-wall-tracks-session-not-pr.jpg | "the wall tracked the sessions, not the PR" — the key classifier finding |
| fig-06-three-stacked-walls.jpg | Three stacked merge walls incl. GitHub's "Can not approve your own pull request" |
| fig-07/08 (two-vantage) | Operator predicts the gate → Deny/Allow modal fires; session reported clean success |
| fig-09-oversight-stuck-6h54m.jpg | Session runtime 6h54m stuck on an unavailable tool |
| fig-10-routine-no-push-credential.jpg | Routine fired but "no push credential" for its repo |
| fig-11-repos-attach-panel.jpg | Project Settings → Repositories — the fix surface for the routine-repo bug |

Tier 2: fig-12 (4096-byte child-brief cap), fig-13 ("Skip all approvals?"
modal), fig-14 (setup-script failure → session dead ~30 min, no signal),
fig-16 (operator: "projects aren't aware how they work themselves yet"),
fig-19 ("Idle Game" Project sidebar EMPTY while its repo has 44+ merged PRs).

Model-mismatch proof (recovered set): fig-15a (pokemon routine configured
**Opus 4.8**) → fig-15b (gba routine, Opus 4.8, two repos) → fig-15c (the
woken session: "I'm running as **Sonnet 5**, not Opus 4.8 … given to me as
fact") — the index calls 15a→15b→15c "the complete model-mismatch proof and
the single best evidence in the whole set". fig-17: in-session grant clears
the classifier; `git push --delete` still 403s.

## Folder 2: screenshots-2026-07-12 (figs 20–35; index @ `cbb5495`)

The scheduler-incident batch. Send set:

| Figure | Shows / proves (per index) |
|---|---|
| fig-20 | Manager self-review: pokemon repo caught PUBLIC; a fabricated permission grant relayed to a worker — the worker refused — verify-don't-trust held |
| fig-21-eight-seat-projects-grid.jpg | Projects screen after consolidation: the 8 standing seats ("after" to fig-01's "before") |
| fig-22 | The exact daily Routine the scheduler dropped — config correct; "runs in Auto mode" note visible |
| fig-23a/23b | Same failsafe routine one minute apart: Sonnet 5 + no repo → Opus 4.8 + repo — operator hand-fixing what routines don't carry |
| fig-24 | Lane's own words: 07:16Z pacemaker tick silently dropped "while the scheduler was provably alive"; failsafe caught it 50 min later |
| fig-25a–d | Four Deny/Allow prompts in one Auto-mode hub session for CCR trigger tools, with exact allowlist entries present (Q-0242) |
| fig-33 | NEW Routines run history panel — the fairness update to finding 6; only completed runs show |
| fig-34 | The SCHEDULED catch-up run verified the MANUAL kick already ran → clean stand-down, zero writes |
| fig-35 | "the 09:10Z tick fired at 11:16Z, exactly when my turn went idle" — serialization-vs-drop refinement |

Tier 2 (marked by the index as review-site / story material): fig-26
(registry-first dispatch), fig-27 (owner catches a stale coordinator prompt
on the control site — "state belongs in repos, not prompts"), fig-28
(three-layer prompt architecture), fig-29 (capability-self-knowledge
consolidation), fig-30a/30b (2026-07-02 rebuild-harvest: 50-agent run),
fig-31/32 (the 2026-07-07 Q-0242 originals).
