"""
Recognizer for relative day words ('сегодня', 'вчера', 'послезавтра').
"""

from datetime import datetime, timedelta

from .recognizer import Recognizer
from ..models import AbstractPeriod, DatesRawData
from ..models.parser_models import FixPeriod
from .recognizer import Recognizer


class RelativeDayRecognizer(Recognizer):
    """
    Recognizes relative day words mapped to pattern chars '2'..'6':
    'позавчера' (2), 'вчера' (3), 'сегодня' (4), 'завтра' (5), 'послезавтра' (6).
    """
    regex_pattern = r'[2-6]'

    def parse_match(self, data: DatesRawData, match, now: datetime) -> bool:
        """
        Shift `now` by the day offset encoded in the pattern char (char - 4, i.e. -2..+2)
        and fix the period down to DAY.

        Returns:
            True (the match is always consumed).
        """
        try:
            relative_day = int(match.group(0))
        except ValueError:
            return False
        relative_day -= 4

        date = AbstractPeriod(now + timedelta(days=relative_day))
        date.fix_down_to(FixPeriod.DAY)

        s, e = match.span()
        data.replace_tokens_by_dates(s, (e - s), date)

        return True
