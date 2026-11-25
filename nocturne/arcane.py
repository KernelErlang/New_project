"""The Arcane Calculus — the hidden formulas that awaken rites.

When a note is inscribed, its words and sigils are weighed against the night's
edicts. Certain patterns perform a *rite*: an animation with its own sound. The
formulas are deliberately not shown in the interface — only a cryptic hint for each
undiscovered rite — so the Codex rewards experiment. (The full list lives in
``docs/FORBIDDEN_LORE.md`` for those who would rather not wonder.)
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Callable

from . import sigils
from .edicts import DayRules
from .numerology import digital_root, gematria, is_palindrome, is_prime, words

MAX_RITES = 3


@dataclass(frozen=True)
class Rite:
    id: str
    name: str
    tier: int  # 0 consequence, 1 minor, 2 major, 3 grand
    hint: str
    lore: str
    animation: str
    sound: str
    discoverable: bool = True

    def to_dict(self, revealed: bool = True) -> dict:
        return {
            "id": self.id,
            "name": self.name if revealed else "???",
            "tier": self.tier,
            "hint": self.hint,
            "lore": self.lore if revealed else None,
            "animation": self.animation,
            "sound": self.sound,
            "discovered": revealed,
        }


RITES: tuple[Rite, ...] = (
    Rite(
        "ouroboros",
        "The Ouroboros",
        3,
        "Gather the four, and let the end bite the beginning.",
        "Bear sigils of all four elements, and begin and end with the same sigil (five or "
        "more). Under the World, the four alone suffice. The Fool's wild sigil counts as "
        "every element, and ⛤ may stand in for one that is missing.",
        "ouroboros",
        "serpent",
    ),
    Rite(
        "master_number",
        "The Master Number",
        3,
        "Some numbers refuse to be reduced.",
        "When a note's weight reduces to 11, 22 or 33 before becoming a single digit.",
        "master",
        "organ",
    ),
    Rite(
        "resonance",
        "Resonance",
        3,
        "Words have weight. Weigh them to the number the Heart keeps.",
        "Sum the letters (A=1 … Z=26) of title and body and reduce the sum to one digit. "
        "If it equals the Heart's number, the night resonates. Under the Wheel the number "
        "turns with the hour.",
        "resonance",
        "chord",
    ),
    Rite(
        "crown_recognition",
        "The Crown Remembers",
        3,
        "Offer the Crown a tribute of sigils equal to its number.",
        "If the values of two or more sigils sum to the Crown card's number, the Crown "
        "remembers you. A sigil's value is the number of the card that rules it. Under the "
        "Emperor, within one is close enough.",
        "crown",
        "fanfare",
    ),
    Rite(
        "eclipse",
        "The Eclipse",
        2,
        "When the sun and the moon stand side by side.",
        "Set ☉ and ☽ next to one another.",
        "eclipse",
        "eclipse",
    ),
    Rite(
        "blood_moon",
        "The Blood Moon",
        2,
        "The moon drinks what Mars spills.",
        "Set ☽ beside ♂ — or bear ☽ and write the word 'blood'.",
        "bloodmoon",
        "heartbeat",
    ),
    Rite(
        "thirteenth_toll",
        "The Thirteenth Toll",
        2,
        "Thirteen is a door. Make your weight knock upon it.",
        "A note whose weight (the sum of its letters) is a multiple of thirteen.",
        "toll",
        "toll",
    ),
    Rite(
        "witching_hour",
        "The Witching Hour",
        2,
        "Some ink only wakes at midnight.",
        "Inscribe between midnight and one, or at exactly 3:33. Under the Moon the hour "
        "lasts from nine at night until five.",
        "witching",
        "witching",
    ),
    Rite(
        "nevermore",
        "Nevermore",
        2,
        "Quoth a certain dark bird…",
        "Write the word 'nevermore'.",
        "raven",
        "raven",
    ),
    Rite(
        "night_moths",
        "Night Moths",
        2,
        "Bones draw moths — but only after dark.",
        "Bear ☠ between nine at night and five in the morning (at any hour under Death).",
        "moths",
        "flutter",
    ),
    Rite(
        "tower_strike",
        "The Tower Strike",
        2,
        "Shout thrice beneath the storm.",
        "Bear ☈ and three exclamation marks (one under the Tower).",
        "lightning",
        "thunder",
    ),
    Rite(
        "balance",
        "The Even Scales",
        2,
        "Light and shadow, weighed and found equal.",
        "Use as many light sigils as dark ones, at least two of each (one under Justice).",
        "scales",
        "scales",
    ),
    Rite(
        "twin_flames",
        "Twin Flames",
        1,
        "Two candles, one flame.",
        "Write the same sigil twice in a row. Under the Lovers, anywhere in the note.",
        "twin",
        "twin",
    ),
    Rite(
        "conjunction",
        "The Conjunction",
        2,
        "Marry fire to water, or air to earth.",
        "Set sigils of opposite elements side by side. Under Temperance, anywhere.",
        "conjunction",
        "alchemy",
    ),
    Rite(
        "ember_storm",
        "Ember Storm",
        1,
        "Three sparks make a wildfire.",
        "Three fire sigils in one note (two under the Magician).",
        "embers",
        "fire",
    ),
    Rite(
        "drowned_tide",
        "The Drowned Tide",
        1,
        "Three drops make a flood.",
        "Three water sigils in one note (two under the Magician).",
        "tide",
        "water",
    ),
    Rite(
        "gale",
        "Gale of Feathers",
        1,
        "Three breaths make a storm.",
        "Three air sigils in one note (two under the Magician).",
        "gale",
        "wind",
    ),
    Rite(
        "thornbloom",
        "Thornbloom",
        1,
        "Three stones make a garden of thorns.",
        "Three earth sigils in one note (two under the Magician).",
        "thorns",
        "creak",
    ),
    Rite(
        "starfall",
        "Starfall",
        1,
        "Wish upon enough stars and they fall to you.",
        "Three star sigils — ✦ ✶ ☄ — in one note (one under the Star).",
        "starfall",
        "sparkle",
    ),
    Rite(
        "petal_rain",
        "Petal Rain",
        1,
        "Love grows where Venus walks beside a heart.",
        "Bear ♀ together with ❦ (♀ alone under the Empress).",
        "petals",
        "harp",
    ),
    Rite(
        "mirror_of_mercury",
        "Mirror of Mercury",
        2,
        "Words that read the same in the looking-glass.",
        "Title the note with a palindrome of five letters or more, or set ☿ three times. "
        "Under the Hanged Man, a palindrome anywhere will do.",
        "quicksilver",
        "glass",
    ),
    Rite(
        "wordless_prayer",
        "The Wordless Prayer",
        2,
        "Speak only in signs.",
        "A note of three or more sigils and not a single word.",
        "prayer",
        "choir",
    ),
    Rite(
        "prime_glint",
        "Prime Glint",
        1,
        "Indivisible weights shine alone.",
        "A note whose weight is a prime number greater than one hundred.",
        "glint",
        "glint",
    ),
    Rite(
        "chariot_streak",
        "The Chariot Streak",
        1,
        "Ride the quill faster than thought.",
        "Write sixty characters or more at 250 characters a minute (150 under the Chariot).",
        "streak",
        "gallop",
    ),
    Rite(
        "lantern_vigil",
        "Lantern Vigil",
        1,
        "A small light for the hour before dawn.",
        "Bear ✶ between four and six in the morning — or, under the Hermit, inscribe the night's first note.",
        "lantern",
        "chime",
    ),
    Rite(
        "trinity_rays",
        "Trinity of Rays",
        2,
        "Three crosses raise a cathedral of light.",
        "Bear ✠ three times (twice under the Hierophant).",
        "rays",
        "choir",
    ),
    Rite(
        "pact_chains",
        "Chains of the Pact",
        0,
        "Use what was forbidden.",
        "A forbidden sigil binds the note in chains: it can no longer be edited.",
        "chains",
        "chains",
    ),
    Rite(
        "warded",
        "The Ward Holds",
        0,
        "Defy the forbidden beneath a ward.",
        "Under Strength or a Bedrock Ward, forbidden sigils are inert and bind nothing.",
        "ward",
        "ward",
    ),
    Rite(
        "ashen",
        "Ashes",
        0,
        "Use what was banished.",
        "Sigils of a banished element crumble to ash and take no part in any rite.",
        "ash",
        "fizzle",
    ),
    Rite(
        "ink_settles",
        "The Ink Settles",
        0,
        "",
        "No rite stirs; the ink simply settles into the page.",
        "settle",
        "seal",
        discoverable=False,
    ),
)
BY_ID: dict[str, Rite] = {rite.id: rite for rite in RITES}
DISCOVERABLE: tuple[Rite, ...] = tuple(r for r in RITES if r.discoverable)


@dataclass
class Inscription:
    title: str
    body: str
    hour: int = 12
    minute: int = 0
    velocity: float = 0.0  # characters per minute while writing
    first_of_night: bool = False


@dataclass
class Reading:
    """Everything the calculus measures about a note."""

    found: list[str]
    active: list[str]
    states: list[str]
    words: list[str]
    weight: int
    root: int
    master_root: int
    sigil_sum: int
    elements: Counter = field(default_factory=Counter)
    light: int = 0
    dark: int = 0
    exclamations: int = 0
    wild: bool = False
    pairs: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class Invocation:
    performed: list[dict]
    bound: bool
    reading: Reading

    @property
    def rite_ids(self) -> list[str]:
        return [r["id"] for r in self.performed]

    @property
    def flames(self) -> int:
        return min(MAX_RITES, sum(1 for r in self.performed if BY_ID[r["id"]].tier > 0))

    def to_dict(self) -> dict:
        return {
            "performed": self.performed,
            "bound": self.bound,
            "flames": self.flames,
            "sigils": [
                {"id": sid, "state": state} for sid, state in zip(self.reading.found, self.reading.states)
            ],
            "weight": self.reading.weight,
            "sigil_sum": self.reading.sigil_sum,
        }


def read(note: Inscription, rules: DayRules) -> Reading:
    text = f"{note.title}\n{note.body}"
    found = sigils.extract(text)
    states = [rules.sigil_state(sid) for sid in found]
    active = [sid for sid, state in zip(found, states) if state not in ("ashen", "forbidden")]
    plain_text = sigils.strip(text)
    weight = gematria(plain_text)
    reading = Reading(
        found=found,
        active=active,
        states=states,
        words=words(plain_text),
        weight=weight,
        root=digital_root(weight),
        master_root=digital_root(weight, keep_master=True),
        sigil_sum=sum(sigils.get(sid).value for sid in active),
        exclamations=text.count("!"),
        wild=rules.wild_sigil is not None and rules.wild_sigil in active,
    )
    reading.pairs = _neighbours(text, rules)
    for sid in active:
        sigil = sigils.get(sid)
        reading.elements[sigil.element] += 1
        if sigil.polarity == "light":
            reading.light += 1
        else:
            reading.dark += 1
    return reading


def _neighbours(text: str, rules: DayRules) -> list[tuple[str, str]]:
    """Pairs of active sigils standing side by side (only whitespace between them)."""
    pairs: list[tuple[str, str]] = []
    previous: str | None = None
    for ch in sigils.expand_shortcodes(text):
        if ch in sigils.VARIATION_SELECTORS or (ch.isspace() and ch != "\n"):
            continue
        sigil = sigils.BY_GLYPH.get(ch)
        if sigil is None or rules.sigil_state(sigil.id) in ("ashen", "forbidden"):
            previous = None
            continue
        if previous is not None:
            pairs.append((previous, sigil.id))
        previous = sigil.id
    return pairs


def _adjacent(pairs: list[tuple[str, str]], test: Callable[[str, str], bool]) -> list[str] | None:
    for a, b in pairs:
        if test(a, b):
            return [a, b]
    return None


def _pair(first: str, second: str) -> Callable[[str, str], bool]:
    return lambda a, b: {a, b} == {first, second}


def _opposed(a: str, b: str) -> bool:
    ea, eb = sigils.get(a).element, sigils.get(b).element
    return sigils.OPPOSITES.get(ea) == eb


def _element_count(r: Reading, element: str) -> int:
    return r.elements[element] + (1 if r.wild else 0)


def _night(hour: int) -> bool:
    return hour >= 21 or hour < 5


def _check(rite_id: str, note: Inscription, r: Reading, rules: DayRules) -> list[str] | None:
    """Return the sigils involved if ``rite_id`` is performed, else ``None``."""
    a = r.active
    has = rules.has
    if rite_id == "ouroboros":
        present = {e for e in sigils.ELEMENTS if r.elements[e]}
        if r.wild:
            present = set(sigils.ELEMENTS)
        missing = 4 - len(present)
        if missing > (1 if "quintessence" in a else 0):
            return None
        if has("ouroboros") or (len(a) >= 5 and a[0] == a[-1]):
            return a
        return None
    if rite_id == "master_number":
        return a if r.master_root in (11, 22, 33) else None
    if rite_id == "resonance":
        return a if r.weight and r.root == rules.resonance_at(note.hour) else None
    if rite_id == "crown_recognition":
        tolerance = 1 if has("decree") else 0
        if len(a) >= 2 and abs(r.sigil_sum - rules.crown_value) <= tolerance:
            return a
        return None
    if rite_id == "eclipse":
        return _adjacent(r.pairs, _pair("sol", "luna"))
    if rite_id == "blood_moon":
        pair = _adjacent(r.pairs, _pair("luna", "mars"))
        if pair:
            return pair
        return ["luna"] if "luna" in a and "blood" in r.words else None
    if rite_id == "thirteenth_toll":
        return a if r.weight and r.weight % 13 == 0 else None
    if rite_id == "witching_hour":
        if has("illusion") and _night(note.hour):
            return a
        return a if note.hour == 0 or (note.hour == 3 and note.minute == 33) else None
    if rite_id == "nevermore":
        return a if "nevermore" in r.words else None
    if rite_id == "night_moths":
        if "skull" in a and (has("moths") or _night(note.hour)):
            return ["skull"]
        return None
    if rite_id == "tower_strike":
        need = 1 if has("tremor") else 3
        return ["thunder"] if "thunder" in a and r.exclamations >= need else None
    if rite_id == "balance":
        need = 1 if has("balance") else 2
        return a if r.light == r.dark and r.light >= need else None
    if rite_id == "twin_flames":
        if has("twin"):
            twins = [sid for sid, n in Counter(a).items() if n >= 2]
            return twins[:1] * 2 if twins else None
        return _adjacent(r.pairs, lambda x, y: x == y)
    if rite_id == "conjunction":
        if has("fusion"):
            for e in ("fire", "air"):
                if r.elements[e] and r.elements[sigils.OPPOSITES[e]]:
                    return [s for s in a if sigils.get(s).element in (e, sigils.OPPOSITES[e])]
            return None
        return _adjacent(r.pairs, _opposed)
    storms = {"ember_storm": "fire", "drowned_tide": "water", "gale": "air", "thornbloom": "earth"}
    if rite_id in storms:
        element = storms[rite_id]
        need = 2 if has("four_tools") else 3
        if _element_count(r, element) >= need:
            return [s for s in a if sigils.get(s).element == element] or a
        return None
    if rite_id == "starfall":
        need = 1 if has("starfield") else 3
        stars = [s for s in a if s in sigils.STAR_SIGILS]
        return stars if len(stars) >= need else None
    if rite_id == "petal_rain":
        if "venus" in a and ("heart" in a or has("bloom")):
            return [s for s in a if s in ("venus", "heart")]
        return None
    if rite_id == "mirror_of_mercury":
        if a.count("mercury") >= 3 or is_palindrome(note.title):
            return [s for s in a if s == "mercury"] or a
        if has("inversion"):
            body = sigils.strip(note.body)
            if is_palindrome(body) or any(is_palindrome(w) for w in r.words):
                return a
        return None
    if rite_id == "wordless_prayer":
        return a if len(a) >= 3 and not r.words else None
    if rite_id == "prime_glint":
        return a if r.weight > 100 and is_prime(r.weight) else None
    if rite_id == "chariot_streak":
        need = 150 if has("velocity") else 250
        if note.velocity >= need and len(note.body) >= 60:
            return a
        return None
    if rite_id == "lantern_vigil":
        if has("lantern") and note.first_of_night:
            return a
        return ["lantern"] if "lantern" in a and 4 <= note.hour < 6 else None
    if rite_id == "trinity_rays":
        need = 2 if has("illuminate") else 3
        return ["cross"] * a.count("cross") if a.count("cross") >= need else None
    raise KeyError(rite_id)


def _performance(rite: Rite, used: list[str], rules: DayRules) -> dict:
    awakened = any(s in rules.awakened or s == rules.wild_sigil for s in used)
    intensity = 1.0 + (0.6 if awakened else 0.0) + 0.08 * min(len(used), 5)
    data = rite.to_dict()
    data.update(
        {
            "awakened": awakened,
            "intensity": round(min(intensity, 2.0), 2),
            "sigils": used,
        }
    )
    return data


def invoke(note: Inscription, rules: DayRules) -> Invocation:
    """Weigh a note against the night's edicts and return the rites it performs."""
    reading = read(note, rules)
    consequences: list[dict] = []
    forbidden_used = [sid for sid, st in zip(reading.found, reading.states) if st == "forbidden"]
    ashen_used = [sid for sid, st in zip(reading.found, reading.states) if st == "ashen"]
    bound = False
    if forbidden_used:
        if rules.has("ward"):
            consequences.append(_performance(BY_ID["warded"], forbidden_used, rules))
        else:
            bound = True
            consequences.append(_performance(BY_ID["pact_chains"], forbidden_used, rules))
    if ashen_used:
        consequences.append(_performance(BY_ID["ashen"], ashen_used, rules))

    performed: list[dict] = []
    candidates = sorted((r for r in DISCOVERABLE if r.tier > 0), key=lambda r: -r.tier)
    for rite in candidates:
        used = _check(rite.id, note, reading, rules)
        if used is not None:
            performed.append(_performance(rite, used, rules))
        if len(performed) >= MAX_RITES:
            break
    if not performed and not consequences:
        performed.append(_performance(BY_ID["ink_settles"], [], rules))
    return Invocation(consequences + performed, bound, reading)


def codex(discovered: dict[str, dict]) -> list[dict]:
    """The Codex of Rites: hints for the unknown, lore for the discovered."""
    out = []
    for rite in DISCOVERABLE:
        entry = rite.to_dict(revealed=rite.id in discovered)
        if rite.id in discovered:
            entry.update(discovered[rite.id])
        out.append(entry)
    return out
