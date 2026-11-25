"""The hidden formulas. Spoilers, naturally."""

import pytest

from nocturne import arcane
from nocturne.arcane import Inscription, invoke
from nocturne.edicts import DayRules
from nocturne.numerology import digital_root, gematria, is_palindrome, is_prime, words


def rules(**changes) -> DayRules:
    r = DayRules(day="2026-11-25")
    r.resonance = 1  # keep plain test notes from resonating by accident
    for key, value in changes.items():
        setattr(r, key, value)
    return r


def performed(body="", title="", r=None, **kw) -> list[str]:
    return invoke(Inscription(title, body, **kw), r or rules()).rite_ids


# -- numerology ---------------------------------------------------------------------


def test_gematria_and_roots():
    assert gematria("abc") == 6
    assert gematria("Élan!") == gematria("elan")
    assert digital_root(29) == 2
    assert digital_root(29, keep_master=True) == 11
    assert digital_root(0) == 0
    assert words("Don't stop — ever") == ["don't", "stop", "ever"]
    assert is_prime(107) and not is_prime(1) and not is_prime(91)
    assert is_palindrome("Level up? No: 'Level'") is False
    assert is_palindrome("Never odd or even")


# -- the rites ----------------------------------------------------------------------


def test_plain_ink_simply_settles():
    assert performed("quiet") == ["ink_settles"]


@pytest.mark.parametrize(
    ("kwargs", "rite"),
    [
        ({"body": "☉☽"}, "eclipse"),
        ({"body": "☽♂ night"}, "blood_moon"),
        ({"body": "☽ blood"}, "blood_moon"),
        ({"title": "m"}, "thirteenth_toll"),
        ({"body": "zc"}, "master_number"),
        ({"body": "quiet", "hour": 0}, "witching_hour"),
        ({"body": "quiet", "hour": 3, "minute": 33}, "witching_hour"),
        ({"title": "Nevermore"}, "nevermore"),
        ({"body": "☠ bones", "hour": 23}, "night_moths"),
        ({"body": "☈ now!!!"}, "tower_strike"),
        ({"body": "☉✦☠♄"}, "balance"),
        ({"body": "✦✦ twice"}, "twin_flames"),
        ({"body": "🜂🜄 steam"}, "conjunction"),
        ({"body": "fire 🜂 🜂 🜂"}, "ember_storm"),
        ({"body": "sea ☽ 🜄 ☠"}, "drowned_tide"),
        ({"body": "sky 🜁 ☿ ✦"}, "gale"),
        ({"body": "soil 🜃 ♄ ✶"}, "thornbloom"),
        ({"body": "✦ ✶ ☄ wishes"}, "starfall"),
        ({"body": "♀❦ love"}, "petal_rain"),
        ({"title": "Level", "body": "x"}, "mirror_of_mercury"),
        ({"body": "☿ ☿ ☿ x"}, "mirror_of_mercury"),
        ({"body": "☉✦♄"}, "wordless_prayer"),
        ({"body": "zzzzc"}, "prime_glint"),
        ({"body": "x" * 61, "velocity": 300}, "chariot_streak"),
        ({"body": "✶ dawn", "hour": 4}, "lantern_vigil"),
        ({"body": "✠✠✠ amen"}, "trinity_rays"),
        ({"body": "☉🜄🜁🜃☉"}, "ouroboros"),
        ({"body": "☉🜄🜁⛤☉"}, "ouroboros"),
    ],
)
def test_each_rite_has_a_trigger(kwargs, rite):
    assert rite in performed(**kwargs)


@pytest.mark.parametrize(
    ("kwargs", "rite"),
    [
        ({"body": "☉ ☿ ☽"}, "eclipse"),  # not adjacent
        ({"body": "☠ bones", "hour": 12}, "night_moths"),
        ({"body": "☈ now!"}, "tower_strike"),
        ({"body": "✦ a ✦"}, "twin_flames"),
        ({"body": "🜂 x 🜄"}, "conjunction"),
        ({"body": "fire 🜂 🜂"}, "ember_storm"),
        ({"body": "x" * 61, "velocity": 200}, "chariot_streak"),
        ({"body": "☉🜄🜁🜃"}, "ouroboros"),
    ],
)
def test_near_misses_do_not_trigger(kwargs, rite):
    assert rite not in performed(**kwargs)


def test_resonance_follows_the_heart():
    assert "resonance" in performed("c", r=rules(resonance=3))
    assert "resonance" not in performed("c", r=rules(resonance=4))


