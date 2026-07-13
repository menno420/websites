# Session logs

Per-session logs live here as `<date>-<slug>.md`, newest first. Create the log as the session's FIRST commit with a born-red status (`> **Status:** `in-progress``) so in-flight work is visible to parallel sessions, then flip it to `complete` as the deliberate LAST step once the close-out is written — a half-done session never reads as finished. Before it counts as complete, a log must carry these markers: Status badge, Model line, Session idea, Previous-session review.

## Card template (copy-paste, then fill)

Start every card from this template. Its four markers are the exact needles
`bootstrap.py check --strict` scans for (`substrate.config.json` →
`session_markers`: `**Status:**`, `📊 Model:`, `💡`, `previous-session
review`) — the required `quality` gate fails the PR while any is missing or
the Status value is still in-progress.

The template lives HERE inside the README **on purpose**: the session gate
treats every other `.sessions/*.md` as a session card (`bootstrap.py`
`latest_session_log` skips only `README.md`, and `quality.yml` derives the
PR's card from any `.sessions/*.md` in the diff except `README.md`), so a
standalone `TEMPLATE.md` file would itself be picked up as a born-red card.
Do not add one.

````markdown
# YYYY-MM-DD — <what this session is about, one line>

> **Status:** `in-progress` — branch `claude/<slug>`; flips to `complete`
> + PR number as the deliberate LAST code step.

- **📊 Model:** <family only, e.g. Claude Fable 5> · <effort or role> · <task-class>

**What this session was about:** <the goal; which work-ladder rung fired
(order / queue-state NEXT / backlog promotion / self-initiated / upkeep)
and why that rung — cite the order id, NEXT item, or backlog bullet>

## What was done

- <each change, with file paths and the load-bearing specifics>
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests -q` —
  <N passed>; `python3 bootstrap.py check --strict` — <verdict>.

⚑ Self-initiated: <no — <order/NEXT/backlog source>, OR yes — one line on
why it is contained + reversible>

## 💡 Session idea

**<idea title>** — <what it is, one or two sentences>. Worth having
because <one line — REQUIRED; the idea does not count without its why>.
Deduped against `docs/ideas/backlog.md` + the queue-state NEXT list:
<result>. Captured in `docs/ideas/backlog.md`. <If genuinely no idea this
session: say so here and why — honest "nothing" beats forced filler.>

## ⟲ Previous-session review

<one line: what the last wake/session did well and what it missed>
````

## Ender checklist (run before flipping `complete`)

- [ ] Status flipped to `complete` + PR number as the LAST code step — never earlier in the session.
- [ ] `📊 Model:` line filled at FAMILY level only (e.g. `Claude Fable 5`, `Claude Opus 4.8`) — never a snapshot/full model ID, and model IDs never go in commit messages or PR bodies either. The value is the family-level model name **your own harness/environment reports this session** — the committed card's self-report is the attribution ground truth; never copy it from an external surface (schedule/Routines screens are evidenced to misattribute).
- [ ] 💡 Session idea carries its one-line "worth having because", is deduped against `docs/ideas/backlog.md`, and is captured there (bullet, or bullet + `docs/ideas/<slug>-<date>.md` file).
- [ ] ⟲ Previous-session review written (one line, well/missed).
- [ ] Real verification output summarized under "What was done" (actual test count + check verdict, not "should pass").
- [ ] No `[[fill:` placeholder left anywhere on the card (unresolved fills keep the card red under `--strict`).
- [ ] Heartbeat `control/status.md` overwrite queued as the session's FINAL step (after the merge; a `control/**`-only diff rides the fast lane and needs no card).

<!-- substrate-kit: model-attribution doctrine (family-level names — ORDER 012) -->
The `📊 Model:` model segment is the **family-level model name your own harness/environment reports this session** (e.g. `fable-5`, `opus-4.8`, `sonnet-5`) — the committed card's self-report is the attribution ground truth. Never copy it from an external surface (schedule/Routines screens are evidenced to misattribute), and never record a full dated model ID — family-level names only.
