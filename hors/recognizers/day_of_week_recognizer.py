"""
Recognizer for weekday names ('во вторник', 'в прошлую пятницу').
"""

from datetime import datetime, timedelta
from re import Match

from .recognizer import Recognizer
from ..dict import Keywords
from ..models import AbstractPeriod, DatesRawData
from ..models.parser_models import FixPeriod
from ..utils import ParserUtils
from .recognizer import Recognizer


class DayOfWeekRecognizer(Recognizer):
    """
    Recognizes weekday names ('D'), optionally preceded by a relative mode word:
    's' прошлый, 'u' этот/текущий, 'y' ближайший/грядущий, 'x' следующий.
    """
    regex_pattern = r'([usxy])?(D)'

    def parse_match(self, data: DatesRawData, match: Match[str], now: datetime) -> bool:
        """
        Resolve a weekday name to an absolute date relative to `now`.

        Without a prefix the nearest matching weekday is taken (it may be today
        or in the past); 'ближайший' ('y') forces strictly ahead (diff += 7 when
        negative), 'следующий' ('x') adds +7 days, 'прошлый' ('s') subtracts 7.
        The period is fixed down to DAY and flagged with fix_day_of_week so later
        merges keep the weekday semantics.

        Returns:
            True (the match is always consumed).
        """
        date = AbstractPeriod()
        day_of_week = ParserUtils.find_index(data.tokens[match.start(2)].value, Keywords.days_of_week()) + 1
        now_day_of_week = now.weekday() + 1
        diff = day_of_week - now_day_of_week

        if match.group(1) is None:
            date.date = now + timedelta(days=diff)
            date.fix(FixPeriod.DAY)
            date.fix_day_of_week = True
        else:
            v = match.group(1)
            if v == 'y':
                if diff < 0:
                    diff += 7
                date.date = now + timedelta(days=diff)
            elif v == 'x':
                date.date = now + timedelta(days=diff + 7)
            elif v == 's':
                date.date = now + timedelta(days=diff - 7)
            elif v == 'u':
                date.date = now + timedelta(days=diff)
            date.fix_down_to(FixPeriod.DAY)

        s, e = match.span()
        data.replace_tokens_by_dates(s, (e - s), date)

        return True
