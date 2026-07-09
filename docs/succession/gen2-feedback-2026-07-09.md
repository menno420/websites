# Gen-2 blueprint/seed feedback — from the websites gen-1 lane

> **Status:** `reference` — succession input for the gen-2 Project design.
> Written
> 2026-07-09 by a wind-down doc worker from (a) the wind-down dossier, (b) this
> repo's own retros (`docs/retro/project-review-2026-07-09.md`,
> `docs/retro/self-review-2026-07-09.md`), and (c) the coordinator's relayed
> platform-gap list. Provenance discipline: claims this lane's committed record
> supports are marked **[first-hand-in-repo-record]**; claims relayed from the
> coordinator or the fleet wind-down briefing are marked **[inherited]** —
> honest uncertainty over invented certainty; "not in this repo's record" is a
> valid finding.

---

## 1. Top three platform gaps this run (relayed from the coordinator — inherited)

These three are the coordinator's ranked platform gaps for the whole run. This
doc-writing session did not hit them all first-hand; they are **[inherited]**
accounts, but each is cross-checked against this repo's committed record where
the record speaks.

### 1a. No scheduler primitive — anywhere

There is no timer/scheduler primitive available to sessions, so every "check X
hourly" task was improvised and repeatedly stalled: the Monitor tool caps at
30 minutes (against a 60-minute need), long foreground sleeps are
harness-blocked, and a subagent arming its own sleep/timer does not re-wake the
session (one monitoring worker backgrounded its sleep and exited early twice
before delivering anything; a second idled until superseded by event-driven
monitoring). **[inherited]**, but strongly corroborated by this repo's own
record: `docs/retro/project-review-2026-07-09.md` names it stall (i), "the
single clearest platform limitation," and the retro's **F3** answer
(`docs/retro/self-review-2026-07-09.md` § F3) calls a scheduler/`send_later`
timer primitive the **one capability the lane would "trade almost anything
for."** The lane's redesign list (project-review § (d), redo item 6) and ideal
seed state (self-review F4 item 6) both carry it. Gen-2 seed implication: if a
scheduler primitive exists in the gen-2 platform, wire it into the founding
instructions; if it does not, seed the event-driven-monitoring pattern
(drift cells, webhook-style wakes) as the *stated* substitute so no lane
re-improvises sleeps.

### 1b. No sanctioned cross-session secret handoff

Per-session scratchpad isolation blocked authenticated verification: a worker
sent to verify the dashboard deployment could not complete the authed check
because the credentials file lived in another session's per-session scratchpad,
unreachable cross-session. The only working path was the owner typing the
secret's *name* (and, for values, holding them owner-side in Railway) — correct
by design, but each instance cost an owner round-trip (the `GITHUB_PAT`
auto-mode hold is the recorded example: a worker scanning the env for the
deploy token was blocked as credential-exploration until the owner named the
variable). **[inherited]** as a ranked gap, corroborated
**[first-hand-in-repo-record]** by project-review § (b) (worker row "Verify
dashboard deployment live": "BLOCKED on the authed check — credentials file
lived in the builder session's per-session scratchpad, unreachable
cross-session") and self-review B1/E2 ("Cross-session shared scratch for
non-secret handoff" is a named missing-at-boot item). Gen-2 seed implication:
an env-facts doc naming every credential (names, never values) at seed
(self-review D4 item 1, F4 item 2), plus — if the platform ever offers it — a
sanctioned shared-scratch or secret-handoff channel.

### 1c. No child-session model introspection for audits

A parent/coordinator cannot verify what model a child session actually ran on;
audits can only report "self-reported" or "inherited from spawn config, not
independently confirmed." **[inherited]** as a ranked gap; corroborated
**[first-hand-in-repo-record]** by the project-review's explicit model note:
the builder's 29 subagents are "opus-4-8 by inheritance, not independently
confirmed," and three spawned sessions are flatly "cannot determine" because
"the coordinator has no model-introspection for child sessions." The lane's
mitigation is doctrine now — retro **F1 rule 1**: every session writes its
model + effort + task in its card from card #1 (the ORDER 004 18-card backfill
is the cost of not doing this). Gen-2 seed implication: the card template
ships with the `📊 Model:` line at seed, and the blueprint should still ask the
platform for real child-model introspection — self-reporting is a convention,
not verification.

---

## 2. Known walls — verbatim strings

Exact recorded strings, each with provenance. "First-hand-in-repo-record"
means the string (or the incident) is in this repo's committed docs or was hit
directly by this wind-down's own workers; "inherited" means it comes from the
coordinator/fleet briefing and is NOT independently confirmable from this
repo's record.

