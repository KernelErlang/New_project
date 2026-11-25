"""Private, local persistence in a single SQLite file.

Nothing ever leaves the machine: notes, rituals and discoveries live in
``codex.sqlite3`` inside the data directory (see :mod:`nocturne.config`).
"""

from __future__ import annotations

import datetime as dt
import json
import secrets
import sqlite3
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

SCHEMA_VERSION = 1

DEFAULT_SETTINGS: dict[str, Any] = {
    "master_volume": 0.7,
    "ambience": True,
    "effects": True,
    "quill_sounds": True,
    "reduced_motion": False,
    "veil_all": False,
    "voice": "",
    "crest_name": "",
}

_SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS rituals (
    day TEXT PRIMARY KEY,
    drawn TEXT NOT NULL,
    drawn_at TEXT NOT NULL,
    keep TEXT,
    sealed_at TEXT
);
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    body TEXT NOT NULL DEFAULT '',
    sigils TEXT NOT NULL DEFAULT '[]',
    rites TEXT NOT NULL DEFAULT '[]',
    bound INTEGER NOT NULL DEFAULT 0,
    weight INTEGER NOT NULL DEFAULT 0,
    x REAL NOT NULL DEFAULT 0.5,
    y REAL NOT NULL DEFAULT 0.5,
    local_time TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS notes_by_day ON notes(day);
