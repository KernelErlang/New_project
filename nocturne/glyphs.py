"""A tiny library of gothic emblems drawn as SVG.

Every emblem is drawn in a 100 × 100 box centred on the origin and returned as an
SVG fragment. :func:`place` positions, scales and rotates it. The emblems are shared
by the heraldry (crest charges) and the tarot card art.
"""

from __future__ import annotations

import math
from typing import Callable
from xml.sax.saxutils import escape

Emblem = Callable[[str, str], str]  # (main colour, shadow colour) -> SVG fragment


def esc(text: str) -> str:
    return escape(text, {'"': "&quot;"})


def place(fragment: str, x: float, y: float, size: float = 100.0, rotate: float = 0.0) -> str:
    scale = size / 100.0
    rot = f" rotate({rotate:g})" if rotate else ""
    return f'<g transform="translate({x:g} {y:g}){rot} scale({scale:.4g})">{fragment}</g>'


def star_points(points: int, outer: float, inner: float, rotation: float = -90.0) -> str:
    coords = []
    for i in range(points * 2):
        radius = outer if i % 2 == 0 else inner
        angle = math.radians(rotation + i * 180.0 / points)
        coords.append(f"{radius * math.cos(angle):.2f},{radius * math.sin(angle):.2f}")
    return " ".join(coords)


def circle_path(cx: float, cy: float, r: float) -> str:
    return f"M{cx - r:g} {cy:g}a{r:g} {r:g} 0 1 0 {2 * r:g} 0a{r:g} {r:g} 0 1 0 {-2 * r:g} 0Z"


# --- emblems ---------------------------------------------------------------


def crescent(c: str, d: str) -> str:
    return f'<path d="M14 -42A44 44 0 1 0 14 42A35 35 0 1 1 14 -42Z" fill="{c}"/>'


def star(c: str, d: str) -> str:
    return f'<polygon points="{star_points(5, 46, 19)}" fill="{c}"/>'


def star8(c: str, d: str) -> str:
    return (
        f'<polygon points="{star_points(8, 48, 16)}" fill="{c}"/>'
        f'<polygon points="{star_points(8, 26, 10, -67.5)}" fill="{d}" opacity=".35"/>'
    )


def candle(c: str, d: str) -> str:
    return (
        f'<path d="M-13 -8H13V44H-13Z" fill="{c}"/>'
        f'<path d="M-13 -8c4 6 8 6 8 14s5 6 5 0 4-10 13-14Z" fill="{d}" opacity=".35"/>'
        f'<path d="M0 -48C11 -34 11 -22 0 -15C-11 -22 -11 -34 0 -48Z" fill="{c}"/>'
        f'<path d="M0 -38C4 -31 4 -25 0 -21C-4 -25 -4 -31 0 -38Z" fill="{d}" opacity=".5"/>'
    )


def chalice(c: str, d: str) -> str:
    return (
        f'<path d="M-32 -40H32C32 -8 14 4 4 6V26C4 32 18 34 24 44H-24C-18 34 -4 32 -4 26V6'
        f'C-14 4 -32 -8 -32 -40Z" fill="{c}"/>'
        f'<path d="M-26 -34H26C24 -18 14 -8 0 -6C-14 -8 -24 -18 -26 -34Z" fill="{d}" opacity=".4"/>'
    )


def skull(c: str, d: str) -> str:
    return (
        f'<path fill-rule="evenodd" fill="{c}" d="M0 -44C26 -44 38 -26 38 -6C38 8 30 14 26 18'
        f"V30H-26V18C-30 14 -38 8 -38 -6C-38 -26 -26 -44 0 -44Z"
        f"M-24 -6a10 11 0 1 0 20 0a10 11 0 1 0 -20 0Z"
        f'M4 -6a10 11 0 1 0 20 0a10 11 0 1 0 -20 0ZM0 6L-6 18H6Z"/>'
        f'<path d="M-18 32H18V44H-18Z" fill="{c}"/>'
        f'<path d="M-9 32V44M0 32V44M9 32V44" stroke="{d}" stroke-width="3"/>'
    )


