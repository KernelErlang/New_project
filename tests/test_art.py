import xml.etree.ElementTree as ET

import pytest

from nocturne import cardart, glyphs, heraldry, tarot

SVG = "{http://www.w3.org/2000/svg}"


def parse(svg: str) -> ET.Element:
    root = ET.fromstring(svg)
    assert root.tag == f"{SVG}svg"
    return root


@pytest.mark.parametrize("card", tarot.DECK, ids=lambda c: c.id)
def test_every_card_face_is_valid_svg(card):
    root = parse(cardart.card_svg(card.id))
    assert root.find(f"{SVG}title").text == card.name
    assert root.get("viewBox") == "0 0 300 500"


def test_card_faces_are_distinct_and_cached():
    faces = {cardart.card_svg(c.id) for c in tarot.DECK}
    assert len(faces) == 78
    assert cardart.card_svg("major-00") is cardart.card_svg("major-00")


def test_card_back():
    root = parse(cardart.back_svg())
    assert root.find(f"{SVG}title").text == "Card back"


def test_every_emblem_renders():
    for name in glyphs.EMBLEMS:
        fragment = glyphs.emblem(name, 50, 50, 80, "#fff", "#000", 10)
        parse(f'<svg xmlns="http://www.w3.org/2000/svg">{fragment}</svg>')


def test_twelve_houses_with_valid_crests():
    assert len(heraldry.HOUSES) == 12
    assert len({h.id for h in heraldry.HOUSES}) == 12
    for house in heraldry.HOUSES:
        root = parse(heraldry.house_svg(house.id))
        assert root.find(f"{SVG}title").text == house.name
        assert house.crest.charge in glyphs.EMBLEMS
        assert house.crest.division in heraldry.DIVISIONS
        assert set(house.crest.field) <= set(heraldry.TINCTURES)
        assert house.to_dict()["art"] == f"/art/crest/{house.id}.svg"


@pytest.mark.parametrize("division", heraldry.DIVISIONS)
def test_every_division_renders(division):
    crest = heraldry.Crest("heater", division, ("or", "gules"), "star", "argent", "three", "rays", "crown")
    parse(heraldry.render_crest(crest, "Test"))


@pytest.mark.parametrize("supporter", heraldry.SUPPORTERS)
def test_every_supporter_renders(supporter):
    crest = heraldry.Crest("kite", "plain", ("azure", "or"), "moth", "or", "single", supporter, "none")
    parse(heraldry.render_crest(crest))


def test_unknown_division_is_refused():
    crest = heraldry.Crest("heater", "nonsense", ("or", "gules"), "star", "argent", "single", "none", "none")
    with pytest.raises(ValueError, match="division"):
        heraldry.render_crest(crest)


def test_the_forge_is_deterministic_and_personal():
    assert heraldry.forge("Maria") == heraldry.forge("  maria ")
    assert heraldry.forge("Maria") != heraldry.forge("Gehrman")
    forged = {heraldry.forge(f"name-{i}") for i in range(40)}
    assert len(forged) > 30
    parse(heraldry.forged_svg("Maria"))
    parse(heraldry.forged_svg('<script>"&'))  # names are escaped
    parse(heraldry.forged_svg(""))
