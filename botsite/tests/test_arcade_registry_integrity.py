"""Data-integrity guard for the committed botsite blocker registries.

Every botsite registry that can carry the shared ``blocker`` object
(``arcade.json``, ``catalog.json``, ``products.json`` and the ``editions``
of ``puddle_museum.json``) feeds the owner-console + arcade surfaces:
availability summaries, the "unblocks N cards" owner-click count
(``arcade.availability_summary``) and the verification chips that join a
public blocker panel to the owner-actions ledger by ``ask_id``
(shipped across #368 / #369 / #371).

Every loader is deliberately **fail-soft**: a malformed ``blocker`` (empty
``owner_action``, a bad ``ask_id``) does not crash — it silently normalizes
to ``None`` (``botsite/blockers.py``). That is the right runtime behaviour,
but it means bad *committed* data fails **silently**: a blocker panel or an
owner-click count just quietly disappears. This guard turns that silent-loss
failure mode into a loud CI failure by asserting the committed JSON is
well-formed, using the shipped schema as the single source of truth
(``blockers.ASK_ID_RE`` / ``blockers.normalized_blocker`` — imported, never
re-stated). It is READ-ONLY: it never writes or mutates the registries.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterator

import pytest

from botsite import arcade, blockers, catalog, products, puddle_museum

# Repo root: botsite/tests/ -> botsite/ -> <repo>.
REPO_ROOT = Path(__file__).resolve().parents[2]
LEDGER_PATH = REPO_ROOT / "docs" / "owner" / "OWNER-ACTIONS.md"

# The canonical ``ID: ASK-NNNN`` marker line under each ⚑ ask block in the
# owner-actions ledger (docs/owner/OWNER-ACTIONS.md) — one per ask,
# append-only. This anchors the orphan-reference guard on the ledger's own
# stated id convention rather than on incidental ASK-NNNN mentions in prose.
_LEDGER_ID_LINE = re.compile(r"^ID:\s*(ASK-\d{4})\s*$", re.MULTILINE)


class _Registry:
    """One committed registry file plus how to read its blocker-bearing rows.

    ``entries`` yields ``(identity, entry_dict)`` for the rows that may carry
    a ``blocker``; ``identity_groups`` yields ``(key_name, [identity, ...])``
    for the duplicate-key guard (an edition registry keys editions and
    exhibits on different fields, so it reports more than one group).
    """

    def __init__(self, name: str, path: Path):
        self.name = name
        self.path = path
        self._raw = json.loads(path.read_text(encoding="utf-8"))

    def entries(self) -> Iterator[tuple[str, dict[str, Any]]]:
        raise NotImplementedError

    def identity_groups(self) -> Iterator[tuple[str, list[str]]]:
        raise NotImplementedError


class _ListRegistry(_Registry):
    """A registry that is a flat JSON list of entries keyed on ``slug``."""

    def entries(self) -> Iterator[tuple[str, dict[str, Any]]]:
        for entry in self._raw:
            if isinstance(entry, dict):
                yield str(entry.get("slug")), entry

    def identity_groups(self) -> Iterator[tuple[str, list[str]]]:
        yield "slug", [str(e.get("slug")) for e in self._raw if isinstance(e, dict)]


class _MuseumRegistry(_Registry):
    """The museum registry: a dict of ``exhibits`` + ``editions``; only the
    editions carry blockers. Editions key on ``lang``, exhibits on ``slug``."""

    def entries(self) -> Iterator[tuple[str, dict[str, Any]]]:
        for edition in self._raw.get("editions") or []:
            if isinstance(edition, dict):
                yield str(edition.get("lang")), edition

    def identity_groups(self) -> Iterator[tuple[str, list[str]]]:
        yield "edition lang", [
            str(e.get("lang")) for e in self._raw.get("editions") or [] if isinstance(e, dict)
        ]
        yield "exhibit slug", [
            str(e.get("slug")) for e in self._raw.get("exhibits") or [] if isinstance(e, dict)
        ]


def _registries() -> list[_Registry]:
    # Paths come from each loader's own ``*_JSON_PATH`` constant so this guard
    # can never drift from the file the service actually reads.
    return [
        _ListRegistry("arcade", arcade.ARCADE_JSON_PATH),
        _ListRegistry("catalog", catalog.CATALOG_JSON_PATH),
        _ListRegistry("products", products.PRODUCTS_JSON_PATH),
        _MuseumRegistry("puddle_museum", puddle_museum.MUSEUM_JSON_PATH),
    ]


def _blocker_entries() -> list[tuple[str, str, dict[str, Any]]]:
    """``(registry_name, identity, entry)`` for every entry carrying a raw
    ``blocker`` object across all committed registries."""
    out: list[tuple[str, str, dict[str, Any]]] = []
    for reg in _registries():
        for identity, entry in reg.entries():
            if isinstance(entry.get("blocker"), dict):
                out.append((reg.name, identity, entry))
    return out


# Parametrize once at import so a malformed row is named individually in the
# pytest report (which registry, which slug) instead of hiding behind a loop.
_BLOCKER_ENTRIES = _blocker_entries()
_BLOCKER_IDS = [f"{name}:{identity}" for name, identity, _ in _BLOCKER_ENTRIES]


def test_registries_carry_blockers() -> None:
    """Sanity floor: the committed registries really do carry blockers, so a
    silently-emptied dataset can never make every other assertion vacuously
    pass."""
    assert _BLOCKER_ENTRIES, "expected committed registries to carry blocker objects"


@pytest.mark.parametrize("name, identity, entry", _BLOCKER_ENTRIES, ids=_BLOCKER_IDS)
def test_blocker_ask_id_is_well_formed(name: str, identity: str, entry: dict[str, Any]) -> None:
    """Every committed ``blocker.ask_id`` (when present) matches the canonical
    ``ASK_ID_RE`` from ``botsite/blockers.py`` — a malformed id would silently
    normalize to ``None`` and cost the ledger join the console verification
    chips depend on."""
    blocker = entry["blocker"]
    if "ask_id" not in blocker:
        return
    ask_id = blocker["ask_id"]
    assert isinstance(ask_id, str), f"{name}:{identity} ask_id must be a string, got {ask_id!r}"
    assert blockers.ASK_ID_RE.fullmatch(ask_id.strip()), (
        f"{name}:{identity} ask_id {ask_id!r} does not match the ledger id shape ASK-NNNN"
    )


@pytest.mark.parametrize("name, identity, entry", _BLOCKER_ENTRIES, ids=_BLOCKER_IDS)
def test_blocker_survives_normalization(name: str, identity: str, entry: dict[str, Any]) -> None:
    """Every committed ``blocker`` normalizes to a real object — non-empty
    ``owner_action`` + ``unblocks`` — rather than degrading to ``None``. A
    blocker present in the data but missing its required fields would render
    an empty "What's blocking launch" panel / vanish from the owner-click
    count; this asserts none does."""
    normalized = blockers.normalized_blocker(entry["blocker"])
    assert normalized is not None, (
        f"{name}:{identity} carries a blocker object that degrades to None "
        f"(missing/empty owner_action or unblocks): {entry['blocker']!r}"
    )
    assert normalized["owner_action"], f"{name}:{identity} blocker has an empty owner_action"
    assert normalized["unblocks"], f"{name}:{identity} blocker has an empty unblocks"


@pytest.mark.parametrize("registry", _registries(), ids=lambda r: r.name)
def test_no_duplicate_identity_keys(registry: _Registry) -> None:
    """No registry repeats an identity key (slug / edition lang). A duplicate
    slug would make ``game_by_slug`` / detail routes silently resolve to
    whichever entry the loader happened to keep first."""
    for key_name, values in registry.identity_groups():
        present = [v for v in values if v and v != "None"]
        duplicates = {v for v in present if present.count(v) > 1}
        assert not duplicates, (
            f"{registry.name} has duplicate {key_name}(s): {sorted(duplicates)}"
        )


def _ledger_ask_ids() -> set[str]:
    """The canonical ``ASK-NNNN`` ids declared by the owner-actions ledger's
    ``ID:`` marker lines — empty if the ledger is unreadable (the caller then
    skips the orphan-reference guard rather than red on a doc restructure)."""
    try:
        text = LEDGER_PATH.read_text(encoding="utf-8")
    except OSError:
        return set()
    return {m.group(1) for m in _LEDGER_ID_LINE.finditer(text)}


def test_referenced_ask_ids_exist_in_ledger() -> None:
    """Orphan-reference guard: every well-formed ``ask_id`` referenced by a
    committed blocker has a matching row in the owner-actions ledger
    (``docs/owner/OWNER-ACTIONS.md``). An orphaned reference — a blocker
    pointing at an ASK id the ledger never declares — would break the owner
    console's id-exact verification join. Defensive: if the ledger is missing
    or declares no ids (e.g. a doc restructure), skip rather than go
    flaky-red — the intrinsic-shape guards above still stand."""
    ledger_ids = _ledger_ask_ids()
    if not ledger_ids:
        pytest.skip("owner-actions ledger unreadable or declares no ID: ASK-NNNN rows")
    referenced: set[str] = set()
    for name, identity, entry in _BLOCKER_ENTRIES:
        ask_id = blockers.normalized_ask_id(entry["blocker"])
        if ask_id is not None:
            referenced.add(ask_id)
    orphans = referenced - ledger_ids
    assert not orphans, (
        f"blocker ask_id(s) reference no ledger row (orphaned): {sorted(orphans)} "
        f"— known ledger ids: {sorted(ledger_ids)}"
    )
