"""Preflight tests for the owner rerun-ci preview + pinned confirm
(2026-07-15, PR A of the launch-console pair).

Contract under test:

- GET /owner/actions/rerun-ci/preview (plain require_owner, read-only)
  resolves the newest failed run with refresh=True and renders its facts +
  a confirm form carrying the PINNED run id. It makes ZERO write calls.
- POST /owner/actions/rerun-ci REQUIRES the pinned run_id, re-resolves with
  refresh=True, and fires ONLY when the pin is still the newest failed run.
  Every mismatch (missing pin / run vanished / no longer failed / newer
  failed appeared / resolution failure) FAILS CLOSED: zero fires, honest
  banner naming what moved, preview re-rendered. It NEVER falls back to
  "whatever is newest failed now".
- After a real fire, a verification chip re-GETs the run (started /
  unexpected-status / honest-unknown on re-GET failure) and the result page
  omits the confirm form (no double-fire invite).
- The preview facts table names the JOBS the fire would re-run ("jobs that
  will re-run: quality (1 of 3 jobs)") from a read-only jobs listing —
  degrading honestly (never blocking the preview) when the listing fails.
- When the confirm pinned the failed jobs before firing, the chip verifies
  at the JOB level (each previously-failed job re-queued), falling back to
  the run-level check when the jobs listing is unavailable.
- GET /owner/actions/refresh/preview rides the same template ("N cache
  entries will drop"); the refresh POST contract itself is unchanged.
- The require_owner_action floor stays intact on the confirm; rate-limit
  buckets stay independent per route path.

All GitHub traffic is faked at the github._get / api_post / api_request
choke points, with every write recorded — the zero-write pins are asserted
against those recorders, never inferred.
"""

import base64
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import config, github, owner  # noqa: E402
from app.main import app  # noqa: E402

OWNER_PW = "test-owner-pw"
SAME_ORIGIN = "http://testserver"

RUN_42 = {
    "id": 42,
    "name": "quality",
    "display_title": "fix the gate",
    "head_branch": "main",
    "head_sha": "abc1234def5678",
    "created_at": "2026-07-15T10:00:00Z",
    "html_url": "https://github.example/run/42",
    "status": "completed",
    "conclusion": "failure",
}
RUN_77 = {
    "id": 77,
    "name": "quality",
    "display_title": "newer breakage",
    "head_branch": "main",
    "head_sha": "def5678abc1234",
    "created_at": "2026-07-15T12:00:00Z",
    "html_url": "https://github.example/run/77",
    "status": "completed",
    "conclusion": "failure",
}


JOB_FAILED = {"id": 901, "name": "quality", "status": "completed",
              "conclusion": "failure",
              "html_url": "https://github.example/job/901"}
JOB_OK = {"id": 902, "name": "lint", "status": "completed",
          "conclusion": "success",
          "html_url": "https://github.example/job/902"}
JOB_SKIPPED = {"id": 903, "name": "deploy", "status": "completed",
               "conclusion": "skipped",
               "html_url": "https://github.example/job/903"}
JOB_REQUEUED = {"id": 999, "name": "quality", "status": "queued",
                "conclusion": None,
                "html_url": "https://github.example/job/999"}


def _jobs_env(*jobs, total=None):
    return _env(data={"total_count": total if total is not None else len(jobs),
                      "jobs": list(jobs)})


