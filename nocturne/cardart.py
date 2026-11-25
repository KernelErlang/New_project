"""Procedural art for the tarot cards: gothic frames, arched windows and emblems.

Card faces carry no text — the page lays the card's numeral and name over the art
in its own fonts — but each SVG has a ``<title>`` for accessibility.
"""

from __future__ import annotations

import math
from functools import cache, lru_cache

from . import tarot
from .glyphs import circle_path, emblem, esc, star_points

W, H = 300, 500
ARCH = "M42 384V168Q42 80 150 46Q258 80 258 168V384Z"

ELEMENT_COLOURS = {
    "fire": ("#2c0d09", "#0f0403", "#ff7a3d"),
    "water": ("#082430", "#020a0e", "#5fd4e8"),
    "air": ("#1c1534", "#07050e", "#c3b5ff"),
    "earth": ("#18230d", "#060904", "#a7c957"),
}
GOLD, BONE, EMBER, SHADE = "#d9b65c", "#e3dccb", "#b3261e", "#0b0809"
ROSE = "#c2185b"

# (emblem, x, y, size, rotation, colour, opacity)
Piece = tuple

MAJOR_ART: dict[int, list[Piece]] = {
    0: [
        ("mountain", 100, 322, 150, 0, BONE, 0.3),
        ("star", 202, 118, 46, 0, GOLD, 1),
        ("flame", 150, 236, 74, 0, "glow", 1),
        ("star", 96, 150, 18, 0, BONE, 0.7),
    ],
    1: [
        ("infinity", 150, 112, 92, 0, GOLD, 1),
        ("wand", 98, 222, 62, 0, BONE, 1),
        ("cup", 202, 222, 58, 0, BONE, 1),
        ("sword", 98, 314, 64, 0, BONE, 1),
        ("pentacle", 202, 314, 56, 0, BONE, 1),
        ("flame", 150, 268, 48, 0, "glow", 1),
    ],
    2: [
        ("pillar", 86, 252, 176, 0, BONE, 0.9),
        ("pillar", 214, 252, 176, 0, "glow", 0.55),
        ("crescent", 150, 150, 72, 0, GOLD, 1),
        ("eye", 150, 272, 54, 0, "glow", 1),
    ],
    3: [
        ("rose", 150, 246, 112, 0, ROSE, 1),
        ("crown", 150, 132, 74, 0, GOLD, 1),
        ("star", 88, 176, 22, 0, GOLD, 1),
        ("star", 212, 176, 22, 0, GOLD, 1),
        ("star", 150, 340, 22, 0, GOLD, 1),
    ],
    4: [
        ("throne", 150, 274, 136, 0, BONE, 0.8),
        ("crown", 150, 132, 84, 0, GOLD, 1),
        ("dagger", 150, 268, 54, 0, EMBER, 1),
    ],
    5: [
        ("key", 116, 276, 112, -30, GOLD, 1),
        ("key", 184, 276, 112, 30, GOLD, 1),
        ("cross", 150, 140, 72, 0, BONE, 1),
    ],
    6: [
        ("candle", 108, 236, 92, 0, BONE, 1),
        ("candle", 192, 236, 92, 0, BONE, 1),
        ("heart", 150, 128, 50, 0, ROSE, 1),
    ],
    7: [
        ("wheel", 150, 274, 124, 0, GOLD, 1),
        ("star8", 150, 128, 62, 0, "glow", 1),
        ("crescent", 88, 176, 30, 0, BONE, 1),
        ("crescent", 212, 176, 30, 180, BONE, 1),
    ],
    8: [
        ("infinity", 150, 118, 84, 0, GOLD, 1),
        ("flame", 150, 252, 126, 0, EMBER, 1),
        ("heart", 150, 270, 38, 0, GOLD, 1),
    ],
    9: [
        ("mountain", 150, 324, 176, 0, BONE, 0.35),
        ("lantern", 150, 204, 104, 0, GOLD, 1),
        ("star", 214, 112, 22, 0, "glow", 1),
    ],
    10: [
        ("wheel", 150, 232, 164, 0, GOLD, 1),
        ("eye", 78, 116, 32, 0, BONE, 1),
        ("crown", 222, 116, 32, 0, BONE, 1),
        ("star", 78, 350, 26, 0, BONE, 1),
        ("flame", 222, 350, 30, 0, BONE, 1),
    ],
    11: [("sword", 150, 208, 204, 0, BONE, 0.85), ("scales", 150, 246, 132, 0, GOLD, 1)],
    12: [
        ("cross", 150, 156, 112, 0, BONE, 1),
        ("sun", 150, 284, 72, 0, GOLD, 1),
        ("droplet", 108, 340, 22, 0, "glow", 1),
        ("droplet", 192, 340, 22, 0, "glow", 1),
    ],
    13: [
        ("scythe", 150, 230, 194, 0, GOLD, 0.9),
        ("skull", 150, 238, 112, 0, BONE, 1),
        ("moth", 150, 116, 52, 0, BONE, 0.85),
    ],
    14: [
        ("cup", 100, 216, 72, -25, GOLD, 1),
        ("cup", 202, 268, 72, 25, GOLD, 1),
        ("flame", 150, 118, 40, 0, "glow", 1),
    ],
    15: [
        ("pentagram_inverted", 150, 168, 124, 0, EMBER, 1),
        ("chains", 150, 306, 150, 0, BONE, 1),
        ("flame", 150, 92, 28, 0, "glow", 1),
    ],
    16: [
        ("tower", 150, 264, 164, 0, BONE, 1),
        ("bolt", 198, 138, 92, 15, "glow", 1),
        ("flame", 88, 200, 30, 0, EMBER, 1),
        ("flame", 212, 232, 26, 0, EMBER, 1),
    ],
    17: [("star8", 150, 172, 132, 0, GOLD, 1), ("droplet", 150, 322, 40, 0, "glow", 0.75)]
    + [
        ("star", 150 + 92 * math.cos(math.radians(a)), 176 + 92 * math.sin(math.radians(a)), 18, 0, "glow", 1)
        for a in range(-90, 270, 52)
    ],
    18: [
        ("crescent", 150, 150, 104, 0, BONE, 1),
        ("tower", 84, 312, 72, 0, BONE, 0.6),
        ("tower", 216, 312, 72, 0, BONE, 0.6),
        ("droplet", 150, 242, 18, 0, GOLD, 1),
        ("droplet", 128, 268, 14, 0, GOLD, 1),
        ("droplet", 172, 268, 14, 0, GOLD, 1),
    ],
    19: [("sun", 150, 204, 174, 0, GOLD, 1), ("rose", 150, 336, 40, 0, ROSE, 1)],
    20: [
        ("trumpet", 150, 130, 112, -15, GOLD, 1),
        ("flame", 100, 302, 72, 0, EMBER, 1),
        ("flame", 150, 290, 94, 0, "glow", 1),
        ("flame", 200, 302, 72, 0, EMBER, 1),
    ],
    21: [
        ("wreath", 150, 232, 192, 0, GOLD, 1),
        ("star", 150, 232, 50, 0, BONE, 1),
        ("flame", 72, 104, 28, 0, BONE, 1),
        ("droplet", 228, 104, 26, 0, BONE, 1),
        ("star", 72, 362, 22, 0, BONE, 1),
        ("mountain", 228, 362, 32, 0, BONE, 1),
    ],
}

