# websites — owner console steps

> **Status:** `owner-guidance` — the console-only steps for THIS repo, at a high
> level: **variable / secret NAMES only, never values.** Nothing here can be
> done by an agent — each is a click in the Railway or GitHub console. Canonical
> owner list: `docs/owner/OWNER-ACTIONS.md` (16 ⚑ asks); this is the curated
> console subset for the fresh start. **Agents: never write a secret value into
> this file or any committed file.**

## 1 · Set the control-plane `/owner` gate variable — Railway console

- **WHAT:** set the `SITE_PASSWORD` variable on the **control-plane** Railway
  service to a value of your choosing.
- **WHERE:** Railway → project `superbot-websites` → service **control-plane** →
  Variables.
- **HOW:** add the variable and type the value directly in the Railway console —
  the value never lives in git, in this repo, or in any agent context.
- **WHY IT MATTERS:** the public site is credential-free **by design** (see
  `docs/current-state.md`); the single gated corner is the `/owner` overlay
  (full-detail board + privileged actions). It is HTTP Basic, any username,
  gating **only** `/owner*`.
- **UNBLOCKS:** `/owner` returns 503 (fail-closed) until this is set; the public
  board, botsite, dashboard, and review all keep working regardless.
- **NOTE:** this gates `/owner` only — there is **no** site-wide password today
  (a site-wide gate would mean re-introducing the previously-removed auth
  middleware). Decide whether `/owner`-only is the intended scope.

## 2 · Provision `BAKE_PAT` for the nightly fleet-data bake — GitHub console

- **WHAT:** create a fine-grained GitHub PAT with pull-request write scope and
  store it as the **`BAKE_PAT`** Actions secret.
- **WHERE:** GitHub → repo **Settings → Secrets and variables → Actions** →
  New repository secret, name `BAKE_PAT`.
- **HOW:** paste the token in the GitHub console; it is never committed.
- **WHY IT MATTERS:** the scheduled `review-bake` workflow's bake PR is created
  with the ambient `GITHUB_TOKEN`, which gets no accepted required-check context
  (GitHub's recursion guard) — so the bake PRs (e.g. #359/#380) freeze as
  `mergeable_state=blocked` instead of self-merging.
- **UNBLOCKS:** hands-off nightly bake self-merge. **Only needed if the
  recreated project keeps the scheduled bake** — otherwise retire `review-bake.yml`
  (see `docs/NEXT-TASKS.md` → "Wind-down / retirement") and this step is moot.

## 3 · Remove the two orphan password variables — Railway console

- **WHAT:** delete the set-but-unused `SITE_PASSWORD` variable from the
  **dashboard** service; and either wire or remove the unwired `SITE_PASSWORD`
  planned on the **botsite** service.
- **WHERE:** Railway → project `superbot-websites` → services **dashboard** and
  **botsite** → Variables.
- **HOW:** delete the variable in the Railway console (dashboard); for botsite,
  decide wire-vs-remove — it is not read by any route today.
- **WHY IT MATTERS:** the dashboard reads no `SITE_PASSWORD` (public by design),
  so the variable is config drift; the botsite copy is planned-but-unwired.
- **UNBLOCKS:** clean, honest config — no variable that looks load-bearing but
  isn't. (Canonical: ASK-0009 dashboard delete; ASK-0006 botsite decision.)

---

*All values are entered by the owner directly in the Railway / GitHub console.
No secret value is ever written to this repo. Variable and secret **names**
(`SITE_PASSWORD`, `BAKE_PAT`, `GITHUB_TOKEN`, `RAILWAY_TOKEN`) are safe to name;
their values are not.*
