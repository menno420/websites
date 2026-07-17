# websites — ideas backlog

> **Status:** `ideas` — the single backlog list (rung 3 of the work ladder,
> `docs/project/project-instructions.md`). One bullet per idea (or one file in
> this directory + a bullet here). Dedup before adding; states per `README.md`:
> `captured → planned → built → retired`. Seeded 2026-07-10 from the ideas
> already scattered across session cards, the queue-state NEXT list, and the
> retros — each with its source cited.

## Captured / planned (pick highest-value buildable first)

- **Arcade + dashboard overnight proposal menu** · `captured` (2026-07-16,
  arcade-dashboard-menu session 💡) — 24 distinct veto-ready proposals across
  botsite/Fleet-Arcade and dashboard, small fixes → ambitious features, grouped
  by service with pitch · effort (S/M/L) · risk & reversibility · what it
  unblocks. Why: owner overnight order (event 55f13541) for a broad morning
  veto-ready menu. Source:
  `docs/planning/arcade-dashboard-menu-2026-07-16.md` (event 55f13541).

- **Shared `drift_report()` renderer — one structured join, three
  surfaces** · `captured` (2026-07-16, release-drift session 💡) — the
  healthcheck's release-drift pass (PR #365 `check_release_drift()`) and
  the owner console's verification chips share verdict logic (askverify
  probes on ask_id) but not presentation, and the baton's console
  release-drift chip plus a future botsite banner (gated on the #355
  SIM-REQUEST answer) would each re-implement the same blocker→probe
  join. A small helper returning structured rows (registry, slug, ask_id,
  verdict, reason) would let the healthcheck text block, the console
  chip, and the banner all render from ONE join. Worth having because the
  join is subtle to get right (claim-once probes, one-probe-per-ask
  dedupe, honest unknown/not-checkable semantics) and three hand-copies
  of it is exactly the drift class this repo keeps closing. Deduped
  against this backlog: the arcade live-URL drift probe, the prompts
  registry-drift chip, and the env-drift bullets each cover a different
  drift surface; nothing covers a shared structured renderer for the
  ask_id release-drift join. Source:
  `.sessions/2026-07-16-release-drift.md` 💡.

