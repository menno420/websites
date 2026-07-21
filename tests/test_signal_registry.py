"""Schema + consumer-reachability guard for the committed signal registry.

``docs/signal-registry.json`` records every cross-repo signal this repo bakes or
mirrors into a ``*/data/*.json`` file and re-renders on sibling surfaces —
``name -> baker -> raw-URL -> consumers`` — so a new drift/parity fan-out is a
data edit there instead of a code hunt across the four services. This guard keeps
those rows HONEST: it validates the schema and then, generalising the
arcade<->web_presence join ``tests/test_registry_drift.py`` proves for one pair,
asserts every declared ``baker`` / ``committed_mirror`` / ``consumer`` path
actually resolves in the tree AND that each consumer file still references its
signal by the mirror basename. A row that lists a consumer which stopped
consuming the signal (or names a baker/mirror that moved) fails here.

Green now (every declared reference verified); red only when a row drifts from
the tree.
"""

import json
import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "docs" / "signal-registry.json"

# name, description, producer_repo, raw_url, consumers are always required and
# non-empty; baker and committed_mirror are nullable (cross-repo / PR-maintained).
_REQUIRED_STR = ("name", "description", "producer_repo", "raw_url")
_NULLABLE_PATH = ("baker", "committed_mirror")
_RAW_URL_RE = re.compile(r"^https://raw\.githubusercontent\.com/[\w.-]+/[\w.-]+/.+\.json$")


def _load() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def _signals() -> list:
    reg = _load()
    signals = reg.get("signals")
    assert isinstance(signals, list) and signals, "registry has no non-empty 'signals' list"
    return signals


def test_registry_is_valid_json_with_signals():
    reg = _load()
    assert isinstance(reg, dict), "registry root must be a JSON object"
    assert isinstance(reg.get("signals"), list) and reg["signals"], "non-empty 'signals' list required"


def test_row_schema_and_types():
    for row in _signals():
        assert isinstance(row, dict), f"each signal must be an object, got {type(row).__name__}"
        for key in _REQUIRED_STR:
            val = row.get(key)
            assert isinstance(val, str) and val.strip(), f"{row.get('name')!r}: '{key}' must be a non-empty string"
        for key in _NULLABLE_PATH:
            val = row.get(key)
            assert val is None or (isinstance(val, str) and val.strip()), (
                f"{row.get('name')!r}: '{key}' must be a non-empty string or null"
            )
        assert _RAW_URL_RE.match(row["raw_url"]), (
            f"{row['name']!r}: raw_url {row['raw_url']!r} is not a well-formed raw.githubusercontent .json URL"
        )
        consumers = row.get("consumers")
        assert isinstance(consumers, list) and consumers, f"{row['name']!r}: 'consumers' must be a non-empty list"
        for c in consumers:
            assert isinstance(c, dict), f"{row['name']!r}: each consumer must be an object"
            assert isinstance(c.get("path"), str) and c["path"].strip(), (
                f"{row['name']!r}: consumer 'path' must be a non-empty string"
            )
            assert isinstance(c.get("note"), str) and c["note"].strip(), (
                f"{row['name']!r}: consumer 'note' must be a non-empty string"
            )


def test_signal_names_are_unique():
    names = [row["name"] for row in _signals()]
    dupes = {n for n in names if names.count(n) > 1}
    assert not dupes, f"duplicate signal name(s): {sorted(dupes)}"


def test_raw_url_basename_matches_committed_mirror():
    # When the mirror lives in THIS repo, its basename must match the raw_url the
    # consumers fetch — otherwise the row points consumers at a different file.
    for row in _signals():
        mirror = row.get("committed_mirror")
        if mirror is None:
            continue
        assert os.path.basename(mirror) == os.path.basename(row["raw_url"]), (
            f"{row['name']!r}: committed_mirror {mirror!r} basename != raw_url basename"
        )


def test_baker_and_mirror_paths_exist_in_tree():
    for row in _signals():
        for key in _NULLABLE_PATH:
            rel = row.get(key)
            if rel is None:
                continue
            path = REPO_ROOT / rel
            assert path.is_file(), f"{row['name']!r}: {key} {rel!r} does not exist in the tree"


def test_every_consumer_is_reachable_and_references_the_signal():
    # The join generalisation: a declared consumer must (a) exist in the tree and
    # (b) actually reference the signal by its raw_url basename — so a consumer
    # that stopped consuming the signal fails this guard the way test_registry_
    # drift.py fails on arcade<->web_presence disagreement.
    for row in _signals():
        token = os.path.basename(row["raw_url"])
        for c in row["consumers"]:
            path = REPO_ROOT / c["path"]
            assert path.is_file(), f"{row['name']!r}: consumer {c['path']!r} does not exist in the tree"
            text = path.read_text(encoding="utf-8")
            assert token in text, (
                f"{row['name']!r}: consumer {c['path']!r} no longer references the signal "
                f"(expected basename {token!r} in the file)"
            )
