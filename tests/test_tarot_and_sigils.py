import pytest

from nocturne import sigils, tarot
from nocturne.edicts import ARCANA, EFFECT_FLAGS, MODES, MODIFIERS


def test_deck_has_seventy_eight_unique_cards():
    assert len(tarot.DECK) == 78
    assert len({c.id for c in tarot.DECK}) == 78
    assert [c.index for c in tarot.DECK] == list(range(78))


def test_deck_structure():
    majors = [c for c in tarot.DECK if c.is_major]
    assert [c.rank for c in majors] == list(range(22))
    for suit in tarot.SUITS:
        cards = [c for c in tarot.DECK if c.suit == suit]
        assert [c.rank for c in cards] == list(range(1, 15))
        assert {c.element for c in cards} == {tarot.SUIT_ELEMENT[suit]}


def test_every_card_is_fully_described():
    for card in tarot.DECK:
        assert card.name and card.epigraph and card.upright and card.reversed
        assert card.sigil in sigils.BY_ID
        data = card.to_dict()
        assert data["art"] == f"/art/card/{card.id}.svg"


def test_fool_counts_as_twenty_two():
    assert tarot.get("major-00").value == 22
    assert tarot.get("major-13").value == 13
    assert tarot.get("cups-14").value == 14


def test_unknown_card_raises():
    with pytest.raises(KeyError):
        tarot.get("major-99")


def test_each_major_rules_its_own_sigil():
    rulers = [s.ruler for s in sigils.SIGILS if s.ruler]
    assert sorted(rulers) == sorted(c.id for c in tarot.MAJORS)
    for card in tarot.MAJORS:
        assert sigils.get(card.sigil).ruler == card.id
        assert sigils.get(card.sigil).value == card.rank or card.rank == 0


def test_arcana_table_is_consistent():
    assert len(ARCANA) == 22
    for card, arcanum in zip(tarot.MAJORS, ARCANA):
        assert arcanum.key == card.arcanum
        assert arcanum.mode in MODES
        assert set(arcanum.boon_effects + arcanum.curse_effects) <= set(EFFECT_FLAGS)
        assert set(arcanum.boon_modifiers + arcanum.curse_modifiers) <= set(MODIFIERS)
        assert arcanum.accent.startswith("#") and len(arcanum.accent) == 7


def test_sigil_catalogue_is_unique():
    assert len(sigils.SIGILS) == 24
    assert len({s.glyph for s in sigils.SIGILS}) == 24
    assert len({s.id for s in sigils.SIGILS}) == 24
    for s in sigils.SIGILS:
        assert s.element in (*sigils.ELEMENTS, "spirit")
        assert s.polarity in sigils.POLARITIES
        assert s.shortcode == f":{s.id}:"


def test_extract_reads_in_order_with_shortcodes_and_selectors():
    text = "☉ then :luna: and ☠️ then :unknown:"
    assert sigils.extract(text) == ["sol", "luna", "skull"]
    assert sigils.expand_shortcodes(":sol::nothing:") == "☉:nothing:"


def test_strip_and_start():
    assert sigils.strip("a☉b︎") == "ab"
    assert sigils.starts_with_sigil("  ☽ moon")
    assert sigils.starts_with_sigil(":sol: rises")
    assert not sigils.starts_with_sigil("moon ☽")
    assert not sigils.starts_with_sigil("")


def test_element_and_polarity_groups():
    fire = sigils.of_element("fire")
    assert "sol" in fire and "fire" in fire and "luna" not in fire
    assert set(sigils.of_polarity("light")) | set(sigils.of_polarity("dark")) == set(sigils.BY_ID)
    assert sigils.OPPOSITES["air"] == "earth"