PIPS: dict[int, tuple[list[tuple[int, int]], int]] = {
    1: ([(150, 232)], 150),
    2: ([(150, 150), (150, 312)], 82),
    3: ([(150, 128), (150, 230), (150, 332)], 72),
    4: ([(104, 160), (196, 160), (104, 302), (196, 302)], 72),
    5: ([(104, 150), (196, 150), (150, 232), (104, 314), (196, 314)], 64),
    6: ([(104, 140), (196, 140), (104, 232), (196, 232), (104, 324), (196, 324)], 60),
    7: ([(104, 140), (196, 140), (150, 186), (104, 232), (196, 232), (104, 324), (196, 324)], 56),
    8: ([(104, 130), (196, 130), (104, 202), (196, 202), (104, 274), (196, 274), (104, 346), (196, 346)], 54),
    9: (
        [
            (104, 128),
            (196, 128),
            (104, 196),
            (196, 196),
            (150, 236),
            (104, 276),
            (196, 276),
            (104, 344),
            (196, 344),
        ],
        50,
    ),
    10: (
        [
            (100, 124),
            (200, 124),
            (150, 162),
            (100, 204),
            (200, 204),
            (100, 264),
            (200, 264),
            (150, 304),
            (100, 346),
            (200, 346),
        ],
        46,
    ),
}
SUIT_EMBLEM = {"wands": "wand", "cups": "cup", "swords": "sword", "pentacles": "pentacle"}
COURT_MARK = {11: ("eye", 44), 12: ("bolt", 48), 13: ("crown", 56), 14: ("crown", 68)}


