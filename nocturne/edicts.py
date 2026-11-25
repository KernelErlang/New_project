"""Edicts: how the cards of the night rewrite the rules of the Codex.

* **The Crown** sets the night's *aspect* — its palette, ambient particles and musical mode.
* **The Heart** sets the *resonant number* and *awakens* sigils.
* **The Shadow** imposes a *constraint* on every note (or grants a boon when reversed).
* **The Ashes** — the two burned cards — banish elements (minor cards) or forbid the
  ruling sigil of a Major Arcanum.

Every Major Arcanum also carries an *arcanum*: a signature mechanic that changes how
the board behaves or how the hidden formulas are evaluated.
"""

from __future__ import annotations

import colorsys
import datetime as dt
from dataclasses import dataclass, field

from . import heraldry, sigils
from .numerology import digital_root, words
from .ritual import DrawnCard, Spread
from .rng import FateStream, derive_seed

MODES: dict[str, tuple[int, ...]] = {
    "ionian": (0, 2, 4, 5, 7, 9, 11),
    "dorian": (0, 2, 3, 5, 7, 9, 10),
    "phrygian": (0, 1, 3, 5, 7, 8, 10),
    "lydian": (0, 2, 4, 6, 7, 9, 11),
    "mixolydian": (0, 2, 4, 5, 7, 9, 10),
    "aeolian": (0, 2, 3, 5, 7, 8, 10),
    "locrian": (0, 1, 3, 5, 6, 8, 10),
    "harmonic_minor": (0, 2, 3, 5, 7, 8, 11),
    "hungarian_minor": (0, 2, 3, 6, 7, 8, 11),
    "double_harmonic": (0, 1, 4, 5, 7, 8, 11),
}
ELEMENT_ROOT_HZ = {"fire": 146.83, "water": 174.61, "air": 110.0, "earth": 130.81}
ELEMENT_HUE = {"fire": 8.0, "water": 192.0, "air": 262.0, "earth": 88.0}
ELEMENT_PARTICLE = {"fire": "embers", "water": "droplets", "air": "feathers", "earth": "spores"}
ELEMENT_COLOURS = {
    "fire": "crimson and amber",
    "water": "teal and drowned silver",
    "air": "violet and pale steel",
    "earth": "moss and old gold",
}
SUIT_MODE = {
    "wands": "phrygian",
    "cups": "aeolian",
    "swords": "dorian",
    "pentacles": "harmonic_minor",
}
ASPECT_NOUN = {"fire": "Embers", "water": "Tides", "air": "Whispers", "earth": "Stones"}
BREVITY = {
    1: 999,
    2: 888,
    3: 777,
    4: 666,
    5: 616,
    6: 555,
    7: 444,
    8: 404,
    9: 333,
    10: 313,
    11: 222,
    12: 213,
    13: 144,
    14: 111,
}

# Presentation flags understood by the front end (see static/js/theme.js).
EFFECT_FLAGS = (
    "veil",
    "lantern",
    "silence",
    "starfield",
    "no_particles",
    "mirror",
    "fading",
    "moths",
    "illusion",
    "gilded",
    "illuminate",
    "bloom",
    "echo",
    "velocity",
    "drift",
    "tremor",
    "scatter",
    "anchored",
    "grid",
    "scramble",
    "chains",
    "quill_song",
)
# Formula modifiers understood by nocturne.arcane.
MODIFIERS = (
    "wild",
    "four_tools",
    "decree",
    "illuminate",
    "twin",
    "velocity",
    "ward",
    "lantern",
    "wheel",
    "balance",
    "inversion",
    "moths",
    "fusion",
    "tremor",
    "starfield",
    "illusion",
    "ouroboros",
    "bloom",
)


@dataclass(frozen=True)
class Arcanum:
    key: str
    accent: str
    glow: str
    particle: str
    mode: str
    boon: str
    boon_text: str
    curse: str
    curse_text: str
    boon_effects: tuple[str, ...] = ()
    boon_modifiers: tuple[str, ...] = ()
    boon_awaken: tuple[str, ...] = ()
    curse_effects: tuple[str, ...] = ()
    curse_modifiers: tuple[str, ...] = ()
    curse_constraints: tuple[tuple[str, object], ...] = ()


