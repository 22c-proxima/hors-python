"""
Recognizer for date-range expressions ('с N по N <месяц>', 'N до N-го числа').
"""

from datetime import datetime
from re import Match

from ..dict import Keywords
from ..models import AbstractPeriod, DatesRawData
from ..models.parser_models import FixPeriod
from ..utils import ParserUtils
from .recognizer import Recognizer


class DatesPeriodRecognizer(Recognizer):
    """
    Recognizes date-range expressions of the form 'с N по N <месяц>' / 'N до N-го числа'
    (pattern f?(0)[ot]0(M|#)): an optional preposition, a day number, a linking word
    ('до'/'по' or 'на'), another day number and a month word or the '#'-marker.

    Only the first day of the range is kept as a period; the rest of the words are
    left in place so other recognizers (e.g. DaysMonthRecognizer) parse them on the next scan.
    """
    regex_pattern = r'f?(0)[ot]0(M|#)'

    def parse_match(self, data: DatesRawData, match: Match[str], now: datetime) -> bool:
        """
        Keep only the first day of the matched range as a period.

        The period is fixed at WEEK+DAY (and MONTH when a month word was given;
        otherwise the current month is used unfixed). The matched slot is replaced
        but the method returns False so the position is skipped on rescan and the
        remaining words of the range are re-parsed by other recognizers.

        Returns:
            False (slots replaced, position marked as skipped).
        """
        month_fixed = False
        m_str = data.tokens[match.start(2)].value
        month = ParserUtils.find_index(m_str, Keywords.months()) + 1
        if month == 0:
            month = now.month
        else:
            month_fixed = True

        t = data.tokens[match.start(1)]
        try:
            day = int(t.value)
        except ValueError:
            day = 0

        period = AbstractPeriod(datetime(now.year, month,
            ParserUtils.get_day_valid_for_month(now.year, month, day)))

        period.fix(FixPeriod.WEEK, FixPeriod.DAY)
        if month_fixed:
            period.fix(FixPeriod.MONTH)

        data.replace_tokens_by_dates(match.start(1), 1, period)

        return False