def _rays(glow: str, count: int = 36) -> str:
    rays = "".join(
        f'<polygon points="146,230 154,230 150,-40" fill="{glow}" opacity="{0.10 if i % 2 else 0.05}"'
        f' transform="rotate({i * 360 / count:.1f} 150 230)"/>'
        for i in range(count)
    )
    return f'<g clip-path="url(#arch)">{rays}</g>'


def _frame(bg1: str, bg2: str, glow: str, title: str, inner: str, rays: bool) -> str:
    corners = "".join(
        f'<polygon points="{star_points(4, 9, 3)}" fill="{GOLD}" transform="translate({x} {y})"/>'
        for x, y in ((24, 24), (276, 24), (24, 476), (276, 476))
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" '
        f'aria-label="{esc(title)}"><title>{esc(title)}</title>'
        f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{bg1}"/><stop offset="1" stop-color="{bg2}"/></linearGradient>'
        f'<radialGradient id="win" cx="50%" cy="42%" r="62%">'
        f'<stop offset="0" stop-color="{glow}" stop-opacity=".42"/>'
        f'<stop offset=".55" stop-color="{glow}" stop-opacity=".08"/>'
        f'<stop offset="1" stop-color="#000" stop-opacity=".5"/></radialGradient>'
        f'<clipPath id="arch"><path d="{ARCH}"/></clipPath></defs>'
        f'<rect width="{W}" height="{H}" rx="18" fill="url(#bg)"/>'
        f'<rect x="8" y="8" width="{W - 16}" height="{H - 16}" rx="13" fill="none" '
        f'stroke="{GOLD}" stroke-width="3"/>'
        f'<rect x="15" y="15" width="{W - 30}" height="{H - 30}" rx="9" fill="none" '
        f'stroke="{GOLD}" stroke-width="1" opacity=".6"/>'
        f'<path d="{ARCH}" fill="url(#win)"/>'
        + (_rays(glow) if rays else "")
        + f'<g clip-path="url(#arch)">{inner}</g>'
        f'<path d="{ARCH}" fill="none" stroke="{GOLD}" stroke-width="2.5"/>'
        f'<path d="M58 384V174Q58 96 150 64Q242 96 242 174V384" fill="none" stroke="{GOLD}" '
        f'stroke-width="1" opacity=".45"/>'
        f'<rect x="34" y="398" width="232" height="64" rx="6" fill="#000" opacity=".35" '
        f'stroke="{GOLD}" stroke-width="1.5"/>'
        f"{corners}</svg>"
    )


def _colour(value: str, glow: str) -> str:
    return glow if value == "glow" else value