ARCANA: tuple[Arcanum, ...] = (
    Arcanum(
        "wild",
        "#8fd3c4",
        "#b8fff0",
        "feathers",
        "lydian",
        "The Wild Card",
        "The Fool's sigil 🜁 counts as every element tonight.",
        "Fool's Errand",
        "The sigil palette is scrambled into a new order.",
        boon_modifiers=("wild",),
        curse_effects=("scramble",),
    ),
    Arcanum(
        "four_tools",
        "#f2c14e",
        "#ffe08a",
        "motes",
        "mixolydian",
        "The Four Tools",
        "All four element sigils are awakened, and a storm needs only two of a kind.",
        "Sleight of Hand",
        "One sigil has been spirited away: it is forbidden tonight.",
        boon_modifiers=("four_tools",),
        boon_awaken=("fire", "water", "air", "earth"),
        curse_constraints=(("forbid_random", 1),),
    ),
    Arcanum(
        "veil",
        "#6c7fd1",
        "#a9b6ff",
        "motes",
        "aeolian",
        "Veil of Isis",
        "Notes stay veiled until you draw near, and ☥ is awakened.",
        "Vow of Secrecy",
        "Notes are veiled, and none may exceed 777 characters.",
        boon_effects=("veil",),
        boon_awaken=("ankh",),
        curse_effects=("veil",),
        curse_constraints=(("char_limit", 777),),
    ),
    Arcanum(
        "bloom",
        "#d46a8c",
        "#ff9fbf",
        "petals",
        "ionian",
        "Bloom",
        "Petals follow every inscription, and ♀ alone calls the Petal Rain.",
        "Overgrowth",
        "Every note must grow to at least 13 words.",
        boon_effects=("bloom",),
        boon_modifiers=("bloom",),
        curse_constraints=(("min_words", 13),),
    ),
    Arcanum(
        "decree",
        "#c0392b",
        "#ff6b5b",
        "embers",
        "harmonic_minor",
        "Imperial Ledger",
        "Notes fall into stately ranks, and the Crown's number may be met within one.",
        "Iron Decree",
        "Notes are anchored where they fall, and none may exceed 666 characters.",
        boon_effects=("grid",),
        boon_modifiers=("decree",),
        curse_effects=("anchored",),
        curse_constraints=(("char_limit", 666),),
    ),
    Arcanum(
        "illuminate",
        "#c8a96e",
        "#ffe3a3",
        "motes",
        "dorian",
        "Illumination",
        "Notes open with gilded initials, and two crosses suffice for the Trinity.",
        "Liturgy",
        "Every note must begin with a sigil.",
        boon_effects=("illuminate",),
        boon_modifiers=("illuminate",),
        curse_effects=("illuminate",),
        curse_constraints=(("begin_with_sigil", True),),
    ),
    Arcanum(
        "twin",
        "#e05a7a",
        "#ff9fb0",
        "petals",
        "lydian",
        "Kindred",
        "Any sigil written twice, anywhere in a note, calls the Twin Flames.",
        "Severed Pair",
        "Sigils must come in pairs: an even number in every note.",
        boon_modifiers=("twin",),
        curse_constraints=(("even_sigils", True),),
    ),
    Arcanum(
        "velocity",
        "#5b8def",
        "#9fc0ff",
        "motes",
        "mixolydian",
        "Momentum",
        "A velocity gauge rides with your quill; swift writing summons the Streak.",
        "Runaway Reins",
        "Your notes drift across the board of their own accord.",
        boon_effects=("velocity",),
        boon_modifiers=("velocity",),
        curse_effects=("drift", "velocity"),
    ),
    Arcanum(
        "ward",
        "#e07b39",
        "#ffb37a",
        "embers",
        "harmonic_minor",
        "Fortitude",
        "Forbidden sigils lose their bite: no note can be bound tonight.",
        "The Leash",
        "No note may exceed 444 characters.",
        boon_modifiers=("ward",),
        curse_constraints=(("char_limit", 444),),
    ),
    Arcanum(
        "lantern",
        "#f0b75a",
        "#ffd28a",
        "motes",
        "dorian",
        "Lantern Vigil",
        "The first note of the night is lit by the Hermit's lantern.",
        "Solitude",
        "Darkness falls: only a lantern lights the page, and the music is silent.",
        boon_modifiers=("lantern",),
        curse_effects=("lantern", "silence"),
        curse_modifiers=("lantern",),
    ),
    Arcanum(
        "wheel",
        "#9d7bd8",
        "#cdb6ff",
        "stars",
        "lydian",
        "Turning Fortune",
        "The resonant number turns with every hour.",
        "Spin of Fate",
        "The resonant number turns each hour, and the sigil palette is scrambled.",
        boon_modifiers=("wheel",),
        curse_effects=("scramble",),
        curse_modifiers=("wheel",),
    ),
    Arcanum(
        "balance",
        "#c9c3b0",
        "#f1ead2",
        "ash",
        "ionian",
        "Even Scales",
        "A single light and a single dark sigil suffice to balance the scales.",
        "Scales Demand",
        "Light and dark sigils must be equal in every note.",
        boon_modifiers=("balance",),
        curse_constraints=(("balanced_sigils", True),),
    ),
    Arcanum(
        "inversion",
        "#3fa7a0",
        "#7fe0d6",
        "droplets",
        "phrygian",
        "New Perspective",
        "A palindrome anywhere in a note, not only in its title, calls the Mirror.",
        "Inversion",
        "The night hangs upside down: the title is mirrored and new notes sink beneath old.",
        boon_modifiers=("inversion",),
        curse_effects=("mirror",),
    ),
    Arcanum(
        "moths",
        "#d9d2c0",
        "#f5efe0",
        "ash",
        "locrian",
        "Memento Mori",
        "☠ calls the moths at any hour, and deleted notes leave as moths.",
        "Memento",
        "Tonight's notes fade unless you draw near, and deleted notes leave as moths.",
        boon_effects=("moths",),
        boon_modifiers=("moths",),
        curse_effects=("fading", "moths"),
    ),
    Arcanum(
        "fusion",
        "#7ec8e3",
        "#bfefff",
        "droplets",
        "dorian",
        "Alchemy",
        "Opposite elements anywhere in a note call the Conjunction.",
        "Measured Breath",
        "No note may exceed 333 characters.",
        boon_modifiers=("fusion",),
        curse_constraints=(("char_limit", 333),),
    ),
    Arcanum(
        "chains",
        "#8b0a1a",
        "#ff2e4d",
        "embers",
        "hungarian_minor",
        "Temptation",
        "Every dark sigil is awakened.",
        "The Pact",
        "Two sigils are forbidden; using one binds the note in chains.",
        boon_awaken=("polarity:dark",),
        curse_effects=("chains",),
        curse_constraints=(("forbid_random", 2),),
    ),
    Arcanum(
        "tremor",
        "#ff7b29",
        "#ffc08a",
        "ash",
        "double_harmonic",
        "Revelation",
        "A single exclamation beneath ☈ calls the lightning.",
        "Upheaval",
        "The board quakes with every inscription, and the notes scatter.",
        boon_modifiers=("tremor",),
        curse_effects=("tremor", "scatter"),
    ),
    Arcanum(
        "starfield",
        "#7fb7ff",
        "#cfe3ff",
        "stars",
        "lydian",
        "Constellation",
        "Each note lights a star, and a single star sigil calls the Starfall.",
        "Starless Night",
        "The sky is empty and the music silent; only your notes light stars.",
        boon_effects=("starfield",),
        boon_modifiers=("starfield",),
        curse_effects=("starfield", "silence", "no_particles"),
    ),
    Arcanum(
        "illusion",
        "#a9b8d6",
        "#e2ebff",
        "motes",
        "aeolian",
        "Lunar Hours",
        "The Witching Hour lasts the whole night, from nine until five.",
        "Lunacy",
        "The ink shimmers and wavers, and the Witching Hour lasts all night.",
        boon_modifiers=("illusion",),
        curse_effects=("illusion",),
        curse_modifiers=("illusion",),
    ),
    Arcanum(
        "gilded",
        "#e6b422",
        "#fff1a8",
        "motes",
        "ionian",
        "Radiance",
        "Every light sigil is awakened.",
        "Glare",
        "The Codex burns too bright, and ☽ is forbidden.",
        boon_effects=("gilded",),
        boon_awaken=("polarity:light",),
        curse_effects=("gilded",),
        curse_constraints=(("forbid", ("luna",)),),
    ),
    Arcanum(
        "echo",
        "#ff9a3c",
        "#ffd08a",
        "embers",
        "mixolydian",
        "The Calling",
        "A voice from a past night returns to the board.",
        "Reckoning",
        "A past note returns, and every note must bear 🜂.",
        boon_effects=("echo",),
        curse_effects=("echo",),
        curse_constraints=(("require", ("fire",)),),
    ),
    Arcanum(
        "ouroboros",
        "#6fbf73",
        "#b5f2b8",
        "spores",
        "ionian",
        "Completion",
        "The four elements alone close the Ouroboros.",
        "Unfinished",
        "Every note must bear at least four sigils.",
        boon_modifiers=("ouroboros",),
        curse_constraints=(("min_sigils", 4),),
    ),
)