1. **Proxy 403 on ruleset/branch-protection writes** —
   `Write access to this GitHub API path is not permitted through this proxy`
   — **[first-hand-in-repo-record, partially elided]**: the incident is
   recorded in self-review B1 and project-review row 14, but the repo's own
   record elides the middle of the string (`403 "Write access … not permitted
   through this proxy"`); the full form above is the known fleet wall the
   dossier matches it to. Consequence here: the agent could not set `quality`
   as a REQUIRED check; the owner set the ruleset by hand. Seed implication:
   pre-set required-check rulesets at repo creation, or give agents a
   proxy-allowed branch-protection path (self-review D4 item 3, F4 item 3).

2. **GitHub MCP rate-limit + stale-cache reads** — no verbatim error string
   exists for the staleness (it is silent, not an error). Recorded as:
   "GitHub MCP read tools served STALE/cached PR+run state (~1 min lag) →
   workers confirmed merges via `git ls-remote` instead"
   (project-review stall (iii)) — **[first-hand-in-repo-record]**. On the
   rate-limit side the repo's `docs/CAPABILITIES.md` records "GraphQL quota
   tight" and that direct `api.github.com` HTTP is blocked (GitHub is
   MCP-tools-only) — **[first-hand-in-repo-record]**; any broader fleet
   rate-limit incidents beyond that are **[inherited]**. Seed implication:
   ship `git ls-remote` as the stated merge-confirmation oracle in the
   founding docs, not a per-lane rediscovery.

3. **Pipe-swallows-exit-code trap** — `bootstrap check | tail` masking a
   real exit 1 — **[inherited]** from the wind-down briefing; NO incident of
   this is recorded in this repo's own docs (the dossier confirms the gap, and
   the wind-down session ran both verification commands unpiped and echoed
   `$?`: pytest 0, check 0). Seed implication: the verification-commands
   section of every seeded CLAUDE.md should say "never piped; check exit
   codes" — this repo's conventions already do (dossier § 5).

4. **Cross-session messaging disabled** —
   `send_message: tool is not enabled for this organization`
   — **[inherited]** from the wind-down briefing: this reportedly killed the
   predecessor session's relay mid-flight, and is the reason a *successor*
   session ran this wind-down at all. NOT found anywhere in this repo's
   committed record (a grep for `send_message` returns nothing) — record-only,
   no first-hand confirmation here. Seed implication: gen-2 coordination must
   not assume live cross-session messaging exists; the committed-file bus
   (`control/inbox.md` / `status.md`) is the reliable channel and should stay
   the designed one.

5. **Blueprint repo unreachable from lane sessions** —
   `Access denied: repository "menno420/fleet-manager" is not configured for
   this session. Allowed repositories: menno420/superbot,
   menno420/substrate-kit, menno420/websites, menno420/superbot-next`
   — **[first-hand-in-repo-record]**: hit directly by this wind-down's Phase-1
   dossier worker (dossier § 7) attempting to read
   `fleet-manager/docs/gen2-blueprint.md`; no local clone exists either. Note
   the asymmetry: the live control-plane *service* CAN read fleet-manager
   content at runtime via its own `GITHUB_TOKEN` (ORDER 005 assumes exactly
   that), but agent *sessions* in this lane cannot. This wall is a seed/scope
   suggestion in itself — see § 3.5.

---

## 3. This lane's own blueprint/seed suggestions

Each suggestion is one paragraph, tied to the incident in this lane's record
that motivates it. Sources: retro F1–F4, the project-review stall classes and
"what I'd redo" list. All **[first-hand-in-repo-record]** unless noted.

**3.1 Per-worker fresh clones + serialized ledger writes, as a founding rule.**
Early parallel workers shared one git checkout/HEAD and collided, producing
superseded PRs #5 and #9 — the run's highest pure-waste sink (self-review
A4/B1/C1; project-review stall (ii)). The lane self-fixed by serializing
ledger-touching workers and giving every worker its own fresh clone, but the
fix was learned from the collision. Retro **F1 rule 2** states it as a
founding rule; gen-2 should seed it in the founding instructions, not
re-derive it. Related first-hand gotcha worth seeding alongside: don't assume
git-worktree isolation works (the first botsite build failed with "not in a
git repository / no WorktreeCreate hooks" and was relaunched on a fresh
clone), and the wind-down worker found the shared clone sitting on a DETACHED
HEAD — branch before committing.

