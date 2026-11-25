"""Small numerological helpers shared by the edicts and the arcane calculus."""

from __future__ import annotations

import re
import unicodedata

MASTER_NUMBERS = frozenset({11, 22, 33})
_WORD = re.compile(r"[a-z]+(?:'[a-z]+)?")


def fold(text: str) -> str:
    """Lower-case ``text`` and strip accents (é → e) so every letter has a value."""
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch)).lower()


def words(text: str) -> list[str]:
    """The Latin-alphabet words of ``text`` (accents folded, apostrophes kept inside words)."""
    return _WORD.findall(fold(text))


def gematria(text: str) -> int:
    """Sum of letter values, a=1 … z=26, ignoring everything that is not a letter."""
    return sum(ord(ch) - 96 for ch in fold(text) if "a" <= ch <= "z")


def digit_sum(number: int) -> int:
    return sum(int(d) for d in str(abs(number)))


def digital_root(number: int, keep_master: bool = False) -> int:
    """Reduce ``number`` by repeated digit sums.

    With ``keep_master`` the reduction stops at the master numbers 11, 22 and 33.
    Zero stays zero.
    """
    number = abs(number)
    while number > 9:
        if keep_master and number in MASTER_NUMBERS:
            return number
        number = digit_sum(number)
    return number


def is_prime(number: int) -> bool:
    if number < 2:
        return False
    if number % 2 == 0:
        return number == 2
    factor = 3
    while factor * factor <= number:
        if number % factor == 0:
            return False
        factor += 2
    return True


def letters_only(text: str) -> str:
    return "".join(ch for ch in fold(text) if "a" <= ch <= "z")


def is_palindrome(text: str, minimum: int = 5) -> bool:
    """True when the letters of ``text`` read the same backwards (and there are enough)."""
    letters = letters_only(text)
    return len(letters) >= minimum and letters == letters[::-1]
