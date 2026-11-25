"""Static checks that keep the browser half of the Codex in step with the Python half."""

import re
from pathlib import Path

import pytest

from nocturne import arcane, sigils
from nocturne.config import STATIC_DIR
from nocturne.edicts import ARCANA, EFFECT_FLAGS

JS = STATIC_DIR / "js"
CSS = (STATIC_DIR / "css" / "nocturne.css").read_text(encoding="utf-8")
INDEX = (STATIC_DIR / "index.html").read_text(encoding="utf-8")


def js(name: str) -> str:
    return (JS / name).read_text(encoding="utf-8")


def test_index_references_exist():
    for ref in re.findall(r'(?:src|href)="/static/([^"]+)"', INDEX):
        assert (STATIC_DIR / ref).is_file(), ref
    assert "{{NOCTURNE_TOKEN}}" in INDEX


@pytest.mark.parametrize("module", sorted(p.name for p in JS.glob("*.js")))
def test_js_imports_resolve(module):
    for target in re.findall(r"from '(\./[^']+)'", js(module)):
        assert (JS / target).is_file(), f"{module} imports missing {target}"


def test_the_page_never_calls_the_outside_world():
    for path in STATIC_DIR.rglob("*"):
        if path.suffix not in {".js", ".css", ".html", ".svg"}:
            continue
        text = path.read_text(encoding="utf-8")
        urls = [u for u in re.findall(r"https?://[^\s'\"`)]+", text) if "www.w3.org" not in u]
        assert not urls, f"{path.name} reaches outside: {urls}"


def test_every_font_in_the_css_is_bundled():
    for ref in re.findall(r'url\("\.\./fonts/([^"]+)"\)', CSS):
        assert (STATIC_DIR / "fonts" / ref).is_file(), ref
    assert (STATIC_DIR / "fonts" / "OFL.txt").is_file()


def _ranges() -> list[tuple[int, int]]:
    spans = []
    for block in re.findall(r"unicode-range:([^;]+);", CSS):
        for part in block.split(","):
            part = part.strip().removeprefix("U+")
            lo, _, hi = part.partition("-")
            spans.append((int(lo, 16), int(hi or lo, 16)))
    return spans


def test_every_sigil_glyph_is_covered_by_the_bundled_font():
    spans = _ranges()
    for sigil in sigils.SIGILS:
        code = ord(sigil.glyph)
        assert any(lo <= code <= hi for lo, hi in spans), f"{sigil.name} ({sigil.glyph}) is not covered"


def test_every_rite_has_an_animation_and_a_sound():
    animations = set(re.findall(r"^  async (\w+)\(", js("fx.js"), re.M))
    sounds = set(re.findall(r"^  (\w+)\(\) \{", js("audio.js"), re.M))
    for rite in arcane.RITES:
        assert rite.animation in animations, f"{rite.id} lacks animation {rite.animation}"
        assert rite.sound in sounds, f"{rite.id} lacks sound {rite.sound}"


def test_every_ambient_particle_is_drawn():
    ambient = set(re.findall(r"^  (\w+): \(w", js("fx.js"), re.M))
    particles = {a.particle for a in ARCANA} | {"embers", "droplets", "feathers", "spores", "motes"}
    assert particles <= ambient


def test_effect_flags_match_the_python_list():
    match = re.search(r"EFFECT_FLAGS = \[(.*?)\];", js("theme.js"), re.S)
    assert match
    flags = re.findall(r"'([a-z_]+)'", match.group(1))
    assert flags == list(EFFECT_FLAGS)


def test_static_dir_is_inside_the_package():
    assert STATIC_DIR.parent == Path(arcane.__file__).parent
