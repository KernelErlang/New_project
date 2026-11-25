"""The seventy-eight cards of the Nocturne deck.

The deck follows the traditional tarot structure — twenty-two Major Arcana and four
suits of fourteen Minor Arcana — but its epigraphs and mechanics are the Codex's own.
"""

from __future__ import annotations

from dataclasses import dataclass, field

SUITS = ("wands", "cups", "swords", "pentacles")
SUIT_ELEMENT = {"wands": "fire", "cups": "water", "swords": "air", "pentacles": "earth"}
SUIT_NOUN = {"wands": "embers", "cups": "tides", "swords": "whispers", "pentacles": "stones"}
SUIT_DOMAIN = {
    "wands": ("passion", "will"),
    "cups": ("feeling", "dreams"),
    "swords": ("thought", "truth"),
    "pentacles": ("matter", "craft"),
}

ROMAN = (
    "0",
    "I",
    "II",
    "III",
    "IV",
    "V",
    "VI",
    "VII",
    "VIII",
    "IX",
    "X",
    "XI",
    "XII",
    "XIII",
    "XIV",
    "XV",
    "XVI",
    "XVII",
    "XVIII",
    "XIX",
    "XX",
    "XXI",
)

RANK_NAMES = {
    1: "Ace",
    2: "Two",
    3: "Three",
    4: "Four",
    5: "Five",
    6: "Six",
    7: "Seven",
    8: "Eight",
    9: "Nine",
    10: "Ten",
    11: "Page",
    12: "Knight",
    13: "Queen",
    14: "King",
}

_RANK_UPRIGHT = {
    1: ("seed", "potential"),
    2: ("choice", "partnership"),
    3: ("growth", "kinship"),
    4: ("rest", "stability"),
    5: ("strife", "loss"),
    6: ("passage", "generosity"),
    7: ("trial", "resolve"),
    8: ("motion", "diligence"),
    9: ("vigil", "fulfilment"),
    10: ("culmination", "burden"),
    11: ("message", "curiosity"),
    12: ("pursuit", "zeal"),
    13: ("intuition", "grace"),
    14: ("command", "mastery"),
}
_RANK_REVERSED = {
    1: ("delay", "blockage"),
    2: ("indecision", "imbalance"),
    3: ("isolation", "excess"),
    4: ("restlessness", "stagnation"),
    5: ("reconciliation", "release"),
    6: ("homesickness", "debt"),
    7: ("doubt", "surrender"),
    8: ("haste", "frustration"),
    9: ("paranoia", "exhaustion"),
    10: ("collapse", "letting go"),
    11: ("gossip", "naivety"),
    12: ("recklessness", "retreat"),
    13: ("coldness", "insecurity"),
    14: ("tyranny", "weakness"),
}
_RANK_LINES = {
    1: "A single spark of {noun}: the first word of a long sentence.",
    2: "Two {noun} that cannot both be chosen.",
    3: "Three {noun} braided into something stronger.",
    4: "Four {noun} at rest behind a locked gate.",
    5: "Five {noun} quarrelling in the dark.",
    6: "Six {noun} carried across the black water.",
    7: "Seven {noun} held against the coming night.",
    8: "Eight {noun} racing the candle to its end.",
    9: "Nine {noun} kept by a sleepless warden.",
    10: "Ten {noun}, and the weight of every one.",
    11: "A page who carries {noun} like letters sealed in wax.",
    12: "A knight who rides toward the {noun} and never back.",
    13: "A queen who listens to the {noun}, and is answered.",
    14: "A king whose crown is forged of {noun}.",
}


