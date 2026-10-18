"""
Recognizer for numeric dates: one or more day numbers followed by a month word or the '#' marker.
"""

from typing import List
from datetime import datetime
from re import Match

from .recognizer import Recognizer
from ..dict import Keywords
from ..models import AbstractPeriod, DatesRawData
from ..models.parser_models import FixPeriod
from ..utils import ParserUtils
from .recognizer import Recognizer


class DaysMonthRecognizer(Recognizer):
    """
    Recognizes one or more day numbers followed by a month word or the '#' marker:
    '1 мая', '3 и 5 июня' (pattern ((0N?)+)(M|#)).
    """
    regex_pattern = r'((0N?)+)(M|#)'

    def parse_match(self, data: DatesRawData, match: Match[str], now: datetime) -> bool:
        """
        Create one period per numeric token before the month word.

        Each day is placed in the matched month of the current year (the current
        month when no month word was found). Every period is fixed at WEEK+DAY and
        additionally MONTH when a month word was explicit. When the month is not
        fixed, a day that would land after an earlier created one is shifted into
        the next month.

        Returns:
            True (the match is always consumed).
        """
        dates: List[AbstractPeriod] = []
        month_fixed = False
        s, e = match.span()
        eg1 = s + len(match.group(1))

        m_str = data.tokens[eg1].value
        month = ParserUtils.find_index(m_str, Keywords.months()) + 1
        if month == 0:
            month = now.month
        else:
            month_fixed = True

        for i in range(s, eg1):
            t = data.tokens[i]
            try:
                day = int(t.value)
            except ValueError:
                continue
            if day <= 0:
                continue

            period = AbstractPeriod(datetime(now.year, month,
                ParserUtils.get_day_valid_for_month(now.year, month, day)))

            period.fix(FixPeriod.WEEK, FixPeriod.DAY)
            if month_fixed:
                period.fix(FixPeriod.MONTH)

            dates.append(period)

            if dates and dates[-1].date < period.date and not month_fixed:
                period.date = datetime(now.year, month + 1,
                    ParserUtils.get_day_valid_for_month(now.year, month + 1, day))

        data.replace_tokens_by_dates(s, (e - s), *dates)

        return True
