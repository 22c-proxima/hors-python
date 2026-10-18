"""
Small stateless helpers used by the recognizers: lemma matching, year and day clamping.
"""

from typing import List
from calendar import monthrange

from ..dict import Morph


class ParserUtils:
    """Static helpers shared by recognizers."""

    @staticmethod
    def find_index(t: str, l: List[List[str]]) -> int:
        """Return the index of the first sublist whose lemmas contain t, -1 if none."""
        for i, sublist in enumerate(l):
            if Morph.has_one_of_lemmas(t, sublist):
                return i
        return -1

    @staticmethod
    def get_year_from_number(n: int) -> int:
        """
        Interpret a numeric year: 70..99 -> 19xx, anything else below 1000 -> 20xx
        ('5' -> 2005), full years pass through.
        """
        if 70 <= n < 100:
            return 1900 + n
        return n if n >= 1000 else n + 2000

    @staticmethod
    def get_day_valid_for_month(year: int, month: int, day: int) -> int:
        """Clamp day into [1, days_in_month(year, month)]."""
        _, days_in_month = monthrange(year, month)
        return max(1, min(day, days_in_month))
