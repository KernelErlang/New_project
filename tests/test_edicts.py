import datetime as dt
import json

import pytest

from nocturne import heraldry, sigils, tarot
from nocturne.edicts import DayRules, check_constraints, compute_rules, palette_for_hue, preview
from nocturne.ritual import DrawnCard, Spread

SECRET = b"e" * 32
DAY = dt.date(2026, 11, 25)


def spread(*cards: tuple[str, bool]) -> Spread:
    """crown, heart, shadow, burned, burned"""
    hand = tuple(DrawnCard(tarot.get(cid), rev) for cid, rev in cards)
    return Spread(DAY, hand, (0, 1, 2))


def rules_of(*cards: tuple[str, bool]) -> DayRules:
    return compute_rules(SECRET, spread(*cards))


BASE = (
    ("major-16", False),  # crown: the Tower
    ("cups-07", False),  # heart: seven of cups
    ("swords-05", False),  # shadow: five of swords
    ("major-19", False),  # burned: the Sun
    ("pentacles-03", False),  # burned: three of pentacles
)


def test_a_full_night_of_edicts():
    rules = rules_of(*BASE)
    assert rules.aspect["name"] == "Aspect of Tower"
    assert rules.aspect["particle"] == "ash"
    assert rules.tonality["mode"] == "double_harmonic"
    assert rules.crown_value == 16
    assert rules.resonance == 7
    assert "tremor" in rules.modifiers  # the Tower's boon
    assert rules.constraints.char_limit == 616
    assert "sol" in rules.forbidden  # burned Sun forbids its sigil
    assert "earth" in rules.banished
    assert set(rules.awakened) <= set(sigils.of_element("water"))
    assert "luna" in rules.awakened
    assert rules.effects["chains"] is True
    assert rules.house in heraldry.BY_ID
    assert rules.omen.startswith("Aspect of Tower.")
    assert rules.sigil_state("sol") == "forbidden"
    assert rules.sigil_state("saturn") == "ashen"
    assert rules.sigil_state("luna") == "awakened"
    assert rules.sigil_state("mercury") == "plain"


def test_rules_are_deterministic_and_serialisable():
    a, b = rules_of(*BASE).to_dict(), rules_of(*BASE).to_dict()
    assert a == b
    json.dumps(a)
    assert set(a["sigil_states"]) == set(sigils.BY_ID)


def test_unsealed_spread_is_refused():
    hand = tuple(DrawnCard(tarot.get(cid), rev) for cid, rev in BASE)
    with pytest.raises(ValueError, match="sealed"):
        compute_rules(SECRET, Spread(DAY, hand))


def test_reversed_heart_reflects_number_and_element():
    rules = rules_of(BASE[0], ("cups-07", True), *BASE[2:])
    assert rules.resonance == 3
    assert "fire" in rules.awakened and "luna" not in rules.awakened


def test_reversed_crown_is_eclipsed():
    rules = rules_of(("wands-04", True), *BASE[1:])
    assert rules.aspect["eclipsed"] is True
    assert rules.aspect["name"].endswith("Eclipsed")
    assert rules.tonality["mode"] == "locrian"


@pytest.mark.parametrize(
    ("shadow", "check"),
    [
        (("wands-12", False), lambda r: r.constraints.min_sigils == 3),
        (("cups-02", False), lambda r: r.effects["fading"]),
        (("swords-14", False), lambda r: r.constraints.char_limit == 111),
        (("pentacles-11", False), lambda r: r.effects["anchored"] and r.effects["silence"]),
        (("wands-03", True), lambda r: "fire" in r.awakened),
        (("cups-03", True), lambda r: r.effects["echo"]),
        (("swords-03", True), lambda r: r.effects["quill_song"]),
        (("pentacles-03", True), lambda r: "ward" in r.modifiers),
        (("major-05", False), lambda r: r.constraints.begin_with_sigil),
        (("major-06", False), lambda r: r.constraints.even_sigils),
        (("major-11", False), lambda r: r.constraints.balanced_sigils),
        (("major-20", False), lambda r: r.constraints.require == ["fire"] and r.effects["echo"]),
        (("major-21", False), lambda r: r.constraints.min_sigils == 4),
        (("major-03", False), lambda r: r.constraints.min_words == 13),
        (("major-09", False), lambda r: r.effects["lantern"] and r.effects["silence"]),
        (("major-12", False), lambda r: r.effects["mirror"]),
        (("major-12", True), lambda r: "inversion" in r.modifiers and not r.effects["mirror"]),
    ],
)
def test_shadow_positions(shadow, check):
    burned = (("cups-09", False), ("swords-09", False))
    rules = rules_of(("wands-01", False), ("wands-02", False), shadow, *burned)
    assert check(rules)


