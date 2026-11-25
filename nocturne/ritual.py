"""The nightly ritual: draw five, keep three, burn two.

The five cards of a day are a pure function of the install's secret and the date,
so the night's hand is fixed — it cannot be redrawn, and it is different for every
day and every Codex.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Sequence

from . import tarot
from .rng import FateStream, derive_seed

POSITIONS = ("crown", "heart", "shadow")
POSITION_TITLES = {
    "crown": "The Crown",
    "heart": "The Heart",
    "shadow": "The Shadow",
    "burned": "The Ashes",
}
POSITION_ROLES = {
    "crown": "What reigns — the night's aspect, colours and music.",
    "heart": "What stirs — the resonant number and the awakened sigils.",
    "shadow": "What binds — the night's constraint, or a boon if reversed.",
    "burned": "What was refused — burned cards banish elements and forbid sigils.",
}
DRAW_SIZE = 5
KEEP_SIZE = 3
REVERSAL_ODDS = (1, 3)  # one card in three falls reversed


class RitualError(ValueError):
    """Raised when a keep request breaks the ritual's rules."""


@dataclass(frozen=True)
class DrawnCard:
    card: tarot.Card
    reversed: bool

    def to_dict(self) -> dict:
        data = self.card.to_dict()
        data["reversed"] = self.reversed
        data["orientation"] = "reversed" if self.reversed else "upright"
        return data

    def to_record(self) -> dict:
        return {"id": self.card.id, "reversed": self.reversed}

    @classmethod
    def from_record(cls, record: dict) -> DrawnCard:
        return cls(tarot.get(record["id"]), bool(record["reversed"]))


def draw_for_day(secret: bytes, day: dt.date) -> list[DrawnCard]:
    """Return the five cards fate deals for ``day``."""
    stream = FateStream(derive_seed(secret, "nocturne/draw", day.isoformat()))
    deck = list(tarot.DECK)
    stream.shuffle(deck)
    return [DrawnCard(card, stream.chance(*REVERSAL_ODDS)) for card in deck[:DRAW_SIZE]]


def validate_keep(keep: Sequence[object]) -> tuple[int, int, int]:
    """Validate the indices of the three kept cards (in Crown, Heart, Shadow order)."""
    if not isinstance(keep, (list, tuple)) or len(keep) != KEEP_SIZE:
        raise RitualError(f"Exactly {KEEP_SIZE} cards must be kept.")
    indices: list[int] = []
    for value in keep:
        if isinstance(value, bool) or not isinstance(value, int):
            raise RitualError("Kept cards are named by their position in the hand (0-4).")
        if not 0 <= value < DRAW_SIZE:
            raise RitualError("A kept card must be one of the five drawn.")
        indices.append(value)
    if len(set(indices)) != KEEP_SIZE:
        raise RitualError("A card cannot be kept twice.")
    return indices[0], indices[1], indices[2]


@dataclass(frozen=True)
class Spread:
    """A day's hand and, once sealed, the choice of which three to keep."""

    day: dt.date
    drawn: tuple[DrawnCard, ...]
    keep: tuple[int, int, int] | None = None

    @property
    def sealed(self) -> bool:
        return self.keep is not None

    @property
    def kept(self) -> dict[str, DrawnCard]:
        if self.keep is None:
            return {}
        return {pos: self.drawn[i] for pos, i in zip(POSITIONS, self.keep)}

    @property
    def burned(self) -> list[DrawnCard]:
        if self.keep is None:
            return []
        return [card for i, card in enumerate(self.drawn) if i not in self.keep]

    def to_dict(self) -> dict:
        kept = self.kept
        return {
            "day": self.day.isoformat(),
            "drawn": [card.to_dict() for card in self.drawn],
            "keep": list(self.keep) if self.keep else None,
            "kept": {pos: card.to_dict() for pos, card in kept.items()},
            "burned": [card.to_dict() for card in self.burned],
        }
