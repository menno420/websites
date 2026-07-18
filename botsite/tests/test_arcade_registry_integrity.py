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


# --------------------------------------------------------------------------- #
# A4 — arcade.json per-entry schema guard.
#
# The blocker guards above cover the shared ``blocker`` object across every
# registry. This section covers the rest of the arcade entry's shape — the
# fields, enums and link-URL requirement that ``botsite/arcade.py`` reads. The
# arcade loader is fail-soft the same way ``blockers`` is: ``arcade._valid``
# SKIPS an entry that is missing a required field or carries an out-of-enum
# ``maturity`` / ``availability`` value (a new game silently drops from the
# arcade), and ``load_games`` silently demotes a ``live`` / ``download`` entry
# whose ``url`` is null/blank out of its link-bearing state (``has_link``
# false — a dead card with no play link and no signal). This guard turns those
# silent-loss modes into a loud CI failure by asserting the committed
# ``arcade.json`` is well-formed, using the shipped ``botsite.arcade`` constants
# (``_REQUIRED`` / ``MATURITIES`` / ``AVAILABILITIES`` / ``LINKED_AVAILABILITIES``)
# as the single source of truth — never re-stated — so the guard can never claim
# an invariant the loader does not actually enforce. READ-ONLY: it never writes
# or mutates the registry.
# --------------------------------------------------------------------------- #

# Allowed top-level keys = the loader's required fields plus the three optional
# keys ``load_games`` reads (``url``, ``status_note``, ``blocker``). Derived from
# ``arcade._REQUIRED`` so a new required field moves the allow-set automatically;
# a new OPTIONAL field is the one line a future schema change must add here.
_ALLOWED_ARCADE_KEYS = frozenset(arcade._REQUIRED) | {"url", "status_note", "blocker"}
# The blocker object's own keys (shape validated in depth by the
# ``normalized_blocker`` guards above; this just rejects typo'd sub-keys).
_ALLOWED_BLOCKER_KEYS = frozenset({"owner_action", "unblocks", "ask_id"})
# A well-formed outbound URL: the arcade only ever renders http(s) links.
_HTTP_URL_RE = re.compile(r"^https?://", re.IGNORECASE)


def arcade_entry_errors(entry: Any) -> list[str]:
    """Every way ``entry`` violates the committed ``arcade.json`` schema.

    Empty list == valid. Every rule is drawn from the shipped
    ``botsite.arcade`` constants, so this validator reflects the real loader
    invariants rather than a re-stated guess.
    """
    if not isinstance(entry, dict):
        return [f"entry is not a JSON object: {entry!r}"]
    errors: list[str] = []
    unknown = set(entry) - _ALLOWED_ARCADE_KEYS
    if unknown:
        errors.append(f"unknown/typo top-level key(s): {sorted(unknown)}")
    for field in arcade._REQUIRED:
        value = entry.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(
                f"required field {field!r} must be a non-empty string, got {value!r}"
            )
    if entry.get("maturity") not in arcade.MATURITIES:
        errors.append(
            f"maturity {entry.get('maturity')!r} not in {arcade.MATURITIES}"
        )
    availability = entry.get("availability")
    if availability not in arcade.AVAILABILITIES:
        errors.append(
            f"availability {availability!r} not in {arcade.AVAILABILITIES}"
        )
    url = entry.get("url")
    if url is not None and not isinstance(url, str):
        errors.append(f"url must be null or a string, got {url!r}")
    # A link-bearing availability MUST carry a well-formed URL, else the loader
    # silently demotes it (``has_link`` false) — the exact "live game with no
    # reachable link" silent loss A4 exists to catch. An ``unavailable`` entry
    # legitimately has a null url and is left alone.
    if availability in arcade.LINKED_AVAILABILITIES:
        if not isinstance(url, str) or not url.strip():
            errors.append(
                f"availability {availability!r} requires a non-empty url, got {url!r}"
            )
        elif not _HTTP_URL_RE.match(url.strip()):
            errors.append(f"url {url!r} is not a well-formed http(s) URL")
    blocker = entry.get("blocker")
    if blocker is not None:
        if not isinstance(blocker, dict):
            errors.append(f"blocker must be a JSON object or absent, got {blocker!r}")
        else:
            unknown_b = set(blocker) - _ALLOWED_BLOCKER_KEYS
            if unknown_b:
                errors.append(f"unknown/typo blocker key(s): {sorted(unknown_b)}")
            if blockers.normalized_blocker(blocker) is None:
                errors.append(
                    "blocker degrades to None (missing/empty owner_action or "
                    f"unblocks): {blocker!r}"
                )
    return errors