@dataclass
class Edict:
    title: str
    text: str
    source: str
    position: str
    tone: str  # "boon" | "bane" | "omen"

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "text": self.text,
            "source": self.source,
            "position": self.position,
            "tone": self.tone,
        }


@dataclass
class Constraints:
    char_limit: int | None = None
    min_sigils: int = 0
    min_words: int = 0
    begin_with_sigil: bool = False
    even_sigils: bool = False
    balanced_sigils: bool = False
    require: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "char_limit": self.char_limit,
            "min_sigils": self.min_sigils,
            "min_words": self.min_words,
            "begin_with_sigil": self.begin_with_sigil,
            "even_sigils": self.even_sigils,
            "balanced_sigils": self.balanced_sigils,
            "require": list(self.require),
        }


@dataclass
class DayRules:
    day: str
    aspect: dict = field(default_factory=dict)
    tonality: dict = field(default_factory=dict)
    resonance: int = 9
    crown_value: int = 0
    awakened: list[str] = field(default_factory=list)
    banished: list[str] = field(default_factory=list)
    forbidden: list[str] = field(default_factory=list)
    wild_sigil: str | None = None
    constraints: Constraints = field(default_factory=Constraints)
    effects: dict[str, bool] = field(default_factory=lambda: dict.fromkeys(EFFECT_FLAGS, False))
    modifiers: list[str] = field(default_factory=list)
    edicts: list[Edict] = field(default_factory=list)
    house: str = heraldry.HOUSES[0].id
    omen: str = ""
    scramble_seed: int = 0

    def has(self, modifier: str) -> bool:
        return modifier in self.modifiers

    def resonance_at(self, hour: int) -> int:
        """The resonant number at a given hour (the Wheel turns it hourly)."""
        if self.has("wheel"):
            return (self.resonance - 1 + hour) % 9 + 1
        return self.resonance

    def sigil_state(self, sigil_id: str) -> str:
        """``forbidden``, ``ashen``, ``awakened``, ``wild`` or ``plain``."""
        if sigil_id in self.forbidden:
            return "forbidden"
        if sigils.get(sigil_id).element in self.banished:
            return "ashen"
        if sigil_id == self.wild_sigil:
            return "wild"
        if sigil_id in self.awakened:
            return "awakened"
        return "plain"

    def to_dict(self) -> dict:
        return {
            "day": self.day,
            "aspect": dict(self.aspect),
            "tonality": dict(self.tonality),
            "resonance": self.resonance,
            "crown_value": self.crown_value,
            "awakened": list(self.awakened),
            "banished": list(self.banished),
            "forbidden": list(self.forbidden),
            "wild_sigil": self.wild_sigil,
            "constraints": self.constraints.to_dict(),
            "effects": dict(self.effects),
            "modifiers": list(self.modifiers),
            "edicts": [e.to_dict() for e in self.edicts],
            "house": self.house,
            "omen": self.omen,
            "scramble_seed": self.scramble_seed,
            "sigil_states": {s.id: self.sigil_state(s.id) for s in sigils.SIGILS},
        }


