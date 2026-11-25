import pytest

from nocturne.storage import DEFAULT_SETTINGS, SCHEMA_VERSION, AlreadySealed, StorageError, Store

HAND = [{"id": "major-13", "reversed": False}, {"id": "cups-02", "reversed": True}]


def test_the_secret_survives_a_reopen(tmp_path):
    path = tmp_path / "codex.sqlite3"
    first = Store(path)
    secret = first.secret()
    assert len(secret) == 32
    assert first.secret() == secret
    first.close()
    second = Store(path)
    assert second.secret() == secret
    assert second.schema_version() == SCHEMA_VERSION
    second.close()


def test_two_codices_have_different_secrets(tmp_path):
    a, b = Store(tmp_path / "a.db"), Store(tmp_path / "b.db")
    assert a.secret() != b.secret()
    a.close()
    b.close()


def test_drawing_is_idempotent_and_sealing_happens_once(store):
    first = store.record_draw("2026-11-25", HAND)
    again = store.record_draw("2026-11-25", [{"id": "major-00", "reversed": False}])
    assert again.drawn == first.drawn == HAND
    assert not first.sealed
    sealed = store.seal("2026-11-25", [1, 0, 2])
    assert sealed.sealed and sealed.keep == [1, 0, 2]
    with pytest.raises(AlreadySealed):
        store.seal("2026-11-25", [0, 1, 2])
    with pytest.raises(StorageError):
        store.seal("2026-11-26", [0, 1, 2])


def add(store, day="2026-11-25", title="t", body="b", **kw):
    defaults = {
        "sigil_ids": [],
        "rite_ids": [],
        "bound": False,
        "weight": 1,
        "x": 0.5,
        "y": 0.5,
        "local_time": "21:00",
    }
    defaults.update(kw)
    return store.add_note(day, title, body, **defaults)


def test_note_lifecycle(store):
    note = add(store, sigil_ids=["sol"], rite_ids=["eclipse"])
    assert note.id and note.sigils == ["sol"] and note.rites == ["eclipse"]
    assert store.count_notes("2026-11-25") == 1
    updated = store.update_note(note.id, "new", "body ☉", ["sol"], [], True, 9)
    assert updated.title == "new" and updated.bound and updated.weight == 9
    moved = store.move_note(note.id, 0.1, 0.9)
    assert (moved.x, moved.y) == (0.1, 0.9)
    assert store.delete_note(note.id)
    assert not store.delete_note(note.id)
    assert store.note(note.id) is None
    with pytest.raises(StorageError):
        store.move_note(note.id, 0, 0)


def test_notes_are_grouped_by_day(store):
    add(store, day="2026-11-24", title="old")
    add(store, day="2026-11-25", title="new")
    assert [n.title for n in store.notes("2026-11-25")] == ["new"]
    assert [n.title for n in store.notes_before("2026-11-25")] == ["old"]
    assert [n.title for n in store.all_notes()] == ["old", "new"]


def test_discoveries_count_and_report_new_ones(store):
    assert store.record_rites(["eclipse", "eclipse", "nevermore"], "2026-11-25", 1) == [
        "eclipse",
        "nevermore",
    ]
    assert store.record_rites(["eclipse"], "2026-11-26", 2) == []
    found = store.discoveries()
    assert found["eclipse"]["count"] == 2
    assert found["eclipse"]["first_day"] == "2026-11-25"


def test_calendar_and_export(store):
    store.record_draw("2026-11-24", HAND + HAND[:1] * 3)
    store.record_draw("2026-11-25", HAND + HAND[:1] * 3)
    store.seal("2026-11-25", [0, 1, 2])
    add(store, day="2026-11-25")
    days = store.calendar()
    assert [d["day"] for d in days] == ["2026-11-25", "2026-11-24"]
    assert days[0]["sealed"] and days[0]["note_count"] == 1
    assert not days[1]["sealed"]
    exported = store.export()
    assert exported["format"] == "nocturne-codex/1"
    assert len(exported["notes"]) == 1 and len(exported["rituals"]) == 2
    assert "soul_secret" not in str(exported)


def test_settings_merge_validate_and_clamp(store):
    assert store.settings() == DEFAULT_SETTINGS
    changed = store.update_settings({"ambience": False, "master_volume": 3})
    assert changed["ambience"] is False and changed["master_volume"] == 1.0
    assert store.settings()["ambience"] is False
    assert store.update_settings({"master_volume": 0})["master_volume"] == 0.0
    with pytest.raises(StorageError):
        store.update_settings({"nonsense": 1})
    with pytest.raises(StorageError):
        store.update_settings({"ambience": "yes"})
    with pytest.raises(StorageError):
        store.update_settings({"master_volume": True})
    assert len(store.update_settings({"crest_name": "x" * 200})["crest_name"]) == 80


def test_in_memory_store_works():
    store = Store(":memory:")
    assert store.secret()
    store.close()
