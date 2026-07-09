"""Control-plane site: readiness board + journal browser.

Auth: HTTP Basic on every route (any username, password = SITE_PASSWORD).
/healthz is the single unauthenticated route (Railway healthcheck).
"""

from __future__ import annotations

import base64
import secrets
from contextlib import asynccontextmanager
from pathlib import Path

import markdown as md
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.templating import Jinja2Templates

from . import config, github, journal, readiness


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = github.make_client()
    raw_client = github.make_raw_client()
    github.set_clients(client, raw_client)
    yield
    await client.aclose()
    await raw_client.aclose()


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def _authorized(request: Request) -> bool:
    if not config.SITE_PASSWORD:
        return False  # fail closed: unset password never means open door
    header = request.headers.get("authorization", "")
    if not header.lower().startswith("basic "):
        return False
    try:
        decoded = base64.b64decode(header.split(" ", 1)[1]).decode("utf-8")
        _user, _, password = decoded.partition(":")
    except Exception:
        return False
    return secrets.compare_digest(password, config.SITE_PASSWORD)


@app.middleware("http")
async def auth_gate(request: Request, call_next):
    if request.url.path == "/healthz":
        return await call_next(request)
    if not _authorized(request):
        detail = (
            "SITE_PASSWORD is not configured on the server."
            if not config.SITE_PASSWORD
            else "Authentication required."
        )
        return Response(
            content=detail,
            status_code=503 if not config.SITE_PASSWORD else 401,
            headers={"WWW-Authenticate": 'Basic realm="control-plane"'},
            media_type="text/plain",
        )
    return await call_next(request)


def _refresh(request: Request) -> bool:
    return request.query_params.get("refresh") in ("1", "true", "yes")


@app.get("/healthz")
async def healthz():
    return {"ok": True, "cache_entries": github.cache_size()}


@app.get("/", response_class=HTMLResponse)
async def board(request: Request):
    rows = await readiness.board(refresh=_refresh(request))
    return templates.TemplateResponse(
        request,
        "board.html",
        {
            "rows": rows,
            "ttl": config.CACHE_TTL_SECONDS,
            "active": "board",
        },
    )


@app.get("/api/readiness.json")
async def board_json(request: Request):
    return JSONResponse(await readiness.board(refresh=_refresh(request)))


@app.get("/journal", response_class=HTMLResponse)
async def journal_index(request: Request):
    repos = await journal.overview(refresh=_refresh(request))
    return templates.TemplateResponse(
        request, "journal.html", {"repos": repos, "active": "journal"}
    )


@app.get("/journal/{repo}", response_class=HTMLResponse)
async def journal_repo(request: Request, repo: str):
    if repo not in config.REPOS:
        return HTMLResponse("unknown repo", status_code=404)
    data = await journal.repo_journal(repo, refresh=_refresh(request))
    return templates.TemplateResponse(
        request, "journal_repo.html", {"j": data, "active": "journal"}
    )


@app.get("/journal/{repo}/file", response_class=HTMLResponse)
async def journal_file(request: Request, repo: str, path: str, ref: str = "main"):
    if repo not in config.REPOS:
        return HTMLResponse("unknown repo", status_code=404)
    if ".." in path or path.startswith("/"):
        return HTMLResponse("bad path", status_code=400)
    res = await github.fetch_file(repo, path, ref=ref, refresh=_refresh(request))
    body_html = ""
    if res["ok"] and isinstance(res["data"], str):
        if path.endswith((".md", ".markdown")):
            body_html = md.markdown(
                res["data"], extensions=["fenced_code", "tables"]
            )
        else:
            import html as _html

            body_html = f"<pre>{_html.escape(res['data'])}</pre>"
    return templates.TemplateResponse(
        request,
        "file.html",
        {
            "repo": repo,
            "path": path,
            "ref": ref,
            "res": res,
            "body_html": body_html,
            "github_url": f"https://github.com/{config.OWNER}/{repo}/blob/{ref}/{path}",
            "active": "journal",
        },
    )