# ---------------------------------------------------------------------------
# colour helpers


def _hsl(hue: float, saturation: float, lightness: float) -> str:
    r, g, b = colorsys.hls_to_rgb((hue % 360) / 360.0, lightness, saturation)
    return f"#{round(r * 255):02x}{round(g * 255):02x}{round(b * 255):02x}"


def _hue_of(hex_colour: str) -> tuple[float, float, float]:
    value = hex_colour.lstrip("#")
    r, g, b = (int(value[i : i + 2], 16) / 255 for i in (0, 2, 4))
    h, lightness, s = colorsys.rgb_to_hls(r, g, b)
    return h * 360.0, s, lightness


def palette_for_hue(hue: float, accent: str | None = None, glow: str | None = None) -> dict:
    """Build the full palette for a base hue (optionally pinning accent/glow)."""
    parchment_hue = 38 + ((hue - 38 + 180) % 360 - 180) * 0.12
    return {
        "accent": accent or _hsl(hue, 0.55, 0.52),
        "accent2": _hsl(hue + 24, 0.35, 0.72),
        "glow": glow or _hsl(hue, 0.85, 0.62),
        "ink": _hsl(hue, 0.55, 0.14),
        "sky": _hsl(hue, 0.45, 0.06),
        "parchment": _hsl(parchment_hue, 0.38, 0.84),
    }


