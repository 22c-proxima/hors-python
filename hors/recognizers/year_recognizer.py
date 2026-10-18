"""
Recognizer for year numbers ('в 2024 году', '1985').
"""

from datetime import datetime
from re import Match

from .recognizer import Recognizer
from ..models import AbstractPeriod, DatesRawData
from ..models.parser_models import FixPeriod
from ..utils import ParserUtils
from .recognizer import Recognizer


class YearRecognizer(Recognizer):
    """
    Recognizes year numbers in the pattern: a four-digit number ('1') optionally
    followed by the word "год" ('Y'), or any other number ('0') followed by "год".

    Short numbers are expanded by ParserUtils.get_year_from_number
    (70..99 -> 19xx, otherwise <1000 -> 20xx), so '25 года' becomes 2025.
    """
    regex_pattern = r'(1)Y?|(0)Y'

    def parse_match(self, data: DatesRawData, match: Match[str], now: datetime) -> bool:
        """
        Build a period fixed at YEAR from the matched numeric token.

        The matched slot(s) are replaced by one AbstractPeriod whose date is Jan 1
        of the year; day and time components stay unfixed for later recognizers.

        Returns:
            True (the match is always consumed).
        """
        s, e = match.span()
        try:
            n = int(data.tokens[s].value)
        except ValueError:
            n = 0
        year = ParserUtils.get_year_from_number(n)
        date = AbstractPeriod(datetime(year, 1, 1))
        date.fix(FixPeriod.YEAR)
        data.replace_tokens_by_dates(s, (e - s), date)
        return True