def crown(c: str, d: str) -> str:
    return (
        f'<path d="M-42 18L-42 -22L-21 0L0 -36L21 0L42 -22L42 18Z" fill="{c}"/>'
        f'<path d="M-42 20H42V34H-42Z" fill="{c}"/>'
        f'<path d="M-30 27h8M-4 27h8M22 27h8" stroke="{d}" stroke-width="5"/>'
        f'<circle cx="-42" cy="-26" r="5" fill="{c}"/><circle cx="0" cy="-40" r="5" fill="{c}"/>'
        f'<circle cx="42" cy="-26" r="5" fill="{c}"/>'
    )


def tower(c: str, d: str) -> str:
    return (
        f'<path d="M-30 -22V-44H-19V-35H-6V-44H6V-35H19V-44H30V-22H24V46H-24V-22Z" fill="{c}"/>'
        f'<path d="M-7 46V30A7 7 0 0 1 7 30V46Z" fill="{d}"/>'
        f'<path d="M-5 -8V-16A5 5 0 0 1 5 -16V-8Z" fill="{d}"/>'
        f'<path d="M-15 10V4A3 3 0 0 1 -9 4V10ZM9 10V4A3 3 0 0 1 15 4V10Z" fill="{d}"/>'
    )


def bell(c: str, d: str) -> str:
    return (
        f'<path d="M-30 24C-30 -2 -24 -34 0 -34C24 -34 30 -2 30 24L40 34H-40Z" fill="{c}"/>'
        f'<circle cx="0" cy="41" r="7" fill="{c}"/>'
        f'<path d="M-6 -34A6 6 0 0 1 6 -34" stroke="{c}" stroke-width="6" fill="none"/>'
        f'<path d="M-22 18C-22 0 -18 -20 -6 -26" stroke="{d}" stroke-width="4" fill="none" '
        f'opacity=".4"/>'
    )


def hourglass(c: str, d: str) -> str:
    return (
        f'<path d="M-28 -46H28V-38H22L4 0L22 38H28V46H-28V38H-22L-4 0L-22 -38H-28Z" fill="{c}"/>'
        f'<path d="M-12 -30H12L0 -6ZM0 14L-14 34H14Z" fill="{d}" opacity=".6"/>'
    )


def key(c: str, d: str) -> str:
    return (
        f'<path fill-rule="evenodd" fill="{c}" d="{circle_path(0, -26, 20)}{circle_path(0, -26, 9)}"/>'
        f'<path d="M-5 -6H5V46H-5Z" fill="{c}"/>'
        f'<path d="M5 22H20V30H5ZM5 36H16V44H5Z" fill="{c}"/>'
    )


def rose(c: str, d: str) -> str:
    petals = "".join(
        f'<circle cx="{18 * math.cos(math.radians(a)):.1f}" cy="{18 * math.sin(math.radians(a)):.1f}"'
        f' r="17" fill="{c}"/>'
        for a in range(-90, 270, 72)
    )
    return (
        petals + f'<circle r="16" fill="{d}" opacity=".45"/><circle r="9" fill="{c}"/>'
        f'<path d="M0 -6a6 6 0 1 1 -6 6" stroke="{d}" stroke-width="2.5" fill="none"/>'
    )


def moth(c: str, d: str) -> str:
    return (
        f'<ellipse cx="-21" cy="-10" rx="23" ry="15" transform="rotate(-28 -21 -10)" fill="{c}"/>'
        f'<ellipse cx="21" cy="-10" rx="23" ry="15" transform="rotate(28 21 -10)" fill="{c}"/>'
        f'<ellipse cx="-15" cy="15" rx="14" ry="10" transform="rotate(30 -15 15)" fill="{c}"/>'
        f'<ellipse cx="15" cy="15" rx="14" ry="10" transform="rotate(-30 15 15)" fill="{c}"/>'
        f'<circle cx="-22" cy="-10" r="6" fill="{d}" opacity=".5"/>'
        f'<circle cx="22" cy="-10" r="6" fill="{d}" opacity=".5"/>'
        f'<ellipse rx="5" ry="26" fill="{d}"/>'
        f'<path d="M-2 -24C-8 -36 -14 -40 -20 -42M2 -24C8 -36 14 -40 20 -42" stroke="{c}" '
        f'stroke-width="2.5" fill="none"/>'
    )