def test_the_devils_pact_forbids_two_sigils_and_strength_wards_it():
    burned = (("cups-09", False), ("swords-09", False))
    pact = rules_of(("wands-01", False), ("wands-02", False), ("major-15", False), *burned)
    assert len(pact.forbidden) == 2
    assert pact.effects["chains"] is True
    warded = rules_of(("major-08", False), ("wands-02", False), ("major-15", False), *burned)
    assert "ward" in warded.modifiers
    assert warded.effects["chains"] is False


def test_banishment_beats_awakening():
    rules = rules_of(
        ("wands-01", False),
        ("cups-05", False),
        ("swords-01", False),
        ("cups-09", False),
        ("pentacles-09", False),
    )
    assert "water" in rules.banished
    assert not set(rules.awakened) & set(sigils.of_element("water"))


def test_the_fool_brings_a_wild_sigil():
    rules = rules_of(("major-00", False), *BASE[1:])
    assert rules.wild_sigil == "air"
    assert rules.sigil_state("air") == "wild"


def test_the_wheel_turns_the_number_hourly():
    rules = rules_of(("major-10", False), ("cups-01", False), *BASE[2:])
    assert rules.resonance == 1
    assert [rules.resonance_at(h) for h in (0, 1, 8, 9)] == [1, 2, 9, 1]


def test_preview_covers_every_position():
    card = DrawnCard(tarot.get("major-13"), False)
    shown = preview(card)
    assert set(shown) == {"crown", "heart", "shadow", "burned"}
    assert all(shown[p] for p in shown)
    assert shown["shadow"][0]["title"] == "Memento"
    assert shown["burned"][0]["title"] == "Ashes of Death"


def test_palette_has_every_token():
    palette = palette_for_hue(200)
    assert set(palette) == {"accent", "accent2", "glow", "ink", "sky", "parchment"}
    assert all(v.startswith("#") and len(v) == 7 for v in palette.values())


def make_rules(**constraints) -> DayRules:
    rules = DayRules(day="2026-11-25")
    for key, value in constraints.items():
        setattr(rules.constraints, key, value)
    return rules


@pytest.mark.parametrize(
    ("constraints", "title", "body", "broken"),
    [
        ({"char_limit": 10}, "", "x" * 11, ["char_limit"]),
        ({"char_limit": 10}, "", "x" * 10, []),
        ({"min_sigils": 2}, "", "☉ only", ["min_sigils"]),
        ({"min_sigils": 2}, "☽", "☉ two", []),
        ({"min_words": 3}, "", "two words", ["min_words"]),
        ({"begin_with_sigil": True}, "", "moon ☽", ["begin_with_sigil"]),
        ({"begin_with_sigil": True}, "", " ☽ moon", []),
        ({"even_sigils": True}, "", "☉☽☿", ["even_sigils"]),
        ({"balanced_sigils": True}, "", "☉☽", []),
        ({"balanced_sigils": True}, "", "☉✦☽", ["balanced_sigils"]),
        ({"require": ["fire"]}, "", "no flame", ["require"]),
        ({"require": ["fire"]}, "", ":fire: flame", []),
    ],
)
def test_check_constraints(constraints, title, body, broken):
    violations = check_constraints(title, body, make_rules(**constraints))
    assert [v.rule for v in violations] == broken
