# 2026-07-12 — envhub: completeness chips on the environments-hub group headers

> **Status:** `in-progress`

- **📊 Model:** Claude Fable 5 · worker · feature-slice

**What this session is about:** the hub (`/owner/environments-hub`) links
each group's create-complete-environment manifest but gives no hint which
environment is unfinished — the completeness checklist (PR #216) is one
click deep per group, while the hub index is where the owner actually
decides where to spend the next console visit. This session promotes the
captured backlog bullet "Completeness chip on the environments-hub group
headers" (`docs/ideas/backlog.md`, source
`.sessions/2026-07-12-envhub-completeness-diff.md` 💡): reuse
`envhub.annotate_completeness` to compute a per-group summary from the SAME
cached `railway.live_overview` read the page already makes (zero new
network calls) and render it as a chip beside each group's manifest link —
"X/Y set live" (green when complete, amber otherwise) or the honest
"live status unknown" WITH the reason whenever the live truth is not
knowable — never a fabricated 0/Y.

## What was done

- [[fill: completed at flip]]

**Decisions made:** [[fill: completed at flip]]

⚑ Self-initiated: no — coordinator-assigned slice executing an existing
backlog bullet.

## 💡 Session idea

[[fill: exactly one genuine idea, deduped against docs/ideas/backlog.md]]

## ⟲ Previous-session review

[[fill: completed at flip]]