def eclipse(palette: dict) -> dict:
    """Dim a palette for a reversed Crown."""
    hue, sat, light = _hue_of(palette["accent"])
    eclipsed = dict(palette)
    eclipsed["accent"] = _hsl(hue, sat * 0.45, light * 0.72)
    eclipsed["glow"] = _hsl(275, 0.6, 0.55)
    eclipsed["sky"] = _hsl(hue, 0.3, 0.035)
    return eclipsed


def _element_word(element: str) -> str:
    return {"fire": "fire", "water": "water", "air": "air", "earth": "earth"}[element]


def _plural(count: int, word: str) -> str:
    return f"{count} {word}" + ("" if count == 1 else "s")


# ---------------------------------------------------------------------------
# the builder


class _Builder:
    def __init__(self, day: str) -> None:
        self.rules = DayRules(day=day)
        self.forbid_random = 0
        self.awaken: list[str] = []

    # small helpers --------------------------------------------------------
    def edict(self, title: str, text: str, card: DrawnCard, position: str, tone: str) -> None:
        self.rules.edicts.append(Edict(title, text, card.card.id, position, tone))

    def flag(self, *names: str) -> None:
        for name in names:
            self.rules.effects[name] = True

    def modify(self, *names: str) -> None:
        for name in names:
            if name not in self.rules.modifiers:
                self.rules.modifiers.append(name)

    def awaken_spec(self, specs: tuple[str, ...] | list[str]) -> None:
        for spec in specs:
            if spec.startswith("polarity:"):
                self.awaken.extend(sigils.of_polarity(spec.split(":", 1)[1]))
            elif spec.startswith("element:"):
                self.awaken.extend(sigils.of_element(spec.split(":", 1)[1]))
            else:
                self.awaken.append(spec)

    def constrain(self, pairs: tuple[tuple[str, object], ...]) -> None:
        c = self.rules.constraints
        for key, value in pairs:
            if key == "char_limit":
                limit = int(value)  # type: ignore[call-overload]
                c.char_limit = limit if c.char_limit is None else min(c.char_limit, limit)
            elif key == "min_sigils":
                c.min_sigils = max(c.min_sigils, int(value))  # type: ignore[call-overload]
            elif key == "min_words":
                c.min_words = max(c.min_words, int(value))  # type: ignore[call-overload]
            elif key in ("begin_with_sigil", "even_sigils", "balanced_sigils"):
                setattr(c, key, True)
            elif key == "require":
                for sigil_id in value:  # type: ignore[union-attr]
                    if sigil_id not in c.require:
                        c.require.append(sigil_id)
            elif key == "forbid":
                for sigil_id in value:  # type: ignore[union-attr]
                    if sigil_id not in self.rules.forbidden:
                        self.rules.forbidden.append(sigil_id)
            elif key == "forbid_random":
                self.forbid_random += int(value)  # type: ignore[call-overload]

    def boon(self, arcanum: Arcanum, card: DrawnCard, position: str) -> None:
        self.flag(*arcanum.boon_effects)
        self.modify(*arcanum.boon_modifiers)
        self.awaken_spec(arcanum.boon_awaken)
        self.edict(arcanum.boon, arcanum.boon_text, card, position, "boon")

    # positions ------------------------------------------------------------
    def crown(self, drawn: DrawnCard) -> None:
        card = drawn.card
        self.rules.crown_value = card.value
        if card.is_major:
            arcanum = ARCANA[card.rank]
            hue, _, _ = _hue_of(arcanum.accent)
            palette = palette_for_hue(hue, arcanum.accent, arcanum.glow)
            particle, mode = arcanum.particle, arcanum.mode
            name = f"Aspect of {card.name.removeprefix('The ')}"
            root = ELEMENT_ROOT_HZ[card.element] * 2 ** ((card.rank % 7) / 12)
        else:
            hue = ELEMENT_HUE[card.element] + (card.rank - 7) * 2.5
            palette = palette_for_hue(hue)
            particle = ELEMENT_PARTICLE[card.element]
            mode = SUIT_MODE[card.suit or "wands"]
            name = f"Aspect of {ASPECT_NOUN[card.element]}"
            root = ELEMENT_ROOT_HZ[card.element] * 2 ** (((card.rank - 1) % 5) / 12)
        if drawn.reversed:
            palette = eclipse(palette)
            mode = "locrian"
            name += ", Eclipsed"
        self.rules.aspect = {
            "name": name,
            "element": card.element,
            "palette": palette,
            "particle": particle,
            "eclipsed": drawn.reversed,
        }
        self.rules.tonality = {
            "root_hz": round(root, 2),
            "mode": mode,
            "intervals": list(MODES[mode]),
        }
        colours = ELEMENT_COLOURS[card.element]
        text = (
            f"{card.name} reigns. The night burns in {colours}, and the music turns {mode.replace('_', ' ')}."
        )
        if drawn.reversed:
            text += " Reversed, its light is eclipsed."
        self.edict(name, text, drawn, "crown", "omen")
        if card.is_major:
            self.boon(ARCANA[card.rank], drawn, "crown")

    def heart(self, drawn: DrawnCard) -> None:
        card = drawn.card
        resonance = digital_root(card.value) or 9
        if drawn.reversed:
            resonance = 10 - resonance
        self.rules.resonance = resonance
        if card.is_major:
            ruling = sigils.get(card.sigil)
            self.awaken.append(ruling.id)
            text = (
                f"{card.name} stirs at the Heart. The resonant number is {resonance}, "
                f"and its sigil {ruling.glyph} is awakened."
            )
        else:
            element = card.element
            if drawn.reversed:
                element = sigils.OPPOSITES[element]
            self.awaken_spec((f"element:{element}",))
            text = (
                f"{card.name} stirs at the Heart. The resonant number is {resonance}, "
                f"and {_element_word(element)} sigils are awakened."
            )
        if drawn.reversed:
            text += " Reversed, the number is reflected."
        self.edict(f"The Heart keeps {resonance}", text, drawn, "heart", "omen")
        if card.is_major:
            self.boon(ARCANA[card.rank], drawn, "heart")

    def shadow(self, drawn: DrawnCard) -> None:
        card = drawn.card
        if card.is_major:
            arcanum = ARCANA[card.rank]
            if drawn.reversed:
                self.boon(arcanum, drawn, "shadow")
                self.rules.edicts[-1].text = "Reversed, the curse breaks. " + arcanum.boon_text
                return
            self.flag(*arcanum.curse_effects)
            self.modify(*arcanum.curse_modifiers)
            self.constrain(arcanum.curse_constraints)
            self.edict(arcanum.curse, arcanum.curse_text, drawn, "shadow", "bane")
            return
        suit, rank = card.suit, card.rank
        if not drawn.reversed:
            if suit == "wands":
                count = 1 + (rank >= 8) + (rank >= 12)
                self.constrain((("min_sigils", count),))
                self.edict(
                    "Ember Tithe",
                    f"Every note must bear at least {_plural(count, 'sigil')}, or the ink will not take.",
                    drawn,
                    "shadow",
                    "bane",
                )
            elif suit == "cups":
                self.flag("fading")
                self.edict(
                    "Tide of Forgetting",
                    "Tonight's notes fade from the board unless you draw near.",
                    drawn,
                    "shadow",
                    "bane",
                )
            elif suit == "swords":
                self.constrain((("char_limit", BREVITY[rank]),))
                self.edict(
                    "Vow of Brevity",
                    f"No note may exceed {BREVITY[rank]} characters.",
                    drawn,
                    "shadow",
                    "bane",
                )
            else:
                self.flag("anchored")
                text = "Notes are anchored where they first fall"
                if rank >= 10:
                    self.flag("silence")
                    text += ", and the music is stilled"
                self.edict("Weight of Stone", text + ".", drawn, "shadow", "bane")
            return
        if suit == "wands":
            self.awaken_spec(("element:fire",))
            self.edict(
                "Free Flame",
                "Reversed, the tithe is forgiven and fire sigils are awakened.",
                drawn,
                "shadow",
                "boon",
            )
        elif suit == "cups":
            self.flag("echo")
            self.edict(
                "The Tide Returns",
                "Reversed, a note from a past night washes back onto the board.",
                drawn,
                "shadow",
                "boon",
            )
        elif suit == "swords":
            self.flag("quill_song")
            self.edict(
                "Unbound Tongue",
                "Reversed, no limit binds your words, and the quill sings in the night's mode.",
                drawn,
                "shadow",
                "boon",
            )
        else:
            self.modify("ward")
            self.edict(
                "Bedrock Ward",
                "Reversed, forbidden sigils lose their bite: no note can be bound.",
                drawn,
                "shadow",
                "boon",
            )

    def burned(self, drawn: DrawnCard) -> None:
        card = drawn.card
        if card.is_major:
            ruling = sigils.get(card.sigil)
            if ruling.id not in self.rules.forbidden:
                self.rules.forbidden.append(ruling.id)
            self.edict(
                f"Ashes of {card.name}",
                f"Its sigil {ruling.glyph} {ruling.name} is forbidden; using it binds the note in chains.",
                drawn,
                "burned",
                "bane",
            )
        else:
            if card.element not in self.rules.banished:
                self.rules.banished.append(card.element)
            self.edict(
                f"Ashes of the {card.name}",
                f"{_element_word(card.element).title()} sigils crumble to ash tonight.",
                drawn,
                "burned",
                "bane",
            )

    # resolution -----------------------------------------------------------
    def finish(self, secret: bytes, spread: Spread) -> DayRules:
        rules = self.rules
        stream = FateStream(derive_seed(secret, "nocturne/edicts", rules.day))
        if self.forbid_random:
            pool = [s.id for s in sigils.SIGILS if s.id not in rules.forbidden]
            for sigil_id in stream.sample(pool, min(self.forbid_random, len(pool))):
                rules.forbidden.append(sigil_id)
                sigil = sigils.get(sigil_id)
                rules.edicts.append(
                    Edict(
                        "A Sigil Forbidden",
                        f"{sigil.glyph} {sigil.name} is forbidden tonight; "
                        "using it binds the note in chains.",
                        "fate",
                        "shadow",
                        "bane",
                    )
                )
        rules.wild_sigil = "air" if rules.has("wild") else None
        if rules.wild_sigil in rules.forbidden:
            rules.wild_sigil = None
        awakened: list[str] = []
        for sigil_id in self.awaken:
            sigil = sigils.get(sigil_id)
            if sigil_id in awakened or sigil_id in rules.forbidden:
                continue
            if sigil.element in rules.banished:
                continue
            awakened.append(sigil_id)
        rules.awakened = awakened
        if rules.has("ward") and rules.forbidden:
            rules.effects["chains"] = False
        elif rules.forbidden:
            rules.effects["chains"] = True
        rules.scramble_seed = stream.below(2**31)
        rules.house = choose_house(spread)
        shadow_title = next((e.title for e in rules.edicts if e.position == "shadow"), "Nothing")
        rules.omen = (
            f"{rules.aspect.get('name', 'An unnamed aspect')}. "
            f"The Heart keeps {rules.resonance}. {shadow_title} holds the night."
        )
        return rules


