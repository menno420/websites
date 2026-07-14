"""Export→import→export deep-equality round-trip pin for the testing DB.

The existing round-trip test (``test_testing_import.py``
``test_round_trip_export_then_import_after_wipe``) spot-checks fields
someone remembered to assert — an import that quietly coerces or defaults
a value passes it. These tests instead populate EVERY ``_IMPORT_SPEC``
table with representative rows via the real store writers, run
``export_all()``, restore the export into a second fresh DB through the
real valve path (``import_all()``), export again, and assert the two
exports are DEEPLY equal — ids, values, base64 blobs, everything. Paired
with the schema-drift pin (``test_import_schema_drift.py``, which proves
the spec covers the schema) this makes every current AND future column
value-fidelity-checked: a new column that reaches the spec is
automatically inside the deep comparison.

Also pinned: the legacy-shape round trip — an OLD backup missing columns
and tables added after it was taken imports to the DOCUMENTED
defaults-filled shape (never blind equality against the legacy input),
and that upgraded export then round-trips deep-equal like any current
backup.

Store-level and network-free: ``testing_store`` only, no app/client —
``import_all`` IS the valve's restore path (the route wraps it in
auth/size/CSRF gates that ``test_testing_import.py`` already covers)."""

from __future__ import annotations

import pytest

from botsite import testing_store

OPEN_TASK = "site-review-botsite"


@pytest.fixture()
def switch_db(tmp_path, monkeypatch):
    """Point the store at a fresh sqlite file; call again for the next DB
    (the redeploy-wipe simulation). Starts on ``source.sqlite3``."""

    def switch(name: str) -> None:
        monkeypatch.setenv("TESTING_DB_PATH", str(tmp_path / name))

    switch("source.sqlite3")
    return switch


def populate_representative_rows() -> None:
    """Fill every ``_IMPORT_SPEC`` table through the real store writers,
    with values chosen to catch coercion: non-defaults everywhere a
    default exists, unicode + newlines, floats, None-able score both set
    and null, blobs spanning all byte values, and every ``_IMPORT_REFS``
    FK edge exercised (submissions→claims, ai_reviews→submissions,
    screenshots→submissions, guide_exchanges→claims,
    payout_ledger→claims)."""
    claim_a = testing_store.create_claim(
        OPEN_TASK, "Ada Tester", "ada@example.com",
        "ada-pay@example.com", "tok-ada",
    )
    claim_b = testing_store.create_claim(
        "arcade-probe", 'Bo "Breaker" Ünïcode', "bo@example.com", "", "tok-bo"
    )
    testing_store.set_claim_status(claim_a["id"], "approved")
    testing_store.set_claim_status(claim_b["id"], "submitted")

    sub_a = testing_store.create_submission(
        claim_a["id"],
        {"what_worked": "nav — éclair", "severity": "major"},
        "Found a broken link.\nSecond line.",
    )
    sub_b = testing_store.create_submission(claim_b["id"], {}, "")

    # One reviewed row (score set, JSON payloads, low_effort on) and one
    # degraded row (score stays NULL) — both branches of the nullable
    # column survive the trip or the deep compare goes red.
    testing_store.save_ai_review(
        sub_a["id"],
        status="reviewed",
        score=87,
        low_effort=True,
        summary="Solid run",
        findings=[{"kind": "bug", "note": "404 on /x"}],
        followups=[{"q": "which browser?"}],
        calls_used=3,
    )
    testing_store.save_ai_review(
        sub_b["id"], status="degraded", degraded_reason="no key"
    )

    # Blobs: all 256 byte values behind a PNG magic — the base64 leg of
    # the renamed screenshots column (data ↔ data_base64) is byte-exact
    # or nothing here matches.
    testing_store.add_screenshot(
        sub_a["id"], "shot one.png", "image/png",
        b"\x89PNG\r\n\x1a\n" + bytes(range(256)),
    )
    testing_store.add_screenshot(
        sub_b["id"], "shot2.jpg", "image/jpeg", b"\xff\xd8\xff\xe0\x00\x00tail"
    )

    testing_store.add_guide_exchange(
        claim_a["id"], 2, "how do I open the palette?", "Press slash.",
        step_title="Open the search palette",
    )
    # step_title left at '' — the pre-provenance-pin default is data too.
    testing_store.add_guide_exchange(claim_b["id"], 0, "stuck at start", "Scroll down.")

    testing_store.add_ledger_entry(
        claim_a["id"], OPEN_TASK, "ada@example.com", 12.5, "owed",
        note="exit-review pass",
    )
    testing_store.add_ledger_entry(
        claim_b["id"], "arcade-probe", "bo@example.com", 5.0, "dry-run"
    )


