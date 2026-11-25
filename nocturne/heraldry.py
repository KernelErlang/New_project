"""Heraldry: the twelve Houses of the night and a forge for personal crests.

Each sealed night is presided over by one House, whose crest seals every note
inscribed that night. Crests are composed from a shield shape, a field division,
tinctures, a charge, a supporter behind the shield and a small crest above it.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import asdict, dataclass
from functools import lru_cache

from .glyphs import emblem, esc
from .rng import FateStream

TINCTURES = {
    "or": "#c9a227",
    "argent": "#d8d2c4",
    "gules": "#8a1c1c",
    "azure": "#1f3a6b",
    "sable": "#17131b",
    "vert": "#2e5233",
    "purpure": "#5a2a6e",
    "sanguine": "#6b1424",
    "cinder": "#4a4644",
}
METALS = ("or", "argent")
COLOURS = ("gules", "azure", "sable", "vert", "purpure", "sanguine", "cinder")

SHIELDS = {
    "heater": "M20 30H220V130C220 190 180 230 120 254C60 230 20 190 20 130Z",
    "french": "M20 30H220V170C220 210 190 234 150 240Q126 242 120 256Q114 242 90 240C50 234 20 210 20 170Z",
    "gothic": "M20 40Q120 18 220 40V130C220 190 180 230 120 256C60 230 20 190 20 130Z",
    "kite": "M120 26C170 30 206 60 206 110C206 170 160 220 120 256C80 220 34 170 34 110C34 60 70 30 120 26Z",
    "swiss": "M20 30Q70 52 120 30Q170 52 220 30V140C220 195 180 232 120 254C60 232 20 195 20 140Z",
}
DIVISIONS = (
    "plain",
    "per_pale",
    "per_fess",
    "per_bend",
    "per_bend_sinister",
    "quarterly",
    "per_chevron",
    "per_saltire",
    "chief",
    "pale",
    "fess",
    "chevron",
    "bordure",
    "gyronny",
    "paly",
    "barry",
    "checky",
)
SUPPORTERS = ("none", "crossed_swords", "crossed_keys", "rays", "laurel", "wings")
CHARGES = (
    "crescent",
    "star",
    "star8",
    "candle",
    "chalice",
    "skull",
    "crown",
    "tower",
    "bell",
    "hourglass",
    "key",
    "rose",
    "moth",
    "raven",
    "serpent",
    "eye",
    "dagger",
    "flame",
    "lantern",
    "heart",
    "droplet",
    "sun",
    "scales",
    "wheel",
)
TOPPERS = ("none", "crescent", "star", "crown", "flame", "eye", "skull", "droplet")


@dataclass(frozen=True)
class Crest:
    shape: str
    division: str
    field: tuple[str, str]
    charge: str
    charge_tincture: str
    arrangement: str  # "single" | "three"
    supporter: str
    topper: str


@dataclass(frozen=True)
class House:
    id: str
    name: str
    motto: str
    blurb: str
    crest: Crest

    def to_dict(self) -> dict:
        data = asdict(self)
        data["crest"]["field"] = list(self.crest.field)
        data["art"] = f"/art/crest/{self.id}.svg"
        return data


HOUSES: tuple[House, ...] = (
    House(
        "vesperine",
        "House Vesperine",
        "We keep the last light.",
        "Candle-keepers of the evening bell, who light the dead their way home.",
        Crest(
            "gothic", "per_pale", ("sable", "argent"), "candle", "or", "single", "crossed_keys", "crescent"
        ),
    ),
    House(
        "ashen-cantors",
        "The Ashen Cantors",
        "Sing, though the throat be smoke.",
        "A choir of the burned, whose hymns rise like cinders.",
        Crest("heater", "chief", ("cinder", "or"), "moth", "argent", "single", "rays", "flame"),
    ),
    House(
        "pale-chalice",
        "Order of the Pale Chalice",
        "Drink, and remember.",
        "Keepers of the cup that holds every forgotten tear.",
        Crest("kite", "bordure", ("azure", "argent"), "chalice", "argent", "single", "wings", "star"),
    ),
    House(
        "ravenmourne",
        "House Ravenmourne",
        "Nevermore is not never.",
        "Messengers between the quick and the dead, cloaked in black feathers.",
        Crest(
            "heater", "per_bend", ("sable", "gules"), "raven", "argent", "single", "crossed_swords", "crown"
        ),
    ),
    House(
        "thornwake",
        "The Thornwake Covenant",
        "Every rose is a wound kept.",
        "Gardeners of the cemetery hedge, sworn to the beauty that bleeds.",
        Crest("french", "quarterly", ("vert", "argent"), "rose", "gules", "single", "laurel", "none"),
    ),
    House(
        "gloamspire",
        "House Gloamspire",
        "Above the fog, the bells.",
        "Bell-ringers of the highest tower, who see the dusk come first.",
        Crest("swiss", "per_fess", ("purpure", "sable"), "tower", "or", "single", "rays", "star"),
    ),
    House(
        "lantern-wardens",
        "The Lantern Wardens",
        "Hold the flame, not the hand.",
        "Night-watchers of the roads between villages and graves.",
        Crest("gothic", "plain", ("sable", "or"), "lantern", "or", "single", "crossed_keys", "flame"),
    ),
    House(
        "morrowbane",
        "House Morrowbane",
        "Tomorrow is a debt.",
        "Chroniclers who count every grain of sand that falls.",
        Crest(
            "heater", "per_saltire", ("argent", "sable"), "hourglass", "gules", "single", "wings", "crescent"
        ),
    ),
    House(
        "hollow-crown",
        "Order of the Hollow Crown",
        "Kings are only heavy hats.",
        "Deposed royalty who rule the empty halls by candlelight.",
        Crest("kite", "chevron", ("gules", "or"), "crown", "or", "three", "crossed_swords", "none"),
    ),
    House(
        "drowned-bell",
        "The Drowned Bell",
        "Toll beneath the waves.",
        "Mariners of the sunken chapel whose bell still rings at low tide.",
        Crest("french", "barry", ("azure", "argent"), "bell", "sable", "single", "laurel", "droplet"),
    ),
    House(
        "sepulchre",
        "House Sepulchre",
        "We are what remains.",
        "Stonemasons of tombs, patient as the marble they carve.",
        Crest("heater", "per_pale", ("sable", "cinder"), "skull", "argent", "single", "wings", "crown"),
    ),
    House(
        "starless-synod",
        "The Starless Synod",
        "Count the dark between.",
        "Astronomers of the absent stars, who map the spaces where light is not.",
        Crest("gothic", "gyronny", ("purpure", "sable"), "star8", "argent", "single", "rays", "eye"),
    ),
)
BY_ID: dict[str, House] = {house.id: house for house in HOUSES}


def get(house_id: str) -> House:
    return BY_ID[house_id]


# ---------------------------------------------------------------------------
# rendering


def _division(division: str, c1: str, c2: str) -> str:
    """Field division drawn over the 240×280 crest box (clipped to the shield later)."""
    if division == "plain":
        return ""
    if division == "per_pale":
        return f'<rect x="120" y="0" width="120" height="280" fill="{c2}"/>'
    if division == "per_fess":
        return f'<rect x="0" y="140" width="240" height="140" fill="{c2}"/>'
    if division == "per_bend":
        return f'<polygon points="20,30 240,260 0,260 0,30" fill="{c2}"/>'
    if division == "per_bend_sinister":
        return f'<polygon points="220,30 0,260 240,260 240,30" fill="{c2}"/>'
    if division == "quarterly":
        return (
            f'<rect x="120" y="0" width="120" height="140" fill="{c2}"/>'
            f'<rect x="0" y="140" width="120" height="140" fill="{c2}"/>'
        )
    if division == "per_chevron":
        return f'<polygon points="0,280 0,230 120,110 240,230 240,280" fill="{c2}"/>'
    if division == "per_saltire":
        return (
            f'<polygon points="0,0 120,140 0,280" fill="{c2}"/>'
            f'<polygon points="240,0 120,140 240,280" fill="{c2}"/>'
        )
    if division == "chief":
        return f'<rect x="0" y="0" width="240" height="88" fill="{c2}"/>'
    if division == "pale":
        return f'<rect x="92" y="0" width="56" height="280" fill="{c2}"/>'
    if division == "fess":
        return f'<rect x="0" y="116" width="240" height="50" fill="{c2}"/>'
    if division == "chevron":
        return f'<polygon points="0,232 120,104 240,232 240,282 120,154 0,282" fill="{c2}"/>'
    if division == "bordure":
        return ""  # drawn as a stroke after the charges
    if division == "gyronny":
        out = []
        corners = [(120, 0), (240, 0), (240, 140), (240, 280), (120, 280), (0, 280), (0, 140), (0, 0)]
        for i in range(0, 8, 2):
            a, b = corners[i], corners[(i + 1) % 8]
            out.append(f'<polygon points="120,140 {a[0]},{a[1]} {b[0]},{b[1]}" fill="{c2}"/>')
        return "".join(out)
    if division == "paly":
        return "".join(
            f'<rect x="{x}" y="0" width="40" height="280" fill="{c2}"/>' for x in range(40, 240, 80)
        )
    if division == "barry":
        return "".join(
            f'<rect x="0" y="{y}" width="240" height="28" fill="{c2}"/>' for y in range(58, 280, 56)
        )
    if division == "checky":
        return "".join(
            f'<rect x="{x}" y="{y}" width="40" height="40" fill="{c2}"/>'
            for y in range(0, 280, 40)
            for x in range((y // 40) % 2 * 40, 240, 80)
        )
    raise ValueError(f"unknown division {division!r}")


def _supporter(kind: str, gold: str, dark: str) -> str:
    if kind == "crossed_swords":
        return emblem("sword", 70, 150, 190, gold, dark, -38) + emblem("sword", 170, 150, 190, gold, dark, 38)
    if kind == "crossed_keys":
        return emblem("key", 66, 150, 170, gold, dark, -36) + emblem("key", 174, 150, 170, gold, dark, 36)
    if kind == "rays":
        rays = "".join(
            f'<polygon points="114,150 126,150 120,{-6 if i % 2 else 14}" fill="{gold}" '
            f'opacity="{0.5 if i % 2 else 0.3}" transform="rotate({a} 120 150)"/>'
            for i, a in enumerate(range(0, 360, 15))
        )
        return f"<g>{rays}</g>"
    if kind == "laurel":
        leaves = []
        for side in (-1, 1):
            for i in range(9):
                angle = 200 - i * 17 if side < 0 else -20 + i * 17
                rad = math.radians(angle)
                x = 120 + 118 * math.cos(rad)
                y = 160 + 112 * math.sin(rad)
                rot = angle + (90 if side > 0 else -90)
                leaves.append(
                    f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="7" ry="15" fill="{gold}" '
                    f'opacity=".85" transform="rotate({rot:.0f} {x:.1f} {y:.1f})"/>'
                )
        return "".join(leaves)
    if kind == "wings":
        wing = (
            "M0 0C-30 -10 -70 -40 -96 -86C-84 -48 -88 -30 -100 -14C-80 -22 -70 -12 -84 10"
            "C-64 2 -50 10 -60 32C-40 18 -24 18 -10 30Z"
        )
        return (
            f'<path d="{wing}" fill="{gold}" opacity=".85" transform="translate(64 130)"/>'
            f'<path d="{wing}" fill="{gold}" opacity=".85" '
            f'transform="translate(176 130) scale(-1 1)"/>'
        )
    return ""


def render_crest(crest: Crest, title: str = "Crest", uid: str = "c") -> str:
    """Render a crest as a standalone SVG document."""
    shield = SHIELDS[crest.shape]
    c1, c2 = (TINCTURES[t] for t in crest.field)
    charge = TINCTURES[crest.charge_tincture]
    gold, dark = TINCTURES["or"], "#0b0809"
    if crest.charge_tincture == "or":
        gold = "#e4c46a"
    shade = dark if crest.charge_tincture in METALS else "#e9e2d0"
    if crest.arrangement == "three":
        charges = (
            emblem(crest.charge, 82, 104, 62, charge, shade)
            + emblem(crest.charge, 158, 104, 62, charge, shade)
            + emblem(crest.charge, 120, 186, 62, charge, shade)
        )
    else:
        charges = emblem(crest.charge, 120, 140, 112, charge, shade)
    bordure = ""
    if crest.division == "bordure":
        bordure = (
            f'<path d="{shield}" fill="none" stroke="{c2}" stroke-width="30" clip-path="url(#{uid}-clip)"/>'
        )
    topper = ""
    if crest.topper != "none":
        topper = emblem(crest.topper, 120, 14, 34, gold, dark)
    ribbon = (
        f'<path d="M30 268Q120 292 210 268L222 284Q120 306 18 284Z" fill="{TINCTURES["sanguine"]}"'
        f' stroke="{gold}" stroke-width="1.5"/>'
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -8 240 312" role="img" '
        f'aria-label="{esc(title)}">'
        f"<title>{esc(title)}</title>"
        f'<defs><clipPath id="{uid}-clip"><path d="{shield}"/></clipPath>'
        f'<radialGradient id="{uid}-sheen" cx="35%" cy="25%" r="80%">'
        f'<stop offset="0" stop-color="#fff" stop-opacity=".22"/>'
        f'<stop offset=".6" stop-color="#fff" stop-opacity="0"/>'
        f'<stop offset="1" stop-color="#000" stop-opacity=".35"/></radialGradient></defs>'
        f"{_supporter(crest.supporter, gold, dark)}"
        f'<g clip-path="url(#{uid}-clip)"><rect x="0" y="0" width="240" height="280" fill="{c1}"/>'
        f"{_division(crest.division, c1, c2)}{charges}</g>{bordure}"
        f'<path d="{shield}" fill="url(#{uid}-sheen)"/>'
        f'<path d="{shield}" fill="none" stroke="{gold}" stroke-width="5"/>'
        f'<path d="{shield}" fill="none" stroke="{dark}" stroke-width="1.5" '
        f'transform="translate(120 142) scale(.94) translate(-120 -142)" opacity=".8"/>'
        f"{topper}{ribbon}</svg>"
    )


@lru_cache(maxsize=64)
def house_svg(house_id: str) -> str:
    house = get(house_id)
    return render_crest(house.crest, house.name, uid=house.id)


def forge(name: str) -> Crest:
    """Forge a personal crest from any name or motto (deterministic)."""
    seed = hashlib.sha256(("nocturne/forge\x1f" + name.strip().lower()).encode()).digest()
    stream = FateStream(seed)
    metal, colour = stream.choice(METALS), stream.choice(COLOURS)
    field = (metal, colour) if stream.chance(1, 2) else (colour, metal)
    division = stream.choice(DIVISIONS)
    charge_tincture = field[1] if division == "plain" else stream.choice(METALS)
    if division == "plain":
        charge_tincture = metal if field[0] != metal else colour
    return Crest(
        shape=stream.choice(tuple(SHIELDS)),
        division=division,
        field=field,
        charge=stream.choice(CHARGES),
        charge_tincture=charge_tincture,
        arrangement="three" if stream.chance(1, 4) else "single",
        supporter=stream.choice(SUPPORTERS),
        topper=stream.choice(TOPPERS),
    )


def forged_svg(name: str) -> str:
    label = name.strip() or "Nameless"
    return render_crest(forge(label), f"Crest of {label}", uid="forged")


def catalogue() -> list[dict]:
    return [house.to_dict() for house in HOUSES]