def _basic(pw: str = OWNER_PW, user: str = "owner") -> dict:
    token = base64.b64encode(f"{user}:{pw}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def _action_headers() -> dict:
    return {**_basic(), "Origin": SAME_ORIGIN}


def _env(ok=True, status=200, data=None, error="", url="") -> dict:
    return {"ok": ok, "status": status, "data": data, "error": error,
            "fetched_at": "", "cached": False, "url": url}


class FakeGitHub:
    """Fake at github's own choke points, recording every call.

    - the failure LISTING (?status=failure) answers ``self.listing``
    - a run's JOBS listing (/actions/runs/{id}/jobs) answers
      ``self.jobs[id]`` — a single env, or a LIST of envs consumed in
      order (before-fire, after-fire; the last one sticks); 404 when
      absent (jobs unavailable — the degrade lane)
    - a single-run GET (/actions/runs/{id}) answers ``self.runs[id]``
      (404 when absent — a vanished run)
    - api_post records the path and answers ``self.post_result``
    - api_request always fails the test: nothing here may use it
    """

    def __init__(self):
        self.listing = _env(data={"workflow_runs": []})
        self.runs: dict = {}
        self.jobs: dict = {}
        self.post_result = _env(status=201, data={})
        self.posts: list = []
        self.get_urls: list = []
        self.listing_refresh: list = []

    def set_newest(self, run):
        self.listing = _env(data={"workflow_runs": [run] if run else []})

    def set_jobs(self, run_id, *envs):
        """One env = every jobs GET answers it; several = consumed in order
        (the last sticks)."""
        self.jobs[str(run_id)] = list(envs) if len(envs) > 1 else envs[0]

    async def _get(self, url, refresh=False, raw=False):
        self.get_urls.append(url)
        if "status=failure" in url:
            self.listing_refresh.append(refresh)
            return dict(self.listing)
        if "/jobs" in url:
            run_id = url.split("/actions/runs/")[1].split("/", 1)[0]
            hit = self.jobs.get(run_id)
            if isinstance(hit, list):
                hit = hit.pop(0) if len(hit) > 1 else hit[0]
            if hit is None:
                return _env(ok=False, status=404, error="Not Found", url=url)
            return dict(hit)
        run_id = url.rstrip("/").rsplit("/", 1)[-1]
        hit = self.runs.get(run_id)
        if hit is None:
            return _env(ok=False, status=404, error="Not Found", url=url)
        return dict(hit)

    async def api_post(self, path, json_body=None):
        self.posts.append(path)
        return dict(self.post_result)

    async def api_request(self, method, path, json_body=None, token=""):
        raise AssertionError(
            f"api_request({method} {path}) must never run in the preflight"
        )


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    owner.reset_rate_limits()
    yield
    owner.reset_rate_limits()


@pytest.fixture()
def fake(monkeypatch):
    fk = FakeGitHub()
    monkeypatch.setattr(config, "SITE_PASSWORD", OWNER_PW)
    monkeypatch.setattr(github, "_get", fk._get)
    monkeypatch.setattr(github, "api_post", fk.api_post)
    monkeypatch.setattr(github, "api_request", fk.api_request)
    return fk


@pytest.fixture()
def client(fake):
    with TestClient(app) as c:
        yield c


# --------------------------------------------------------------------------- #
# Preview — read-only resolution
# --------------------------------------------------------------------------- #
def test_preview_renders_resolved_run_facts(client, fake):
    fake.set_newest(RUN_42)
    r = client.get(
        "/owner/actions/rerun-ci/preview?repo=websites", headers=_basic()
    )
    assert r.status_code == 200
    assert "#42" in r.text
    assert "quality" in r.text
    assert "fix the gate" in r.text
    assert "abc1234d" in r.text                      # head sha, shortened
    assert "https://github.example/run/42" in r.text  # evidence link
    # the confirm form pins the id and posts to the existing route
    assert 'name="run_id" value="42"' in r.text
    assert 'name="repo" value="websites"' in r.text
    assert 'action="/owner/actions/rerun-ci"' in r.text


def test_preview_makes_zero_write_calls(client, fake):
    fake.set_newest(RUN_42)
    cache_before = github.cache_size()
    r = client.get(
        "/owner/actions/rerun-ci/preview?repo=websites", headers=_basic()
    )
    assert r.status_code == 200
    assert fake.posts == []                    # no api_post ever
    assert github.cache_size() == cache_before  # cache untouched


def test_preview_resolves_with_refresh_true(client, fake):
    """The pin is minted from a live listing, never the TTL cache."""
    fake.set_newest(RUN_42)
    client.get("/owner/actions/rerun-ci/preview?repo=websites", headers=_basic())
    assert fake.listing_refresh == [True]


def test_preview_no_failed_run_is_honest(client, fake):
    fake.set_newest(None)
    r = client.get(
        "/owner/actions/rerun-ci/preview?repo=websites", headers=_basic()
    )
    assert r.status_code == 200
    assert "nothing to re-run" in r.text
    assert 'name="run_id"' not in r.text  # no confirm form to fire


def test_preview_listing_failure_fails_closed(client, fake):
    fake.listing = _env(ok=False, status=0, error="offline test")
    r = client.get(
        "/owner/actions/rerun-ci/preview?repo=websites", headers=_basic()
    )
    assert r.status_code == 200
    assert "could not resolve" in r.text
    assert 'name="run_id"' not in r.text


def test_preview_unknown_repo_honest_200(client, fake):
    r = client.get(
        "/owner/actions/rerun-ci/preview?repo=not-a-repo", headers=_basic()
    )
    assert r.status_code == 200
    assert "unknown repo" in r.text
    assert 'name="run_id"' not in r.text
    assert fake.posts == []


def test_preview_requires_auth(client, fake):
    assert client.get("/owner/actions/rerun-ci/preview?repo=websites").status_code == 401
    assert client.get("/owner/actions/refresh/preview").status_code == 401


# --------------------------------------------------------------------------- #
# Preview — the "jobs that will re-run" facts row
# --------------------------------------------------------------------------- #
def test_preview_jobs_row_names_the_failed_subset(client, fake):
    fake.set_newest(RUN_42)
    fake.set_jobs(42, _jobs_env(JOB_FAILED, JOB_OK, JOB_SKIPPED))
    r = client.get(
        "/owner/actions/rerun-ci/preview?repo=websites", headers=_basic()
    )
    assert r.status_code == 200
    assert "jobs that will re-run" in r.text
    assert "quality (1 of 3 jobs)" in r.text
    assert fake.posts == []  # the jobs listing is read-only


def test_preview_jobs_row_degrades_honestly_never_blocks(client, fake):
    """A failed jobs listing degrades to an honest unknown row — the
    preview and its confirm form are unaffected."""
    fake.set_newest(RUN_42)  # no fake.jobs entry → the jobs GET answers 404
    r = client.get(
        "/owner/actions/rerun-ci/preview?repo=websites", headers=_basic()
    )
    assert r.status_code == 200
    assert "jobs that will re-run" in r.text
    assert "unknown — could not list jobs" in r.text
    assert 'name="run_id" value="42"' in r.text  # confirm still offered


def test_preview_jobs_row_zero_failed_is_honest(client, fake):
    fake.set_newest(RUN_42)
    fake.set_jobs(42, _jobs_env(JOB_OK, JOB_SKIPPED))
    r = client.get(
        "/owner/actions/rerun-ci/preview?repo=websites", headers=_basic()
    )
    assert r.status_code == 200
    assert "none listed as failed right now (0 of 2 jobs)" in r.text


# --------------------------------------------------------------------------- #
# Confirm — fires at the pinned id exactly
# --------------------------------------------------------------------------- #
def test_confirm_fires_at_pinned_run_id_exactly(client, fake):
    fake.set_newest(RUN_42)
    fake.runs["42"] = _env(data={"status": "queued",
                                 "html_url": RUN_42["html_url"]})
    r = client.post(
        "/owner/actions/rerun-ci",
        data={"repo": "websites", "run_id": "42"},
        headers=_action_headers(),
    )
    assert r.status_code == 200
    assert fake.posts == [
        "/repos/menno420/websites/actions/runs/42/rerun-failed-jobs"
    ]
    assert "re-ran failed jobs of run #42" in r.text
    # post-action verification chip: the rerun really started
    assert "rerun started — queued" in r.text
    # the result page must not invite a double-fire
    assert 'name="run_id"' not in r.text


def test_confirm_without_run_id_rejected_never_falls_back(client, fake):
    fake.set_newest(RUN_42)
    r = client.post(
        "/owner/actions/rerun-ci",
        data={"repo": "websites"},
        headers=_action_headers(),
    )
    assert r.status_code == 200
    assert fake.posts == []                       # ZERO fires
    assert "no pinned run id" in r.text
    # the fresh preview is re-rendered so the owner can pin and confirm
    assert 'name="run_id" value="42"' in r.text


def test_confirm_stale_pin_newer_failed_appeared(client, fake):
    fake.set_newest(RUN_77)  # newest failed moved past the pin
    fake.runs["42"] = _env(data={"status": "completed",
                                 "conclusion": "failure",
                                 "html_url": RUN_42["html_url"]})
    r = client.post(
        "/owner/actions/rerun-ci",
        data={"repo": "websites", "run_id": "42"},
        headers=_action_headers(),
    )
    assert r.status_code == 200
    assert fake.posts == []
    assert "nothing fired" in r.text
    assert "newer failed run (#77)" in r.text
    # the re-preview pins what is newest NOW
    assert 'name="run_id" value="77"' in r.text


def test_confirm_stale_pin_run_vanished(client, fake):
    fake.set_newest(None)
    # no fake.runs entry for 42 → the re-check GET answers 404
    r = client.post(
        "/owner/actions/rerun-ci",
        data={"repo": "websites", "run_id": "42"},
        headers=_action_headers(),
    )
    assert r.status_code == 200
    assert fake.posts == []
    assert "nothing fired" in r.text
    assert "no longer exists" in r.text


def test_confirm_stale_pin_no_longer_failed(client, fake):
    fake.set_newest(None)
    fake.runs["42"] = _env(data={"status": "completed",
                                 "conclusion": "success",
                                 "html_url": RUN_42["html_url"]})
    r = client.post(
        "/owner/actions/rerun-ci",
        data={"repo": "websites", "run_id": "42"},
        headers=_action_headers(),
    )
    assert r.status_code == 200
    assert fake.posts == []
    assert "nothing fired" in r.text
    assert "no longer failed (now success)" in r.text


def test_confirm_resolution_failure_fails_closed(client, fake):
    fake.listing = _env(ok=False, status=0, error="offline test")
    r = client.post(
        "/owner/actions/rerun-ci",
        data={"repo": "websites", "run_id": "42"},
        headers=_action_headers(),
    )
    assert r.status_code == 200
    assert fake.posts == []
    assert "could not re-verify the pinned run #42" in r.text


def test_confirm_fire_rejected_is_honest(client, fake):
    fake.set_newest(RUN_42)
    fake.post_result = _env(ok=False, status=403, error="Forbidden")
    r = client.post(
        "/owner/actions/rerun-ci",
        data={"repo": "websites", "run_id": "42"},
        headers=_action_headers(),
    )
    assert r.status_code == 200
    assert len(fake.posts) == 1  # the fire was attempted, once
    assert "re-run rejected for run #42" in r.text
    assert "actions:write" in r.text


# --------------------------------------------------------------------------- #
# Post-fire verification chip
# --------------------------------------------------------------------------- #
def test_post_fire_chip_honest_unknown_when_reget_fails(client, fake):
    fake.set_newest(RUN_42)
    fake.runs["42"] = _env(ok=False, status=0, error="offline test")
    r = client.post(
        "/owner/actions/rerun-ci",
        data={"repo": "websites", "run_id": "42"},
        headers=_action_headers(),
    )
    assert r.status_code == 200
    assert fake.posts == [
        "/repos/menno420/websites/actions/runs/42/rerun-failed-jobs"
    ]
    assert "rerun not verified" in r.text
    assert "outcome unknown" in r.text


def test_post_fire_chip_verifies_jobs_requeued(client, fake):
    """Job-level verification: the previously-failed job reports queued on
    the post-fire jobs re-GET — the chip names it precisely."""
    fake.set_newest(RUN_42)
    fake.set_jobs(
        42,
        _jobs_env(JOB_FAILED, JOB_OK, JOB_SKIPPED),   # before the fire
        _jobs_env(JOB_REQUEUED, JOB_OK, JOB_SKIPPED),  # after the fire
    )
    r = client.post(
        "/owner/actions/rerun-ci",
        data={"repo": "websites", "run_id": "42"},
        headers=_action_headers(),
    )
    assert r.status_code == 200
    assert fake.posts == [
        "/repos/menno420/websites/actions/runs/42/rerun-failed-jobs"
    ]
    assert "failed jobs re-queued" in r.text
    assert "quality: queued" in r.text
    assert 'name="run_id"' not in r.text  # still no double-fire invite


def test_post_fire_chip_warns_when_jobs_not_requeued_yet(client, fake):
    """The after-listing still shows the job failed (a fresh attempt can lag)
    — honest warn naming the job's current status, never an assumed
    success."""
    fake.set_newest(RUN_42)
    fake.set_jobs(42, _jobs_env(JOB_FAILED, JOB_OK, JOB_SKIPPED))
    r = client.post(
        "/owner/actions/rerun-ci",
        data={"repo": "websites", "run_id": "42"},
        headers=_action_headers(),
    )
    assert r.status_code == 200
    assert "failed jobs not all re-queued yet" in r.text
    assert "quality: completed" in r.text


def test_post_fire_chip_falls_back_to_run_level_when_jobs_reget_fails(
    client, fake
):
    """Jobs pinned before the fire but the after re-GET fails — the chip
    falls back to the original run-level check."""
    fake.set_newest(RUN_42)
    fake.set_jobs(
        42,
        _jobs_env(JOB_FAILED, JOB_OK, JOB_SKIPPED),
        _env(ok=False, status=0, error="offline test"),
    )
    fake.runs["42"] = _env(data={"status": "queued",
                                 "html_url": RUN_42["html_url"]})
    r = client.post(
        "/owner/actions/rerun-ci",
        data={"repo": "websites", "run_id": "42"},
        headers=_action_headers(),
    )
    assert r.status_code == 200
    assert "rerun started — queued" in r.text


def test_post_fire_chip_warns_on_unexpected_status(client, fake):
    fake.set_newest(RUN_42)
    fake.runs["42"] = _env(data={"status": "completed",
                                 "conclusion": "failure",
                                 "html_url": RUN_42["html_url"]})
    r = client.post(
        "/owner/actions/rerun-ci",
        data={"repo": "websites", "run_id": "42"},
        headers=_action_headers(),
    )
    assert r.status_code == 200
    assert "run status: completed" in r.text


# --------------------------------------------------------------------------- #
# Gate floor — unchanged on the confirm, auth-only on the read previews
# --------------------------------------------------------------------------- #
def test_confirm_gate_floor_intact(client, fake):
    fake.set_newest(RUN_42)
    # auth precedes everything
    assert client.post(
        "/owner/actions/rerun-ci", data={"repo": "websites", "run_id": "42"}
    ).status_code == 401
    # strict same-origin still enforced
    r = client.post(
        "/owner/actions/rerun-ci",
        data={"repo": "websites", "run_id": "42"},
        headers={**_basic(), "Origin": "https://evil.example"},
    )
    assert r.status_code == 403
    assert fake.posts == []


def test_confirm_rate_limit_bucket_independent(client, fake):
    """Tripping the confirm bucket blocks only the confirm route — the
    preview GET and the refresh POST (their own paths) stay live."""
    fake.set_newest(None)  # every confirm fails closed cheaply (no fires)
    for _ in range(owner.RATE_LIMIT_MAX_REQUESTS):
        assert client.post(
            "/owner/actions/rerun-ci",
            data={"repo": "websites", "run_id": "42"},
            headers=_action_headers(),
        ).status_code == 200
    tripped = client.post(
        "/owner/actions/rerun-ci",
        data={"repo": "websites", "run_id": "42"},
        headers=_action_headers(),
    )
    assert tripped.status_code == 429
    assert fake.posts == []
    # independent buckets: the preview GET and refresh POST still answer
    assert client.get(
        "/owner/actions/rerun-ci/preview?repo=websites", headers=_basic()
    ).status_code == 200
    assert client.post(
        "/owner/actions/refresh", headers=_action_headers()
    ).status_code == 200


# --------------------------------------------------------------------------- #
# Refresh preview — the cheap uniform ride on the same template
# --------------------------------------------------------------------------- #
def test_refresh_preview_facts(client, fake, monkeypatch):
    monkeypatch.setattr(github, "cache_size", lambda: 7)
    r = client.get("/owner/actions/refresh/preview", headers=_basic())
    assert r.status_code == 200
    assert "cache entries that will drop" in r.text
    assert "clear the cache now (7 entries)" in r.text
    assert 'action="/owner/actions/refresh"' in r.text
    assert fake.posts == []  # read-only, like every preview


def test_refresh_post_contract_unchanged(client, fake, monkeypatch):
    """The preview is additive: the direct POST keeps answering exactly as
    the ORDER 013 suite pins it (no new required fields, same banner)."""
    monkeypatch.setattr(github, "clear_cache", lambda: 3)
    r = client.post("/owner/actions/refresh", headers=_action_headers())
    assert r.status_code == 200
    assert "cache cleared" in r.text


def test_owner_board_routes_rerun_through_preview(client, fake):
    """The board's rerun form GETs the preflight — the blind direct-fire
    form is gone."""
    r = client.get("/owner", headers=_basic())
    assert r.status_code == 200
    assert 'action="/owner/actions/rerun-ci/preview"' in r.text
    assert 'method="post" action="/owner/actions/rerun-ci"' not in r.text
