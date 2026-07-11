# Self-review 2026-07-11 — websites lane, last ~24h (ORDER 011)

> **Status:** `audit` — owner-directed fleet-wide self-review (ORDER 011,
> P1, filed 2026-07-11T09:59Z, relayed by the fleet-manager coordinator on
> the owner's in-session instruction). Window: 2026-07-10 ~20:00Z →
> 2026-07-11 ~10:20Z. Written by the continuous-mode chain that did the
> work — honest, citation-tied, in this lane's report convention
> (`control/status.md` is overwritten every wake, so the dated section
> lives here; the heartbeat carries the pointer + mirrored ⚑ items).

## 1 · What went wrong (each with citation)

**Mistakes made by this lane (and how they were corrected):**

- **PR-number misprediction** — the slice-2 session card pre-wrote "PR #66"
  but a sibling took #66 and the real PR was **#67**; fixup commits
  corrected card/ledger/current-state. Discipline adopted since: open the
  PR first, flip the card with the real number after (held for all
  subsequent slices). Citation: PR #67 fixup commits.
- **Cron-arithmetic error, repeated 5×** — heartbeats stated the
  healthcheck cron's next slot as "~02:17Z"; `17 */6 * * *` anchors to
  wall-clock hours 00/06/12/18, so the real slot was 06:17Z. Wrong in five
  consecutive heartbeat overwrites before self-caught. Corrections:
  `docs/CAPABILITIES.md` cron finding + `scripts/cron_slots.py` with the
  incident pinned as a test. Citation: PR #96 (`cbc87c8`).
- **Claim-classifier false positive (caught pre-merge)** — the /orders
  claim matcher initially regex-matched order ids inside claim free text,
  so id "00" matched inside the "21:00Z" timestamp; caught by this lane's
  own boundary test before merge and rewritten to numeric matching against
  the claim's id-spec token only. Citation: PR #77 (`b30b4f1`),
  boundary case pinned in `tests/test_orders.py`.
- **Suite-scope overclaim in evidence (caught pre-merge)** — the slice-19
  card first said "pytest tests/ → 235 passed" when 235 is the FULL
  three-service suite (tests/ alone was 177); corrected before merge, and
  cards now state both numbers. Citation: PR #109 close-out.
- **Doc-truth drift in our own orientation ledger** —
  `docs/current-state.md` went 17 slices stale and carried four claims
  that were no longer true (kit version, "PAT is set", manifest-as-registry,
  exhausted NEXT pointer). Found and fixed by a rung-5 sweep. Citation:
  PR #111 (`13554fc`).

**Things that broke or misbehaved (none shipped broken):**

- **Time-bomb test detonated** — at 2026-07-11T08:45Z
  `test_overview_sorts_stranded_landing_above_healthy_and_counts` began
  failing on an UNTOUCHED tree: fixed fixture stamps crossed
  `FLEET_STALE_HOURS` against the real wall clock inside
  `fleet.overview()` and flipped the attention sort. Defused same hour
  (injectable `now=`, PR #111); the class-wide guard then **caught 17 more
  latent sites across 5 test files** (PR #114, `02adf7c`). Without the
  catch, every PR after 08:45Z would have gone mystery-red on the required
  check.
- **Upstream registry supersession broke /fleet's lane source** — the
  superbot fleet-manifest went `historical` and parsed to ZERO lanes;
  caught by run 2 of the new healthcheck cron (a real regression catch,
  not flakiness) and repointed to the fleet-manager `gen_roster.py` LANES
  registry, live-verified at 18 lanes. Citations: cron PR #69 (`fc8354e`),
  repoint PR #102 (`ce2ec38`), registry decision stamped in `docs/site.md`
  § Routes + the decision ledger.
- **Routine-fired (4-hourly) sessions are unreliable landers** — the
  04:03Z fire did work but stranded its heartbeat (no PR tooling in that
  session; rescued verbatim by this chain as PR #98, `b09d0b1`); the
  ~08:00Z fire left no trace at all (second silent window). The relay
  doctrine (any session may land another's green control-only work) is now
  written in `control/README.md`. Citations: PR #98, PR #99 (`d6b91c9`).
  The send_later chain has been the lane's only consistent producer.
- **Born-red first CI runs on every build PR** — each build PR's first
  quality run is red BY DESIGN (in-progress session card holds the merge);
  flagged four times by the coordinator as possible failures (#69, #72,
  #75, #96 first runs), each verified as the designed hold with log
  evidence, resolved by the flip commit. Not a defect; noted because red
  runs in the Actions history need this reading key.
- **Merge 405s (branch-behind-main)** — the ruleset requires up-to-date
  branches; sibling merges raced this chain's PRs four times (#64, #67,
  #69, #75-era); each resolved by merging origin/main and re-greening.
  Expected friction of parallel lanes, no losses.
- **Kit upgrade regressions found here, fixed upstream** — v1.9.0
  `upgrade --apply-docs` silently dropped the carve-out audit section
  (hand-restored; flagged to the kit lane; fixed in kit #176, verified on
  the v1.10.0 upgrade) and the model-doctrine idempotence check missed
  emphasis-wrapped phrasing (flagged; fixed in kit #187, verified on
  v1.10.1). Citations: PRs #101, #105, #113 session cards.

**Walls hit (verified, in `docs/CAPABILITIES.md`):**

- `api.github.com` blocked from session containers (proxy 403) — GitHub
  MCP tools work for menno420/websites only; `scripts/open_work.py`
  degrades to "PR state unknown".
- Agents cannot delete remote branches (403) — hence the prune list below.
- GitHub Actions cron is best-effort delivery — never gate on a slot
  (finding recorded after the cron watch).

## 2 · Requiring owner attention (click-level)

- **⚑ Botsite database (blocks the public submission feature):** in
  railway.app open project `superbot-websites` → New → Database →
  PostgreSQL; then open service `botsite` → Variables → add
  `DATABASE_URL` = the connection string Railway shows. One paste. Until
  then the public /submit form stays a labeled stub. (Agent-side is
  policy-walled: the Railway-safety decision in the ledger forbids
  agent-initiated Railway mutations.)
- **⚑ GitHub token (rate headroom for all fleet pages):** on github.com go
  to Settings → Developer settings → Fine-grained tokens → create a token
  scoped to your repos (contents+actions read; actions write if you want
  the CI re-run button); then railway.app → `superbot-websites` →
  `control-plane` → Variables → set `GITHUB_TOKEN`. Today every fleet page
  runs on the anonymous 60-requests/hour ceiling. Exact steps:
  `docs/deployment.md` § owner TODO.
- **Branch cleanup (one click each, agents get 403):** delete four stale
  remote branches whose content is verified landed or abandoned:
  `claude/harden-verify`, `claude/rework-dashboard`,
  `claude/wire-github-token-docs`, `manager/control-plant`.
- **Decide-and-flag decisions taken this window (reversible, no veto
  needed unless you disagree):** repointing /fleet's lane registry to the
  `LANES` literal inside fleet-manager's `scripts/gen_roster.py` (decision
  in the ledger; honest but coupled to a script's internals — the standing
  ask to the manager for a generated `lanes.json` makes it stable); adopting the
  relay-landing doctrine in `control/README.md`; self-arming this lane's
  4-hourly wake trigger (ORDER 008) and running the send_later
  continuation chain through the 2026-07-14 free window.
- **Spend/publish:** none — no Railway resources created, no external
  publishing, live bot untouched.

## 3 · Current health (one line)

**Green and shipping:** 22 slices + 2 rescues landed and deployed
(#64→#114, this review in flight) — fleet-info surfaces (/fleet /orders
/reviews /projects /queue /ideas + JSON contracts), registry migration,
board chips, nav overflow guard, time-bomb defuse + class guard (237
tests, deterministic), kit at v1.10.1; next: quality.yml every-card gate
port, then nav manifest; backlog holds 3 buildable bullets and the lane
is ready for routed work.
