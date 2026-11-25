import datetime as dt

import pytest

from nocturne import tarot
from nocturne.ritual import DrawnCard, RitualError, Spread, draw_for_day, validate_keep

SECRET = b"s" * 32
DAY = dt.date(2026, 11, 25)


def test_the_draw_is_fixed_for_a_day():
    first = draw_for_day(SECRET, DAY)
    second = draw_for_day(SECRET, DAY)
    assert [(c.card.id, c.reversed) for c in first] == [(c.card.id, c.reversed) for c in second]


def test_five_distinct_cards():
    hand = draw_for_day(SECRET, DAY)
    assert len(hand) == 5
    assert len({c.card.id for c in hand}) == 5


def test_every_day_is_unique():
    hands = {tuple(c.card.id for c in draw_for_day(SECRET, DAY + dt.timedelta(days=i))) for i in range(60)}
    assert len(hands) == 60


def test_every_codex_is_unique():
    assert [c.card.id for c in draw_for_day(SECRET, DAY)] != [c.card.id for c in draw_for_day(b"t" * 32, DAY)]


def test_roughly_one_card_in_three_is_reversed():
    flags = [c.reversed for i in range(300) for c in draw_for_day(SECRET, DAY + dt.timedelta(days=i))]
    ratio = sum(flags) / len(flags)
    assert 0.27 < ratio < 0.40


@pytest.mark.parametrize(
    "keep",
    [[0, 1], [0, 1, 2, 3], [0, 0, 1], [0, 1, 5], [-1, 1, 2], ["0", 1, 2], [True, 1, 2], None, "012"],
)
def test_invalid_keeps_are_refused(keep):
    with pytest.raises(RitualError):
        validate_keep(keep)


def test_valid_keep_preserves_order():
    assert validate_keep([4, 0, 2]) == (4, 0, 2)


def test_spread_positions_and_ashes():
    hand = tuple(draw_for_day(SECRET, DAY))
    open_spread = Spread(DAY, hand)
    assert not open_spread.sealed
    assert open_spread.kept == {} and open_spread.burned == []
    spread = Spread(DAY, hand, (3, 0, 4))
    assert spread.kept["crown"] is hand[3]
    assert spread.kept["heart"] is hand[0]
    assert spread.kept["shadow"] is hand[4]
    assert spread.burned == [hand[1], hand[2]]
    data = spread.to_dict()
    assert data["keep"] == [3, 0, 4] and len(data["burned"]) == 2


def test_drawn_card_round_trip():
    card = DrawnCard(tarot.get("major-13"), True)
    assert DrawnCard.from_record(card.to_record()) == card
    assert card.to_dict()["orientation"] == "reversed"