def test_the_wheel_turns_resonance_with_the_hour():
    turning = rules(resonance=1, modifiers=["wheel"])
    assert "resonance" in performed("c", r=turning, hour=2)
    assert "resonance" not in performed("c", r=turning, hour=3)


def test_the_crown_remembers_its_number():
    assert "crown_recognition" in performed("☉☿", r=rules(crown_value=20))
    assert "crown_recognition" not in performed("☉☿", r=rules(crown_value=21))
    assert "crown_recognition" in performed("☉☿", r=rules(crown_value=21, modifiers=["decree"]))


@pytest.mark.parametrize(
    ("modifier", "kwargs", "rite"),
    [
        ("twin", {"body": "✦ a ✦"}, "twin_flames"),
        ("fusion", {"body": "🜂 x 🜄"}, "conjunction"),
        ("four_tools", {"body": "fire 🜂 ☉"}, "ember_storm"),
        ("starfield", {"body": "✦ once"}, "starfall"),
        ("bloom", {"body": "♀ alone"}, "petal_rain"),
        ("tremor", {"body": "☈ now!"}, "tower_strike"),
        ("moths", {"body": "☠ noon", "hour": 12}, "night_moths"),
        ("illusion", {"body": "quiet", "hour": 22}, "witching_hour"),
        ("balance", {"body": "☉ ☽ dusk"}, "balance"),
        ("illuminate", {"body": "✠ ✠ amen"}, "trinity_rays"),
        ("velocity", {"body": "x" * 61, "velocity": 160}, "chariot_streak"),
        ("ouroboros", {"body": "🜂🜄🜁🜃"}, "ouroboros"),
        ("inversion", {"body": "a racecar passes"}, "mirror_of_mercury"),
        ("lantern", {"body": "first", "first_of_night": True}, "lantern_vigil"),
    ],
)
def test_arcana_bend_the_formulas(modifier, kwargs, rite):
    assert rite not in performed(**kwargs)
    assert rite in performed(r=rules(modifiers=[modifier]), **kwargs)


def test_the_wild_sigil_counts_as_every_element():
    wild = rules(wild_sigil="air", modifiers=["wild"])
    assert "ember_storm" in performed("fire 🜂 🜂 🜁", r=wild)
    assert "ember_storm" not in performed("fire 🜂 🜂 🜁")


def test_forbidden_sigils_bind_unless_warded():
    forbid = rules(forbidden=["sol"])
    result = invoke(Inscription("", "☉ rises"), forbid)
    assert result.bound and result.rite_ids[0] == "pact_chains"
    warded = invoke(Inscription("", "☉ rises"), rules(forbidden=["sol"], modifiers=["ward"]))
    assert not warded.bound and warded.rite_ids[0] == "warded"


def test_banished_sigils_turn_to_ash_and_count_for_nothing():
    ash = rules(banished=["fire"])
    ids = performed("fire 🜂 🜂 🜂", r=ash)
    assert ids[0] == "ashen"
    assert "ember_storm" not in ids and "twin_flames" not in ids


def test_no_more_than_three_rites_at_once():
    ids = performed("☉☽♂ blood nevermore ✦✦ ✶ ☄", title="Level", hour=0)
    assert len([i for i in ids if arcane.BY_ID[i].tier > 0]) == arcane.MAX_RITES


def test_grand_rites_come_first():
    ids = performed("☉🜄🜁🜃☉ nevermore")
    assert ids[0] == "ouroboros"


def test_awakened_sigils_intensify_the_rite():
    plain = invoke(Inscription("", "☉☽"), rules()).performed[0]
    awake = invoke(Inscription("", "☉☽"), rules(awakened=["sol"])).performed[0]
    assert not plain["awakened"] and awake["awakened"]
    assert awake["intensity"] > plain["intensity"]


def test_invocation_serialises():
    result = invoke(Inscription("Level", "☉☽ :fire:"), rules(forbidden=["fire"])).to_dict()
    assert result["bound"] is True
    assert {"id": "fire", "state": "forbidden"} in result["sigils"]
    assert result["flames"] >= 1
    assert result["weight"] == gematria("Level")


def test_codex_hides_undiscovered_lore():
    entries = arcane.codex({"eclipse": {"count": 2, "first_day": "2026-11-25", "first_note": 1}})
    eclipse = next(e for e in entries if e["id"] == "eclipse")
    hidden = next(e for e in entries if e["id"] == "ouroboros")
    assert eclipse["discovered"] and eclipse["lore"] and eclipse["count"] == 2
    assert not hidden["discovered"] and hidden["lore"] is None and hidden["name"] == "???"
    assert all(e["hint"] for e in entries)
    assert "ink_settles" not in {e["id"] for e in entries}
