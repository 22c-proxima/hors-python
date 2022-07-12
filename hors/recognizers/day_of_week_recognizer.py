from datetime import datetime, timedelta

from .recognizer import Recognizer
from ..dict import Keywords
from ..models import AbstractPeriod, DatesRawData
from ..models.parser_models import FixPeriod
from ..utils import ParserUtils
from .recognizer import Recognizer


class DayOfWeekRecognizer(Recognizer):
    regex_pattern = r'([usxy])?(D)'

    def parse_match(self, data: DatesRawData, match, now: datetime) -> bool:
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