# The real committed arcade registry, read once at import so each entry is a
# named row in the pytest report (by slug) rather than hidden behind a loop.
_ARCADE_RAW = json.loads(arcade.ARCADE_JSON_PATH.read_text(encoding="utf-8"))
_ARCADE_IDS = [
    str(e.get("slug")) if isinstance(e, dict) else repr(e) for e in _ARCADE_RAW
]


def test_arcade_registry_is_nonempty_list() -> None:
    """Sanity floor: ``arcade.json`` is a non-empty JSON list, so a
    silently-emptied file can never make the per-entry guard vacuously pass."""
    assert isinstance(_ARCADE_RAW, list) and _ARCADE_RAW, (
        "arcade.json must be a non-empty JSON list of game entries"
    )


@pytest.mark.parametrize("entry", _ARCADE_RAW, ids=_ARCADE_IDS)
def test_arcade_entry_matches_schema(entry: Any) -> None:
    """Every committed arcade entry is well-formed against the shipped
    ``botsite.arcade`` schema — required fields present, ``maturity`` /
    ``availability`` in-enum, a link-bearing availability carrying a real URL,
    no unknown top-level key, and a well-formed blocker when present."""
    errors = arcade_entry_errors(entry)
    identity = entry.get("slug") if isinstance(entry, dict) else entry
    assert not errors, f"arcade.json entry {identity!r} violates schema: {errors}"


def test_arcade_slugs_unique() -> None:
    """No two arcade entries share a slug — a duplicate would make
    ``game_by_slug`` / the /arcade/{slug} detail route silently resolve to
    whichever entry ``load_games`` kept first."""
    slugs = [e.get("slug") for e in _ARCADE_RAW if isinstance(e, dict)]
    duplicates = {s for s in slugs if slugs.count(s) > 1}
    assert not duplicates, f"arcade.json has duplicate slug(s): {sorted(duplicates)}"


# --------------------------------------------------------------------------- #
# Guard-has-teeth: prove ``arcade_entry_errors`` REJECTS malformed entries, so
# the positive guard above is not vacuously green. The negative case ships as a
# committed parametrized assertion over an inline malformed-sample table rather
# than by mutating the real registry file.
# --------------------------------------------------------------------------- #

# A minimal entry the schema accepts; each malformed sample is one mutation of
# it, so exactly the single injected fault is what the validator must catch.
_VALID_ARCADE_SAMPLE = {
    "slug": "sample-game",
    "name": "Sample Game",
    "tagline": "A sample arcade entry.",
    "description": "A sample game used only to exercise the schema guard.",
    "maturity": "beta",
    "availability": "unavailable",
    "source_repo": "menno420/sample",
    "url": None,
    "status_note": "a note",
}


def _sample(**overrides: Any) -> dict[str, Any]:
    entry = dict(_VALID_ARCADE_SAMPLE)
    entry.update(overrides)
    return entry


_MALFORMED_ARCADE_SAMPLES = [
    ("missing-required-field", {k: v for k, v in _VALID_ARCADE_SAMPLE.items() if k != "name"}),
    ("empty-required-field", _sample(tagline="   ")),
    ("non-string-required-field", _sample(name=123)),
    ("bad-maturity-enum", _sample(maturity="released")),
    ("bad-availability-enum", _sample(availability="soon")),
    ("live-with-null-url", _sample(availability="live", url=None)),
    ("download-with-malformed-url", _sample(availability="download", url="not-a-url")),
    ("live-with-blank-url", _sample(availability="live", url="   ")),
    ("non-string-url", _sample(url=42)),
    ("unknown-top-level-key", _sample(statusnote="typo of status_note")),
    ("blocker-not-object", _sample(blocker="blocked on owner")),
    ("blocker-missing-owner-action", _sample(blocker={"unblocks": "gives a URL"})),
    ("blocker-empty-owner-action", _sample(blocker={"owner_action": "  ", "unblocks": "x"})),
    ("blocker-unknown-key", _sample(blocker={"owner_action": "do x", "unblocks": "y", "asked_id": "ASK-0001"})),
    ("entry-not-an-object", "just a string, not a game object"),
]


def test_arcade_schema_accepts_valid_sample() -> None:
    """Positive control: the untouched valid sample passes cleanly, so a
    malformed sample failing below is the injected fault, not a broken base."""
    assert arcade_entry_errors(_VALID_ARCADE_SAMPLE) == []


@pytest.mark.parametrize(
    "entry",
    [sample for _, sample in _MALFORMED_ARCADE_SAMPLES],
    ids=[name for name, _ in _MALFORMED_ARCADE_SAMPLES],
)
def test_arcade_schema_rejects_malformed(entry: Any) -> None:
    """The guard has teeth: each known-bad entry yields at least one schema
    error. If any of these passed, a real malformed committed entry of the same
    kind would slip through and silently drop from the arcade."""
    assert arcade_entry_errors(entry), (
        f"validator should reject malformed entry but returned no errors: {entry!r}"
    )
