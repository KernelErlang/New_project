from collections import Counter

import pytest

from nocturne.rng import FateStream, derive_seed


def test_same_seed_same_stream():
    a, b = FateStream(b"night"), FateStream(b"night")
    assert [a.below(1000) for _ in range(50)] == [b.below(1000) for _ in range(50)]


def test_different_seeds_diverge():
    a, b = FateStream(b"night"), FateStream(b"day")
    assert [a.below(1000) for _ in range(20)] != [b.below(1000) for _ in range(20)]


def test_known_answer_locks_the_algorithm():
    # If this changes, every past night's draw would change too.
    assert FateStream(b"nocturne").take_bytes(4).hex() == "0793fb89"
    stream = FateStream(b"nocturne")
    assert [stream.below(78) for _ in range(5)] == [23, 40, 66, 4, 29]


def test_below_bounds_and_rough_uniformity():
    stream = FateStream(b"uniform")
    counts = Counter(stream.below(6) for _ in range(6000))
    assert set(counts) == set(range(6))
    assert all(800 < n < 1200 for n in counts.values())


@pytest.mark.parametrize("bound", [0, -1, 2**32 + 1])
def test_below_rejects_bad_bounds(bound):
    with pytest.raises(ValueError, match="bound"):
        FateStream(b"x").below(bound)


def test_shuffle_is_a_permutation():
    items = list(range(78))
    FateStream(b"shuffle").shuffle(items)
    assert sorted(items) == list(range(78))
    assert items != list(range(78))


def test_sample_and_choice():
    stream = FateStream(b"sample")
    sample = stream.sample(range(10), 4)
    assert len(set(sample)) == 4
    assert stream.choice("abc") in "abc"
    with pytest.raises(IndexError):
        stream.choice([])
    with pytest.raises(ValueError, match="sample"):
        stream.sample([1, 2], 3)


def test_chance_extremes():
    stream = FateStream(b"chance")
    assert all(stream.chance(1, 1) for _ in range(20))
    assert not any(stream.chance(0, 5) for _ in range(20))


def test_derive_seed_depends_on_every_part():
    base = derive_seed(b"secret", "draw", "2026-11-25")
    assert len(base) == 32
    assert base == derive_seed(b"secret", "draw", "2026-11-25")
    assert base != derive_seed(b"secret", "draw", "2026-11-26")
    assert base != derive_seed(b"other", "draw", "2026-11-25")
    assert derive_seed(b"s", "ab", "c") != derive_seed(b"s", "a", "bc")
