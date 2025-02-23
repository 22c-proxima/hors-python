from datetime import datetime, timedelta

from .recognizer import Recognizer
from ..models import AbstractPeriod, DatesRawData
from ..models.parser_models import FixPeriod
from .recognizer import Recognizer


class RelativeDayRecognizer(Recognizer):
    regex_pattern = r'[2-6]'

    def parse_match(self, data: DatesRawData, match, now: datetime) -> bool:
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
