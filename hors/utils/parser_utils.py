from typing import List
from calendar import monthrange

from ..dict import Morph


class ParserUtils:

    @staticmethod
    def find_index(t: str, l: List[List[str]]) -> int:
        for i, sublist in enumerate(l):
            if Morph.has_one_of_lemmas(t, sublist):
                return i
        return -1

    @staticmethod
    def get_year_from_number(n: int) -> int:
        if 70 <= n < 100:
            return 1900 + n
        return n if n >= 1000 else n + 2000

    def get_day_valid_for_month(year: int, month: int, day: int) -> int:
        _, days_in_month = monthrange(year, month)
        return max(1, min(day, days_in_month))