def raven(c: str, d: str) -> str:
    return (
        f'<path fill="{c}" d="M-46 12L-22 2C-14 -18 6 -28 22 -24L34 -28L48 -22L35 -15'
        f'C35 -2 27 9 13 15L21 36H13L5 18L-3 19L-1 36H-9L-12 19C-25 19 -35 17 -46 12Z"/>'
        f'<circle cx="26" cy="-19" r="2.6" fill="{d}"/>'
        f'<path d="M-18 4C-8 -2 4 -2 14 6" stroke="{d}" stroke-width="2.5" fill="none" opacity=".5"/>'
    )


def serpent(c: str, d: str) -> str:
    return (
        f'<path d="M-28 -34C30 -42 32 -6 0 0C-32 6 -30 42 30 36" stroke="{c}" stroke-width="12"'
        f' fill="none" stroke-linecap="round"/>'
        f'<path d="M-28 -34C30 -42 32 -6 0 0C-32 6 -30 42 30 36" stroke="{d}" stroke-width="3"'
        f' fill="none" stroke-dasharray="2 7" opacity=".6"/>'
        f'<ellipse cx="-32" cy="-34" rx="11" ry="8" fill="{c}"/>'
        f'<circle cx="-35" cy="-36" r="2.2" fill="{d}"/>'
        f'<path d="M-43 -33L-50 -30M-43 -33L-50 -36" stroke="{c}" stroke-width="2"/>'
    )


def eye(c: str, d: str) -> str:
    return (
        f'<path d="M-48 0C-24 -30 24 -30 48 0C24 30 -24 30 -48 0Z" fill="{c}"/>'
        f'<circle r="16" fill="{d}"/><circle r="7" fill="{c}"/>'
        f'<circle cx="-4" cy="-5" r="3" fill="{c}" opacity=".8"/>'
    )


def dagger(c: str, d: str) -> str:
    return (
        f'<path d="M0 -48L9 8H-9Z" fill="{c}"/><path d="M0 -40V4" stroke="{d}" stroke-width="2"/>'
        f'<path d="M-24 8H24V15H-24Z" fill="{c}"/><path d="M-4 15H4V36H-4Z" fill="{c}"/>'
        f'<circle cx="0" cy="42" r="6" fill="{c}"/>'
    )


def flame(c: str, d: str) -> str:
    return (
        f'<path d="M0 -46C22 -20 30 4 18 26C10 40 -10 40 -18 26C-30 4 -16 -10 -6 -24'
        f'C-4 -10 4 -6 6 -2C10 -16 4 -30 0 -46Z" fill="{c}"/>'
        f'<path d="M0 0C9 10 10 22 4 30C0 34 -6 32 -8 26C-10 18 -4 10 0 0Z" fill="{d}" opacity=".45"/>'
    )


def lantern(c: str, d: str) -> str:
    return (
        f'<path d="M-6 -48A6 6 0 0 1 6 -48V-40H-6Z" fill="{c}"/>'
        f'<path d="M-24 -26L0 -42L24 -26Z" fill="{c}"/>'
        f'<path fill-rule="evenodd" fill="{c}" d="M-20 -26H20L26 30H-26ZM-13 -18H13L17 22H-17Z"/>'
        f'<path d="M0 -10C7 0 7 8 0 14C-7 8 -7 0 0 -10Z" fill="{c}"/>'
        f'<path d="M-30 30H30V40H-30Z" fill="{c}"/>'
        f'<circle cy="4" r="16" fill="{c}" opacity=".18"/>'
    )


def wand(c: str, d: str) -> str:
    return (
        f'<path d="M-5 -46H5V46H-5Z" fill="{c}" transform="rotate(18)"/>'
        f'<ellipse cx="-14" cy="-22" rx="8" ry="4" transform="rotate(-30 -14 -22)" fill="{c}"/>'
        f'<ellipse cx="14" cy="8" rx="8" ry="4" transform="rotate(30 14 8)" fill="{c}"/>'
        f'<circle cx="14" cy="-42" r="6" fill="{c}"/>'
        f'<path d="M-12 -2H4M-2 20H10" stroke="{d}" stroke-width="2.5" transform="rotate(18)"/>'
    )


def cup(c: str, d: str) -> str:
    return chalice(c, d)


def sword(c: str, d: str) -> str:
    return (
        f'<path d="M0 -50L7 -40V18H-7V-40Z" fill="{c}"/>'
        f'<path d="M0 -42V14" stroke="{d}" stroke-width="2"/>'
        f'<path d="M-24 18H24L20 25H-20Z" fill="{c}"/><path d="M-4 25H4V42H-4Z" fill="{c}"/>'
        f'<circle cx="0" cy="46" r="5" fill="{c}"/>'
    )


