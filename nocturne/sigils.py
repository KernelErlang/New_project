"""The sigil catalogue: the magical marks that can be woven into a note.

Twenty-two sigils are each *ruled* by one card of the Major Arcana. Two more — Earth
and the Quintessence pentagram — answer to no card. Every sigil has an element, a
polarity (light or dark) and a numeric value used by the hidden formulas in
:mod:`nocturne.arcane`.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass

ELEMENTS = ("fire", "water", "air", "earth")
OPPOSITES = {"fire": "water", "water": "fire", "air": "earth", "earth": "air"}
POLARITIES = ("light", "dark")

# Characters that may follow a glyph to request text/emoji presentation. They are
# ignored when sigils are read out of a note.
VARIATION_SELECTORS = ("︎", "️")


@dataclass(frozen=True)
class Sigil:
    id: str
    glyph: str
    name: str
    element: str  # one of ELEMENTS, or "spirit"
    polarity: str  # "light" | "dark"
    value: int
    ruler: str | None  # id of the ruling Major Arcana card
    lore: str

    @property
    def shortcode(self) -> str:
        return f":{self.id}:"

    def to_dict(self) -> dict:
        data = asdict(self)
        data["shortcode"] = self.shortcode
        return data


SIGILS: tuple[Sigil, ...] = (
    Sigil(
        "air", "🜁", "Air", "air", "light", 22, "major-00", "The breath before the leap. Ruled by the Fool."
    ),
    Sigil(
        "mercury",
        "☿",
        "Mercury",
        "air",
        "light",
        1,
        "major-01",
        "Quicksilver, messenger of will. Ruled by the Magician.",
    ),
    Sigil(
        "ankh",
        "☥",
        "Ankh",
        "water",
        "light",
        2,
        "major-02",
        "The key of the veiled temple. Ruled by the High Priestess.",
    ),
    Sigil(
        "venus",
        "♀",
        "Venus",
        "earth",
        "light",
        3,
        "major-03",
        "Copper mirror of love and growing things. Ruled by the Empress.",
    ),
    Sigil(
        "mars",
        "♂",
        "Mars",
        "fire",
        "dark",
        4,
        "major-04",
        "Iron, war and the stern throne. Ruled by the Emperor.",
    ),
    Sigil(
        "cross",
        "✠",
        "Cross Pattée",
        "earth",
        "light",
        5,
        "major-05",
        "Mark of creeds and consecrated stone. Ruled by the Hierophant.",
    ),
    Sigil(
        "heart",
        "❦",
        "Floral Heart",
        "air",
        "light",
        6,
        "major-06",
        "Two hearts on one stem. Ruled by the Lovers.",
    ),
    Sigil(
        "comet",
        "☄",
        "Comet",
        "water",
        "light",
        7,
        "major-07",
        "A burning road across the dark. Ruled by the Chariot.",
    ),
    Sigil(
        "sulfur",
        "🜍",
        "Sulfur",
        "fire",
        "dark",
        8,
        "major-08",
        "The red lion, the fierce soul of matter. Ruled by Strength.",
    ),
    Sigil(
        "lantern",
        "✶",
        "Lantern Star",
        "earth",
        "light",
        9,
        "major-09",
        "A small light carried up a mountain. Ruled by the Hermit.",
    ),
    Sigil(
        "jupiter",
        "♃",
        "Jupiter",
        "air",
        "light",
        10,
        "major-10",
        "Tin and turning fortune. Ruled by the Wheel.",
    ),
    Sigil(
        "scales",
        "⚖",
        "Scales",
        "air",
        "light",
        11,
        "major-11",
        "The weighing of what was done. Ruled by Justice.",
    ),
    Sigil(
        "water",
        "🜄",
        "Water",
        "water",
        "dark",
        12,
        "major-12",
        "The drowned depth that reflects the sky. Ruled by the Hanged Man.",
    ),
    Sigil(
        "skull",
        "☠",
        "Skull",
        "water",
        "dark",
        13,
        "major-13",
        "What remains when the candle is out. Ruled by Death.",
    ),
    Sigil(
        "alembic",
        "⚗",
        "Alembic",
        "fire",
        "light",
        14,
        "major-14",
        "The vessel where opposites are married. Ruled by Temperance.",
    ),
    Sigil(
        "pact",
        "⛧",
        "Inverted Pentagram",
        "earth",
        "dark",
        15,
        "major-15",
        "A bargain written upside down. Ruled by the Devil.",
    ),
    Sigil(
        "thunder",
        "☈",
        "Thunder",
        "fire",
        "dark",
        16,
        "major-16",
        "The sky's sudden honesty. Ruled by the Tower.",
    ),
    Sigil(
        "star",
        "✦",
        "Star",
        "air",
        "light",
        17,
        "major-17",
        "Hope poured out under open sky. Ruled by the Star.",
    ),
    Sigil(
        "luna",
        "☽",
        "Luna",
        "water",
        "dark",
        18,
        "major-18",
        "The waxing moon and its beautiful lies. Ruled by the Moon.",
    ),
    Sigil("sol", "☉", "Sol", "fire", "light", 19, "major-19", "The golden eye of noon. Ruled by the Sun."),
    Sigil(
        "fire",
        "🜂",
        "Fire",
        "fire",
        "light",
        20,
        "major-20",
        "The flame that calls the dead to rise. Ruled by Judgement.",
    ),
    Sigil(
        "saturn",
        "♄",
        "Saturn",
        "earth",
        "dark",
        21,
        "major-21",
        "Lead, time and the closing circle. Ruled by the World.",
    ),
    Sigil("earth", "🜃", "Earth", "earth", "dark", 4, None, "Grave-soil and root. It answers to no card."),
    Sigil(
        "quintessence",
        "⛤",
        "Quintessence",
        "spirit",
        "light",
        5,
        None,
        "The fifth element that binds the four. It answers to no card.",
    ),
)

BY_ID: dict[str, Sigil] = {s.id: s for s in SIGILS}
BY_GLYPH: dict[str, Sigil] = {s.glyph: s for s in SIGILS}
BY_RULER: dict[str, Sigil] = {s.ruler: s for s in SIGILS if s.ruler}
ELEMENT_SIGIL = {"fire": "fire", "water": "water", "air": "air", "earth": "earth"}
STAR_SIGILS = frozenset({"star", "lantern", "comet"})

_SHORTCODE = re.compile(r":([a-z]+):")


def get(sigil_id: str) -> Sigil:
    """Return a sigil by id, raising ``KeyError`` for unknown ids."""
    return BY_ID[sigil_id]


def of_element(element: str) -> list[str]:
    """Ids of every sigil belonging to ``element``."""
    return [s.id for s in SIGILS if s.element == element]


def of_polarity(polarity: str) -> list[str]:
    """Ids of every sigil of the given polarity."""
    return [s.id for s in SIGILS if s.polarity == polarity]


def expand_shortcodes(text: str) -> str:
    """Replace ``:sol:``-style shortcodes with their glyphs (unknown codes are kept)."""

    def swap(match: re.Match[str]) -> str:
        sigil = BY_ID.get(match.group(1))
        return sigil.glyph if sigil else match.group(0)

    return _SHORTCODE.sub(swap, text)


def extract(text: str) -> list[str]:
    """Return the ids of all sigils found in ``text``, in reading order.

    Shortcodes are honoured and variation selectors are ignored.
    """
    text = expand_shortcodes(text)
    for selector in VARIATION_SELECTORS:
        text = text.replace(selector, "")
    return [BY_GLYPH[ch].id for ch in text if ch in BY_GLYPH]


def strip(text: str) -> str:
    """Remove sigil glyphs (and variation selectors) from ``text``."""
    text = expand_shortcodes(text)
    return "".join(ch for ch in text if ch not in BY_GLYPH and ch not in VARIATION_SELECTORS)


def starts_with_sigil(text: str) -> bool:
    """True if the first visible character of ``text`` is a sigil."""
    text = expand_shortcodes(text).lstrip()
    return bool(text) and text[0] in BY_GLYPH


def catalogue() -> list[dict]:
    """The full catalogue, serialisable to JSON."""
    return [s.to_dict() for s in SIGILS]
