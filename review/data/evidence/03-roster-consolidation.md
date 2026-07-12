# Fleet seats — roster + consolidation story

> Provenance: superbot `docs/owner/fleet-8seat-structure-2026-07-11.md` @
> `95fc025bb56d0901940ccd5a9b6184a2d8a813de`; fleet-manager PR #88 commit
> `639b0f09d7e99056cb8be83abc733edc198f1728` (2026-07-12T03:15:10Z);
> fleet-manager `docs/roster.md` @ `10fc4f7a95c3ca2be96eac7017dbb2fdb3e6a172`
> (GENERATED, gen #13, 2026-07-12T08:13Z); fleet-manager
> `docs/research/2026-07-12-staleness-sweep-8seat.md` @
> `4111da44ae218bb37442ad958d740b782b1c859a`.

## The 8 standing seats (from `95fc025`)

| # | Seat | Repos | One job |
|---|---|---|---|
| 1 | Project Manager | fleet-manager | Hub — single source of truth; routes work; keeps records truthful |
| 2 | Venture Lab | venture-lab · trading-strategy | Make money; trading = research toolkit only (holdout spent) |
| 3 | SuperBot World | superbot-games · superbot-idle · superbot-mineverse | The bot's games |
| 4 | SuperBot 2.0 | superbot-next · superbot (prod) | Drive the rebuild to cutover; keep prod alive |
| 5 | Ideas Lab | idea-engine · sim-lab | Generate → verify; honest nulls are the product |
| 6 | Game Lab | gba-homebrew · pokemon-mod-lab | Standalone games; strict public/private isolation |
| 7 | Self Improvement | substrate-kit | Improve the workflow all seats run on |
| 8 | Websites | websites | Control plane; merge = deploy |

Retired/folded (same doc): codetool-lab ×3 (archived), mobile-lab (parked),
games-program + superbot-retro (folded into the game seats), product-forge
(on-demand incubator awaiting owner disposition).

Key structural decisions: the money merge (venture-lab + trading-strategy =
one seat), and TWO game seats split by SuperBot-economy coupling (mineverse
sits in SuperBot World because it reads the bot's mining economy).

## Consolidation story ("peaked ~15 → 8")

- **Peak (~15 Projects):** best evidence is fig-01 ("Projects grid (14+
  tiles) … ~15 Projects, each its own repo"; screenshots index @ `e3eb0eb`).
  The 07-11 night review (@ `e1090db`) surveys 13 active lanes +
  fleet-manager. The sent email says "~15 Projects". **No exact machine
  count of 15 exists — say "~15", anchored to fig-01 and the night-review
  lane table, never an exact 15.**
- **Consolidation:** decided late 2026-07-11 (`95fc025`); canonicalized in
  fleet-manager 2026-07-12T03:15Z (`639b0f0` et seq.). Fig-21
  (`screenshots-2026-07-12/fig-21-eight-seat-projects-grid.jpg` @ `cbb5495`)
  is the "after" screenshot — the email pairs fig-01/fig-21 as before/after.
- Generations framing (sent email @ `8558179`): gen-1 (10 Projects, one day,
  deliberate wind-down) → gen-2 (overnight relaunch; the "116 PRs across 13
  repos in ~6 hours" figure is the email's claim — attribute, don't assert)
  → gen-3 ("the scale experiment ended, the standing program began").
  A verified intermediate data point: 2026-07-09 was "the fleet's first full
  day at 10 Projects" across 9 public repos (external review pack @ `b0e9ab2`).

## Heartbeat / trigger data (roster gen #13, 2026-07-12T08:13Z @ `10fc4f7`)

Notable per-lane heartbeats at generation time: superbot-next FRESH
(07:55Z), idea-engine FRESH (08:11Z), sim-lab 03:25Z, venture-lab 00:26Z
(ACTIVE — money seat), websites 2026-07-11T19:49Z (CLOSING — parked by
owner archive-prep order), trading-strategy ARCHIVE-READY,
pokemon-mod-lab NOT MEASURED (auth wall — private repo).

Trigger evidence in the same roster: "783-record export, **15 enabled**:
7 standing crons + 1 poke-only + 7 one-shots." The wake-state column
preserves the incident signature (kit-lab loop "last never · next
2026-07-12T06:08"; venture-lab failsafe "last 02:07:24").

**Caveat:** gen #13 was generated at 08:13Z, mid-incident — its STALE
verdicts partly reflect the scheduler outage itself. The seat-level sweep
(@ `4111da4`, run ~04:00–05:00Z) rated 7 of 8 seats FRESH with only
superbot-world STALE (its games heartbeat was contradicted: 5 "parked" PRs
had actually merged). Per-seat states as of ~08:45Z are the night-review §2
table (@ `8558179`): manager green, superbot-2.0 yellow, Ideas Lab green
idle, Venture Lab red/dark, Self Improvement re-fired, SuperBot World
yellow, Game Lab yellow, Websites parked (intentional).