def pentacle(c: str, d: str) -> str:
    return (
        f'<path fill-rule="evenodd" fill="{c}" d="{circle_path(0, 0, 44)}{circle_path(0, 0, 37)}"/>'
        f'<circle r="37" fill="{d}" opacity=".3"/>'
        f'<polygon points="{star_points(5, 35, 13.5)}" fill="{c}"/>'
    )


def pentagram_inverted(c: str, d: str) -> str:
    return (
        f'<path fill-rule="evenodd" fill="{c}" d="{circle_path(0, 0, 46)}{circle_path(0, 0, 40)}"/>'
        f'<polygon points="{star_points(5, 38, 14.5, 90)}" fill="{c}"/>'
    )


def wheel(c: str, d: str) -> str:
    spokes = "".join(
        f'<path d="M0 0L{40 * math.cos(math.radians(a)):.1f} {40 * math.sin(math.radians(a)):.1f}"'
        f' stroke="{c}" stroke-width="5"/>'
        for a in range(0, 360, 45)
    )
    return (
        f'<path fill-rule="evenodd" fill="{c}" d="{circle_path(0, 0, 46)}{circle_path(0, 0, 38)}"/>'
        + spokes
        + f'<circle r="11" fill="{c}"/><circle r="5" fill="{d}"/>'
    )


def scales(c: str, d: str) -> str:
    return (
        f'<path d="M-3 -36H3V40H-3Z" fill="{c}"/><path d="M-24 40H24V46H-24Z" fill="{c}"/>'
        f'<path d="M-42 -28H42" stroke="{c}" stroke-width="5"/><circle cy="-40" r="6" fill="{c}"/>'
        f'<path d="M-40 -28L-50 4M-40 -28L-30 4M40 -28L30 4M40 -28L50 4" stroke="{c}" stroke-width="2"/>'
        f'<path d="M-54 4H-26A14 9 0 0 1 -54 4ZM26 4H54A14 9 0 0 1 26 4Z" fill="{c}"/>'
    )


def sun(c: str, d: str) -> str:
    rays = "".join(
        f'<polygon points="{-5:g},-30 5,-30 0,-49" fill="{c}" transform="rotate({a})"/>'
        for a in range(0, 360, 30)
    )
    return (
        rays + f'<circle r="26" fill="{c}"/><circle r="18" fill="{d}" opacity=".3"/>'
        f'<circle r="10" fill="{c}"/>'
    )


def infinity(c: str, d: str) -> str:
    return (
        f'<path d="M0 0C12 -18 38 -18 38 0C38 18 12 18 0 0C-12 -18 -38 -18 -38 0'
        f'C-38 18 -12 18 0 0Z" stroke="{c}" stroke-width="7" fill="none"/>'
    )


def heart(c: str, d: str) -> str:
    return (
        f'<path d="M0 40C-30 18 -44 2 -44 -16C-44 -32 -30 -42 -18 -42C-8 -42 -2 -36 0 -28'
        f'C2 -36 8 -42 18 -42C30 -42 44 -32 44 -16C44 2 30 18 0 40Z" fill="{c}"/>'
        f'<path d="M-26 -22C-26 -30 -20 -34 -14 -34" stroke="{d}" stroke-width="4" fill="none" '
        f'opacity=".4"/>'
    )


def bolt(c: str, d: str) -> str:
    return f'<path d="M8 -50L-22 4H-2L-12 50L24 -10H4L18 -50Z" fill="{c}"/>'


def mountain(c: str, d: str) -> str:
    return (
        f'<path d="M-50 40L-12 -26L4 -2L18 -24L50 40Z" fill="{c}"/>'
        f'<path d="M-12 -26L-4 -12L-12 -8L-20 -12ZM18 -24L26 -12L18 -10L12 -14Z" fill="{d}" '
        f'opacity=".5"/>'
    )


def pillar(c: str, d: str) -> str:
    return (
        f'<path d="M-14 -46H14V-38H10V38H14V46H-14V38H-10V-38H-14Z" fill="{c}"/>'
        f'<path d="M-4 -34V34M4 -34V34" stroke="{d}" stroke-width="2" opacity=".4"/>'
    )


