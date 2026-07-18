# 2026-07-18 — Baked release-drift banner in the review service (ORDER 033)

> **Status:** `complete` — branch `claude/release-drift-banner`; a bake-time
> release-drift banner for the **review/** service. A new `review/gen_releases.py`
> bakes, per arcade game with a source repo, the release tag the committed
> `botsite/data/arcade.json` expects versus the live latest tag on that source
> repo (read over anonymous `git ls-remote --tags`, the same tokenless git
> transport `gen_fleet.py` uses because REST is proxy-walled in session
> containers) into a committed `review/data/releases.json`; a `fleetdata`-style
> loader, a `_base_ctx` flag, a fourth `base.html` banner block, and a
> `/releases.json` JSON sibling render the drift on every review page. Canonical
> case: `lumen-drift` expects `lumen-drift-v1.3` on `menno420/gba-homebrew`
> (blocked on ASK-0010, tag not yet published) → drift=true. Stdlib-only bake,
> fail-soft everywhere; no workflow edits (daily auto-rebake wiring rides the
> hub venue). GET/read-only routes only — the CSRF/same-origin floor is
> untouched. Born red; flips to `complete` on green.

- **📊 Model:** Opus 4.8 (family) · high effort · coordinator feature-build (orchestrated via worker subagents)

**What this session is about:** botsite must stay outbound-free at runtime, and
it literally cannot read `review/data/`. Following the review service's
established doctrine — bake cross-repo facts into committed `review/data/*.json`
at build time via a `gen_*.py`, render from that baked data — this session adds
a release-drift signal. "Release drift" = for each arcade game that names a
`source_repo`, the release tag the committed arcade registry expects (parsed from
the game's `blocker.owner_action` / `status_note` free text — arcade.json has no
structured tag field, and adding one would break the botsite schema-integrity
guard, so a regex reads the tag the loader itself never stores) versus the live
latest tag on that repo. The banner names each drifting game so a reviewer sees,
site-wide, which expected releases have not been published. Verdict A of
SIM-REQUEST #355 keeps botsite outbound-free by baking into review/data (which
only review/ can read), so the banner renders in the review service — a
decide-and-flag call the owner may veto.

⚑ Self-initiated: no — coordinator-dispatched (ORDER 033, SIM-REQUEST #355 verdict A).

## Close-out

**Evidence:**

- files touched this branch:
  - `review/gen_releases.py` — new stdlib-only bake: for each arcade game with a
    `source_repo`, parses the expected release tag out of the committed
    `botsite/data/arcade.json` free text (regex, since arcade.json has no
    structured tag field and adding one would trip the botsite schema-integrity
    guard) and compares it against the live latest tag on that repo, read over
    anonymous `git ls-remote --tags` (the tokenless git transport `gen_fleet.py`
    already uses because REST is proxy-walled in session containers). Writes the
    committed `review/data/releases.json`. Fail-soft throughout.
  - `review/data/releases.json` — baked in-session; canonical case `lumen-drift`
    expects `lumen-drift-v1.3` on `menno420/gba-homebrew` (ASK-0010, unpublished)
    → `drift=true`.
  - `review/app.py` — a `fleetdata`-style loader for `releases.json`, a
    `_base_ctx` flag, and a `/releases.json` JSON sibling route (GET / read-only).
  - `review/templates/base.html` — a fourth banner block rendering the drift on
    every review page, naming each drifting game.
  - tests (review/tests) covering the bake, loader, banner render, and the
    `pick_latest_tag` fallback path.
  - `control/status.md` — heartbeat `landing:` line rewritten to the
    classifiable `pushed-unmerged claude/release-drift-banner` form so
    `fleet.classify_landing` reads it as `kind="pushed"` (was free prose the
    classifier misread as `unknown`, failing
    `tests/test_own_heartbeat.py::test_optional_enriched_lines_parse_when_present`).
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q`
  — **1917 passed**, 0 failed (exit 0); `python3 bootstrap.py check --strict`
  green, the only red having been the DESIGNED born-red hold on this card,
  released at this flip.
- git: branch `claude/release-drift-banner`; commits `7f0beec` (born-red card),
  `47608c4` (baked banner), `a8483ac` (heartbeat ack), `4baa90f` (classifiable
  landing line), + this flip.

**Judgment:**

- Decisions made: (1) Verdict-A interpretation — botsite must stay outbound-free
  at runtime and literally cannot read `review/data/`, so the drift signal is
  baked into `review/data/*.json` and rendered by the **review** service, not
  botsite; a decide-and-flag call the owner may veto. (2) Baked `releases.json`
  in-session via `git ls-remote --tags` rather than REST (REST is proxy-walled
  in session containers). (3) Deferred the daily auto-rebake **workflow wiring**
  to the hub venue — deliberately NOT in this PR — so the ORDER 033 diff stays
  product-only.
- Next session should pick up: wire `python3 review/gen_releases.py` into
  `.github/workflows/review-bake.yml` so `review/data/releases.json` auto-rebakes
  daily (hands-off release-drift refresh) — rides the hub venue. Known NIT:
  `pick_latest_tag`'s all-tags fallback can surface an unrelated tag as a shared
  repo's `live_tag` when the version-prefixed match set is empty; it does not
  manifest in the current data and is deliberately covered by test, but a
  stricter repo-scoped filter would harden it.

## 💡 Session idea

**A published-Release REST cross-check in the review-bake job.**
`gen_releases.py` currently reads git tags over `git ls-remote --tags`, which
can't tell a bare tag from a *published GitHub Release*. In the review-bake
Actions job (where GITHUB_TOKEN is available), a `/repos/{repo}/releases/latest`
REST cross-check would let the banner distinguish 'tag pushed but no Release
published' from 'no tag at all' — the exact ASK-0010 state for lumen-drift —
falling back to the ls-remote result in session containers where REST is walled.

## ⟲ Previous-session review

`.sessions/2026-07-18-review-questions-nav.md` (R1) did well to pin its
reachability fix with two directly-asserting tests — extending
`test_nav_covers_all_sections` and adding `test_nav_surfaces_questions_ledger`,
which checks both the `/questions` NAV link and its own `aria-current="page"`
active state — so a regression on either the visibility or the active-state half
is caught rather than trusted; the one thing to watch is the new `Answer log`
NAV label sitting adjacent to the existing `Q&A` entry, two ledger-ish names in
the header a reviewer could still conflate.
