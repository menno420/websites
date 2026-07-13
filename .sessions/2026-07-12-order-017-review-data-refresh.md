# 2026-07-12 — ORDER 017 workstream A: review-site data refresh (incident, 8 seats, stamps)

> **Status:** `complete` — branch `claude/order-017-data-refresh`, PR #175
> (READY + targeting main; merge is the coordinator/owner's call — this
> worker opens, never merges).

- **📊 Model:** Claude Fable 5 · worker (ORDER 017 dispatch, PR 1 of the review-site refresh) · data-refresh + feature-build

**What this session was about:** ORDER 017 (control/inbox.md, 2026-07-12T13:46Z,
P1, window through 2026-07-14 — the Anthropic Claude Code team reviews the
public program-review site this week) workstream A + the workstream-D accuracy
subset, dispatched by the sprint coordinator: regenerate every review/data
mirror through 2026-07-12; put the 2026-07-12 scheduler-degradation incident
("finding 7") first on /problems, commit-linked; reflect the ~15 → 8-seat
consolidation on /fleet from baked source data; stamp every stats surface and
footer with as-of times read from the data; make the review-bake workflow
degrade honestly at its known PR-create wall; add the review service to the
control-plane deploy board; soften/attribute every unverifiable number.

## What was done

- **Data refresh (regenerated, never hand-edited):**
  `review/data/snapshot.json` re-baked by `gen_snapshot.py` at head `869cb76`
  (4 days through 2026-07-12: 159 PRs, 193 commits, 89 session cards, 326
  test functions); `review/data/fleet.json` re-baked by the extended
  `gen_fleet.py` (2026-07-12T14:15Z, 19 lanes, 17/18 heartbeats mirrored —
  pokemon-mod-lab stays an honest 404 gap); `review/data/stats.json` landed
  for the first time, taken VERBATIM from the scheduled review-bake Actions
  run of 2026-07-12T07:38Z (run 29184552812, branch
  `bake/review-data-20260712-073843`) — this session's egress reaches the
  GitHub REST API for this repo only (other-repo calls return the session
  proxy's 403), so the pipeline's own tokened output is the honest refresh;
  regenerating locally would have written proxy errors as if GitHub said them.
- **gen_fleet.py extended:** commit-pinned `SEATS` (8 standing seats, roles)
  + `CONSOLIDATION` ("peaked at ~15 Projects; consolidation decided
  2026-07-11, canonicalized 2026-07-12T03:15Z") transcribed from superbot
  `docs/owner/fleet-8seat-structure-2026-07-11.md` @ `95fc025b` and
  fleet-manager restructure commit `639b0f09`; new `bake_seats()` joins the
  structure to the same live heartbeat fetches the lane mirror uses — seat
  numbers regenerate, never hand-written. Every evidence permalink was
  verified resolving (HTTP 200) before commit.
- **/problems now leads with the 2026-07-12 scheduler incident** as a
  structured `PROBLEMS[0]` entry (existing model + a new optional `details`
  sub-findings list, rendered by `problems.html`): three self-wake
  mechanisms, three silent failure modes (9 dropped one-shots across 5 seat
  sessions 06:12–08:23Z; 2 wedged crons frozen at 06:06/06:08; the dropped
  daily fire re-fired 08:46Z, ~2.7h late), the Q-0265 dead-man failsafe
  ("a failsafe only protects while it is alive"), serialization-vs-real-drop
  (§8 addendum), and the duplicate-fire zero-write stand-down — every claim
  linked to superbot night-review-2026-07-12 @ `8558179e`, the fig set
  @ `cbb54953`, roster gen 13 @ `10fc4f7a`, the 8-seat sweep @ `4111da4`.
- **/fleet:** new "The 8 standing seats" section (roles, per-member heartbeat
  freshness, freshest-member seat chip, consolidation phrased precisely with
  its commit links, sources line); lane grid retitled "The per-repo lanes
  under the seats". `fleetdata.seats_view()` added (honest `ok=False` on
  pre-consolidation mirrors).
- **Stamps:** as-of stamps on `/` (stat-row note) and `/growth` (hero);
  every footer now reads `data last refreshed <generated_at>` + snapshot
  commit + fleet-mirror stamp, all read from the committed data files.
- **Accuracy pass (D subset):** glossary "~10-lane fleet" → the
  peaked-~15/8-seat story; successes "0 to 226 test functions in three
  days" re-dated to the repo's first three days; growth hero de-hardcoded
  from "Three days"; "ten lanes" → "parallel lanes" (2×); index hero
  "three deployed services … in three days" → four services, dated from
  2026-07-09; the 84/85 baseline ATTRIBUTED to the night review's own
  registry evidence, never asserted bare; review SERVICES url set to the
  live https://review-production-f027.up.railway.app; milestone added for
  07-11/12 (consolidation + incident + site live).
- **review-bake.yml degrade:** both historical runs (incl. run 29184552812)
  baked + pushed their branch then FAILED the job at `gh pr create`
  ("GitHub Actions is not permitted to create or approve pull requests" —
  an owner console toggle, documented verbatim in the workflow header:
  Settings → Actions → General → Workflow permissions → allow PR creation).
  The PR-create step is now best-effort: on refusal the job stays green,
  the pushed bake branch is the deliverable, and the step summary carries a
  compare link + the owner fix. No new secrets.
- **Deploy board (ORDER 017 coordinator add-on):** `review` added to
  `app/config.py SERVICE_DEPLOY_TARGETS` (public `/version` endpoint), so
  the control-plane websites row tracks all four services; readiness
  docstrings updated; the pinned deploy-state test extended.
- **Tests (+9):** incident leads `/problems` with every sub-finding
  evidence-linked; the 84/85 attribution pinned; committed mirror carries
  exactly the 8 named seats with honest heartbeat records; `/fleet` renders
  seats + precise consolidation phrasing + the labeled private gap; footer
  stamp provably follows the data file (synthetic-snapshot monkeypatch);
  `seats_view` freshest-member + absent-section units.
- **Coordinator extension (owner directive, same session):** comprehensive
  coverage sweep — `list_repos` discovery found 19 account repos; every
  fleet repo is already covered by the registry mirror except
  `superbot-plugin-hello` (a superbot plugin satellite, NOT a registry lane
  — flagged to the manager rather than hand-added, one-source-of-truth).
  `gen_fleet.py` gained `head_probe()`: every repo-backed lane's latest
  committed state (HEAD sha + committer date) read over anonymous git
  transport (`ls-remote` + depth-1 `--filter=tree:0` fetch — reachable
  where the REST API is proxy-walled; tokenless in Actions too); rendered
  on the lane cards with honest reasons for unreachable repos. Mirrors
  re-baked at the final head (17/18 HEADs probed). `review/README.md`
  gained the manual-refresh path (workflow_dispatch → run summary →
  compare-link PR) + the exact owner toggle that retires it. origin/main
  merged in twice (landability — main advanced mid-session), no conflicts.
- **Verified (final head):** `python3 -m pytest tests/ botsite/tests
  dashboard/tests review/tests -q` — **378 passed**; `python3 bootstrap.py
  check --strict` — all checks passed (advisory-only warnings). Born-red
  gate simulated locally with the exact CI invocation before first push
  (designed HOLD observed, confirmed verbatim in the CI log); quality on
  the flip head f755ce5 completed SUCCESS in CI before the extension.
- Claim `control/claims/claude-order-017-data-refresh.md` created in the
  first commit and deleted at this flip per the claims README.

⚑ Self-initiated: no — ORDER 017 dispatch (sprint coordinator, owner-directed).

## 💡 Session idea

**Verify evidence permalinks in CI (review service).** The review site's
honesty rides on commit-pinned cross-repo permalinks that nothing checks
after commit — a force-push or repo rename upstream would rot them silently.
A tiny advisory CI step (or a `gen_*`-time check) that HEAD-requests every
`https://github.com/menno420/...` URL in `story.py` + baked JSON and warns
on non-200 would catch rot the day it happens. Worth having because this PR
hand-verified 7 permalinks with curl — a ritual a script should own. Deduped
against `docs/ideas/backlog.md` (link-check exists there only for THIS
repo's docs via the kit's doc hygiene, not for cross-repo evidence URLs).

## ⟲ Previous-session review

The /projects dispatch-view session (#158) verified scope unclaimed before
branching and render-verified its HTML through TestClient — both imitated
here (claims scan + the born-red gate simulated with CI's exact command
before push). What it missed that this session also hit: nothing checks
cross-repo permalinks after they land (see the idea above). Workflow
improvement surfaced: session-scoped egress walls (REST API reachable for
this repo only) belong in docs/CAPABILITIES.md with the verbatim proxy 403 —
this session recorded the finding in the PR body instead because the
capability ledger is outside a data-refresh PR's file scope; the coordinator
may want a follow-up slice to ledger it.
