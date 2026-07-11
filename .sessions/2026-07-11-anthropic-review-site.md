# 2026-07-11 — Anthropic review site: fourth service (`review/`) telling the program's story

> **Status:** `in-progress` — branch `claude/anthropic-review-site`; flips to `complete`
> + PR number as the deliberate LAST code step.

- **📊 Model:** claude-fable-5 · worker · owner-directed build (full session goal, not a slice)

**What this session was about:** owner-directed (rung 1 equivalent — direct
owner order, not an inbox ORDER): "create a website specifically for anthropic
to review the way we have been running our projects, think of it like the
control plane website, but then with the sole purpose of giving a clear visual
explanation of the problems and successes as well as the process and the way
we managed to grow so quickly." Build a FOURTH independent service `review/`
following the exact botsite/dashboard pattern (own Dockerfile + requirements +
tests, server-rendered FastAPI + Jinja2, vendored `ds/`), rendering the real
repo record — git history, `.sessions/` cards, `docs/retro/`, `control/` —
for an outside (Anthropic) reviewer. Honest by design: the problems page
leads with real failures, mirroring the ORDER 011 retro.

## What was done

- <build in progress — this card flips complete with the full list>

## 💡 Session idea

- <captured at close-out>

## ⟲ Previous-session review

- <written at close-out>