def scythe(c: str, d: str) -> str:
    return (
        f'<path d="M-30 46L22 -40" stroke="{c}" stroke-width="5" stroke-linecap="round"/>'
        f'<path d="M22 -40C0 -50 -26 -44 -44 -26C-24 -36 -4 -36 14 -28Z" fill="{c}"/>'
    )


def trumpet(c: str, d: str) -> str:
    return (
        f'<path d="M-44 -6H10L40 -26V26L10 6H-44Z" fill="{c}"/>'
        f'<path d="M-44 -10V10" stroke="{c}" stroke-width="6"/>'
        f'<path d="M-30 6V20H-10V6" stroke="{c}" stroke-width="3" fill="none"/>'
        f'<path d="M14 -2H36" stroke="{d}" stroke-width="3" opacity=".5"/>'
    )


def cross_pattee(c: str, d: str) -> str:
    return (
        f'<path fill="{c}" d="M-10 -46H10L6 -8L44 -10V10L6 8L10 46H-10L-6 8L-44 10V-10L-6 -8Z"/>'
        f'<circle r="6" fill="{d}" opacity=".5"/>'
    )


def droplet(c: str, d: str) -> str:
    return (
        f'<path d="M0 -46C16 -20 28 -4 28 14C28 32 14 44 0 44C-14 44 -28 32 -28 14'
        f'C-28 -4 -16 -20 0 -46Z" fill="{c}"/>'
        f'<path d="M-14 14C-14 24 -8 30 -2 32" stroke="{d}" stroke-width="4" fill="none" opacity=".4"/>'
    )


def chains(c: str, d: str) -> str:
    links = "".join(
        f'<ellipse cx="{x}" cy="0" rx="13" ry="8" fill="none" stroke="{c}" stroke-width="5"'
        f' transform="rotate({20 if i % 2 else -20} {x} 0)"/>'
        for i, x in enumerate(range(-40, 50, 20))
    )
    return links


def wreath(c: str, d: str) -> str:
    leaves = "".join(
        f'<ellipse cx="0" cy="-42" rx="6" ry="11" fill="{c}" transform="rotate({a})"/>'
        for a in range(0, 360, 20)
    )
    return leaves + f'<ellipse rx="30" ry="40" fill="none" stroke="{c}" stroke-width="2"/>'


def ouroboros(c: str, d: str) -> str:
    return (
        f'<circle r="36" fill="none" stroke="{c}" stroke-width="10"/>'
        f'<circle r="36" fill="none" stroke="{d}" stroke-width="3" stroke-dasharray="3 8" opacity=".6"/>'
        f'<ellipse cx="0" cy="-36" rx="13" ry="9" fill="{c}"/>'
        f'<circle cx="5" cy="-38" r="2.4" fill="{d}"/>'
    )


def throne(c: str, d: str) -> str:
    return (
        f'<path d="M-30 -44H30V6H40V46H30V20H-30V46H-40V6H-30Z" fill="{c}"/>'
        f'<path d="M-20 -34H20V0H-20Z" fill="{d}" opacity=".45"/>'
    )


EMBLEMS: dict[str, Emblem] = {
    "crescent": crescent,
    "star": star,
    "star8": star8,
    "candle": candle,
    "chalice": chalice,
    "skull": skull,
    "crown": crown,
    "tower": tower,
    "bell": bell,
    "hourglass": hourglass,
    "key": key,
    "rose": rose,
    "moth": moth,
    "raven": raven,
    "serpent": serpent,
    "eye": eye,
    "dagger": dagger,
    "flame": flame,
    "lantern": lantern,
    "wand": wand,
    "cup": cup,
    "sword": sword,
    "pentacle": pentacle,
    "pentagram_inverted": pentagram_inverted,
    "wheel": wheel,
    "scales": scales,
    "sun": sun,
    "infinity": infinity,
    "heart": heart,
    "bolt": bolt,
    "mountain": mountain,
    "pillar": pillar,
    "scythe": scythe,
    "trumpet": trumpet,
    "cross": cross_pattee,
    "droplet": droplet,
    "chains": chains,
    "wreath": wreath,
    "ouroboros": ouroboros,
    "throne": throne,
}


def emblem(name: str, x: float, y: float, size: float, colour: str, shade: str, rotate: float = 0.0) -> str:
    """Render the named emblem at ``(x, y)`` with the given size and colours."""
    return place(EMBLEMS[name](colour, shade), x, y, size, rotate)
