# Merge-automation verification probe

> **Status:** `reference` — one-shot verification artifact for the 2026-07-15
> merge-on-green audit; safe to delete once verification is confirmed.

This file was created on 2026-07-15 as a merge-automation verification probe.

It is a plain, inert content-only change (no `.github/workflows/**` touched) used to confirm,
end-to-end with a real PR, that ordinary code/doc PRs in this repo land on green CI with zero
human click via the repo's existing native auto-merge mechanism
(`.github/workflows/auto-merge-enabler.yml` + `.github/workflows/host-automerge-extras.yml`).

Linked from [docs/audits/README.md](audits/README.md) to satisfy the docs-reachability check.

Safe to delete at any time after verification is confirmed.