**3.2 Keep the born-red session gate — it works — and ship gate-tightening
with its grandfather step.** The gate's value is proven both directions: PR
#19 auto-merged EMPTY on its born-red card (a real leak, fixed by kit v1.0.0 +
diff-aware `--session-log` in PR #24, regression-tested in
`tests/test_born_red_session_gate.py`), and this wind-down's own PR #46 was
held red by the gate until the card was genuinely complete — the mechanism is
first-hand verified as recently as the last PR of the lane. Two refinements
from the record: (a) a gate-tightening upgrade must carry its
grandfather/backfill step in the same PR (the kit v1.2.0 `Model:`-line
requirement shipped without backfilling 18 old cards, so PR #38 went
false-red on an unrelated card via the mtime fallback and ORDER 004 had to
exist at all — retro F2a, B2); (b) tiny docs/status PRs with no runtime risk
could open born-complete and skip the round-trip (project-review redo item 4).

**3.3 Machine-checkable `done-when` tracking in `control/status.md`.** The
protocol's sharpest trap is that orders stay `status: new` in `inbox.md`
forever; execution lives only in the lane's own `status.md` `done=` line.
ORDER 005 is the live specimen: at wind-down, status.md reads
`orders: acked=001,002,003,004,005,006 done=001,002,003,004,006` — 005 is
**acked but unexecuted and unclaimed**, and the status notes have to warn the
successor in prose ("never infer execution from a PR title"; the retro's E4
names this exact misread as what a fresh session gets wrong first). Suggestion:
make the order lifecycle machine-checkable — a structured per-order field in
`status.md` (e.g. `order-005: acked done-when-unmet` with the order's
`done-when:` condition evaluated or at least restated per order), so `/fleet`
and a waking session compute "what's outstanding" instead of diffing three
files by hand. This is the concrete form of the retro's G3 ask
("machine-readable outstanding-orders field").

**3.4 Walking-skeleton-first, including the deploy trigger.** The lane's
smoothest stretch was skeleton-first: the control-plane deployed to Railway at
PR #3, and every later feature landed on a live, verifiable surface (merge =
deploy, `/version` drift cell as the oracle). The counter-example is the
dashboard: its Railway service was created **without a push→deploy trigger**,
so it silently served a stale sha until the board's own drift cell caught it —
a two-session hunt (PR #26 surfaced the lag, PR #29 root-caused and recreated
the trigger). Seed rule: deploy the walking skeleton first, and treat "the
deploy path itself is verified end-to-end (push → build → live sha matches)"
as part of service creation, not a later discovery (project-review redo item
2; self-review C4 item 2, F4 item 5).

**3.5 Session-scope repo lists declared up front.** The fleet-manager
access-denial wall (§ 2.5) shows the failure shape: ORDER 005 requires
rendering fleet-manager content, but no session in this lane can read that
repo — the error message itself enumerates the session's allowed-repos list,
and the blueprint the lane is supposed to feed was unreachable from the lane.
Suggestion: when the manager cuts an order (and when a lane is seeded), the
repos the work will need to *read* are declared up front and checked against
the session's configured allowlist, so scope mismatches surface at dispatch
time rather than mid-execution; the lane's own docs should record its
allowed-repos set in `docs/CAPABILITIES.md` the first time the boundary is
discovered (this repo's discovery-rule convention already fits).

**3.6 Seed an env-facts doc (credential names, Railway IDs, hard lines).**
The PAT-scan auto-mode hold cost a full owner round-trip solely because the
fact "the deploy token is named `GITHUB_PAT`" lived nowhere an agent could
read (self-review B1/D1). This repo's later `docs/RAILWAY-SAFETY.md` +
ambient-ID CI guard show the mature end-state. Gen-2 lanes should be born with
it: named tokens (names, never values), each service's Railway IDs, and the
explicit pre-authorization line for non-destructive ops ("redeploy/trigger ops
on this project's own Railway project are pre-authorized; the ambient
production IDs are the only hard line" — self-review D3/D4).

**3.7 The `.sessions/` card template ships at seed.** The `📊 Model: <model> ·
<effort> · <task>` sub-format was documented nowhere a backfiller could see it
— it had to be reverse-engineered by grepping an existing card (self-review
B4). A seeded card template carrying the Model line + the ender checklist
(idea, previous-session review, status flip) removes the whole ORDER-004 class
and is the practical half of gap 1c above (F1 rule 1, F4 item 1).

---

## 4. What this document could NOT verify

- The full, unelided proxy-403 string: this repo's record only preserves it
  partially elided (§ 2.1).
- The `send_message` error string and the predecessor-relay failure: nothing
  in this repo's record; briefing-only (§ 2.4).
- The scheduler-stall details (Monitor 30-min cap, harness-blocked sleeps,
  subagent self-timers not re-waking): relayed + reconstructed from the
  project-review's worker rows; this doc-writing session did not attempt a
  timer itself.
- Child-session models generally: unverifiable by design — that is gap 1c.