@dataclass(frozen=True)
class Card:
    id: str
    index: int
    name: str
    arcana: str  # "major" | "minor"
    suit: str | None
    rank: int  # majors 0..21, minors 1..14
    numeral: str
    element: str
    sigil: str  # ruling sigil for majors, element sigil for minors
    upright: tuple[str, ...]
    reversed: tuple[str, ...]
    epigraph: str
    arcanum: str | None = None
    tags: tuple[str, ...] = field(default=())

    @property
    def is_major(self) -> bool:
        return self.arcana == "major"

    @property
    def value(self) -> int:
        """The card's number for the formulas (the Fool counts as 22)."""
        if self.is_major and self.rank == 0:
            return 22
        return self.rank

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "index": self.index,
            "name": self.name,
            "arcana": self.arcana,
            "suit": self.suit,
            "rank": self.rank,
            "numeral": self.numeral,
            "element": self.element,
            "sigil": self.sigil,
            "upright": list(self.upright),
            "reversed_keywords": list(self.reversed),
            "epigraph": self.epigraph,
            "arcanum": self.arcanum,
            "value": self.value,
            "art": f"/art/card/{self.id}.svg",
        }


# (name, element, ruling sigil, arcanum, upright, reversed, epigraph)
_MAJORS = (
    (
        "The Fool",
        "air",
        "air",
        "wild",
        ("beginnings", "the leap", "innocence"),
        ("recklessness", "hesitation", "folly"),
        "One step more, and the abyss becomes a road.",
    ),
    (
        "The Magician",
        "air",
        "mercury",
        "four_tools",
        ("will", "craft", "manifestation"),
        ("trickery", "scattered power", "vanity"),
        "All four tools lie upon the table, and none of them are toys.",
    ),
    (
        "The High Priestess",
        "water",
        "ankh",
        "veil",
        ("secrets", "intuition", "the unseen"),
        ("hidden agendas", "broken silence", "doubt"),
        "Behind the veil there is another veil, and she keeps both.",
    ),
    (
        "The Empress",
        "earth",
        "venus",
        "bloom",
        ("abundance", "nurture", "beauty"),
        ("smothering", "stagnation", "vanity"),
        "Where she walks, the graves grow roses.",
    ),
    (
        "The Emperor",
        "fire",
        "mars",
        "decree",
        ("order", "structure", "authority"),
        ("tyranny", "rigidity", "coldness"),
        "Stone remembers the hand that laid it.",
    ),
    (
        "The Hierophant",
        "earth",
        "cross",
        "illuminate",
        ("tradition", "doctrine", "ritual"),
        ("heresy", "rebellion", "hollow vows"),
        "Every rite was once a rebellion that won.",
    ),
    (
        "The Lovers",
        "air",
        "heart",
        "twin",
        ("union", "choice", "harmony"),
        ("discord", "temptation", "imbalance"),
        "Two candles, one shadow.",
    ),
    (
        "The Chariot",
        "water",
        "comet",
        "velocity",
        ("drive", "triumph", "willpower"),
        ("aimlessness", "collision", "lost reins"),
        "Hold the reins of two black horses that despise each other.",
    ),
    (
        "Strength",
        "fire",
        "sulfur",
        "ward",
        ("courage", "patience", "mastery of self"),
        ("doubt", "rage", "weakness"),
        "The beast lies down, not from fear, but from love.",
    ),
    (
        "The Hermit",
        "earth",
        "lantern",
        "lantern",
        ("solitude", "insight", "guidance"),
        ("isolation", "withdrawal", "lost way"),
        "A single lantern is a whole sky to the lost.",
    ),
    (
        "Wheel of Fortune",
        "air",
        "jupiter",
        "wheel",
        ("cycles", "fate", "turning point"),
        ("ill luck", "resistance", "chaos"),
        "What rises is already falling; what falls is already rising.",
    ),
    (
        "Justice",
        "air",
        "scales",
        "balance",
        ("truth", "fairness", "consequence"),
        ("injustice", "dishonesty", "evasion"),
        "The scales do not care for your reasons.",
    ),
    (
        "The Hanged Man",
        "water",
        "water",
        "inversion",
        ("surrender", "new perspective", "pause"),
        ("stalling", "martyrdom", "indecision"),
        "Upside down, the stars are a well to drink from.",
    ),
    (
        "Death",
        "water",
        "skull",
        "moths",
        ("endings", "transformation", "release"),
        ("stagnation", "fear of change", "decay"),
        "Nothing is lost. It is only rearranged in the dark.",
    ),
    (
        "Temperance",
        "fire",
        "alembic",
        "fusion",
        ("balance", "alchemy", "patience"),
        ("excess", "imbalance", "haste"),
        "Pour fire into water slowly, and you make neither steam nor ruin.",
    ),
    (
        "The Devil",
        "earth",
        "pact",
        "chains",
        ("bondage", "desire", "the shadow self"),
        ("release", "breaking free", "reclaiming"),
        "The chains are loose. That is the cruelty.",
    ),
    (
        "The Tower",
        "fire",
        "thunder",
        "tremor",
        ("upheaval", "revelation", "sudden change"),
        ("averted ruin", "dread", "delay"),
        "Lightning is only the sky telling the truth.",
    ),
    (
        "The Star",
        "air",
        "star",
        "starfield",
        ("hope", "renewal", "serenity"),
        ("despair", "disconnection", "faithlessness"),
        "Even ash, scattered high enough, becomes a constellation.",
    ),
    (
        "The Moon",
        "water",
        "luna",
        "illusion",
        ("dreams", "illusion", "intuition"),
        ("clarity returning", "repressed fear", "deceit"),
        "The path is real. The hounds are real. The light is lying.",
    ),
    (
        "The Sun",
        "fire",
        "sol",
        "gilded",
        ("joy", "vitality", "clarity"),
        ("dimmed joy", "pride", "glare"),
        "Even the grave is warm at noon.",
    ),
    (
        "Judgement",
        "fire",
        "fire",
        "echo",
        ("reckoning", "rebirth", "a calling"),
        ("self-doubt", "refusal", "silence"),
        "The trumpet sounds for the living first.",
    ),
    (
        "The World",
        "earth",
        "saturn",
        "ouroboros",
        ("completion", "wholeness", "integration"),
        ("incompletion", "delay", "loose ends"),
        "The serpent finishes its meal and finds it was hungry for itself.",
    ),
)