def choose_house(spread: Spread) -> str:
    """Pick the heraldic House that presides over a sealed spread."""
    kept = list(spread.kept.values())
    score = sum((i + 1) * (dc.card.index + 1) for i, dc in enumerate(kept))
    score += 7 * sum(dc.reversed for dc in kept)
    return heraldry.HOUSES[score % len(heraldry.HOUSES)].id


def compute_rules(secret: bytes, spread: Spread) -> DayRules:
    """Compute the full rules of a sealed spread."""
    if not spread.sealed:
        raise ValueError("The spread has not been sealed: three cards must be kept first.")
    builder = _Builder(spread.day.isoformat())
    kept = spread.kept
    builder.crown(kept["crown"])
    builder.heart(kept["heart"])
    builder.shadow(kept["shadow"])
    for drawn in spread.burned:
        builder.burned(drawn)
    return builder.finish(secret, spread)


def preview(drawn: DrawnCard) -> dict[str, list[dict]]:
    """What a single card would do in each position — shown while choosing."""
    out: dict[str, list[dict]] = {}
    for position in ("crown", "heart", "shadow", "burned"):
        builder = _Builder("preview")
        getattr(builder, position)(drawn)
        out[position] = [e.to_dict() for e in builder.rules.edicts]
    return out


def rules_for_day(secret: bytes, day: dt.date, drawn: list[DrawnCard], keep) -> DayRules:
    """Convenience wrapper used by the server."""
    return compute_rules(secret, Spread(day, tuple(drawn), tuple(keep)))