CREATE TABLE IF NOT EXISTS discoveries (
    rite TEXT PRIMARY KEY,
    first_day TEXT NOT NULL,
    first_note INTEGER,
    count INTEGER NOT NULL DEFAULT 1
);
"""


class StorageError(RuntimeError):
    pass


class AlreadySealed(StorageError):
    pass


@dataclass
class RitualRecord:
    day: str
    drawn: list[dict]
    drawn_at: str
    keep: list[int] | None
    sealed_at: str | None

    @property
    def sealed(self) -> bool:
        return self.keep is not None


@dataclass
class NoteRecord:
    id: int
    day: str
    title: str
    body: str
    sigils: list[str]
    rites: list[str]
    bound: bool
    weight: int
    x: float
    y: float
    local_time: str
    created_at: str
    updated_at: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "day": self.day,
            "title": self.title,
            "body": self.body,
            "sigils": list(self.sigils),
            "rites": list(self.rites),
            "bound": self.bound,
            "weight": self.weight,
            "x": self.x,
            "y": self.y,
            "local_time": self.local_time,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


def _now() -> str:
    return dt.datetime.now().replace(microsecond=0).isoformat()


def _note(row: sqlite3.Row) -> NoteRecord:
    return NoteRecord(
        id=row["id"],
        day=row["day"],
        title=row["title"],
        body=row["body"],
        sigils=json.loads(row["sigils"]),
        rites=json.loads(row["rites"]),
        bound=bool(row["bound"]),
        weight=row["weight"],
        x=row["x"],
        y=row["y"],
        local_time=row["local_time"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class Store:
    """Thread-safe access to the Codex database."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        if str(path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._db = sqlite3.connect(str(path), check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        with self._lock:
            self._db.executescript(_SCHEMA)
            self._db.execute(
                "INSERT OR IGNORE INTO meta(key, value) VALUES ('schema_version', ?)",
                (str(SCHEMA_VERSION),),
            )
            self._db.commit()

    # -- plumbing ----------------------------------------------------------
    def close(self) -> None:
        with self._lock:
            self._db.close()

    def _query(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        with self._lock:
            return list(self._db.execute(sql, params))

    def _write(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        with self._lock:
            cursor = self._db.execute(sql, params)
            self._db.commit()
            return cursor

    def _meta(self, key: str) -> str | None:
        rows = self._query("SELECT value FROM meta WHERE key = ?", (key,))
        return rows[0]["value"] if rows else None

    def _set_meta(self, key: str, value: str) -> None:
        self._write(
            "INSERT INTO meta(key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )

    # -- the soul secret ---------------------------------------------------
    def secret(self) -> bytes:
        """The install's private secret; it makes every Codex's draws unique."""
        with self._lock:
            value = self._meta("soul_secret")
            if value is None:
                value = secrets.token_hex(32)
                self._set_meta("soul_secret", value)
            return bytes.fromhex(value)

    def schema_version(self) -> int:
        return int(self._meta("schema_version") or 0)

    # -- settings ------------------------------------------------------------
    def settings(self) -> dict[str, Any]:
        stored = json.loads(self._meta("settings") or "{}")
        merged = dict(DEFAULT_SETTINGS)
        merged.update({k: v for k, v in stored.items() if k in DEFAULT_SETTINGS})
        return merged

    def update_settings(self, changes: dict[str, Any]) -> dict[str, Any]:
        current = self.settings()
        for key, value in changes.items():
            if key not in DEFAULT_SETTINGS:
                raise StorageError(f"Unknown setting: {key}")
            expected = type(DEFAULT_SETTINGS[key])
            if expected is float and isinstance(value, int) and not isinstance(value, bool):
                value = float(value)
            if not isinstance(value, expected) or (expected is not bool and isinstance(value, bool)):
                raise StorageError(f"Setting {key} must be a {expected.__name__}")
            if key == "master_volume":
                value = max(0.0, min(1.0, value))
            if isinstance(value, str):
                value = value[:80]
            current[key] = value
        self._set_meta("settings", json.dumps(current))
        return current

    # -- rituals -------------------------------------------------------------
    def ritual(self, day: str) -> RitualRecord | None:
        rows = self._query("SELECT * FROM rituals WHERE day = ?", (day,))
        if not rows:
            return None
        row = rows[0]
        return RitualRecord(
            day=row["day"],
            drawn=json.loads(row["drawn"]),
            drawn_at=row["drawn_at"],
            keep=json.loads(row["keep"]) if row["keep"] else None,
            sealed_at=row["sealed_at"],
        )

    def record_draw(self, day: str, drawn: list[dict]) -> RitualRecord:
        """Record the night's hand. Drawing again returns the original record."""
        with self._lock:
            existing = self.ritual(day)
            if existing:
                return existing
            self._write(
                "INSERT INTO rituals(day, drawn, drawn_at) VALUES (?, ?, ?)",
                (day, json.dumps(drawn), _now()),
            )
            record = self.ritual(day)
            assert record is not None
            return record

    def seal(self, day: str, keep: list[int]) -> RitualRecord:
        with self._lock:
            record = self.ritual(day)
            if record is None:
                raise StorageError("The cards must be drawn before they can be kept.")
            if record.sealed:
                raise AlreadySealed("The night's hand is already sealed.")
            self._write(
                "UPDATE rituals SET keep = ?, sealed_at = ? WHERE day = ?",
                (json.dumps(list(keep)), _now(), day),
            )
            sealed = self.ritual(day)
            assert sealed is not None
            return sealed

    def rituals(self) -> list[RitualRecord]:
        rows = self._query("SELECT day FROM rituals ORDER BY day DESC")
        return [r for r in (self.ritual(row["day"]) for row in rows) if r]

    # -- notes ---------------------------------------------------------------
    def notes(self, day: str) -> list[NoteRecord]:
        rows = self._query("SELECT * FROM notes WHERE day = ? ORDER BY id", (day,))
        return [_note(row) for row in rows]

    def note(self, note_id: int) -> NoteRecord | None:
        rows = self._query("SELECT * FROM notes WHERE id = ?", (note_id,))
        return _note(rows[0]) if rows else None

    def count_notes(self, day: str) -> int:
        rows = self._query("SELECT COUNT(*) AS n FROM notes WHERE day = ?", (day,))
        return int(rows[0]["n"])

    def add_note(
        self,
        day: str,
        title: str,
        body: str,
        sigil_ids: list[str],
        rite_ids: list[str],
        bound: bool,
        weight: int,
        x: float,
        y: float,
        local_time: str,
    ) -> NoteRecord:
        now = _now()
        cursor = self._write(
            "INSERT INTO notes(day, title, body, sigils, rites, bound, weight, x, y, local_time,"
            " created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                day,
                title,
                body,
                json.dumps(sigil_ids),
                json.dumps(rite_ids),
                int(bound),
                weight,
                x,
                y,
                local_time,
                now,
                now,
            ),
        )
        note = self.note(int(cursor.lastrowid or 0))
        assert note is not None
        return note

    def update_note(
        self,
        note_id: int,
        title: str,
        body: str,
        sigil_ids: list[str],
        rite_ids: list[str],
        bound: bool,
        weight: int,
    ) -> NoteRecord:
        self._write(
            "UPDATE notes SET title = ?, body = ?, sigils = ?, rites = ?, bound = ?, weight = ?,"
            " updated_at = ? WHERE id = ?",
            (title, body, json.dumps(sigil_ids), json.dumps(rite_ids), int(bound), weight, _now(), note_id),
        )
        note = self.note(note_id)
        if note is None:
            raise StorageError("No such note.")
        return note

    def move_note(self, note_id: int, x: float, y: float) -> NoteRecord:
        self._write("UPDATE notes SET x = ?, y = ? WHERE id = ?", (x, y, note_id))
        note = self.note(note_id)
        if note is None:
            raise StorageError("No such note.")
        return note

    def delete_note(self, note_id: int) -> bool:
        return self._write("DELETE FROM notes WHERE id = ?", (note_id,)).rowcount > 0

    def notes_before(self, day: str) -> list[NoteRecord]:
        rows = self._query("SELECT * FROM notes WHERE day < ? ORDER BY id", (day,))
        return [_note(row) for row in rows]

    def all_notes(self) -> Iterator[NoteRecord]:
        for row in self._query("SELECT * FROM notes ORDER BY day, id"):
            yield _note(row)

    def calendar(self) -> list[dict]:
        rows = self._query(
            "SELECT r.day AS day, r.keep AS keep, r.drawn AS drawn,"
            " (SELECT COUNT(*) FROM notes n WHERE n.day = r.day) AS notes"
            " FROM rituals r ORDER BY r.day DESC"
        )
        return [
            {
                "day": row["day"],
                "sealed": row["keep"] is not None,
                "keep": json.loads(row["keep"]) if row["keep"] else None,
                "drawn": json.loads(row["drawn"]),
                "note_count": row["notes"],
            }
            for row in rows
        ]

    # -- discoveries ---------------------------------------------------------
    def discoveries(self) -> dict[str, dict]:
        rows = self._query("SELECT * FROM discoveries")
        return {
            row["rite"]: {
                "first_day": row["first_day"],
                "first_note": row["first_note"],
                "count": row["count"],
            }
            for row in rows
        }

    def record_rites(self, rite_ids: list[str], day: str, note_id: int | None) -> list[str]:
        """Count performed rites and return the ones performed for the first time."""
        new: list[str] = []
        with self._lock:
            known = self.discoveries()
            for rite in dict.fromkeys(rite_ids):
                if rite in known:
                    self._db.execute("UPDATE discoveries SET count = count + 1 WHERE rite = ?", (rite,))
                else:
                    self._db.execute(
                        "INSERT INTO discoveries(rite, first_day, first_note) VALUES (?, ?, ?)",
                        (rite, day, note_id),
                    )
                    new.append(rite)
            self._db.commit()
        return new

    # -- export --------------------------------------------------------------
    def export(self) -> dict:
        return {
            "format": "nocturne-codex/1",
            "exported_at": _now(),
            "rituals": [
                {"day": r.day, "drawn": r.drawn, "keep": r.keep, "sealed_at": r.sealed_at}
                for r in self.rituals()
            ],
            "notes": [n.to_dict() for n in self.all_notes()],
            "discoveries": self.discoveries(),
        }