def _build_deck() -> tuple[Card, ...]:
    cards: list[Card] = []
    for rank, (name, element, sigil, arcanum, up, rev, epigraph) in enumerate(_MAJORS):
        cards.append(
            Card(
                id=f"major-{rank:02d}",
                index=len(cards),
                name=name,
                arcana="major",
                suit=None,
                rank=rank,
                numeral=ROMAN[rank],
                element=element,
                sigil=sigil,
                upright=up,
                reversed=rev,
                epigraph=epigraph,
                arcanum=arcanum,
            )
        )
    for suit in SUITS:
        domain = SUIT_DOMAIN[suit]
        for rank in range(1, 15):
            rank_name = RANK_NAMES[rank]
            cards.append(
                Card(
                    id=f"{suit}-{rank:02d}",
                    index=len(cards),
                    name=f"{rank_name} of {suit.title()}",
                    arcana="minor",
                    suit=suit,
                    rank=rank,
                    numeral=rank_name if rank > 10 or rank == 1 else str(rank),
                    element=SUIT_ELEMENT[suit],
                    sigil=SUIT_ELEMENT[suit],
                    upright=(*_RANK_UPRIGHT[rank], domain[0]),
                    reversed=(*_RANK_REVERSED[rank], domain[1]),
                    epigraph=_RANK_LINES[rank].format(noun=SUIT_NOUN[suit]),
                    tags=("court",) if rank > 10 else (),
                )
            )
    return tuple(cards)


DECK: tuple[Card, ...] = _build_deck()
BY_ID: dict[str, Card] = {card.id: card for card in DECK}
MAJORS: tuple[Card, ...] = tuple(card for card in DECK if card.is_major)


def get(card_id: str) -> Card:
    """Return a card by id, raising ``KeyError`` for unknown ids."""
    return BY_ID[card_id]


def catalogue() -> list[dict]:
    """The whole deck, serialisable to JSON."""
    return [card.to_dict() for card in DECK]