# ---------------------------------------------------------------------------
# constraint checking


@dataclass
class Violation:
    rule: str
    message: str

    def to_dict(self) -> dict:
        return {"rule": self.rule, "message": self.message}


def check_constraints(title: str, body: str, rules: DayRules) -> list[Violation]:
    """Return every edict a note breaks (an empty list means the ink will take)."""
    c = rules.constraints
    text = f"{title}\n{body}"
    found = sigils.extract(text)
    out: list[Violation] = []
    expanded_body = sigils.expand_shortcodes(body)
    if c.char_limit is not None and len(expanded_body) > c.char_limit:
        out.append(
            Violation(
                "char_limit", f"The Vow allows {c.char_limit} characters; this note has {len(expanded_body)}."
            )
        )
    if len(found) < c.min_sigils:
        out.append(Violation("min_sigils", f"The night demands at least {_plural(c.min_sigils, 'sigil')}."))
    if c.min_words and len(words(sigils.strip(text))) < c.min_words:
        out.append(Violation("min_words", f"The note must grow to {c.min_words} words."))
    if c.begin_with_sigil and not sigils.starts_with_sigil(body):
        out.append(Violation("begin_with_sigil", "The Liturgy demands the note begin with a sigil."))
    if c.even_sigils and len(found) % 2:
        out.append(Violation("even_sigils", "Every sigil must have its partner."))
    if c.balanced_sigils:
        light = sum(sigils.get(s).polarity == "light" for s in found)
        if light * 2 != len(found):
            out.append(Violation("balanced_sigils", "Light and dark sigils must balance."))
    for sigil_id in c.require:
        if sigil_id not in found:
            glyph = sigils.get(sigil_id).glyph
            out.append(Violation("require", f"Every note tonight must bear {glyph}."))
    return out
