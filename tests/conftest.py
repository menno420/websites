"""Suite-level ambient-token pin — env independence as structure, not discipline.

The control-plane snapshots ``GITHUB_TOKEN``/``RAILWAY_TOKEN`` into
``app.config`` at import time, and ``app/writeback.py`` re-reads the env per
attempt. Whether the RUNNER exports those vars therefore used to leak into
test meaning: an unpinned reason assertion could exercise a different rung
of the degradation ladder locally (this dev container proxy-injects a
GITHUB_TOKEN) than in CI (which may export none) and pass on BOTH rungs
without pinning either — the flake class PR #250 flagged and PR #251 closed
per-test. This fixture closes it structurally (ORDER 027 item 5;
``docs/ideas/backlog.md`` "Suite-level token pin").

The pinned state is the UNSET rung — ``config.GITHUB_TOKEN``/
``config.RAILWAY_TOKEN`` forced to ``""`` and both env vars deleted — because
it matches CI and the documented production default for ``RAILWAY_TOKEN``,
and it is the state every existing not-configured assertion already expects.
Tests that need a token keep opting in explicitly exactly as they do today
(``monkeypatch.setattr(config, "GITHUB_TOKEN", "tok")`` /
``monkeypatch.setenv(writeback.ENV_TOKEN, ...)``): test-level patches apply
after this fixture's setup, so they always win.

A private ``pytest.MonkeyPatch`` instance is used instead of the function
``monkeypatch`` fixture on purpose: tests that call ``monkeypatch.undo()``
mid-test (``test_env_parse_hardening.test_import_survives_hostile_env``)
must not tear down the suite pin with their own patches.

Only ``tests/`` (control-plane) carries this pin: the botsite/dashboard
suites reference neither token, and review's only runtime read
(``review/gen_questions.py``, baker-side) is stubbed at the ``fetch_issues``
seam in its tests — no assertion there can flip on the ambient env.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import config  # noqa: E402


@pytest.fixture(autouse=True)
def _pin_ambient_tokens():
    """Every test starts on the unset rung, regardless of the runner's env."""
    mp = pytest.MonkeyPatch()
    mp.setattr(config, "GITHUB_TOKEN", "")
    mp.setattr(config, "RAILWAY_TOKEN", "")
    mp.delenv("GITHUB_TOKEN", raising=False)
    mp.delenv("RAILWAY_TOKEN", raising=False)
    yield
    mp.undo()