def test_export_import_export_is_deep_equal(switch_db):
    """The pin: export → import into a fresh DB → export is IDENTICAL,
    across every imported table, with only export-act metadata
    normalized."""
    populate_representative_rows()
    first = testing_store.export_all()

    # Guard the pin's teeth, driven by the spec itself: a table added to
    # ``_IMPORT_SPEC`` later must gain fixture rows here, or this fails —
    # deep equality over an empty table proves nothing.
    for table in testing_store._IMPORT_SPEC:
        assert first[table], (
            f"round-trip fixture left {table!r} empty — populate it in"
            " populate_representative_rows() or the pin is toothless"
        )

    switch_db("restored.sqlite3")  # the redeploy wipe: a brand-new DB
    assert testing_store.list_claims() == []
    imported = testing_store.import_all(first)
    assert imported == {t: len(first[t]) for t in testing_store._IMPORT_SPEC}

    second = testing_store.export_all()

    # The ONLY normalizations, both export-act metadata, never row state:
    # - exported_at: stamped by export_all() at call time — the two calls
    #   legitimately happen at different moments.
    # - db_path: names the sqlite file behind the export — the second DB
    #   is a different file BY DESIGN (that fresh file is the wipe being
    #   simulated), so equality here would be self-contradictory.
    # Row timestamps (created_at/updated_at) are NOT normalized: the spec
    # imports them verbatim, so they must survive byte-identical.
    for export in (first, second):
        for meta in ("exported_at", "db_path"):
            assert meta in export
            del export[meta]

    assert first == second


def test_legacy_backup_round_trips_to_documented_defaults(switch_db):
    """An OLD backup — no ``paypal_email``/``status`` on claims, no
    ``answers_json``/``findings`` on submissions, no ``step_index``/
    ``step_title`` on guide_exchanges, the ai_reviews / screenshots /
    payout_ledger tables absent entirely — imports through the valve and
    exports as the DOCUMENTED upgraded shape: schema defaults filled in,
    missing tables empty. Asserted against explicit expected rows, never
    blind equality with the legacy input (the whole point is that the
    output is NOT the input)."""
    legacy = {
        "claims": [
            {
                "id": 41,
                "task_id": OPEN_TASK,
                "name": "Old Tester",
                "email": "old@example.com",
                "token": "legacy-token",
                "created_at": "2026-06-01T00:00:00Z",
            }
        ],
        "submissions": [
            {"id": 9, "claim_id": 41, "created_at": "2026-06-01T01:00:00Z"}
        ],
        "guide_exchanges": [
            {
                "id": 5,
                "claim_id": 41,
                "message": "stuck here",
                "reply": "Try the menu.",
                "created_at": "2026-06-01T00:30:00Z",
            }
        ],
    }
    testing_store.import_all(legacy)
    upgraded = testing_store.export_all()

    assert upgraded["claims"] == [
        {
            "id": 41,
            "task_id": OPEN_TASK,
            "name": "Old Tester",
            "email": "old@example.com",
            "paypal_email": "",  # column postdates the backup
            "token": "legacy-token",
            "status": "claimed",  # lifecycle column postdates the backup
            "created_at": "2026-06-01T00:00:00Z",
        }
    ]
    assert upgraded["submissions"] == [
        {
            "id": 9,
            "claim_id": 41,
            "answers_json": "{}",
            "findings": "",
            "created_at": "2026-06-01T01:00:00Z",
        }
    ]
    assert upgraded["guide_exchanges"] == [
        {
            "id": 5,
            "claim_id": 41,
            "step_index": 0,
            "step_title": "",  # honest "no snapshot was taken"
            "message": "stuck here",
            "reply": "Try the menu.",
            "created_at": "2026-06-01T00:30:00Z",
        }
    ]
    # Tables that postdate the oldest exports restore as empty.
    assert upgraded["ai_reviews"] == []
    assert upgraded["screenshots"] == []
    assert upgraded["payout_ledger"] == []

    # Once upgraded, the export is current-shape: from here on it must
    # round-trip deep-equal like any other backup (same normalizations as
    # the main pin — export-act metadata only, see above).
    switch_db("upgraded-restore.sqlite3")
    testing_store.import_all(upgraded)
    again = testing_store.export_all()
    for export in (upgraded, again):
        del export["exported_at"], export["db_path"]
    assert upgraded == again
