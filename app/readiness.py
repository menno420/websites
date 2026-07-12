"""Readiness board: per-repo signals, each shown as configured? AND working now?

Generalizes superbot's hand-maintained docs/operations/repo-settings-state.md
ledger into a live view. Every cell carries its own fetch result so a single
failing endpoint (e.g. secrets without admin scope) degrades that cell only.
"""

from __future__ import annotations

import asyncio
import re
from typing import Any

from . import config, github

OWNER = config.OWNER

CODEOWNERS_PATHS = [".github/CODEOWNERS", "CODEOWNERS", "docs/CODEOWNERS"]


def _gh(repo: str, tail: str = "") -> str:
    return f"https://github.com/{OWNER}/{repo}{tail}"


async def _codeowners(repo: str, refresh: bool) -> dict:
    for path in CODEOWNERS_PATHS:
        res = await github.repo_api(repo, f"/contents/{path}", refresh=refresh)
        if res["ok"]:
            return {"present": True, "path": path, "result": res}
        if res["status"] not in (404, 0):
            return {"present": None, "path": None, "result": res}
    return {"present": False, "path": None, "result": res}


async def _ruleset_details(repo: str, rulesets_res: dict, refresh: bool) -> list[dict]:
    """Fetch per-ruleset detail (rules incl. required_status_checks)."""
    details = []
    if not rulesets_res["ok"] or not isinstance(rulesets_res["data"], list):
        return details
    branch_rulesets = [
        r
        for r in rulesets_res["data"]
        if r.get("target") == "branch" and r.get("enforcement") == "active"
    ]
    fetched = await asyncio.gather(
        *[
            github.repo_api(repo, f"/rulesets/{r['id']}", refresh=refresh)
            for r in branch_rulesets
        ]
    )
    for res in fetched:
        if res["ok"] and isinstance(res["data"], dict):
            details.append(res["data"])
    return details


def _required_checks_from(rulesets: list[dict], protection: dict) -> list[str]:
    checks: list[str] = []
    for rs in rulesets:
        for rule in rs.get("rules", []) or []:
            if rule.get("type") == "required_status_checks":
                for c in (rule.get("parameters") or {}).get(
                    "required_status_checks", []
                ):
                    ctx = c.get("context")
                    if ctx and ctx not in checks:
                        checks.append(ctx)
    if protection.get("ok") and isinstance(protection.get("data"), dict):
        for ctx in (
            (protection["data"].get("required_status_checks") or {}).get("contexts")
            or []
        ):
            if ctx not in checks:
                checks.append(ctx)
    return checks


def _codeowner_review_required(rulesets: list[dict], protection: dict) -> bool | None:
    found = None
    for rs in rulesets:
        for rule in rs.get("rules", []) or []:
            if rule.get("type") == "pull_request":
                found = bool(
                    (rule.get("parameters") or {}).get(
                        "require_code_owner_review", False
                    )
                )
    if found is None and protection.get("ok") and isinstance(
        protection.get("data"), dict
    ):
        prr = protection["data"].get("required_pull_request_reviews") or {}
        if prr:
            found = bool(prr.get("require_code_owner_reviews", False))
    return found


def _match_run(name: str, runs: list[dict]) -> dict | None:
    """Match a required-check context to a live check run.

    Contexts look like 'Code Quality' (job name) or 'tests, ci' (job, workflow).
    """
    job = name.split(",")[0].strip()
    for r in runs:
        if r.get("name") == name or r.get("name") == job:
            return r
    for r in runs:
        rn = (r.get("name") or "").split(",")[0].strip()
        if rn == job:
            return r
    return None


def _run_state(run: dict | None) -> str:
    if run is None:
        return "missing"
    if run.get("status") != "completed":
        return run.get("status") or "pending"
    return run.get("conclusion") or "unknown"


async def _service_deploy_state(
    service: str, url: str | None, head_sha: str, refresh: bool
) -> dict:
    """One service's deploy state: its DEPLOYED short-sha vs the repo HEAD short-sha.

    control-plane (``url is None``) is THIS app — it knows its own deployed sha
    from the environment directly, no network. The others are queried over
    their public ``/version`` JSON through the shared TTL cache (raw client, no
    token). A failed fetch or an absent sha is reported as ``unknown`` honestly,
    never a crash or a faked value.
    """
    head_short = head_sha[:8] if head_sha else ""

    def _clean(val: str) -> str:
        # `/version` reports the literal "unknown" when no sha is set; treat that
        # (and empty) as "not known", not as a real short-sha to compare.
        return "" if val in ("", "unknown") else val

    if url is None:
        sha = config.deployed_sha()
        deployed_short = sha[:8] if sha else ""
        error = "" if deployed_short else "GIT_SHA / RAILWAY_GIT_COMMIT_SHA unset"
    else:
        res = await github._get(url, refresh=refresh, raw=True)
        if res["ok"] and isinstance(res["data"], dict):
            deployed_short = _clean(str(res["data"].get("short") or "")) or _clean(
                str(res["data"].get("sha") or "")
            )[:8]
            error = "" if deployed_short else "service reports unknown sha"
        else:
            deployed_short = ""
            error = f"HTTP {res['status']} {res['error']}".strip()

    known = bool(deployed_short)
    if not known or not head_short:
        state = "unknown"
    elif deployed_short == head_short:
        state = "in_sync"
    else:
        state = "drift"
    return {
        "service": service,
        "state": state,
        "deployed_short": deployed_short,
        "head_short": head_short,
        "known": known,
        "error": error,
    }


