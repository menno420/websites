# 2026-07-09 — substrate-kit upgrade v1.0.0 → v1.2.0 + engagement audit

> **Status:** `in-progress`
>
> 📊 **Model:** claude-fable-5

## What I'm about to do

Upgrade the vendored `bootstrap.py` from kit v1.0.0 to the just-released
v1.2.0 (sha256-verified against the release's `release.json`) via the kit's
§4.3 `upgrade` verb — archive-first, hash-classified doc report, staged
artifacts regenerated. Then walk the new release's engagement/coordination
surface: run `check --strict` before/after, fix any new findings (the KL-7
engagement gate + the KL-8 `control/status.md` heartbeat checker are new
since our vendored version), port the v1.2.0 **control fast lane** into our
single enforced `quality` gate, write a fresh status heartbeat, and close
with the full app test suite green.

Also on the docket: honest inventory against the stale fleet-review claim
that this repo is still "stranded" (it is not — PRs #16/#19/#20 rendered the
docs, wired CI, and engaged the session loop; this card records the evidence).
