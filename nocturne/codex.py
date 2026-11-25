"""The application logic of the Codex, independent of HTTP."""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path
from typing import Any

from . import __version__, arcane, cardart, edicts, heraldry, ritual, sigils, tarot
from .edicts import DayRules
from .numerology import words
from .rng import FateStream, derive_seed
from .storage import AlreadySealed, NoteRecord, Store

MAX_TITLE = 120
MAX_BODY = 10_000
_DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TIME = re.compile(r"^(\d{1,2}):(\d{2})$")


class Clock:
    """The source of 'now' — replaceable in tests."""

    def now(self) -> dt.datetime:
        return dt.datetime.now()

    def today(self) -> dt.date:
        return self.now().date()


class CodexError(Exception):
    """An error that maps onto an HTTP status and a stable machine-readable code."""

    def __init__(self, status: int, code: str, message: str, **extra: Any) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.extra = extra

    def to_dict(self) -> dict:
        return {"error": self.code, "message": self.message, **self.extra}


def parse_day(value: str | None, default: dt.date) -> dt.date:
    if not value:
        return default
    if not _DAY.match(value):
        raise CodexError(400, "bad_day", "Days are written YYYY-MM-DD.")
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise CodexError(400, "bad_day", "That day is not on any calendar.") from exc


class Codex:
    def __init__(self, store: Store, clock: Clock | None = None, data_dir: Path | None = None) -> None:
        self.store = store
        self.clock = clock or Clock()
        self.data_dir = data_dir
        self._secret = store.secret()
        self._rules: dict[str, DayRules] = {}

    # -- helpers -----------------------------------------------------------
    @property
    def today(self) -> dt.date:
        return self.clock.today()

    def _hand(self, day: dt.date) -> list[ritual.DrawnCard] | None:
        record = self.store.ritual(day.isoformat())
        if record is None:
            return None
        return [ritual.DrawnCard.from_record(r) for r in record.drawn]

    def rules(self, day: dt.date) -> DayRules | None:
        key = day.isoformat()
        if key in self._rules:
            return self._rules[key]
        record = self.store.ritual(key)
        if record is None or record.keep is None:
            return None
        hand = [ritual.DrawnCard.from_record(r) for r in record.drawn]
        rules = edicts.rules_for_day(self._secret, day, hand, record.keep)
        self._rules[key] = rules
        return rules

    def _require_tonight(self, day: str) -> DayRules:
        if day != self.today.isoformat():
            raise CodexError(403, "night_sealed", "That night is sealed; its ink has long since dried.")
        rules = self.rules(self.today)
        if rules is None:
            raise CodexError(409, "ritual_required", "Draw and keep the night's cards before you write.")
        return rules

    def _local_time(self, value: object) -> tuple[int, int, str]:
        if isinstance(value, str):
            match = _TIME.match(value.strip())
            if match:
                hour, minute = int(match.group(1)), int(match.group(2))
                if 0 <= hour < 24 and 0 <= minute < 60:
                    return hour, minute, f"{hour:02d}:{minute:02d}"
        now = self.clock.now()
        return now.hour, now.minute, f"{now.hour:02d}:{now.minute:02d}"

    @staticmethod
    def _text(payload: dict, key: str, limit: int) -> str:
        value = payload.get(key, "")
        if value is None:
            value = ""
        if not isinstance(value, str):
            raise CodexError(400, "bad_field", f"'{key}' must be text.")
        value = sigils.expand_shortcodes(value).replace("\r\n", "\n")
        if len(value) > limit:
            raise CodexError(413, "too_long", f"'{key}' may hold at most {limit} characters.")
        return value

    @staticmethod
    def _velocity(payload: dict) -> float:
        value = payload.get("velocity", 0)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return 0.0
        return float(max(0.0, min(2000.0, value)))

    @staticmethod
    def _coord(payload: dict, key: str) -> float | None:
        value = payload.get(key)
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise CodexError(400, "bad_field", f"'{key}' must be a number between 0 and 1.")
        return float(max(0.0, min(1.0, value)))

    def _auto_place(self, rules: DayRules, count: int) -> tuple[float, float]:
        if rules.effects.get("grid"):
            col, row = count % 4, (count // 4) % 3
            return round(0.14 + col * 0.24, 4), round(0.18 + row * 0.3, 4)
        stream = FateStream(derive_seed(self._secret, "nocturne/place", rules.day, str(count)))
        return round(0.1 + stream.below(800) / 1000, 4), round(0.12 + stream.below(740) / 1000, 4)

    def _note_dict(self, note: NoteRecord) -> dict:
        data = note.to_dict()
        data["rite_names"] = [arcane.BY_ID[r].name for r in note.rites if r in arcane.BY_ID]
        return data

    def _house(self, rules: DayRules | None) -> dict | None:
        return heraldry.get(rules.house).to_dict() if rules else None

    def _echo(self, day: dt.date, rules: DayRules | None) -> dict | None:
        if not rules or not rules.effects.get("echo"):
            return None
        past = self.store.notes_before(day.isoformat())
        if not past:
            return None
        stream = FateStream(derive_seed(self._secret, "nocturne/echo", day.isoformat()))
        return self._note_dict(stream.choice(past))

    # -- the ritual ------------------------------------------------------------
    def _ritual_view(self, day: dt.date) -> dict:
        record = self.store.ritual(day.isoformat())
        if record is None:
            status = "untouched" if day == self.today else "unobserved"
            return {"status": status, "drawn": [], "keep": None}
        hand = [ritual.DrawnCard.from_record(r) for r in record.drawn]
        drawn = []
        for card in hand:
            data = card.to_dict()
            data["previews"] = edicts.preview(card)
            drawn.append(data)
        return {
            "status": "sealed" if record.sealed else "drawn",
            "drawn": drawn,
            "keep": record.keep,
        }

    def draw(self) -> dict:
        day = self.today
        hand = ritual.draw_for_day(self._secret, day)
        self.store.record_draw(day.isoformat(), [card.to_record() for card in hand])
        return self._ritual_view(day)

    def keep(self, payload: dict) -> dict:
        day = self.today
        try:
            keep = ritual.validate_keep(payload.get("keep"))  # type: ignore[arg-type]
        except ritual.RitualError as exc:
            raise CodexError(400, "bad_keep", str(exc)) from exc
        if self.store.ritual(day.isoformat()) is None:
            raise CodexError(409, "not_drawn", "Draw the night's five cards first.")
        try:
            self.store.seal(day.isoformat(), list(keep))
        except AlreadySealed as exc:
            raise CodexError(409, "already_sealed", str(exc)) from exc
        return self.state(day.isoformat())

    # -- views -----------------------------------------------------------------
    def state(self, day_value: str | None = None) -> dict:
        today = self.today
        day = parse_day(day_value, today)
        if day > today:
            raise CodexError(403, "future_veiled", "The future is veiled. Ask again tomorrow.")
        rules = self.rules(day)
        discovered = self.store.discoveries()
        return {
            "version": __version__,
            "today": today.isoformat(),
            "day": day.isoformat(),
            "is_today": day == today,
            "ritual": self._ritual_view(day),
            "rules": rules.to_dict() if rules else None,
            "house": self._house(rules),
            "notes": [self._note_dict(n) for n in self.store.notes(day.isoformat())],
            "echo": self._echo(day, rules),
            "settings": self.store.settings(),
            "discovered": sorted(discovered),
            "rites_total": len(arcane.DISCOVERABLE),
            "data_dir": str(self.data_dir) if self.data_dir else None,
        }

    def catalogue(self) -> dict:
        return {
            "sigils": sigils.catalogue(),
            "deck": tarot.catalogue(),
            "houses": heraldry.catalogue(),
            "rites": arcane.codex(self.store.discoveries()),
            "positions": {
                key: {"title": ritual.POSITION_TITLES[key], "role": ritual.POSITION_ROLES[key]}
                for key in ritual.POSITION_TITLES
            },
        }

    def calendar(self) -> dict:
        days = []
        for entry in self.store.calendar():
            day = dt.date.fromisoformat(entry["day"])
            rules = self.rules(day)
            kept = []
            if entry["keep"]:
                kept = [
                    {
                        "name": tarot.get(entry["drawn"][i]["id"]).name,
                        "reversed": entry["drawn"][i]["reversed"],
                        "id": entry["drawn"][i]["id"],
                    }
                    for i in entry["keep"]
                ]
            days.append(
                {
                    "day": entry["day"],
                    "sealed": entry["sealed"],
                    "note_count": entry["note_count"],
                    "kept": kept,
                    "house": rules.house if rules else None,
                    "aspect": rules.aspect.get("name") if rules else None,
                }
            )
        return {"today": self.today.isoformat(), "days": days}

    # -- notes -----------------------------------------------------------------
    def _inscription(self, payload: dict, day: str, first: bool) -> tuple[arcane.Inscription, str]:
        title = self._text(payload, "title", MAX_TITLE).strip()
        body = self._text(payload, "body", MAX_BODY)
        hour, minute, stamp = self._local_time(payload.get("local_time"))
        note = arcane.Inscription(title, body, hour, minute, self._velocity(payload), first)
        return note, stamp

    def _validate(self, note: arcane.Inscription, rules: DayRules) -> None:
        if not note.title and not note.body.strip():
            raise CodexError(400, "empty", "An empty page performs no rite.")
        violations = edicts.check_constraints(note.title, note.body, rules)
        if violations:
            raise CodexError(
                422, "edict_violation", violations[0].message, violations=[v.to_dict() for v in violations]
            )

    def _invoke(self, note: arcane.Inscription, rules: DayRules) -> arcane.Invocation:
        return arcane.invoke(note, rules)

    def create_note(self, payload: dict) -> dict:
        day = self.today.isoformat()
        rules = self._require_tonight(day)
        count = self.store.count_notes(day)
        note, stamp = self._inscription(payload, day, first=count == 0)
        self._validate(note, rules)
        invocation = self._invoke(note, rules)
        x, y = self._coord(payload, "x"), self._coord(payload, "y")
        if x is None or y is None or rules.effects.get("grid"):
            x, y = self._auto_place(rules, count)
        record = self.store.add_note(
            day,
            note.title,
            note.body,
            invocation.reading.found,
            [r for r in invocation.rite_ids if r != "ink_settles"],
            invocation.bound,
            invocation.reading.weight,
            x,
            y,
            stamp,
        )
        new = self.store.record_rites(
            [r for r in invocation.rite_ids if arcane.BY_ID[r].discoverable], day, record.id
        )
        return {
            "note": self._note_dict(record),
            "invocation": invocation.to_dict(),
            "new_discoveries": [arcane.BY_ID[r].to_dict() for r in new],
        }

    def _existing(self, note_id: int) -> NoteRecord:
        note = self.store.note(note_id)
        if note is None:
            raise CodexError(404, "no_such_note", "No such note exists in the Codex.")
        return note

    def update_note(self, note_id: int, payload: dict) -> dict:
        existing = self._existing(note_id)
        rules = self._require_tonight(existing.day)
        if existing.bound:
            raise CodexError(423, "bound", "This note is bound in chains and cannot be changed.")
        note, _ = self._inscription(payload, existing.day, first=False)
        self._validate(note, rules)
        invocation = self._invoke(note, rules)
        record = self.store.update_note(
            note_id,
            note.title,
            note.body,
            invocation.reading.found,
            [r for r in invocation.rite_ids if r != "ink_settles"],
            invocation.bound,
            invocation.reading.weight,
        )
        new = self.store.record_rites(
            [r for r in invocation.rite_ids if arcane.BY_ID[r].discoverable],
            existing.day,
            record.id,
        )
        return {
            "note": self._note_dict(record),
            "invocation": invocation.to_dict(),
            "new_discoveries": [arcane.BY_ID[r].to_dict() for r in new],
        }

    def move_note(self, note_id: int, payload: dict) -> dict:
        existing = self._existing(note_id)
        rules = self._require_tonight(existing.day)
        if rules.effects.get("anchored"):
            raise CodexError(409, "anchored", "Tonight's notes are anchored in stone.")
        x, y = self._coord(payload, "x"), self._coord(payload, "y")
        if x is None or y is None:
            raise CodexError(400, "bad_field", "Both 'x' and 'y' are needed.")
        return {"note": self._note_dict(self.store.move_note(note_id, x, y))}

    def delete_note(self, note_id: int) -> dict:
        existing = self._existing(note_id)
        rules = self.rules(dt.date.fromisoformat(existing.day))
        self.store.delete_note(note_id)
        return {"deleted": note_id, "moths": bool(rules and rules.effects.get("moths"))}

    def divine(self, payload: dict) -> dict:
        """Read a draft without saving it: the omen candle and the edicts it breaks."""
        day = self.today.isoformat()
        rules = self._require_tonight(day)
        count = self.store.count_notes(day)
        note, _ = self._inscription(payload, day, first=count == 0)
        invocation = self._invoke(note, rules)
        data = invocation.to_dict()
        return {
            "flames": data["flames"],
            "sigils": data["sigils"],
            "bound": data["bound"],
            "violations": [v.to_dict() for v in edicts.check_constraints(note.title, note.body, rules)],
            "words": len(words(sigils.strip(f"{note.title} {note.body}"))),
        }

    # -- settings & export -----------------------------------------------------
    def settings(self) -> dict:
        return self.store.settings()

    def update_settings(self, payload: dict) -> dict:
        from .storage import StorageError

        try:
            return self.store.update_settings(payload)
        except StorageError as exc:
            raise CodexError(400, "bad_setting", str(exc)) from exc

    def export_markdown(self) -> str:
        lines = ["# Nocturne Codex — exported notes", ""]
        current = None
        for note in self.store.all_notes():
            if note.day != current:
                current = note.day
                lines += [f"## {note.day}", ""]
                rules = self.rules(dt.date.fromisoformat(note.day))
                if rules:
                    lines += [f"*{rules.omen}*", ""]
            title = note.title or "Untitled"
            lines += [f"### {title}", "", f"*Inscribed at {note.local_time}*"]
            if note.rites:
                names = ", ".join(arcane.BY_ID[r].name for r in note.rites if r in arcane.BY_ID)
                lines.append(f"*Rites: {names}*")
            lines += ["", note.body, ""]
        return "\n".join(lines)

    def export_json(self) -> dict:
        return self.store.export()

    # -- art -------------------------------------------------------------------
    @staticmethod
    def card_art(card_id: str) -> str:
        if card_id == "back":
            return cardart.back_svg()
        if card_id not in tarot.BY_ID:
            raise CodexError(404, "no_such_card", "No such card in the deck.")
        return cardart.card_svg(card_id)

    @staticmethod
    def crest_art(house_id: str) -> str:
        if house_id not in heraldry.BY_ID:
            raise CodexError(404, "no_such_house", "No such House.")
        return heraldry.house_svg(house_id)

    @staticmethod
    def forged_art(name: str) -> str:
        return heraldry.forged_svg(name[:60])
