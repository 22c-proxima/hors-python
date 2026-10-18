"""
Recognizer for part-of-day words adjacent to a date ('сегодня вечером').
"""

from datetime import datetime, timedelta
from re import Match

from .recognizer import Recognizer
from ..models import AbstractPeriod, DatesRawData
from ..models.parser_models import FixPeriod
from .recognizer import Recognizer


class PartOfDayRecognizer(Recognizer):
    """
    Recognizes part-of-day words adjacent to a date (pattern (@)?f?([ravgdn])f?(@)?):
    'утром', 'днём', 'полднем', 'вечером', 'ночью' — e.g. 'сегодня вечером'.

    The word must touch an already matched date ('@') on either side, otherwise
    the match is rejected.
    """
    regex_pattern = r'(@)?f?([ravgdn])f?(@)?'

    def parse_match(self, data: DatesRawData, match: Match[str], now: datetime) -> bool:
        """
        Pin a part-of-day word to a representative hour of the day.

        'r' (утро) -> 09:00, 'a'/'d'/'n' (день/днём/полдень) -> 12:00,
        'v' (вечер) -> 17:00, 'g' (ночь) -> 23:00. The resulting period is fixed at
        TIME_UNCERTAIN; only the part-of-day word slot is replaced, adjacent dates
        and prepositions stay in place.

        Returns:
            True when a date marker was present, otherwise False.
        """
        if (match.group(1) is not None) or (match.group(3) is not None):
            hours = 0
            m = match.group(2)
            if m == 'r':
                hours = 9
            elif m in ['a', 'd', 'n']:
                hours = 12
            elif m == 'v':
                hours = 17
            elif m == 'g':
                hours = 23

            if hours != 0:
                date = AbstractPeriod(time=timedelta(seconds=hours*60*60))
                date.fix(FixPeriod.TIME_UNCERTAIN)

                start = match.span()[0]
                length = match.span()[1] - start - 1
                if match.group(1) is not None:
                    start += 1
                    if match.group(3) is not None:
                        length -= 1
                data.replace_tokens_by_dates(start, length, date)

                return True
        # if match.group(1) is not None and match.group(3) is not None:

        return False
