"""Deterministic, portable randomness.

The daily draw must be *fixed* for a given day: drawing again (even after a reinstall
with the same secret) must reveal the very same five cards. Python's :mod:`random`
module is deterministic too, but its algorithms are an implementation detail. This
module specifies everything explicitly — SHA-256 in counter mode, rejection sampling
and a Fisher–Yates shuffle — so the output is stable across platforms and versions
and could be re-implemented byte-for-byte in another language.
"""

from __future__ import annotations

import hashlib
import hmac
from typing import MutableSequence, Sequence, TypeVar

T = TypeVar("T")

_WORD = 1 << 32


def derive_seed(secret: bytes, *parts: str) -> bytes:
    """Derive a 32-byte seed from a secret and a tuple of labels using HMAC-SHA256."""
    message = "\x1f".join(parts).encode("utf-8")
    return hmac.new(secret, message, hashlib.sha256).digest()


class FateStream:
    """A reproducible stream of random values derived from a seed.

    >>> a, b = FateStream(b"seed"), FateStream(b"seed")
    >>> [a.below(10) for _ in range(5)] == [b.below(10) for _ in range(5)]
    True
    """

    def __init__(self, seed: bytes) -> None:
        self._seed = bytes(seed)
        self._counter = 0
        self._buffer = b""

    def take_bytes(self, count: int) -> bytes:
        """Return the next ``count`` bytes of the stream."""
        while len(self._buffer) < count:
            block = hashlib.sha256(self._seed + self._counter.to_bytes(8, "big")).digest()
            self._counter += 1
            self._buffer += block
        out, self._buffer = self._buffer[:count], self._buffer[count:]
        return out

    def below(self, bound: int) -> int:
        """Return a uniformly distributed integer in ``[0, bound)``."""
        if bound <= 0 or bound > _WORD:
            raise ValueError("bound must be in 1..2**32")
        limit = _WORD - (_WORD % bound)
        while True:
            value = int.from_bytes(self.take_bytes(4), "big")
            if value < limit:
                return value % bound

    def chance(self, numerator: int, denominator: int) -> bool:
        """Return ``True`` with probability ``numerator / denominator``."""
        return self.below(denominator) < numerator

    def choice(self, items: Sequence[T]) -> T:
        """Pick one element of a non-empty sequence."""
        if not items:
            raise IndexError("cannot choose from an empty sequence")
        return items[self.below(len(items))]

    def shuffle(self, items: MutableSequence[T]) -> None:
        """Shuffle ``items`` in place (Fisher–Yates, from the end)."""
        for i in range(len(items) - 1, 0, -1):
            j = self.below(i + 1)
            items[i], items[j] = items[j], items[i]

    def sample(self, items: Sequence[T], count: int) -> list[T]:
        """Return ``count`` distinct elements, in draw order."""
        pool = list(items)
        if count > len(pool):
            raise ValueError("sample larger than population")
        self.shuffle(pool)
        return pool[:count]
