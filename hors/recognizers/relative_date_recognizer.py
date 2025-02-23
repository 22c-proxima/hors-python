from datetime import datetime, timedelta

from .recognizer import Recognizer
from ..models import AbstractPeriod, DatesRawData
from ..models.parser_models import FixPeriod
from .recognizer import Recognizer


class RelativeDateRecognizer(Recognizer):
    regex_pattern = r'([usxy])([Ymwd])'

    def parse_match(self, data: DatesRawData, match, now: datetime) -> bool:
        date = AbstractPeriod()
        direction = 0
        m = match.group(1)
        if m in ['y', 'x']:
            direction = 1
        elif m == 's':
            direction = -1

        m = match.group(2)
        if m == 'Y':
            date.date = now.replace(year=now.year + direction)
            date.fix(FixPeriod.YEAR)
        elif m == 'm':
            date.date = now.replace(month=now.month + direction)
            date.fix_down_to(FixPeriod.MONTH)
        elif m == 'w':
            date.date = now + timedelta(days=direction*7)
            date.fix_down_to(FixPeriod.WEEK)
        elif m == 'd':
            date.date = now + timedelta(days=direction)
            date.fix_down_to(FixPeriod.DAY)

        s, e = match.span()
        data.replace_tokens_by_dates(s, (e - s), date)

        return True
