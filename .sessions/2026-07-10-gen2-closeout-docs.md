# 2026-07-10 — Gen-2 close-out: docs sweep + ORDER 008 wake routine armed

> **Status:** `in-progress`

- **📊 Model:** withheld per session policy
- **Start (UTC):** 2026-07-10T13:50:28Z

**What this session is about to do:** the gen-2 close-out / hand-off pass after
ORDER 005 + 007 shipped (#51–#54). (1) Execute **ORDER 008** (claimed on main via
fast-lane PR #56, `claimed-by: 008 gen2-closeout 2026-07-10T13:48Z`): self-arm the
lane's 4-hourly wake routine and document the exact mechanism. (2) Docs sweep:
append the fleet-manager anonymous-readability correction + the routine-creation
capability to `docs/CAPABILITIES.md` per the discovery rule; resolve/refresh the
wake-trigger ⚑ in `docs/owner/OWNER-ACTIONS.md` (preserving the verbatim
coordinator probe error); add the next-session brief to the queue-state ledger
(resume point, non-derivable facts, the coordinator's independent live
verification); move the session-memory-only gotchas (Jinja `q.items`,
container `GITHUB_TOKEN`) into `.session-journal.md`; update
`docs/current-state.md`. A final control-fast-lane heartbeat PR
(status overwrite, done=001–008) follows this PR's merge.

## What was done

- **ORDER 008 executed** (claim-first per `control/README.md`: fast-lane PR
  #56 landed `claimed-by: 008 gen2-closeout 2026-07-10T13:48Z` on main, bus
  re-read clean): wake routine self-armed via
  `mcp__claude-code-remote__create_trigger` → trigger
  `trig_017H9Qb9oxtLgUy6sw2gnSHg`, cron `0 */4 * * *`, enabled,
  fresh-session-per-fire in this environment, prompt = the standing inbox
  ritual, `next_run_at 2026-07-10T16:00:31Z`. First fire is after this
  session ends — recorded as **armed, first fire unconfirmed** everywhere
  (status, OWNER-ACTIONS conditional fallback ⚑, CAPABILITIES caveat);
  the first routine-woken heartbeat is the confirmation.
- **`docs/CAPABILITIES.md`**: two discovery-rule append entries —
  fleet-manager is anonymously readable (corrects the "runtime-token-only"
  inference; evidence = the app's own runtime fetch path returning real
  content tokenless during the PR #53 build; the session-side allowlist wall
  stands and is a tooling-scope fact, not a visibility fact) and
  routine-creation works from this worker surface (coordinator surface still
  has no scheduler tool — verbatim probe error preserved). Seed wall bullet
  annotated as partially superseded for routines.
- **`docs/owner/OWNER-ACTIONS.md`**: Open row 7 (external wake trigger) →
  Decided row E (self-armed, ORDER 008); the active ⚑ replaced by a
  CONDITIONAL fallback (act only if no fresh heartbeat by 2026-07-11);
  historical coordinator probe error + no-scheduler statement kept verbatim.
- **`docs/planning/queue-state-2026-07-09-winddown.md`**: next-session brief
  (resume point = NEXT item 2, the `/fleet` manifest-parse smoke check; then
  items 3–4; non-derivable facts incl. routine state, fleet-manager
  readability, the re-justified GITHUB_TOKEN ⚑; the coordinator's independent
  live verification of all three services at `330f9b4`, ~02:50Z 2026-07-10 —
  attributed to the coordinator).
- **`.session-journal.md`**: durable homes for the Jinja `q.items`
  dict-method gotcha and the container-`GITHUB_TOKEN` /
  local-proxy-blocks-contents-API gotcha (both previously only in off-repo
  session memory). The third dossier gotcha (stamp-discipline, one-doc-home
  per `[D-NNNN]`) was already durable in the journal's "Recurring problems"
  — not duplicated.
- **`docs/current-state.md`**: shipped entry for this close-out.

## 💡 Session idea

**Machine-readable `routine:` line in the status heartbeat + a
routine-state column on `/fleet`** — each lane's status.md carries e.g.
`routine: armed · 0 */4 * * * · last-fired <ISO8601>` (the woken session
updates `last-fired` on every wake), and `/fleet` renders armed/stale-fire
badges. Why worth having: ORDER 008 makes every lane self-arm its clock, and
"armed but silently dead" is now the exact failure nothing surfaces — a
routine that stops firing looks identical to a healthy idle lane until
someone diffs timestamps. This folds naturally into queue-state NEXT item 4
(heartbeat enrichment), which covers outstanding-orders/deployed-sha but not
routine state. Deduped against `docs/ideas/` (README, atom-feed [done],
per-repo filter, scheduled-healthcheck-workflow — that one is a CI-side
healthcheck cron, adjacent but distinct: it watches the sites, not the
lanes' wake clocks).

## ⟲ Previous-session review

Previous session: `.sessions/2026-07-10-order-005-queue-environments.md`
(PRs #52–#54). Did very well: claim-first discipline, keying degradation off
the actual fetch result instead of the dossier's stated wall (which is why
the pages shipped live, not needlessly degraded), and honest correction of
the "fleet-manager is private" inference in its card + status. One genuine
miss: that correction never reached `docs/CAPABILITIES.md` the same session
— the discovery rule's step 4 ("append the finding same session") applied,
and only the build PR could have carried it (the status PR is control-only
by design, but PR #53 was a full PR with no such constraint). The finding
lived in status.md + an off-repo dossier until this close-out paid the debt.
Concrete workflow improvement: treat a CAPABILITIES.md append as part of the
same commit that exploits the discovery — a one-bullet diff riding the build
PR — rather than deferring capability facts to a later docs pass; off-repo
dossiers evaporate with the session that wrote them.

- **End (UTC):** 2026-07-10T13:53:46Z
