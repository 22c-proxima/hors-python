"""
Recognizer for month names ('в мае', 'в прошлом мае').
"""

from datetime import datetime
from re import Match

from .recognizer import Recognizer
from ..dict import Keywords
from ..models import AbstractPeriod, DatesRawData
from ..models.parser_models import FixPeriod
from ..utils import ParserUtils
from .recognizer import Recognizer


class MonthRecognizer(Recognizer):
    """
    Recognizes month words ('M'), optionally preceded by a relative mode word:
    's' прошлый, 'u' этот/текущий, 'y' ближайший/грядущий, 'x' следующий.
    """
    regex_pattern = r'([usxy])?M'

    def parse_match(self, data: DatesRawData, match: Match[str], now: datetime) -> bool:
        """
        Resolve a month name to the first day of that month in the right year.

        'прошлый' ('s') moves the year back when the month is not already past;
        'ближайший' ('y') moves it forward when the month is past; 'следующий' ('x')
        moves it forward unless the month is still ahead in the current year.

        Returns:
            True (the match is always consumed).
        """
        year = now.year
        year_fixed = False
        s, e = match.span()

        g1 = match.group(1) or ''
        m_str = data.tokens[s + len(g1)].value
        month = ParserUtils.find_index(m_str, Keywords.months()) + 1
        if month == 0:
            month = now.month

        month_past = month < now.month
        month_future = month > now.month

        if g1 is not None:
            if g1 == 's' and not month_past:
                year -= 1
            elif g1 == 'y' and month_past:
                year += 1
            elif g1 == 'x' and not month_future:
                year += 1

        date = AbstractPeriod(datetime(year, month, 1))
        date.fix(FixPeriod.MONTH)
        if year_fixed:
            date.fix(FixPeriod.YEAR)

        data.replace_tokens_by_dates(s, (e - s), date)

        return True
