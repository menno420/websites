# Dashboard auto-deploy trigger

The dashboard Railway service must have a GitHub push→deploy trigger
(`deploymentTriggers`: provider `github`, repo `menno420/websites`, branch `main`)
so that merges to `main` rebuild it automatically — the same trigger control-plane
and botsite carry.

On 2026-07-09 this trigger was found **missing** on the dashboard service (auto-deploy
`enabled:false`), which is why merges silently failed to redeploy the dashboard while the
other two services updated. It was restored non-destructively via the Railway API
(`deploymentTriggerCreate`). This file's first commit doubled as the live end-to-end proof
that the restored trigger fires on merge. See
`.sessions/2026-07-09-dashboard-autodeploy-fix.md`.
