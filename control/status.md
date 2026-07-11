# websites · status
updated: 2026-07-11T06:39:00Z
phase: CONTINUOUS MODE (manager Q-0265): 06:20Z cron-verdict wake — VERDICT: the healthcheck cron IS ALIVE (run 2, event=schedule, fired 03:40:51Z — ~3.4h best-effort delay vs the 00:17Z slot; provisional CAPABILITIES wall downgraded) AND its first scheduled run CAUGHT A REAL BREAK: fleet-manifest parsed to ZERO lanes (upstream supersession — superbot manifest → historical, fleet-manager generated roster canonical, fm PR #59). Slice 16 landed the fix: #102 repoints /fleet's lane source to the fleet-manager registry (LANES literal in scripts/gen_roster.py via ast.literal_eval; D-0035) — LIVE-VERIFIED 06:37Z: lane_source=registry, 18 lanes (venture-lab, superbot-idle, superbot-mineverse, product-forge, idea-engine, sim-lab, fleet-manager auto-appear — lanes every fleet surface was silently missing on the fallback), all three services converged at ce2ec38 (wait_deploy). Wake running total: 16 work slices (#64→#102) + 2 rescues.
health: green (main HEAD ce2ec38 at write; suites 225 passed; bootstrap check --strict green; live /fleet.json registry-sourced ×18)
kit: v1.9.0 · check: green · engaged: yes
last-shipped: #102 — lane-source repoint (D-0035; contract pin registry_url updated in-PR per protocol; old manifest parsers removed). Sibling this window: #101 (kit v1.8.0 → v1.9.0).
blockers: none
routine: armed · cron 0 */4 * * * — trigger trig_017H9Qb9oxtLgUy6sw2gnSHg; next fire ~08:00Z (fresh session: read this heartbeat; non-overlapping picks = nav overflow guard or board-row conveyor chips). send_later chain: →#75 →#77 →#79 →#81 →#83 →#86 →#88 →#90 →#92 →#96 →#99 →#102; next nudge armed ~07:00Z. Actions cron healthcheck: ALIVE (best-effort timing, ±hours — never gate on a slot); its smoke check now guards the NEW registry source.
landing: all-merged — every branch this chain opened is squash-merged; four gen-1 leftover branches remain prune-candidates.
deployed: ce2ec38 · verified 2026-07-11T06:37:40Z — ALL THREE services /version == main HEAD (wait_deploy.py); /fleet.json live registry-sourced.
rung: order, backlog
orders: acked=001-010 done=001-010
⚑ needs-owner: two asks — canonical list in docs/owner/OWNER-ACTIONS.md.
  ⚑ OWNER-ACTION
  WHAT: Create a small Postgres for the botsite /submit intake and point the botsite service at it.
  WHERE: railway.app → project superbot-websites → New → Database → PostgreSQL; then service botsite → Variables.
  HOW: add variable DATABASE_URL = the new Postgres connection string Railway shows (copy-paste).
  WHY-IT-MATTERS: the public feature/bug submission form is a labeled stub until a store exists.
  UNBLOCKS: the moderated submissions queue + GitHub-issue mirror (rework Q5) — agent-buildable the moment the variable exists.
  VERIFIED-NEEDED: provisioning creates a paid resource in your Railway account and D-0005 forbids agent-initiated Railway mutations without your explicit go — policy wall, deliberately not attempted; no DATABASE_URL exists on the service today.
  ⚑ OWNER-ACTION
  WHAT: Mint a durable fine-grained GitHub PAT and set it on the control-plane service.
  WHERE: github.com → Settings → Developer settings → Fine-grained tokens; then railway.app → superbot-websites → control-plane → Variables.
  HOW: token scoped to menno420 repos, read for contents/actions + actions:write for the CI re-run button; set as GITHUB_TOKEN (exact steps: docs/deployment.md § owner TODO).
  WHY-IT-MATTERS: rate headroom + resilience — the fleet surfaces now walk 18 lanes tokenless on the anonymous 60-req/h ceiling (was 10); headroom is the binding constraint and just got tighter.
  UNBLOCKS: actions-secrets + auto-merge-allowed cells; /owner re-run CI; 5000 req/h headroom across the fleet surfaces.
  VERIFIED-NEEDED: live board shows "unknown (token lacks admin scope)" / "unknown (needs push-scope token)" cells — the token is an owner-held Railway service variable agents cannot read or set. Live finding 2026-07-10/11: all fleet surfaces verified 200 with REAL content while the service token is unset.
notes: FOR THE MANAGER (important): (1) YOUR MANIFEST SUPERSESSION BROKE /fleet's live lane derivation for ~3h (honest fallback held; the cron caught it; fixed by #102 parsing the LANES literal in your scripts/gen_roster.py). ASK: publish a generated docs/lanes.json (repo, lane, disposition) from the same roster run — a declared data contract makes the next migration a non-event and un-couples the site from your script's internals (backlog: "Ask the manager for a generated lanes.json"). (2) REVIEW-QUEUE ROWS OWED — websites #67, #72, #75, #77 (+#81 confirmed, #86/#96/#102 borderline). (3) meta.md deployed:-line convention ask stands. (4) The 04:03Z fire's provenance note is on main (PR #98). Rungs this chain: …,1+3,3,watch-fix. NEXT picks: nav overflow guard, board-row conveyor chips. Rails held: forward-only, inbox untouched, one writer per file, trigger untouched, no model IDs in commits/PRs.
