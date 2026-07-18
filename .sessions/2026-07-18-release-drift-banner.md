# 2026-07-18 — Baked release-drift banner in the review service (ORDER 033)

> **Status:** `in-progress` — branch `claude/release-drift-banner`; a bake-time
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

- **📊 Model:** [[fill:]]

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

[[fill:]]

## 💡 Session idea

[[fill:]]

## ⟲ Previous-session review

[[fill:]]
