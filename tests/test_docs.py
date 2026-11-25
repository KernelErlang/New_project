"""The documentation must keep up with the code."""

import re
from pathlib import Path

from nocturne import arcane, sigils, tarot

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_every_linked_file_and_image_exists():
    for page in [ROOT / "README.md", *DOCS.glob("*.md")]:
        for link in re.findall(r"\]\(((?!https?:|#|mailto:)[^)\s]+)\)", read(page)):
            assert (page.parent / link).exists(), f"{page.name} links to missing {link}"


def test_forbidden_lore_spoils_every_rite():
    lore = read(DOCS / "FORBIDDEN_LORE.md")
    for rite in arcane.DISCOVERABLE:
        assert rite.name in lore and rite.hint in lore


def test_mechanics_covers_every_major_and_sigil():
    mechanics = read(DOCS / "MECHANICS.md")
    for card in tarot.MAJORS:
        assert card.name in mechanics
    for sigil in sigils.SIGILS:
        assert sigil.shortcode in mechanics


def test_launchers_exist_and_are_executable():
    assert (ROOT / "Open Nocturne Codex.bat").read_bytes().count(b"\r\n") > 5
    for name in ("Open Nocturne Codex.command", "open-nocturne-codex.sh", "launch.py"):
        path = ROOT / name
        assert path.is_file()
        assert "nocturne" in read(path)