async def _deploy_board(head_sha: str, refresh: bool) -> dict:
    """Deploy-state summary for every websites Railway service.

    All four services (control-plane, botsite, dashboard, review) deploy from
    this repo's ``main`` on merge (Railway auto-deploy), so drift = a deploy
    in progress or a failed/stale deploy.
    """
    services = list(
        await asyncio.gather(
            *[
                _service_deploy_state(name, url, head_sha, refresh)
                for name, url in config.SERVICE_DEPLOY_TARGETS.items()
            ]
        )
    )
    any_drift = any(s["state"] == "drift" for s in services)
    known = [s for s in services if s["known"]]
    all_in_sync = bool(known) and all(s["state"] == "in_sync" for s in known)
    return {
        "head_short": head_sha[:8] if head_sha else "",
        "services": services,
        "any_drift": any_drift,
        "all_in_sync": all_in_sync,
    }


async def repo_readiness(
    repo: str, refresh: bool = False, reveal_secrets: bool = False
) -> dict[str, Any]:
    cfg = config.REPOS[repo]

    meta, rulesets_res, pulls_res, workflows_res, secrets_res, co = (
        await asyncio.gather(
            github.repo_api(repo, refresh=refresh),
            github.repo_api(repo, "/rulesets", refresh=refresh),
            github.repo_api(
                repo,
                "/pulls?state=open&per_page=100&sort=created&direction=asc",
                refresh=refresh,
            ),
            github.repo_api(repo, "/contents/.github/workflows", refresh=refresh),
            github.repo_api(repo, "/actions/secrets", refresh=refresh),
            _codeowners(repo, refresh),
        )
    )

    default_branch = "main"
    if meta["ok"] and isinstance(meta["data"], dict):
        default_branch = meta["data"].get("default_branch") or "main"

    protection, checkruns_res, rs_details = await asyncio.gather(
        github.repo_api(
            repo, f"/branches/{default_branch}/protection", refresh=refresh
        ),
        github.repo_api(
            repo, f"/commits/{default_branch}/check-runs?per_page=100", refresh=refresh
        ),
        _ruleset_details(repo, rulesets_res, refresh),
    )

    # --- live check runs on the main head ---
    runs: list[dict] = []
    head_sha = ""
    if checkruns_res["ok"] and isinstance(checkruns_res["data"], dict):
        runs = checkruns_res["data"].get("check_runs", []) or []
        if runs:
            head_sha = runs[0].get("head_sha", "") or ""
    red_by_design = cfg.get("red_by_design", {})

    # --- deploy-state drift (websites row only) ---
    # The three websites Railway services all deploy from this repo's `main`, so
    # the websites row shows whether each running service is on the latest merged
    # commit. Other repos have no such coupling → no deploy-state cell.
    deploy_state = None
    if repo == "websites":
        deploy_state = await _deploy_board(head_sha, refresh)

    def annotate(run: dict) -> dict:
        job = (run.get("name") or "").split(",")[0].strip()
        note = red_by_design.get(run.get("name")) or red_by_design.get(job) or ""
        state = _run_state(run)
        effective = state
        if note and state not in ("success", "neutral", "skipped"):
            effective = "red-by-design"
        return {
            "name": run.get("name"),
            "state": state,
            "effective": effective,
            "note": note,
            "url": run.get("html_url") or _gh(repo, f"/commits/{default_branch}"),
            "app": ((run.get("app") or {}).get("name") or ""),
        }

    live_runs = [annotate(r) for r in runs]
    broken_runs = [
        r
        for r in live_runs
        if r["effective"]
        in ("failure", "timed_out", "cancelled", "action_required", "startup_failure")
    ]

    # --- required checks: configured AND currently green ---
    required = _required_checks_from(rs_details, protection)
    required_rows = []
    for ctx in required:
        run = _match_run(ctx, runs)
        state = _run_state(run)
        job = ctx.split(",")[0].strip()
        note = red_by_design.get(ctx) or red_by_design.get(job) or ""
        required_rows.append(
            {
                "context": ctx,
                "state": state,
                "note": note,
                "url": (run or {}).get("html_url")
                or _gh(repo, f"/commits/{default_branch}"),
            }
        )

    rulesets_unknown = not rulesets_res["ok"]
    ruleset_names = (
        [
            f"{r.get('name')} ({r.get('enforcement')})"
            for r in rulesets_res["data"]
            if r.get("target") == "branch"
        ]
        if rulesets_res["ok"] and isinstance(rulesets_res["data"], list)
        else []
    )

    # --- CODEOWNERS enforced? ---
    co_required = _codeowner_review_required(rs_details, protection)

    # --- secrets ---
    # The PUBLIC board masks this to a COUNT only: the secret *names* are the one
    # non-public datum on an otherwise public-repo-derived board, so they are
    # never rendered or serialized on the public path (the original masking
    # decision). They ARE the point of the gated /owner area, so when
    # `reveal_secrets=True` (the authed path only) the names ride along in a
    # `names` key. Default False keeps the public output byte-identical.
    # Degrade on 403 (token lacks admin scope) like every other cell.
    if secrets_res["ok"] and isinstance(secrets_res["data"], dict):
        secret_names = [
            s.get("name") for s in secrets_res["data"].get("secrets", []) or []
        ]
        secret_count = len(secret_names)
        secrets_cell = {
            "known": True,
            "count": secret_count,
            "detail": f"{secret_count} secret(s)" if secret_count else "none",
        }
        if reveal_secrets:
            secrets_cell["names"] = secret_names
    else:
        reason = (
            "token lacks admin scope"
            if secrets_res["status"] in (403, 401)
            else f"HTTP {secrets_res['status']} {secrets_res['error']}".strip()
        )
        secrets_cell = {"known": False, "count": 0, "detail": f"unknown ({reason})"}

    # --- auto-merge ---
    allow_am = None
    if meta["ok"] and isinstance(meta["data"], dict):
        allow_am = meta["data"].get("allow_auto_merge")  # absent w/o push perm
    enabler_files = []
    if workflows_res["ok"] and isinstance(workflows_res["data"], list):
        enabler_files = [
            f.get("name")
            for f in workflows_res["data"]
            if re.search(r"auto.?merge", f.get("name") or "", re.I)
        ]

    # --- open PR health ---
    open_prs: list[dict] = (
        pulls_res["data"]
        if pulls_res["ok"] and isinstance(pulls_res["data"], list)
        else []
    )
    oldest = open_prs[0] if open_prs else None

    return {
        "repo": repo,
        "cfg": cfg,
        "github_url": _gh(repo),
        "default_branch": default_branch,
        "head_sha": head_sha,
        "deploy_state": deploy_state,
        "meta": meta,
        "visibility": (meta.get("data") or {}).get("visibility")
        if meta["ok"]
        else None,
        "rulesets": {
            "result": rulesets_res,
            "unknown": rulesets_unknown,
            "names": ruleset_names,
            "details": rs_details,
        },
        "protection": protection,
        "required_checks": {
            "configured": required,
            "expected": cfg.get("expected_required_checks", []),
            "rows": required_rows,
        },
        "live_runs": live_runs,
        "broken_runs": broken_runs,
        "checkruns_result": checkruns_res,
        "codeowners": {
            "present": co["present"],
            "path": co["path"],
            "enforced": co_required,
        },
        # NOTE: the raw secrets_res is deliberately NOT included — it carries the
        # secret names under data.secrets[].name, which must never reach the public
        # board HTML or /api/readiness.json. On the public path only the count is
        # in secrets_cell; the names ride along in secrets_cell["names"] ONLY when
        # the authed /owner path passed reveal_secrets=True.
        "secrets": {"status": secrets_res["status"], **secrets_cell},
        "auto_merge": {
            "allowed": allow_am,
            "enabler_files": enabler_files,
            "enabler_expected": cfg.get("automerge_enabler_expected", False),
            "workflows_result": workflows_res,
        },
        "prs": {
            "result": pulls_res,
            "open_count": len(open_prs),
            "capped": len(open_prs) == 100,
            "oldest": {
                "number": oldest.get("number"),
                "title": oldest.get("title"),
                "created_at": oldest.get("created_at"),
                "url": oldest.get("html_url"),
            }
            if oldest
            else None,
        },
    }


async def board(refresh: bool = False, reveal_secrets: bool = False) -> list[dict]:
    return list(
        await asyncio.gather(
            *[
                repo_readiness(r, refresh=refresh, reveal_secrets=reveal_secrets)
                for r in config.REPOS
            ]
        )
    )