- **Fast-lane pin-map drift pin — assert quality.yml's grammar-pin
  selection stays aligned with the machine-read control files and real
  test paths** · `captured` (2026-07-13, fastlane-outbox-gate session 💡)
  — the fast-lane grammar-pins gate (PR #314) is shell text inside
  `.github/workflows/quality.yml`: it hard-codes two test paths and two
  control filenames, and nothing ever executes that mapping in the full
  lane — rename `tests/test_outbox_grammar_pin.py`, move the outbox, or
  add a third machine-read control file and the gate goes hollow while
  staying green. A small pytest that parses the workflow's lane step
  (YAML + the embedded shell) and asserts (1) every referenced pin test
  file exists on disk and (2) every control file the app machine-reads
  (`app/briefing.py`'s OUTBOX_PATH, `app/fleet.py`'s status parsing) has
  a pin entry would redden the PR that breaks the mapping. Worth having
  because a gate that exists only as unexecuted workflow shell decays
  invisibly — exactly the merge-lag class PR #314 just closed for the
  outbox. Deduped against this backlog: the shipped "Fast-lane control
  gates in quality.yml" bullet is the gates themselves, not a pin on
  their mapping; the env-sweep shape-coverage bullet covers the env
  scanner, never CI. Source:
  `.sessions/2026-07-13-fastlane-outbox-gate.md` 💡.

- **Hostile-env import smoke — dynamically import every service module
  under a poisoned environment** · `built` (2026-07-13, PR #287 —
  `tests/test_hostile_env_smoke.py` imports every runtime module of all
  four services in a subprocess per service per poison mode (every
  documented env var set to `""`, then to garbage; 8 subprocesses, poison
  passed via `subprocess.run(env=...)` so nothing leaks into pytest;
  failures name the module + carry the subprocess traceback); zero real
  crash sites found — PR #282/#285 hardening held; captured 2026-07-13,
  env-guard-gate session 💡) — the dynamic complement to `tests/test_env_guard_gate.py`
  (PR #285): set every documented env var (the envhub manifest knows the
  names) to "" and "garbage", then `importlib.import_module` every module
  in app/, botsite/, dashboard/, review/, proving no import-time crash of
  ANY kind. Worth having because the static gate only sees `int()`/
  `float()` — `json.loads`, date parsing, `.split()[0]`, or a `Path`
  read over an env var at module level are the same crash class and
  invisible to an AST cast-scan; a real import under hostile values
  catches them all. Deduped: `test_env_parse_hardening.py` reloads only
  `app.config` with hostile INT_VARS; the healthcheck bullets probe live
  `/healthz`, never imports. Source:
  `.sessions/2026-07-13-env-guard-gate.md` 💡.
- **Suite-level token pin in `tests/conftest.py` — ambient-env independence
  as structure, not discipline** · `built` (2026-07-13, PR #309 —
  new `tests/conftest.py` autouse fixture
  pins every control-plane test to the unset rung: `config.GITHUB_TOKEN`/
  `config.RAILWAY_TOKEN` forced to `""` plus both env vars deleted, on a
  private `pytest.MonkeyPatch` instance so a test-level `monkeypatch.undo()`
  can't strip the pin; rung-specific tests keep opting in explicitly and
  their patches win. The unpinned-reason-assertion flake class is now
  impossible — a test's meaning can never again change with whether the
  runner exports a token (this dev container proxy-injects one, CI may
  not). botsite/dashboard/review suites verified token-free (review's only
  runtime read is stubbed at the `fetch_issues` seam), so the pin lives in
  `tests/` only. Full four-suite run proven identical with tokens exported
  and deleted. Source: `.sessions/2026-07-13-tighten-ladder-pins.md` 💡.
- **Manifest completeness diff — "what is missing to finish this
  environment"** · `built` (2026-07-12, PR #216 —
  `envhub.annotate_completeness` badges every manifest schema row against
  the slice-1 `railway.live_overview` NAME read: set-live / missing-live,
  honest `unknown` when the token is unset, the read fails, a per-service
  fetch errors, or the group is outside the token's scope — never a
  fabricated green/red; a service absent from a successful live read is
  honestly missing-live ("not created yet"); group summary "X/Y set live";
  the copyable plan blocks stay pure committed-registry output) — original
  capture: the ORDER 021 slice-2 manifest page
  (`/owner/environments-hub/manifest/{group}`) renders the owner-executed
  plan (names + placeholders); merging the slice-1 live variable-NAME read
  (superbot-websites group, project-scoped `RAILWAY_TOKEN`) would badge
  each schema row set-live / missing-live, turning the plan into a
  run-down checklist. Worth having because the owner executes these plans
  by hand and today must eyeball the console against the plan to know what
  remains. Distinct from the estate-page drift-check bullet below (that
  one is documented-vs-live on `/owner/environments`; this is
  manifest-vs-live per project group). Source:
  `.sessions/2026-07-12-environments-hub-slice2.md` 💡.

- **Completeness chip on the environments-hub group headers** · `built`
  (2026-07-12, PR #219 — `envhub.group_summary` runs a minimal
  manifest-shaped stub per group through the UNCHANGED PR #216
  `annotate_completeness`, fed from the SAME cached `railway.live_overview`
  read the hub index already makes, zero new network surface; chip beside
  each group's manifest link: green "X/Y set live" when complete, amber
  when unfinished, honest "live status unknown" WITH the exact reason
  (token unset / read failed / out-of-scope group) — never a fabricated
  0/Y) — original capture:
  the hub (`/owner/environments-hub`) links each group's manifest but
  gives no hint which environment is unfinished; reusing PR #216's
  `envhub.annotate_completeness` to render the group summary ("18/25 set
  live" / "live status unknown") as a chip next to each group's
  create-complete-environment manifest link would surface "which
  environment needs finishing" on the front door itself. Worth having
  because the checklist is one click deep per group — the hub index is
  where the owner actually decides where to spend the next console visit.
  Deduped against this backlog + the queue-state NEXT list: nothing
  touches hub-level summaries (the projects-registry completeness bullet
  is a different page and data source). Source:
  `.sessions/2026-07-12-envhub-completeness-diff.md` 💡.

- **Environments-completeness rollup chip on the /owner board** · `built`
  (2026-07-12, PR #223 — `envhub.board_rollup` runs the UNCHANGED PR #219
  `group_summary` across ALL registry groups and reduces it to ONE chip on
  the gated /owner readiness board, fed by the SAME cached
  `railway.live_overview` read the environments-hub makes, zero new
  network surface, zero new routes: green "environments: all complete"
  when every readable group is strictly complete (out-of-scope groups
  counted honestly as `+M unknown`, never assumed), amber "environments:
  N groups incomplete" with the groups NAMED + the hub deep link, honest
  "live status unknown" WITH the exact reason (token unset / read failed /
  broken registry) — never a fabricated green or 0/Y) — original capture
  (recorded on the #219 card but never appended here; backfilled by the
  building session): the group completeness summary exists as a cheap pure
  function (`envhub.group_summary`) over the cached live read, but it only
  renders on the hub index; the /owner readiness board — the owner's
  actual habit path — says nothing about unfinished environments; one chip
  there repeats the promotion ladder that paid off twice (#213's /prompts
  drift chip → #217's /fleet coverage rollup). Worth having because the
  hub is a click the owner must remember to make, while the board is where
  he already looks every session. Source:
  `.sessions/2026-07-12-envhub-group-chips.md` 💡.

- **/owner/environments drift check: documented vs live variable names** ·
  `built` (2026-07-12, PR #218 — `app/envdrift.py` `annotate()` diffs the
  committed `railway.SERVICES` names against the slice-1 live NAME read per
  service: documented-but-missing-live / live-but-undocumented chips + a
  page-level rollup + per-variable "live (Railway)?" badges on
  `/owner/environments`; Railway unreachable → honest drift-unknown with the
  exact reason, never a fabricated match; Railway-provided `RAILWAY_*` names
  and runtime-injected `PORT` classified informationally, not drift; a
  documented service absent from a successful read = honest drift, the #216
  semantics) — original capture: once the owner's project-scoped
  `RAILWAY_TOKEN` lands, the
  page holds both halves of a diff it does not yet compute: the COMMITTED
  documented env-var names per service (`app/railway.py` SERVICES) and the
  LIVE names Railway reports. One comparison column (documented-but-unset /
  set-but-undocumented badges per service) turns the page from two lists
  into an actionable drift detector, exactly like the readiness board's
  deploy-drift cell. Worth having because undocumented live variables are
  invisible config debt and documented-but-missing ones are outage
  foot-guns — today both hide in plain sight. Deduped against this backlog
  + the queue-state NEXT list: nothing touches env-var drift. Source:
  `.sessions/2026-07-12-order-015-owner-environments.md` 💡.

- **Committed-inventory consistency pin: `railway.SERVICES` vs the envhub
  registry** · `built` (2026-07-13, PR #225 —
  `tests/test_inventory_consistency.py` pins the two inventories to each
  other, zero network: service-name sets, per-service variable-NAME sets in
  BOTH directions with named-variable failure messages, and URLs, over the
  real `envhub.load_registry` loader; explicit per-entry-justified
  allowlists for legitimate one-sided variables — currently empty — with a
  stale-allowlist check so exemptions cannot outlive their reason; the one
  found drift reconciled evidence-first: `ANTHROPIC_API_KEY` added to
  SERVICES' botsite entry, the registry side proven right by
  `docs/owner/OWNER-ACTIONS.md` row K + the live consumer
  `botsite/testing_ai.py`) — original capture: the repo hand-keeps TWO
  committed inventories of
  the same four services' variable names (`app/railway.py` SERVICES and
  `app/data/environments.json`'s superbot-websites group) and they have
  already drifted (the registry documents `ANTHROPIC_API_KEY` for botsite;
  SERVICES does not — verified 2026-07-12). One zero-network suite test
  asserting the two name sets agree per service (or a declared-exceptions
  list) would catch repo-internal doc drift that the PR #218 live check
  cannot see — the live diff compares each source against Railway, never
  against each other. Worth having because both surfaces claim to document
  the same truth and their silent divergence makes one of them lie to the
  owner. Deduped against this backlog + the queue-state NEXT list: nothing
  pins the two committed inventories to each other. Source:
  `.sessions/2026-07-12-owner-envs-name-drift.md` 💡.

- **Tester-task URL liveness guard** · `built` (2026-07-12, PR #221 —
  `botsite/testing_probe.py` cold-fetches every `status: "open"` task's
  `product_url` via a new `check_testing_urls` pass in
  `scripts/healthcheck.py` (the 6-hourly healthcheck.yml schedule); reuses
  the arcade probe's `probe_url` verdicts (final-200, redirects followed),
  flags non-200 / timeout / connection error / malformed or missing URL,
  prints explicit "not probed" lines for `coming-soon`/`closed` tasks,
  fail-soft per URL plus a zero-task catalog alert, folds into the script's
  exit-1-on-failure idiom; catalog loader extracted to
  `botsite/testing_catalog.py` so the probe and `/testing` read the SAME
  loader; the required `quality` gate stays network-free —
  `httpx.MockTransport` throughout. The bullet's render-time-probe and
  auto-flip-to-`coming-soon` variants were NOT taken: the healthcheck-pass
  variant alerts without adding request-path network calls or data
  writes) — original capture: every `open` task in
  `botsite/testing_tasks.json` points a paying tester at a `product_url`;
  if that URL dies (service renamed, deploy broken) the program burns real
  testers' time and its own credibility before anyone notices. A small
  check — `scripts/healthcheck.py` growing a testing-catalog pass, or a
  botsite startup/`/testing` render-time probe — that verifies each open
  task's `product_url` answers 200 and visibly flags (or auto-treats as
  `coming-soon`) the ones that don't, keeps the catalog honest by default;
  same pattern would auto-open the seeded coming-soon game tasks the day
  their games deploy. Worth having because the tester program's whole pitch
  is "real products, honestly described" — a dead link is the fastest way
  to break that promise. Deduped against this backlog + the queue-state
  NEXT list: healthcheck ideas exist for fleet services, nothing touches
  the testing catalog. Source:
  `.sessions/2026-07-12-order-018-testing-platform-pr1.md` 💡.

- **Guide chat transcript as exit-review evidence** · `built` (2026-07-13,
  PR #292 — `guide_exchanges` table in `botsite/testing_store.py`;
  successful chat exchanges persist per claim, bounded by the existing
  guide cap, and attach to the submission: grade + re-grade prompts carry
  an `<untrusted_guide_chat_transcript>` engagement-evidence block, the
  owner queue and tester status page render it, the JSON export carries
  it; the frame path stays write-free and the guide page discloses the
  persistence) — original capture: the
  guided-walkthrough side panel (ORDER 018 PR3) generates a per-step Q&A
  between tester and AI guide, but it evaporates when the tab closes: the
  exit reviewer grades the final answers blind to how the tester actually
  engaged. Persisting the TEXT transcript only (bounded, per claim — screen
  frames stay in-memory-only by the privacy contract) and appending it to
  the submission as untrusted context would let the grader and the owner see
  engagement, confusion points, and coached-vs-independent answers. Worth
  having because the program pays on report quality and the guide already
  produces first-hand evidence of it that is currently thrown away. Deduped
  against this backlog + the queue-state NEXT list: nothing touches the
  guide flow (it ships this PR). Source:
  `.sessions/2026-07-12-order-018-testing-guided-mode-pr3.md` 💡.

- **Shared contents-listing honesty classifier** · `built` (2026-07-13,
  PR #250 — `github.classify_listing(result, *, on_404, reason_404,
  subject) -> (state, reason)` with the 404 disposition as the explicit
  per-caller parameter; migrated `projects.overview`, `projects.detail`,
  `prompts.registry_drift` AND `ideas.repo_ideas` onto the one ladder;
  honest supersets where the copies had diverged: token-unset failures
  name the token on /prompts and /ideas, non-list 2xx payloads say
  "unexpected listing payload (HTTP <status>)" everywhere, and every
  composed reason is re-bounded by `short_reason` at 140 chars) —
  original capture: three
  surfaces now hand-roll the same degraded-listing ladder over a
  `github.repo_api` contents result: `projects.overview`, `projects.detail`
  (404 → empty / no-token → not-configured / else unavailable) and
  `prompts.registry_drift` (any failure → unknown, 404 reworded). One
  helper (e.g. `github.classify_listing(result) -> (state, reason)`) with
  the 404 disposition as an explicit parameter would make the pages share
  one ladder and make deliberate differences declared instead of
  re-derived. Worth having because the honesty ladder is the site's core
  UI promise and three hand-rolled copies have already begun to diverge —
  the next copy forks it silently. Deduped against this backlog + the
  queue-state NEXT list: nothing touches listing-degradation plumbing.
  Source: `.sessions/2026-07-12-prompts-registry-drift-chip.md` 💡.

- **/prompts pinned-registry drift chip** · `built` (2026-07-12, PR #213 —
  `prompts.registry_drift` cross-checks the pinned `SEATS` against the live
  `projects/` contents listing via the SAME TTL-cached `github.repo_api`
  URL /projects fetches, zero new network surface; chip states: matched ✓ /
  "pinned list drifted: +X new in registry / −Y no longer present" with the
  actual seat names / listing unavailable = drift UNKNOWN, never a
  fabricated green; empty-but-listed registry is real drift, not unknown) —
  original capture: the /prompts
  artifact list is pinned in `app/prompts.py` (the raw host cannot list
  directories), so a seat added or renamed in fleet-manager `projects/`
  silently degrades to a 404 cell here until someone edits the constant.
  One cheap cross-check: when the /projects registry listing is available
  (same TTL cache, zero extra fetch on a warm cache), compare its directory
  set against `prompts.SEATS` and render a "pinned list drifted: +X / −Y"
  chip on /prompts. Worth having because the page's one honest weakness is
  registry drift, and the site already fetches the ground truth elsewhere.
  Deduped against this backlog + the queue-state NEXT list: nothing touches
  the prompt library (it ships this PR). Source:
  `.sessions/2026-07-12-prompt-library.md` 💡.

- **Deep-link fleet lane files into the widened /journal/{repo}/file view**
  · `built` (2026-07-12, console-home discoverability PR — every /fleet
  lane card header now links the lane's status source and its
  `docs/current-state.md` through the in-app `/journal/{repo}/file`
  renderer (`fleet._file_view_url`); a lane outside the render allow-set
  gets no dead link, and the GitHub ↗ links stay as fallback) — original
  capture: PR #177 lets the file route render markdown from every
  FLEET_LANES repo, but no page links there for lane repos: the capability
  is reachable only by hand-typed URLs. Add per-lane deep-links from the
  /fleet lane cards (e.g. the lane's `docs/current-state.md` and its
  `control/status.md` source) through the in-app renderer. Worth having
  because a shipped capability nothing navigates to is invisible to the
  owner. Deduped against this backlog + queue-state NEXT: the lanes.json
  and pickup ideas touch /fleet data, not file-view navigation. Source:
  `.sessions/2026-07-12-journal-guard-fleet.md` 💡.

- **Coverage-chip rollup on the /fleet board** · `built` (2026-07-12,
  PR #217 — `projects.coverage_rollup` reduces the seats' role coverage
  over the SAME TTL-cached registry data /projects renders, zero new
  network surface; /fleet header chip: green "coverage: complete (N
  seats)" / amber "packages incomplete: N" with the incomplete seats named
  inline + a /projects link / honest unknown when the registry or a seat's
  own listing is unreadable — never a fabricated zero; retired stubs
  excluded, same population as the /projects dispatch-ready summary;
  `/fleet.json` carries `coverage`, contract pinned same PR) — original
  capture: the
  per-seat instructions/coordinator/failsafe coverage now computed for the
  /projects index (`projects.role_coverage`, ORDER 015 slice) could feed
  one "packages incomplete: N" rollup cell on the `/fleet` monitoring
  surface, so registry lint fires where the manager already looks instead
  of only when the owner opens the dispatch index. Worth having because
  the chips double as registry lint but today only surface on `/projects`.
  Deduped against this backlog + the queue-state NEXT list: nothing rolls
  coverage up to the monitoring surfaces. Source:
  `.sessions/2026-07-12-projects-role-coverage-chips.md` 💡.

- **Seat role-coverage chips on the /projects dispatch index** · `built`
  (2026-07-12, ORDER 015 plans-sweep slice — `projects.role_coverage` chips
  each seat card instructions / coordinator / failsafe ✓/✗ from the
  already-fetched role-classified listing; `dispatch_ready` flag + "N of M
  dispatch-ready" index summary; unlistable package = NO chips, honest
  unknown; `/projects.json` carries `coverage` + `dispatch_ready`, contract
  pins updated same PR) — original capture:
  the dispatch screen (PR #158) renders whatever role files a package
  has, but the INDEX doesn't say which seats are dispatch-READY: a seat
  missing its coordinator prompt or failsafe looks identical to a complete
  one until the owner opens it mid-dispatch. One chip row per seat card
  (instructions ✓ / coordinator ✗ / failsafe ✓ — derived from the
  role-classified listing the page already fetches, zero extra API calls)
  turns "which seat can't launch yet" into a glance, and doubles as
  registry lint the fleet-manager lane can act on. Worth having because
  the single-screen dispatch flow's remaining blind spot is incomplete
  packages discovered at paste time. Deduped against this backlog + the
  queue-state NEXT list: nothing touches projects-registry completeness.
  Source: `.sessions/2026-07-12-projects-dispatch-view.md` 💡.

- **Ask superbot for a sanitized guild list in `dashboard.json`** ·
  `captured` — the /admin management flows (dry-run today, armed later) all
  start with "which server?", but NO committed feed carries a guild list, so
  the UI honestly falls back to a raw guild-id text input. One sanitized
  `guilds[]` family (id, name, maybe member_count — no tokens, no channels)
  in superbot's `export_dashboard_data.py` output turns every management
  form's weakest field into a real picker, and the armed panel inherits it
  for free. Routing half: a superbot-side export change — flag to the
  manager/superbot lane. Worth having because every management action is
  keyed by guild id and today's honest-but-hostile digit-pasting will be the
  #1 papercut the moment the panel goes live. Deduped against this backlog +
  the queue-state NEXT list: nothing touches guild data. Source:
  `.sessions/2026-07-11-dashboard-bot-management.md` 💡.

- **Bake-time questions sync from GitHub issues** · `built` (2026-07-13,
  PR #297, branch `claude/review-questions-bake-sync-0713` —
  `review/gen_questions.py`, stdlib-only fail-soft: one capped issues
  call, `[program-review]` title filter, PR objects excluded, merge keyed
  by url preserving hand-written `answer_url`/`answer_label` +
  `status_override` pins; wired into review-bake.yml) — the
  review site's `/questions` ledger is a hand-kept `questions.json` today;
  the `review-bake` workflow already has the Actions token, so a fourth
  generator could list this repo's issues titled `[program-review]` (one
  REST call) and merge them into the ledger automatically (asked date, url,
  open/closed status), leaving only the answer-links hand-written. Worth
  having because the interaction loop's slowest step is a session noticing
  a question exists — the bake noticing it daily makes the ledger honest by
  default. Deduped: nothing in this backlog touches questions intake.
  Source: `.sessions/2026-07-11-review-site-expansion.md` 💡.
- **⚑ owner-gated: live answer-bot on the review site** · `captured` —
  `/questionnaire` is agent-authored static answers by design; a real
  ask-anything endpoint (evidence-cited answers generated on demand) needs
  a model API key provisioned as a service variable — an owner decision
  with spend attached, deliberately not built. Flagged on the page itself.
  Source: `.sessions/2026-07-11-review-site-expansion.md` (directive ⚑).
- **Snapshot-aging banner on the review site** · `built` (2026-07-11,
  review-site expansion PR — `_base_ctx` compares the deployed sha
  (`RAILWAY_GIT_COMMIT_SHA`/`GIT_SHA`) against the snapshot's `git_head`
  and renders the site-wide "numbers baked at X — the repo has moved
  since" banner on mismatch; regen habit = the scheduled `review-bake`
  workflow, which re-bakes all three data mirrors daily) — original
  capture: the review service's numbers are baked into
  `review/data/snapshot.json` at commit time, so once deployed they
  silently fossilize as the repo moves on. Worth having because a review
  surface whose numbers silently age misleads exactly the outside audience
  it was built for. Source: `.sessions/2026-07-11-anthropic-review-site.md` 💡.

- **Flag to kit lane: `upgrade --apply-docs` rewrites `.substrate/upgrade-report.md`
  without the Carve-out scan section** · `retired` (fixed upstream in kit #176;
  verified live on this repo's v1.10.0 upgrade, PR #105 — `--apply-docs` rode
  the upgrade invocation and the carve-out section survived natively) —
  originally verified live on the v1.9.0 upgrade (this repo, PR #101): the
  main upgrade pass wrote the #156-mandated explicit carve-out section, then
  the post-hoc `--apply-docs` pass regenerated the report with only the docs
  table + an "Applied" section, silently dropping the carve-out audit record
  (hand-restored here). Source: `.sessions/2026-07-11-kit-upgrade-v1.9.0.md` 💡.

- **Flag to kit lane: model-doctrine idempotence phrase-match should be
  emphasis-insensitive** · `retired` (fixed upstream in kit #187, shipped in
  v1.10.1; verified live on this repo's v1.10.1 upgrade, PR #113 —
  `.sessions/README.md` byte-identical across the upgrade, no new append) —
  originally verified live on the v1.10.0 upgrade
  (this repo, PR #105): websites' `.sessions/README.md` already carried the
  hand-merged doctrine from #101, but with bold markers inside the sentence
  (`family-level model name **your own harness/environment reports this
  session**`), so `_merge_model_doctrine`'s exact-substring detection phrase
  missed it and appended a second, near-duplicate doctrine paragraph
  (harmless — append-only + provenance-marked — but noise on every adopter
  that hand-merged before the retroactive pass). The detector should
  normalize markdown emphasis (`*`/`_`) away before phrase matching. Source:
  `.sessions/2026-07-11-kit-upgrade-v1.10.0.md` 💡.

- **Apply the HANDOFF read-first line to the live `.claude/CLAUDE.md` via
  `upgrade --apply-docs`** · `built` (PR #146 — the v1.12.0 kit upgrade ran
  `upgrade --apply-docs`; the live working agreement now carries the
  three-surface boot set incl. the HANDOFF read-first line, diff-reviewed
  against the staged `.substrate/claude/CLAUDE.md` render) — the v1.11.0 upgrade report (PR
  #129) classes the live working agreement as "consumer-untouched + template
  improved — safe to apply with `upgrade --apply-docs`": one flag-run adopts
  the staged orientation change (read boot-generated `HANDOFF.md` before
  re-deriving history from `git log`) into the file agents actually boot
  from. The v1.11.0 HANDOFF composer only pays off once sessions are told to
  read it — the live orientation list still routes agents straight to
  `current-state.md`. Out of the distribution lane's scope (live CLAUDE.md is
  host-owned); a websites session should run it deliberately and diff-review.
  Source: `.sessions/2026-07-11-kit-upgrade-v1.11.0.md` 💡.

- **Hand-merge the v1.12.0 boot-set-trim deltas into the two diverged
  planted docs (CONSTITUTION.md, docs/AGENT_ORIENTATION.md)** · `captured` —
  the v1.12.0 upgrade (PR #146) could not auto-apply the trim to them (both
  the template and the docs moved); the exact diffs were preserved in
  `.substrate/upgrade-report.md` § Template deltas — the v1.12.1 upgrade
  (PR #155) overwrote that file, so retrieve them from git:
  `git show 31cfd9f:.substrate/upgrade-report.md`.
  AGENT_ORIENTATION still carries the duplicate start-list + duplicate
  verify block the new template deletes ("one list, one home");
  CONSTITUTION still enumerates the full PL register the new template
  condenses to a cite-the-register pointer. Apply by hand, diff-review, keep
  the host slot content. Source: `.sessions/2026-07-11-kit-upgrade-v1.12.0.md` 💡.

- **Pin the current-state kit line to `substrate.config.json` with a test**
  · `captured` — `docs/current-state.md`'s "vendored `bootstrap.py` is kit
  vX.Y.Z" line is hand-edited every upgrade and has drifted before (it said
  v1.6.0 until 2026-07-11 while the tree was five releases ahead). A small
  suite test that extracts that version token and asserts it equals
  `substrate.config.json` `kit_version` makes the ledger drift impossible —
  same exact-pin philosophy as `tests/test_born_red_session_gate.py`, aimed
  at the docs ledger instead of the config. Source:
  `.sessions/2026-07-11-kit-upgrade-v1.12.1.md` 💡.

- **Ask the manager for a generated `lanes.json`** · `captured` — /fleet
  now parses the LANES literal out of fleet-manager's gen_roster.py source
  (honest but coupled to a script's internals); one generated
  docs/lanes.json (repo, lane, disposition) from the same roster run makes
  the registry a real API and the next migration a non-event (the
  manifest→roster move broke this site once already, caught by the cron).
  Routing half: flagged to the manager in the heartbeat. Source:
  `.sessions/2026-07-11-lane-source-registry.md` 💡.
- **Backlog low-water signal in the heartbeat** · `captured` — when the
  captured+planned count drops below ~3, the heartbeat notes carry
  `backlog: low (N left)` so the manager routes work BEFORE a lane hits
  upkeep-dry (routing latency beats idle wakes); rung telemetry records
  which rung fired, not depth. Source:
  `.sessions/2026-07-11-fleet-chip-tooling-token.md` 💡.
- **`meta.md` state-line convention in the fleet-manager projects/ registry**
  · `captured` — ask the manager to standardize ONE `deployed:` line format
  in `projects/*/meta.md` (e.g. `deployed: <where> · <ISO date>`) while the
  registry is still forming; `/projects` extracts the state badge with
  tolerant heuristics against an unborn format, and one line agreed at
  zero-packages cost makes the badge exact forever (routing half: flagged to
  the manager in the heartbeat notes). Source:
  `.sessions/2026-07-10-order-009-projects.md` 💡.
- **Chain-entry refresh as a close-out ender** · `captured` — the
  consolidated current-state chain entry went twelve slices stale
  because extending it belongs to no slice; make it part of the
  CHAIN-END ritual (or every Nth slice's enders): one bullet-line per
  ~5 slices, test-truth line refreshed. Worth having because the
  living ledger is orientation doc #2 and its staleness was found by
  our own sweep twice today — recurring drift wants a recurring owner,
  not a rediscovery. Source:
  `.sessions/2026-07-11-chain-entry-refresh.md` 💡.
- **Dogfood the pickup convention in this lane's own heartbeat** ·
  `built` (the #150 catch-up heartbeat seeded `pickup: 011 19m` as writer
  #1; LIVE-VERIFIED end-to-end on deployed /orders — 011 pickup 19.0,
  summary.pickup count 1) — the consumer (#148) is honest-empty until SOMEONE
  writes `pickup:` tokens; this lane can be writer #1: when the next
  order's done= move happens, append `pickup: <id> <mins>m` to the
  heartbeat notes (ORDER 011's known 19m figure can seed it). Worth
  having because a convention with zero writers is a spec, not a
  protocol — and the first write live-verifies the whole parser path
  end-to-end. Source: `.sessions/2026-07-11-pickup-history-consumer.md` 💡.
- **Verdict-inheritance guard for carried heartbeat watches** ·
  `captured` — a watch claim copied across N heartbeat overwrites (the
  'never delivered' cron verdict rode five) should carry a
  last-verified timestamp (`watch: <claim> · verified <ISO>`) so
  readers see staleness and writers re-verify before copying; /fleet
  could badge watches whose verified-stamp lags the heartbeat. Worth
  having because inheritance is how this chain's one durable wrong
  claim propagated. Source: `.sessions/2026-07-11-chain-closeout.md` 💡.
- **Provenance-token list to the kit lane (gate half)** · `captured` —
  the /orders advisory and the future staged-gate provenance warning
  should share ONE token convention (cse_/session_/coordinator/
  manager/URL); flag to the kit lane that when it builds the gate half
  it should adopt (or supersede) the app/orders.py _PROVENANCE_TOKENS
  list rather than inventing a second heuristic — two half-matching
  spoof detectors are worse than one. Routing half: flagged in the
  heartbeat notes. Worth having because the advisory just created the
  convention de facto, and conventions fork silently. Source:
  `.sessions/2026-07-11-inbox-provenance-advisory.md` 💡.
- **Hand-kept-list audit sweep** · `retired` (executed 2026-07-11,
  continuous-mode slice 32, PR #142: CLASS CLEAR — every hit in tests/ +
  scripts/ is a single-file pointer or legitimate allowlist; the Railway
  guard enumerates git-tracked files; no third instance) — the nav guard's own
  hand-kept list is the SECOND self-referential drift this chain found
  (the first: the overflow guard's markup/tuple duplication #122); a
  one-off rung-5 sweep grepping tests/ and scripts/ for hard-coded
  module/file lists that shadow a globbable truth (e.g. any
  `= [REPO_ROOT /` or literal path-list patterns) would either clear
  the class or find the third instance. Worth having because this
  failure shape keeps recurring in guards specifically — the places
  drift hurts most. Source: `.sessions/2026-07-11-nav-scan-glob.md` 💡.
- **Port the clock-freeze pattern to botsite/dashboard if they grow
  age-measuring code** · `captured` — premise-checked: TODAY neither
  botsite/app.py nor dashboard/app.py measures ages against the wall
  clock (no datetime.now in either — verified by grep this slice), so
  there is nothing to port YET; this bullet exists so the first
  age-measuring feature in either service starts from app/clock.py's
  pattern instead of re-learning the 08:45Z lesson. Worth having
  because the failure class is service-agnostic and the fix is one
  small module. Source: `.sessions/2026-07-11-route-clock-freeze.md` 💡.
- **Persist pickup latencies before claims clear** · `captured` — the
  rollup can only see CURRENTLY-standing claims (done orders drop
  their claimed-by annotation per doctrine, taking the latency datum
  with them — live-verified on ORDER 011 post-#133); the honest fix is
  at the protocol layer, not scraping: ask the manager to consider a
  one-line convention where the executor's done= move appends the
  pickup figure to the heartbeat notes (e.g. `pickup: 011 19m`), which
  /orders could then parse into a durable per-lane history. Routing
  half: flag to the manager in the heartbeat. Worth having because the
  SLO's history vanishes exactly when an order completes — the moment
  it becomes most meaningful. Source:
  `.sessions/2026-07-11-pickup-latency-rollup.md` 💡.
- **Control-gate suite tests** — shipped 2026-07-11 (continuous-mode
  slice 26): tests/test_control_gates.py drives the real
  `check --strict --status-only [--inbox-base]` CLI against a synthetic
  fixture install, pinning FIVE lanes (clean 0 / broken heartbeat 1 /
  inbox rewrite 1 / pure append 0 / malformed append 1 — the grammar
  lane was found while prototyping). Source:
  `.sessions/2026-07-11-fastlane-control-gates.md` 💡.

- **Fast-lane control gates in quality.yml** — shipped 2026-07-11
  (continuous-mode slice 25): the control fast lane no longer
  short-circuits green unvalidated — a control-status gate runs ON the
  fast lane (stdlib-only --status-only; heartbeat PRs stay fast and
  card-free) and an inbox append-only + ORDER-grammar gate runs on BOTH
  lanes (--inbox-base vs merge-base; self-skips when the inbox is
  untouched). All four lane behaviors validated locally pre-push.
  Source: `.sessions/2026-07-11-quality-every-card-gate.md` 💡.

- **Nav manifest** — shipped 2026-07-11 (continuous-mode slice 24):
  `app/nav.py` is the single `(href, label, key)` source for the header
  nav; base.html iterates it via Jinja globals, the overflow tests
  import it, and `tests/test_nav_manifest.py` holds every route's
  `active` key to it (membership + uniqueness + no-dead-entries) — page
  12 physically cannot skip the overflow guard. Source:
  `.sessions/2026-07-11-nav-overflow-guard.md` 💡.

- **quality.yml every-card session gate** — shipped 2026-07-11
  (continuous-mode slice 23): the folded lane's `tail -1` single-card
  picker (multi-card shadowing loophole) replaced with the staged
  substrate-gate.yml every-card loop — added cards get the per-card
  born-red HOLD lane (siblings advisory), modified-only diffs get the
  locked door per card, no-card diffs use the explicit advisory
  sentinel, and PRs touching the gate file keep the full locked door +
  --simulate-added-card (semantics only tighten mid-PR); gate_regen
  path adapted to quality.yml; validated live on the port PR's own
  runs. Source: `.sessions/2026-07-11-kit-upgrade-v1.10.1.md` 💡.

- **Time-discipline guard for tests** — shipped 2026-07-11
  (continuous-mode slice 21): `tests/test_time_discipline.py` AST-scans
  the suite and fails any call to an age-measuring entry point
  (`fleet.overview`/`lane_status`/`freshness`/`heartbeat_freshness`,
  `orders.overview`/`classify_order`) without a frozen `now=`; first run
  caught 17 latent sites across 5 files, all threaded with frozen NOW
  constants; `heartbeat_freshness` + `orders.overview` gained the
  module-standard injectable `now=`. Source:
  `.sessions/2026-07-11-current-state-truth-sweep.md` 💡.

- **Nav overflow guard** — shipped 2026-07-11 (continuous-mode slice 19, the
  last buildable captured bullet): secondary pages (environments, projects,
  reviews, orders, ideas) grouped under a no-JS `<details>` "more ▾" nav
  dropdown — top-level links 11 → 6; every page stays reachable; a grouped
  page's active state opens the group and highlights the summary; pure
  HTML/CSS, no dependency. Source:
  `.sessions/2026-07-11-activity-repo-filter.md` 💡.

- **Board-row fleet chip (heartbeat freshness on the habit path)** — shipped
  2026-07-11 (continuous-mode slice 18): each board repo row shows its
  lane's heartbeat age/stale badge via `fleet.heartbeat_freshness` (only the
  board repos' status.md files over the TTL cache — deliberately not the
  18-lane overview fan-out); no readable/parseable heartbeat → no chip,
  never a guessed age. Source:
  `.sessions/2026-07-11-board-conveyor-chips.md` 💡.
- **`tooling:` capability token in fired heartbeats** — shipped 2026-07-11
  (slice 18): optional `tooling: pr-capable | ritual-only` status line
  (control/README.md + fleet.KNOWN_KEYS leak-guard + /fleet row flagging
  ritual-only as "cannot land work"); this repo's heartbeat writes it from
  this wake on. Source:
  `.sessions/2026-07-11-relay-doctrine-backlog-factcheck.md` 💡.

- **Conveyor-health chips on the readiness board rows** — shipped 2026-07-11
  (continuous-mode slice 17): each board row with a readable ideas dir shows
  lifecycle count chips (deep-linked to the /ideas ?state= filters), reusing
  the exact TTL-cached /ideas fetch path; a repo with no/unreadable ideas
  shows no chip (the board stays a readiness surface — /ideas holds the
  honest absence); /api/readiness.json untouched (pinned by test). Source:
  `.sessions/2026-07-11-ideas-states-waitdeploy.md` 💡.

- **Relay-PR merge protocol on the bus** — shipped 2026-07-11 (continuous-mode
  slice 15): doctrine section "Landing other sessions' control-only work" in
  `control/README.md` — any session may land a green control-only relay or
  stranded heartbeat verbatim (one WRITER, not one MERGER); generalized from
  two same-night incidents (relay PR #94; 04:03Z heartbeat rescued as PR #98).
  Source: `.sessions/2026-07-11-order-010-and-tooling.md` 💡.
- **Backlog fact-check pass before promoting a bullet** — shipped 2026-07-11
  (slice 15): the habit line lives in `docs/ideas/README.md` § Lifecycle
  ("fact-check before promoting"), and the first full pass was executed the
  same slice (verdicts: unseen-orders badge retired as superseded; nav guard
  + board chips + meta.md convention confirmed still-live). Source:
  `.sessions/2026-07-10-own-heartbeat-selfcheck.md` 💡.

- **Cron-slot helper** — shipped 2026-07-11 (continuous-mode slice 14) as
  `scripts/cron_slots.py`: 5-field cron → next wall-clock UTC fire slots
  (loud on malformed, never a guess); the incident case (`17 */6 * * *`
  after 21:03Z → 00:17Z, not "+6h") is a pinned test. Source:
  `.sessions/2026-07-11-open-work-rung-cronfinding.md` 💡.
- **Review-queue row auto-check** — shipped 2026-07-11 (slice 14) as
  `scripts/review_row_check.py`: sums runtime/product changed lines over a
  git range with the ledger's exact exclusions (docs/, control/,
  .sessions/, tests, markdown; binary counts 0) and prints ROW OWED past
  the binding 50-line threshold; first live run confirmed #81's squash owes
  a row. Row-appending stays a fleet-manager write — flag to the manager.
  Source: `.sessions/2026-07-10-order-009-reviews.md` 💡.

- **`/ideas` state filter (conveyor health)** — shipped 2026-07-11
  (continuous-mode slice 13): each idea's front-matter `state:` surfaces as
  a badge, per-repo captured/planned/built/retired/unstated counts (honest
  scope: the newest enriched files), and a `?state=` filter that narrows the
  list but never the counts; unknown states flag, never guess. Source:
  `.sessions/2026-07-11-json-contracts-pr9-retire.md` 💡.
- **`scripts/wait-deploy.py` post-merge sha-convergence poller** — shipped
  2026-07-11 (slice 13) as `scripts/wait_deploy.py`: poll all three
  `/version` endpoints until sha == a given commit or timeout — one
  deterministic PASS/FAIL instead of hand-curling (first live run:
  CONVERGED in one poll at 7f948445). Source:
  `.sessions/2026-07-10-gen2-walking-skeleton.md` 💡.

- **Open-PR awareness at wake** — shipped 2026-07-11 (continuous-mode slice
  12): `scripts/open_work.py` classifies every remote `claude/*`/`manager/*`
  branch as PR-OPEN (leave to its session) / PR-LESS (rescue candidate) /
  MERGED-STALE (prune candidate) / PR-UNKNOWN (api wall — labeled, never
  guessed); run at session start before picking a rung. First live run
  surfaced exactly the four gen-1 leftover branches. File:
  [open-pr-awareness-at-wake-2026-07-10.md](open-pr-awareness-at-wake-2026-07-10.md).
- **Ladder-rung telemetry in the heartbeat** — shipped 2026-07-11 (slice 12):
  optional `rung:` status line (documented in `control/README.md`, in
  `fleet.KNOWN_KEYS` so it can never leak into the previous field — the
  routine:-line incident class — and rendered as a /fleet row when present);
  this repo's heartbeat writes it from this wake on. Source:
  `.sessions/2026-07-10-never-idle-work-ladder.md` 💡.

- **Same-shape contract tests for /orders.json, /queue.json, /projects.json,
  /reviews.json** — shipped 2026-07-11 (continuous-mode slice 11):
  `tests/test_json_contracts.py` pins every payload's key sets (cards/orders,
  items/sources/fleet_manager, packages/files, rows/links) with named-key
  drift messages and rendered-HTML-absence asserts; companion to the
  /fleet.json pin. Update the pinned sets in the same PR that changes a
  payload. Source: `.sessions/2026-07-10-fleet-json-contract.md` 💡.

- **Per-repo `?repo=` filter on the activity views** — shipped 2026-07-11
  (continuous-mode slice 10; decision stamped in `docs/site.md` § 2 + the
  decision ledger): /activity, /activity.json, /activity.xml narrow to one
  fleet repo (filtered case fetches only that repo; the Atom feed becomes a
  per-lane subscription with the repo in its title; unknown repo = honest
  empty state). File:
  [activity-per-repo-filter-2026-07-09.md](activity-per-repo-filter-2026-07-09.md).

- **`/fleet.json` shape-contract test** — shipped 2026-07-10 (continuous-mode
  slice 9): `tests/test_fleet_json_contract.py` pins the exact key sets of
  the /fleet.json payload (top level, summary incl. kit_versions, every lane
  incl. orders_info/routine_info/landing_info, and the degraded-lane
  same-shape guarantee) — any key add/remove/rename goes red BY NAME; update
  the pinned sets in the same PR that changes the payload. Source:
  `.sessions/2026-07-10-fleet-polish-batch.md` 💡.

- **Fleet polish batch: stalled-claim aging on `/orders` + `/queue.json` +
  kit-version rollup on `/fleet`** — shipped 2026-07-10 (continuous-mode
  slice 8; decision stamped in the decision ledger; details in
  `docs/site.md` §§ 3a/3f/Routes). Three captures closed in one batch, zero
  new fetches: `parse_orders` extracts `claimed_at` and claimed orders badge
  `claim stale?` past 24h (the ritual's expiry rule); `/queue.json` gives
  the manager the file-an-ask → poll → confirm round-trip; `/fleet` header
  shows "kit adoption: N×vX.Y.Z · M×none" over readable heartbeats.

- **Own-heartbeat parse self-check in `quality`** — shipped 2026-07-10
  (continuous-mode slice 7): `tests/test_own_heartbeat.py` runs the REAL
  committed `control/status.md` through the `/fleet` parsers every suite run
  — required fields present, `updated:` parses, `health:` classifies,
  `orders:` machine-readable, optional `routine:`/`landing:` lines classify,
  and no enriched key leaks into `blockers:` as a continuation (the
  pre-enrichment failure class). Honest scope: heartbeat-only PRs ride the
  control fast lane and skip pytest, so a bad heartbeat reds the NEXT
  non-control PR — a standing floor, not same-PR enforcement. Source:
  `.sessions/2026-07-10-heartbeat-enrichment.md` 💡.

- **Per-repo inbox ORDER visibility on the site** — shipped 2026-07-10
  (continuous-mode slice 6; decision stamped in `docs/site.md` § 3f + the
  decision ledger): `/orders` (+ `.json`) parses every fleet repo's
  `control/inbox.md` ORDER blocks and cross-references each id against the
  repo's own heartbeat `done=`/`claimed-by:` lines (one parser — the
  heartbeat enrichment's `parse_orders`) into done / claimed / open /
  unknown badges, attention-sorted with fleet-wide roll-ups. Source at
  capture: `control/inbox.md` ORDER 009 audit.
- **ORDER 009 increment (3): review-queue rows + findings links** — shipped
  2026-07-10 (continuous-mode slice 5; decision stamped in `docs/site.md`
  § 3e + the decision ledger): `/reviews` (+ `.json`) renders the
  fleet-manager post-merge review-queue ledger — open rows as cards with
  `repo#N` deep-linked, struck rows classified reviewed, findings/records
  links extracted from the doc itself (never hardcoded), full ledger
  rendered below; empty/not-configured/unavailable degradation. Increment
  (1) `/projects` shipped earlier the same day; increment (2) verified
  already-covered on `/fleet`. Source: `control/inbox.md` ORDER 009.

- **Scheduled healthcheck workflow (standing liveness verification)** —
  shipped 2026-07-10 (backlog promotion, 20:00Z continuous-mode wake slice 3;
  retro F3): `.github/workflows/healthcheck.yml`, cron every 6 h (minute-17
  offset) + `workflow_dispatch`, runs `scripts/healthcheck.py` (three live
  services `/healthz` + `/` 200, plus the `/fleet` manifest live-parse smoke
  check); read-only, no secret, NOT a required check — failure notifies via
  the failed-workflow email. File:
  [scheduled-healthcheck-workflow-2026-07-10.md](scheduled-healthcheck-workflow-2026-07-10.md).
- **Heartbeat enrichment: machine-readable fields in `control/status.md`** —
  shipped 2026-07-10 (decision stamped in `docs/site.md` § 3a + the decision
  ledger; queue-state NEXT item 4, retro G3): `/fleet`
  parses `orders:` (outstanding = acked minus done, ranges expanded,
  `claimed-by:` captured) + the new OPTIONAL `routine:` / `landing:` /
  `deployed:` lines (documented in `control/README.md`); armed-but-silently-dead
  routines and stranded (`LOCAL-ONLY` / pushed-unmerged) landings badge and
  sort attention-first; `/fleet.json` carries the parsed structures. Folded in
  both sibling captures (`routine:` — `.sessions/2026-07-10-gen2-closeout-docs.md`
  💡; `landing:` — `.sessions/2026-07-10-rescue-landing-project-package.md` 💡).
- **`.sessions/` card template with `📊 Model:` line + ender checklist** —
  shipped 2026-07-10 (queue-state NEXT item 3): copy-paste template + ender
  checklist embedded in `.sessions/README.md` (embedded there on purpose — the
  session gate treats any other `.sessions/*.md` as a card, so a standalone
  TEMPLATE.md would itself go born-red). The 💡 section carries the required
  one-line "worth having because" prompt. Sources at capture:
  `docs/planning/queue-state-2026-07-09-winddown.md` NEXT item 3;
  `.sessions/2026-07-10-gen2-walking-skeleton.md` ⟲ review.
- **`/activity.xml` Atom feed** — shipped; see the decision ledger +
  `docs/site.md`. File:
  [activity-atom-feed-2026-07-09.md](activity-atom-feed-2026-07-09.md).
- **Merge holds announced in a file at HEAD** · `captured` — repo-wide
  merge holds coordinated by session messages failed twice on 2026-07-11
  (#143/#146 merged mid-hold by wakes that never saw the hold); announce
  holds as a `control/claims/HOLD-<scope>.md` file at origin/main HEAD so
  every session's mandatory pull sees them mechanically, and lift = delete
  the file. Routing half: flag to the kit/manager layer for one fleet-wide
  shape. Worth having because a file at HEAD reaches every future session
  by construction — session messages only reach sessions alive at send
  time. Deduped: nothing in this backlog covers hold coordination. File:
  [merge-hold-at-head-2026-07-11.md](merge-hold-at-head-2026-07-11.md).
  Source: `docs/retro/archive-ready-2026-07-11.md` §3 💡.

## Retired

- **"Unseen orders?" badge on `/fleet`** — retired 2026-07-11 (slice 15
  fact-check pass): superseded by `/orders` (decision home `docs/site.md`
  § 3f) — the badge would have flagged "inbox commit newer than status
  updated:" as a heuristic; /orders now computes the actual outstanding
  orders per repo (done/claimed/open/unknown badges + fleet-wide roll-up),
  strictly stronger than the commit-time proxy. Nothing left to build.

- **Re-check closed-unmerged PR #9 branch `claude/rework-dashboard` for lost
  hardening work** — retired 2026-07-11 (slice 11 investigation, nothing to
  salvage): the branch shares NO merge base with main (parallel-checkout
  root); its only unique hardening commit `a0b459f` ("drop literal
  control-API env-var name from served HTML; extend denylist test to
  templates") is fully superseded on main by PR #10 — verified by diff:
  main's `dashboard/tests/test_dashboard.py::test_no_control_api_token_or_url_anywhere`
  scans `*.py` AND `*.html` with the same denylist, and a repo-wide grep
  finds ZERO forbidden literals in shipped dashboard files. The branch's
  other commits are the superseded parallel dashboard build PR #8 replaced.
  Branch stays on the remote (branch deletion is a documented 403 wall,
  `docs/CAPABILITIES.md`) — safe to prune whenever someone with delete
  rights sweeps; nothing on it is needed.

- **`/fleet` badge: "manifest live parse: last verified \<age\>"** — retired
  2026-07-10 (slice 7 fact-check): already shipped — `fleet.html` has
  rendered `lane_source` on the page since the PR #36 manifest work ("lane
  set: live from manifest — N lanes parsed" vs the fallback banner), which is
  exactly the surfacing this capture asked for; verified in the template +
  covered by `test_fleet_overview_is_manifest_sourced`. Nothing to build.

- **Harvest the AI-assistant question log into the /questions ledger** —
  captured 2026-07-12 (ORDER 017 B session). `review/ai.py` logs every
  visitor question as a structured JSON line on stdout (mode, truncated
  text, outcome, salted IP hash); a harvest step (manual or baked) could
  promote real reviewer questions into `review/data/questions.json` so the
  ledger fills from real traffic instead of starting empty. Worth having
  because the order itself says the question log "feeds the Q&A page" —
  this closes that loop.

- **Site-wide privacy lint for the review service** · `built` (2026-07-13,
  PR #233 — `review/tests/test_privacy_lint.py` (5 tests, zero network)
  walks EVERY GET route in `review/app.py` via TestClient — parameterized
  routes expanded to every concrete variant from the committed data (all
  fleet repos incl. the private lane's 404 probe, all edition slugs, all
  static assets, the catch-all 404) — plus every committed
  `review/data/**` file as raw text, asserting no private-lane token;
  matching is accent-aware per this bullet's `pok[eé]mon…` spec
  (NFKD-strip combining marks + casefold on both haystack and tokens),
  token list = the stem + `fleetdata.PRIVATE_LANES` so a new private lane
  is linted automatically; explicit per-entry-justified allowlist
  (currently empty) with stale-entry rejection, and a completeness guard
  failing any future parameterized route/mount without a registered
  expansion; proven red on planted accented leaks in both directions, no
  real leak found on main) — original capture 2026-07-12 (ORDER 017 D
  private-lane-filter session): today's escapees were the accented
  "Pokémon" in a template footnote and an evidence table that plain
  `grep -i pokemon` missed. Worth having because privacy compliance
  shouldn't depend on remembering which surface to grep.

- **Arcade live-URL drift probe** · `built` (2026-07-12, PR #214 —
  `botsite/arcade_probe.py` cold-fetches every `availability: live` URL via
  a new `check_arcade_urls` pass in `scripts/healthcheck.py` (the 6-hourly
  healthcheck.yml schedule); flags non-200 / timeout / connection error /
  malformed or missing URL, prints explicit "not probed" lines for non-live
  entries, fail-soft per URL, folds into the script's exit-1-on-failure
  idiom; the required `quality` gate stays network-free — probe logic is
  unit-tested against `httpx.MockTransport`) — original capture 2026-07-12
  (ORDER 022 drift session): a network-marked test or CI cron step that
  cold-fetches every `availability: live` URL in `botsite/data/arcade.json`
  and flags when one stops returning 200, so a dead game link never quietly
  outlives its card. Worth having because the arcade honesty doctrine
  currently depends on manual reconciles (ORDER 022 flipped mineverse by
  hand) to notice drift.

- **Probe download-availability arcade URLs too** · `built` (2026-07-12,
  PR #220 — `botsite/arcade_probe.py` `PROBED_AVAILABILITIES = ("live",
  "download")` drives the filter; `probe_live_urls` renamed
  `probe_registry_urls`, rows carry `availability`, healthcheck label/output
  updated; final-200 semantics unchanged — redirect chains ending in 200
  count healthy via the existing `follow_redirects=True`, a FINAL redirect
  status stays flagged, a redirect loop degrades to a flagged
  `TooManyRedirects` finding; new MockTransport coverage for download
  200 / 302→200 / 404 / timeout / redirect loop / no-URL / mixed registry)
  — original capture: the /arcade page renders an outbound link for
  `availability: download` entries with a URL (`has_link` covers live AND
  download), but the healthcheck drift probe (PR #214) only cold-fetched
  `live` entries — the moment Lumen Drift's GitHub Release lands and its
  card flips to `download`, its link re-enters the unverified-drift class
  this probe was built to close. Worth having because the first `download`
  flip is already queued (lumen-drift's release is one owner click away)
  and it would silently re-open the exact hole just closed. Source:
  `.sessions/2026-07-12-arcade-url-drift-probe.md` 💡.

- **Single source of truth for link-bearing arcade availabilities** ·
  `built` (2026-07-13, branch `claude/arcade-link-truth-0713` —
  `botsite/arcade.py` now owns `LINKED_AVAILABILITIES = ("live", "download")`
  as the ONE constant; `has_link` consumes it and
  `arcade_probe.PROBED_AVAILABILITIES` is defined AS it (identity, not a
  duplicate literal); pin tests assert the probe's coverage tuple IS the
  page's link-bearing tuple, that the constant is a valid non-`unavailable`
  subset of `AVAILABILITIES`, and that both `has_link` and the probe's
  probed/skipped partition track the constant for every registry
  availability) — original capture 2026-07-12 (arcade download-probe session
  💡): two copies of the doctrine "which availabilities carry outbound links"
  that nothing pins together. Worth having because the probe's whole
  guarantee is "coverage never disagrees with the page" — that agreement was
  by coincidence of two literals, and the next new availability value (a
  "beta" that gets links, say) would silently under-cover exactly like the
  `download` gap just closed. Source:
  `.sessions/2026-07-12-arcade-download-probe.md` 💡.

- **review-bake self-janitor for stale bake branches** — captured 2026-07-12
  (docs truth sweep session). The review-bake workflow's token can now
  create branches and PRs (proven by run 29202721928 → PR #194 auto-merged);
  a final workflow step deleting its own merged/superseded
  `bake/review-data-*` branches (plus the two 2026-07-11/12 orphans) would
  remove the owner errand entirely. Worth having because branch deletion is
  403-walled for agent sessions (`docs/CAPABILITIES.md`) — the workflow is
  the one actor that can keep its own house clean.

- **Pin open tester-task `product_url` hosts to the healthcheck `SERVICES`
  table** · `captured` (2026-07-12, tester-task URL guard session 💡) — the
  repo now hand-keeps the fleet's public hosts in TWO committed places:
  `scripts/healthcheck.py` `SERVICES` and the `product_url`s of the open
  tasks in `botsite/testing_tasks.json` (today all four open-task URLs sit
  on the three SERVICES hosts). A service rename that updates one file but
  not the other leaves testers pointed at a dead host for up to 6 hours
  until the cron probe fires; one zero-network suite test asserting every
  open task's `product_url` host is a `SERVICES` host (or on a
  declared-exceptions list, for the day a task points at a non-fleet
  product) would catch that drift in CI at PR time. Worth having because
  the liveness guard just shipped is a RUNTIME net — this pin is the
  cheaper compile-time net for the most likely way those URLs die, the
  same committed-inventory-consistency move already captured for
  `railway.SERVICES` vs the envhub registry (that bullet covers env-var
  NAMES, not hosts — deduped against it, this backlog, and the queue-state
  NEXT list). Source: `.sessions/2026-07-12-tester-task-url-guard.md` 💡.

- **Environments rollup in the authed /owner readiness JSON** · `built`
  (2026-07-13, PR #246 — `/owner/api/readiness.json` becomes
  `{"rows": [...], "environments": <envhub.board_rollup dict>}`; same
  TTL-cached `railway.live_overview` read, honest `unknown` passthrough
  intact, gate/GET-only unchanged; contract pinned in
  `tests/test_owner_readiness_json_contract.py` — top-level keys,
  environments key set, states enum `{ok, unknown}`, never-values)
  — the board chip's rollup
  (`envhub.board_rollup`, PR #223) renders on the `/owner` HTML only;
  `/owner/api/readiness.json` (the authed machine view of the same board)
  does not carry it, so a script or agent wanting the "N groups
  incomplete" signal must scrape HTML. Attach the same rollup dict to that
  JSON — the exact #217 precedent, where `/fleet.json` carries the
  coverage rollup with its key set pinned in
  `tests/test_fleet_json_contract.py`. Worth having because the board chip
  only helps while the owner is looking; the JSON makes the same honesty
  ladder consumable by the machinery (scheduled healthcheck, fleet-manager
  sessions) that watches when he is not. Deduped against this backlog +
  the queue-state NEXT list: nothing touches the owner JSON contract or a
  machine-readable environments rollup. Source:
  `.sessions/2026-07-12-owner-readiness-env-chip.md` 💡.

- **Align `.sessions/README.md`'s model-line examples with the family-level
  rule** · `built` (2026-07-13, PR #226 — template + ender-checklist examples
  now "Claude Fable 5" / "Claude Opus 4.8", plus a 102-card historical sweep
  normalizing exact-ID model-line tokens to family-level names; original
  capture 2026-07-12, card-model-line-fix session 💡) — the
  README's template and ender checklist say "FAMILY level only" but give
  `claude-fable-5` / `claude-opus-4-8` as the examples, i.e. the exact-ID
  shape; agents copy templates literally, so the doc that defines the rule
  keeps seeding its violation into new cards (the #223 card was one).
  Update the two example strings to "Fable 5" / "Opus 4.8" phrasing. Worth
  having because it stops the exact-ID form at its source instead of fixing
  cards one at a time. Deduped against this backlog + the queue-state NEXT
  list: nothing touches the session-card template or model-attribution
  examples. Source: `.sessions/2026-07-12-card-model-line-fix.md` 💡.

- **Kit-gate advisory for exact-ID model lines** · `captured` (2026-07-13,
  model-line-hygiene session 💡) — extend the session-card scan in
  `bootstrap.py check` (the `session_markers` machinery) with an advisory
  that flags any `📊 Model:` line matching the lowercase exact-ID token
  shape, so regressions are caught at the gate instead of by manual sweeps
  like PR #226. Worth having because a one-time sweep decays — without a
  checker the old shape creeps back via copy-paste from pre-sweep cards in
  other fleet repos. Kit-owned surface, so the build routes via the kit
  lane, not this repo. Deduped against this backlog + the queue-state NEXT
  list: the README-example fix above is now `built` and nothing else adds a
  gate/checker for model-line shape. Source:
  `.sessions/2026-07-13-model-line-hygiene.md` 💡.

- **Structural clarity-bar gate** · `built` (2026-07-13, PR #241 — landed
  across ALL FOUR services, not just the control-plane: one route-walking
  `test_clarity_structure.py` per service in tests/, botsite/tests/,
  dashboard/tests/, review/tests/, each asserting its own header idiom (h2 +
  `p.dim.small` for app/, sb-page-hero h1 + `p.sb-lead` / detail `p.tagline`
  for the sb services), with PARAM_EXPANDERS + two-way completeness guards
  and explicit documented non-page classifications, shaped like the PR #233
  privacy lint) — a test that walks every registered
  page route on the control-plane app and asserts the header idiom (h2 with
  em-dash purpose + `p.dim.small` lede), so a new page can never ship below
  the clarity bar. Worth having because it turns the one-off manual 24-page
  audit (PR #229) into a permanent structural gate — the ledes pinned in
  `tests/test_clarity_ledes.py` protect existing pages only; a
  route-walking assert protects pages that don't exist yet. Deduped against
  this backlog + the queue-state NEXT list: nothing touches the clarity bar
  or a header-idiom gate. Source:
  `.sessions/2026-07-13-clarity-control-plane.md` 💡.

- **Code-consumed env names vs the committed inventories (the third
  inventory is the code itself)** · `built` (2026-07-13, PR #227 — both
  inventories now document every genuinely code-consumed name: botsite
  gains its 12 undocumented names (`TESTING_AI_MODEL` /
  `TESTING_AI_DAILY_CAP` / `TESTING_AI_GUIDE_CAP`, `SITE_PASSWORD`,
  `TESTING_DB_PATH`, `TESTING_BOUNTY_CAP_USD`, the four
  `TESTING_AUTOPAY_*`/`TESTING_PAYOUT_*` knobs, the `PAYPAL_*` credential
  pair — names only), control-plane gains 5 (`ANTHROPIC_API_KEY`,
  `OWNER_ASSIST_*`, `WRITEBACK_*`); the #225 pin grows a third leg in
  `tests/test_inventory_consistency.py`: `botsite/testing_ai.py`'s consumed
  names, read from its own `ENV_*` constants, must be ⊆ BOTH documented
  sets, with an explicit justified allowlist + stale-entry check, plus a
  completeness guard that every environ read in that file goes through an
  `ENV_*` constant; backfilled here as a capture-miss repair — the #225
  session's card carried this 💡 but never landed the bullet) — original
  capture: `botsite/testing_ai.py` reads `TESTING_AI_MODEL`,
  `TESTING_AI_DAILY_CAP`, and `TESTING_AI_GUIDE_CAP` (all optional,
  defaulted in code), but neither `railway.SERVICES` nor the envhub
  registry lists them for botsite — review's equivalents ARE documented, so
  the omission is inconsistent, not a policy. Either document the three
  names in both inventories, or grow the consistency pin a third leg:
  assert every code-consumed name is documented (or explicitly allowlisted
  as internal). Worth having because the #225 pin only proves the two
  ledgers agree with each other — they can still agree on an incomplete
  picture, and the incompleteness found that day was found by accident.
  Source: `.sessions/2026-07-13-inventory-consistency-pin.md` 💡.

- **Generalize the code-vs-inventory leg to every service module** ·
  `captured` (2026-07-13, testing-ai-inventory session 💡) — the PR #227
  pin covers ONE file (`botsite/testing_ai.py`, the module with importable
  `ENV_*` constants throughout); the other 14 undocumented names that
  session fixed were found by hand-grepping `os.environ` across
  `botsite/testing*.py`, `app/owner_assist.py` and `app/writeback.py`. A
  per-service scan (module `ENV_*` constants where they exist + a
  literal-string regex over each service package) asserting every
  code-consumed name is documented in both inventories or explicitly
  allowlisted (platform-injected `GIT_SHA`/`RAILWAY_GIT_COMMIT_SHA`,
  gen-script build-time reads) would make the next
  `testing_payouts.py`-style knob impossible to ship undocumented. Worth
  having because that session's completeness was restored by a one-off
  manual grep — the shipped pin only holds for the one module it watches.
  Deduped against this backlog + the queue-state NEXT list: the bullet
  above (built) covers `testing_ai.py` only; nothing covers a repo-wide
  code-consumption scan. Source:
  `.sessions/2026-07-13-testing-ai-inventory.md` 💡.

- **Storefront freshness pin — nag when `products.json` goes stale** ·
  `captured` (2026-07-13, venture-products-page session 💡) — each entry in
  `botsite/data/products.json` carries an `as_of` date; a CI-time check (or
  small on-page note) comparing those dates against a staleness horizon
  (~14 days) would nag when the curated storefront has not been re-verified
  against venture-lab. Worth having because a hand-curated registry drifts
  silently the moment a product goes live or changes price — the honesty
  doctrine dies through staleness, not lies. Deduped against this backlog +
  the queue-state NEXT list: nearest neighbors are the tester-task
  `product_url` liveness pins; nothing covers registry as-of staleness.
  Source: `.sessions/2026-07-13-venture-products-page.md` 💡.

- **Privacy-boundary decision + lint for the OTHER three services** ·
  `captured` (2026-07-13, review-privacy-lint session 💡) — the new
  review-side privacy lint (PR #233) covers `review/` only, but the
  private lane's name appears verbatim in `app/config.py` (LANES entry)
  and `app/reviews.py`, and the control-plane serves without auth — so
  either the ORDER 017 D privacy contract is deliberately review-scoped
  (the control plane is the owner's own console; document that boundary
  where the next privacy session will look) or the same accent-aware
  walker pattern (every GET route via TestClient + committed data files,
  allowlist with stale rejection) should be stamped onto app/, botsite/
  and dashboard/. Decide first, lint second — the lint shape is now
  proven and cheap to port. Worth having because the one leak class we
  actually shipped (2026-07-12) escaped precisely on the surfaces nobody
  had decided about. Deduped against this backlog + the queue-state NEXT
  list: the built review-privacy-lint bullet covers review/ only; the
  dashboard denylist test covers control-API tokens, not the private
  lane; nothing covers a cross-service privacy boundary. Source:
  `.sessions/2026-07-13-review-privacy-lint.md` 💡.

- **Reason-bound conformance test over ALL error-minting modules** ·
  `captured` (2026-07-13, railway-reason-bound session 💡) — one
  parametrized test covering every module that mints user-visible failure
  reasons (`app/github.py`, `app/railway.py`, `app/freshness.py`, and any
  future client), asserting each routes through `short_reason` — e.g. a
  shared fixture that feeds each mint path an HTML/huge/multiline body and
  asserts the bounded contract, plus a scan for bare `[:N]` caps on error
  strings — so the next new client cannot reintroduce an unbounded reason.
  Worth having because the same bug has now been fixed three times (#237
  page-side, #240 github-source, #244 railway-source) — the pattern wants
  a gate, not a fourth session. Deduped against this backlog + the
  queue-state NEXT list: #240's envelope-level fix bullet covers the
  github source only; nothing adds a cross-module conformance gate.
  Source: `.sessions/2026-07-13-railway-reason-bound.md` 💡.

- **Surface the environments rollup in `scripts/healthcheck.py`** ·
  `captured` (2026-07-13, readiness-env-rollup session 💡) — the
  environments rollup now ships machine-readably on the authed
  `/owner/api/readiness.json` (PR #246), and that bullet's own "why" names
  the scheduled healthcheck as the machinery that should watch it when the
  owner is not looking — but the cron probe today checks service liveness
  only. One authed read of the JSON (the site password already lives in
  the service env) could report `environments.state` +
  `incomplete_names` alongside the liveness rows, with the same honest
  `unknown` passthrough. Worth having because the rollup now exists for
  machines yet nothing scheduled actually reads it — the honesty ladder
  still only helps while someone is looking. Deduped against this backlog
  + the queue-state NEXT list: the env-drift and inventory-consistency
  bullets pin COMMITTED inventories against each other; nothing consumes
  the LIVE rollup from the cron probe. Source:
  `.sessions/2026-07-13-readiness-env-rollup.md` 💡.

- **Catalog sha-drift pin — nag when the vetting catalog's pinned source
  sha falls behind venture-lab HEAD** · `captured` (2026-07-13,
  venture-vetting-catalog session 💡) — every entry in
  `botsite/data/catalog.json` (PR #248) pins its provenance to venture-lab
  @ `2c039e3`; a scheduled or CI-time check comparing that pinned sha
  against venture-lab's current HEAD for `docs/publishing/vetting/` +
  `OWNER-QUEUE.md` (one raw-content read of the default-branch sha, the
  read-only forward-only channel the fleet already uses) would nag when
  packets changed upstream while the committed catalog still claims them.
  Worth having because a 22-entry hand-curated registry decays the moment
  the vetting lane moves — a title going live upstream while the catalog
  still says publish-ready is exactly the dishonesty the page exists to
  avoid. Deduped against this backlog + the queue-state NEXT list: the
  storefront-freshness bullet above is TIME-based (`as_of` horizon,
  products.json only); nothing compares pinned source shas against the
  upstream repo, and nothing covers catalog.json. Source:
  `.sessions/2026-07-13-venture-vetting-catalog.md` 💡.

- **Cited-fact drift pin for /agent-pr-check — nag when the tree's quoted
  sources move on main** · `captured` (2026-07-13, agent-pr-diagnostic
  session 💡) — every leaf in `botsite/data/agent_pr_tree.json` quotes
  facts pinned at `@2a4c78a` (enabler guard wording, the quality.yml
  fast-lane rationale, the review-bake landing ladder, CAPABILITIES wall
  entries). A CI-time check that extracts each `file@sha` citation,
  verifies the path still exists, and diffs the cited file between the
  pinned sha and HEAD (pure `git diff --name-only <sha>..HEAD -- <path>`,
  no network) would nag when a cited source changed while the tree still
  quotes its old text. Worth having because that page's whole value is
  "every verdict cited" — a guard rewritten upstream while the tree still
  quotes the old wording is exactly the rot the citations exist to
  prevent. Deduped against this backlog: the catalog sha-drift pin above
  compares a pin against a REMOTE repo's HEAD over the raw channel, and
  the storefront-freshness bullet is time-based; nothing checks this
  repo's own file@sha citations against local HEAD, and nothing covers
  agent_pr_tree.json. Source:
  `.sessions/2026-07-13-agent-pr-diagnostic.md` 💡.

- **Embed the manager outbox tally in /owner/briefing — one URL for the
  owner read AND the manager roll-up** · `built` (2026-07-13, briefing
  REPORTS-section PR, branch `claude/briefing-outbox-0713` —
  `briefing.outbox_report` + `latest_report` render the newest
  `control/outbox.md` REPORT entry in a sixth briefing card over the same
  `github.fetch_file` path ASKS rides; unreadable file → honest
  `unknown — <reason>`, no REPORT entries → explicit honest-empty,
  malformed REPORT-like headings skipped and counted, body bounded to 40
  lines with the cap noted; captured 2026-07-13,
  coordinator-sitting ender 💡) — give `/owner/briefing` (PR #273) a
  "reports to the manager" section rendering the newest `control/outbox.md`
  REPORT entry over the same committed-file read path the fleet pages
  already use (`app/briefing.py` sections today: shipped / orders / asks /
  fleet-attention / watches — no outbox section). Worth having because the
  owner's morning read and the manager's roll-up currently live at two
  URLs; one briefing URL carrying both means an ORDER 023-style "post your
  night report" ask is satisfied by a page the owner already opens.
  Deduped against this backlog (no briefing/outbox bullet) and against
  `app/briefing.py` at HEAD. Source:
  `.sessions/2026-07-13-coordinator-sitting.md` 💡.

- **Structural no-bare-numeric-env-parse gate — make the int("") class
  unshippable, not just fixed** — shipped 2026-07-13 (PR #285):
  `tests/test_env_guard_gate.py` AST-scans app/, botsite/, dashboard/,
  review/ (excluding bootstrap.py/.substrate, tests dirs, and the
  review/gen_*.py offline bakers) and fails on any IMPORT-TIME bare
  `int(`/`float(` over `os.environ`/`os.getenv` — module scope, top-level
  if/try blocks, class bodies, and function defaults all count; function
  bodies are exempt, which is exactly what lets `_env_int`-guarded sites
  (PR #282) pass. Self-tests seed a violation fixture and prove the
  scanner catches it without touching real service modules. Source:
  `.sessions/2026-07-13-env-hardening.md` 💡.

- **Self-deriving poison list — pin the hostile-env smoke's ENV_VARS
  against a live source sweep** · `built` (2026-07-13, branch
  `claude/env-poison-pin-0713` — `tests/test_env_poison_pin.py` AST-sweeps
  the SAME files the smoke discovers (service dirs + exclusions imported
  from the smoke module, one source of truth) and fails BY NAME + read site
  when source reads a name `ENV_VARS` misses; resolves literal reads,
  module-constant `ENV_*` indirection, and guarded-wrapper call sites
  (`_env_int("X", …)`); non-derivable reads must sit on an explicit
  per-entry-justified dynamic allowlist with a stale-entry check (currently
  one entry: `app/railway.py` `_committed_services`, a presence-only read
  of committed-inventory names); per-service nonzero meta-test so a lost
  read shape can't blank the sweep; red-proven on a planted unpoisoned
  read; original capture 2026-07-13, hostile-env-smoke session 💡) —
  `tests/test_hostile_env_smoke.py` (PR #287) poisons a
  hand-collected 38-name literal; a companion assertion (AST or regex sweep
  of `os.environ`/`os.getenv`/`ENV_* =` over app/, botsite/, dashboard/,
  review/ at test time, same exclusions as the smoke) failing when source
  reads a name the list misses would make the poison
  self-updating-or-loud. Worth having because a new env-var read added
  after PR #287 is silently unpoisoned — the exact rot class the smoke
  exists to close, reopened one variable at a time. Deduped against this
  backlog: the code-vs-inventory bullets (#227 and its per-service
  generalization) check env-var NAME *documentation* completeness against
  docs tables, never the smoke's poison list; the env-guard gate covers
  only bare `int()`/`float()` casts. Source:
  `.sessions/2026-07-13-hostile-env-smoke.md` 💡.

- **Outbox REPORT grammar drift pin — parse the committed outbox at HEAD
  in CI** · `built` (2026-07-13, PR #289, branch
  `claude/outbox-grammar-pin-0713` —
  `tests/test_outbox_grammar_pin.py` reads the committed `control/outbox.md`
  from disk, zero network, feeds it through `briefing.latest_report` and
  fails naming the drift when a REPORT-like level-2 heading is skipped or
  zero reports parse while `## REPORT` text exists; plus synthetic cases
  keeping the pin's REPORT-like regex and the parser aligned; captured
  2026-07-13, briefing-outbox session 💡) — a small
  offline test feeding this repo's own committed `control/outbox.md`
  (read from disk, zero network) through `briefing.latest_report` and
  failing when the real file drifts out of the grammar the briefing reads
  (REPORT-like headings skipped, or zero reports found while `## REPORT`
  text exists). Worth having because the /owner/briefing REPORTS card
  (PR #286) and the coordinator's hand-written outbox entries share a
  grammar enforced by nothing — one heading typo silently demotes the
  newest night report to the honest-empty state on the page the owner
  opens every morning. Deduped against this backlog: the grammar
  source-of-truth notes pin status.md/inbox/claims formats (kit-owned,
  `src/engine/grammar.py`); no bullet covers `control/outbox.md`'s REPORT
  grammar or a parse-the-committed-file pin for it. Source:
  `.sessions/2026-07-13-briefing-outbox.md` 💡.

- **Environ-mention accounting leg for the poison pin** · `captured`
  (2026-07-13, env-poison-pin session 💡) — `tests/test_env_poison_pin.py`
  derives env-var names from a recognized-shape list
  (`_name_expr_of_read`: get/getenv/subscript/in/pop/setdefault, constant
  indirection, wrapper call sites), so aliasing (`e = os.environ` then
  `e.get("X")`) or a novel access idiom is silently ignored rather than
  loud. A completeness guard asserting every AST occurrence of
  `environ`/`getenv` in service source is accounted for — consumed by a
  recognized name-read, part of a whole-env use (`{**os.environ}` /
  `dict(os.environ)`), or explicitly allowlisted — would make the
  scanner's own shape coverage self-checking. Worth having because the
  pin's guarantee is only as strong as its shape list, and an unrecognized
  idiom today slips beneath it — the same silent-rot class, one level up.
  Deduped against this backlog: the code-vs-inventory bullets check
  documentation completeness against docs tables; nothing checks the
  sweep's own shape coverage. Source:
  `.sessions/2026-07-13-env-poison-pin.md` 💡.

- **Outbox grammar gate in the CI control fast lane — run the pin on the
  PRs that write the outbox** · `built` (2026-07-13, PR #314, ORDER 027
  item 7 — `quality.yml`'s lane step now emits a `pin_tests` output and a
  fast-lane grammar-pins gate (setup-python + `pip install pytest httpx`
  only — the pins' sole third-party import) runs
  `tests/test_outbox_grammar_pin.py` when a control-only diff touches
  `control/outbox.md`, plus `tests/test_own_heartbeat.py` when it touches
  `control/status.md` (the incident-#307 heartbeat class); control-only
  diffs touching neither keep the bare fast path unchanged) — original
  capture: `quality.yml`'s control fast lane short-circuits GREEN on a
  control/**-only diff (pytest never runs), and outbox appends are exactly
  control/**-only PRs, so `tests/test_outbox_grammar_pin.py` (PR #289)
  fires only on the NEXT non-control PR — after the typo'd report has
  already spent a morning rendering honest-empty on /owner/briefing. The
  fast lane already runs in-job control gates (control-status, inbox
  append-only); add an outbox grammar step there when `control/outbox.md`
  is in the diff — run the single pin test file or a tiny inline parse —
  so the drift reddens the PR that introduces it. Deduped against this
  backlog: the grammar-drift-pin bullet above is the pytest pin itself
  (merge-lagged by the fast lane's design); the grammar source-of-truth
  notes cover status.md/inbox/claims kit-owned grammars; no bullet touches
  the fast lane's gate set. Source:
  `.sessions/2026-07-13-outbox-grammar-pin.md` 💡.

- **Abandoned guided sessions surfaced on the owner queue** · `built`
  (2026-07-13, PR #293 — `abandoned_guided_claims()` in
  `botsite/testing_store.py` joins `claims` × `guide_exchanges` filtered to
  status='claimed' with no submission row and ≥1 exchange; `_owner_page`
  builds a read-only `dropoffs` ctx list and `testing_owner.html` renders a
  "Drop-offs" section with exchange count, last exchange time, and the
  transcript behind the same collapsed `<details>` block as #292) —
  original capture: a claim that chats
  with the AI guide but never submits now leaves persisted transcript rows
  (PR #292) the owner can never see: the owner queue iterates submissions,
  so drop-off evidence — where testers engaged, got confused, and gave
  up — is stored but invisible. A small owner-queue section listing
  claimed-but-never-submitted claims with guide-chat activity (exchange
  count + last exchange time, transcript behind the same collapsed
  details) would turn silent abandonment into product feedback: the
  walkthrough step where chats cluster before a claim dies is exactly the
  step that needs rewriting. Deduped against this backlog + the
  queue-state NEXT list: the transcript bullet above covers submissions
  only; the tester-task URL liveness bullet probes product URLs; nothing
  touches unsubmitted-claim visibility or drop-off signals. Source:
  `.sessions/2026-07-13-guide-transcript-evidence.md` 💡.

- **Drop-off step heatmap on the owner queue** · `built` (2026-07-13,
  PR #294 — `guided_step_dropoff()` in `botsite/testing_store.py`
  aggregates the same claims × guide_exchanges scope as
  `abandoned_guided_claims()` per task and step_index into
  touched/died-here counts; `_owner_page` feeds it to
  `testing_owner.html`, which renders a per-task heatmap strip at the top
  of the Drop-offs section, cell shading scaled by the died-here share) —
  original capture: the Drop-offs section (PR #293) shows
  each abandoned claim's transcript individually, but the signal the
  capture named — "the walkthrough step where chats cluster before a claim
  dies is exactly the step that needs rewriting" — still requires reading
  every transcript. A tiny per-task aggregate over the same
  `guide_exchanges` rows (per step_index: how many abandoned claims' chats
  touched it, and how many died there — i.e. it was their LAST exchange)
  rendered as a one-line count strip per task would rank the rewrite queue
  at a glance. Worth having because per-claim transcripts are anecdotes;
  the per-step aggregate is the actionable product-feedback number the
  drop-off data exists to produce. Deduped against this backlog + the
  queue-state NEXT list: the drop-off bullet above (now built) surfaces
  claims, not step aggregates; the transcript bullet covers submissions;
  nothing aggregates guide-chat activity per step. Source:
  `.sessions/2026-07-13-owner-queue-dropoff.md` 💡.

- **Step text labels on the drop-off heatmap** · `built` (2026-07-13,
  PR #295 — `_owner_page` joins each heatmap cell's step_index against
  the guided task's walkthrough step titles, truncated at 80 chars, and
  the cell tooltip carries the text; unknown task / out-of-range index
  keeps the bare number) — the heatmap strip (PR #294) names steps by
  number only; the guided tasks' walkthrough step texts already live in
  the tester-facing task data (`shaped_tasks()` / `task_by_id(...)` feed
  the guide with the step list), so joining `step_index` against the
  task's step text in `_owner_page` would let each cell's tooltip (or a
  per-task legend line) say WHAT the deadliest step asks the tester to
  do — "step 3 · open the theme toggle" instead of "step 3". Worth having
  because the heatmap's whole point is naming the step that needs
  rewriting, and today the owner still has to open the tester page to
  learn what the number means. Deduped against this backlog: the drop-off
  and heatmap bullets above (both now built) cover surfacing and
  aggregating; nothing joins step_index back to the walkthrough step
  text. Source: `.sessions/2026-07-13-dropoff-heatmap.md` 💡.

- **Heatmap tail — render the walkthrough's full length, not just the
  observed steps** · `built` (2026-07-13, PR #296 — `_owner_page` pads
  each task's heatmap cells with zero-count `reached: False` entries out
  to `len(step_script)` after the step-text join; the template renders
  never-reached cells hollow with a "never reached" tooltip plus an
  "of N steps" label; the store aggregate stays observed-data-only,
  unknown tasks keep the observed-only strip) — original capture:
  `guided_step_dropoff()` densifies cells from 0 to the highest
  step any drop-off's chat touched, so steps no tester ever reached are
  invisible: dying at step 2 of a 6-step script renders the same strip
  as dying at step 2 of 2. The script's real length is already in
  `_owner_page` since the step-text join (`task_steps(task_by_id(...))`),
  so padding the strip with zero cells out to `len(steps)` is a few
  lines. Worth having because distance-to-finish is the severity signal
  the strip currently hides — "died 4 steps from the end" and "died at
  the last step" should not read the same. Deduped against this backlog:
  the heatmap bullet (built) aggregates observed steps only, the
  step-text bullet (built) covers labels; nothing covers the unreached
  tail. Source: `.sessions/2026-07-13-heatmap-step-labels.md` 💡.

- **Heatmap survival contrast — fold finishers' guide chats into the
  strip** · `built` (2026-07-13, PR #298 — `guided_step_dropoff()` emits
  per-step `finished` finisher counts + `died_share` over ALL touchers,
  finisher chats extend the dense range, and the strip shades by
  lethality with a "N finisher(s) asked" cell annotation) — original
  capture (2026-07-13, heatmap-tail session 💡): the
  drop-off heatmap aggregates ONLY abandoned claims
  (`guided_step_dropoff()` scopes to status='claimed' with no submission
  row), so a step where ten finishers also chatted heavily but pushed
  through renders identically to one where every toucher died: the strip
  can't distinguish "hard but passable" from "wall". The finished
  claims' guide exchanges are already persisted (PR #292 stores them
  regardless of outcome; the heatmap scope merely excludes them), so a
  per-step survivor count ("N finishers also asked here") joined into
  the same cells — or a shading that scales by died-share among ALL
  touchers, not just drop-offs — would rank rewrite urgency by lethality
  rather than raw death count. Worth having because a step everyone
  asks about but everyone passes needs a hint, while a step half its
  touchers die on needs a rewrite — today both read the same. Deduped
  against this backlog: the drop-off, heatmap, step-text, and tail
  bullets (all built) aggregate abandoned claims only; the transcript
  bullet covers submissions' transcripts per claim, not per-step
  aggregates; nothing folds finished claims' guide activity into the
  step strip. Source: `.sessions/2026-07-13-heatmap-tail.md` 💡.

- **Closed-but-unanswered nag for the questions ledger** · `built`
  (2026-07-13, PR #299, branch `claude/questions-answer-nag-0713` —
  `story.unanswered_closed` over the existing `question_status`/
  `question_answer_state` filter semantics feeds a warn banner on
  `/questions` naming the closed-but-unanswered records;
  `review/gen_questions.py` gained the same pure-read helper plus
  `advise_unanswered`, printing one `ADVISORY: closed without a published
  answer: <url>` line per record on EVERY run with a readable ledger —
  merged, no-change, and fetch-failed paths alike; zero network) —
  original capture (2026-07-13, review-questions-bake-sync session 💡):
  the bake sync
  (PR #297) now flips a ledger record's status to `closed` when its
  GitHub issue closes, but the answer link stays hand-written — so a
  `[program-review]` issue closed without a published answer renders as
  "closed / pending" forever, silently breaking the ledger's own promise
  ("the evidence-backed answer publishes in the next review edition AND
  lands here"). A bake-time or CI-time advisory flagging records where
  `status == closed` and `answer_url` is missing (pure read of the
  committed questions.json, no network) would turn that silent gap into
  a visible nag for the next session. Worth having because the sync
  automates intake but thereby makes it POSSIBLE to close a question
  without answering it on record — exactly the quiet dishonesty the
  ledger exists to prevent. Deduped against this backlog + the
  queue-state NEXT list: the bake-sync bullet (now built) covers intake
  only; the owner-gated answer-bot bullet is about generating answers,
  not auditing their absence; nothing watches answer-lag on the ledger.
  Source: `.sessions/2026-07-13-review-questions-bake-sync.md` 💡.

- **Finisher-question hotspots — tasks with zero drop-offs never surface
  their hint-needing steps** · `built` (2026-07-13, PR #303 —
  `guided_finisher_hotspots()` aggregates per-step `finished` counts over
  finisher claims on tasks with NO drop-offs — tasks with any drop-off
  stay on the heatmap as contrast — and the owner queue lists the strip
  under the heatmap with the same step-text join + full-length padding,
  no lethality shading) — original capture (2026-07-13,
  heatmap-survival-contrast session 💡): the survival contrast (PR #298)
  only renders on tasks that HAVE drop-offs (`guided_step_dropoff()`
  keys the strip off abandoned claims; finishers are contrast, not
  subject), so a task where every tester finished but half of them asked
  the guide about step 3 shows nothing at all: the "needs a hint" signal
  the contrast separates from "needs a rewrite" is invisible exactly
  where it's purest. A small finisher-only aggregate (same `finished`
  counts, no lethality shading) listed under the heatmap — or folded in
  as contrast-only task rows — would surface question hotspots before
  the first drop-off ever happens. Worth having because hint-worthy
  friction on a passable task is the cheapest UX fix available, and
  today it only becomes visible after someone gives up. Deduped against
  this backlog: the drop-off, heatmap, step-text, tail, and
  survival-contrast bullets (all built) key the strip off abandoned
  claims; the transcript bullet is per-claim evidence, not per-step;
  nothing aggregates finisher chats on tasks without drop-offs.
  Source: `.sessions/2026-07-13-heatmap-survival-contrast.md` 💡.

- **Stamp `closed_at` on questions-ledger records at bake time — turn the
  closed-but-unanswered nag into an answer-debt age** · `built`
  (2026-07-13, PR #301 — `gen_questions` stamps the issue's own
  `closed_at` on closed records (same REST response; dropped on reopen,
  `status_override` pins the pair); the advisory and the /questions
  banner say "closed N days without an answer" via a mirrored
  `answer_debt_days` (UTC, `None` on missing/bad stamps → binary-wording
  fallback for old baked data) and the banner ranks offenders
  oldest-`closed_at`-first; captured 2026-07-13,
  questions-answer-nag session 💡) —
  `gen_questions.issue_record` reads the issue's state but discards its
  `closed_at` timestamp, so the nag (PR #299) is binary: "closed without a
  published answer" reads the same whether the question closed an hour ago
  (answer plausibly in flight) or two weeks ago (promise genuinely
  broken). Recording `closed_at` on the record when the sync flips a
  status to closed (one field, same single REST call, hand-written fields
  untouched) would let the advisory and the /questions banner say "closed
  N days without an answer" and let the ledger sort by answer debt. Worth
  having because a nag with an age ranks itself — the oldest broken
  promise is the one the next session should pay first, and today the
  advisory can't tell it from this morning's. Deduped against this
  backlog: the bake-sync and closed-but-unanswered bullets (both built)
  cover intake and the binary flag; the owner-gated answer-bot bullet
  generates answers; nothing carries closure timestamps or measures
  answer lag. Source: `.sessions/2026-07-13-questions-answer-nag.md` 💡.

- **Answer-latency stat on /questions — measure the promise kept, not
  just broken** · `built`
  (2026-07-13, PR #302 — `story.answer_latency` medians the whole-day
  asked→closed turnaround over the answered records
  (`answer_latency_days`: `None` on a missing/unparseable timestamp →
  record ignored, clamped at 0; int when whole, exact half-day float on
  even counts) and /questions renders the one-line stat only when ≥1
  record qualifies, so the committed pre-stamp ledger renders
  byte-identically; captured 2026-07-13, answer-debt-age session 💡) —
  the bake (PR #301) stamps `closed_at` on EVERY closed ledger record,
  answered ones included, so `closed_at − asked` is a real per-question
  resolution time; a small honest stat over the answered records
  ("answered questions resolved in a median of N days", hidden until ≥1
  answered record exists) on /questions would measure the intake promise
  being KEPT — the positive complement to the answer-debt nag, which only
  measures it breaking. Worth having because the ledger's whole pitch to
  reviewers is "ask and it lands answered here": a measured turnaround
  number is stronger evidence than an empty nag banner, and it costs zero
  new fields — both timestamps are already baked. Deduped against this
  backlog: the bake-sync, closed-but-unanswered, and answer-debt-age
  bullets (all `built`) cover intake and failure signals; the
  pickup-latency rollup measures order pickup, not question resolution;
  nothing computes asked→closed turnaround.
  Source: `.sessions/2026-07-13-answer-debt-age.md` 💡.

- **Bake a full `asked_at` timestamp on questions-ledger records — give
  the latency stat sub-day resolution** · `built` (2026-07-13, PR #305 —
  `issue_record` stamps `asked_at` from the same response's full
  `created_at` (`asked` untouched as the display date, never fabricated);
  `answer_latency_days` prefers the full stamp — fractional days, int
  when whole — and falls back to the date-precision `asked` so committed
  pre-stamp records compute byte-identically, the merge never backfills
  existing records; `answer_latency` grows a `median_label` ("6 hours"
  under a day; whole/half-day wording byte-identical) that /questions
  renders) — original capture (2026-07-13, questions-answer-latency
  session 💡): `gen_questions.issue_record`
  truncates the issue's `created_at` to a date (`created[:10]`) while
  `closed_at` keeps its full timestamp, so `answer_latency_days` (PR
  #302) can never resolve finer than whole days and a same-day answer
  reads "0 days" — the stat's weakest wording exactly when the
  turnaround is most impressive. Baking `asked_at` alongside the display
  date (same single REST response, `asked` untouched for the table and
  existing sorts) would let the stat say "resolved in a median of 6
  hours" once real turnarounds are fast, honest at the resolution the
  data actually has. Worth having because the ledger's pitch is
  turnaround speed, and the current floor understates precisely the best
  evidence. Deduped against this backlog: the bake-sync,
  closed-but-unanswered, answer-debt-age, and answer-latency bullets all
  read or write only the date-precision `asked` plus `closed_at`;
  nothing carries a full asked timestamp.
  Source: `.sessions/2026-07-13-questions-answer-latency.md` 💡.

- **Per-step question digest — surface WHAT testers asked at a hotspot,
  not just how many** · `built` (2026-07-13, PR #304 —
  `guided_step_questions()` groups the persisted `guide_exchanges`
  tester message text by (task, step) across ALL claims, drop-offs and
  finishers alike, newest 5 per cell + a running total; the owner queue
  renders one collapsed `<details>` per asked-at step under both strips,
  autoescaped + truncated at 160 chars) — original capture (2026-07-13,
  finisher-hotspots session 💡): the heatmap and the finisher hotspots (PRs #294/#298/#303)
  rank WHERE guide chats cluster, but the owner still has to open each
  drop-off's per-claim transcript one by one to learn what confused
  people — and finishers' transcripts on hotspot tasks aren't rendered
  anywhere at all (PR #292 attaches them to submissions, not to the
  strip). A per-step digest — group the persisted `guide_exchanges`
  messages by (task, step) across ALL claims and render the tester
  questions (message text only, untrusted-input framing, maybe capped +
  collapsed) behind each cell — would turn "step 3 · 4 asked" into the
  actual rewrite input: the four questions themselves. Worth having
  because the hotspot tells the owner a hint is needed but not which
  hint; the raw questions are already persisted and answer that
  directly. Deduped against this backlog: the transcript bullet
  (built, #292) is per-claim evidence on submissions; the heatmap,
  survival-contrast, and finisher-hotspots bullets (all built) count
  claims per step but never render message text; nothing groups guide
  messages by step across claims.
  Source: `.sessions/2026-07-13-finisher-hotspots.md` 💡.

- **Guide-question step provenance — pin what the step SAID when the
  question was asked** · `built` (2026-07-13, step-provenance session —
  `guide_exchanges.step_title` snapshots the step's title at persist time
  (`add_guide_exchange` + an in-place column retrofit for pre-pin DB
  files, rows before the pin honestly keep `''`); the owner-queue digest
  resolves each question via `testing._digest_question` — pin == current
  title renders clean, a differing pin renders "asked when this step said
  …" with the ask-time title, a pinned-free legacy row says the wording
  wasn't recorded instead of guessing; captured 2026-07-13,
  step-question-digest session 💡) — `guide_exchanges` rows pin only `step_index`, so the
  digest (PR #304) and both strips (#294/#298/#303) attribute every
  persisted question to whatever text CURRENTLY sits at that index: the
  moment a walkthrough script inserts, removes, or reorders a step,
  history is silently re-attributed to the wrong step and a hotspot can
  point the owner at a step nobody actually asked about. Persisting a
  small step snapshot with each exchange (the step's title, or a hash of
  it — the title already joins into tooltips via `_heatmap_step_text`)
  would let the strips flag "asked against an older version of this
  step" instead of misattributing. Worth having because the digest's
  whole pitch is turning counts into trustworthy rewrite input — and the
  first script rewrite the hotspots trigger is exactly the event that
  corrupts the attribution. Deduped against this backlog: the heatmap,
  survival-contrast, finisher-hotspots, and digest bullets all consume
  `step_index` as-is; the step-text bullet (built, #294) joins the
  CURRENT title for display only; nothing versions or snapshots step
  identity.
  Source: `.sessions/2026-07-13-step-question-digest.md` 💡.

- **One-shot `asked_at` backfill for the committed pre-stamp questions
  ledger** · `captured` (2026-07-13, asked-at-timestamp session 💡) —
  PR #305 gives sub-day latency resolution only to records baked AFTER
  it lands: the merge deliberately never backfills `asked_at` onto
  existing records (pinned by test, so that PR's committed file stayed
  byte-identical), which leaves every historical answered record floored
  at date precision forever — and a median over mixed-precision records
  stays coarse as long as the legacy majority dominates. The GitHub API
  still serves `created_at` for every issue url already in the ledger,
  so either a one-time backfill run or teaching the merge to stamp
  `asked_at` when missing (bake-owned, exactly like `closed_at` — a
  strictly additive field, no display change) would give the ENTIRE
  ledger the same honest resolution in one bake diff. Worth having
  because the stat's pitch is measured turnaround, and today its history
  understates precision the API still has on record. Deduped against
  this backlog: the asked_at bullet (built, #305) stamps new records
  only and its entry documents the no-backfill pin; the bake-sync and
  answer-debt bullets own status/closed_at, not asked stamps; nothing
  proposes backfilling.
  Source: `.sessions/2026-07-13-asked-at-timestamp.md` 💡.

- **Scheduled browser-level smoke-crawl in CI — a Playwright job that
  cold-crawls the three live sites the way the manual cold passes do** ·
  `built` (2026-07-14, PR #321 — `scripts/smoke_crawl.py` +
  `.github/workflows/smoke-crawl.yml`: headless Chromium crawls the three
  public sites + the control-plane root every 6h (cron `47 2-23/6 * * *`,
  offset from healthcheck's `17 */6 * * *` on both fields), same-site link
  discovery, desktop 1280×900 + mobile 375×812, failing on console errors /
  non-200 pages / 4xx-5xx same-site links; per-site page cap + global
  deadline keep a run well under 5 minutes and blowing the deadline is
  itself a FAILURE; console-error allowlist seeded EMPTY (the #311 pass
  left zero known noise); gated `/owner` corner skipped by documented
  design; env/CLI overrides carry the agent-container proxy workaround so
  CI runs plain; proven by a local live crawl of all four sites —
  original capture, 2026-07-13 cold-browser-review session 💡) — the existing
  `healthcheck.yml` smoke is curl-level (`/healthz` + `/` status codes);
  both 2026-07-13 cold passes found real regressions it can never see
  (dead chrome wiring, a blank hamburger, a lost footer gutter, a favicon
  404) because they only exist in a rendering browser. A scheduled Actions
  job launching headless Chromium over each site's route inventory,
  failing on console errors / pageerrors / failed requests / horizontal
  overflow at 375px, would make the cold pass a standing gate instead of
  a hand-run ritual (GitHub runners need no proxy TLS flag; the local
  recipe is in `docs/CAPABILITIES.md`). Worth having because both manual
  passes paid for themselves within hours of each other — visual-layer
  rot demonstrably recurs and nothing automatic watches it. Deduped
  against this backlog + `.sessions/*.md` cards: the healthcheck bullets
  are status-code probes; the webhook-analyzer card used Playwright once,
  ad hoc, locally; no scheduled/browser-level crawl idea exists anywhere.
  Source: `.sessions/2026-07-13-cold-browser-review.md` 💡.

- **Orientation-budget headroom readout in `bootstrap.py check` — print
  the boot-set word total + remaining headroom even when green** ·
  `captured` (2026-07-13, env-leads-close session 💡) — the 7000-word
  orientation budget is invisible until breached: the env-leads-close
  session edited `docs/current-state.md` blind, breached at 7065 words,
  and needed four trim/re-run cycles to land 1 word under the cap. A
  standing "6999/7000" line in every check run turns trim work from
  iteration into arithmetic before writing starts. Kit-side
  (`bootstrap.py` is generated) — also a substrate-kit worthiness relay
  per the working agreement. Deduped against this backlog + the
  queue-state NEXT list: no orientation-budget/headroom bullet exists.
  Source: `.sessions/2026-07-13-env-leads-close.md` 💡.

- **Cross-table reference check on the testing-DB import valve — reject
  backups with orphan rows** · `built` (2026-07-14, PR #323 — a
  referential pass in
  `_validated_import_rows` (`botsite/testing_store.py`): every cross-table
  reference edge (`submissions.claim_id` / `guide_exchanges.claim_id` /
  `payout_ledger.claim_id` → claims, `ai_reviews.submission_id` /
  `screenshots.submission_id` → submissions, the `_IMPORT_REFS` constant)
  must resolve among the UPLOADED rows of the target table, or the import
  400s loudly naming the referencing table, row id, FK column, and the
  missing target — before anything is written. PR #320's legacy tolerance
  preserved: absent newer tables mean no referencing rows to check, and
  every FK column is NOT NULL + required so there is no nullable case;
  non-scalar FK values from untrusted JSON are the 400 path, never a 500.
  One orphan test per edge plus valid-full/legacy/non-scalar coverage in
  `botsite/tests/test_testing_import.py`) — original capture: SQLite
  foreign keys are OFF by default (`PRAGMA foreign_keys` is never enabled
  in `botsite/testing_store.py`'s `_connect()`), so a truncated or
  hand-edited backup whose submissions reference missing claims imports
  "successfully" through `POST /testing/owner/import.json` (PR #320), and
  the owner queue's INNER JOINs (`list_submissions`) then silently drop the
  orphan rows — a restore that reports ok but shows less than it inserted.
  A referential pass in `_validated_import_rows` would 400 loudly instead.
  Worth having because the valve's entire promise is a faithful restore,
  and orphan rows are the one corruption class its validation still
  admitted silently. Source:
  `.sessions/2026-07-14-testing-import-valve.md` 💡.

- **Import valve for the testing-DB export — restore `export.json` after a
  redeploy wipe** · `built` (2026-07-14, PR #320 — `POST
  /testing/owner/import.json` (`botsite/testing.py`) restores the raw
  export.json body via `testing_store.import_all()`: same owner auth as
  every owner route (503 fail-closed / 401) plus the standard
  `guard_state_change` same-origin + rate-limit dependency; body bounded
  at 10 MB (413), shape/enum-validated per record (400 with the exact
  reason); REPLACE-into-empty semantics — 409 on a non-empty DB unless
  `?replace=1` wipes-then-inserts in one atomic transaction; legacy
  backups missing newer columns (`guide_exchanges.step_title`,
  `claims.paypal_email`, whole postdating tables) restore with the
  schema defaults via `.get`, never invented values; row ids preserved so
  cross-table references survive) — original capture: the ephemeral-disk
  mitigation is half a lifeboat: `GET /testing/owner/export.json`
  (owner-auth) dumps the full tester-program DB before a redeploy, but
  nothing can put the backup BACK — after the wipe the owner holds a JSON
  file and the queue starts empty (claims, transcripts, ledger,
  provenance pins all gone until Postgres lands). An owner-auth import
  valve (upload the export, rows re-inserted with the same honest
  `.get`-default handling this session used for pre-pin rows, so old
  backups without newer columns restore cleanly) would close the loop the
  export half-opened. Worth having because every backup valve that can't
  restore is a promise the disaster will break — and the Postgres ask it
  bridges to is still an OPEN owner action. Source:
  `.sessions/2026-07-13-step-provenance.md` 💡.

- **Wire `scripts/review_row_check.py` into `quality.yml` as the advisory
  owed-row step** · `captured` (2026-07-13, build-direct session 💡) — the
  script shipped 2026-07-11 (slice 14) but no workflow calls it: idea A's
  named CI-wiring slice stayed open, and it unblocks now that the
  fastlane-outbox-gate PR (#314) has landed and the workflow is free
  again. One advisory (never exit-affecting) full-lane step that runs the
  range check and prints ROW OWED keeps the review-queue ledger honest
  without waiting on a manager sweep. Worth having because a shipped
  checker nobody invokes is drift waiting to happen — the same hollow-gate
  class the fast-lane pin-map bullet warns about. Deduped against this
  backlog + the queue-state NEXT list: the review-queue row auto-check
  bullet records the script as shipped and defers row-APPENDING to the
  manager; no bullet covers invoking the CHECK from CI, and `quality.yml`
  contains zero references to the script. Source:
  `.sessions/2026-07-13-build-direct.md` 💡.

- **Claim bullet carries its PR number once opened — closes the claims-drift
  gate's pruned-ref blind spot** · `captured` (2026-07-14, claims-drift-gate
  session 💡) — the drift gate (PR #318) treats a claim whose branch
  resolves to no ref as LIVE (fail-safe), so a repo that prunes branches on
  merge would never flag an orphan. An optional `PR #N` token appended to
  the claim bullet when the PR opens would give the gate a fallback:
  `git log origin/main --grep='(#N)'` — the squash-merge subject survives
  the pruned ref, same zero-network git plumbing. Worth having because the
  gate's one documented indeterminate lane is exactly the state GitHub's
  "delete branch on merge" setting would make the common case. Deduped
  against this backlog + the queue-state NEXT list: existing claim bullets
  cover order-claim pickup latency, stalled-claim aging on /orders, and
  sweep-hold claim files — nothing touches claim grammar or branch
  terminality. Source: `.sessions/2026-07-14-claims-drift-gate.md` 💡.

- **Index-drift advisory in `check` — existence-check `project.index.json`
  paths on every run** · `captured` (2026-07-14, project-index session 💡) —
  the contextpack generator existence-checks `source_roots` only when
  someone runs `python3 bootstrap.py contextpack`, which nothing schedules;
  a renamed folio or moved source root rots the newly populated index
  silently until the next manual generation. A `check`-time advisory
  (never exit-affecting) walking every area's `folio`, `binding_docs` and
  `source_roots` entries and warning on missing paths would surface drift
  in every CI run for near-zero cost. Kit-side (`bootstrap.py` is
  generated) — also a substrate-kit worthiness relay per the working
  agreement. Worth having because a populated-but-stale index is worse
  than the empty placeholder it replaced — it misleads with confidence
  instead of signalling neglect. Deduped against this backlog + the
  queue-state NEXT list: no bullet mentions contextpacks or
  project.index.json. Source: `.sessions/2026-07-14-project-index.md` 💡.

- **Rewrite relative links inside rendered remote markdown to their GitHub
  source (or de-linkify them)** · `built` (2026-07-14, PR #322 —
  `app/journal.py` `render_markdown(source=)` rewrites relative hrefs to
  github.com blob URLs and relative img srcs to raw-content URLs, resolved
  against the fetched file's directory; unknown source or a root-escaping
  `../` de-linkifies instead; all 7 render sites pass their source; the
  smoke-crawl `.md`-container carve-out deleted, and `/favicon.ico` added
  fleet-wide for the sibling #321 finding; captured 2026-07-14, smoke-crawl
  session 💡) — the control-plane renders other repos' markdown verbatim in
  `<div class="md">` (heartbeats on /fleet, the fleet-manager ledger on
  /reviews, environment docs on /environments), and relative links inside
  that content (`README.md`, `gen2-blueprint.md`, `docs/retro/…`) resolve
  against this origin and 404 — the first smoke-crawl run (PR #321) flagged
  20 of them live, every one clickable by a real visitor today. The
  renderer already knows each document's source repo + path, so rewriting
  relative hrefs to the GitHub blob URL (or the in-app
  `/journal/{repo}/file` view for fleet repos) is a contained fix. Worth
  having because three public pages serve clickable 404s right now, and
  fixing it lets `scripts/smoke_crawl.py` delete its documented
  `.md`-container exclusion — restoring browser-gate coverage over exactly
  the surfaces that degrade silently. Deduped against this backlog + the
  queue-state NEXT list: the "Deep-link fleet lane files into the widened
  /journal/{repo}/file view" bullet ADDS chrome links via the in-app
  renderer; nothing touches relative hrefs inside rendered markdown bodies.
  Source: `.sessions/2026-07-14-smoke-crawl.md` 💡.

- **Sample-verify rewritten source-link targets — a bounded existence check
  on the github.com blob URLs the markdown rewriter mints** · `built`
  (2026-07-14, branch `claude/md-link-sample-0714` — `scripts/smoke_crawl.py`
  pass 4: collects the rewriter's github.com blob/raw +
  raw.githubusercontent.com URL shapes from crawled control-plane pages
  only, deterministically samples ≤10 (sorted + evenly strided, no
  randomness/clock), HEAD-checks each with GET fallback (~5s/request, own
  30s budget) — 2xx/3xx pass, 403 passes with a private-repo note, 404
  fails naming the URL + its source page, network errors warn; pure-logic
  pins in `tests/test_smoke_crawl_rewritten_links.py`; original capture
  2026-07-14, md-relative-links session 💡) — the relative-link fix
  (PR #322) converts same-origin 404s inside rendered remote markdown into
  EXTERNAL github.com/raw links, and the smoke-crawl never follows or
  fetches external links by documented design — so the failure class did
  not die, it moved outside every gate's scope: a wrong path resolution, or
  an upstream file rename after the TTL cache refreshes, now yields a
  GitHub 404 nothing measures. A bounded sample (say 10 rewritten targets
  per scheduled crawl, HEAD via the raw host the app already uses) would
  put a floor back under the rewrite without hammering GitHub. Worth having
  because a rewriter that mints dead external links is exactly as broken
  for the visitor as the 404s it replaced — just invisible to the gate that
  caught the originals. Deduped against this backlog + the queue-state NEXT
  list: the rewrite bullet above ships the rewriter itself; no bullet
  checks external/rewritten link liveness anywhere. Source:
  `.sessions/2026-07-14-md-relative-links.md` 💡.

- **Pin `_IMPORT_SPEC`/`_IMPORT_REFS` against the live schema with a drift
  test** · `built` (2026-07-14, branch `claude/import-schema-pin-0714` —
  `botsite/tests/test_import_schema_drift.py` builds an in-memory DB from
  the real `_SCHEMA` and derives tables via `sqlite_master`, columns via
  `PRAGMA table_info`, FK edges via `PRAGMA foreign_key_list`, then asserts
  exact two-way coverage against `_IMPORT_SPEC`/`_IMPORT_REFS`/
  `_IMPORT_ENUMS`, failing with the drifted table/column/edge named; the
  two deliberate spec↔schema gaps are pinned explicitly, never skipped —
  `screenshots.data_base64`→`data` as a rename pin, and the
  `payout_ledger.claim_id`→claims edge (checked on import, undeclared in
  the schema) as an extra-refs pin that must shrink if the schema gains
  the REFERENCES clause) — original capture (import-referential session
  💡): the
  import valve's field spec and its new reference-edge list
  (`botsite/testing_store.py`) are hand-kept constants that mirror
  `_SCHEMA` by convention only: the next table or FK column added to
  `_SCHEMA` imports as silently-absent (spec) or silently-unchecked
  (refs), and nothing goes red — the hand-kept-list drift class this repo
  has been bitten by before. A test that opens an in-memory DB, walks
  `PRAGMA table_info` + `PRAGMA foreign_key_list` per table, and asserts
  the derived column set and FK edges match the two constants would make
  schema growth un-forgettable, while keeping the constants explicit and
  reviewable (runtime introspection would trade that away for magic).
  Worth having because the referential session hand-derived the edges from
  `REFERENCES` clauses and a JOIN grep — a derivation that was manual
  exactly once and should never need to be trusted manual again. Deduped
  against this backlog + the queue-state NEXT list: no
  import-spec/schema-drift/foreign_key_list bullet exists anywhere.
  Source: `.sessions/2026-07-14-import-referential.md` 💡.

- **Export→import→export deep-equality round-trip pin** · `built`
  (2026-07-14, branch `claude/roundtrip-pin-0714` —
  `botsite/tests/test_import_roundtrip.py`: every `_IMPORT_SPEC` table
  populated via the real store writers (non-default values, unicode,
  null-vs-set score, all-256-byte blobs, every `_IMPORT_REFS` FK edge),
  exported, restored into a fresh DB through `import_all()`, re-exported,
  and the two exports asserted DEEPLY equal — only the export-act
  metadata (`exported_at`, `db_path`) is normalized, each with a
  documented reason; a spec-driven guard fails if any `_IMPORT_SPEC`
  table is left empty in the fixture so future tables must join the pin.
  Plus the legacy-shape round trip: an old backup missing newer
  columns/tables imports to explicit expected defaults-filled rows, and
  the upgraded export then round-trips deep-equal) — original capture
  (import-schema-pin session 💡): populate every table, run
  `export_all()`, import the result into a fresh DB via `import_all()`,
  re-export, and assert the two exports are DEEPLY equal (ids, values,
  base64 blobs — everything), instead of the current round-trip test's
  spot-checks of fields someone remembered to assert
  (`botsite/tests/test_testing_import.py`
  `test_round_trip_export_then_import_after_wipe`). Worth having because
  this pin plus the schema-drift pin (branch
  `claude/import-schema-pin-0714`) makes every current AND future column
  value-fidelity-checked for free: the drift pin proves the spec covers
  the schema, deep equality proves the covered values survive the trip —
  an import that quietly coerces or defaults a value today passes the
  spot-checks. Deduped against this backlog + the queue-state NEXT list:
  the import bullets are the valve (#320), the referential pass (#323),
  and the spec pin; nothing asserts export/import round-trip equality.
  Source: `.sessions/2026-07-14-import-schema-pin.md` 💡.

- **Freeze a real export.json as a committed golden legacy fixture** ·
  `captured` (2026-07-14, roundtrip-pin session 💡) — every "legacy
  backup" in the import tests is a hand-simulated shape: the test author
  guesses which columns old exports lacked, and if that guess is wrong
  the valve's legacy tolerance is tested against a fiction. Commit a
  REAL `export_all()` output now (tiny fixture data, secrets-free by
  construction — the export carries no secret), e.g.
  `botsite/tests/data/export-2026-07.json`, and assert forever that THIS
  file imports cleanly through `import_all()`; each future schema era
  freezes one more file instead of re-simulating history. Worth having
  because the valve's whole purpose is restoring backups taken by OLDER
  code, and no test currently exercises bytes an older version actually
  wrote. Deduped against this backlog + the queue-state NEXT list: the
  import bullets are the valve (#320), the referential pass (#323), the
  spec pin (#326), and the round-trip pin (branch
  `claude/roundtrip-pin-0714`); nothing commits a frozen real-export
  fixture. Source: `.sessions/2026-07-14-roundtrip-pin.md` 💡.

- **Disambiguate the smoke-crawl pass-4 404s from repo privacy — GitHub
  answers anonymous requests to PRIVATE repos with 404, not 403** ·
  `captured` (2026-07-14, md-link-sample session 💡) — the sampled
  rewritten-link check (branch `claude/md-link-sample-0714`) passes 403 as
  "private repo", but the 403 observed from the agent container is the CCR
  egress proxy's per-session GitHub gate (verified: the response body is
  the proxy's "access not enabled for this session" JSON, not GitHub's);
  in proxy-less CI, GitHub itself returns 404 for a private repo's blob
  URL — indistinguishable from a genuine rewrite defect, so a scheduled
  smoke-crawl FAIL can be repo privacy rather than rot. A small
  disambiguator — probe the failing repo's public visibility (e.g. one
  extra request to the repo root or the already-used raw host) or keep a
  committed known-private-repo list, and downgrade those 404s to the
  private-repo PASS note — would keep the gate's reds honest. Worth having
  because the first real scheduled-run 404 will otherwise be triaged as a
  rewriter bug when it may just be a private lane repo. Deduped against
  this backlog + the queue-state NEXT list: the sample-verify bullet ships
  the check itself; the private-lane bullets are botsite/review-side;
  nothing addresses 404-vs-privacy ambiguity in the crawl.
  Source: `.sessions/2026-07-14-md-link-sample.md` 💡.

- **Synthetic zero-commit-branch pin for the claims-drift gate — settle the
  relayed #319 false-positive LEAD** · `captured` (2026-07-14, eap-audit
  session 💡) — the gate's Lane 1 (`git merge-base --is-ancestor branch
  main`, `tests/test_claims_drift_gate.py:99`) is trivially TRUE for a
  claim whose branch was pushed with zero unique commits (tip = a main
  commit), so the gate would call a brand-new claim "merged" and red the
  build on honest in-flight work. A coordinator-relayed false positive
  "reported by PR #319" was NOT found in the repo record (body, comments,
  commits, check runs all clean — EAP close-out audit §11), so the lead is
  unconfirmed; one synthetic-repo test arming a claim on a zero-commit
  branch would either pin the bug (and motivate a not-yet-merged guard,
  e.g. require the branch tip to predate the claim or have unique commits)
  or retire the lead for good. Worth having because the gate is one day
  old, already load-bearing in the control fast lane, and this is its one
  alleged failure the synthetic suite doesn't cover. Deduped against this
  backlog + the queue-state NEXT list: the only claims-gate bullet (claim
  bullet carries its PR number) covers the pruned-ref indeterminate lane,
  not the zero-commit lane-1 false positive; no other bullet touches the
  gate. Source: `.sessions/2026-07-14-eap-audit.md` 💡.

- **Kit-gate advisory for the capability-seed fence itself** · `captured`
  (2026-07-14, order-028-fence session 💡) — extend the `bootstrap.py
  check` docs scan with an advisory that flags `docs/CAPABILITIES.md` when
  the `capability-seed` BEGIN/END pair is missing, unpaired, or
  out-of-order, so the fence can't be silently dropped again by a future
  rewrite of the file. Worth having because that is exactly what ORDER 028
  exists to repair — the fence vanished in a content rewrite and only a
  manual audit caught it, an order and a full PR later; the seat-digest
  render degrades silently meanwhile. Kit-owned surface, so the build
  routes via the kit lane, not this repo. Deduped against this backlog +
  the queue-state NEXT list: the only marker-scan bullet ("Kit-gate
  advisory for exact-ID model lines") covers session-card model lines;
  nothing covers the CAPABILITIES fence.
  Source: `.sessions/2026-07-14-order-028-fence.md` 💡.

- **Quick-reference drift check in the kit gate — pin the journal's pytest
  command to the CLAUDE.md verify line** · `captured` (2026-07-14,
  order-029-truing session 💡) — `bootstrap.py check` could grep
  `.session-journal.md`'s ⚡ Quick reference for the pytest command string
  and warn/fail when it diverges from the CLAUDE.md "Verifying a change"
  line, the way the word-budget gate already pins `docs/current-state.md`.
  Worth having because INC-23 and INC-24 are the same failure class (a
  boot-set surface nobody re-reads after the world changes) and the
  journal's test command is exactly machine-checkable. Deduped against
  this backlog + the queue-state NEXT list: no journal-drift or
  quick-reference bullet exists. Source:
  `.sessions/2026-07-14-order-029-truing.md` 💡.

- **Owner-actions renderer: generate the checklist from the ⚑ blocks** ·
  `captured` (2026-07-14, order-030-closeout session 💡) — the close-out
  walkthrough's section C hand-copies what/where/verify from the 9
  six-field ⚑ blocks in `docs/owner/OWNER-ACTIONS.md`; the control-plane
  already parses six-field blocks for `/queue` (`app/` owner-queue
  pipeline), so a small `scripts/owner_checklist.py` (or a `/queue.md`
  export) could emit the same compact checklist on demand and never drift
  from the source blocks. Worth having because every close-out/briefing
  that hand-copies the asks is a drift surface — one renderer keeps
  recommendation docs honest as asks are struck. Deduped against this
  backlog + the queue-state NEXT list: no checklist-export/renderer bullet
  exists (the backlog's owner-queue bullets are page features, not
  exports). Source: `.sessions/2026-07-14-order-030-closeout.md` 💡.

- **Teach the sweep job the `do-not-automerge` label** · `captured`
  (2026-07-14, automerge-reconcile session 💡) — the half-hourly sweep in
  `.github/workflows/host-automerge-extras.yml` selects open unarmed
  `claude/*` PRs and arms them without ever checking labels; a PR parked
  with `do-not-automerge` that does NOT touch `.github/workflows/**`
  (owner discretion, or a future rail) gets re-armed by the next sweep,
  silently overriding the kit enabler's own carve-out. One `--jq` clause
  in the sweep's PR selection (drop PRs whose labels contain
  `do-not-automerge`) closes the only remaining writer that ignores the
  label. Worth having because the reconciled workflow-touching rail (this
  session) made the label load-bearing for automerge parking. Source:
  `.sessions/2026-07-14-automerge-reconcile.md` 💡.

- **Truth-check `docs/reading-path.md` § sibling map against the
  fleet-manager roster** · `captured` (2026-07-14, kit-upgrade-v1.16.0
  session 💡) — the new v1.16.0 plant renders its fleet facts (sibling
  roster, dark repos, one-command orient) from hand-answered interview
  slots, so the sibling map is frozen at answer time and will silently
  drift as lanes are added/retired/archived; a small advisory checker (or
  a `gen_*.py`-style refresh) comparing the map's repo list against the
  generated `fleet-manager docs/roster.md` lane rows would flag drift the
  same way this repo already pins other cross-repo mirrors. Worth having
  because a stale "who is who" map misroutes every future cross-repo
  session, and this repo already owns the pattern (review/fleetdata
  roster-parse cron). Source:
  `.sessions/2026-07-14-kit-upgrade-v1.16.0.md` 💡.