def card_svg_uncached(card: tarot.Card) -> str:
    bg1, bg2, glow = ELEMENT_COLOURS[card.element]
    pieces: list[str] = []
    if card.is_major:
        if card.rank == 6:
            pieces.append('<ellipse cx="150" cy="334" rx="64" ry="12" fill="#000" opacity=".55"/>')
        if card.rank == 14:
            pieces.append(
                f'<path d="M116 206C150 214 158 236 188 252" stroke="{glow}" '
                f'stroke-width="6" fill="none" stroke-linecap="round" opacity=".8"/>'
            )
        for name, x, y, size, rot, colour, opacity in MAJOR_ART[card.rank]:
            frag = emblem(name, x, y, size, _colour(colour, glow), SHADE, rot)
            pieces.append(f'<g opacity="{opacity}">{frag}</g>' if opacity < 1 else frag)
        return _frame(bg1, bg2, glow, card.name, "".join(pieces), rays=True)
    suit_emblem = SUIT_EMBLEM[card.suit or "wands"]
    if card.rank <= 10:
        positions, size = PIPS[card.rank]
        for x, y in positions:
            pieces.append(emblem(suit_emblem, x, y, size, GOLD if card.rank > 1 else glow, SHADE))
        return _frame(bg1, bg2, glow, card.name, "".join(pieces), rays=card.rank == 1)
    mark, mark_size = COURT_MARK[card.rank]
    if card.rank == 14:
        pieces.append(f'<g opacity=".25">{emblem("throne", 150, 268, 156, BONE, SHADE)}</g>')
    pieces.append(f'<circle cx="150" cy="258" r="70" fill="{glow}" opacity=".12"/>')
    pieces.append(emblem(suit_emblem, 150, 262, 116, GOLD, SHADE))
    pieces.append(emblem(mark, 150, 124, mark_size, BONE, SHADE))
    return _frame(bg1, bg2, glow, card.name, "".join(pieces), rays=False)


@cache
def card_svg(card_id: str) -> str:
    """The SVG face of a card (cached)."""
    return card_svg_uncached(tarot.get(card_id))


@lru_cache(maxsize=1)
def back_svg() -> str:
    """The shared card back: a gothic rose window."""
    gold, deep, glow = GOLD, "#3a0a10", "#ff4d5e"
    petals = []
    for i in range(12):
        angle = i * 30
        petals.append(
            f'<path d="M150 250C132 214 132 178 150 150C168 178 168 214 150 250Z" fill="{deep}" '
            f'stroke="{gold}" stroke-width="1.6" transform="rotate({angle} 150 250)"/>'
        )
        petals.append(
            f'<circle cx="150" cy="138" r="9" fill="none" stroke="{gold}" stroke-width="1.4" '
            f'transform="rotate({angle + 15} 150 250)"/>'
        )
    tracery = "".join(
        f'<path d="M150 250L150 128" stroke="{gold}" stroke-width=".8" opacity=".5" '
        f'transform="rotate({i * 15} 150 250)"/>'
        for i in range(24)
    )
    border_stars = "".join(
        f'<polygon points="{star_points(4, 6, 2)}" fill="{gold}" transform="translate({x} {y})"/>'
        for x in (40, 150, 260)
        for y in (40, 460)
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" '
        f'aria-label="Card back"><title>Card back</title>'
        f'<defs><radialGradient id="rw" cx="50%" cy="50%" r="50%">'
        f'<stop offset="0" stop-color="{glow}" stop-opacity=".55"/>'
        f'<stop offset=".7" stop-color="{deep}" stop-opacity=".25"/>'
        f'<stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient>'
        f'<pattern id="lattice" width="20" height="20" patternUnits="userSpaceOnUse">'
        f'<path d="M0 10L10 0L20 10L10 20Z" fill="none" stroke="{gold}" stroke-width=".5" '
        f'opacity=".25"/></pattern></defs>'
        f'<rect width="{W}" height="{H}" rx="18" fill="#140608"/>'
        f'<rect width="{W}" height="{H}" rx="18" fill="url(#lattice)"/>'
        f'<rect x="8" y="8" width="{W - 16}" height="{H - 16}" rx="13" fill="none" '
        f'stroke="{gold}" stroke-width="3"/>'
        f'<rect x="15" y="15" width="{W - 30}" height="{H - 30}" rx="9" fill="none" '
        f'stroke="{gold}" stroke-width="1" opacity=".6"/>'
        f'<circle cx="150" cy="250" r="128" fill="url(#rw)"/>'
        f'<path fill-rule="evenodd" fill="{gold}" d="{circle_path(150, 250, 130)}'
        f'{circle_path(150, 250, 124)}"/>'
        f"{tracery}{''.join(petals)}"
        f'<circle cx="150" cy="250" r="34" fill="{deep}" stroke="{gold}" stroke-width="2"/>'
        + emblem("star8", 150, 250, 56, gold, deep)
        + emblem("crescent", 150, 70, 34, gold, deep)
        + emblem("crescent", 150, 430, 34, gold, deep, 180)
        + f"{border_stars}</svg>"
    )
