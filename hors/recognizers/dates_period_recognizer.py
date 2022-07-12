from datetime import datetime

from ..dict import Keywords
from ..models import AbstractPeriod, DatesRawData
from ..models.parser_models import FixPeriod
from ..utils import ParserUtils
from .recognizer import Recognizer


class DatesPeriodRecognizer(Recognizer):
    regex_pattern = r'f?(0)[ot]0(M|#)'

    def parse_match(self, data: DatesRawData, match, now: datetime) -> bool:
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
